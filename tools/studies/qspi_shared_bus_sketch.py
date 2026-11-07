"""Main-board pass, Q32 (second round, 7 Nov 2026): the workaround for the one fast quad port. The joystick screen and the flash
share the port's clock and four data lines and take turns; only the chip selects are separate. A: on the H7B0, a 74LVC1G19
(1-of-2 selector) steers the port's one chip select. B: on an STM32U5A5 (same LQFP100), the chip does it itself (Octo-SPI
multiplexed mode: two controllers, port 2's chip select is bonded out on LQFP100). Pure matplotlib:
  python3 tools/studies/qspi_shared_bus_sketch.py docs/img/qspi-shared-bus-q32.png"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

fig = plt.figure(figsize=(15, 9.4), dpi=130)
ax = fig.add_axes([0.02, 0.02, 0.96, 0.9]); ax.axis("off"); ax.set_xlim(0, 150); ax.set_ylim(0, 92)
fig.text(0.02, 0.975, "Q32, second round: the screen and the flash share the one fast port and take turns. Both get full quad speed.",
         fontsize=13, weight="bold", va="top")
fig.text(0.02, 0.945, "Clock and the four data lines go to both; only the chip select is separate, so one listens at a time. "
         "Pins: 74 used of 82, 8 spare (was 5). Pin maps solved from ST's pin data.", fontsize=9.5, va="top")


def box(x, y, w, h, text, fc, fs=9, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5", fc=fc, ec="#333", lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, weight="bold" if bold else None)


def line(pts, col, lw, ls="-"):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=col, lw=lw, ls=ls, solid_capstyle="round")


BUS, CS = "#2e7d32", "#c62828"
for x0, tag, chip, note, sel in (
        (0, "A (recommended): keep the H7B0, add a tiny selector chip", "STM32H7B0\nLQFP100\n(as now)",
         ["One Octo-SPI controller. Its one chip select goes through a 74LVC1G19",
          "(1-of-2 selector, 6 pins, about 1.6 x 2 mm, 1.8 ns); one spare pin picks",
          "screen or flash. The program: a small loader in the chip's 128 KB copies",
          "it from the flash into RAM at power-up (about 0.01 s now, at quad speed).",
          "Keeps the 280 MHz M7, 6 SPI ports, everything planned so far."], True),
        (76, "B: swap to an STM32U5A5 (same LQFP100 footprint)", "STM32U5A5\nLQFP100",
         ["Two Octo-SPI controllers share the lines in hardware (ST's multiplexed",
          "mode; LQFP100 bonds out port 2's chip select) [S pin data, ST forum].",
          "No selector chip. 4 MB program flash and 2.5 MB RAM on the chip, no loader.",
          "But: 160 MHz M33 (not 280 MHz M7), 3 SPI ports (exactly enough),",
          "new chip family for the firmware; price and stock to check [C]."], False)):
    ax.text(x0 + 1, 87, tag, fontsize=11.5, weight="bold")
    box(x0 + 2, 52, 16, 22, chip, "#ffcdd2", 10, True)
    box(x0 + 50, 70, 22, 8, "joystick screen\n(CO5300)", "#c8e6c9")
    box(x0 + 50, 52, 22, 8, "flash\n(animations + program)", "#c8e6c9")
    # shared bus: CLK + IO0-3
    line([(x0 + 18.5, 66), (x0 + 38, 66), (x0 + 38, 74), (x0 + 49.5, 74)], BUS, 4)
    line([(x0 + 38, 66), (x0 + 38, 56), (x0 + 49.5, 56)], BUS, 4)
    ax.text(x0 + 21, 67.2, "CLK + IO0-3 (5 lines)", fontsize=8.2, color=BUS)
    if sel:
        box(x0 + 26, 41, 10, 6, "74LVC1G19", "#fff9c4", 8)
        line([(x0 + 18.5, 58), (x0 + 22, 58), (x0 + 22, 45), (x0 + 25.5, 45)], CS, 1.4)
        line([(x0 + 18.5, 54), (x0 + 20.5, 54), (x0 + 20.5, 43), (x0 + 25.5, 43)], "#6a1b9a", 1.4)
        ax.text(x0 + 22.8, 49.5, "NCS", fontsize=7.8, color=CS)
        ax.text(x0 + 20, 47.5, "SEL (spare pin)", fontsize=7.8, color="#6a1b9a", ha="right")
        line([(x0 + 36.5, 45), (x0 + 44, 45), (x0 + 44, 72), (x0 + 49.5, 72)], CS, 1.4, "--")
        line([(x0 + 36.5, 43), (x0 + 46, 43), (x0 + 46, 54), (x0 + 49.5, 54)], CS, 1.4, "--")
        ax.text(x0 + 37, 39.5, "CS screen / CS flash", fontsize=7.8, color=CS)
    else:
        line([(x0 + 18.5, 60), (x0 + 44, 60), (x0 + 44, 72), (x0 + 49.5, 72)], CS, 1.4, "--")
        line([(x0 + 18.5, 54), (x0 + 49.5, 54)], CS, 1.4, "--")
        ax.text(x0 + 21, 61.2, "port 1 NCS", fontsize=7.8, color=CS); ax.text(x0 + 21, 51.8, "port 2 NCS", fontsize=7.8, color=CS)
    for i, ln in enumerate(note):
        ax.text(x0 + 2, 34 - i * 3.3, ln, fontsize=8.8)

# what it buys: one full frame of the joystick screen streamed from the flash, in turns on the shared lines
ax.text(1, 14.5, "Same speed either way. A full 456 x 280 frame streamed from the flash to the joystick screen, on the shared lines:",
        fontsize=9.5, weight="bold")
t0, sc = 3, 4.2   # ms -> axis units
ax.add_patch(Rectangle((t0, 6), 6.4 * sc, 5, fc="#bbdefb", ec="#333", lw=0.6))
ax.text(t0 + 3.2 * sc, 8.5, "read flash 6.4 ms\n(quad, 80 MHz)", ha="center", va="center", fontsize=7.8)
ax.add_patch(Rectangle((t0 + 6.4 * sc, 6), 10.2 * sc, 5, fc="#c8e6c9", ec="#333", lw=0.6))
ax.text(t0 + 11.5 * sc, 8.5, "write screen 10.2 ms (quad, 50 MHz)", ha="center", va="center", fontsize=7.8)
ax.text(t0 + 16.6 * sc + 2, 8.5, "= 16.6 ms: about 60 full frames a second from the flash\n"
        "(the first answer gave 24-39). Redraws from RAM: about 98 a second, as before.", va="center", fontsize=8.8)
ax.text(1, 1.5, "Considered and dropped: the LQFP144 (no room, see the first Q32 picture); the STM32H7A3 (same pins as the H7B0 with "
        "2 MB flash, but US\\$25.62 with 4 in stock at LCSC vs US\\$5.38 and 916 for the H7B0, 7 Nov).", fontsize=8.3, color="#555")
fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "qspi-shared-bus-q32.png")
