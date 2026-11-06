"""Picture of a routed 4-layer jack board (knob step 2, 6 Nov 2026): F.Cu, In2.Cu and B.Cu one above the other, all seen from the
front (panel x to the right, panel y up); In1.Cu is the ground plane and is not drawn. Tracks coloured by net (ground grey), pads
outlined, vias as rings. With a DRC report, the connections still missing are drawn as dashed black lines on every panel (what is
left to route by hand). Run with the system python that has pcbnew:
  /usr/bin/python3 routed_picture.py <board.kicad_pcb> <out.png> [title] [drc.rpt]"""
import re, sys
import pcbnew, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon

JY = -44.40; O = 100.0
PAL = ["#00897b", "#5e35b1", "#c0ca33", "#f4511e", "#3949ab", "#8d6e63", "#d81b60", "#43a047", "#fb8c00", "#039be5", "#6d4c41",
       "#00acc1", "#7cb342", "#e53935", "#8e24aa"]
NC = {"GND": "#757575", "VBUS": "#c62828", "VSYS": "#ad1457", "3V3": "#ef6c00", "P12V5": "#2e7d32", "N12V": "#1565c0"}


def col(n):
    return NC.get(n) or (PAL[sum(map(ord, n)) % len(PAL)] if n else "#bdbdbd")


def P(x, y):   # board-local KiCad nm -> panel mm
    return pcbnew.ToMM(x) - O, JY - (pcbnew.ToMM(y) - O)


def missing(rpt):
    """[(net, (x0, y0), (x1, y1))] panel mm, from the [unconnected_items] entries of a KiCad DRC report."""
    out = []
    for blk in open(rpt).read().split("[unconnected_items]")[1:]:
        pts = re.findall(r"@\(([-\d.]+) mm, ([-\d.]+) mm\): \w+[^\[]*\[([^\]]+)\]", blk)[:2]
        if len(pts) == 2:
            (ax, ay, n), (bx, by, _) = pts
            out.append((n, (float(ax) - O, JY - (float(ay) - O)), (float(bx) - O, JY - (float(by) - O))))
    return out


def main(pcb, out, title="", rpt=None):
    b = pcbnew.LoadBoard(pcb)
    miss = missing(rpt) if rpt else []
    edge = [P(d.GetStart().x, d.GetStart().y) for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
    layers = [(pcbnew.F_Cu, "F.Cu (top face)"), (pcbnew.In2_Cu, "In2.Cu (inner signal layer; In1.Cu is the ground plane)"),
              (pcbnew.B_Cu, "B.Cu (underside, seen through from the front)")]
    fig, axs = plt.subplots(3, 1, figsize=(13.5, 11.0), dpi=140)
    xs = [p[0] for p in edge]; ys = [p[1] for p in edge]
    for ax, (L, name) in zip(axs, layers):
        segs = [(d.GetStart(), d.GetEnd()) for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
        for s0, s1 in segs:
            ax.plot(*zip(P(s0.x, s0.y), P(s1.x, s1.y)), color="black", lw=1.0, zorder=1)
        for f in b.GetFootprints():
            for p in f.Pads():
                if not p.IsOnLayer(L):
                    continue
                x, y = P(p.GetPosition().x, p.GetPosition().y); w, h = pcbnew.ToMM(p.GetSize().x), pcbnew.ToMM(p.GetSize().y)
                if round(p.GetOrientationDegrees()) % 180 == 90:
                    w, h = h, w
                c = col(p.GetNetname())
                if p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:
                    ax.add_patch(Circle((x, y), w / 2, fc=c, ec="black", lw=0.3, alpha=0.45, zorder=2))
                else:
                    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=c, ec="black", lw=0.3, alpha=0.45, zorder=2))
        for t in b.GetTracks():
            n = t.GetNetname()
            if t.GetClass() == "PCB_VIA":
                x, y = P(t.GetPosition().x, t.GetPosition().y)
                ax.add_patch(Circle((x, y), pcbnew.ToMM(t.GetWidth()) / 2, fc=col(n), ec="black", lw=0.3, zorder=5))
                ax.add_patch(Circle((x, y), pcbnew.ToMM(t.GetDrillValue()) / 2, fc="white", ec="none", zorder=6))
            elif t.GetLayer() == L:
                (x0, y0), (x1, y1) = P(t.GetStart().x, t.GetStart().y), P(t.GetEnd().x, t.GetEnd().y)
                ax.plot([x0, x1], [y0, y1], color=col(n), lw=pcbnew.ToMM(t.GetWidth()) * 72 / 25.4 * 2.6, solid_capstyle="round", zorder=4)
        for n, a, c in miss:
            ax.plot([a[0], c[0]], [a[1], c[1]], color="black", lw=0.9, ls=(0, (3, 2)), zorder=7)
            ax.plot(*a, "o", ms=2.2, color="black", zorder=7); ax.plot(*c, "o", ms=2.2, color="black", zorder=7)
        ax.set_xlim(min(xs) - 0.4, max(xs) + 0.4); ax.set_ylim(min(ys) - 0.4, max(ys) + 0.4); ax.set_aspect("equal")
        ax.set_title(name, fontsize=9, loc="left"); ax.grid(alpha=0.12)
    axs[-1].set_xlabel("x (mm, panel)")
    h = [plt.Line2D([], [], color=c, lw=3, label=n) for n, c in NC.items()]
    h += [plt.Line2D([], [], color="#5e35b1", lw=3, label="signals (one colour per net)")]
    if miss:
        h += [plt.Line2D([], [], color="black", lw=0.9, ls=(0, (3, 2)), label=f"left to route by hand ({len(miss)})")]
    fig.legend(handles=h, loc="lower center", ncol=8, fontsize=8, frameon=False)
    if title:
        fig.suptitle(title, fontsize=10, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.03, 1, 0.97 if title else 1)); fig.savefig(out); print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "", sys.argv[4] if len(sys.argv) > 4 else None)
