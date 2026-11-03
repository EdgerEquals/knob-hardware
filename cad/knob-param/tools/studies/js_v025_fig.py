# v0.25 joystick cradle in the case (3 Nov 2026 evening, joystick v0.9, [Ed 18:35 / 19:12]): the pictures for docs/img.
#   js-quarter-v025.png      3D quarter cut-away of the joystick stack (x > 0, y > place_y removed); the cradle is part of the case
#   js-sections-v025.png     the two cuts of that view, straight on (x = 0 from +x; y = place_y - 3 from the knob side)
#   js-topboard-path-v025.png  the top board going in from the back past the top corner posts (plan at the posts' bases + a cut)
# Run from cad/knob-param:  PYTHONPATH=. xvfb-run -a python tools/studies/js_v025_fig.py <out dir> [quarter|sections|path ...]
# Recipe (handover 3 Nov): build the parts, add joystick.placed(), each part (shape & region) - quadrant, tessellate, pyvista with the
# material colours, clear resin at opacity ~0.4, add_point_labels; parallel projection for the straight-on cuts.
import os, sys, math, textwrap
sys.path.insert(0, ".")
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
WHAT = sys.argv[2:] or ["quarter", "sections", "path"]


def load():
    from knobparam.assembly.section_atlas import _parts
    return _parts()


def region_parts(D, JD, parts, x0, x1, y0, y1, z0, z1, drop=None):
    """(name, shape) clipped to the box, less the 'drop' box (the quarter), skipping parts outside."""
    from build123d import Box, Pos, Align
    A = (Align.MIN, Align.MIN, Align.MIN)
    reg = Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=A)
    out = []
    for n, s in parts.items():
        try:
            bb = s.bounding_box()
        except Exception:
            continue
        if bb.max.X < x0 or bb.min.X > x1 or bb.max.Y < y0 or bb.min.Y > y1 or bb.max.Z < z0 or bb.min.Z > z1:
            continue
        try:
            q = s & reg
            if drop is not None:
                q = q - drop
        except Exception:
            continue
        if q is None:
            continue
        try:
            if not q.solids() and not q.faces():
                continue
        except Exception:
            pass
        out.append((n, q))
    return out


def to_pv(shape, tol=0.03):
    import pyvista as pv
    try:
        vs, ts = shape.tessellate(tol, 0.3)
    except Exception:
        return None
    if not ts:
        return None
    P = np.array([(v.X, v.Y, v.Z) for v in vs])
    F = np.hstack([[3, *t] for t in ts]).astype(np.int64)
    return pv.PolyData(P, F)


def scene(pl, items):
    from knobparam.assembly.colours import colour, see_through
    for n, q in items:
        m = to_pv(q)
        if m is None:
            continue
        clear = see_through(n)
        pl.add_mesh(m, color=colour(n), opacity=0.38 if clear else 1.0, smooth_shading=False, specular=0.15,
                    show_edges=False)


def labels(pl, pts):
    if not pts:
        return
    P = np.array([p for p, _ in pts]); T = [t for _, t in pts]
    pl.add_point_labels(P, T, font_size=13, point_size=6, point_color="#d81b60", text_color="black", shape_color="#f2f2f2",
                        shape_opacity=0.85, always_visible=True, render_points_as_spheres=True)



def quarter(D, JD, parts):
    import pyvista as pv
    from build123d import Box, Pos, Align
    py = JD["place_y"]
    x0, x1, y0, y1, z0, z1 = -26.0, 26.0, py - 18.0, D["panel_y1"] + 0.5, -7.5, JD["scr_top"] + 0.6
    drop = Pos(0.0, py, z0 - 1) * Box(40, 40, 80, align=(Align.MIN, Align.MIN, Align.MIN))
    items = region_parts(D, JD, parts, x0, x1, y0, y1, z0, z1, drop)
    pl = pv.Plotter(off_screen=True, window_size=(1800, 1400))
    pl.set_background("white")
    scene(pl, items)
    V = D["vb"]; Q = D["vb_pin"]
    t1 = D["vb_tabs"][-1]
    labels(pl, [
        ((0.0, py - 8.0, JD["z_bz1"] - 1.0), "grip block (screen on top)"),
        ((0.0, py, JD["z_cup0"] + 0.4), "cup in the bezel, ceiling on the stem"),
        ((0.0, py - 3.5, JD["z_sw1"] - 0.6), "switch"),
        ((D["vb_top_x"], py - 9.0, JD["z_sock0"] + 1.0), "4.5 socket, pins slide in it (they take the stack)"),
        ((-V["x"] - 0.5, (t1[0] + t1[1]) / 2, D["vb_z1"] - 0.6), f"end tab, {V['top_board_z'] - D['vb_z1']:.1f} under the top board"),
        ((-JD["nest_hw"] - 0.5, py - 6.0, JD["z_nest0"] + 2.5), "printed in the case: hanger, shoulder, ball seat"),
        ((-JD["hole_hw"] + 0.6, py - 6.0, JD["z_lip1"] - 0.5), "lip ring = cutout wall (one print)"),
        ((-JD["tb_notch_x"] - 0.6, py + JD["board_y1"] - 1.0, JD["z_db1"]), "corner notch (top board)"),
        ((-21.2, 45.35, -1.0), "top corner post base"),
        ((D["vb_face_out"] + 1.5, 37.0, 2.0), "hybrid header"),
        ((0.0, D["mcu"]["xy"][1] - 6, 1.6), "H7B0"),
        ((12.5, py - 1.5, 18.0), "hold-down spring"),
    ])
    pl.add_text(f"Joystick v0.9 on knob v0.25 (3 Nov evening, [Ed 18:35 / 19:12]): quarter cut out through the joystick axis (x > 0, y > {py:.1f} "
                "removed).\nThe cradle is printed into the case (clear); no bead, no top-edge step; the pins take the stack; the top board "
                "goes in from the back.", position="upper_left", font_size=9, color="black")
    c = np.array([0.0, py - 3.0, 18.0])
    pl.camera.position = tuple(c + np.array([95.0, 80.0, 85.0]))
    pl.camera.focal_point = tuple(c)
    pl.camera.up = (0, 0, 1)
    pl.camera.zoom(0.95)
    out = os.path.join(OUT, "js-quarter-v025.png")
    pl.screenshot(out); pl.close()
    print("wrote", out)


def sections(D, JD, parts):
    import pyvista as pv
    from build123d import Box, Pos, Align
    from PIL import Image
    py = JD["place_y"]
    x0, x1, y0, y1, z0, z1 = -26.0, 26.0, py - 18.0, D["panel_y1"] + 0.5, -4.0, JD["scr_top"] + 0.6
    outs = []
    for tag in ("A", "B"):
        if tag == "A":   # cut at x = 0, seen from +x: keep x <= 0
            drop = Pos(0.0, -50, -50) * Box(60, 200, 200, align=(Align.MIN, Align.MIN, Align.MIN))
        else:            # cut at y = place_y - 3 (through the -x guide), seen from the knob side: keep y >= that
            drop = Pos(-60, py - 3.0 - 200, -50) * Box(120, 200, 200, align=(Align.MIN, Align.MIN, Align.MIN))
        items = region_parts(D, JD, parts, x0, x1, y0, y1, z0, z1, drop)
        pl = pv.Plotter(off_screen=True, window_size=(1300, 1000))
        pl.set_background("white")
        scene(pl, items)
        V, Q = D["vb"], D["vb_pin"]
        if tag == "A":
            labels(pl, [((0.0, py, JD["scr_top"] - 0.4), "screen"), ((0.0, py - 9.0, JD["z_bz0"] + 2.0), "grip block"),
                        ((0.0, py, JD["z_cup0"] + 0.4), "cup (bezel) on the stem"), ((0.0, py + 2.0, JD["z_sw1"] - 0.5), "switch"),
                        ((0.0, py + 4.0, JD["z_db0"] + 0.5), "top board (glued under the shoulders)"),
                        ((0.0, py + JD["board_y1"] + 0.7, JD["z_nest0"] + 2.0), "end wall (printed in the case)"),
                        ((0.0, py - JD["hole_hh"] + 0.5, JD["z_fp0"] - 0.3), "flange + riser + lip ring (one print with the faceplate)"),
                        ((0.0, py + JD["hole_hh"] + 4.0, JD["z_fp0"] + 1.6), "faceplate"), ((0.0, D["mcu"]["xy"][1], 1.0), "H7B0"),
                        ((0.0, py - 8.0, 0.0), "main board")])
            cam = (np.array([0.0, py - 1.0, 19.0]), np.array([1.0, 0.0, 0.0]))
            title = "A: cut at x = 0 through the joystick axis, seen straight on from +x. y (up the panel) to the right."
        else:
            yb = py - 3.0
            labels(pl, [((0.0, yb, JD["scr_top"] - 0.4), "screen"), ((-6.5, yb, JD["g_z0"] - 0.8), "guide head"),
                        ((-6.5 - 2.0, yb, JD["g_boss0"] - 0.8), "HT-870 cushion (float above the head)"),
                        ((D["vb_top_x"], yb, JD["z_sock0"] + 0.4), "pins in the 4.5 socket"),
                        ((-V["x"], yb, 15.0), "vertical board L"), ((V["x"], yb, 15.0), "vertical board R"),
                        ((-D["vb_face_out"] - 1.5, yb, 1.3), "hybrid header (THT)"), ((0.0, yb, JD["z_db0"] + 0.5), "top board"),
                        ((-JD["nest_hw"] - 0.5, yb, JD["z_nest0"] + 1.5), "hanger + shoulder (case)"),
                        ((JD["hole_hw"] - 0.6, yb, JD["z_lip1"] - 0.6), "lip ring = cutout wall"),
                        ((12.5, py - 1.5, 20.0), "hold-down spring"), ((0.0, py - 2.7, JD["z_cup0"] + 0.3), "cup (bezel)")])
            cam = (np.array([0.0, yb, 19.0]), np.array([0.0, -1.0, 0.0]))
            title = f"B: cut at y = {py - 3.0:.1f} through the -x guide, seen straight on from the knob side. x to the right."
        c, d = cam
        pl.camera.position = tuple(c + 200 * d); pl.camera.focal_point = tuple(c); pl.camera.up = (0, 0, 1)
        pl.enable_parallel_projection(); pl.camera.parallel_scale = 29.0
        pl.add_text(title, position="lower_left", font_size=9, color="black")
        f = os.path.join(OUT, f"_js-sec-{tag}.png"); pl.screenshot(f); pl.close(); outs.append(f)
    ims = [Image.open(f) for f in outs]
    W = sum(i.width for i in ims); H = max(i.height for i in ims) + 50
    canvas = Image.new("RGB", (W, H), "white")
    x = 0
    for i in ims:
        canvas.paste(i, (x, 50)); x += i.width
    from PIL import ImageDraw
    ImageDraw.Draw(canvas).text((20, 15), "Joystick v0.9 / knob v0.25 ([Ed 18:35 / 19:12]): the cradle printed into the case; the two cuts of the "
                                "quarter view, straight on. z (out of the panel) is up.", fill="black")
    out = os.path.join(OUT, "js-sections-v025.png")
    canvas.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out)


def path(D, JD, parts):
    """The top board going in from the back on its own, past the top corner posts' bases (z -1.6..-0.42 inside the cutout plan)."""
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, Polygon as MPoly, FancyArrowPatch
    from knobparam.assembly.plan_sheet import cut, draw
    py = JD["place_y"]; V, Q = D["vb"], D["vb_pin"]; S = JD["tb_sock"]
    cx, cy = D["corners"][3]; rp = D["screw_boss_r"]
    shell = {n: q for n, q in parts.items() if n == "case" or n.startswith(("corner insert", "glow coat"))}
    fig = plt.figure(figsize=(22, 8.2), dpi=110)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.0, 1.25], wspace=0.18)
    legend = {}

    def outline(ax, pts, **k):
        ax.add_patch(MPoly(pts, closed=True, fill=False, zorder=5, **k))

    def board_outline(sx):
        x1 = JD["board_x1"]; nx = JD["tb_notch_x"]; ny0 = JD["tb_notch_y0"] + py; ycen = JD["tb_notch"][0][1] + py
        r = JD["tb_notch"][0][2]; y0b, y1b = JD["board_y0"] + py, JD["board_y1"] + py
        arc = []
        a0 = math.atan2(ny0 - ycen, x1 - abs(cx)) % (2 * math.pi)   # below-left of the post (about 230°), round its left side to 180°
        a1 = math.pi
        for i in range(31):
            a = a0 + (a1 - a0) * i / 30
            arc.append((abs(cx) + r * math.cos(a), ycen + r * math.sin(a)))
        pts = [(0, y0b), (x1, y0b), (x1, ny0)] + arc + [(nx, y1b), (0, y1b)]
        return [(sx * x, y) for x, y in pts]

    # (1) plan at the posts' bases
    ax = fig.add_subplot(gs[0, 0])
    legend.update(draw(ax, cut(shell, "z", -1.0), "plan z = −1.0 (the top corner posts' bases, under the joystick cutout) with what goes "
                       "past them from the back: the top board (notched), its sockets, the vertical boards' male headers", (8, 25), (34, 51)))
    pts = board_outline(1)
    outline(ax, pts, ec="#2e7d32", lw=1.6)
    ys0, ys1 = JD["sock_y"][0] + py, JD["sock_y"][1] + py
    xs = D["vb_top_x"]
    outline(ax, [(xs - S["w"] / 2, ys0), (xs + S["w"] / 2, ys0), (xs + S["w"] / 2, ys1), (xs - S["w"] / 2, ys1)], ec="#212121", lw=1.2, ls="--")
    hb0, hb1 = D["vb_sock_y"][0] + 0.2, D["vb_sock_y"][1] - 0.2
    fo = D["vb_face_out"]
    outline(ax, [(fo, hb0), (fo + Q["body_x"], hb0), (fo + Q["body_x"], hb1), (fo, hb1)], ec="#6a1b9a", lw=1.2, ls=":")
    outline(ax, [(V["x"] - V["t"] / 2, V["y"][0]), (V["x"] + V["t"] / 2, V["y"][0]), (V["x"] + V["t"] / 2, V["y"][1]), (V["x"] - V["t"] / 2, V["y"][1])],
            ec="#1b5e20", lw=0.8)
    th = np.linspace(0, 2 * math.pi, 120)
    ax.plot(cx + rp * np.cos(th), cy + rp * np.sin(th), color="#c62828", lw=0.8, ls="-.")
    ax.plot(cx + (rp + JD["notch_air"]) * np.cos(th), cy + (rp + JD["notch_air"]) * np.sin(th), color="#c62828", lw=0.5, ls=":")

    def gap(pxy, txt, at):
        ax.annotate(txt, pxy, at, fontsize=7.5, arrowprops=dict(arrowstyle="-", lw=0.5, color="0.25"), color="0.1")
    sc = (xs + S["w"] / 2, ys1)
    dsock = math.hypot(cx - sc[0], cy - sc[1]) - rp
    hc = (fo + Q["body_x"], hb1)
    dhdr = math.hypot(cx - hc[0], cy - hc[1]) - rp
    gap(sc, f"socket R corner: {dsock:.2f} from the post (TIGHT)", (8.5, 41.0))
    gap(hc, f"male header R body: {dhdr:.2f} from the post", (8.5, 39.5))
    gap((JD["tb_notch_x"], cy), f"notch {JD['tb_notch_size'][0]:.2f} × {JD['tb_notch_size'][1]:.2f}:\nboard {JD['notch_air']:.2f} from the post",
        (8.5, 47.0))
    gap((cx - rp + 0.3, cy - 1.8), "post base (case), z −1.6..−0.42", (19.0, 36.0))
    gap((cx - 1.75, cy + 0.6), "brass insert", (21.5, 50.3))
    ax.plot([], [], color="#2e7d32", lw=1.6, label="top board (v0.25, notched)")
    ax.plot([], [], color="#212121", lw=1.2, ls="--", label=f"socket R (x {xs:g} ± 1.0, y {ys0:.1f}..{ys1:.1f})")
    ax.plot([], [], color="#6a1b9a", lw=1.2, ls=":", label="male header R body (0.3 inboard)")
    ax.plot([], [], color="#c62828", lw=0.8, ls="-.", label="post Ø6.5 (dotted: + 0.3)")
    ax.legend(loc="lower left", fontsize=7).set_zorder(10)
    # (2) straight-on cut at y = the posts' centres, the board coming up from the back
    ax = fig.add_subplot(gs[0, 1])
    legend.update(draw(ax, cut(shell, "y", cy), f"cut at y = {cy:.2f} (through both top corner posts), seen from the knob side: the "
                       "top board rises from behind the case, past the posts' bases, to its printed nest", (-26, 26), (-6, 40),
                       xlabel="x (mm)", ylabel="z (mm)"))
    for z0, ls, lw in ((-6.0, ":", 0.8), (-1.6, "--", 1.0), (JD["z_db0"], "-", 1.6)):
        xh = JD["tb_notch_x"]
        ax.add_patch(MPoly([(-xh, z0), (xh, z0), (xh, z0 + 1.0), (-xh, z0 + 1.0)], closed=True, fill=False, ec="#2e7d32", ls=ls, lw=lw))
    ax.add_patch(FancyArrowPatch((0, -4.5), (0, JD["z_db0"] - 0.6), arrowstyle="-|>", mutation_scale=18, color="#d81b60", lw=1.4))
    ax.text(0.6, 12, "top board, on its own,\nfrom the back (+z)", fontsize=8, color="#d81b60")
    ax.annotate(f"at this y the notched board is ±{JD['tb_notch_x']:.2f}", (JD["tb_notch_x"], -1.1), (3.0, 4.0), fontsize=7.5,
                arrowprops=dict(arrowstyle="-", lw=0.5))
    ax.annotate("printed hanger + shoulder (case)", (JD["nest_hw"] + 0.5, JD["z_nest0"] + 1.5), (8.0, 24.0), fontsize=7.5,
                arrowprops=dict(arrowstyle="-", lw=0.5))
    # (3) plan just under the top board: what sits by the notch
    ax = fig.add_subplot(gs[0, 2])
    js_ = {n: q for n, q in parts.items() if n.startswith(("joystick: joystick top board", "joystick: top-board socket",
                                                             "joystick: screen FPC socket", "joystick: SW1"))}
    legend.update(draw(ax, cut(dict(shell, **js_), "z", JD["z_db0"] + 0.5), f"plan z = {JD['z_db0'] + 0.5:.1f} (in the top board) with the "
                       "sockets under it (dashed) and the screen socket on top (dotted): nothing sits in the notches", (-24, 24), (24, 52)))
    for sx in (-1, 1):
        outline(ax, [(sx * xs - S["w"] / 2, ys0), (sx * xs + S["w"] / 2, ys0), (sx * xs + S["w"] / 2, ys1), (sx * xs - S["w"] / 2, ys1)],
                ec="#212121", lw=1.0, ls="--")
        ax.plot(sx * cx + rp * np.cos(th), cy + rp * np.sin(th), color="#c62828", lw=0.8, ls="-.")
    sl_, ss_, _ = JD["db_fpc_sock"]; fx = JD["db_sock_x"]
    outline(ax, [(fx - ss_ / 2, py - sl_ / 2), (fx + ss_ / 2, py - sl_ / 2), (fx + ss_ / 2, py + sl_ / 2), (fx - ss_ / 2, py + sl_ / 2)],
            ec="#ffeb3b", lw=1.6, ls=":")
    ax.annotate("screen FPC socket (top face): body 0.19 from the notch [C: its end pad in KiCad]", (fx + ss_ / 2, py + sl_ / 2), (-20, 50.5),
                fontsize=7.5, arrowprops=dict(arrowstyle="-", lw=0.5))
    ax.annotate(f"sockets {JD['sock_y_shift']:+g} toward the knob [A]", (xs, ys0 + 2), (2.0, 26.0), fontsize=7.5,
                arrowprops=dict(arrowstyle="-", lw=0.5))
    fig.suptitle(textwrap.fill("Joystick v0.9 / knob v0.25 [Ed 18:35]: the top board goes in from the back on its own and is glued up under the "
                               "shoulders printed in the case. Corner notches take it past the top corner posts' bases (it caught them by ~1 in "
                               "v0.24); its sockets and the vertical boards' male headers pass them because the pin rows moved 0.3 inboard "
                               "[Ed 19:12 (4)] and 2.5 toward the knob [A].", 175), fontsize=11, x=0.01, ha="left")
    fig.legend(handles=[Patch(fc=c, ec="k", lw=0.3, label=l) for l, c in sorted(legend.items())], loc="lower center", ncol=6, fontsize=7.5,
               frameon=False)
    out = os.path.join(OUT, "js-topboard-path-v025.png")
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    D, JD, parts = load()
    for w in WHAT:
        {"quarter": quarter, "sections": sections, "path": path}[w](D, JD, parts)
