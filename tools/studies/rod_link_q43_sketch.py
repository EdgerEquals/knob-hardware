"""Q43 picture (8 Nov 2026): the rod link, the dial's power and data on one wire (the M1.6 rod; the brass tube is the return).
Two ways to put data on the 5 V feed. Figures [A] unless marked; MAX22088 [S Analog Devices]. Pure matplotlib:
  python3 tools/studies/rod_link_q43_sketch.py docs/img/rod-link-q43.png"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig = plt.figure(figsize=(16, 10.4), dpi=125)
ax = fig.add_axes([0.01, 0.01, 0.98, 0.9]); ax.axis("off"); ax.set_xlim(0, 160); ax.set_ylim(0, 100)
fig.text(0.015, 0.975, "Q43: the rod link: the dial's power and data on one wire", fontsize=14, weight="bold", va="top")
fig.text(0.015, 0.945, "The rod up the middle carries 5 V to the dial (its graphics chip, screen, LEDs, mic: about 0.12 A, 0.6 W) and the data "
         "both ways; the brass tube is the return. The question is how the data rides on the power.", fontsize=10, va="top")


def box(x, y, w, h, t, fc, fs=8.4, b=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4", fc=fc, ec="#333", lw=0.8))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, weight="bold" if b else None)


def line(x0, y0, x1, y1, col="#555", lw=1.4, arrow=False):
    if arrow:
        ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", color=col, lw=lw))
    else:
        ax.plot([x0, x1], [y0, y1], color=col, lw=lw)


for x0, title, rec in ((1, "A (recommended): data as a high-frequency signal on top of the DC", True),
                       (82, "B: data as the supply level itself", False)):
    ax.text(x0, 86, title, fontsize=11.5, weight="bold")
    box(x0 + 1, 60, 16, 16, "MAIN BOARD\n5 V (ring /\ndial branch)", "#e3f2fd", 8.2, True)
    box(x0 + 60, 60, 16, 16, "DIAL\n(knob top)", "#e3f2fd", 8.2, True)
    line(x0 + 17.5, 68, x0 + 59.5, 68, "#6d4c41", 4)
    ax.text(x0 + 38.5, 69.8, "rod (one wire)", ha="center", fontsize=8, color="#6d4c41")
    line(x0 + 17.5, 63, x0 + 59.5, 63, "#9e9e9e", 4)
    ax.text(x0 + 38.5, 59.5, "brass tube (return)", ha="center", fontsize=8, color="#757575")
    if rec:
        box(x0 + 20, 72.5, 9, 6, "choke", "#fff9c4", 7.6)
        box(x0 + 48, 72.5, 9, 6, "choke", "#fff9c4", 7.6)
        box(x0 + 20, 78.8, 9, 5, "cap + rx", "#c8e6c9", 7.4)
        box(x0 + 48, 78.8, 9, 5, "cap + rx", "#c8e6c9", 7.4)
        ax.text(x0 + 38.5, 75.5, "steady DC through the chokes;\nthe data passes the caps", ha="center", fontsize=7.6, color="#2e7d32")
        notes = ["Power: plain DC through a small choke at each end; the dial draws",
                 "a steady current, so nothing on the 5 V follows the data.",
                 "Data: a DC-free code (Manchester) at about 2 Mbit/s, through a small",
                 "capacitor at each end; its energy sits at 1-4 MHz, far above audio.",
                 "Each end: a choke, a capacitor, a small comparator, a resistor.",
                 "The dial chip (ESP32-S3) codes it with its pulse peripheral; the",
                 "main chip with a timer + DMA. Two main-chip pins (spare today).",
                 "Fast enough for the dial's commands, the mic's sound back (about",
                 "0.8 Mbit/s raw) and a firmware update in about a minute.",
                 "Tight, said plainly: the dial-end choke must carry 0.2 A in about",
                 "2 x 2 mm [C: part to pick and check its rating]."]
    else:
        box(x0 + 20, 72.5, 10, 6, "level\nswitch", "#fff9c4", 7.4)
        box(x0 + 47, 72.5, 10, 6, "diode +\nhold cap", "#fff9c4", 7.4)
        box(x0 + 20, 78.8, 10, 5, "current rx", "#c8e6c9", 7.4)
        box(x0 + 47, 78.8, 10, 5, "level rx +\nload sw", "#c8e6c9", 7.2)
        ax.text(x0 + 38.5, 75.5, "5.0 / 4.4 V to send down;\na 20 mA load blip to send up", ha="center", fontsize=7.6, color="#c62828")
        notes = ["Down: the main end switches the rod between 5.0 and 4.4 V; the dial",
                 "reads the level. Up: the dial switches a small extra load; the",
                 "main end reads the current. A plain UART, up to about 1 Mbit/s.",
                 "Fewest parts, no chokes.",
                 "Noise: the supply itself carries the data, so the dial's hold-up",
                 "capacitor recharges in step with it. Bursts (a screen update 60",
                 "times a second) put 60 Hz and its harmonics on the 5 V and its",
                 "ground: audible unless the link sends filler all the time.",
                 "",
                 "Not offered: a ready-made power+data chip (MAX22088 class):",
                 "200 kbit/s, 4 x 4 mm at both ends [S]: too slow, too big."]
    for k, t in enumerate(notes):
        ax.text(x0 + 1, 52 - k * 4.1, t, fontsize=8.9)
fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "rod-link-q43.png")
