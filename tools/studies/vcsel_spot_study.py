"""Where could a red VCSEL go? (8 Nov 2026, Ed 13:35: "put at least one somewhere else"). A top-emitting VCSEL on the main board
front shines straight up. For every spot on the board, how far does the beam travel before it meets something opaque, and what
does it meet? Clear parts (UTR-8100, borosilicate, glass balls) let it through. Slices every part every DZ mm and keeps, for each
(x, y) cell, the lowest opaque hit above the board, and whether the board front there is free for the package.
Run from cad/knob-param:
  KNOBPARAM_CACHE=$PWD/.cache-knob PYTHONPATH=$PWD .venv/bin/python ../../tools/studies/vcsel_spot_study.py <out.npz>"""
import math, re, sys, json
import numpy as np
from matplotlib.path import Path
from build123d import Plane
from knobparam.common import model
from knobparam.assembly.build import build_all
from knobparam.assembly.export_parts import classify

out = sys.argv[1]
D = model.derive(model.default_params())
parts, _, _, owner = build_all(D)
H, X0, X1, Y0, Y1 = 0.2, -30.0, 30.0, -12.0, 52.0
xs = np.arange(X0, X1, H) + H / 2; ys = np.arange(Y0, Y1, H) + H / 2
XG, YG = np.meshgrid(xs, ys); pts = np.c_[XG.ravel(), YG.ravel()]
ZTOP, DZ = 56.0, 0.5
first = np.full(XG.shape, np.inf); who = np.full(XG.shape, -1, int)
front_busy = np.zeros(XG.shape, bool); board = np.zeros(XG.shape, bool)
names, clear = [], {}
for n, s in parts.items():
    kind, mat, proc = classify(n)
    clear[n] = bool(re.search(r"clear|borosilicate|glass|transparent", mat, re.I)) and "OLED" not in n
names = list(parts)


def fill(s, z):
    m = np.zeros(XG.shape, bool)
    try:
        sec = s.intersect(Plane.XY.offset(z))
    except Exception:
        return m
    if sec is None:
        return m
    for f in sec.faces():
        for k, w in enumerate([f.outer_wire()] + list(f.inner_wires())):
            poly = np.array([(p.X, p.Y) for e in w.edges() for p in [e.position_at(t) for t in np.linspace(0, 1, 16)]])
            if len(poly) < 3:
                continue
            inside = Path(poly).contains_points(pts).reshape(XG.shape)
            m = (m | inside) if k == 0 else (m & ~inside)
    return m


board = fill(parts["PCB"], -0.8)
for i, n in enumerate(names):
    s = parts[n]; b = s.bounding_box()
    if n == "PCB" or b.max.Z < 0.05 or b.min.X > X1 or b.max.X < X0 or b.min.Y > Y1 or b.max.Y < Y0:
        continue
    if b.min.Z < 0.9:                                   # anything on the board front where the package would sit
        front_busy |= fill(s, 0.45)
    if clear[n]:
        continue
    for z in np.arange(max(1.0, b.min.Z + 0.01), min(ZTOP, b.max.Z), DZ):
        m = fill(s, z)
        upd = m & (z < first)
        first[upd] = z; who[upd] = i
    print("sliced", n[:60], flush=True)
np.savez_compressed(out, xs=xs, ys=ys, first=first, who=who, front_busy=front_busy, board=board, names=np.array(names),
                    clear=np.array([clear[n] for n in names]))
json.dump(dict(knob_r=D["knob_od"] / 2, z_glass=D.get("z_glass")), open(out.replace(".npz", ".json"), "w"))
print("done")
