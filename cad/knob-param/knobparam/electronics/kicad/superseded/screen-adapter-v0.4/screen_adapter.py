"""Reader + drawer for the round screen adapter board. The board is authored in KiCad (single source of truth):
  kicad/screen-adapter.kicad_pcb (made by kicad/make_board.py) -> screen-adapter.step (kicad-cli, board only).
This module holds no board geometry: it reads the outline, thickness and footprint positions from the KiCad file,
imports the STEP, and adds component ENVELOPES [A] (boxes) at the KiCad footprint positions for the drawings.
Local frame: board centre at X = Y = 0 (STEP Y = -KiCad y), board BACK face at Z = 0, front (components) up +Z."""
import os, re, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tools"))
KICAD_PCB = os.path.join(HERE, "kicad", "screen-adapter.kicad_pcb")
STEP = os.path.join(HERE, "screen-adapter.step")
ENVELOPES = {   # [A] component bodies (w, d, h), footprint-local
    "FPC_14P_0.5mm_Top": (10.6, 3.6, 1.0),
    "QFN-20_3x3_P0.4_CH32V003": (3.0, 3.0, 0.75),
}
ENVELOPES_ALL = {**ENVELOPES,   # v0.3 parts kept out of ENVELOPES (holder v0.1 takes comp_h = max of ENVELOPES = J1 1.0)
    "SOT-23-6_TMAG5273": (1.6, 2.9, 1.45),   # [S] TI DBV body 2.90 x 1.60, 1.45 max height
    "C_0402": (1.0, 0.5, 0.5), "R_0402": (1.0, 0.5, 0.35),
}
HALL_Z = 0.65   # [A] TMAG5273 Hall element height above the board top (package centre in plan)

def kicad_facts(path=KICAD_PCB):
    t = open(path).read()
    thick = float(re.search(r"\(general\s*\(thickness ([\d.]+)\)", t).group(1))
    gx, gy = map(float, re.search(r"\(grid_origin ([\d.\-]+) ([\d.\-]+)\)", t).group(1, 2))
    m = [m for m in re.finditer(r'\n\t\(gr_circle\s*\(center ([\d.\-]+) ([\d.\-]+)\)\s*\(end ([\d.\-]+) ([\d.\-]+)\)(.*?)\n\t\)', t, re.S)
         if '"Edge.Cuts"' in m.group(5)][0]   # board outline only (pad primitives also use gr_circle)
    d = 2 * ((float(m.group(3)) - float(m.group(1))) ** 2 + (float(m.group(4)) - float(m.group(2))) ** 2) ** 0.5
    fps = {}
    for blk in re.split(r'\n\t\(footprint ', t)[1:]:
        name = re.match(r'"footprints:([^"]+)"', blk).group(1)
        layer = re.search(r'\(layer "([^"]+)"\)', blk).group(1)
        mm_ = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)', blk)
        x, y = float(mm_.group(1)), float(mm_.group(2)); rot = float(mm_.group(3) or 0)
        ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
        fps[ref] = dict(name=name, layer=layer, x=x - gx, y=-(y - gy), rot=rot)   # STEP/world y up
    return dict(thickness=thick, diameter=round(d, 3), fps=fps)

F = kicad_facts()

def npth_holes(path=KICAD_PCB):
    """NPTH holes (x, y, d) from the KiCad file, board-centre coords, y up (footprints at 0° rotation)."""
    t = open(path).read(); gx, gy = map(float, re.search(r"\(grid_origin ([\d.\-]+) ([\d.\-]+)\)", t).group(1, 2)); out = []
    for blk in re.split(r'\n\t\(footprint ', t)[1:]:
        fx, fy = map(float, re.search(r'\(at ([\d.\-]+) ([\d.\-]+)', blk).group(1, 2))
        for hx, hy, d in re.findall(r'np_thru_hole circle\s*\(at ([\d.\-]+) ([\d.\-]+)\).*?\(drill ([\d.]+)\)', blk, re.S):
            out.append((fx - gx + float(hx), -(fy - gy + float(hy)), float(d)))
    return out

def board_solid():
    """KiCad STEP; kicad-cli 9.0.2 drops the holes for this circular outline, so the NPTH holes are cut here from the KiCad data."""
    s = import_step(STEP); b = s.bounding_box()
    s = Pos(0, 0, -b.min.Z) * s; h = b.max.Z - b.min.Z
    for x, y, d in npth_holes():
        s = s - Pos(x, y, 0) * Cylinder(d / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return s

def components(top_z=None):
    """Envelope boxes on the front face (top_z defaults to the KiCad thickness)."""
    z = board_solid().bounding_box().max.Z if top_z is None else top_z   # on the STEP top face
    out = []
    for ref, f in F["fps"].items():
        if f["name"] in ENVELOPES_ALL and f["layer"] == "F.Cu":
            w, dd, h = ENVELOPES_ALL[f["name"]]
            if round(f.get("rot", 0)) % 180 == 90: w, dd = dd, w
            out.append(Pos(f["x"], f["y"], z) * Box(w, dd, h, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return out

RINGS = dict(gnd_b=(1.6, 2.8), vbus_f=(1.2, 1.8), hole=1.8)   # [K] C1 = TubeRodClamp_Adapter_M1.6 (kicad/make_rodclamp_footprints.py)

def clamp_pads_ref(top_z=None):
    """C1 copper rings as 0.02 thin annuli (reference only, the KiCad STEP omits copper): GND under the back face, VBUS_DATA on top."""
    z = board_solid().bounding_box().max.Z if top_z is None else top_z
    A = (Align.CENTER, Align.CENTER, Align.MIN)
    def ann(a, b, z0): return Pos(0, 0, z0) * (Cylinder(b, 0.02, align=A) - Cylinder(a, 0.02, align=A))
    return [ann(*RINGS["gnd_b"], -0.02), ann(*RINGS["vbus_f"], z)]

if __name__ == "__main__":
    from sheet import Sheet
    b = board_solid(); comps = components(); bb = b.bounding_box()
    asm = Compound(children=[b] + comps + clamp_pads_ref(), label="screen-adapter")
    export_step(asm, os.path.join(HERE, "screen-adapter-with-envelopes.step"))
    R = F["diameter"] / 2; T = F["thickness"]; j, u = F["fps"]["J1"], F["fps"]["U1"]
    sh = Sheet(layout="panel", shape=asm, gap=22, scale=5, label_pad=12)
    sh.hdim("front", -R, R, -R, -R - 2, f"Ø{F['diameter']:.2f} board [K]")
    sh.vdim("front", 0, j["y"], -R, -R - 2, f"{j['y']:.2f} J1 [K]")
    sh.vdim("front", 0, u["y"], R, R + 2, f"{-u['y']:.2f} U1 [K]")
    sh.note("front", -5.3, j["y"] + 2.3, "J1 FPC 14P 0.5 [A] (cable entry ↑)", 6.5)
    sh.note("front", 1.8, u["y"] - 0.3, "U1 CH32V003 QFN-20 [A]", 6.5)
    c2 = F["fps"]["C2"]; sh.note("front", c2["x"] - 3.2, c2["y"] - 1.2, "C2 100n", 6.5)
    sh.vdim("plan", 0, bb.max.Z, -R, -R - 2, f"{T:.1f} [A] (STEP {bb.max.Z:.2f})")
    sh.vdim("plan", bb.max.Z, bb.max.Z + 1.0, R, R + 2, "1.0 J1 body [A]")
    lines = [f"Round 2-layer board in KiCad (electronics/kicad/screen-adapter/kicad), Ø{F['diameter']:.1f} [A], {T:.1f} thick [A]; DRC clean",
             "Footprints: shared library kicad/footprints.pretty; placed only, not routed",
             "v0.2: C1 replaces W1 (wires): data over power on 2 conductors [Ed]",
             "M1.6 rod (VBUS_DATA) through the NPTH Ø1.8; DIN 934 nut (1.3) on the F.Cu ring (Ø2.4–Ø3.6), 3.0 [A] cord room above",
             "v0.4 (knob v0.16b): U3 TMAG5273, R1/R2 and SDA/SCL/HALL_INT removed (dial sensor dropped, rel_sensor=False)",
             f"C2 100n at U1 VDD (6) / VSS (4), ({c2['x']:.2f}, {c2['y']:.2f}); nets VCC [A], GND, VBUS_DATA; schematic + DRC parity, 0 violations (placed, not routed)",
             "Brass tube top end (GND) presses on the B.Cu ring (Ø3.2–Ø5.6); nets GND / VBUS_DATA [A]",
             "C1 at the centre: NPTH Ø1.8 (rings dotted in the front view)",
             "J1 moved to 3.7 and U1 to 3.8 from the centre (were 3.2 / 3.5) to clear the nut",
             "Component bodies are envelopes [A]; the KiCad STEP is the bare board"]
    for i, l in enumerate(["NOTES"] + lines):
        sh.note("side", sh.bb["side"][1] + 3, R - i * 1.2, l, 8 if i == 0 else 6.5, **(dict(weight="bold") if i == 0 else {}))
    title = "Screen adapter board — v0.4, 2026-11-01"
    sub = ["Source: KiCad kicad/screen-adapter.kicad_pcb (STEP export).", "[K] = from KiCad, [A] = assumed.", "Third-angle projection · mm · plan view drawn front-up"]
    sh.dxf(os.path.join(HERE, "screen-adapter.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "screen-adapter-drawing.png"), title, sub)
    print(F, "step z", round(bb.min.Z, 3), round(bb.max.Z, 3))
