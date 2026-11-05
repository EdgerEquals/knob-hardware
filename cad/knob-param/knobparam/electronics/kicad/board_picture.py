"""Picture of a small 2-layer board, both sides, nets coloured (knob step 2, 5 Nov 2026).
  /usr/bin/python3 board_picture.py <board.kicad_pcb> <out.png> [title]
Board-local mm from the KiCad origin (100, 100), y drawn up (up the panel for the USB-C board). The B side is drawn as seen from the back."""
import sys, pcbnew, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, Polygon
pcb, out = sys.argv[1], sys.argv[2]
TITLE = sys.argv[3] if len(sys.argv) > 3 else ""
O = 100.0
b = pcbnew.LoadBoard(pcb)
mm = pcbnew.ToMM
bb = b.GetBoardEdgesBoundingBox()
X0, X1 = mm(bb.GetX()) - O, mm(bb.GetRight()) - O
Y0, Y1 = -(mm(bb.GetBottom()) - O), -(mm(bb.GetY()) - O)
# the outline as one polygon when Edge.Cuts is a chain of straight segments (else the bounding box)
segs = [((mm(d.GetStart().x) - O, -(mm(d.GetStart().y) - O)), (mm(d.GetEnd().x) - O, -(mm(d.GetEnd().y) - O)))
        for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts and d.GetClass() == "PCB_SHAPE" and d.GetShape() == pcbnew.SHAPE_T_SEGMENT]
EDGE = []
if segs:
    left = segs[1:]; EDGE = [segs[0][0], segs[0][1]]
    while left:
        nxt = next((s_ for s_ in left if abs(s_[0][0] - EDGE[-1][0]) < 1e-4 and abs(s_[0][1] - EDGE[-1][1]) < 1e-4), None)
        if nxt is None:
            EDGE = []; break
        left.remove(nxt); EDGE.append(nxt[1])
NC = {"VBUS": "#d32f2f", "GND": "#424242", "DP": "#1976d2", "DN": "#7b1fa2", "CC1": "#2e7d32", "CC2": "#ef6c00"}
PAL = ["#00897b", "#5e35b1", "#c0ca33", "#f4511e", "#3949ab", "#8d6e63", "#d81b60", "#43a047", "#fb8c00", "#039be5"]


def col(n):
    if n in NC:
        return NC[n]
    if not n or n.startswith("unconnected"):
        return "#9e9e9e"
    return PAL[sum(map(ord, n)) % len(PAL)]
fig, axs = plt.subplots(1, 2, figsize=(13, 4.4), dpi=150)
T_F = sys.argv[4] if len(sys.argv) > 4 else "F side, seen from the front"
T_B = sys.argv[5] if len(sys.argv) > 5 else "B side, seen from the back"
for ax, L, title in ((axs[0], pcbnew.F_Cu, T_F), (axs[1], pcbnew.B_Cu, T_B)):
    if EDGE:
        ax.add_patch(Polygon(EDGE, fc="#e8f5e9", ec="black", lw=1))
    else:
        ax.add_patch(Rectangle((X0, Y0), X1 - X0, Y1 - Y0, fc="#e8f5e9", ec="black", lw=1))
    for z in b.Zones():
        if z.IsOnLayer(L):
            for i in range(z.GetFilledPolysList(L).OutlineCount()):
                o = z.GetFilledPolysList(L).Outline(i)
                pts = [(mm(o.CPoint(k).x) - O, -(mm(o.CPoint(k).y) - O)) for k in range(o.PointCount())]
                ax.add_patch(Polygon(pts, fc="#bdbdbd", ec="none", alpha=0.6, zorder=1))
    for f in b.GetFootprints():
        for p in f.Pads():
            if not p.IsOnLayer(L) and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                continue
            x, y = mm(p.GetPosition().x) - O, -(mm(p.GetPosition().y) - O); w, h = mm(p.GetSize().x), mm(p.GetSize().y)
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                ax.add_patch(Circle((x, y), w / 2, fc="white", ec="black", lw=0.6, zorder=5)); continue
            c = col(p.GetNetname())
            if p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:
                ax.add_patch(Circle((x, y), w / 2, fc=c, ec="black", lw=0.4, alpha=0.55, zorder=3))
            elif p.GetShape() == pcbnew.PAD_SHAPE_OVAL:
                ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle=f"round,pad=0,rounding_size={min(w, h) / 2}", fc=c, ec="black", lw=0.4, alpha=0.55, zorder=3))
                ax.add_patch(FancyBboxPatch((x - 0.425, y - 0.3), 0.85, 0.6, boxstyle="round,pad=0,rounding_size=0.3", fc="white", ec="black", lw=0.4, zorder=6))
            else:
                ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=c, ec="black", lw=0.4, alpha=0.55, zorder=3))
            lab = f.GetReference() if f.GetReference() != "J1" else p.GetNumber()
            if f.GetReference().startswith("P") or (f.GetReference() == "J1" and p.GetNumber() not in ("S", "")):
                ax.text(x, y, lab, fontsize=4.5 if f.GetReference() == "J1" else 6, ha="center", va="center", zorder=8, rotation=90 if f.GetReference() == "J1" else 0)
            elif f.GetReference() in ("D1", "U1"):
                ax.text(x, y, f"{f.GetReference()}.{p.GetNumber()}", fontsize=4, ha="center", va="center", zorder=8)
    for t in b.GetTracks():
        n = t.GetNetname()
        if t.GetClass() == "PCB_VIA":
            x, y = mm(t.GetPosition().x) - O, -(mm(t.GetPosition().y) - O)
            ax.add_patch(Circle((x, y), mm(t.GetWidth()) / 2, fc=col(n), ec="black", lw=0.4, zorder=7))
            ax.add_patch(Circle((x, y), mm(t.GetDrillValue()) / 2, fc="white", ec="none", zorder=7))
        elif t.GetLayer() == L:
            ax.plot([mm(t.GetStart().x) - O, mm(t.GetEnd().x) - O], [-(mm(t.GetStart().y) - O), -(mm(t.GetEnd().y) - O)], color=col(n),
                    lw=mm(t.GetWidth()) * 72 / 25.4 * fig.dpi / 150 * 4.2, solid_capstyle="round", zorder=4)
    ax.set_xlim(X0 - 0.3, X1 + 0.3); ax.set_ylim(Y0 - 0.3, Y1 + 0.3); ax.set_aspect("equal"); ax.set_title(title, fontsize=9, loc="left"); ax.grid(alpha=0.15)
    if L == pcbnew.B_Cu:
        ax.invert_xaxis()
used = sorted({p.GetNetname() for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() and not p.GetNetname().startswith("unconnected")})
h = [plt.Line2D([], [], color=col(n), lw=3, label=n) for n in used]
fig.legend(handles=h, loc="lower center", ncol=min(len(h), 10), fontsize=8, frameon=False)
if TITLE:
    fig.suptitle(TITLE, fontsize=10, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0.06, 1, 0.95 if TITLE else 1)); fig.savefig(out)
print("wrote", out)
