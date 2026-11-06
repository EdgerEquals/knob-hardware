# Step 2 boards, jack power board (6 Nov): the Ø2 brass posts in the board's ears. The ears are ±1.3 round each post and reach only
# 1.05 below its centre (0.3 above the shell's bottom ledge), so a Ø2 hole would leave 0.0 of board under it. Q24, two ways:
#   A  the post steps down to a Ø1.0 pin through the ear (plated Ø1.15 hole, Ø1.6 pad), the board sitting on the Ø2 shoulder
#   B  the post stays Ø2 and sits in a plated U-slot open to the ear's bottom edge, soldered along the slot
#   post-ear-sketch.png
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/post_ear_sketch.py <out dir>
import os, sys
sys.path.insert(0, ".")
OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle, Wedge, Polygon
    from knobparam.common import model
    D = model.derive(model.default_params())
    px, py = D["jb_post_xy"][1]; r = D["jb_post_d"] / 2; hx, ty = D["jb_tab"]; by0 = D["jack_bot_y"]
    ly = D["pcb_y0"] + D["ledge_w"]
    fig, axs = plt.subplots(1, 3, figsize=(13.0, 4.2), dpi=130)
    for k, (ax, title) in enumerate(zip(axs, ("now: a Ø2 hole has no board under it",
                                              "A: Ø1.0 pin on a Ø2 shoulder (plated Ø1.15 hole, Ø1.6 pad)",
                                              "B: Ø2 post in a plated U-slot open to the edge"))):
        board = [(px - 4.0, by0 + 2.0), (px - 4.0, by0), (px - hx, by0), (px - hx, ty), (px + hx, ty), (px + hx, by0), (px + 4.0, by0),
                 (px + 4.0, by0 + 2.0)]
        ax.add_patch(Polygon(board, closed=True, fc="#2e7d32", ec="black", lw=0.8, alpha=0.85))
        ax.axhline(ly, color="#6d4c41", lw=1.2, ls="--")
        ax.text(px - 3.9, ly - 0.1, "shell's bottom ledge (0.3 below the ear)", fontsize=6.5, ha="left", va="top", color="#6d4c41")
        if k == 0:
            ax.add_patch(Circle((px, py), r, fc="#ffb300", ec="#e65100", lw=0.8))
            ax.annotate("0.05 of board\nbelow the post", (px + 0.2, ty + 0.03), (px + 1.6, py - 0.3), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.6))
        elif k == 1:
            ax.add_patch(Circle((px, py), r, fc="none", ec="#e65100", lw=0.8, ls="--"))
            ax.add_patch(Circle((px, py), 0.8, fc="#fdd835", ec="#827717", lw=0.6))
            ax.add_patch(Circle((px, py), 0.575, fc="white", ec="black", lw=0.5))
            ax.add_patch(Circle((px, py), 0.5, fc="#ffb300", ec="#e65100", lw=0.6))
            ax.annotate("pad 0.25 from\nthe ear's edges", (px + 0.2, py - 0.78), (px + 1.6, py - 0.3), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.6))
            ax.text(px - 3.9, by0 + 1.7, "dashed: the Ø2 shoulder under the board", fontsize=6.5, va="top")
        else:
            slot = [(px - 1.05, py), (px - 1.05, ty - 0.01), (px + 1.05, ty - 0.01), (px + 1.05, py)]
            ax.add_patch(Polygon(slot, closed=True, fc="white", ec="none"))
            ax.add_patch(Wedge((px, py), 1.05, 0, 180, fc="white", ec="none"))
            ax.add_patch(Wedge((px, py), 1.3, 0, 180, width=0.25, fc="#fdd835", ec="#827717", lw=0.5))
            ax.add_patch(Circle((px, py), r, fc="#ffb300", ec="#e65100", lw=0.8))
            ax.annotate("plating only round the top half;\nthe ear's legs 0.25 wide", (px + 1.18, ty + 0.5), (px + 1.5, py + 0.9), fontsize=7,
                        arrowprops=dict(arrowstyle="->", lw=0.6))
        ax.set_xlim(px - 4.0, px + 4.0); ax.set_ylim(ly - 0.9, by0 + 2.0); ax.set_aspect("equal")
        ax.set_title(title, fontsize=8.5, loc="left"); ax.grid(alpha=0.15)
        ax.set_xlabel("x (mm, panel)")
    axs[0].set_ylabel("y (mm, panel)")
    fig.suptitle(f"The right post (VSYS) in the power board's ear, from the front: post Ø{D['jb_post_d']:g} at ({px:g}, {py:.2f}); "
                 f"ear ±{hx:g} down to y {ty:g}", fontsize=9.5)
    fig.tight_layout()
    out = os.path.join(OUT, "post-ear-sketch.png"); fig.savefig(out); print("wrote", out)


if __name__ == "__main__":
    main()
