# Step 2 boards, jack power boards (6 Nov): Q25. Even split over two boards, the approved packages leave them 67 % and 73 % full of
# footprints (KiCad courtyards); the annealing placer could not lay them out without overlaps. The same chips in 4x4 QFNs (the three
# TMUX7212 and the TCA9535) bring both boards to about 63 %.
#   package-swap-sketch.png
# Run from cad/knob-param:  python tools/studies/package_swap_sketch.py <out dir>
import os, sys
OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    fig = plt.figure(figsize=(12.5, 4.6), dpi=130)
    ax = fig.add_axes([0.03, 0.12, 0.50, 0.76])
    # courtyards to scale [KiCad library footprints]: TSSOP-16 7.7 x 5.5, WQFN-16 4x4 4.9 x 4.9 (P0.65), TSSOP-24 7.7 x 8.3, VQFN-24 4.9 x 4.9
    items = [("TMUX7212PWR\nTSSOP-16 (x3)", 7.7, 5.5, "#90caf9", 0.0), ("TMUX7212RUMR\nWQFN-16 4x4", 4.9, 4.9, "#1e88e5", 0.0),
             ("TCA9535PWR\nTSSOP-24", 7.7, 8.3, "#c5e1a5", 12.0), ("TCA9535RGER\nVQFN-24 4x4", 4.9, 4.9, "#7cb342", 12.0)]
    x = 0.0
    for i, (nm, w, h, c, yo) in enumerate(items):
        xx = (i % 2) * 10.0
        ax.add_patch(Rectangle((xx, yo), w, h, fc=c, ec="black", lw=0.8))
        ax.text(xx + w / 2, yo + h + 0.4, nm + f"\n{w * h:.0f} mm²", ha="center", va="bottom", fontsize=7.5)
    ax.annotate("", xy=(9.6, 2.7), xytext=(7.9, 2.7), arrowprops=dict(arrowstyle="->", lw=1.0))
    ax.annotate("", xy=(9.6, 16.0), xytext=(7.9, 16.0), arrowprops=dict(arrowstyle="->", lw=1.0))
    ax.set_xlim(-1, 16); ax.set_ylim(-1, 26); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("Same chips, smaller packages (footprints to scale, mm)", fontsize=9.5, loc="left")
    bx = fig.add_axes([0.62, 0.18, 0.35, 0.66])
    rows = [("power board, approved packages", 67), ("lower board, approved packages", 73),
            ("power board, A (QFNs; +12.5 V and 3.3 V moved up)", 64), ("lower board, A", 62)]
    for k, (nm, v) in enumerate(rows):
        bx.barh(len(rows) - k, v, color="#ef9a9a" if v > 65 else "#a5d6a7", ec="black", lw=0.5)
        bx.text(v + 1, len(rows) - k, f"{v} %", va="center", fontsize=8)
    bx.axvline(65, color="#c62828", ls="--", lw=1.0); bx.text(65.5, 0.35, "about where a 4-layer\nboard still routes", fontsize=7, color="#c62828")
    bx.set_yticks(range(len(rows), 0, -1)); bx.set_yticklabels([r[0] for r in rows], fontsize=7.5)
    bx.set_xlim(0, 100); bx.set_xlabel("parts' footprints / free board (%)")
    bx.set_title("How full each board is", fontsize=9.5, loc="left")
    out = os.path.join(OUT, "package-swap-sketch.png"); fig.savefig(out); print("wrote", out)


if __name__ == "__main__":
    main()
