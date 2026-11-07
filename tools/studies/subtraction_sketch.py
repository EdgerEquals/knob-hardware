"""Main-board pass, subtraction (7 Nov 2026, Ed 19:29: "we keep adding things; maybe we can remove things and get it done").
What comes out of the first build, and what is left. Numbers: pin maps from tools/main_board_pinmap.py (ST pin data), prices
LCSC 7 Nov. Pure matplotlib:
  python3 tools/studies/subtraction_sketch.py docs/img/subtraction-q33.png"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig = plt.figure(figsize=(16, 9.6), dpi=125)
ax = fig.add_axes([0.01, 0.01, 0.98, 0.88]); ax.axis("off"); ax.set_xlim(0, 160); ax.set_ylim(0, 96)
fig.text(0.015, 0.975, "Take things out instead: the back screens wait for their own board, and a bigger-memory chip in the same "
         "footprint removes the flash", fontsize=13, weight="bold", va="top")
fig.text(0.015, 0.945, "Nothing is added. The geometry stays: the back screens stay in the model as 'later', exactly as planned on "
         "3 Nov (\"aesthetics, can come later\").", fontsize=10, va="top")


def box(x, y, w, h, text, fc, fs=8.8, bold=False, ls="-", ec="#333"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.45", fc=fc, ec=ec, lw=0.9, ls=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, weight="bold" if bold else None)


def link(p0, p1, text, col, lw, ls="-", ha="left", dx=0.8, dy=0.0):
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=col, lw=lw, ls=ls)
    ax.text((p0[0] + p1[0]) / 2 + dx, (p0[1] + p1[1]) / 2 + dy, text, fontsize=7.8, color=col, ha=ha, va="center")


# left: what comes out
ax.text(1, 89, "OUT of the first build", fontsize=11.5, weight="bold", color="#b71c1c")
outs = [("Back screens x2 (2.4\" AMOLED)", "US$41 each retail [S]; their flex pin-out still unknown,", "DisplayModule silent since 2 Nov"),
        ("Their power chip(s)", "ELVDD / ELVSS for each panel", ""),
        ("Their two connectors on the main board", "top back, and the bottom strip that", "only takes one connector"),
        ("The lower screen's ~7 lines past window D", "through the tightest channel on the board", "(2 x 2.3 mm strips beside D)"),
        ("12 main-chip pins", "two SPI groups, CS, D/C, TE, reset, power", ""),
        ("Animation flash + selector chip + loader", "the new chip holds the program and", "the joystick screen's pictures itself"),
        ("Two extra screen chips (last round's A)", "never added", "")]
y = 84
for t, a, b in outs:
    ax.text(2, y, "x  " + t, fontsize=9.2, weight="bold", color="#b71c1c")
    ax.text(5.2, y - 2.2, a, fontsize=8.2, color="#444")
    if b:
        ax.text(5.2, y - 4.1, b, fontsize=8.2, color="#444")
    y -= 7.4 if b else 5.6

# middle: what is left
X = 58
ax.text(X, 89, "LEFT: one main chip, one fast port, one screen on it", fontsize=11.5, weight="bold")
box(X + 22, 52, 32, 13, "MAIN CHIP STM32H743VIT6\nsame LQFP100 land as the H7B0\n2 MB program flash, 1 MB RAM, 480 MHz",
    "#ffcdd2", 8.6, True)
box(X + 40, 76, 22, 8, "joystick screen 1.64\"\n(on the one quad port)", "#c8e6c9")
box(X + 2, 76, 22, 8, "dial screen + its own chip\n(decided 3 Nov)", "#bbdefb")
box(X + 2, 34, 24, 8, "jack unit: clear OLED,\nCV DAC (link flex)", "#eeeeee")
box(X + 30, 34, 24, 8, "motor, encoder, Halls,\nRGB + VCSEL rings, CAN", "#eeeeee")
box(X + 64, 52, 22, 13, "LATER: cover board\nback screens x2\n+ its own chip", "#fafafa", 8.4, ls="--", ec="#888")
link((X + 46, 65.5), (X + 50, 75.5), "QSPI 50 MHz\n(slower still works:\n25 MHz = 49 frames/s)", "#c62828", 2.2)
link((X + 30, 65.5), (X + 14, 75.5), "rod: one wire,\npower + commands", "#1565c0", 1.4, ha="right", dx=-0.8)
link((X + 30, 51.5), (X + 14, 42.5), "", "#555", 1.2)
link((X + 42, 51.5), (X + 42, 42.5), "", "#555", 1.2)
link((X + 54.5, 58.5), (X + 63.5, 58.5), "3 pins kept\n(UART + enable)", "#888", 1.2, ls="--", dx=-4.5, dy=4.2)

# bottom: the numbers
rows = [("", "Q32 shared port (round 2 A)", "Local drawing (Q33 A)", "Subtract (new)"),
        ("Main chip", "H7B0, 128 KB + loader", "H7B0", "H743VIT6, 2 MB, 1 MB RAM"),
        ("Main-chip pins used / spare", "74 / 8", "60 / 22", "64 / 18"),
        ("Chips added to the main board", "flash + selector", "2 x ESP32-S3", "none (flash removed)"),
        ("Back screens on the first build", "yes, ~12 frames/s", "yes, ~46 if QSPI tail", "no: later, own board"),
        ("Main chip price, LCSC 7 Nov [S]", "US$5.38 + flash + selector", "US$5.38 + 2 x ESP32-S3", "US$7.86 (5,931 in stock)")]
y = 25
for i, r in enumerate(rows):
    for j, (x, txt) in enumerate(zip((1, 40, 80, 118), r)):
        ax.text(x, y, txt, fontsize=8.8, weight="bold" if (i == 0 or j == 0 or j == 3) else None,
                color="#0d47a1" if j == 3 else "#222")
    y -= 2.6
ax.text(1, 6.5, "Said plainly: the joystick screen's fast lines still pass board R, the pins and sockets and the jumper (ground pins between "
        "them; it slows down rather than fails). The 2 MB holds the program and drawn pictures (gauges, text, icons), not long "
        "full-screen video.", fontsize=8.4, color="#555", wrap=True)
ax.text(1, 3.6, "This revises Q31 (back screens on the first board) back to the 3 Nov plan. The H743's other pins (power, VCAP, BOOT) "
        "differ from the H7B0's; no schematic is drawn yet, so that costs nothing now.", fontsize=8.4, color="#555")
fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "subtraction-q33.png")
