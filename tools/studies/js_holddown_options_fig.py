"""10 Nov, Ed 14:44: two hold-down springs instead of four, and could they hook onto a pin through the vertical boards instead of
passing through the main board? Section across the joystick at its axis (panel y 40.63), from the cached v0.56 meshes, with the
springs as they are and the two options drawn over it.
  .venv/bin/python tools/studies/js_holddown_options_fig.py <out.png>   (from cad/knob-param)"""
import os, sys, json
import numpy as np
import pyvista as pv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
idx = json.load(open(os.path.join(HERE, "..", "..", "cad", "knob-param", ".cache-knob", "anim", "index.json")))["parts"]
Y = 40.63
STYLE = [("case", "#cfd8dc", "#90a4ae"), ("PCB", "#2e7d32", "#1b5e20"), ("vertical board", "#43a047", "#1b5e20"),
         ("joystick: joystick top board", "#43a047", "#1b5e20"), ("joystick: joystick carrier", "#78909c", "#37474f"),
         ("joystick: screen carrier", "#90a4ae", "#37474f"), ("joystick: top screen", "#212121", "#000"),
         ("MCU", "#212121", "#000"), ("joystick: rear spring anchor", "#8d6e63", "#4e342e"), ("joystick: cross pin", "#616161", "#212121"),
         ("joystick: ball", "#bdbdbd", "#616161"), ("joystick: SW1", "#424242", "#000"), ("back cover", "#455a64", "#263238")]


def mesh(n):
    z = np.load(idx[n]["mesh"]); P, T = z["P"], z["T"]
    return pv.PolyData(P, np.hstack([np.full((len(T), 1), 3), T]).astype(np.int64))


def section(ax, n, fc, ec):
    s = mesh(n).slice(normal="y", origin=(0, Y, 0))
    if s.n_points == 0:
        return
    for c in s.connectivity().split_bodies() if False else [s]:
        pass
    lines = s.lines.reshape(-1, 3)[:, 1:] if s.lines.size else []
    P = s.points
    for a, b in lines:
        ax.plot([P[a, 0], P[b, 0]], [P[a, 2], P[b, 2]], color=ec, lw=0.9)


fig, axs = plt.subplots(1, 2, figsize=(17, 9.6), dpi=110, gridspec_kw=dict(width_ratios=[1.35, 1]))
ax = axs[0]
for key, fc, ec in STYLE:
    for n in idx:
        if n.startswith(key) and not n.startswith("PCB back parts") and not n.startswith("PCB front parts"):
            section(ax, n, fc, ec)
# springs as built: four, two per side at y ±1.5 (this section sits between them): draw the side pair's outline
for sx in (-1, 1):
    ax.add_patch(Rectangle((sx * 12.5 - 1.0, -3.77), 2.0, 36.5 + 3.77, fc="#bdbdbd", ec="#616161", lw=0.8, alpha=0.55, zorder=3))
# option: a pin through both vertical boards near their bottom, the two springs hooked on it
zp = 4.2
ax.plot([-17.4, 17.4], [zp, zp], color="#7b1fa2", lw=3.2, zorder=6, solid_capstyle="round")
for sx in (-1, 1):
    ax.add_patch(Rectangle((sx * 12.5 - 1.0, zp), 2.0, 36.5 - zp, fc="none", ec="#7b1fa2", lw=1.6, ls="--", zorder=6))
ax.add_patch(Rectangle((-15.5, 1.6), 31.0, 30.0 - 1.6, fc="#ffcdd2", ec="none", alpha=0.35, zorder=1))
ax.text(0, zp + 0.8, "pin (Ed's idea)", ha="center", fontsize=10.5, color="#6a1b9a", weight="bold", zorder=8)
ax.text(0, 20.0, "boxed in", ha="center", fontsize=11, color="#b71c1c", weight="bold", zorder=8)
ax.text(0, -6.0, "rear anchor + cross pins (today)", ha="center", fontsize=10, color="#4e342e", zorder=8)
ax.text(-12.5, 37.6, "carrier hooks", ha="center", fontsize=9.5)
ax.set_xlim(-28, 28); ax.set_ylim(-17, 46); ax.set_aspect("equal")
ax.set_xlabel("x (mm, panel)"); ax.set_ylabel("z (mm; main board front at 0)")
ax.set_title("1. Across the joystick at its axis (y 40.63), seen from the panel's bottom", loc="left", fontsize=12.5, weight="bold")

# 2. plan of the main board holes: the figure-8 now, one round hole per side with two springs on the axis
ax = axs[1]
for col, sx in enumerate((-1, 1)):
    cx = sx * 12.5
    for dy in (-1.5, 1.5):
        ax.add_patch(Circle((cx, Y + dy), 1.7, fc="#eceff1", ec="#455a64", lw=1.2))
        ax.add_patch(Circle((cx, Y + dy), 1.0, fc="#bdbdbd", ec="#616161", lw=0.6))
    ax.add_patch(Circle((cx, Y), 1.7, fc="none", ec="#2e7d32", lw=2.2, zorder=5))
    ax.add_patch(Circle((cx, Y), 1.0, fc="none", ec="#2e7d32", lw=1.2, ls="--", zorder=5))
ax.set_xlim(-17.5, 17.5); ax.set_ylim(Y - 6, Y + 6); ax.set_aspect("equal")
ax.set_xlabel("x (mm, panel)"); ax.set_ylabel("y (mm, panel)")
ax.set_title("2. Main board holes, from the front", loc="left", fontsize=12.5, weight="bold")
ax.set_ylim(Y - 4.5, Y + 4.5)
fig.text(0.01, 0.975, "Joystick hold-down springs: two instead of four, and where they hook", fontsize=16, weight="bold", va="top")
fig.text(0.01, 0.935, "Two springs on the joystick's axis, each pulling 1.8 N (twice today's 0.9), give the same 3.6 N on the axis, so every "
         "tipping margin stays the same (the model's tipping sums use the total pull at the axis).", fontsize=11, va="top")
fig.subplots_adjust(bottom=0.17, top=0.86)
fig.text(0.01, 0.07, "1. Grey: the springs as built (four, two per side at y ±1.5, through the main board to the rear anchor's cross pins). "
         "Purple: Ed's pin through both vertical boards near their bottom (z ~4, over the H743), the two springs hooked on it.\n"
         "Pink: once the board stack is in the case this space is closed (main board below, top board above, a vertical board each side). "
         "The joystick goes in from the front and the stack from the back,\nso one end of each spring has to be hooked after both are in: today that is "
         "the lower end, from the back with the cover off. On the pin, nothing can reach it.", fontsize=10.5, va="top")
fig.text(0.62, 0.30, "2. Grey: today, one figure-8 per side. Green: two springs on the axis,\none round Ø3.4 hole per side. "
         "It sits inside today's routing:\nnearest copper 0.29 (right, the same track as now) and 0.43 (left).\nNo re-route.", fontsize=10.5, va="top")
fig.savefig(sys.argv[1])
print("wrote", sys.argv[1])
