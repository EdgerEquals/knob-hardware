"""Fixed hollow shaft, 4 mm, ONE PIECE (FDM), v0.1 (2026-10-31). Supersedes fixed-hollow-shaft-6mm (two-piece).
Ed: one piece, no spigot or socket joint; a splined top for the knob centre to glue onto. A microcontroller behind
the screen means only 4 x 36 AWG wires go down the bore. Fixed on the dial axis, does not rotate.
Tags: [Ed] = Ed, [K] = read from the KiCad board, [A] = assumed.
Part-local axes: shaft axis = Z (forward = +Z); flange FRONT face (glued to the PCB back) at Z = 0."""
import os, sys, math
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "pcbs/knob-main-pcb"):
    sys.path.insert(0, os.path.join(LIB, d))
import knob_main_pcb as pcb

_board = pcb.board_solid().bounding_box(); _k = pcb.kicad_facts()
P = dict(
    pcb_width=_board.size.X,                       # [K] 49.0
    axis_x=_k["shaft_x"], axis_y=_k["shaft_y"],    # [K] dial axis = H1 shaft hole
    pcb_hole_now=_k["shaft_hole"],                 # [K] 6.2 today
    pcb_hole_new=4.2,     # [A] PCB hole to reduce to 4.2 (not yet changed)
    flange_t=2.0,         # [A]
    od=4.0,               # [Ed]
    bore=1.5,             # [A] through, including the flange
    length=45.0,          # [A] from the flange front face to the top
    spline_len=8.0,       # [A]
    spline_n=6,           # [A] straight-sided splines
    spline_major=4.0,     # [A] = OD
    spline_minor=3.2,     # [A]
    spline_tooth_w=1.0,   # [A] tooth width (straight sides)
    chamfer=0.3,          # [A] top bore
)
P["flange_side"] = P["pcb_width"]
NOTE = "One piece, FDM CF-ASA or PETG; knob bonded on spline with toughened epoxy; 4 x 36 AWG through bore"

def spline_profile(p=P):
    """Splined cross-section as a Face in XY (teeth on the root circle, cut to the major circle, bore removed)."""
    Rm, Rr = p["spline_major"] / 2, p["spline_minor"] / 2
    with BuildSketch() as sk:
        Circle(Rr)
        for i in range(p["spline_n"]):
            a = 360 * i / p["spline_n"]
            with Locations(Location((0, 0, 0), (0, 0, a))):
                Rectangle(Rm + 0.5, p["spline_tooth_w"], align=(Align.MIN, Align.CENTER))
        Circle(Rm, mode=Mode.INTERSECT)
        Circle(p["bore"] / 2, mode=Mode.SUBTRACT)
    return sk.sketch.faces()[0]

def build(p=P):
    A = (Align.CENTER, Align.CENTER, Align.MIN)
    s, t, L, Ls = p["flange_side"], p["flange_t"], p["length"], p["spline_len"]
    body = Pos(0, 0, -t) * Box(s, s, t, align=A)
    body += Cylinder(p["od"] / 2, L - Ls, align=A)
    body += Pos(0, 0, L - Ls) * extrude(spline_profile(p), Ls)
    body -= Pos(0, 0, -t) * Cylinder(p["bore"] / 2, L + t, align=A)
    top_bore = [e for e in body.edges().filter_by(GeomType.CIRCLE)
                if abs(e.radius - p["bore"] / 2) < 1e-6 and abs(e.center().Z - L) < 1e-6]
    return chamfer(top_bore, p["chamfer"])

def placed(shape, p=P):
    z_back = pcb.board_solid().bounding_box().min.Z
    return Pos(p["axis_x"], -p["axis_y"], z_back) * shape

if __name__ == "__main__":
    from sheet import Sheet
    p = P; part = build(); L = p["length"]; Ls = p["spline_len"]; t = p["flange_t"]; s2 = p["flange_side"] / 2
    R = p["od"] / 2; rb = p["bore"] / 2
    export_step(part, os.path.join(HERE, "fixed-hollow-shaft-4mm-onepiece.step"))
    sec = section(part, section_by=Plane.XY.offset(L - Ls / 2)).faces()[0]
    sh = Sheet(part, gap=26, scale=2.2, label_pad=16)
    sh.hdim("front", -s2, s2, -s2, -s2 - 5, f"{p['flange_side']:.1f} flange = PCB width [K]")
    sh.vdim("front", -s2, s2, -s2, -s2 - 5, f"{p['flange_side']:.1f} square [A] 2.0 thick")
    sh.note("front", -s2 + 1.5, s2 - 4, "spline end, Ø1.5 bore through (see SECTION A-A)", 6.5)
    sh.vdim("plan", -t, 0, -s2, -s2 - 4, f"{t:.1f} [A]")
    sh.vdim("plan", 0, L, -R, -R - 8, f"{L:.1f} from flange front [A]")
    sh.vdim("plan", L - Ls, L, R, R + 4, f"{Ls:.1f} spline [A]")
    sh.note("plan", R + 1.5, L - Ls / 2 - 0.5, "A-A", 7, weight="bold")
    sh.vdim("side", -R, R, -(L - Ls) / 2, -(L + 5), f"Ø{p['od']:.1f} [Ed]")
    sh.vdim("side", -rb, rb, t, t + 4, f"Ø{p['bore']:.1f} bore [A]")
    for i, line in enumerate(["NOTES",
        f"1. {NOTE}",
        f"2. PCB hole to reduce to {p['pcb_hole_new']:.1f} mm (not yet changed; H1 is Ø{p['pcb_hole_now']:.1f} today)",
        f"3. Bore Ø{p['bore']:.1f} [A] right through, including the flange; {p['chamfer']:.1f} × 45° chamfer at the top bore [A]",
        f"4. Flange {p['flange_side']:.0f} × {p['flange_side']:.0f} × {t:.0f} [A] glues flat to the PCB back, centred on the dial axis",
        f"   at board ({p['axis_x']:.2f}, {p['axis_y']:.1f}) = H1 in KiCad [K]",
        "5. Fixed shaft: does not rotate"]):
        sh.note("plan", s2 + 5, L + 2 - i * 2.0, line, 8 if i == 0 else 7, weight="bold" if i == 0 else "normal")
    sh.add_section("SECTION A-A", sec, 10, [
        f"{p['spline_n']} straight splines [A], tooth width {p['spline_tooth_w']:.1f} [A]",
        f"major Ø{p['spline_major']:.1f} [A], minor Ø{p['spline_minor']:.1f} [A], bore Ø{p['bore']:.1f} [A]",
        f"spline {Ls:.0f} long at the top [A]; knob centre bonds here"])
    title = "Fixed hollow shaft 4 mm, one piece — v0.1, 2026-10-31"
    sub = ["Square flange + Ø4 shaft + splined top, Ø1.5 bore through.",
           "[Ed] = Ed, [K] = from KiCad board, [A] = assumed.",
           "Third-angle projection · mm · plan view drawn front-up"]
    sh.dxf(os.path.join(HERE, "fixed-hollow-shaft-4mm-onepiece.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "fixed-hollow-shaft-4mm-onepiece-drawing.png"), title, sub)
    print("ok", part.is_valid, round(part.volume, 1), "section area", round(sec.area, 3))
