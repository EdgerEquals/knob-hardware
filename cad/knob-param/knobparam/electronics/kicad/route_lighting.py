"""Route knob-main-pcb. GND pour on In1.Cu. Signals on F.Cu, In2.Cu and B.Cu
(0.2 mm, clearance 0.15, via 0.6 / 0.3). +3V3 is routed, not poured, so In2 stays a free layer.

Freerouting's neighbour search does not finish this board. Run after make_board.py:

    python3 route_lighting.py [path/to/knob-main-pcb.kicad_pcb]
"""
import heapq, math, os, sys, time
from collections import defaultdict
import numpy as np
import pcbnew

G = 0.20
TRACK_W = 0.20
CLEAR = 0.15
VIA_D, VIA_DRILL = 0.60, 0.30
VIA_R = VIA_D / 2
# A little over the KiCad rule so a grid step cannot land 0.001 mm inside the clearance.
MARGIN = 0.0
TRACK_PAD = TRACK_W / 2 + CLEAR + MARGIN
TRACK_TRACK = TRACK_W / 2 + CLEAR + TRACK_W / 2 + MARGIN
VIA_PAD = VIA_R + CLEAR + MARGIN
VIA_TRACK = VIA_R + CLEAR + TRACK_W / 2 + MARGIN
VIA_VIA = VIA_D + CLEAR + MARGIN
HOLE_CLEAR = 0.25
EDGE = 0.30
VIA_COST = 2
PLANE = {"GND", "+3V3"}   # GND on In1, +3V3 on In2. Signals stay on F and B.
# outline centreline (panel + KiCad origin 100, 100). Corner radius 1.0.
OX0, OY0, OX1, OY1, ORAD = 100.75, 110.50, 149.75, 218.00, 1.0

X0, Y0 = OX0, OY0
W = int(round((OX1 - OX0) / G)) + 1
H = int(round((OY1 - OY0) / G)) + 1
F_CU, B_CU = pcbnew.F_Cu, pcbnew.B_Cu
LAYERS = (F_CU, B_CU, pcbnew.In2_Cu)
NL = 3


def in_rr(x, y, inset):
    r = ORAD - inset
    x0, y0, x1, y1 = OX0 + inset, OY0 + inset, OX1 - inset, OY1 - inset
    if r <= 0.02:
        return x0 <= x <= x1 and y0 <= y <= y1
    ix = min(max(x, x0 + r), x1 - r)
    iy = min(max(y, y0 + r), y1 - r)
    return (x - ix) ** 2 + (y - iy) ** 2 <= r * r + 1e-9


def cell_mm(ix, iy):
    return X0 + ix * G, Y0 + iy * G


def mm_cell(x, y):
    return int(round((x - X0) / G)), int(round((y - Y0) / G))


class Pad:
    __slots__ = ("net", "layer", "cx", "cy", "w", "h", "ang", "pth", "ref", "num")
    def __init__(self, net, layer, cx, cy, w, h, ang, pth, ref, num):
        self.net, self.layer = net, layer
        self.cx, self.cy, self.w, self.h, self.ang = cx, cy, w, h, ang
        self.pth, self.ref, self.num = pth, ref, num


class Hole:
    __slots__ = ("cx", "cy", "w", "h", "ang")
    def __init__(self, cx, cy, w, h, ang):
        self.cx, self.cy, self.w, self.h, self.ang = cx, cy, w, h, ang


def dist_rect(px, py, cx, cy, w, h, ang):
    th = math.radians(-ang)
    dx, dy = px - cx, py - cy
    lx = dx * math.cos(th) - dy * math.sin(th)
    ly = dx * math.sin(th) + dy * math.cos(th)
    hx, hy = w / 2.0, h / 2.0
    ox, oy = abs(lx) - hx, abs(ly) - hy
    if ox <= 0 and oy <= 0:
        return 0.0
    return math.hypot(max(ox, 0.0), max(oy, 0.0))


def closest_rect(px, py, cx, cy, w, h, ang):
    th = math.radians(-ang)
    c, s = math.cos(th), math.sin(th)
    dx, dy = px - cx, py - cy
    lx = dx * c - dy * s
    ly = dx * s + dy * c
    qx = min(max(lx, -w / 2), w / 2)
    qy = min(max(ly, -h / 2), h / 2)
    # inverse of (lx, ly) = R(-ang) * (dx, dy) is R(ang)
    return cx + qx * c + qy * s, cy + -qx * s + qy * c


def collect(board):
    pads, holes = [], []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for p in fp.Pads():
            pos = p.GetPosition()
            cx, cy = pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)
            sz, dr = p.GetSize(), p.GetDrillSize()
            w, h = pcbnew.ToMM(sz.x), pcbnew.ToMM(sz.y)
            # KiCad's pad angle is clockwise in this Y-down frame; the geometry helper is counter-clockwise.
            ang = -p.GetOrientation().AsDegrees()
            attr = p.GetAttribute()
            # custom copper (the rod pad) is much larger than the nominal size
            if p.GetShape() == pcbnew.PAD_SHAPE_CUSTOM:
                bb = p.GetBoundingBox()
                w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
                cx, cy = pcbnew.ToMM(bb.GetCenter().x), pcbnew.ToMM(bb.GetCenter().y)
                ang = 0.0
            if attr == pcbnew.PAD_ATTRIB_NPTH:
                dw, dh = pcbnew.ToMM(dr.x), pcbnew.ToMM(dr.y)
                if dw > 0 and dh > 0:
                    holes.append(Hole(cx, cy, dw, dh, ang))
                continue
            name = p.GetNetname()
            if not name or name.startswith("unconnected"):
                # spare MCU pins are still copper; a track through one is a short
                name = f"NC-{ref}.{p.GetNumber()}"
            pth = attr == pcbnew.PAD_ATTRIB_PTH
            if pth:
                layer = None  # both
            elif p.IsOnLayer(F_CU) and not p.IsOnLayer(B_CU):
                layer = 0
            elif p.IsOnLayer(B_CU) and not p.IsOnLayer(F_CU):
                layer = 1
            else:
                layer = None
            shape = p.GetShape()
            if shape == pcbnew.PAD_SHAPE_CIRCLE:
                w = h = max(w, h)
            pads.append(Pad(name, layer, cx, cy, w, h, ang, pth, ref, p.GetNumber()))
    return pads, holes


def bucketize(pads, reach_extra=1.2):
    buckets = defaultdict(list)
    for p in pads:
        reach = max(p.w, p.h) / 2 + reach_extra
        x0, x1 = int((p.cx - reach) // 2), int((p.cx + reach) // 2)
        y0, y1 = int((p.cy - reach) // 2), int((p.cy + reach) // 2)
        for ix in range(x0, x1 + 1):
            for iy in range(y0, y1 + 1):
                buckets[(ix, iy)].append(p)
    return buckets


def near_pads(buckets, x, y):
    return buckets[(int(x // 2), int(y // 2))]


class Grid:
    def __init__(self, pads, holes):
        self.pads, self.holes = pads, holes
        self.buckets = bucketize(pads)
        self.block = np.zeros((NL, H, W), np.int16)
        self.via = np.zeros((H, W), np.int16)
        # 1 = real copper centreline (cheap to walk). Halo cells are this net but costly,
        # so a later branch of the same net does not lay a parallel track in its own clearance.
        self.spine = np.zeros((NL, H, W), np.uint8)
        self.net_id = {}
        self.id_net = {}
        names = sorted({p.net for p in pads})
        for i, n in enumerate(names, start=1):
            self.net_id[n] = i
            self.id_net[i] = n
        self._mask_edge()
        self._paint_pads_holes()

    def nid(self, name):
        return self.net_id[name]

    def _mask_edge(self):
        for iy in range(H):
            for ix in range(W):
                x, y = cell_mm(ix, iy)
                if not in_rr(x, y, EDGE + TRACK_W / 2):
                    for L in range(NL):
                        self.block[L, iy, ix] = -1
                if not in_rr(x, y, EDGE + VIA_R):
                    self.via[iy, ix] = -1

    def _paint(self, arr, y, x, nid):
        cur = int(arr[y, x])
        if cur == -1:
            return
        if cur == 0 or cur == nid:
            arr[y, x] = nid
        else:
            arr[y, x] = -1

    def _paint_pads_holes(self):
        for p in self.pads:
            nid = self.nid(p.net)
            reach = max(p.w, p.h) / 2 + VIA_PAD + G
            ix0, iy0 = mm_cell(p.cx - reach, p.cy - reach)
            ix1, iy1 = mm_cell(p.cx + reach, p.cy + reach)
            layers = tuple(range(NL)) if p.layer is None else (p.layer,)
            for iy in range(max(0, iy0), min(H, iy1 + 1)):
                for ix in range(max(0, ix0), min(W, ix1 + 1)):
                    if self.block[0, iy, ix] == -1 and self.via[iy, ix] == -1:
                        # still need to paint a layer that is inside the board; edge cells are -1 on both
                        if not in_rr(*cell_mm(ix, iy), 0.0):
                            continue
                    x, y = cell_mm(ix, iy)
                    d = dist_rect(x, y, p.cx, p.cy, p.w, p.h, p.ang)
                    if d < TRACK_PAD - 1e-6:
                        for L in layers:
                            if int(self.block[L, iy, ix]) == -1:
                                continue
                            self._paint(self.block[L], iy, ix, nid)
                            if d < 1e-6 and int(self.block[L, iy, ix]) == nid:
                                self.spine[L, iy, ix] = 1
                    if d < VIA_PAD - 1e-6 and self.via[iy, ix] != -1:
                        self._paint(self.via, iy, ix, nid)
        for h in self.holes:
            reach = max(h.w, h.h) / 2 + VIA_R + HOLE_CLEAR + G
            ix0, iy0 = mm_cell(h.cx - reach, h.cy - reach)
            ix1, iy1 = mm_cell(h.cx + reach, h.cy + reach)
            for iy in range(max(0, iy0), min(H, iy1 + 1)):
                for ix in range(max(0, ix0), min(W, ix1 + 1)):
                    x, y = cell_mm(ix, iy)
                    d = dist_rect(x, y, h.cx, h.cy, h.w, h.h, h.ang)
                    if d < HOLE_CLEAR + TRACK_W / 2:
                        for L in range(NL):
                            self.block[L, iy, ix] = -1
                    if d < HOLE_CLEAR + VIA_R:
                        self.via[iy, ix] = -1

    def claim_disk(self, x, y, nid, rad, layers, via_rad=None, spine_r=0.16):
        rad_c = int(math.ceil(max(rad, via_rad or 0) / G)) + 1
        ix, iy = mm_cell(x, y)
        for dy in range(-rad_c, rad_c + 1):
            for dx in range(-rad_c, rad_c + 1):
                jx, jy = ix + dx, iy + dy
                if not (0 <= jx < W and 0 <= jy < H):
                    continue
                cx, cy = cell_mm(jx, jy)
                d = math.hypot(cx - x, cy - y)
                if d <= rad + 1e-9:
                    for L in layers:
                        self._paint(self.block[L], jy, jx, nid)
                        if d <= spine_r and int(self.block[L, jy, jx]) == nid:
                            self.spine[L, jy, jx] = 1
                if via_rad is not None and d <= via_rad + 1e-9 and self.via[jy, jx] != -1:
                    self._paint(self.via, jy, jx, nid)

    def claim_segment(self, x1, y1, x2, y2, layer, nid, width=TRACK_W):
        length = math.hypot(x2 - x1, y2 - y1)
        steps = max(1, int(length / (G * 0.5)) + 1)
        rad = width / 2 + CLEAR + TRACK_W / 2 + MARGIN
        vrad = width / 2 + CLEAR + VIA_R + MARGIN
        for i in range(steps + 1):
            t = i / steps
            self.claim_disk(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, nid, rad, (layer,), vrad)

    def foreign_hit(self, x, y, nid, kind, layer=None):
        """kind 'track' or 'via'. True if this copper clears every foreign pad and hole.
        A track on one side ignores SMD pads on the other side. A through via does not."""
        limit = TRACK_PAD if kind == "track" else VIA_PAD
        for p in near_pads(self.buckets, x, y):
            if self.nid(p.net) == nid:
                continue
            if kind == "track" and p.layer is not None and layer is not None and p.layer != layer:
                continue
            if dist_rect(x, y, p.cx, p.cy, p.w, p.h, p.ang) < limit - 1e-6:
                return False
        hlim = (HOLE_CLEAR + TRACK_W / 2) if kind == "track" else (HOLE_CLEAR + VIA_R)
        for h in self.holes:
            if math.hypot(x - h.cx, y - h.cy) > max(h.w, h.h) + 2:
                continue
            if dist_rect(x, y, h.cx, h.cy, h.w, h.h, h.ang) < hlim - 1e-6:
                return False
        inset = EDGE + (TRACK_W / 2 if kind == "track" else VIA_R)
        if not in_rr(x, y, inset):
            return False
        return True


def add_track(board, net, x1, y1, x2, y2, layer, width=TRACK_W):
    if math.hypot(x2 - x1, y2 - y1) < 1e-4:
        return None
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
    t.SetWidth(pcbnew.FromMM(width))
    t.SetLayer(LAYERS[layer])
    t.SetNet(net)
    board.Add(t)
    return t


def add_via(board, net, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    v.SetWidth(pcbnew.FromMM(VIA_D))
    v.SetDrill(pcbnew.FromMM(VIA_DRILL))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(F_CU, B_CU)
    v.SetNet(net)
    board.Add(v)
    return v


def _disk_clear(grid, x, y, nid, rad=VIA_TRACK):
    """Every grid cell the via copper crowds must be empty or already this net."""
    rad_c = int(math.ceil(rad / G)) + 1
    ix, iy = mm_cell(x, y)
    for dy in range(-rad_c, rad_c + 1):
        for dx in range(-rad_c, rad_c + 1):
            jx, jy = ix + dx, iy + dy
            if not (0 <= jx < W and 0 <= jy < H):
                continue
            cx, cy = cell_mm(jx, jy)
            if math.hypot(cx - x, cy - y) > rad:
                continue
            if int(grid.block[0, jy, jx]) not in (0, nid):
                return False
            if int(grid.block[1, jy, jx]) not in (0, nid):
                return False
            if int(grid.via[jy, jx]) not in (0, nid):
                return False
    return True


def place_plane_vias(board, grid, net_items):
    """One via on every SMD pad of GND and +3V3, with a short neck when the via sits off the pad."""
    vias = []  # (x, y, nid)
    failed = []
    pads = [p for p in grid.pads if p.net in PLANE and not p.pth]
    # small pads first so the LQFP fanout sees the vias already taken
    pads.sort(key=lambda p: max(p.w, p.h))
    for p in pads:
        nid = grid.nid(p.net)
        ux = math.cos(math.radians(p.ang if p.w >= p.h else p.ang + 90))
        uy = math.sin(math.radians(p.ang if p.w >= p.h else p.ang + 90))
        sx, sy = -uy, ux
        cands = []
        for t in (0.0, 0.45, -0.45, 0.9, -0.9, 1.25, -1.25, 1.7, -1.7, 2.2, -2.2, 2.8, -2.8):
            cands.append((p.cx + ux * t, p.cy + uy * t))
        for t in (1.3, 1.9, 2.6):
            for s in (0.55, -0.55, 0.95, -0.95):
                cands.append((p.cx + ux * t + sx * s, p.cy + uy * t + sy * s))
        placed = False
        for x, y in cands:
            if not grid.foreign_hit(x, y, nid, "via"):
                continue
            if any(math.hypot(x - vx, y - vy) < (0.62 if vn == nid else VIA_VIA) for vx, vy, vn in vias):
                continue
            # the via disk has to be free of copper already claimed on either side
            if not _disk_clear(grid, x, y, nid):
                continue
            dpad = dist_rect(x, y, p.cx, p.cy, p.w, p.h, p.ang)
            neck = None
            if dpad >= VIA_R - 0.02:
                qx, qy = closest_rect(x, y, p.cx, p.cy, p.w, p.h, p.ang)
                ok = True
                n = max(1, int(math.hypot(x - qx, y - qy) / 0.12))
                for i in range(n + 1):
                    t = i / n
                    px, py = qx + (x - qx) * t, qy + (y - qy) * t
                    if not grid.foreign_hit(px, py, nid, "track", p.layer):
                        ok = False
                        break
                    if any(math.hypot(px - vx, py - vy) < VIA_TRACK - 1e-6 for vx, vy, vn in vias if vn != nid):
                        ok = False
                        break
                if not ok:
                    continue
                neck = (qx, qy, x, y)
            item = net_items[p.net]
            if neck and p.layer is not None:
                add_track(board, item, neck[0], neck[1], neck[2], neck[3], p.layer)
                grid.claim_segment(neck[0], neck[1], neck[2], neck[3], p.layer, nid)
            add_via(board, item, x, y)
            grid.claim_disk(x, y, nid, VIA_TRACK, tuple(range(NL)), VIA_VIA)
            vias.append((x, y, nid))
            placed = True
            break
        if not placed:
            failed.append(p)
    return vias, failed


def access_cells(grid, pad):
    nid = grid.nid(pad.net)
    reach = max(pad.w, pad.h) / 2 + G
    ix0, iy0 = mm_cell(pad.cx - reach, pad.cy - reach)
    ix1, iy1 = mm_cell(pad.cx + reach, pad.cy + reach)
    layers = tuple(range(NL)) if pad.layer is None else (pad.layer,)
    out = []
    for iy in range(max(0, iy0), min(H, iy1 + 1)):
        for ix in range(max(0, ix0), min(W, ix1 + 1)):
            x, y = cell_mm(ix, iy)
            if dist_rect(x, y, pad.cx, pad.cy, pad.w, pad.h, pad.ang) > 0.02:
                continue
            for L in layers:
                if int(grid.block[L, iy, ix]) in (0, nid):
                    out.append((L, ix, iy))
    return out


def route_net(grid, pads, anchors=None, relax=False):
    """Return a list of (layer, x1, y1, x2, y2) and vias (x, y), or None."""
    if not pads:
        return []
    nid = grid.nid(pads[0].net)
    acc = []
    for p in pads:
        cells = access_cells(grid, p)
        if not cells and not p.pth:
            return None
        acc.append(cells)
    # anchors (plane vias / pth) are an already-connected terminal
    connected = set()
    if anchors:
        for x, y in anchors:
            ix, iy = mm_cell(x, y)
            if 0 <= ix < W and 0 <= iy < H:
                for L in range(NL):
                    connected.add((L, ix, iy))
        remaining = set(range(len(pads)))
    else:
        connected = set(acc[0])
        remaining = set(range(1, len(pads)))
    if not connected:
        return None
    # Keep long runs off the bottom pin field. Escapes are spine, destinations have a pad halo.
    use_mask = (not relax) and any(p.ref == "U1" for p in pads) and _has_top_via(grid, pads, nid)
    bot = _bottom_mask(pads) if use_mask else None
    drawn = []
    guard = 0
    while remaining and guard < len(pads) + 2:
        guard += 1
        done = [i for i in remaining if set(acc[i]) & connected]
        for i in done:
            remaining.discard(i)
            connected.update(acc[i])
        if not remaining:
            break
        # nearest remaining pad by centroid distance
        sx = sum(c[1] for c in connected) / len(connected)
        sy = sum(c[2] for c in connected) / len(connected)
        best_i, best_d = None, 1e18
        for i in remaining:
            if not acc[i]:
                return None
            cx = sum(c[1] for c in acc[i]) / len(acc[i])
            cy = sum(c[2] for c in acc[i]) / len(acc[i])
            d = (cx - sx) ** 2 + (cy - sy) ** 2
            if d < best_d:
                best_i, best_d = i, d
        path = _search(grid, connected, acc[best_i], nid, margin=40, bot=bot)
        if path is None:
            path = _search(grid, connected, acc[best_i], nid, margin=None, bot=bot)
        if path is None:
            return None
        drawn.extend(_emit(path))
        for L, ix, iy in path:
            connected.add((L, ix, iy))
        connected.update(acc[best_i])
        remaining.discard(best_i)
    if remaining:
        return None
    return drawn


def _has_top_via(grid, pads, nid):
    """True when fanout dropped a via for this net (top-layer spine near the MCU pad)."""
    for p in pads:
        if p.ref != "U1":
            continue
        ix, iy = mm_cell(p.cx, p.cy)
        for dy in range(-40, 41):
            yy = iy + dy
            if not (0 <= yy < H):
                continue
            for dx in range(-40, 41):
                xx = ix + dx
                if 0 <= xx < W and int(grid.spine[0, yy, xx]) and int(grid.block[0, yy, xx]) == nid:
                    return True
    return False


def _bottom_mask(pads):
    """Bottom copper the long runs may use: a pad's own neighbourhood, not the whole MCU side.
    U1 itself is reached along its fanout spine, so it does not open the bottom."""
    mask = np.zeros((H, W), np.uint8)
    rad = int(2.6 / G)
    r2 = (2.6 / G) ** 2
    for p in pads:
        if p.ref == "U1" or p.layer == 0:
            continue
        ix, iy = mm_cell(p.cx, p.cy)
        for dy in range(-rad, rad + 1):
            for dx in range(-rad, rad + 1):
                if dx * dx + dy * dy > r2:
                    continue
                jx, jy = ix + dx, iy + dy
                if 0 <= jx < W and 0 <= jy < H:
                    mask[jy, jx] = 1
    return mask


def _cell_ok(grid, layer, ix, iy, nid, bot):
    if not (0 <= ix < W and 0 <= iy < H):
        return False
    b = int(grid.block[layer, iy, ix])
    if b not in (0, nid):
        return False
    if layer == 1 and bot is not None and not int(grid.spine[1, iy, ix]) and not bot[iy, ix]:
        return False
    return True


def _idx(layer, ix, iy):
    return (layer * H + iy) * W + ix


def _search(grid, sources, targets, nid, margin, bot=None):
    if not targets:
        return None
    tgt = set()
    xs, ys = [], []
    for L, ix, iy in sources:
        xs.append(ix); ys.append(iy)
    for L, ix, iy in targets:
        tgt.add(_idx(L, ix, iy))
        xs.append(ix); ys.append(iy)
    if margin is None:
        ix0, iy0, ix1, iy1 = 0, 0, W - 1, H - 1
    else:
        ix0 = max(0, min(xs) - margin); iy0 = max(0, min(ys) - margin)
        ix1 = min(W - 1, max(xs) + margin); iy1 = min(H - 1, max(ys) + margin)
    dist = {}
    prev = {}
    hq = []
    src_idx = set()
    for L, ix, iy in sources:
        if not (ix0 <= ix <= ix1 and iy0 <= iy <= iy1):
            continue
        i = _idx(L, ix, iy)
        dist[i] = 0
        src_idx.add(i)
        heapq.heappush(hq, (0, i))
    block = grid.block
    via = grid.via
    found = None
    while hq:
        d, i = heapq.heappop(hq)
        if d != dist.get(i):
            continue
        if i in tgt and i not in src_idx:
            found = i
            break
        layer = i // (H * W)
        rem = i - layer * H * W
        iy, ix = divmod(rem, W)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            jx, jy = ix + dx, iy + dy
            if not (ix0 <= jx <= ix1 and iy0 <= jy <= iy1):
                continue
            if not _cell_ok(grid, layer, jx, jy, nid, bot):
                continue
            b = int(block[layer, jy, jx])
            # halo of our own copper is legal but expensive, so branches don't double up
            step = 1 if b == 0 or int(grid.spine[layer, jy, jx]) else 5
            j = _idx(layer, jx, jy)
            nd = d + step
            if nd < dist.get(j, 10 ** 9):
                dist[j] = nd
                prev[j] = i
                heapq.heappush(hq, (nd, j))
        vb = int(via[iy, ix])
        if vb in (0, nid):
            for ol in range(NL):
                if ol == layer or not _cell_ok(grid, ol, ix, iy, nid, bot):
                    continue
                j = _idx(ol, ix, iy)
                nd = d + VIA_COST
                if nd < dist.get(j, 10 ** 9):
                    dist[j] = nd
                    prev[j] = i
                    heapq.heappush(hq, (nd, j))
    if found is None:
        return None
    path = []
    cur = found
    seen = set()
    while cur not in src_idx:
        if cur in seen:
            return None
        seen.add(cur)
        layer = cur // (H * W)
        rem = cur - layer * H * W
        iy, ix = divmod(rem, W)
        path.append((layer, ix, iy))
        cur = prev.get(cur)
        if cur is None:
            return None
    layer = cur // (H * W)
    rem = cur - layer * H * W
    iy, ix = divmod(rem, W)
    path.append((layer, ix, iy))
    path.reverse()
    return path


def _emit(path):
    """Path cells -> ('t', layer, x1, y1, x2, y2) and ('v', x, y)."""
    out = []
    for a, b in zip(path, path[1:]):
        if a[0] != b[0]:
            x, y = cell_mm(b[1], b[2])
            out.append(("v", x, y))
        else:
            x1, y1 = cell_mm(a[1], a[2])
            x2, y2 = cell_mm(b[1], b[2])
            out.append(("t", a[0], x1, y1, x2, y2))
    return out


def commit(board, grid, net_item, nid, drawn):
    for item in drawn:
        if item[0] == "v":
            _, x, y = item
            add_via(board, net_item, x, y)
            grid.claim_disk(x, y, nid, VIA_TRACK, tuple(range(NL)), VIA_VIA)
        else:
            _, layer, x1, y1, x2, y2 = item
            add_track(board, net_item, x1, y1, x2, y2, layer)
            grid.claim_segment(x1, y1, x2, y2, layer, nid)


def add_zones(board):
    def poly(inset=0.40):
        r = ORAD - inset
        x0, y0, x1, y1 = OX0 + inset, OY0 + inset, OX1 - inset, OY1 - inset
        pts = []
        steps = 8
        corners = (
            (x1 - r, y0 + r, -90, 0),
            (x1 - r, y1 - r, 0, 90),
            (x0 + r, y1 - r, 90, 180),
            (x0 + r, y0 + r, 180, 270),
        )
        for cx, cy, a0, a1 in corners:
            for i in range(steps):
                a = math.radians(a0 + (a1 - a0) * i / steps)
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        ps = pcbnew.SHAPE_POLY_SET()
        ps.NewOutline()
        for x, y in pts:
            ps.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        return ps

    made = []
    for name, layer in (("GND", pcbnew.In1_Cu), ("+3V3", pcbnew.In2_Cu)):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(board.FindNet(name))
        z.SetZoneName(name + " plane")
        z.SetAssignedPriority(1)
        z.SetIsRuleArea(False)
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetMinThickness(pcbnew.FromMM(0.20))
        z.SetLocalClearance(pcbnew.FromMM(CLEAR))
        z.SetThermalReliefGap(pcbnew.FromMM(0.20))
        z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.30))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
        z.SetFillMode(pcbnew.ZONE_FILL_MODE_POLYGONS)
        ps = poly()
        ps.thisown = False
        made.append(ps)
        z.SetOutline(ps)
        z.SetNeedRefill(True)
        board.Add(z)
    filler = pcbnew.ZONE_FILLER(board)
    ok = filler.Fill(board.Zones())
    print("zone fill", ok)
    return ok


def fanout_u1(board, grid, net_items):
    """One via per LQFP pin, just outside or just inside the package, then a short neck.
    Long runs then leave on the top layer so they do not wall off the pin row."""
    pads = [p for p in grid.pads if p.ref == "U1" and p.layer is not None and not p.net.startswith("NC-")]
    if not pads:
        return
    cx = sum(p.cx for p in pads) / len(pads)
    cy = sum(p.cy for p in pads) / len(pads)
    linked = 0
    missed = []
    for p in sorted(pads, key=lambda q: (0 if q.net in ("+3V3", "GND") else 1, int(q.num))):
        dx, dy = p.cx - cx, p.cy - cy
        nrm = math.hypot(dx, dy) or 1.0
        ux, uy = dx / nrm, dy / nrm
        tx, ty = -uy, ux
        nid = grid.nid(p.net)
        pin = int(p.num)
        base = 1.3 if pin % 2 == 0 else 2.1
        src = set(access_cells(grid, p))
        linked_this = False
        for sign in (1, -1):
            for extra in (0.0, 0.7, 1.4, 2.2):
                for k in (0, 1, -1, 2, -2, 3, -3):
                    x = p.cx + sign * ux * (base + extra) + tx * (k * 0.25)
                    y = p.cy + sign * uy * (base + extra) + ty * (k * 0.25)
                    sx, sy = mm_cell(x, y)
                    if not (0 <= sx < W and 0 <= sy < H):
                        continue
                    x, y = cell_mm(sx, sy)
                    if not grid.foreign_hit(x, y, nid, "via") or not _disk_clear(grid, x, y, nid):
                        continue
                    link = _search(grid, src, [(p.layer, sx, sy)], nid, margin=30)
                    if link is None:
                        continue
                    commit(board, grid, net_items[p.net], nid, _emit(link) + [("v", x, y)])
                    linked_this = True
                    break
                if linked_this:
                    break
            if linked_this:
                break
        if linked_this:
            linked += 1
        else:
            missed.append(pin)
    print(f"U1 fanout necks {linked}/{len(pads)} missed {missed}")
    return


def route_signals(board, grid, net_items, plane_vias, failed_plane, prefer=None):
    by_net = defaultdict(list)
    for p in grid.pads:
        by_net[p.net].append(p)
    # anchors so a plane pad that could not take its own via can still reach the plane
    anchors = defaultdict(list)
    for x, y, nid in plane_vias:
        anchors[grid.id_net[nid]].append((x, y))
    for p in grid.pads:
        if p.net in PLANE and p.pth:
            anchors[p.net].append((p.cx, p.cy))
    order = []
    for name, pads in by_net.items():
        if name.startswith("NC-"):
            continue
        if name in PLANE:
            pads = [p for p in failed_plane if p.net == name]
            if not pads:
                continue
        else:
            pads = list(pads)
        # shortest first, power trunks before the long signal webs
        xs = [p.cx for p in pads]; ys = [p.cy for p in pads]
        span = (max(xs) - min(xs)) + (max(ys) - min(ys)) if pads else 0
        pin = min((int(p.num) for p in pads if p.ref == "U1"), default=999)
        # MCU nets first, while each pin's fanout is still an open door. Ring power next.
        # +5 V last: it is the net that walks the whole board.
        if name == "+3V3":
            pri, key = -2, 0
        elif prefer and name in prefer:
            pri, key = -1, prefer[name]
        elif pin != 999:
            pri, key = 1, span   # short MCU nets before the long ones, so they are not cut
        elif name in ("VLED", "V_LASER", "KCOM", "+5V"):
            pri, key = -1, span
        elif name == "+5V":
            pri, key = 9, span
        else:
            pri, key = 5, span
        order.append((pri, key, span, name, pads))
    order.sort()
    failed = []
    t0 = time.time()
    for n_i, (pri, npads, span, name, pads) in enumerate(order):
        nid = grid.nid(name)
        anc = anchors.get(name) if name in PLANE else None
        t1 = time.time()
        drawn = route_net(grid, pads, anc)
        dt = time.time() - t1
        if drawn is None:
            print(f"  FAIL {name} pads {len(pads)} {dt:.1f}s")
            failed.append(name)
            continue
        commit(board, grid, net_items[name], nid, drawn)
        if n_i < 6 or dt > 2 or (n_i + 1) % 25 == 0:
            print(f"  {n_i+1}/{len(order)} {name} pads {len(pads)} segs {len(drawn)} {dt:.1f}s")
    # one full-board retry for anything that missed
    if failed:
        print("retry", len(failed))
        still = []
        for name in failed:
            pads = [p for p in by_net[name] if name not in PLANE or p in failed_plane]
            if name in PLANE:
                pads = [p for p in failed_plane if p.net == name]
            drawn = route_net(grid, pads, anchors.get(name) if name in PLANE else None)
            if drawn is None:
                still.append(name)
                print("  still", name)
            else:
                commit(board, grid, net_items[name], grid.nid(name), drawn)
                print("  recovered", name)
        failed = still
    print(f"signals done in {time.time()-t0:.0f}s, failed {len(failed)}")
    return failed, by_net


def fill_open(board, grid, net_items, failed, by_net, anchors, failed_plane, rounds=4):
    """Commit any failed net that still has a path once the rest of the copper is down."""
    for rnd in range(rounds):
        if not failed:
            break
        still, n = [], 0
        for name in failed:
            if name in PLANE:
                pads = [p for p in failed_plane if p.net == name]
                anc = anchors.get(name)
            else:
                pads = by_net[name]
                anc = None
            drawn = route_net(grid, pads, anc, relax=True)
            if drawn is None:
                still.append(name)
            else:
                commit(board, grid, net_items[name], grid.nid(name), drawn)
                n += 1
                print(f"  fill {name} segs {len(drawn)}")
        print(f"fill round {rnd + 1}: recovered {n}, left {len(still)}")
        failed = still
        if n == 0:
            break
    return failed


def main():
    pcb_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "knob-main-pcb", "kicad", "knob-main-pcb.kicad_pcb")
    print("load", pcb_path)
    board = pcbnew.LoadBoard(pcb_path)
    # drop any earlier router copper (keep footprints and rule areas).
    # Zones first: removing tracks invalidates the zone wrappers.
    for z in list(board.Zones()):
        if not z.GetIsRuleArea():
            board.Remove(z)
    for t in list(board.GetTracks()):
        board.Remove(t)
    pads, holes = collect(board)
    print(f"pads {len(pads)} holes {len(holes)} grid {W}x{H}")
    grid = Grid(pads, holes)
    net_items = {}
    for name in grid.net_id:
        if name.startswith("NC-"):
            continue
        item = board.FindNet(name)
        if item is None:
            raise SystemExit("missing net " + name)
        net_items[name] = item
    t0 = time.time()
    vias, failed_plane = place_plane_vias(board, grid, net_items)
    print(f"plane vias {len(vias)} failed {len(failed_plane)} in {time.time()-t0:.1f}s")
    fanout_u1(board, grid, net_items)
    for t in board.GetTracks():
        t.SetLocked(True)   # plane vias and pin escapes stay while signal tracks are ripped
    for p in failed_plane[:12]:
        print(f"  no via {p.net} {p.ref}.{p.num} at ({p.cx-100:.2f},{p.cy-100:.2f})")
    failed, by_net = route_signals(board, grid, net_items, vias, failed_plane)
    anchors = {}
    for x, y, nid in vias:
        anchors.setdefault(grid.id_net[nid], []).append((x, y))
    for p in pads:
        if p.net in PLANE and p.pth:
            anchors.setdefault(p.net, []).append((p.cx, p.cy))
    failed = fill_open(board, grid, net_items, failed, by_net, anchors, failed_plane)
    if failed and os.environ.get("SHUFFLE"):
        print(f"shuffle {len(failed)} unrouted nets ahead of the ones that landed")
        for t in list(board.GetTracks()):
            if not t.IsLocked():
                board.Remove(t)
        grid = Grid(pads, holes)
        for t in board.GetTracks():
            name = t.GetNetname()
            if name not in grid.net_id:
                continue
            nid = grid.nid(name)
            if t.GetClass() == "PCB_VIA":
                grid.claim_disk(pcbnew.ToMM(t.GetPosition().x), pcbnew.ToMM(t.GetPosition().y),
                                nid, VIA_TRACK, tuple(range(NL)), VIA_VIA)
            else:
                layer = t.GetLayer()
                if layer not in LAYERS:
                    continue
                s, e = t.GetStart(), t.GetEnd()
                grid.claim_segment(pcbnew.ToMM(s.x), pcbnew.ToMM(s.y), pcbnew.ToMM(e.x), pcbnew.ToMM(e.y),
                                   LAYERS.index(layer), nid, pcbnew.ToMM(t.GetWidth()))
        failed, _by = route_signals(board, grid, net_items, vias, failed_plane,
                                    prefer={n: i for i, n in enumerate(failed)})
        failed = fill_open(board, grid, net_items, failed, _by, anchors, failed_plane)
    add_zones(board)
    pcbnew.SaveBoard(pcb_path, board)
    # SaveBoard rewrites the project; put the clearance rules back
    sys.path.insert(0, os.path.join(os.path.dirname(pcb_path)))
    import make_board
    make_board.write_project()
    print("saved", pcb_path)
    if failed:
        print("UNROUTED", ", ".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    main()
