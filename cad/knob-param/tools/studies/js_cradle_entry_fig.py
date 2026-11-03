"""Review figure (3 Nov, item 5): why the joystick cradle + top board cannot go into the case from the back.
Left: plan at z 20 (the case cut there) with the cradle's and the top board's outlines over it. Right: straight-on cut at x = -20.7
(through the top-left corner post): the post, the top wall, the cradle above. Run from cad/knob-param:
  .venv/bin/python tools/studies/js_cradle_entry_fig.py OUT.png"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import FancyArrowPatch
import assembly_anim as A
from knobparam.assembly.plan_sheet import _cut_faces
from knobparam.assembly.colours import colour

idx = A.load_index(); g = A.Geo(idx)
want = ("case", "glow coat", "corner insert", "PCB", "joystick: joystick case cradle", "joystick: joystick top board",
        "joystick: top-board socket", "vertical board", "joystick: joystick carrier", "joystick: screen carrier (printed)")
names = [n for n in idx["parts"] if n.startswith(want) and not n.startswith("PCB back") and not n.startswith("PCB rod")]
S = {n: g.brep(n) for n in names}
fig, (aP, aS) = plt.subplots(1, 2, figsize=(16, 8.6), dpi=115, gridspec_kw=dict(width_ratios=[1.0, 1.25]))


def add(ax, t, col, a=1.0, z=1, ec=None):
    if t:
        ax.add_collection(PolyCollection(t, facecolors=col, edgecolors=ec or col, linewidths=0.3, alpha=a, zorder=z))


# plan: case + posts at z 20, then the cradle and top board as outlines (their own plan cuts at their heights)
for n in ("case", "glow coat", "corner insert 3 M2.5 brass", "corner insert 4 M2.5 brass"):
    if n in S:
        add(aP, _cut_faces(S[n], "z", 20.0 if not n.startswith("corner") else 1.0), colour(n), 0.9 if n != "glow coat" else 0.5)
cr = "joystick: joystick case cradle (SLA, lip in the faceplate cutout)"
tb = [n for n in S if n.startswith("joystick: joystick top board")][0]
from shapely.geometry import Polygon
from shapely.ops import unary_union


def outline(ax, tris, col, lw=2.0):
    u = unary_union([Polygon(t).buffer(0.002) for t in tris if len(t) == 3])
    for geom in getattr(u, "geoms", [u]):
        for ring in [geom.exterior] + list(geom.interiors):
            x, y = ring.xy
            ax.plot(x, y, color=col, lw=lw, zorder=6)


outline(aP, _cut_faces(S[cr], "z", 36.6), "#d62728")
outline(aP, _cut_faces(S[tb], "z", 30.5), "#1f77b4", 1.6)
aP.text(0, 57.5, "red outline = the cradle's flange (z 36.6)\nblue outline = the top board", ha="center", fontsize=10)
aP.annotate("top corner posts with their inserts:\nthe flange overhangs them", (-20.7, 45.3), (-24, 15), fontsize=10, color="#d62728",
            arrowprops=dict(arrowstyle="-", lw=0.9, color="#d62728"))
aP.annotate("", (20.7, 45.3), (-12, 17.5), arrowprops=dict(arrowstyle="-", lw=0.9, color="#d62728"))
aP.set_xlim(-28, 28); aP.set_ylim(10, 68); aP.set_aspect("equal"); aP.grid(alpha=0.2)
aP.set_xlabel("x (mm)"); aP.set_ylabel("y (mm, up the panel)")
aP.set_title("Plan (looking at the panel), case cut at z 20", fontsize=11, loc="left")

# section at y = 45.35 through both top corner posts (x-z plane)
for n, sh in S.items():
    t = _cut_faces(sh, "y", 45.35)
    add(aS, t, colour(n), 0.85 if not n.startswith(("case", "glow")) else 0.7, 2 if n.startswith("joystick") else 1)
for sx in (-1, 1):
    aS.add_patch(FancyArrowPatch((sx * 21.2, 4.0), (sx * 21.2, 27.0), arrowstyle="-|>", mutation_scale=16, lw=2.0,
                                 color="#d62728", zorder=6))
aS.text(0, 14, "coming UP from the back, the flange's\nends (x ±22.1) run into the corner\nposts, which stand inside x ±21",
        ha="center", color="#d62728", fontsize=10)
aS.set_xlim(-27, 27); aS.set_ylim(-4, 42); aS.set_aspect("equal"); aS.grid(alpha=0.2)
aS.set_xlabel("x (mm)"); aS.set_ylabel("z (mm, out of the panel)")
aS.set_title("Straight-on cut at y = 45.35, through both top corner posts", fontsize=11, loc="left")
fig.suptitle("Item 5: the joystick cradle (with the top board) cannot come into the case from the back", fontsize=13, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(sys.argv[1]); print("wrote", sys.argv[1])
