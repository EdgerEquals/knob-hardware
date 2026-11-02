"""Joystick v0.6 sections through the DO0164FMST02 connector: along the long axis (y = 0) and across it (x = header centre),
plus a close-up of the header end. Run from cad/joystick-param:  python section_v06.py <out.png>"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch
from build123d import Pos, Box, Align
from jsparam import params, parts

D = params.derive(params.P)
P = parts.build(D)

def faces(solid, axis, at):
    if axis == "y":
        slab = Pos(0, at - 0.001, 0) * Box(200, 0.002, 200, align=(Align.CENTER, Align.MIN, Align.CENTER))
    else:
        slab = Pos(at - 0.001, 0, 0) * Box(0.002, 200, 200, align=(Align.MIN, Align.CENTER, Align.CENTER))
    sl = solid & slab
    tris = []
    for f in sl.faces():
        n = f.normal_at()
        if abs(n.Y if axis == "y" else n.X) < 0.99:
            continue
        vs, ts = f.tessellate(0.02)
        tris += [[((v.X if axis == "y" else v.Y), v.Z) for v in (vs[i] for i in t)] for t in ts]
    return tris

KEYS = [("screen (glass + back)", "#1b2433", lambda n: n.startswith("top screen")),
        ("foam pads [A]", "#7a7a7a", lambda n: n.startswith("screen foam")),
        ("jumper connectors [A]", "#111111", lambda n: "jumper" in n and ("socket" in n or "plug end" in n)),
        ("jumper flex [A]", "#e0a020", lambda n: n.startswith("screen jumper FPC")),
        ("grip block / carrier / cradle (MJF)", "#c9dbe3", lambda n: n.startswith(("screen carrier", "joystick carrier", "joystick cradle", "rear spring"))),
        ("faceplate (case)", "#e8f3f6", lambda n: n.startswith("faceplate")),
        ("brass, steel (inserts, guides, peg, springs, balls)", "#9aa3a8", lambda n: n.startswith(("guide", "press peg", "brass", "grub", "compression", "ball", "hold-down", "cross pin", "cradle locating"))),
        ("boards", "#1e6b35", lambda n: n.startswith(("joystick daughterboard", "main PCB"))),
        ("switch, sockets, headers", "#2b2b2b", lambda n: True)]

def colour(n):
    for lab, c, f in KEYS:
        if f(n):
            return lab, c

views = [("y", 0.0, (-23, 23), (29.5, 46), "along the long axis, y = 0"),
         ("x", D["jmp_x"], (-15.5, 15.5), (29.5, 46), f"across, x = {D['jmp_x']:g} (the B2B header)"),
         ("y", 0.0, (3.0, 21.0), (37.5, 45.5), "close-up of the header end, y = 0"),
         ("y", D["g_xy"][0][1], (2.0, 14.0), (31.0, 45.5), f"through the +x guide, y = {D['g_xy'][0][1]:g}")]
fig, axs = plt.subplots(2, 2, figsize=(17, 12))
used = {}
for ax, (axis, at, xl, zl, title) in zip(axs.flat, views):
    for n, s in P.items():
        if n.startswith(("main PCB", "rear spring", "cross pin")):
            continue
        b = s.bounding_box()
        lo, hi = (b.min.Y, b.max.Y) if axis == "y" else (b.min.X, b.max.X)
        if not (lo < at < hi):
            continue
        tr = faces(s, axis, at)
        if tr:
            lab, c = colour(n); used[lab] = c
            ax.add_collection(PolyCollection(tr, facecolors=c, edgecolors="none", alpha=0.95))
    ax.set_xlim(*xl); ax.set_ylim(*zl); ax.set_aspect("equal"); ax.grid(True, lw=0.3)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel(("x" if axis == "y" else "y") + " (mm)"); ax.set_ylabel("z (mm, main-PCB front = 0)")
fig.legend(handles=[Patch(fc=c, label=l) for l, c in used.items()], loc="lower center", ncol=5, fontsize=8, frameon=False)
fig.suptitle(f"Joystick {D['version']}: DO0164FMST02 in a {D['roof_t']:.2f} roof (pockets + foam pads), window and step at the "
             f"connector, custom jumper [A] to the daughterboard socket at x {D['db_sock_x']:g}; guides at (±{D['g_xy'][0][0]:g}, ±{D['g_xy'][0][1]:g})",
             fontsize=10.5, x=0.01, ha="left")
fig.subplots_adjust(top=0.94, bottom=0.08, hspace=0.15, wspace=0.1)
fig.savefig(out, dpi=100); print("wrote", out)
