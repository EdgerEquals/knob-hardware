"""Authoring script for the round screen adapter board (KiCad is the single source of truth for this board).
Run with the system python that has pcbnew:  /usr/bin/python3 make_board.py
Writes screen-adapter.kicad_pcb / .kicad_pro / fp-lib-table, then exports ../screen-adapter.step with kicad-cli.
Contents: round Edge.Cuts outline, 2 layers, 1.0 thick [A]; footprints from the shared library (cad/library/kicad/footprints.pretty):
  J1 = FPC_14P_0.5mm_Top   for the 0.71" round TFT tail (14 pin, 0.5 pitch [A], Zhunyi Z07101-P14)
  U1 = QFN-20_3x3_P0.4_CH32V003   CH32V003F4U6 [A]
  W1 = WirePads_4x_0.7mm_Back      VCC, GND, D1, D2 at the centre, back side, over the Ø3.0 wire bore
Placed only, no routing. Grid origin = board centre (x right, y down in KiCad)."""
import os, json, subprocess, pcbnew

ORIGIN = (100.0, 100.0)     # KiCad position of the board centre (sheet placement only)
BOARD_D = 15.5              # [A] <= 18 (Ed); smallest round that holds J1 with 0.3 courtyard-to-edge
BOARD_T = 1.0               # [A]
J1_POS = (0.0, -3.2)        # [A] KiCad coords (y up = negative): cable entry toward the board top edge
U1_POS = (0.0, 3.5)         # [A]
W1_POS = (0.0, 0.0)         # centre, over the wire bore
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

def place(fpname, ref, pos, back=False):
    fp = pcbnew.FootprintLoad(LIBDIR, fpname); fp.SetFPID(pcbnew.LIB_ID("footprints", fpname))
    fp.SetReference(ref); fp.SetPosition(P(*pos))
    board.Add(fp)   # add first, then flip (flipping an unparented footprint crashes pcbnew 9)
    if back: fp.Flip(P(*pos), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
    return fp
place("FPC_14P_0.5mm_Top", "J1", J1_POS)
place("QFN-20_3x3_P0.4_CH32V003", "U1", U1_POS)
place("WirePads_4x_0.7mm_Back", "W1", W1_POS, back=True)
ds.SetAuxOrigin(P(0, 0)); ds.SetGridOrigin(P(0, 0))

pcb_path = os.path.join(HERE, NAME + ".kicad_pcb")
pcbnew.SaveBoard(pcb_path, board)
json.dump({"meta": {"filename": NAME + ".kicad_pro", "version": 1}, "board": {"design_settings": {"rules": {"min_copper_edge_clearance": EDGE_CLEAR_CU}}}, "libraries": {}},
          open(os.path.join(HERE, NAME + ".kicad_pro"), "w"), indent=2)
open(os.path.join(HERE, "fp-lib-table"), "w").write(
    '(fp_lib_table\n  (version 7)\n  (lib (name "footprints")(type "KiCad")(uri "${KIPRJMOD}/../../../kicad/footprints.pretty")(options "")(descr "Ed project footprints"))\n)\n')
step = os.path.join(HERE, "..", NAME + ".step")
subprocess.run(["kicad-cli", "pcb", "export", "step", "--grid-origin", "--force", "-o", step, pcb_path], check=True)
print("board Ø", BOARD_D, "J1", J1_POS, "U1", U1_POS, "W1", W1_POS)
