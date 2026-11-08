"""Q35 picture (8 Nov 2026): the ring lights under the thrust race. The model has 24 emitters on the main board's back firing
forward through holes. A reverse-mount RGB part exists for that (SK6812MINI-E, recessed in a cut-out); the red VCSEL (JNJ 2835)
is an ordinary top-emitting part, so on the back it shines backward. Section views, schematic, mm. Pure matplotlib:
  python3 tools/studies/ring_lights_q35_sketch.py docs/img/ring-lights-q35.png"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch

fig, axs = plt.subplots(1, 3, figsize=(16, 7.4), dpi=125)
fig.subplots_adjust(left=0.02, right=0.98, top=0.8, bottom=0.2, wspace=0.08)
fig.text(0.02, 0.965, "Q35: the ring lights. Light has to get from the board's back, through the board, up into the clear race.",
         fontsize=13.5, weight="bold", va="top")
fig.text(0.02, 0.925, "Section through one emitter site (front of the module up). PCB 1.6 mm; the clear race sits flat on the "
         "front with the Ø2 balls; floor under a ball 1.0 mm.", fontsize=9.8, va="top")
PCB, RACE, BODY = "#2e7d32", "#e1f5fe", "#ffcc80"


def base(ax, title, verdict, col, hole_w):
    ax.set_xlim(-4.5, 4.5); ax.set_ylim(-4.3, 4.2); ax.set_aspect("equal"); ax.axis("off")
    # board with a hole of width hole_w
    ax.add_patch(Rectangle((-4.5, -1.6), 4.5 - hole_w / 2, 1.6, fc=PCB, ec="k", lw=0.6))
    ax.add_patch(Rectangle((hole_w / 2, -1.6), 4.5 - hole_w / 2, 1.6, fc=PCB, ec="k", lw=0.6))
    # race on the front
    ax.add_patch(Rectangle((-4.5, 0), 9, 2.0, fc=RACE, ec="#4fc3f7", lw=0.8))
    ax.add_patch(Circle((0, 2.0), 1.0, fc="#bdbdbd", ec="k", lw=0.6))
    ax.text(3.0, 1.4, "clear race", fontsize=8, color="#0277bd", ha="center")
    ax.text(3.0, -0.8, "PCB", fontsize=8, color="w", ha="center", weight="bold")
    ax.set_title(title, fontsize=10.5, weight="bold", loc="left")
    ax.text(-4.4, -4.2, verdict, fontsize=9.5, color=col, weight="bold")


# 1: the VCSEL as drawn
ax = axs[0]
base(ax, "As drawn: red VCSEL (JNJ 2835) on the back", "Shines backward, away from the knob.\nThe Ø0.62 hole above it stays dark.",
     "#c62828", 0.62)
ax.add_patch(Rectangle((-1.75, -2.4), 3.5, 0.8, fc=BODY, ec="k", lw=0.6))
ax.text(0, -2.0, "2835, lens on its far side", fontsize=7.6, ha="center", va="center")
ax.add_patch(FancyArrowPatch((0, -2.5), (0, -3.25), arrowstyle="-|>", mutation_scale=14, color="#c62828", lw=2))
ax.text(0.25, -0.8, "?", fontsize=14, color="#c62828")

# 2: SK6812MINI-E recessed
ax = axs[1]
base(ax, "RGB: SK6812MINI-E, recessed in a cut-out", "Shines forward into the race (made for this:\nkeyboards use it the same way).",
     "#2e7d32", 3.4)
ax.add_patch(Rectangle((-1.6, -2.49), 3.2, 1.78, fc=BODY, ec="k", lw=0.6))
ax.plot([-2.6, -1.6], [-1.6, -1.6], color="#9e9e9e", lw=3); ax.plot([1.6, 2.6], [-1.6, -1.6], color="#9e9e9e", lw=3)
ax.text(0, -1.9, "body 3.2 x 2.8 x 1.78\nleads halfway up", fontsize=7.4, ha="center", va="center")
ax.add_patch(FancyArrowPatch((0, -0.65), (0, 0.9), arrowstyle="-|>", mutation_scale=14, color="#2e7d32", lw=2))
ax.text(2.0, -2.5, "cut-out ~3.4 x 3.0", fontsize=7.4, color="#1b5e20")

# 3: VCSEL on the front
ax = axs[2]
base(ax, "To keep the red VCSELs: on the front, in the race", "Needs a 0.8 mm pocket in the race's 1.0 mm\nfloor: "
     "the race has to be redrawn thicker.", "#ef6c00", 0.0)
ax.add_patch(Rectangle((-1.75, 0), 3.5, 0.8, fc=BODY, ec="k", lw=0.6, zorder=3))
ax.add_patch(FancyArrowPatch((0, 0.85), (0, 1.0), arrowstyle="-|>", mutation_scale=12, color="#ef6c00", lw=2, zorder=4))
ax.text(0, 0.4, "2835 on the front", fontsize=7.4, ha="center", va="center", zorder=4)

fig.text(0.02, 0.105, "Found: JNJ's 5730 VCSEL sheet has the lens on the package top and the heat path through the pads [S]; the 2835 is the same "
         "kind of package [A].\nReverse-mount parts turn up only as ordinary LEDs (Broadcom, Dialight, Wurth, the SK6812MINI-E), "
         "no red VCSEL [S search].",
         fontsize=9.2)
fig.text(0.02, 0.06, "SK6812MINI-E: LCSC C5149201, US$0.045, 104,360 in stock; 5 V, 12 mA per colour, 800 kbit/s, one data line "
         "through the whole chain [S].", fontsize=9.2)
fig.text(0.02, 0.025, "A 3.4 x 3.0 cut-out at each RGB site leaves about 1.8 mm of board between neighbours on the ring (chord 5.18 mm "
         "at 15 degrees); traces cross the ring through those webs.", fontsize=9.2, color="#555")
fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "ring-lights-q35.png")
