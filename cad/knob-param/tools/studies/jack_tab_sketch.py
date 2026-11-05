# Step 2 boards, jack board Q16 (5 Nov): the jack board's tab carries the 8 Harwin P70-5100045 spring contacts (pad Ø1.2 [S-dist])
# opposite the USB-C board's landing pads. As modelled (v0.40) the tab ends at y -53.60, so the lower row's pads (centres y -53.00)
# reach its edge, and the outer lower pads (x ±5.0) are 0.20 from its sides.
#   jack-tab-sketch.png  left: front view of the tab now and proposal A (tab to -53.90 and ±5.85; the key's top stepped down 0.25
#   where the tab passes); right: side view (y-z) of the channel with the key step.
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/jack_tab_sketch.py <out dir>
import os, sys
sys.path.insert(0, ".")
OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    from knobparam.common import model
    D = model.derive(model.default_params())
    tw, ty = D["usb_pwr_tab"]; ch = D["usb_ch_hw"]; key_top = D["y_in0"] - D["usb_key_gap"]
    by0 = D["jack_bot_y"]; pad = D["usb_pwr_pad"]
    k = dict(fontsize=8, arrowprops=dict(arrowstyle="-", lw=0.7))
    fig, (a, b) = plt.subplots(1, 2, figsize=(12.5, 5.0), dpi=130, gridspec_kw=dict(width_ratios=[1.5, 1]))

    def R(ax, x0, x1, y0, y1, fc="none", ec="none", al=1.0, ls="-", lw=1.0, z=1, hatch=None):
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=fc, ec=ec, alpha=al, ls=ls, lw=lw, zorder=z, hatch=hatch))
    # front view
    R(a, -8, -ch, -56.6, -47.8, "#b0bec5", al=0.8); R(a, ch, 8, -56.6, -47.8, "#b0bec5", al=0.8)
    R(a, -ch + D["usb_key_gap"], ch - D["usb_key_gap"], -56.4, key_top, "#ffcc80", "#ef6c00", al=0.6, z=1)
    R(a, -tw, tw, ty, by0, "#a5d6a7", "#1b5e20", al=0.5, lw=1.2, z=2)
    R(a, -5.85, 5.85, -53.90, by0, "none", "#c62828", ls="--", lw=1.4, z=4)
    for x, y in D["usb_pwr_contacts"]:
        a.add_patch(Circle((x, y), pad / 2, fc="#ffd54f", ec="#e65100", lw=0.7, zorder=5))
    a.annotate(f"tab now: ±{tw:g}, bottom y {ty:g}\nlower pads reach the edge (0.00);\nouter lower pads 0.20 from the sides", (tw, ty + 0.3), (6.4, -50.3), **k)
    a.annotate("A: tab ±5.85, bottom y -53.90 (red dashed):\npads 0.30 from the bottom, 0.25 from the sides;\n0.30 to the channel walls", (-5.85, -53.9),
               (-13.0, -55.9), **k)
    a.annotate(f"printed key (top y {key_top:.2f} today)", (0, -55.0), (-13.0, -49.0), **k)
    a.set_xlim(-13.5, 13.5); a.set_ylim(-57.2, -47.6); a.set_aspect("equal"); a.grid(alpha=0.2)
    a.set_xlabel("x (mm)"); a.set_ylabel("y (mm, up the panel)")
    a.set_title("Front view: the jack board's tab in the USB-C channel, 8 contact pads Ø1.2", fontsize=9, loc="left")
    # side view (y-z)
    z_board0, z_board1 = D["usb_z0"], D["usb_z1"]
    R(b, D["jb_z0"], D["jb_z1"], ty, by0 + 1.0, "#a5d6a7", "#1b5e20", al=0.5, lw=1.2, z=2)
    R(b, D["jb_z0"], D["jb_z1"], -53.9, ty, "none", "#c62828", ls="--", lw=1.4, z=3)
    R(b, z_board0, z_board1, -56.4, -50.4, "#7e57c2", "#4527a0", al=0.5, z=2)
    R(b, 20.0, z_board0 - 0.02, -56.4, key_top, "#ffcc80", "#ef6c00", al=0.6, z=1)
    R(b, 20.0, D["jb_z1"] + 0.3, key_top - 0.25, key_top, "white", "#c62828", ls="--", lw=1.2, z=3, hatch="///")
    for y in (-53.0, -51.4):
        R(b, D["jb_z1"], z_board0, y - D["usb_pwr_d"] / 2, y + D["usb_pwr_d"] / 2, "#ffd54f", "#e65100", al=0.9, lw=0.6, z=4)
    b.annotate("jack board tab (z 24.7-26.3)", (25.5, -49.6), (20.3, -48.6), **k)
    b.annotate("USB-C board", (31.2, -51.0), (29.0, -48.6), **k)
    b.annotate("spring contacts", (28.3, -53.0), (27.2, -57.6), **k)
    b.annotate("A: key top stepped down 0.25\nbehind the tab's path (hatched),\nfull height where it presses the board", (23.0, key_top - 0.12), (20.3, -58.6), **k)
    b.set_xlim(20, 33); b.set_ylim(-59.5, -47.8); b.grid(alpha=0.2)
    b.set_xlabel("z (mm, towards the faceplate)"); b.set_ylabel("y (mm)")
    b.set_title("Side view at x 0 (the stack comes in along z)", fontsize=9, loc="left")
    fig.tight_layout()
    out = os.path.join(OUT, "jack-tab-sketch.png"); fig.savefig(out); print("wrote", out)


if __name__ == "__main__":
    main()
