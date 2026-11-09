"""The crowded spot right of the H743 (9 Nov 2026, main board routing): every layer's copper over each other, the pads, and the
connections still not joined (red, named), for the question on how to finish them.
  /usr/bin/python3 tools/studies/main_board_crowded_sketch.py <board.kicad_pcb> <drc.rpt> <out.png> [x0 x1 y0 y1 (KiCad mm)]"""
import sys, re
import pcbnew
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

COL = {pcbnew.F_Cu: "#c62828", pcbnew.In2_Cu: "#2e7d32", pcbnew.In3_Cu: "#f9a825", pcbnew.B_Cu: "#1565c0"}
NAME = {pcbnew.F_Cu: "front", pcbnew.In2_Cu: "In2", pcbnew.In3_Cu: "In3", pcbnew.B_Cu: "back"}
b = pcbnew.LoadBoard(sys.argv[1]); txt = open(sys.argv[2]).read()
x0, x1, y0, y1 = [float(v) for v in sys.argv[4:8]] if len(sys.argv) > 7 else (99.0, 123.0, 52.0, 78.0)
T = lambda v: (pcbnew.ToMM(v.x), pcbnew.ToMM(v.y))
inside = lambda x, y: x0 - 1 < x < x1 + 1 and y0 - 1 < y < y1 + 1
fig = plt.figure(figsize=(13, 13.5), dpi=120)
ax = fig.add_axes([0.03, 0.06, 0.94, 0.86])
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts:
        (ax_, ay_), (bx_, by_) = T(d.GetStart()), T(d.GetEnd())
        if inside(ax_, ay_) or inside(bx_, by_):
            ax.plot([ax_, bx_], [ay_, by_], color="#33691e", lw=1.2)
for f in b.GetFootprints():
    for p in f.Pads():
        x, y = T(p.GetPosition())
        if not inside(x, y) or not (p.IsOnLayer(pcbnew.F_Cu) or p.IsOnLayer(pcbnew.B_Cu)):
            continue
        bb = p.GetBoundingBox(); w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
        front = p.IsOnLayer(pcbnew.F_Cu)
        ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc="#9e9e9e" if front else "none", ec="#616161", lw=0.5, alpha=0.6))
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        x, y = T(t.GetPosition())
        if inside(x, y):
            ax.add_patch(Circle((x, y), pcbnew.ToMM(t.GetWidth()) / 2, fc="white", ec="#424242", lw=0.6, zorder=3))
        continue
    if t.GetLayer() not in COL:
        continue
    (ax_, ay_), (bx_, by_) = T(t.GetStart()), T(t.GetEnd())
    if inside(ax_, ay_) or inside(bx_, by_):
        ax.plot([ax_, bx_], [ay_, by_], color=COL[t.GetLayer()], lw=pcbnew.ToMM(t.GetWidth()) * 24, alpha=0.55, solid_capstyle="round")
for m in re.finditer(r"\[unconnected_items\][^\n]*\n[^\n]*\n\s*@\(([\d.]+) mm, ([\d.]+) mm\): [^\[]*\[([^\]]+)\][^\n]*\n\s*@\(([\d.]+) mm, ([\d.]+) mm\)", txt):
    ax_, ay_, net, bx_, by_ = float(m.group(1)), float(m.group(2)), m.group(3), float(m.group(4)), float(m.group(5))
    ax.plot([ax_, bx_], [ay_, by_], color="red", lw=2.2, zorder=5)
    mx, my = (ax_ + bx_) / 2, (ay_ + by_) / 2
    if inside(mx, my):
        ax.text(mx, my, net, fontsize=10, color="red", weight="bold", zorder=6, bbox=dict(fc="white", ec="none", alpha=0.75, pad=1))
ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect("equal"); ax.axis("off")
fig.text(0.03, 0.975, "Main board: the last connections, right of the chip", fontsize=15, weight="bold", va="top")
fig.text(0.03, 0.945, "All four signal layers drawn over each other (" + ", ".join(f"{NAME[k]} {c}" for k, c in
         [(k, {"#c62828": "red", "#2e7d32": "green", "#f9a825": "yellow", "#1565c0": "blue"}[v]) for k, v in COL.items()])
         + "), vias white, front pads grey; red lines: still not joined.", fontsize=10.5, va="top")
fig.savefig(sys.argv[3])
