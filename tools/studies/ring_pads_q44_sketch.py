"""Q44 picture (8 Nov 2026, main board step 3): the ring LEDs' solder pads against the windows and the board edge.
The SK6812MINI-E's four leads come out of its two short ends, so its pads sit 2.0-3.4 mm out from its centre along the 3.2 mm
body (Keebio-Parts, MIT, and marbastlib, CERN-OHL-P, agree [S]). The model (v0.52) points that axis along the radius.
  python3 tools/studies/ring_pads_q44_sketch.py <mb_room.pkl> <out.png>"""
import sys, math, pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely import affinity

R = pickle.load(open(sys.argv[1], "rb"))
b = R["board"]
keep = [i for i in b.interiors if abs(Polygon(i).area - 10.2) > 0.05]          # the model's 24 cut-outs out
B = Polygon(b.exterior, keep)
R0 = 19.8387                                                                    # thrust pitch radius [S model]
CASES = [("Now (model v0.52): 24, along the radius", 24, 0.0, "rad"),
         ("A: 12, turned along the ring", 12, 15.0, "tan"),
         ("B: 16, turned along the ring", 16, 11.25, "tan")]


def site(a, orient):
    pads = []
    for sr in (-1, 1):
        for st in (-1, 1):
            pads.append(box(sr * 2.70 - 0.70, st * 0.75 - 0.41, sr * 2.70 + 0.70, st * 0.75 + 0.41) if orient == "rad" else
                        box(st * 0.75 - 0.41, sr * 2.70 - 0.70, st * 0.75 + 0.41, sr * 2.70 + 0.70))
    cut = box(-1.7, -1.5, 1.7, 1.5) if orient == "rad" else box(-1.5, -1.7, 1.5, 1.7)
    T = lambda g: affinity.translate(affinity.rotate(g, a, origin=(0, 0)), R0 * math.cos(math.radians(a)), R0 * math.sin(math.radians(a)))
    return [T(p) for p in pads], T(cut)


def draw(ax, g, **kw):
    for p in ([g] if isinstance(g, Polygon) else list(g.geoms)):
        ax.add_patch(plt.Polygon(list(p.exterior.coords), **kw))
        for i in p.interiors:
            ax.add_patch(plt.Polygon(list(i.coords), fc="white", ec=kw.get("ec", "none"), lw=kw.get("lw", 0.5)))


fig = plt.figure(figsize=(16.5, 8.4), dpi=130)
stats = []
for k, (title, n, ph, orient) in enumerate(CASES):
    ax = fig.add_axes([0.01 + k * 0.33, 0.13, 0.31, 0.74])
    draw(ax, B, fc="#e8f5e9", ec="#33691e", lw=0.8)
    bad = 0; groups = []
    for j in range(n):
        pads, cut = site(ph + j * 360.0 / n, orient)
        draw(ax, cut, fc="white", ec="#455a64", lw=0.7)
        for p in pads:
            ok = B.buffer(-0.2).contains(p)
            bad += not ok
            draw(ax, p, fc="#f9a825" if ok else "#d32f2f", ec="#5d4037" if ok else "#b71c1c", lw=0.4)
        groups.append(unary_union(pads + [cut]))
    gap = min(groups[j].distance(groups[(j + 1) % n]) for j in range(n))
    stats.append((bad, gap))
    ax.add_patch(plt.Circle((0, 0), R0, fill=False, ls=":", lw=0.6, color="#555"))
    ax.set_xlim(-25, 25); ax.set_ylim(-26, 26); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title, fontsize=12.5, weight="bold", loc="left")
    line = (f"{bad} of {4 * n} pads in a window or off the board" if bad else f"every pad on board; {gap:.2f} mm between neighbours")
    ax.text(-24.5, -25.5, line, fontsize=10.5, color="#b71c1c" if bad else "#1b5e20", weight="bold")
fig.text(0.01, 0.975, "Q44: the ring LEDs' solder pads don't fit as the model has them", fontsize=15, weight="bold", va="top")
fig.text(0.01, 0.925, "Seen from the front. Green = board, white = windows and cut-outs, orange = pads, red = a pad that lands in a "
         "window or off the board edge. The LED's leads leave its short ends, so its pads sit up to 3.4 mm out from its centre.",
         fontsize=10.2, va="top")
fig.text(0.01, 0.07, "A: 30° apart; pads under the race, 3 mm clear of the windows; the gaps between cut-outs widen from 1.8 to "
         "about 7 mm, so the ~40 tracks that cross the ring get easier.", fontsize=10.2)
fig.text(0.01, 0.035, "B: 22.5° apart; fits, but neighbours sit 0.6 mm apart (tight); tracks cross the ring on the inner "
         "layers only. Either way the model's cut-outs and the race's two locating pegs turn with the LEDs.", fontsize=10.2)
fig.savefig(sys.argv[2])
print(stats)
