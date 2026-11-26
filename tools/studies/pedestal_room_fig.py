"""26 Nov [Ed: "Can we make the plate it screws into longer ... the area just around the grub extruded up. Isn't there room?"]:
what sits above the cradle plate round the detent pedestal. Plan section at z 4.0 (plate top 3.5) from the cached model, with the
dial's parts swept over its travel (±travel_deg) and the knob's swept round. Gaps measured from the pocket outline
(shapely, at z 3.6 to 5.0): detent block 0.45, dial 0.62 (z >= 4; 1.39 below), idler pinion 2 1.07, knob ring 2.7.
  .venv/bin/python tools/studies/pedestal_room_fig.py <out.png>   (from cad/knob-param)"""
import os, sys, json, math
import numpy as np
import pyvista as pv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

idx = json.load(open(os.path.join(".cache-knob", "anim", "index.json")))["parts"]
TRAVEL = 10.738823720349224        # interface travel_deg
ZC = 4.0
ANG, R0, R1, HALF, CL = 173.0, 12.55, 14.45, 13.43, 0.1   # pedestal (panel angle, r span, half angle), pocket clearance
SHOW = [("control dial lower part", "#1e88e5", "dial"), ("detent block (", "#fbc02d", None), ("detent block locating pin", "#795548", None),
        ("idler pinion 2", "#8e24aa", None), ("idler pin 2", "#8e24aa", None), ("bottom internal ring", "#90a4ae", "knob"),
        ("detent train pedestal", "#8d6e63", None)]


def rot(P, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.c_[c * P[:, 0] - s * P[:, 1], s * P[:, 0] + c * P[:, 1]]


fig, ax = plt.subplots(figsize=(12.5, 9.6), dpi=110)
for key, col, mode in SHOW:
    for n in idx:
        if not n.startswith(key):
            continue
        z = np.load(idx[n]["mesh"]); P, T = z["P"], z["T"]
        s = pv.PolyData(P, np.hstack([np.full((len(T), 1), 3), T]).astype(np.int64)).slice(normal="z", origin=(0, 0, ZC))
        if not s.lines.size:
            continue
        Q = s.points[:, :2]; L = s.lines.reshape(-1, 3)[:, 1:]
        angs = [0.0]
        if mode == "dial":
            angs = list(np.linspace(-TRAVEL, TRAVEL, 9))
        for k, a in enumerate(angs):
            R = rot(Q, a)
            for i, j in L:
                ax.plot([R[i, 0], R[j, 0]], [R[i, 1], R[j, 1]], color=col, lw=1.4 if a == 0 else 0.5, alpha=1.0 if a == 0 else 0.45)
        if mode == "knob":   # swept full circle: its inner radius at this z
            rmin = np.hypot(Q[:, 0], Q[:, 1]).min()
            ax.add_patch(plt.Circle((0, 0), rmin, fc="none", ec=col, lw=0.8, ls="--"))
ax.add_patch(Wedge((0, 0), R1 + CL, ANG - HALF - CL / 13.5 * 57.3, ANG + HALF + CL / 13.5 * 57.3, width=R1 - R0 + 2 * CL, fc="none", ec="k",
                   lw=1.0, ls=":"))
c = np.array([13.5 * math.cos(math.radians(ANG)), 13.5 * math.sin(math.radians(ANG))])
ax.plot(*c, "k+", ms=10)
kw = dict(fontsize=10.5, arrowprops=dict(arrowstyle="-", lw=0.7))
ax.annotate("outside: 0.45 from the pocket\nto the detent block's wall", (-15.0, 2.0), (-21.5, 9.0), **kw)
ax.annotate("one end: 0.6 to the dial's Hall spoke\nat full travel (thin blue: its sweep)", (-11.5, 4.7), (-12.0, 11.0), **kw)
ax.annotate("other end: 1.1 to idler pinion 2", (-13.3, -2.6), (-20.5, -7.5), **kw)
ax.annotate("inside: 2.9 free to the dial's tube", (-11.0, 1.2), (-8.0, -6.2), **kw)
ax.annotate("pedestal (brown) in its pocket (dotted)", (-13.9, 0.0), (-24.5, 4.2), **kw)
ax.set_xlim(-25, -4); ax.set_ylim(-9, 13); ax.set_aspect("equal")
ax.set_xlabel("x (mm, panel)"); ax.set_ylabel("y (mm, panel)")
fig.text(0.01, 0.985, "Room above the cradle plate round the pedestal (section at z 4.0; plate top 3.5)", fontsize=14, weight="bold", va="top")
fig.text(0.01, 0.95, "A taller thread needs the pocket floor raised, and the block then needs taller walls round it to stay guided. "
         "Only the inside has room for a wall.", fontsize=10.5, va="top")
fig.subplots_adjust(top=0.9, bottom=0.07)
fig.savefig(sys.argv[1])
print("wrote", sys.argv[1])
