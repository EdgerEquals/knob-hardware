"""Main-board pass, plan picture (7 Nov 2026): the main board's outline and windows from the model (v0.50), with what sits on it
now - the fixed-position parts (Hall row, emitter ring, encoder, motor, rod pad, MCU, vertical-board headers, the jack unit's posts,
the link flex pads) - front and back. Run from cad/knob-param:
  KNOBPARAM_CACHE=$PWD/.cache-knob .venv/bin/python ../../tools/studies/main_board_inventory_sketch.py <out.png>"""
import os, sys
sys.path.insert(0, os.getcwd())
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from build123d import Plane
from knobparam.common import model
from knobparam.assembly.build import build_all

D = model.derive(model.default_params())
parts, _, _, owner = build_all(D)
pcb = parts["PCB"]
sec = pcb.intersect(Plane.XY.offset(-0.8))
loops = [[(v.X, v.Y) for v in w.positions([i / 200 for i in range(201)])] for f in sec.faces() for w in f.wires()]
z_front, z_back = 0.0, -1.6
GROUPS = [  # (label, name test, colour)
    ("Hall row", lambda n: n.startswith("hall sensor"), "#8e24aa"),
    ("emitters (12 RGB + 12 VCSEL)", lambda n: n.startswith("emitter"), "#ef6c00"),
    ("MCU H7B0 LQFP100", lambda n: n.startswith("MCU"), "#c62828"),
    ("clear OLED", lambda n: n.startswith("clear OLED 1.51"), "#00acc1"),
    ("encoder sensor + bearings", lambda n: n.startswith(("encoder sensor", "encoder bearing")), "#f9a825"),
    ("1220 motor", lambda n: n == "motor", "#6d4c41"),
    ("rod pad / rod clamp", lambda n: n.startswith("PCB rod pad"), "#5d4037"),
    ("vertical boards L / R", lambda n: n.startswith("vertical board") and "header" in n, "#1565c0"),
    ("jack unit posts (15 V, GND)", lambda n: n.startswith("jack unit post"), "#424242"),
    ("link flex pads", lambda n: n.startswith("link flex ("), "#d32f2f"),
    ("back parts (KiCad v0.11 proxy)", lambda n: n.startswith("PCB back parts"), "#9e9e9e"),
]
fig, axs = plt.subplots(1, 2, figsize=(14, 12), dpi=130)
for ax, (side, title) in zip(axs, (("F", "front (towards the knob and faceplate)"), ("B", "back (towards the back cover)"))):
    for lp in loops:
        ax.add_patch(Polygon(lp, closed=True, fc="#e8f5e9", ec="#2e7d32", lw=0.8, zorder=1))
    for lab, test, col in GROUPS:
        first = True
        for n, s in parts.items():
            if not test(n):
                continue
            for sol in ([s] if not hasattr(s, "solids") else s.solids() or [s]):
                bb = sol.bounding_box()
                on_front = bb.max.Z > z_front + 0.01 and bb.min.Z < z_front + 6.0
                on_back = bb.min.Z < z_back - 0.01 and bb.max.Z > z_back - 6.0
                if (side == "F" and not on_front) or (side == "B" and not on_back):
                    continue
                if bb.max.Z - bb.min.Z > 30:   # tall things (motor can) drawn only where they meet the board
                    pass
                ax.add_patch(Rectangle((bb.min.X, bb.min.Y), bb.max.X - bb.min.X, bb.max.Y - bb.min.Y, fc=col, ec="black", lw=0.3,
                                       alpha=0.55, zorder=3, label=lab if first else None))
                first = False
    bb = pcb.bounding_box()
    ax.set_xlim(bb.min.X - 2, bb.max.X + 2); ax.set_ylim(bb.min.Y - 2, bb.max.Y + 2); ax.set_aspect("equal"); ax.grid(alpha=0.15)
    ax.set_title(f"Main board, {title}; panel coordinates, seen from the front", fontsize=9, loc="left")
    ax.set_xlabel("x (mm)")
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.06), ncol=2, fontsize=7.5, frameon=False)
axs[0].set_ylabel("y (mm)")
fig.suptitle(f"Main board inventory, model {D.get('version')}: outline and windows from the model; boxes = what is placed now", fontsize=10,
             x=0.01, ha="left")
fig.tight_layout(); fig.savefig(sys.argv[1]); print("wrote", sys.argv[1])
