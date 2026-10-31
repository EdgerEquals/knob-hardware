"""Authoring script for the KiCad knob main PCB (KiCad is the single source of truth for the board).
Run with the system python that has pcbnew:  /usr/bin/python3 make_board.py
Writes knob-main-pcb.kicad_pcb / .kicad_pro / fp-lib-table, then exports knob-main-pcb.step with kicad-cli.
Contents: Edge.Cuts outline, 1.6 mm board, M1 = footprints:Motor_1220_Tabs at the motor position (offset from the dial axis),
H1 = footprints:Shaft_Hole_NPTH_5.2mm on the dial axis (v0.3; was 6.2 in v0.2). Nothing else.
Tags: [L] layout v5 (scope/knob-module-v1.md + knob-panel-layout/make_v5.py), [A] assumed.
Coordinates: panel top-left = KiCad grid origin (ORIGIN); x right, y down from panel top (same as the layout)."""
import os, json, subprocess, pcbnew

# ---------------- params ----------------
ORIGIN = (100.0, 100.0)               # KiCad position of the panel top-left corner (sheet placement only)
PANEL_W, PANEL_H = 50.5, 128.5        # [L] 10HP x 3U
RAIL = 10.0                           # [L] rail zone top/bottom
CUT_Y0, CAR_INSET, CAR_H = 10.0, 0.8, 20.6   # [L] top-screen carriage
BEZ_GAP, BEZ_D = 4.0, 35.0            # [L]
DIAL_X = PANEL_W / 2                                        # [L] 25.25
DIAL_Y = CUT_Y0 + CAR_INSET + CAR_H + BEZ_GAP + BEZ_D / 2   # [L] 52.9
PCB_T = 1.6                           # [L] FR4
EDGE_CLEAR = 0.75                     # [A] board edge to panel edge (left/right)
RAIL_CLEAR = 0.5                      # [A] board edge to rail-zone line (top/bottom)
CORNER_R = 1.0                        # [A]
# dial / fixed-shaft axis (H1) and motor (M1) are separate (Ed, 2026-10-31: motor offset from the dial axis)
SHAFT_X, SHAFT_Y = DIAL_X, DIAL_Y     # [L] shaft hole on the dial axis
MOTOR_OFFSET = 14.0                   # [A] motor offset TBC, gear/belt drive TBC: centre distance, to the right, same height
MOTOR_X, MOTOR_Y = DIAL_X + MOTOR_OFFSET, DIAL_Y
MOTOR_FP = ("footprints", "Motor_1220_Tabs")   # project library, cad/library/kicad/footprints.pretty
MOTOR_ROT = 0.0                       # tabs side by side along x
SHAFT_FP = ("footprints", "Shaft_Hole_NPTH_5.2mm")   # Ø5.2 NPTH [A] for the Ø5.0 brass tube (v0.2 was 6.2)
# ----------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "knob-main-pcb"
LIBDIR = os.path.normpath(os.path.join(HERE, "..", "..", "..", "kicad", "footprints.pretty"))
mm = pcbnew.FromMM
def P(x, y): return pcbnew.VECTOR2I(mm(ORIGIN[0] + x), mm(ORIGIN[1] + y))

board = pcbnew.BOARD()
ds = board.GetDesignSettings(); ds.SetBoardThickness(mm(PCB_T))
x0, x1 = EDGE_CLEAR, PANEL_W - EDGE_CLEAR
y0, y1 = RAIL + RAIL_CLEAR, PANEL_H - RAIL - RAIL_CLEAR
r = CORNER_R

def seg(a, b):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.05))
    s.SetStart(P(*a)); s.SetEnd(P(*b)); board.Add(s)
def arc(c, start, mid, end):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.05))
    s.SetArcGeometry(P(*start), P(*mid), P(*end)); board.Add(s)
import math
k = r * (1 - math.sqrt(0.5))
seg((x0 + r, y0), (x1 - r, y0)); seg((x1, y0 + r), (x1, y1 - r)); seg((x1 - r, y1), (x0 + r, y1)); seg((x0, y1 - r), (x0, y0 + r))
arc(None, (x1 - r, y0), (x1 - k, y0 + k), (x1, y0 + r))
arc(None, (x1, y1 - r), (x1 - k, y1 - k), (x1 - r, y1))
arc(None, (x0 + r, y1), (x0 + k, y1 - k), (x0, y1 - r))
arc(None, (x0, y0 + r), (x0 + k, y0 + k), (x0 + r, y0))

fp = pcbnew.FootprintLoad(LIBDIR, MOTOR_FP[1])
fp.SetFPID(pcbnew.LIB_ID(MOTOR_FP[0], MOTOR_FP[1]))
fp.SetReference("M1"); fp.SetPosition(P(MOTOR_X, MOTOR_Y)); fp.SetOrientationDegrees(MOTOR_ROT)
board.Add(fp)
h = pcbnew.FootprintLoad(LIBDIR, SHAFT_FP[1])
h.SetFPID(pcbnew.LIB_ID(SHAFT_FP[0], SHAFT_FP[1]))
h.SetReference("H1"); h.SetPosition(P(SHAFT_X, SHAFT_Y))
board.Add(h)
ds.SetAuxOrigin(P(0, 0)); ds.SetGridOrigin(P(0, 0))

pcb_path = os.path.join(HERE, NAME + ".kicad_pcb")
pcbnew.SaveBoard(pcb_path, board)
json.dump({"meta": {"filename": NAME + ".kicad_pro", "version": 1}, "board": {}, "libraries": {}}, open(os.path.join(HERE, NAME + ".kicad_pro"), "w"), indent=2)
open(os.path.join(HERE, "fp-lib-table"), "w").write(
    '(fp_lib_table\n  (version 7)\n  (lib (name "footprints")(type "KiCad")(uri "${KIPRJMOD}/../../../kicad/footprints.pretty")(options "")(descr "Ed project footprints"))\n)\n')
step = os.path.join(HERE, "..", NAME + ".step")
subprocess.run(["kicad-cli", "pcb", "export", "step", "--grid-origin", "--force", "-o", step, pcb_path], check=True)
print("board", x0, x1, y0, y1, "M1 at", MOTOR_X, MOTOR_Y, "H1 at", SHAFT_X, SHAFT_Y)
