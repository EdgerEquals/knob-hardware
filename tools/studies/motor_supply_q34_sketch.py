"""Q34 picture (8 Nov 2026): which rail feeds the 1220's driver, now that it is the 6 V version [Ed 12:38]. Pure matplotlib:
  python3 tools/studies/motor_supply_q34_sketch.py docs/img/motor-supply-q34.png"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig = plt.figure(figsize=(15, 8), dpi=125)
ax = fig.add_axes([0.01, 0.01, 0.98, 0.88]); ax.axis("off"); ax.set_xlim(0, 150); ax.set_ylim(0, 80)
fig.text(0.015, 0.975, "Q34: the 1220 is the 6 V version. Which rail feeds its driver?", fontsize=14, weight="bold", va="top")
fig.text(0.015, 0.94, "Both use one small H-bridge chip under the H743's PWM. The difference is how much voltage can ever reach "
         "a 6 V motor.", fontsize=10, va="top")


def box(x, y, w, h, text, fc, fs=9, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.45", fc=fc, ec="#333", lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, weight="bold" if bold else None)


def arrow(p0, p1, text, col):
    ax.annotate("", p1, p0, arrowprops=dict(arrowstyle="-|>", lw=2, color=col))
    ax.text((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + 2, text, ha="center", fontsize=8.5, color=col)


for x0, tag, rail, rail_c, notes in (
        (0, "A (recommended): from the 5 V rail", "5 V rail\n(board L, already planned)", "#2e7d32",
         ["The motor can never see more than 5 V, even if the firmware goes wrong.",
          "No extra converter. A small low-voltage H-bridge (11 V class).",
          "About 5/6 of the listed speed and stall torque (your bench numbers at 5 V",
          "will say what that is). Lower supply = less PWM ripple and heat in a",
          "coreless motor [S maxon]; PWM at 50-100 kHz.",
          "Its current is added to the 5 V converter's load (decision 2)."]),
        (76, "B: from 15 V, PWM capped at 40 % in firmware", "15 V (VSYS)", "#c62828",
         ["Up to 6 V average, and a short boost above it if wanted.",
          "A firmware fault or a stuck PWM puts 15 V on a 6 V motor.",
          "2.5x the supply = much more ripple current and heat in a coreless",
          "motor at the same PWM frequency [S maxon].",
          "Needs a driver rated above 15 V (bigger part).",
          "Keeps the motor's current off the 5 V converter."])):
    ax.text(x0 + 1, 74, tag, fontsize=12, weight="bold")
    box(x0 + 2, 52, 18, 12, rail, "#e3f2fd", 9)
    box(x0 + 28, 52, 18, 12, "H-bridge\n(IN1, IN2, nSLEEP\nfrom the H743)", "#fff9c4", 9)
    box(x0 + 54, 52, 16, 12, "1220\n6 V coreless", "#ffcdd2", 9.5, True)
    arrow((x0 + 20.5, 58), (x0 + 27.5, 58), "", rail_c)
    arrow((x0 + 46.5, 58), (x0 + 53.5, 58), "5 V max" if x0 == 0 else "up to 15 V", rail_c)
    for i, ln in enumerate(notes):
        ax.text(x0 + 2, 44 - i * 4.4, ln, fontsize=9.2)
ax.text(1, 2, "Then, one at a time: the bench numbers at the chosen voltage (no-load and stall current) size the driver and its "
        "current limit.", fontsize=9, color="#555")
fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "motor-supply-q34.png")
