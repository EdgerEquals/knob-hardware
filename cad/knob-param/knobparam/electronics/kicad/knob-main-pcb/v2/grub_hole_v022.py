"""Main board v2.2 [Ed 26 Nov, "A"]: the detent pedestal grub's key hole becomes a clearance hole for the M2 grub, so the grub can run
down into the board (±0.50 of travel instead of ±0.25; docs/img/pedestal-grub-travel.png). The Ø1.6 key hole at r 13.5 (drawn on
Edge.Cuts as short segments) comes out and a Ø2.4 circle goes in at r 13.1 on the same line (panel 173°), 0.4 further in so it keeps
the 0.25 copper-to-edge rule from the OLED tracks on F.Cu (no track moves). The model makes the same hole from the interface params
sp_access_d / sp_grub_r / sp_ang, so make_board.py would draw it there too. Edits the routed board in place, sets the revision,
refills the planes and runs DRC.
  /usr/bin/python3 grub_hole_v022.py"""
import os, sys, math
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from kicad7_tools import save_board, drc

PCB = os.path.join(HERE, "kicad", "knob-main-pcb.kicad_pcb")
ANG = 263.0 - 90.0                 # sp_ang (mechanism frame) turned into the panel frame (mech_rot -90)
OLD_R, OLD_D = 13.5, 1.6           # v2.1: sp_r, the old sp_access_d
NEW_R, NEW_D = 13.1, 2.4           # v2.2: sp_grub_r, sp_access_d [Ed 26 Nov A]
REV = "v2.2"
T, F = pcbnew.ToMM, pcbnew.FromMM
KEEP = []                          # pcbnew (SWIG) needs removed items kept alive


def kicad_xy(r):
    x, y = r * math.cos(math.radians(ANG)), r * math.sin(math.radians(ANG))
    return 100.0 + x, 100.0 - y    # panel frame -> KiCad (origin 100, 100; y down)


b = pcbnew.LoadBoard(PCB)
ox, oy = kicad_xy(OLD_R)
old = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts and
       all(abs(T(p.x) - ox) <= OLD_D / 2 + 0.1 and abs(T(p.y) - oy) <= OLD_D / 2 + 0.1 for p in (d.GetStart(), d.GetEnd()))]
xs = [T(p.x) for d in old for p in (d.GetStart(), d.GetEnd())]; ys = [T(p.y) for d in old for p in (d.GetStart(), d.GetEnd())]
assert old and abs(max(xs) - min(xs) - OLD_D) < 0.1 and abs(max(ys) - min(ys) - OLD_D) < 0.1, (len(old), xs and (min(xs), max(xs)))
for d in old:
    KEEP.append(d); b.Remove(d)
nx, ny = kicad_xy(NEW_R)
c = pcbnew.PCB_SHAPE(b); c.SetShape(pcbnew.SHAPE_T_CIRCLE); c.SetLayer(pcbnew.Edge_Cuts); c.SetWidth(F(0.05))
c.SetCenter(pcbnew.VECTOR2I(F(nx), F(ny))); c.SetEnd(pcbnew.VECTOR2I(F(nx + NEW_D / 2), F(ny)))
b.Add(c)
print(f"key hole: {len(old)} segments of the Ø{OLD_D:g} at r {OLD_R:g} out, Ø{NEW_D:g} at r {NEW_R:g} in ({nx - 100:+.3f}, {100 - ny:+.3f} panel)")
tb = b.GetTitleBlock(); tb.SetRevision(REV); b.SetTitleBlock(tb)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
save_board(PCB, b)
v, u, _ = drc(PCB)
print("DRC:", v, "violations,", u, "unconnected")
