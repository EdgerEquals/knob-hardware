"""Main board placement plan, v0.52 (8 Nov 2026, step 3, Ed 19:02 "Go"): the room map (main_board_room.py) with a block for every
circuit group, where it goes and how big [A], and the corridors the signals take past the windows and through the ring of LED
cut-outs. A block outlined red does not fit the free room where drawn.
  python3 tools/studies/main_board_plan_fig.py <mb_room.pkl> <out.png>"""
import sys, pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, box

R = pickle.load(open(sys.argv[1], "rb"))
board, occ, free = R["board"], R["occ"], R["free"]
COL = {"digital": "#9ecae1", "noisy": "#fc9272", "quiet": "#a1d99b", "power": "#fdd0a2", "conn": "#d9d9d9"}
# (face, x, y, w, h, label, kind): panel frame, mm; sizes [A] from the parts lists
BLOCKS = [
    ("front", 0.0, 37.0, 16.0, 16.0, "H743 LQFP100\n+ decoupling, VCAP,\ncrystal, BOOT0, NRST", "digital"),
    ("front", -11.9, 32.0, 4.0, 8.0, "Tag-\nConnect\npads", "conn"),
    ("front", 11.8, 31.5, 5.0, 6.0, "22 Ω x6\n33 Ω x2", "digital"),
    ("front", 0.6, 25.6, 2.8, 3.6, "power\nlight", "digital"),
    ("back", -7.5, 29.0, 4.5, 4.5, "REF3430\n3.0 V\n+ caps", "quiet"),
    ("back", 0.5, 30.5, 7.5, 5.0, "ADC inputs:\n100 Ω + 1 nF x14,\n1 MΩ (QGND sense)", "quiet"),
    ("back", 0.0, 23.8, 3.5, 3.0, "light\ndriver", "digital"),
    ("back", 14.0, 21.0, 4.0, 2.6, "enc. R x3", "quiet"),
    ("back", 6.5, -12.0, 8.0, 6.5, "DRV8213 + caps,\ncurrent limit,\nIPROPI, NTC,\nmotor voice", "noisy"),
    ("back", 9.25, 3.0, 6.0, 6.0, "rod link:\nchoke 3x3,\ncap, comparator", "noisy"),
    ("back", -6.5, -12.0, 5.0, 4.0, "ring 5 V:\nferrite +\n2 x 22 µF", "noisy"),
    ("back", -12.0, 8.0, 3.5, 3.0, "I2C\npull-ups", "quiet"),
    ("back", 0.0, 46.6, 12.0, 2.4, "cover board pads (later)", "conn"),
]


def polys(g):
    return [g] if isinstance(g, Polygon) else list(getattr(g, "geoms", []))


def draw(ax, g, **kw):
    for p in polys(g):
        if p.is_empty:
            continue
        ax.add_patch(plt.Polygon(list(p.exterior.coords), **kw))
        for i in p.interiors:
            ax.add_patch(plt.Polygon(list(i.coords), fc="white", ec=kw.get("ec", "none"), lw=kw.get("lw", 0.4)))


fig = plt.figure(figsize=(17, 14), dpi=120)
for k, face in enumerate(("front", "back")):
    ax = fig.add_axes([0.01 + k * 0.33, 0.04, 0.31, 0.86])
    draw(ax, board, fc="#f1f8e9", ec="#33691e", lw=0.8)
    draw(ax, free[face], fc="#e6f2d9", ec="none")
    for n, g in occ[face].items():
        draw(ax, g.intersection(board.buffer(0.5)), fc="#cfd8dc", ec="#90a4ae", lw=0.3, alpha=0.9)
    placed = []
    for (f, x0, y0, w, h, lab, kind) in BLOCKS:
        if f != face:
            continue
        fixed = "H743" in lab or lab.startswith("power")
        x, y, fits = x0, y0, fixed
        if not fixed:
            room = free[face].buffer(-0.3)
            for rr in [i * 0.25 for i in range(0, 41)]:
                cands = [(x0 + dx * 0.25, y0 + dy * 0.25) for dx in range(-40, 41) for dy in range(-40, 41)
                         if abs((dx * 0.25) ** 2 + (dy * 0.25) ** 2 - rr ** 2) < 0.13 * max(rr, 0.25)]
                for cx, cy in sorted(cands, key=lambda c: (c[0] - x0) ** 2 + (c[1] - y0) ** 2):
                    rb = box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
                    if rb.within(room) and not any(rb.intersects(o) for o in placed):
                        x, y, fits = cx, cy, True
                        break
                if fits:
                    break
        r = box(x - w / 2, y - h / 2, x + w / 2, y + h / 2); placed.append(r.buffer(0.3))
        ax.add_patch(plt.Rectangle((x - w / 2, y - h / 2), w, h, fc=COL[kind], ec="#333" if fits else "red", lw=0.8 if fits else 1.8))
        ax.text(x, y, lab, ha="center", va="center", fontsize=5.4)
    # corridors (both faces' tracks; drawn on each face)
    ax.plot([20.75, 20.75, 17.3, 16.6, 17.3, 20.75, 20.75], [-50, -23, -15.5, 0, 15.5, 23, 34], color="#6a1b9a", lw=2.2, alpha=0.75)
    ax.plot([-20.75, -20.75, -17.3, -16.6, -17.3, -20.75, -20.75], [-50, -23, -15.5, 0, 15.5, 23, 34], color="#ef6c00", lw=2.2, alpha=0.75)
    ax.set_title(("FRONT (toward the panel)" if face == "front" else "BACK, seen through the board from the front"), fontsize=11, loc="left")
    b = board.bounds
    ax.set_xlim(b[0] - 1.5, b[2] + 1.5); ax.set_ylim(b[1] - 1.5, b[3] + 1.5); ax.set_aspect("equal"); ax.axis("off")
fig.text(0.01, 0.975, "Main board plan: where each circuit goes (blocks, sizes [A]) and how the signals get past the windows and "
         "the ring of LED cut-outs", fontsize=13.5, weight="bold", va="top")
tx = fig.add_axes([0.67, 0.04, 0.32, 0.88]); tx.axis("off")
L = [("Most parts go on the BACK", True),
     ("The front is the knob drive's (free 985 mm², mostly round the", None),
     ("chip); the back is 2,451 mm² free (parts up to 2 mm tall).", None),
     ("", None),
     ("Front", True),
     ("H743 under the joystick (fixed since layout v4); Tag-Connect,", None),
     ("the screen and SPI resistors beside it; the power light (fixed).", None),
     ("", None),
     ("Back", True),
     ("Behind the chip: the 3.0 V reference and the ADC input filters", None),
     ("(quiet, short to the pins). Inside the ring: the 1220 driver by", None),
     ("the motor, the rod link by the rod, the ring LEDs' own 5 V", None),
     ("branch, the Hall caps (fixed). The encoder parts by its sensor.", None),
     ("", None),
     ("The tight spot: getting past the middle", True),
     ("Window D (clear screen) leaves a 2.8 mm strip each side; the 24", None),
     ("LED cut-outs then leave only 0.6 mm outside the ring at the", None),
     ("sides, so every track from the bottom (link flex, 15 V post)", None),
     ("to the top (chip, boards L and R) threads between two cut-outs", None),
     ("(1.76 mm webs) into the ring, then out again (purple right,", None),
     ("orange left). A web takes about 5 tracks a layer at PCBWay's", None),
     ("0.1 / 0.1 mm, 0.3 off each cut-out [A].", None),
     ("", None),
     ("What has to pass", True),
     ("Link flex 21 signals + USB pair; inside the ring to the chip: 4", None),
     ("Halls, Hall enable, motor 5, rod link 2, LED data, NTC, light;", None),
     ("15 V up to board L; 5 V (up to 1.8 A) and 3.3 V back down.", None),
     ("About 40 tracks plus three rails and ground: more than two", None),
     ("layers can carry through those webs. So 4 layers at least;", None),
     ("the count is settled after placing (next question).", None),
     ("", None),
     ("Red outline = a block that does not fit where drawn.", None)]
y = 0.98
for t, b in L:
    tx.text(0, y, t, fontsize=10.2 if b else 9.3, weight="bold" if b else None, va="top", transform=tx.transAxes); y -= 0.029
fig.savefig(sys.argv[2])
