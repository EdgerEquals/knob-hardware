# v0.25 dial job (3 Nov 2026, [Ed 18:12 / 18:15 / 18:26 / 19:12 / 19:46]): the dial split at the top of its tube, the detent
# block, the cap split (PA-12 hub in the clear cap) and the cartridge's sideways magnets + key ribs, cut from the real parts.
# Panel frame (+x right, +y up the panel, z out of the panel, dial axis at the origin); the mechanism frame is the panel turned
# +90° (mech_rot -90): a mechanism angle a is the panel angle a - 90.
# Run from cad/knob-param:
#   PYTHONPATH=. python tools/studies/dial_v025_fig.py sections <out.png>
#   PYTHONPATH=. xvfb-run -a python tools/studies/dial_v025_fig.py quarter <out.png>
#   PYTHONPATH=. xvfb-run -a python tools/studies/dial_v025_fig.py block <out.png>
import math, sys, textwrap
sys.path.insert(0, ".")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
from build123d import Rot, Pos, Box, Align
from knobparam.assembly.plan_sheet import cut, draw


def load(zmin=-2.0):
    from knobparam.common import model
    from knobparam.assembly.build import build_all, view
    D = model.derive(model.default_params())
    parts, stats, keys, owner = build_all(D, only=["control_dial", "electronics", "main_knob", "base_drive"])
    parts, keys = view(parts, keys, D, "panel")
    P = {}
    for n, s in parts.items():
        b = s.bounding_box()
        if b.max.Z > zmin and max(abs(b.min.X), abs(b.max.X), abs(b.min.Y), abs(b.max.Y)) < 26 and n != "PCB":
            P[n] = s
    return D, P


def ann(ax, txt, xy, xyt, fs=7.4, **kw):
    ax.annotate(txt, xy, xyt, fontsize=fs, arrowprops=dict(arrowstyle="-", lw=0.6, color="#b00000"), color="0.05",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.88), **kw)


def radial(P, a):
    """Parts turned so the radial plane at panel angle a lies on y = 0, x > 0 (cut with axis 'y')."""
    return {n: Rot(0, 0, -a) * s for n, s in P.items()}


def sections(out):
    D, P = load()
    bz, ct = D["bz"], D["ct"]; mr = D["mech_rot"]
    W = lambda t, n=95: textwrap.fill(t, n)
    fig = plt.figure(figsize=(26, 24), dpi=100)
    gs = fig.add_gridspec(3, 3, width_ratios=[1.9, 1.0, 1.0], hspace=0.16, wspace=0.10)
    legend = {}
    # ---- A: y = 0, the whole knob height: key rib (180°) on the left, the detent block's plane (mech 270°) below it ----
    ax = fig.add_subplot(gs[:, 0])
    legend.update(draw(ax, cut(P, "y", 0.0), W("A: y = 0 through the axis (left = panel 180°: the key rib, and mechanism 270°: the "
                       "detent block, 7° off its boss; right = panel 0°). Dial: lower part + bonded dish; cap: PA-12 hub + clear part", 70),
                       (-22.5, 22.5), (-2.0, 62.5), xlabel="x (mm)", ylabel="z (mm, main-PCB front = 0)"))
    ann(ax, f"dial lower part (tube, spokes, lever),\nin first; tube end z {D['dsp_z1']:.2f}", (-3.3, 30.0), (-21.5, 33.0))
    ann(ax, f"dish bonded on last: socket over the tube,\n{D['dsp_engage']:.2f} engaged, split at z {D['dsp_z0']:.2f}", (-6.0, 47.6), (-21.5, 41.5))
    ann(ax, "cap: PA-12 hub (teeth, 45° race)\nkeyed + glued in the clear part [Ed 19:46]", (-8.0, 45.0), (3.0, 35.0))
    ann(ax, f"key rib (180°) in its slot,\nbottom = the seat z {D['rib_z0']:.2f}", (-19.0, 54.5), (-21.5, 58.5))
    ann(ax, "detent block (UTR-8100)\non its glued seat", (-16.0, 9.0), (-21.5, 17.0))
    ann(ax, "base cradle", (-10.0, 1.5), (-21.5, -1.2))
    # ---- B: the split joint and the cap joint, radial plane through the key flat ----
    af = D["dsp_flat_ang"] + mr
    ax = fig.add_subplot(gs[0, 1])
    legend.update(draw(ax, cut(radial(P, af), "y", 0.0), W(f"B: the joints, radial plane at panel {af % 360:.0f}° (the tube's key flat)"),
                       (0.0, 13.0), (38.5, 51.5), xlabel=f"r along {af % 360:.0f}° (mm)", ylabel="z (mm)"))
    ann(ax, f"tube Ø{D['dial_tube_od']:.2f}/Ø{D['dial_tube_id']:.2f}, flat {D['dsp']['flat']:g} deep\n(wall {D['dsp_tube_wall_flat']:.2f} at the flat)",
        (D["dsp_flat_d"] - 0.3, 47.5), (0.3, 50.6))
    ann(ax, f"dish socket Ø{2 * D['dsp_r_sock']:.2f} (bond {D['dsp']['glue']:g}),\nwall {D['dsp_dish_wall']:.2f} to the hub OD", (5.5, 47.2), (6.6, 50.6))
    ann(ax, f"cap bore Ø{2 * D['r_knob_bore']:.2f} over the tube\n({D['r_knob_bore'] - D['dial_tube_od'] / 2:.2f} a side)", (4.2, 42.0), (0.3, 39.2))
    ann(ax, f"PA-12 hub: teeth z {D['knob_hub_z0']:.1f}-{D['h_band1']:.1f}, race\n+ groove; rim on the clear ledge z {D['cs_z_step']:.2f}",
        (7.0, 44.6), (5.2, 39.2))
    ann(ax, f"clear UTR-8100 part (web, plug, seat)", (12.0, 46.5), (8.0, 42.7))
    ann(ax, "race ball Ø1", (D["kb_rc"], D["kb_zc"]), (9.8, 48.6))
    # ---- C: a magnet pair (30°) ----
    a = bz["mag_angs"][0]; ax = fig.add_subplot(gs[0, 2])
    legend.update(draw(ax, cut(radial(P, a), "y", 0.0), W(f"C: magnet pair at {a:g}° (pairs at " + ", ".join(f"{x:g}" for x in bz["mag_angs"]) + "°)"),
                       (15.0, 22.0), (51.5, 61.5), xlabel=f"r along {a:g}° (mm)", ylabel="z (mm)"))
    (rd, zd), (rs, zs) = D["cart_mags"][0][1], D["cart_mags"][0][2]
    fr, fz = D["cm_F_pair"]
    ann(ax, f"dial-wall magnet Ø{bz['mag'][0]:g}x{bz['mag'][1]:g} N52, facing out;\nwall {D['cm_skin_dial']:.2f} over / under it", (rd, zd), (15.2, 52.2))
    ann(ax, f"bezel magnet {bz['mag_dz']:+g} above it, facing in,\nattracting: {-fz:.3f} N down + {-fr:.3f} N in a pair", (rs, zs), (15.2, 57.6))
    ann(ax, f"skirt skin {D['cm_skin_out']:.2f} (TIGHT: PCBWay MJF wall 1.0)", (20.8, zs), (17.0, 60.8))
    ann(ax, f"gap {D['cm_gap']:.2f}", (19.35, 53.4), (20.3, 52.2))
    # ---- D: the key rib (180°) ----
    a = bz["rib_angs"][0]; ax = fig.add_subplot(gs[1, 1])
    legend.update(draw(ax, cut(radial(P, a), "y", 0.0), W(f"D: the key rib at {a:g}° (seat ribs at " + ", ".join(f"{x:g}" for x in bz["rib_angs"][1:]) + "°)"),
                       (15.0, 22.0), (51.5, 61.5), xlabel=f"r along {a:g}° (mm)", ylabel="z (mm)"))
    ann(ax, f"rib r {bz['rib_r_in']:g}-{D['bz_bore_r']:g}, {bz['rib_w']:g} wide, up to the glass seat;\nnothing inside r 18.5 below the glass",
        (bz["rib_r_in"] + 0.1, 57.5), (15.2, 60.6))
    ann(ax, f"slot from r {D['rib_slot_r0']:g}, {bz['slot_depth']:g} deep; rib bottom on its floor\n= the axial seat z {D['rib_z0']:.2f} [Ed 19:12]",
        (18.9, D["rib_z0"]), (15.2, 52.2))
    ann(ax, f"dial board top {D['db_z1']:.2f}", (16.0, D["db_z1"] - 0.2), (15.2, 57.2))
    # ---- E: the detent block, radial plane through the boss (mech sp_ang) ----
    a = D["sp_ang"] + mr; ax = fig.add_subplot(gs[1, 2])
    legend.update(draw(ax, cut(radial(P, a), "y", 0.0), W(f"E: detent block, radial plane through the boss (mechanism {D['sp_ang']:g}° = panel {a % 360:.0f}°)"),
                       (8.0, 19.0), (-1.8, 14.5), xlabel=f"r along mech {D['sp_ang']:g}° (mm)", ylabel="z (mm)"))
    r0, r1, a0, a1 = D["dt_seat"]
    ann(ax, f"block: head ±{D['dt_head_half']:g}° from the boss to the wall,\nfoot r {r0:.2f}-{r1:.3f} = the cradle OD", (15.9, 11.5), (8.2, 14.0))
    ann(ax, f"glued flat seat z {D['plate_t']:g}\n({D['dt_seat_area']:.1f} mm²)", (15.9, D["plate_t"]), (16.6, 1.2))
    ann(ax, f"ball Ø{D['det_ball']:g}, spring, M2 grub\nin the bore (grease holds the ball)", (13.5, 9.0), (8.2, 10.6))
    ann(ax, "flange on the train,\npedestal on its grub", (12.8, 6.3), (8.2, 3.0))
    ann(ax, "knob ring (turns)", (17.6, 7.0), (16.3, -1.2))
    # ---- F: plan at the magnet level ----
    z = zd + 0.2; ax = fig.add_subplot(gs[2, 1])
    legend.update(draw(ax, cut(P, "z", z), W(f"F: plan z {z:.2f}: the three magnet pairs, the key and the seat ribs in their slots"),
                       (-22.5, 22.5), (-22.5, 22.5)))
    for a_, (rd_, _), (rs_, _) in D["cart_mags"]:
        x, y = rd_ * math.cos(math.radians(a_)), rd_ * math.sin(math.radians(a_))
        ann(ax, f"pair {a_:g}°", (x, y), (x * 0.62, y * 0.62))
    for a_, cl, k in D["cart_ribs"]:
        x, y = 18.9 * math.cos(math.radians(a_)), 18.9 * math.sin(math.radians(a_))
        ann(ax, f"{'key' if k == 'key' else 'seat rib'} {a_:g}° ({cl:g} a side)", (x, y), (x * 0.55, y * 0.55 - 1.5))
    # ---- G: plan just over the block's seat ----
    z = D["plate_t"] + 0.3; ax = fig.add_subplot(gs[2, 2])
    Pm = {n: Rot(0, 0, -mr) * s for n, s in P.items()}   # mechanism frame for this one
    legend.update(draw(ax, cut(Pm, "z", z), W(f"G: plan z {z:.1f} (mechanism frame, motor at +x): the block's foot, its two pins, the pedestal", 70), (-9.0, 6.0), (-19.0, -9.0)))
    for k, (x, y) in enumerate(D["dt_pin_xy"], 1):
        ann(ax, f"Ø{D['dt_pin'][0]:g} pin {k} ({D['dt_pin_angs'][k - 1]:g}°)", (x, y), (x - 2.5, y + 3.2))
    ann(ax, f"foot r {r0:.2f}-{r1:.3f}: {r1 - r0:.3f} wide\n(an M2 from behind needs {D['dt_screw_need']['M2']:.1f}, M1.6 {D['dt_screw_need']['M1.6']:.2f})",
        (-1.0, -15.9), (-8.8, -10.2))
    fig.subplots_adjust(top=0.95)
    fig.text(0.01, 0.985, "v0.25 dial: split dial (lower part + bonded dish), detent block, cap split (PA-12 hub in a clear cap), cartridge "
             "magnets sideways + key ribs", fontsize=16, weight="bold")
    fig.text(0.01, 0.972, "Panel frame, cut from the real parts (mechanism angle = panel + 90°). [Ed 18:12/18:15/18:26/19:12/19:46] Danny's, "
             "[A] assumed. Doc: docs/layout-v4-2026-11-03.md, 'v0.25: dial split, detent block, cartridge'.", fontsize=10)
    hs = [Patch(fc=c, ec="k", lw=0.3, label=l) for l, c in sorted(legend.items())]
    fig.legend(handles=hs, loc="lower center", ncol=5, fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.06))
    fig.savefig(out, bbox_inches="tight"); print("wrote", out)


def _mesh(pl, n, q, col, see_through, op_clear=0.38):
    import numpy as np, pyvista as pv
    V, T = q.tessellate(0.02, 0.3)
    if not T:
        return
    pts = np.array([(v.X, v.Y, v.Z) for v in V]); tri = np.hstack([np.full((len(T), 1), 3), np.array(T)]).ravel()
    m = pv.PolyData(pts, tri); clear = see_through(n)
    pl.add_mesh(m, color=col(n), opacity=op_clear if clear else 1.0, smooth_shading=False, specular=0.15, ambient=0.35, diffuse=0.75)
    fe = m.extract_feature_edges(35)
    if fe.n_points:
        pl.add_mesh(fe, color="#202020" if not clear else "#5a7f8c", line_width=1.0, opacity=0.6 if clear else 1.0)


def quarter(out):
    import numpy as np, pyvista as pv
    from knobparam.assembly.colours import colour as col, see_through
    D, P = load(zmin=36.0)
    bz = D["bz"]
    from knobparam.control_dial.parts.dial import wedge
    region = Pos(-26, -26, 38.0) * Box(52, 52, 25.0, align=(Align.MIN, Align.MIN, Align.MIN))
    # wedge removed between panel 180° and 240°: the key rib (180°) and the 240° magnet pair lie on the two cut faces
    quad = wedge(180.0, 240.0, 30.0, 40.0, 40.0)
    pl = pv.Plotter(off_screen=True, window_size=(1900, 1450)); pl.set_background("white")
    for n, s in P.items():
        try:
            q = (s & region) - quad
        except Exception:
            continue
        if q is None or not q.solids():
            continue
        _mesh(pl, n, q, col, see_through)
    pol = lambda r, a, z: (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), z)
    (rd, zd), (rs, zs) = D["cart_mags"][2][1], D["cart_mags"][2][2]
    A2 = 240.0
    L = [(pol(6.0, A2, D["z_top"]), "lens (top 61.2)"), ((-20.5, 0.0, 57.5), "bezel"),
         ((-18.9, 0.0, D["rib_z0"] + 1.0), "key rib (180°) in its slot: the seat"), (pol(rd - 0.2, A2, zd), "dial-wall magnet (240°)"),
         (pol(rs + 0.3, A2, zs), "bezel magnet, 0.4 higher"), ((-12.0, 0.0, D["db_z1"] + 0.4), "dial board"),
         (pol(9.0, A2, 51.0), "dial dish (bonded on)"), (pol(3.3, A2, 44.0), "dial tube (lower part)"),
         (pol(6.2, A2, 41.5), "PA-12 hub: hub-gear teeth"), (pol(D["kb_rc"], A2, D["kb_zc"]), "race balls on the PA-12 hub"),
         (pol(14.0, A2, 47.6), "clear cap (UTR-8100)"), (pol(11.2, A2, D["cs_z_step"]), "hub rim on the clear ledge (keyed, glued)"),
         (pol(4.6, A2, 47.8), "dish socket over the tube end"), ((-20.6, 0.0, 45.0), "knob glass")]
    pl.add_point_labels(np.array([p for p, _ in L]), [t for _, t in L], font_size=16, point_size=6, point_color="#c00000",
                        shape_color="#f2f2f2", shape_opacity=0.85, always_visible=True)
    pl.add_text("v0.25 knob top: 60° wedge cut out (panel 180-240°), panel frame, z out of the panel. Dial = lower part + bonded dish;\n"
                "cap = PA-12 hub keyed into the clear UTR-8100 part; sideways magnet pairs; key + seat ribs. Clear parts at 38 %.",
                font_size=12, color="black")
    pl.camera_position = [(-100 * math.cos(math.radians(30)), -100 * math.sin(math.radians(30)), 112), (-2.0, -1.0, 49.0), (0, 0, 1)]
    pl.camera.zoom(1.3)
    pl.screenshot(out); print("wrote", out)


def block(out):
    """The detent block, its glued seat and two pins; no screw from behind (the foot is too narrow): matplotlib cuts + a 3D view."""
    import numpy as np, pyvista as pv
    from knobparam.assembly.colours import colour as col, see_through
    D, P = load()
    mr = D["mech_rot"]
    Pm = {n: Rot(0, 0, -mr) * s for n, s in P.items()}   # mechanism frame
    # 3D: the block lifted 6 mm over its seat (exploded), the cradle, the pedestal + train, the dial's lower part, the pins
    keep = ("base cradle", "detent", "track ", "control dial lower part", "spring anchor", "centring spring")
    from knobparam.common.util import sector
    reg = sector(5.5, 17.4, 32.0, -0.5, 15.0, D["sp_ang"])   # a sector round the block, the knob ring left out
    pl = pv.Plotter(off_screen=True, window_size=(1700, 1400)); pl.set_background("white")
    for n, s in Pm.items():
        if not n.startswith(keep):
            continue
        q = s & reg
        if q is None or not q.solids():
            continue
        if n.startswith("detent block (") or n.startswith("detent 1"):
            q = Pos(0, 0, 5.0) * q
        _mesh(pl, n, q, col, see_through, op_clear=0.5)
    x, y = D["det_xy"][0]
    L = [((x, y, D["det_z1"] + 5.2), "detent block (UTR-8100), lifted 5 mm"), ((x, y, D["det_z0"] + 4.6), "ball in the bore (grease)"),
         (tuple(list(D["dt_pin_xy"][0]) + [D["plate_t"] + 1.5]), "Ø1 pin 1"), (tuple(list(D["dt_pin_xy"][1]) + [D["plate_t"] + 1.5]), "Ø1 pin 2"),
         ((x, y, D["ad_z_land"]), "flange (dial lower part)"), ((x * 0.92, y * 0.92, D["plate_t"] - 0.2), "glued seat on the plate top"),
         ((0.0, -8.0, 9.0), "anchor post 2 (floating in the cradle model)")]
    pl.add_point_labels(np.array([p for p, _ in L]), [t for _, t in L], font_size=30, point_size=8, point_color="#c00000",
                        shape_color="#f2f2f2", shape_opacity=0.85, always_visible=True)
    ua = math.radians(D["sp_ang"] - 25.0)
    pl.camera_position = [(x + 34 * math.cos(ua), y + 34 * math.sin(ua), 34.0), (x * 0.9, y * 0.9, 7.0), (0, 0, 1)]
    pl.camera.zoom(0.85)
    img = pl.screenshot(None, return_img=True)
    fig = plt.figure(figsize=(24, 10.5), dpi=100)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.35, 1.0, 1.0], wspace=0.10)
    ax = fig.add_subplot(gs[0, 0]); ax.imshow(img); ax.axis("off")
    ax.set_title("1. The block lifted 5 mm off its seat (seen from outside, above), the two pins, the pedestal + train, the dial's flange",
                 fontsize=9, loc="left")
    legend = {}
    # 2: radial cut through pin 2, showing the pin in the plate and the foot
    a = D["dt_pin_angs"][1]; ax = fig.add_subplot(gs[0, 1])
    Pr = {n: Rot(0, 0, -a) * s for n, s in Pm.items()}
    legend.update(draw(ax, cut(Pr, "y", 0.0), f"2. Radial cut through pin 2 (mech {a:g}°): pin pressed in the plate, the foot over it",
                       (11.0, 19.0), (-1.8, 14.5), xlabel=f"r along mech {a:g}° (mm)", ylabel="z (mm)"))
    r0, r1, a0, a1 = D["dt_seat"]; p = D["dt_lift_parts"]
    ann(ax, f"foot r {r0:.2f}-{r1:.3f} ({r1 - r0:.3f} wide), flush with the cradle OD\n(v0.24 wall 16.89 stood 0.035 past it)", (16.4, 6.0), (11.2, 13.6))
    ann(ax, f"Ø{D['dt_pin'][0]:g} pin, {D['dt_pin'][1]:g} in the plate, {D['dt_pin'][2]:g} in the foot;\nfoot wall {D['dt_pin_wall']:.2f} round its hole",
        ((r0 + r1) / 2, D["plate_t"] + 0.6), (11.2, 1.0))
    ann(ax, f"epoxy seat z {D['plate_t']:g}, {D['dt_seat_area']:.1f} mm²,\npeak {D['dt_bond_sigma']:.2f} MPa under the spring", (r1 - 0.2, D["plate_t"]), (16.6, -1.3))
    # 3: plan at the PCB back with the would-be screw (why no screw)
    ax = fig.add_subplot(gs[0, 2])
    z = D["plate_t"] + 0.3
    legend.update(draw(ax, cut(Pm, "z", z), f"3. Plan z {z:.1f} (mechanism frame): the foot vs a screw from behind", (-8.5, 5.5), (-18.5, -10.0)))
    rm = (r0 + r1) / 2
    for nm, dd, cc in (("M2 tap Ø1.6 + 2 x 0.8 SLA wall", 3.2, "#d62728"), ("M1.6 tap Ø1.25 + 2 x 0.8", 2.85, "#ff7f0e")):
        xx, yy = rm * math.cos(math.radians(263.0)), rm * math.sin(math.radians(263.0))
        ax.add_patch(plt.Circle((xx, yy), dd / 2, fill=False, ec=cc, lw=1.4, ls="--"))
        ax.annotate(nm, (xx + dd / 2 * 0.7, yy + dd / 2 * 0.7), (-8.2, -12.3 if dd > 3 else -13.0), color=cc, fontsize=8,
                    arrowprops=dict(arrowstyle="-", lw=0.6, color=cc))
    ann(ax, f"foot {r1 - r0:.3f} wide between the flange's sweep (r {r0 - D['sp_wall_gap']:.2f} + {D['sp_wall_gap']:g})\nand the cradle OD; the knob ring's "
            f"tips {D['skirt_id'] / 2 - r1:.2f} outside it", (rm * math.cos(math.radians(270)), rm * math.sin(math.radians(270))), (-8.2, -10.9))
    fig.text(0.01, 0.98, "v0.25 detent block [Ed 18:15]: separate UTR-8100 block (wall, head, boss with ball, spring, grub), glued on its flat seat on two "
             "Ø1 pins (Danny's fallback): the screw from behind does not fit the foot", fontsize=13, weight="bold")
    fig.text(0.01, 0.955, f"Boss lift under the {D['det_force_max']:.2f} N spring: {D['dt_lift'] * 1e3:.1f} µm (target 10): wall {p['wall'] * 1e3:.1f}, "
             f"head {p['head'] * 1e3:.2f}, bond {p['bond'] * 1e3:.2f}, plate + PCB under the seat {p['plate'] * 1e3:.1f} (conservative). "
             f"One-piece v0.24 formula at this wall: {D['sp_lift'] * 1e3:.1f} µm.", fontsize=10)
    hs = [Patch(fc=c, ec="k", lw=0.3, label=l) for l, c in sorted(legend.items())]
    fig.legend(handles=hs, loc="lower center", ncol=5, fontsize=8, frameon=False, bbox_to_anchor=(0.6, -0.02))
    fig.savefig(out, bbox_inches="tight"); print("wrote", out)


if __name__ == "__main__":
    kind, out = sys.argv[1], sys.argv[2]
    {"sections": sections, "quarter": quarter, "block": block}[kind](out)
