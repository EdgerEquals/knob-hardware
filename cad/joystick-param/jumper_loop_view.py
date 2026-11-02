"""Joystick v0.6 jumper loop [Ed 17:16]: plan cut through the loop band and a section along the S2 leg.
Run from cad/joystick-param:  python jumper_loop_view.py <out.png>"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch
from build123d import Pos, Box, Align
from jsparam import params, parts
from section_v06 import faces, colour


def zfaces(solid, z):
    sl = solid & (Pos(0, 0, z - 0.001) * Box(200, 200, 0.002, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    tris = []
    for f in sl.faces():
        if abs(f.normal_at().Z) < 0.99:
            continue
        vs, ts = f.tessellate(0.02)
        tris += [[(vs[i].X, vs[i].Y) for i in t] for t in ts]
    return tris


def main(out):
    D = params.derive(params.P); P = parts.build(D)
    zb, zt = D["z_leg"]; zm = (zb + zt) / 2
    fig, axs = plt.subplots(1, 2, figsize=(17, 8.5))
    used = {}
    for ax, kind in zip(axs, ("plan", "sec")):
        for n, s in P.items():
            if n.startswith(("main PCB", "rear spring", "cross pin", "faceplate")):
                continue
            b = s.bounding_box()
            if kind == "plan":
                if not (b.min.Z < zm < b.max.Z):
                    continue
                tr = zfaces(s, zm)
            else:
                if not (b.min.Y < D["jmp_y2"] < b.max.Y):
                    continue
                tr = faces(s, "y", D["jmp_y2"])
            if tr:
                lab, c = colour(n); used[lab] = c
                ax.add_collection(PolyCollection(tr, facecolors=c, edgecolors="none", alpha=0.95))
        ax.grid(True, lw=0.3); ax.set_aspect("equal")
        if kind == "plan":
            ax.set_xlim(2, 22); ax.set_ylim(-10, 8)
            ax.set_title(f"plan cut at z {zm:.2f} through the loop (looking down): S1 along y, S2 along -x, crease, S3 back", fontsize=9.5)
            ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm)")
            for (x, y) in D["cs_xy"][:2]:
                ax.add_patch(plt.Circle((x, y), 0.65, fill=False, ls=":", ec="#d62728"))
            ax.text(10.0, -6.9, "grub key line (behind)", fontsize=7, color="#d62728")
        else:
            ax.set_xlim(2, 22); ax.set_ylim(29.5, 46)
            ax.set_title(f"section along the S2 leg, y = {D['jmp_y2']:g}", fontsize=9.5)
            ax.set_xlabel("x (mm)"); ax.set_ylabel("z (mm)")
    e = D["jmp_eps"]; fat = D["jmp_fatigue"]
    fig.legend(handles=[Patch(fc=c, label=l) for l, c in used.items()], loc="lower center", ncol=5, fontsize=8, frameon=False)
    fig.suptitle(f"Joystick {D['version']} screen jumper [Ed 17:16]: {D['fpc_w']:g} mm, 13 lines, no touch; about {D['jmp_len']:.0f} mm in a loose loop "
                 f"under the carrier. Copper strain (cautious case) x {100*e['x']:.3f}% ({fat/e['x']:.1f}x), y {100*e['y']:.3f}% "
                 f"({fat/e['y']:.1f}x), press {100*e['z']:.3f}% ({fat/e['z']:.1f}x) under {100*fat:.1f}% [A]", fontsize=10, x=0.01, ha="left")
    fig.subplots_adjust(top=0.9, bottom=0.1, wspace=0.12)
    fig.savefig(out, dpi=100); print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1])
