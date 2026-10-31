"""Knob stack assembly v0.2 (2026-10-31): main PCB + 1220 motor (offset) + two-piece 6 mm fixed shaft.
Nothing else (no panel, gears or dial). Supersedes v0.1 (kept in ../knob-stack-v0.1 as a snapshot).
All parts come from the library by import/parameter; positions are read from the KiCad board:
  PCB    pcbs/knob-main-pcb  (KiCad STEP; H1 = Ø6.2 shaft hole on the dial axis, M1 = motor tabs at the offset)
  motor  motors/1220-coreless-planetary  (VARIANTS["motor-1220"]) end cap on the PCB FRONT face at M1
  shaft  shafts/fixed-hollow-shaft-6mm   base flange flat on the PCB BACK face at H1, top bonded on the spigot
World axes as in tools/sheet.py (X panel x, Y = -panel y, Z = -depth behind the panel front)."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "motors/1220-coreless-planetary", "pcbs/knob-main-pcb", "shafts/fixed-hollow-shaft-6mm"):
    sys.path.insert(0, os.path.join(LIB, d))
import motor_gearbox as mg
import knob_main_pcb as pcb
import fixed_hollow_shaft_6mm as shaft
from sheet import Sheet

M = mg.VARIANTS["motor-1220"]
F = pcb.kicad_facts()
SP = shaft.P
MOTOR_OFFSET = F["motor_x"] - F["shaft_x"]   # [A] 14.0 in make_board.py: motor offset TBC, gear/belt drive TBC

def motor_placed():
    m = mg.build(M)   # local: axis +X, end-cap rear face at X=0, tabs along Y
    return Pos(F["motor_x"], -F["motor_y"], -pcb.Z_PCB_FRONT) * Rot(0, 0, -90) * Rot(0, -90, 0) * m

if __name__ == "__main__":
    board = pcb.board_solid(); motor = motor_placed()
    base, top = shaft.build_pair()
    base = shaft.placed(base); top = shaft.placed(top)
    asm = Compound(children=[board, motor, base, top], label="knob-stack-v0.2")
    export_step(asm, os.path.join(HERE, "knob-stack-v0.2.step"))

    bb = board.bounding_box(); zf = bb.max.Z; zb = bb.min.Z     # PCB front / back faces
    x0, x1, y0, y1 = bb.min.X, bb.max.X, -bb.max.Y, -bb.min.Y
    hx, hy, mx, my = F["shaft_x"], F["shaft_y"], F["motor_x"], F["motor_y"]
    R = M["body_d"] / 2; Rs = SP["od"] / 2; s2 = SP["flange_side"] / 2
    Lm = M["motor_len"] + M["gearbox_len"] + M["boss_len"]; Lt = Lm + M["shaft_len"]
    z_motor_front, z_motor_tip = zf + Lm, zf + Lt
    sbb = top.bounding_box(); z_shaft_top = sbb.max.Z
    fbb = base.bounding_box(); z_fl_back = fbb.min.Z
    clash = base.intersect(motor)
    clash_vol = sum(c.volume for c in (clash if isinstance(clash, (list, ShapeList)) else [clash]) if c is not None) if clash is not None else 0.0
    print("shaft top above PCB front", round(z_shaft_top - zf, 2), "motor", Lm, Lt, "flange/tab clash vol", round(clash_vol, 3))

    sh = Sheet(asm, gap=30, scale=1.15, label_pad=20)
    # front view
    sh.hdim("front", hx, mx, -hy, -hy - R - 6, f"{MOTOR_OFFSET:.1f} motor offset [A] TBC")
    sh.hdim("front", x0, x1, -y1, -y1 - 8, f"{x1 - x0:.2f} PCB")
    sh.vdim("front", -hy + s2, -hy - s2, x0, x0 - 8, f"{SP['flange_side']:.1f} flange (hidden, behind PCB)")
    sh.vdim("front", -y0, -y1, x1, x1 + 8, f"{y1 - y0:.2f} PCB")
    sh.note("front", x0 + 2, -hy + R + 3, "shaft (dial axis, H1)", 6.5)
    sh.note("front", mx - 4, -hy + R + 3, "motor (M1)", 6.5)
    sh.note("front", x0 + 2, -hy - R - 14, "[A] motor offset TBC, gear/belt drive TBC", 6.5)
    sh.note("front", x0 + 2, -hy - R - 17, f"shaft height = 45.0 − STEP board {zf - zb:.2f}", 6.5)
    # plan view (y = Z, front up)
    sh.vdim("plan", zf, z_shaft_top, hx - Rs, x0 - 12, f"{z_shaft_top - zf:.1f} shaft above PCB front")
    sh.vdim("plan", zf, z_motor_front, mx + R, x1 + 5, f"{Lm:.1f} motor")
    sh.vdim("plan", zf, z_motor_tip, mx + R, x1 + 12, f"{Lt:.1f} to motor shaft tip")
    sh.vdim("plan", z_fl_back, zb, x0, x0 - 4, f"{SP['flange_t']:.1f} flange")
    if clash_vol > 1e-6:
        sh.note("plan", x1 + 18, zb, "flange needs relief for motor tabs [check]", 7, color="red", weight="bold")
        sh.note("side", -zb + 3, -hy - s2 - 6, "flange needs relief for motor tabs [check]", 7, color="red", weight="bold")
    title = "Knob stack v0.2 — PCB + 1220 motor + 6 mm shaft"
    sub = ["2026-10-31. PCB = KiCad STEP v0.2 (H1 shaft hole, M1 offset motor).",
           "Motor v0.1 + shaft 6 mm v0.1 by parameter. [A] = assumed.",
           "Third-angle projection · mm · plan view drawn front-up"]
    sh.dxf(os.path.join(HERE, "knob-stack-v0.2.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "knob-stack-v0.2-drawing.png"), title, sub)
