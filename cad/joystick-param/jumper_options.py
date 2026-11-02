"""Jumper options sketch (2 Nov, after the v0.6 build): section y = 0 at the +x end with the two candidate routes drawn over it.
A: a long flex down the free column just outside the cradle ring to a socket on the main PCB. B: a fine-wire pigtail in the
existing drop, from a small board on the panel's header to pads on the daughterboard tab. Routes are sketches, not parts.
Run from cad/joystick-param:  python jumper_options.py <out.png>"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Rectangle, Patch
from matplotlib.lines import Line2D
from jsparam import params, parts
from section_v06 import faces, colour

D = params.derive(params.P)
P = parts.build(D)
fig, axs = plt.subplots(1, 2, figsize=(17, 10.5))
zr, xr = D["z_run"], D["jmp_x"] + D["jmp_stiff"][0] / 2
for ax, opt in zip(axs, "AB"):
    for n, s in P.items():
        if n.startswith(("main PCB", "rear spring", "cross pin", "screen jumper FPC", "screen jumper plug")):
            continue
        b = s.bounding_box()
        if not (b.min.Y < 0 < b.max.Y):
            continue
        tr = faces(s, "y", 0.0)
        if tr:
            ax.add_collection(PolyCollection(tr, facecolors=colour(n)[1], edgecolors="none", alpha=0.95))
    ax.add_patch(Rectangle((-30, -1.6), 60, 1.6, fc="#1e6b35", ec="none"))                       # main PCB
    ax.add_patch(Rectangle((16.3, 0.5), 3.9, 36.6, fill=False, ls="--", lw=1.2, ec="#555555"))    # free column
    ax.text(16.4, 26.5, "free column\noutside the cradle\n4 × 10 × 30\n(x 16.3–20.2, y ±5)", fontsize=7.5, color="#444444")
    ax.add_patch(Rectangle((18.95, -1.6), 4.5, 6.45, fill=False, ls=":", lw=1.0, ec="#8a6d00"))    # case corner screw (y 2.5-7)
    ax.text(20.4, 5.3, "case corner screw\n(y +2.5..+7)", fontsize=7, color="#8a6d00")
    if opt == "A":
        ax.plot([xr, 18.0, 18.0], [zr + 0.06, zr + 0.06, 21.0], color="#d62728", lw=2.2)
        ax.plot([18.0, 17.2, 17.2], [21.0, 19.5, 6.0], color="#d62728", lw=2.2, ls=(0, (4, 1.5)))
        ax.plot([17.2, 17.2], [6.0, 2.2], color="#d62728", lw=2.2)
        ax.add_patch(Rectangle((16.4, 0.0), 2.6, 2.2, fc="#111111", ec="none"))
        ax.text(18.3, 30.0, "x-facing section\n~17 mm: 0.03%", fontsize=8, color="#d62728")
        ax.text(17.5, 13.0, "90° fold;\ny-facing section\n~15 mm: 0.04%", fontsize=8, color="#d62728")
        ax.text(12.0, 3.0, "socket on the main PCB,\npress taken in a stub\nalong y (~9 mm): 0.08%", fontsize=8, color="#d62728", ha="right")
        ttl = ("A: flex down beside the cradle to the main PCB\nsingle-layer 0.07 [A], ~3 mm wide; strains vs 0.15%: x 4.6×, y 3.6×, press ~1.9×")
    else:
        import numpy as np
        t = np.linspace(0, 1, 60)
        x = 16.0 + 1.6 * np.sin(2 * np.pi * t) * (1 - t) ** 0.5
        z = (zr + 0.06) * (1 - t) + 32.3 * t
        ax.plot([xr, 16.0], [zr + 0.06, zr + 0.06], color="#1f77b4", lw=2.2)
        ax.plot(x, z, color="#1f77b4", lw=2.2)
        ax.add_patch(Rectangle((D["jmp_x"] - 2.2, D["z_js0"] - 0.6), 4.4, 0.6, fc="#2e7d32", ec="none"))
        ax.text(9.0, 38.5, "small board on the\npanel's header (socket)", fontsize=8, color="#1f77b4", ha="right")
        ax.text(17.8, 34.5, "~16 fine wires, loose loop\n(silicone 36–40 AWG [A])", fontsize=8, color="#1f77b4")
        ax.text(17.8, 32.0, "soldered to pads on the\ndaughterboard tab", fontsize=8, color="#1f77b4")
        ttl = ("B: fine-wire pigtail in the existing drop\nwire bending strain ≪ 0.1% in every direction; main PCB unchanged")
    ax.set_xlim(4, 24); ax.set_ylim(-2, 46); ax.set_aspect("equal"); ax.grid(True, lw=0.3)
    ax.set_title(ttl, fontsize=9.5); ax.set_xlabel("x (mm)"); ax.set_ylabel("z (mm, main-PCB front = 0)")
fig.suptitle("Joystick v0.6: two ways to get the screen's signals past the ±0.45 slide and the 0.35 press (section y = 0, +x end; routes are sketches)",
             fontsize=10.5, x=0.01, ha="left")
fig.subplots_adjust(top=0.9, bottom=0.06, wspace=0.12)
fig.savefig(out, dpi=100); print("wrote", out)
