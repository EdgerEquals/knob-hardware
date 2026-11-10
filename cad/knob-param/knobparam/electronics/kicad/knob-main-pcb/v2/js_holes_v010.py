"""Joystick v0.10 [Ed 10 Nov, "A: two springs, hooked from the back"]: two hold-down springs on the joystick's axis instead of four at
y ±1.5, so each side's figure-8 cut-out (two Ø3.4 holes 3.0 apart) becomes one round Ø3.4 hole at (±12.5, 40.63). Edits the routed
board in place (make_board.py would re-place and re-route it): takes out the two figure-8 outlines, cuts the two round holes,
refills the planes and runs DRC. The round holes sit inside the old outlines' span, so no track moves.
  /usr/bin/python3 js_holes_v010.py"""
import os, sys, math, json
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from kicad7_tools import save_board, drc

PCB = os.path.join(HERE, "kicad", "knob-main-pcb.kicad_pcb")
GEOM = os.path.join(os.path.dirname(os.path.dirname(HERE)), "joystick-daughterboard", "geom.json")
holes = json.load(open(GEOM))["main_pcb_holes"]          # the joystick model's (panel frame): two Ø3.4 at (±12.5, 40.63)
assert len(holes) == 2, holes
T, F = pcbnew.ToMM, pcbnew.FromMM
KEEP = []                                                # pcbnew (SWIG) needs removed items kept alive

b = pcbnew.LoadBoard(PCB)
for h in holes:
    cx, cy, r = 100.0 + h["x"], 100.0 - h["y"], h["d"] / 2
    # the old figure-8: Edge.Cuts pieces wholly inside the two old holes' span (x ±1.75, y ±3.25 round the new centre)
    old = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts and
           all(abs(T(p.x) - cx) <= 1.75 and abs(T(p.y) - cy) <= 3.25 for p in (d.GetStart(), d.GetEnd()))]
    xs = [T(p.x) for d in old for p in (d.GetStart(), d.GetEnd())]; ys = [T(p.y) for d in old for p in (d.GetStart(), d.GetEnd())]
    assert old and abs(max(xs) - min(xs) - 3.4) < 0.05 and abs(max(ys) - min(ys) - 6.4) < 0.05, (len(old), min(xs), max(xs), min(ys), max(ys))
    for d in old:
        KEEP.append(d); b.Remove(d)
    c = pcbnew.PCB_SHAPE(b); c.SetShape(pcbnew.SHAPE_T_CIRCLE); c.SetLayer(pcbnew.Edge_Cuts); c.SetWidth(F(0.05))
    c.SetCenter(pcbnew.VECTOR2I(F(cx), F(cy))); c.SetEnd(pcbnew.VECTOR2I(F(cx + r), F(cy)))
    b.Add(c)
    print(f"({h['x']:+.2f}, {h['y']:.2f}): {len(old)} figure-8 pieces out, Ø{h['d']:g} hole in")
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
save_board(PCB, b)
v, u, _ = drc(PCB)
print("DRC:", v, "violations,", u, "unconnected")
