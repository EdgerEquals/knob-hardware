"""Idler pinions in the bottom ring. Both run on a Ø1.5 steel pin in the cradle.
v0.17 [Ed]: the idler farther from the 1220 is a compound gear — the small gear stays in the ring, a larger gear
on the same pin under the PCB is driven by the 716's catalogue pinion. No extra shaft."""
import math
from build123d import *
from ...common import util
from ...common.util import A, cyl, ext_gear, ext_herringbone, ext_mesh_spin, ring_phase, fresnel_cap
SRC_DEPS = [util]

def idler(D):
    g = ext_herringbone(D, D["z_enc_pinion"], D["h_pin0"], D["pin_face"], D["hb_mid"])
    hub = cyl(D["pinion_hub_d"] / 2, D["idler_floor"], D["idler_hub_len"])
    g = (g + hub) - cyl(D["idler_bore"] / 2, D["idler_floor"], D["h_pin1"] - D["idler_floor"])
    # underside of the tooth tips cleared for the Ø1.5 thrust balls, which sit just under this band
    tip = D["d_pin_tip"] / 2
    g -= cyl(tip + 0.05, D["h_pin0"] - 0.02, 0.55) - cyl(tip - 0.9, D["h_pin0"] - 0.04, 0.6)
    return g

def compound_gear(D):
    """Printed big gear on the compound idler: toothed rim, a 0.8 web, a short hub. Bore clears the existing pin."""
    z, m = D["fg_z_gear"], D["fg_mod"]
    Dm = dict(D); Dm["module"] = m
    face, z1 = D["fg_face"], D["fg_z_top"]
    zb = z1 - face
    root_r = max((z - 2.5) * m / 2, D["pin_d"])
    hub_r = D["pin_d"] / 2 + 0.9
    web_t = 0.8   # [A]
    web_z = zb + (face - web_t) / 2
    g = ext_gear(Dm, z, zb, face, dthick=-D["brass_backlash"] / 2, addendum=D["spur_addendum"], dedendum=D["spur_dedendum"])
    g -= cyl(root_r - 0.3, zb - 0.02, face + 0.04) - cyl(hub_r, zb - 0.04, face + 0.08)
    g += cyl(root_r - 0.2, web_z, web_t) - cyl(hub_r - 0.01, web_z - 0.02, web_t + 0.04)
    g -= cyl(D["pin_d"] / 2 + 0.05, zb - 0.05, face + 0.1)
    hub_h = zb - D["fg_z_bot"]
    if hub_h > 0.05:
        g += cyl(max(D["pinion_hub_d"] / 2, hub_r), D["fg_z_bot"], hub_h)
        g -= cyl(D["pin_d"] / 2 + 0.05, D["fg_z_bot"] - 0.02, hub_h + 0.04)
    return g

def build(D):
    out = {}
    hd, ht = D["pin_head"]
    ix, iy = D["fg_xy"]
    fx, fy = D["fm_xy"]
    alpha = math.degrees(math.atan2(fy - iy, fx - ix))
    spin = ext_mesh_spin(D["fg_z_gear"], D["fg_z_pin"], alpha, 0.0)
    for i, (a, (x, y)) in enumerate(zip(D["idler_angs"], D["idler_xy"]), 1):
        out[f"idler pinion {i}"] = Pos(x, y, 0) * Rot(0, 0, ring_phase(D, a)) * idler(D)
        root_r = D["z_enc_pinion"] * D["hb_mt"] / 2 - D["hb_dedendum"] * D["hb_mn"]
        out[f"idler pinion {i} cap"] = Pos(x, y, 0) * fresnel_cap(
            2 * (root_r - 0.25), D["pin_head"][0] + 2 * D["cap_fit_gap"], D["h_pin1"] + D["cap_seat_gap"],
            D["cap_t"], D["cap_rings"], D["cap_step_h"], D["cap_step_w"])
        pin = cyl(D["pin_d"] / 2, 0, D["pin_z1"] - ht, x, y) + cyl(hd / 2, D["pin_z1"] - ht, ht, x, y)
        if i - 1 == D["fg_idler"]:
            pin += cyl(D["pin_d"] / 2, D["fg_z_bot"], -D["fg_z_bot"], x, y)   # same pin, down through the PCB
            out[f"feel compound gear {D['fg_z_gear']}T"] = Pos(x, y, 0) * Rot(0, 0, spin) * compound_gear(D)
        out[f"idler pin {i}"] = pin
    return out
