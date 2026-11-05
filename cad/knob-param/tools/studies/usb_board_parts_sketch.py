# Step 2 boards, after Q4 [Ed 5 Nov 11:17 = A: USB data on the same socket]: where the USB-C PD sink chip goes.
# The USB-C board (12 x 5.5 x 1.0, v0.36) seen from behind, at its back face. Its front face bears on the case ledge round the receptacle
# pocket (no parts there); the printed key bears on the lower 2.45 of the back face; the upper 3.05 band faces the gap (4.15) to the jack
# board's tab, where the spring contacts land.
#   usb-board-parts-sketch.png  A: PD chip on this board (3 Nov plan) with 6 contacts; B: PD chip on the jack power board, 8 contacts
#   (adds CC1, CC2), only the two small protection parts here, in pockets in the printed key.
# Footprints are typical [A]: HUSB238 DFN-10 3 x 3 [S], VBUS TVS DFN1610, data ESD SOT-563 1.6 x 1.6, 0402 passives, shell legs of a
# vertical 16-pin USB-C at x ±4.9 [A, part not chosen].
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/usb_board_parts_sketch.py <out dir>
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
    bw, bh, _ = D["usb_board"]; x0, x1 = -bw / 2, bw / 2
    y0, y1 = D["usb_board_y0"], D["usb_board_y1"]
    ky = D["y_in0"] - D["usb_key_gap"]                      # top of the key's face on the board
    cy = D["usb_xy"][1]
    uw, uh, _ = D["usb_rcpt"]
    k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    outs = []

    def R(ax, a, b, c, d, fc="none", ec="none", al=1.0, ls="-", lw=1.0, hatch=None, z=1):
        ax.add_patch(Rectangle((a, c), b - a, d - c, fc=fc, ec=ec, alpha=al, ls=ls, lw=lw, hatch=hatch, zorder=z))

    def base(ax):
        R(ax, x0, x1, y0, y1, "#2e7d32", "#1b5e20", al=0.25, lw=1.4)
        R(ax, x0, x1, y0, ky, "none", "#ef6c00", hatch="///", lw=0.8, z=2)              # key face
        R(ax, -uw / 2, uw / 2, cy - uh / 2, cy + uh / 2, "none", "#6a1b9a", ls="--", lw=1.0, z=2)   # receptacle (front face)
        for sx in (-1, 1):
            for dy in (-1.3, 1.3):
                ax.add_patch(Circle((sx * 4.9, cy + dy), 0.55, fc="#9e9e9e", ec="#424242", lw=0.6, zorder=3))
        ax.axhline(ky, color="#ef6c00", lw=0.6)

    cases = (
        ("A. PD chip on the USB-C board (3 Nov plan), 6 contacts", [(-5.0 + 2.0 * i, -52.4) for i in range(6)], 1.3,
         [("PD chip HUSB238\n3 x 3 [S]", -1.5, 1.5, -54.6, -51.6, "#c62828"), ("TVS", -5.6, -4.0, -56.2, -55.2, "#1565c0"),
          ("ESD", 3.9, 5.5, -56.2, -55.0, "#1565c0")]),
        ("B. PD chip on the jack power board, 8 contacts (adds CC1, CC2)",
         [(-2.4 + 1.6 * i, yy) for yy in (-51.75, -52.95) for i in range(4)], 0.8,
         [("TVS", -3.2, -1.6, -56.0, -55.0, "#1565c0"), ("ESD", 1.6, 3.2, -56.1, -54.5, "#1565c0")]),
    )
    for n, (title, cts, pd, chips) in enumerate(cases):
        fig = plt.figure(figsize=(8.4, 5.0), dpi=125); ax = fig.add_axes([0.08, 0.13, 0.9, 0.74])
        base(ax)
        for x, y in cts:
            ax.add_patch(Circle((x, y), pd / 2, fc="#ffd54f", ec="#e65100", lw=0.7, zorder=4))
        for lab, a, b, c, d, col in chips:
            R(ax, a, b, c, d, col, "black", al=0.85, lw=0.6, z=5)
            ax.text((a + b) / 2, (c + d) / 2, lab, ha="center", va="center", fontsize=7, color="white", zorder=6)
        if n == 0:
            ax.annotate("the 3 x 3 chip lands on the contacts\nand the key line: no room", (1.5, -52.0), (7.0, -50.4), **k)
            ax.annotate("outer contacts also meet\nthe socket's shell legs [A]", (5.0, -52.4), (7.0, -53.4), **k)
        else:
            ax.annotate("8 gold pads, 2 rows of 4 at 1.6 pitch,\nclear of the shell legs: a slimmer\nspring contact (about Ø0.6-0.7) [C]", (2.4, -51.75), (7.0, -50.9), **k)
            ax.annotate("TVS and ESD in pockets\nin the printed key", (3.2, -55.3), (7.0, -56.9), **k)
        ax.annotate("printed key presses here (hatched)", (-5.0, -55.6), (-13.5, -57.6), **k)
        ax.annotate("receptacle (front face, dashed)\nand its 4 shell legs [A]", (-4.9, cy + 1.3), (-13.5, -49.6), **k)
        ax.set_xlim(-14, 19); ax.set_ylim(-58.2, -48.6); ax.set_aspect("equal"); ax.grid(alpha=0.2)
        ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm, up the panel)")
        ax.set_title(title, fontsize=10, loc="left")
        f = os.path.join(OUT, f"_ub_{n}.png"); fig.savefig(f); plt.close(fig); outs.append(f)
    ims = [Image.open(f) for f in outs]
    W = max(i.width for i in ims)
    cv = Image.new("RGB", (W, sum(i.height for i in ims)), "white"); y = 0
    for i in ims:
        cv.paste(i, (0, y)); y += i.height
    out = os.path.join(OUT, "usb-board-parts-sketch.png"); cv.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out)


if __name__ == "__main__":
    main()
