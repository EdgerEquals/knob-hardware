# Step 2 boards, Q14/Q15 (5 Nov): the real PJ366ST footprint on the jack board, front view of the jack row.
# [S-lib] (KiCad QingPu PJ398SM footprint, which Thonk says the stereo shares; 4ms, GuavTek, westlicht, clacktronics, requencer):
# tip on one side of the axis (+4.92 .. +5.21), ring (-3.35 .. -3.38) and sleeve (-5.715 .. -6.48) on the other; the body outline runs
# -4.5 .. +6.0 from the axis, so the sleeve pin is about 2 mm outside the body. [Ed 15:42 Q14 = B]: plated slots cover every published
# position (slot widths as KiCad: T 1.43, R 1.42, S 1.22; ring 0.35; board outline 0.3 round the pads).
#   jack-pins-sketch.png  1: sleeve pins down at 11.5 pitch: the outer tongues hit the round corner posts and the bottom ledge;
#                         2: proposal A: 11.0 pitch, sleeve pins down, the bottom ledge notched under each tongue.
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/jack_pins_sketch.py <out dir>
import math, os, sys
sys.path.insert(0, ".")
OUT = sys.argv[1] if len(sys.argv) > 1 else "."

T_RANGE, R_RANGE, S_RANGE = (4.92, 5.21), (-3.38, -3.35), (-6.48, -5.715)
W = {"T": 1.43, "R": 1.42, "S": 1.22}
RING, EDGE = 0.35, 0.3
LIT = (-17.525, 17.525, -39.90, -24.58)          # [A] clear OLED lit area 35.05 x 15.32 [S], bottom edge from the jack-row decisions


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
    from PIL import Image
    from knobparam.common import model
    D = model.derive(model.default_params())
    ax_y = D["jack_y"]
    k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    outs = []

    def R(ax, a, b, c, d, fc="none", ec="none", al=1.0, ls="-", lw=1.0, hatch=None, z=1):
        ax.add_patch(Rectangle((a, c), b - a, d - c, fc=fc, ec=ec, alpha=al, ls=ls, lw=lw, hatch=hatch, zorder=z))

    def slot(ax, x, y0, y1, w, z=5):
        L = (y1 - y0) + w
        ax.add_patch(FancyBboxPatch((x - w / 2 - RING, y0 - w / 2 - RING), w + 2 * RING, L + 2 * RING,
                                    boxstyle=f"round,pad=0,rounding_size={w / 2 + RING}", fc="#ffb300", ec="#e65100", lw=0.6, zorder=z))
        ax.add_patch(FancyBboxPatch((x - w / 2, y0 - w / 2), w, L, boxstyle=f"round,pad=0,rounding_size={w / 2}", fc="white",
                                    ec="#5d4037", lw=0.5, zorder=z + 1))

    cases = ((11.5, False, "1. Sleeve pins down at the present 11.5 pitch: the outer tongues hit the corner posts; all four hit the bottom ledge"),
             (11.0, True, "2. Proposal A: 11.0 pitch, sleeve pins down, bottom ledge notched under each tongue"))
    for n, (pitch, notch, title) in enumerate(cases):
        fig = plt.figure(figsize=(9.6, 5.6), dpi=125); ax = fig.add_axes([0.07, 0.11, 0.91, 0.79])
        xs = [-1.5 * pitch, -0.5 * pitch, 0.5 * pitch, 1.5 * pitch]
        R(ax, *LIT, "#90caf9", al=0.5)
        R(ax, -24.0, 24.0, -56.4, D["y_in0"], "#b0bec5", al=0.9)                                  # bottom wall
        for sx in (-1, 1):
            R(ax, sx * 22.75, sx * 24.0, -56.4, -30, "#b0bec5", al=0.9)                          # side walls
        R(ax, -22.75, 22.75, D["pcb_y0"], -51.8, "#78909c", al=0.7)                               # bottom ledge
        if notch:
            for x in xs:
                R(ax, x - 1.26 - 0.3, x + 1.26 + 0.3, -52.45, -51.8, "white")
        R(ax, -6.15, 6.15, -56.4, -51.8, "white")                                                  # USB channel
        R(ax, -6.0, 6.0, -56.4, -50.4, "none", "#6a1b9a", lw=1.2, z=3)                             # USB-C board
        for sx in (-1, 1):
            cx, cy = sx * 21.2, -53.35
            th = math.acos(min(1, (D["post_clip_y"] - cy) / 3.25))
            import numpy as np
            a = np.linspace(-math.pi, math.pi, 200); px = cx + 3.25 * np.cos(a); py = np.minimum(cy + 3.25 * np.sin(a), D["post_clip_y"])
            ax.fill(px, py, color="#546e7a", alpha=0.9, zorder=2)
        for x in xs:
            R(ax, x - 5.0, x + 5.0, ax_y - 4.5, ax_y + 6.0, "#424242", "#212121", al=0.35, lw=0.8, z=3)    # body (real, off-centre)
            ax.add_patch(Circle((x, ax_y), 3.0, fc="none", ec="#212121", lw=0.8, zorder=4))
            # jack board outline round the pins: tongue down to the sleeve pad
            yb = ax_y + S_RANGE[0] - W["S"] / 2 - RING - EDGE
            R(ax, x - W["S"] / 2 - RING - EDGE, x + W["S"] / 2 + RING + EDGE, yb, ax_y - 4.5, "#2e7d32", "#1b5e20", al=0.45, lw=0.8, z=3)
            slot(ax, x, ax_y + T_RANGE[0], ax_y + T_RANGE[1], W["T"])
            slot(ax, x, ax_y + R_RANGE[0], ax_y + R_RANGE[1], W["R"])
            slot(ax, x, ax_y + S_RANGE[0], ax_y + S_RANGE[1], W["S"])
        xo = xs[-1]
        yb = ax_y + S_RANGE[0] - W["S"] / 2 - RING - EDGE
        nx = min(max(21.2, xo - 1.26), xo + 1.26); ny = min(max(-53.35, yb), ax_y)
        g = math.hypot(21.2 - nx, -53.35 - ny) - 3.25
        ax.annotate(f"outer tongue to the corner post: {g:+.2f}", (xo + 1.26, yb), (8.0, -59.0), **k)
        ax.annotate(f"tongue bottom y {yb:.2f}; bottom ledge's inner face y -51.80" + (" (notched to -52.45 under each tongue)" if notch else ": they overlap"),
                    (xs[1], yb), (-25.5, -60.8), **k)
        cov = ax_y + 6.0 - LIT[2]
        ax.annotate(f"clear screen's lit area (blue): jack bodies cover its bottom {cov:.2f} ({100 * (1 - cov / 15.32):.0f}% seen)",
                    (xs[0], ax_y + 6.0), (-25.5, -24.0), **k)
        ax.annotate("tip / ring / sleeve slots (every published position)", (xs[2], ax_y + 5.0), (6.0, -27.0), **k)
        ax.set_xlim(-26, 26); ax.set_ylim(-62, -22.5); ax.set_aspect("equal"); ax.grid(alpha=0.2)
        ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm, up the panel)")
        ax.set_title(title, fontsize=10, loc="left")
        f = os.path.join(OUT, f"_jp_{n}.png"); fig.savefig(f); plt.close(fig); outs.append(f)
    ims = [Image.open(f) for f in outs]
    Wd = max(i.width for i in ims)
    cv = Image.new("RGB", (Wd, sum(i.height for i in ims)), "white"); y = 0
    for i in ims:
        cv.paste(i, (0, y)); y += i.height
    out = os.path.join(OUT, "jack-pins-sketch.png"); cv.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out)


if __name__ == "__main__":
    main()
