# Run from cad/knob-param:  PYTHONPATH=. python tools/cover_cuts.py out.png
import os, sys, math
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from knobparam.common import model
from knobparam.assembly.build import build_all, view
from knobparam.assembly.plan_sheet import cut, draw
D = model.derive(model.default_params())
parts, stats, keys, owner = build_all(D)
parts, keys = view(parts, keys, D, "panel")
sel = {n: s for n, s in parts.items() if n.startswith(("back cover", "lower screen pad", "corner", "back AMOLED", "case", "PCB", "encoder", "feel"))}
print([n for n in sel])
zs = [-16.6, -15.6, -14.75, -13.75, -11.0, -8.0, -5.0, -3.0]
fig, axs = plt.subplots(1, len(zs), figsize=(3.4 * len(zs), 8.5))
for ax, z in zip(axs, zs):
    lay = cut(sel, "z", z)
    draw(ax, lay, f"z {z}", (-27, 27), (D["panel_y0"] - 2, D["panel_y1"] + 2))
    for n, *_ in lay: pass
fig.savefig(sys.argv[1], dpi=90, bbox_inches="tight")
b = parts["back cover (PETG)"].bounding_box() if "back cover (PETG)" in parts else None
print("cover bb", b)
