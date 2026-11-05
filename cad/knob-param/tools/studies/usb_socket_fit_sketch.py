# Step 2 boards, after the parts search (5 Nov): the real vertical 16-pin USB-C socket on the USB-C board.
# Land pattern [S-lib, 4 sources; e.g. SHOU HAN TYPE-C 16P LTH6.8, LCSC C5187468]: shell legs through plated slots at (±2.40, ±2.15)
# from the socket centre, pads 1.35 x 1.10; locating posts Ø0.40 at (±3.75, 0) (holes ~Ø0.8); 16 SMT signal pads on the front face.
# Spring contacts: Harwin P70-5100045 [S-dist], pad Ø1.20, body about Ø1.03.
#   usb-socket-fit-sketch.png  1: v0.37 as modelled with the real footprint (board 5.5 tall): the leg pads reach the board edges and the
#   upper legs land under two contacts; 2: proposal: socket and board 0.25 up, board 6.0 tall, the 8 contacts laid round the legs and
#   posts, the TVS and ESD between the lower legs; the jacks 0.25 up so the board keeps 0.75 to them.
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/usb_socket_fit_sketch.py <out dir>
import os, sys
sys.path.insert(0, ".")
OUT = sys.argv[1] if len(sys.argv) > 1 else "."

LEGS = [(-2.40, -2.15), (2.40, -2.15), (-2.40, 2.15), (2.40, 2.15)]
LEG_PAD = (1.35, 1.10)
POSTS = [(-3.75, 0.0), (3.75, 0.0)]
POST_HOLE = 0.8


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    from PIL import Image
    from knobparam.common import model
    D = model.derive(model.default_params())
    bw = D["usb_board"][0]; x0, x1 = -bw / 2, bw / 2
    ky = D["y_in0"] - D["usb_key_gap"]
    jb = D["jack_bot_y"]
    k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    outs = []

    def R(ax, a, b, c, d, fc="none", ec="none", al=1.0, ls="-", lw=1.0, hatch=None, z=1):
        ax.add_patch(Rectangle((a, c), b - a, d - c, fc=fc, ec=ec, alpha=al, ls=ls, lw=lw, hatch=hatch, zorder=z))

    cases = (
        dict(title="1. v0.37 as modelled, with the real socket's footprint", cy=D["usb_xy"][1], by0=D["usb_board_y0"], by1=D["usb_board_y1"],
             jb=jb, cts=list(D["usb_pwr_contacts"]), prot=[(-3.2, -1.6, -56.0, -55.0, "TVS"), (1.6, 3.2, -56.1, -54.5, "ESD")]),
        dict(title="2. Proposal: socket and board 0.25 up, board 6.0 tall, contacts round the legs (jacks 0.25 up)",
             cy=D["usb_xy"][1] + 0.25, by0=D["usb_board_y0"], by1=D["usb_board_y0"] + 6.0, jb=jb + 0.25,
             cts=[(-0.8, -51.4), (0.8, -51.4), (-0.8, -53.0), (0.8, -53.0), (-4.6, -51.4), (4.6, -51.4), (-5.0, -53.0), (5.0, -53.0)],
             prot=[(-1.4, 0.2, -56.05, -55.05, "TVS"), (3.4, 5.0, -56.05, -54.45, "ESD")]),
    )
    for n, c in enumerate(cases):
        fig = plt.figure(figsize=(8.6, 5.4), dpi=125); ax = fig.add_axes([0.08, 0.12, 0.9, 0.76])
        cy = c["cy"]
        R(ax, x0, x1, c["by0"], c["by1"], "#2e7d32", "#1b5e20", al=0.25, lw=1.4)
        R(ax, x0, x1, c["by0"], ky, "none", "#ef6c00", hatch="///", lw=0.8, z=2)
        R(ax, -6.5, 6.5, c["jb"], c["jb"] + 1.2, "#424242", al=0.5, z=1)
        R(ax, -4.47, 4.47, cy - 1.58, cy + 1.58, "none", "#6a1b9a", ls="--", lw=1.0, z=2)
        for lx, ly in LEGS:
            R(ax, lx - LEG_PAD[0] / 2, lx + LEG_PAD[0] / 2, cy + ly - LEG_PAD[1] / 2, cy + ly + LEG_PAD[1] / 2, "#9e9e9e", "#424242", lw=0.6, z=3)
        for px, py in POSTS:
            ax.add_patch(Circle((px, cy + py), POST_HOLE / 2, fc="white", ec="#424242", lw=0.7, zorder=3))
        for x, y in c["cts"]:
            ax.add_patch(Circle((x, y), 0.6, fc="#ffd54f", ec="#e65100", lw=0.7, zorder=4, alpha=0.9))
        for a, b, cc, d, lab in c["prot"]:
            R(ax, a, b, cc, d, "#1565c0", "black", al=0.85, lw=0.6, z=5)
            ax.text((a + b) / 2, (cc + d) / 2, lab, ha="center", va="center", fontsize=7, color="white", zorder=6)
        top_m = c["by1"] - (cy + 2.15 + LEG_PAD[1] / 2); bot_m = (cy - 2.15 - LEG_PAD[1] / 2) - c["by0"]
        if n == 0:
            ax.annotate(f"leg pads {bot_m:.2f} from the bottom edge,\n{top_m:.2f} from the top edge (need ≥ 0.3)", (2.4, cy - 2.7), (6.8, -57.4), **k)
            ax.annotate("upper legs land under\nthe two outer top contacts", (2.4, cy + 2.15), (6.8, -50.6), **k)
        else:
            ax.annotate(f"leg pads {bot_m:.2f} / {top_m:.2f} from the edges", (2.4, cy - 2.7), (6.8, -57.4), **k)
            ax.annotate("8 contacts (pads Ø1.2): ≥ 0.3 from the leg pads,\nthe post holes and the board edges", (4.6, -51.4), (6.8, -50.0), **k)
            ax.annotate("TVS and ESD between the lower legs\n(in pockets in the printed key)", (4.2, -55.3), (6.8, -55.6), **k)
        ax.annotate(f"jack bodies (from y {c['jb']:.2f}): {c['jb'] - c['by1']:.2f} above the board", (-6.0, c["jb"] + 0.3), (-15.0, -48.0), **k)
        ax.annotate("socket outline (dashed), its 4 shell-leg pads (grey)\nand 2 locating-post holes", (-4.47, cy), (-15.0, -59.0), **k)
        ax.set_xlim(-15.5, 17.5); ax.set_ylim(-59.8, -47.2); ax.set_aspect("equal"); ax.grid(alpha=0.2)
        ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm, up the panel)")
        ax.set_title(c["title"], fontsize=10, loc="left")
        f = os.path.join(OUT, f"_usf_{n}.png"); fig.savefig(f); plt.close(fig); outs.append(f)
    ims = [Image.open(f) for f in outs]
    W = max(i.width for i in ims)
    cv = Image.new("RGB", (W, sum(i.height for i in ims)), "white"); y = 0
    for i in ims:
        cv.paste(i, (0, y)); y += i.height
    out = os.path.join(OUT, "usb-socket-fit-sketch.png"); cv.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out)


if __name__ == "__main__":
    main()
