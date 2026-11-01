"""Colour sheets for the case: section, isometric, plan, clean, and quarter cut-aways.

PyVista off-screen, same stack the knob sheets use. The resin is drawn translucent
Pantone 2577 C. The green skin is the Shimicoat glow coat on the inside walls.
"""
import math
import os
import numpy as np

from build123d import Rot
from .export import export_case, mesh_of
from .parts.shell import _box, _sub, beam_solid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # cad/


def _colour(D, name):
    if name == "case":
        return tuple(c / 255.0 for c in D["dye_rgb"]), D["dye_opacity"]
    if name.startswith("glow"):
        return tuple(c / 255.0 for c in D["glow_rgb"]), 0.9
    if name.startswith("scanner motor"):
        return (0.55, 0.56, 0.58), 1.0
    if name.startswith("scanner mirror"):
        return (0.75, 0.78, 0.82), 1.0
    if name.startswith("grating"):
        return (0.85, 0.65, 0.20), 0.85
    if name.startswith("VCSEL"):
        return (0.75, 0.05, 0.08), 1.0
    if name.startswith("back cover"):
        return tuple(c / 255.0 for c in D["cover_rgb"]), D["cover_opacity"]
    if name == "PCB":
        return (0.12, 0.42, 0.22), 1.0
    if name.startswith("corner screw") or name.startswith("knob bolt"):
        return (0.72, 0.74, 0.78), 1.0
    if name.startswith("cross pin"):
        return (0.85, 0.75, 0.35), 1.0
    if name == "beam":
        return (0.85, 0.15, 0.12), 0.28
    return (0.6, 0.6, 0.6), 1.0


def _cut(shape, kind, screw=None):
    bb = shape.bounding_box()
    z0, z1 = bb.min.Z - 1.0, bb.max.Z + 1.0
    y0, y1 = bb.min.Y - 1.0, bb.max.Y + 1.0
    x0, x1 = bb.min.X - 1.0, bb.max.X + 1.0
    if kind == "section":
        return shape.intersect(_box(x0, 0.0, y0, y1, z0, z1))
    if kind == "corner" and screw is not None:
        # rotate the screw onto +X, then keep y <= 0 so the cut plane holds the collar and that screw
        ang = math.degrees(math.atan2(screw[1], screw[0]))
        spun = Rot(0, 0, -ang) * shape
        sb = spun.bounding_box()
        box = _box(sb.min.X - 1.0, sb.max.X + 1.0, min(sb.min.Y - 1.0, -1.0), 0.0, sb.min.Z - 1.0, sb.max.Z + 1.0)
        try:
            hit = spun.intersect(box)
        except Exception:
            return None
        return hit if hit is not None and hit.solids() else None
    if kind == "quarter-scan":
        return _sub(shape, _box(0.0, x1, 0.0, y1, z0, z1))
    if kind == "quarter-front":
        return _sub(shape, _box(x0, 0.0, 0.0, y1, z0, z1))
    return shape


def _shot(items, path, view, size, zoom, bounds=None, labels=None):
    import pyvista as pv
    pv.OFF_SCREEN = True
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background("white")
    any_mesh = False
    for P, T, rgb, opacity in items:
        if len(T) == 0:
            continue
        any_mesh = True
        faces = np.hstack([np.full((len(T), 1), 3), T]).ravel()
        pl.add_mesh(pv.PolyData(np.ascontiguousarray(P), faces), color=rgb, opacity=opacity,
                    smooth_shading=True, specular=0.25, ambient=0.35, diffuse=0.7)
    if labels:
        pl.add_point_labels([p for p, _ in labels], [t for _, t in labels],
                            font_size=16, text_color="black", point_color="black", point_size=8,
                            shape_color="white", shape_opacity=0.85, always_visible=True, bold=True)
    if not any_mesh:
        pl.close()
        return path
    pl.enable_parallel_projection()
    if bounds is not None and view == "xz":
        # fit the cut, looking along +Y onto the section. A plain reset_camera widens the
        # frame to the long axis and pulls the deep cover pocket into view.
        x0, x1, _y0, _y1, z0, z1 = bounds
        cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
        pl.camera.focal_point = (cx, 0.0, cz)
        pl.camera.position = (cx, abs(x1 - x0) + abs(z1 - z0), cz)
        pl.camera.up = (0.0, 0.0, 1.0)
        pl.camera.parallel_scale = abs(z1 - z0) / 2.0
        pl.camera.clipping_range = (1.0, 1.0e4)
    else:
        if view == "plan":
            pl.view_xy()
        elif view == "section":
            pl.view_yz()
        else:
            pl.view_isometric()
        pl.reset_camera()
        pl.camera.zoom(zoom)
    pl.screenshot(path)
    pl.close()
    return path


def _section_frame(D):
    """Camera box and labels for the cut that holds one corner screw and the collar."""
    sx, sy = D["corners"][0]
    ang = math.atan2(sy, sx)
    rad = math.hypot(sx, sy)
    # the cut rotates that screw onto +X; labels sit on the cut face, just toward the camera
    y = 0.6
    t = _ray_hit(ang, D["pcb_x1"], D["pcb_y0"], D["pcb_y1"])
    labels = [
        ((-D["collar_r"] + 8.0, y, (D["z_collar0"] + D["z_fp0"]) / 2), "collar"),
        ((-4.0, y, D["lab_z0"] + 2.5), "labyrinth"),
        ((t * 0.35, y, D["z_pcb_back"] - 3.5), "PCB"),
        ((t * 0.55, y, D["z_ledge1"] + 2.2), "shell ledge"),
        ((t - 4.0, y, D["z_flange_out"] - 3.0), "clamp rim"),
        ((rad - 7.0, y, (D["z_thread0"] + D["z_tip"]) / 2 + 2.0), "printed thread"),
        ((rad + 7.0, y, D["z_pad_out"] - 1.5), "PETG pad"),
        ((rad + 7.0, y, (D["z_pad_out"] + D["z_rim"]) / 2), "M3 screw"),
    ]
    x0, x1 = -D["collar_r"] - 10.0, rad + D["screw_boss_r"] + 16.0
    z0, z1 = D["z_pad_out"] - 5.0, D["z_fp1"] + 3.0
    return (x0, x1, -2.0, 2.0, z0, z1), labels


def _ray_hit(ang, x1, y0, y1):
    """Distance from the origin to the PCB rectangle along a ray at angle ang."""
    dx, dy = math.cos(ang), math.sin(ang)
    ts = []
    if abs(dx) > 1e-9:
        for x in (-x1, x1):
            t = x / dx
            if t > 0 and y0 - 1e-6 <= t * dy <= y1 + 1e-6:
                ts.append(t)
    if abs(dy) > 1e-9:
        for y in (y0, y1):
            t = y / dy
            if t > 0 and -x1 - 1e-6 <= t * dx <= x1 + 1e-6:
                ts.append(t)
    return min(ts) if ts else x1


def _items(D, shapes, tol):
    out = []
    for name, shape in shapes:
        if shape is None:
            continue
        sols = list(shape.solids()) if hasattr(shape, "solids") else []
        if not sols:
            continue
        P, T = mesh_of(shape, tol)
        rgb, op = _colour(D, name)
        out.append((P, T, rgb, op))
    return out


def _compose(paths, titles, out, D, footer):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    n = len(paths)
    cols = 2
    rows = (n + 1) // 2
    fig = plt.figure(figsize=(14.5, 6.4 * rows + 1.6), dpi=120)
    fig.suptitle(f"Enclosure {D['case_rev']}  —  UTR-8100 clear resin, varnished, dyed Pantone 2577 C",
                 fontsize=15, fontweight="bold", x=0.01, ha="left")
    for i, (p, t) in enumerate(zip(paths, titles)):
        ax = fig.add_subplot(rows, cols, i + 1)
        ax.imshow(plt.imread(p))
        ax.set_title(t, loc="left", fontsize=11, fontweight="bold")
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
    handles = [Patch(facecolor=tuple(c / 255 for c in D["dye_rgb"]), label="shell, translucent 2577 C"),
               Patch(facecolor=tuple(c / 255 for c in D["cover_rgb"]), label="back cover, smoky PETG"),
               Patch(facecolor=tuple(c / 255 for c in D["glow_rgb"]), label="Shimicoat glow coat, inside walls"),
               Patch(facecolor=(0.72, 0.74, 0.78), label="ISO 10642 screws, printed resin threads")]
    fig.legend(handles=handles, loc="lower left", ncol=2, fontsize=9, frameon=False,
               bbox_to_anchor=(0.01, 0.0))
    fig.text(0.01, 0.045, footer, fontsize=8.5, va="bottom", family="monospace", color="#222")
    fig.tight_layout(rect=(0, 0.11, 1, 0.96))
    fig.savefig(out)
    plt.close(fig)


def render_case(D, parts, preview=False, full=True, export=False, rows=None, clashes=None):
    """Write the sheets (and, when export is set, STEP / STL / USDZ) under cad/assemblies/case-<rev>/."""
    rev = D["case_rev"]
    out = os.path.join(ROOT, "assemblies", f"case-{rev}")
    os.makedirs(out, exist_ok=True)
    tol = 0.28 if preview else 0.15
    size = (1100, 780) if preview else (1400, 1000)
    zoom = 1.15
    case = parts["case"]
    glow = parts["glow coat (inside walls)"]
    beam = beam_solid(D)
    show = [("case", case), ("glow", glow), ("back cover", parts["back cover (PETG)"]),
            ("PCB", parts["PCB"]), ("corner screw 1", parts["corner screw 1"]), ("beam", beam)]
    if not preview:
        show += [(n, parts[n]) for n in parts if n not in ("case", "glow coat (inside walls)", "back cover (PETG)", "corner screw 1")]
    clean = [("case", case), ("back cover", parts["back cover (PETG)"]), ("glow", glow)]
    paths = []
    shots = []
    joint = [("case", case), ("back cover", parts["back cover (PETG)"]),
             ("corner screw 1", parts["corner screw 1"]), ("PCB", parts["PCB"])]
    if preview:
        shots = [("corner", "SECTION  —  corner screw, collar, PCB ledge, clamp rim", joint, "xz"),
                 ("iso", "ISOMETRIC", show, "iso")]
    elif full:
        shots = [("corner", "SECTION  —  corner screw, collar, PCB ledge, clamp rim", joint, "xz"),
                 ("iso", "ISOMETRIC", show, "iso"),
                 ("plan", "PLAN  (panel up = +Y)", show, "plan"),
                 ("clean", "CLEAN  (shell, cover, glow)", clean, "iso")]
    tmp = os.path.join(out, "_tmp")
    os.makedirs(tmp, exist_ok=True)
    pngs = []
    for key, title, shapes, view in shots:
        cut_shapes = []
        for name, shape in shapes:
            if key == "corner":
                shape = _cut(shape, "corner", D["corners"][0])
            cut_shapes.append((name, shape))
        items = _items(D, cut_shapes, 0.08 if key == "corner" else tol)
        p = os.path.join(tmp, key + ".png")
        bounds, labels = (None, None)
        shot_size = size
        if key == "corner":
            bounds, labels = _section_frame(D)
            x0, x1, _y0, _y1, z0, z1 = bounds
            h = 860
            w = int(h * abs(x1 - x0) / max(abs(z1 - z0), 1.0))
            shot_size = (min(w, 1800), h)
        _shot(items, p, view, shot_size, zoom, bounds=bounds, labels=labels)
        pngs.append(p)
        paths.append(p)
    mass = case.volume * D["case_rho"]
    nf = sum(not r["ok"] for r in rows) if rows else 0
    nt = len(rows) if rows else 0
    nc = len(clashes or {})
    footer = (f"{D['hp']} HP × 3U   {D['panel_w']:.2f} × {D['panel_h']:.1f} × {D['z_fp1'] - D['z_foot']:.2f} mm"
              f"    faceplate to PCB {D['fp_to_pcb']:.2f} mm    shell {case.volume / 1000:.1f} cm³  {mass:.1f} g\n"
              f"knob top {D['knob_top_used']:.2f} ({D['knob_top_src']}) − proud {D['knob_proud']:.1f} → plate {D['z_fp1']:.2f}; "
              f"rear stack {D['rear_stack']:.2f} + ratio {D['cover_clear_ratio']:.2f} → cover depth {D['cover_depth']:.2f}\n"
              f"thread M{D['screw_d']:.0f} engagement {D['tap_len']:.2f} ({D['tap_len'] / D['screw_d']:.2f}×d)  "
              f"boss wall {(D['screw_boss_r'] - D['screw_d'] / 2) / D['screw_d']:.2f}×d    checks {nt - nf}/{nt}  clashes {nc}")
    sheet = os.path.join(out, f"case-{rev}-preview.png" if preview else f"case-{rev}.png")
    titles = [s[1] for s in shots]
    _compose(pngs, titles, sheet, D, footer)
    paths = [sheet]
    if full and not preview:
        qshots = []
        qpngs = []
        for key, title, kind, view in (
                ("q1", "QUARTER CUT  (−X −Y kept, scanner bay)", "quarter-scan", "iso"),
                ("q2", "QUARTER CUT  (+X −Y kept)", "quarter-front", "iso2")):
            shapes = [("case", _cut(case, kind)), ("glow", _cut(glow, kind)), ("back cover", _cut(parts["back cover (PETG)"], kind)),
                  ("beam", _cut(beam, kind))]
            items = _items(D, shapes, tol)
            p = os.path.join(tmp, key + ".png")
            _shot(items, p, view, size, zoom)
            qpngs.append(p)
            qshots.append(title)
        qsheet = os.path.join(out, f"case-{rev}-quarter.png")
        _compose(qpngs, qshots, qsheet, D, footer)
        paths.append(qsheet)
    if export:
        from build123d import export_step, export_stl
        paths += export_case(case, D, out)
        cover = parts["back cover (PETG)"]
        cstep = os.path.join(out, f"case-{rev}-cover.step")
        cstl = os.path.join(out, f"case-{rev}-cover.stl")
        export_step(cover, cstep)
        export_stl(cover, cstl, tolerance=D["stl_tol"], angular_tolerance=D["stl_ang"])
        paths += [cstep, cstl]
    return paths
