# Step 2, decision 2 (4 Nov evening): the USB-C slot through the bottom wall, sketched on the v0.31 case cut (the cut and the key are
# drawn over the model, not modelled yet). USB-C 4.4 lower [Ed 11:09]; jacks 4.95 lower [Ed 20:12].
#   usb-slot-sketch.png  1: cut at x 0 (side view); 2: cut at y -55.0 through the bottom wall (seen from below).
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/usb_slot_sketch.py <out dir>
import os, sys
sys.path.insert(0, ".")
OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Rectangle
    from PIL import Image, ImageDraw
    from knobparam.common import model
    from knobparam.assembly.build import build_all
    from knobparam.assembly.plan_sheet import _cut_faces
    D = model.derive(model.default_params())
    parts, *_ = build_all(D)
    case, pcb = parts["case"], parts["PCB"]
    oled = parts['clear OLED 1.51" SSD1309 (PCB front, over window D)']
    jw, jh = D["jack_w"], D["jack_h"]
    jy = D["jack_y"] - 4.95                                # [Ed 20:12]
    uy = D["usb_xy"][1] - 4.4; ubh = 5.5                  # [Ed 11:09]
    bw, _, bt = D["usb_board"]; uw, uh, ud = D["usb_rcpt"]
    zf0, zf1, zr = D["z_fp0"], D["z_fp1"], D["z_rim"]
    zu0 = zf1 - ud - bt; zu1 = zu0 + bt                   # board back / front face
    wy0, wy1 = -56.4, -53.9                               # bottom wall (model)
    cw = bw / 2 + 0.15                                    # channel half width [A]
    rw = uw / 2 + 0.15                                    # receptacle pocket half width (as the faceplate opening)
    k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    outs = []

    def poly(ax, s, axis, at, fc, al=1.0):
        t = _cut_faces(s, axis, at)
        if t:
            ax.add_collection(PolyCollection(t, facecolors=fc, edgecolors=fc, alpha=al, linewidths=0.2))

    def R(ax, x0, x1, y0, y1, fc, ec="none", al=1.0, ls="-", lw=1.0):
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=fc, ec=ec, alpha=al, ls=ls, lw=lw))

    # ---- 1: cut at x 0 ----
    fig = plt.figure(figsize=(7.6, 7.6), dpi=125); ax = fig.add_axes([0.11, 0.09, 0.86, 0.84])
    poly(ax, case, "x", 0.0, "#b0bec5"); poly(ax, pcb, "x", 0.0, "#2e7d32"); poly(ax, oled, "x", 0.0, "#90caf9")
    R(ax, wy0, -51.7, zr, zu1, "white")                                       # the channel (wall + lip)
    R(ax, uy - uh / 2 - 0.15, wy1, zu1, zf1 + 0.1, "white")                    # receptacle pocket in the wall + faceplate opening
    R(ax, uy - uh / 2 - 0.15, uy + uh / 2 + 0.15, zf0 - 0.1, zf1 + 0.1, "white")
    oy = D["usb_xy"][1]
    R(ax, oy - uh / 2 - 0.15, oy + uh / 2 + 0.15, zf0, zf1, "#b0bec5")       # today's opening closes (the opening moves down)
    R(ax, wy0, wy1 - 0.05, zr, zu0 - 0.02, "#ffb74d", "#e65100")              # key
    R(ax, uy - ubh / 2, uy + ubh / 2, zu0, zu1, "#6a1b9a")                     # board
    R(ax, uy - uh / 2, uy + uh / 2, zu1, zf1 - 0.02, "#9575cd")                # receptacle
    R(ax, jy - jh / 2, jy + jh / 2, D["jack_depth_z0"], zf0, "#1565c0", al=0.85)
    ax.axvline(-56.4, color="#455a64", lw=0.8, ls=":")
    ax.annotate("printed key (orange): slides in from the\nback edge behind the board, clamps it", (-55.2, 12.0), (-51.0, 14.0), **k)
    ax.annotate("USB-C board, 4.4 lower: its bottom\nedge on the bottom face (rail line)", (uy, zu0 + 0.5), (-52.0, 24.5), **k)
    ax.annotate("ledge: the wall left in front of the\nboard takes the plug-in push", (-56.0, 33.5), (-59.5, 43.0), **k)
    ax.annotate("jack 2, 4.95 lower:\n1.0 above the board", (jy, 30.0), (-45.0, 20.0), **k)
    ax.annotate("back edge: the back cover\ncloses over the key's end", (-55.0, zr), (-51.0, -6.5), **k)
    ax.set_xlim(-60, -40); ax.set_ylim(-9, 46); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("y (mm, up the panel)"); ax.set_ylabel("z (mm)")
    ax.set_title("1. Cut at x 0: the channel through the bottom wall", fontsize=10, loc="left")
    f = os.path.join(OUT, "_us_1.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    # ---- 2: cut at y -55.0 through the bottom wall, seen from below ----
    yc = -55.0
    fig = plt.figure(figsize=(7.6, 7.6), dpi=125); ax = fig.add_axes([0.11, 0.09, 0.86, 0.84])
    poly(ax, case, "y", yc, "#b0bec5")
    R(ax, -cw, cw, zr - 0.1, zu1, "white")
    R(ax, -rw, rw, zu1, zf1 + 0.1, "white")
    R(ax, -cw + 0.05, cw - 0.05, zr, zu0 - 0.02, "#ffb74d", "#e65100")
    R(ax, -bw / 2, bw / 2, zu0, zu1, "#6a1b9a")
    R(ax, -uw / 2, uw / 2, zu1, zf1 - 0.02, "#9575cd")
    ax.annotate(f"channel {2 * cw:.1f} wide, from the back edge\nto the board's front face", (cw, 15.0), (-15.0, -6.0), **k)
    ax.annotate("receptacle pocket on through\nthe faceplate", (rw, 37.0), (7.5, 41.5), **k)
    ax.annotate("ledges each side and under\nthe receptacle", (-5.5, 33.0), (-15.5, 41.5), **k)
    ax.set_xlim(-16, 16); ax.set_ylim(-9, 46); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("x (mm)"); ax.set_ylabel("z (mm)")
    ax.set_title(f"2. Cut at y {yc:g} through the bottom wall (from below)", fontsize=10, loc="left")
    f = os.path.join(OUT, "_us_2.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    ims = [Image.open(f) for f in outs]
    H = max(i.height for i in ims); ims = [i.resize((int(i.width * H / i.height), H)) for i in ims]
    cv = Image.new("RGB", (sum(i.width for i in ims), H + 50), "white"); x = 0
    for i in ims:
        cv.paste(i, (x, 50)); x += i.width
    ImageDraw.Draw(cv).text((20, 15), "Step 2, decision 2 (sketch on the v0.31 case): the USB-C board slides in from behind along a channel through the "
                            "bottom wall onto a ledge; a printed key fills the channel behind it.", fill="black")
    out = os.path.join(OUT, "usb-slot-sketch.png"); cv.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out)


if __name__ == "__main__":
    main()
