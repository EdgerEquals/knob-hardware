# Dial cartridge in the model (v0.24 work, 3 Nov 2026): straight-on sections and 3D quarter cut-aways of the knob top, cut from the
# real parts (panel frame: +x right, +y up the panel, z out of the panel, dial axis at the origin).
# Run from cad/knob-param:
#   PYTHONPATH=. python tools/studies/dial_cart_fig.py sections <out.png>
#   PYTHONPATH=. xvfb-run -a python tools/studies/dial_cart_fig.py quarter <out.png> [axis|plug]
import math, sys, textwrap
sys.path.insert(0, ".")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from build123d import Rot, Pos, Box, Align
from knobparam.assembly.plan_sheet import cut, draw, colour


def load():
    from knobparam.common import model
    from knobparam.assembly.build import build_all, view
    D = model.derive(model.default_params())
    parts, stats, keys, owner = build_all(D, only=["control_dial", "electronics", "main_knob", "base_drive"])
    parts, keys = view(parts, keys, D, "panel")
    top = {}
    for n, s in parts.items():   # the knob top only
        b = s.bounding_box()
        if b.max.Z > 43.0 and max(abs(b.min.X), abs(b.max.X), abs(b.min.Y), abs(b.max.Y)) < 26 and n != "PCB":
            top[n] = s
    return D, top


def ann(ax, txt, xy, xyt, **kw):
    ax.annotate(txt, xy, xyt, fontsize=7.6, arrowprops=dict(arrowstyle="-", lw=0.6, color="#b00000"), color="0.05",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85), **kw)


def sections(out):
    D, P = load()
    zp, db, ct, bz = D["zp"], D["db"], D["ct"], D["bz"]
    zl = (44.0, 62.6); hl = (-22.5, 22.5)
    fig = plt.figure(figsize=(25, 21), dpi=110)
    gs = fig.add_gridspec(3, 2, width_ratios=[2.45, 1.0], hspace=0.20, wspace=0.08)
    legend = {}
    W = lambda t: textwrap.fill(t, 120)
    # ---- A: y = -9.55, along the tail and through the plug and receptacle centre ----
    ty = sum(zp["tail_y"]) / 2; ax = fig.add_subplot(gs[0, 0]); yA = db["rec"][1]
    legend.update(draw(ax, cut(P, "y", yA), W(f"A: y = {yA:g} (along the panel's tail: U-turn, lower leg, plug on its printed pad, receptacle on "
                       "the dial board); viewed from below the panel"), hl, zl, xlabel="x (mm)", ylabel="z (mm, main-PCB front = 0)"))
    zc = (D["lcm_z0"] + D["leg_z0"]) / 2
    ann(ax, f"tail U-turn: outer x {zp['uturn_x']:g} [S]\n(corner r {D['cart_reach']['U-turn corner']:.2f}): {D['bz_bore_clear']:.2f} to the bore",
        (zp["uturn_x"], zc), (-21.8, 46.2))
    ann(ax, f"lower leg {zp['leg_back']:g} behind the lens back\n(z {D['leg_z0']:.2f}), {D['leg_z0'] - D['db_z1']:.2f} over the board", (-6, D["leg_z0"] + 0.05), (-12.5, 52.2))
    ann(ax, f"24-pin 0.4 plug on the receptacle (mated {zp['mated']:g} [S]);\nmating face z {D['plug_face_z']:.2f}, {D['plug_engage']:.2f} inside it",
        (D["plug_xy"][0], D["rec_z1"] + 0.1), (1.5, 47.0))
    ann(ax, f"printed plug pad z {D['pad_z'][0]:.1f}-{D['pad_z'][1]:.1f}\n(glued to its arm with the cartridge seated)", (D["plug_xy"][0], 57.6), (3.5, 61.6))
    ann(ax, f"dial board {db['t']:g}, top {D['db_z1']:.2f}\n(Waveshare's {db['behind']:g} behind the lens back)", (-3, D["db_z0"] + 0.4), (-8.5, 49.3))
    ann(ax, f"lens Ø{zp['lens_d']:.2f} x {zp['lens_t']:.2f} [S], top {D['z_top']:.1f} (+4.4)", (-4, D["z_top"] - 0.4), (-19.5, 61.9))
    ann(ax, f"bezel: OD {D['knob_od']:g}, bore Ø{bz['bore_d']:g}\n(wall {D['bz_wall']:.1f}), underside {D['z_lip0']:.1f}", (-20.3, 55.0), (-21.8, 49.6))
    ann(ax, f"main knob unchanged\n(glass top {D['z_knob_top']:.1f}, {D['z_lip0'] - D['z_knob_top']:.1f} under the bezel)", (20.0, D["z_knob_top"] - 0.3), (13.0, 44.6))
    ann(ax, f"pocket floor on a {ct['wall']:g} wall over the 30° cone", (12.0, 52.6), (12.5, 50.2))
    # ---- B: x = 0 ----
    ax = fig.add_subplot(gs[1, 0])
    legend.update(draw(ax, cut(P, "x", 0.0), W("B: x = 0 (through the axis, up the panel: strap loop over the nut, ESP32 under the board, "
                       "bottom COF bend at -y, top tab and the Ø1 pin at +y)"), hl, zl, xlabel="y (mm, up the panel)", ylabel="z (mm)"))
    ann(ax, f"strap loop: {D['ls']['lines']} lines, PI ribbon on edge\nfrom (0, {D['ls']['a'][1]:g}) to (0, {D['ls']['b'][1]:g}); "
            f"{D['ls_run_z'][0] - D['z_rod_top']:.1f} over the nut", (-1.0, D["ls_run_z"][1] - 0.3), (-15.0, 49.6))
    ann(ax, f"rod-link board Ø{D['adapter_d']:g} at {D['z_floor']:.1f}-{D['z_board_top']:.1f},\nnut on top (dial up-stop {D['dial_lift']:.1f})",
        (-5.0, D["z_floor"] + 0.5), (-21.5, 45.0))
    pe = db["parts"][0]
    ann(ax, f"ESP32-S3-PICO-1-N8R8 {pe[3]:g} x {pe[4]:g} x {pe[5]:g} [S]\nunder the board", (pe[2], D["db_z0"] - 0.5), (4.5, 48.5))
    ann(ax, f"bottom COF bend to r {zp['bend_r']:g} [S],\n{zp['bend_top']:g} under the glass seat [A]", (-18.6, 59.3), (-21.9, 61.6))
    ann(ax, f"Ø{bz['pin'][0]:g} pin at 90°: land -> boss", (bz["mag_r"], D["db_z1"] + 0.5), (8.0, 61.6))
    ann(ax, f"LED site (270°)", (-db["led"][0], D["db_z0"] - 0.5), (-16.5, 52.5))
    ann(ax, f"ledge {D['db_z0']:.1f} (board rim {D['db_on_ledge']:.1f} on it),\nland {D['db_z1']:.1f}, dial r {ct['outer_r']:g}", (16.8, D["db_z0"]),
        (13.0, 50.6))
    # ---- C: the radial plane at the plug pad's arm (305°) ----
    a = bz["arm_ang"]; ax = fig.add_subplot(gs[2, 0])
    Pc = {n: Rot(0, 0, 90.0 - a) * s for n, s in P.items()}   # the 305° ray turned onto +y
    legend.update(draw(ax, cut(Pc, "x", 0.0), W(f"C: the radial plane through the axis at {a:g}° (right) / {a - 180:g}° (left): the pad's arm to "
                       f"the bezel, the plug and receptacle, the board's lobe in the land cut"), hl, zl,
                       xlabel=f"r along {a:g}° (mm)", ylabel="z (mm)"))
    ann(ax, f"pad arm at {a:g}° glued to the bezel\n(glue line {bz['arm_glue']:g}; arm {bz['arm_w']:g} x {bz['arm_t']:g} [A])", (17.0, D["pad_z"][1] - 0.5), (13.5, 61.7))
    ann(ax, f"board lobe to r {db['lobe'][2]:g} ({db['lobe'][0]:g}-{db['lobe'][1]:g}°)\nin the land cut to the ledge", (17.5, D["db_z0"] + 0.4), (12.6, 50.0))
    ann(ax, "receptacle (faces up)\nand plug", (12.2, D["rec_z1"] - 0.2), (2.0, 48.0))
    # ---- plans ----
    xl = (-22.5, 22.5)
    for row, (z, ttl) in enumerate([(D["db_z0"] + 0.4, "board, lobe, land with its cut, magnets and pins"),
                                    ((D["bz_boss_z"][0] + D["pad_z"][0]) / 2 + 0.5, "cartridge: bosses with magnets / pins, plug pad and arm, tail's lower leg"),
                                    (D["db_z0"] - 0.45, "under the board: ESP32, LDO, PHY, 405 nm diode, LEDs; strap")]):
        ax = fig.add_subplot(gs[row, 1])
        legend.update(draw(ax, cut(P, "z", z), W(f"plan z {z:.2f}: {ttl}")[:400], xl, xl))
        if row == 0:
            for k, a_, d, (x, y) in D["cart_holes"]:
                t = (f"Ø{bz['mag'][0]:g}x{bz['mag'][1]:g} pair {a_:g}°" if k == "magnet" else f"Ø{bz['pin'][0]:g} pin {a_:g}°")
                ann(ax, t, (x, y), (x * 0.62, y * 0.62))
            ann(ax, f"lobe to r {db['lobe'][2]:g}\n(land cut to the ledge)", (14.0, -10.5), (2.0, -4.0))
            ann(ax, f"board Ø{db['d']:g} [A]", (-12.0, 0.0), (-9.0, -5.0))
        if row == 1:
            ann(ax, f"pad + arm at {bz['arm_ang']:g}°", (9.0, -9.5), (-2.0, -3.0))
            ann(ax, "U-turn", (zp["uturn_x"], -9.5), (-12.0, -3.0))
        if row == 2:
            spots = {"ESP32-S3-PICO-1-N8R8": (-4.0, 18.6), "LDO 3.3 V": (9.0, 15.0), "rod-link PHY": (-19.0, 14.5)}
            for nm, x, y, w_, l_, h_ in db["parts"]:
                ann(ax, nm, (x, y), spots.get(nm, (x, y - 6)))
            ann(ax, "405 nm diode", tuple(db["diode"][:2]), (-14.0, -6.0))
            ann(ax, "strap foot (0, 4)", (0.0, 4.0), (3.0, 0.0))
    fig.subplots_adjust(top=0.945)
    fig.text(0.01, 0.985, f"Dial screen as a drop-in bezel cartridge in the model (knob {D['version']} + job 1 = v0.24): Waveshare Z132A2441, "
             f"lens top {D['z_top']:.1f} (+4.4), faceplate stays at {D['faceplate_z']:.1f}", fontsize=15, weight="bold")
    fig.text(0.01, 0.970, "Panel frame, cut from the real parts. [S] Waveshare STEP/drawing numbers, [A] assumed, [Ed] Danny's. "
             "Concept: docs/img/dial-concept-2-cartridge.png", fontsize=10)
    hs = [Patch(fc=c, ec="k", lw=0.3, label=l) for l, c in sorted(legend.items())]
    fig.legend(handles=hs, loc="lower center", ncol=5, fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.045))
    fig.savefig(out, bbox_inches="tight")
    print("wrote", out)


def quarter(out, which="axis"):
    import numpy as np, pyvista as pv
    from knobparam.assembly.colours import colour as col, see_through
    D, P = load()
    zp, db, bz = D["zp"], D["db"], D["bz"]
    from knobparam.control_dial.parts.dial import wedge
    region = Pos(-26, -26, 45.0) * Box(52, 52, 18.0, align=(Align.MIN, Align.MIN, Align.MIN))
    if which == "axis":
        quad = Pos(0, -40, 40) * Box(40, 40, 30, align=(Align.MIN, Align.MIN, Align.MIN))
    else:   # quarter between the plug's radial plane (through the receptacle centre) and 90° before it
        a1 = math.degrees(math.atan2(db["rec"][1], db["rec"][0])) % 360; a0 = a1 - 90.0
        quad = wedge(a0, a1, 40.0, 30.0, 45.0)
    pl = pv.Plotter(off_screen=True, window_size=(1800, 1350)); pl.set_background("white")
    for n, s in P.items():
        if n.startswith(("rod sleeve", "rod M1.6")) and which == "plug":
            continue
        try:
            q = (s & region) - quad
        except Exception:
            continue
        if q is None or not q.solids():
            continue
        V, T = q.tessellate(0.02, 0.3)
        if not T:
            continue
        pts = np.array([(v.X, v.Y, v.Z) for v in V]); tri = np.hstack([np.full((len(T), 1), 3), np.array(T)]).ravel()
        m = pv.PolyData(pts, tri)
        clear = see_through(n)
        pl.add_mesh(m, color=col(n), opacity=0.4 if clear else 1.0, smooth_shading=False, specular=0.15,
                    ambient=0.35, diffuse=0.75, show_edges=False)
        fe = m.extract_feature_edges(35)
        if fe.n_points:
            pl.add_mesh(fe, color="#202020" if not clear else "#5a7f8c", line_width=1.0, opacity=0.6 if clear else 1.0)
    L = []
    pol = lambda r, a, z: (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), z)
    if which == "axis":
        L = [((0, -6, D["z_top"]), "lens Ø36.40, top 61.2 (+4.4)"), ((0, -19.8, 57.0), "bezel (OD 42, bore Ø39)"),
             ((0, -18.6, 59.2), "bottom COF bend"), ((0, -12, D["lcm_z0"] + 0.4), "panel (AMOLED)"),
             ((0, -9.6, D["leg_z0"] + 0.05), "tail, lower leg"), ((-14.5, -9.6, 57.6), "tail U-turn"),
             ((0, -8.0, D["db_z1"]), "dial board (top 55.9)"), ((0, -13.5, D["db_z0"] - 0.6), "LED site"),
             ((0, -2.0, D["ls_run_z"][1]), "strap loop"), ((0, -4.0, D["z_board_top"]), "rod-link board + nut"),
             ((10, 0, 52.0), "dial (pocket on a 2.0 wall)"), ((14.0, 0, 58.3), "flex parts patch"),
             ((20.6, 0, 50.0), "main knob glass (unchanged)")]
    else:
        rr = math.hypot(*db["rec"][:2]); ty = sum(zp["tail_y"]) / 2
        L = [(pol(rr + 3.2, a1, D["db_z1"] + 0.3), "receptacle (dial board)"), (pol(rr - 2.6, a1, D["rec_z1"] + 0.15), "24-pin plug (faces down)"),
             (pol(rr - 1.0, a1, D["pad_z"][1] - 0.4), "printed plug pad"), (pol(17.6, a1, D["db_z0"] + 0.4), "board lobe in the land cut"),
             (pol(ty / math.sin(math.radians(a0)), a0, D["leg_z0"] + 0.05), "tail, lower leg"), ((zp["uturn_x"], ty, 57.65), "tail U-turn"),
             (pol(20.3, a1, 56.5), "bezel"), (pol(8.0, a1, D["z_top"]), "lens, top 61.2"), (pol(6.0, a1, D["lcm_z0"] + 0.5), "panel (AMOLED)"),
             (pol(13.0, a1, 52.7), "dial (pocket floor, 2.0 wall)"), (pol(19.5, a0, 59.0), "glass seat + lap"),
             ((0.0, 2.0, D["ls_run_z"][1]), "strap loop"), ((0.0, 0.0, D["z_rod_top"]), "nut on the rod-link board")]
    pl.add_point_labels(np.array([p for p, _ in L]), [t for _, t in L], font_size=17, point_size=6, point_color="#c00000",
                        shape_color="#f2f2f2", shape_opacity=0.85, always_visible=True)
    title = ("Dial cartridge (v0.24 work): quarter cut out through the dial axis (x > 0, y < 0 removed), knob top only.\n"
             if which == "axis" else
             f"Dial cartridge (v0.24 work): quarter cut out between {a0:.0f}° and {a1:.0f}° (the plane through the plug and receptacle), knob top only.\n")
    pl.add_text(title + "Panel frame: z out of the panel, y up the panel. Clear parts (glass) at 40 %.", font_size=12, color="black")
    if which == "axis":
        pl.camera_position = [(60, -75, 105), (-2, 2, 53), (0, 0, 1)]
    else:
        am = math.radians((a0 + a1) / 2)
        pl.camera_position = [(95 * math.cos(am), 95 * math.sin(am), 100), (2.0 * math.cos(am), 2.0 * math.sin(am), 55), (0, 0, 1)]
    pl.camera.zoom(1.55 if which == "axis" else 1.75)
    pl.screenshot(out); print("wrote", out)


if __name__ == "__main__":
    kind, out = sys.argv[1], sys.argv[2]
    if kind == "sections":
        sections(out)
    else:
        quarter(out, sys.argv[3] if len(sys.argv) > 3 else "axis")
