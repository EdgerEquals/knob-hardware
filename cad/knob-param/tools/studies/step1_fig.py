# Layout v4 step 1 in the model (3 Nov 2026): sections through the joystick and plans of the main-board front, the case cradle's
# flange and the lip in the faceplate, all cut from the real parts (knob model + the joystick placed at (0, place_y)), panel frame.
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/step1_fig.py <out.png>
import sys, textwrap
sys.path.insert(0, ".")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
from knobparam.assembly.section_atlas import _parts
from knobparam.assembly.plan_sheet import cut, draw

out = sys.argv[1] if len(sys.argv) > 1 else "step1.png"
D, JD, parts = _parts()
py = JD["place_y"]
M = D["mcu"]; V = D["vb"]
yl = (py - 22.5, D["panel_y1"] + 0.5)     # joystick region, up to the panel top
zl = (-7.5, JD["scr_top"] + 2.0)
xl = (-26.5, 26.5)

fig = plt.figure(figsize=(24, 17.5), dpi=110)
gs = fig.add_gridspec(2, 3, height_ratios=[zl[1] - zl[0], 44.0], hspace=0.22, wspace=0.14)
legend = {}
_draw = draw


def draw(ax, layer, title, *a, **k):   # wrapped panel titles (they ran into each other)
    return _draw(ax, layer, textwrap.fill(title, 78), *a, **k)


def ann(ax, txt, xy, xyt, **kw):
    ax.annotate(txt, xy, xyt, fontsize=7.5, arrowprops=dict(arrowstyle="-", lw=0.5, color="0.25"), color="0.1", **kw)


# ---- (1) x = 0: front to back through the chip, the top board, the cradle's end walls and lip ring, the standoff
ax = fig.add_subplot(gs[0, 0])
legend.update(draw(ax, cut(parts, "x", 0.0), "x = 0 (front to back through the joystick axis, the H7B0 and the vertical boards' standoff); "
                   "y up the panel, z out of it", yl, zl, xlabel="y (mm, panel)", ylabel="z (mm, main-PCB front = 0)"))
ann(ax, f"H7B0 LQFP100 on the board front\n({M['xy'][0]:g}, {M['xy'][1]:g}), 16 x 16 x 1.6", (M["xy"][1], 1.0), (M["xy"][1] - 9, 7))
ann(ax, f"standoff joining L and R\ny {D['vb_standoff']['y']:g}, z {D['vb_standoff']['z']:g}", (D["vb_standoff"]["y"], D["vb_standoff"]["z"]),
    (D["vb_standoff"]["y"] - 10, D["vb_standoff"]["z"] + 5))
ann(ax, f"top board z {JD['z_db0']:g}-{JD['z_db1']:g}\n(on the spring contacts)", (py - 6, JD["z_db0"] + 0.5), (py - 21, JD["z_db0"] - 6))
ann(ax, f"case cradle: flange z {JD['z_fl0']:.1f}-{JD['z_fl1']:.1f}\non a {JD['gasket']['t']:g} gasket ({JD['gk_nom']:.2f} at nominal)",
    (py + JD["fl_y0"] + 1, JD["z_fl1"] - 0.5), (py - 21.5, 11.5))
ann(ax, f"lip ring in the cutout\nz {JD['z_fp0']:g}-{JD['z_lip1']:g}", (py - JD["lip_out_hh"] + 0.5, JD["z_lip1"] - 0.5),
    (py - 18, JD["z_lip1"] + 5.5))
ann(ax, "+y: lip ring only (the faceplate sits\non the rail strip: no flange, no gasket)", (py + JD["lip_out_hh"] - 0.5, JD["z_lip1"] - 0.5),
    (py + 2, JD["z_lip1"] + 7))

# ---- (2) y = 37: across through the chip, both vertical boards, headers, contact strips, the top board, the cradle hangers and lip
ax = fig.add_subplot(gs[0, 1])
legend.update(draw(ax, cut(parts, "y", M["xy"][1]), f"y = {M['xy'][1]:g} (across, through the H7B0, both vertical boards, the top board, "
                   "the case cradle's hangers, flange and lip); viewed from below the panel", xl, zl, xlabel="x (mm)", ylabel="z (mm)"))
ann(ax, f"vertical board L (power)\nx −{V['x']:g}, z {V['z0']:g}-{D['vb_z1']:g}", (-V["x"], 15), (-25.5, 20))
ann(ax, f"vertical board R (CAN,\njoystick lines)", (V["x"], 15), (18.2, 20))
ann(ax, f"right-angle header\n(legs x ±{D['vb_pin_x']:.2f})", (D["vb_pin_x"], 1.2), (18.2, 6))
ann(ax, f"spring contacts, {D['vb_n_contacts']} [A]\n{D['vb_pogo']['work']:g} of {D['vb_pogo']['travel']:g} travel at nominal",
    (D["vb_contact_x"], D["vb_z1"] + 0.5), (19.5, 24))
ann(ax, f"hanger + shoulder (top board glued),\nlip {JD['cc']['lip_t']:g} wall, {JD['cc']['lip_c']:g} to the cutout",
    (JD["nest_hw"] + 0.5, JD["z_db1"] + 0.5), (-1, 16.5))
ann(ax, f"carrier ±{JD['car_hw']:.2f} (was ±20.46)\n+ slide {JD['slide']:g} + {JD['tol_sla']:g} = lip inner ±{JD['lip_in_hw']:.2f}",
    (JD["car_hw"] - 1, JD["z_c0"] + 0.5), (-13, 23))
ann(ax, f"H7B0", (0, 1.0), (-4, 8))

# ---- (3) y through the hold-down springs and the top ball seats
ys = py + JD["spr_y"]
ax = fig.add_subplot(gs[0, 2])
legend.update(draw(ax, cut(parts, "y", ys), f"y = {ys:.2f} (across, through the top pair of hold-down springs, between the chip's "
                   "courtyard and the vertical boards)", xl, zl, xlabel="x (mm)", ylabel="z (mm)"))
ann(ax, "hold-down spring: rear anchor\n→ main PCB → top board → carrier", (JD["spr_x"], 18), (2, 22))
ann(ax, f"inner face to the spring:\n{D['vb_face_in'] - JD['spr_x'] - JD['spr_d'] / 2:.1f}", (D["vb_face_in"], 10), (17.5, 9))

# ---- (4) plan at the main-board front
zf = 0.8
ax = fig.add_subplot(gs[1, 0])
lay = cut(parts, "z", zf)
legend.update(draw(ax, lay, f"plan z = {zf:g}: main-board front under the joystick (H7B0, vertical boards and headers, hold-down "
                   "springs, top corner posts); looking at the panel face", xl, (py - 19, D["panel_y1"] - 9), xlabel="x (mm)", ylabel="y (mm)"))
(mx, my), c = M["xy"], M["court"] / 2
ax.add_patch(Rectangle((mx - c, my - c), 2 * c, 2 * c, fill=False, ls="--", lw=0.8, ec="k"))
ann(ax, f"courtyard {M['court']:g} □ [A]", (mx + c, my - c + 1), (mx + c - 2, my - c - 4))
ax.axhline(26.06, lw=0.6, ls=":", color="k"); ax.text(-26, 26.3, "A/B windows stop at the grip block's edge, y 26.06", fontsize=7)
for cx, cy in D["corners"][2:]:
    ax.add_patch(plt.Circle((cx, cy), D["notch_r"], fill=False, ls=":", lw=0.7, ec="k"))
ann(ax, f"header legs stop at y {D['vb_pin_y'][-1]:.1f}:\n1.0+ from the corner notch", (D["vb_pin_x"], D["vb_pin_y"][-1]), (5, D["panel_y1"] - 13))

# ---- (5) plan through the cradle flange (behind the faceplate)
zc = (JD["z_fl0"] + JD["z_fl1"]) / 2
ax = fig.add_subplot(gs[1, 1])
legend.update(draw(ax, cut(parts, "z", zc), f"plan z = {zc:.2f}: the case cradle's flange behind the faceplate (U: knob side and both "
                   "long sides), ball seats, carrier cup bosses above", xl, (py - 19, D["panel_y1"] + 0.5), xlabel="x (mm)", ylabel="y (mm)"))
ax.axhline(D["panel_y1"] - 10.0 - 0.4, lw=0.6, ls=":", color="k")
ax.text(-26, D["panel_y1"] - 10.2, "rail strip: nothing behind the panel above here", fontsize=7)
ann(ax, f"gasket land {JD['gk_land_x']:.2f} (sides, tight)\n{JD['gk_land_y']:.2f} (knob side)", (JD["fl_x1"], py), (6, py - 14))

# ---- (6) plan inside the faceplate: lip ring, carrier floor, cutout
zp = (JD["z_lip1"] + D["z_fp0"]) / 2 + 0.5
ax = fig.add_subplot(gs[1, 2])
legend.update(draw(ax, cut(parts, "z", zp), f"plan z = {zp:.2f}: inside the faceplate: cutout (unchanged), the cradle's lip ring and the "
                   "narrower carrier floor (the lip ring is also the anti-rotation stop)", xl, (py - 19, D["panel_y1"] + 0.5), xlabel="x (mm)", ylabel="y (mm)"))
ann(ax, f"cutout ±{JD['hole_hw']:.2f} × ±{JD['hole_hh']:.2f}\ngrip block covers it by {JD['block_cover_rest']:.2f} ({JD['block_cover_slide']:.2f} at full slide)",
    (JD["hole_hw"], py + 5), (4, D["panel_y1"] - 3))

lax = fig.add_axes([0.06, 0.0, 0.9, 0.05]); lax.axis("off")
lax.legend(handles=[Patch(fc=c_, ec="k", lw=0.3, label=l_) for l_, c_ in sorted(legend.items())], loc="center", ncol=5, fontsize=8, frameon=False)
fig.suptitle(textwrap.fill(
    f"Knob module {D['version']}, layout v4 step 1 [Ed 3 Nov]: H7B0 on the main-board front at ({M['xy'][0]:g}, {M['xy'][1]:g}) under the joystick; "
    f"two vertical boards (x ±{V['x']:g}, y {V['y'][0]:g}-{V['y'][1]:g}) carry the signals up through {D['vb_n_contacts']} spring contacts to the "
    f"joystick top board; the top board is glued into a clear SLA cradle with a flange behind the faceplate (on a gasket) and a lip ring "
    f"in the faceplate cutout. Joystick at (0, {py:.2f}).", 190), fontsize=12, x=0.01, ha="left", y=0.995)
fig.subplots_adjust(top=0.92, bottom=0.07, left=0.04, right=0.99)
fig.savefig(out, bbox_inches="tight")
print("wrote", out)
