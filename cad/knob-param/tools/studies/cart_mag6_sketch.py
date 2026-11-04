# Sketch for Danny (4 Nov 10:42, dial item 3): six Ø1 x 0.5 magnet pairs instead of three Ø1 x 0.8, so the skirt skin outside each
# bezel magnet is 1.00 (PCBWay MJF wall) and the pull-down goes up. Two sets of three at 120° (0/120/240, 30/150/270), so the sideways
# pulls cancel. Drawn from the v0.25 numbers (not cut from the model). Forces from control_dial.params._pair_force.
# Run from cad/knob-param:  .venv/bin/python tools/studies/cart_mag6_sketch.py OUT.png
import sys, math
sys.path.insert(0, ".")
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Rectangle, Polygon
from knobparam.control_dial.params import _pair_force

R, RB, RO, RW0 = 21.0, 19.5, 19.2, 17.3       # bezel OD, bezel bore, dial outer wall, land inner edge
NEW = (0, 30, 120, 150, 240, 270); OLD = (30, 150, 240)
KEY, SEAT, PLUG = 180, (60, 340), (298, 332)
fig = plt.figure(figsize=(15, 7.6), dpi=120)
ax = fig.add_axes([0.02, 0.06, 0.50, 0.86]); ax2 = fig.add_axes([0.58, 0.12, 0.40, 0.76])
ax.add_patch(Wedge((0, 0), R, 0, 360, width=R - RB, fc="#3a3f44", ec="none"))
ax.add_patch(Wedge((0, 0), RO, 0, 360, width=RO - RW0, fc="#8a8f94", ec="none"))
ax.add_patch(Wedge((0, 0), RO + 0.02, PLUG[0], PLUG[1], width=RO - 16.0, fc="#ffe0b2", ec="#e65100", lw=0.8, alpha=0.8))
def box(a, r0, r1, w, **k):
    t = math.radians(a); u = np.array([math.cos(t), math.sin(t)]); v = np.array([-u[1], u[0]])
    P = [r0 * u - w / 2 * v, r1 * u - w / 2 * v, r1 * u + w / 2 * v, r0 * u + w / 2 * v]
    ax.add_patch(Polygon(P, closed=True, **k))
box(KEY, 18.6, RB, 1.2, fc="#d81b60", ec="none")
for a in SEAT:
    box(a, 18.6, RB, 1.2, fc="#f48fb1", ec="none")
for a in OLD:
    box(a, RO - 0.8, RO, 1.05, fc="none", ec="#1565c0", ls="--", lw=0.9); box(a, RB, RB + 0.8, 1.05, fc="none", ec="#1565c0", ls="--", lw=0.9)
for a in NEW:
    box(a, RO - 0.5, RO, 1.05, fc="#b0bec5", ec="black", lw=0.6); box(a, RB, RB + 0.5, 1.05, fc="#b0bec5", ec="black", lw=0.6)
    t = math.radians(a); ax.text(23.3 * math.cos(t), 23.3 * math.sin(t), f"{a}°", ha="center", va="center", fontsize=9)
t = math.radians(KEY); ax.annotate("key 180°", (19.0 * math.cos(t), 19.0 * math.sin(t)), (-17, 6), fontsize=9,
                                   arrowprops=dict(arrowstyle="-", lw=0.7))
for a in SEAT:
    t = math.radians(a); ax.annotate(f"seat rib {a}°", (19.0 * math.cos(t), 19.0 * math.sin(t)),
                                     (8 if a == 60 else 6, 9 if a == 60 else -8), fontsize=9, arrowprops=dict(arrowstyle="-", lw=0.7))
ax.annotate("plug lobe + pad arm (298-332°): keep clear", (13.5, -13.5), (4, -24.5), fontsize=9, arrowprops=dict(arrowstyle="-", lw=0.7))
ax.text(0, 1.5, "plan of the dial top (panel angles)\nfilled: proposed 6 pairs Ø1 x 0.5\ndashed blue: now, 3 pairs Ø1 x 0.8",
        ha="center", va="center", fontsize=9.5)
ax.text(0, -3.6, "dark ring: bezel skirt (r 19.5-21.0)\ngrey ring: dial wall (to r 19.2)\n0.30 gap between them", ha="center",
        va="center", fontsize=8.5, color="#444")
ax.set_xlim(-25, 25); ax.set_ylim(-25, 25); ax.set_aspect("equal"); ax.axis("off")
ax.set_title("1. Where the six pairs go (two sets of three, 120° apart: the sideways pulls cancel)", fontsize=10.5, loc="left")
# ---- 2: radial cut through one pair ----
a2 = ax2
a2.add_patch(Rectangle((RB, 52.8), R - RB, 8.4, fc="#3a3f44", ec="none"))
a2.add_patch(Rectangle((16.3, 52.8), RO - 16.3, 3.1, fc="#8a8f94", ec="none"))
zd = 54.35; zs = zd + 0.4
a2.add_patch(Rectangle((RO - 0.5, zd - 0.5), 0.5, 1.0, fc="#b0bec5", ec="black", lw=0.8))
a2.add_patch(Rectangle((RB, zs - 0.5), 0.5, 1.0, fc="#b0bec5", ec="black", lw=0.8))
a2.add_patch(Rectangle((RO - 0.8, zd - 0.5), 0.8, 1.0, fc="none", ec="#1565c0", ls="--", lw=0.9))
a2.add_patch(Rectangle((RB, zs - 0.5), 0.8, 1.0, fc="none", ec="#1565c0", ls="--", lw=0.9))
k = dict(fontsize=9, arrowprops=dict(arrowstyle="-", lw=0.7))
a2.annotate("skin 1.00 outside the Ø1 x 0.5\n(meets PCBWay's 1.0 MJF wall;\nwas 0.70 with Ø1 x 0.8, dashed)", (20.5, zs), (21.4, 57.6), **k)
a2.annotate("0.30 gap: slip fit\n(both parts MJF ±0.25)", (19.35, 53.6), (14.6, 51.6), **k)
a2.annotate("dial magnet, facing out", (RO - 0.25, zd - 0.3), (14.6, 57.0), **k)
a2.annotate("bezel magnet, 0.4 higher,\nfacing in (attracting)", (RB + 0.25, zs + 0.3), (14.6, 59.3), **k)
a2.text(16.5, 55.3, "dial", fontsize=9, color="white"); a2.text(20.0, 60.4, "bezel\nskirt", fontsize=9, color="white", ha="center")
a2.set_xlim(14.3, 24.5); a2.set_ylim(51.0, 61.4); a2.set_aspect("equal"); a2.grid(alpha=0.2)
a2.set_xlabel("r (mm)"); a2.set_ylabel("z (mm)")
a2.set_title("2. Radial cut through one pair", fontsize=10.5, loc="left")
def tot(h, n):
    return -_pair_force(1.0, h, 0.30, 0.4, 1.45)[2] * n
fig.suptitle(f"Dial item 3: magnets. Now 3 x Ø1 x 0.8: {tot(0.8, 3):.2f} N pull-down, skin 0.70. Proposed 6 x Ø1 x 0.5: {tot(0.5, 6):.2f} N, "
             "skin 1.00, no net sideways pull", fontsize=11.5, x=0.01, ha="left")
fig.savefig(sys.argv[1]); print("wrote", sys.argv[1])
