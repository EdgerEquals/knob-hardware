"""10 Nov sweep, item A3: the dial's detent pedestal grub (M2 x 2 in the cradle plate, key hole Ø1.6 through the main board). Section
through the knob axis at the detent (mechanism 263°, panel 173°) from the cached model.
  .venv/bin/python tools/studies/pedestal_grub_fig.py <out.png>   (from the repo root)"""
import os, sys, json, math
import numpy as np
import pyvista as pv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
idx = json.load(open(os.path.join(HERE, "..", "..", "cad", "knob-param", ".cache-knob", "anim", "index.json")))["parts"]
A = math.radians(173.0)                       # panel frame = mechanism 263° turned -90°
u = np.array([math.cos(A), math.sin(A), 0.0]); nrm = np.array([-math.sin(A), math.cos(A), 0.0])
STY = [("base cradle", "#90a4ae"), ("detent block (", "#fbc02d"), ("detent train pedestal", "#8d6e63"), ("detent pedestal grub", "#212121"),
       ("detent 1 ", "#424242"), ("track 1 ", "#757575"), ("control dial lower part", "#1e88e5"), ("PCB", "#2e7d32"),
       ("control dial dish", "#64b5f6"), ("knob lower-cap land", "#b0bec5"), ("bottom internal ring", "#b0bec5")]
fig, ax = plt.subplots(figsize=(13, 8.4), dpi=110)
for key, col in STY:
    for n in idx:
        if not n.startswith(key) or n.startswith(("PCB back", "PCB front", "PCB rod")):
            continue
        z = np.load(idx[n]["mesh"]); P, T = z["P"], z["T"]
        s = pv.PolyData(P, np.hstack([np.full((len(T), 1), 3), T]).astype(np.int64)).slice(normal=tuple(nrm), origin=(0, 0, 0))
        if not s.lines.size:
            continue
        Q = s.points; r = Q @ u
        for a, b in s.lines.reshape(-1, 3)[:, 1:]:
            if r[a] > 0:
                ax.plot([r[a], r[b]], [Q[a, 2], Q[b, 2]], color=col, lw=1.3 if "grub" in n else 0.9)
ax.annotate("pedestal grub M2x2\n(tapped into the plate)", (13.5, 1.3), (17.2, -4.6), fontsize=10.5, arrowprops=dict(arrowstyle="-", lw=0.8))
ax.annotate("key hole Ø1.6 through the\nmain board, from behind", (13.5, -0.8), (5.0, -6.2), fontsize=10.5, arrowprops=dict(arrowstyle="-", lw=0.8))
ax.annotate("pedestal and ball train", (13.6, 4.6), (17.2, 1.8), fontsize=10.5, arrowprops=dict(arrowstyle="-", lw=0.8))
ax.annotate("detent flange on the dial's lower part (blue)", (13.4, 6.4), (2.0, 13.0), fontsize=10.5, arrowprops=dict(arrowstyle="-", lw=0.8))
ax.annotate("detent block (ball, spring, grub)", (13.5, 11.5), (16.5, 15.5), fontsize=10.5, arrowprops=dict(arrowstyle="-", lw=0.8))
ax.set_xlim(0, 25); ax.set_ylim(-8, 18); ax.set_aspect("equal")
ax.set_xlabel("distance from the knob axis along the detent's line (mm)"); ax.set_ylabel("z (mm; main board front at 0)")
fig.text(0.01, 0.975, "The dial's detent pedestal grub", fontsize=15, weight="bold", va="top")
fig.text(0.01, 0.94, "Its v0.22 job: set the ball train under the detent so the dial's spoke just lifted off the knob race. Since the v0.25 split "
         "the dish sits on the race and the lower part on the train,\nand the bond between them takes up the difference, so that job has gone. "
         "What it can still do: lift or drop the lower part ±0.25 before the dish is bonded, which sets\nthe Hall bar's gap to H3 "
         "(0.30 now against a 0.29 minimum, the tightest row there; the MJF parts are ±0.25).", fontsize=10.5, va="top")
fig.subplots_adjust(top=0.84, bottom=0.08)
fig.savefig(sys.argv[1])
print("wrote", sys.argv[1])
