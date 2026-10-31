"""Knob stack v0.6: shaded 3D ISOMETRIC half-section on plane A-A (world Y = -dial y, through the dial and motor axes).
The half nearest the viewer (Y > -dial y) is removed. Parts and clashes come from knob_stack.build_parts() (no new geometry).
Cut faces are drawn lighter with a dark outline; clash volumes (pairwise intersections) in red.
Outputs: knob-stack-v0.6-iso-section.png (A3 sheet) and knob-stack-v0.6-half-section.step. Rendered headless with pyvista (VTK offscreen)."""
import os, sys, math, itertools
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import knob_stack as ks
from build123d import *
import pyvista as pv

VIEW = (1.0, 1.0, 1.0)      # true isometric: camera on the (+X, +Y, +Z) diagonal, Z (toward the panel front) up
GROUPS = [   # (legend label, colour, part-name predicate)
    ("PCB (KiCad STEP)", "#2e7d32", lambda n: n == "PCB"),
    ("1220 motor", "#78909c", lambda n: n == "motor"),
    ("brass tube 5×3", "#c9a227", lambda n: n == "brass tube"),
    ("shaft flange (printed)", "#8d6e63", lambda n: n == "flange"),
    ("knob cap + skirt", "#1565c0", lambda n: n == "knob cap+skirt"),
    ("68T internal ring", "#42a5f5", lambda n: n == "internal ring 68T"),
    ("90T bottom internal ring", "#5c6bc0", lambda n: n == "bottom internal ring"),
    ("12T motor pinion", "#ef6c00", lambda n: n == "pinion"),
    ("PTFE liner 10×8", "#f5f5f5", lambda n: n == "PTFE liner"),
    ("bezel (PETG)", "#26a69a", lambda n: n == "bezel"),
    ("screen holder", "#6d4c41", lambda n: n == "screen holder"),
    ("TFT glass / backing / tail", "#263238", lambda n: n.startswith("TFT")),
    ("screen adapter + parts", "#7cb342", lambda n: n.startswith("adapter")),
    ("encoder pinion / shaft / gear", "#ab47bc", lambda n: n in ("encoder pinion", "encoder shaft", "encoder big gear")),
    ("F682ZZ bearings", "#9e9e9e", lambda n: n.startswith("encoder bearing")),
]
CLASH = "#e00000"

def group_of(n):
    for i, (_, c, f) in enumerate(GROUPS):
        if f(n): return i
    raise KeyError(n)

def lighten(hexc, k=0.45):
    c = np.array([int(hexc[i:i + 2], 16) for i in (1, 3, 5)]) / 255.0
    return tuple(c + (1 - c) * k)

def solids_of(s):
    if s is None: return []
    if isinstance(s, (list, ShapeList)): return [x for y in s for x in solids_of(y)]
    return list(s.solids())

def mesh_faces(solids, y_cut, tol=0.03):
    """Tessellate; split faces into (cut faces on the A-A plane, other faces)."""
    out = {True: ([], []), False: ([], [])}
    off = {True: 0, False: 0}
    for so in solids:
        for f in so.faces():
            try: vs, tris = f.tessellate(tol, 0.3)
            except Exception: continue
            if not tris: continue
            c = f.center(); is_cut = False
            if f.geom_type == GeomType.PLANE and abs(c.Y - y_cut) < 1e-3:
                nrm = f.normal_at(c); is_cut = abs(abs(nrm.Y) - 1) < 1e-6
            P, T = out[is_cut]
            P += [(v.X, v.Y, v.Z) for v in vs]
            T += [(3, off[is_cut] + a, off[is_cut] + b, off[is_cut] + d) for a, b, d in tris]
            off[is_cut] += len(vs)
    res = {}
    for k, (P, T) in out.items():
        if P: res[k] = pv.PolyData(np.array(P), np.array(T).ravel())
    return res

if __name__ == "__main__":
    parts, board, zf, zb, hx, hy, BZ, dz = ks.build_parts()
    y_cut = -hy
    asm_bb = Compound(children=list(parts.values())).bounding_box()
    pad = 5
    keep = Pos(0, 0, 0) * Box(asm_bb.max.X - asm_bb.min.X + 2 * pad, y_cut - asm_bb.min.Y + pad, asm_bb.max.Z - asm_bb.min.Z + 2 * pad,
                              align=(Align.MIN, Align.MIN, Align.MIN))
    keep = Pos(asm_bb.min.X - pad, asm_bb.min.Y - pad, asm_bb.min.Z - pad) * keep     # keeps Y <= y_cut (far half)
    halves = {}
    for n, s in parts.items():
        if ks.bbox_overlap(s, keep): 
            r = solids_of(s.intersect(keep))
            if r: halves[n] = r
    # clash volumes (pairwise, same rule as the sheet), then the far half of each
    clash = {}
    for (na, a), (nb, b) in itertools.combinations(parts.items(), 2):
        if not ks.bbox_overlap(a, b): continue
        sol = solids_of(a.intersect(b)); v = sum(x.volume for x in sol)
        if v > 1e-3:
            cut = [x for y in sol for x in solids_of(y.intersect(keep))]
            clash[f"{na} / {nb}"] = (v, cut if cut else sol, bool(cut))
    print("kept", list(halves), "clash", {k: (round(v, 2), inside) for k, (v, _, inside) in clash.items()})
    step = Compound(children=[Compound(children=s, label=n) for n, s in halves.items()] +
                    [Compound(children=s, label="CLASH " + k) for k, (_, s, _) in clash.items()], label="knob-stack-v0.6-half-section")
    export_step(step, os.path.join(HERE, "knob-stack-v0.6-half-section.step"))

    pv.OFF_SCREEN = True
    pl = pv.Plotter(off_screen=True, window_size=(3000, 2600))
    pl.set_background("white")
    for n, s in halves.items():
        g = group_of(n); col = GROUPS[g][1]
        ms = mesh_faces(s, y_cut)
        if False in ms:
            pl.add_mesh(ms[False], color=col, smooth_shading=False, specular=0.15, ambient=0.25, diffuse=0.8)
            fe = ms[False].clean().extract_feature_edges(feature_angle=35, boundary_edges=False, non_manifold_edges=False, manifold_edges=False)
            if fe.n_points: pl.add_mesh(fe, color="#202020", line_width=1.2)
        if True in ms:
            pl.add_mesh(ms[True], color=lighten(col), smooth_shading=False, ambient=0.45, diffuse=0.6)
            be = ms[True].clean().extract_feature_edges(boundary_edges=True, feature_edges=False, non_manifold_edges=False, manifold_edges=False)
            if be.n_points: pl.add_mesh(be, color="#101010", line_width=1.6)
    for k, (_, sol, _) in clash.items():
        ms = mesh_faces(sol, 1e9)
        for m in ms.values(): pl.add_mesh(m, color=CLASH, ambient=0.5, diffuse=0.7)
    c = np.array([(asm_bb.min.X + asm_bb.max.X) / 2, (asm_bb.min.Y + y_cut) / 2, (asm_bb.min.Z + asm_bb.max.Z) / 2])
    d = np.array(VIEW) / np.linalg.norm(VIEW)
    pl.camera.position = tuple(c + 400 * d); pl.camera.focal_point = tuple(c); pl.camera.up = (0, 0, 1)
    pl.enable_parallel_projection(); pl.reset_camera(); pl.camera.zoom(1.15)
    pl.enable_lightkit() if hasattr(pl, "enable_lightkit") else None
    pl.enable_anti_aliasing("ssaa")
    raw = os.path.join("/tmp", "iso_raw.png"); pl.screenshot(raw); pl.close()

    # ---- A3 sheet: render + legend + title block ----
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, Rectangle
    img = plt.imread(raw)
    fig = plt.figure(figsize=(16.54, 11.69), dpi=200)
    ax = fig.add_axes([0.01, 0.02, 0.70, 0.93]); ax.imshow(img); ax.axis("off")
    fig.text(0.02, 0.965, "ISOMETRIC HALF-SECTION A-A (through the dial and motor axes; near half removed)", fontsize=13, weight="bold")
    used = sorted({group_of(n) for n in halves})
    hs = [Patch(facecolor=GROUPS[i][1], edgecolor="k", label=GROUPS[i][0]) for i in used]
    hs.append(Patch(facecolor=lighten("#888888"), edgecolor="k", label="cut face (lighter tint of the part colour)"))
    hs.append(Patch(facecolor=CLASH, edgecolor="k", label="clash volume"))
    fig.legend(handles=hs, loc="upper left", bbox_to_anchor=(0.72, 0.93), fontsize=9, title="PARTS", title_fontsize=10, frameon=True)
    y = 0.42
    fig.text(0.725, y, "CLASHES (pairwise, not fixed)", fontsize=10, weight="bold", color=CLASH)
    for i, (k, (v, _, inside)) in enumerate(clash.items()):
        fig.text(0.725, y - 0.022 * (i + 1), f"{k}: {v:.2f} mm³" + ("" if inside else " (removed half, shown whole)"), fontsize=8, color=CLASH)
    y2 = y - 0.022 * (len(clash) + 2)
    for i, t in enumerate(["Encoder pinion, shaft and bearings sit 19.0 below the dial",
                           "axis in the kept half (shown whole); the 94T big gear is cut.",
                           "Back panel not drawn (assumed 25 behind the PCB).",
                           "Same parts/placement as the assembly sheet.",
                           "True isometric, parallel projection."]):
        fig.text(0.725, y2 - 0.02 * i, t, fontsize=7.5)
    tb = fig.add_axes([0.72, 0.03, 0.27, 0.12]); tb.axis("off")
    tb.add_patch(Rectangle((0, 0), 1, 1, fill=False, lw=1.2, transform=tb.transAxes))
    tb.plot([0, 1], [0.62, 0.62], color="k", lw=0.8, transform=tb.transAxes)
    tb.text(0.03, 0.78, "Knob stack v0.6 — isometric half-section A-A", fontsize=11, weight="bold", transform=tb.transAxes, va="center")
    for i, t in enumerate(["2026-10-31 · Ed (Edger_Equals) · knob module v1, 10HP", "Not to scale · mm · Z toward the panel front is up",
                           "STEP: knob-stack-v0.6-half-section.step (iso_section.py)"]):
        tb.text(0.03, 0.47 - i * 0.16, t, fontsize=7.5, transform=tb.transAxes, va="center")
    fig.savefig(os.path.join(HERE, "knob-stack-v0.6-iso-section.png"), dpi=200)
    print("done")
