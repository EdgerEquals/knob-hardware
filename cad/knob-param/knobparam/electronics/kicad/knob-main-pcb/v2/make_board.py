"""Main board v2 generator (8 Nov 2026, step 3: placing). Builds the KiCad board from design.py (the netlist) and the model's
room map (tools/studies/main_board_room.py pickle: the board outline with its windows and cut-outs, what the mechanics take on
each face, and the model's numbers for the parts it fixes). Run with the KiCad python (pcbnew):
  /usr/bin/python3 make_board.py <mb_room.pkl> [--iters N] [--seed S]
Writes kicad/knob-main-pcb.kicad_pcb (+ project, rules), placement.json and a placement picture.

Frames: panel (x right, y up, mm, the dial axis at 0, 0) -> KiCad local (x, -y) + ORIGIN. Mechanism-frame numbers from the model
(Halls, ring LEDs, the encoder sensor, the motor, the rod) are turned by mech_rot first.
Fixed here from the model: the H743's centre (its quarter turn is the placer's), the five Halls, the 12 ring LEDs, the encoder
sensor, the power-light VCSEL, the two posts, the link flex pads, board L and R headers, the rod clamp, the 1220's tabs.
Everything else is placed by ../../placer.py (annealing) inside its block's zone [A, from the plan picture], on the free room of
its face (what the model leaves after the mechanics), via a raster mask (a summed-area table: an O(1) "how much of this courtyard
is not allowed")."""
import os, sys, json, math, pickle, argparse
import numpy as np
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
KI = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, KI); sys.path.insert(0, HERE)
import design, placer
from kicad7_tools import FP, V, mm, save_fp, write_project, drc, save_board

NAME = "knob-main-pcb"; PCB_VERSION = "v2.0"
LIB = "mb"; LIB_DIR = os.path.join(HERE, LIB + ".pretty")
KLIB = "/usr/share/kicad/footprints"; REPO_LIB = os.path.join(KI, "footprints.pretty")
OUT = os.path.join(HERE, "kicad")
ORIGIN = (100.0, 100.0)
BT = 1.6
RULES = dict(clearance=0.1, track=0.127, min_track=0.1, via_d=0.45, via_drill=0.2, edge=0.25)
GRID = 0.1                     # mm, the placer's room raster
EDGE_KEEP = 0.25               # courtyards this far inside the board edge, the windows and the cut-outs
POWER_W = {"GND": 0.0, "3V3": 0.15, "5V": 0.3, "VSYS": 0.5, "VM": 0.5, "RING_5V": 0.3, "RING_IN": 0.5, "VDDA": 0.5, "VREFP": 0.8}
# the parts the model draws itself and this board places as fixed parts: left out of the mechanical keep-out
ELECTRICAL = ("MCU ", "hall sensor", "power light VCSEL", "emitter RGB", "encoder sensor EE-SX1321")
# block zones [A, after docs/img/main-board-plan.png], panel frame (x0, y0, x1, y1) per face
Z = {
    "mcu": {"F": [(-13.0, 23.0, 13.0, 49.0)]},
    "link": {"F": [(-13.0, 23.0, 16.0, 49.0)]},
    "screen": {"F": [(4.0, 24.0, 16.5, 47.0)]},
    "debug": {"F": [(-16.5, 24.0, -6.0, 47.0)]},
    "light": {"F": [(-4.0, 21.0, 5.0, 30.0)], "B": [(-5.0, 19.5, 6.0, 31.0)]},
    "adc": {"B": [(-15.0, 21.0, 15.0, 48.5)]},
    "halls": {"B": [(-16.0, 0.0, 0.0, 16.0)]},
    "encoder": {"B": [(6.0, 17.0, 21.0, 34.0)]},
    "motor": {"B": [(-9.0, -19.0, 15.0, -2.0)]},
    "ring": {"B": [(-22.5, -24.0, 22.5, 24.0)]},
    "rod": {"B": [(-8.0, -8.0, 13.0, 9.0)]},
    "power": {"B": [(-4.0, -53.5, 21.0, -42.0), (-22.5, 18.0, -6.0, 47.0)]},
    "cover": {"B": [(-14.0, 42.0, 14.0, 49.5)]},
}
MOTOR_TAB_CAP_FACE = "B"


def L(x, y):           # panel -> KiCad local
    return x, -y


def P(lx, ly):         # KiCad local -> board
    return V(ORIGIN[0] + lx, ORIGIN[1] + ly)


def rot2(x, y, a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return x * c - y * s, x * s + y * c


# ------------------------------------------------------------------ footprints
_FP_CACHE, _KEEP, _SCRATCH = {}, [], []
R = None   # the room pickle (main() loads it)


def fp_post(board):
    pin, hole, pad, _ = R["D"]["jb_post_pin"]
    f = FP(board, LIB, "Post_Pin_1.0", f"Ø{pin:g} pin of the Ø2 brass post: plated Ø{hole:g}, Ø{pad:g} pad [Ed 6 Nov Q24 = A; "
                                       "the jack power board's end, C the main-board end]")
    f.pth("1", 0, 0, pad, pad, hole, shape="circle")
    f.rect(-1.0, -1.0, 1.0, 1.0, pcbnew.F_Fab); f.rect(-1.1, -1.1, 1.1, 1.1, pcbnew.F_CrtYd)
    return f.done(0.0)


def _header(board, name, side):
    """Board L / R bottom header: 2 x 11 legs at the model's places (vb_legs), THT 0.7 in 0.95 pads, SMT feet [A] 0.8 x 0.8.
    Pin 2k+1 = the inner row's k-th leg from the bottom, 2k+2 = the outer row's [A]."""
    legs = R["D"]["vb_legs"][side]; h = R["D"]["vb_hdr"]
    cx, cy = HDR_C[side]
    inner = sorted([l for l in legs if abs(abs(l[0]) - 17.4) < 0.05], key=lambda l: l[1])
    outer = sorted([l for l in legs if abs(l[0]) - 17.4 > 0.5], key=lambda l: l[1])
    f = FP(board, LIB, name, f"vertical board {'L' if side < 0 else 'R'} bottom header, 2 x 11 at 1.27, legs from model vb_legs "
                             f"({'all THT' if side < 0 else 'SMT over the encoder sensor, THT above'}) [S layout v4, A pin order]")
    k = 0
    for a, b in zip(inner, outer):
        for leg in (a, b):
            k += 1
            lx, ly = L(leg[0] - cx, leg[1] - cy)
            if leg[2] == "tht":
                f.pth(str(k), lx, ly, h["pad"], h["pad"], h["drill"], shape="circle")
            else:
                f.smd(str(k), lx, ly, 0.8, 0.8, shape="roundrect")   # the bent foot of a hybrid leg [A]
    xs = [L(l[0] - cx, 0)[0] for l in legs]; ys = [L(0, l[1] - cy)[1] for l in legs]
    f.rect(min(xs) - 0.7, min(ys) - 0.7, max(xs) + 0.7, max(ys) + 0.7, pcbnew.F_CrtYd)
    return f.done(0.0)


def fp_hdr_l(board):
    return _header(board, "VBoard_L_Header_2x11_P1.27_THT", -1)


def fp_hdr_r(board):
    return _header(board, "VBoard_R_Header_2x11_P1.27_Hybrid", 1)


def fp_pads6(board):
    f = FP(board, LIB, "Pads_1x6_P1.27_SMD", "six SMD pads at 1.27 for the later cover board [A]")
    for i in range(6):
        f.smd(str(i + 1), (i - 2.5) * 1.27, 0, 0.8, 1.6, shape="roundrect")
    f.rect(-3.75, -1.05, 3.75, 1.05, pcbnew.F_CrtYd)
    return f.done(0.0)


def fp_led(board):
    """SK6812MINI-E, reverse mount: pads 1.35 x 0.82 at x +-2.725, y +-0.75 (marbastlib LED_6028R, CERN-OHL-P; Keebio-Parts
    SK6812-MINI-E, MIT, the same within 0.05); pin numbers as Keebio's: 1 VDD (-x, +y), 2 DOUT (-x, -y), 3 GND (+x, -y),
    4 DIN (+x, +y) [S; C against the datasheet drawing]. Authored on F.Cu, placed flipped on B.Cu (lens through the board's
    cut-out, which is in the board outline from the model)."""
    f = FP(board, LIB, "LED_SK6812MINI-E_Reverse", "SK6812MINI-E reverse mount; pads after marbastlib (CERN-OHL-P) and Keebio-Parts (MIT)")
    for num, x, y in (("1", -2.725, 0.75), ("2", -2.725, -0.75), ("3", 2.725, -0.75), ("4", 2.725, 0.75)):
        f.smd(num, x, y, 1.35, 0.82, shape="roundrect")
    f.rect(-1.6, -1.4, 1.6, 1.4, pcbnew.F_Fab); f.rect(-3.55, -1.3, 3.55, 1.3, pcbnew.F_CrtYd)
    return f.done(0.0)


OWN = {"mb:Post_Pin_1.0": fp_post, "mb:VBoard_L_Header_2x11_P1.27_THT": fp_hdr_l, "mb:VBoard_R_Header_2x11_P1.27_Hybrid": fp_hdr_r,
       "mb:Pads_1x6_P1.27_SMD": fp_pads6, "mb:LED_SK6812MINI-E_Reverse": fp_led}


def load_fp(board, name):
    if name not in _FP_CACHE:
        _FP_CACHE[name] = _load_fp(board, name)
    return _FP_CACHE[name].Duplicate().Cast()


def _load_fp(board, name):
    if name in OWN:
        f = OWN[name](board)
    else:
        lib, fn = name.split(":")
        path = REPO_LIB if lib == "footprints" else os.path.join(KLIB, lib + ".pretty")
        f = pcbnew.FootprintLoad(path, fn)
        f.SetFPID(pcbnew.LIB_ID(LIB, fn))
    for g in list(f.GraphicalItems()):
        if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            f.Remove(g); _KEEP.append(g)
    try:
        f.Value().SetVisible(False)
    except AttributeError:
        pass
    return f


def geometry(name, side, rot, cache={}):
    key = (name, side, rot)
    if key in cache:
        return cache[key]
    if not _SCRATCH:
        _SCRATCH.append(pcbnew.BOARD())
    b = _SCRATCH[0]; f = load_fp(b, name); b.Add(f); _KEEP.append(f)
    f.SetPosition(V(0, 0)); f.SetOrientationDegrees(rot)
    if side == "B":
        f.Flip(f.GetPosition(), False)
    pads = {}
    for p in f.Pads():
        n = p.GetNumber()
        if n and n not in pads:
            pads[n] = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
    xs, ys = [], []
    lay = pcbnew.B_CrtYd if side == "B" else pcbnew.F_CrtYd
    for g in f.GraphicalItems():
        if g.GetLayer() == lay:
            bb = g.GetBoundingBox(); xs += [pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight())]
            ys += [pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom())]
    if not xs:
        for p in f.Pads():
            bb = p.GetBoundingBox(); xs += [pcbnew.ToMM(bb.GetLeft()) - 0.25, pcbnew.ToMM(bb.GetRight()) + 0.25]
            ys += [pcbnew.ToMM(bb.GetTop()) - 0.25, pcbnew.ToMM(bb.GetBottom()) + 0.25]
    cache[key] = (min(xs), min(ys), max(xs), max(ys), pads)
    return cache[key]


# ------------------------------------------------------------------ the model's fixed parts
HDR_C = {}


def fixed_parts(parts):
    """{ref: (lx, ly, side, rot)} in KiCad local, rot before the flip (as the placer and build() use it)."""
    D = R["D"]; mr = D["mech_rot"]; fx = {}
    by_val = lambda v: [p["ref"] for p in parts if p["value"] == v]
    # Halls: design order U3-U6 = rows 1, 2, 4, 5 (TMAG5253), U7 = row 3 (TMAG5273); mechanism (hv_r, hv_phi_s), long side tangential
    rows = [0, 1, 3, 4, 2]
    halls = by_val("TMAG5253BA3IQDMRR") + by_val("TMAG5273A2QDBVR")
    for ref, i in zip(halls, rows):
        x, y = rot2(D["hv_r"][i] * math.cos(math.radians(D["hv_phi_s"][i])), D["hv_r"][i] * math.sin(math.radians(D["hv_phi_s"][i])), mr)
        fx[ref] = (*L(x, y), "F", round((D["hv_phi_s"][i] + mr) % 360.0, 3))
    # ring LEDs, in chain order round the ring: long axis (pads) along the ring [Q44]. Flip(False) mirrors about the horizontal
    # axis, so an axis at angle t before the flip lies at -t after it: rotate by -(site angle + 90).
    leds = [p["ref"] for p in parts if p["value"] == "SK6812MINI-E"]
    holes = sorted(D["em_holes"], key=lambda h: h["i"])
    assert len(leds) == len(holes), (len(leds), len(holes))
    for ref, h in zip(leds, holes):
        x, y = rot2(h["x"], h["y"], mr)
        fx[ref] = (*L(x, y), "B", round((-(h["ang"] + mr + 90.0)) % 360.0, 3))
    # encoder sensor: slot (footprint Y) along the disc's tangent at sens_dir (mechanism), on the back
    enc = by_val("EE-SX1321")[0]
    x, y = rot2(*D["sens_xy"], mr); t = D["sens_dir"] + 90.0 + mr          # tangent, panel
    fx[enc] = (*L(x, y), "B", round((-(t) - 90.0) % 360.0, 3))              # local Y at 90 + r, flipped -> -(90 + r) = t
    vc = by_val("JNJ-V-2835CW-665003-S-D1")[0]
    fx[vc] = (*L(*D["pwr_vcsel_xy"]), "F", 0.0)
    for ref, (x, y) in zip(("MP1", "MP2"), D["jb_post_xy"]):
        fx[ref] = (*L(x, y), "F", 0.0)
    lf = D["link_flex"]
    fx["J1"] = (*L(lf["x1"] + (lf["n"] - 1) * lf["pitch"] / 2, sum(lf["pad_y"]) / 2), "F", 0.0)
    for ref, side in (("J2", -1), ("J3", 1)):
        legs = D["vb_legs"][side]
        HDR_C[side] = ((min(l[0] for l in legs) + max(l[0] for l in legs)) / 2, (min(l[1] for l in legs) + max(l[1] for l in legs)) / 2)
        fx[ref] = (*L(*HDR_C[side]), "F", 0.0)
    fx["H1"] = (*L(0.0, 0.0), "F", round(mr % 360.0, 3))
    fx["M1"] = (*L(*rot2(D["motor_offset"], 0.0, mr)), "F", round(mr % 360.0, 3))
    return fx


# ------------------------------------------------------------------ room raster
class Room:
    """Allowed-room rasters per (zone, face) as summed-area tables over the board's bounding box (KiCad local)."""

    def __init__(self, free):
        from PIL import Image, ImageDraw
        b = R["board"].bounds
        self.x0, self.y0 = L(b[0], b[3])[0] - 1.0, L(b[0], b[3])[1] - 1.0
        self.nx = int((b[2] - b[0] + 2.0) / GRID) + 1; self.ny = int((b[3] - b[1] + 2.0) / GRID) + 1
        self.base = {}
        for face, g in free.items():
            img = Image.new("L", (self.nx, self.ny), 0); dr = ImageDraw.Draw(img)
            for poly in ([g] if g.geom_type == "Polygon" else list(g.geoms)):
                if poly.is_empty:
                    continue
                dr.polygon([self.cell(*L(x, y)) for x, y in poly.exterior.coords], fill=1)
                for hole in poly.interiors:
                    dr.polygon([self.cell(*L(x, y)) for x, y in hole.coords], fill=0)
            self.base[face] = np.array(img, dtype=np.int32)
        self.sat = {}

    def cell(self, lx, ly):
        return ((lx - self.x0) / GRID, (ly - self.y0) / GRID)

    def key(self, zone, face):
        k = (zone, face)
        if k not in self.sat:
            m = self.base[face].copy()
            zm = np.zeros_like(m)
            for (a, b_, c, d) in Z[zone][face]:
                (lx0, ly0), (lx1, ly1) = L(a, d), L(c, b_)
                i0, j0 = self.cell(lx0, ly0); i1, j1 = self.cell(lx1, ly1)
                zm[max(0, int(j0)):max(0, int(j1)), max(0, int(i0)):max(0, int(i1))] = 1
            s = np.zeros((self.ny + 1, self.nx + 1), dtype=np.int64)
            s[1:, 1:] = (m * zm).cumsum(0).cumsum(1)
            self.sat[k] = s
        return k

    def allowed(self, k, x0, y0, x1, y1):
        s = self.sat[k]
        i0 = min(max(int(round((x0 - self.x0) / GRID)), 0), self.nx); i1 = min(max(int(round((x1 - self.x0) / GRID)), 0), self.nx)
        j0 = min(max(int(round((y0 - self.y0) / GRID)), 0), self.ny); j1 = min(max(int(round((y1 - self.y0) / GRID)), 0), self.ny)
        if i1 <= i0 or j1 <= j0:
            return 0.0
        return float(s[j1, i1] - s[j0, i1] - s[j1, i0] + s[j0, i0]) * GRID * GRID


class MaskPlacer(placer.Placer):
    def __init__(self, items, regions, nets, room, **kw):
        super().__init__(items, regions, nets, **kw)
        self.room = room

    def out_area(self, i):
        m = self.items[i].get("mask")
        if not m:
            return super().out_area(i)
        k = m.get(self.o[i][0])
        x0, y0, x1, y1 = self.rect(i)
        a = (x1 - x0) * (y1 - y0)
        if k is None:
            return a * 4.0 + 50.0
        bad = a - self.room.allowed(k, x0, y0, x1, y1)
        return max(bad, 0.0) * 4.0 if bad > 0.5 * GRID * GRID else 0.0


# ------------------------------------------------------------------ placing
def run_placer(parts, fixed, room, iters, seed, log=print):
    items, nets = [], {}
    for p in parts:
        r = p["ref"]
        for num, n in p["pins"].items():
            if n:
                nets.setdefault(n, []).append((r, num))
        if r in fixed:
            x, y, s, rot = fixed[r]
            items.append(dict(ref=r, geoms={(s, rot): geometry(p["fp"], s, rot)}, fixed=(x, y, s, rot)))
            continue
        zone = p["block"]
        faces = [p["face"]] if p["face"] in Z[zone] else list(Z[zone])   # the netlist's face where the zone has it
        if r == "U1":   # the H743: its centre is the model's, its quarter turn is free
            mx, my = L(*R["D"]["mcu"]["xy"])
            g = {("F", rot): geometry(p["fp"], "F", rot) for rot in (0, 90, 180, 270)}
            reg = {"F": [(mx - 9.2, my - 9.2, mx + 9.2, my + 9.2)]}
            items.append(dict(ref=r, geoms=g, regions=reg, margin=0.3))
            continue
        g = {(s, rot): geometry(p["fp"], s, rot) for s in faces for rot in (0, 90, 180, 270)}
        reg = {}
        for s in ("F", "B"):
            rs = []
            for (a, b_, c, d) in Z[zone].get(s, []):
                (lx0, ly0), (lx1, ly1) = L(a, d), L(c, b_)
                rs.append((lx0, ly0, lx1, ly1))
            reg[s] = rs or [(0, 0, 0.01, 0.01)]
        items.append(dict(ref=r, geoms=g, regions=reg, mask={s: room.key(zone, s) for s in faces},
                          margin=0.12 if r[0] in "UJQ" else 0.08))
    netlist = [(POWER_W.get(n, 1.0), pins) for n, pins in nets.items()]
    # decoupling: each capacitor to the same supply's pin on the part with three or more pins just before it
    last = None
    for p in parts:
        if len([v for v in p["pins"].values() if v]) >= 3:
            last = p
        if p["ref"][0] == "C" and "GND" in p["pins"].values() and last is not None:
            sup = [n for n in p["pins"].values() if n != "GND"][0]
            ic = [k for k, v in last["pins"].items() if v == sup]
            if ic:
                netlist.append((2.5, [(p["ref"], [k for k, v in p["pins"].items() if v == sup][0]), (last["ref"], ic[0])]))
    b = R["board"].bounds
    whole = [(L(b[0], b[3])[0], L(b[0], b[3])[1], L(b[2], b[1])[0], L(b[2], b[1])[1])]
    pl = MaskPlacer(items, {"F": whole, "B": whole}, netlist, room, margin=0.08, seed=seed)
    pl.init_random()
    pl.run(iters=iters, log=log)
    pl.snap(0.05)
    ok = pl.repair(rounds=120, tries=200, log=log)
    if not ok:
        pl.legalise(rounds=300); pl.snap(0.05); ok = pl.repair(rounds=60, tries=200, log=log)
    if not ok:
        ok = pl.relocate(g=0.25, log=log)
    if not ok:
        pl.mscale = 0.0; ok = pl.repair(rounds=60, tries=200, log=log)
    if not ok:
        ok = pl.evict(log=log)
    wl, ov, out = pl.total()
    bad = [pl.items[i]["ref"] for i in range(pl.n) if not pl.fixed[i] and (pl.overlap(i) > 1e-6 or pl.out_area(i) > 1e-6)]
    log(f"placed: wirelength {wl:.1f}, overlap {ov:.3f} mm², outside {out:.3f}, legal {ok}; not legal: {bad}")
    return pl.result(), (wl, ov, out, bad)


# ------------------------------------------------------------------ the board
def footprint_holes(fixed):
    """Holes the footprints drill themselves (left out of Edge.Cuts): header legs, the rod, the motor and its tab slots (panel)."""
    D = R["D"]; out = []
    for side in (-1, 1):
        out += [(l[0], l[1]) for l in D["vb_legs"][side] if l[2] == "tht"]
    out.append((0.0, 0.0))
    mx, my = rot2(D["motor_offset"], 0.0, D["mech_rot"])
    out += [(mx, my), (mx, my - 3.0), (mx, my + 3.0)]
    return out


def build(parts, placement):
    from shapely.geometry import Polygon, Point
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings(); ds.SetBoardThickness(mm(BT)); ds.SetCopperLayerCount(4)
    ds.m_CopperEdgeClearance = mm(RULES["edge"])
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    skip = footprint_holes(None)
    loops = [list(R["board"].exterior.coords)]
    dropped = 0
    for hole in R["board"].interiors:
        c = Polygon(hole).centroid
        if any(math.hypot(c.x - x, c.y - y) < 0.15 for x, y in skip) and Polygon(hole).area < 9.0:
            dropped += 1
            continue
        loops.append(list(hole.coords))
    for pts in loops:
        pts = [L(x, y) for x, y in pts]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            if math.hypot(bx - ax, by - ay) < 1e-4:
                continue
            s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.05))
            s.SetStart(P(ax, ay)); s.SetEnd(P(bx, by)); board.Add(s)
    nets = {}

    def net(n):
        if n not in nets:
            nets[n] = pcbnew.NETINFO_ITEM(board, n); board.Add(nets[n])
        return nets[n]
    for p in parts:
        x, y, side, rot = placement[p["ref"]]
        f = load_fp(board, p["fp"])
        f.SetReference(p["ref"]); f.SetValue(p["value"])
        board.Add(f)
        f.SetPosition(P(x, y)); f.SetOrientationDegrees(rot)
        if side == "B":
            f.Flip(f.GetPosition(), False)
        f.Reference().SetLayer(pcbnew.B_Fab if side == "B" else pcbnew.F_Fab)
        f.Reference().SetTextSize(V(0.4, 0.4)); f.Reference().SetTextThickness(mm(0.06))
        if p["dnp"]:
            f.SetAttributes(f.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        if p["ref"][:2] in ("MP", "H1", "M1") or p["ref"] in ("J1", "J4", "J5"):   # hand-fitted, pads only, or bonded
            f.SetAttributes(f.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        for k, v in (("MPN", p["mpn"]), ("LCSC", p["lcsc"]), ("Note", p["note"])):
            if v:
                f.SetProperty(k, v)
        for pad in f.Pads():
            n = p["pins"].get(pad.GetNumber())
            if n:
                pad.SetNet(net(n))
    t = pcbnew.PCB_TEXT(board); t.SetText(f"knob main {PCB_VERSION} (model {R['D'].get('version', '?')})")
    t.SetPosition(P(*L(0.0, -45.0))); t.SetLayer(pcbnew.F_Fab); t.SetTextSize(V(0.8, 0.8)); t.SetTextThickness(mm(0.12)); board.Add(t)
    ds.SetAuxOrigin(P(0, 0)); ds.SetGridOrigin(P(0, 0))
    return board, dropped


def checks(pcb_path, fixed):
    """The model's fixed parts where the model has them: LED pads along the ring, the encoder slot along the disc's tangent."""
    b = pcbnew.LoadBoard(pcb_path); D = R["D"]; mr = D["mech_rot"]; out = []
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    to_panel = lambda v: (pcbnew.ToMM(v.x) - ORIGIN[0], -(pcbnew.ToMM(v.y) - ORIGIN[1]))
    worst = 0.0
    for p in fps.values():
        if p.GetValue() != "SK6812MINI-E":
            continue
        cx, cy = to_panel(p.GetPosition()); a = math.atan2(cy, cx)
        for pad in p.Pads():
            px, py = to_panel(pad.GetPosition())
            radial = (px - cx) * math.cos(a) + (py - cy) * math.sin(a)
            worst = max(worst, abs(radial))
    out.append(f"ring LED pads: largest radial offset {worst:.2f} (0.75 = pads along the ring, 2.7 = across it)")
    enc = next(f for f in fps.values() if f.GetValue() == "EE-SX1321")
    ex, ey = rot2(*D["enc_xy"], mr); cx, cy = to_panel(enc.GetPosition())
    p1 = to_panel(enc.FindPadByNumber("1").GetPosition()); p6 = to_panel(enc.FindPadByNumber("6").GetPosition())
    across = (p6[0] - p1[0], p6[1] - p1[1]); rad = (cx - ex, cy - ey)
    cosang = abs(across[0] * rad[0] + across[1] * rad[1]) / (math.hypot(*across) * math.hypot(*rad))
    out.append(f"encoder sensor: its arms (pad 1 to pad 6) lie {math.degrees(math.acos(min(1, cosang))):.1f} deg off the radius "
               "(0 = slot along the rim's tangent)")
    return out


BLOCK_COL = {"mcu": "#9ecae1", "link": "#c6dbef", "screen": "#6baed6", "debug": "#d9d9d9", "light": "#fdae6b", "adc": "#a1d99b",
             "halls": "#74c476", "encoder": "#c7e9c0", "motor": "#fc9272", "ring": "#fdd0a2", "rod": "#de2d26", "power": "#fee391",
             "cover": "#bdbdbd", "headers": "#969696"}


def picture(parts, placement, path, stats):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from shapely.geometry import Polygon
    fig = plt.figure(figsize=(15, 15.5), dpi=120)
    for k, face in enumerate(("F", "B")):
        ax = fig.add_axes([0.01 + k * 0.5, 0.05, 0.47, 0.86])
        g = R["board"]
        ax.add_patch(plt.Polygon(list(g.exterior.coords), fc="#f1f8e9", ec="#33691e", lw=0.8))
        for i in g.interiors:
            ax.add_patch(plt.Polygon(list(i.coords), fc="white", ec="#33691e", lw=0.5))
        key = "front" if face == "F" else "back"
        for n, m in R["occ"][key].items():
            if n.startswith(ELECTRICAL):
                continue
            for p in ([m] if m.geom_type == "Polygon" else list(m.geoms)):
                ax.add_patch(plt.Polygon(list(p.exterior.coords), fc="#eceff1", ec="#b0bec5", lw=0.3, alpha=0.8))
        for p in parts:
            x, y, s, rot = placement[p["ref"]]
            if s != face:
                continue
            x0, y0, x1, y1, pads = geometry(p["fp"], s, rot)
            ax.add_patch(plt.Rectangle((x + x0, -(y + y1)), x1 - x0, y1 - y0, fc=BLOCK_COL.get(p["block"], "#eee"),
                                       ec="#333", lw=0.4, alpha=0.95))
            for (px, py) in pads.values():
                ax.plot(x + px, -(y + py), ".", ms=1.2, color="#5d4037")
            if (x1 - x0) * (y1 - y0) > 3.0 or p["ref"][0] in "UJQY":
                ax.text(x, -y, p["ref"], fontsize=4.6, ha="center", va="center")
        b = g.bounds
        ax.set_xlim(b[0] - 1, b[2] + 1); ax.set_ylim(b[1] - 1, b[3] + 1); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title("FRONT (toward the panel)" if face == "F" else "BACK, seen through the board from the front", fontsize=11, loc="left")
    wl, ov, out, bad = stats
    fig.text(0.01, 0.975, f"Main board {PCB_VERSION}: first placement (model {R['D'].get('version', '?')})", fontsize=15, weight="bold", va="top")
    fig.text(0.01, 0.95, f"{len(parts)} parts; colour = circuit block; grey = what the mechanics take on that face; white = windows, "
             f"cut-outs, holes. Wirelength {wl:.0f} mm (half-perimeter); not legal: {', '.join(bad) if bad else 'none'}.",
             fontsize=10, va="top")
    hand = [plt.Rectangle((0, 0), 1, 1, fc=c) for c in BLOCK_COL.values()]
    fig.legend(hand, list(BLOCK_COL), loc="lower center", ncol=len(BLOCK_COL), fontsize=8.5, frameon=False)
    fig.savefig(path)


def main():
    global R
    ap = argparse.ArgumentParser(); ap.add_argument("room"); ap.add_argument("--iters", type=int, default=300000)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    R = pickle.load(open(a.room, "rb"))
    from shapely.ops import unary_union
    os.makedirs(OUT, exist_ok=True); os.makedirs(LIB_DIR, exist_ok=True)
    parts = design.build()
    fixed = fixed_parts(parts)
    for nm, fn in OWN.items():   # the board's own footprints, saved so the project opens on its own
        save_fp(LIB_DIR, _FP_CACHE.setdefault(nm, _load_fp(pcbnew.BOARD(), nm)))
    free = {}
    for face, key in (("F", "front"), ("B", "back")):
        mech = unary_union([g for n, g in R["occ"][key].items() if not n.startswith(ELECTRICAL)])
        free[face] = R["board"].difference(mech).buffer(-EDGE_KEEP)
    room = Room(free)
    placement, stats = run_placer(parts, fixed, room, a.iters, a.seed)
    placement.update(fixed)
    pcb = os.path.join(OUT, NAME + ".kicad_pcb")
    write_project(OUT, NAME, RULES, [(LIB, "${KIPRJMOD}/../" + LIB + ".pretty")], ())
    board, dropped = build(parts, placement)
    save_board(pcb, board)
    json.dump({r: list(v) for r, v in placement.items()}, open(os.path.join(HERE, "placement.json"), "w"), indent=0)
    picture(parts, placement, os.path.join(HERE, "placement.png"), stats)
    v, u, _txt = drc(pcb, os.path.join(OUT, "drc.rpt"))
    print("edge cuts: model holes drilled by footprints instead:", dropped)
    for line in checks(pcb, fixed):
        print(line)
    print(f"DRC: {v} violations, {u} unconnected (not routed yet)")


if __name__ == "__main__":
    main()
