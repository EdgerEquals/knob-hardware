"""Multi-layer grid router for the step-2 jack boards (knob step 2, 6 Nov 2026; Ed Q26 = A). Freerouting leaves the dense 4-layer jack
power boards part-routed, so this routes them on a grid with negotiated congestion (PathFinder: McMurchie & Ebeling, 1995), as
grid_router.py does for the 2-layer USB-C board, but built to scale:
  - routing layers F.Cu, In2.Cu, B.Cu (In1.Cu stays a solid ground plane); 8 directions; through vias (0.45 / 0.2)
  - the search runs in C (router4_core.c, compiled on first use with gcc)
  - congestion is kept as counts of nets whose clearance zone covers each cell, one count array per track-width class, so ripping
    up or adding a net is a few array stamps instead of distance transforms
  - static obstacles (other nets' pads, holes, the board edge) from exact pad shapes, per width class
  - ground: every ground pad gets a short track to a via into the In1 plane (or to ground copper already there); an exposed ground
    pad gets one via in its middle; through-hole ground pads are on the plane already
  - then each net is pulled tight (straight lines wherever every clearance still holds)
Clearances: the board's rules plus a margin of at least half a grid diagonal, so the straight lines between cell centres keep them
too; KiCad's DRC checks the result. Run with the system python that has pcbnew and numpy (/usr/bin/python3)."""
import ctypes, math, os, subprocess, time
import numpy as np
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
SHAPE = {pcbnew.PAD_SHAPE_CIRCLE: "circle", pcbnew.PAD_SHAPE_RECT: "rect", pcbnew.PAD_SHAPE_OVAL: "oval",
         pcbnew.PAD_SHAPE_ROUNDRECT: "rect", pcbnew.PAD_SHAPE_TRAPEZOID: "rect"}
LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
INF = np.float32(np.inf)


def _lib():
    src = os.path.join(HERE, "router4_core.c"); bdir = os.path.join(HERE, ".build"); so = os.path.join(bdir, "router4_core.so")
    if not os.path.exists(so) or os.path.getmtime(so) < os.path.getmtime(src):
        os.makedirs(bdir, exist_ok=True)
        subprocess.run(["gcc", "-O2", "-shared", "-fPIC", "-o", so, src, "-lm"], check=True)
    lib = ctypes.CDLL(so)
    P = ctypes.POINTER
    lib.route_search.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, P(ctypes.c_float), P(ctypes.c_float), P(ctypes.c_uint8),
                                 P(ctypes.c_int), ctypes.c_int, P(ctypes.c_uint8), P(ctypes.c_float), P(ctypes.c_int), ctypes.c_int,
                                 ctypes.c_float, P(ctypes.c_int), ctypes.c_int, P(ctypes.c_int), ctypes.c_long]
    lib.route_search.restype = ctypes.c_int
    return lib


def _ptr(a, t):
    return a.ctypes.data_as(ctypes.POINTER(t)) if a is not None else None


def shape_dist(X, Y, x, y, w, h, shape):
    """Signed distance (mm) from points to a pad shape (negative inside)."""
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


def board_pads(board, origin):
    out = []
    for f in board.GetFootprints():
        for p in f.Pads():
            pos, s = p.GetPosition(), p.GetSize()
            w, h = pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)
            if round(p.GetOrientationDegrees()) % 180 == 90:
                w, h = h, w
            npth = p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH
            tht = p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
            if not (npth or tht or p.IsOnLayer(pcbnew.F_Cu) or p.IsOnLayer(pcbnew.B_Cu)):
                continue   # paste-only apertures (the exposed pads' paste segments): no copper
            lay = {0, 1, 2} if (tht or npth) else ({0} if p.IsOnLayer(pcbnew.F_Cu) else {2})
            d = p.GetDrillSize()
            out.append(dict(ref=f.GetReference(), num=p.GetNumber(), net=p.GetNetname(), x=pcbnew.ToMM(pos.x) - origin[0],
                            y=pcbnew.ToMM(pos.y) - origin[1], w=w, h=h, shape=SHAPE.get(p.GetShape(), "rect"), layers=lay,
                            npth=npth, tht=tht, drill=pcbnew.ToMM(d.x)))
    return out


class Router4:
    def __init__(self, pads, outline, rules, widths, g=0.05, margin=0.036, via_cost=1.2, gnd="GND", ep_min=1.4, log=print):
        self.lib = _lib(); self.log = log
        self.g, self.rules, self.via_cost, self.gnd = g, rules, via_cost, gnd
        self.c = rules["clearance"]; self.vr = rules["via_d"] / 2; self.mt = margin
        xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        # cell centres on multiples of g: part centres are snapped to 0.05 and most pad offsets are multiples of 0.05 too, so pins
        # at 0.5 pitch get a row of cells on their centre line (half a cell off, both of a narrow pad's middle cells can be blocked)
        self.x0, self.y0 = math.floor(x0 / g) * g, math.floor(y0 / g) * g
        self.nx, self.ny = int(math.ceil((x1 - self.x0) / g)) + 1, int(math.ceil((y1 - self.y0) / g)) + 1
        self.N = self.nx * self.ny; self.nl = 3
        X, Y = np.meshgrid(self.x0 + g * np.arange(self.nx), self.y0 + g * np.arange(self.ny))
        from matplotlib.path import Path
        inside = Path(outline).contains_points(np.c_[X.ravel(), Y.ravel()]).reshape(X.shape)
        dd = np.full(X.shape, np.inf)
        for (ax_, ay_), (bx_, by_) in zip(outline, outline[1:] + outline[:1]):
            vx, vy = bx_ - ax_, by_ - ay_; L2 = vx * vx + vy * vy or 1e-12
            t = np.clip(((X - ax_) * vx + (Y - ay_) * vy) / L2, 0, 1)
            dd = np.minimum(dd, np.hypot(X - ax_ - t * vx, Y - ay_ - t * vy))
        d_edge = np.where(inside, dd, -dd)
        names = sorted({p["net"] for p in pads if p["net"] and not p["net"].startswith("unconnected")})
        self.nets = names; self.nid = {n: i for i, n in enumerate(names)}
        self.width = {n: widths.get(n, widths["default"]) for n in names}
        self.classes = sorted(set(self.width.values()))
        self.kof = {n: self.classes.index(self.width[n]) for n in names}
        ms, c, vr, hole_c = margin, self.c, self.vr, rules.get("hole_clearance", 0.2)
        Rmax = max(self.classes) / 2 + c + ms + vr + 0.3
        nk = len(self.classes)
        self.owner = np.full((nk, 3, self.ny, self.nx), -1, np.int32)
        self.owner_v = np.full((self.ny, self.nx), -1, np.int32)
        self.near_pad_v = np.zeros((self.ny, self.nx), bool)
        self.hole_blk = np.zeros((nk, self.ny, self.nx), bool); self.hole_v = np.zeros((self.ny, self.nx), bool)
        self.edge_blk = np.stack([d_edge < rules["edge"] + w / 2 + ms for w in self.classes])
        self.edge_v = d_edge < rules["edge"] + vr + ms
        self.terms = {n: [] for n in names}
        self.pads = pads; self.pad_cells = []
        for i, p in enumerate(pads):
            r = max(p["w"], p["h"]) / 2 + Rmax
            ix0 = max(0, int((p["x"] - r - self.x0) / g)); ix1 = min(self.nx, int((p["x"] + r - self.x0) / g) + 2)
            iy0 = max(0, int((p["y"] - r - self.y0) / g)); iy1 = min(self.ny, int((p["y"] + r - self.y0) / g) + 2)
            sl = (slice(iy0, iy1), slice(ix0, ix1))
            if p["npth"]:
                d = shape_dist(X[sl], Y[sl], p["x"], p["y"], p["drill"], p["drill"], "circle")
                for k, w in enumerate(self.classes):
                    self.hole_blk[k][sl] |= d < hole_c + w / 2 + ms
                self.hole_v[sl] |= d < max(hole_c + vr, 0.25 + rules["via_drill"] / 2) + ms
                self.pad_cells.append(None)
                continue
            d = shape_dist(X[sl], Y[sl], p["x"], p["y"], p["w"], p["h"], p["shape"])
            q = self.nid.get(p["net"], 100000 + i)
            for k, w in enumerate(self.classes):
                m = d < c + w / 2 + ms
                for L in p["layers"]:
                    o = self.owner[k, L][sl]
                    o[m] = np.where((o[m] == -1) | (o[m] == q), q, -2)
            m = d < c + vr + ms
            o = self.owner_v[sl]; o[m] = np.where((o[m] == -1) | (o[m] == q), q, -2)
            self.near_pad_v[sl] |= d < vr + 0.02
            inset = min(0.03, 0.3 * min(p["w"], p["h"]))
            cells = np.flatnonzero(_embed(d <= -inset, sl, self.ny, self.nx))
            if cells.size == 0:
                cells = np.array([int(round((p["y"] - self.y0) / g)) * self.nx + int(round((p["x"] - self.x0) / g))])
            self.pad_cells.append(cells)
            if p["net"] in self.terms:
                nodes = np.concatenate([L * self.N + cells for L in sorted(p["layers"])])
                self.terms[p["net"]].append((i, nodes))
        self.X, self.Y = X, Y
        self.occ = np.zeros((nk, 3, self.N), np.int16); self.occv = np.zeros(self.N, np.int16)
        self.hist = np.zeros((3, self.N), np.float32); self.hist_v = np.zeros(self.N, np.float32)
        self.state = {n: dict(segs=[], vias=[], stamps=None) for n in names}
        self.fixed_vias = {n: [] for n in names}
        self.done_pads = set(); self.failed = {}
        self._discs = {}
        # ground: a via in the middle of every exposed ground pad; through-hole ground pads are on the plane
        if gnd in self.nid:
            for i, nodes in self.terms[gnd]:
                p = pads[i]
                if p["tht"]:
                    self.done_pads.add(i)
                elif min(p["w"], p["h"]) >= ep_min:
                    # the via goes through every layer: a part on the other face may have a pad right over it, so pick the cell
                    # nearest the pad's middle that is clear of every other net's pads on all layers (else route it as a pad)
                    q = self.nid[gnd]
                    ok = (((self.owner_v == -1) | (self.owner_v == q)) & ~self.edge_v & ~self.hole_v).ravel()
                    cand = self.pad_cells[i][ok[self.pad_cells[i]]]
                    if cand.size:
                        cy, cx = np.divmod(cand, self.nx)
                        dd2 = (self.x0 + cx * g - p["x"]) ** 2 + (self.y0 + cy * g - p["y"]) ** 2
                        self.fixed_vias[gnd].append(int(cand[np.argmin(dd2)])); self.done_pads.add(i)
            self._stamp(gnd, +1)

    def islands(self):
        """Terminals that no path can join because the other nets' pads, the holes and the edge wall them off (any layer, through
        any legal via): {net: [[pad labels], ...]} for every net split into more than one group."""
        from scipy import ndimage
        out = {}
        for n in self.nets:
            if n == self.gnd:
                continue
            blk = self.blocked(n).reshape(3, self.ny, self.nx); vok = self.via_ok(n)
            lab = [ndimage.label(~blk[L], structure=np.ones((3, 3)))[0].ravel() for L in range(3)]
            parent = {}

            def f(a):
                while parent.setdefault(a, a) != a:
                    a = parent[a]
                return a
            for c in np.flatnonzero(vok):
                ls = [(L, int(lab[L][c])) for L in range(3) if lab[L][c] > 0]
                for a_ in ls[1:]:
                    parent[f(a_)] = f(ls[0])
            groups = []
            for i, nodes in self.terms[n]:
                s = {f((int(u) // self.N, int(lab[int(u) // self.N][int(u) % self.N]))) for u in nodes if lab[int(u) // self.N][int(u) % self.N] > 0}
                nm = self.pads[i]["ref"] + "." + self.pads[i]["num"]
                for g_ in groups:
                    if g_[1] & s:
                        g_[0].append(nm); g_[1] |= s; break
                else:
                    groups.append([[nm], set(s)])
            if len(groups) > 1:
                out[n] = sorted([g_[0] for g_ in groups], key=len, reverse=True)
        return out

    # ---- per-net static maps ----
    def blocked(self, n):
        k, q = self.kof[n], self.nid[n]
        o = self.owner[k]
        return ((o != -1) & (o != q)).reshape(3, self.N) | (self.hole_blk[k] | self.edge_blk[k]).reshape(1, self.N)

    def via_ok(self, n):
        q = self.nid[n]
        return (~self.edge_v & ~self.hole_v & ~self.near_pad_v & ((self.owner_v == -1) | (self.owner_v == q))).ravel()

    # ---- congestion stamps ----
    def _disc(self, r):
        key = round(r, 4)
        if key not in self._discs:
            k = int(math.ceil(r / self.g))
            dy, dx = np.mgrid[-k:k + 1, -k:k + 1]
            m = (dx * dx + dy * dy) * self.g * self.g < r * r
            self._discs[key] = (dy[m].ravel(), dx[m].ravel())
        return self._discs[key]

    def _dilate(self, cells, r):
        if len(cells) == 0:
            return np.zeros(0, np.int64)
        cells = np.asarray(cells, np.int64)
        iy, ix = np.divmod(cells, self.nx)
        dy, dx = self._disc(r)
        yy = iy[:, None] + dy[None, :]; xx = ix[:, None] + dx[None, :]
        ok = (yy >= 0) & (yy < self.ny) & (xx >= 0) & (xx < self.nx)
        return (yy * self.nx + xx)[ok]

    def _copper(self, n):
        st = self.state[n]
        per = [[] for _ in range(3)]
        for path in st["segs"]:
            path = np.asarray(path)
            for L in range(3):
                per[L].append(path[path // self.N == L] % self.N)
        per = [np.unique(np.concatenate(a)) if a else np.zeros(0, np.int64) for a in per]
        vias = np.unique(np.asarray(st["vias"] + self.fixed_vias[n], np.int64))
        return per, vias

    def _stamp(self, n, s):
        st = self.state[n]
        if s < 0:
            if st["stamps"] is None:
                return
            for k in range(len(self.classes)):
                for L in range(3):
                    self.occ[k, L, st["stamps"][0][k][L]] -= 1
            self.occv[st["stamps"][1]] -= 1
            st["stamps"] = None
            return
        per, vias = self._copper(n)
        w, c, vr, mt = self.width[n], self.c, self.vr, self.mt
        ks = []
        for k, wk in enumerate(self.classes):
            vd = self._dilate(vias, vr + wk / 2 + c + mt)
            row = []
            for L in range(3):
                idx = np.unique(np.concatenate([self._dilate(per[L], w / 2 + wk / 2 + c + mt), vd]))
                self.occ[k, L, idx] += 1; row.append(idx)
            ks.append(row)
        vidx = np.unique(np.concatenate([self._dilate(per[L], w / 2 + vr + c + mt) for L in range(3)] +
                                        [self._dilate(vias, 2 * vr + c + mt)]))
        self.occv[vidx] += 1
        st["stamps"] = (ks, vidx)

    # ---- one search ----
    def _search(self, cost, vcost, blk, src, tgt=None, sinkc=None, tboxes=None, maxexp=40_000_000):
        out = np.zeros(200000, np.int32); rs = ctypes.c_int(0)
        src = np.ascontiguousarray(src, np.int32)
        tb = np.ascontiguousarray(tboxes, np.int32) if tboxes is not None else None
        n = self.lib.route_search(self.nx, self.ny, 3, _ptr(cost, ctypes.c_float), _ptr(vcost, ctypes.c_float), _ptr(blk, ctypes.c_uint8),
                                  _ptr(src, ctypes.c_int), len(src), _ptr(tgt, ctypes.c_uint8), _ptr(sinkc, ctypes.c_float),
                                  _ptr(tb, ctypes.c_int), 0 if tb is None else len(tb), self.g, _ptr(out, ctypes.c_int), len(out),
                                  ctypes.byref(rs), maxexp)
        return out[:n].tolist(), bool(rs.value)

    def _costs(self, n, pf):
        k = self.kof[n]
        blk = self.blocked(n)
        cost = ((1.0 + self.hist) * (1.0 + pf * self.occ[k])).astype(np.float32)
        cost[blk] = INF
        vc = (self.via_cost * (1.0 + self.hist_v) * (1.0 + pf * self.occv)).astype(np.float32)
        vc[~self.via_ok(n)] = INF
        return cost.ravel(), vc, blk.astype(np.uint8).ravel()

    def _box(self, nodes):
        c = nodes % self.N; iy, ix = np.divmod(c, self.nx)
        return [int(ix.min()), int(iy.min()), int(ix.max()), int(iy.max())]

    def _vias_of(self, path):
        return [path[i] % self.N for i in range(len(path) - 1) if path[i] // self.N != path[i + 1] // self.N]

    def route_net(self, n, pf):
        st = self.state[n]; st["segs"], st["vias"] = [], []
        if n == self.gnd:
            return self.route_gnd(pf)
        terms = self.terms[n]
        if len(terms) < 2:
            return 0
        cost, vc, blk = self._costs(n, pf)
        tree = set(terms[0][1].tolist()); left = list(range(1, len(terms))); fail = 0
        owner = {}
        while left:
            tgt = np.zeros(3 * self.N, np.uint8)
            for t in left:
                tgt[terms[t][1]] = 1
                for u in terms[t][1].tolist():
                    owner[u] = t
            path, _ = self._search(cost, vc, blk, list(tree), tgt=tgt, tboxes=[self._box(terms[t][1]) for t in left])
            if not path:
                fail += len(left); break
            t = owner[path[-1]]
            nv_ = self._vias_of(path)
            st["segs"].append(path); st["vias"] += nv_
            self._space_own_vias(vc, nv_)
            tree.update(path); tree.update(terms[t][1].tolist()); left.remove(t)
        self.failed[n] = fail
        return fail

    def route_gnd(self, pf):
        n = self.gnd; st = self.state[n]
        cost, vc, blk = self._costs(n, pf)
        sinkc = np.full(3 * self.N, INF, np.float32)
        for L in range(3):
            sinkc[L * self.N:(L + 1) * self.N] = vc
        cu = np.zeros(3 * self.N, bool)
        for v in self.fixed_vias[n]:
            cu[[v, self.N + v, 2 * self.N + v]] = True
        for i, nodes in self.terms[n]:
            if i in self.done_pads:
                cu[nodes] = True
        sinkc[cu] = 0.0
        fail = 0
        for i, nodes in self.terms[n]:
            if i in self.done_pads:
                continue
            if cu[nodes].any():
                continue
            path, sink = self._search(cost, vc, blk, nodes.tolist(), sinkc=sinkc, maxexp=3_000_000)
            if not path:
                fail += 1; continue
            last = path[-1]
            st["segs"].append(path); new_v = self._vias_of(path)
            if sink and not cu[last]:
                new_v.append(last % self.N)
            st["vias"] += new_v
            self._space_own_vias(vc, new_v, sinkc)
            cu[path] = True; sinkc[path] = 0.0
            for v in new_v:
                cu[[v, self.N + v, 2 * self.N + v]] = True; sinkc[[v, self.N + v, 2 * self.N + v]] = 0.0
            cu[nodes] = True; sinkc[nodes] = 0.0
        self.failed[n] = fail
        return fail

    def _space_own_vias(self, vc, vias, sinkc=None):
        """No new via of the same net within hole-to-hole reach of one just placed (the via itself stays usable)."""
        if not vias:
            return
        r = self.rules["via_drill"] + 0.25 + self.mt
        near = self._dilate(vias, r)
        keep = vc[vias].copy()
        vc[near] = INF; vc[vias] = keep
        if sinkc is not None:
            for L in range(3):
                s = sinkc[L * self.N:(L + 1) * self.N]
                kk = s[vias].copy(); s[near] = np.where(s[near] == 0.0, 0.0, INF); s[vias] = kk

    # ---- negotiated congestion ----
    def hot_cells(self):
        """Board-local (x, y) of every crowded cell of the current routes (for pictures and placement feedback)."""
        out = []
        for n in self.nets:
            per, vias = self._copper(n); k = self.kof[n]
            for L in range(3):
                if len(per[L]):
                    out += [(n, L) + self._xy(c) for c in per[L][self.occ[k, L, per[L]] > 1]]
            if len(vias):
                out += [(n, -1) + self._xy(c) for c in vias[self.occv[vias] > 1]]
        return out

    def overuse(self):
        bad = {}
        for n in self.nets:
            per, vias = self._copper(n)
            k = self.kof[n]; cnt = 0
            for L in range(3):
                if len(per[L]):
                    cl = self.occ[k, L, per[L]] > 1
                    cnt += int(cl.sum()); self.hist[L, per[L][cl]] += self.h_inc
            if len(vias):
                cl = self.occv[vias] > 1
                cnt += int(cl.sum()); self.hist_v[vias[cl]] += self.h_inc
            if cnt:
                bad[n] = cnt
        return bad

    def run(self, iters=80, pf0=0.5, pf_mult=1.35, h_inc=0.4, order=None, time_limit=None, pf_max=30.0, shuffle=True, seed=7):
        self.h_inc = h_inc
        order = order or sorted(self.nets, key=lambda n: (n == self.gnd, -self.width[n], -len(self.terms[n])))
        pf = pf0; t0 = time.time(); best = None
        import random
        rng = random.Random(seed); self.seed = seed
        for it in range(iters):
            if shuffle and it >= 3:   # after a few rounds: the crowded nets first, the rest in a new random order each round
                bad_now = getattr(self, "_bad", {})
                rest = [n for n in order if n not in bad_now]; rng.shuffle(rest)
                order = sorted(bad_now, key=lambda n: -bad_now[n]) + rest
            for n in order:
                self._stamp(n, -1)
                self.route_net(n, pf)
                self._stamp(n, +1)
            bad = self.overuse(); self._bad = bad
            nf = sum(self.failed.values())
            nv = sum(len(self.state[n]["vias"]) for n in self.nets)
            self.log(f"  round {it + 1}: {sum(bad.values())} crowded cells on {len(bad)} nets, {nf} unroutable, {nv} vias, "
                     f"{time.time() - t0:.0f} s" + (f"  worst: {sorted(bad.items(), key=lambda kv: -kv[1])[:4]}" if bad else ""))
            score = (nf, sum(bad.values()))
            if best is None or score < best[0]:
                best = (score, {n: dict(segs=[list(s) for s in self.state[n]["segs"]], vias=list(self.state[n]["vias"])) for n in self.nets})
            if not bad and nf == 0:
                return True
            if time_limit and time.time() - t0 > time_limit:
                break
            pf = min(pf * pf_mult, pf_max)
        self.log(f"  best round: {best[0][0]} unroutable, {best[0][1]} crowded cells")
        for n in self.nets:
            self._stamp(n, -1); self.state[n]["segs"] = best[1][n]["segs"]; self.state[n]["vias"] = best[1][n]["vias"]; self._stamp(n, +1)
        return self.cleanup()

    def cleanup(self, rounds=24, pf=1e4, reach=0.8):
        """Last pass from the best round: reroute only the nets still crowded, each with the others' space all but forbidden (a net
        that can get round them takes that way), keeping whatever is best."""
        import random
        rng = random.Random(getattr(self, "seed", 7) + 11)
        bad = self.overuse()
        score = lambda b: (sum(self.failed.values()), sum(b.values()))
        best = (score(bad), {n: (list(map(list, self.state[n]["segs"])), list(self.state[n]["vias"])) for n in self.nets})
        for rd in range(rounds):
            if not bad and sum(self.failed.values()) == 0:
                break
            # the crowded nets and, every other round, the nets with copper near the crowded spots (so they can make room)
            nets = set(bad)
            if rd % 2:
                hot = self.hot_cells()
                for n in self.nets:
                    per, vias = self._copper(n)
                    pts = [self._xy(c) for L in range(3) for c in per[L][::4]] + [self._xy(c) for c in vias]
                    if any(abs(px - hx) < reach and abs(py - hy) < reach for _n, _L, hx, hy in hot for px, py in pts):
                        nets.add(n)
            nets = list(nets); rng.shuffle(nets)
            for n in nets:
                self._stamp(n, -1); self.route_net(n, pf); self._stamp(n, +1)
            self.hist *= 0.0; self.hist_v *= 0.0   # no history needed here: overuse() below only counts
            bad = self.overuse()
            s = score(bad)
            self.log(f"  cleanup {rd + 1}: {s[1]} crowded cells on {len(bad)} nets, {s[0]} unroutable")
            if s < best[0]:
                best = (s, {n: (list(map(list, self.state[n]["segs"])), list(self.state[n]["vias"])) for n in self.nets})
        for n in self.nets:
            self._stamp(n, -1); self.state[n]["segs"], self.state[n]["vias"] = best[1][n]; self._stamp(n, +1)
        self._bad = self.overuse()
        return best[0] == (0, 0)

    # ---- pull tight ----
    def _xy(self, c):
        iy, ix = divmod(c % self.N, self.nx)
        return (self.x0 + ix * self.g, self.y0 + iy * self.g)

    def _runs(self, n):
        """Each path split into same-layer runs; a cell where another path of the net starts or ends stays a run end."""
        segs = self.state[n]["segs"]; N = self.N
        anchors = set()
        for p in segs:
            anchors.add(p[0] % N); anchors.add(p[-1] % N)
        for v in self.state[n]["vias"] + self.fixed_vias[n]:
            anchors.add(v)
        out = []
        for p in segs:
            run = [p[0]]
            for u in p[1:]:
                if u // N != run[-1] // N:
                    if len(run) > 1:
                        out.append((run[0] // N, [r % N for r in run]))
                    run = [u]
                else:
                    run.append(u)
                    if u % N in anchors:
                        out.append((run[0] // N, [r % N for r in run])); run = [u]
            if len(run) > 1:
                out.append((run[0] // N, [r % N for r in run]))
        return out

    def smooth(self):
        self.lines = {}
        for n in self.nets:
            self._stamp(n, -1)
            k = self.kof[n]; blk = self.blocked(n)
            free = [(~blk[L]) & (self.occ[k, L] == 0) for L in range(3)]
            out, cells = [], [[] for _ in range(3)]
            for L, run in self._runs(n):
                pts = [self._xy(c) for c in run]
                pulled = self._pull(pts, free[L])
                out.append((L, pulled))
                cells[L] += self._raster(pulled)
            self.lines[n] = out
            segs = [[L * self.N + c for c in cs] for L, cs in enumerate(cells) if cs]
            keep = self.state[n]["segs"]; self.state[n]["segs"] = segs
            self._stamp(n, +1)
            self.state[n]["segs_grid"] = keep

    def _raster(self, pts):
        out = []
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            k = max(2, int(math.hypot(bx - ax, by - ay) / (self.g / 3)) + 1)
            for t in np.linspace(0, 1, k):
                ix = int(round((ax + t * (bx - ax) - self.x0) / self.g)); iy = int(round((ay + t * (by - ay) - self.y0) / self.g))
                out.append(iy * self.nx + ix)
        return out

    def _clear(self, a, b, free):
        for c in self._raster([a, b]):
            if not free.flat[c]:
                return False
        return True

    def _pull(self, pts, free):
        pts = _simplify(pts)
        if len(pts) <= 2:
            return pts
        out = [pts[0]]; i = 0
        while i < len(pts) - 1:
            j = len(pts) - 1
            while j > i + 1 and not self._clear(pts[i], pts[j], free):
                j -= 1
            out.append(pts[j]); i = j
        return out

    def apply(self, board, origin, via_d, via_drill):
        V = lambda x, y: pcbnew.VECTOR2I(pcbnew.FromMM(origin[0] + x), pcbnew.FromMM(origin[1] + y))
        nt = nv = 0
        for n in self.nets:
            ni = board.FindNet(n)
            lines = self.lines.get(n) if getattr(self, "lines", None) else [(L, _simplify([self._xy(c) for c in run])) for L, run in self._runs(n)]
            for L, pts in lines:
                for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                    t = pcbnew.PCB_TRACK(board); t.SetStart(V(ax, ay)); t.SetEnd(V(bx, by))
                    t.SetWidth(pcbnew.FromMM(self.width[n])); t.SetLayer(LAYERS[L]); t.SetNet(ni); board.Add(t); nt += 1
            for c in sorted(set(self.state[n]["vias"] + self.fixed_vias[n])):
                x, y = self._xy(c)
                v = pcbnew.PCB_VIA(board); v.SetPosition(V(x, y)); v.SetWidth(pcbnew.FromMM(via_d)); v.SetDrill(pcbnew.FromMM(via_drill))
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(ni); board.Add(v); nv += 1
        return nt, nv


def _embed(mask, sl, ny, nx):
    out = np.zeros((ny, nx), bool); out[sl] = mask; return out


def _simplify(pts):
    out = [pts[0]]
    for p in pts[1:]:
        if len(out) >= 2:
            (ax, ay), (bx, by) = out[-2], out[-1]
            if abs((bx - ax) * (p[1] - by) - (by - ay) * (p[0] - bx)) < 1e-9:
                out[-1] = p; continue
        if p != out[-1]:
            out.append(p)
    return out
