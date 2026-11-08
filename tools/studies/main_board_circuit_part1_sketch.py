"""Main-board circuit, part 1 picture (7-8 Nov 2026): the groups written without a decision (green) and the ones still to come
(amber), around the STM32H743VIT6, with what crosses each connector. Pure matplotlib:
  python3 tools/studies/main_board_circuit_part1_sketch.py docs/img/main-board-circuit-part1.png"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig = plt.figure(figsize=(16, 10), dpi=125)
ax = fig.add_axes([0.01, 0.01, 0.98, 0.9]); ax.axis("off"); ax.set_xlim(0, 160); ax.set_ylim(0, 100)
fig.text(0.015, 0.975, "Main board circuit, part 1: what is written (green) and what still needs a decision (amber)",
         fontsize=14, weight="bold", va="top")
fig.text(0.015, 0.945, "STM32H743VIT6 (Q33 = A): 64 nets on 82 I/O pins, 18 spare. Values from ST's AN4938, ST's pin data and "
         "our v0.11 board; details in docs/main-board-circuit-2026-11-07.md.", fontsize=10, va="top")
DONE, TODO, MCU, OFF = "#c8e6c9", "#ffe0b2", "#ffcdd2", "#eeeeee"


def box(x, y, w, h, text, fc, fs=8.4, bold=False, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.45", fc=fc, ec="#333", lw=0.8, ls=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, weight="bold" if bold else None)


def wire(p0, p1, text="", col="#555", lw=1.2, ha="center", dy=1.4, z=2):
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=col, lw=lw, zorder=z)
    if text:
        ax.text((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + dy, text, fontsize=7.6, color=col, ha=ha, va="center")


box(62, 40, 36, 20, "STM32H743VIT6\nLQFP100, 480 MHz\n2 MB flash, 1 MB RAM\n(LCSC C114409)", MCU, 10, True)

# left column: core
box(3, 76, 36, 13, "Supply pins [AN4938]\n5 x 100 nF + 10 µF on VDD\nVCAP 2 x 2.2 µF, tied together\n"
    "VDDA: ferrite + 1 µF + 100 nF; VREF+ 47 Ω", DONE)
box(3, 60, 36, 11, "Reset, boot, battery pin\nNRST 100 nF; BOOT0 10 kΩ down\n+ a test pad; VBAT to VDD", DONE)
box(3, 45, 36, 10, "Crystal 25 MHz, 12 pF (C9006)\n2 x 15 pF; check the frequency\non the first boards", DONE)
box(3, 30, 36, 10, "Tag-Connect TC2030 pads\n(nothing fitted): 3V3, SWDIO,\nnRESET, SWCLK, GND, SWO", DONE)
for y in (82, 65, 50, 35):
    wire((39.5, y), (61.5, 50))

# top: joystick path
box(66, 86, 30, 9, "Board R: 13 top pins\nCLK + CS + IO0-3, RST, TE, PWR_EN\nwith 4 grounds between", DONE, 7.8)
box(104, 86, 26, 9, "top board → jumper\n→ joystick screen", OFF)
box(132, 86, 26, 9, "Board L top pins:\n3.3 V, the switch ladder,\ngrounds", DONE, 7.8)
wire((80, 60.5), (80, 85.5), "QUADSPI, 22 Ω in series", "#c62828", 2.0, ha="left", dy=0)
wire((96.5, 90.5), (103.5, 90.5))
wire((130.5, 90.5), (131.5, 90.5))
box(104, 74, 26, 7, "Halls: 4 x TMAG5253 +\nTMAG5273 (v0.11 parts)", DONE, 7.8)
box(132, 74, 26, 7, "Encoder EE-SX1321\n220 Ω, 2 x 10 kΩ, TIM3", DONE, 7.8)
wire((95, 60.5), (117, 73.5))
wire((97, 60.5), (145, 73.5))

# right: links out
box(112, 49, 46, 11, "Link flex (25 pins) → jack unit\nSPI3 33 Ω; I2C (pull-ups already on the jack board);\n"
    "USB FS straight (ESD at the USB-C); CV / audio in\n100 Ω + 1 nF at the pin; audio out from DAC1", DONE, 7.8)
box(112, 36, 46, 8, "CAN: TX, RX, STBY to board R\n(transceiver and where the bus leaves: with board R)", DONE, 7.8)
box(112, 24, 46, 8, "Cover board, later: pads only\nTX, RX, EN, 3.3 V, 5 V, GND", DONE, 7.8, ls="--")
for y in (54.5, 40, 28):
    wire((98.5, 50), (111.5, y))

# bottom: the decisions still to come, in order
ax.text(3, 21.5, "Still to come, one decision at a time:", fontsize=10.5, weight="bold")
todo = [("1. The 1220 driver and its supply", "needs your bench numbers:\nvoltage version, no-load and\nstall current"),
        ("2. Power on board L", "15 V → 5 V and 3.3 V,\nsized with the motor's share"),
        ("3. RGB part, VCSEL driver", "the rings on the board's back"),
        ("4. The rod link (dial)", "main-board end of the one-wire\npower + data, with the dial board"),
        ("5. Layer count", "after a first placement")]
for i, (t, d) in enumerate(todo):
    x = 3 + i * 31.2
    box(x, 3, 28.5, 14, t + "\n\n" + d, TODO, 7.9)
    wire((x + 14, 17.5), (80, 39.5), col="#e0a060", lw=0.8, z=0.5)   # behind the boxes
fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "main-board-circuit-part1.png")
