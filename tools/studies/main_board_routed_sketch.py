"""The routed main board (9 Nov 2026, step 3 of the main-board pass): tracks coloured by layer, one panel per signal layer pair, and
what KiCad's DRC still reports (red lines = not joined, red rings = rule errors).
  /usr/bin/python3 tools/studies/main_board_routed_sketch.py <board.kicad_pcb> <drc.rpt> <out.png>"""
import sys, re
import pcbnew
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ORIGIN = (100.0, 100.0)
COL = {pcbnew.F_Cu: "#c62828", pcbnew.In2_Cu: "#2e7d32", pcbnew.In3_Cu: "#f9a825", pcbnew.B_Cu: "#1565c0"}
NAME = {pcbnew.F_Cu: "front", pcbnew.In2_Cu: "In2", pcbnew.In3_Cu: "In3", pcbnew.B_Cu: "back"}


def xy(v):
    return pcbnew.ToMM(v.x) - ORIGIN[0], -(pcbnew.ToMM(v.y) - ORIGIN[1])


b = pcbnew.LoadBoard(sys.argv[1])
txt = open(sys.argv[2]).read()
edges = [(xy(d.GetStart()), xy(d.GetEnd())) for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
pads = [(xy(p.GetPosition()), p.IsOnLayer(pcbnew.F_Cu), p.IsOnLayer(pcbnew.B_Cu)) for f in b.GetFootprints() for p in f.Pads()]
segs = {k: [] for k in COL}; vias = []; length = {k: 0.0 for k in COL}
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        vias.append(xy(t.GetPosition())); continue
    if t.GetLayer() in segs:
        segs[t.GetLayer()].append((xy(t.GetStart()), xy(t.GetEnd()), pcbnew.ToMM(t.GetWidth())))
        length[t.GetLayer()] += pcbnew.ToMM(t.GetLength())
unc = [tuple(float(v) for v in m.groups()) for m in
       re.finditer(r"\[unconnected_items\][^\n]*\n[^\n]*\n\s*@\(([\d.]+) mm, ([\d.]+) mm\)[^\n]*\n\s*@\(([\d.]+) mm, ([\d.]+) mm\)", txt)]
errs = [(float(m.group(2)), float(m.group(3)), m.group(1)) for m in
        re.finditer(r"^\[(\w+)\][^\n]*\n[^\n]*\n\s*@\(([\d.]+) mm, ([\d.]+) mm\)", txt, re.M)
        if m.group(1) not in ("unconnected_items", "track_dangling", "via_dangling", "lib_footprint_issues")]
stubs = len(re.findall(r"^\[(track_dangling|via_dangling)\]", txt, re.M))
nv = re.search(r"\*\* Found (\d+) DRC violations", txt); nu = re.search(r"\*\* Found (\d+) unconnected pads", txt)


def base(ax, title):
    for (x0, y0), (x1, y1) in edges:
        ax.plot([x0, x1], [y0, y1], color="#33691e", lw=0.6)
    ax.set_aspect("equal"); ax.axis("off"); ax.set_title(title, fontsize=11.5, loc="left", weight="bold")


fig = plt.figure(figsize=(17, 11.5), dpi=120)
panels = [((pcbnew.F_Cu,), "Front (with the front pads)"), ((pcbnew.In2_Cu,), "In2 (signal, between the planes)"),
          ((pcbnew.In3_Cu,), "In3 (signal; the flex's analog lines)"), ((pcbnew.B_Cu,), "Back (with the back pads)")]
for k, (lays, title) in enumerate(panels):
    ax = fig.add_axes([0.005 + k * 0.248, 0.1, 0.24, 0.78]); base(ax, title)
    for (x, y), on_f, on_b in pads:
        if (pcbnew.F_Cu in lays and on_f) or (pcbnew.B_Cu in lays and on_b):
            ax.plot(x, y, "s", ms=0.9, color="#757575")
    for lay in lays:
        for (x0, y0), (x1, y1), w in segs[lay]:
            ax.plot([x0, x1], [y0, y1], color=COL[lay], lw=max(0.35, w * 2.2), alpha=0.9, solid_capstyle="round")
    for x, y in vias:
        ax.plot(x, y, "o", ms=0.9, mfc="none", mec="#424242", mew=0.25)
    for x0, y0, x1, y1 in unc:
        ax.plot([x0 - ORIGIN[0], x1 - ORIGIN[0]], [-(y0 - ORIGIN[1]), -(y1 - ORIGIN[1])], color="red", lw=1.4)
    for x, y, _kind in errs:
        ax.plot(x - ORIGIN[0], -(y - ORIGIN[1]), "o", ms=7, mfc="none", mec="red", mew=1.2)
    ax.text(0.02, -0.01, f"{length[lays[0]]:.0f} mm of track", transform=ax.transAxes, fontsize=9.5, va="top")
u = int(nu.group(1)) if nu else -1; v = len(errs)
fig.text(0.005, 0.975, "Main board, routed on 6 layers", fontsize=16, weight="bold", va="top")
fig.text(0.005, 0.945, f"KiCad DRC: {u} not joined (red lines), {v} rule errors; {stubs} unused stub ends (cleared at the end); "
         f"{len(vias)} vias. In1 and In4 are the two unbroken ground planes (not drawn). Seen from the front.", fontsize=11, va="top")
fig.text(0.005, 0.045, "Every ground pad has its own via to the planes. The link flex's lines run as laid ribbons: up the right side on In3 "
         "(analog) and the back (USB; on the finished board the slow I2C, MIDI and interrupt lines leave it near the flex pads and go "
         "round on the inner layers), up the left on the front (SPI). VSYS (15 V) on In2 from the post to board L.", fontsize=10.2, va="top", wrap=True)
fig.savefig(sys.argv[3])
print(u, v, len(vias), {NAME[k]: round(x) for k, x in length.items()})
