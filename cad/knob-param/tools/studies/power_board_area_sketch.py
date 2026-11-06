# Step 2 boards, jack power board (6 Nov): the parts don't fit. Left: the area the parts' footprints need (KiCad courtyards, all
# ~125 passives counted) against the free board on both faces. Right: a side section through the jack unit with option A, a second
# board under the power board (the 17 mm of air there is hidden behind the jacks; nothing else in the model is in it).
#   power-board-area-sketch.png
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/power_board_area_sketch.py <out dir> [area.json]
import os, sys, json
sys.path.insert(0, ".")
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
AREA = sys.argv[2] if len(sys.argv) > 2 else None


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
    from knobparam.common import model
    D = model.derive(model.default_params())
    a = json.load(open(AREA)) if AREA else None
    fig = plt.figure(figsize=(13.5, 6.4), dpi=130)
    ax = fig.add_axes([0.10, 0.12, 0.33, 0.76])
    # --- left: area bars ---
    need = a["need"] if a else {}
    free = a["free"] if a else {}
    cols = {"supply": "#ef9a9a", "jack circuits": "#90caf9", "digital": "#c5e1a5", "OLED": "#ffe082", "passives": "#d7ccc8"}
    y = 0
    b0 = 0
    for k, v in need.items():
        ax.barh(1, v, left=b0, color=cols.get(k, "#bdbdbd"), ec="black", lw=0.5)
        if v > 45:
            ax.text(b0 + v / 2, 1, f"{k}\n{v:.0f}", ha="center", va="center", fontsize=7)
        b0 += v
    ax.text(b0 + 15, 1, f"{b0:.0f} mm²", va="center", fontsize=8)
    f0 = 0
    for k, v in free.items():
        ax.barh(0, v, left=f0, color="#e8f5e9", ec="black", lw=0.5)
        ax.text(f0 + v / 2, 0, f"{k}\n{v:.0f}", ha="center", va="center", fontsize=7)
        f0 += v
    ax.text(f0 + 15, 0, f"{f0:.0f} mm²: {b0 / f0 * 100:.0f} % full", va="center", fontsize=8)
    if a:
        ax.axvline(b0 / 0.65, color="#c62828", ls="--", lw=1.0)
        ax.text(b0 / 0.65 - 10, -1.75, f"≈{b0 / 0.65:.0f} mm² of board: a 4-layer board\nlike this routes at about 65 % full", ha="right", va="bottom", fontsize=7, color="#c62828")
        f2 = a.get("free_two_boards")
        if f2:
            ax.barh(-1.15, f2, color="#c8e6c9", ec="black", lw=0.5)
            ax.text(f2 / 2, -1.15, f"{f2:.0f} mm² free: {b0 / f2 * 100:.0f} % full", ha="center", va="center", fontsize=8)
    ax.set_yticks([1, 0, -1.15]); ax.set_yticklabels(["parts'\nfootprints", "free on the\npower board", "option A:\nwith a 2nd board"], fontsize=8)
    ax.set_xlim(0, 1500); ax.set_ylim(-2.3, 1.6); ax.set_xlabel("mm²")
    ax.set_title("Footprint area: needed vs free", fontsize=10, loc="left")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    # --- right: side section (y up the panel, z toward the faceplate) ---
    bx = fig.add_axes([0.50, 0.08, 0.48, 0.84])
    by0, by1 = D["jack_bot_y"], D["jack_top_y"]
    def box(z0, z1, y0, y1, fc, ec="black", lw=0.7, ls="-", label=None, fs=7, alpha=1.0):
        bx.add_patch(Rectangle((z0, y0), z1 - z0, y1 - y0, fc=fc, ec=ec, lw=lw, ls=ls, alpha=alpha))
        if label:
            bx.text((z0 + z1) / 2, (y0 + y1) / 2, label, ha="center", va="center", fontsize=fs, rotation=90)
    zf0 = D["z_fp1"] - D["plate_t"]
    box(zf0, D["z_fp1"], -57, -30, "#cfd8dc", label="faceplate")
    box(D["jack_depth_z0"], zf0, by0, by1, "#9e9e9e", label="jack body")
    box(D["jb_z0"], D["jb_z1"], by0, by1, "#2e7d32", label="")
    bx.text(D["jb_z1"] + 0.2, by1 + 0.8, "jack board", fontsize=7, rotation=0)
    box(D["jb_z0"] - 4.9, D["jb_z0"], -46.9, -39.2, "#bdbdbd", label="2x6 stacks")
    box(D["jb2_z0"], D["jb2_z1"], by0, by1, "#1b5e20")
    bx.text(D["jb2_z1"] + 0.2, by1 + 0.8, "power board (A)", fontsize=7)
    bx.add_patch(Rectangle((D["jb2_z0"], D["jb_tab"][1]), D["jb2_t"], by0 - D["jb_tab"][1], fc="#1b5e20", ec="black", lw=0.7))
    zb1 = D["jb2_z0"] - 4.9; zb0 = zb1 - 1.6
    box(zb1, D["jb2_z0"], -46.9, -39.2, "#e0e0e0", ls="--", label="2nd stacks")
    box(zb0, zb1, by0, by1, "#43a047", ec="#c62828", lw=1.4)
    bx.text(zb0 - 0.3, by1 + 0.8, "option A: 2nd board (B)", fontsize=7.5, color="#c62828", ha="right")
    box(zb0 - 2.0, zb0, by0 + 0.75, by0 + 0.75 + 5.2, "#9e9e9e", label="ZIFs", fs=6)
    box(0.0, D["clear_oled"][2], -48.8, -30, "#b3e5fc", label="clear OLED", fs=6)
    box(-1.6, 0.0, -56, -30, "#558b2f", label="main board", fs=6)
    bx.add_patch(Rectangle((0.62, -49.0), zb0 - 2.0 - 0.62 + 1.0, 0.15, fc="#ffb74d", ec="#e65100", lw=0.6))
    bx.text(2.0, -48.6, "the flexes rise to the ZIFs", fontsize=6.5, va="bottom")
    bx.add_patch(Rectangle((0.02, -51.45), D["jb2_z0"] - 0.02, 2.0, fc="#ffb300", ec="#e65100", lw=0.6, alpha=0.6))
    bx.text(2.0, -51.8, "Ø2 posts, past B's bottom edge, to A's ears", fontsize=6.5, va="top")
    bx.annotate("", xy=(zb0 - 2.0, -44), xytext=(D["clear_oled"][2], -44), arrowprops=dict(arrowstyle="<->", lw=0.6))
    bx.text((zb0 - 2.0 + 1.25) / 2, -43.6, f"{zb0 - 2.0 - D['clear_oled'][2]:.1f} air", fontsize=7, ha="center")
    bx.set_xlim(-3, 40); bx.set_ylim(-57.5, -33)
    bx.set_xlabel("z (mm, toward the faceplate)"); bx.set_ylabel("y (mm, panel)")
    bx.set_title("Side section through the jack unit (x ≈ -11): option A", fontsize=10, loc="left")
    bx.grid(alpha=0.15)
    out = os.path.join(OUT, "power-board-area-sketch.png"); fig.savefig(out); print("wrote", out)


if __name__ == "__main__":
    main()
