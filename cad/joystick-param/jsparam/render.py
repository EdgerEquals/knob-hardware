"""One colour PNG: A-A section (plane y = 0 through the switch, plunger, cup, header and FPC) + isometric cut-away
(quadrant x > switch axis, y < ball row removed) + a dimensioned plan view. Cut faces in a lighter tint. No insets."""
import math, os, tempfile
import numpy as np
from build123d import *
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, Patch, FancyArrowPatch

GROUPS = [
    ("main PCB (local patch)", "#2e7d32", lambda n: n.startswith("main PCB")),
    ("J2 2×3 socket 11 mm (main PCB) / J1 header", "#424242", lambda n: n.startswith(("J2", "J1"))),
    ("joystick daughterboard (1.0 FR4)", "#1b5e20", lambda n: n == "joystick daughterboard"),
    ("M2×11 brass standoffs (GND)", "#c9a227", lambda n: n.startswith("brass standoff")),
    ("SKRHADE010 body (45°)", "#b0bec5", lambda n: n.startswith("SW1") and "body" in n),
    ("SKRHADE010 stem", "#fff176", lambda n: n.startswith("SW1") and "stem" in n),
    ("base (printed, glued, 4 pins, round stop)", "#8d6e63", lambda n: n.startswith("joystick base")),
    ("balls Ø2 stainless", "#90a4ae", lambda n: n.startswith("ball ")),
    ("carrier (printed): round stop, cup, spring hooks", "#ab47bc", lambda n: n.startswith("joystick carrier")),
    ("spider spring + plunger (printed nylon)", "#ff7043", lambda n: n.startswith("screen spider")),
    ("top screen 1.64\" AMOLED", "#101828", lambda n: n.startswith("top screen")),
    ("screen FPC [A]", "#ffb300", lambda n: n.startswith("screen FPC")),
    ("hold-down extension springs (to back panel)", "#fdd835", lambda n: n.startswith("hold-down")),
]
def group_of(n):
    for i, (_, _, f) in enumerate(GROUPS):
        if f(n): return i
    return 0
def lighten(hexc, k=0.45):
    h = hexc.lstrip("#"); r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % tuple(int(v + (255 - v) * k) for v in (r, g, b))

BIG = 200.0
def _mesh(solid, removed, planes, tol=0.02):
    """removed: solid region cut away (or None). planes: [(point, normal)] of the cut faces. -> {cut?: (P, T)}"""
    s = solid if removed is None else solid - removed
    out = {}
    for f in s.faces():
        try: vs, tri = f.tessellate(tol, 0.25)
        except Exception: continue
        if not tri: continue
        cut = False
        if f.geom_type == GeomType.PLANE:
            c = f.center(); nrm = f.normal_at(c)
            for p, nv in planes:
                if abs(np.dot(np.subtract((c.X, c.Y, c.Z), p), nv)) < 1e-4 and abs(abs(nrm.dot(Vector(*nv))) - 1) < 1e-6: cut = True
        P0, T0 = out.get(cut, (np.zeros((0, 3)), np.zeros((0, 3), int)))
        P = np.array([(v.X, v.Y, v.Z) for v in vs]); T = np.array(tri) + len(P0)
        out[cut] = (np.vstack([P0, P]), np.vstack([T0, T]))
    return out

def _shot(meshes, cam_dir, up, path, size, zoom=1.0, scale=None, centre=None):
    import pyvista as pv; pv.OFF_SCREEN = True
    pl = pv.Plotter(off_screen=True, window_size=size); pl.set_background("white")
    for n, m in meshes.items():
        col = GROUPS[group_of(n)][1]
        for cut, (P, T) in m.items():
            pm = pv.PolyData(P, np.hstack([np.full((len(T), 1), 3), T]).ravel())
            if cut:
                pl.add_mesh(pm, color=lighten(col), ambient=0.5, diffuse=0.6)
                be = pm.clean().extract_feature_edges(boundary_edges=True, feature_edges=False, non_manifold_edges=False, manifold_edges=False)
                if be.n_points: pl.add_mesh(be, color="#101010", line_width=1.6)
            else:
                pl.add_mesh(pm, color=col, specular=0.1, ambient=0.3, diffuse=0.75)
                fe = pm.clean().extract_feature_edges(feature_angle=35, boundary_edges=False, non_manifold_edges=False, manifold_edges=False)
                if fe.n_points: pl.add_mesh(fe, color="#303030", line_width=1.0)
    P = np.vstack([p for m in meshes.values() for (p, _) in m.values()])
    c = np.array(centre if centre is not None else (P.min(0) + P.max(0)) / 2); d = np.array(cam_dir, float); d /= np.linalg.norm(d)
    pl.camera.position = tuple(c + 500 * d); pl.camera.focal_point = tuple(c); pl.camera.up = up
    pl.enable_parallel_projection()
    if scale: pl.camera.parallel_scale = scale
    else: pl.reset_camera(); pl.camera.zoom(zoom)
    pl.camera.clipping_range = (1, 2000)
    pl.enable_anti_aliasing("ssaa"); pl.screenshot(path); pl.close()
    im = plt.imread(path); nz = np.where((im[..., :3] < 0.97).any(-1))
    if len(nz[0]): im = im[max(nz[0].min() - 8, 0): nz[0].max() + 8, max(nz[1].min() - 8, 0): nz[1].max() + 8]
    return im

def plan(ax, D):
    """Plan view, carrier frame (panel up = +y). The knob sits toward -y."""
    sw = D["sw"]; cw, ch = D["car"]
    y_pcb = D["pcb_above"] - D["place_y"]
    ax.add_patch(Rectangle((-D["pcb_w"] / 2, -D["place_y"] - 6), D["pcb_w"], y_pcb + D["place_y"] + 6, fc=lighten("#2e7d32", 0.75), ec="#2e7d32", lw=0.8))
    ax.plot([-D["pcb_w"] / 2, D["pcb_w"] / 2], [y_pcb, y_pcb], color="#1b5e20", lw=1.4)
    # knob arcs (design Ø41.7 and the live knob-param OD)
    for od, col, ls in ((D["knob_od_design"], "#1565c0", "-"), (D["knob_od_live"], "#90caf9", ":")):
        ax.add_patch(Circle((0, -D["place_y"]), od / 2, fill=False, ec=col, lw=1.2, ls=ls, zorder=2))
    x0b, x1b, y0b, y1b = D["base_x0"], D["base_x1"], D["base_y0"], D["base_y1"]
    ax.add_patch(Rectangle((x0b, y0b), x1b - x0b, y1b - y0b, fc=lighten("#8d6e63", 0.35), ec="#4e342e", lw=1.2))
    wx0, wx1, wy0, wy1 = D["win"]
    ax.add_patch(Rectangle((wx0, wy0), wx1 - wx0, wy1 - wy0, fc="white", ec="#4e342e", lw=0.8))
    ax.add_patch(Rectangle((D["hole_x0"], -D["hole_hy"]), D["hole_x1"] - D["hole_x0"], 2 * D["hole_hy"], fc="white", ec="#c62828", lw=1.2, ls="--"))
    dx, dy = D["db_xy"]; dw, dh, _ = D["db"]
    ax.add_patch(Rectangle((dx - dw / 2, dy - dh / 2), dw, dh, fc=lighten("#1b5e20", 0.15), ec="k", lw=1.2, zorder=3))
    hx, hy = D["hdr_xy"]
    ax.add_patch(Rectangle((hx - D["hdr_body"][0] / 2, hy - D["hdr_body"][1] / 2), D["hdr_body"][0], D["hdr_body"][1], fc="#424242", ec="k", zorder=4))
    for ix in (-1, 1):
        for iy in (-1, 0, 1):
            ax.add_patch(Circle((hx + ix * 1.27, hy + iy * 2.54), 0.32, fc="#ffd54f", ec="k", lw=0.5, zorder=5))
    for x, y in D["standoff_xy"]:
        ax.add_patch(Circle((x, y), D["standoff_d"] / 2, fc="#c9a227", ec="k", lw=0.6, zorder=5))
        ax.add_patch(Circle((x, y), 1.2, fc="white", ec="k", lw=0.4, zorder=6))
    th = math.radians(D["sw_rot"]); x0, y0 = D["sw_xy"]
    def rot(px, py): return (x0 + px * math.cos(th) - py * math.sin(th), y0 + px * math.sin(th) + py * math.cos(th))
    w2, d2 = sw["w"] / 2, sw["d"] / 2
    ax.add_patch(Polygon([rot(-w2, -d2), rot(w2, -d2), rot(w2, d2), rot(-w2, d2)], fc="#b0bec5", ec="k", lw=1.2, zorder=4))
    for px in (-3.575, 3.575):
        for py in (-1.425, 0, 1.425):
            q = [rot(px - 0.675, py - 0.5), rot(px + 0.675, py - 0.5), rot(px + 0.675, py + 0.5), rot(px - 0.675, py + 0.5)]
            ax.add_patch(Polygon(q, fc="#ffd54f", ec="k", lw=0.4, zorder=5))
    ax.add_patch(Circle((x0, y0), sw["stem_d"] / 2, fc="#fff176", ec="k", zorder=6))
    ax.add_patch(Circle((x0, y0), D["cup_od"] / 2, fill=False, ec="#ab47bc", lw=1.2, ls="--", zorder=6))
    for (adx, ady) in ((0, 1), (0, -1), (-1, 0), (1, 0)):
        ax.add_patch(FancyArrowPatch((x0 + 2.2 * adx, y0 + 2.2 * ady), (x0 + 4.8 * adx, y0 + 4.8 * ady), arrowstyle="-|>", mutation_scale=12, color="#c62828", lw=1.5, zorder=7))
    ax.text(x0 + 0.3, y0 + 5.2, "UP", color="#c62828", fontsize=9, weight="bold", zorder=7)
    qx, qy = D["stop_xy"]
    ax.add_patch(Circle((qx, qy), D["stop_d"] / 2, fc="#6d4c41", ec="k", zorder=5))
    ax.add_patch(Circle((qx, qy), D["stop_bore"] / 2, fill=False, ec="#4e342e", lw=1.0, ls="--", zorder=5))
    for x, y in D["balls"]:
        ax.add_patch(Circle((x, y), D["ball_d"] / 2, fc="#90a4ae", ec="k", zorder=4))
    for x, y in D["springs"]:
        ax.add_patch(Circle((x, y), D["spr_bore"] / 2, fc="white", ec="#4e342e", lw=0.8, zorder=4))
        ax.add_patch(Circle((x, y), D["spr_d"] / 2, fc="#fdd835", ec="k", lw=0.6, zorder=5))
    for x, y in D["pins"]:
        ax.add_patch(Circle((x, y), D["pin"][0] / 2, fc="#5d4037", ec="k", lw=0.5, zorder=4))
    ax.add_patch(Rectangle((D["fpc_x"] - 0.1, -D["fpc_w"] / 2), 0.2, D["fpc_w"], fc="#ffb300", ec="#ff6f00", zorder=6))
    ax.add_patch(Rectangle((-cw / 2, -ch / 2), cw, ch, fill=False, ec="#8e24aa", lw=1.6, ls="--", zorder=8))
    S = D["scr"]
    ax.add_patch(Rectangle((-S["w"] / 2, -S["h"] / 2), S["w"], S["h"], fill=False, ec="#101828", lw=1.0, ls="-.", zorder=8))
    ax.add_patch(Rectangle((D["sp_x"][0], -D["sp_hy"]), D["sp_x"][1] - D["sp_x"][0], 2 * D["sp_hy"], fill=False, ec="#ff7043", lw=0.9, ls=":", zorder=8))
    L = dict(fontsize=8, zorder=9)
    ax.annotate(f"daughterboard {dw:g}×{dh:g}, riser {D['riser_h']:g}", (dx, dy - dh / 2), (-24, -18), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    ax.annotate("SKRHADE010 −45°, round stop Ø0.8 travel", (x0, y0), (-24, -20.2), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    ax.annotate("J2 11 mm socket + two M2×11 standoffs", (hx, hy), (8, -18), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    ax.annotate("FPC bend [A] under the glass", (D["fpc_x"], D["slot_hy"]), (22, 6), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    ax.annotate("Ø2 stainless ball", D["balls"][0], (18, 12), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    ax.annotate("round stop", (qx, qy), (-24, 8), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    bx, by = D["board_xy"]
    ax.text(-24, 16.2, f"dashed purple = carrier {cw:.2f} × {ch:.2f}; dash-dot = screen {S['w']:g} × {S['h']:g}", fontsize=8)
    ax.text(-24, 14.6, f"blue arc = knob Ø{D['knob_od_design']:.2f} (design) / Ø{D['knob_od_live']:.2f} (live); green line = PCB top", fontsize=8)
    ax.text(-24, -22.2, f"base {D['base_w']:.1f} × {D['base_h']:.1f}; carrier centre board ({bx:.2f}, {by:.2f}); screen top z {D['scr_top']:.2f}", fontsize=8)
    ax.plot([8, 18], [-24.2, -24.2], color="k", lw=3); ax.text(13, -23.6, "10 mm", ha="center", fontsize=9)
    ax.set_xlim(-26, 32); ax.set_ylim(-26, 18); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])

def render(D, P, rows, png):
    tmp = tempfile.mkdtemp()
    # A-A: plane y = 0, keep y >= 0, look from -y
    remA = Pos(0, -BIG / 2, 0) * Box(BIG, BIG, BIG)
    mA = {n: _mesh(s, remA, [((0, 0, 0), (0, 1, 0))]) for n, s in P.items()}
    mA = {n: m for n, m in mA.items() if m}
    imA = _shot(mA, (0, -1, 0), (0, 0, 1), os.path.join(tmp, "a.png"), (1500, 1100), centre=(0, 0, 22.0), scale=30.0)
    # iso: remove x > switch axis and y below the lower ball row
    xr = D["sw_xy"][0]
    yr = min(y for _, y in D["balls"]) + 1.0
    remI = Pos(xr + BIG / 2, yr - BIG / 2, 0) * Box(BIG, BIG, BIG)
    mI = {n: _mesh(s, remI, [((xr, 0, 0), (1, 0, 0)), ((0, yr, 0), (0, 1, 0))]) for n, s in P.items()}
    mI = {n: m for n, m in mI.items() if m}
    imI = _shot(mI, (1.0, -1.25, 0.95), (0, 0, 1), os.path.join(tmp, "i.png"), (1400, 1200), centre=(0, 0, 22.0), scale=32.0)
    fig = plt.figure(figsize=(28, 13.5), dpi=110)
    axA = fig.add_axes([0.005, 0.27, 0.355, 0.64]); axA.imshow(imA); axA.axis("off")
    axI = fig.add_axes([0.365, 0.27, 0.30, 0.64]); axI.imshow(imI); axI.axis("off")
    axP = fig.add_axes([0.67, 0.25, 0.325, 0.68]); plan(axP, D)
    axA.set_title(f"SECTION A-A (plane y = 0 through the switch, cup, plunger,\nheader and FPC; viewed from -y, panel bottom)", fontsize=13, weight="bold", loc="left")
    axI.set_title(f"ISOMETRIC CUT-AWAY (block x > switch axis, y < ball row\nremoved: shows the switch, cup, plunger, ball + spring)", fontsize=13, weight="bold", loc="left")
    axP.set_title("PLAN (front view, panel up = +y)", fontsize=13, weight="bold", loc="left")
    sw = D["sw"]
    fig.suptitle(f"Top-screen joystick {D['version']} — DO0164FMST05 on the SKRHADE010, round stop, 11 mm riser (1 Nov 2026, Ed)", fontsize=16, weight="bold", x=0.01, ha="left", y=0.985)
    nf = sum(not r["ok"] for r in rows)
    key = (f"Stack (z from the main-PCB front): screen top {D['scr_top']:.2f} = knob top {D['z_knob_top']:.2f} − {D['scr_below_knob']:g}. "
           f"J2 / riser 0–{D['z_db0']:g} · daughterboard {D['z_db0']:g}–{D['z_db1']:g} · stem top {D['z_stem_top']:.2f} · "
           f"carrier underside {D['z_c0']:.2f} · floor thickness {D['car_floor']:.1f} · spider {D['z_sp0']:.2f}–{D['z_sp1']:.2f} (travel {D['sp_gap']:g}) · "
           f"screen {D['z_scr0']:.2f}–{D['scr_top']:.2f}.\n"
           f"Slide: round stop radius {D['slide']:g} (circle Ø{2*D['slide']:g}) in every direction, including diagonals. A direction needs {D['slide_need']:.3f}. "
           f"Press: spider +{D['sp_f_click']:.2f} N on {sw['push_f']:g} N → {D['press_f']:.2f} N; the switch stop takes the full press. "
           f"Hold-down: 4 × {D['spr_f']:g} N, length {D['spr_len']:.0f} mm (back panel {D['back_panel']:.1f} [A]). "
           f"Carrier {D['car'][0]:.2f} × {D['car'][1]:.2f}.\n"
           f"Checks: {len(rows) - nf}/{len(rows)} PASS. Footprint −45°: a/b/c/d → UP/RIGHT/LEFT/DOWN, confirmed at first-power calibration. "
           f"FPC exit, pitch and pin-out are still open [A].")
    fig.text(0.01, 0.235, key, fontsize=12, va="top")
    shown = sorted({group_of(n) for n in P})
    fig.legend(handles=[Patch(facecolor=GROUPS[i][1], edgecolor="#222", label=GROUPS[i][0]) for i in shown], loc="lower center", ncol=4, fontsize=11.5, frameon=True,
               title="PART COLOURS (cut faces lighter)", title_fontsize=12, bbox_to_anchor=(0.5, 0.005))
    fig.savefig(png, dpi=fig.dpi)
    # separate plan PNG too (same drawing, bigger)
    f2, ax2 = plt.subplots(figsize=(12, 10), dpi=120); plan(ax2, D)
    ax2.set_title(f"Top-screen joystick {D['version']} — plan (front view, panel up = +y)", fontsize=14, weight="bold", loc="left")
    f2.tight_layout(); f2.savefig(png.replace(".png", "-plan.png"))
