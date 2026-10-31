"""Knob stack assembly v0.3 (2026-10-31): main PCB + 1220 motor (offset) + brass 5x3 fixed shaft with printed flange.
Nothing else (no panel, gears or dial). Supersedes v0.2 (kept in ../knob-stack-v0.2, 6 mm two-piece shaft).
All parts come from the library by import/parameter; positions are read from the KiCad board:
  PCB    pcbs/knob-main-pcb  (KiCad STEP; H1 = Ø5.2 NPTH on the dial axis, M1 = motor tabs at the offset)
  motor  motors/1220-coreless-planetary  (VARIANTS["motor-1220"]) end cap on the PCB FRONT face at M1
  shaft  shafts/fixed-shaft-brass-5x3   flange front face bonded to the PCB BACK face at H1; the tube passes
         through H1 and runs forward, its back end flush with the flange back face
World axes as in tools/sheet.py (X panel x, Y = -panel y, Z = -depth behind the panel front)."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "motors/1220-coreless-planetary", "pcbs/knob-main-pcb", "shafts/fixed-shaft-brass-5x3"):
    sys.path.insert(0, os.path.join(LIB, d))
import motor_gearbox as mg
import knob_main_pcb as pcb
import fixed_shaft_brass as shaft
from sheet import Sheet

M = mg.VARIANTS["motor-1220"]
F = pcb.kicad_facts()
SP = shaft.P
MOTOR_OFFSET = F["motor_x"] - F["shaft_x"]   # [A] 14.0 in make_board.py: motor offset TBC, gear/belt drive TBC

def motor_placed():
    m = mg.build(M)   # local: axis +X, end-cap rear face at X=0, tabs along Y
    return Pos(F["motor_x"], -F["motor_y"], -pcb.Z_PCB_FRONT) * Rot(0, 0, -90) * Rot(0, -90, 0) * m

def vol(s):
    if s is None: return 0.0
    items = s if isinstance(s, (list, ShapeList)) else [s]
    return sum(c.volume for c in items if c is not None)

if __name__ == "__main__":
    board = pcb.board_solid(); motor = motor_placed()
    tube = shaft.placed(shaft.build_tube()); fl = shaft.placed(shaft.build_flange())
    asm = Compound(children=[board, motor, tube, fl], label="knob-stack-v0.3")
    export_step(asm, os.path.join(HERE, "knob-stack-v0.3.step"))

    bb = board.bounding_box(); zf = bb.max.Z; zb = bb.min.Z     # PCB front / back faces (STEP)
    x0, x1, y0, y1 = bb.min.X, bb.max.X, -bb.max.Y, -bb.min.Y
    hx, hy, mx, my = F["shaft_x"], F["shaft_y"], F["motor_x"], F["motor_y"]
    R = M["body_d"] / 2; Rs = SP["tube_od"] / 2; s2 = SP["flange_side"] / 2; ft = SP["flange_t"]
    Lm = M["motor_len"] + M["gearbox_len"] + M["boss_len"]; Lt = Lm + M["shaft_len"]
    z_motor_front, z_motor_tip = zf + Lm, zf + Lt
    tbb = tube.bounding_box(); z_tube_top, z_tube_back = tbb.max.Z, tbb.min.Z
    fbb = fl.bounding_box(); z_fl_back, z_fl_front = fbb.min.Z, fbb.max.Z
    pairs = {"tube/PCB": (tube, board), "tube/motor": (tube, motor), "flange/PCB": (fl, board), "flange/motor": (fl, motor)}
    clashes = {k: vol(a.intersect(b)) for k, (a, b) in pairs.items()}
    clashes = {k: v for k, v in clashes.items() if v > 1e-6}
    near = min(F["motor_pads"], key=lambda q: abs(q[0] - hx)); pad_edge = near[0] - near[2] / 2
    clear = pad_edge - (hx + s2)
    print("tube top above PCB front", round(z_tube_top - zf, 2), "tube back", round(z_tube_back, 3), "flange back", round(z_fl_back, 3),
          "flange front vs PCB back", round(z_fl_front - zb, 4), "motor", Lm, Lt, "pad clear", round(clear, 3), "clashes", clashes,
          "hole", F["shaft_hole"])

    sh = Sheet(asm, gap=48, scale=1.15, label_pad=20)
    # front view
    sh.hdim("front", hx, mx, -hy, -hy - R - 6, f"{MOTOR_OFFSET:.1f} motor offset [A] TBC")
    sh.hdim("front", x0, x1, -y1, -y1 - 8, f"{x1 - x0:.2f} PCB")
    sh.vdim("front", -hy + s2, -hy - s2, x0, x0 - 8, f"{SP['flange_side']:.1f} flange (hidden, behind PCB)")
    sh.vdim("front", -y0, -y1, x1, x1 + 8, f"{y1 - y0:.2f} PCB")
    sh.note("front", x0 + 2, -hy + R + 3, f"brass tube Ø{SP['tube_od']:.0f}×{SP['tube_id']:.0f} (H1 Ø{F['shaft_hole']:.1f} NPTH)", 6.5)
    sh.note("front", mx + 1, -hy + R + 3, "motor (M1)", 6.5)
    sh.note("front", x0 + 2, -hy - R - 14, "[A] motor offset TBC, gear/belt drive TBC", 6.5)
    sh.note("front", x0 + 2, -hy - R - 17, f"tube height = {SP['above_flange']:.1f} − STEP board {zf - zb:.2f}", 6.5)
    # plan view (y = Z, front up)
    sh.vdim("plan", zf, z_tube_top, hx - Rs, x0 - 12, f"{z_tube_top - zf:.2f} tube above PCB front")
    sh.vdim("plan", zf, z_motor_front, mx + R, x1 + 5, f"{Lm:.1f} motor")
    sh.vdim("plan", zf, z_motor_tip, mx + R, x1 + 12, f"{Lt:.1f} to motor shaft tip")
    sh.vdim("plan", z_fl_back, zb, hx - s2, x0 - 4, f"{ft:.1f} flange")
    sh.hdim("plan", hx - s2, hx + s2, z_fl_back, z_fl_back - 4, f"{SP['flange_side']:.1f} flange")
    sh.hdim("plan", hx + s2, pad_edge, zb, z_fl_back - 10, f"{clear:.2f} flange to tab pad [K]")
    sh.note("plan", x1 + 18, zb - 2, "flange bonded to PCB back; tube flush with flange back", 6.5)
    if clashes:
        txt = "CLASH: " + ", ".join(f"{k} {v:.3f} mm³" for k, v in clashes.items()) + " [check]"
        sh.note("plan", x1 + 18, zb - 6, txt, 7, color="red", weight="bold")
        sh.note("side", -zb + 3, -hy - s2 - 6, txt, 7, color="red", weight="bold")
    title = "Knob stack v0.3 — PCB + 1220 motor + brass shaft"
    sub = [f"2026-10-31. PCB = KiCad STEP v0.3 (H1 Ø{F['shaft_hole']:.1f} NPTH, M1 offset motor).",
           "Motor v0.1 + brass 5×3 tube + printed flange v0.1. [A] = assumed.",
           "Third-angle projection · mm · plan view drawn front-up"]
    sh.dxf(os.path.join(HERE, "knob-stack-v0.3.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "knob-stack-v0.3-drawing.png"), title, sub)
