# Step 2, decision 4, option 2 (4 Nov 22:01, Danny "I was thinking two as well"): the jack unit stays in the shell and nothing is plugged
# inside. The clear OLED's ZIF goes back onto the main board's bottom strip (the bottom ledge notched for it), and the link to the jack
# unit is spring contacts from the (lowered) jack power board onto gold pads in the same strip. Sketch over the v0.33 model.
#   jack-link2-sketch.png  1: front view of the strip (main board, OLED, the ZIF, the two pad fields, the power board's outline);
#                          2: cut at x 12.7 through a pad field (spring contacts); 3: cut at x 0 through the ZIF and the OLED's flex loop.
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/jack_link2_sketch.py <out dir>
import os, sys
sys.path.insert(0, ".")
OUT = sys.argv[1] if len(sys.argv) > 1 else "."

ZIF = (17.65, 4.5, 2.0)       # [S] ER-CON24HT-1, the clear OLED's matching ZIF (docs/screens-2026-11-02.md): w, d, h
PB_Z0 = 18.1                  # the 36 mm flex [S] needs a ~16 mm loop, so the power board cannot come down: contacts ~18 long
PB_EXT_Y = -51.4              # [A] power board's tab down over the strip, |x| <= 18.0 (0.4 over the bottom ledge, clear of the posts)
PADS = dict(x0=9.5, n=6, p=1.27, rows=(-50.85, -49.58))   # [A] two rows of 6 each side at 1.27 mm (24 contacts)


def main():
    import math
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Rectangle, Circle
    from PIL import Image, ImageDraw
    from knobparam.common import model
    from knobparam.assembly.build import build_all
    from knobparam.assembly.plan_sheet import _cut_faces
    D = model.derive(model.default_params())
    parts, *_ = build_all(D)
    case, pcb = parts["case"], parts["PCB"]
    oled = parts['clear OLED 1.51" SSD1309 (PCB front, over window D)']
    y0, y1 = D["jack_bot_y"], D["jack_top_y"]; bx0, bx1 = D["jb_x"]
    oy0 = D["clear_oled_xy"][1] - D["clear_oled"][1] / 2; ow = D["clear_oled"][0] / 2; ot = D["clear_oled"][2]
    zy0, zy1 = oy0 - ZIF[1], oy0
    pb1 = PB_Z0 + D["jb2_t"]
    k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    outs = []

    def poly(ax, s, axis, at, fc, al=1.0):
        t = _cut_faces(s, axis, at)
        if t:
            ax.add_collection(PolyCollection(t, facecolors=fc, edgecolors=fc, alpha=al, linewidths=0.2))

    def R(ax, a, b, c, d, fc="none", ec="none", al=1.0, ls="-", lw=1.0):
        ax.add_patch(Rectangle((a, c), b - a, d - c, fc=fc, ec=ec, alpha=al, ls=ls, lw=lw))

    def pad_xs():
        return [s * (PADS["x0"] + i * PADS["p"]) for s in (-1, 1) for i in range(PADS["n"])]

    # ---- 1: front view of the strip ----
    fig = plt.figure(figsize=(9.0, 5.6), dpi=125); ax = fig.add_axes([0.08, 0.12, 0.9, 0.78])
    poly(ax, pcb, "z", -0.8, "#2e7d32", 0.55); poly(ax, case, "z", 1.3, "#b0bec5")
    R(ax, -ow, ow, oy0, -36.0, "#90caf9", al=0.8)
    R(ax, -ZIF[0] / 2 - 0.3, ZIF[0] / 2 + 0.3, D["pcb_y0"], D["pcb_y0"] + D["ledge_w"] + 0.05, "white")   # ledge notched for the ZIF
    R(ax, -ZIF[0] / 2, ZIF[0] / 2, zy0, zy1, "#424242")
    for x in pad_xs():
        for y in PADS["rows"]:
            ax.add_patch(Circle((x, y), 0.45, fc="#ffb300", ec="#e65100", lw=0.5))
    ax.plot([bx0, bx0, -18.0, -18.0, 18.0, 18.0, bx1, bx1, bx0], [y1, y0, y0, PB_EXT_Y, PB_EXT_Y, y0, y0, y1, y1], color="#1b5e20", lw=1.4, ls="--")
    ax.annotate("the OLED's own ZIF (ER-CON24HT-1, 17.65 x 4.5 [S]): it fills the\nstrip under the OLED exactly (4.5), bottom ledge notched", (0.0, zy0 + 1.0),
                (-26.0, -60.5), **k)
    ax.annotate(f"gold pads, {2 * PADS['n'] * len(PADS['rows'])} spring contacts [A]\n(two rows of {PADS['n']} each side, 1.27)", (PADS["x0"] + 3, PADS["rows"][0]),
                (6.0, -60.5), **k)
    ax.annotate("jack power board's outline (dashed): a tab down over\nthe strip for |x| <= 18, 0.4 above the bottom ledge", (-18.0, PB_EXT_Y),
                (-26.0, -36.5), **k)
    ax.annotate("clear OLED", (10.0, -40.0), (12.0, -37.5), **k)
    ax.set_xlim(-27, 27); ax.set_ylim(-62, -35); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm, up the panel)")
    ax.set_title("1. Front view: the main board's bottom strip under the OLED", fontsize=10, loc="left")
    f = os.path.join(OUT, "_l2_1.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    def side(ax, xc):
        poly(ax, case, "x", xc, "#b0bec5"); poly(ax, pcb, "x", xc, "#2e7d32"); poly(ax, oled, "x", xc, "#90caf9")
        poly(ax, parts["USB-C PD board"], "x", min(xc, 5.9), "#6a1b9a") if abs(xc) < 6 else None
        R(ax, y0, y1, D["jack_depth_z0"], D["z_fp0"] - 0.02, "#1565c0", al=0.4)
        R(ax, y0, y1, D["jb_z0"], D["jb_z1"], "#2e7d32", "#1b5e20")
        pyb = PB_EXT_Y if abs(xc) <= 18.0 else y0
        R(ax, pyb, y1, PB_Z0, pb1, "#66bb6a", "#1b5e20")
        R(ax, y0 + 0.3, y1 - 0.3, pb1, pb1 + D["jb2_parts"], "#9e9e9e", al=0.5)

    # ---- 2: cut at x 12.7 (through a pad field) ----
    xc = PADS["x0"] + 2.5 * PADS["p"]
    fig = plt.figure(figsize=(7.0, 7.6), dpi=125); ax = fig.add_axes([0.12, 0.09, 0.85, 0.84])
    side(ax, xc)
    for y in PADS["rows"]:
        R(ax, y - 0.45, y + 0.45, 0.0, PB_Z0, "#ffb300", "#e65100", lw=0.5)
    ax.annotate(f"spring contacts would have to be ~{PB_Z0:.0f} long (the power\nboard stays up for the flex loop): long test-probe\n"
                "pins, or a riser board on the strip [A]", (PADS["rows"][1], 5.0), (-47.5, -7.5), **k)
    ax.annotate("jack power board (stays at z 18.1)", (-45.0, pb1), (-46.0, 23.0), **k)
    ax.annotate("jack board on the jacks' backs", (-45.0, D["jb_z1"]), (-46.0, 29.5), **k)
    ax.set_xlim(-60, -36); ax.set_ylim(-9, 42); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("y (mm, up the panel)"); ax.set_ylabel("z (mm)")
    ax.set_title(f"2. Cut at x {xc:.1f}: a pad field", fontsize=10, loc="left")
    f = os.path.join(OUT, "_l2_2.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    # ---- 3: cut at x 0 (ZIF, flex loop) ----
    fig = plt.figure(figsize=(7.0, 7.6), dpi=125); ax = fig.add_axes([0.12, 0.09, 0.85, 0.84])
    side(ax, 0.0)
    poly(ax, parts["USB-C key (printed, held by the back cover)"], "x", 0.0, "#ffb74d")
    R(ax, D["pcb_y0"], D["pcb_y0"] + D["ledge_w"] + 0.05, 0.05, D["z_ledge1"], "white")   # bottom ledge + key tab notched here
    R(ax, zy0, zy1, 0.0, ZIF[2], "#424242")
    # the OLED's flex: out of its bottom edge, a loop up in front of the OLED's lower edge (behind the jacks), back down into the ZIF
    ax.plot([oy0 + 0.1, oy0 + 0.1, oy0 + 2.6, oy0 + 2.6, zy1 + 0.3], [ot / 2, 16.0, 16.0, 1.2, 1.2], color="#e65100", lw=1.6, ls="--")
    ax.annotate("the OLED's own flex is 36.0 long [S] (made to fold\nback): from a ZIF right at its edge it needs a\n~16 mm loop (dashed) or a fold",
                (oy0 + 0.1, 5.0), (-59.0, 18.0), **k)
    ax.annotate("ZIF on the main board,\nplugged on the bench", (zy0 + 1.0, 1.0), (-59.5, -6.5), **k)
    ax.annotate("bottom ledge and the key's tab\nnotched over the ZIF", (D["pcb_y0"] + 0.5, 1.5), (-50.0, -7.5), **k)
    ax.set_xlim(-60, -36); ax.set_ylim(-9, 42); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("y (mm, up the panel)"); ax.set_ylabel("z (mm)")
    ax.set_title("3. Cut at x 0: the ZIF and the OLED's flex", fontsize=10, loc="left")
    f = os.path.join(OUT, "_l2_3.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    ims = [Image.open(f) for f in outs]
    H = max(i.height for i in ims); ims = [i.resize((int(i.width * H / i.height), H)) for i in ims]
    cv = Image.new("RGB", (sum(i.width for i in ims), H + 50), "white"); x = 0
    for i in ims:
        cv.paste(i, (x, 50)); x += i.width
    ImageDraw.Draw(cv).text((20, 15), "Step 2, decision 4, option 2 checked against the OLED's real flex and ZIF (sketch over v0.33): the ZIF fills the strip "
                            "exactly, and the 36 mm flex needs a ~16 mm loop, so the power board stays up and the contacts get long.", fill="black")
    out = os.path.join(OUT, "jack-link2-sketch.png"); cv.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out)


if __name__ == "__main__":
    main()
