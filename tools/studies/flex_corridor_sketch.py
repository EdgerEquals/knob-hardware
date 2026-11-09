"""The link flex's way up the main board, looked at again (9 Nov 2026, Ed: "is there something we can do about this?").
Board from the room map (v0.53), copper 0.25 off every edge; the corridor beside windows D and E, the pinch at the LEDs, and how
many tracks fit (0.1 track / 0.1 gap is PCBWay's 4-6 layer standard, here 0.127 / 0.1 as the board's rules).
  python3 tools/studies/flex_corridor_sketch.py <mb_room.pkl> <out.png>"""
import sys, pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, box

R = pickle.load(open(sys.argv[1], "rb"))
b = R["board"]
fig = plt.figure(figsize=(14, 11), dpi=130)
ax = fig.add_axes([0.0, 0.03, 0.52, 0.88])
ax.add_patch(plt.Polygon(list(b.exterior.coords), fc="#f1f8e9", ec="#33691e", lw=0.8))
for i in b.interiors:
    ax.add_patch(plt.Polygon(list(i.coords), fc="white", ec="#33691e", lw=0.5))
cor = b.buffer(-0.25).intersection(box(19.0, -47.5, 22.2, 26.0))
for p in ([cor] if cor.geom_type == "Polygon" else list(cor.geoms)):
    ax.add_patch(plt.Polygon(list(p.exterior.coords), fc="#ffcc80", ec="none", alpha=0.9))
# the flex pads, and the bundle: up beside D and C, in through the gap between the LEDs at 4 o'clock, across inside the ring,
# out between the LEDs at 2 o'clock, up beside B to the chip
ax.add_patch(plt.Rectangle((10.35, -50.4), 7.5, 1.2, fc="#5d4037"))
path = [(14.1, -49.2), (14.1, -48.2), (20.7, -47.0), (20.7, -13.0), (17.2, -9.9), (14.0, -5.0), (14.0, 5.0), (17.2, 9.9), (20.7, 13.0), (20.7, 27.0), (8.0, 31.0)]
ax.plot(*zip(*path), color="#6a1b9a", lw=4, alpha=0.65, solid_capstyle="round")
for (x, y, t) in ((21.5, -36.0, "2.3 mm\nbeside D"), (21.5, -17.0, "2.3 mm\nbeside C"), (22.6, -5.0, "0.6 mm\noutside the\nLEDs"),
                  (21.5, 19.0, "2.3 mm\nbeside B")):
    ax.annotate(t, (x, y), (25.0, y), fontsize=9, va="center", arrowprops=dict(arrowstyle="-", lw=0.6))
ax.text(14.1, -52.2, "link flex pads", ha="center", fontsize=9)
ax.text(11.0, 0.0, "inside the ring:\ninner layers free", ha="center", fontsize=8.5, color="#4a148c")
b_ = b.bounds
ax.set_xlim(b_[0] - 1, b_[2] + 9); ax.set_ylim(b_[1] - 2, b_[3] + 1); ax.set_aspect("equal"); ax.axis("off")
fig.text(0.01, 0.975, "The flex's way up: tight, but not full", fontsize=15, weight="bold", va="top")
tx = fig.add_axes([0.55, 0.05, 0.43, 0.86]); tx.axis("off")
L = [("What the router did", True),
     ("Both trials sent all the flex lines up the right side (orange),", None),
     ("but put them on only one or two layers there: 10 lines on 4", None),
     ("layers, 13 on 6. Then it ran out and left the rest.", None),
     ("", None),
     ("What fits", True),
     ("The strip beside windows D, C and B is 2.3 mm wide once copper", None),
     ("keeps 0.25 off each edge: about 10 tracks a layer. The board", None),
     ("now has 4 signal layers there, so about 40. The flex brings", None),
     ("18 lines up (16 signals and the USB pair). The left strip is", None),
     ("just as wide and empty.", None),
     ("", None),
     ("The one real pinch", True),
     ("Outside the LEDs at about 2 and 4 o'clock only 0.6 mm is left.", None),
     ("So the lines turn in through the gap between two LEDs (6.2 mm", None),
     ("since they turned along the ring), cross inside the ring, where", None),
     ("the inner layers are free, and come out again above (purple).", None),
     ("", None),
     ("So, nothing added or moved", True),
     ("I lay the flex lines myself first as one planned ribbon, spread", None),
     ("over the layers: the analog ones (CV, audio, ground sense) on", None),
     ("In3, between the two ground planes; SPI, I2C, MIDI, USB on In2", None),
     ("and the outer layers. Then the router does the rest of the", None),
     ("board around them.", None)]
y = 0.98
for t, bold in L:
    tx.text(0, y, t, fontsize=11 if bold else 10.2, weight="bold" if bold else None, va="top", transform=tx.transAxes); y -= 0.038
fig.savefig(sys.argv[2])
