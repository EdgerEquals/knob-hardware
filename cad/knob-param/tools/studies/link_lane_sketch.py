# Step 2, decision 6 (4 Nov evening): where the link flex rises from the main board's strip under the clear OLED to its ZIF on the jack
# power board, past the two posts (v0.35). Front-view schematic from the params (no build).
#   link-lane-sketch.png  1: v0.35: the link flex (11 wide ZIF at x 10..21) has to rise through the right post; 2: proposal: the right post
#                         moves in to x 8, the link flex gets the lane x 9.5..18.5 (9 wide), the two posts carry 15 V and GND.
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/link_lane_sketch.py <out dir>
import os, sys
sys.path.insert(0, ".")
OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    from PIL import Image
    from knobparam.common import model
    D = model.derive(model.default_params())
    oy0 = D["clear_oled_xy"][1] - D["clear_oled"][1] / 2; ow = D["clear_oled"][0] / 2
    y0 = D["jack_bot_y"]; zy = y0 + D["zif_y_off"]
    k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    outs = []

    def R(ax, a, b, c, d, fc="none", ec="none", al=1.0, ls="-", lw=1.0, hatch=None):
        ax.add_patch(Rectangle((a, c), b - a, d - c, fc=fc, ec=ec, alpha=al, ls=ls, lw=lw, hatch=hatch))

    def base(ax):
        R(ax, -D["pcb_x1"], D["pcb_x1"], D["pcb_y0"], -40.0, "#2e7d32", al=0.35)
        for x, y in D["corners"][:2]:
            ax.add_patch(Circle((x, y), D["notch_r"], fc="white", ec="none"))
        R(ax, -ow, ow, oy0, -40.0, "#90caf9", al=0.9)
        R(ax, -D["pcb_x1"], D["pcb_x1"], D["pcb_y0"], D["pcb_y0"] + D["ledge_w"], "#b0bec5", al=0.8)
        R(ax, -6.25, 6.25, oy0 - 0.6, oy0, "#e65100", al=0.8)                                   # OLED flex rising
        w, dd, _h, xc = D["zif_oled"]
        R(ax, xc - w / 2, xc + w / 2, zy, zy + dd, "none", "#424242", ls="--", lw=1.2)          # OLED ZIF (on the power board, above)

    for n, (posts, lane, zl, title) in enumerate((
            (D["jb_post_xy"], (10.0, 21.0), (10.0, 21.0), "1. v0.35: the link flex (11 wide) would rise through the right post"),
            (((-16.5, -50.45), (8.0, -50.45)), (9.5, 18.5), (9.1, 19.1), "2. Proposal: right post in to x 8; link lane x 9.5-18.5; posts = 15 V + GND"))):
        fig = plt.figure(figsize=(8.6, 5.2), dpi=125); ax = fig.add_axes([0.08, 0.12, 0.9, 0.78])
        base(ax)
        R(ax, lane[0], lane[1], oy0 - 2.6, oy0 - 0.15, "#6d4c41", al=0.7)                       # link flex rising from its pads
        R(ax, zl[0], zl[1], zy, zy + 5.5, "none", "#6d4c41", ls="--", lw=1.2)                    # link ZIF above
        for x, y in posts:
            ax.add_patch(Circle((x, y), D["jb_post_d"] / 2, fc="#c8a951", ec="#6d4c41", lw=0.8))
        ax.annotate("the OLED's flex (12.5 wide [S]) rising to its ZIF (dashed, on the power board above)", (0.0, oy0 - 0.3), (-23.0, -40.8), **k)
        ax.annotate("link flex rising from its pads in the strip (brown) to its ZIF (dashed)", ((lane[0] + lane[1]) / 2, oy0 - 1.5),
                    (-6.0, -55.7), **k)
        ax.annotate("posts", posts[0], (-23.0, -55.7), **k)
        ax.set_xlim(-24, 24); ax.set_ylim(-56.5, -40); ax.set_aspect("equal"); ax.grid(alpha=0.2)
        ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm)")
        ax.set_title(title, fontsize=10, loc="left")
        f = os.path.join(OUT, f"_ll_{n}.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    ims = [Image.open(f) for f in outs]
    W = max(i.width for i in ims)
    cv = Image.new("RGB", (W, sum(i.height for i in ims)), "white"); y = 0
    for i in ims:
        cv.paste(i, (0, y)); y += i.height
    out = os.path.join(OUT, "link-lane-sketch.png"); cv.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out)


if __name__ == "__main__":
    main()
