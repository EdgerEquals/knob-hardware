# Step-1 follow-ups in the model (3 Nov 2026, joystick v0.8 / knob v0.24 draft): the pictures for docs/img.
#   js-quarter-v024.png   3D quarter cut-away of the joystick stack (x > 0, y > place_y removed)
#   js-sections-v024.png  the two cuts of that view, straight on (x = 0 from +x; y = place_y from the knob side)
#   js-boards-v024.png    the vertical boards: hybrid bottom headers, male pins into the top board's sockets, end tabs, encoder riser
# Run from cad/knob-param:  PYTHONPATH=. xvfb-run -a python tools/studies/js_v024_fig.py <out dir> [quarter|sections|boards ...]
# Recipe (handover 3 Nov): build the parts, add joystick.placed(), each part (shape & region) - quadrant, tessellate, pyvista with the
# material colours, clear resin at opacity ~0.4, add_point_labels; parallel projection for the straight-on cuts.
import os, sys, math, textwrap
sys.path.insert(0, ".")
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
WHAT = sys.argv[2:] or ["quarter", "sections", "boards"]


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
    labels(pl, [
        ((0.0, py - 8.0, JD["z_bz1"] - 1.0), "grip block (screen on top)"),
        ((0.0, py, JD["z_cup0"] + 0.4), "cup in the bezel, ceiling on the stem"),
        ((0.0, py - 3.5, JD["z_sw1"] - 0.6), "switch (its click is the press)"),
        ((D["vb_top_x"], py - 5.0, JD["z_sock0"] + 1.0), "13-way 1.27 socket, male pins in"),
        ((V["x"] + 0.5, (D["vb_tabs"][0][0] + D["vb_tabs"][0][1]) / 2, V["top_board_z"] - 1.0), "end tab = post (bears on the top board)"),
        ((D["vb_face_out"] + 1.5, 29.0, 2.0), "hybrid header: SMT legs over the riser"),
        ((D["vb_face_out"] + 1.5, 37.0, 2.0), "THT legs"),
        ((0.0, py + JD["hole_hh"] + 0.6, JD["z_dam1"] + 0.2), "rebate + dam + bead (top edge)"),
        ((JD["fl_x1"] - 0.4, py - 8.0, JD["z_fl1"]), "flange on the silicone bead"),
        ((0.0, D["mcu"]["xy"][1] - 6, 1.6), "H7B0"),
        ((12.5, py - 1.5, 18.0), "hold-down spring"),
    ])
    pl.add_text(f"Joystick v0.8 on knob v0.24 draft (3 Nov, step-1 follow-ups): quarter cut out through the joystick axis (x > 0, y > {py:.1f} "
                "removed).\nNo press springs, grubs or peg; pins into sockets; the vertical boards are the posts; no standoff.",
                position="upper_left", font_size=9, color="black")
    c = np.array([0.0, py - 3.0, 18.0])
    pl.camera.position = tuple(c + np.array([95.0, 80.0, 85.0]))
    pl.camera.focal_point = tuple(c)
    pl.camera.up = (0, 0, 1)
    pl.camera.zoom(0.95)
    out = os.path.join(OUT, "js-quarter-v024.png")
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
                        ((0.0, py + 4.0, JD["z_db0"] + 0.5), "top board"), ((0.0, py + JD["hole_hh"] + 0.6, JD["z_dam1"] - 0.3),
                        "dam + bead in the rebate"), ((0.0, py - JD["hole_hh"] - 1.4, JD["z_fl1"] - 0.6), "flange on the bead (knob side)"),
                        ((0.0, py + JD["hole_hh"] + 4.0, JD["z_fp0"] + 1.6), "faceplate"), ((0.0, D["mcu"]["xy"][1], 1.0), "H7B0"),
                        ((0.0, py - 8.0, 0.0), "main board")])
            cam = (np.array([0.0, py - 1.0, 19.0]), np.array([1.0, 0.0, 0.0]))
            title = f"A: cut at x = 0 through the joystick axis, seen straight on from +x. y (up the panel) to the right."
        else:
            yb = py - 3.0
            labels(pl, [((0.0, yb, JD["scr_top"] - 0.4), "screen"), ((-6.5, yb, JD["g_z0"] - 0.8), "guide head"),
                        ((-6.5 - 2.0, yb, JD["g_boss0"] - 0.8), "cushion ring (float above the head)"),
                        ((D["vb_top_x"], yb, JD["z_sock0"] + 0.4), "pins in the 1.27 socket"),
                        ((-V["x"], yb, 15.0), "vertical board L"), ((V["x"], yb, 15.0), "vertical board R"),
                        ((-D["vb_face_out"] - 1.5, yb, 1.3), "hybrid header (THT)"), ((0.0, yb, JD["z_db0"] + 0.5), "top board"),
                        ((JD["fl_x1"] - 0.4, yb, JD["z_fl1"] + 0.2), "bead (long side)"), ((12.5, py - 1.5, 20.0), "hold-down spring"),
                        ((0.0, py - 2.7, JD["z_cup0"] + 0.3), "cup (bezel)")])
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
    ImageDraw.Draw(canvas).text((20, 15), "Joystick v0.8 / knob v0.24 draft (step-1 follow-ups): the two cuts of the quarter view, straight on. "
                                "z (out of the panel) is up.", fill="black")
    out = os.path.join(OUT, "js-sections-v024.png")
    canvas.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out)


def boards(D, JD, parts):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, Circle, Rectangle
    from knobparam.assembly.plan_sheet import cut, draw
    py = JD["place_y"]; V, H, Q = D["vb"], D["vb_hdr"], D["vb_pin"]
    a = math.radians(D["mech_rot"]); ca, sa = math.cos(a), math.sin(a)
    enc = [(ca * x - sa * y, sa * x + ca * y) for x, y in D["enc_pin_xy"]]
    fig = plt.figure(figsize=(22, 15), dpi=110)
    gs = fig.add_gridspec(2, 3, hspace=0.25, wspace=0.18)
    legend = {}

    _draw = draw

    def draw(ax, layer, title, *a, **k):   # wrapped panel titles
        return _draw(ax, layer, textwrap.fill(title, 70), *a, **k)

    def ann(ax, txt, xy, xyt):
        ax.annotate(txt, xy, xyt, fontsize=7.5, arrowprops=dict(arrowstyle="-", lw=0.5, color="0.25"), color="0.1")

    def legs(ax):
        for sx in (-1, 1):
            for x, y, k in D["vb_legs"][sx]:
                if k == "tht":
                    ax.add_patch(Circle((x, y), H["pad"] / 2, fc="none", ec="#d81b60", lw=0.8))
                else:
                    ax.add_patch(Rectangle((x - H["pad"] / 2, y - H["pad"] / 2), H["pad"], H["pad"], fc="none", ec="#1565c0", lw=0.8))
        for k, (x, y) in enumerate(enc):
            tht = k in D["enc_header_tht"]
            ax.add_patch(Circle((x, y), 0.6, fc="none", ec="#d81b60" if tht else "#1565c0", lw=1.0, ls="-" if tht else "--"))

    # (1) plan at the main-board front
    ax = fig.add_subplot(gs[0, 0])
    legend.update(draw(ax, cut(parts, "z", 0.4), "plan z = 0.4: main-board front. Hybrid two-row 1.27 headers: circles THT legs, squares SMT legs "
                       "(R over the encoder riser); dashed circles: the riser's SMT pins on the back, solid: its THT pins", (-24, 24), (20, 50)))
    legs(ax)
    ann(ax, f"R: {sum(k == 'smt' for *_, k in D['vb_legs'][1])} SMT legs over y {H['smt'][0][1]:g}-{H['smt'][0][2]:g}\n"
            f"{sum(k == 'tht' for *_, k in D['vb_legs'][1])} THT legs above", (18.67, 29.0), (4.0, 22.0))
    ann(ax, f"L: {len(D['vb_legs'][-1])} THT legs", (-18.67, 35.0), (-23.0, 22.5))
    ann(ax, "riser THT pins (inner end)", enc[5], (-9.5, 21.0))
    ann(ax, f"rows stop at y {H['y_max'][0]:g} / {H['y_max'][1]:g}:\n1.0+ from the corner notch", (18.67, 39.8), (6.0, 47.5))
    # (2) plan behind the main board
    ax = fig.add_subplot(gs[0, 1])
    legend.update(draw(ax, cut(parts, "z", -2.2), "plan z = −2.2: behind the main board. THT leg tails, the encoder riser's header "
                       "(2 THT pins through the board, 4 SMT under R's foot), no standoffs; the joystick rear anchor", (-24, 24), (20, 50)))
    legs(ax)
    ann(ax, "no standoffs (v0.23 had two)", (15.5, 26.9), (3.0, 21.5))
    # (3) cross cut through R's SMT region and the riser
    ax = fig.add_subplot(gs[0, 2])
    yc = 30.3
    legend.update(draw(ax, cut(parts, "y", yc), f"y = {yc}: across R's SMT legs and the encoder riser (viewed from below the panel)",
                       (2, 24), (-9, 33), xlabel="x (mm)", ylabel="z (mm)"))
    ann(ax, "SMT legs: nothing comes through", (17.4, 0.3), (19.0, 6.0))
    ann(ax, f"encoder riser, {D['enc_standoff_h']:.1f} off the back", (12.0, -5.8), (6.5, -8.5))
    ann(ax, "male pins up into the socket", (D["vb_top_x"], JD["z_sock0"] + 1.0), (8.0, 24.0))
    # (4) side cut through R's board plane: tabs and the lowered edge
    ax = fig.add_subplot(gs[1, 0])
    legend.update(draw(ax, cut(parts, "x", V["x"]), f"x = {V['x']:g}: vertical board R in its plane. End tabs (posts) up to the top board, the "
                       f"edge {Q['sock_h'] + Q['sock_clear']:.1f} lower between them", (22, 52), (-4, 34), xlabel="y (mm, panel)", ylabel="z (mm)"))
    t0, t1 = D["vb_tabs"]
    ann(ax, f"tab {t0[1] - t0[0]:.1f} wide", ((t0[0] + t0[1]) / 2, 29.0), (23.0, 33.0))
    ann(ax, f"tab {t1[1] - t1[0]:.1f}", ((t1[0] + t1[1]) / 2, 29.0), (47.0, 33.0))
    ann(ax, "no standoff hole", (31.0, 15.0), (36.0, 12.0))
    # (5) side cut through the pin row
    ax = fig.add_subplot(gs[1, 1])
    xr = D["vb_top_x"]
    legend.update(draw(ax, cut(parts, "x", xr), f"x = {xr:g}: the pin row. {Q['n']} male pins in the 13-way socket under the top board "
                       f"({D['vb_eng_nom']:.2f} engaged of {Q['sock_ins'][0]:g}-{Q['sock_ins'][1]:g}); the right-angle header body under them",
                       (22, 52), (18, 34), xlabel="y (mm, panel)", ylabel="z (mm)"))
    # (6) top board underside plan
    ax = fig.add_subplot(gs[1, 2])
    legend.update(draw(ax, cut(parts, "z", JD["z_db0"] - 0.3), f"plan z = {JD['z_db0'] - 0.3:.1f}: just under the top board. The two "
                       "sockets, the tabs bearing beside them, the cradle's hangers", (-24, 24), (20, 52)))
    ann(ax, "tab", (V["x"], (t0[0] + t0[1]) / 2), (5.0, 23.0))
    ann(ax, "socket R", (D["vb_top_x"], 37.0), (6.0, 40.0))
    fig.suptitle(textwrap.fill("Joystick v0.8 / knob v0.24 draft (3 Nov, step-1 follow-ups [Ed 13:31-14:08]): vertical boards on hybrid two-row "
                               "1.27 headers (no standoff), male 1.27 pins into 13-way sockets under the top board, end tabs as posts; "
                               "the encoder riser on a hybrid 6-pin header (no standoffs).", 170), fontsize=11, x=0.01, ha="left")
    fig.legend(handles=[Patch(fc=c, ec="k", lw=0.3, label=l) for l, c in sorted(legend.items())], loc="lower center", ncol=5, fontsize=7.5,
               frameon=False)
    out = os.path.join(OUT, "js-boards-v024.png")
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    D, JD, parts = load()
    for w in WHAT:
        {"quarter": quarter, "sections": sections, "boards": boards}[w](D, JD, parts)
