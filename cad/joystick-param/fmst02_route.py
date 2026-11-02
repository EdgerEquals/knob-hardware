"""Joystick v0.5 + DO0164FMST02: section on y = 0 (x-z), both flex-exit ends, with the jumper route sketched from the B2B header to
the daughterboard socket. Study for the flex-exit decision (2 Nov, after [Ed 16:14]).
Run from cad/joystick-param with the knob-param venv:  python fmst02_route.py <board.stp or fmst02.brep> <out.png>"""
import sys, os
sys.path.insert(0, os.getcwd())
src, out = sys.argv[1], sys.argv[2]
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch
from build123d import import_step, import_brep, Pos, Rot, Box, Align
from jsparam import params, parts

D = params.derive(params.P)
P = parts.build(D)
if src.endswith(".brep"):
    scr = import_brep(src)
else:
    def find(s, name):
        if (getattr(s, "label", "") or "") == name: return s
        for ch in getattr(s, "children", []) or []:
            r = find(ch, name)
            if r is not None: return r
    scr = find(import_step(src), "MS-DO0164FMST02").solids()[0]
bb = scr.bounding_box(); cy = (bb.min.Y + bb.max.Y) / 2
z0 = D["z_scr0"]
skip = ("top screen", "screen FPC [A]", "screen jumper FPC")

def faces_y(solid, y=0.0):
    sl = solid & (Pos(0, y - 0.001, 0) * Box(200, 0.002, 200, align=(Align.CENTER, Align.MIN, Align.CENTER)))
    tris = []
    for f in sl.faces():
        if abs(f.normal_at().Y) < 0.99: continue
        vs, ts = f.tessellate(0.02)
        tris += [[(vs[i].X, vs[i].Z) for i in t] for t in ts]
    return tris

def col(n):
    if "carrier" in n or "cradle" in n or "faceplate" in n or "anchor" in n: return "#c9dbe3"
    if "socket" in n: return "#c98a1b"
    if "PCB" in n or "daughterboard" in n: return "#1e6b35"
    if "SKRHADE" in n: return "#1c1c1c"
    return "#9aa3a8"

sx = D["db_sock_x"]; z_sock = D["z_db1"] + D["db_fpc_sock"][2]
hz = z0 - 2.15                       # header mating face
rz = hz - 0.9                        # mated receptacle + stiffener under it [A]
cases = [("A: flex leaves the -x end, header at +11.75 (recommended)", -90.0,
          [(11.75, rz), (sx, rz), (sx, z_sock + 0.3)]),
         ("B: flex leaves the +x end (v0.5 side), header at -11.75", 90.0,
          [(-11.75, rz), (sx, rz), (sx, z_sock + 0.3)])]
fig, axs = plt.subplots(2, 1, figsize=(15, 11.5))
for ax, (title, ang, route) in zip(axs, cases):
    for n, s in P.items():
        if n.startswith(skip): continue
        b = s.bounding_box()
        if not (b.min.Y < 0 < b.max.Y): continue
        tr = faces_y(s)
        if tr: ax.add_collection(PolyCollection(tr, facecolors=col(n), edgecolors="none", alpha=0.9))
    scrp = Pos(0, 0, z0) * Rot(0, 0, ang) * Pos(0, -cy, 0) * scr
    tr = faces_y(scrp)
    if tr: ax.add_collection(PolyCollection(tr, facecolors="#e08a1e", edgecolors="none", alpha=0.8))
    xs, zs = zip(*route)
    ax.plot(xs, zs, color="#d62728", lw=2.2)
    L = sum(((xs[i + 1] - xs[i]) ** 2 + (zs[i + 1] - zs[i]) ** 2) ** 0.5 for i in range(len(xs) - 1))
    ax.text(route[0][0], rz - 0.9, f"jumper ≈ {L:.0f} mm + slack loop", color="#d62728", fontsize=9, ha="center", va="top")
    ax.set_xlim(-24, 24); ax.set_ylim(28.5, 46); ax.set_aspect("equal"); ax.grid(True, lw=0.3)
    ax.set_title(title, fontsize=10); ax.set_xlabel("x (mm, carrier frame)"); ax.set_ylabel("z (mm, PCB front = 0)")
fig.legend(handles=[Patch(fc="#e08a1e", label="DO0164FMST02 (glass, folded flex, B2B header)"),
                    Patch(fc="#c9dbe3", label="grip block, carrier, cradle, faceplate"),
                    Patch(fc="#9aa3a8", label="inserts, guides, peg, springs, balls"),
                    Patch(fc="#1e6b35", label="joystick daughterboard / main PCB"),
                    Patch(fc="#c98a1b", label="daughterboard flex socket (x 16)"),
                    Patch(fc="#d62728", label="jumper route (sketch)")], loc="lower center", ncol=3, fontsize=8, frameon=False)
fig.suptitle("Joystick v0.5 section on y = 0 with the DO0164FMST02: where the jumper has to go for each flex-exit end",
             fontsize=11, x=0.01, ha="left")
fig.subplots_adjust(top=0.94, bottom=0.1, hspace=0.22)
fig.savefig(out, dpi=100); print("wrote", out)
