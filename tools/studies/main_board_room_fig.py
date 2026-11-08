"""Picture of the main board room map (main_board_room.py's pickle): both faces, what the mechanics fix there, what is free.
  python3 tools/studies/main_board_room_fig.py <mb_room.pkl> <out.png>"""
import sys, pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon

R = pickle.load(open(sys.argv[1], "rb"))
board, occ, free = R["board"], R["occ"], R["free"]


def polys(g):
    return [g] if isinstance(g, Polygon) else list(getattr(g, "geoms", []))


def draw(ax, g, **kw):
    for p in polys(g):
        if p.is_empty:
            continue
        ax.add_patch(plt.Polygon(list(p.exterior.coords), **kw))
        for i in p.interiors:
            ax.add_patch(plt.Polygon(list(i.coords), fc="white", ec=kw.get("ec", "none"), lw=kw.get("lw", 0.4)))


fig = plt.figure(figsize=(15, 13.5), dpi=120)
for k, (face, title) in enumerate((("front", "FRONT (toward the panel): the knob drive sits here"),
                                   ("back", "BACK (toward the back cover), seen through the board from the front"))):
    ax = fig.add_axes([0.02 + k * 0.49, 0.03, 0.46, 0.88])
    draw(ax, board, fc="#f1f8e9", ec="#33691e", lw=0.8)
    draw(ax, free[face], fc="#c5e1a5", ec="none")
    big = sorted(occ[face].items(), key=lambda kv: -kv[1].area)
    for n, g in big:
        draw(ax, g.intersection(board.buffer(0.5)), fc="#cfd8dc", ec="#546e7a", lw=0.4, alpha=0.9)
    for n, g in big[:16]:
        c = g.representative_point()
        ax.text(c.x, c.y, n.split("(")[0][:26], fontsize=5.6, ha="center", va="center", color="#263238")
    ax.set_title(f"{title}\nfree {free[face].area:.0f} of {board.area:.0f} mm²", fontsize=10.5, loc="left")
    b = board.bounds
    ax.set_xlim(b[0] - 2, b[2] + 2); ax.set_ylim(b[1] - 2, b[3] + 2); ax.set_aspect("equal"); ax.grid(alpha=0.15)
fig.text(0.02, 0.975, "Main board, v0.52: what the mechanics fix on each face (grey) and the free room (green). Windows are the "
         "white cut-outs.", fontsize=13, weight="bold", va="top")
fig.savefig(sys.argv[2])
