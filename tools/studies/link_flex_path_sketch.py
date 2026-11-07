"""Link flex, decision picture (7 Nov 2026): section at x 14 (the middle of the link lane), seen from the +x side.
Two paths for the flex from its solder pads on the main board strip up into the FH26W on the jack lower board's underside.
FH26W-25S-0.3SHW(60): bottom contact, takes a 0.20 FPC [S DigiKey]; upside down under the lower board, so the flex's contacts must
face up (+z) where it goes in. Input: a section pickle from the model (scratch script), output docs/img/link-flex-path-sketch.png.
Run:  python3 tools/studies/link_flex_path_sketch.py <section.pkl>"""
import sys, os, math, pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Arc

_, sec = pickle.load(open(sys.argv[1], "rb"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs", "img", "link-flex-path-sketch.png")
COL = {"FPC connector": "#6d4c41", "PCB back parts": "#a5d6a7", "PCB": "#2e7d32", "case": "#bdbdbd", "clear OLED": "#80deea",
       "parts (envelope)": "#c8e6c9", "jack lower board": "#43a047",
       "back cover": "#9e9e9e"}


def colour(n):
    for k, c in COL.items():
        if k in n:
            return c
    return None


def flex(ax, pts, fingers, label, col):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=col, lw=2.6, solid_capstyle="round", zorder=6, label=label)
    for (y0, z0), (y1, z1), side in fingers:   # contact side marked with short ticks
        n = 6
        for i in range(n + 1):
            y = y0 + (y1 - y0) * i / n; z = z0 + (z1 - z0) * i / n
            dy, dz = (0, 0.25 * side) if abs(z1 - z0) < 1e-6 else (0.25 * side, 0)
            ax.plot([y, y + dy], [z, z + dz], color=col, lw=1.2, zorder=6)


def arc_pts(cy, cz, r, a0, a1, n=12):
    return [(cy + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]


fig, axs = plt.subplots(1, 2, figsize=(14, 6.4), dpi=150, sharey=True)
for ax, title in zip(axs, ("A  J path out towards the case: contacts on the same face at both ends (single-layer flex)",
                           "B  straight riser by the OLED (as drawn now): contacts on opposite faces (2-layer flex, vias)")):
    for n, polys in sec.items():
        c = colour(n)
        if c is None or n.startswith("link flex"):
            continue
        for p in polys:
            if len(p) > 2:
                ax.add_patch(Polygon(p, closed=True, fc=c, ec="black", lw=0.4, alpha=0.8, zorder=2))
    ax.set_xlim(-55.4, -43.8); ax.set_ylim(-2.2, 14.6); ax.set_aspect("equal"); ax.grid(alpha=0.15)
    ax.set_title(title, fontsize=8.5, loc="left"); ax.set_xlabel("y (mm, panel; up the module →)")
    ax.text(-55.2, 13.9, "case", fontsize=7); ax.text(-53.1, 2.75, "ledge", fontsize=7); ax.text(-48.6, 0.35, "clear OLED", fontsize=7)
    ax.text(-48.6, 12.25, "jack lower board", fontsize=7, color="white"); ax.text(-46.9, 10.95, "FH26W", fontsize=6.5, color="white", zorder=7)
    ax.text(-53.2, -1.1, "main board", fontsize=7, color="white")
axs[0].set_ylabel("z (mm above the main board's front)")
zs = 11.19   # slot centre: 1.0 tall connector hanging under the board [A]
# A: pads y -50.3..-49.0 on the board, leave towards -y, r 0.8 up, riser at y -51.35, r 1.6 over into the slot
r1, r2, yr = 0.8, 1.6, -51.35
A = [(-49.0, 0.06), (-50.3, 0.06)] + arc_pts(-50.3 - 0, 0.06 + r1, r1, 270, 180)[1:]
A = [(-49.0, 0.06), (-50.55, 0.06)] + arc_pts(-50.55, 0.06 + r1, r1, 270, 180)[1:] + [(yr, zs - r2)] + arc_pts(yr + r2, zs - r2, r2, 180, 90)[1:] + [(-44.95, zs)]
flex(axs[0], A, [((-49.0, 0.06), (-50.3, 0.06), -1), ((-48.15, zs), (-44.95, zs), +1)], "flex (0.1 single layer)", "#d32f2f")
axs[0].annotate("solder fingers face down\n(pads in the strip)", (-49.6, 0.06), (-50.4, 4.4), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.6))
axs[0].annotate("contacts face up into the\nbottom-contact FH26W", (-46.4, zs), (-49.9, 7.0), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.6))
axs[0].annotate(f"riser 0.45 off the ledge\nbends r {r1:g} and r {r2:g}", (yr, 5.5), (-55.2, 8.6), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.6))
# B: pads y -50.6..-49.6, riser at y -49.33 (model), top bend must fit between the riser and the slot: r <= 0.8
rb = 0.75
B = [(-50.6, 0.06), (-49.33 - 0.5, 0.06)] + arc_pts(-49.83, 0.56, 0.5, 270, 360)[1:] + [(-49.33, zs - rb)] + arc_pts(-49.33 + rb, zs - rb, rb, 180, 90)[1:] + [(-44.95, zs)]
flex(axs[1], B, [((-50.6, 0.06), (-49.85, 0.06), -1), ((-48.15, zs), (-44.95, zs), +1)], "flex (0.2 two layers)", "#1565c0")
axs[1].annotate("fingers down here ...", (-50.2, 0.06), (-55.2, 4.0), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.6))
axs[1].annotate("... but the bends turn that face\naway from the contacts up here,\nso the ends need opposite faces", (-46.4, zs), (-55.2, 7.6),
                fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.6))
axs[1].annotate("top bend r ≤ 0.8 between the riser\nand the slot (a 2-layer flex wants ≥ 2)", (-49.0, zs - 0.5), (-48.4, 4.6), fontsize=7,
                arrowprops=dict(arrowstyle="->", lw=0.6))
for ax in axs:
    ax.legend(loc="lower right", fontsize=7, frameon=False)
fig.suptitle("Link flex: section at x 14 (middle of the lane x 9.5-18.5), from the +x side. Ticks = the contact face.", fontsize=9, x=0.01, ha="left")
fig.tight_layout(); fig.savefig(OUT); print("wrote", OUT)
