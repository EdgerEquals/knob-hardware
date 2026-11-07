"""Picture of the link flex (7 Nov 2026): left, the flat flex from the copper side (as make_flex.py draws it); right, the same flex on
its J path in the section at x 14 (model geometry, link_flex_geom.json). Run with the system python (pcbnew):
    /usr/bin/python3 flex_picture.py <out.png>"""
import json, math, os, sys
import pcbnew, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
G = json.load(open(os.path.join(HERE, "link_flex_geom.json")))
b = pcbnew.LoadBoard(os.path.join(HERE, "kicad", "jack-link-flex.kicad_pcb"))
mm = pcbnew.ToMM
fig, (a, c) = plt.subplots(1, 2, figsize=(13.5, 7.2), dpi=150, gridspec_kw=dict(width_ratios=[1.0, 1.25]))
NC = {"GND": "#757575", "DP": "#c62828", "DN": "#c62828", "AOUT": "#1565c0", "AIN": "#1565c0"}
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts:
        a.plot([mm(d.GetStart().x), mm(d.GetEnd().x)], [-mm(d.GetStart().y), -mm(d.GetEnd().y)], color="black", lw=1.0)
    elif d.GetLayer() == pcbnew.User_1 and d.GetClass() == "PCB_SHAPE":
        x0, y0, x1, y1 = mm(d.GetStart().x), -mm(d.GetStart().y), mm(d.GetEnd().x), -mm(d.GetEnd().y)
        a.add_patch(Rectangle((min(x0, x1), min(y0, y1)), abs(x1 - x0), abs(y1 - y0), fc="#ffe082", ec="#f9a825", lw=0.6, alpha=0.6, zorder=1))
    elif d.GetLayer() == pcbnew.User_2 and d.GetClass() == "PCB_SHAPE":
        a.plot([mm(d.GetStart().x), mm(d.GetEnd().x)], [-mm(d.GetStart().y), -mm(d.GetEnd().y)], color="#8e24aa", lw=0.6, ls="--")
for t in b.GetTracks():
    n = t.GetNetname(); col = NC.get(n.split("_p")[0], "#ef6c00")
    a.plot([mm(t.GetStart().x), mm(t.GetEnd().x)], [-mm(t.GetStart().y), -mm(t.GetEnd().y)], color=col, lw=0.9, zorder=3)
for f in b.GetFootprints():
    for p in f.Pads():
        x, y = mm(p.GetPosition().x), -mm(p.GetPosition().y); w, h = mm(p.GetSize().x), mm(p.GetSize().y)
        a.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc="#ffd54f", ec="#b8860b", lw=0.3, zorder=4))
xs = [106.0, 126.0]
a.set_xlim(*xs); a.set_aspect("equal"); a.grid(alpha=0.12)
L, W = G["flat_len"], G["w"]
a.text(114.1, -99.3, "FH26W end: contacts up (bottom-contact connector)\n" f"stiffener on the back, {G['stiff']:g} long, 0.20 total",
       ha="center", fontsize=7.5)
a.text(114.1, -100 - L - 1.4, f"main-board end: solder fingers down onto the strip's pads\n(hot-bar at PCBWay, or by hand)", ha="center", fontsize=7.5, va="top")
a.text(118.6, -100 - L / 2, f"{W:g} x {L:.2f} flat\n25 x 0.15 at 0.3\nsingle-sided PI\n\npin 1 (SCK) left,\nas J6", fontsize=7.5, va="center")
a.set_ylim(-100 - L - 3.6, -97.6)
a.set_title("Flat, seen from the copper side (x = panel x + 100)", fontsize=9, loc="left")
for n_, col in (("grounds", "#757575"), ("USB D+/D-", "#c62828"), ("audio out / in", "#1565c0"), ("other signals", "#ef6c00")):
    a.plot([], [], color=col, lw=2, label=n_)
a.plot([], [], color="#8e24aa", ls="--", lw=0.8, label="bend lines")
a.legend(loc="upper right", fontsize=7, frameon=False)
# right: the J in section
t = G["t"]; y0, y1 = G["pad_y"]; rb, rt = G["r_bottom"], G["r_top"]; yi = G["riser_y"][1]; ye = G["end_y"]
z0 = 0.02; zbc = z0 + t + rb; ztc = G["contact_face_z"] - t - rt


def arc(cy, cz, r, a0, a1, n=24):
    return [(cy + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)), cz + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


mid = [(y1, z0 + t / 2), (y0, z0 + t / 2)] + arc(y0, zbc, rb + t / 2, 270, 180) + [(yi - t / 2, ztc)] + arc(yi + rt, ztc, rt + t / 2, 180, 90) + [(ye, ztc + rt + t / 2)]
c.plot(*zip(*mid), color="#d32f2f", lw=2.4, solid_capstyle="butt", zorder=5, label=f"flex, t {t:g}")
c.add_patch(Rectangle((ye - G["stiff"], ztc + rt - (G["t_end"] - t)), G["stiff"], G["t_end"] - t, fc="#ffe082", ec="#f9a825", lw=0.6, zorder=5))
c.add_patch(Rectangle((-53.3, -1.6), 6.4, 1.6, fc="#2e7d32", ec="black", lw=0.4)); c.text(-53.1, -1.15, "main board", color="white", fontsize=7)
c.add_patch(Rectangle((G["oled_edge_y"], 0), 4.0, 1.25, fc="#80deea", ec="black", lw=0.4)); c.text(-48.6, 0.35, "clear OLED", fontsize=7)
c.add_patch(Rectangle((-53.3, 0), 1.5, 2.55, fc="#bdbdbd", ec="black", lw=0.4)); c.text(-53.25, 2.75, "ledge", fontsize=7)
c.add_patch(Rectangle((-48.9, 11.7), 4.9, 1.6, fc="#43a047", ec="black", lw=0.4)); c.text(-48.7, 12.3, "jack lower board", color="white", fontsize=7)
c.add_patch(Rectangle((G["mouth_y"], 10.7), 3.7, 0.98, fc="#6d4c41", ec="black", lw=0.4, alpha=0.55)); c.text(-46.9, 10.85, "FH26W", color="white", fontsize=7)
c.annotate(f"r {rb:.2f}", (y0 - 0.7, zbc - 0.6), (-50.6, 3.6), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.5))
c.annotate(f"r {rt:g}", (yi + 0.4, ztc + 1.2), (-50.2, 8.4), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.5))
c.annotate(f"end {G['mate']:g} into the connector", (ye, ztc + rt), (-47.6, 14.0), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.5))
c.set_xlim(-54.0, -43.6); c.set_ylim(-2.0, 15.0); c.set_aspect("equal"); c.grid(alpha=0.12)
c.set_xlabel("y (mm, panel)"); c.set_ylabel("z above the main board (mm)")
c.set_title("Installed: section at x 14, from the +x side (model v0.50)", fontsize=9, loc="left")
c.legend(loc="lower right", fontsize=7, frameon=False)
fig.suptitle("Link flex v0.1 (Q29 = A, J path)", fontsize=10, x=0.01, ha="left")
fig.tight_layout(); fig.savefig(sys.argv[1]); print("wrote", sys.argv[1])
