"""Review figure (3 Nov, item 4, Danny's blue mark): the zone between the dial's outer wall and the bezel skirt.
Left: today (cut through the 30° boss). Right: sketch of the idea: magnets turned sideways in that zone, a key in place of the
pins, nothing inside the glass's path. The right panel is a sketch over the model cut (bosses removed, new parts drawn), not a model.
Run from cad/knob-param:  .venv/bin/python tools/studies/cart_side_mag_fig.py OUT.png"""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Rectangle, FancyArrowPatch
import assembly_anim as A
from knobparam.assembly.plan_sheet import _cut_faces
from knobparam.assembly.colours import colour
from build123d import Rot

idx = A.load_index(); g = A.Geo(idx)
names = [n for n in idx["parts"] if n.startswith(("dial bezel", "dial screen", "cartridge magnet", "cartridge locating pin",
                                                   "control dial", "dial board", "knob glass sleeve", "knob upper-cap"))]
cuts = {}
for n in names:
    t = _cut_faces(Rot(0, 0, -30.0) * g.brep(n), "y", 0.0)
    if t:
        cuts[n] = t
fig, (aL, aR) = plt.subplots(1, 2, figsize=(15, 8.4), dpi=120)
MAG = "#b8bec6"


def base(ax, drop_bosses=False):
    for n, t in cuts.items():
        if drop_bosses and n.startswith(("cartridge magnet", "cartridge locating pin")):
            continue
        if drop_bosses and n.startswith("dial bezel"):   # the boss hanging inside r 19.45 below the glass seat goes
            t = [tri for tri in t if not (max(x for x, z in tri) < 19.45 + 1e-6 and min(z for x, z in tri) < 59.0)]
        ax.add_collection(PolyCollection(t, facecolors=colour(n), edgecolors=colour(n), linewidths=0.2, alpha=0.95))
    ax.set_xlim(13.5, 22.5); ax.set_ylim(51.0, 62.5); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("r (mm)"); ax.set_ylabel("z (mm)")
    ax.axvline(18.2, color="#1f77b4", ls="--", lw=1.4); ax.text(18.15, 61.9, "lens edge r 18.2", color="#1f77b4", ha="right", fontsize=9)


base(aL)
aL.add_patch(FancyArrowPatch((17.6, 52.2), (17.6, 55.4), arrowstyle="-|>", mutation_scale=16, lw=2, color="#d62728"))
aL.text(13.7, 52.0, "glass comes UP here\nand hits the boss", color="#d62728", fontsize=10)
aL.annotate("your blue mark:\ndial wall r 19.2 | gap 0.3 |\nbezel skirt r 19.5-21", (19.35, 54.4), (19.6, 51.5), fontsize=9.5,
            color="#0b3d91", arrowprops=dict(arrowstyle="-", lw=0.8, color="#0b3d91"))
aL.set_title("Today (cut through the 30° boss): the boss + magnets\nsit at r 17.4-19.5, inside the glass's way up", fontsize=11, loc="left")

base(aR, drop_bosses=True)
aR.add_patch(Rectangle((17.15, 55.95), 2.33, 2.55, fc="white", ec="none", zorder=4))   # the printed boss goes
aR.add_patch(Rectangle((18.2, 54.3), 1.0, 1.0, fc=MAG, ec="k", lw=0.8, zorder=5))     # 1: dial magnet, facing out
aR.add_patch(Rectangle((19.5, 53.9), 1.0, 1.0, fc=MAG, ec="k", lw=0.8, zorder=5))     # 2: bezel magnet, facing in, 0.4 lower
aR.add_patch(Rectangle((18.85, 52.9), 0.65, 3.0, fc="none", ec="#2ca02c", lw=1.5, ls="--", zorder=6))   # 3: key (other angle)
aR.add_patch(FancyArrowPatch((17.6, 52.2), (17.6, 58.6), arrowstyle="-|>", mutation_scale=16, lw=2, color="#2ca02c", zorder=7))
for (x, y), k in (((18.7, 54.8), "1"), ((20.0, 54.4), "2"), ((19.17, 56.35), "3"), ((17.15, 57.3), "4")):
    aR.text(x, y, k, ha="center", va="center", fontsize=10, fontweight="bold", color="white" if k in "12" else "#1a7f37",
            bbox=dict(boxstyle="circle,pad=0.15", fc="#333333" if k in "12" else "white", ec="#1a7f37" if k in "34" else "none"),
            zorder=8)
fig.text(0.40, 0.17, "1  magnet in the dial's outer wall, facing out\n"
        "2  magnet in the bezel skirt, facing in, 0.4 lower: pulls the cartridge DOWN as well as centring it\n"
        "3  the pins become a key: a rib on the skirt's inside in a slot in the dial wall (at another angle, dashed)\n"
        "4  the bosses are gone: nothing inside r 18.5 below the glass, so the glass + panel go straight up in",
        fontsize=10.5, va="top")
aR.set_title("Idea: use the zone you marked. Magnets turned SIDEWAYS\nacross the gap, a key instead of the pins (sketch, not modelled)",
             fontsize=11, loc="left")
fig.suptitle("Item 4, your blue mark: the space between the dial's outer wall and the bezel skirt", fontsize=13, x=0.01, ha="left")
fig.subplots_adjust(left=0.06, right=0.98, top=0.86, bottom=0.27, wspace=0.25)
fig.savefig(sys.argv[1]); print("wrote", sys.argv[1])
