"""Authoring script for the KiCad knob main PCB (KiCad is the single source of truth for the board).
Run with the system python that has pcbnew:  /usr/bin/python3 make_board.py
Writes knob-main-pcb.kicad_pcb / .kicad_pro / fp-lib-table, then exports knob-main-pcb.step with kicad-cli.
Contents: Edge.Cuts outline, 1.6 mm board, M1 = footprints:Motor_1220_Tabs at the motor position (offset from the dial axis),
H1 = footprints:Shaft_Hole_NPTH_5.2mm on the dial axis (v0.3; was 6.2 in v0.2).
H2 = footprints:Bearing_F682ZZ_Press_NPTH_5.0mm, encoder take-off bearing, ENC_CD below the dial axis (v0.4); v0.5 flipped H2 to the back; v0.6 (2026-10-31) puts H2 back on the FRONT: the bearing is pressed in from the front through the base cradle
floor and into the PCB (locating dowel for gluing the cradle), flange on the cradle floor. Hole Ø5.0 NPTH unchanged.
v0.7 (2026-10-31): H2 rotated 3.0° [A] about the dial axis toward the motor side (still 19.0 from the axis) so the two idler
pinions at 120°/240° clear the motor.
v0.8 (2026-10-31): H1 = TubeRodClamp_Main_M1.6: the brass tube (GND) is soldered on a F.Cu ring pad, the M1.6 rod (VBUS_DATA,
data over power) passes an NPTH Ø1.8 and clamps on a B.Cu ring pad. Nets GND, VBUS_DATA [A]. Nothing else.
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
# encoder take-off (encoder-takeoff v0.1): bearing hole H2 below the dial axis (panel y down = 90° from the motor) [A]
ENC_CD = 19.0                         # (90T bottom internal ring - 14T encoder pinion) x m0.5 / 2, see encoder_takeoff.py
# v0.7: the encoder + 2 idler pinion set (120° apart) is rotated by ENC_SET_ROT so the idler nearest the motor clears the
# motor body by 0.5 [A] (at 0° it would be at 30° from the motor, 9.81 from its axis: overlap). Positive = toward the motor side.
ENC_SET_ROT = 3.0                     # [A] degrees, minimum 2.88 for 0.5 clearance, rounded up
import math as _m
ENC_X, ENC_Y = DIAL_X + ENC_CD * _m.sin(_m.radians(ENC_SET_ROT)), DIAL_Y + ENC_CD * _m.cos(_m.radians(ENC_SET_ROT))
ENC_FP = ("footprints", "Bearing_F682ZZ_Press_NPTH_5.0mm")   # Ø5.0 NPTH press fit for F682ZZ 2x5x2.3 [A]
SHAFT_FP = ("footprints", "TubeRodClamp_Main_M1.6")   # v0.8: brass tube SOLDERED on a F.Cu ring (GND), M1.6 rod [A] through NPTH Ø1.8, B.Cu clamp ring (VBUS_DATA)
# (v0.3–v0.7: Shaft_Hole_NPTH_5.2mm for the tube through the board)
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
NETS = {n: pcbnew.NETINFO_ITEM(board, n) for n in ("GND", "VBUS_DATA")}   # [A] net names
for n in NETS.values(): board.Add(n)
for pad in h.Pads():
    if pad.GetNumber() == "1": pad.SetNet(NETS["GND"])         # tube solder ring, F.Cu
    elif pad.GetNumber() == "2": pad.SetNet(NETS["VBUS_DATA"]) # rod clamp ring, B.Cu
e = pcbnew.FootprintLoad(LIBDIR, ENC_FP[1])
e.SetFPID(pcbnew.LIB_ID(ENC_FP[0], ENC_FP[1]))
e.SetReference("H2"); e.SetPosition(P(ENC_X, ENC_Y))
board.Add(e)
# v0.6: no flip (v0.5 flipped H2 to B); the bearing inserts from the FRONT through the base cradle v0.3 floor
ds.SetAuxOrigin(P(0, 0)); ds.SetGridOrigin(P(0, 0))

pcb_path = os.path.join(HERE, NAME + ".kicad_pcb")
pcbnew.SaveBoard(pcb_path, board)
json.dump({"meta": {"filename": NAME + ".kicad_pro", "version": 1}, "board": {}, "libraries": {}}, open(os.path.join(HERE, NAME + ".kicad_pro"), "w"), indent=2)
open(os.path.join(HERE, "fp-lib-table"), "w").write(
    '(fp_lib_table\n  (version 7)\n  (lib (name "footprints")(type "KiCad")(uri "${KIPRJMOD}/../../../kicad/footprints.pretty")(options "")(descr "Ed project footprints"))\n)\n')
step = os.path.join(HERE, "..", NAME + ".step")
subprocess.run(["kicad-cli", "pcb", "export", "step", "--grid-origin", "--force", "-o", step, pcb_path], check=True)
print("board", x0, x1, y0, y1, "M1 at", MOTOR_X, MOTOR_Y, "H1 at", SHAFT_X, SHAFT_Y, "H2 at", ENC_X, ENC_Y)
