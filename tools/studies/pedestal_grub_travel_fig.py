"""25 Nov, pedestal grub travel study [Ed 10 Nov, "A: study more travel"]: the grub trims the Hall bar's gap over H3, and the
untrimmed print stack is about ±0.39 RSS, but the grub only moves ±0.25. Section through the grub (now / option A) and the main
board's copper round the key hole (v2.1). Needs pcbnew, so run it with the system Python:
  /usr/bin/python3 tools/studies/pedestal_grub_travel_fig.py <out.png>   (from the repo root)"""
import os, sys, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Wedge
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "..", "cad", "knob-param", "knobparam", "electronics", "kicad", "knob-main-pcb", "v2", "kicad",
                   "knob-main-pcb.kicad_pcb")
PT, BT = 3.5, 1.6                    # cradle plate, main board (base_drive / interface params)
BLK_R, BLK_TOP = (12.55, 14.45), 5.15  # pedestal block r span (sp_ped), top (train seat)
POCKET_C = 0.1                       # sp_ped_clear
NEED = 0.39                          # untrimmed stack, RSS [A] (base_drive/params.py sp_grub)
ANG = 173.0                          # panel angle of the grub (mechanism 263°)
CASES = [  # title, grub r, pocket depth, block lift, grub length, key hole Ø, travel
    ("Now (v0.58): ±0.25", 13.5, 1.5, 0.25, 2.0, 1.6, 0.25),
    ("Option A: ±0.50", 13.1, 2.0, 0.50, 3.0, 2.4, 0.50),
]
C = dict(pcb="#2e7d32", plate="#b0bec5", blk="#8d6e63", grub="#212121", thread="#78909c")


def section(ax, title, gr, pocket, lift, gl, hole, a):
    zf = PT - pocket; zb = zf + lift; zg = zb - gl
    # board with the key hole
    ax.add_patch(Rectangle((8.8, -BT), gr - hole / 2 - 8.8, BT, fc=C["pcb"], ec="none", alpha=0.85))
    ax.add_patch(Rectangle((gr + hole / 2, -BT), 16.5 - gr - hole / 2, BT, fc=C["pcb"], ec="none", alpha=0.85))
    # plate: below the floor (thread), the pocket walls either side
    p0, p1 = BLK_R[0] - POCKET_C, BLK_R[1] + POCKET_C
    ax.add_patch(Rectangle((8.8, 0), gr - 1.0 - 8.8, zf, fc=C["plate"], ec="none"))
    ax.add_patch(Rectangle((gr + 1.0, 0), 16.5 - gr - 1.0, zf, fc=C["plate"], ec="none"))
    ax.add_patch(Rectangle((8.8, zf), p0 - 8.8, PT - zf, fc=C["plate"], ec="none"))
    ax.add_patch(Rectangle((p1, zf), 16.5 - p1, PT - zf, fc=C["plate"], ec="none"))
    for x in (gr - 1.0, gr + 1.0):   # the tapped length
        ax.plot([x, x], [0, zf], color=C["thread"], lw=2.2)
    # block and grub at nominal, the grub's limits dashed
    ax.add_patch(Rectangle((BLK_R[0], zb), BLK_R[1] - BLK_R[0], BLK_TOP - zb, fc=C["blk"], ec="k", lw=0.6, alpha=0.9))
    ax.add_patch(Rectangle((gr - 1.0, zg), 2.0, gl, fc=C["grub"], ec="none"))
    for s, ls in ((-a, (0, (3, 2))), (a, (0, (1, 1.5)))):
        ax.add_patch(Rectangle((gr - 1.0, zg + s), 2.0, gl, fc="none", ec="#e65100", lw=1.0, ls=ls))
    ax.plot([8.8, 16.5], [0, 0], color="k", lw=0.5); ax.plot([8.8, 16.5], [PT, PT], color="k", lw=0.5)
    # the numbers, along the right
    eng_top = zf - max(zg + a, 0.0)
    gtop = PT - zb - a
    bot = zg - a
    txt = (f"pocket {pocket:g} deep, block {lift:g} off its floor\n"
           f"M2 x {gl:g} grub, key hole Ø{hole:g} at r {gr:g}\n\n"
           f"down {a:.2f}: block meets the floor" + (f"; grub to z {bot:+.2f}\n  (inside the board, {bot + BT:.2f} from its back)" if bot < 0 else
                                                    "\n  and the grub meets the board") + "\n"
           f"up {a:.2f}: {eng_top:.2f} of thread left\n"
           f"block guided {PT - zb:.2f} ({gtop:.2f} at the top)")
    ax.text(16.75, 5.6, txt, fontsize=9.6, va="top")
    ax.set_xlim(8.8, 25.0); ax.set_ylim(-2.4, 6.2); ax.set_aspect("equal")
    ax.set_title(title, loc="left", fontsize=12.5, weight="bold", color="#2e7d32" if a >= NEED else "#c62828")
    ax.set_xlabel("r from the knob axis (mm)"); ax.set_ylabel("z (mm; board front 0)")
    ax.text(BLK_R[0] + 0.1, BLK_TOP - 0.45, "block", fontsize=8.5, color="w")
    ax.text(8.95, -1.05, "main board", fontsize=8.5, color="w")
    ax.text(8.95, 0.25, "cradle plate", fontsize=8.5)


def plan(ax):
    b = pcbnew.LoadBoard(PCB); T = pcbnew.ToMM
    x0, y0 = 13.3 * math.cos(math.radians(ANG)), 13.3 * math.sin(math.radians(ANG))
    W = 3.3
    col = {"F.Cu": "#d32f2f", "B.Cu": "#1976d2"}
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            x, y = T(t.GetPosition().x) - 100, 100 - T(t.GetPosition().y)
            if abs(x - x0) < W + 1 and abs(y - y0) < W + 1:
                ax.add_patch(Circle((x, y), T(t.GetWidth()) / 2, fc="#9e9e9e", ec="none"))
            continue
        ax_, ay_ = T(t.GetStart().x) - 100, 100 - T(t.GetStart().y); bx, by = T(t.GetEnd().x) - 100, 100 - T(t.GetEnd().y)
        if min(ax_, bx) > x0 + W + 1 or max(ax_, bx) < x0 - W - 1 or min(ay_, by) > y0 + W + 1 or max(ay_, by) < y0 - W - 1:
            continue
        ln = b.GetLayerName(t.GetLayer())
        ax.plot([ax_, bx], [ay_, by], color=col.get(ln, "#7cb342"), lw=T(t.GetWidth()) * 72 / 25.4 * 7.2, solid_capstyle="round",
                alpha=0.75)
    ax.add_patch(Wedge((0, 0), BLK_R[1], ANG - 13.4, ANG + 13.4, width=BLK_R[1] - BLK_R[0], fc="#8d6e63", alpha=0.18, ec="#8d6e63"))
    for (_, gr, _, _, _, hole, _), ls, c in zip(CASES, ("--", "-"), ("#616161", "#e65100")):
        x, y = gr * math.cos(math.radians(ANG)), gr * math.sin(math.radians(ANG))
        ax.add_patch(Circle((x, y), hole / 2, fc="none", ec=c, lw=1.6, ls=ls))
        ax.add_patch(Circle((x, y), hole / 2 + 0.25, fc="none", ec=c, lw=0.7, ls=":"))
    ax.set_xlim(x0 - W, x0 + W); ax.set_ylim(y0 - W, y0 + W); ax.set_aspect("equal")
    ax.set_title("Main board v2.1 round the key hole", loc="left", fontsize=12.5, weight="bold")
    ax.set_xlabel("x (mm, panel)"); ax.set_ylabel("y (mm, panel)")
    ax.text(x0 - W + 0.15, y0 - W + 0.2, "grey dashed: today's Ø1.6 at r 13.5\norange: option A's Ø2.4 at r 13.1\n"
            "dotted: the 0.25 copper-to-edge rule\nred F.Cu, blue B.Cu, green inner; brown: the block",
            fontsize=8.6, va="bottom", bbox=dict(fc="w", ec="none", alpha=0.85))


fig = plt.figure(figsize=(16, 8.6), dpi=110)
gs = fig.add_gridspec(2, 2, width_ratios=[1.75, 1], hspace=0.38, wspace=0.12)
for i, cs in enumerate(CASES):
    section(fig.add_subplot(gs[i, 0]), *cs)
plan(fig.add_subplot(gs[:, 1]))
fig.text(0.01, 0.985, "Pedestal grub: more travel for the H3 trim", fontsize=15, weight="bold", va="top")
fig.text(0.01, 0.948, f"Needed: about ±{NEED:g} (the untrimmed print stack, RSS). Now the grub moves ±0.25: it stops on the board below and runs "
         "out of thread above, in a 3.5 plate.\nOption A lets the grub run down into the board (key hole opened to Ø2.4, a clearance "
         "hole for the M2), so a longer grub and a deeper pocket fit: ±0.50.\nThe bigger hole moves 0.4 in, to r 13.1, to keep 0.25 from the "
         "OLED tracks on F.Cu; no track moves. Dashed and dotted orange: the grub at its limits.", fontsize=10.5, va="top")
fig.subplots_adjust(top=0.84, bottom=0.07, left=0.05, right=0.98)
fig.savefig(sys.argv[1])
print("wrote", sys.argv[1])
