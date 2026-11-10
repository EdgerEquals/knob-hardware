"""10 Nov sweep, item A2: the knob collar under the faceplate (case/parts/shell.py: a Ø47.4 x 7.5 tube round the knob hole, from v0.1,
for the labyrinth and the knob bolts, both gone). Section through the knob axis from the cached model, the glass and the case.
  .venv/bin/python tools/studies/knob_collar_fig.py <out.png>   (from the repo root)"""
import os, sys, json
import numpy as np
import pyvista as pv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
idx = json.load(open(os.path.join(HERE, "..", "..", "cad", "knob-param", ".cache-knob", "anim", "index.json")))["parts"]
R_HOLE, R_COL, Z0, ZFP0, ZFP1 = 21.2, 23.7, 28.8, 36.3, 38.8   # case/params.py (v0.57)


def cut(name):
    z = np.load(idx[name]["mesh"]); P, T = z["P"], z["T"]
    s = pv.PolyData(P, np.hstack([np.full((len(T), 1), 3), T]).astype(np.int64)).slice(normal="x", origin=(0, 0, 0))
    L = s.lines.reshape(-1, 3)[:, 1:] if s.lines.size else []
    return s.points, L


fig, axs = plt.subplots(1, 2, figsize=(15, 8.6), dpi=110, gridspec_kw=dict(width_ratios=[1.25, 1]))
for ax, (x0, x1, z0, z1) in zip(axs, ((-27, 27, 0, 55), (17.5, 26.5, 25.5, 42.5))):
    for n, col, lw in (("case", "#455a64", 1.0), ("knob glass sleeve", "#0288d1", 1.6), ("knob drip O-ring 40x1 silicone (on the glass)", "#6d4c41", 1.2),
                       ("knob upper-cap (clear UTR-8100: web, plug, glass seat)", "#90a4ae", 0.8), ("knob lower-cap land", "#90a4ae", 0.8)):
        P, L = cut(n)
        for a, b in L:   # the axes clip what is outside the window
            ax.plot([P[a, 1], P[b, 1]], [P[a, 2], P[b, 2]], color=col, lw=lw)
    for sx in (-1, 1):
        x = R_HOLE if sx > 0 else -R_COL
        ax.add_patch(Rectangle((x, Z0), R_COL - R_HOLE, ZFP0 - Z0, fc="#ff9800", ec="none", alpha=0.45))
    ax.set_xlim(x0, x1); ax.set_ylim(z0, z1); ax.set_aspect("equal")
    ax.set_xlabel("y (mm, panel; + toward the joystick)"); ax.set_ylabel("z (mm; main board front at 0)")
ax = axs[1]
ax.annotate("", (R_HOLE, Z0 - 1.2), (R_HOLE, ZFP1), arrowprops=dict(arrowstyle="<->", color="#c62828", lw=1.2))
ax.text((R_HOLE + R_COL) / 2 + 0.1, 34.0, "glass in a bore\nwith 0.20 air:\n10.0 long", ha="center", fontsize=10, color="#c62828")
ax.annotate("faceplate (2.5)", (24.5, (ZFP0 + ZFP1) / 2), (24.0, 41.2), fontsize=10, arrowprops=dict(arrowstyle="-", lw=0.7))
ax.text((R_HOLE + R_COL) / 2 + 0.1, Z0 + 1.2, "collar\n(orange)", ha="center", fontsize=10.5)
ax.plot([R_HOLE + 0.7] * 2, [Z0, ZFP0], color="#2e7d32", lw=2, ls="--")
ax.text(R_HOLE + 0.85, Z0 - 2.6, "option: collar bored out\nto 0.7 air (green)", fontsize=10, color="#2e7d32")
ax.set_title("2. Close-up, the side toward the joystick", loc="left", fontsize=12, weight="bold")
axs[0].set_title("1. Through the knob axis (x 0), from the side", loc="left", fontsize=12, weight="bold")
fig.text(0.01, 0.975, "Knob collar under the faceplate: a Ø47.4 x 7.5 tube round the knob hole (orange)", fontsize=15, weight="bold", va="top")
fig.text(0.01, 0.93, "Added in v0.1 for the labyrinth seal and the four knob bolts (both gone; bolts removed 2 Nov). The glass (blue) now runs 10 mm "
         "through a bore with 0.20 mm of air instead of the faceplate's 2.5 mm.\nThe tube still stiffens the faceplate round its biggest hole "
         "(4.05 mm of plate each side of the hole), and the joystick cradle's flange edge is set from its radius.", fontsize=10.5, va="top")
fig.subplots_adjust(top=0.84, bottom=0.08)
fig.savefig(sys.argv[1])
print("wrote", sys.argv[1])
