"""Main-board pass, fresh look (7 Nov 2026, Ed: "are we adding a band-aid? zoom out"). Who draws each screen, and what crosses
each connector. Left: central drawing (the main chip draws the joystick and back screens; Q32 second round A). Right: local
drawing (each screen place has its own small graphics chip that draws from its own memory; the main chip sends short commands,
the way the dial already works through the rod). Numbers from docs/main-board-signals-2026-11-07.md and the pin-map solver.
  python3 tools/studies/architecture_fresh_look.py docs/img/architecture-fresh-look.png"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig = plt.figure(figsize=(16, 11), dpi=125)
ax = fig.add_axes([0.01, 0.01, 0.98, 0.9]); ax.axis("off"); ax.set_xlim(0, 160); ax.set_ylim(0, 110)
fig.text(0.015, 0.975, "Fresh look: who draws each screen, and what has to cross each connector", fontsize=14, weight="bold", va="top")
fig.text(0.015, 0.945, "Five screens in four places. The dial already draws its own pictures (its own chip, fed through the rod). "
         "The question is whether the joystick and back screens should too.", fontsize=10, va="top")

C_MAIN, C_NODE, C_SCR, C_JACK = "#ffcdd2", "#bbdefb", "#c8e6c9", "#eeeeee"


def box(x, y, w, h, text, fc, fs=8.6, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.45", fc=fc, ec="#333", lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, weight="bold" if bold else None)


def link(p0, p1, text, col, lw, side=1, dx=0.0):
    ax.annotate("", p1, p0, arrowprops=dict(arrowstyle="-", lw=lw, color=col))
    mx, my = (p0[0] + p1[0]) / 2 + dx, (p0[1] + p1[1]) / 2
    ax.text(mx + 0.8 * side, my, text, fontsize=7.6, color=col, ha="left" if side > 0 else "right", va="center")


FAST, THIN = "#c62828", "#1565c0"
for x0, title, central in ((0, "NOW: central drawing (Q32 second round A)", True),
                           (81, "PROPOSED: local drawing (\"one brain, local painters\")", False)):
    ax.text(x0 + 1, 103, title, fontsize=11.5, weight="bold")
    # places
    box(x0 + 3, 84, 22, 9, "dial screen 1.32\" round\n466 x 466", C_SCR)
    box(x0 + 3, 72, 22, 7, "dial chip ESP32-S3\n(in the cartridge)", C_NODE)
    box(x0 + 50, 84, 24, 9, "joystick screen 1.64\"\n456 x 280", C_SCR)
    if central:
        box(x0 + 50, 72, 24, 7, "top board\n(switch, sockets)", C_JACK)
    else:
        box(x0 + 50, 72, 24, 7, "joystick chip ESP32-S3\n(top board or board R)", C_NODE)
    box(x0 + 22, 44, 30, 14, "MAIN CHIP H7B0\n" + ("draws joystick + back screens,\nmotor, sensors, audio, CV, MIDI, USB"
                                                    if central else "motor, sensors, audio, CV,\nMIDI, USB, LEDs; sends commands"),
        C_MAIN, 8.4, True)
    if central:
        box(x0 + 3, 44, 14, 8, "flash\n(shared port)", C_JACK)
    box(x0 + 58, 32, 18, 9, "back screens x2\n2.4\" 450 x 600", C_SCR)
    if not central:
        box(x0 + 58, 46, 18, 7, "back chip ESP32-S3\n(board back)", C_NODE)
    box(x0 + 3, 22, 28, 9, "jack unit: clear OLED,\nCV DAC, jacks (link flex)", C_JACK)
    # links
    link((x0 + 14, 79.5), (x0 + 14, 83.5), "QSPI, short", FAST, 2.0)
    link((x0 + 14, 71.5), (x0 + 30, 58.5), "rod: one wire, power + data\n(commands, a few Mbit/s)", THIN, 1.4, side=-1, dx=-5)
    link((x0 + 62, 79.5), (x0 + 62, 83.5), "jumper", FAST if central else FAST, 2.0)
    if central:
        link((x0 + 40, 58.5), (x0 + 58, 71.5), "QSPI 50 MHz, 9 lines\nthrough board R, pins and\nsockets, top board, jumper",
             FAST, 2.4, side=1, dx=3)
        link((x0 + 17.5, 48), (x0 + 21.5, 48), "", FAST, 2.4)
        link((x0 + 52.5, 47), (x0 + 60, 41.5), "1-bit SPI x2\n(about 12 frames/s each)", FAST, 2.0, side=1, dx=4)
    else:
        link((x0 + 40, 58.5), (x0 + 58, 71.5), "UART, 2 lines\n(commands)", THIN, 1.4, side=1, dx=3)
        link((x0 + 52.5, 50), (x0 + 57.5, 50), "", THIN, 1.4)
        ax.text(x0 + 53, 52.2, "UART", fontsize=7.6, color=THIN)
        link((x0 + 67, 45.5), (x0 + 67, 41.5), "QSPI each, short\n(about 46 frames/s each\nif the tail has QSPI [C])", FAST, 2.0, side=-1)
    link((x0 + 30, 43.5), (x0 + 20, 31.5), "SPI (OLED, DAC), I2C,\nUSB, MIDI, CV, audio", "#555", 1.2, side=1, dx=2)

# scorecard
rows = [("", "NOW (central)", "PROPOSED (local)"),
        ("Main chip pins", "74 of 82 used, 8 spare", "60 of 82 used, 22 spare"),
        ("Joystick link through the connectors", "9 lines of 50 MHz QSPI through 3 joints", "2 slow lines (+ power), QSPI stays on its own board"),
        ("Back screens, full frames / s", "about 12 each (1-bit SPI)", "about 46 each if their tail has QSPI [C]; else 12"),
        ("Main chip's program", "graphics + real time in 128 KB + loader", "real time only: graphics live in the screen chips"),
        ("Animations", "one flash, shared with the joystick screen", "8 MB flash + 8 MB RAM in each screen chip"),
        ("Extra parts", "74LVC1G19 selector", "2 more ESP32-S3-PICO-1 (7 x 7 mm), a few capacitors"),
        ("Extra power", "-", "about 0.2-0.3 W per screen chip [A]"),
        ("Firmware", "one program", "main program + one screen program for all 3 screen chips"),
        ("Dev kits to start the screen code now", "-", "Waveshare's 1.64\" and 1.32\" boards: ESP32-S3 on these panels [S]")]
y = 18.5
for i, (a, b, c) in enumerate(rows):
    w = "bold" if i == 0 else None
    ax.text(1, y, a, fontsize=8.6, weight="bold" if i else None)
    ax.text(48, y, b, fontsize=8.6, weight=w, color="#b71c1c" if i == 0 else "#222")
    ax.text(100, y, c, fontsize=8.6, weight=w, color="#0d47a1" if i == 0 else "#222")
    y -= 1.95
fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "architecture-fresh-look.png")
