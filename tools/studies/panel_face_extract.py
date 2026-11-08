# Saved from the 8 Nov logo study: the case shell's polished front face (z_fp1) and its openings as polylines -> <dir>/front.json.
# Run from cad/knob-param: PYTHONPATH=$PWD .venv/bin/python ../../tools/studies/panel_face_extract.py <dir with case.brep>
import sys, json
import numpy as np
from build123d import import_brep, Vector
S = sys.argv[1]
case = import_brep(f"{S}/case.brep")
zf = 38.8
cands = []
for f in case.faces():
    try:
        n = f.normal_at(f.center())
    except Exception:
        continue
    c = f.center()
    if abs(n.Z) > 0.99 and n.Z > 0 and abs(c.Z - zf) < 0.05:
        cands.append(f)
print("front faces at z_fp1:", len(cands), [round(f.area, 1) for f in cands])
# other +Z faces above the plate (the seal ring top etc.)
up = sorted({round(f.center().Z, 2) for f in case.faces() if abs(f.normal_at(f.center()).Z) > 0.99 and f.normal_at(f.center()).Z > 0 and f.center().Z > zf + 0.01})
print("+Z faces above the plate at z:", up)
def poly(w):
    pts = []
    for e in w.edges():
        n = max(2, int(e.length / 0.2))
        for t in np.linspace(0, 1, n, endpoint=False):
            p = e.position_at(t); pts.append((round(p.X, 3), round(p.Y, 3)))
    return pts
out = []
for f in cands:
    out.append(dict(area=f.area, outer=poly(f.outer_wire()), inner=[poly(w) for w in f.inner_wires()]))
json.dump(out, open(f"{S}/front.json", "w"))
for f in out:
    xs = [p[0] for p in f["outer"]]; ys = [p[1] for p in f["outer"]]
    print("outer bbox", min(xs), max(xs), min(ys), max(ys), "holes", len(f["inner"]))
    for h in f["inner"]:
        hx = [p[0] for p in h]; hy = [p[1] for p in h]
        print("  hole bbox x %.2f..%.2f y %.2f..%.2f" % (min(hx), max(hx), min(hy), max(hy)))
