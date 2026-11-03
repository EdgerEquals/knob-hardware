"""v0.25 gear figures [Ed 3 Nov 19:00-19:10]: the spur ring stage and the 1220 hub mesh with the PA-12 hub-gear ring in the clear cap.
Parts come from the model (cached build), panel frame. Run from cad/knob-param:
  KNOBPARAM_CACHE=... xvfb-run -a .venv/bin/python tools/studies/gears_v025_fig.py ring OUT.png
  KNOBPARAM_CACHE=... xvfb-run -a .venv/bin/python tools/studies/gears_v025_fig.py hub OUT.png"""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from knobparam.common import model, gearcheck
from knobparam.assembly.build import build_all, view
from knobparam.assembly.plan_sheet import _cut_faces
from knobparam.assembly.colours import colour

which, out = sys.argv[1], sys.argv[2]
D = model.derive(model.default_params())
parts, _st, keys, _own = build_all(D, only=["main_knob", "base_drive", "under_pcb", "control_dial"])
parts, keys = view(parts, keys, D, "panel")
P = lambda pre: [n for n in parts if n.startswith(pre)]
PIN, RING, CAP, TUBE, CLR = "#e67e22", "#6e7377", "#9fd3e6", "#c8ccd0", "#d4ecf2"
rot = D["mech_rot"]


def pol(r, a):
    a = math.radians(a + rot)
    return r * math.cos(a), r * math.sin(a)


def add(ax, name, col, at, axis="z", a=1.0, z=1):
    t = _cut_faces(parts[name], axis, at)
    if t:
        ax.add_collection(PolyCollection(t, facecolors=col, edgecolors=col, linewidths=0.25, alpha=a, zorder=z))


def ann(ax, txt, xy, xyt, **kw):
    ax.annotate(txt, xy, xyt, fontsize=kw.pop("fs", 9.5), arrowprops=dict(arrowstyle="-", lw=0.7), **kw)


def pv_mesh(pl, solid, col, opacity=1.0, edges=True):
    import pyvista as pv
    V, T = solid.tessellate(0.02, 0.2)
    if not T:
        return
    m = pv.PolyData(np.array([(v.X, v.Y, v.Z) for v in V]), np.hstack([np.full((len(T), 1), 3), np.array(T)]).ravel())
    pl.add_mesh(m, color=col, opacity=opacity, smooth_shading=False, ambient=0.3, diffuse=0.8, specular=0.2)
    if edges:
        fe = m.extract_feature_edges(35)
        if fe.n_points:
            pl.add_mesh(fe, color="#202020", line_width=0.8, opacity=min(1.0, opacity + 0.3))


if which == "ring":
    zr = D["hb_mid"]; zc = (D["fg_z_top"] + D["fg_z_bot"]) / 2
    fig = plt.figure(figsize=(19, 8.4), dpi=110)
    a1 = fig.add_axes([0.03, 0.08, 0.36, 0.80]); a2 = fig.add_axes([0.42, 0.08, 0.30, 0.80]); a3 = fig.add_axes([0.75, 0.30, 0.23, 0.58])
    ring_names = P("bottom internal ring") + P("knob lower-cap land") + P("knob glass sleeve")
    for n in ring_names:
        add(a1, n, RING if "ring" in n else (CLR if "land" in n else colour(n)), zr, a=1.0 if "ring" in n else 0.6)
    add(a1, "base cradle", CLR, zr, a=0.7)
    add(a1, "motor", colour("motor"), zr)
    for n in ["encoder pinion", "idler pinion 1", "idler pinion 2"]:
        add(a1, n, PIN, zr, z=2)
    for n in P("idler pin ") + ["encoder shaft"]:
        add(a1, n, colour(n), zr, z=3)
    add(a1, "control dial", colour("control dial"), zr, a=0.8)
    ex, ey = pol(D["enc_cd"], D["enc_ang"]); i1 = pol(D["enc_cd"], D["idler_angs"][0]); i2 = pol(D["enc_cd"], D["idler_angs"][1])
    ann(a1, f"encoder pinion {D['z_enc_pinion']}T (r {D['enc_cd']:.3f})", (ex - 1.5, ey + 3.0), (ex - 16, ey + 9.5))
    ann(a1, f"idler 1 {D['z_enc_pinion']}T (the feel\ncompound is on its\npin, under the PCB)", (i1[0] + 2.5, i1[1] - 2.5), (i1[0] + 2.5, i1[1] - 16.0))
    ann(a1, f"idler 2 {D['z_enc_pinion']}T", (i2[0] - 2.5, i2[1] - 3.0), (i2[0] - 11, i2[1] - 12))
    ann(a1, f"internal ring {D['z_ring']}T m{D['hb_mn']:g}, straight, one piece\n(v0.24: 54T 25° herringbone, two halves)",
        (14.0, 12.0), (2, 25.0))
    ann(a1, "1220 can", (2.5, -D["offset"] - 2.5), (8, -21.5), fs=9)
    ann(a1, "clear land (bottom race)", (-14.5, -14.5), (-24.0, -22.3), fs=9)
    ann(a1, "Hall arm", (-2.0, 6.0), (-9.5, 2.0), fs=9)
    th = np.linspace(0, 2 * np.pi, 361)
    a1.set_xlim(-25, 25); a1.set_ylim(-23.5, 27.5); a1.set_aspect("equal"); a1.grid(alpha=0.2)
    a1.set_xlabel("x (mm, panel)"); a1.set_ylabel("y (mm, up the panel)")
    a1.set_title(f"1. Plan, cut through the ring stage (z {zr:.2f})", fontsize=11, loc="left")
    # 2. compound stage under the PCB
    fg = P("feel compound gear")[0]; fp = [n for n in P("feel motor pinion") if not n.endswith("cap")][0]
    add(a2, fg, PIN, zc, z=2); add(a2, fp, "#b9770e", zc, z=2)
    for n in P("idler pin ") + ["encoder shaft", "feel motor shaft Ø2 [A]"] + P("encoder disc") + P("encoder bearing"):
        if n in parts:
            add(a2, n, colour(n), zc, z=3)
    xw, xe = 22.75, D["fg_edge_x"]
    for s_ in (-1, 1):
        a2.axvline(s_ * xw, color="k", lw=1.0); a2.axvline(s_ * xe, color="k", lw=0.8, ls="--")
    tip = i1[0] + D["fg_tip"]
    a2.plot([tip, tip], [i1[1] - 2, i1[1] + 2], color="#c0392b", lw=1.5)
    ann(a2, f"compound {D['fg_z_gear']}T m{D['fg_mod']:g} on idler 1\n(tip x {tip:.2f}; a 40T would reach {i1[0] + (40 / 2 + D['spur_addendum']) * D['fg_mod']:.2f})",
        (i1[0] - 6.0, i1[1] - 6.0), (-5.5, -21.5))
    fx, fy = D["fm_xy"]; fpx, fpy = pol(math.hypot(fx, fy), math.degrees(math.atan2(fy, fx)))
    ann(a2, f"716 feel pinion {D['fg_z_pin']}T m{D['fg_mod']:g}\n(printed PA-12, was \"nylon 0.5M-12T\")", (fpx - 1.5, fpy + 1.5), (-5.5, 16.5))
    ann(a2, "encoder shaft", (0, ex and ey), (-5.5, 9.5), fs=9)
    ann(a2, f"cover side wall\nx {xw:g} (solid);\nfg_edge_x {xe:g} [A]\n(dashed)", (xe, 6.0), (14.3, 9.6), fs=9)
    a2.set_xlim(-6, 25); a2.set_ylim(-23.5, 20); a2.set_aspect("equal"); a2.grid(alpha=0.2)
    a2.set_xlabel("x (mm, panel)")
    a2.set_title(f"2. Plan under the PCB, feel compound stage (z {zc:.2f})", fontsize=11, loc="left")
    # 3. zoom on the encoder mesh
    for n in P("bottom internal ring"):
        add(a3, n, RING, zr)
    add(a3, "encoder pinion", PIN, zr, z=2); add(a3, "encoder shaft", colour("encoder shaft"), zr, z=3)
    ox, oy = pol(D["enc_cd"] + 4.0, D["enc_ang"])
    a3.set_xlim(ox - 3.2, ox + 3.2); a3.set_ylim(oy - 2.6, oy + 2.0); a3.set_aspect("equal"); a3.grid(alpha=0.2)
    a3.set_title("3. Zoom: encoder pinion in the ring", fontsize=11, loc="left")
    g = gearcheck.mesh(D["z_enc_pinion"], D["z_ring"], D["hb_mt"], D["hb_pressure"], D["enc_cd"], True, D["hb_backlash"],
                       D["hb_addendum"], D["hb_dedendum"])
    S = gearcheck.strength(D)
    txt = (f"module {D['hb_mn']:g}: the smallest on the 0.05 grid (DIN 780)\nwhose 12T tip keeps 0.50 [Ed 19:06]\n"
           f"12T tip {D['hb_tip_th']:.3f} after 0.10 backlash (floor 0.50: TIGHT)\n"
           f"contact ratio {g['eps_eff']:.2f} effective ({g['eps']:.2f} geometric)\n"
           f"ring wall {D['hb_wall']:.2f}, ring tips r {D['hb_tip_r']:.3f},\npinion centres r {D['enc_cd']:.3f} (v0.24 13.903)\n"
           f"feel ratio ({D['fg_z_gear']}/{D['fg_z_pin']}) x ({D['z_ring']}/{D['z_enc_pinion']}) = {D['fm_ratio']:.2f}:1\n(v0.24 16.36; 40T needs fg_edge_x 22.51)\n"
           f"knob torque through one pinion: {S['ring_T_fat_knob']:.0f} mNm fatigue SF 1.5,\n"
           f"{S['ring_T_static_knob']:.0f} static SF 2 (716 burst ~8)")
    fig.text(0.745, 0.10, txt, fontsize=8.6, va="bottom", family="monospace")
    fig.suptitle(f"v0.25 ring stage: straight teeth, one-piece {D['z_ring']}T ring, m{D['hb_mn']:g}, three {D['z_enc_pinion']}T pinions "
                 f"[Ed 3 Nov 19:00-19:06]", fontsize=13, x=0.01, ha="left")
    fig.savefig(out); print("wrote", out)

else:
    hg = P("knob hub gear ring")[0]
    RING = "#3d4b57"     # the PA-12 ring drawn darker than the PA-12 dial so the two read apart
    zp0 = D["h_pinion0"]; zp1 = zp0 + D["motor_pinion_face"]; zm = (zp0 + zp1) / 2; zk = (D["h_band1"] + D["hg_z1"]) / 2
    py = -D["offset"]
    fig = plt.figure(figsize=(20, 8.6), dpi=110)
    a1 = fig.add_axes([0.03, 0.42, 0.22, 0.48]); a1b = fig.add_axes([0.03, 0.03, 0.22, 0.33])
    a2 = fig.add_axes([0.28, 0.08, 0.30, 0.80]); a3 = fig.add_axes([0.60, 0.20, 0.39, 0.70])
    add(a1, hg, RING, zm); add(a1, "pinion", PIN, zm, z=2)
    for n in ("control dial", "brass tube"):
        add(a1, n, colour(n) if n != "brass tube" else TUBE, zm, a=0.5)
    a1.plot([0, 0], [0, py], color="k", lw=0.7, ls="--")
    ann(a1, f"hub-gear ring {D['z_hub_gear']}T m{D['hub_mod']:g}, x {D['hub_x_gear']:+.2f}\n(PA-12, glued in the clear cap)", (4.6, 4.6), (2.5, 9.5))
    ann(a1, f"1220 pinion {D['z_pinion']}T m{D['hub_mod']:g}\n(printed PA-12)", (3.4, py - 3.2), (5.5, py - 6.5), color="#a04000")
    ann(a1, f"motor axis {D['offset']:.2f}\n(pair cut for {D['hub_cd']:.2f})", (0, py / 2 - 0.5), (-10.5, py / 2 - 2.5), fs=8.5)
    a1.set_xlim(-11, 13); a1.set_ylim(py - 8, 12.5); a1.set_aspect("equal"); a1.grid(alpha=0.2)
    a1.set_title(f"1. Plan through the pinion (z {zm:.1f})", fontsize=11, loc="left")
    # 1b. through the collar and keys
    add(a1b, "knob upper-cap", CAP, zk, a=0.75); add(a1b, hg, RING, zk, z=2)
    for n in ("control dial", "brass tube"):
        add(a1b, n, colour(n) if n != "brass tube" else TUBE, zk, a=0.5)
    ann(a1b, f"{D['hg_keys']} keys {D['hg_key_w']:g} x {D['hg_key_h']:g}", (0, D["hg_collar_r"] + 0.3), (3.5, 10.0), fs=9)
    ann(a1b, "clear cap (UTR-8100)", (-9.5, 0), (-12.5, -10.5), fs=9)
    a1b.set_xlim(-12.5, 12.5); a1b.set_ylim(-11.5, 11.5); a1b.set_aspect("equal"); a1b.grid(alpha=0.2)
    a1b.set_title(f"1b. Plan through the collar in the cap (z {zk:.2f})", fontsize=10.5, loc="left")
    # 2. straight-on cut through both axes (x = 0)
    for n, col, al in (("knob upper-cap", CAP, 0.75), (hg, RING, 1.0), ("pinion", PIN, 1.0), ("motor", colour("motor"), 0.9),
                       ("control dial", colour("control dial"), 0.45), ("brass tube", TUBE, 1.0), ("knob glass sleeve", colour("knob glass sleeve"), 0.35)):
        add(a2, n, col, 0.0, "x", al, 2 if n in ("pinion", hg) else 1)
    ann(a2, f"pinion, face {D['motor_pinion_face']:g}\n(z {zp0:.1f}-{zp1:.1f},\n0.5 under the cap)", (py - 4.0, zm), (py - 16.0, 42.0), color="#a04000")
    ann(a2, f"hub-gear ring (PA-12):\nteeth z {D['knob_hub_z0']:.1f}-{D['h_band1']:.1f},\nkeyed collar to {D['hg_z1']:.1f}\nin the cap; wall to\n"
            f"the bore {D['race_wall']:.2f} (TIGHT)", (6.0, 41.5), (6.3, 30.3), fs=8.5)
    ann(a2, f"clear cap (UTR-8100):\n{D['hg_resin_over']:.2f} of resin over the collar;\nball race in the 45° chamfer", (-13.0, 48.0), (-26.5, 50.5))
    ann(a2, "dial tube (PA-12) on\nthe brass tube", (-3.2, 36.0), (-26.5, 30.5), fs=9)
    ann(a2, "1220 gearbox", (py - 3, 35), (-26.5, 35.0))
    a2.set_xlim(py - 16.5, 15.5); a2.set_ylim(29.5, 54); a2.set_aspect("equal"); a2.grid(alpha=0.2)
    a2.set_xlabel("y (mm, up the panel)"); a2.set_ylabel("z (mm, out of the panel)")
    a2.set_title("2. Straight-on cut through both axes (x = 0)", fontsize=11, loc="left")
    # 3. 3D quarter cut-away: clear cap translucent
    import pyvista as pv
    from build123d import Box, Pos, Align
    region = Pos(-12, py - 7.0, 37.0) * Box(24, 7.0 - py + 12, 11.0, align=(Align.MIN,) * 3)
    quad = Pos(0, -40, 20) * Box(40, 80, 40, align=(Align.MIN, Align.MIN, Align.MIN))
    pl = pv.Plotter(off_screen=True, window_size=(1300, 1000)); pl.set_background("white")
    for n, col, op in (("pinion", PIN, 1.0), (hg, RING, 1.0), ("motor", colour("motor"), 1.0), ("brass tube", TUBE, 1.0),
                       ("knob upper-cap", CAP, 0.4)):
        try:
            q = (parts[n] & region) - quad
        except Exception:
            continue
        if q is None or not q.solids():
            continue
        pv_mesh(pl, q, col, op, edges=op > 0.5)
    pl.camera_position = [(-29, py - 22, 62), (0, py / 2 + 1.0, 42.0), (0, 0, 1)]
    pl.add_text("pinion (orange), PA-12 hub-gear ring (dark), clear cap (blue, see-through); x > 0 cut away", font_size=13, color="black")
    a3.imshow(pl.screenshot(None, return_img=True)); a3.axis("off")
    a3.set_title("3. 3D quarter cut-away", fontsize=11, loc="left")
    S = gearcheck.strength(D)
    g = gearcheck.mesh(D["z_pinion"], D["z_hub_gear"], D["hub_mod"], D["pressure"], D["offset"], False, D["brass_backlash"],
                       D["spur_addendum"], D["spur_dedendum"], D["hub_x_pin"], D["hub_x_gear"])
    txt = (f"m{D['hub_mod']:g} {D['z_pinion']}/{D['z_hub_gear']} = {D['ratio_knob_motor']:.3f}, shift x {D['hub_x_pin']:+.2f}/{D['hub_x_gear']:+.3f}, "
           f"cut for {D['hub_cd']:.2f}, runs at {D['offset']:.2f}\n"
           f"tips {D['hub_pin_tip_th']:.2f}/{D['hub_tip_th']:.2f}; contact ratio {g['eps_eff']:.2f} at {D['offset']:.2f} "
           f"(backlash {g['backlash']:.3f}); face {D['hub_face']:g}\n"
           f"allowable (Lewis, MJF PA-12, weak member: {S['hub_weak']}):\n"
           f"  1220 output: {S['hub_T_static_out']:.1f} mNm static SF 2 (limit {D['hub_i_limit']:g}: TIGHT), {S['hub_T_fat_out']:.1f} fatigue SF 1.5\n"
           f"  knob:        {S['hub_T_static_knob']:.0f} mNm static SF 2, {S['hub_T_fat_knob']:.0f} fatigue SF 1.5, break {S['hub_T_break_knob']:.0f}\n"
           f"  (v0.24 m0.6 14/22 x 3.0: {S['hub_v024_static_knob']:.0f} / {S['hub_v024_fat_knob']:.0f})")
    fig.text(0.60, 0.03, txt, fontsize=9.5, va="bottom", family="monospace")
    fig.suptitle(f"v0.25 hub mesh: straight m{D['hub_mod']:g} {D['z_pinion']}T / {D['z_hub_gear']}T, both PA-12, face {D['hub_face']:g}; "
                 f"the hub gear is a PA-12 ring glued into the clear upper cap [Ed 3 Nov 19:00-19:10]", fontsize=13, x=0.01, ha="left")
    fig.savefig(out); print("wrote", out)
