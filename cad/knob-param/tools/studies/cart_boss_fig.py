"""Review figure (3 Nov, item 4): the dial cartridge's bosses stand in the glass's path as it goes up into the bezel.
Plan from below at the boss height, a straight-on cut through the 30° boss, and the proposed fix (bosses as a glued insert).
Reads the animation cache's BREPs (panel frame). Run from cad/knob-param:  .venv/bin/python tools/studies/cart_boss_fig.py OUT.png"""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Circle, Wedge, FancyArrowPatch
import assembly_anim as A
from knobparam.assembly.plan_sheet import _cut_faces
from knobparam.assembly.colours import colour
from build123d import Rot

idx = A.load_index(); g = A.Geo(idx)
names = [n for n in idx["parts"] if n.startswith(("dial bezel", "dial screen", "cartridge magnet", "cartridge locating pin",
                                                   "dial cartridge plug pad", "control dial", "dial board"))]
S = {n: g.brep(n) for n in names}

fig = plt.figure(figsize=(19, 7.6), dpi=110)
axP = fig.add_axes([0.02, 0.06, 0.29, 0.80]); axS = fig.add_axes([0.35, 0.10, 0.33, 0.72]); axF = fig.add_axes([0.70, 0.06, 0.29, 0.80])


def draw(ax, tris, col, alpha=1.0, z=1):
    if tris:
        ax.add_collection(PolyCollection(tris, facecolors=col, edgecolors=col, linewidths=0.2, alpha=alpha, zorder=z))


# ---- 1: plan from below at the boss height (z 57.2), looking up (x mirrored so it reads as seen from below)
zc = 57.2
for n, s in S.items():
    if n.startswith(("control dial", "dial board")):
        continue
    t = _cut_faces(s, "z", zc)
    t = [[(-x, y) for x, y in tri] for tri in t]
    draw(axP, t, colour(n), 1.0, 2 if "magnet" in n or "pin" in n else 1)
for r, ls, lab, c in ((18.2, "--", "lens edge Ø36.4", "#1f77b4"), (17.7, ":", "panel edge Ø35.4", "#444444")):
    axP.add_patch(Circle((0, 0), r, fill=False, ls=ls, lw=1.6, ec=c, zorder=5))
for a, lab in ((30, "magnet 30°"), (90, "pin 90°"), (150, "magnet 150°"), (180, "pin 180°"), (240, "magnet 240°")):
    x, y = 18.45 * math.cos(math.radians(a)), 18.45 * math.sin(math.radians(a))
    axP.add_patch(Wedge((-0.0, 0), 18.2, 180 - a - 4, 180 - a + 4, width=0.8, color="#d62728", alpha=0.75, zorder=6))
    axP.annotate(lab, (-x, y), (-x * 1.28, y * 1.28), fontsize=9, ha="center", va="center",
                 arrowprops=dict(arrowstyle="-", lw=0.6))
axP.text(0, 0, "red = where each boss\nsits inside the lens edge\n(0.8 overlap): the glass\ncannot pass it", ha="center",
         va="center", fontsize=10, color="#d62728")
axP.set_xlim(-24, 24); axP.set_ylim(-24, 24); axP.set_aspect("equal"); axP.grid(alpha=0.2)
axP.set_title("1. Bezel seen from BELOW, cut at z 57.2 (the boss height)\nbosses vs the lens (blue dashed) and panel (grey dotted) edges",
              fontsize=11, loc="left")

# ---- 2: straight-on cut through the 30° boss (radial plane), glass shown part-way up with the arrow
a = 30.0
for n, s in S.items():
    rs = Rot(0, 0, -a) * s           # the 30° plane becomes the x-z plane (y = 0)
    t = _cut_faces(rs, "y", 0.0)
    if not t:
        continue
    lens_like = n.startswith(("dial screen Z132A2441 lens", "dial screen Z132A2441 panel"))
    draw(axS, t, colour(n), 0.95, 2)
    if lens_like:   # the same parts 3 mm lower: on their way up
        draw(axS, [[(x, z - 3.0) for x, z in tri] for tri in t], colour(n), 0.25, 1)
axS.add_patch(FancyArrowPatch((17.4, 52.6), (17.4, 55.6), arrowstyle="-|>", mutation_scale=18, lw=2.2, color="#d62728", zorder=7))
axS.annotate("glass + panel on their way UP\n(faint: 3 mm short of home)", (9, 57.4), (1.0, 51.0), fontsize=9.5,
             arrowprops=dict(arrowstyle="-", lw=0.6))
axS.annotate("boss + magnet: the lens\nedge runs into it", (18.0, 57.6), (8.5, 63.0), fontsize=9.5, color="#d62728",
             arrowprops=dict(arrowstyle="-", lw=0.9, color="#d62728"))
axS.annotate("bezel", (20.6, 60.4), (21.2, 63.6), fontsize=9.5, arrowprops=dict(arrowstyle="-", lw=0.6))
axS.annotate("dial land\n+ its magnet", (18.6, 55.3), (20.3, 50.6), fontsize=9.5, arrowprops=dict(arrowstyle="-", lw=0.6))
axS.set_xlim(0, 24); axS.set_ylim(49.5, 64.5); axS.set_aspect("equal"); axS.grid(alpha=0.2)
axS.set_xlabel("r (mm, along 30°)"); axS.set_ylabel("z (mm)")
axS.set_title("2. Straight-on cut through the 30° boss (axis at the left edge)", fontsize=11, loc="left")

# ---- 3: the fix: the bezel printed WITHOUT the bosses; the bosses come as two glued inserts after the glass
for n, s in S.items():
    if not n.startswith(("dial bezel", "dial screen")):
        continue
    t = _cut_faces(s, "z", zc)
    t = [[(-x, y) for x, y in tri] for tri in t]
    if n.startswith("dial bezel"):   # keep the ring only (r > 19.4): the printed bosses go
        t = [tri for tri in t if min(math.hypot(x, y) for x, y in tri) > 19.4]
    draw(axF, t, colour(n), 1.0, 1)
axF.add_patch(Circle((0, 0), 18.2, fill=False, ls="--", lw=1.6, ec="#1f77b4", zorder=5))
ins = "#2ca02c"
for a0, a1, lab in ((-25, 200, "insert 1: one arc, bosses at 30°, 90°, 150°, 180°"), (226, 252, "insert 2: tab, boss at 240°")):
    axF.add_patch(Wedge((0, 0), 19.5, 180 - a1, 180 - a0, width=2.1, color=ins, alpha=0.55, zorder=4))
for a0, a1, lab in ((206, 219, "tail U-turn"), (256, 284, "bottom bend"), (290, 330, "plug + socket lobe")):
    am = math.radians((a0 + a1) / 2)
    axF.add_patch(Wedge((0, 0), 19.5, 180 - a1, 180 - a0, width=2.1, color="#ff7f0e", alpha=0.35, zorder=3))
    axF.text(-21.8 * math.cos(am), 21.8 * math.sin(am), lab, fontsize=8.5, ha="center", va="center", color="#b35900")
axF.text(0, 6.5, "green = the bosses as two printed\ninserts, glued into the bezel bore\nAFTER the glass + panel are in;\n"
         "keyed so the angles can't be off", ha="center", fontsize=10, color="#1a7f37")
axF.text(0, -6.5, "orange = flex bends / plug:\nthe inserts stay clear of them", ha="center", fontsize=10, color="#b35900")
axF.set_xlim(-24, 24); axF.set_ylim(-24, 24); axF.set_aspect("equal"); axF.grid(alpha=0.2)
axF.set_title("3. Proposed: same view, bosses as glued inserts", fontsize=11, loc="left")
fig.suptitle("Dial cartridge, item 4: the glass goes UP into the bezel from underneath, but the five bosses hang inside its path",
             fontsize=13, x=0.01, ha="left")
fig.savefig(sys.argv[1])
print("wrote", sys.argv[1])
