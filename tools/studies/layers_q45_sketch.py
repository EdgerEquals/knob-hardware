"""Q45 picture (8 Nov 2026, main board step 3): the layer count. Draws the two routing trials of the placed main board (make_board.py
--trial 4 / --trial 6: ground fanned out to the In1 plane, the rest by Freerouting 1.9.0), tracks coloured by layer, what was
left unrouted as red lines, with the counts from each trial's DRC report.
  /usr/bin/python3 tools/studies/layers_q45_sketch.py <trial4.kicad_pcb> <trial6.kicad_pcb> <out.png>"""
import sys, re, os
import pcbnew
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ORIGIN = (100.0, 100.0)
COL = {pcbnew.F_Cu: "#c62828", pcbnew.In1_Cu: "#6d4c41", pcbnew.In2_Cu: "#2e7d32", pcbnew.In3_Cu: "#f9a825",
       pcbnew.In4_Cu: "#6a1b9a", pcbnew.B_Cu: "#1565c0"}
NAME = {pcbnew.F_Cu: "front", pcbnew.In1_Cu: "In1", pcbnew.In2_Cu: "In2", pcbnew.In3_Cu: "In3", pcbnew.In4_Cu: "In4",
        pcbnew.B_Cu: "back"}


def xy(v):
    return pcbnew.ToMM(v.x) - ORIGIN[0], -(pcbnew.ToMM(v.y) - ORIGIN[1])


def draw(ax, path, title):
    b = pcbnew.LoadBoard(path)
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts:
            (x0, y0), (x1, y1) = xy(d.GetStart()), xy(d.GetEnd())
            ax.plot([x0, x1], [y0, y1], color="#33691e", lw=0.5)
    for f in b.GetFootprints():
        for p in f.Pads():
            x, y = xy(p.GetPosition())
            ax.plot(x, y, ".", ms=0.8, color="#9e9e9e")
    n_via = 0; length = {}
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            n_via += 1
            x, y = xy(t.GetPosition()); ax.plot(x, y, "o", ms=1.1, mfc="none", mec="#424242", mew=0.3)
            continue
        (x0, y0), (x1, y1) = xy(t.GetStart()), xy(t.GetEnd())
        ax.plot([x0, x1], [y0, y1], color=COL.get(t.GetLayer(), "#000"), lw=0.45, alpha=0.85, solid_capstyle="round")
        length[t.GetLayer()] = length.get(t.GetLayer(), 0.0) + pcbnew.ToMM(t.GetLength())
    rpt = os.path.join(os.path.dirname(path), os.path.basename(path).replace(".kicad_pcb", "_drc.rpt"))
    txt = open(rpt).read() if os.path.exists(rpt) else ""
    nv = re.search(r"\*\* Found (\d+) DRC violations", txt); nu = re.search(r"\*\* Found (\d+) unconnected pads", txt)
    for m in re.finditer(r"\[unconnected_items\][^\n]*\n[^\n]*\n\s*@\(([\d.]+) mm, ([\d.]+) mm\)[^\n]*\n\s*@\(([\d.]+) mm, ([\d.]+) mm\)", txt):
        x0, y0, x1, y1 = (float(v) for v in m.groups())
        ax.plot([x0 - ORIGIN[0], x1 - ORIGIN[0]], [-(y0 - ORIGIN[1]), -(y1 - ORIGIN[1])], color="red", lw=1.2)
    ax.set_aspect("equal"); ax.axis("off")
    u = int(nu.group(1)) if nu else -1; v = int(nv.group(1)) if nv else -1
    ax.set_title(f"{title}\n{u} left unrouted, {v} rule errors, {n_via} vias", fontsize=11.5, loc="left", weight="bold")
    return u, v, n_via, length


fig = plt.figure(figsize=(15, 14), dpi=120)
res = []
for k, (path, title) in enumerate(((sys.argv[1], "A: 4 layers"), (sys.argv[2], "B: 6 layers"))):
    ax = fig.add_axes([0.01 + k * 0.5, 0.06, 0.47, 0.84])
    res.append(draw(ax, path, title))
fig.text(0.01, 0.975, "Q45: how many layers for the main board", fontsize=15, weight="bold", va="top")
fig.text(0.01, 0.95, "The placed board routed twice by Freerouting (In1 = an unbroken ground plane in both; ground goes to it by a via "
         "at every pad). Track colour = layer; red = left unrouted.", fontsize=10, va="top")
hand = [plt.Line2D([0], [0], color=c, lw=2) for c in COL.values()]
fig.legend(hand, list(NAME.values()), loc="lower center", ncol=6, fontsize=9.5, frameon=False)
fig.savefig(sys.argv[3])
print(res)
