"""Small grid router for tiny 2-layer boards (knob step 2, 5 Nov 2026). Freerouting leaves the 12 x 6 USB-C board part-routed, so this
routes it on a fine grid with negotiated congestion (PathFinder: McMurchie & Ebeling, 1995): every net is routed, nets may first
overlap at a price, and the price of shared places rises each round until no two nets come too close.
  - grid 0.025 mm, 2 layers, 8 directions (45 degree steps), through vias
  - clearances from the board's own rules, plus a small margin for the grid; KiCad's DRC checks the result
  - no via on a pad: a via may overlap the rim of a same-net pad that has no paste (a landing pad), its hole kept 0.05 outside
Run with the system python that has pcbnew, numpy and scipy (/usr/bin/python3)."""
import heapq, math
import numpy as np
from scipy import ndimage
import pcbnew

SHAPE = {pcbnew.PAD_SHAPE_CIRCLE: "circle", pcbnew.PAD_SHAPE_RECT: "rect", pcbnew.PAD_SHAPE_OVAL: "oval",
         pcbnew.PAD_SHAPE_ROUNDRECT: "rect", pcbnew.PAD_SHAPE_TRAPEZOID: "rect"}


def board_pads(board, origin):
    """Pads in board-local mm (origin subtracted), one dict per pad."""
    out = []
    for f in board.GetFootprints():
        for p in f.Pads():
            pos, s = p.GetPosition(), p.GetSize()
            w, h = pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)
            if round(p.GetOrientationDegrees()) % 180 == 90:
                w, h = h, w
            lay = set()
            if p.IsOnLayer(pcbnew.F_Cu):
                lay.add(0)
            if p.IsOnLayer(pcbnew.B_Cu):
                lay.add(1)
            npth = p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH
            d = p.GetDrillSize()
            out.append(dict(ref=f.GetReference(), num=p.GetNumber(), net=p.GetNetname(), x=pcbnew.ToMM(pos.x) - origin[0],
                            y=pcbnew.ToMM(pos.y) - origin[1], w=w, h=h, shape=SHAPE.get(p.GetShape(), "rect"), layers=lay,
                            npth=npth, drill=(pcbnew.ToMM(d.x), pcbnew.ToMM(d.y)), smd=p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD,
                            paste=p.IsOnLayer(pcbnew.F_Paste) or p.IsOnLayer(pcbnew.B_Paste)))
    return out


def shape_dist(X, Y, x, y, w, h, shape):
    """Signed distance (mm) from grid points to a pad shape (negative inside)."""
    ax, ay = np.abs(X - x), np.abs(Y - y)
    if shape == "circle":
        return np.hypot(ax, ay) - w / 2
    if shape == "oval":
        if w >= h:
            return np.hypot(np.maximum(ax - (w - h) / 2, 0), ay) - h / 2
        return np.hypot(ax, np.maximum(ay - (h - w) / 2, 0)) - w / 2
    dx, dy = ax - w / 2, ay - h / 2
    out = np.hypot(np.maximum(dx, 0), np.maximum(dy, 0))
    return np.where((dx < 0) & (dy < 0), np.maximum(dx, dy), out)


class Router:
    def __init__(self, pads, bounds, rules, width, g=0.025, margin=0.02, via_cost=0.8, nets=None):
        self.g, self.m, self.rules, self.via_cost = g, margin, rules, via_cost
        x0, y0, x1, y1 = bounds
        self.nx, self.ny = int(round((x1 - x0) / g)), int(round((y1 - y0) / g))
        self.x0, self.y0 = x0 + g / 2, y0 + g / 2
        xs = self.x0 + g * np.arange(self.nx); ys = self.y0 + g * np.arange(self.ny)
        self.X, self.Y = np.meshgrid(xs, ys)
        X, Y = self.X, self.Y
        c, edge = rules["clearance"], rules["edge"]
        hole_c = rules.get("hole_clearance", 0.2)
        self.via_r = rules["via_d"] / 2
        self.pads = [p for p in pads]
        for p in self.pads:
            p["dist"] = shape_dist(X, Y, p["x"], p["y"], p["w"], p["h"], "circle" if p["npth"] else p["shape"])
        d_edge = np.minimum.reduce([X - x0, x1 - X, Y - y0, y1 - Y])
        self.nets = nets or sorted({p["net"] for p in pads if p["net"] and not p["net"].startswith("unconnected")})
        self.width = {n: width.get(n, width.get("default", 0.127)) for n in self.nets}
        self.block, self.via_ok, self.terms = {}, {}, {}
        vr = self.via_r
        for n in self.nets:
            w2 = self.width[n] / 2
            blk = [d_edge < edge + w2 + margin, d_edge < edge + w2 + margin]
            vok = d_edge >= edge + vr + margin
            for p in self.pads:
                if p["npth"]:
                    for L in (0, 1):
                        blk[L] |= p["dist"] < hole_c + w2 + margin
                    vok &= p["dist"] >= max(hole_c + vr, 0.25 + rules["via_drill"] / 2) + margin
                    continue
                same = p["net"] == n
                for L in p["layers"]:
                    if not same:
                        blk[L] |= p["dist"] < c + w2 + margin
                if same:
                    # a pad with no paste (a spring-contact landing pad) may carry the via's ring on its rim, but the hole stays
                    # 0.05 outside it (and so outside its mask opening); a soldered pad keeps the whole via off
                    vok &= p["dist"] >= (rules["via_drill"] / 2 + 0.05 if (p["smd"] and not p["paste"]) else vr + 0.02)
                else:
                    vok &= p["dist"] >= c + vr + margin
            self.block[n] = blk; self.via_ok[n] = vok
            ts = []
            for p in self.pads:
                if p["net"] == n and not p["npth"]:
                    cells = [(p["dist"] <= -0.04) if L in p["layers"] else np.zeros_like(X, bool) for L in (0, 1)]
                    if any(cl.any() for cl in cells):
                        ts.append((p["ref"] + "." + p["num"], cells))
            self.terms[n] = ts
        self.hist = [np.zeros_like(X), np.zeros_like(X)]
        self.hist_v = np.zeros_like(X)
        self.centre = {n: [np.zeros_like(X, bool), np.zeros_like(X, bool)] for n in self.nets}
        self.vias = {n: np.zeros_like(X, bool) for n in self.nets}
        self.paths = {n: [] for n in self.nets}

    # ---- occupancy of the other nets, seen from net n ----
    def _copper(self, m):
        g = self.g
        out = []
        vdisk = ndimage.distance_transform_edt(~self.vias[m]) * g <= self.via_r if self.vias[m].any() else np.zeros_like(self.X, bool)
        for L in (0, 1):
            cm = self.centre[m][L]
            cu = (ndimage.distance_transform_edt(~cm) * g <= self.width[m] / 2) if cm.any() else np.zeros_like(self.X, bool)
            out.append(cu | vdisk)
        return out

    def _occupancy(self, n, coppers):
        c, g = self.rules["clearance"], self.g
        occ = [np.zeros(self.X.shape), np.zeros(self.X.shape)]; occv = np.zeros(self.X.shape)
        for m in self.nets:
            if m == n:
                continue
            for L in (0, 1):
                cu = coppers[m][L]
                if not cu.any():
                    continue
                d = ndimage.distance_transform_edt(~cu) * g
                occ[L] += d < c + self.width[n] / 2 + self.m
                occv += d < c + self.via_r + self.m
        return occ, occv

    # ---- one net: grow a tree from the first terminal to the others (A*) ----
    def _route_net(self, n, occ, occv, pf):
        nx, ny, N = self.nx, self.ny, self.nx * self.ny
        g = self.g
        cost = []
        for L in (0, 1):
            cc = (1.0 + self.hist[L]) * (1.0 + pf * occ[L])
            cc[self.block[n][L]] = np.inf
            cost.append(cc.ravel().tolist())
        vc = self.via_cost * (1.0 + self.hist_v) * (1.0 + pf * occv)
        vc[~self.via_ok[n]] = np.inf
        vcost = vc.ravel().tolist()
        blocked = [self.block[n][0].ravel().tolist(), self.block[n][1].ravel().tolist()]
        terms = self.terms[n]
        if len(terms) < 2:
            return [], []
        tree = set()
        for L in (0, 1):
            for i in np.flatnonzero(terms[0][1][L]):
                tree.add(L * N + int(i))
        left = list(range(1, len(terms)))
        segs, vias = [], []
        diag = g * math.sqrt(2)
        moves = [(1, 0, g), (-1, 0, g), (0, 1, g), (0, -1, g), (1, 1, diag), (1, -1, diag), (-1, 1, diag), (-1, -1, diag)]
        while left:
            tgt = np.zeros((2, ny, nx), bool)
            for k in left:
                tgt[0] |= terms[k][1][0]; tgt[1] |= terms[k][1][1]
            tset = set((np.flatnonzero(tgt.ravel())).tolist())
            h2 = (ndimage.distance_transform_edt(~(tgt[0] | tgt[1])) * g).ravel().tolist()
            dist = {}; prev = {}; pq = []
            for s in tree:
                dist[s] = 0.0; prev[s] = -1
                heapq.heappush(pq, (h2[s % N], 0.0, s))
            found = -1
            while pq:
                f, d, u = heapq.heappop(pq)
                if d > dist.get(u, math.inf):
                    continue
                if u in tset:
                    found = u; break
                L, cidx = divmod(u, N)
                iy, ix = divmod(cidx, nx)
                cl = cost[L]; bl = blocked[L]
                for dx, dy, ln in moves:
                    jx, jy = ix + dx, iy + dy
                    if jx < 0 or jy < 0 or jx >= nx or jy >= ny:
                        continue
                    j = jy * nx + jx
                    cj = cl[j]
                    if cj == math.inf:
                        continue
                    if dx and dy and (bl[iy * nx + jx] or bl[jy * nx + ix]):
                        continue
                    v = L * N + j; nd = d + ln * cj
                    if nd < dist.get(v, math.inf):
                        dist[v] = nd; prev[v] = u
                        heapq.heappush(pq, (nd + h2[j], nd, v))
                vcst = vcost[cidx]
                if vcst != math.inf:
                    v = (1 - L) * N + cidx; nd = d + vcst
                    if cost[1 - L][cidx] != math.inf and nd < dist.get(v, math.inf):
                        dist[v] = nd; prev[v] = u
                        heapq.heappush(pq, (nd + h2[cidx], nd, v))
            if found < 0:
                return None, None
            path = []; u = found
            while u != -1:
                path.append(u); u = prev[u]
            path.reverse()
            segs.append(path)
            for a, b in zip(path, path[1:]):
                if a // N != b // N:
                    vias.append(a % N)
            tree.update(path)
            hit = [k for k in left if tgt_hit(terms[k][1], set(path), N)]
            for k in hit:
                for L in (0, 1):
                    for i in np.flatnonzero(terms[k][1][L]):
                        tree.add(L * N + int(i))
            left = [k for k in left if k not in hit]
        return segs, vias

    def _set(self, n, segs, vias):
        N = self.nx * self.ny
        c0 = np.zeros(2 * N, bool)
        for s in segs:
            c0[s] = True
        self.centre[n] = [c0[:N].reshape(self.ny, self.nx), c0[N:].reshape(self.ny, self.nx)]
        v = np.zeros(N, bool)
        if vias:
            v[vias] = True
        self.vias[n] = v.reshape(self.ny, self.nx)
        self.paths[n] = (segs, vias)

    def run(self, iters=40, order=None, pf0=0.6, pf_mult=1.6, h_inc=0.6, log=print):
        order = order or self.nets
        pf = pf0
        for it in range(iters):
            for n in order:
                self._set(n, [], [])
                coppers = {m: self._copper(m) for m in self.nets}
                occ, occv = self._occupancy(n, coppers)
                segs, vias = self._route_net(n, occ, occv, pf)
                if segs is None:
                    log(f"  net {n}: no path at all (blocked)"); return False
                self._set(n, segs, vias)
            coppers = {m: self._copper(m) for m in self.nets}
            bad = 0
            for n in self.nets:
                occ, occv = self._occupancy(n, coppers)
                for L in (0, 1):
                    clash = self.centre[n][L] & (occ[L] > 0)
                    self.hist[L][clash] += h_inc; bad += int(clash.sum())
                vclash = self.vias[n] & (occv > 0)
                self.hist_v[vclash] += h_inc; bad += int(vclash.sum())
            log(f"  round {it + 1}: {bad} crowded cells, {sum(len(v[1]) for v in self.paths.values() if v)} vias")
            if bad == 0:
                return True
            pf *= pf_mult
        return False

    # ---- pull the grid paths tight: replace stair steps by straight lines where the straight line keeps every clearance ----
    def smooth(self):
        N, nx, ny, g = self.nx * self.ny, self.nx, self.ny, self.g
        c = self.rules["clearance"]
        self.smooth_paths = {}
        for n in self.nets:
            coppers = {m: self._copper(m) for m in self.nets}
            free = []
            for L in (0, 1):
                ok = ~self.block[n][L]
                for m in self.nets:
                    if m != n and coppers[m][L].any():
                        ok &= ndimage.distance_transform_edt(~coppers[m][L]) * g >= c + self.width[n] / 2 + self.m
                free.append(ok)
            lines, _ = self._raw_polylines(n)
            out = []
            for L, pts in lines:
                out.append((L, self._pull(pts, free[L])))
            self.smooth_paths[n] = out
            cm = [np.zeros((ny, nx), bool), np.zeros((ny, nx), bool)]
            for L, pts in out:
                for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                    k = max(2, int(math.hypot(bx - ax, by - ay) / (g / 3)) + 1)
                    for t in np.linspace(0, 1, k):
                        ix = int(round((ax + t * (bx - ax) - self.x0) / g)); iy = int(round((ay + t * (by - ay) - self.y0) / g))
                        cm[L][iy, ix] = True
            self.centre[n] = cm

    def _clear(self, a, b, free):
        g = self.g
        k = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / (g / 3)) + 1)
        for t in np.linspace(0, 1, k):
            ix = int(round((a[0] + t * (b[0] - a[0]) - self.x0) / g)); iy = int(round((a[1] + t * (b[1] - a[1]) - self.y0) / g))
            if not free[iy, ix]:
                return False
        return True

    def _pull(self, pts, free):
        if len(pts) <= 2:
            return pts
        out = [pts[0]]; i = 0
        while i < len(pts) - 1:
            j = len(pts) - 1
            while j > i + 1 and not self._clear(pts[i], pts[j], free):
                j -= 1
            out.append(pts[j]); i = j
        return out

    # ---- output ----
    def polylines(self, n):
        """[(layer, [(x, y), ...])], [(x, y) vias] in board-local mm (pulled tight if smooth() ran)."""
        lines, vias = self._raw_polylines(n)
        if getattr(self, "smooth_paths", None):
            lines = self.smooth_paths[n]
        return lines, vias

    def _raw_polylines(self, n):
        N, nx, g = self.nx * self.ny, self.nx, self.g
        segs, vias = self.paths[n]
        out = []

        def xy(c):
            iy, ix = divmod(c % N, nx)
            return (round(self.x0 + ix * g, 4), round(self.y0 + iy * g, 4))
        # a later branch of the tree starts on a cell of an earlier path: keep those cells as run ends, so pulling a run tight
        # never moves a junction away from the branch that starts there
        anchors = set()
        for path in segs:
            anchors.add(path[0] % N); anchors.add(path[-1] % N)
        for path in segs:
            run = [path[0]]
            for u in path[1:]:
                if u // N != run[-1] // N:
                    if len(run) > 1:
                        out.append((run[0] // N, _simplify([xy(c) for c in run])))
                    run = [u]
                else:
                    run.append(u)
                    if u % N in anchors:
                        out.append((run[0] // N, _simplify([xy(c) for c in run])))
                        run = [u]
            if len(run) > 1:
                out.append((run[0] // N, _simplify([xy(c) for c in run])))
        return out, [xy(v) for v in vias]


def tgt_hit(cells, pathset, N):
    for L in (0, 1):
        idx = np.flatnonzero(cells[L])
        if idx.size and any((L * N + int(i)) in pathset for i in idx):
            return True
    return False


def _simplify(pts):
    out = [pts[0]]
    for p in pts[1:]:
        if len(out) >= 2:
            (ax, ay), (bx, by) = out[-2], out[-1]
            if abs((bx - ax) * (p[1] - by) - (by - ay) * (p[0] - bx)) < 1e-9:
                out[-1] = p; continue
        out.append(p)
    return out


def apply(board, router, origin, via_d, via_drill):
    """Add the routed tracks and vias to a pcbnew board."""
    V = lambda x, y: pcbnew.VECTOR2I(pcbnew.FromMM(origin[0] + x), pcbnew.FromMM(origin[1] + y))
    lay = {0: pcbnew.F_Cu, 1: pcbnew.B_Cu}
    for n in router.nets:
        ni = board.FindNet(n)
        lines, vias = router.polylines(n)
        for L, pts in lines:
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(board); t.SetStart(V(ax, ay)); t.SetEnd(V(bx, by))
                t.SetWidth(pcbnew.FromMM(router.width[n])); t.SetLayer(lay[L]); t.SetNet(ni); board.Add(t)
        for x, y in vias:
            v = pcbnew.PCB_VIA(board); v.SetPosition(V(x, y)); v.SetWidth(pcbnew.FromMM(via_d)); v.SetDrill(pcbnew.FromMM(via_drill))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(ni); board.Add(v)
