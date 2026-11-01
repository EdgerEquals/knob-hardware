"""Colour sheets for the case: section, isometric, plan, clean, and quarter cut-aways.

PyVista off-screen, same stack the knob sheets use. The resin is plain clear, no tint.
The green skin is the Shimicoat glow coat on the inside walls.
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
        return tuple(c / 255.0 for c in D["resin_rgb"]), D["resin_opacity"]
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
    if name.startswith("bottom TFT"):
        return (0.25, 0.75, 0.95), 0.35
    if name.startswith("laser"):
        return (0.95, 0.25, 0.35), 0.45
    return (0.6, 0.6, 0.6), 1.0


def _cut(shape, kind, screw=None):
    bb = shape.bounding_box()
    z0, z1 = bb.min.Z - 1.0, bb.max.Z + 1.0
    y0, y1 = bb.min.Y - 1.0, bb.max.Y + 1.0
    x0, x1 = bb.min.X - 1.0, bb.max.X + 1.0
    if kind == "section":
        return shape.intersect(_box(x0, 0.0, y0, y1, z0, z1))
    if kind == "mid":
        return shape.intersect(_box(x0, x1, min(y0, -1.0), 0.0, z0, z1))
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


def _shot(items, path, view, size, zoom, bounds=None):
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
        # Flat shading. Smooth normals on a coarse helix turn each printed M3 thread into a capsule.
        pl.add_mesh(pv.PolyData(np.ascontiguousarray(P), faces), color=rgb, opacity=opacity,
                    smooth_shading=False, specular=0.05, ambient=0.35, diffuse=0.75)
    if not any_mesh:
        pl.close()
        return path
    pl.enable_parallel_projection()
    if bounds is not None and view == "xz":
        # The window aspect matches the cut, so the frame is exactly the bounds:
        # collar through the corner screw, pad through the faceplate, nothing cropped.
        # Camera sits on +Y. With +Z up, world +X lands on the left of the image.
        x0, x1, _y0, _y1, z0, z1 = bounds
        cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
        pl.camera.focal_point = (cx, 0.0, cz)
        pl.camera.position = (cx, abs(x1 - x0) + abs(z1 - z0), cz)
        pl.camera.up = (0.0, 0.0, 1.0)
        pl.camera.parallel_scale = abs(z1 - z0) / 2.0
        pl.camera.clipping_range = (1.0, 1.0e4)
    elif bounds is not None and view == "plan":
        x0, x1, y0, y1, _z0, _z1 = bounds
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        pl.camera.focal_point = (cx, cy, 0.0)
        pl.camera.position = (cx, cy, abs(x1 - x0) + abs(y1 - y0))
        pl.camera.up = (0.0, 1.0, 0.0)
        pl.camera.parallel_scale = abs(y1 - y0) / 2.0
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


def _mid_frame(D):
    """Full outer width, from just behind the parting line up through the faceplate."""
    return (D["x_out0"] - 6.0, D["x_out1"] + 6.0, -2.0, 2.0, D["z_rim_seat"] - 12.0, D["z_fp1"] + 4.0)


def _annotate_mid(ax, D, bounds, fs):
    """Straight cut on the dial axis. +X is on the left of the image."""
    def fx(x):
        return _fx(x, bounds)

    def fz(z):
        return _fz(z, bounds)

    _tag(ax, fx(D["x_out0"] + 1.2), fz((D["z_fp0"] + D["z_rim"]) / 2.0), "shell", fs)
    _tag(ax, fx(D["x_out0"] + 1.2), fz(D["z_rim_seat"] - 4.0), "cover", fs)
    _tag(ax, fx(0.0), fz(D["z_pcb_back"] / 2.0), "PCB inside", fs)
    _tag(ax, fx(D["win_x0"] + 8.0), fz((D["tft_z0"] + D["tft_z1"]) / 2.0),
         f"TFT {D['win_w']:.2f}×{D['win_h']:.2f}", fs)
    _tag(ax, fx(D["pcb_x1"] - 2.0), fz(D["z_ledge1"] + 3.0), "ledge", fs)
    xd = fx(D["pcb_x1"] * 0.35)
    ax.annotate("", xy=(xd, fz(D["z_fp1"])), xytext=(xd, fz(0.0)),
                xycoords=ax.transAxes, textcoords=ax.transAxes,
                arrowprops=dict(arrowstyle="<->", color="#111", lw=1.4))
    _tag(ax, xd + 0.08, fz(D["z_fp1"] * 0.55), f"{D['fp_to_pcb']:.2f} mm\nfaceplate to PCB", fs)
    _tag(ax, 0.50, 0.96, f"knob_proud {D['knob_proud']:.2f} mm  ·  outer faces flush  ·  PCB embedded", fs)


def _section_frame(D):
    """Camera box for the cut that holds one corner screw and the collar. Margin stays inside the frame."""
    sx, sy = D["corners"][0]
    rad = math.hypot(sx, sy)
    x0, x1 = -D["collar_r"] - 14.0, rad + D["screw_boss_r"] + 18.0
    z0, z1 = D["z_pad_out"] - 8.0, D["z_fp1"] + 6.0
    return (x0, x1, -2.0, 2.0, z0, z1)


def _fx(x, bounds):
    """Image fraction from the left. Camera on +Y puts world +X on the left."""
    x0, x1 = bounds[0], bounds[1]
    return (x1 - x) / (x1 - x0)


def _fz(z, bounds):
    z0, z1 = bounds[4], bounds[5]
    return (z - z0) / (z1 - z0)


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


def _tag(ax, x, y, text, fs):
    ax.text(x, y, text, transform=ax.transAxes, fontsize=fs, fontweight="bold", color="black",
            ha="center", va="center", zorder=5,
            bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="#222", alpha=0.92))


def _annotate_section(ax, D, bounds, fs):
    """Part names and the dimensions Ed asked to be able to read. fs is in points on the final figure."""
    sx, sy = D["corners"][0]
    ang = math.atan2(sy, sx)
    rad = math.hypot(sx, sy)
    t = _ray_hit(ang, D["pcb_x1"], D["pcb_y0"], D["pcb_y1"])
    _tag(ax, _fx(-D["collar_r"] + 2.0, bounds), _fz(D["z_fp0"] + 2.8, bounds), "collar", fs)
    _tag(ax, _fx(-14.0, bounds), _fz(D["lab_z0"], bounds), "labyrinth", fs)
    _tag(ax, _fx(-8.0, bounds), _fz(D["z_pcb_back"] - 1.6, bounds), "PCB", fs)
    _tag(ax, _fx(t - 2.0, bounds), _fz(16.0, bounds), "shell ledge", fs)
    _tag(ax, _fx(4.0, bounds), _fz(D["z_flange_out"] - 5.2, bounds), "clamp rim", fs)
    _tag(ax, _fx(rad - 30.0, bounds), _fz(8.0, bounds), "printed thread", fs)
    _tag(ax, _fx(rad - 1.0, bounds), _fz(D["z_pad_out"] - 5.2, bounds), "PETG pad", fs)
    _tag(ax, _fx(rad - 2.0, bounds), _fz(22.0, bounds), "M3 screw", fs)
    # faceplate front → PCB front
    xd = _fx(t * 0.18, bounds)
    ax.annotate("", xy=(xd, _fz(D["z_fp1"], bounds)), xytext=(xd, _fz(0.0, bounds)),
                xycoords=ax.transAxes, textcoords=ax.transAxes,
                arrowprops=dict(arrowstyle="<->", color="#111", lw=1.4))
    _tag(ax, xd + 0.055, _fz(D["z_fp1"] * 0.62, bounds), f"{D['fp_to_pcb']:.2f} mm\nfaceplate to PCB", fs)
    _tag(ax, _fx(rad - 12.0, bounds), _fz(D["z_pcb_back"] - 2.4, bounds),
         f"{D['cover_skin']:.2f} mm PETG\nunder the head", fs)
    _tag(ax, 0.50, 0.97,
         f"knob_proud {D['knob_proud']:.2f} mm  →  plate {D['z_fp1']:.2f} mm", fs)


def _plan_frame(D):
    return (D["panel_x0"] - 8.0, D["panel_x1"] + 8.0, D["panel_y0"] - 10.0, D["panel_y1"] + 10.0, -40.0, 40.0)


def _annotate_plan(ax, D, fs):
    """Plan is viewed from +Z with +X to the right and +Y up, framed on the panel."""
    x0, x1, y0, y1 = _plan_frame(D)[:4]

    def fx(x):
        return (x - x0) / (x1 - x0)

    def fy(y):
        return (y - y0) / (y1 - y0)

    _tag(ax, fx(0.0), fy(D["panel_y1"] + 4.0), f"{D['panel_w']:.2f} mm   {D['hp']} HP", fs)
    _tag(ax, fx(0.0), fy(D["place_y"]), f"bezel {D['bezel_w']:.1f}", fs)
    for x, y in D["corners"]:
        _tag(ax, fx(x + (7.5 if x > 0 else -7.5)), fy(y), "M3", fs)
    _tag(ax, fx(0.0), fy((D["win_y0"] + D["win_y1"]) / 2.0),
         f"TFT {D['win_w']:.2f}×{D['win_h']:.2f}", fs)
    _tag(ax, fx(0.0), fy(D["panel_y0"] + 8.0), f"PCB {D['nest_w']:.2f}   wall {D['wall']:.1f}", fs)


def _compose_preview(section, plan, iso, out, D, bounds, footer):
    """Section full width, plan beside the notes. Labels are drawn here so they stay ≥ 14 px."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    dpi = 120
    fs = 16   # 16 pt at 120 dpi = 27 px
    fig = plt.figure(figsize=(18.5, 18.0), dpi=dpi)
    fig.suptitle(f"Enclosure {D['case_rev']}  —  plain clear resin, front face polished    {D['panel_w']:.2f} mm    wall {D['wall']:.1f} mm",
                 fontsize=fs, fontweight="bold", x=0.01, ha="left")
    ax = fig.add_axes((0.02, 0.48, 0.96, 0.46))
    ax.imshow(plt.imread(section), aspect="equal")
    ax.set_axis_off()
    _annotate_mid(ax, D, bounds, fs)
    ax2 = fig.add_axes((0.01, 0.18, 0.30, 0.28))
    ax2.imshow(plt.imread(plan), aspect="equal")
    ax2.set_title("PLAN  (+Z, panel up = +Y)", loc="left", fontsize=fs, fontweight="bold")
    ax2.set_axis_off()
    _annotate_plan(ax2, D, fs - 2)
    ax3 = fig.add_axes((0.32, 0.18, 0.30, 0.28))
    ax3.imshow(plt.imread(iso), aspect="equal")
    ax3.set_title("ISOMETRIC", loc="left", fontsize=fs, fontweight="bold")
    ax3.set_axis_off()
    handles = [Patch(facecolor=tuple(c / 255 for c in D["resin_rgb"]), label="shell, plain clear resin"),
               Patch(facecolor=tuple(c / 255 for c in D["cover_rgb"]), label="back cover, smoky PETG"),
               Patch(facecolor=(0.12, 0.42, 0.22), label="PCB"),
               Patch(facecolor=(0.72, 0.74, 0.78), label="ISO 4762 M3×10 socket head"),
               Patch(facecolor=(0.25, 0.75, 0.95), label="bottom TFT window"),
               Patch(facecolor=(0.95, 0.25, 0.35), label="laser placeholder")]
    fig.legend(handles=handles, loc="upper left", fontsize=fs - 2, frameon=False, bbox_to_anchor=(0.62, 0.44))
    fig.text(0.02, 0.005, footer, fontsize=fs - 2, va="bottom", family="monospace", color="#222")
    fig.savefig(out)
    plt.close(fig)


def _compose(paths, titles, out, D, footer):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    n = len(paths)
    cols = 2
    rows = (n + 1) // 2
    fig = plt.figure(figsize=(14.5, 6.4 * rows + 1.6), dpi=120)
    fig.suptitle(f"Enclosure {D['case_rev']}  —  UTR-8100 plain clear resin; front face polished, other faces as-printed",
                 fontsize=15, fontweight="bold", x=0.01, ha="left")
    for i, (p, t) in enumerate(zip(paths, titles)):
        ax = fig.add_subplot(rows, cols, i + 1)
        ax.imshow(plt.imread(p))
        ax.set_title(t, loc="left", fontsize=11, fontweight="bold")
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
    handles = [Patch(facecolor=tuple(c / 255 for c in D["resin_rgb"]), label="shell, plain clear resin"),
               Patch(facecolor=tuple(c / 255 for c in D["cover_rgb"]), label="back cover, smoky PETG"),
               Patch(facecolor=tuple(c / 255 for c in D["glow_rgb"]), label="Shimicoat glow coat, inside walls"),
               Patch(facecolor=(0.72, 0.74, 0.78), label="ISO 4762 M3×10 socket head, A2")]
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
    tol = 0.08 if preview else 0.08
    size = (1100, 780) if preview else (1400, 1000)
    zoom = 1.15
    case = parts["case"]
    glow = parts["glow coat (inside walls)"]
    beam = beam_solid(D) if D["scanner_enabled"] else None
    show = [("case", case), ("glow", glow), ("back cover", parts["back cover (PETG)"]),
            ("PCB", parts["PCB"]), ("bottom TFT window", parts["bottom TFT window"]),
            ("corner screw 1", parts["corner screw 1"])]
    if beam is not None:
        show.append(("beam", beam))
    show += [(n, parts[n]) for n in parts if n.startswith("laser")]
    if not preview:
        show += [(n, parts[n]) for n in parts if n not in ("case", "glow coat (inside walls)", "back cover (PETG)", "corner screw 1")]
    clean = [("case", case), ("back cover", parts["back cover (PETG)"]), ("glow", glow)]
    paths = []
    shots = []
    joint = [("case", case), ("back cover", parts["back cover (PETG)"]),
             ("corner screw 1", parts["corner screw 1"]), ("PCB", parts["PCB"]),
             ("bottom TFT window", parts["bottom TFT window"])]
    plan_show = [("case", case), ("back cover", parts["back cover (PETG)"]),
                 ("PCB", parts["PCB"]), ("bottom TFT window", parts["bottom TFT window"]),
                 ("corner screw 1", parts["corner screw 1"])]
    plan_show += [(n, parts[n]) for n in parts if n.startswith("laser")]
    if preview:
        shots = [("mid", "SECTION through both side walls", joint, "xz"),
                 ("plan", "PLAN", plan_show, "plan"),
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
            elif key == "mid":
                shape = _cut(shape, "mid")
            cut_shapes.append((name, shape))
        items = _items(D, cut_shapes, 0.08 if key == "corner" else tol)
        p = os.path.join(tmp, key + ".png")
        bounds = None
        shot_size = size
        if key == "mid":
            bounds = _mid_frame(D)
            x0, x1, _y0, _y1, z0, z1 = bounds
            h = 1000
            w = int(round(h * abs(x1 - x0) / max(abs(z1 - z0), 1.0)))
            shot_size = (w, h)
        elif key == "corner":
            bounds = _section_frame(D)
            x0, x1, _y0, _y1, z0, z1 = bounds
            h = 1100
            w = int(round(h * abs(x1 - x0) / max(abs(z1 - z0), 1.0)))
            shot_size = (w, h)
        elif key == "plan":
            bounds = _plan_frame(D)
            x0, x1, y0, y1 = bounds[:4]
            h = 1500
            w = int(round(h * abs(x1 - x0) / max(abs(y1 - y0), 1.0)))
            shot_size = (max(w, 400), h)
        _shot(items, p, view, shot_size, zoom, bounds=bounds)
        pngs.append(p)
        paths.append(p)
    section_bounds = _mid_frame(D) if any(s[0] == "mid" for s in shots) else (
        _section_frame(D) if any(s[0] == "corner" for s in shots) else None)
    mass = case.volume * D["case_rho"]
    nf = sum(not r["ok"] for r in rows) if rows else 0
    nt = len(rows) if rows else 0
    nc = len(clashes or {})
    behind = D["z_fp1"] - D["z_foot"]
    past_stack = behind - D["fp_to_pcb"] - D["pcb_t"] - D["rear_stack"]
    bosses = "   ".join(f"({x:.2f}, {y:.2f})" for x, y in D["corners"])
    footer = (f"{D['hp']} HP × 3U    {D['panel_w']:.2f} × {D['panel_h']:.1f} × {behind:.2f} mm"
              f"    behind the front face {behind:.2f} mm    skiff ~40 mm, over by {behind - 40:.2f}\n"
              f"knob top {D['knob_top_used']:.2f} − proud {D['knob_proud']:.2f} → plate {D['z_fp1']:.2f}"
              f"    plate {D['wall']:.2f} + cavity {D['z_fp0']:.2f} + PCB {D['pcb_t']:.2f}"
              f" + rear {D['rear_stack']:.2f} + cover past stack {past_stack:.2f}\n"
              f"TFT {D['win_w']:.2f} × {D['win_h']:.2f}    "
              f"x {D['win_x0']:.2f}..{D['win_x1']:.2f}    "
              f"y {D['win_y0']:.2f}..{D['win_y1']:.2f}    "
              f"z {D['tft_z0']:.2f}..{D['tft_z1']:.2f}\n"
              f"bosses {bosses}\n"
              f"PETG under the head {D['cover_skin']:.2f} mm    "
              f"PCB {D['pcb_max_w']:.2f} mm    wall {D['wall']:.2f}    "
              f"scanner parked    checks {nt - nf}/{nt}    clashes {nc}")
    sheet = os.path.join(out, f"case-{rev}-preview.png" if preview else f"case-{rev}.png")
    titles = [s[1] for s in shots]
    if preview and section_bounds is not None:
        _compose_preview(pngs[0], pngs[1], pngs[2], sheet, D, section_bounds, footer)
    else:
        _compose(pngs, titles, sheet, D, footer)
    paths = [sheet]
    if full and not preview:
        qshots = []
        qpngs = []
        for key, title, kind, view in (
                ("q1", "QUARTER CUT  (−X −Y kept)", "quarter-scan", "iso"),
                ("q2", "QUARTER CUT  (+X −Y kept)", "quarter-front", "iso2")):
            shapes = [("case", _cut(case, kind)), ("glow", _cut(glow, kind)),
                      ("back cover", _cut(parts["back cover (PETG)"], kind))]
            if beam is not None:
                shapes.append(("beam", _cut(beam, kind)))
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
