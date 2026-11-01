"""Idler pinions in the bottom ring. Both run on a Ø1.5 steel pin in the cradle (v0.16: idler 1 no longer shares the feel-motor shaft)."""
from build123d import *
from ...common.util import A, cyl, ext_gear, ring_phase

def idler(D):
    g = ext_gear(D, D["z_enc_pinion"], D["h_pin0"], D["pin_face"])
    hub = cyl(D["pinion_hub_d"] / 2, D["idler_floor"], D["idler_hub_len"])
    return (g + hub) - cyl(D["idler_bore"] / 2, D["idler_floor"], D["h_pin1"] - D["idler_floor"])

def build(D):
    out = {}
    hd, ht = D["pin_head"]
    for i, (a, (x, y)) in enumerate(zip(D["idler_angs"], D["idler_xy"]), 1):
        out[f"idler pinion {i}"] = Pos(x, y, 0) * Rot(0, 0, ring_phase(D, a)) * idler(D)
        out[f"idler pin {i}"] = cyl(D["pin_d"] / 2, 0, D["pin_z1"] - ht, x, y) + cyl(hd / 2, D["pin_z1"] - ht, ht, x, y)
    return out
