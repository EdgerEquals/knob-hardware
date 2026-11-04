# Step 2, decision 3 (4 Nov evening): the jack board. Schematic from the v0.32 params (not modelled yet).
#   jack-board-sketch.png  1: the jack board's underside as planned [Ed 11:22] (one board on the jacks' backs): its outline is fixed by the
#                          jacks' path from behind; the jack pin blocks (the model's placeholder [A]; the real PJ366ST layout is a [C])
#                          and the two ZIFs [A]; 2: option B, cut at x 0: a second board of the same outline hanging under the jack
#                          board on two headers, carrying the ZIFs and the power parts; the two flexes rise to it.
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/jack_board_sketch.py <out dir>
import os, sys
sys.path.insert(0, ".")
OUT = sys.argv[1] if len(sys.argv) > 1 else "."

ZIF24 = (16.0, 5.5, 2.0)   # [A] 24-pin 0.5 mm ZIF, w x d x h (the clear OLED's flex)
ZIF20 = (14.0, 5.5, 2.0)   # [A] ~20-pin 0.5 mm ZIF (the link flex to the main board)


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    from PIL import Image
    from knobparam.common import model
    D = model.derive(model.default_params())
    jw, jh = D["jack_w"], D["jack_h"]
    x0, x1 = min(D["jack_xs"]) - jw / 2, max(D["jack_xs"]) + jw / 2
    y0, y1 = D["jack_bot_y"], D["jack_top_y"]
    zb1 = D["jack_depth_z0"]; zb0 = zb1 - 1.6; zp = zb1 - D["jack_pin_len"]
    k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    outs = []

    def R(ax, a, b, c, d, fc="none", ec="none", al=1.0, ls="-", lw=1.0, hatch=None):
        ax.add_patch(Rectangle((a, c), b - a, d - c, fc=fc, ec=ec, alpha=al, ls=ls, lw=lw, hatch=hatch))

    # ---- 1: underside, one board ----
    fig = plt.figure(figsize=(9.0, 5.2), dpi=125); ax = fig.add_axes([0.08, 0.13, 0.9, 0.75])
    R(ax, x0, x1, y0, y1, "#2e7d32", al=0.25, ec="#1b5e20", lw=1.2)
    for x, y in D["jack_xy"]:
        R(ax, x - jw / 2, x + jw / 2, y - jh / 2, y + jh / 2, ec="#1565c0", ls="--")
        R(ax, x - 2.0, x + 2.0, y - 3.0, y + 3.0, "#9e9e9e", "#616161", hatch="///")
    zy = y0 + 0.2
    R(ax, -ZIF24[0] / 2, ZIF24[0] / 2, zy, zy + ZIF24[1], "none", "#d32f2f", lw=1.6)
    R(ax, 4.0, 4.0 + ZIF20[0], zy, zy + ZIF20[1], "none", "#d32f2f", lw=1.6, ls="--")
    area = (x1 - x0) * (y1 - y0); pins = 4 * 4.0 * 6.0
    ax.annotate(f"jack board = the jack row's own outline, {x1 - x0:.1f} x {y1 - y0:.1f} = {area:.0f} mm²\n"
                "(wider meets the side walls, lower the posts, higher hides the OLED)", (x1, y1), (-22.0, y1 + 2.0), **k)
    ax.annotate(f"jack pins (the model's placeholder blocks [A];\nthe real PJ366ST layout is a [C]): {pins:.0f} mm²", (-15.25, D["jack_y"] + 2.0),
                (-30.0, y0 - 6.5), **k)
    ax.annotate(f"24-pin ZIF for the clear OLED ({ZIF24[0]:g} x {ZIF24[1]:g} [A]) and the\nlink-flex ZIF ({ZIF20[0]:g} x {ZIF20[1]:g} [A], dashed): "
                "they land on the pins", (0.0, zy + ZIF24[1]), (2.0, y0 - 6.5), **k)
    ax.set_xlim(-31, 31); ax.set_ylim(y0 - 8, y1 + 5.5); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm)")
    ax.set_title("1. As planned (11:22): one board on the jacks' backs, seen from behind (its underside)", fontsize=10, loc="left")
    f = os.path.join(OUT, "_jb_1.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    # ---- 2: option B, side cut at x 0 ----
    fig = plt.figure(figsize=(7.0, 7.6), dpi=125); ax = fig.add_axes([0.12, 0.09, 0.85, 0.84])
    gap = 5.0; zm1 = zb0 - gap; zm0 = zm1 - 1.0
    R(ax, -56.4, -53.9, -1.6, D["z_fp0"], "#b0bec5")                                     # bottom wall
    R(ax, -60.0, -30.0, D["z_fp0"], D["z_fp1"], "#b0bec5")                               # faceplate
    R(ax, D["pcb_y0"], -30.0, -1.6, 0.0, "#2e7d32")                                      # main PCB
    cy = D["clear_oled_xy"][1]; ch = D["clear_oled"][1]
    R(ax, cy - ch / 2, -30.0, 0.0, D["clear_oled"][2], "#90caf9")                        # OLED
    R(ax, y0, y1, zb1, D["z_fp0"] - 0.02, "#1565c0", al=0.5)                             # jack body (x 0 is between 2 and 3: drawn pale)
    R(ax, y0, y1, zb0, zb1, "#2e7d32", "#1b5e20")                                         # jack board
    R(ax, y0, y1, zm0, zm1, "#66bb6a", "#1b5e20")                                         # second board
    R(ax, y1 - 3.0, y1 - 0.5, zm1, zb0, "#424242")                                        # header
    R(ax, y0 + 0.2, y0 + 0.2 + ZIF24[1], zm0 - ZIF24[2], zm0, "#d32f2f")                 # ZIFs on its underside
    R(ax, D["usb_board_y0"], D["usb_board_y1"], D["usb_z0"], D["usb_z1"], "#6a1b9a")
    R(ax, -56.4, -53.95, D["z_rim"], D["usb_z0"] - 0.02, "#ffb74d")
    oy0 = cy - ch / 2
    zz = zm0 - ZIF24[2]
    ax.plot([oy0, oy0 - 0.6, oy0 - 0.6, y0 + 1.5, y0 + 1.5], [0.6, 0.6, zz - 1.2, zz - 1.2, zz], color="#e65100", lw=1.6)
    ax.plot([D["pcb_y0"] + 1.2, D["pcb_y0"] + 1.2, y0 + 3.5, y0 + 3.5], [0.0, zz - 2.4, zz - 2.4, zz], color="#6d4c41", lw=1.6, ls="--")
    ax.annotate("jack board on the jacks' backs\n(jacks + the small analog parts)", ((y0 + y1) / 2, zb1 - 0.8), (-44.0, 30.0), **k)
    ax.annotate(f"option B: a second board the same outline,\n{gap:g} below on two headers: both ZIFs (red)\n"
                "and the power parts (±12 V, the OLED's 12.5 V)", ((y0 + y1) / 2, zm0), (-47.0, 9.0), **k)
    ax.annotate("the clear OLED's 36 mm flex\n(from its bottom edge)", (oy0 - 0.6, 8.0), (-59.5, 3.0), **k)
    ax.annotate("link flex from the main board's\nbottom strip (dashed)", (D["pcb_y0"] + 1.2, 6.0), (-59.5, -6.5), **k)
    ax.annotate("USB-C board + key", (D["usb_board_y0"] + 1.0, D["usb_z0"]), (-59.5, 24.0), **k)
    ax.set_xlim(-60, -30); ax.set_ylim(-9, 42); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("y (mm, up the panel)"); ax.set_ylabel("z (mm)")
    ax.set_title("2. Option B, cut at x 0 (schematic)", fontsize=10, loc="left")
    f = os.path.join(OUT, "_jb_2.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    ims = [Image.open(f) for f in outs]
    H = max(i.height for i in ims); ims = [i.resize((int(i.width * H / i.height), H)) for i in ims]
    cv = Image.new("RGB", (sum(i.width for i in ims), H), "white"); x = 0
    for i in ims:
        cv.paste(i, (x, 0)); x += i.width
    out = os.path.join(OUT, "jack-board-sketch.png"); cv.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out)


if __name__ == "__main__":
    main()
