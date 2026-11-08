"""Q41 picture (8 Nov 2026, noise sweep): the ground difference between the jack lower board (where the CV ins are made) and the
main board (where they are read), and a sense line on the link flex. Flex pins: step-2 circuit [S]; resistances [A]. Pure matplotlib:
  python3 tools/studies/ground_sense_q41_sketch.py docs/img/ground-sense-q41.png"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

CENT_UV = 1 / 1200 * 0.113 * 1e6          # 1 cent at the jack, at the ADC, after Q40 (x 0.113)
fig = plt.figure(figsize=(16, 9.4), dpi=125)
ax = fig.add_axes([0.01, 0.01, 0.98, 0.9]); ax.axis("off"); ax.set_xlim(0, 160); ax.set_ylim(0, 92)
fig.text(0.015, 0.975, "Q41: the ground the CV ins are made on is not the ground they are read on", fontsize=14, weight="bold", va="top")
fig.text(0.015, 0.945, f"After Q40, 1 cent at a CV jack is {CENT_UV:.0f} µV at the ADC, so 1 mV between the two grounds reads as about "
         f"{1000 / CENT_UV:.0f} cents.", fontsize=10, va="top")


def box(x, y, w, h, t, fc, fs=8.6, b=False, ec="#333"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.45", fc=fc, ec=ec, lw=0.9))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, weight="bold" if b else None)


def arrow(x0, y0, x1, y1, t="", col="#555", lw=1.4, dy=1.6, ls="-"):
    ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", color=col, lw=lw, linestyle=ls))
    if t:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + dy, t, ha="center", fontsize=8, color=col)


# boards
box(2, 66, 64, 12, "", "#f5f5f5")
ax.text(4, 75.5, "MAIN BOARD", fontsize=9.5, weight="bold")
box(30, 68, 16, 7, "ADC (H743)\nreads against VSSA", "#fff9c4", 8)
box(49, 68, 15, 7, "motor, ring LEDs,\nscreen: up to 0.9 A\nfrom 15 V", "#ffcdd2", 7.4)
box(2, 18, 30, 12, "", "#f5f5f5")
ax.text(4, 27.5, "JACK POWER BOARD (upper)", fontsize=9, weight="bold")
box(4, 19.5, 26, 5, "USB-C power in, eFuse", "#e3f2fd", 8)
box(40, 4, 26, 12, "", "#f5f5f5")
ax.text(42, 13.5, "JACK LOWER BOARD", fontsize=9, weight="bold")
box(42, 5.5, 22, 5.5, "CV-in op-amps\nmake 0.23-2.95 V on its ground", "#c8e6c9", 7.6)
# paths
ax.plot([10, 10], [30.5, 65.5], color="#8d6e63", lw=5, solid_capstyle="butt")
ax.text(11.5, 48, "GND post\n(brass Ø1),\na few mΩ [A]", fontsize=8, color="#5d4037")
ax.plot([22, 22], [30.5, 65.5], color="#8d6e63", lw=5, solid_capstyle="butt")
ax.text(23.5, 40, "VSYS post", fontsize=8, color="#5d4037")
ax.plot([26, 44], [18, 16.5], color="#8d6e63", lw=3)
ax.text(28, 13.6, "2x6 stacks", fontsize=8, color="#5d4037")
ax.plot([56, 56], [16.5, 65.5], color="#7986cb", lw=7, solid_capstyle="butt")
ax.text(58, 36, "link flex: 8 grounds,\nCV_IN1-3, AIN, ...", fontsize=8, color="#3949ab")
arrow(52, 65, 52, 18, col="#c62828")
ax.text(51, 44, "return current\nsplits: some\ndown the flex", ha="right", fontsize=8, color="#c62828")
arrow(8, 65, 8, 31, col="#c62828")
ax.text(7, 56, "most\nhere", ha="right", fontsize=8, color="#c62828")
ax.text(66, 52, "ΔV between the boards' grounds =\nreturn current x the flex's share:\nlikely 1-3 mV [A] = 10-30 cents,\nmoving with the motor and the LEDs", fontsize=9, color="#c62828", weight="bold")

# A
x0 = 96
ax.text(x0, 84, "A (recommended): a ground-sense line on flex pin 24", fontsize=11.5, weight="bold")
la = ["Pin 24 stops being a ground and carries the lower board's analog ground,",
      "taken at the CV-in op-amps, to an ADC pin on the main board. It carries no",
      "current, so it arrives at exactly that ground's voltage.",
      "It sits between grounds 23 and 25, so it stays shielded. Grounds 8 → 7.",
      "",
      "The H743 reads each CV in on one ADC and the sense line on the other at",
      "the same instant (its two ADCs can sample together) and subtracts: the",
      "difference, slow or fast, cancels [A]. The audio in gets the same.",
      "",
      "Parts: none new. 100 Ω + 1 nF at the ADC pin like the others, and 1 MΩ",
      "to ground so it reads 0 with the flex out [A]. One spare ADC pin.",
      "",
      "B: leave the 8 grounds and measure the difference on the first boards.",
      "If it is there, the fix then needs a new flex pin-out on both boards."]
for k, t in enumerate(la):
    ax.text(x0, 78 - k * 3.9, t, fontsize=9, weight="bold" if t.startswith("B:") else None)
fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "ground-sense-q41.png")
