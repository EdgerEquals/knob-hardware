"""Authoring script for the round screen adapter board (KiCad is the single source of truth for this board).
Run with the system python that has pcbnew:  /usr/bin/python3 make_board.py
Writes screen-adapter.kicad_pcb / .kicad_pro / fp-lib-table, then exports ../screen-adapter.step with kicad-cli.
Contents: round Edge.Cuts outline, 2 layers, 1.0 thick [A]; footprints from the shared library (cad/library/kicad/footprints.pretty):
  J1 = FPC_14P_0.5mm_Top   for the 0.71" round TFT tail (14 pin, 0.5 pitch [A], Zhunyi Z07101-P14)
  U1 = QFN-20_3x3_P0.4_CH32V003   CH32V003F4U6 [A]
  C1 = TubeRodClamp_Adapter_M1.6   v0.2 (2026-10-31): NPTH Ø1.8 for the M1.6 rod; B.Cu ring GND on the tube top, F.Cu ring VBUS_DATA
       under the thin nut (data over power; replaces W1, the 4 wire pads)
  v0.3 (2026-10-31, Ed): U3 = SOT-23-6_TMAG5273  TI TMAG5273 3D Hall sensor (control-dial angle, magnet Ø3x1 N52 in the dial
       hub web below), I2C to U1 (PC1 SDA pin 8, PC2 SCL pin 9; VDD pin 6, VSS pin 4 [CH32V003 DS]); INT to PC3 (pin 10) [A];
       C2 100 nF 0402 decoupling at U3 VCC; R1/R2 4.7k 0402 I2C pull-ups [A]. Nets VCC [A: 3.3 V rail, regulator TBC], GND, SDA, SCL.
       Top nut is now a DIN 934 (1.3) with 3.0 cord room above (holder v0.5).
Placed only, no routing (ratsnest left for the layout). Grid origin = board centre (x right, y down in KiCad)."""
import os, json, subprocess, pcbnew

ORIGIN = (100.0, 100.0)     # KiCad position of the board centre (sheet placement only)
BOARD_D = 15.5              # [A] <= 18 (Ed); smallest round that holds J1 with 0.3 courtyard-to-edge
BOARD_T = 1.0               # [A]
J1_POS = (0.0, -3.7)        # [A] KiCad coords (y up = negative); v0.2: 0.5 out for the M1.6 nut at the centre (was -3.2)
U1_POS = (0.0, 3.8)         # [A] v0.2: was 3.5
C1_POS = (0.0, 0.0)         # centre: tube / rod clamp (v0.2 replaces the W1 wire pads)
U3_POS, U3_ROT = (5.7, 0.2), 90.0   # [A] v0.3 TMAG5273: r 5.70 from the dial axis = magnet radius in control dial v0.7
C2_POS = (3.3, 3.2)         # [A] 100 nF at U3
R1_POS, R2_POS = (-3.3, 2.6), (-3.3, 3.6)   # [A] I2C pull-ups
EDGE_CLEAR_CU = 0.3         # [A] copper to board edge (default 0.5 relaxed for the small board)

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "screen-adapter"
LIBDIR = os.path.normpath(os.path.join(HERE, "..", "..", "..", "kicad", "footprints.pretty"))
mm = pcbnew.FromMM
def P(x, y): return pcbnew.VECTOR2I(mm(ORIGIN[0] + x), mm(ORIGIN[1] + y))

board = pcbnew.BOARD()
ds = board.GetDesignSettings(); ds.SetBoardThickness(mm(BOARD_T)); ds.SetCopperLayerCount(2)
ds.m_CopperEdgeClearance = mm(EDGE_CLEAR_CU)
c = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_CIRCLE); c.SetLayer(pcbnew.Edge_Cuts); c.SetWidth(mm(0.05))
c.SetCenter(P(0, 0)); c.SetEnd(P(BOARD_D / 2, 0)); board.Add(c)

def place(fpname, ref, pos, back=False, rot=0.0):
    fp = pcbnew.FootprintLoad(LIBDIR, fpname); fp.SetFPID(pcbnew.LIB_ID("footprints", fpname))
    fp.SetReference(ref); fp.SetPosition(P(*pos))
    if rot: fp.SetOrientationDegrees(rot)
    board.Add(fp)   # add first, then flip (flipping an unparented footprint crashes pcbnew 9)
    if back: fp.Flip(P(*pos), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
    return fp
place("FPC_14P_0.5mm_Top", "J1", J1_POS)
u1 = place("QFN-20_3x3_P0.4_CH32V003", "U1", U1_POS)
c1 = place("TubeRodClamp_Adapter_M1.6", "C1", C1_POS)
u3 = place("SOT-23-6_TMAG5273", "U3", U3_POS, rot=U3_ROT)
c2 = place("C_0402", "C2", C2_POS); r1 = place("R_0402", "R1", R1_POS); r2 = place("R_0402", "R2", R2_POS)
for fp, v in ((u3, "TMAG5273A1"), (c2, "100n"), (r1, "4k7"), (r2, "4k7"), (u1, "CH32V003F4U6")): fp.SetValue(v)
NETS = {n: pcbnew.NETINFO_ITEM(board, n) for n in ("GND", "VBUS_DATA", "VCC", "SDA", "SCL", "HALL_INT")}   # [A]
for n in NETS.values(): board.Add(n)
def net(fp, pin, n):
    for pad in fp.Pads():
        if pad.GetNumber() == pin: pad.SetNet(NETS[n])
for pin, n in (("4", "GND"), ("6", "VCC"), ("8", "SDA"), ("9", "SCL"), ("10", "HALL_INT")): net(u1, pin, n)
for pin, n in (("1", "SCL"), ("2", "GND"), ("3", "GND"), ("4", "VCC"), ("5", "HALL_INT"), ("6", "SDA")): net(u3, pin, n)
net(c2, "1", "VCC"); net(c2, "2", "GND"); net(r1, "1", "VCC"); net(r1, "2", "SDA"); net(r2, "1", "VCC"); net(r2, "2", "SCL")
for pad in c1.Pads():
    if pad.GetNumber() == "1": pad.SetNet(NETS["GND"])         # B.Cu ring on the brass tube top
    elif pad.GetNumber() == "2": pad.SetNet(NETS["VBUS_DATA"]) # F.Cu ring under the M1.6 thin nut
ds.SetAuxOrigin(P(0, 0)); ds.SetGridOrigin(P(0, 0))

pcb_path = os.path.join(HERE, NAME + ".kicad_pcb")
pcbnew.SaveBoard(pcb_path, board)
json.dump({"meta": {"filename": NAME + ".kicad_pro", "version": 1}, "board": {"design_settings": {"rules": {"min_copper_edge_clearance": EDGE_CLEAR_CU}}}, "libraries": {}},
          open(os.path.join(HERE, NAME + ".kicad_pro"), "w"), indent=2)
open(os.path.join(HERE, "fp-lib-table"), "w").write(
    '(fp_lib_table\n  (version 7)\n  (lib (name "footprints")(type "KiCad")(uri "${KIPRJMOD}/../../../kicad/footprints.pretty")(options "")(descr "Ed project footprints"))\n)\n')
step = os.path.join(HERE, "..", NAME + ".step")
subprocess.run(["kicad-cli", "pcb", "export", "step", "--grid-origin", "--force", "-o", step, pcb_path], check=True)
print("board Ø", BOARD_D, "J1", J1_POS, "U1", U1_POS, "C1", C1_POS, "U3", U3_POS, U3_ROT, "C2", C2_POS, "R1", R1_POS, "R2", R2_POS)
