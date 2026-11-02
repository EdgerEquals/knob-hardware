"""Control dial (v0.15: ball seating groove in the cone, lip bonded round the panel, Hall bar down through the cradle): tube on the thrust balls, dial half of the 45 deg cone race, hub/web/lip, Hall arm (printed in one), screen cut + FPC slot."""
import math
from build123d import *
from ...common.util import A, rev, cyl
from . import thrust, hall_arm as hall
SRC_DEPS = [thrust, hall]

def profile(D):
    ri, rt, rb, rh = D["dial_tube_id"] / 2, D["dial_tube_od"] / 2, D["dial_bore_d"] / 2, D["dial_hub_od"] / 2
    rc, rw, rl, g, f = D["r_cup"], D["r_web"], D["knob_od"] / 2, D["gusset"], D["lip_fillet"]
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

def build(D):
    d = rev(profile(D))
    if D["tb_on"]: d -= thrust.groove(D)   # v0.19b [Ed]: no thrust ring, the tube end is plain over an air gap
    if D["rel_sensor"]: d -= tm_pocket(D)   # v0.16b [Ed]: relative sensor removed -> no pocket
    if D["kb_race"] != "chamfer": d += race_add(D)
    if D["kb_groove_h"] > 0: d -= seat_groove(D)
    d += hall.arm(D)
    d -= cyl(D["lip_id"] / 2, D["z_screen_cut"], 10, *panel_ctr(D))
    if D["screen_on_dial"]:   # v0.16 carrier magnet pocket + locating-pin hole in the dial shoulder
        md, mh = D["carr_mag"]; zh = D["z_holder0"]
        d -= cyl(md / 2 + D["dial_mag_press"] / 2, zh - D["carr_mag_gap"] - mh, mh + D["carr_mag_gap"] + 0.01, *D["carr_mag_xy"])
        d -= cyl(D["carr_pin"][0] / 2, zh - D["carr_pin"][1], D["carr_pin"][1] + 0.01, *D["carr_pin_xy"])
    d -= bend_pocket(D) if (D["screen_on_dial"] and D["lip_closed"]) else lip_slot(D)
    return {"control dial": d} | (tm_sensor(D) if D["rel_sensor"] else {})
