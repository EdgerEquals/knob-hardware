# Step 2 boards, jack power board (5 Nov): a first floorplan to show it fits, both faces, before any KiCad work.
# Boxes are the parts' footprints with their pads [S datasheets, packages as in docs/step2-parts-2026-11-05.md]; passives are not drawn
# (about 70, mostly 0402/0603) [A]. The outline is the model's power board (jack row 43.0 x 10.5 + the ears over the two posts).
#   power-board-floorplan.png  top face (toward the jack board; parts ≤ 2.0 tall under the jack pins) and bottom face (ZIFs).
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/power_board_floorplan.py <out dir>
import os, sys
sys.path.insert(0, ".")
OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    from knobparam.common import model
    D = model.derive(model.default_params())
    bx0, bx1 = D["jb_x"]; by0, by1 = D["jack_bot_y"], D["jack_top_y"]; hx, ty = D["jb_tab"]
    hw, hl, hdx = D["jb_hdr"]; hy = (by0 + by1) / 2
    C = {"pow": "#ef9a9a", "ana": "#90caf9", "dig": "#c5e1a5", "con": "#bdbdbd", "aud": "#ffe082"}
    top = [("H1 2x6 socket", -hdx, hy, 7.1, 5.7, "con"), ("H2 2x6 socket", hdx, hy, 7.1, 5.7, "con"),
           ("HUSB238\n3x3", -19.6, -41.0, 3.2, 3.2, "pow"), ("eFuse\n[to pick]", -19.6, -45.0, 3.0, 3.0, "pow"),
           ("CC ESD x2", -17.0, -47.6, 2.6, 1.4, "pow"),
           ("DAC80504\n3x3", 3.3, -40.6, 3.2, 3.2, "ana"), ("OPA4197\nTSSOP-14", -3.9, -43.7, 5.0, 6.4, "ana"),
           ("TLV9064\nTSSOP-14", 3.4, -45.6, 6.4, 5.0, "ana"), ("3G07\nMIDI", 6.6, -40.6, 2.3, 3.1, "dig"),
           ("TCA9535\nQFN-24 4x4", 18.0, -41.4, 4.2, 4.2, "dig"), ("audio in/out\nfilters", 18.0, -46.0, 4.6, 3.6, "aud")]
    bot = [("ZIF 24p\nclear OLED", D["zif_oled"][3], by0 + D["zif_y_off"] + D["zif_oled"][1] / 2, D["zif_oled"][0], D["zif_oled"][1], "con"),
           ("FPC 25p 0.3\nlink flex", D["zif_link"][3], by0 + D["zif_y_off"] + D["zif_link"][1] / 2, D["zif_link"][0], D["zif_link"][1], "con"),
           ("TPS55340\nboost", -19.4, -40.9, 3.2, 3.2, "pow"), ("L boost\n5x5", -14.6, -41.2, 5.0, 5.0, "pow"),
           ("BAT54S\npump", -19.6, -44.4, 3.0, 2.6, "pow"),
           ("TPS7A4901\n+12.5", -19.4, -47.4, 4.9, 2.6, "pow"), ("TPS7A3001\n-12", -13.6, -47.0, 4.9, 3.0, "pow"),
           ("TPS62933\n3.3 V", -10.2, -43.4, 2.1, 1.8, "pow"), ("L 3.3 V", -10.4, -40.4, 2.6, 2.2, "pow"),
           ("TMUX7212", -5.6, -40.6, 6.4, 3.4, "ana"), ("TMUX7212", 1.2, -40.6, 6.4, 3.4, "ana"),
           ("TMUX7212\nQFN 3x3?", 6.6, -40.6, 3.2, 3.2, "ana"),
           ("OLED 12.5 V\nfilter", 12.4, -40.8, 4.0, 3.2, "pow"), ("audio buffers", 17.8, -40.8, 5.0, 3.2, "aud")]
    fig, axs = plt.subplots(2, 1, figsize=(12.5, 8.4), dpi=130)
    for ax, parts, title in ((axs[0], top, "Top face (toward the jack board; parts under 2.0, the jack pins 1.0 above them)"),
                             (axs[1], bot, "Bottom face, seen through from the front (ZIFs; nothing below but air down to the clear OLED, about 17)")):
        ax.add_patch(Rectangle((bx0, by0), bx1 - bx0, by1 - by0, fc="#e8f5e9", ec="black", lw=1.0))
        for i, (x, y) in enumerate(D["jb_post_xy"]):
            ax.add_patch(Rectangle((x - hx, ty), 2 * hx, by0 - ty, fc="#e8f5e9", ec="black", lw=1.0))
            ax.add_patch(Circle((x, y), D["jb_post_d"] / 2, fc="#ffb300", ec="#e65100", lw=0.8))
            ax.text(x + 1.6, y, "GND post" if i == 0 else "VSYS post", fontsize=7, va="center")
        for x, _y in D["jack_xy"]:
            ax.add_patch(Rectangle((x - 1.4, by0), 2.8, by1 - by0, fc="none", ec="#757575", ls=":", lw=0.8))
        for name, x, y, w, h, c in parts:
            ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=C[c], ec="black", lw=0.6, alpha=0.9))
            ax.text(x, y, name, fontsize=6.2, ha="center", va="center")
        ax.set_xlim(-23, 23); ax.set_ylim(-52.2, -37.6); ax.set_aspect("equal"); ax.grid(alpha=0.15)
        ax.set_title(title, fontsize=9, loc="left"); ax.set_ylabel("y (mm)")
    axs[1].set_xlabel("x (mm); dotted: under each jack (pins come down 1.9 below the jack board)")
    h = [Rectangle((0, 0), 1, 1, fc=c) for c in C.values()]
    fig.legend(h, ["power", "jack circuits", "digital", "connectors", "audio"], loc="lower center", ncol=5, fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    out = os.path.join(OUT, "power-board-floorplan.png"); fig.savefig(out); print("wrote", out)


if __name__ == "__main__":
    main()
