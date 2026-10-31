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

def kicad_facts(path=KICAD_PCB):
    t = open(path).read()
    thick = float(re.search(r"\(general\s*\(thickness ([\d.]+)\)", t).group(1))
    gx, gy = map(float, re.search(r"\(grid_origin ([\d.\-]+) ([\d.\-]+)\)", t).group(1, 2))
    m = re.search(r'\(gr_circle\s*\(center ([\d.\-]+) ([\d.\-]+)\)\s*\(end ([\d.\-]+) ([\d.\-]+)\)', t)
    d = 2 * ((float(m.group(3)) - float(m.group(1))) ** 2 + (float(m.group(4)) - float(m.group(2))) ** 2) ** 0.5
    fps = {}
    for blk in re.split(r'\n\t\(footprint ', t)[1:]:
        name = re.match(r'"footprints:([^"]+)"', blk).group(1)
        layer = re.search(r'\(layer "([^"]+)"\)', blk).group(1)
        x, y = map(float, re.search(r'\(at ([\d.\-]+) ([\d.\-]+)', blk).group(1, 2))
        ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
        fps[ref] = dict(name=name, layer=layer, x=x - gx, y=-(y - gy))   # STEP/world y up
    return dict(thickness=thick, diameter=round(d, 3), fps=fps)

F = kicad_facts()

def board_solid():
    s = import_step(STEP); b = s.bounding_box()
    return Pos(0, 0, -b.min.Z) * s

def components(top_z=None):
    """Envelope boxes on the front face (top_z defaults to the KiCad thickness)."""
    z = board_solid().bounding_box().max.Z if top_z is None else top_z   # on the STEP top face
    out = []
    for ref, f in F["fps"].items():
        if f["name"] in ENVELOPES and f["layer"] == "F.Cu":
            w, dd, h = ENVELOPES[f["name"]]
            out.append(Pos(f["x"], f["y"], z) * Box(w, dd, h, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return out

def wire_pads_ref():
    """W1 pads as 0.02 thin discs under the back face (reference only, the KiCad STEP omits copper)."""
    w = F["fps"]["W1"]
    return [Pos(w["x"] + dx, w["y"] + dy, 0) * Cylinder(0.35, 0.02, align=(Align.CENTER, Align.CENTER, Align.MAX))
            for dx in (-0.5, 0.5) for dy in (-0.5, 0.5)]

if __name__ == "__main__":
    from sheet import Sheet
    b = board_solid(); comps = components(); bb = b.bounding_box()
    asm = Compound(children=[b] + comps + wire_pads_ref(), label="screen-adapter")
    export_step(asm, os.path.join(HERE, "screen-adapter-with-envelopes.step"))
    R = F["diameter"] / 2; T = F["thickness"]; j, u, w = F["fps"]["J1"], F["fps"]["U1"], F["fps"]["W1"]
    sh = Sheet(layout="panel", shape=asm, gap=22, scale=5, label_pad=12)
    sh.hdim("front", -R, R, -R, -R - 2, f"Ø{F['diameter']:.2f} board [K]")
    sh.vdim("front", 0, j["y"], -R, -R - 2, f"{j['y']:.2f} J1 [K]")
    sh.vdim("front", 0, u["y"], R, R + 2, f"{-u['y']:.2f} U1 [K]")
    sh.note("front", -5.3, j["y"] + 2.3, "J1 FPC 14P 0.5 [A] (cable entry ↑)", 6.5)
    sh.note("front", 1.8, u["y"] - 0.3, "U1 CH32V003 QFN-20 [A]", 6.5)
    sh.note("front", -7.0, -1.5, "W1: 4 pads on the back (VCC GND D1 D2), Ø0.7 at 1.0 [A]", 6.5)
    sh.vdim("plan", 0, bb.max.Z, -R, -R - 2, f"{T:.1f} [A] (STEP {bb.max.Z:.2f})")
    sh.vdim("plan", bb.max.Z, bb.max.Z + 1.0, R, R + 2, "1.0 J1 body [A]")
    lines = [f"Round 2-layer board in KiCad (pcbs/screen-adapter/kicad), Ø{F['diameter']:.1f} [A], {T:.1f} thick [A]; DRC clean",
             "Footprints: shared library kicad/footprints.pretty; placed only, not routed",
             "W1 sits over the Ø3.0 wire bore: 4 × 36 AWG from the fixed tube",
             "Component bodies are envelopes [A]; the KiCad STEP is the bare board"]
    for i, l in enumerate(["NOTES"] + lines):
        sh.note("side", sh.bb["side"][1] + 3, R - i * 1.2, l, 8 if i == 0 else 6.5, **(dict(weight="bold") if i == 0 else {}))
    title = "Screen adapter board — v0.1, 2026-10-31"
    sub = ["Source: KiCad kicad/screen-adapter.kicad_pcb (STEP export).", "[K] = from KiCad, [A] = assumed.", "Third-angle projection · mm · plan view drawn front-up"]
    sh.dxf(os.path.join(HERE, "screen-adapter.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "screen-adapter-drawing.png"), title, sub)
    print(F, "step z", round(bb.min.Z, 3), round(bb.max.Z, 3))
