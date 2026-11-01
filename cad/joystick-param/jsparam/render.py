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
    ("J2 2×3 socket (main PCB) / J1 header", "#424242", lambda n: n.startswith(("J2", "J1"))),
    ("joystick daughterboard (1.0 FR4)", "#1b5e20", lambda n: n == "joystick daughterboard"),
    ("SKRHADE010 body (45°)", "#b0bec5", lambda n: n.startswith("SW1") and "body" in n),
    ("SKRHADE010 stem", "#fff176", lambda n: n.startswith("SW1") and "stem" in n),
    ("base (printed, glued, 4 pins, riser post)", "#8d6e63", lambda n: n.startswith("joystick base")),
    ("balls Ø2 (steel)", "#78909c", lambda n: n.startswith("ball ")),
    ("carrier (printed): skirt stop, cup, spring bosses", "#ab47bc", lambda n: n.startswith("joystick carrier")),
    ("spider spring + plunger (printed nylon)", "#ff7043", lambda n: n.startswith("screen spider")),
    ("top screen 1.14\" (glass)", "#101828", lambda n: n.startswith("top screen")),
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
    """Plan view from the front (panel up = +y), outlines from the params."""
    sw = D["sw"]; cw, ch = D["car"]
    ax.add_patch(Rectangle((-20, -12.5), 40, 25, fc=lighten("#2e7d32", 0.6), ec="#2e7d32", lw=1))
    bw, bh = D["base_w"], D["base_h"]
    ax.add_patch(Rectangle((-bw / 2, -bh / 2), bw, bh, fc=lighten("#8d6e63", 0.35), ec="#4e342e", lw=1.2))
    ax.add_patch(Rectangle((-D["win"][0] / 2, -D["win"][1] / 2), *D["win"], fc="white", ec="#4e342e", lw=0.8))
    ax.add_patch(Rectangle((D["hole_x0"], -D["hole_hy"]), D["hole_x1"] - D["hole_x0"], 2 * D["hole_hy"], fc="white", ec="#c62828", lw=1.2, ls="--"))
    dw, dh, _ = D["db"]
    ax.add_patch(Rectangle((-dw / 2, -dh / 2), dw, dh, fc=lighten("#1b5e20", 0.15), ec="k", lw=1.2, zorder=3))
    ax.add_patch(Rectangle((D["hdr_x"] - D["hdr_body"][0] / 2, -D["hdr_body"][1] / 2), D["hdr_body"][0], D["hdr_body"][1], fc="#424242", ec="k", zorder=4))
    for ix in (-1, 1):
        for iy in (-1, 0, 1): ax.add_patch(Circle((D["hdr_x"] + ix * 1.27, iy * 2.54), 0.32, fc="#ffd54f", ec="k", lw=0.5, zorder=5))
    # switch body (rotated) + stem + direction arrows (switch a/b/c/d -> screen UP/RIGHT/LEFT/DOWN)
    th = math.radians(D["sw_rot"]); x0 = D["sw_x"]
    def rot(px, py): return (x0 + px * math.cos(th) - py * math.sin(th), px * math.sin(th) + py * math.cos(th))
    w2, d2 = sw["w"] / 2, sw["d"] / 2
    ax.add_patch(Polygon([rot(-w2, -d2), rot(w2, -d2), rot(w2, d2), rot(-w2, d2)], fc="#b0bec5", ec="k", lw=1.2, zorder=4))
    for px in (-3.575, 3.575):
        for py in (-1.425, 0, 1.425):
            q = [rot(px - 0.675, py - 0.5), rot(px + 0.675, py - 0.5), rot(px + 0.675, py + 0.5), rot(px - 0.675, py + 0.5)]
            ax.add_patch(Polygon(q, fc="#ffd54f", ec="k", lw=0.4, zorder=5))
    ax.add_patch(Circle((x0, 0), sw["stem_d"] / 2, fc="#fff176", ec="k", zorder=6))
    ax.add_patch(Circle((x0, 0), D["cup_od"] / 2, fill=False, ec="#ab47bc", lw=1.2, ls="--", zorder=6))
    for lab, (dx, dy) in (("UP", (0, 1)), ("DOWN", (0, -1)), ("LEFT", (-1, 0)), ("RIGHT", (1, 0))):
        ax.add_patch(FancyArrowPatch((x0 + 2.0 * dx, 2.0 * dy), (x0 + 4.6 * dx, 4.6 * dy), arrowstyle="-|>", mutation_scale=12, color="#c62828", lw=1.6, zorder=7))
    ax.text(x0 + 0.2, 5.0, "UP", color="#c62828", fontsize=9, weight="bold", zorder=7)
    for x, y in [(sx * D["ball_xy"][0], sy * D["ball_xy"][1]) for sx in (1, -1) for sy in (1, -1)]:
        ax.add_patch(Circle((x, y), D["ball_d"] / 2, fc="#78909c", ec="k", zorder=4))
    for x, y in [(sx * D["spr_xy"][0], sy * D["spr_xy"][1]) for sx in (1, -1) for sy in (1, -1)]:
        ax.add_patch(Circle((x, y), D["spr_bore"] / 2, fc="white", ec="#4e342e", lw=0.8, zorder=4))
        ax.add_patch(Circle((x, y), D["spr_d"] / 2, fc="#fdd835", ec="k", lw=0.6, zorder=5))
    py = bh / 2 - D["base_wall"] / 2
    for x, y in [(sx * D["pin_xy"], sy * py) for sx in (1, -1) for sy in (1, -1)]:
        ax.add_patch(Circle((x, y), D["pin"][0] / 2, fc="#5d4037", ec="k", lw=0.5, zorder=4))
    ax.add_patch(Rectangle((D["fpc_x"] - 0.1, -D["fpc_w"] / 2), 0.2, D["fpc_w"], fc="#ffb300", ec="#ff6f00", zorder=6))
    ax.add_patch(Rectangle((-cw / 2, -ch / 2), cw, ch, fill=False, ec="#8e24aa", lw=1.6, ls="--", zorder=8))
    S = D["scr"]; ax.add_patch(Rectangle((-S["w"] / 2, -S["h"] / 2), S["w"], S["h"], fill=False, ec="#101828", lw=1.0, ls="-.", zorder=8))
    ax.add_patch(Rectangle((D["sp_x"][0], -D["sp_hy"]), D["sp_x"][1] - D["sp_x"][0], 2 * D["sp_hy"], fill=False, ec="#ff7043", lw=0.9, ls=":", zorder=8))
    # labels
    L = dict(fontsize=8.5, zorder=9)
    ax.annotate(f"daughterboard {dw:g} × {dh:g} × {D['db'][2]:g}", (-dw / 2, -dh / 2), (-19.5, -15.5), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    ax.annotate("SKRHADE010 at 45°, stem / Ø3.15 cup", (x0 - 2, -2.5), (-19.5, -17.3), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    ax.annotate("J1 2×3 2.54 → J2 socket 8.5 on the main PCB", (D["hdr_x"], -3.8), (-1.0, -15.5), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    ax.annotate(f"FPC slot: carrier {D['slot_x'][1] - D['slot_x'][0]:g} × {2 * D['slot_hy']:g};\nbase notch / PCB {D['hole_x1'] - D['hole_x0']:.1f} × {2 * D['hole_hy']:.1f}", (D["hole_x1"], 0), (17.2, -2.0), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    ax.annotate(f"Ø{D['ball_d']:g} ball in a hemisphere seat", (D["ball_xy"][0], D["ball_xy"][1]), (12.0, 14.2), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    ax.annotate(f"spring Ø{D['spr_d']:g} in Ø{D['spr_bore']:g} (base + PCB)", (D["spr_xy"][0], D["spr_xy"][1]), (-1.0, 15.6), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    ax.annotate(f"locating pin Ø{D['pin'][0]:g}", (-D["pin_xy"], py), (-19.5, 14.2), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    ax.text(-19.5, 17.4, f"dashed purple = carrier {cw:g} × {ch:g}; dash-dot = screen {S['w']:g} × {S['h']:g}; dotted orange = spider", fontsize=8.5)
    ax.text(-19.5, -19.3, f"base {bw:.1f} × {bh:.1f} glued to the main PCB; carrier centre = board ({25.25:.2f}, {52.9 - D['place_y']:.1f})", fontsize=8.5)
    ax.plot([10, 20], [-21.0, -21.0], color="k", lw=3); ax.text(15, -20.6, "10 mm", ha="center", fontsize=9)
    ax.set_xlim(-21, 33); ax.set_ylim(-22, 18.5); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])

def render(D, P, rows, png):
    tmp = tempfile.mkdtemp()
    # A-A: plane y = 0, keep y >= 0, look from -y
    remA = Pos(0, -BIG / 2, 0) * Box(BIG, BIG, BIG)
    mA = {n: _mesh(s, remA, [((0, 0, 0), (0, 1, 0))]) for n, s in P.items()}
    mA = {n: m for n, m in mA.items() if m}
    imA = _shot(mA, (0, -1, 0), (0, 0, 1), os.path.join(tmp, "a.png"), (1500, 1000), centre=(0, 0, 7.0), scale=16.5)
    # iso: remove x > sw_x and y < ball row
    xr, yr = D["sw_x"], D["ball_xy"][1]
    remI = Pos(xr + BIG / 2, yr - BIG / 2, 0) * Box(BIG, BIG, BIG)
    mI = {n: _mesh(s, remI, [((xr, 0, 0), (1, 0, 0)), ((0, yr, 0), (0, 1, 0))]) for n, s in P.items()}
    mI = {n: m for n, m in mI.items() if m}
    imI = _shot(mI, (1.0, -1.25, 0.95), (0, 0, 1), os.path.join(tmp, "i.png"), (1400, 1200), centre=(0, 0, 8.0), scale=19.0)
    fig = plt.figure(figsize=(28, 13.5), dpi=110)
    axA = fig.add_axes([0.005, 0.27, 0.355, 0.64]); axA.imshow(imA); axA.axis("off")
    axI = fig.add_axes([0.365, 0.27, 0.30, 0.64]); axI.imshow(imI); axI.axis("off")
    axP = fig.add_axes([0.67, 0.25, 0.325, 0.68]); plan(axP, D)
    axA.set_title(f"SECTION A-A (plane y = 0 through the switch, cup, plunger,\nheader and FPC; viewed from -y, panel bottom)", fontsize=13, weight="bold", loc="left")
    axI.set_title(f"ISOMETRIC CUT-AWAY (block x > switch axis, y < ball row\nremoved: shows the switch, cup, plunger, ball + spring)", fontsize=13, weight="bold", loc="left")
    axP.set_title("PLAN (front view, panel up = +y)", fontsize=13, weight="bold", loc="left")
    sw = D["sw"]
    fig.suptitle(f"Top-screen joystick stack {D['version']} — {sw['part']} on a daughterboard over the main PCB; ball-slide carrier, spider, cup (1 Nov 2026, Ed / Edger_Equals)", fontsize=17, weight="bold", x=0.01, ha="left", y=0.985)
    nf = sum(not r["ok"] for r in rows)
    key = (f"Stack (z from the main-PCB front): J2 socket / riser 0-{D['z_db0']:g} · daughterboard {D['z_db0']:g}-{D['z_db1']:g} · switch body to {D['z_sw1']:.2f}, stem top {D['z_stem_top']:.2f} · "
           f"cup {D['z_cup0']:.2f}-{D['z_c0']:.2f} · balls (Ø{D['ball_d']:g}) centre {D['z_ball']:.2f} = base top · carrier underside {D['z_c0']:.2f} · spider {D['z_sp0']:.2f}-{D['z_sp1']:.2f} "
           f"(free travel {D['sp_gap']:g}) · screen {D['z_scr0']:.2f}-{D['scr_top']:.2f} [A].\n"
           f"Slide: ±{D['slide']:g} per axis to the skirt stop; a direction needs {D['slide_need']:.3f} (cup clearance {D['cup_rad_clear']:.3f} + tilt {sw['tilt_travel']:g}). Press: plunger {D['plunger_gap']:g} above the stem, "
           f"{sw['push_travel']:g} click, spider k ≈ {D['sp_k']:.1f} N/mm → ≈ {D['press_f']:.1f} N total; the switch's own stop takes the full press. "
           f"Hold-down: 4 × {D['spr_f']:g} N extension springs (~{D['spr_len']:.0f} mm to the back panel) inside the balls.\n"
           f"Checks: {len(rows) - nf}/{len(rows)} PASS. Footprint turned 45°: switch a/b/c/d → screen UP/RIGHT/LEFT/DOWN [verify on the bench]; diagonals = two contacts in firmware.")
    fig.text(0.01, 0.235, key, fontsize=12, va="top")
    shown = sorted({group_of(n) for n in P})
    fig.legend(handles=[Patch(facecolor=GROUPS[i][1], edgecolor="#222", label=GROUPS[i][0]) for i in shown], loc="lower center", ncol=4, fontsize=11.5, frameon=True,
               title="PART COLOURS (cut faces lighter)", title_fontsize=12, bbox_to_anchor=(0.5, 0.005))
    fig.savefig(png, dpi=fig.dpi)
    # separate plan PNG too (same drawing, bigger)
    f2, ax2 = plt.subplots(figsize=(12, 10), dpi=120); plan(ax2, D)
    ax2.set_title(f"Top-screen joystick {D['version']} — plan (front view, panel up = +y)", fontsize=14, weight="bold", loc="left")
    f2.tight_layout(); f2.savefig(png.replace(".png", "-plan.png"))
