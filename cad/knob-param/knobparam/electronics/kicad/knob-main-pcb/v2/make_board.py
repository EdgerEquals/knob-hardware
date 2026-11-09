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
K7_DIR = os.path.join(HERE, ".k7cache.pretty")   # KiCad 7 copies of the repo's footprints (scratch, not committed)
KLIB = "/usr/share/kicad/footprints"; REPO_LIB = os.path.join(KI, "footprints.pretty")
OUT = os.path.join(HERE, "kicad")
ORIGIN = (100.0, 100.0)
BT = 1.6
RULES = dict(clearance=0.1, track=0.127, min_track=0.1, via_d=0.45, via_drill=0.2, edge=0.25)
GRID = 0.1                     # mm, the placer's room raster
PLANE_LAYERS = (pcbnew.In1_Cu, pcbnew.In4_Cu)   # the two ground planes [Q45 = B]
EDGE_KEEP = 0.25               # courtyards this far inside the board edge, the windows and the cut-outs
POWER_W = {"GND": 0.0, "3V3": 0.15, "5V": 0.3, "VSYS": 0.5, "VM": 0.5, "RING_5V": 0.3, "RING_IN": 0.5, "VDDA": 0.5, "VREFP": 0.8}
# the parts the model draws itself and this board places as fixed parts: left out of the mechanical keep-out
ELECTRICAL = ("MCU ", "hall sensor", "power light VCSEL", "emitter RGB", "encoder sensor EE-SX1321")
# block zones [A, after docs/img/main-board-plan.png], panel frame (x0, y0, x1, y1) per face
Z = {
    "mcu": {"F": [(-13.0, 23.0, 13.0, 49.0)]},
    "link": {"F": [(-13.0, 23.0, 16.0, 49.0)]},
    "screen": {"F": [(4.0, 24.0, 16.5, 47.0)]},
    "debug": {"F": [(-16.5, 24.0, -6.0, 47.0)], "B": [(-16.5, 24.0, -6.0, 47.0)]},   # B: only for the Tag-Connect's holes
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


def _k7_copy(fn):
    """The repo's footprints.pretty files are KiCad 8+ (version 20241229: (property "Reference" ...), (fill yes/no)); KiCad 7's
    reader needs fp_text reference / value and fill solid / none. Same geometry, older spelling."""
    import re
    t = open(os.path.join(REPO_LIB, fn + ".kicad_mod")).read()
    t = re.sub(r"\(version \d+\)", "(version 20221018)", t, count=1)
    t = t.replace('(property "Reference" ', "(fp_text reference ").replace('(property "Value" ', "(fp_text value ")
    t = t.replace("(fill yes)", "(fill solid)").replace("(fill no)", "(fill none)")
    os.makedirs(K7_DIR, exist_ok=True)
    open(os.path.join(K7_DIR, fn + ".kicad_mod"), "w").write(t)


def save_fp_if_changed(fp):
    """Write a footprint to the board's library only if it changed (ignoring time stamps and the order of its lines): a re-run
    otherwise rewrites every file with new stamps."""
    import tempfile, shutil, re, glob
    tmp = tempfile.mkdtemp()
    save_fp(tmp, fp)
    norm = lambda t: sorted(re.sub(r"\((tstamp|uuid) [^)]*\)", "", ln).strip() for ln in t.splitlines())
    for f in glob.glob(os.path.join(tmp, "*.kicad_mod")):
        dst = os.path.join(LIB_DIR, os.path.basename(f))
        if not os.path.exists(dst) or norm(open(dst).read()) != norm(open(f).read()):
            shutil.copy(f, dst)
    shutil.rmtree(tmp)


def load_fp(board, name):
    if name not in _FP_CACHE:
        _FP_CACHE[name] = _load_fp(board, name)
    return _FP_CACHE[name].Duplicate().Cast()


def _load_fp(board, name):
    if name in OWN:
        f = OWN[name](board)
    else:
        lib, fn = name.split(":")
        path = os.path.join(KLIB, lib + ".pretty")
        if lib == "footprints":   # the repo's own, written in KiCad 8+ syntax: a KiCad 7 copy in this board's library
            path = K7_DIR; _k7_copy(fn)
        f = pcbnew.FootprintLoad(path, fn)
        assert f is not None, f"footprint {name} did not load"
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


def far_pads(name, side, rot, cache={}):
    """Boxes (KiCad local, about the part's origin) of what a part puts on its OTHER face: through-hole pads, NPTH holes, and
    pads on the far copper (the rod clamp's back pad). Parts there must keep off them."""
    key = (name, side, rot)
    if key in cache:
        return cache[key]
    b = _SCRATCH[0]; f = load_fp(b, name); b.Add(f); _KEEP.append(f)
    f.SetPosition(V(0, 0)); f.SetOrientationDegrees(rot)
    if side == "B":
        f.Flip(f.GetPosition(), False)
    far = pcbnew.F_Cu if side == "B" else pcbnew.B_Cu
    out = []
    for p in f.Pads():
        if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) or p.IsOnLayer(far):
            bb = p.GetBoundingBox()
            out.append((pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())))
    cache[key] = out
    return out


def turned_courtyard(name, side, rot, row=0.5):
    """A part turned off the 90° grid, as horizontal strips (KiCad local, about its origin) covering its real courtyard: the
    placer's boxes are axis-aligned, and the bounding box of a ring LED at 30° is more than twice its courtyard."""
    x0, y0, x1, y1, _ = geometry(name, "F", 0)
    t = math.radians(rot if side == "F" else -rot)   # Flip(False) mirrors about the horizontal axis: rot -> -rot
    c, s_ = math.cos(t), math.sin(t)
    pts = [(x * c + y * s_, -x * s_ + y * c) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]   # CCW on screen, y down
    bx = geometry(name, side, rot)
    assert abs(min(p[0] for p in pts) - bx[0]) < 0.05 and abs(min(p[1] for p in pts) - bx[1]) < 0.05, (name, rot, pts, bx[:4])
    ys = [p[1] for p in pts]; out = []
    yy = min(ys)
    while yy < max(ys) - 1e-9:
        ya, yb = yy, min(yy + row, max(ys))
        xs = []
        for (ax, ay), (cx, cy) in zip(pts, pts[1:] + pts[:1]):   # the polygon's x extent over this row (edges and corners)
            for yv in (ya, yb):
                if (ay - yv) * (cy - yv) <= 0 and ay != cy:
                    xs.append(ax + (yv - ay) * (cx - ax) / (cy - ay))
            if ya <= ay <= yb:
                xs.append(ax)
        out.append((min(xs), ya, max(xs), yb))
        yy = yb
    return out


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

    def count(self, k, x0, y0, x1, y1):
        """(cells of this rectangle the zone allows, cells of the rectangle): cells off the raster count as not allowed."""
        s = self.sat[k]
        i0 = int(round((x0 - self.x0) / GRID)); i1 = int(round((x1 - self.x0) / GRID))
        j0 = int(round((y0 - self.y0) / GRID)); j1 = int(round((y1 - self.y0) / GRID))
        tot = max(i1 - i0, 0) * max(j1 - j0, 0)
        i0, i1 = min(max(i0, 0), self.nx), min(max(i1, 0), self.nx); j0, j1 = min(max(j0, 0), self.ny), min(max(j1, 0), self.ny)
        if i1 <= i0 or j1 <= j0:
            return 0, tot
        return int(s[j1, i1] - s[j0, i1] - s[j1, i0] + s[j0, i0]), tot

    def fits(self, k, x0, y0, x1, y1):
        ok, tot = self.count(k, x0, y0, x1, y1)
        return ok >= tot


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
        ok, tot = self.room.count(k, x0, y0, x1, y1)
        return (tot - ok) * GRID * GRID * 4.0


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
            g = geometry(p["fp"], s, rot)
            if abs(rot / 90.0 - round(rot / 90.0)) > 1e-6:   # turned off the grid: its true courtyard as strips, not its bounding box
                strips = turned_courtyard(p["fp"], s, rot)
                g = (-0.01, -0.01, 0.01, 0.01, g[4])
                for k, (a0, b0, a1, b1) in enumerate(strips):
                    items.append(dict(ref=f"KEEP_{r}_cy{k}", geoms={(s, 0): (a0, b0, a1, b1, {})}, fixed=(x, y, s, 0)))
            items.append(dict(ref=r, geoms={(s, rot): g}, fixed=(x, y, s, rot)))
            for k, (a0, b0, a1, b1) in enumerate(far_pads(p["fp"], s, rot)):   # its holes and back pads on the other face
                o = "B" if s == "F" else "F"
                items.append(dict(ref=f"KEEP_{r}_{k}", geoms={(o, 0): (a0 - 0.3, b0 - 0.3, a1 + 0.3, b1 + 0.3, {})}, fixed=(x, y, o, 0)))
            continue
        zone = p["block"]
        faces = [p["face"]] if p["face"] in Z[zone] else list(Z[zone])   # the netlist's face where the zone has it
        if r == "U1":   # the H743: its centre is the model's (to 0.05), its quarter turn is free unless the pin map set it
            mx, my = L(*R["D"]["mcu"]["xy"])
            rots = [int(design.PINMAP["mcu_rot"]) % 360] if "mcu_rot" in design.PINMAP else [0, 90, 180, 270]
            g = {("F", rot): geometry(p["fp"], "F", rot) for rot in rots}
            reg = {"F": [(mx - 8.8, my - 8.8, mx + 8.8, my + 8.8)]}
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
    # decoupling: each capacitor to a pin of the same supply on the part with three or more pins just before it, taking that part's
    # pins of the supply in turn (the H743's five 100 nF go one to each VDD pin, its two 2.2 uF one to each VCAP)
    last = None; turn = {}
    for p in parts:
        if len([v for v in p["pins"].values() if v]) >= 3:
            last = p
        if p["ref"][0] == "C" and "GND" in p["pins"].values() and last is not None:
            sup = [n for n in p["pins"].values() if n != "GND"][0]
            ic = sorted([k for k, v in last["pins"].items() if v == sup], key=lambda k: int(k) if k.isdigit() else 0)
            if ic:
                k = turn.get((last["ref"], sup), 0); turn[(last["ref"], sup)] = k + 1
                netlist.append((2.5, [(p["ref"], [q for q, v in p["pins"].items() if v == sup][0]), (last["ref"], ic[k % len(ic)])]))
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
    return {k: v for k, v in pl.result().items() if not k.startswith("KEEP_")}, (wl, ov, out, bad)


def place_debug(parts, room, fixed):
    """The Tag-Connect pads (J4) have NPTH locating holes through the board: a spot where its courtyard fits the front's free room
    and its holes (+0.3) the back's, nearest the plan's (-11.9, 32) [A]."""
    p = next(q for q in parts if q["ref"] == "J4")
    kf, kb = room.key("debug", "F"), room.key("debug", "B")
    tx, ty = L(-11.9, 32.0); best = None
    for rot in (0, 90, 180, 270):
        x0, y0, x1, y1, _ = geometry(p["fp"], "F", rot); holes = far_pads(p["fp"], "F", rot)
        for i in range(-60, 61):
            for j in range(-90, 91):
                x, y = tx + i * 0.1, ty + j * 0.1
                if not room.fits(kf, x + x0, y + y0, x + x1, y + y1):
                    continue
                if not all(room.fits(kb, x + h0 - 0.3, y + h1 - 0.3, x + h2 + 0.3, y + h3 + 0.3) for h0, h1, h2, h3 in holes):
                    continue
                d = math.hypot(x - tx, y - ty)
                if best is None or d < best[0]:
                    best = (d, x, y, rot)
    assert best, "no room for the Tag-Connect pads in the debug zone"
    fixed["J4"] = (round(best[1], 2), round(best[2], 2), "F", best[3])
    return best


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


def edge_polygon():
    """The board as drawn on Edge.Cuts (panel frame): the room map's board less the holes a footprint drills itself (the header
    pins' holes are plated holes of their pads, not cut-outs)."""
    from shapely.geometry import Polygon
    skip = footprint_holes(None)
    keep = [h for h in R["board"].interiors
            if not (any(math.hypot(Polygon(h).centroid.x - x, Polygon(h).centroid.y - y) < 0.15 for x, y in skip) and Polygon(h).area < 9.0)]
    return Polygon(R["board"].exterior.coords, [h.coords for h in keep])


def build(parts, placement):
    from shapely.geometry import Polygon, Point
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings(); ds.SetBoardThickness(mm(BT)); ds.SetCopperLayerCount(6)
    ds.m_CopperEdgeClearance = mm(RULES["edge"])
    for lay in PLANE_LAYERS:   # Q45 = B [Ed 9 Nov 09:24]: front, In1 ground, In2, In3, In4 ground, back
        board.SetLayerType(lay, pcbnew.LT_POWER)
    edge = edge_polygon()
    loops = [list(edge.exterior.coords)] + [list(h.coords) for h in edge.interiors]
    dropped = len(R["board"].interiors) - len(edge.interiors)
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


# ------------------------------------------------------------------ routing trial (the layer-count question)
FREEROUTING = os.environ.get("FREEROUTING_JAR", "/home/claude/tools/freerouting-1.9.0.jar")
# the link flex's lines as one planned ribbon [Ed 9 Nov 09:31 "Y"]: routed first, each group on its own layers, then locked
FLEX_CLASSES = [("FlexAnalog", 0.15, 0.127, ["CV_IN1_L", "CV_IN2_L", "CV_IN3_L", "AUDIO_IN_L", "AUDIO_OUT", "AGND_SENSE_L"], ["In3.Cu"]),
                ("FlexSPI", 0.1, 0.127, ["SCK_L", "MOSI_L", "CS_DAC", "CS_OLED", "OLED_DC", "OLED_RES"], ["F.Cu"]),
                ("FlexBus", 0.1, 0.127, ["I2C_SCL", "I2C_SDA", "IO_INT", "MIDI_TX", "USB_DP", "USB_DM"], ["B.Cu"])]
CLASSES = [(n, c, w, nets) for n, c, w, nets, _l in FLEX_CLASSES] + [("GND", 0.1, 0.25, ["GND"]),   # its own class so the router's -inc GND leaves ground to the planes and fanout vias
           ("Power", 0.1, 0.4, ["VSYS", "5V", "VM", "RING_IN", "RING_5V", "MOT_A", "MOT_B"]),
           ("Supply", 0.1, 0.25, ["3V3", "VDDA", "VREFP", "VCAP", "ROD"])]


KEEP = []   # board items taken off a board: KiCad 7's python loses the board's track list once their wrappers are freed


def _pad_rects(board):
    out = []
    for f in board.GetFootprints():
        for p in f.Pads():
            if not p.IsOnCopperLayer():   # paste-only apertures (an exposed pad's paste windows): no copper
                continue
            bb = p.GetBoundingBox()
            lay = ({"F"} if p.IsOnLayer(pcbnew.F_Cu) and not p.IsOnLayer(pcbnew.B_Cu) else
                   {"B"} if p.IsOnLayer(pcbnew.B_Cu) and not p.IsOnLayer(pcbnew.F_Cu) else {"F", "B", "I"})
            out.append((lay, pcbnew.ToMM(bb.GetLeft()) - ORIGIN[0], pcbnew.ToMM(bb.GetTop()) - ORIGIN[1],
                        pcbnew.ToMM(bb.GetRight()) - ORIGIN[0], pcbnew.ToMM(bb.GetBottom()) - ORIGIN[1], p.GetNetname(), _pad_key(p)))
    return out


def _pad_key(p):
    """A pad's identity: SWIG gives a new python object for the same pad on every call, so `is` never matches."""
    return (p.GetParent().GetReference(), p.GetNumber(), p.GetPosition().x, p.GetPosition().y)


def _rect_dist(px, py, x0, y0, x1, y1):
    return math.hypot(max(x0 - px, 0.0, px - x1), max(y0 - py, 0.0, py - y1))


def fanout_gnd(board, via_d=0.45, via_drill=0.2, clr=0.13, width=0.25, skip_done=False):
    """A via to the In1 ground plane beside every ground SMD pad (in the middle of an exposed pad), with a short track on the pad's
    face, clear of every pad, the other vias, the edge and the holes (as the jack power board's fanout_gnd)."""
    from shapely.geometry import Point
    inside = R["board"].buffer(-(via_d / 2 + RULES["edge"] + 0.02))
    inside_t = {}   # where a short track of this width may run: its copper keeps the edge rule too (C12's ran 0.2 from the edge)
    rects = _pad_rects(board); gnd = board.FindNet("GND"); n_ok = n_fail = 0
    vias = [(pcbnew.ToMM(v.GetPosition().x) - ORIGIN[0], pcbnew.ToMM(v.GetPosition().y) - ORIGIN[1])   # vias already there
            for v in board.GetTracks() if v.GetClass() == "PCB_VIA"]
    holes = []   # every drilled hole (PTH, NPTH): the via's drill keeps the hole rule (0.2) + 0.03 to them
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                holes.append((pcbnew.ToMM(p.GetPosition().x) - ORIGIN[0], pcbnew.ToMM(p.GetPosition().y) - ORIGIN[1],
                              pcbnew.ToMM(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2))
    segs = []   # tracks already on the board (the ribbon): (layer, x0, y0, x1, y1, half width), KiCad local
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA" or t.GetNetname() == "GND":   # ground copper may touch ground
            continue
        segs.append((t.GetLayer(), pcbnew.ToMM(t.GetStart().x) - ORIGIN[0], pcbnew.ToMM(t.GetStart().y) - ORIGIN[1],
                     pcbnew.ToMM(t.GetEnd().x) - ORIGIN[0], pcbnew.ToMM(t.GetEnd().y) - ORIGIN[1], pcbnew.ToMM(t.GetWidth()) / 2))

    def seg_d(px, py, x0, y0, x1, y1):
        vx, vy = x1 - x0, y1 - y0; l2 = vx * vx + vy * vy or 1e-12
        u = max(0.0, min(1.0, ((px - x0) * vx + (py - y0) * vy) / l2))
        return math.hypot(px - x0 - u * vx, py - y0 - u * vy)
    done, failed = [], []
    order = []   # exposed pads first (a via in the pad), so a neighbouring pin's via does not take its spot
    for f in board.GetFootprints():
        cx, cy = pcbnew.ToMM(f.GetPosition().x) - ORIGIN[0], pcbnew.ToMM(f.GetPosition().y) - ORIGIN[1]
        for p in f.Pads():
            if p.GetNetname() == "GND" and p.GetAttribute() in (pcbnew.PAD_ATTRIB_SMD, pcbnew.PAD_ATTRIB_CONN):   # CONN: the Tag-Connect's pads
                if skip_done and any(t.GetNetname() == "GND" and (p.HitTest(t.GetStart()) or p.HitTest(t.GetEnd()))
                                     for t in board.GetTracks()):
                    done.append(p); continue   # already has its via (finishing a routed board)
                w_, h_ = pcbnew.ToMM(p.GetBoundingBox().GetWidth()), pcbnew.ToMM(p.GetBoundingBox().GetHeight())
                order.append((0 if w_ * h_ >= 1.0 and min(w_, h_) >= 0.85 else 1, f, cx, cy, p))
    order.sort(key=lambda o: o[0])
    for _ep, f, cx, cy, p in order:
        if True:
            side = "B" if p.IsOnLayer(pcbnew.B_Cu) else "F"
            px, py = pcbnew.ToMM(p.GetPosition().x) - ORIGIN[0], pcbnew.ToMM(p.GetPosition().y) - ORIGIN[1]
            w, h = pcbnew.ToMM(p.GetBoundingBox().GetWidth()), pcbnew.ToMM(p.GetBoundingBox().GetHeight())
            if w * h >= 1.0 and min(w, h) >= 0.85 and math.hypot(px - cx, py - cy) < 0.3:   # an exposed pad: the via in it
                cands = [(px, py)]
            else:
                ang0 = math.atan2(py - cy, px - cx) if math.hypot(px - cx, py - cy) > 0.05 else 0.0
                cands = []
                for dist in (0.45, 0.6, 0.8, 1.0, 1.25, 1.5, 1.8, 2.2, 2.6, 3.0):
                    for k in range(16):
                        a_ = ang0 + (k // 2 + 1) * (math.pi / 8) * (1 if k % 2 else -1) if k else ang0
                        cands.append((px + (w / 2 + dist) * math.cos(a_) if abs(math.cos(a_)) > 0.7 else px + dist * math.cos(a_),
                                      py + (h / 2 + dist) * math.sin(a_) if abs(math.sin(a_)) > 0.7 else py + dist * math.sin(a_)))
            placed = False; me = _pad_key(p); tw = min(width, w, h)
            if tw not in inside_t:
                inside_t[tw] = R["board"].buffer(-(tw / 2 + RULES["edge"] + 0.02))
            for vx, vy in cands:
                if not inside.contains(Point(vx, -vy)):
                    continue
                if any(not inside_t[tw].contains(Point(px + (vx - px) * t_ / 20, -(py + (vy - py) * t_ / 20))) for t_ in range(1, 20)
                       if not (abs((vx - px) * t_ / 20) <= w / 2 and abs((vy - py) * t_ / 20) <= h / 2)):
                    continue   # the track outside its pad must keep the edge rule
                ok = True
                for lay, x0, y0, x1, y1, n, pp in rects:
                    if pp == me:
                        continue
                    d = _rect_dist(vx, vy, x0, y0, x1, y1)
                    if n == "GND":
                        if d < via_d / 2 + 0.02:
                            ok = False; break
                        continue
                    if d < via_d / 2 + clr:
                        ok = False; break
                    if side in lay and (vx, vy) != (px, py):   # the short track, outside its own pad (a narrow pad's track is as wide as it)
                        tw = min(width, w, h)
                        for t in range(1, 21):
                            sx, sy = px + (vx - px) * t / 20, py + (vy - py) * t / 20
                            if abs(sx - px) <= w / 2 and abs(sy - py) <= h / 2:
                                continue
                            if _rect_dist(sx, sy, x0, y0, x1, y1) < tw / 2 + clr:
                                ok = False; break
                        if not ok:
                            break
                if ok and any(math.hypot(qx - vx, qy - vy) < via_d + 0.15 for qx, qy in vias):
                    ok = False
                if ok and any(math.hypot(hx - vx, hy - vy) < via_d / 2 + hr + 0.23 for hx, hy, hr in holes):
                    ok = False   # the hole rule is copper to hole: the via's ring, not its drill
                if ok and any(seg_d(vx, vy, x0, y0, x1, y1) < via_d / 2 + clr + hw for _l, x0, y0, x1, y1, hw in segs):
                    ok = False   # the via goes through every layer: clear of the ribbon on all of them
                if ok and (vx, vy) != (px, py):
                    lay_id = pcbnew.B_Cu if side == "B" else pcbnew.F_Cu
                    tw = min(width, w, h)
                    for t_ in range(0, 21):
                        sx, sy = px + (vx - px) * t_ / 20, py + (vy - py) * t_ / 20
                        if any(l == lay_id and seg_d(sx, sy, x0, y0, x1, y1) < tw / 2 + clr + hw for l, x0, y0, x1, y1, hw in segs):
                            ok = False; break
                if ok:
                    v = pcbnew.PCB_VIA(board); v.SetPosition(P(vx, vy)); v.SetWidth(mm(via_d)); v.SetDrill(mm(via_drill))
                    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(gnd); v.SetLocked(True); board.Add(v)
                    if (vx, vy) != (px, py):
                        tr = pcbnew.PCB_TRACK(board); tr.SetStart(P(px, py)); tr.SetEnd(P(vx, vy)); tr.SetWidth(mm(min(width, w, h)))
                        tr.SetLayer(pcbnew.B_Cu if side == "B" else pcbnew.F_Cu); tr.SetNet(gnd); tr.SetLocked(True); board.Add(tr)
                    vias.append((vx, vy)); placed = True; n_ok += 1
                    break
            if placed:
                done.append(p)
            else:
                failed.append(p)
    # no room for a via (C12 by the edge): a straight track on the pad's face to the nearest ground pad that has one
    for p in failed:
        side = pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Cu
        px, py = pcbnew.ToMM(p.GetPosition().x) - ORIGIN[0], pcbnew.ToMM(p.GetPosition().y) - ORIGIN[1]
        w, h = pcbnew.ToMM(p.GetBoundingBox().GetWidth()), pcbnew.ToMM(p.GetBoundingBox().GetHeight())
        near = []
        for q in done:
            if not q.IsOnLayer(side):
                continue
            qx, qy = pcbnew.ToMM(q.GetPosition().x) - ORIGIN[0], pcbnew.ToMM(q.GetPosition().y) - ORIGIN[1]
            if math.hypot(qx - px, qy - py) < 3.0:
                near.append((math.hypot(qx - px, qy - py), q, qx, qy))
        joined = False
        for _d, q, qx, qy in sorted(near, key=lambda o: o[0]):
            qw, qh = pcbnew.ToMM(q.GetBoundingBox().GetWidth()), pcbnew.ToMM(q.GetBoundingBox().GetHeight())
            tw = min(width, w, h, qw, qh); mine = (_pad_key(p), _pad_key(q)); ok = True
            area = R["board"].buffer(-(tw / 2 + RULES["edge"] + 0.02))
            for k in range(1, 40):
                sx, sy = px + (qx - px) * k / 40, py + (qy - py) * k / 40
                if (abs(sx - px) <= w / 2 and abs(sy - py) <= h / 2) or (abs(sx - qx) <= qw / 2 and abs(sy - qy) <= qh / 2):
                    continue
                if not area.contains(Point(sx, -sy)):
                    ok = False; break
                if any(n != "GND" and pk not in mine and ("F" if side == pcbnew.F_Cu else "B") in lay and
                       _rect_dist(sx, sy, x0, y0, x1, y1) < tw / 2 + clr for lay, x0, y0, x1, y1, n, pk in rects):
                    ok = False; break
                if any(l == side and seg_d(sx, sy, x0, y0, x1, y1) < tw / 2 + clr + hw for l, x0, y0, x1, y1, hw in segs):
                    ok = False; break
                if any(math.hypot(hx - sx, hy - sy) < tw / 2 + hr + 0.23 for hx, hy, hr in holes):
                    ok = False; break
            if ok:
                tr = pcbnew.PCB_TRACK(board); tr.SetStart(P(px, py)); tr.SetEnd(P(qx, qy)); tr.SetWidth(mm(tw)); tr.SetLayer(side)
                tr.SetNet(gnd); tr.SetLocked(True); board.Add(tr); joined = True; n_ok += 1
                print(f"  {p.GetParent().GetReference()} pad {p.GetNumber()}: no room for a via, joined to "
                      f"{q.GetParent().GetReference()} pad {q.GetNumber()} ({_d:.2f} mm)")
                break
        n_fail += not joined
    return n_ok, n_fail


def _dsn_inset(dsn, d):
    """Move the .dsn's board boundary in by d (Freerouting keeps only its own clearance to it), with shapely: kicad7_tools' corner
    intersection inset folds over on this outline's short arc segments (Freerouting then reported a winding error and hung)."""
    import re
    from shapely.geometry import Polygon
    txt = open(dsn).read()
    m = re.search(r"\(boundary\s*\(path pcb 0\s+([-\d\s.]+)\)", txt)
    nums = [float(v) for v in m.group(1).split()]
    k = 1000.0 if re.search(r"\(unit um\)", txt) else 1.0
    g = Polygon(list(zip(nums[0::2], nums[1::2]))).buffer(-d * k, join_style=2)
    if g.geom_type != "Polygon":
        g = max(g.geoms, key=lambda q: q.area)
    body = "  ".join(f"{x:.1f} {y:.1f}" for x, y in g.exterior.coords)
    txt = txt[:m.start(1)] + body + txt[m.end(1):]

    def grow(mm_):   # the board's holes and windows (keepouts) grown by the same d, so tracks keep the edge rule there too
        nums = [float(v) for v in mm_.group(1).split()]
        q = Polygon(list(zip(nums[0::2], nums[1::2]))).buffer(d * k, join_style=1, resolution=4)
        return '(keepout "" (polygon signal 0  ' + "  ".join(f"{x:.1f} {y:.1f}" for x, y in q.exterior.coords) + ")"
    txt = re.sub(r'\(keepout "" \(polygon signal 0\s+([-\d\s.]+)\)', grow, txt)
    open(dsn, "w").write(txt)


def _dsn_layers(dsn, layers):
    """Give some net classes their own layers in the .dsn ((circuit (use_layer ...)), Specctra), so the router keeps them there."""
    import re
    txt = open(dsn).read()
    for cls, lays in layers.items():
        m = re.search(r"\(class " + re.escape(cls) + r"\b.*?\(circuit\s*\n?\s*\(use_via [^)]*\)", txt, re.S)
        if m:
            txt = txt[:m.end()] + "\n        (use_layer " + " ".join(lays) + ")" + txt[m.end():]
        else:
            print("no class in the dsn:", cls)
    open(dsn, "w").write(txt)


def _route(tp, passes, timeout, ignore=("GND",), layers=None, tag="", resume=False):
    """Freerouting 1.9.0 on the board (ignored classes left alone, e.g. ground to the planes); imports the session without
    doubling what was already there and locked; returns (unconnected, violations) from KiCad's DRC."""
    import subprocess, kicad7_tools as kt
    tp = os.path.abspath(tp)
    dsn = tp.replace(".kicad_pcb", ".dsn"); ses = tp.replace(".kicad_pcb", ".ses")
    kt._fresh("dsn", tp, dsn)
    _dsn_inset(dsn, RULES["edge"] - 0.1 + 0.03)   # the router keeps only its 0.1 clearance to these (0.22-0.249 seen with 0.105)
    if layers:
        _dsn_layers(dsn, layers)
    log = open(tp.replace(".kicad_pcb", f"_freerouting{tag}.txt"), "w")
    try:
        subprocess.run(["xvfb-run", "-a", "java", "-jar", FREEROUTING, "-de", dsn, "-do", ses, "-mp", str(passes), "-inc", ",".join(ignore)],
                       check=True, timeout=timeout, stdout=log, stderr=subprocess.STDOUT, cwd=os.path.dirname(tp))
    except subprocess.TimeoutExpired:
        print("router timed out with no session saved"); return None
    b = pcbnew.LoadBoard(tp)
    key = lambda t: (t.GetClass(), t.GetNetname(), t.GetLayer(), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y)
    if resume:   # the router was free to move the unlocked tracks: the session has what it kept, so the old ones go
        for t in [t for t in b.GetTracks() if not t.IsLocked()]:
            b.Remove(t); KEEP.append(t)
    had = {key(t) for t in b.GetTracks()}
    print("imported", kt.import_ses(b, ses))
    seen = set(); dup = 0
    for t in list(b.GetTracks()):
        k = key(t)
        if not t.IsLocked() and (k in had or k in seen):
            b.Remove(t); KEEP.append(t); dup += 1
        seen.add(k)
    if dup:
        print("dropped", dup, "copies of what was already there")
    save_board(tp, b)
    nv, nu, _ = kt.drc(tp)
    return nu, nv


def trial_planes(tp, planes, log=print):
    """Fill the trial's ground planes (In1, and In4 on the two-plane stack) over the whole board and count what is left, so ground
    pads joined only through their vias read as joined."""
    import re, kicad7_tools as kt
    from collections import Counter
    b = pcbnew.LoadBoard(tp); gnd = b.FindNet("GND")
    for k in planes:
        z = pcbnew.ZONE(b); z.SetLayer({1: pcbnew.In1_Cu, 2: pcbnew.In2_Cu, 3: pcbnew.In3_Cu, 4: pcbnew.In4_Cu}[k]); z.SetNet(gnd)
        z.SetLocalClearance(mm(0.2)); z.SetMinThickness(mm(0.15)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        ol = z.Outline(); ol.NewOutline()
        for x, y in R["board"].exterior.coords:
            ol.Append(mm(ORIGIN[0] + x), mm(ORIGIN[1] - y))
        b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); save_board(tp, b)
    nv, nu, txt = kt.drc(tp)
    left = Counter(re.findall(r"\[unconnected_items\][^\n]*\n[^\n]*\n[^\n]*\[([^\]]+)\]", txt))
    kinds = Counter(re.findall(r"^\[(\w+)\]", txt, re.M))
    vias = sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_VIA")
    log(f"with the planes: unconnected {nu}, violations {nv}, vias {vias}; {dict(kinds)}")
    log("left: " + ", ".join(f"{n} {c}" for n, c in left.most_common()))
    return nu, nv, vias, left


def add_planes(board):
    """The two ground planes, over the whole board (KiCad keeps them off the windows, cut-outs and holes by the edge rule)."""
    gnd = board.FindNet("GND")
    for lay in PLANE_LAYERS:
        z = pcbnew.ZONE(board); z.SetLayer(lay); z.SetNet(gnd); z.SetLocalClearance(mm(0.2)); z.SetMinThickness(mm(0.15))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL); z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetZoneName("GND " + board.GetLayerName(lay))
        ol = z.Outline(); ol.NewOutline()
        for x, y in R["board"].exterior.coords:
            ol.Append(mm(ORIGIN[0] + x), mm(ORIGIN[1] - y))
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


def trim_dangling(board, locked_too=False):
    """Remove track ends that lead nowhere (the router joined a ribbon line part way along, leaving the rest as a stub), segment by
    segment until none is left. An end is joined if a pad on that layer covers it, a via sits on it, or another track of the net
    touches it. Worked out on a snapshot, the board's items removed once at the end."""
    items = [t for t in board.GetTracks() if t.GetClass() != "PCB_VIA"]
    S = [dict(i=k, lay=t.GetLayer(), net=t.GetNetCode(), a=(t.GetStart().x, t.GetStart().y), b=(t.GetEnd().x, t.GetEnd().y),
              hw=t.GetWidth() / 2, locked=t.IsLocked()) for k, t in enumerate(items)]
    V = [(v.GetNetCode(), v.GetPosition().x, v.GetPosition().y, v.GetWidth() / 2) for v in board.GetTracks() if v.GetClass() == "PCB_VIA"]
    PD = [(p, p.GetNetCode()) for f in board.GetFootprints() for p in f.Pads()]
    pad_hit = {}

    def on_seg(q, s_):
        (ax, ay), (bx, by) = s_["a"], s_["b"]; vx, vy = bx - ax, by - ay; l2 = vx * vx + vy * vy or 1
        u = max(0.0, min(1.0, ((q[0] - ax) * vx + (q[1] - ay) * vy) / l2))
        return math.hypot(q[0] - ax - u * vx, q[1] - ay - u * vy) <= s_["hw"]

    alive = {s_["i"] for s_ in S}
    while True:
        drop = []
        for s_ in S:
            if s_["i"] not in alive or (s_["locked"] and not locked_too):
                continue
            for q in (s_["a"], s_["b"]):
                if any(o["i"] in alive and o["i"] != s_["i"] and o["lay"] == s_["lay"] and o["net"] == s_["net"] and on_seg(q, o) for o in S):
                    continue
                if any(n == s_["net"] and math.hypot(x - q[0], y - q[1]) <= r for n, x, y, r in V):
                    continue
                key = (s_["lay"], s_["net"], q)
                if key not in pad_hit:
                    pad_hit[key] = any(n == s_["net"] and p.IsOnLayer(s_["lay"]) and p.HitTest(pcbnew.VECTOR2I(int(q[0]), int(q[1])))
                                       for p, n in PD)
                if pad_hit[key]:
                    continue
                drop.append(s_["i"]); break
        if not drop:
            break
        alive -= set(drop)
    gone = [items[k] for k in range(len(items)) if k not in alive]
    for t in gone:
        board.Remove(t); KEEP.append(t)
    return len(gone)


def route_board(passes, timeout):
    """The real thing on 6 layers: ground fanned out to the planes, the rest by Freerouting with the edge rule kept at windows and
    holes, the planes filled, KiCad's DRC. Works on the placed board in place (re-run the placement to start over)."""
    import re, kicad7_tools as kt
    from collections import Counter
    pcb = os.path.join(OUT, NAME + ".kicad_pcb")
    write_project(OUT, NAME, RULES, [(LIB, "${KIPRJMOD}/../" + LIB + ".pretty")], CLASSES)
    import shutil
    shutil.copy(os.path.join(OUT, "placed.kicad_pcb"), pcb)   # start from the placed board: the ribbon and its In2 rule area, no routes
    b = pcbnew.LoadBoard(pcb)
    print("ribbon laid again (old tracks, new items):", refresh_ribbons(b))
    print("ground vias (placed, no room):", fanout_gnd(b, skip_done=True))
    laid, failed = preroute(b)
    print("laid before the router:\n  " + "\n  ".join(laid)); print("not laid:", failed or "none")
    save_board(pcb, b)
    res = _route(pcb, passes=passes, timeout=timeout)
    print("first pass:", res)
    # finishing pass: everything routed so far fixed, the router only completes what is left
    b = pcbnew.LoadBoard(pcb); print("dangling track ends trimmed:", trim_dangling(b))
    for t in b.GetTracks():
        t.SetLocked(True)
    save_board(pcb, b)
    res = _route(pcb, passes=max(20, passes // 2), timeout=timeout, tag="_finish")
    print("finishing pass:", res)
    b = pcbnew.LoadBoard(pcb); print("dangling track ends trimmed:", trim_dangling(b)); add_planes(b); save_board(pcb, b)
    nv, nu, txt = kt.drc(pcb, os.path.join(OUT, "drc.rpt"))
    left = Counter(re.findall(r"\[unconnected_items\][^\n]*\n[^\n]*\n[^\n]*\[([^\]]+)\]", txt))
    kinds = Counter(re.findall(r"^\[(\w+)\]", txt, re.M))
    vias = sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_VIA")
    print(f"routed: unconnected {nu}, violations {nv}, vias {vias}; {dict(kinds)}")
    print("left: " + ", ".join(f"{n} {c}" for n, c in left.most_common()))


def finish_route(passes, timeout):
    """Finish a routed board: start again from the placed board (ribbon, In2 rule area), bring the routed copper across with the
    ground fan-out and the ribbon fixed and the router's own tracks free, drop fan-out tracks that break the edge rule, add the
    ground vias still missing, and let the router complete what is left, ripping up its own tracks where it needs to."""
    import re, shutil, kicad7_tools as kt
    from collections import Counter
    from shapely.geometry import Point
    pcb = os.path.join(OUT, NAME + ".kicad_pcb"); routed = os.path.join(OUT, "routed_prev.kicad_pcb")
    shutil.copy(pcb, routed)
    write_project(OUT, NAME, RULES, [(LIB, "${KIPRJMOD}/../" + LIB + ".pretty")], CLASSES)
    old = pcbnew.LoadBoard(routed); b = pcbnew.LoadBoard(os.path.join(OUT, "placed.kicad_pcb"))
    from shapely.geometry import LineString
    key = lambda t: (t.GetClass(), t.GetNetname(), t.GetLayer(), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y)
    loc = lambda v: (pcbnew.ToMM(v.x) - ORIGIN[0], pcbnew.ToMM(v.y) - ORIGIN[1])

    def shape(t):   # (layer or None for a via, copper outline), KiCad local mm
        if t.GetClass() == "PCB_VIA":
            return None, Point(*loc(t.GetPosition())).buffer(pcbnew.ToMM(t.GetWidth()) / 2, 12)
        return t.GetLayer(), LineString([loc(t.GetStart()), loc(t.GetEnd())]).buffer(pcbnew.ToMM(t.GetWidth()) / 2, 8)

    def copy(t, locked):
        if t.GetClass() == "PCB_VIA":
            n = pcbnew.PCB_VIA(b); n.SetPosition(t.GetPosition()); n.SetWidth(t.GetWidth()); n.SetDrill(t.GetDrillValue())
            n.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        else:
            n = pcbnew.PCB_TRACK(b); n.SetStart(t.GetStart()); n.SetEnd(t.GetEnd()); n.SetWidth(t.GetWidth()); n.SetLayer(t.GetLayer())
        n.SetNet(b.FindNet(t.GetNetname())); n.SetLocked(locked); b.Add(n)
    have = {key(t) for t in b.GetTracks()}
    # 1. the ground fan-out, fixed; tracks whose copper comes within the edge rule go with their via (the pad is done again)
    for t in old.GetTracks():
        if t.GetNetname() == "GND" and key(t) not in have:
            copy(t, True)
    bad = []
    for t in b.GetTracks():
        if t.GetNetname() != "GND" or t.GetClass() == "PCB_VIA":
            continue
        hw = pcbnew.ToMM(t.GetWidth()) / 2; ok_area = R["board"].buffer(-(hw + RULES["edge"] - 0.005))
        (x0, y0), (x1, y1) = [(pcbnew.ToMM(v.x) - ORIGIN[0], -(pcbnew.ToMM(v.y) - ORIGIN[1])) for v in (t.GetStart(), t.GetEnd())]
        if any(not ok_area.contains(Point(x0 + (x1 - x0) * k / 10, y0 + (y1 - y0) * k / 10)) for k in range(1, 11)):
            bad.append(t)
    for t in bad:
        for v in [v for v in b.GetTracks() if v.GetClass() == "PCB_VIA" and v.GetNetname() == "GND" and
                  (v.GetPosition() == t.GetEnd() or v.GetPosition() == t.GetStart())]:
            b.Remove(v); KEEP.append(v)
        b.Remove(t); KEEP.append(t)
    print(f"fan-out tracks off for the edge rule: {len(bad)}")
    # 2. the ground pads still without a via, with the router's copper not there yet (it gives way, step 3)
    before = {key(t) for t in b.GetTracks()}
    print("ground vias added (placed, no room):", fanout_gnd(b, skip_done=True))
    new = [shape(t) for t in b.GetTracks() if key(t) not in before]
    print("tiny tracks dropped:", drop_tiny(b))
    # 3. the router's copper, free to move; what now clashes with the new fan-out is left out for the router to redo
    n_copy = n_drop = 0
    for t in old.GetTracks():
        if t.GetNetname() == "GND" or key(t) in have:
            continue
        lay, g = shape(t)
        if any((lay is None or nl is None or nl == lay) and g.distance(ng) < RULES["clearance"] + 0.01 for nl, ng in new):
            n_drop += 1; continue
        copy(t, False); n_copy += 1
    print(f"router's items brought across: {n_copy}; left out where the new fan-out is: {n_drop}")
    save_board(pcb, b)
    res = _route(pcb, passes=passes, timeout=timeout, tag="_resume", resume=True)
    print("resumed:", res)
    b = pcbnew.LoadBoard(pcb); print("dangling track ends trimmed:", trim_dangling(b))
    save_board(pcb, b)
    nv, nu, txt = kt.drc(pcb)
    if nu == 0:   # every net joined: the ribbon's unused ends can go too
        b = pcbnew.LoadBoard(pcb); print("ribbon stubs trimmed:", trim_dangling(b, locked_too=True)); save_board(pcb, b)
    b = pcbnew.LoadBoard(pcb); add_planes(b); save_board(pcb, b)
    nv, nu, txt = kt.drc(pcb, os.path.join(OUT, "drc.rpt"))
    left = Counter(re.findall(r"\[unconnected_items\][^\n]*\n[^\n]*\n[^\n]*\[([^\]]+)\]", txt))
    kinds = Counter(re.findall(r"^\[(\w+)\]", txt, re.M))
    vias = sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_VIA")
    print(f"finished: unconnected {nu}, violations {nv}, vias {vias}; {dict(kinds)}")
    print("left: " + ", ".join(f"{n} {c}" for n, c in left.most_common()))
    os.remove(routed)


def _patch_router(b):
    """patch_router.PatchRouter on this board: the four signal layers, the board as drawn on Edge.Cuts, the net classes' widths,
    the flex's analog lines kept further off, no tracks on In2 over the analog ribbon."""
    import patch_router
    from shapely.geometry import Polygon, LineString
    kic = lambda pts: [(ORIGIN[0] + x, ORIGIN[1] - y) for x, y in pts]
    eg = edge_polygon()
    outline = Polygon(kic(eg.exterior.coords), [kic(i.coords) for i in eg.interiors])
    keep = []
    for rb in RIBBONS:
        if rb["clear_in2"]:
            half = (len(rb["layers"]["In3.Cu"]) - 1) / 2 * RIB_PITCH + 0.3
            path = rb.get("centre_by_layer", {}).get("In3.Cu", rb["centre"])
            keep.append(Polygon(kic(LineString(path).buffer(half, cap_style=2, join_style=2).exterior.coords)))
    widths = {"default": RULES["track"]}
    for name, _c, w, members in CLASSES:
        for n in members:
            widths[n] = w
    analog = [n for name, c, w, members, _l in FLEX_CLASSES if name == "FlexAnalog" for n in members]
    rules = dict(RULES, hole_clearance=0.2, hole_to_hole=0.25)
    return patch_router.PatchRouter(b, [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.B_Cu], outline, rules, widths, analog=analog,
                                    keepouts={pcbnew.In2_Cu: keep}), widths


# laid before the router, on the empty board (with the ribbon and the ground fan-out): the connections the router could not make
# in any number of passes once the rest was in (9 Nov): board L's 15 V feed from the post (75 mm), the USB pair from the flex pads
# through the ribbon into the chip, and every flex line from its pad into its ribbon line (the far ends are left to the router)
PREROUTE_FULL = ["VSYS", "USB_DP", "USB_DM"]
# pins and pads the router could not reach on the 9 Nov runs: each gets a short stub to its own via first (escape), so the router
# can come in on any layer: the chip's right-side pins 54-58 (walled in by their neighbours' front tracks to J3), pin 44 (DIAL_RX),
# and the ADC filters R4 and R5 the flex's CV lines go to
ESCAPES = [("U1", "54"), ("U1", "55"), ("U1", "56"), ("U1", "58"), ("U1", "44"), ("R4", "1"), ("R5", "2")]
# (tried 9 Nov: laying the last eight first as well; MIDI_TX and CV_IN1_L then went 95 mm round, the ribbon's top end is walled
# in by J3's pins, window B and the lines that leave it first: that end needs a planned fan-out like the flex pads')
# VSYS up the left strip on In2 (empty there; the other layers are the router's), the USB pair on the back and front, as its ribbon
PREROUTE_LAYERS = {"VSYS": {pcbnew.F_Cu: 4.0, pcbnew.In3_Cu: 4.0, pcbnew.B_Cu: 4.0},
                   "USB_DP": {pcbnew.In2_Cu: 4.0, pcbnew.In3_Cu: 4.0}, "USB_DM": {pcbnew.In2_Cu: 4.0, pcbnew.In3_Cu: 4.0}}
PREROUTE_PADS = False   # the flex pads' links: laid as part of the ribbon now (flex_fanout)


def preroute(b):
    pr, widths = _patch_router(b); out = []; failed = []
    j1 = {p.GetNetname(): pcbnew.ToMM(p.GetPosition().x) for f in b.GetFootprints() if f.GetReference() == "J1" for p in f.Pads()}
    flex = [n for _c, _cl, _w, nets, _l in FLEX_CLASSES for n in nets if n not in PREROUTE_FULL]
    pad_and_ribbon = lambda its: any(it.get("ref") == "J1" or it["kind"] == "track" for it in its)
    for ref, num in ESCAPES:
        v = pr.escape(ref, num)
        out.append(f"{ref}.{num}: " + (f"via at {v}" if v else "no via spot"))
        if not v:
            failed.append(f"{ref}.{num}")
    jobs = [(n, None) for n in PREROUTE_FULL] + ([(n, pad_and_ribbon) for n in sorted(flex, key=lambda n: -j1.get(n, 0))]
                                                  if PREROUTE_PADS else [])
    for n, want in jobs:
        left, added, _v = pr.route_net(n, want=want, layer_cost=PREROUTE_LAYERS.get(n))
        out += [f"{n}: {a['length']:.1f} mm on {', '.join(b.GetLayerName(l) for l in a['layers'])}, {len(a['vias'])} via(s)" for a in added]
        if left:
            failed.append(f"{n} ({left})")
    return out, failed


def free_router_tracks(b):
    """Unlock the router's own tracks and vias (route_board locks everything after its first pass) so the patch router may take
    them up; what was laid on purpose stays locked: ground, the nets laid before the router, the ribbon and the flex pads' stubs and
    vias. Returns how many were freed."""
    from shapely.geometry import LineString, Point
    lines = {}
    for net, _lay, pts in ribbon_lines(b):
        lines.setdefault(net, []).append(LineString([(ORIGIN[0] + x, ORIGIN[1] - y) for x, y in pts]))
    vias, _left = flex_fanout(b)
    stub = {(net, round(px, 3), round(py, 3), round(vx, 3), round(vy, 3)) for (net, _k), (px, py, vx, vy) in vias.items()}
    via_at = {(net, round(vx, 3), round(vy, 3)) for (net, _k), (_px, _py, vx, vy) in vias.items()}
    n = 0
    for t in b.GetTracks():
        net = t.GetNetname()
        if not t.IsLocked() or net == "GND" or net in PREROUTE_FULL:
            continue
        if t.GetClass() == "PCB_VIA":
            x, y = pcbnew.ToMM(t.GetPosition().x), pcbnew.ToMM(t.GetPosition().y)
            if (net, round(x, 3), round(y, 3)) in via_at:
                continue
        else:
            a = (pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y)); e = (pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y))
            if any(l.distance(Point(a)) < 0.002 and l.distance(Point(e)) < 0.002 for l in lines.get(net, [])):
                continue
            if (net, round(a[0], 3), round(a[1], 3), round(e[0], 3), round(e[1], 3)) in stub:
                continue
        t.SetLocked(False); n += 1
    return n


PATCH_DEPTH = int(os.environ.get("PATCH_DEPTH", "0"))   # levels of taking up the router's tracks (0: none; 2 made it worse on 9 Nov)
PATCH_PEN = float(os.environ.get("PATCH_PEN", "200"))   # per cell of the router's copper crossed: ~100 mm of detour per track


def drop_tiny(board, below=0.01):
    """Tracks shorter than this (the router's own leftovers, 0.003 mm seen) go: Freerouting fails to read a net that has one back
    ("normalization of net failed") and hangs."""
    tiny = [t for t in board.GetTracks() if t.GetClass() != "PCB_VIA" and pcbnew.ToMM(t.GetLength()) < below]
    for t in tiny:
        board.Remove(t); KEEP.append(t)
    return len(tiny)


def force_and_resume(passes, timeout):
    """For what neither router can join: the patch router forces each one through, taking up the router's tracks in its way
    (they stay out), then Freerouting, given the board again with the forced paths fixed and its own tracks free, joins the nets
    that were taken up (it is better at many easy nets than at a few walled-in ones); then the patch step."""
    import re, shutil, kicad7_tools as kt
    pcb = os.path.join(OUT, NAME + ".kicad_pcb")
    nv, nu, txt = kt.drc(pcb)
    nets = sorted(set(re.findall(r"\[unconnected_items\][^\n]*\n[^\n]*\n[^\n]*\[([^\]]+)\]", txt)) - {"GND"})
    b = pcbnew.LoadBoard(pcb)
    print("router's tracks freed:", free_router_tracks(b))
    pr, widths = _patch_router(b); taken = set()
    for n in nets:
        left, added, victims = pr.route_net(n, rip=True, pen0=PATCH_PEN)
        taken |= victims
        print(f"  {n}: {'forced' if not left else 'still ' + str(left) + ' left'}"
              + (f", {sum(a['length'] for a in added):.1f} mm, {sum(len(a['vias']) for a in added)} via(s)" if added else "")
              + (f"; took up {', '.join(sorted(victims))}" if victims else ""))
    print("taken up for the router to join again:", ", ".join(sorted(taken)) or "none")
    # the board again from the placed one (no planes: the router works without them), everything carried over as it is locked
    key = lambda t: (t.GetClass(), t.GetNetname(), t.GetLayer(), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y)
    nb = pcbnew.LoadBoard(os.path.join(OUT, "placed.kicad_pcb")); refresh_ribbons(nb)
    have = {key(t) for t in nb.GetTracks()}
    for t in b.GetTracks():
        if key(t) in have:
            continue
        if t.GetClass() == "PCB_VIA":
            n_ = pcbnew.PCB_VIA(nb); n_.SetPosition(t.GetPosition()); n_.SetWidth(t.GetWidth()); n_.SetDrill(t.GetDrillValue())
            n_.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        else:
            n_ = pcbnew.PCB_TRACK(nb); n_.SetStart(t.GetStart()); n_.SetEnd(t.GetEnd()); n_.SetWidth(t.GetWidth()); n_.SetLayer(t.GetLayer())
        n_.SetNet(nb.FindNet(t.GetNetname())); n_.SetLocked(t.IsLocked()); nb.Add(n_)
    print("tiny tracks dropped:", drop_tiny(nb))
    save_board(pcb, nb)
    write_project(OUT, NAME, RULES, [(LIB, "${KIPRJMOD}/../" + LIB + ".pretty")], CLASSES)
    print("router again:", _route(pcb, passes=passes, timeout=timeout, tag="_force", resume=True))
    b2 = pcbnew.LoadBoard(pcb); print("dangling track ends trimmed:", trim_dangling(b2)); add_planes(b2); save_board(pcb, b2)
    patch_finish()


def patch_finish(narrow=(0.25, 0.2, 0.127)):
    """Join what the router left (patch_router.py): each unjoined net searched on a 0.05 grid around the copper already there,
    at its class width first, narrower only if that finds no way. Then the dangling ends, the planes refilled, KiCad's DRC."""
    import re, kicad7_tools as kt, patch_router
    from collections import Counter
    from shapely.geometry import Polygon, LineString
    pcb = os.path.join(OUT, NAME + ".kicad_pcb")
    nv, nu, txt = kt.drc(pcb)
    nets = sorted(set(re.findall(r"\[unconnected_items\][^\n]*\n[^\n]*\n[^\n]*\[([^\]]+)\]", txt)) - {"GND"})
    b = pcbnew.LoadBoard(pcb)
    print("router's tracks freed for taking up:", free_router_tracks(b))
    pr, widths = _patch_router(b)
    report = []; failed = []

    def join(n, depth):
        """Join net n; up to depth 2 it may take up the router's tracks of other nets (dearer each level), and the nets it took up
        are joined again one level down; at the last level nothing is taken up, so the chain stops."""
        w0 = widths.get(n, widths["default"])
        for w in [w0] + [x for x in narrow if x < w0]:
            left, added, victims = pr.route_net(n, width=w, rip=depth < PATCH_DEPTH, pen0=PATCH_PEN * 5 ** depth)
            for a in added:
                report.append("  " * depth + f"{n}: {a['length']:.1f} mm at {w} mm on "
                              f"{', '.join(b.GetLayerName(l) for l in a['layers'])}, {len(a['vias'])} via(s)")
            if victims:
                report.append("  " * depth + f"  taken up for {n}: {', '.join(sorted(victims))}")
                for v in sorted(victims):
                    join(v, depth + 1)
            if left == 0:
                return
        failed.append(n)
    for n in nets:
        join(n, 0)
    queue = failed
    print("\n".join(report))
    if queue:
        print("not joined:", ", ".join(queue))
    print("dangling track ends trimmed:", trim_dangling(b))   # on the board in hand (a second load in this process came back unusable)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); save_board(pcb, b)
    nv, nu, txt = kt.drc(pcb)
    if nu == 0:   # every net joined: the ribbon's unused ends can go too
        print("ribbon stubs trimmed:", trim_dangling(b, locked_too=True))
        pcbnew.ZONE_FILLER(b).Fill(b.Zones()); save_board(pcb, b)
    nv, nu, txt = kt.drc(pcb, os.path.join(OUT, "drc.rpt"))
    left = Counter(re.findall(r"\[unconnected_items\][^\n]*\n[^\n]*\n[^\n]*\[([^\]]+)\]", txt))
    kinds = Counter(re.findall(r"^\[(\w+)\]", txt, re.M))
    vias = sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_VIA")
    print(f"patched: unconnected {nu}, violations {nv}, vias {vias}; {dict(kinds)}")
    print("left: " + ", ".join(f"{n} {c}" for n, c in left.most_common()))
    return report


def route_trial(pcb, layers, timeout):
    """Copy of the placed board with this many copper layers (In1 = the ground plane), ground fanned out to it, the rest by
    Freerouting 1.9.0 (ground left to the plane): how much is left unrouted answers the layer count."""
    import shutil, kicad7_tools as kt
    planes = [int(v) for v in os.environ.get("PLANES", "1").split(",")]   # inner layers kept as ground planes (In1, In4 ...)
    d = os.path.join(OUT, f"trial{layers}" + ("" if planes == [1] else "p" + "".join(map(str, planes)))); os.makedirs(d, exist_ok=True)
    tp = os.path.join(d, NAME + ".kicad_pcb")
    write_project(d, NAME, RULES, [(LIB, "${KIPRJMOD}/../../" + LIB + ".pretty")], CLASSES)
    b = pcbnew.LoadBoard(pcb)
    b.GetDesignSettings().SetCopperLayerCount(layers)
    for k in planes:
        b.SetLayerType({1: pcbnew.In1_Cu, 2: pcbnew.In2_Cu, 3: pcbnew.In3_Cu, 4: pcbnew.In4_Cu}[k], pcbnew.LT_POWER)
    print(f"{layers} layers: ground vias (placed, no room):", fanout_gnd(b))
    save_board(tp, b)
    res = _route(tp, passes=int(os.environ.get("ROUTE_PASSES", "30")), timeout=timeout)
    b = pcbnew.LoadBoard(tp)
    nv = sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_VIA")
    ln = sum(pcbnew.ToMM(t.GetLength()) for t in b.GetTracks() if t.GetClass() != "PCB_VIA")
    print(f"{layers} layers: unconnected {res[0][0] if isinstance(res[0], tuple) else res[0]}, result {res}, vias {nv}, track {ln:.0f} mm")
    if res is not None:
        trial_planes(tp, planes)
    return res


def pin_targets(pcb, parts, out):
    """For re-solving the pin map against the placement: where each H743 pad would sit at each quarter turn (panel), and for each
    MCU net the centroid of what it goes to, followed once through a series part (a 2-pin R or bead whose other side is not a
    supply), so the pin is drawn toward the far end, not toward its own filter resistor."""
    b = pcbnew.LoadBoard(pcb)
    to_panel = lambda v: (pcbnew.ToMM(v.x) - ORIGIN[0], -(pcbnew.ToMM(v.y) - ORIGIN[1]))
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    u1 = fps["U1"]; cx, cy = to_panel(u1.GetPosition())
    pads = {p.GetNumber(): to_panel(p.GetPosition()) for p in u1.Pads()}
    rot0 = u1.GetOrientationDegrees()
    pin_xy = {}
    for q in (0, 90, 180, 270):   # turn the chip by q more about its centre (panel CCW)
        c, s_ = math.cos(math.radians(q)), math.sin(math.radians(q))
        pin_xy[str(int((rot0 + q) % 360))] = {n: (round(cx + (x - cx) * c - (y - cy) * s_, 3), round(cy + (x - cx) * s_ + (y - cy) * c, 3))
                                              for n, (x, y) in pads.items()}
    supplies = {"GND", "3V3", "5V", "VSYS", "VDDA", "VREFP", "VCAP", "VM", "RING_5V", "RING_IN"}
    bynet = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname():
                bynet.setdefault(p.GetNetname(), []).append((f.GetReference(), p.GetNumber(), to_panel(p.GetPosition())))
    two = {p["ref"]: p for p in parts if len([v for v in p["pins"].values() if v]) == 2 and p["ref"][0] in "RF"}
    rib_end = {net: pts[-1] for net, _lay, pts in ribbon_lines()}   # the flex lines arrive at the top of their ribbon
    for net, end in rib_end.items():
        bynet[net] = [(r, n_, end if r == "J1" else xy) for r, n_, xy in bynet.get(net, [])]
    targets = {}
    for net in design.PINMAP["nets"]:
        pts = []
        for ref, num, xy in bynet.get(net, []):
            if ref == "U1":
                continue
            if ref in two:
                other = [v for k, v in two[ref]["pins"].items() if k != num and v][0]
                if other not in supplies:
                    pts += [q[2] for q in bynet.get(other, []) if q[0] != ref]
                    continue
            pts.append(xy)
        if pts:
            targets[net] = (round(sum(x for x, _ in pts) / len(pts), 3), round(sum(y for _, y in pts) / len(pts), 3))
    json.dump(dict(centre=(cx, cy), rot=rot0, pin_xy=pin_xy, targets=targets), open(out, "w"), indent=0)
    return len(targets)


# ------------------------------------------------------------------ the link flex's ribbon [Ed 9 Nov 09:31 "Y"]
# (docs/img/flex-corridor.png) Laid before the router, locked: the analog lines on In3 (between In4's ground and an In2 kept
# clear above them) and the I2C / MIDI / USB lines on the back, stacked, up the right strip beside windows D and C, in through
# the gap between the LEDs at 330 deg, up inside the ring, out at 30 deg, up beside window B; the SPI lines on the front, left
# along the strip under window D and up the left side the same way (210 / 150 deg). Panel frame; 0.3 pitch [A].
RIB_PITCH = 0.3
# 9 Nov, second layout: the right ribbon now starts under the flex pads (on the back and In3, below the front pads) and each flex
# pad gets a planned way down into it, a short front stub to its own via (every other pad up, the rest down, two staggered rows),
# so the 0.3 mm pads no longer leave it to the router; the left ribbon's lines start at their pads. Lines are listed from the
# right-hand side of the ribbon's direction (panel frame) to the left, in the order their pads' vias come.
RIBBONS = [
    dict(name="right", centre=[(12.3, -49.725), (18.0, -49.725), (20.7, -47.025), (20.7, -13.0), (18.19, -10.5), (14.29, -8.25),
                               (14.29, 8.25), (18.19, 10.5), (20.7, 13.0), (20.7, 25.4)],
         layers={"B.Cu": ["USB_DM", "IO_INT", "I2C_SCL", "I2C_SDA", "MIDI_TX", "USB_DP"],
                 "In3.Cu": ["AGND_SENSE_L", "AUDIO_IN_L", "AUDIO_OUT", "CV_IN3_L", "CV_IN1_L", "CV_IN2_L"]}, clear_in2=True),
         # (tried 9 Nov: carrying the analog lines on west along window B's notch, centre_by_layer; their last hop to the ADC
         # filters then found no via room in the filters' tight cluster on the back, worse than leaving them to the router)
    dict(name="left", centre=[(9.9, -48.2), (-20.7, -48.2), (-20.7, -13.0), (-18.19, -10.5), (-15.5, -8.95), (-15.5, 8.95),
                              (-18.19, 10.5), (-20.7, 13.0), (-20.7, 25.4)],
         layers={"F.Cu": ["OLED_RES", "OLED_DC", "CS_OLED", "CS_DAC", "MOSI_L", "SCK_L"]}, clear_in2=False),
]
# the flex pads' vias (KiCad frame): pads 8-25 alternate, odd up, even down (pad 7's front line to the left ribbon passes where
# pad 8's via would be above); each row staggered 0.3 so neighbours keep 0.2 mm
FAN_UP_Y, FAN_DOWN_Y, FAN_STAGGER = (148.3, 148.0), (151.15, 151.45), 0.3


def flex_fanout(board):
    """{net: (pad x, pad y, via x, via y)} for the flex pads that drop to a via (KiCad frame), and the left ribbon's pads
    {net: (x, y)}."""
    j1 = [p for f in board.GetFootprints() if f.GetReference() == "J1" for p in f.Pads()]
    vias, left = {}, {}
    left_nets = [n for rb in RIBBONS if rb["name"] == "left" for n in rb["layers"]["F.Cu"]]
    for p in j1:
        k = int(p.GetNumber()); x, y = pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y); n = p.GetNetname()
        if n in left_nets:
            left[n] = (x, y); continue
        if k < 8 and n != "GND":
            continue
        up = k % 2 == 1 and k >= 8
        row = FAN_UP_Y if up else FAN_DOWN_Y
        vias[(n, k)] = (x, y, x, row[((k - 1) // 2) % 2] if up else row[(k // 2) % 2])
    return vias, left


LAYER_ID = {"F.Cu": pcbnew.F_Cu, "In2.Cu": pcbnew.In2_Cu, "In3.Cu": pcbnew.In3_Cu, "B.Cu": pcbnew.B_Cu}


def _offset(pts, d):
    """A polyline moved d to its left (positive d), corners mitred: each segment shifted along its normal, neighbours joined where
    their lines cross."""
    segs = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        lx, ly = bx - ax, by - ay; ln = math.hypot(lx, ly); nx, ny = -ly / ln * d, lx / ln * d
        segs.append(((ax + nx, ay + ny), (bx + nx, by + ny)))
    out = [segs[0][0]]
    for (p1, p2), (q1, q2) in zip(segs, segs[1:]):
        d1 = (p2[0] - p1[0], p2[1] - p1[1]); d2 = (q2[0] - q1[0], q2[1] - q1[1])
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-12:
            out.append(p2); continue
        t = ((q1[0] - p1[0]) * d2[1] - (q1[1] - p1[1]) * d2[0]) / den
        out.append((p1[0] + t * d1[0], p1[1] + t * d1[1]))
    out.append(segs[-1][1])
    return out


def ribbon_lines(board=None):
    """[(net, layer name, [(x, y) panel ...])]: each ribbon line, offset from its ribbon's centre line (mitred corners). With the
    board: the right ribbon's lines begin at their pads' vias (a stub from the line to the via) and the left ribbon's at their pads."""
    out = []
    vias, left = flex_fanout(board) if board is not None else ({}, {})
    via_of = {n: (vx - ORIGIN[0], ORIGIN[1] - vy) for (n, _k), (_px, _py, vx, vy) in vias.items()}
    for rb in RIBBONS:
        for lay, nets in rb["layers"].items():
            n = len(nets)
            for i, net in enumerate(nets):
                off = (i - (n - 1) / 2) * RIB_PITCH
                pts = [(round(x, 4), round(y, 4)) for x, y in _offset(rb.get("centre_by_layer", {}).get(lay, rb["centre"]), off)]
                if rb["name"] == "right" and net in via_of:
                    vx, vy = via_of[net]
                    pts = [(vx, vy), (vx, pts[0][1])] + pts[1:]          # from the via, to the line, along it (first point dropped)
                elif rb["name"] == "left" and net in left:
                    px, py = left[net][0] - ORIGIN[0], ORIGIN[1] - left[net][1]
                    pts = [(px, py), (px, pts[0][1])] + pts             # from the pad, up to the line, along it
                out.append((net, lay, pts))
    return out


def ribbon_corridor(face, extra=0.25):
    """Where the ribbon runs on a face (F, B): kept free of parts by the placer."""
    from shapely.geometry import LineString
    from shapely.ops import unary_union
    lay = {"F": "F.Cu", "B": "B.Cu"}[face]
    gs = []
    for rb in RIBBONS:
        if lay in rb["layers"]:
            half = (len(rb["layers"][lay]) - 1) / 2 * RIB_PITCH + 0.0635 + extra
            gs.append(LineString(rb["centre"]).buffer(half, cap_style=2, join_style=2))
    return unary_union(gs) if gs else None


def add_ribbons(board, rule_area=True):
    """The ribbon's tracks, locked; the flex pads' front stubs and vias; a no-track area on In2 over the analog lines."""
    from shapely.geometry import LineString
    n_seg = 0
    vias, _left = flex_fanout(board)
    for net, lay, pts in ribbon_lines(board):
        ni = board.FindNet(net)
        assert ni is not None, net
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            if (ax, ay) == (bx, by):
                continue
            t = pcbnew.PCB_TRACK(board); t.SetStart(P(*L(ax, ay))); t.SetEnd(P(*L(bx, by))); t.SetWidth(mm(RULES["track"]))
            t.SetLayer(LAYER_ID[lay]); t.SetNet(ni); t.SetLocked(True); board.Add(t); n_seg += 1
    for (net, _k), (px, py, vx, vy) in vias.items():   # front stub from the pad to its via
        ni = board.FindNet(net); w = RULES["track"] if net != "GND" else 0.15
        t = pcbnew.PCB_TRACK(board); t.SetStart(pcbnew.VECTOR2I(mm(px), mm(py))); t.SetEnd(pcbnew.VECTOR2I(mm(vx), mm(vy)))
        t.SetWidth(mm(w)); t.SetLayer(pcbnew.F_Cu); t.SetNet(ni); t.SetLocked(True); board.Add(t); n_seg += 1
        v = pcbnew.PCB_VIA(board); v.SetPosition(pcbnew.VECTOR2I(mm(vx), mm(vy))); v.SetWidth(mm(RULES["via_d"]))
        v.SetDrill(mm(RULES["via_drill"])); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(ni); v.SetLocked(True); board.Add(v)
    for rb in RIBBONS if rule_area else []:
        if not rb["clear_in2"]:
            continue
        half = (len(rb["layers"]["In3.Cu"]) - 1) / 2 * RIB_PITCH + 0.3
        g = LineString(rb.get("centre_by_layer", {}).get("In3.Cu", rb["centre"])).buffer(half, cap_style=2, join_style=2)
        z = pcbnew.ZONE(board); z.SetIsRuleArea(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(False)
        z.SetDoNotAllowCopperPour(False); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        z.SetLayer(pcbnew.In2_Cu); z.SetZoneName("keep In2 clear over the analog ribbon")
        ol = z.Outline(); ol.NewOutline()
        for x, y in list(g.exterior.coords)[:-1]:
            ol.Append(mm(ORIGIN[0] + x), mm(ORIGIN[1] - y))
        board.Add(z)
    return n_seg


def refresh_ribbons(board):
    """The placed board's ribbon (laid at placement) taken off and laid again as RIBBONS now has it, with the flex pads' stubs and
    vias; an extra In2 rule area over the new stretch under the flex pads (the placed one stays)."""
    from shapely.geometry import LineString
    old = [t for t in board.GetTracks() if t.IsLocked()]
    for t in old:
        board.Remove(t); KEEP.append(t)
    n = add_ribbons(board, rule_area=False)
    rb = [r for r in RIBBONS if r["name"] == "right"][0]
    half = (len(rb["layers"]["In3.Cu"]) - 1) / 2 * RIB_PITCH + 0.3
    path = rb.get("centre_by_layer", {}).get("In3.Cu", rb["centre"])
    for part, name in ((path[:4], "flex pads"), (path[-3:], "top, along window B")):   # the stretches the placed board's area lacks
        g = LineString(part).buffer(half, cap_style=2, join_style=2)
        z = pcbnew.ZONE(board); z.SetIsRuleArea(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(False)
        z.SetDoNotAllowCopperPour(False); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        z.SetLayer(pcbnew.In2_Cu); z.SetZoneName(f"keep In2 clear over the analog ribbon ({name})")
        ol = z.Outline(); ol.NewOutline()
        for x, y in list(g.exterior.coords)[:-1]:
            ol.Append(mm(ORIGIN[0] + x), mm(ORIGIN[1] - y))
        board.Add(z)
    return len(old), n


BLOCK_COL = {"mcu": "#9ecae1", "link": "#c6dbef", "screen": "#6baed6", "debug": "#d9d9d9", "light": "#fdae6b", "adc": "#a1d99b",
             "halls": "#74c476", "encoder": "#c7e9c0", "motor": "#fc9272", "ring": "#fdd0a2", "rod": "#de2d26", "power": "#fee391",
             "cover": "#bdbdbd", "headers": "#969696"}


def clean_board():
    """The model's board less the stale v0.11 KiCad holes: the model still reads the old board's joystick-stack holes (MH1, Ø3.4 at
    x ±10.8, y 25.2 and 38.4) back from pcb_proxy.json, but nothing in v0.53 passes through them (room map: both faces empty at
    25.2; at 38.4 only the new spring bores, which are cut on their own). They are filled in; the windows and the joystick's
    present holes stay [A]. The model reads the new board's holes after this board's proxy export (step 4)."""
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union
    D = R["D"]; b = R["board"]
    stale = [Point(h["x"], h["y"]).buffer(h["d"] / 2 + 0.02, 64) for h in D.get("pcb_kicad", {}).get("holes", []) if h["ref"] == "MH1"]
    if not stale:
        return b, 0
    real = [Polygon(p) for p in D["pcb_windows"].values()] + [Point(h["x"], h["y"]).buffer(h["d"] / 2, 64) for h in D.get("js_pcb_holes", [])]
    fill = unary_union(stale).difference(unary_union(real).buffer(1e-3))
    nb = b.union(fill).buffer(0)
    return nb, round(nb.area - b.area, 1)


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
            if abs(rot / 90.0 - round(rot / 90.0)) > 1e-6:   # turned: draw its real courtyard
                u0, v0, u1, v1, _ = geometry(p["fp"], "F", 0); t = math.radians(rot if s == "F" else -rot)
                c, s_ = math.cos(t), math.sin(t)
                pts = [(x + u * c + v * s_, -(y - u * s_ + v * c)) for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]
                ax.add_patch(plt.Polygon(pts, fc=BLOCK_COL.get(p["block"], "#eee"), ec="#333", lw=0.4, alpha=0.95))
            else:
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
    ap.add_argument("--trial", type=int, default=0, help="route a copy of the placed board on this many layers (4 or 6) and stop")
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--targets", help="write the pin-map targets of the placed board to this json and stop")
    ap.add_argument("--route", type=int, default=0, help="route the placed board in place with this many router passes and stop")
    ap.add_argument("--force", type=int, default=0, help="force the unjoined through (taking up the router's tracks), then the router again with this many passes, then --patch")
    ap.add_argument("--patch", action="store_true", help="join what the router left with the patch router (patch_router.py)")
    ap.add_argument("--finish", type=int, default=0, help="finish the routed board (router's tracks free, rip-up allowed) with this many passes")
    a = ap.parse_args()
    R = pickle.load(open(a.room, "rb"))
    R["board"], n_filled = clean_board()
    if a.targets:
        print("pin targets for", pin_targets(os.path.join(OUT, NAME + ".kicad_pcb"), design.build(), a.targets), "nets")
        return
    if a.route:
        route_board(a.route, a.timeout)
        return
    if a.finish:
        finish_route(a.finish, a.timeout)
        return
    if a.patch:
        patch_finish()
        return
    if a.force:
        force_and_resume(a.force, a.timeout)
        return
    if os.environ.get("TRIAL_PLANES_ONLY"):   # fill the planes of a finished trial and count (TRIAL_PLANES_ONLY=<trial dir name>)
        trial_planes(os.path.join(OUT, os.environ["TRIAL_PLANES_ONLY"], NAME + ".kicad_pcb"),
                     [int(v) for v in os.environ.get("PLANES", "1").split(",")])
        return
    if a.trial:
        route_trial(os.path.join(OUT, NAME + ".kicad_pcb"), a.trial, a.timeout)
        return
    print(f"stale v0.11 holes filled in: {n_filled} mm²; board {R['board'].area:.0f} mm²")
    from shapely.ops import unary_union
    os.makedirs(OUT, exist_ok=True); os.makedirs(LIB_DIR, exist_ok=True)
    parts = design.build()
    fixed = fixed_parts(parts)
    for nm, fn in OWN.items():   # the board's own footprints, saved so the project opens on its own
        save_fp_if_changed(_FP_CACHE.setdefault(nm, _load_fp(pcbnew.BOARD(), nm)))
    free = {}
    for face, key in (("F", "front"), ("B", "back")):
        mech = unary_union([g for n, g in R["occ"][key].items() if not n.startswith(ELECTRICAL)])
        free[face] = R["board"].difference(mech).buffer(-EDGE_KEEP)
        cor = ribbon_corridor(face)
        if cor is not None:
            free[face] = free[face].difference(cor)
    room = Room(free)
    d = place_debug(parts, room, fixed)
    print(f"Tag-Connect pads at panel ({d[1]:.2f}, {-d[2]:.2f}), turned {d[3]}, {d[0]:.2f} from the plan's spot")
    placement, stats = run_placer(parts, fixed, room, a.iters, a.seed)
    placement.update(fixed)
    pcb = os.path.join(OUT, NAME + ".kicad_pcb")
    write_project(OUT, NAME, RULES, [(LIB, "${KIPRJMOD}/../" + LIB + ".pretty")], ())
    board, dropped = build(parts, placement)
    print("ribbon tracks:", add_ribbons(board))
    save_board(pcb, board)
    import shutil
    shutil.copy(pcb, os.path.join(OUT, "placed.kicad_pcb"))   # --route starts from this
    for nm in {p["fp"] for p in parts}:   # every footprint the board uses, as placed (no silkscreen), in its own library
        save_fp_if_changed(_FP_CACHE[nm])
    json.dump({r: list(v) for r, v in placement.items()}, open(os.path.join(HERE, "placement.json"), "w"), indent=0)
    picture(parts, placement, os.path.join(HERE, "placement.png"), stats)
    v, u, _txt = drc(pcb, os.path.join(OUT, "drc.rpt"))
    print("edge cuts: model holes drilled by footprints instead:", dropped)
    for line in checks(pcb, fixed):
        print(line)
    print(f"DRC: {v} violations, {u} unconnected (not routed yet)")


if __name__ == "__main__":
    main()
