"""Main-board pass, Q32 picture (7 Nov 2026): the H7B0's one fast quad port on LQFP100, and why the LQFP144 (two ports) is not
offered. Left: the top of the main board from the model (v0.50) with the LQFP100 and LQFP144 land outlines centred where the MCU
sits now. Right: the two ways to use the one quad port, with the numbers. Run from cad/knob-param:
  KNOBPARAM_CACHE=$PWD/.cache-knob .venv/bin/python ../../tools/studies/qspi_port_choice_sketch.py <out.png>"""
import os, sys
sys.path.insert(0, os.getcwd())
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, FancyBboxPatch
from build123d import Plane
from knobparam.common import model
from knobparam.assembly.build import build_all

D = model.derive(model.default_params())
parts, _, _, owner = build_all(D)
pcb = parts["PCB"]
sec = pcb.intersect(Plane.XY.offset(-0.8))
loops = [[(v.X, v.Y) for v in w.positions([i / 300 for i in range(301)])] for f in sec.faces() for w in f.wires()]
mcu = [s for n, s in parts.items() if n.startswith("MCU")][0].bounding_box()
cx, cy = (mcu.min.X + mcu.max.X) / 2, (mcu.min.Y + mcu.max.Y) / 2
hdr = [s.bounding_box() for n, s in parts.items() if n.startswith("vertical board") and "header" in n]

# land outlines: lead tips + 0.6 mm pad overhang (IPC-7351 nominal), and a 1 mm courtyard
LANDS = [("LQFP100 (14 x 14 body, 16 x 16 over leads)", 16.0 + 1.2, "#2e7d32"),
         ("LQFP144 (20 x 20 body, 22 x 22 over leads)", 22.0 + 1.2, "#c62828")]

fig = plt.figure(figsize=(15, 8.2), dpi=130)
ax = fig.add_axes([0.04, 0.1, 0.36, 0.78])
for lp in loops:
    ax.add_patch(Polygon(lp, closed=True, fc="#e8f5e9", ec="#2e7d32", lw=0.8, zorder=1))
for b in hdr:
    ax.add_patch(Rectangle((b.min.X, b.min.Y), b.max.X - b.min.X, b.max.Y - b.min.Y, fc="#1565c0", alpha=0.5, ec="k", lw=0.3, zorder=2))
for lab, w, col in LANDS:
    ax.add_patch(Rectangle((cx - w / 2, cy - w / 2), w, w, fc=col, alpha=0.18, ec=col, lw=1.5, zorder=3, label=lab + f": land {w:.1f}"))
    ax.add_patch(Rectangle((cx - w / 2 - 1, cy - w / 2 - 1), w + 2, w + 2, fc="none", ec=col, lw=0.8, ls="--", zorder=3))
ax.text(cx, cy, "LQFP144 runs into\nthe board edge, the\njoystick's screw and\nspring holes and\nthe window", ha="center", va="center",
        fontsize=8.5, color="#c62828")


def gap(w):   # smallest distance from a square land (side w, centred on the MCU) to any cut-out or the board edge
    import math
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - w / 2, cy + w / 2
    best = 1e9
    for lp in loops:
        for x, y in lp:
            dx = max(x0 - x, 0, x - x1); dy = max(y0 - y, 0, y - y1)
            inside = x0 < x < x1 and y0 < y < y1
            best = min(best, -1 if inside else math.hypot(dx, dy))
    return best


for lab, w, col in LANDS:
    print(lab, "land to nearest cut-out / edge:", round(gap(w), 2), "mm" if gap(w) >= 0 else "(overlaps)")
ax.set_xlim(-24, 24); ax.set_ylim(18, 51); ax.set_aspect("equal"); ax.grid(alpha=0.15)
ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm)")
ax.set_title(f"Top of the main board, front, model {D.get('version')}\n(dashed = 1 mm courtyard; blue = vertical-board headers)",
             fontsize=9, loc="left")
ax.legend(loc="upper left", bbox_to_anchor=(0, -0.11), fontsize=8, frameon=False)

bx = fig.add_axes([0.43, 0.02, 0.56, 0.88]); bx.axis("off"); bx.set_xlim(0, 100); bx.set_ylim(0, 100)


def box(x, y, w, h, text, fc, fs=9, bold=False):
    bx.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6", fc=fc, ec="#333", lw=0.8))
    bx.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, weight="bold" if bold else None)


def arrow(x0, y0, x1, y1, text, col, lw):
    bx.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", lw=lw, color=col))
    bx.text((x0 + x1) / 2, (y0 + y1) / 2 + 1.6, text, ha="center", va="bottom", fontsize=8, color=col)


for y0, tag, fast, slow, notes in (
        (52, "A  (recommended)", "joystick screen", "flash (animations + program)",
         ["Joystick screen on the quad port, as its jumper is drawn now (no change).",
          "Full 456 x 280 frame at 50 MHz: about 98 per second.",
          "Flash on a plain 1-bit SPI: about 6-10 MB/s, a full screen-sized frame 24-39 times a second.",
          "Program: a small loader in the chip's own 128 KB; the main program is copied",
          "from the flash into RAM at power-up (about 0.05 s for 0.5 MB). Normal practice."]),
        (4, "B", "flash (animations + program)", "joystick screen",
         ["Program runs straight from the flash (no 128 KB limit, no copy at power-up).",
          "Joystick screen on a plain 1-bit SPI: full frame about 24 per second at 50 MHz.",
          "The joystick jumper changes: the screen's mode straps to SPI, a D/C line added.",
          "", ""])):
    bx.text(0, y0 + 44, tag, fontsize=12, weight="bold")
    box(2, y0 + 22, 18, 14, "STM32H7B0\nLQFP100", "#ffcdd2", 10, True)
    box(46, y0 + 31, 30, 7, fast, "#c8e6c9")
    box(46, y0 + 20, 30, 7, slow, "#fff9c4")
    arrow(21, y0 + 33, 45, y0 + 34.5, "quad port (4 data lines, 6 pins)", "#2e7d32", 2.4)
    arrow(21, y0 + 25, 45, y0 + 23.5, "plain SPI (1 data line, 4 pins)", "#9e9d24", 1.2)
    for i, ln in enumerate(notes):
        bx.text(2, y0 + 16 - i * 3.6, ln, fontsize=8.6)
fig.text(0.04, 0.975, "Q32: the H7B0 on LQFP100 has one fast quad port (ST pin data: Octo-SPI port 1 only). Who gets it?",
        fontsize=12, weight="bold", va="top")
fig.text(0.04, 0.945, "Both fit: 77 nets on 82 I/O pins, 5 spare either way. Pin map solved from ST's own pin data.",
        fontsize=9, va="top")
fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "qspi-port-choice.png")
print("mcu centre", round(cx, 2), round(cy, 2))
