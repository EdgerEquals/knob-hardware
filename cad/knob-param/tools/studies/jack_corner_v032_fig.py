# v0.32 as built (step 2, decisions 1-2 [Ed 4 Nov 20:12-20:25]): the jacks 4.95 lower with a clear straight path from behind (side
# ledges notched, bottom posts 1.0 lower and cut flat 0.4 under the jacks), the USB-C board in its bottom-wall channel with the key.
#   jack-corner-v032.png  1: front view, the case cut at z 10 with the ledges (z 0-2.55) darker, jacks and USB-C board outlined;
#                         2: cut at y -50.0 (left half): jack 1's bottom edge over the flat-cut post; 3: cut at x 0: the channel, key,
#                         ledge, board, receptacle.
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/jack_corner_v032_fig.py <out dir>
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
    case, glow, pcb = parts["case"], parts["glow coat (inside walls)"], parts["PCB"]
    oled = parts['clear OLED 1.51" SSD1309 (PCB front, over window D)']
    key = parts["USB-C key (printed, held by the back cover)"]
    brd, rc = parts["USB-C PD board"], parts["USB-C receptacle [S]"]
    cover = [s for n, s in parts.items() if n.startswith("back cover")][0]
    jw, jh = D["jack_w"], D["jack_h"]
    k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    outs = []

    def poly(ax, s, axis, at, fc, al=1.0):
        t = _cut_faces(s, axis, at)
        if t:
            ax.add_collection(PolyCollection(t, facecolors=fc, edgecolors=fc, alpha=al, linewidths=0.2))

    # ---- 1: front view ----
    fig = plt.figure(figsize=(7.6, 7.6), dpi=125); ax = fig.add_axes([0.11, 0.09, 0.86, 0.84])
    poly(ax, case, "z", 1.3, "#78909c"); poly(ax, case, "z", 10.0, "#b0bec5"); poly(ax, glow, "z", 10.0, "#c5e1a5")
    poly(ax, key, "z", 10.0, "#ffb74d"); poly(ax, key, "z", 1.3, "#ffb74d")
    for x, y in D["jack_xy"]:
        ax.add_patch(Rectangle((x - jw / 2, y - jh / 2), jw, jh, fill=False, ec="#1565c0", lw=1.4))
    bw, bh, _ = D["usb_board"]
    ax.add_patch(Rectangle((-bw / 2, D["usb_board_y0"]), bw, bh, fill=False, ec="#6a1b9a", lw=1.4))
    ny0, ny1 = D["jack_notch_y"]
    ax.annotate(f"side ledges notched y {ny0:.1f}..{ny1:.1f}\n(darker = ledge, z 0-2.55)", (-21.5, (ny0 + ny1) / 2), (-24.5, -27.0), **k)
    c = D["corners"][0]
    ax.annotate(f"bottom posts {D['bot_post_drop']:g} lower, cut flat\n{D['post_jack_air']:g} under the jacks", (c[0] + 1.0, D["post_clip_y"]),
                (-24.5, -62.5), **k)
    ax.annotate("jacks 4.95 lower (blue)", (D["jack_xs"][-1], D["jack_top_y"]), (6.0, -31.0), **k)
    ax.annotate("USB-C board (purple), 1.0 under the jacks;\nkey (orange) in the channel", (bw / 2, D["usb_board_y0"] + 1.0), (3.0, -62.5), **k)
    ax.set_xlim(-27, 27); ax.set_ylim(-66, -22); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm, up the panel)")
    ax.set_title(f"1. Front view, {D['version']}: the case at z 10, ledges darker", fontsize=10, loc="left")
    f = os.path.join(OUT, "_j2_1.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    # ---- 2: cut at y -50.0 ----
    yc = -50.0
    fig = plt.figure(figsize=(7.6, 7.6), dpi=125); ax = fig.add_axes([0.11, 0.09, 0.86, 0.84])
    poly(ax, case, "y", yc, "#b0bec5"); poly(ax, glow, "y", yc, "#c5e1a5"); poly(ax, pcb, "y", yc, "#2e7d32"); poly(ax, oled, "y", yc, "#90caf9")
    yb = D["jack_bot_y"] + 0.05
    for n in ("jack 1 PJ366ST body + pins [S]", "jack 2 PJ366ST body + pins [S]"):
        poly(ax, parts[n], "y", yb, "#1565c0", 0.85)
    ax.annotate(f"jacks 1 and 2 (cut just above their bottom edge, y {D['jack_bot_y']:.2f})", (-17.25, 31.0), (-25.0, 41.0), **k)
    ax.annotate(f"bottom-left post at y {yc:g}: nothing; it is cut flat\nat y {D['post_clip_y']:.2f}, under this cut", (-21.0, 5.0), (-17.0, 12.0), **k)
    ax.annotate("side wall: the jack row passes 0.5 from it", (-22.75, 20.0), (-17.0, 21.5), **k)
    ax.set_xlim(-27, 1); ax.set_ylim(-9, 43); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("x (mm)"); ax.set_ylabel("z (mm, out of the panel)")
    ax.set_title(f"2. Cut at y {yc:g}: jack 1's bottom edge, no post in its path", fontsize=10, loc="left")
    f = os.path.join(OUT, "_j2_2.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    # ---- 3: cut at x 0 ----
    fig = plt.figure(figsize=(7.6, 7.6), dpi=125); ax = fig.add_axes([0.11, 0.09, 0.86, 0.84])
    poly(ax, case, "x", 0.0, "#b0bec5"); poly(ax, pcb, "x", 0.0, "#2e7d32"); poly(ax, oled, "x", 0.0, "#90caf9")
    poly(ax, cover, "x", 0.0, "#455a64")
    poly(ax, key, "x", 0.0, "#ffb74d"); poly(ax, brd, "x", 0.0, "#6a1b9a"); poly(ax, rc, "x", 0.0, "#9575cd")
    poly(ax, parts["jack 2 PJ366ST body + pins [S]"], "x", -5.75 + 0.01, "#1565c0", 0.5)
    ax.axvline(-56.4, color="#455a64", lw=0.8, ls=":")
    ax.annotate("key (orange): back cover holds it,\n0.02 to the board and to the cover;\nits tab is the PCB ledge here", (-55.0, 12.0), (-51.0, 13.0), **k)
    ax.annotate("board on the ledge (the wall left in front)", (-55.5, 31.5), (-59.5, 43.0), **k)
    ax.annotate("jack 2 behind (pale): 1.0 above the board", (-48.0, 30.0), (-47.0, 24.0), **k)
    ax.annotate("back cover", (-50.0, -5.0), (-45.0, -7.5), **k)
    ax.set_xlim(-60, -40); ax.set_ylim(-9, 46); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("y (mm, up the panel)"); ax.set_ylabel("z (mm)")
    ax.set_title("3. Cut at x 0: the USB-C channel, key and ledge", fontsize=10, loc="left")
    f = os.path.join(OUT, "_j2_3.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    ims = [Image.open(f) for f in outs]
    H = max(i.height for i in ims); ims = [i.resize((int(i.width * H / i.height), H)) for i in ims]
    cv = Image.new("RGB", (sum(i.width for i in ims), H + 50), "white"); x = 0
    for i in ims:
        cv.paste(i, (x, 50)); x += i.width
    ImageDraw.Draw(cv).text((20, 15), f"Knob {D['version']} as built (step 2, decisions 1-2, Ed 4 Nov 20:12-20:25): the jacks' path from behind is clear "
                            "(0.4 at the posts, 0.5 at the side walls); the USB-C board sits in its channel, the key behind it.", fill="black")
    out = os.path.join(OUT, "jack-corner-v032.png"); cv.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out)


if __name__ == "__main__":
    main()
