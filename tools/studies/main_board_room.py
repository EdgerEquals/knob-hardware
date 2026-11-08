"""Main board room map, v0.52 (8 Nov 2026, step 3: placing the main board). Slices the assembly (panel frame) just above the board's
front and just below its back, and writes what is fixed there and what is free, per face, as a pickle for the plan picture.
Run from cad/knob-param:
  KNOBPARAM_CACHE=$PWD/.cache-knob PYTHONPATH=$PWD .venv/bin/python ../../tools/studies/main_board_room.py <out.pkl>"""
import sys, pickle, time
from shapely.geometry import Polygon
from shapely.ops import unary_union
from knobparam.assembly.section_atlas import _parts
from knobparam.assembly.plan_sheet import _cut_faces

t0 = time.time()
D, JD, parts = _parts()
zf, zb = 0.0, D["z_pcb_back"]
FRONT = [zf + 0.05, zf + 0.5, zf + 1.0, zf + 1.6, zf + 2.2]          # parts up to about 2 mm tall on the front
BACK = [zb - 0.05, zb - 0.5, zb - 1.0, zb - 1.6, zb - 2.2]           # and on the back
SKIP = ("PCB",)                                                     # the board itself


def section(s, z):
    tris = _cut_faces(s, "z", z)
    if not tris:
        return None
    g = unary_union([Polygon(t).buffer(1e-4) for t in tris if len(t) >= 3 and Polygon(t).area > 1e-9])
    return None if g.is_empty else g


board = section(parts["PCB"], (zf + zb) / 2)
occ = {}
for face, zs in (("front", FRONT), ("back", BACK)):
    per = {}
    for n, s in parts.items():
        if n.startswith(SKIP):
            continue
        try:
            bb = s.bounding_box()
        except Exception:
            continue
        if bb.max.Z < min(zs) or bb.min.Z > max(zs):
            continue
        gs = [g for g in (section(s, z) for z in zs if bb.min.Z <= z <= bb.max.Z) if g is not None]
        if gs:
            g = unary_union(gs).intersection(board.envelope.buffer(2))
            if not g.is_empty and g.area > 0.05:
                per[n] = g
    occ[face] = per
    print(face, len(per), "parts touch it;", round(time.time() - t0), "s")
free = {f: board.difference(unary_union(list(occ[f].values()))) for f in occ}
for f in free:
    print(f, "board", round(board.area), "mm2, free", round(free[f].area), "mm2")
pickle.dump(dict(board=board, occ=occ, free=free, D={k: D[k] for k in ("pcb_windows", "mcu", "vb", "pwr_vcsel_xy", "clear_oled",
                                                                        "clear_oled_xy", "z_pcb_back") if k in D}),
            open(sys.argv[1], "wb"))
