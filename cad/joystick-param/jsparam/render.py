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
    ("1×3 H11 sockets (main PCB)", "#546e7a", lambda n: n.startswith("socket ")),
    ("1×3 long-pin headers (underside)", "#424242", lambda n: n.startswith("header ")),
    ("joystick daughterboard (1.0 FR4)", "#1b5e20", lambda n: n == "joystick daughterboard"),
    ("M2×35 brass standoffs (GND, ×4)", "#c9a227", lambda n: n.startswith("brass standoff")),
    ("SKRHADE010 body (45°)", "#b0bec5", lambda n: n.startswith("SW1") and "body" in n),
    ("SKRHADE010 stem", "#fff176", lambda n: n.startswith("SW1") and "stem" in n),
    ("seat plate (glued on the daughterboard)", "#8d6e63", lambda n: n.startswith("seat plate")),
    ("balls Ø2 stainless", "#90a4ae", lambda n: n.startswith("ball ")),
    ("carrier (thin shell, round stop, cup)", "#ab47bc", lambda n: n.startswith("joystick carrier")),
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
    """Plan view, carrier frame (panel up = +y). The knob sits toward -y. The switch is on the origin."""
    sw = D["sw"]; cw, ch = D["car"]
    y_pcb = D["y_pcb"]
    ax.add_patch(Rectangle((-D["pcb_w"] / 2, -D["place_y"] - 6), D["pcb_w"], y_pcb + D["place_y"] + 6, fc=lighten("#2e7d32", 0.75), ec="#2e7d32", lw=0.8))
    ax.plot([-D["pcb_w"] / 2, D["pcb_w"] / 2], [y_pcb, y_pcb], color="#1b5e20", lw=1.4)
    for od, col, ls in ((D["knob_od_design"], "#1565c0", "-"), (D["knob_od_live"], "#90caf9", ":")):
        ax.add_patch(Circle((0, -D["place_y"]), od / 2, fill=False, ec=col, lw=1.2, ls=ls, zorder=2))
    x0, x1, y0, y1 = D["board_x0"], D["board_x1"], D["board_y0"], D["board_y1"]
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=lighten("#1b5e20", 0.25), ec="k", lw=1.2, zorder=3))
    ax.add_patch(Circle((0, 0), D["cut_r"], fc="white", ec="#4e342e", lw=0.8, zorder=3))
    ax.add_patch(Rectangle((D["hole_x0"], -D["hole_hy"]), D["hole_x1"] - D["hole_x0"], 2 * D["hole_hy"], fc="none", ec="#c62828", lw=1.0, ls="--", zorder=3))
    for hx, hy in D["hdr_xy"]:
        ax.add_patch(Rectangle((hx - D["hdr_len"] / 2, hy - D["hdr_wid"] / 2), D["hdr_len"], D["hdr_wid"], fc="#424242", ec="k", zorder=4))
        for k in (-1, 0, 1):
            ax.add_patch(Circle((hx + k * D["pitch"], hy), 0.32, fc="#ffd54f", ec="k", lw=0.4, zorder=5))
    for x, y in D["standoff_xy"]:
        ax.add_patch(Circle((x, y), D["standoff_d"] / 2, fc="#c9a227", ec="k", lw=0.6, zorder=5))
        ax.add_patch(Circle((x, y), D["drill_m2"] / 2, fc="white", ec="k", lw=0.4, zorder=6))
    th = math.radians(D["sw_rot"])
    def rot(px, py): return (px * math.cos(th) - py * math.sin(th), px * math.sin(th) + py * math.cos(th))
    w2, d2 = sw["w"] / 2, sw["d"] / 2
    ax.add_patch(Polygon([rot(-w2, -d2), rot(w2, -d2), rot(w2, d2), rot(-w2, d2)], fc="#b0bec5", ec="k", lw=1.2, zorder=4))
    ax.add_patch(Circle((0, 0), sw["stem_d"] / 2, fc="#fff176", ec="k", zorder=6))
    ax.add_patch(Circle((0, 0), D["cup_od"] / 2, fill=False, ec="#ab47bc", lw=1.2, ls="--", zorder=6))
    for (adx, ady) in ((0, 1), (0, -1), (-1, 0), (1, 0)):
        ax.add_patch(FancyArrowPatch((2.2 * adx, 2.2 * ady), (4.6 * adx, 4.6 * ady), arrowstyle="-|>", mutation_scale=12, color="#c62828", lw=1.4, zorder=7))
    ax.text(0.4, 5.3, "UP", color="#c62828", fontsize=9, weight="bold", zorder=7)
    qx, qy = D["stop_xy"]
    ax.add_patch(Circle((qx, qy), D["stop_d"] / 2, fc="#6d4c41", ec="k", zorder=5))
    ax.add_patch(Circle((qx, qy), D["stop_bore"] / 2, fill=False, ec="#4e342e", lw=1.0, ls="--", zorder=5))
    for x, y in D["balls"]:
        ax.add_patch(Circle((x, y), D["ball_d"] / 2, fc="#90a4ae", ec="k", zorder=4))
    for x, y in D["springs"]:
        ax.add_patch(Circle((x, y), D["spr_bore"] / 2, fc="white", ec="#4e342e", lw=0.8, zorder=4))
        ax.add_patch(Circle((x, y), D["spr_d"] / 2, fc="#fdd835", ec="k", lw=0.6, zorder=5))
    ax.add_patch(Rectangle((D["fpc_x"] - 0.1, -D["fpc_w"] / 2), 0.2, D["fpc_w"], fc="#ffb300", ec="#ff6f00", zorder=6))
    ax.add_patch(Rectangle((-cw / 2, -ch / 2), cw, ch, fill=False, ec="#8e24aa", lw=1.6, ls="--", zorder=8))
    S = D["scr"]
    ax.add_patch(Rectangle((-S["w"] / 2, -S["h"] / 2), S["w"], S["h"], fill=False, ec="#101828", lw=1.0, ls="-.", zorder=8))
    L = dict(fontsize=8, zorder=9)
    ax.annotate(f"daughterboard {D['db'][0]:.1f}×{D['db'][1]:.1f}, riser {D['riser_h']:g}", (0, y0), (-24, y0 - 3), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    ax.annotate("SKRHADE010 on the axis, −45°", (0, 0), (-24, -16), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    ax.annotate("two 1×3 headers + four M2×35", D["hdr_xy"][0], (8, -14), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    ax.annotate("FPC bend [A]", (D["fpc_x"], D["slot_hy"]), (18, 8), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    ax.annotate("Ø2 ball", D["balls"][0], (16, 10), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    ax.annotate("round stop", (qx, qy), (-22, qy - 2), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    bx, by = D["board_xy"]
    ax.text(-24, 16.2, f"dashed purple = carrier {cw:.2f} × {ch:.2f}; dash-dot = screen {S['w']:g} × {S['h']:g}", fontsize=8)
    ax.text(-24, 14.6, f"blue arc = knob Ø{D['knob_od_design']:.2f} (design) / Ø{D['knob_od_live']:.2f} (live); green line = PCB top", fontsize=8)
    ax.text(-24, -22.5, f"no base enclosure; carrier centre board ({bx:.2f}, {by:.2f}); screen top z {D['scr_top']:.2f}; floor {D['car_floor']:.2f}", fontsize=8)
    ax.plot([8, 18], [-24.4, -24.4], color="k", lw=3); ax.text(13, -23.8, "10 mm", ha="center", fontsize=9)
    ax.set_xlim(-26, 32); ax.set_ylim(-26, 18); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])

def _meshes(parts, removed, planes, tol):
    out = {}
    for n, s in parts.items():
        m = _mesh(s, removed, planes, tol)
        if m: out[n] = m
    return out

def _centre_z(D):
    return (0.0, 0.0, D["scr_top"] * 0.55)

def preview(D, P, png):
    """Low-resolution isometric, written before the colour sheet."""
    tmp = tempfile.mkdtemp()
    m = _meshes(P, None, [], tol=0.18)
    im = _shot(m, (1.05, -1.15, 0.85), (0, 0, 1), os.path.join(tmp, "p.png"), (900, 700), centre=_centre_z(D), scale=34.0)
    fig, ax = plt.subplots(figsize=(9, 7), dpi=80)
    ax.imshow(im); ax.axis("off")
    ax.set_title(f"Top-screen joystick {D['version']} — preview (low res)", fontsize=13, weight="bold", loc="left")
    fig.tight_layout(); fig.savefig(png); plt.close(fig)

def render(D, P, rows, png):
    tmp = tempfile.mkdtemp()
    zc = _centre_z(D)
    # A-A: plane y = 0, keep y >= 0, look from -y
    remA = Pos(0, -BIG / 2, 0) * Box(BIG, BIG, BIG)
    mA = _meshes(P, remA, [((0, 0, 0), (0, 1, 0))], 0.04)
    imA = _shot(mA, (0, -1, 0), (0, 0, 1), os.path.join(tmp, "a.png"), (1500, 1100), centre=zc, scale=28.0)
    # iso quarter: drop +x and -y so the switch, a header, a ball and the stop show
    remI = Pos(BIG / 2, -BIG / 2, 0) * Box(BIG, BIG, BIG)
    mI = _meshes(P, remI, [((0, 0, 0), (1, 0, 0)), ((0, 0, 0), (0, 1, 0))], 0.04)
    imI = _shot(mI, (1.05, -1.2, 0.9), (0, 0, 1), os.path.join(tmp, "i.png"), (1400, 1200), centre=zc, scale=30.0)
    fig = plt.figure(figsize=(28, 13.5), dpi=110)
    axA = fig.add_axes([0.005, 0.27, 0.355, 0.64]); axA.imshow(imA); axA.axis("off")
    axI = fig.add_axes([0.365, 0.27, 0.30, 0.64]); axI.imshow(imI); axI.axis("off")
    axP = fig.add_axes([0.67, 0.25, 0.325, 0.68]); plan(axP, D)
    axA.set_title("SECTION A-A (plane y = 0 through the switch, both headers,\ncup and plunger; viewed from -y)", fontsize=13, weight="bold", loc="left")
    axI.set_title("ISOMETRIC QUARTER CUT (+x and -y removed:\nswitch on axis, header, ball seat, round stop)", fontsize=13, weight="bold", loc="left")
    axP.set_title("PLAN (front view, panel up = +y)", fontsize=13, weight="bold", loc="left")
    sw = D["sw"]
    fig.suptitle(f"Top-screen joystick {D['version']} — DO0164FMST05 on the SKRHADE010, thin carrier, {D['riser_h']:g} mm riser (1 Nov 2026, Ed)", fontsize=16, weight="bold", x=0.01, ha="left", y=0.985)
    nf = sum(not r["ok"] for r in rows)
    key = (f"Stack (z from the main-PCB front): screen top {D['scr_top']:.2f} = knob top {D['z_knob_top']:.2f} − {D['scr_below_knob']:g}. "
           f"Riser 0–{D['z_db0']:g} (four M2×{D['riser_h']:g} + two 1×3 H11 sockets) · daughterboard {D['z_db0']:g}–{D['z_db1']:g} · "
           f"stem top {D['z_stem_top']:.2f} · carrier underside {D['z_c0']:.2f} · floor {D['car_floor']:.2f} · "
           f"spider {D['z_sp0']:.2f}–{D['z_sp1']:.2f} (travel {D['sp_gap']:g}) · screen {D['z_scr0']:.2f}–{D['scr_top']:.2f}.\n"
           f"Slide: round stop radius {D['slide']:g} (circle Ø{2*D['slide']:g}) in every direction. A direction needs {D['slide_need']:.3f}. "
           f"Press: spider +{D['sp_f_click']:.2f} N on {sw['push_f']:g} N → {D['press_f']:.2f} N. "
           f"Hold-down: 4 × {D['spr_f']:g} N, length {D['spr_len']:.0f} mm (back panel {D['back_panel']:g} [A]). "
           f"Well wall {D['well_wall']:.2f}. Carrier {D['car'][0]:.2f} × {D['car'][1]:.2f}. No printed base.\n"
           f"Checks: {len(rows) - nf}/{len(rows)} PASS. Switch on the carrier axis. Footprint −45°: a/b/c/d → UP/RIGHT/LEFT/DOWN, confirmed at first-power calibration. "
           f"FPC exit, pitch and pin-out are still open [A].")
    fig.text(0.01, 0.235, key, fontsize=12, va="top")
    shown = sorted({group_of(n) for n in P})
    fig.legend(handles=[Patch(facecolor=GROUPS[i][1], edgecolor="#222", label=GROUPS[i][0]) for i in shown], loc="lower center", ncol=4, fontsize=11, frameon=True,
               title="PART COLOURS (cut faces lighter)", title_fontsize=12, bbox_to_anchor=(0.5, 0.005))
    fig.savefig(png, dpi=fig.dpi); plt.close(fig)
    f2, ax2 = plt.subplots(figsize=(12, 10), dpi=120); plan(ax2, D)
    ax2.set_title(f"Top-screen joystick {D['version']} — plan (front view, panel up = +y)", fontsize=14, weight="bold", loc="left")
    f2.tight_layout(); f2.savefig(png.replace(".png", "-plan.png")); plt.close(f2)
    # clean: the whole stack, no cut, no dimensions
    mC = _meshes(P, None, [], 0.05)
    imC = _shot(mC, (1.05, -1.15, 0.82), (0, 0, 1), os.path.join(tmp, "c.png"), (1600, 1200), centre=zc, scale=32.0)
    fc, ac = plt.subplots(figsize=(14, 10), dpi=110)
    ac.imshow(imC); ac.axis("off")
    ac.set_title(f"Top-screen joystick {D['version']} — clean view", fontsize=14, weight="bold", loc="left")
    shown = sorted({group_of(n) for n in P})
    fc.legend(handles=[Patch(facecolor=GROUPS[i][1], edgecolor="#222", label=GROUPS[i][0]) for i in shown], loc="lower center", ncol=3, fontsize=9, frameon=True)
    fc.tight_layout(); fc.savefig(png.replace(".png", "-clean.png")); plt.close(fc)
    views(D, P, os.path.join(os.path.dirname(png), "views"), tmp)

def views(D, P, folder, tmp=None):
    """iso above, iso below, section X, section Y, exploded, quarter cut."""
    os.makedirs(folder, exist_ok=True)
    tmp = tmp or tempfile.mkdtemp()
    zc = _centre_z(D)
    remX = Pos(-BIG / 2, 0, 0) * Box(BIG, BIG, BIG)
    remY = Pos(0, -BIG / 2, 0) * Box(BIG, BIG, BIG)
    remQ = Pos(BIG / 2, -BIG / 2, 0) * Box(BIG, BIG, BIG)
    mX = _meshes(P, remX, [((0, 0, 0), (1, 0, 0))], 0.05)
    mY = _meshes(P, remY, [((0, 0, 0), (0, 1, 0))], 0.05)
    mQ = _meshes(P, remQ, [((0, 0, 0), (1, 0, 0)), ((0, 0, 0), (0, 1, 0))], 0.05)
    mAll = _meshes(P, None, [], 0.06)
    _shot(mAll, (0.55, -0.7, 1.45), (0, 0, 1), os.path.join(tmp, "va.png"), (1400, 1100), centre=zc, scale=30.0)
    _save_view(os.path.join(tmp, "va.png"), os.path.join(folder, "iso-above.png"), "iso above")
    _shot(mAll, (0.65, -0.75, -1.2), (0, 0, 1), os.path.join(tmp, "vb.png"), (1400, 1100), centre=zc, scale=30.0)
    _save_view(os.path.join(tmp, "vb.png"), os.path.join(folder, "iso-below.png"), "iso below")
    im = _shot(mX, (-1, -0.15, 0.08), (0, 0, 1), os.path.join(tmp, "vx.png"), (1500, 1000), centre=zc, scale=28.0)
    _save_im(im, os.path.join(folder, "section-x.png"), "section X (plane x = 0, from -x)")
    im = _shot(mY, (0.1, -1, 0.05), (0, 0, 1), os.path.join(tmp, "vy.png"), (1500, 1000), centre=zc, scale=28.0)
    _save_im(im, os.path.join(folder, "section-y.png"), "section Y (plane y = 0, from -y)")
    im = _shot(mQ, (1.05, -1.15, 0.9), (0, 0, 1), os.path.join(tmp, "vq.png"), (1400, 1100), centre=zc, scale=30.0)
    _save_im(im, os.path.join(folder, "quarter-cut.png"), "quarter cut (+x, -y removed)")
    exploded = _explode(P, D)
    mE = _meshes(exploded, None, [], 0.08)
    im = _shot(mE, (1.0, -1.1, 0.75), (0, 0, 1), os.path.join(tmp, "ve.png"), (1200, 1600), centre=(0, 0, D["scr_top"]), scale=48.0)
    _save_im(im, os.path.join(folder, "exploded.png"), "exploded")

def _explode(P, D):
    """Lift the stack apart along z. Headers stay on the daughterboard; sockets stay on the main PCB."""
    lift = {
        "top screen": 55, "screen spider": 42, "joystick carrier": 28, "ball ": 18,
        "seat plate": 12, "SW1": 12, "joystick daughterboard": 8, "header ": 8,
        "brass standoff": 0, "socket ": 0, "main PCB": 0, "screen FPC": 8, "hold-down": 0,
    }
    out = {}
    for n, s in P.items():
        dz = 0
        for k, v in lift.items():
            if n.startswith(k): dz = v; break
        out[n] = Pos(0, 0, dz) * s
    return out

def _save_im(im, path, title):
    fig, ax = plt.subplots(figsize=(11, 8.5), dpi=110)
    ax.imshow(im); ax.axis("off"); ax.set_title(title, fontsize=13, weight="bold", loc="left")
    fig.tight_layout(); fig.savefig(path); plt.close(fig)

def _save_view(src, path, title):
    im = plt.imread(src); _save_im(im, path, title)
