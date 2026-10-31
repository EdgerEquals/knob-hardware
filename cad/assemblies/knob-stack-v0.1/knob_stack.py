"""Knob stack assembly v0.1 (2026-10-31): main PCB + 1220 motor soldered on.
Imports the library parts by parameter (no copied geometry):
  PCB: the KiCad STEP (pcbs/knob-main-pcb/knob-main-pcb.step, exported by kicad-cli), via knob_main_pcb.board_solid();
       motor position and board thickness are read from the .kicad_pcb (KiCad = single source of truth)
  motors/1220-coreless-planetary/motor_gearbox.py  (VARIANTS["motor-1220"])
Motor: rear end cap on the board front face, tabs through the board slots, axis perpendicular to the board
on the dial centre, shaft pointing forward (+Z, toward the panel). World axes as in tools/sheet.py."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "motors/1220-coreless-planetary", "pcbs/knob-main-pcb"):
    sys.path.insert(0, os.path.join(LIB, d))
import motor_gearbox as mg
import knob_main_pcb as pcb
from sheet import Sheet

MOTOR_VARIANT = "motor-1220"
M = mg.VARIANTS[MOTOR_VARIANT]

F = pcb.kicad_facts()

def motor_placed():
    m = mg.build(M)   # local: axis +X, end-cap rear face at X=0, tabs spaced along Y
    loc = Pos(F["motor_x"], -F["motor_y"], -pcb.Z_PCB_FRONT) * Rot(0, 0, -90) * Rot(0, -90, 0)
    return loc * m

if __name__ == "__main__":
    board = pcb.board_solid(); motor = motor_placed()
    asm = Compound(children=[board, motor], label="knob-stack-v0.1")
    export_step(asm, os.path.join(HERE, "knob-stack-v0.1.step"))
    bb = motor.bounding_box(); print("motor bbox", bb.min, bb.max)
    L = M["motor_len"] + M["gearbox_len"] + M["boss_len"]; Lt = L + M["shaft_len"]
    bbb = board.bounding_box()
    zf = -pcb.Z_PCB_FRONT; zb = bbb.min.Z
    x0, x1, y0, y1 = bbb.min.X, bbb.max.X, -bbb.max.Y, -bbb.min.Y; r = M["body_d"] / 2
    DX, DY = F["motor_x"], F["motor_y"]
    sh = Sheet(layout="panel", shape=Compound(children=[board, motor]))
    # front view
    sh.hdim("front", x0, x1, -y1, -y1 - 9, f"{x1 - x0:.2f} board")
    sh.vdim("front", -y0, -y1, x0, x0 - 9, f"{y1 - y0:.2f} board")
    sh.hdim("front", x0, DX, -y0, -y0 + 7, f"{DX - x0:.2f} to motor axis")
    sh.vdim("front", -y0, -DY, x1, x1 + 7, f"{DY - y0:.2f} to motor axis")
    sh.hdim("front", DX - r, DX + r, -DY - r, -DY - r - 5, f"Ø{M['body_d']:.1f} motor")
    # side view (horizontal = -Z: board at right, motor runs left toward the panel)
    sh.hdim("side", -zf, -(zf + L), -DY + r, -DY + r + 6, f"{L:.1f} motor + gearbox")
    sh.hdim("side", -zf, -(zf + Lt), -DY + r, -DY + r + 12, f"{Lt:.1f} to shaft tip")
    sh.hdim("side", -zf, -zb, -y1, -y1 - 4, f"{F['thickness']:.1f} PCB")
    sh.note("side", -zf - 40, -DY - r - 4, "end cap on PCB front face; tabs through slots", 6.5)
    sh.note("side", -zf - 30, -y1 - 13, f"PCB front face at {pcb.Z_PCB_FRONT:.1f} behind panel front [L]", 6.5)
    title = "Knob stack v0.1 — PCB + 1220 motor, 2026-10-31"
    sub = ["PCB = KiCad STEP (knob-main-pcb v0.1); motor-1220 v0.1 by parameter.",
           "Motor dims from listings, verify with calipers. [A] = assumed.",
           "Third-angle projection · mm · plan view drawn front-up (shaft up)"]
    sh.dxf(os.path.join(HERE, "knob-stack-v0.1.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "knob-stack-v0.1-drawing.png"), title, sub)
