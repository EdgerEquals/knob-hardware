"""Q42 restated (8 Nov 2026, Ed 16:21: "it feels like a bit of a band-aid ... can we just remove or rearrange things so that we don't
have the problem?"): rearrange the jack unit's grounds instead of correcting for them. A quiet ground (the sleeves and the CV
circuits) on its own stack pins, the power ground (USB-C, eFuse, posts, boost) on the rest, joined at one point under the DAC.
Stack pins: jack-board make_board.py HDR_NETS and jack-power-board design.py STACK2 [S, ours]. Pure matplotlib:
  python3 tools/studies/quiet_ground_q42_sketch.py docs/img/quiet-ground-q42.png"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig = plt.figure(figsize=(16, 10), dpi=125)
ax = fig.add_axes([0.01, 0.01, 0.98, 0.9]); ax.axis("off"); ax.set_xlim(0, 160); ax.set_ylim(0, 96)
fig.text(0.015, 0.975, "Q42, rearranged: give the jacks and the CV circuits a ground of their own", fontsize=14, weight="bold", va="top")
fig.text(0.015, 0.945, "Nothing added. The ground pins in the two stacks are split into two groups, and the two grounds meet at exactly one "
         "point, under the DAC. No supply current can flow in the quiet one, so there is nothing to correct.", fontsize=10, va="top")
PWR, QUIET = "#c62828", "#2e7d32"


def board(x, y, w, h, title, items):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5", fc="#f7f7f7", ec="#333", lw=0.9))
    ax.text(x + 1, y + h - 1.6, title, fontsize=9.5, weight="bold", va="top")
    for (ix, iy, iw, ih, t, col) in items:
        ax.add_patch(FancyBboxPatch((x + ix, y + iy), iw, ih, boxstyle="round,pad=0.35", fc=col, ec="#555", lw=0.6))
        ax.text(x + ix + iw / 2, y + iy + ih / 2, t, ha="center", va="center", fontsize=7.8)


board(2, 66, 66, 16, "JACK BOARD", [(2, 2, 30, 7, "the 4 jacks' sleeves", "#c8e6c9"), (36, 2, 26, 7, "USB-C contacts (15 V, GND)", "#ffcdd2")])
board(2, 38, 66, 16, "JACK POWER BOARD (upper)", [(2, 2, 26, 7, "switches, MIDI, expander", "#eeeeee"),
                                                   (32, 2, 30, 7, "PD chip, eFuse, LDOs, 3.3 V; the posts", "#ffcdd2")])
board(2, 6, 66, 18, "JACK LOWER BOARD", [(2, 2, 28, 9, "DAC, CV-out + CV-in op-amps,\naudio stages", "#c8e6c9"),
                                          (36, 2, 26, 9, "boost, charge pump,\nclear OLED, link flex", "#ffcdd2")])
# stacks: quiet pins (green) on the left of each pair, power pins (red) on the right
for x, col, lab in ((14, QUIET, "2 quiet"), (50, PWR, "6 power")):
    ax.plot([x, x], [55, 65.5], color=col, lw=6, solid_capstyle="butt")
    ax.text(x + 1.5, 60, lab, fontsize=8.4, color=col, weight="bold", va="center")
for x, col, lab in ((14, QUIET, "2 quiet"), (50, PWR, "1 power\n(+ the flex's 7\nvia the main board)")):
    ax.plot([x, x], [25, 37.5], color=col, lw=6, solid_capstyle="butt")
    ax.text(x + 1.5, 31, lab, fontsize=8.4, color=col, weight="bold", va="center")
ax.text(70.5, 60, "first stacks: 8 grounds today\n→ 2 quiet + 6 power [Ed Q42 = A]\n(no current in the quiet: 2 for\nredundancy; 0.75 A a power pin at 3 A)", fontsize=8.4, va="center")
ax.text(70.5, 31, "second stacks: 3 grounds today\n→ 2 quiet + 1 power", fontsize=8.4, va="center")
ax.plot([32.6], [12.5], marker="*", ms=18, color="#f9a825", mec="#333")
ax.text(33.2, 20.2, "the one join (Q41's 0R, moved here)", fontsize=8, ha="center", color="#6d4c41")
ax.text(70.5, 72, "supply current: USB-C → the power pins\n→ eFuse → posts → main board", fontsize=8.4, color=PWR, va="center")

x0 = 98
ax.text(x0, 84, "What changes", fontsize=11.5, weight="bold")
lines = [("Quiet ground: the sleeves, the DAC, the op-amps and their", None),
         ("reference, on its own pins all the way. Only the CV outputs'", None),
         ("own tiny load currents flow in it: microvolts, not millivolts.", None),
         ("", None),
         ("Power ground: USB-C, the eFuse, the posts, the LDOs, the", None),
         ("boost and OLED, the link flex. All the supply current.", None),
         ("", None),
         ("One join, under the DAC, where the SPI comes in. Q41's 0R is", None),
         ("that join; flex pin 24 then reads the quiet ground directly.", None),
         ("", None),
         ("Parts: none added. The sleeve-sense line and its resistor", None),
         ("networks (the old A) and the firmware fix (the old B) are not", None),
         ("needed. Q41 stays: it handles the main board against the jack", None),
         ("unit, which this does not touch.", None),
         ("", None),
         ("Cost: the three jack boards re-laid out (two ground nets on the", "#c62828"),
         ("jack board, a quiet track through the upper board, the lower", "#c62828"),
         ("board's quiet parts on their own net). Margin on the power pins:", "#c62828"),
         ("6 pins, 0.75 A a pin at 3 A from a computer port, as VBUS.", "#c62828")]
for k, (t, c) in enumerate(lines):
    ax.text(x0, 78 - k * 3.75, t, fontsize=9, color=c or "#222")
fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "quiet-ground-q42.png")
