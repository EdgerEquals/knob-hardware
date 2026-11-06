"""Jack power board and jack lower board (knob step 2, CAD v0.48; Ed 6 Nov Q23 = A: two boards, Q24 = A: post pins). Builds both
boards from design.py (one netlist): footprints, outline, the fixed connectors, an annealed placement of the rest (../placer.py),
schematics, projects, and with --route Freerouting on 4 layers. Run with the system python that has pcbnew (KiCad 7.0.11):
  /usr/bin/python3 make_boards.py [--place] [--route] [upper|lower]
    --place  re-run the placer (else the saved <board>/placement_in.json is used when it exists)
    --route  Freerouting (GPL-3.0, https://github.com/freerouting/freerouting), In1 a ground plane
KiCad frame as the jack board's: x = panel x, y = -(panel y - JY), JY = the jack axes (panel y -44.40); KiCad origin (100, 100).
  upper = the jack power board: the jack row 43.0 x 10.5 + two ears round the posts (x -16.5 GND, x +8.0 VSYS, down to panel y -51.5);
          top face: H1/H2 sockets under the jack board's stacks [nets by position from jack-board/placement.json]; underside: H3/H4,
          the second stacks' males; posts: Ø1.0 pins in plated Ø1.15 holes, Ø1.6 pads [Q24 = A].
  lower = the jack lower board: the jack row only, 4.9 under the power board; top face: H5/H6 sockets; underside: the clear OLED's
          ZIF J5 and the link flex connector J6, both opening toward the bottom edge where the flexes come up.
4 layers, 1.6 mm: F.Cu, In1.Cu (ground plane), In2.Cu (power and signals), B.Cu. Rules PCBWay standard: 0.1 clearance (routed at
0.127), 0.127 tracks, vias 0.45 / 0.2. KiCad library footprints (CC-BY-SA 4.0 with the design exception) copied into jpb.pretty."""
import os, sys, json, math, subprocess
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
KI = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, KI); sys.path.insert(0, HERE)
import sch_gen, design, placer
from kicad7_tools import FP, V, mm, save_fp, write_project, drc, save_board

PCB_VERSION = "v0.1"
CAD_VERSION = "v0.48"
LIB = "jpb"; LIB_DIR = os.path.join(HERE, LIB + ".pretty")
KLIB = "/usr/share/kicad/footprints"
ORIGIN = (100.0, 100.0)
BT = 1.6
RULES = dict(clearance=0.1, track=0.127, min_track=0.1, via_d=0.45, via_drill=0.2, edge=0.25)
FREEROUTING = os.environ.get("FREEROUTING_JAR", "/home/claude/tools/freerouting-1.9.0.jar")   # 1.9.0: -mp and -inc work (2.1.0 ignores them)
JY = -44.40
ROW_X = (-21.5, 21.5); ROW_Y = (-48.9, -38.4)          # the jack row (panel)
POSTS = [(-16.5, -50.45, "GND"), (8.0, -50.45, "VSYS")]
EAR = (1.3, -51.5)                                     # half width round each post, bottom edge (panel)
POST_PIN = (1.0, 1.15, 1.6)                            # [Ed 6 Nov Q24 = A] pin, plated hole, pad
HDR_X, HDR_Y = 11.15, JY + 0.75                        # both pairs of 2x6 stacks: x ∓11.15, centre panel y -43.65
ZIF_OLED = (0.0, ROW_Y[0] + 0.75)                      # x centre, front edge (panel y) of the clear OLED's ZIF body (model zif_oled)
ZIF_LINK = (14.1, ROW_Y[0] + 0.75)                     # the link flex connector (model zif_link)
BOARDS = {"upper": dict(name="jack-power-board", dir="upper", title="Jack power board"),
          "lower": dict(name="jack-lower-board", dir="lower", title="Jack lower board")}
# net classes for routing (name, clearance, width, nets): VBUS/VSYS carry about 1.2 A at 5 V in (6 W peak [A]); 0.5 wide as on the
# jack board, 0.1 clear so they still reach the 0.5-pitch pins of the PD chip, the boost and the buck
CLASSES = [("GND", 0.1, 0.25, ["GND"]),          # not routed: every ground pad has its via to the In1 plane (fanout_gnd) or the pours
           ("Power", 0.1, 0.5, ["VBUS", "VSYS"]),
           ("Supply", 0.1, 0.3, ["SW_B", "BOOST", "SW_3", "3V3", "P12V5", "N12V", "VNEG_RAW", "OLED_VCC", "CP_R", "CP_A"])]
MARGINS = {}          # {board: {ref: margin}}: parts given more room after the router found pins walled in (main() fills it)
ESCAPE = 0.0          # (0.9 tried 6 Nov: no legal placement) mm kept free beside the stacks' pad rows and in front of the flex connectors' pads (escape tracks and vias)
EDGE_IC = 0.55        # mm from a chip's courtyard to the board edge: with 0.15 its pins facing the edge were walled in (6 Nov)
IC_MARGIN = 0.08      # (0.35 tried 6 Nov: no legal placement) mm between an IC's courtyard and its neighbours' (room for its fanout)
POWER = {"3V3": 0.2, "P12V5": 0.2, "N12V": 0.2, "GND": 0.0, "VBUS": 1.0, "VSYS": 1.0, "SW_B": 3.0, "CP_R": 2.0, "CP_A": 2.0,
         "BOOST": 1.0, "VNEG_RAW": 0.5, "SW_3": 3.0, "BST_3": 2.0, "OLED_VCC": 0.5}


def kc(px, py):
    return px, -(py - JY)


def P(x, y):
    return V(ORIGIN[0] + x, ORIGIN[1] + y)


# ------------------------------------------------------------------ footprints
def fp_xunpu(board):
    """XUNPU FPC-05F-24PH20 (LCSC C2856805): 24 pads 0.30 x 1.25 at 0.5 pitch on y -1.29, mounting pads 2.0 x 2.5 at (±7.44, +1.29)
    [S-lib: LCSC/EasyEDA footprint]; body about 16.3 x 5.2 from y -0.6 to +4.57; the flex enters from the +y side [A, C]."""
    f = FP(board, LIB, "XUNPU_FPC-05F-24PH20", "XUNPU FPC-05F-24PH20 0.5 mm 24-pin flip-lock, bottom contact, 2.0 tall (LCSC C2856805); "
           "land pattern from LCSC/EasyEDA; flex enters from +y [A]")
    for i in range(24):
        f.smd(str(i + 1), -5.75 + 0.5 * i, -1.29, 0.30, 1.25)
    f.smd("25", 7.44, 1.29, 2.0, 2.5); f.smd("26", -7.44, 1.29, 2.0, 2.5)
    f.rect(-8.15, -0.6, 8.15, 4.57, pcbnew.F_Fab)
    f.rect(-8.7, -2.2, 8.7, 4.85, pcbnew.F_CrtYd)
    return f.done(2.0)


def fp_rpw(board):
    """PLACEHOLDER [C] for TI RPW0010A (VQFN-HR 2x2, 10 pads): the pad positions are not readable from TI's drawing text; this keeps
    the space and the pin numbers until the drawing (mpqf568) or TI's CAD files arrive."""
    f = FP(board, LIB, "TI_RPW0010A_VQFN-HR-10_2x2_PLACEHOLDER", "PLACEHOLDER for TI RPW0010A; replace from TI's drawing [C]")
    for k, y in enumerate((0.75, 0.25, -0.25, -0.75)):
        f.smd(str(k + 1), -0.85, -y, 0.5, 0.25)          # 1-4 down the left
        f.smd(str(10 - k), 0.85, -y, 0.5, 0.25)          # 10-7 down the right
    f.smd("5", -0.25, 0.0, 0.3, 1.6); f.smd("6", 0.25, 0.0, 0.3, 1.6)
    f.rect(-1.0, -1.0, 1.0, 1.0, pcbnew.F_Fab); f.rect(-1.3, -1.3, 1.3, 1.3, pcbnew.F_CrtYd)
    return f.done(0.0)


def fp_post(board):
    f = FP(board, LIB, "Post_Pin_1.0", f"Ø{POST_PIN[0]:g} pin of the Ø2 brass post: plated Ø{POST_PIN[1]:g} hole, Ø{POST_PIN[2]:g} pad [Ed 6 Nov Q24 = A]")
    f.pth("1", 0, 0, POST_PIN[2], POST_PIN[2], POST_PIN[1], shape="circle")
    f.rect(-1.0, -1.0, 1.0, 1.0, pcbnew.F_Fab)
    return f.done(0.0)


OWN = {"jpb:XUNPU_FPC-05F-24PH20": fp_xunpu, "jpb:TI_RPW0010A_VQFN-HR-10_2x2": fp_rpw, "jpb:Post_Pad": fp_post}
ALIAS = {"jpb:Hirose_FH26W-25S-0.3SHW": "Connector_FFC-FPC:Hirose_FH26-25S-0.3SHW_2Rows-25Pins-1MP_P0.60mm_Horizontal"}


_KEEP = []


_FP_CACHE = {}
_SCRATCH = []


def load_fp(board, name):
    """A fresh copy of a footprint. Each library is read once: pcbnew.FootprintLoad caches the whole .pretty folder on every call and
    never frees it (about 400 MB per board build before this cache, 6 Nov)."""
    if name not in _FP_CACHE:
        _FP_CACHE[name] = _load_fp(board, name)
    return _FP_CACHE[name].Duplicate().Cast()   # Duplicate: new IDs for the footprint and its pads


def _load_fp(board, name):
    if name in OWN:
        f = OWN[name](board)
    else:
        lib, fn = ALIAS.get(name, name).split(":")
        f = pcbnew.FootprintLoad(os.path.join(KLIB, lib + ".pretty"), fn)
        f.SetFPID(pcbnew.LIB_ID(LIB, fn))
    for g in list(f.GraphicalItems()):
        if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            f.Remove(g); _KEEP.append(g)   # keep the removed items' wrappers alive: freeing them breaks pcbnew's SWIG types (KiCad 7)
    try:
        f.Value().SetVisible(False)
    except AttributeError:
        pass
    return f


def fp_libname(name):
    return (ALIAS.get(name, name).split(":")[1]) if name not in OWN else load_fp(pcbnew.BOARD(), name).GetFPID().GetLibItemName().wx_str()


def geometry(name, side, rot, cache={}):
    """Pads (number -> offset) and courtyard box of a footprint placed at the origin with this rotation and face (KiCad frame)."""
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


# ------------------------------------------------------------------ outline and fixed parts
def outline(which):
    x0, x1 = ROW_X; yb, yt = ROW_Y
    if which == "lower":
        return [(x0, yt), (x1, yt), (x1, yb), (x0, yb)]
    pts = [(x0, yt), (x1, yt), (x1, yb)]
    for px, py, _n in sorted(POSTS, key=lambda p: -p[0]):
        pts += [(px + EAR[0], yb), (px + EAR[0], EAR[1]), (px - EAR[0], EAR[1]), (px - EAR[0], yb)]
    pts.append((x0, yb))
    return pts


def zif_place(name, cx, front_y):
    """A flex connector on the underside with its opening toward the bottom edge: try the four turns, keep the one whose opening
    side (the +y side of the footprint, from the local pads) faces panel -y, and put the body's front on front_y."""
    for rot in (0, 90, 180, 270):
        x0, y0, x1, y1, pads = geometry(name, "B", rot)
        # local opening side: XUNPU +y (mounting pads at +1.29, signal pads at -1.29); FH26 +x (the even row)
        if "XUNPU" in name:
            sig = [v for k, v in pads.items() if k in ("1", "24")]; mp = [v for k, v in pads.items() if k in ("25", "26")]
        else:
            sig = [v for k, v in pads.items() if k in ("1", "25")]; mp = [v for k, v in pads.items() if k in ("2", "24")]
        sy = sum(p[1] for p in sig) / len(sig); my = sum(p[1] for p in mp) / len(mp)
        if my > sy + 0.3:   # KiCad +y = panel -y: the opening side is lower on the panel
            kx, ky = kc(cx, front_y)
            return (kx, ky - y1 + 0.0, "B", rot)
    raise RuntimeError("no orientation opens to the bottom edge for " + name)


def fixed_parts(which, parts):
    out = {}
    hx, hy = kc(HDR_X, HDR_Y)
    for p in parts:
        r = p["ref"]
        if r in ("H1", "H2", "H5", "H6"):
            out[r] = ((-hx if r in ("H1", "H5") else hx), hy, "F", 0)
        elif r in ("H3", "H4"):
            out[r] = ((-hx if r == "H3" else hx), hy, "B", 0)
        elif r in ("MP1", "MP2"):
            px, py, _n = POSTS[0 if r == "MP1" else 1]; x, y = kc(px, py); out[r] = (x, y, "F", 0)
        elif r == "J5":
            out[r] = zif_place(p["fp"], *ZIF_OLED)
        elif r == "J6":
            out[r] = zif_place(p["fp"], *ZIF_LINK)
    return out


def header_nets(parts, fixed):
    """Nets of the stacks' pads by position: H1/H2 from the jack board's placement.json; H3-H6 from design.STACK2."""
    jb = json.load(open(os.path.join(KI, "jack-board", "placement.json")))
    res = {}
    for ref in ("H1", "H2", "H3", "H4", "H5", "H6"):
        if ref not in fixed:
            continue
        p = next(q for q in parts if q["ref"] == ref)
        x, y, side, rot = fixed[ref]
        x0, y0, x1, y1, pads = geometry(p["fp"], side, rot)
        cx = x
        rows = sorted({round(y + d[1], 3) for d in pads.values()})
        m = {}
        for num, (dx, dy) in pads.items():
            inner = abs(x + dx) < abs(cx)
            row = rows.index(round(y + dy, 3))                   # 0 = top (KiCad y smallest = panel highest)
            if ref in ("H1", "H2"):
                src = "H1" if ref == "H1" else "H2"
                cand = [q for q in jb["pads"] if q["ref"] == src]
                ys = sorted({q["xy"][1] for q in cand}, reverse=True)       # panel y, top first
                want = [q for q in cand if (abs(q["xy"][0]) < HDR_X) == inner and abs(q["xy"][1] - ys[row]) < 1e-3]
                m[num] = want[0]["net"]
            else:
                side_ = "left" if ref in ("H3", "H5") else "right"
                m[num] = design.STACK2[side_][0 if inner else 1][row]
        res[ref] = m
    return res


# ------------------------------------------------------------------ placement
# floorplan [A, 6 Nov]: which part of the board each circuit may use (panel x ranges, full height, both faces). Upper: the jack-1
# switching and the +12.5 V LDO at the left end (by H1/H3: J1's lines, BOOST up, the rails down); the jack-2/3 switching, the expander,
# the PD chip, the eFuse and the MIDI buffer between the stacks; the -12 V LDO and the 3.3 V buck at the right end. Lower: the boost
# and charge pump at the left (away from the DAC), the DAC and op-amps from the middle, the audio parts by H6 (J4).
ZONES = {"upper": {"L": (-21.5, -7.8), "M": (-7.8, 7.8), "R": (7.8, 21.5), "LM": (-21.5, 7.8), "MR": (-7.8, 21.5)},
         "lower": {"L": (-21.5, -3.0), "M": (-9.0, 9.0), "R": (3.0, 21.5), "MR": (-9.0, 21.5), "ALL": (-21.5, 21.5)}}


def zone_of(p, which, owner=None):
    """owner: the zone of the chip this part follows in design.py (each chip's parts come right after it)."""
    n = set(v for v in p["pins"].values() if v)
    v = p["value"]
    if which == "upper" and p["block"] == "jack1":
        return "L"
    if p["ref"][0] in "RCLD" and owner and not (n - {"GND", "3V3", "P12V5", "N12V", "VSYS", "VBUS", "BOOST"}) and p["block"] != "jack1":
        return owner                       # a supply capacitor or pull-up/down: with its chip
    if which == "upper":
        if n & {"J1_TIP", "J1_RING", "SW1_CV", "MT1", "MR1", "MY1", "RS1", "CV1_S"} - {"MY1"} and not v.startswith("TCA"):
            return "L"
        if n & {"P_FB", "P_NR"} or v.startswith("TPS7A49") or n == {"P12_EN", "GND"}:
            return "LM"
        if n & {"N_FB", "N_NR"} or v.startswith("TPS7A30") or n == {"N12_EN", "GND"} or (n == {"VNEG_RAW", "GND"}):
            return "MR"
        if n & {"SW_3", "BST_3", "SS_3", "FB_3"} or v.startswith("TPS62933"):
            return "MR"
        return "M"
    if n & {"SW_B", "CP_R", "CP_A", "B_SS", "B_COMP", "B_CZ", "B_FB", "B_FREQ"} or v.startswith(("TPS55340", "BAT54S", "PMEG")) or \
            n == {"VNEG_RAW", "GND"} or n == {"BOOST", "GND"} or (n == {"VSYS", "GND"}):
        return "L"
    if n & {"AO_C", "AO_N", "AO_O", "AI_C", "AI_N", "ABIAS", "AIN", "AOUT"} and not v.startswith(("OPA", "TLV")):
        return "R"
    return "ALL"


def tca_pin_swap(parts, placement, log=print):
    """The expander's 16 port pins are interchangeable: give each function the free port pin nearest its far end (a TMUX select pin,
    a ring-sense node, an LDO's or the boost's enable, the eFuse's fault), by optimal assignment. Returns {function net: port}."""
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    tca = next((p for p in parts if p["value"].startswith("TCA9535")), None)
    if tca is None or tca["ref"] not in placement:
        return {}
    import re
    port_pins = {k: v for k, v in tca["names"].items() if re.fullmatch(r"P[01][0-7]", v)}   # pin number -> P00..P17
    funcs = [tca["pins"][k] for k in port_pins]                                       # nets now on the ports
    def pad_xy(ref, num):
        p = next(q for q in parts if q["ref"] == ref)
        x, y, s, r = placement[ref]
        g = geometry(p["fp"], s, r)[4]
        dx, dy = g.get(num, (0.0, 0.0))
        return x + dx, y + dy
    targets = {}
    for f in funcs:
        pts = [pad_xy(q["ref"], k) for q in parts if q["ref"] != tca["ref"] and q["ref"] in placement for k, v in q["pins"].items() if v == f]
        targets[f] = pts
    pins = list(port_pins)
    cost = np.zeros((len(funcs), len(pins)))
    for i, f in enumerate(funcs):
        for j, pn in enumerate(pins):
            px, py = pad_xy(tca["ref"], pn)
            cost[i, j] = min((math.hypot(px - x, py - y) for x, y in targets[f]), default=0.0)
    r, c = linear_sum_assignment(cost)
    before = sum(cost[i, pins.index(k)] for i, k in enumerate(port_pins))
    new = {pins[c[k]]: funcs[i] for k, i in enumerate(r)}
    for pn, f in new.items():
        tca["pins"][pn] = f
    log(f"  expander ports reassigned: {before:.1f} -> {cost[r, c].sum():.1f} mm of straight-line length")
    return {f: port_pins[pn] for pn, f in new.items()}


def run_placer(which, parts, fixed, hdr, iters, seed=1, log=print, init=None):
    rx0, rx1 = ROW_X; ky_top = kc(0, ROW_Y[1])[1]; ky_bot = kc(0, ROW_Y[0])[1]
    region = [(rx0 + 0.15, ky_top + 0.15, rx1 - 0.15, ky_bot - 0.15)]   # courtyards 0.15 inside the edge: every pad >= 0.25 from it
    items, nets = [], {}
    owner = None
    for p in parts:
        r = p["ref"]
        if r[0] == "U":
            owner = zone_of(p, which)
        pins = hdr.get(r, p["pins"])
        for num, n in pins.items():
            if n:
                nets.setdefault(n, []).append((r, num))
        if r in fixed:
            x, y, s, rot = fixed[r]
            items.append(dict(ref=r, geoms={(s, rot): geometry(p["fp"], s, rot)}, fixed=(x, y, s, rot)))
        else:
            g = {}
            for s in ("F", "B"):
                for rot in (0, 90, 180, 270):
                    g[(s, rot)] = geometry(p["fp"], s, rot)
            zx0, zx1 = ZONES[which][zone_of(p, which, owner)]
            # a chip's pins need room for a track along the edge: fine-pitch parts keep EDGE_IC from it, the rest 0.15
            e = EDGE_IC if r[0] == "U" else 0.15
            zr = [(max(rx0 + e, zx0), ky_top + e, min(rx1 - e, zx1), ky_bot - e)]
            items.append(dict(ref=r, geoms=g, regions={"F": zr, "B": zr}))
    # room to escape: no parts within ESCAPE of the stacks' pad rows (either face: their vias go through) or in front of the flex
    # connectors' pads; ICs keep IC_MARGIN, passives the default
    for r, (x, y, s, rot) in fixed.items():
        p = next(q for q in parts if q["ref"] == r)
        x0, y0, x1, y1, _pads = geometry(p["fp"], s, rot)
        if ESCAPE <= 0:
            continue
        if r.startswith("H"):
            box_ = (x0 - ESCAPE, y0, x1 + ESCAPE, y1)
        elif r in ("J5", "J6"):
            box_ = (x0, y0 - ESCAPE, x1, y1)
        else:
            continue
        for face in ("F", "B"):
            items.append(dict(ref=f"KEEP_{r}_{face}", geoms={(face, 0): (*box_, {})}, fixed=(x, y, face, 0)))
    for it in items:
        if it.get("fixed") is None and it["ref"][0] in "UJ":
            it["margin"] = IC_MARGIN
        if it["ref"] in MARGINS.get(which, {}):
            it["margin"] = MARGINS[which][it["ref"]]
    netlist = [(POWER.get(n, 1.0), pins) for n, pins in nets.items()]
    # decoupling: each capacitor between a supply and ground to the pin of the same supply on the part made just before it
    last_ic = None
    for p in parts:
        if p["ref"][0] in "UJ" and p["ref"] not in fixed or p["ref"] in ("J5",):
            last_ic = p
        if p["ref"][0] == "C" and "GND" in p["pins"].values() and last_ic is not None:
            sup = [n for n in p["pins"].values() if n != "GND"][0]
            if sup in POWER or sup in ("VREF", "VMID", "VCOMH", "3V3"):
                ic_pins = [k for k, v in last_ic["pins"].items() if v == sup]
                cap_pin = [k for k, v in p["pins"].items() if v == sup][0]
                if ic_pins:
                    netlist.append((2.0, [(p["ref"], cap_pin), (last_ic["ref"], ic_pins[0])]))
    pl = placer.Placer(items, {"F": region, "B": region}, netlist, margin=0.08, seed=seed)
    if init:   # refine a placement: start from it, cool and short-stepped, overlaps already costly
        pl.init_from(init)
        pl.run(iters=iters, log=log, t0=0.08, step0=0.8, lam0=200.0)
    else:
        pl.init_random()
        pl.run(iters=iters, log=log)
    pl.snap(0.05)
    ok = pl.repair(rounds=120, tries=200, log=log)
    pl.snap(0.05)
    ok = pl.repair(rounds=60, tries=200, log=log)
    if not ok:   # the margin is for routing room; a DRC-legal placement needs only the courtyards apart
        pl.mscale = 0.0
        ok = pl.repair(rounds=60, tries=200, log=log)
    if not ok:   # shove the last few apart, then tidy what that disturbed
        pl.legalise(rounds=300)
        pl.snap(0.05)
        ok = pl.repair(rounds=40, tries=200, log=log)
    if not ok:
        ok = pl.relocate(g=0.25, log=log)
    if not ok:
        ok = pl.nudge(maxd=5.0, log=log)
    if not ok:
        ok = pl.evict(log=log)
    wl, ov, out = pl.total()
    log(f"{which}: wirelength {wl:.1f}, overlap {ov:.3f} mm², outside {out:.3f}, legal {ok}")
    res = {k: v for k, v in pl.result().items() if not k.startswith("KEEP_")}
    return res, (wl, ov, out)


# ------------------------------------------------------------------ the board
def build(which, placement, parts, hdr):
    cfg = BOARDS[which]
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings(); ds.SetBoardThickness(mm(BT)); ds.SetCopperLayerCount(4)
    ds.m_CopperEdgeClearance = mm(RULES["edge"])
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    pts = [kc(x, y) for x, y in outline(which)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
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
        f.SetPath(pcbnew.KIID_PATH(sch_gen.fp_path(cfg["name"], p["ref"])))
        f.SetProperty("Sheetname", "Root"); f.SetProperty("Sheetfile", cfg["name"] + ".kicad_sch")
        if p["ref"].startswith("MP"):   # the posts' pins: hand-soldered at assembly, not parts
            f.SetAttributes(f.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        for k, v in (("MPN", p["mpn"]), ("LCSC", p["lcsc"]), ("Note", p["note"])):
            if v:
                f.SetProperty(k, v)
        pins = hdr.get(p["ref"], p["pins"])
        for pad in f.Pads():
            n = pins.get(pad.GetNumber())
            if n:
                pad.SetNet(net(n))
    t = pcbnew.PCB_TEXT(board); t.SetText(f"{'jack power' if which == 'upper' else 'jack lower'} {PCB_VERSION}")
    t.SetPosition(P(0.0, -5.4)); t.SetLayer(pcbnew.F_Fab); t.SetTextSize(V(0.6, 0.6)); t.SetTextThickness(mm(0.1)); board.Add(t)
    ds.SetAuxOrigin(P(0, 0)); ds.SetGridOrigin(P(0, 0))
    return board


def _pad_rects(board):
    """Every pad as (layers, x0, y0, x1, y1, net) in board-local mm (bounding box; enough for clearance checks here)."""
    out = []
    for f in board.GetFootprints():
        for p in f.Pads():
            bb = p.GetBoundingBox()
            lay = {"F"} if p.IsOnLayer(pcbnew.F_Cu) and not p.IsOnLayer(pcbnew.B_Cu) else {"B"} if p.IsOnLayer(pcbnew.B_Cu) and not p.IsOnLayer(pcbnew.F_Cu) else {"F", "B", "I"}
            out.append((lay, pcbnew.ToMM(bb.GetLeft()) - ORIGIN[0], pcbnew.ToMM(bb.GetTop()) - ORIGIN[1], pcbnew.ToMM(bb.GetRight()) - ORIGIN[0],
                        pcbnew.ToMM(bb.GetBottom()) - ORIGIN[1], p.GetNetname(), p))
    return out


def _rect_dist(px, py, r):
    dx = max(r[1] - px, 0.0, px - r[3]); dy = max(r[2] - py, 0.0, py - r[4])
    return math.hypot(dx, dy)


def fanout_gnd(board, which, via_d=0.45, via_drill=0.2, clr=0.13, width=0.25):
    """A via to the In1 ground plane next to every ground SMD pad (one in the middle of each grounded exposed pad), with a short
    track on the pad's face, so the router never has to reach the plane: candidates round the pad, away from its part's centre
    first, clear of every pad on both faces, the other vias and the board edge."""
    rects = _pad_rects(board)
    gnd = board.FindNet("GND")
    ol = [kc(x, y) for x, y in outline(which)]
    xs = [p[0] for p in ol]; ys = [p[1] for p in ol]
    ex0, ex1, ey0, ey1 = min(xs), max(xs), min(ys), max(ys)       # the jack row's box (vias stay in it)
    ey1 = kc(0, ROW_Y[0])[1]
    vias = []; n_ok = n_fail = 0
    done = set()
    for f in board.GetFootprints():
        cx, cy = pcbnew.ToMM(f.GetPosition().x) - ORIGIN[0], pcbnew.ToMM(f.GetPosition().y) - ORIGIN[1]
        for p in f.Pads():
            if p.GetNetname() != "GND" or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            key = (f.GetReference(), p.GetNumber())
            if key in done:
                continue
            done.add(key)
            side = "B" if p.IsOnLayer(pcbnew.B_Cu) else "F"
            px, py = pcbnew.ToMM(p.GetPosition().x) - ORIGIN[0], pcbnew.ToMM(p.GetPosition().y) - ORIGIN[1]
            w, h = pcbnew.ToMM(p.GetBoundingBox().GetWidth()), pcbnew.ToMM(p.GetBoundingBox().GetHeight())
            cands = []
            if w >= 1.4 and h >= 1.4 and abs(px - cx) < 0.3 and abs(py - cy) < 0.3:   # an exposed pad: via in its middle
                cands = [(px, py)]
            else:
                ang0 = math.atan2(py - cy, px - cx) if math.hypot(px - cx, py - cy) > 0.05 else 0.0
                for dist in (0.45, 0.6, 0.8, 1.0, 1.25, 1.5):
                    for k in range(16):
                        a_ = ang0 + (k // 2 + 1) * (math.pi / 8) * (1 if k % 2 else -1) if k else ang0
                        cands.append((px + (w / 2 + dist) * math.cos(a_) if abs(math.cos(a_)) > 0.7 else px + dist * math.cos(a_),
                                      py + (h / 2 + dist) * math.sin(a_) if abs(math.sin(a_)) > 0.7 else py + dist * math.sin(a_)))
            placed = False
            for vx, vy in cands:
                if not (ex0 + via_d / 2 + 0.3 <= vx <= ex1 - via_d / 2 - 0.3 and ey0 + via_d / 2 + 0.3 <= vy <= ey1 - via_d / 2 - 0.3):
                    continue
                ok = True
                for lay, x0, y0, x1, y1, n, pp in rects:
                    if pp is p or (n == "GND" and (vx, vy) == (px, py)):
                        continue
                    if n == "GND" and _rect_dist(vx, vy, (None, x0, y0, x1, y1)) >= 0:
                        if _rect_dist(vx, vy, (None, x0, y0, x1, y1)) < via_d / 2 + 0.02 and pp is not p:
                            ok = False; break
                        continue
                    if _rect_dist(vx, vy, (None, x0, y0, x1, y1)) < via_d / 2 + clr:
                        ok = False; break
                    # the track from the pad to the via, on the pad's face
                    if side in lay and (vx, vy) != (px, py):
                        for s in range(1, 11):
                            tx, ty = px + (vx - px) * s / 10, py + (vy - py) * s / 10
                            if _rect_dist(tx, ty, (None, x0, y0, x1, y1)) < width / 2 + clr:
                                ok = False; break
                        if not ok:
                            break
                if ok:
                    for qx, qy in vias:
                        if math.hypot(qx - vx, qy - vy) < via_d + 0.15:
                            ok = False; break
                if ok:
                    v = pcbnew.PCB_VIA(board); v.SetPosition(P(vx, vy)); v.SetWidth(mm(via_d)); v.SetDrill(mm(via_drill))
                    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(gnd); v.SetLocked(True); board.Add(v)
                    if (vx, vy) != (px, py):
                        tr = pcbnew.PCB_TRACK(board); tr.SetStart(P(px, py)); tr.SetEnd(P(vx, vy)); tr.SetWidth(mm(width))
                        tr.SetLayer(pcbnew.B_Cu if side == "B" else pcbnew.F_Cu); tr.SetNet(gnd); tr.SetLocked(True); board.Add(tr)
                    vias.append((vx, vy)); placed = True; n_ok += 1
                    break
            if not placed:
                n_fail += 1
    return n_ok, n_fail


GRID_WIDTHS = {"default": 0.127, "GND": 0.25, "VBUS": 0.3, "VSYS": 0.3,   # [C] VBUS/VSYS 0.3: they reach 0.5-pitch pins
               **{n: 0.25 for n in ("SW_B", "SW_3", "CP_R", "CP_A")},            # switching loops
               **{n: 0.15 for n in ("BOOST", "3V3", "P12V5", "N12V", "VNEG_RAW", "OLED_VCC")}}   # rails, all under 60 mA [A]


def grid_route(pcb_path, which, iters=80, time_limit=3000, log=print, g=0.05, margin=0.036):
    """Route with router4 (Ed Q26 = A): 3 routing layers (F, In2, B), In1 the ground plane; then pull tight. Returns (ok, router)."""
    import router4
    b = pcbnew.LoadBoard(pcb_path)
    for t in list(b.GetTracks()):
        b.Remove(t); _KEEP.append(t)   # keep the wrappers alive (KiCad 7 SWIG)
    ol = [kc(x, y) for x, y in outline(which)]
    r = router4.Router4(router4.board_pads(b, ORIGIN), ol, dict(RULES, hole_clearance=0.2), GRID_WIDTHS, g=g, margin=margin, log=log)
    log(f"{which}: grid {r.nx} x {r.ny} x 3 layers, {len(r.nets)} nets")
    ok = r.run(iters=iters, time_limit=time_limit)
    r.smooth()
    log(f"{which}: tracks, vias {r.apply(b, ORIGIN, RULES['via_d'], RULES['via_drill'])}")
    save_board(pcb_path, b)
    return ok, r


def add_planes(pcb_path, which, inner_only=False):
    """Ground: a plane on In1 (before routing, so Freerouting sees it as the plane), and pours on F and B (after routing)."""
    b = pcbnew.LoadBoard(pcb_path)
    gnd = b.FindNet("GND")
    pts = [kc(x, y) for x, y in outline(which)]
    have = {z.GetLayer() for z in b.Zones() if z.GetNetname() == "GND"}
    want = [pcbnew.In1_Cu] if inner_only else [pcbnew.In1_Cu, pcbnew.F_Cu, pcbnew.B_Cu]
    for layer, pri in ((L, 0) for L in want if L not in have):
        z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(gnd); z.SetAssignedPriority(pri)
        z.SetLocalClearance(mm(0.2)); z.SetMinThickness(mm(0.15)); z.SetThermalReliefGap(mm(0.2)); z.SetThermalReliefSpokeWidth(mm(0.3))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if layer == pcbnew.In1_Cu else pcbnew.ZONE_CONNECTION_THT_THERMAL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        ol = z.Outline(); ol.NewOutline()
        for x, y in pts:
            ol.Append(mm(ORIGIN[0] + x), mm(ORIGIN[1] + y))
        b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    save_board(pcb_path, b)


def schematic(which, parts, hdr, path):
    cfg = BOARDS[which]
    comps = []
    for p in parts:
        pins_n = hdr.get(p["ref"], p["pins"])
        nums = sorted(set(pins_n) | set(p["names"]), key=lambda s: (len(s), s))
        if not nums:
            continue
        pl = [(n, p["names"].get(n, n), "passive", "L" if i % 2 == 0 else "R") for i, n in enumerate(nums)]
        comps.append(dict(ref=p["ref"], sym=(p["value"].split()[0] + "_" + p["fp"].split(":")[1])[:60], pins=pl, value=p["value"],
                          footprint=LIB + ":" + fp_libname(p["fp"]), nets={n: pins_n.get(n) for n in nums},
                          fields={k: v for k, v in (("MPN", p["mpn"]), ("LCSC", p["lcsc"])) if v}))
    sch_gen.write(path, f"{cfg['title']} {PCB_VERSION}", cfg["name"], comps, rev=PCB_VERSION,
                  comment=f"knob CAD {CAD_VERSION}; generated by make_boards.py from design.py")


def write_placement(pcb_path, out, which):
    b = pcbnew.LoadBoard(pcb_path)
    to_panel = lambda x, y: (round(pcbnew.ToMM(x) - ORIGIN[0], 4), round(JY - (pcbnew.ToMM(y) - ORIGIN[1]), 4))
    d = dict(cad_version=CAD_VERSION, pcb_version=PCB_VERSION, thickness=BT, outline=outline(which), parts={}, pads=[])
    for f in b.GetFootprints():
        d["parts"][f.GetReference()] = dict(xy=to_panel(f.GetPosition().x, f.GetPosition().y), side="B" if f.IsFlipped() else "F",
                                            rot=f.GetOrientationDegrees(), value=f.GetValue())
        for p in f.Pads():
            d["pads"].append(dict(ref=f.GetReference(), num=p.GetNumber(), net=p.GetNetname(), xy=to_panel(p.GetPosition().x, p.GetPosition().y),
                                  size=(round(pcbnew.ToMM(p.GetSize().x), 4), round(pcbnew.ToMM(p.GetSize().y), 4)),
                                  drill=(round(pcbnew.ToMM(p.GetDrillSize().x), 4), round(pcbnew.ToMM(p.GetDrillSize().y), 4)),
                                  rot=p.GetOrientationDegrees(), side="B" if f.IsFlipped() else "F"))
    json.dump(d, open(out, "w"), indent=1)


def _build_saved(which, allp, fixed, hdr, placement_in, pcb, d, libs, reswap):
    """Build and save a board from a placement {ref: (x, y, side, rot), _tca_ports: ...}; returns (parts, placement_in)."""
    parts = [dict(p, pins=dict(p["pins"])) for p in allp if p["board"] == which]
    placement = dict(placement_in); swap = placement.pop("_tca_ports", None); placement.update(fixed)
    if which == "upper":
        tca = next(p for p in parts if p["value"].startswith("TCA9535"))
        if swap is None or reswap:
            swap = tca_pin_swap(parts, placement); placement_in = dict(placement_in, _tca_ports=swap)
        else:
            port_num = {v: k for k, v in tca["names"].items()}
            for f, port in swap.items():
                tca["pins"][port_num[port]] = f
    write_project(d, BOARDS[which]["name"], RULES, libs, CLASSES)
    save_board(pcb, build(which, placement, parts, hdr))
    return parts, placement_in


def refine(which, allp, fixed, hdr, pin_file, mfile, pcb, d, libs, rounds, log=print):
    """Ed Q26 = A: route, then give the parts round the crowded spots more room, re-place them from where they are (cool, short
    steps), and route again; keep the best. Walled-in pins found before routing get room the same way."""
    import shutil, router4
    best = None
    place = json.load(open(pin_file))
    for rnd in range(rounds):
        if rnd:
            parts = [dict(p, pins=dict(p["pins"])) for p in allp if p["board"] == which]
            init = {k: v for k, v in place.items() if not k.startswith("_")}
            res, _ = run_placer(which, parts, fixed, hdr, int(os.environ.get("REFINE_ITERS", "250000")), seed=rnd, init=init,
                                log=lambda s: None)
            place = dict(res, _tca_ports=place.get("_tca_ports"))
        parts, place = _build_saved(which, allp, fixed, hdr, place, pcb, d, libs, reswap=rnd > 0)
        rb = pcbnew.LoadBoard(pcb)
        isl = router4.Router4(router4.board_pads(rb, ORIGIN), [kc(x, y) for x, y in outline(which)], dict(RULES, hole_clearance=0.2),
                              GRID_WIDTHS, log=lambda *a: None).islands()
        walled = sorted({nm.split(".")[0] for groups in isl.values() for g_ in groups[1:] for nm in g_} - set(fixed))
        hot_parts = set(walled)
        if not walled:
            ok, r = grid_route(pcb, which, iters=int(os.environ.get("GRID_ITERS", "60")), time_limit=int(os.environ.get("GRID_TIME", "900")),
                               g=float(os.environ.get("GRID_G", "0.05")), margin=float(os.environ.get("GRID_M", "0.036")), log=lambda s: None)
            hc = r.hot_cells(); nf = sum(r.failed.values())
            score = (nf, len(hc))
            log(f"{which} refine round {rnd + 1}: {nf} unroutable, {len(hc)} crowded cells")
            if best is None or score < best[0]:
                best = (score, dict(place)); shutil.copy(pcb, pcb + ".best")
            if score == (0, 0):
                break
            # parts whose courtyard (+0.3) holds a crowded cell
            for p in parts:
                if p["ref"] in fixed:
                    continue
                x, y, s, rot = place[p["ref"]]
                x0, y0, x1, y1, _ = geometry(p["fp"], s, rot)
                if any(x + x0 - 0.3 <= hx <= x + x1 + 0.3 and y + y0 - 0.3 <= hy <= y + y1 + 0.3 for _n, _L, hx, hy in hc):
                    hot_parts.add(p["ref"])
        else:
            log(f"{which} refine round {rnd + 1}: walled-in pins on {walled}")
        for r_ in hot_parts:   # small steps, low cap: on a board this full, big margins leave no legal placement
            MARGINS[which][r_] = round(min(MARGINS[which].get(r_, IC_MARGIN if r_[0] in "UJ" else 0.08) + 0.05, 0.25), 3)
        json.dump(MARGINS[which], open(mfile, "w"), indent=1)
    json.dump(best[1], open(pin_file, "w"), indent=1)
    shutil.copy(pcb + ".best", pcb); os.remove(pcb + ".best")
    return best[0]


def main():
    which_list = [w for w in ("upper", "lower") if w in sys.argv] or ["upper", "lower"]
    allp = design.build()
    if os.path.isdir(LIB_DIR):
        import shutil; shutil.rmtree(LIB_DIR)
    done = set()
    for p in allp:
        if p["fp"] not in done:
            save_fp(LIB_DIR, load_fp(pcbnew.BOARD(), p["fp"])); done.add(p["fp"])
    for which in which_list:
        cfg = BOARDS[which]
        d = os.path.join(HERE, cfg["dir"], "kicad"); os.makedirs(d, exist_ok=True)
        parts = [p for p in allp if p["board"] == which]
        fixed = fixed_parts(which, parts)
        hdr = header_nets(parts, fixed)
        pin_file = os.path.join(HERE, cfg["dir"], "placement_in.json")
        mfile = os.path.join(HERE, cfg["dir"], "margins.json")
        MARGINS[which] = json.load(open(mfile)) if os.path.exists(mfile) else {}
        pcb = os.path.join(d, cfg["name"] + ".kicad_pcb")
        libs = [(LIB, "${KIPRJMOD}/../../" + LIB + ".pretty")]
        placing = "--place" in sys.argv or not os.path.exists(pin_file)
        for attempt in range(int(os.environ.get("PLACE_ROUNDS", "4")) if placing else 1):
            parts = [dict(p, pins=dict(p["pins"])) for p in allp if p["board"] == which]
            if placing:
                iters = int(os.environ.get("PLACE_ITERS", "150000"))
                best = None
                for seed in range(1, int(os.environ.get("PLACE_SEEDS", "1")) + 1):
                    res, (wl, ov, out) = run_placer(which, parts, fixed, hdr, iters, seed=seed)
                    if best is None or (ov + out, wl) < best[0]:
                        best = ((ov + out, wl), res)
                json.dump(best[1], open(pin_file, "w"), indent=1)
            placement = json.load(open(pin_file))
            swap = placement.pop("_tca_ports", None)
            placement.update(fixed)
            if which == "upper":
                if swap is None or placing:
                    swap = tca_pin_swap(parts, placement)
                    saved = json.load(open(pin_file)); saved["_tca_ports"] = swap; json.dump(saved, open(pin_file, "w"), indent=1)
                else:
                    tca = next(p for p in parts if p["value"].startswith("TCA9535"))
                    port_num = {v: k for k, v in tca["names"].items()}
                    for f, port in swap.items():
                        tca["pins"][port_num[port]] = f
            write_project(d, cfg["name"], RULES, libs, CLASSES)
            board = build(which, placement, parts, hdr)
            if "--grid" not in sys.argv:
                print(which, "ground vias (placed, no room):", fanout_gnd(board, which))
            save_board(pcb, board)
            if not placing:
                break
            # pins walled in by their neighbours: give those parts more room and place again [the router can never reach them]
            import router4
            rb = pcbnew.LoadBoard(pcb)
            isl = router4.Router4(router4.board_pads(rb, ORIGIN), [kc(x, y) for x, y in outline(which)], dict(RULES, hole_clearance=0.2),
                                  GRID_WIDTHS, log=lambda *a: None).islands()
            refs = sorted({nm.split(".")[0] for groups in isl.values() for g_ in groups[1:] for nm in g_} - set(fixed))
            print(which, f"placement round {attempt + 1}: walled-in pins on {len(isl)} nets, parts {refs}")
            if not refs:
                break
            for r_ in refs:
                MARGINS[which][r_] = round(min(MARGINS[which].get(r_, IC_MARGIN if r_[0] in "UJ" else 0.08) + 0.1, 0.3), 3)
            json.dump(MARGINS[which], open(mfile, "w"), indent=1)
        if "--refine" in sys.argv:
            print(which, "refined:", refine(which, allp, fixed, hdr, pin_file, mfile, pcb, d, libs, int(os.environ.get("REFINE_ROUNDS", "6"))))
            parts, _ = [dict(p, pins=dict(p["pins"])) for p in allp if p["board"] == which], None
            sw = json.load(open(pin_file)).get("_tca_ports")
            if which == "upper" and sw:
                tca = next(p for p in parts if p["value"].startswith("TCA9535")); port_num = {v: k for k, v in tca["names"].items()}
                for f, port in sw.items():
                    tca["pins"][port_num[port]] = f
        schematic(which, parts, hdr, os.path.join(d, cfg["name"] + ".kicad_sch"))
        write_project(d, cfg["name"], RULES, libs, CLASSES)
        if "--grid" in sys.argv and "--refine" not in sys.argv:
            print(which, "grid route complete:", grid_route(pcb, which, iters=int(os.environ.get("GRID_ITERS", "80")),
                                                           time_limit=int(os.environ.get("GRID_TIME", "3000")),
                                                           g=float(os.environ.get("GRID_G", "0.025")),
                                                           margin=float(os.environ.get("GRID_M", "0.018")))[0])
        elif "--route" in sys.argv:
            import kicad7_tools as kt
            # ground is left to the planes: Freerouting skips the GND class (-inc) and sees no plane, so other nets' vias pass In1
            print(which, "routed:", kt.route(pcb, FREEROUTING, passes=int(os.environ.get("ROUTE_PASSES", "100")),
                                             attempts=int(os.environ.get("ROUTE_ATTEMPTS", "3")), edge_inset=RULES["edge"] - 0.15 + 0.005,
                                             extra=("-inc", "GND"), timeout=int(os.environ.get("ROUTE_TIMEOUT", "2400"))))
        add_planes(pcb, which)
        nv, nu, rep = drc(pcb, os.path.join(d, "drc.rpt"))
        print(which, "DRC violations", nv, "unconnected", nu)
        write_placement(pcb, os.path.join(HERE, cfg["dir"], "placement.json"), which)


if __name__ == "__main__":
    main()
