"""Review figure (3 Nov, item 6): the 1220 pinion / knob hub-gear mesh. Plan cut through the mesh, a straight-on cut through both
axes, and a 3D close-up. Run from cad/knob-param:  xvfb-run -a .venv/bin/python tools/studies/hub_mesh_fig.py OUT.png"""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import assembly_anim as A
from knobparam.assembly.plan_sheet import _cut_faces
from knobparam.assembly.colours import colour

idx = A.load_index(); g = A.Geo(idx)
S = {n: g.brep(n) for n in ("pinion", "knob upper-cap", "motor", "control dial", "brass tube", "knob glass sleeve")}
pb = idx["parts"]["pinion"]["bb"]
mb = idx["parts"]["motor"]["bb"]
px, py = (mb[0] + mb[3]) / 2, (mb[1] + mb[4]) / 2          # 1220 axis (panel frame), from the round can
zm = (pb[2] + pb[5]) / 2
fig = plt.figure(figsize=(18, 8.2), dpi=115)
a1 = fig.add_axes([0.03, 0.10, 0.30, 0.76]); a2 = fig.add_axes([0.36, 0.10, 0.27, 0.76]); a3 = fig.add_axes([0.66, 0.06, 0.33, 0.84])


def add(ax, t, col, a=1.0, z=1):
    if t:
        ax.add_collection(PolyCollection(t, facecolors=col, edgecolors=col, linewidths=0.25, alpha=a, zorder=z))


PIN, HUB = "#e67e22", "#7f8c8d"   # pinion drawn orange to tell it apart (it is printed PA-12 today)
TUBE = "#c8ccd0"
for n, col in (("knob upper-cap", HUB), ("pinion", PIN), ("control dial", colour("control dial")), ("brass tube", TUBE)):
    add(a1, _cut_faces(S[n], "z", zm), col, 1.0, 2 if n == "pinion" else 1)
a1.plot([0, px], [0, py], color="k", lw=0.7, ls="--")
a1.text(px + 0.4, (py) / 2, f"motor axis {math.hypot(px, py):.2f} from the knob axis\n(gears cut for 10.80: 0.05 tight,\ninside the 0.10 backlash)",
        fontsize=9, va="center")
a1.annotate("1220 pinion 14T m0.6\n(printed PA-12 today)", (px, py - 3.6), (px + 6.5, py - 7.5), fontsize=10, color="#a04000",
            arrowprops=dict(arrowstyle="-", lw=0.7))
a1.annotate("hub gear 22T m0.6\n(printed into the knob's upper cap)", (5.0, 4.0), (5.5, 9.0), fontsize=10,
            arrowprops=dict(arrowstyle="-", lw=0.7))
a1.annotate("dial tube + brass tube\n(the hub gear turns round them)", (0, 0), (-12.5, 9.5), fontsize=9.5, arrowprops=dict(arrowstyle="-", lw=0.6))
a1.set_xlim(-13, 14); a1.set_ylim(py - 9.5, 12); a1.set_aspect("equal"); a1.grid(alpha=0.2)
a1.set_xlabel("x (mm)"); a1.set_ylabel("y (mm)")
a1.set_title(f"1. Plan, cut through the middle of the pinion (z {zm:.1f})", fontsize=11, loc="left")

for n, col in (("knob upper-cap", HUB), ("pinion", PIN), ("motor", colour("motor")), ("control dial", colour("control dial")),
               ("brass tube", TUBE), ("knob glass sleeve", colour("knob glass sleeve"))):
    add(a2, _cut_faces(S[n], "x", 0.0), col, 0.9 if n != "knob glass sleeve" else 0.35, 2 if n == "pinion" else 1)
a2.annotate("pinion, face 3.0", (-9.0, 42.0), (-18.5, 47.5), fontsize=10, color="#a04000", arrowprops=dict(arrowstyle="-", lw=0.8))
a2.annotate("hub gear teeth, face 4.4\n(the pinion meshes 3.0 of it)", (-5.2, 41.5), (-3.0, 50.5), fontsize=10,
            arrowprops=dict(arrowstyle="-", lw=0.8))
a2.annotate("dial tube round\nthe brass tube", (2.0, 36.0), (3.5, 31.0), fontsize=9.5, arrowprops=dict(arrowstyle="-", lw=0.6))
a2.annotate("1220 gearbox + motor\n(shaft up into the pinion)", (py, 34), (py - 8.0, 30.5), fontsize=10, arrowprops=dict(arrowstyle="-", lw=0.7))
a2.set_xlim(py - 9, 10); a2.set_ylim(28, 54); a2.set_aspect("equal"); a2.grid(alpha=0.2)
a2.set_xlabel("y (mm, up the panel)"); a2.set_ylabel("z (mm, out of the panel)")
a2.set_title("2. Straight-on cut through both axes (x = 0)", fontsize=11, loc="left")

# 3D close-up: pinion + the cap's hub-gear region, cut through the axes plane so the teeth show
import pyvista as pv
from build123d import Box, Pos, Align
region = Pos(-9, py - 6.5, 38.0) * Box(18, 6.5 - py + 8.5, 9.0, align=(Align.MIN,) * 3)
quad = Pos(0, -40, 30) * Box(40, 80, 30, align=(Align.MIN, Align.MIN, Align.MIN))
pl = pv.Plotter(off_screen=True, window_size=(1100, 1000)); pl.set_background("white")
for n, col in (("pinion", PIN), ("knob upper-cap", HUB), ("motor", colour("motor"))):
    try:
        q = (S[n] & region) - quad
    except Exception:
        continue
    if q is None or not q.solids():
        continue
    V, T = q.tessellate(0.02, 0.2)
    m = pv.PolyData(np.array([(v.X, v.Y, v.Z) for v in V]), np.hstack([np.full((len(T), 1), 3), np.array(T)]).ravel())
    pl.add_mesh(m, color=col, smooth_shading=False, ambient=0.3, diffuse=0.8, specular=0.2)
    fe = m.extract_feature_edges(35)
    if fe.n_points:
        pl.add_mesh(fe, color="#202020", line_width=1.0)
pl.camera_position = [(-38, py - 26, 66), (0, py / 2 + 1.0, 42.0), (0, 0, 1)]
pl.add_text("pinion (orange) in the hub gear (grey), cut through the axes", font_size=16, color="black")
img = pl.screenshot(None, return_img=True)
a3.imshow(img); a3.axis("off")
a3.set_title("3. 3D close-up (x > 0 cut away)", fontsize=11, loc="left")
fig.suptitle("Item 6: the 1220 pinion and the knob's hub gear (ratio 22/14 = 1.571, backlash designed 0.10)", fontsize=13, x=0.01,
             ha="left")
fig.savefig(sys.argv[1]); print("wrote", sys.argv[1])
