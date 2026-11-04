"""Control dial (v0.15: ball seating groove in the cone, lip bonded round the panel, Hall bar down through the cradle): tube on the thrust balls, dial half of the 45 deg cone race, hub/web/lip, Hall arm (printed in one), screen cut + FPC slot."""
import math
from build123d import *
from ...common.util import A, rev, cyl, tube
from . import thrust, hall_arm as hall
from .. import params as _p
SRC_DEPS = [thrust, hall]

def wedge(a0, a1, z0, h, r=60.0):
    """Prism over the plan angles a0..a1 (degrees, a1 > a0, span < 180), from the axis out to r."""
    n = max(2, int((a1 - a0) / 10) + 1)
    pts = [(0.0, 0.0)] + [(r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    return Pos(0, 0, z0) * extrude(Face(Wire.make_polygon([Vector(x, y, 0) for x, y in pts], close=True)), h)

def ring_sector(r0, r1, a0, a1, z0, h):
    """Exact annular sector r0..r1 over a0..a1 degrees, z0..z0+h."""
    return tube(r0, r1, z0, h) & wedge(a0, a1, z0 - 0.01, h + 0.02, r1 + 5.0)

def to_mech(D, s):
    """v0.24: cartridge geometry is drawn in the panel frame; the control_dial parts live in the mechanism frame."""
    return Rot(0, 0, -D["mech_rot"]) * s

def cart_profile(D):
    """v0.24 [Ed 12:58]: underside unchanged (Danny's 30° cone) out to the outer wall r 19.2; top = well floor, then the pocket on a
    2.0 normal wall to r 16.3, the ledge (board underside) to r 17.3, the land (board top) out to the wall."""
    ri, rt, ct = D["dial_tube_id"] / 2, D["dial_tube_od"] / 2, D["ct"]
    under = _p.cart_under(D)
    top = [(ct["outer_r"], D["db_z1"]), (D["ct_land_r"], D["db_z1"]), (D["ct_land_r"], D["db_z0"]), (ct["pocket_r"], D["db_z0"])]
    return [(ri, D["dial_z_base"]), (rt, D["dial_z_base"])] + under + top + list(reversed(D["ct_top"]))

def radial_cyl(r_in, r_out, d, z, a):
    """Cylinder of diameter d on the radial line at panel angle a (deg), from radius r_in to r_out, axis at height z."""
    return Rot(0, 0, a) * Pos(r_in, 0, z) * Rot(0, 90, 0) * Cylinder(d / 2, r_out - r_in, align=(Align.CENTER, Align.CENTER, Align.MIN))

def rib_box(r0, r1, w, z0, z1, a):
    """Radial block at panel angle a: r0..r1, tangential width w, z0..z1."""
    return Rot(0, 0, a) * Pos(r0, -w / 2, z0) * Box(r1 - r0, w, z1 - z0, align=(Align.MIN, Align.MIN, Align.MIN))

def cart_cuts(D):
    """Land cut to the ledge round the board's lobe; v0.25 [Ed 18:26]: sideways magnet pockets in the outer wall (open outward)
    and the slots for the key and seat ribs (open at the top and outward). Panel frame."""
    ct, db, bz = D["ct"], D["db"], D["bz"]
    a0, a1, rl = db["lobe"]; c = ct["lobe_clear"]; da = math.degrees(c / rl)
    cut = ring_sector(D["ct_land_r"] - 0.01, rl + c, a0 - da, a1 + da, D["db_z0"], D["db_z1"] - D["db_z0"] + 0.5)
    d, h = bz["mag"]; ro = ct["outer_r"]
    for a, (rd, zd), _ in D["cart_mags"]:
        cut += radial_cyl(ro - h, ro + 0.5, d + bz["mag_press"], zd, a)
    for a, cl, _k in D["cart_ribs"]:
        cut += rib_box(D["rib_slot_r0"], ro + 0.5, bz["rib_w"] + 2 * cl, D["rib_z0"], D["db_z1"] + 0.5, a)
    return cut

def profile(D):
    ri, rt, rb, rh = D["dial_tube_id"] / 2, D["dial_tube_od"] / 2, D["dial_bore_d"] / 2, D["dial_hub_od"] / 2
    rc, rw, rl, g, f = D["r_cup"], D["r_web"], D["knob_od"] / 2, D["gusset"], D["lip_fillet"]
    if D.get("cart"):
        return cart_profile(D)
    if D["dial_shape"] == "cone" and D["kb_race"] == "chamfer":
        # v0.21 [Ed 2 Nov]: no steps. Underside: hub bottom, the 45° race, then one straight cone up to the lip over the glass.
        # Top: the well round the adapter board, one straight cone parallel to the underside, then the flat carrier seat.
        hub = [(rt, D["z_hub0"]), (rh, D["z_hub0"])] + ([(rh, D["z_web0"] - g)] if D["z_hub0"] < D["z_web0"] - g - 1e-6 else [])
        rs, zs = D["cone_seat_r"], D["z_screen_cut"]
        return ([(ri, D["dial_z_base"]), (rt, D["dial_z_base"])] + hub + [(D["cone_under_r0"], D["z_web0"]), (D["cone_lip_r"], D["z_lip0"])]
                + _lip_edge(D, rl) + [(rl, D["z_top"]), (rs, D["z_top"]), (rs, zs), (D["cone_well_r"], D["cone_top_z_well"]),
                                      (D["cone_well_r"], D["z_well_top"]), (ri, D["z_well_top"])])
    if D["kb_race"] == "chamfer":   # v0.15c: plain tube straight into the hub (no flare, no collar); the gusset is the ball face
        hub = [(rt, D["z_hub0"]), (rh, D["z_hub0"])] + ([(rh, D["z_web0"] - g)] if D["z_hub0"] < D["z_web0"] - g - 1e-6 else [])
        top = [(rc, D["z_web1"]), (D["r_well"], D["z_web1"]), (D["r_well"], D["z_well_top"])]
        bore = [(rb, D["z_well"]), (rb, D["z_bore0"]), (ri, D["z_bore0"])] if D["adapter_cup"] else [(ri, D["z_well_top"])]   # no cup: plain tube ID
        return ([(ri, D["dial_z_base"]), (rt, D["dial_z_base"])] + hub + [(rh + g, D["z_web0"]),
                (rw, D["z_web0"]), (rw, D["z_lip0"] - f), (rw + f, D["z_lip0"])] + _lip_edge(D, rl) + [(rl, D["z_top"]), (rc, D["z_top"])] + top + bore)
    return [(ri, D["dial_z_base"]), (rt, D["dial_z_base"]), (rt, D["z_hub0"]), (D["dial_collar_d"] / 2, D["z_hub0"]),
            (D["dial_collar_d"] / 2, D["z_hubf"]), (rh, D["z_hubf"]), (rh, D["z_web0"] - g), (rh + g, D["z_web0"]),
            (rw, D["z_web0"]), (rw, D["z_lip0"] - f), (rw + f, D["z_lip0"]), (rl, D["z_lip0"]), (rl, D["z_top"]), (rc, D["z_top"]),
            (rc, D["z_web1"]), (D["r_well"], D["z_web1"]), (D["r_well"], D["z_well"]), (rb, D["z_well"]), (rb, D["z_bore0"]), (ri, D["z_bore0"])]

def _lip_edge(D, rl):
    """v0.19b [Ed 2 Nov]: the lip underside outer edge gets the same 45° chamfer as the glass top outer edge."""
    c = D.get("sleeve_top_cout", 0.0)
    return [(rl - c, D["z_lip0"]), (rl, D["z_lip0"] + c)] if c > 0 else [(rl, D["z_lip0"])]

def seat_groove(D):   # v0.15 ball seating groove (torus, tube radius kb_seat_r, centre on the 45 deg line through the ball centre)
    cr, cz = D["kb_seat_c"]
    return Pos(0, 0, cz) * Torus(cr, D["kb_seat_r"])

def panel_ctr(D):
    a = math.radians(D["tail_ang"]); o = D["lip_ctr_off"]
    return (-o * math.cos(a), -o * math.sin(a))

def race_add(D):   # 45 deg flare + collar on the tube, up into the hub
    rt, zd0 = D["kb_rt"], D["kb_zd0"]
    return rev([(rt - 0.6, zd0 - 1.6), (rt, zd0 - 1.6), (rt, zd0), (D["kb_r_collar"], D["kb_zd1"]),
                (D["kb_r_collar"], D["z_hub0"] + 0.2), (rt - 0.6, D["z_hub0"] + 0.2)])

def lip_slot(D):   # through the lip where the COF bend passes, widened for the dial travel
    r0 = math.sqrt(max((D["lip_id"] / 2) ** 2 - (D["lip_slot_w"] / 2) ** 2, 0)) - D["lip_ctr_off"] - 0.3   # through the ring over the slot width
    return Rot(0, 0, D["tail_ang"]) * Pos(r0, 0, D["z_holder0"] - 0.4) * Box(D["R"] + 2 - r0, D["lip_slot_w"], 10, align=(Align.MIN, Align.CENTER, Align.MIN))

def tm_pocket(D):   # v0.16: generous pocket through the dial web for the TMAG5273 board (open to the top under the carrier)
    br, bt, _ = D["tm_board"]; c = D["tm_pocket_clear"]; w, l, _, _ = D["tm_pkg"]
    z0 = D["tm_z_floor"]; z1 = D["z_holder0"] + 0.01
    r0 = D["tm_r"] - br / 2 - c
    box = Pos(r0, 0, z0) * Box(br + 2 * c, bt + 2 * c, z1 - z0, align=(Align.MIN, Align.CENTER, Align.MIN))
    return Rot(0, 0, D["tm_ang"]) * box

def tm_sensor(D):
    br, bt, bh = D["tm_board"]; w, l, h, _ = D["tm_pkg"]; r = D["tm_r"]
    board = Pos(r, 0, D["tm_z_board0"]) * Box(br, bt, bh, align=A)
    pkg = Pos(r, 0, D["tm_z_floor"]) * Box(w, l, h, align=A)
    return {"dial sensor board (turns with the dial)": Rot(0, 0, D["tm_ang"]) * board,
            "dial TMAG5273 (3D Hall, face-down)": Rot(0, 0, D["tm_ang"]) * pkg}

def bend_pocket(D):   # v0.16 closed lip: blind pocket in the lip ID for the ledge + COF bend (open to the top for screen service)
    S = D["S"]; c = D["bend_clear"]; z0 = D["z_holder0"] - 0.01; h = D["z_top"] - z0 + 1.0
    r_b = S["r_edge"] + (0 if S["rigid"] else S["bend"]) + c
    band = Pos(D["scr_r"] - 1.0, 0, z0) * Box(r_b - D["scr_r"] + 1.5, S["ledge_w"] + 2 * c, h, align=(Align.MIN, Align.CENTER, Align.MIN))
    led = cyl(S["r_edge"] + c, z0, h) & band
    if not S["rigid"]:
        hb = S["ledge_w"] / 2 - D["cof_inset"] + c
        led += cyl(r_b, z0, h) & (Pos(D["scr_r"] - 1.0, 0, z0) * Box(r_b - D["scr_r"] + 1.5, 2 * hb, h, align=(Align.MIN, Align.CENTER, Align.MIN)))
    a = math.radians(D["tail_ang"]); o = D["scr_off"]
    return Pos(-o * math.cos(a), -o * math.sin(a), 0) * Rot(0, 0, D["tail_ang"]) * led

def _flat_cut(D, r_flat, z0, h):
    """Half-space slab beyond the key flat (distance r_flat from the axis, facing dsp_flat_ang), z0..z0+h."""
    return Rot(0, 0, D["dsp_flat_ang"]) * Pos(r_flat, -10, z0) * Box(10, 20, h, align=(Align.MIN, Align.MIN, Align.MIN))

def split_parts(D, body):
    """v0.25 [Ed 18:12]: body = the one-piece dial (revolved profile, race groove cut). Lower part: the tube up to dsp_z1 with
    the key flat over the socket length, plus the Hall arm, detent spoke and lever. Dish: everything from the split up, less the
    through socket (tube OD + bond line, with the matching flat) and the cartridge cuts."""
    ri, rt = D["dial_tube_id"] / 2, D["dial_tube_od"] / 2; z0, z1 = D["dsp_z0"], D["dsp_z1"]; g = D["dsp"]["glue"]
    lower = rev([(ri, D["dial_z_base"]), (rt, D["dial_z_base"]), (rt, z1), (ri, z1)])
    lower -= _flat_cut(D, D["dsp_flat_d"], z0 - 0.3, z1 - z0 + 0.4)
    lower += hall.arm(D)
    sock = cyl(D["dsp_r_sock"], z0 - 0.5, D["z_well_top"] - z0 + 1.0) - _flat_cut(D, D["dsp_flat_d"] + g, z0 - 0.6, D["z_well_top"] - z0 + 1.2)
    dish = body - cyl(40, D["dial_z_base"] - 1.0, z0 - D["dial_z_base"] + 1.0) - sock
    nm = "control dial lower part (tube, Hall and detent spokes)" if D.get("cc_on") else "control dial lower part (tube, Hall and detent spokes, lever)"
    return {nm: lower,
            "control dial dish (bonded on the tube)": dish - to_mech(D, cart_cuts(D))}

def build(D):
    d = rev(profile(D))
    if D["tb_on"]: d -= thrust.groove(D)   # v0.19b [Ed]: no thrust ring, the tube end is plain over an air gap
    if D["rel_sensor"]: d -= tm_pocket(D)   # v0.16b [Ed]: relative sensor removed -> no pocket
    if D["kb_race"] != "chamfer": d += race_add(D)
    if D["kb_groove_h"] > 0: d -= seat_groove(D)
    if D.get("cart") and D["dsp"]["on"]:   # v0.25 [Ed 18:12]: two parts, split at the dish's underside
        return split_parts(D, d)
    d += hall.arm(D)
    if D.get("cart"):   # v0.24 [Ed 12:58]: no lip, screen cut, bend pocket or carrier magnet / pin: the bezel cartridge sits on the land
        return {"control dial": d - to_mech(D, cart_cuts(D))}
    d -= cyl(D["lip_id"] / 2, D["z_screen_cut"], 10, *panel_ctr(D))
    if D["screen_on_dial"]:   # v0.16 carrier magnet pocket + locating-pin hole in the dial shoulder
        md, mh = D["carr_mag"]; zh = D["z_holder0"]
        d -= cyl(md / 2 + D["dial_mag_press"] / 2, zh - D["carr_mag_gap"] - mh, mh + D["carr_mag_gap"] + 0.01, *D["carr_mag_xy"])
        d -= cyl(D["carr_pin"][0] / 2, zh - D["carr_pin"][1], D["carr_pin"][1] + 0.01, *D["carr_pin_xy"])
    d -= bend_pocket(D) if (D["screen_on_dial"] and D["lip_closed"]) else lip_slot(D)
    return {"control dial": d} | (tm_sensor(D) if D["rel_sensor"] else {})
