"""Section atlas [Ed 2 Nov 13:23]: the complete assembly as it stands (knob stack, case, joystick), drawn whole and in many sections.

Sheets, all in the panel frame (x across the panel, y up the panel, z out of the panel, PCB front = 0):
  1  overall: front view, iso, iso half-section (x < 0 kept), rear iso
  2  horizontal slices every 2.5 mm, from the back cover to the knob screen
  3  vertical slices front to back (x = const), every 5 mm across the panel
  4  vertical slices across (y = const) through the main features
  5  oblique slices: vertical planes at angles through the knob axis and the joystick, and two tilted planes
Run from cad/knob-param:  PYTHONPATH=. python -m knobparam.assembly.section_atlas   (xvfb-run -a for sheet 1 if headless)."""
import math, os, sys, textwrap, time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from .plan_sheet import cut, draw, colour


def _parts():
    from knobparam.common import model
    from knobparam.assembly.build import build_all, view
    from knobparam.assembly import joystick as js
    D = model.derive(model.default_params())
    parts, stats, keys, owner = build_all(D)
    parts, keys = view(parts, keys, D, "panel")
    jp, JD = js.placed()
    parts = dict(parts); parts.update(jp)
    # [Ed 3 Nov] v0.23: the H7B0 (LQFP100) is an electronics part on the board front under the joystick; D is whole
    return D, JD, parts


def _moved(parts, loc):
    out = {}
    for n, s in parts.items():
        try:
            out[n] = loc * s
        except Exception:
            pass
    return out


def vertical_plane(parts, x0, y0, deg):
    """Vertical plane through (x0, y0), running at deg from +x. Returns cut layers in (u, z): u along the plane."""
    from build123d import Pos, Rot
    loc = Rot(0, 0, -deg) * Pos(-x0, -y0, 0)
    return cut(_moved(parts, loc), "y", 0.0)


def tilted_plane(parts, y0, z0, tilt):
    """Plane through (0, y0, z0) containing the x direction, tilted 'tilt' degrees from vertical (top leaning toward +y)."""
    from build123d import Pos, Rot
    loc = Rot(tilt, 0, 0) * Pos(0, -y0, -z0)
    return cut(_moved(parts, loc), "y", 0.0)


def _limits(layer, pad=3.0, fallback=((-30, 30), (-20, 60))):
    xs, ys = [], []
    for _, _, _, tris in layer:
        for t in tris:
            for x, y in t:
                xs.append(x); ys.append(y)
    if not xs:
        return fallback
    return (min(xs) - pad, max(xs) + pad), (min(ys) - pad, max(ys) + pad)


def _legend(fig, legend, ax):
    ax.axis("off")
    ax.legend(handles=[Patch(fc=c, ec="k", lw=0.3, label=l) for l, c in sorted(legend.items())], loc="upper left",
              fontsize=7, frameon=False, title="materials", title_fontsize=8)


def _save(fig, out):
    """Pull the grid up under the title (matplotlib's default top margin is a fraction of a very tall figure)."""
    H = fig.get_figheight()
    st = fig._suptitle
    lines = st.get_text().count("\n") + 1 if st is not None else 0
    if st is not None:
        st.set_y(1 - 0.15 / H); st.set_va("top")
    fig.subplots_adjust(top=1 - (0.75 + 0.27 * lines) / H)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out, flush=True)


def _label_for(z, named):
    best = min(named, key=lambda kv: abs(kv[0] - z)) if named else None
    return best[1] if best and abs(best[0] - z) <= 1.3 else ""


def _z_levels(D, JD, step):
    """A slice every 'step' mm from the back cover to the knob screen, with the key feature levels swapped in."""
    feats = [(D["amo_upper_z"][0] + D["amo_t"] / 2, "rear AMOLED"), (D["amo_lower_z"][0] + D["amo_t"] / 2, "front AMOLED"),
             ((D["fg_z_top"] + D["fg_z_bot"]) / 2, "feel compound gear"), (D["z_pcb_back"] - 0.6, "PCB back: emitters"),
             (D["z_pcb_back"] / 2, "main PCB (windows)"), (0.5, "PCB front: Hall sensors, clear OLED, H7B0, vertical-board headers"),
             (D["hb_mid"], "herringbone ring band"), (5.0, "Hall arm, detent, lever"), (12.0, "1220 and 716 cans"),
             (20.0, "jack bodies, knob shell"), ((JD["z_db0"] + JD["z_db1"]) / 2, "joystick top board on the vertical boards' end tabs"),
             (15.0, "vertical boards (no standoff since v0.24)"), (D["vb_ze"] - 1.0, "vertical boards' male 1.27 headers"),
             ((JD["z_sock0"] + JD["z_db0"]) / 2, "1.27 pins in the top board's sockets, the end tabs (posts)"),
             ((JD["z_fl0"] + JD["z_fl1"]) / 2, "joystick case cradle: flange behind the faceplate"),
             (JD["z_sw1"] - 0.3, "joystick switch, guide heads"), (JD["z_ball"], "joystick balls in their cups"),
             ((D["z_fp0"] + D["z_fp1"]) / 2, "faceplate, joystick carrier floor"), ((JD["z_bz0"] + JD["z_roof"]) / 2, "joystick grip block"),
             ((JD["z_scr0"] + JD["scr_top"]) / 2, "joystick glass"), (JD["z_knob_top"] - 0.5, "knob, top of the shell")]
    if "h_big_top" in D:
        feats.append(((D["h_big_top"] + D["h_big_bot"]) / 2, "encoder disc"))
    if D.get("cart"):   # v0.24 [Ed 3 Nov 12:41] dial screen as a bezel cartridge
        feats += [(D["db_z0"] - 0.5, "dial board underside: ESP32, diode, LEDs in the pocket"),
                  ((D["db_z0"] + D["db_z1"]) / 2, "dial board on the ledge; magnets and pins in the land"),
                  ((D["bz_boss_z"][0] + D["pad_z"][0]) / 2 + 0.2, "cartridge: bosses, plug pad, tail's lower leg"),
                  ((D["patch_z0"] + D["lcm_z0"]) / 2, "panel's flex patches, pad arm"),
                  ((D["bend_z"][0] + D["bend_z"][1]) / 2, "panel and its bends under the glass seat"),
                  ((D["lens_step_z"] + D["z_top"]) / 2, "lens step in the bezel lap")]
    grid, z = [], math.floor(D["z_cover_out"] + 0.5)
    while z <= D["z_top"] - 0.5:
        grid.append(z); z += step
    lv = list(feats) + [(g, "") for g in grid if min(abs(g - f) for f, _ in feats) > 0.9]
    return sorted(((round(z, 2), l) for z, l in lv), key=lambda t: t[0])


def sheet_horizontal(D, JD, parts, out, step=2.5):
    lv = _z_levels(D, JD, step)
    ncol = 7
    nrow = math.ceil((len(lv) + 1) / ncol)
    fig = plt.figure(figsize=(ncol * 3.3, nrow * 7.4), dpi=100)
    gs = fig.add_gridspec(nrow, ncol, hspace=0.30, wspace=0.18)
    xl, yl = (-27, 27), (D["panel_y0"] - 2, D["panel_y1"] + 2)
    legend = {}
    t0 = time.time()
    for i, (z, lab) in enumerate(lv):
        ax = fig.add_subplot(gs[i // ncol, i % ncol])
        lay = cut(parts, "z", z)
        legend.update(draw(ax, lay, f"z {z:+.2f}" + ("\n" + "\n".join(textwrap.wrap(lab, 30)) if lab else ""), xl, yl))
        print(f"  z {z:+.2f}: {len(lay)} parts ({time.time() - t0:.0f} s)", flush=True)
    _legend(fig, legend, fig.add_subplot(gs[len(lv) // ncol, len(lv) % ncol]))
    fig.suptitle(f"Knob module {D['version']}: slices parallel to the panel face, every {step:g} mm plus the key levels "
                 f"(looking at the panel face; z from the main-PCB front, + out toward the knob).\n"
                 f"Lying flat on the bench these are the horizontal slices; in the rack they stand vertical.", fontsize=15, x=0.01, ha="left")
    _save(fig, out)


def sheet_long(D, parts, out, xs=(-20, -16, -15, -10, -5, 0, 5, 10, 15, 16, 20)):
    ncol = 3
    nrow = math.ceil(len(xs) / ncol)
    fig = plt.figure(figsize=(ncol * 8.2, nrow * 5.6 + 1.5), dpi=100)
    gs = fig.add_gridspec(nrow + 1, ncol, height_ratios=[5.6] * nrow + [1.5], hspace=0.32, wspace=0.12)
    yl, zl = (D["panel_y0"] - 2, D["panel_y1"] + 2), (D["z_cover_out"] - 2, D["z_top"] + 2)
    legend = {}
    for i, x in enumerate(xs):
        ax = fig.add_subplot(gs[i // ncol, i % ncol])
        lay = cut(parts, "x", float(x))
        legend.update(draw(ax, lay, f"x = {x:+d} mm (front to back; knob axis at y 0, joystick at y {D['place_y']:.1f})",
                           yl, zl, xlabel="y (mm, up the panel)", ylabel="z (mm)"))
        print(f"  x {x:+d}: {len(lay)} parts", flush=True)
    _legend(fig, legend, fig.add_subplot(gs[nrow, :]))
    fig.suptitle(f"Knob module {D['version']}: vertical slices front to back (x = const), viewed from +x", fontsize=15, x=0.01, ha="left")
    _save(fig, out)


def sheet_across(D, JD, parts, out):
    py = D["place_y"]
    a = math.radians(D["mech_rot"]); ex, ey = D["enc_xy"]; enc_y = math.sin(a) * ex + math.cos(a) * ey
    cuts = [(py + JD["by_top"], "joystick top balls and their seats on the case cradle"), (py + 3.0, "joystick guide (+x): head, cushion, sleeve"),
            (py, "joystick axis: switch, the bezel's cup, guides, hold-down springs"), (py - JD["by_bot"], "joystick knob-side balls and seats"),
            (D["vb_legs"][1][3][1], "vertical boards' hybrid headers (R: SMT legs over the encoder riser)"),
            (enc_y, "encoder wheel"), (0.0, "knob axis"), (-10.0, "1220 motor and lower knob"),
            (D["clear_oled_xy"][1], "clear OLED centre, window D (whole again)"),
            (D["mcu"]["xy"][1], "the H7B0 (LQFP100) on the board front under the joystick, between the vertical boards"),
            (D["jack_y"], "jacks"), (D["usb_xy"][1], "USB-C"),
            (D["corners"][0][1], "bottom corner posts")]
    ncol = 4
    nrow = math.ceil((len(cuts) + 1) / ncol)
    fig = plt.figure(figsize=(ncol * 5.4, nrow * 6.6), dpi=100)
    gs = fig.add_gridspec(nrow, ncol, hspace=0.32, wspace=0.16)
    xl, zl = (-27, 27), (D["z_cover_out"] - 2, D["z_top"] + 2)
    legend = {}
    for i, (y, what) in enumerate(cuts):
        ax = fig.add_subplot(gs[i // ncol, i % ncol])
        lay = cut(parts, "y", float(y))
        legend.update(draw(ax, lay, f"y = {y:+.1f}: " + "\n".join(textwrap.wrap(what, 40)), xl, zl, xlabel="x (mm)", ylabel="z (mm)"))
        print(f"  y {y:+.1f}: {len(lay)} parts", flush=True)
    _legend(fig, legend, fig.add_subplot(gs[len(cuts) // ncol, len(cuts) % ncol]))
    fig.suptitle(f"Knob module {D['version']}: slices across the panel (y = const), viewed from below the panel. "
                 f"In the rack these are the horizontal slices.", fontsize=15, x=0.01, ha="left")
    _save(fig, out)


def sheet_oblique(D, JD, parts, out):
    py = D["place_y"]
    jobs = [("v", 0.0, 0.0, 30, "knob axis, 30°"), ("v", 0.0, 0.0, 45, "knob axis, 45°"), ("v", 0.0, 0.0, 60, "knob axis, 60°"),
            ("v", 0.0, 0.0, 120, "knob axis, 120°"), ("v", 0.0, 0.0, 135, "knob axis, 135°"), ("v", 0.0, 0.0, 150, "knob axis, 150°"),
            ("v", 0.0, py, 35, f"joystick centre, 35° (through two ball corners)"),
            ("v", 0.0, py, 145, "joystick centre, 145° (the other diagonal)"),
            ("v", 9.0, 0.0, 90, "off-axis, x = +9 (through the 1220 side of the knob)"),
            ("v", -12.0, 0.0, 70, "off-axis, through x −12 at 70°"),
            ("t", 0.0, 20.0, 25, "tilted plane through the knob axis at z 20, leaning 25° toward the joystick\n"
                                  "as it comes out of the panel"),
            ("t", py, JD["z_ball"], -30, "tilted plane through the joystick axis at the ball height, leaning 30°\n"
                                         "toward the knob as it comes out of the panel"),
            ("v", D["mcu"]["xy"][0], D["mcu"]["xy"][1], 25, "through the H7B0 (LQFP100), 25°"),
            ("v", D["mcu"]["xy"][0], D["mcu"]["xy"][1], 155, "through the H7B0 (LQFP100), 155°"),
            ("t", D["mcu"]["xy"][1], 0.8, 35, f"tilted plane through the board front at y {D['mcu']['xy'][1]:g} (the H7B0), leaning 35°\n"
                                              "toward the knob as it comes out of the panel")]
    ncol = 3
    nrow = math.ceil(len(jobs) / ncol)
    fig = plt.figure(figsize=(ncol * 7.6, nrow * 5.8 + 1.6), dpi=100)
    gs = fig.add_gridspec(nrow + 1, ncol, height_ratios=[5.8] * nrow + [1.6], hspace=0.34, wspace=0.14)
    legend = {}
    for i, (kind, a, b, deg, what) in enumerate(jobs):
        ax = fig.add_subplot(gs[i // ncol, i % ncol])
        if kind == "v":
            lay = vertical_plane(parts, a, b, deg)
            xl, yl = _limits(lay)
            title = f"vertical plane, {what}\n(u along the plane; plan angle {deg}° from +x)"
            xlab, ylab = "u (mm along the plane)", "z (mm)"
        else:
            lay = tilted_plane(parts, a, b, deg)
            xl, yl = _limits(lay)
            title = what
            xlab, ylab = "x (mm)", "along the tilted plane (mm)"
        legend.update(draw(ax, lay, title, xl, yl, xlabel=xlab, ylabel=ylab))
        print(f"  oblique {i + 1}: {len(lay)} parts", flush=True)
    _legend(fig, legend, fig.add_subplot(gs[nrow, :]))
    fig.suptitle(f"Knob module {D['version']}: oblique and off-axis slices", fontsize=15, x=0.01, ha="left")
    _save(fig, out)


def sheet_overall(D, parts, out, tol=0.08):
    """Front view, iso, iso half-section (x < 0 kept), rear iso. The resin case is drawn see-through."""
    import numpy as np
    import pyvista as pv
    pv.OFF_SCREEN = True
    os.makedirs(os.path.dirname(out), exist_ok=True)
    meshes = []
    for n, s in parts.items():
        try:
            vs, ts = s.tessellate(tol)
        except Exception:
            continue
        if not ts:
            continue
        P = np.array([(v.X, v.Y, v.Z) for v in vs]); T = np.array(ts)
        m = pv.PolyData(P, np.hstack([np.full((len(T), 1), 3), T]).ravel())
        _, c = colour(n)
        see = n in ("case",) or n.startswith(("glow coat", "back cover")) or "clear OLED" in n or "glass" in n
        meshes.append((n, m, c, see))
    print(f"  meshed {len(meshes)} parts", flush=True)
    views = [("front (looking at the panel)", (0, 0, 1), (0, 1, 0), False),
             ("iso, front left", (-1.0, -1.1, 1.0), (0, 0, 1), False),
             ("iso half-section: everything with x > 0 removed", (1.2, -0.9, 0.8), (0, 0, 1), True),
             ("rear iso (the back cover)", (0.9, -0.8, -1.0), (0, 0, 1), False)]
    imgs = []
    for title, d, up, clip in views:
        pl = pv.Plotter(off_screen=True, window_size=(1800, 2000)); pl.set_background("white")
        for n, m, c, see in meshes:
            mm = m
            if clip:
                try:
                    mm = m.clip(normal="x", origin=(0, 0, 0), invert=True)
                except Exception:
                    continue
                if mm.n_points == 0:
                    continue
            op = 0.22 if (see and not clip) else (0.45 if see else 1.0)
            pl.add_mesh(mm, color=c, opacity=op, specular=0.1, ambient=0.3, diffuse=0.75, smooth_shading=False)
        cen = np.array([0.0, (D["panel_y0"] + D["panel_y1"]) / 2, 15.0]); dd = np.array(d, float); dd /= np.linalg.norm(dd)
        pl.camera.position = tuple(cen + 600 * dd); pl.camera.focal_point = tuple(cen); pl.camera.up = up
        pl.enable_parallel_projection(); pl.camera.parallel_scale = 75
        pl.enable_anti_aliasing("ssaa")
        path = out.replace(".png", f"-v{len(imgs)}.png")
        pl.screenshot(path); pl.close()
        imgs.append((title, path))
        print("  view:", title, flush=True)
    fig, axs = plt.subplots(2, 2, figsize=(22, 25), dpi=100, gridspec_kw=dict(hspace=0.06, wspace=0.02))
    for ax, (title, path) in zip(axs.ravel(), imgs):
        im = plt.imread(path)
        nz = np.where((im[..., :3] < 0.97).any(-1))
        if len(nz[0]):
            im = im[max(nz[0].min() - 10, 0): nz[0].max() + 10, max(nz[1].min() - 10, 0): nz[1].max() + 10]
        ax.imshow(im); ax.axis("off"); ax.set_title(title, fontsize=13, loc="left")
        os.remove(path)
    legend = {}
    for n, _, c, _ in meshes:
        l, _c = colour(n); legend.setdefault(l, _c)
    fig.legend(handles=[Patch(fc=c, ec="k", lw=0.3, label=l) for l, c in sorted(legend.items())], loc="lower center", ncol=4,
               fontsize=11, frameon=False)
    fig.suptitle(f"Knob module {D['version']}: complete assembly (knob stack, case, joystick v0.7 on the vertical boards; H7B0 LQFP100 on the board front under the joystick). "
                 "Resin case drawn see-through.",
                 fontsize=16, x=0.01, ha="left")
    fig.subplots_adjust(bottom=0.08, left=0.01, right=0.99)
    _save(fig, out)


def main():
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, here)
    only = set(sys.argv[1:])
    t0 = time.time()
    D, JD, parts = _parts()
    print(f"{len(parts)} parts ({time.time() - t0:.0f} s)", flush=True)
    base = os.path.join(os.path.dirname(here), "assemblies", f"knob-stack-{D['version']}", "atlas")
    v = D["version"]
    if not only or "overall" in only:
        sheet_overall(D, parts, os.path.join(base, f"{v}-atlas-1-overall.png"))
    if not only or "horizontal" in only:
        sheet_horizontal(D, JD, parts, os.path.join(base, f"{v}-atlas-2-parallel-to-panel.png"))
    if not only or "long" in only:
        sheet_long(D, parts, os.path.join(base, f"{v}-atlas-3-front-to-back.png"))
    if not only or "across" in only:
        sheet_across(D, JD, parts, os.path.join(base, f"{v}-atlas-4-across.png"))
    if not only or "oblique" in only:
        sheet_oblique(D, JD, parts, os.path.join(base, f"{v}-atlas-5-oblique.png"))
    print(f"done {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
