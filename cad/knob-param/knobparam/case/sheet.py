"""Four-view case sheet, same colour language as the knob assembly sections.

Three sections and one isometric. Internals are the knob stack, the joystick, the PCB
and the cover. Cut faces are a lighter tint with a dark outline, as on the assembly sheet.
"""
import os
import sys

from build123d import Align, Box, Pos

from ..assembly.render import GROUPS as KNOB_GROUPS
from ..assembly.render import cut_meshes, _mesh, _solids, _trim
from ..common.cache import CACHE

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))  # cad/


CASE_GROUPS = [
    ("shell, plain clear resin — printed M3 threads in the bosses", "#c5d0d8", lambda n: n == "case"),
    ("Shimicoat glow coat, inside walls", "#8fd184", lambda n: n.startswith("glow")),
    ("back cover, smoky PETG", "#84888e", lambda n: n.startswith("back cover")),
    ("TFT light path (air, keep-out)", "#3ec0f0", lambda n: n.startswith("bottom TFT")),
    ("laser placeholder", "#f23b52", lambda n: n.startswith("laser")),
    ("ISO 4762 M3×10 corner screws, A2", "#b7bcc6", lambda n: n.startswith("corner screw")),
    ("knob bolts, M3", "#9aa0aa", lambda n: n.startswith("knob bolt")),
    ("joystick cross pin", "#d4b44a", lambda n: n.startswith("cross pin")),
]
JOY_GROUPS = [
    ("joystick PCB patch", "#2e7d32", lambda n: n.startswith("main PCB")),
    ("J2 socket / J1 header", "#424242", lambda n: n.startswith(("J2", "J1"))),
    ("joystick daughterboard", "#1b5e20", lambda n: n == "joystick daughterboard"),
    ("SKRHADE010 body", "#b0bec5", lambda n: n.startswith("SW1") and "body" in n),
    ("SKRHADE010 stem", "#fff176", lambda n: n.startswith("SW1") and "stem" in n),
    ("joystick base", "#8d6e63", lambda n: n.startswith("joystick base")),
    ("joystick balls", "#78909c", lambda n: n.startswith("ball ")),
    ("joystick carrier", "#ab47bc", lambda n: n.startswith("joystick carrier")),
    ("screen spider + plunger", "#ff7043", lambda n: n.startswith("screen spider")),
    ("joystick screen", "#101828", lambda n: n.startswith("top screen")),
    ("joystick screen FPC", "#ffb300", lambda n: n.startswith("screen FPC")),
    ("joystick hold-down springs", "#fdd835", lambda n: n.startswith("hold-down")),
]
GROUPS = CASE_GROUPS + JOY_GROUPS + list(KNOB_GROUPS)


def group_of(name):
    for i, (_, _, pred) in enumerate(GROUPS):
        if pred(name):
            return i
    return None


def _bbox(parts):
    bbs = [s.bounding_box() for s in parts.values() if s is not None]
    return [min(b.min.X for b in bbs), min(b.min.Y for b in bbs), min(b.min.Z for b in bbs),
            max(b.max.X for b in bbs), max(b.max.Y for b in bbs), max(b.max.Z for b in bbs)]


def _slice(parts, axis, a0, a1, tol):
    """Keep a slab between a0 and a1 on axis (0=X, 1=Y, 2=Z). Both end faces are cuts."""
    bb = _bbox(parts)
    lo = [bb[0] - 2, bb[1] - 2, bb[2] - 2]
    hi = [bb[3] + 2, bb[4] + 2, bb[5] + 2]
    lo[axis], hi[axis] = a0, a1
    reg = Pos(*lo) * Box(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2], align=(Align.MIN,) * 3)
    planes = []
    for val, sign in ((a0, -1.0), (a1, 1.0)):
        origin = [0.0, 0.0, 0.0]
        normal = [0.0, 0.0, 0.0]
        origin[axis] = val
        normal[axis] = sign
        planes.append((tuple(origin), tuple(normal)))
    out = {}
    for n, s in parts.items():
        if s is None:
            continue
        bs = s.bounding_box()
        b0 = (bs.min.X, bs.min.Y, bs.min.Z)[axis]
        b1 = (bs.max.X, bs.max.Y, bs.max.Z)[axis]
        if b1 < a0 or b0 > a1:
            continue
        try:
            hit = _solids(s.intersect(reg))
        except Exception:
            hit = []
        if not hit:
            continue
        m = _mesh(hit, planes, tol)
        if m:
            out[n] = m
    return out


def _place_joystick(parts, keys, paths):
    """Joystick frame is the knob frame: origin on the main PCB front, placed at its own place_y."""
    sys.path.insert(0, os.path.join(ROOT, "joystick-param"))
    from jsparam.params import P, derive
    from jsparam.parts import build
    from build123d import export_brep
    joy_d = derive(dict(P))
    joy = build(joy_d)
    os.makedirs(CACHE, exist_ok=True)
    for n, shape in joy.items():
        placed = Pos(0, joy_d["place_y"], 0) * shape
        slug = "".join(c if c.isalnum() else "_" for c in n)[:48]
        path = os.path.join(CACHE, "case-sheet-" + slug + ".brep")
        export_brep(placed, path)
        parts[n] = placed
        keys[n] = "joy-" + n
        paths[n] = path


def _restore_pcb(parts, keys, paths, D):
    """The case ships a nest-sized PCB box under the same name. Put the real proxy board back."""
    from ..common import model
    from ..common.cache import build_module
    import knobparam.electronics.parts.pcb as pcb_mod
    out, key, got = build_module(pcb_mod, model.view(D, "electronics"), [])
    for n, shape in out.items():
        parts[n] = shape
        keys[n] = key + n
        paths[n] = got[n]


def _lighten(hexc, k=0.45):
    h = hexc.lstrip("#")
    rgb = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % tuple(int(v + (255 - v) * k) for v in rgb)


def _draw(pl, pv, meshes, lw=1.2):
    """Solids in the part colours. The TFT keep-out is an outline, not a filled part."""
    import numpy as np
    for n, m in meshes.items():
        gi = group_of(n)
        col = GROUPS[gi][1] if gi is not None else "#9e9e9e"
        keep = n.startswith("bottom TFT")
        for _cut, (P, T) in m.items():
            if len(T) == 0:
                continue
            pm = pv.PolyData(np.ascontiguousarray(P), np.hstack([np.full((len(T), 1), 3), T]).ravel())
            if keep:
                fe = pm.extract_feature_edges(feature_angle=25, boundary_edges=True,
                                              feature_edges=True, non_manifold_edges=False, manifold_edges=True)
                if fe.n_points:
                    pl.add_mesh(fe, color="#0288d1", line_width=3.0)
                continue
            pl.add_mesh(pm, color=_lighten(col) if _cut else col, smooth_shading=False,
                        specular=0.05, ambient=0.35, diffuse=0.75)
            if _cut:
                be = pm.extract_feature_edges(boundary_edges=True, feature_edges=False,
                                              non_manifold_edges=False, manifold_edges=False)
                if be.n_points:
                    pl.add_mesh(be, color="#101010", line_width=lw)
            else:
                fe = pm.extract_feature_edges(feature_angle=35, boundary_edges=False,
                                              non_manifold_edges=False, manifold_edges=False)
                if fe.n_points:
                    pl.add_mesh(fe, color="#303030", line_width=lw * 0.7)


def _shot(meshes, centre, cam_dir, up, w_mm, h_mm, ppm, path, iso=False):
    import numpy as np
    import pyvista as pv
    pv.OFF_SCREEN = True
    if iso:
        pl = pv.Plotter(off_screen=True, window_size=(1500, 1500))
    else:
        pl = pv.Plotter(off_screen=True, window_size=(max(int(w_mm * ppm), 50), max(int(h_mm * ppm), 50)))
    pl.set_background("white")
    _draw(pl, pv, meshes)
    if iso:
        P = np.vstack([p for m in meshes.values() for pair in m.values() for p in (pair[0],) if len(pair[0])])
        lo, hi = P.min(0), P.max(0)
        c = (lo + hi) / 2
        d = np.array([1.0, 1.0, 0.9]); d /= np.linalg.norm(d)
        pl.camera.position = tuple(c + 500 * d)
        pl.camera.focal_point = tuple(c)
        pl.camera.up = (0, 0, 1)
        pl.enable_parallel_projection()
        pl.reset_camera()
        pl.camera.zoom(1.25)
    else:
        c = np.array(centre, float)
        d = np.array(cam_dir, float); d /= np.linalg.norm(d)
        pl.camera.position = tuple(c + 500 * d)
        pl.camera.focal_point = tuple(c)
        pl.camera.up = up
        pl.enable_parallel_projection()
        pl.camera.parallel_scale = h_mm / 2
    pl.camera.clipping_range = (1, 2000)
    pl.screenshot(path)
    pl.close()
    return path


def render_sheet(D, parts, keys, paths, out_png):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, Rectangle

    tol = 0.12
    bb = _bbox(parts)
    x0, y0, z0, x1, y1, z1 = bb
    pad = 8.0
    # Thin slices, so the cut is the picture. A half-box leaves the far wall filling the frame.
    print("meshing section along Y", flush=True)
    m_y = _slice(parts, 0, -1.2, 1.2, tol)          # plane x = 0, panel up
    print("meshing section across X", flush=True)
    m_x = _slice(parts, 1, -1.2, 1.2, tol)          # plane y = 0, dial axis up
    print("meshing plan just above the PCB", flush=True)
    m_p = _slice(parts, 2, -0.4, 3.2, tol)         # just above the PCB front, through the window and the bosses
    spec_iso = dict(kind="quarter", bb=[v - pad if i < 3 else v + pad for i, v in enumerate(bb)], a0=-20.0, a1=110.0)
    print("meshing isometric", flush=True)
    m_i = cut_meshes(parts, keys, spec_iso, tol)
    tmp = os.path.join(os.path.dirname(out_png), "_sheet_tmp")
    os.makedirs(tmp, exist_ok=True)
    ppm = 11
    _shot(m_y, (0.0, (y0 + y1) / 2, (z0 + z1) / 2), (-1, 0, 0), (0, 1, 0),
          (z1 - z0) + 2 * pad, (y1 - y0) + 2 * pad, ppm, f"{tmp}/sy.png")
    _shot(m_x, ((x0 + x1) / 2, 0.0, (z0 + z1) / 2), (0, 1, 0), (0, 0, 1),
          (x1 - x0) + 2 * pad, (z1 - z0) + 2 * pad, ppm, f"{tmp}/sx.png")
    _shot(m_p, ((x0 + x1) / 2, (y0 + y1) / 2, 1.4), (0, 0, 1), (0, 1, 0),
          (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad, ppm, f"{tmp}/sp.png")
    _shot(m_i, None, None, None, 1, 1, ppm, f"{tmp}/iso.png", iso=True)

    behind = D["z_fp1"] - D["z_foot"]
    shots = [
        (f"{tmp}/sy.png", "SECTION  —  knob axis, along Y",
         f"Panel up (+Y). Depth behind the front face {behind:.2f} mm. Faceplate to PCB {D['fp_to_pcb']:.2f} mm."),
        (f"{tmp}/sx.png", "SECTION  —  across X, through the knob axis",
         f"Dial axis up. {D['hp']} HP, {D['panel_w']:.2f} mm wide."),
        (f"{tmp}/sp.png", "SECTION  —  just above the PCB",
         f"TFT window {D['win_w']:.2f} × {D['win_h']:.2f} mm, x {D['win_x0']:.2f}..{D['win_x1']:.2f}, y {D['win_y0']:.2f}..{D['win_y1']:.2f}."),
        (f"{tmp}/iso.png", "ISOMETRIC CUT-AWAY",
         "Helices in the bosses are the printed M3 threads. The cyan outline is the TFT light path, not a part."),
    ]
    shown = []
    for meshes in (m_y, m_x, m_p, m_i):
        for n in meshes:
            g = group_of(n)
            if g is not None and g not in shown:
                shown.append(g)
    shown.sort()

    FW, FH = 24.0, 22.0
    fig = plt.figure(figsize=(FW, FH), dpi=120)
    fig.text(0.012, 0.985, f"Enclosure {D['case_rev']}  —  case with the knob stack", fontsize=26, weight="bold", va="top")
    fig.text(0.012, 0.942,
             "Plain clear UTR-8100. Front face polished, other faces as-printed.\n"
             "Cut faces are a lighter tint of the part colour, with a dark outline.",
             fontsize=14, va="top", color="#333333", linespacing=1.35)
    # title block, same job as the drawing sheet: the four sizes Ed asked to be able to read
    tb = fig.add_axes([0.70, 0.905, 0.28, 0.075])
    tb.set_xlim(0, 1)
    tb.set_ylim(0, 1)
    tb.axis("off")
    tb.add_patch(Rectangle((0.01, 0.02), 0.98, 0.96, fill=False, lw=1.0, edgecolor="#222222", transform=tb.transAxes))
    tb.text(0.06, 0.72, f"10 HP    {D['panel_w']:.2f} mm wide", fontsize=14, va="center", transform=tb.transAxes)
    tb.text(0.06, 0.40, f"depth {behind:.2f} mm    faceplate to PCB {D['fp_to_pcb']:.2f} mm", fontsize=14, va="center", transform=tb.transAxes)
    tb.text(0.06, 0.12, f"TFT {D['win_w']:.2f} × {D['win_h']:.2f} mm", fontsize=14, va="center", transform=tb.transAxes)

    rects = [
        [0.02, 0.56, 0.46, 0.30],
        [0.52, 0.56, 0.46, 0.30],
        [0.02, 0.22, 0.46, 0.28],
        [0.52, 0.22, 0.46, 0.28],
    ]
    for rect, (path, title, sub) in zip(rects, shots):
        ax = fig.add_axes(rect)
        ax.imshow(_trim(plt.imread(path), 8), interpolation="lanczos")
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
        fig.text(rect[0], rect[1] + rect[3] + 0.004, title, fontsize=17, weight="bold", va="bottom")
        fig.text(rect[0], rect[1] - 0.004, sub, fontsize=14, va="top", color="#222222")
    hand = [Patch(facecolor=GROUPS[i][1], edgecolor="#222222", label=GROUPS[i][0]) for i in shown]
    fig.legend(handles=hand, loc="lower center", ncol=4, fontsize=14, frameon=True,
               bbox_to_anchor=(0.5, 0.004), title="PART COLOURS", title_fontsize=16,
               handlelength=2.0, handleheight=1.15, columnspacing=1.2, labelspacing=0.35)
    fig.savefig(out_png, dpi=fig.dpi)
    plt.close(fig)
    print("wrote", out_png, flush=True)
    return out_png


def main():
    from ..assembly.build import PATHS, build_all
    from ..common import model
    D = model.derive(model.default_params())
    parts, stats, keys, owner = build_all(D)
    _restore_pcb(parts, keys, PATHS, D)
    _place_joystick(parts, keys, PATHS)
    out = os.path.join(ROOT, "assemblies", f"case-{D['case_rev']}", f"case-{D['case_rev']}-sheet.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    render_sheet(D, parts, keys, PATHS, out)


if __name__ == "__main__":
    main()
