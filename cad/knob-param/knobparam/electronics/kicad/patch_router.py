"""Finish the last few connections of a routed board by hand-rule search (main board v2, 9 Nov 2026).

Freerouting left a handful of connections on the main board that it would not make in any number of passes (board L's header
pins, the USB pair into the chip, one flex line into its ribbon). This joins them one at a time, around the copper already on
the board, without moving anything:
  - each net's copper is split into islands (pads, tracks and vias that touch on a shared layer)
  - on a 0.05 mm grid over the net's area, every other net's copper on each routing layer is measured exactly (pads in their own
    frame, tracks as segments, vias as discs, non-plated holes as holes) and a cell is blocked where a track of the net's width
    would come within the clearance of it (+ a margin for the straight lines between cell centres), or within the edge rule of the
    board's outline and windows; a no-track rule area on a layer blocks that layer
  - a through via may go where it clears every routing layer, the holes and the other vias
  - the search is router4's A* in C (8 directions, vias between any two routing layers), from the largest island to the rest
  - the path becomes tracks (collinear cells merged) and vias, added to the board locked; KiCad's DRC checks the result.
Run with the system python that has pcbnew (/usr/bin/python3)."""
import ctypes, math
import numpy as np
import pcbnew
from shapely.geometry import Point, LineString, Polygon, box
from shapely import affinity
import shapely
import router4

INF = np.float32(np.inf)
KEEP = []   # every board item taken off the board: KiCad 7's python loses the board's track list if their wrappers are freed


def _mm(v):
    return pcbnew.ToMM(v)


def pad_info(p):
    x, y = _mm(p.GetPosition().x), _mm(p.GetPosition().y)
    sh = p.GetShape(); ang = p.GetOrientationDegrees()
    w, h = _mm(p.GetSize().x), _mm(p.GetSize().y)
    if sh == pcbnew.PAD_SHAPE_CIRCLE:
        kind = "circle"
    elif sh == pcbnew.PAD_SHAPE_OVAL:
        kind = "oval"
    elif sh == pcbnew.PAD_SHAPE_CUSTOM:   # its outline's box, square to the board (larger than the pad: safe)
        bb = p.GetBoundingBox(); kind = "rect"; ang = 0.0
        w, h = _mm(bb.GetWidth()), _mm(bb.GetHeight())
    else:
        kind = "rect"
    return dict(x=x, y=y, w=w, h=h, kind=kind, ang=ang)


def pad_dist(X, Y, pi):
    """Signed distance from points to the pad (negative inside), in the pad's own frame."""
    a = math.radians(pi["ang"]); dx, dy = X - pi["x"], Y - pi["y"]
    # KiCad's y points down and its angles turn counter-clockwise on screen: the pad frame is the board frame turned by -a in y-down
    u = dx * math.cos(a) - dy * math.sin(a); v = dx * math.sin(a) + dy * math.cos(a)
    return router4.shape_dist(u, v, 0.0, 0.0, pi["w"], pi["h"], pi["kind"])


def pad_poly(pi, grow=0.0):
    if pi["kind"] == "circle":
        return Point(pi["x"], pi["y"]).buffer(pi["w"] / 2 + grow, 16)
    if pi["kind"] == "oval":
        r = min(pi["w"], pi["h"]) / 2; l = (max(pi["w"], pi["h"]) - 2 * r) / 2
        g = LineString([(-l, 0), (l, 0)] if pi["w"] >= pi["h"] else [(0, -l), (0, l)]).buffer(r + grow, 16)
    else:
        g = box(-pi["w"] / 2 - grow, -pi["h"] / 2 - grow, pi["w"] / 2 + grow, pi["h"] / 2 + grow)
    # the same turn as pad_dist: a point (u, v) of the pad frame sits at x = u cos a + v sin a, y = -u sin a + v cos a
    a = math.radians(pi["ang"])
    g = affinity.affine_transform(g, [math.cos(a), math.sin(a), -math.sin(a), math.cos(a), pi["x"], pi["y"]])
    return g


class PatchRouter:
    def __init__(self, board, layers, outline_poly, rules, widths, analog=(), analog_extra=0.05, keepouts=None, g=0.05,
                 margin=0.04, via_cost=0.8, log=print):
        """layers: the routing layers in order (pcbnew ids); outline_poly: the board with its windows as holes (shapely, KiCad mm);
        rules: clearance, edge, via_d, via_drill, hole_clearance, hole_to_hole; widths: {net: width, 'default': w};
        analog: nets that keep clearance + analog_extra to everything; keepouts: {layer id: [shapely polygons]} (no tracks)."""
        self.b, self.layers, self.rules, self.widths = board, list(layers), rules, widths
        self.L = {l: i for i, l in enumerate(self.layers)}
        self.outline, self.analog, self.ax = outline_poly, set(analog), analog_extra
        self.keepouts = keepouts or {}; self.g, self.ms, self.via_cost, self.log = g, margin, via_cost, log
        self.lib = router4._lib()
        self.items = []   # dict(net, layers (set of routing layer indices), kind, geom data)
        for f in board.GetFootprints():
            for p in f.Pads():
                lays = {self.L[l] for l in self.layers if p.IsOnLayer(l)}
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    self.items.append(dict(net="", kind="hole", x=_mm(p.GetPosition().x), y=_mm(p.GetPosition().y),
                                           r=_mm(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2, layers=set(range(len(self.layers)))))
                    continue
                if not lays:
                    continue
                it = dict(net=p.GetNetname(), kind="pad", layers=lays, pi=pad_info(p), ref=f.GetReference(), num=p.GetNumber())
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                    it["drill"] = _mm(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2
                self.items.append(it)
        for t in board.GetTracks():
            if t.GetClass() == "PCB_VIA":
                self.items.append(dict(net=t.GetNetname(), kind="via", x=_mm(t.GetPosition().x), y=_mm(t.GetPosition().y),
                                       r=_mm(t.GetWidth()) / 2, drill=_mm(t.GetDrillValue()) / 2, layers=set(range(len(self.layers))),
                                       obj=t, locked=t.IsLocked()))
            elif t.GetLayer() in self.L:
                self.items.append(dict(net=t.GetNetname(), kind="track", layers={self.L[t.GetLayer()]},
                                       a=(_mm(t.GetStart().x), _mm(t.GetStart().y)), b=(_mm(t.GetEnd().x), _mm(t.GetEnd().y)),
                                       hw=_mm(t.GetWidth()) / 2, obj=t, locked=t.IsLocked()))
        self.ripped = {}   # net -> times its tracks were taken up for another net (each time dearer to take up again)

    # ---- geometry
    def _shape(self, it, grow=0.0):
        if it["kind"] == "pad":
            return pad_poly(it["pi"], grow)
        if it["kind"] in ("via", "hole"):
            return Point(it["x"], it["y"]).buffer(it["r"] + grow, 16)
        return LineString([it["a"], it["b"]]).buffer(it["hw"] + grow, 8) if it["a"] != it["b"] else Point(it["a"]).buffer(it["hw"] + grow, 8)

    def _bbox(self, it):
        if it["kind"] == "pad":
            r = math.hypot(it["pi"]["w"], it["pi"]["h"]) / 2
            return it["pi"]["x"] - r, it["pi"]["y"] - r, it["pi"]["x"] + r, it["pi"]["y"] + r
        if it["kind"] in ("via", "hole"):
            return it["x"] - it["r"], it["y"] - it["r"], it["x"] + it["r"], it["y"] + it["r"]
        (ax, ay), (bx, by) = it["a"], it["b"]
        return min(ax, bx) - it["hw"], min(ay, by) - it["hw"], max(ax, bx) + it["hw"], max(ay, by) + it["hw"]

    def _dist(self, it, X, Y):
        if it["kind"] == "pad":
            return pad_dist(X, Y, it["pi"])
        if it["kind"] in ("via", "hole"):
            return np.hypot(X - it["x"], Y - it["y"]) - it["r"]
        (ax, ay), (bx, by) = it["a"], it["b"]; vx, vy = bx - ax, by - ay; l2 = vx * vx + vy * vy or 1e-12
        t = np.clip(((X - ax) * vx + (Y - ay) * vy) / l2, 0, 1)
        return np.hypot(X - ax - t * vx, Y - ay - t * vy) - it["hw"]

    def islands(self, net):
        its = [i for i, it in enumerate(self.items) if it["net"] == net]
        geo = {i: self._shape(self.items[i], 0.001) for i in its}
        par = {i: i for i in its}

        def find(i):
            while par[i] != i:
                par[i] = par[par[i]]; i = par[i]
            return i
        for k, i in enumerate(its):
            for j in its[k + 1:]:
                if self.items[i]["layers"] & self.items[j]["layers"] and geo[i].intersects(geo[j]):
                    par[find(i)] = find(j)
        groups = {}
        for i in its:
            groups.setdefault(find(i), []).append(i)
        return sorted(groups.values(), key=len, reverse=True)

    # ---- one net
    def soft(self, it):
        """Copper that may be taken up and laid again: the router's own tracks and vias (not locked), not ground."""
        return it["kind"] in ("track", "via") and not it.get("locked", True) and it["net"] not in ("GND", "")

    def route_net(self, net, width=None, pad=6.0, maxexp=60_000_000, rip=False, pen0=30.0, want=None, layer_cost=None):
        """Join the net's islands; returns (islands left unjoined, what was added, nets whose tracks were taken up). With rip, the
        router's own tracks of other nets may be crossed at a price (pen0 per cell, more for a net taken up before); the ones crossed
        are taken up and their nets come back for the caller to join again."""
        width = width or self.widths.get(net, self.widths["default"])
        isl = self.islands(net)
        if want is not None:   # only these islands are joined (the rest of the net's copper is still free to cross)
            isl = [grp for grp in isl if want([self.items[i] for i in grp])]
        if len(isl) < 2:
            return 0, [], set()
        g, ms, c = self.g, self.ms, self.rules["clearance"] + (self.ax if net in self.analog else 0.0)
        bbs = [self._bbox(self.items[i]) for grp in isl for i in grp]
        x0 = math.floor((min(b_[0] for b_ in bbs) - pad) / g) * g; y0 = math.floor((min(b_[1] for b_ in bbs) - pad) / g) * g
        x1 = max(b_[2] for b_ in bbs) + pad; y1 = max(b_[3] for b_ in bbs) + pad
        bx0, by0, bx1, by1 = self.outline.bounds
        x0, y0, x1, y1 = max(x0, math.floor(bx0 / g) * g), max(y0, math.floor(by0 / g) * g), min(x1, bx1), min(y1, by1)
        nx, ny = int((x1 - x0) / g) + 2, int((y1 - y0) / g) + 2; N = nx * ny; nl = len(self.layers)
        X, Y = np.meshgrid(x0 + g * np.arange(nx), y0 + g * np.arange(ny))
        D = np.full((nl, ny, nx), np.inf, np.float32)      # distance to other nets' copper (analog copper counted bigger)
        Dv = np.full((ny, nx), np.inf, np.float32)         # via: to every other via and hole (hole to hole, any net)
        Dsmd = np.full((ny, nx), np.inf, np.float32)       # via: to the net's own SMD pads (no via in a pad: solder runs down it)
        Ds = np.full((nl, ny, nx), np.inf, np.float32)     # the same for copper that may be taken up (rip)
        Dvs = np.full((ny, nx), np.inf, np.float32); Pc = np.zeros((ny, nx), np.float32)
        reach = width / 2 + c + ms + 0.6
        for it in self.items:
            sft = rip and it["net"] != net and self.soft(it)
            own_smd = it["net"] == net and it["kind"] == "pad" and "drill" not in it
            if it["net"] == net and it["kind"] != "hole" and "drill" not in it and not own_smd:
                continue   # own tracks: free (own vias and plated holes still keep hole-to-hole from a new via)
            bx_0, by_0, bx_1, by_1 = self._bbox(it)
            ix0 = max(0, int((bx_0 - reach - x0) / g)); ix1 = min(nx, int((bx_1 + reach - x0) / g) + 2)
            iy0 = max(0, int((by_0 - reach - y0) / g)); iy1 = min(ny, int((by_1 + reach - y0) / g) + 2)
            if ix0 >= ix1 or iy0 >= iy1:
                continue
            sl = (slice(iy0, iy1), slice(ix0, ix1)); Xs, Ys = X[sl], Y[sl]
            if own_smd:
                Dsmd[sl] = np.minimum(Dsmd[sl], self._dist(it, Xs, Ys)); continue
            if "drill" in it or it["kind"] == "hole":   # hole to hole for new vias (drill edge to drill edge)
                hx, hy = (it["x"], it["y"]) if it["kind"] in ("via", "hole") else (it["pi"]["x"], it["pi"]["y"])
                dh = np.hypot(Xs - hx, Ys - hy) - it.get("drill", it.get("r"))
                if sft:
                    Dvs[sl] = np.minimum(Dvs[sl], dh)
                else:
                    Dv[sl] = np.minimum(Dv[sl], dh)
            if it["net"] == net:
                continue
            d = self._dist(it, Xs, Ys)
            if sft:
                if it["net"] in self.analog:
                    d = d - self.ax
                pen = pen0 * (1 + 2 * self.ripped.get(it["net"], 0))
                Pc[sl] = np.where(d < c + self.rules["via_d"] / 2 + ms, np.maximum(Pc[sl], pen), Pc[sl])
                for L in it["layers"]:
                    Ds[L][sl] = np.minimum(Ds[L][sl], d)
                continue
            if it["kind"] == "hole":
                d = d - (self.rules["hole_clearance"] - self.rules["clearance"])
            elif it["net"] in self.analog:
                d = d - self.ax
            for L in it["layers"]:
                D[L][sl] = np.minimum(D[L][sl], d)
        inside = shapely.contains_xy(self.outline, X.ravel(), Y.ravel()).reshape(X.shape)
        from scipy.ndimage import distance_transform_edt
        dedge = (distance_transform_edt(inside) - 1.0) * g      # cells to the nearest outside cell, less a cell (the edge lies between)
        # a cell is closed to steps where the net's track would come within the clearance at the cell's centre (+ mo); the corner
        # cells of a diagonal step must keep the clearance + half a cell diagonal, so the diagonal keeps it all along; straight runs
        # are checked exactly once found (_violations) and the search goes again around anything they come too close to
        mo = 0.005
        blk = (D < c + width / 2 + mo) | (dedge < self.rules["edge"] + width / 2 + mo)[None]
        blk_d = (D < c + width / 2 + ms) | (dedge < self.rules["edge"] + width / 2 + ms)[None]
        for lay, polys in self.keepouts.items():
            if lay in self.L:
                for pg in polys:
                    km = shapely.contains_xy(pg.buffer(width / 2 + ms), X.ravel(), Y.ravel()).reshape(X.shape)
                    blk[self.L[lay]] |= km; blk_d[self.L[lay]] |= km
        vr = self.rules["via_d"] / 2
        via_ok = ((D >= c + vr + ms).all(axis=0) & (dedge >= self.rules["edge"] + vr + ms) &
                  (Dv >= self.rules["via_drill"] / 2 + self.rules["hole_to_hole"] + ms) & (Dsmd >= vr + 0.05))
        soft_c = (Ds < c + width / 2 + ms) & ~blk                     # crossing the router's copper: allowed at a price
        soft_v = (Ds < c + vr + ms).any(axis=0) | (Dvs < self.rules["via_drill"] / 2 + self.rules["hole_to_hole"] + ms)
        # own copper: its cells are free to enter (a pad's own clearance zone is part of it)
        cells = []
        for grp in isl:
            m = np.zeros((nl, ny, nx), bool)
            for i in grp:
                it = self.items[i]
                core = self._shape(it, -min(0.03, 0.3 * self._minw(it)))
                inn = shapely.contains_xy(core, X.ravel(), Y.ravel()).reshape(X.shape)
                for L in it["layers"]:
                    m[L] |= inn & ~blk[L]   # cells in its copper where this net's track keeps every clearance
                if not any((inn & ~blk[L]).any() for L in it["layers"]):   # none: its middle cell (the track starts in the copper)
                    ix = int(round((self._ctr(it)[0] - x0) / g)); iy = int(round((self._ctr(it)[1] - y0) / g))
                    if 0 <= ix < nx and 0 <= iy < ny:
                        for L in it["layers"]:
                            m[L][iy, ix] = True
            cells.append(m)
        cost = np.ones((nl, ny, nx), np.float32) + soft_c * Pc[None]
        if layer_cost:   # {layer id: factor}: steer the net onto some layers
            for lay, f in layer_cost.items():
                if lay in self.L:
                    cost[self.L[lay]] *= np.float32(f)
        cost[blk] = INF
        own = np.zeros((nl, ny, nx), bool)
        for m in cells:
            own |= m
        cost[own] = 1.0; blk_u8 = ((blk_d | blk) & ~own).astype(np.uint8)
        vc = np.where(via_ok, np.float32(self.via_cost) + soft_v * Pc * 8 * g, INF).astype(np.float32)
        victims = set()
        # join islands while any search succeeds: from the largest group first; if it finds none of the rest, from the next group
        group = list(range(len(isl))); added = []
        def members(gid):
            return [k for k in range(len(isl)) if group[k] == gid]
        P = router4._ptr
        tried = set(); retries = {}
        while len(set(group)) > 1:
            gids = sorted(set(group), key=lambda q: -sum(len(isl[k]) for k in members(q)))
            src_g = next((q for q in gids if q not in tried), None)
            if src_g is None:
                break
            tree = np.zeros((nl, ny, nx), bool)
            for k in members(src_g):
                tree |= cells[k]
            for (pth, _w) in [(a["path"], None) for a in added if a["gid"] == src_g]:
                pm = np.zeros(nl * N, bool); pm[pth] = True; tree |= pm.reshape(nl, ny, nx)
            tgt = np.zeros(nl * N, np.uint8); owner = {}; boxes = []
            for k in range(len(isl)):
                if group[k] == src_g:
                    continue
                f = np.flatnonzero(cells[k].ravel()); tgt[f] = 1
                for u in f.tolist():
                    owner[u] = k
                f2 = f % N; iy, ix = np.divmod(f2, nx)
                boxes.append([int(ix.min()), int(iy.min()), int(ix.max()), int(iy.max())])
            src = np.flatnonzero(tree.ravel()).astype(np.int32)
            out = np.zeros(400000, np.int32); rs = ctypes.c_int(0); tb = np.ascontiguousarray(boxes, np.int32)
            n = self.lib.route_search(nx, ny, nl, P(cost.ravel(), ctypes.c_float), P(vc.ravel(), ctypes.c_float),
                                      P(blk_u8.ravel(), ctypes.c_uint8), P(src, ctypes.c_int), len(src), P(tgt, ctypes.c_uint8), None,
                                      P(tb, ctypes.c_int), len(tb), g, P(out, ctypes.c_int), len(out), ctypes.byref(rs), maxexp)
            if n == 0:
                tried.add(src_g); continue
            path = out[:n].tolist()
            bad = self._violations(net, width, c, path, x0, y0, nx, N)
            if bad:
                if retries.get(src_g, 0) >= 12:
                    tried.add(src_g); continue
                retries[src_g] = retries.get(src_g, 0) + 1
                for L, bx_, by_ in bad:   # close the cells around each spot that came too close, and search again
                    near = np.hypot(X - bx_, Y - by_) < 0.08
                    cost[L][near & ~own[L]] = INF
                continue
            k = owner[path[-1]]; old_g = group[k]
            if rip:
                victims |= self._take_up(net, width, c, path, x0, y0, nx, N)
            a = self._apply(net, width, path, x0, y0, nx, N); a["path"] = path; a["gid"] = src_g; added.append(a)
            for j in range(len(isl)):
                if group[j] == old_g:
                    group[j] = src_g
            for a2 in added:
                if a2["gid"] == old_g:
                    a2["gid"] = src_g
            tried.discard(src_g)
            for v in a["vias"]:   # the new vias: no second via of this net right beside them
                vx_, vy_ = v
                near = np.hypot(X - vx_, Y - vy_) < self.rules["via_drill"] + self.rules["hole_to_hole"] + ms
                vc[near] = INF
        left = list(range(len(set(group)) - 1))
        for v in victims:
            self.ripped[v] = self.ripped.get(v, 0) + 1
        self.last = dict(blk=blk, cells=cells, x0=x0, y0=y0, nx=nx, ny=ny, D=D, dedge=dedge, via_ok=via_ok, X=X, Y=Y)   # for a look
        return len(left), added, victims

    def _runs(self, path, x0, y0, nx, N):
        """The path as (layer index, corner points) runs, collinear cells merged, and its vias."""
        g = self.g
        pts = [(u // N, x0 + g * ((u % N) % nx), y0 + g * ((u % N) // nx)) for u in path]
        runs, cur, vias = [], [pts[0]], []
        for p in pts[1:]:
            if p[0] != cur[-1][0]:
                vias.append((p[1], p[2])); runs.append(cur); cur = [p]
            else:
                cur.append(p)
        runs.append(cur)
        out = []
        for run in runs:
            q = [(x, y) for _l, x, y in run]
            simp = [q[0]]
            for i in range(1, len(q) - 1):
                (ax, ay), (bx, by), (cx, cy) = simp[-1], q[i], q[i + 1]
                if abs((bx - ax) * (cy - by) - (by - ay) * (cx - bx)) > 1e-9:
                    simp.append(q[i])
            if len(q) > 1:
                simp.append(q[-1])
            out.append((run[0][0], simp))
        return out, vias, pts

    def _violations(self, net, width, c, path, x0, y0, nx, N):
        """Spots along the path's tracks (every 0.01 mm) that come within the clearance of other nets' copper, the holes or the
        edge, measured exactly: [(layer index, x, y)]."""
        runs, _v, _p = self._runs(path, x0, y0, nx, N)
        bad = []
        bnd = self.outline.boundary
        for L, simp in runs:
            for (ax, ay), (bx, by) in zip(simp, simp[1:]):
                n_ = max(2, int(math.hypot(bx - ax, by - ay) / 0.01) + 1)
                sx = np.linspace(ax, bx, n_); sy = np.linspace(ay, by, n_)
                lo_x, hi_x, lo_y, hi_y = min(ax, bx) - 1.0, max(ax, bx) + 1.0, min(ay, by) - 1.0, max(ay, by) + 1.0
                worst = np.full(n_, np.inf)
                for it in self.items:
                    if it["net"] == net or L not in it["layers"]:
                        continue
                    b0, b1, b2, b3 = self._bbox(it)
                    if b2 < lo_x or b0 > hi_x or b3 < lo_y or b1 > hi_y:
                        continue
                    d = self._dist(it, sx, sy)
                    if it["kind"] == "hole":
                        d = d - (self.rules["hole_clearance"] - self.rules["clearance"])
                    elif it["net"] in self.analog:
                        d = d - self.ax
                    worst = np.minimum(worst, d)
                de = shapely.distance(bnd, shapely.points(np.c_[sx, sy]))
                hit = (worst < c + width / 2 - 1e-4) | (de < self.rules["edge"] + width / 2 - 1e-4)
                for j in np.flatnonzero(hit)[::3]:
                    bad.append((L, float(sx[j]), float(sy[j])))
        return bad

    def _take_up(self, net, width, c, path, x0, y0, nx, N):
        """Remove the router's copper of other nets that the path comes too close to; returns their nets."""
        g, ms = self.g, self.ms; vr = self.rules["via_d"] / 2
        pts = np.array([(u // N, x0 + g * ((u % N) % nx), y0 + g * ((u % N) // nx)) for u in path])
        vias = [(pts[i + 1][1], pts[i + 1][2]) for i in range(len(pts) - 1) if pts[i][0] != pts[i + 1][0]]
        gone, nets = [], set()
        for it in self.items:
            if it["net"] == net or not self.soft(it):
                continue
            extra = self.ax if it["net"] in self.analog else 0.0
            hit = False
            for L in it["layers"]:
                q = pts[pts[:, 0] == L]
                if len(q) and (self._dist(it, q[:, 1], q[:, 2]) < c + extra + width / 2 + 0.02).any():
                    hit = True; break
            if not hit and vias:
                va = np.array(vias)
                if (self._dist(it, va[:, 0], va[:, 1]) < c + extra + vr + 0.02).any():
                    hit = True
                elif it["kind"] == "via" and (np.hypot(va[:, 0] - it["x"], va[:, 1] - it["y"]) <
                                              self.rules["via_drill"] + self.rules["hole_to_hole"] + 0.02).any():
                    hit = True
            if hit:
                gone.append(it); nets.add(it["net"])
        ids = {id(it) for it in gone}
        for it in gone:
            self.b.Remove(it["obj"]); KEEP.append(it["obj"])
        self.items = [it for it in self.items if id(it) not in ids]
        return nets

    def _minw(self, it):
        if it["kind"] == "pad":
            return min(it["pi"]["w"], it["pi"]["h"])
        return 2 * it.get("hw", it.get("r", 0.1))

    def _ctr(self, it):
        if it["kind"] == "pad":
            return it["pi"]["x"], it["pi"]["y"]
        if it["kind"] in ("via", "hole"):
            return it["x"], it["y"]
        return ((it["a"][0] + it["b"][0]) / 2, (it["a"][1] + it["b"][1]) / 2)

    def _apply(self, net, width, path, x0, y0, nx, N):
        b = self.b; ni = b.FindNet(net)
        runs, vias, pts = self._runs(path, x0, y0, nx, N)
        segs = 0
        for L, simp in runs:
            lay = self.layers[L]
            for (ax, ay), (bx, by) in zip(simp, simp[1:]):
                t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(ax), pcbnew.FromMM(ay)))
                t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(bx), pcbnew.FromMM(by))); t.SetWidth(pcbnew.FromMM(width)); t.SetLayer(lay)
                t.SetNet(ni); t.SetLocked(True); b.Add(t); segs += 1
                self.items.append(dict(net=net, kind="track", layers={L}, a=(ax, ay), b=(bx, by), hw=width / 2, obj=t, locked=True))
        for vx, vy in vias:
            v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(vx), pcbnew.FromMM(vy)))
            v.SetWidth(pcbnew.FromMM(self.rules["via_d"])); v.SetDrill(pcbnew.FromMM(self.rules["via_drill"]))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(ni); v.SetLocked(True); b.Add(v)
            self.items.append(dict(net=net, kind="via", x=vx, y=vy, r=self.rules["via_d"] / 2, drill=self.rules["via_drill"] / 2,
                                   layers=set(range(len(self.layers))), obj=v, locked=True))
        length = sum(math.hypot(b_[1] - a_[1], b_[2] - a_[2]) for a_, b_ in zip(pts, pts[1:]) if a_[0] == b_[0])
        return dict(segs=segs, vias=vias, length=length, layers=sorted({self.layers[l] for l, _x, _y in pts}))
