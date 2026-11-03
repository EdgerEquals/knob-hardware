"""One colour PNG: A-A section (plane y = 0 through the switch, cup, peg, springs and FPC) + isometric cut-away
(quadrant x > switch axis, y < ball row removed) + a dimensioned plan view. Cut faces in a lighter tint. No insets."""
import math, os, tempfile
import numpy as np
from build123d import *
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, Patch, FancyArrowPatch

GROUPS = [
    ("faceplate (UTR-8100 case proxy)", "#b3e5fc", lambda n: n.startswith("faceplate")),
    ("main PCB (local patch)", "#2e7d32", lambda n: n.startswith("main PCB")),
    ("2×5 H11 sockets (main PCB)", "#546e7a", lambda n: n.startswith("socket ")),
    ("2×5 long-pin headers (underside)", "#424242", lambda n: n.startswith("header ")),
    ("screen socket AXE530127 (daughterboard tab)", "#263238", lambda n: n.startswith("screen FPC socket")),
    ("guide screws + brass sleeves + inserts (up-stop)", "#b0855a", lambda n: n.startswith("guide ")),
    ("joystick daughterboard (1.0 FR4)", "#1b5e20", lambda n: n == "joystick daughterboard"),
    ("v0.7 top board on the vertical boards' spring contacts (1.0 FR4)", "#1b5e20", lambda n: n.startswith("joystick top board")),
    ("v0.7 case cradle (UTR-8100 SLA): lip in the cutout, flange, ball seats", "#80deea", lambda n: n.startswith("joystick case cradle")),
    ("v0.7 cradle gasket (silicone sponge) [A]", "#8a8f94", lambda n: n.startswith("joystick cradle gasket")),
    ("M2 female-female brass standoffs (GND, ×4)", "#c9a227", lambda n: n.startswith("brass standoff")),
    ("M2 socket-head screws", "#f9a825", lambda n: n.startswith("M2 socket screw")),
    ("SKRHADE010 body (45°)", "#b0bec5", lambda n: n.startswith("SW1") and "body" in n),
    ("SKRHADE010 stem", "#fff176", lambda n: n.startswith("SW1") and "stem" in n),
    ("seat plate (glued on the daughterboard)", "#6d4c41", lambda n: n.startswith("seat plate")),
    ("cradle (printed, glued to the PCB) + dowels", "#8d6e63", lambda n: n.startswith(("joystick cradle", "cradle locating"))),
    ("balls Ø2 stainless", "#90a4ae", lambda n: n.startswith("ball ")),
    ("carrier (thin floor, pilots, cup)", "#ab47bc", lambda n: n.startswith("joystick carrier")),
    ("screen carrier: 5 mm grip block", "#5c6bc0", lambda n: n.startswith("screen carrier")),
    ("M2 grub screws + brass inserts", "#8d6e63", lambda n: n.startswith("grub ") or n.startswith("brass insert")),
    ("compression springs (Lee CI 008B)", "#546e7a", lambda n: n.startswith("compression spring")),
    ("top screen 1.64\" AMOLED", "#101828", lambda n: n.startswith("top screen")),
    ("screen FPC [A]", "#ffb300", lambda n: n.startswith(("screen FPC [", "screen jumper FPC"))),
    ("rear spring anchor (glued to PCB back)", "#26a69a", lambda n: n.startswith("rear spring")),
    ("cross pins (two, side entry)", "#455a64", lambda n: n.startswith("cross pin")),
    ("hold-down extension springs", "#fdd835", lambda n: n.startswith("hold-down")),
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
    if D.get("base") == "cradle":   # v0.5 cradle ring (dashed) and corner towers
        ax.add_patch(Rectangle((-D["cr_out_x"], D["cr_out_y0"]), 2 * D["cr_out_x"], D["cr_out_y1"] - D["cr_out_y0"], fill=False, ec="#6d4c41", lw=1.0, ls="--", zorder=3))
        ax.add_patch(Rectangle((-D["cr_in_x"], -D["cr_in_y"]), 2 * D["cr_in_x"], 2 * D["cr_in_y"], fill=False, ec="#6d4c41", lw=0.8, ls=":", zorder=3))
        for x, y in D["balls"]:
            ax.add_patch(Circle((x, y), D["boss_r"], fc="#bcaaa4", ec="#6d4c41", lw=0.6, zorder=3))
    else:
        ax.add_patch(Circle((0, 0), D["cut_r"], fc="white", ec="#4e342e", lw=0.8, zorder=3))
    if D.get("fpc_to_db"):   # v0.5 tab with the screen socket (long side along y)
        ax.add_patch(Rectangle((x1, -D["tab_hy"]), D["tab_x1"] - x1, 2 * D["tab_hy"], fc=lighten("#1b5e20", 0.25), ec="k", lw=1.2, zorder=3))
        sl_, ss_, _ = D["db_fpc_sock"]
        ax.add_patch(Rectangle((D["db_sock_x"] - ss_ / 2, -sl_ / 2), ss_, sl_, fc="#263238", ec="k", lw=0.6, zorder=4))
    else:
        ax.add_patch(Rectangle((D["hole_x0"], -D["hole_hy"]), D["hole_x1"] - D["hole_x0"], 2 * D["hole_hy"], fc="none", ec="#c62828", lw=1.0, ls="--", zorder=3))
    rows = D["hdr"].get("rows", 1)
    for hx, hy in D["hdr_xy"]:
        ax.add_patch(Rectangle((hx - D["hdr_len"] / 2, hy - D["hdr_wid"] / 2), D["hdr_len"], D["hdr_wid"], fc="#424242", ec="k", zorder=4))
        for dx, dy in D["hdr_pins"]:
            ax.add_patch(Circle((hx + dx, hy + dy), 0.32, fc="#ffd54f", ec="k", lw=0.4, zorder=5))
    for x, y in D.get("g_xy", []):   # v0.5 guides: sleeve and head
        ax.add_patch(Circle((x, y), D["guide"]["head_d"] / 2, fc="#cfd8dc", ec="k", lw=0.4, zorder=4))
        ax.add_patch(Circle((x, y), D["guide"]["sleeve_od"] / 2, fc="#c9a227", ec="k", lw=0.6, zorder=5))
    for x, y in D["standoff_xy"]:
        ax.add_patch(Circle((x, y), D["shcs"]["head_d"] / 2, fc="#f9a825", ec="k", lw=0.4, zorder=4))
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
    for x, y in D["cs_xy"]:
        ax.add_patch(Circle((x, y), D["sh_r"], fc="#8d6e63", ec="k", lw=0.4, zorder=5))
        ax.add_patch(Circle((x, y), D["cs"]["od"] / 2, fc="#546e7a", ec="k", lw=0.4, zorder=6))
    for x, y in D["balls"]:
        ax.add_patch(Circle((x, y), D["ball_d"] / 2, fc="#90a4ae", ec="k", zorder=4))
    for x, y in D["springs"]:
        ax.add_patch(Circle((x, y), D["spr_bore"] / 2, fc="white", ec="#4e342e", lw=0.8, zorder=4))
        ax.add_patch(Circle((x, y), D["spr_d"] / 2, fc="#fdd835", ec="k", lw=0.6, zorder=5))
    ax.add_patch(Rectangle((D["fpc_x"] - 0.1, -D["fpc_w"] / 2), 0.2, D["fpc_w"], fc="#ffb300", ec="#ff6f00", zorder=6))
    hw, hh, hm, xn = D["half_w"], D["half_h"], D["h_mid"], D["x_notch"]
    outline = [(-hw, -hh), (-xn, -hh), (-xn, -hm), (xn, -hm), (xn, -hh), (hw, -hh),
               (hw, hh), (xn, hh), (xn, hm), (-xn, hm), (-xn, hh), (-hw, hh)]
    ax.add_patch(Polygon(outline, fill=False, ec="#8e24aa", lw=1.6, ls="--", zorder=8, closed=True))
    S = D["scr"]
    ax.add_patch(Rectangle((-S["w"] / 2, -S["h"] / 2), S["w"], S["h"], fill=False, ec="#101828", lw=1.0, ls="-.", zorder=8))
    L = dict(fontsize=8, zorder=9)
    ax.annotate(f"daughterboard {D['db'][0]:.1f}×{D['db'][1]:.1f}, riser {D['riser_h']:g}", (0, y0), (-hw - 1, y0 - 1),
                arrowprops=dict(arrowstyle="-", lw=0.6), ha="right", **L)
    ax.annotate("SKRHADE010, −45°", (0, 0), (-hw - 1, 3), arrowprops=dict(arrowstyle="-", lw=0.6), ha="right", **L)
    ax.annotate(f"two {rows}×{D['hdr']['n']}" + (f", cradle {D['riser_h']:g} mm" if D.get("base") == "cradle" else f" + four M2×{D['riser_h']:g}"),
                D["hdr_xy"][0], (hw + 1, -4), arrowprops=dict(arrowstyle="-", lw=0.6), ha="left", **L)
    ax.annotate("screen socket on the tab" if D.get("fpc_to_db") else "FPC bend [A]", (D["fpc_x"], D["slot_hy"]), (hw + 1, 6), arrowprops=dict(arrowstyle="-", lw=0.6), ha="left", **L)
    if D.get("g_xy"):
        ax.annotate("guide screw + sleeve (up-stop)", D["g_xy"][0], (-hw - 1, 8), arrowprops=dict(arrowstyle="-", lw=0.6), ha="right", **L)
    ax.annotate("Ø2 ball", D["balls"][0], (D["balls"][0][0] + 6, D["balls"][0][1] + 6), arrowprops=dict(arrowstyle="-", lw=0.6), **L)
    ax.annotate("grub + spring", D["cs_xy"][0], (hw - 4, hh + 2.2), arrowprops=dict(arrowstyle="-", lw=0.6), ha="left", **L)
    bx, by = D["board_xy"]
    ax.text(-hw, hh + 4.6, f"dashed purple = carrier {cw:.1f} × {ch:.1f}, notched to ±{hm:.1f}; dash-dot = screen {S['w']:g} × {S['h']:g}", fontsize=8)
    ax.text(-hw, hh + 3.0, f"blue arc = knob Ø{D['knob_od_design']:.2f} (design) / Ø{D['knob_od_live']:.2f} (live); green = PCB top", fontsize=8)
    ax.text(-hw, -hm - 12, f"centre board ({bx:.2f}, {by:.2f}); screen top z {D['scr_top']:.2f}; finger gap to the knob {D.get('finger_gap', 0):.2f}", fontsize=8)
    ax.plot([4, 14], [-hm - 9.2, -hm - 9.2], color="k", lw=3); ax.text(9, -hm - 8.2, "10 mm", ha="center", fontsize=9)
    ax.set_xlim(-hw - 18, hw + 16); ax.set_ylim(-hm - 16, hh + 7); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])

def _meshes(parts, removed, planes, tol):
    out = {}
    for n, s in parts.items():
        m = _mesh(s, removed, planes, tol)
        if m: out[n] = m
    return out

def _centre_z(D):
    return (0.0, 0.0, D["scr_top"] * 0.55)

def section_preview(D, P, png):
    """Low-resolution section through the +y cross pin (plane y = spr_y), from -y."""
    tmp = tempfile.mkdtemp()
    y = D["spr_y"]
    rem = Pos(0, y - BIG / 2, 0) * Box(BIG, BIG, BIG)
    m = _meshes(P, rem, [((0, y, 0), (0, 1, 0))], tol=0.12)
    zc = 0.5 * (D["scr_top"] + D["z_pin"])
    im = _shot(m, (0, -1, 0), (0, 0, 1), os.path.join(tmp, "s.png"), (1100, 800),
               centre=(0.0, y, zc), scale=30.0)
    fig, ax = plt.subplots(figsize=(11, 8), dpi=70)
    ax.imshow(im); ax.axis("off")
    ax.set_title(f"Top-screen joystick {D['version']} — section through the +y pin (y={y:.2f})", fontsize=12, weight="bold", loc="left")
    fig.tight_layout(); fig.savefig(png); plt.close(fig)

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
    axA.set_title("SECTION A-A (plane y = 0 through the switch, both headers,\ncup, press peg and FPC; viewed from -y)", fontsize=13, weight="bold", loc="left")
    axI.set_title("ISOMETRIC QUARTER CUT (+x and -y removed:\nswitch on axis, header, ball seat, spring pilot)", fontsize=13, weight="bold", loc="left")
    axP.set_title("PLAN (front view, panel up = +y)", fontsize=13, weight="bold", loc="left")
    sw = D["sw"]
    fig.suptitle(f"Top-screen joystick {D['version']} — {D['grip_h']:g} mm grip block on four compression springs and two guides, {D['riser_h']:g} mm riser (2 Nov 2026, Ed)", fontsize=16, weight="bold", x=0.01, ha="left", y=0.985)
    nf = sum(not r["ok"] for r in rows)
    key = (f"Stack (z from the main-PCB front): faceplate front {D['z_fp1']:.2f} = knob top {D['z_knob_top']:.2f} − knob_proud {D['knob_proud']:.1f}. "
           f"Screen top {D['scr_top']:.2f}. "
           + (f"Printed cradle 0–{D['z_db0']:.2f}, glued, two dowels; balls at the corners (±{D['bx']:.1f}, +{D['by_top']:.2f}/−{D['by_bot']:.1f}) · " if D.get("base") == "cradle"
              else f"Derived riser 0–{D['z_db0']:.2f} (catalog {D['standoff']['part']}, {D['standoff']['length']:.0f} mm) · ")
           + f"daughterboard {D['z_db0']:.2f}–{D['z_db1']:.2f} · "
           f"stem top {D['z_stem_top']:.2f} · carrier underside {D['z_c0']:.2f} · floor {D['car_floor']:.2f} · "
           f"bezel {D['z_bz0']:.2f}–{D['z_bz1']:.2f} · spring roof {D['z_roof']:.2f} · screen {D['z_scr0']:.2f}–{D['scr_top']:.2f}.\n"
           f"Tilt stop is the switch: slide {D['slide']:.2f} mm (cup clearance {D['cup_rad_clear']:.2f} + tilt {sw['tilt_travel']:g}). "
           f"Press: {D['cs_f_press']:.2f} N at the switch bottom ({D['cs_turns']:g} turn preload {D['cs_f_preload']:.2f} N, "
           f"{D['cs_f_turn_1']:.3f} N/turn each spring). "
           f"Hold-down: 4 × {D['spr_f']:g} N, length {D['spr_len']:.0f} mm (tips at {D['tip_f_top_y']:.2f} N on the glass top, up/down). "
           f"Guides: {D['guide']['part']} (M2×{D['g_len']:.0f}); heads are the up-stop. "
           f"Finger gap to the knob {D['finger_gap']:.2f} mm.\n"
           f"Checks: {len(rows) - nf}/{len(rows)} PASS. Switch on the carrier axis. Footprint −45°: a/b/c/d → UP/RIGHT/LEFT/DOWN, confirmed at first-power calibration. "
           + ("Screen DO0164FMST02, flex out at -x; custom jumper [A] from its B2B header to the daughterboard socket (B2B family [C])."
              if "win_x" in D else "FPC exit, pitch and pin-out are still open [A]."))
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
        "top screen": 62, "screen carrier": 46, "compression spring": 36, "joystick carrier": 24,
        "grub screw": 16, "brass insert": 16, "ball ": 14,
        "seat plate": 10, "SW1": 10, "joystick daughterboard": 6, "header ": 6,
        "brass standoff": 0, "M2 socket screw bottom": -10, "M2 socket screw top": 12,
        "socket ": 0, "main PCB": 0, "screen FPC": 8,
        "hold-down": -6, "rear spring": -14, "cross pin": -14,
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
