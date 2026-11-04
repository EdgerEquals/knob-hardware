# Step 2 start (4 Nov evening): the jacks 5.45 lower and the USB-C board 4.4 lower [Ed 10:07, 11:09], and what in today's case (v0.31)
# is in their straight path from behind.
#   jack-corner-v031.png  1: front view: the case cut at z 10 (walls, bottom corner posts) with the PCB lip (z 0-2.55) darker, the
#                         lowered jacks (blue) and USB-C board (purple); red = case or glow coat inside their straight path from behind;
#                         2: cut at y -50.0 through jack 1's bottom edge and the corner post (left half); 3: cut at x 0 through the
#                         USB-C board and the bottom wall.
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/jack_corner_v031_fig.py <out dir>
import os, sys
sys.path.insert(0, ".")
OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Rectangle
    from PIL import Image, ImageDraw
    from build123d import Box, Pos, Align
    from knobparam.common import model
    from knobparam.assembly.build import build_all
    from knobparam.assembly.plan_sheet import _cut_faces
    D = model.derive(model.default_params())
    parts, *_ = build_all(D)
    case, glow, pcb = parts["case"], parts["glow coat (inside walls)"], parts["PCB"]
    oled = parts['clear OLED 1.51" SSD1309 (PCB front, over window D)']
    jw, jh = D["jack_w"], D["jack_h"]
    dj, du, ubh = 5.45, 4.4, 5.5                         # [Ed 10:07, 11:09] jacks 5.45 lower; USB-C 4.4 lower, board 5.5 tall
    jy = D["jack_y"] - dj
    ux, uy0 = D["usb_xy"]; uy = uy0 - du
    bw, _, bt = D["usb_board"]; uw, uh, ud = D["usb_rcpt"]
    zb0, zb1, zr = D["jack_depth_z0"], D["z_fp0"], D["z_rim"]
    zp = D["jack_depth_z0"] - D["jack_pin_len"]
    box = lambda x0, x1, y0, y1, z0, z1: Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=(Align.MIN,) * 3)
    # the new positions (home) and their straight paths from behind (prisms from the back rim to home)
    jacks = [box(x - jw / 2, x + jw / 2, jy - jh / 2, jy + jh / 2, zb0, zb1 - 0.02) for x in D["jack_xs"]]
    jpath = [box(x - jw / 2, x + jw / 2, jy - jh / 2, jy + jh / 2, zr - 1.0, zb1 - 0.02) for x in D["jack_xs"]]
    zu0 = D["z_fp1"] - ud - bt
    usb = box(ux - bw / 2, ux + bw / 2, uy - ubh / 2, uy + ubh / 2, zu0, zu0 + bt)
    rcpt = box(ux - uw / 2, ux + uw / 2, uy - uh / 2, uy + uh / 2, zu0 + bt, D["z_fp1"] - 0.02)
    upath = box(ux - bw / 2, ux + bw / 2, uy - ubh / 2, uy + ubh / 2, zr - 1.0, zu0 + bt)
    hits = []
    for p in jpath + [upath]:
        for f in (case, glow):
            try:
                x = p & f
                if x is not None and x.solids():
                    hits.append(x)
            except Exception:
                pass
    k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    outs = []

    def poly(ax, s, axis, at, fc, al=1.0):
        t = _cut_faces(s, axis, at)
        if t:
            ax.add_collection(PolyCollection(t, facecolors=fc, edgecolors=fc, alpha=al, linewidths=0.2))

    # ---- 1: front view ----
    fig = plt.figure(figsize=(7.6, 7.6), dpi=125); ax = fig.add_axes([0.11, 0.09, 0.86, 0.84])
    poly(ax, case, "z", 1.3, "#78909c"); poly(ax, case, "z", 10.0, "#b0bec5"); poly(ax, glow, "z", 10.0, "#c5e1a5")
    for h in hits:
        for zc in (1.3, 2.3, 10.0):
            poly(ax, h, "z", zc, "#d32f2f")
    for x in D["jack_xs"]:
        ax.add_patch(Rectangle((x - jw / 2, jy - jh / 2), jw, jh, fill=False, ec="#1565c0", lw=1.4))
    ax.add_patch(Rectangle((ux - bw / 2, uy - ubh / 2), bw, ubh, fill=False, ec="#6a1b9a", lw=1.4))
    ax.axhline(-56.4, color="#455a64", lw=0.8, ls=":")
    c = D["corners"][0]
    ax.annotate("bottom corner post + M2.5 insert\n(up to z 21.8): 1.3 into jack 1", (c[0] + 1.6, c[1] + 2.6), (-24.5, -32.5), **k)
    ax.annotate("PCB lip (z 0-2.55, darker):\n1.6 into jacks 1 and 4", (-21.0, -44.0), (-12.0, -25.5), **k)
    ax.annotate("jacks 5.45 lower (blue), row 44.5 wide", (D["jack_xs"][-1], jy + jh / 2), (4.0, -33.5), **k)
    ax.annotate("USB-C board 4.4 lower (purple): its whole\npath runs through the bottom wall and lip", (ux + bw / 2, uy - 1.0), (5.0, -61.5), **k)
    ax.annotate("rail line y -56.4", (-15, -56.4), (-24, -63.5), **k)
    ax.set_xlim(-27, 27); ax.set_ylim(-66, -22); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm, up the panel)")
    ax.set_title("1. Front view: the case at z 10, its PCB lip darker; red = in the way", fontsize=10, loc="left")
    f = os.path.join(OUT, "_jc_1.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    # ---- 2: cut at y -50.0, left half ----
    yc = -50.0
    fig = plt.figure(figsize=(7.6, 7.6), dpi=125); ax = fig.add_axes([0.11, 0.09, 0.86, 0.84])
    poly(ax, case, "y", yc, "#b0bec5"); poly(ax, glow, "y", yc, "#c5e1a5"); poly(ax, pcb, "y", yc, "#2e7d32")
    poly(ax, jacks[0], "y", yc, "#1565c0", 0.85); poly(ax, jacks[1], "y", yc, "#1565c0", 0.85)
    poly(ax, jpath[0], "y", yc, "#1565c0", 0.12)
    for h in hits:
        poly(ax, h, "y", yc, "#d32f2f")
    ax.annotate("jack 1 home (5.45 lower)", (-17.25, 31.0), (-14.0, 39.5), **k)
    ax.annotate("its straight path from behind (pale)", (-14.0, 12.0), (-12.5, 16.0), **k)
    ax.annotate("corner post (to z 21.8) and the lip:\nred = in the path", (-20.0, 10.0), (-17.5, 4.0), **k)
    ax.annotate("main PCB (goes in after)", (-12.0, -0.8), (-12.0, -6.5), **k)
    ax.set_xlim(-27, 1); ax.set_ylim(-9, 43); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("x (mm)"); ax.set_ylabel("z (mm, out of the panel)")
    ax.set_title(f"2. Cut at y {yc:g}: jack 1's bottom edge and the corner post", fontsize=10, loc="left")
    f = os.path.join(OUT, "_jc_2.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    # ---- 3: cut at x 0: USB-C ----
    fig = plt.figure(figsize=(7.6, 7.6), dpi=125); ax = fig.add_axes([0.11, 0.09, 0.86, 0.84])
    poly(ax, case, "x", 0.0, "#b0bec5"); poly(ax, glow, "x", 0.0, "#c5e1a5"); poly(ax, pcb, "x", 0.0, "#2e7d32")
    poly(ax, oled, "x", 0.0, "#90caf9")
    poly(ax, usb, "x", 0.0, "#6a1b9a"); poly(ax, rcpt, "x", 0.0, "#9575cd"); poly(ax, upath, "x", 0.0, "#6a1b9a", 0.12)
    for h in hits:
        poly(ax, h, "x", 0.0, "#d32f2f")
    ax.axvline(-56.4, color="#455a64", lw=0.8, ls=":")
    ax.annotate("USB-C + its board 4.4 lower\n(board's bottom edge on the rail line)", (uy, 33.0), (-50.0, 26.0), **k)
    ax.annotate("bottom wall y -56.4..-53.9 and its lip:\nred = what a straight path from behind\nwould cut (a channel 12 wide)", (-55.0, 12.0), (-50.5, 9.0), **k)
    ax.annotate("faceplate", (-40.0, 37.5), (-38.0, 41.0), **k)
    ax.set_xlim(-60, -30); ax.set_ylim(-9, 44); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("y (mm, up the panel)"); ax.set_ylabel("z (mm)")
    ax.set_title("3. Cut at x 0: the USB-C board and the bottom wall", fontsize=10, loc="left")
    f = os.path.join(OUT, "_jc_3.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    ims = [Image.open(f) for f in outs]
    H = max(i.height for i in ims); ims = [i.resize((int(i.width * H / i.height), H)) for i in ims]
    cv = Image.new("RGB", (sum(i.width for i in ims), H + 50), "white"); x = 0
    for i in ims:
        cv.paste(i, (x, 50)); x += i.width
    ImageDraw.Draw(cv).text((20, 15), f"Knob {D['version']}, step 2: jacks 5.45 lower and USB-C 4.4 lower [Ed 10:07, 11:09], both coming in straight from "
                            "behind. Red = parts of today's case (or glow coat) in that path.", fill="black")
    out = os.path.join(OUT, "jack-corner-v031.png"); cv.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out)
    for h in hits:
        b = h.bounding_box()
        print(f"hit {sum(s.volume for s in h.solids()):.2f} mm3  x {b.min.X:.2f}..{b.max.X:.2f} y {b.min.Y:.2f}..{b.max.Y:.2f} z {b.min.Z:.2f}..{b.max.Z:.2f}")


if __name__ == "__main__":
    main()
