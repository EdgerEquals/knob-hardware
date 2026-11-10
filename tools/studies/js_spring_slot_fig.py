"""10 Nov sweep, question 1: the joystick hold-down spring holes on main board v2. The springs sit at y ±1.5 from the joystick's
axis (moved there on 2 Nov for the press-spring grub holes, which went in v0.8), so each side's two Ø3.4 holes merge into one
figure-8 cut-out. Plan of both sides, from the front, with the copper round them and where the holes would be at y ±2.0.
  /usr/bin/python3 tools/studies/js_spring_slot_fig.py <board.kicad_pcb> <out.png>"""
import sys, math
import pcbnew
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

b = pcbnew.LoadBoard(sys.argv[1]); T = pcbnew.ToMM
COL = {pcbnew.F_Cu: "#c62828", pcbnew.In2_Cu: "#2e7d32", pcbnew.In3_Cu: "#f9a825", pcbnew.B_Cu: "#1565c0"}
JY = 40.63   # the joystick's axis, panel y
fig, axs = plt.subplots(1, 2, figsize=(13, 7.2), dpi=120)
for ax, sx in zip(axs, (-1, 1)):
    cx, cy = 100 + sx * 12.5, 100 - JY
    box = (cx - 4.5, cx + 4.5, cy - 4.5, cy + 4.5)
    inside = lambda x, y: box[0] < x < box[1] and box[2] < y < box[3]
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            if inside(T(p.x), T(p.y)):
                ax.add_patch(Circle((T(p.x), T(p.y)), T(t.GetWidth()) / 2, fc="white", ec="#424242", lw=0.6, zorder=3))
            continue
        if t.GetLayer() not in COL:
            continue
        a, e = t.GetStart(), t.GetEnd()
        if inside(T(a.x), T(a.y)) or inside(T(e.x), T(e.y)):
            ax.plot([T(a.x), T(e.x)], [T(a.y), T(e.y)], color=COL[t.GetLayer()], lw=T(t.GetWidth()) * 30, alpha=0.5, solid_capstyle="round")
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts:
            a, e = d.GetStart(), d.GetEnd()
            if inside(T(a.x), T(a.y)):
                ax.plot([T(a.x), T(e.x)], [T(a.y), T(e.y)], color="black", lw=1.6, zorder=4)
    for dy in (-1.5, 1.5):
        ax.add_patch(Circle((cx, cy - dy), 1.0, fc="#9e9e9e", ec="#424242", lw=0.8, alpha=0.8, zorder=5))
    for dy in (-2.0, 2.0):
        ax.add_patch(Circle((cx, cy - dy), 1.7, fc="none", ec="#7b1fa2", lw=1.4, ls="--", zorder=6))
    ax.set_xlim(box[0], box[1]); ax.set_ylim(box[3], box[2]); ax.set_aspect("equal")
    ax.set_title(f"{'Left' if sx < 0 else 'Right'} pair (x {sx * 12.5:+.1f})", loc="left", fontsize=12, weight="bold")
    ax.set_xticks([]); ax.set_yticks([])
fig.text(0.01, 0.97, "Joystick hold-down springs on the main board: one figure-8 cut-out per side", fontsize=15, weight="bold", va="top")
fig.text(0.01, 0.925, "Black: the cut-out as routed (two Ø3.4 holes 3.0 apart, a 1.6 neck). Grey: the springs (Ø2). Purple dashed: the "
         "holes at y ±2.0, two separate holes with a 0.6 web.\nCopper: front red, In2 green, In3 yellow, back blue, vias white. "
         "At ±2.0 the holes would cut through tracks and a pad that are routed there now (USB D+, MOSI, CAN_STBY, C14).",
         fontsize=10.5, va="top")
fig.savefig(sys.argv[2])
