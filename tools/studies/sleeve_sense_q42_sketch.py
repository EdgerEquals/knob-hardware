"""Q42 picture (8 Nov 2026, noise sweep, found while doing Q41): the jack sleeves' ground and the jack lower board's analog ground
(DAC, CV-out and CV-in op-amps) are joined only through the two 2x6 stacks, and the whole module's supply current crosses the first
pair. Stack pin lists: jack-board make_board.py HDR_NETS and jack-power-board design.py STACK2 [S, ours]; contact resistance and
currents [A]. Pure matplotlib:
  python3 tools/studies/sleeve_sense_q42_sketch.py docs/img/sleeve-sense-q42.png"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig = plt.figure(figsize=(16, 9.6), dpi=125)
ax = fig.add_axes([0.01, 0.01, 0.98, 0.9]); ax.axis("off"); ax.set_xlim(0, 160); ax.set_ylim(0, 92)
fig.text(0.015, 0.975, "Q42: the jacks' sleeves and the CV circuits' ground are two stacks apart", fontsize=14, weight="bold", va="top")
fig.text(0.015, 0.945, "A CV is the voltage between tip and sleeve, so any voltage between the sleeves and the lower board's ground adds "
         "straight to every CV out and every CV-in reading: 1 mV = 1.2 cents.", fontsize=10, va="top")


def box(x, y, w, h, t, fc, fs=8.6, b=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.45", fc=fc, ec="#333", lw=0.9))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, weight="bold" if b else None)


box(2, 70, 40, 9, "JACK BOARD: the sleeves; USB-C power in (VBUS, GND)", "#e3f2fd", 8.6, True)
box(2, 44, 40, 9, "JACK POWER BOARD (upper): eFuse, posts to the main board", "#f5f5f5", 8.6, True)
box(2, 18, 40, 9, "JACK LOWER BOARD: DAC, CV-out and CV-in op-amps", "#c8e6c9", 8.6, True)
for y0, y1, t in ((53.5, 69.5, "first stacks: 7 grounds\nthe whole module's current\n(about 1 A from a charger)"),
                  (27.5, 43.5, "second stacks: 3 grounds\nthe lower board's own current\n+ part of the main board's")):
    ax.plot([22, 22], [y0, y1], color="#8d6e63", lw=6, solid_capstyle="butt")
    ax.text(24, (y0 + y1) / 2, t, fontsize=8.2, color="#5d4037", va="center")
ax.annotate("", (12, 54), (12, 69), arrowprops=dict(arrowstyle="-|>", color="#c62828", lw=1.4))
ax.annotate("", (12, 28), (12, 43), arrowprops=dict(arrowstyle="-|>", color="#c62828", lw=1.4))
ax.text(1.5, 9, "Sleeves to the lower board's ground: likely 2-5 mV at full load [A: about 10-20 mΩ a contact],\n"
        "so 2-6 cents on every CV out and CV in, moving with the motor and the LEDs. Q41 does not see this one\n"
        "(it measures the lower board against the main board).", fontsize=9.2, color="#c62828", weight="bold")

x0 = 90
ax.text(x0, 84, "A (recommended): a sleeve-sense line", fontsize=11.5, weight="bold")
la = ["One ground pin in the first stacks and one in the second become SLEEVE_SENSE:",
      "the jacks' ground, carried down to the lower board with no current in it.",
      "",
      "There it shifts the op-amps' reference by just the right share of the",
      "difference, so the outputs and the inputs follow the sleeves, not the",
      "board: two small resistor networks (about 6 resistors, 0.1 %, and caps) in",
      "place of the plain VMID on the op-amps' + inputs, one for the CV outs, one",
      "for the CV ins [A, worked through: out 1/7 of the difference, in 0.10].",
      "",
      "Grounds: first stacks 7 → 6, second stacks 3 → 2. The three jack boards",
      "are re-routed (the lower one is being re-routed now for Q41 anyway).",
      "",
      "B: firmware only. It knows the loads (the motor current on MOT_SENSE, the",
      "LED and screen settings): one resistance measured once on the bench, and",
      "the CV outs and readings pre-corrected. No hardware; leaves maybe a fifth",
      "of it, and it is only as good as the load estimate [A]."]
for k, t in enumerate(la):
    ax.text(x0, 78 - k * 3.9, t, fontsize=9, weight="bold" if t.startswith("B:") else None)
fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "sleeve-sense-q42.png")
