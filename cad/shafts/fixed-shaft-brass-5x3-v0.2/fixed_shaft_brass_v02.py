"""Fixed shaft: brass tube 5 x 3 + printed square flange, v0.2 (2026-10-31). Supersedes v0.1 (../fixed-shaft-brass-5x3).
v0.2: the tube length is DERIVED: its top ends at the blind end of the screen-holder socket (holders/screen-holder-v0.1),
which sits 0.3 [A] above the knob v0.1 top (45.5 above the PCB front). The knurl zone = the holder socket engagement.
Supersedes fixed-hollow-shaft-6mm (two-piece printed) and fixed-hollow-shaft-4mm-onepiece (printed spline).
Ed: METAL shaft, brass stock tube Ø5.0 OD x Ø3.0 ID (1.0 wall). Fixed on the dial axis, does not rotate.
A microcontroller behind the screen means only 4 x 36 AWG wires go down the bore.
  TUBE:   length = 45 [A] above the flange front face + the flange thickness; back end flush with the flange back.
          Top 8 [A]: straight knurl for the epoxy bond with the knob centre, or 2 opposed 0.3 flats [A].
          The knurl is NOT modelled as geometry; it is drawn as a hatched zone on the sheets.
  FLANGE: printed CF-ASA or PETG, custom square (no longer tied to the PCB width): 20.0 target [A],
          4.0 thick [A], Ø5.0 bore, centred on the dial axis, glued flat to the PCB back; tube bonded in with epoxy.
          The side shrinks automatically (0.1 steps) until it clears the motor tab pads (read from KiCad) by >= 1.5 [A].
Tags: [Ed] = Ed, [K] = read from the KiCad board, [A] = assumed.
Part-local axes: shaft axis = Z (forward = +Z); flange FRONT face at Z = 0, flange back at Z = -flange_t."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "pcbs/knob-main-pcb", "holders/screen-holder-v0.1"):
    sys.path.insert(0, os.path.join(LIB, d))
import knob_main_pcb as pcb
import screen_holder as holder

_board = pcb.board_solid().bounding_box(); _k = pcb.kicad_facts()
_step_t = _board.max.Z - _board.min.Z   # KiCad STEP board 1.51 (flange front face = PCB back)
H = holder.P
P = dict(
    axis_x=_k["shaft_x"], axis_y=_k["shaft_y"],    # [K] dial axis = H1
    pcb_hole=_k["shaft_hole"],                     # [K] 5.2 NPTH (KiCad PCB v0.3; was 6.2 in v0.2)
    tube_od=5.0,          # [Ed] brass stock
    tube_id=3.0,          # [Ed] brass stock (1.0 wall)
    above_flange=H["z_socket_top"] + _step_t,   # derived: tube top = holder socket blind end (51.8 above the PCB front)
    knurl_len=H["socket_len"],   # = holder socket engagement 6.0 [A]: straight knurl for the epoxy bond, or 2 flats
    flat_depth=0.3,       # [A] alternative: 2 opposed flats
    deburr=0.3,           # [A] 45 deg chamfer/deburr at both bore ends (wire protection)
    flange_side_target=20.0,   # [A] square side
    flange_t=4.0,         # [A]
    flange_bore=5.0,      # [Ed] tube passes through, epoxy bonded
    min_pad_clear=1.5,    # [A] flange edge to the nearest motor tab pad
)
PADS = _k["motor_pads"]   # [K] motor tab pads (x, y, w, h), panel coords

def pad_clearance(side, p=P):
    """Smallest edge-to-edge gap between the flange square (centred on the axis) and any motor pad rectangle."""
    h = side / 2; best = None
    for x, y, w, hh in PADS:
        dx = max(abs(x - p["axis_x"]) - w / 2 - h, 0.0); dy = max(abs(y - p["axis_y"]) - hh / 2 - h, 0.0)
        g = (dx * dx + dy * dy) ** 0.5
        best = g if best is None else min(best, g)
    return best

def flange_side(p=P):
    side = p["flange_side_target"]
    while pad_clearance(side, p) < p["min_pad_clear"] - 1e-9:
        side = round(side - 0.1, 1)
    return side
P["flange_side"] = flange_side()
P["pad_clear"] = pad_clearance(P["flange_side"])
P["tube_len"] = P["above_flange"] + P["flange_t"]
NOTE_TUBE = "Brass tube 5 OD x 3 ID stock, cut to length, knurl dial end only; 4 x 36 AWG through the 3.0 mm bore"
NOTE_LEN = f"Length derived: top at {H['z_socket_top']:.1f} above PCB front = holder socket end (knob top {H['knob_top']:.1f} + {H['run_clear']:.1f} + {H['socket_len']:.0f}); v0.1 was 49.0"
NOTE_FL = "Flange printed CF-ASA or PETG; tube bonded in with epoxy, flush with the back face; flange bonded to PCB back"
NOTE_KN = "Straight knurl for epoxy bond, or 2 flats"
NOTE_PCB = f"PCB hole Ø{_k['shaft_hole']:.1f} NPTH [K] (KiCad PCB v0.3)"
A = (Align.CENTER, Align.CENTER, Align.MIN)

def build_tube(p=P):
    """Tube in flange-relative position: back end at Z = -flange_t (flush with the flange back)."""
    z0 = -p["flange_t"]; L = p["tube_len"]
    t = Pos(0, 0, z0) * (Cylinder(p["tube_od"] / 2, L, align=A) - Cylinder(p["tube_id"] / 2, L, align=A))
    ends = [e for e in t.edges().filter_by(GeomType.CIRCLE) if abs(e.radius - p["tube_id"] / 2) < 1e-6]
    return chamfer(ends, p["deburr"])

def build_flange(p=P):
    s, t = p["flange_side"], p["flange_t"]
    return Pos(0, 0, -t) * (Box(s, s, t, align=A) - Cylinder(p["flange_bore"] / 2, t, align=A))

def placed(shape, p=P):
    z_back = pcb.board_solid().bounding_box().min.Z
    return Pos(p["axis_x"], -p["axis_y"], z_back) * shape

def notes(sh, view, x, ytop, lines, step):
    for i, line in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold" if i == 0 else "normal")
        if isinstance(line, tuple): line, kw = line
        sh.note(view, x, ytop - i * step, line, 8 if i == 0 else 7, **kw)

SUB3 = "Third-angle projection · mm · plan view drawn front-up"

if __name__ == "__main__":
    from sheet import Sheet
    p = P; R = p["tube_od"] / 2; r = p["tube_id"] / 2; t = p["flange_t"]; H = p["above_flange"]
    Lk = p["knurl_len"]; Lt = p["tube_len"]; s2 = p["flange_side"] / 2
    tube = build_tube(); fl = build_flange()
    export_step(tube, os.path.join(HERE, "brass-tube-5x3.step"))
    export_step(fl, os.path.join(HERE, "shaft-flange-printed.step"))
    export_step(Compound(children=[tube, fl]), os.path.join(HERE, "fixed-shaft-brass-5x3-assembled.step"))

    # ---- sheet 1: brass tube (local Z from -t to H) ----
    sh = Sheet(layout="panel", shape=tube, gap=26, scale=3.5, label_pad=16)
    sh.hdim("front", -R, R, -R, -R - 3, f"Ø{p['tube_od']:.1f} OD [Ed]")
    sh.hdim("front", -r, r, R, R + 2.5, f"Ø{p['tube_id']:.1f} ID [Ed]")
    sh.vdim("plan", -t, H, -R, -R - 4, f"{Lt:.2f} tube = {H:.2f} + {t:.0f} flange")
    sh.vdim("plan", H - Lk, H, R, R + 3, f"{Lk:.1f} knurl zone [A]")
    sh.hatch_zone("plan", -R, H - Lk, R, H); sh.hatch_zone("side", -H, -R, -(H - Lk), R)
    sh.vdim("side", -R, R, t, t + 3, f"Ø{p['tube_od']:.1f}")
    notes(sh, "plan", R + 14, H, [NOTE_TUBE, f"{NOTE_KN}: top {Lk:.0f} mm [A]; flats {p['flat_depth']:.1f} deep, opposed [A]",
        f"Deburr / {p['deburr']:.1f} × 45° chamfer at both bore ends (wire protection) [A]",
        f"Back end flush with the flange back face; {H:.2f} above the flange front", NOTE_LEN,
        (f"Ed said shorten: derived {Lt:.2f} is LONGER than v0.1 49.0 [check]", dict(color="red", weight="bold")), NOTE_PCB], 1.5)
    title = "Brass tube 5 × 3 fixed shaft — v0.2, 2026-10-31"
    sub = ["Brass stock tube Ø5.0 × Ø3.0 (1.0 wall), hatched = knurl zone.", "[Ed] = Ed, [A] = assumed.", SUB3]
    sh.dxf(os.path.join(HERE, "brass-tube-5x3.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "brass-tube-5x3-drawing.png"), title, sub)

    # ---- sheet 2: printed flange ----
    # motor tab pads as thin reference rectangles (axis-relative, panel y -> -Y), front view only matters
    refs = [Pos(x - p["axis_x"], -(y - p["axis_y"]), -t) * Box(w, hh, 0.02, align=(Align.CENTER, Align.CENTER, Align.MAX))
            for x, y, w, hh in PADS]
    near = min(PADS, key=lambda q: abs(q[0] - p["axis_x"]))
    nx0 = near[0] - p["axis_x"] - near[2] / 2
    sh = Sheet(layout="panel", shape=Compound(children=[fl] + refs), gap=20, scale=3, label_pad=16)
    sh.hdim("front", -s2, s2, -s2, -s2 - 4, f"{p['flange_side']:.1f} [A]")
    sh.vdim("front", -s2, s2, -s2, -s2 - 4, f"{p['flange_side']:.1f} square [A]")
    sh.hdim("front", -p["flange_bore"] / 2, p["flange_bore"] / 2, 0.0, 4, f"Ø{p['flange_bore']:.1f} bore [Ed]")
    sh.hdim("front", s2, nx0, near[3] / 2, s2 + 8, f"{p['pad_clear']:.2f} clear")
    sh.hdim("front", 0, near[0] - p["axis_x"], near[3] / 2, s2 + 3, f"{near[0] - p['axis_x']:.1f} axis to tab [K]")
    sh.note("front", nx0 - 0.5, -near[3] / 2 - 2.2, "motor tab pads (ref, KiCad M1)", 6.5)
    sh.vdim("plan", -t, 0, -s2, -s2 - 3, f"{t:.1f} [A]")
    notes(sh, "side", 9, s2, [NOTE_FL, "FDM: CF-ASA or PETG",
        f"Custom square: target {p['flange_side_target']:.1f} [A], shrunk to {p['flange_side']:.1f} for >= {p['min_pad_clear']:.1f} [A] to the motor pads",
        f"Clearance flange edge to nearest motor tab pad: {p['pad_clear']:.2f} (motor at {_k['motor_x'] - p['axis_x']:.1f} offset [A])",
        f"Centred on the dial axis at board ({p['axis_x']:.2f}, {p['axis_y']:.1f}) = H1 in KiCad [K]",
        NOTE_PCB, "Check the flange vs. back-side connectors"], 1.6)
    title = "Shaft flange, printed — v0.2, 2026-10-31"
    sub = [f"Square flange {p['flange_side']:.1f} × {p['flange_side']:.1f} × {t:.1f}, Ø5.0 bore for the brass tube.", "[Ed] = Ed, [K] = from KiCad, [A] = assumed.", SUB3]
    sh.dxf(os.path.join(HERE, "shaft-flange-printed.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "shaft-flange-printed-drawing.png"), title, sub)

    # ---- sheet 3: together ----
    pair = Compound(children=[tube, fl])
    sh = Sheet(layout="panel", shape=pair, gap=24, scale=3, label_pad=16)
    sh.hdim("front", -s2, s2, -s2, -s2 - 5, f"{p['flange_side']:.1f} flange")
    sh.vdim("front", -s2, s2, -s2, -s2 - 5, f"{p['flange_side']:.1f}")
    sh.vdim("plan", 0, H, -R, -R - 6, f"{H:.2f} above flange front (derived)")
    sh.vdim("plan", -t, H, R, R + 6, f"{Lt:.2f} tube")
    sh.vdim("plan", -t, 0, -s2, -s2 - 3, f"{t:.1f}")
    sh.hatch_zone("plan", -R, H - Lk, R, H); sh.hatch_zone("side", -H, -R, -(H - Lk), R)
    notes(sh, "plan", s2 + 8, H, [NOTE_TUBE, NOTE_FL, f"Flange {p['flange_side']:.1f} square × {t:.1f}; {p['pad_clear']:.2f} clear of the motor tab pads", f"Hatched top {Lk:.0f} mm [A]: {NOTE_KN.lower()}", NOTE_PCB,
        "Tube back end flush with the flange back face", NOTE_LEN], 2.4)
    title = "Fixed shaft, brass 5 × 3 + flange — v0.2"
    sub = ["2026-10-31. Brass tube bonded into the printed flange.", "[A] values as on the part sheets.", SUB3]
    sh.dxf(os.path.join(HERE, "fixed-shaft-brass-5x3-assembled.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "fixed-shaft-brass-5x3-assembled-drawing.png"), title, sub)
    print("ok", tube.is_valid, fl.is_valid, "tube", Lt, "flange", p["flange_side"], "clear", round(p["pad_clear"], 3))
