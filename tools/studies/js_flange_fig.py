"""26 Nov, sweep item A6: the joystick cradle's flange (printed with the case since v0.25) stops 0.85 short of the case's side wall:
0.20 air past the drawn glow coat, which is modelled 0.35 thick and 0.30 off the wall (the real coat is a film on the wall). Its
height is the v0.8 bead's (flange top 0.62 under the faceplate back, closed by a riser). Section across the case through the
joystick, from the cached model.
  .venv/bin/python ../../tools/studies/js_flange_fig.py <out.png>   (from cad/knob-param)"""
import os, sys, json
import numpy as np
import pyvista as pv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

idx = json.load(open(os.path.join(".cache-knob", "anim", "index.json")))["parts"]
Y = float(sys.argv[2]) if len(sys.argv) > 2 else 34.0
STY = [("case", "#455a64", 1.1), ("glow coat (inside walls)", "#7cb342", 1.4), ("joystick: joystick carrier (printed)", "#8e24aa", 0.9),
       ("joystick: joystick top board", "#2e7d32", 0.9), ("joystick: screen carrier (printed)", "#f57c00", 0.9),
       ("joystick: top-board socket R", "#6d4c41", 0.8)]
fig, axs = plt.subplots(1, 2, figsize=(15, 7.2), dpi=110, gridspec_kw=dict(width_ratios=[1.35, 1]))
for ax, (x0, x1, z0, z1) in zip(axs, ((0, 25.8, 24, 46), (19.0, 23.4, 32.6, 37.4))):
    for key, col, lw in STY:
        for n in idx:
            if not n.startswith(key):
                continue
            z = np.load(idx[n]["mesh"]); P, T = z["P"], z["T"]
            s = pv.PolyData(P, np.hstack([np.full((len(T), 1), 3), T]).astype(np.int64)).slice(normal="y", origin=(0, Y, 0))
            if not s.lines.size:
                continue
            Q = s.points
            for a, b in s.lines.reshape(-1, 3)[:, 1:]:
                ax.plot([Q[a, 0], Q[b, 0]], [Q[a, 2], Q[b, 2]], color=col, lw=lw)
    ax.set_xlim(x0, x1); ax.set_ylim(z0, z1); ax.set_aspect("equal")
    ax.set_xlabel("x (mm, panel)"); ax.set_ylabel("z (mm; main board front 0)")
ax = axs[1]; kw = dict(fontsize=10.5, arrowprops=dict(arrowstyle="-", lw=0.7))
ax.annotate("faceplate (2.5)", (21.0, 37.0), (20.4, 36.85), fontsize=10.5)
ax.annotate("flange + riser\n(printed with the case)", (21.0, 35.5), (20.25, 35.0), fontsize=10.5)
ax.annotate("side wall", (23.0, 34.0), (22.85, 33.4), fontsize=10.5)
ax.annotate("the notch: 0.85 wide,\n1.62 deep, open below", (22.3, 35.2), (20.4, 33.2), **kw)
ax.annotate("glow coat as drawn\n(really a film on the wall)", (22.25, 35.4), (22.85, 36.6), **kw)
axs[0].set_title(f"1. Across the case through the joystick (y {Y:g}), +x half", loc="left", fontsize=12, weight="bold")
axs[1].set_title("2. Close-up: flange edge and side wall", loc="left", fontsize=12, weight="bold")
fig.text(0.01, 0.98, "Joystick cradle flange (sweep item A6): grey = the case with the cradle printed in, green = the drawn glow coat",
         fontsize=14, weight="bold", va="top")
fig.text(0.01, 0.935, "The flange stops 0.85 from the side wall: 0.20 air past the glow coat, which the model draws 0.35 thick and 0.30 off "
         "the wall (the real coat is a film on the wall).\nIn the print that leaves a narrow slot between flange and wall, open underneath. "
         "Joining the flange to the wall closes the slot; the coat would stop under the flange there.", fontsize=10.5, va="top")
fig.subplots_adjust(top=0.84, bottom=0.08, wspace=0.12)
fig.savefig(sys.argv[1])
print("wrote", sys.argv[1])
