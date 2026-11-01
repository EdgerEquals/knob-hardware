"""Encoder take-off at H2: F682ZZ x2, Ø2 shaft, 14T pinion in the bottom ring, plain disc + slotted rim behind the PCB,
Omron EE-SX1131 on the PCB back. All built in the encoder frame, moved to enc_xy."""
import math
from build123d import *
from ...common.util import A, cyl, tube, ext_gear, ring_phase

def bearing(D, z_top):
    B = D["brg"]; z0 = z_top - B["B"]
    return tube(B["d"] / 2, B["D"] / 2, z0, B["B"]) + tube(B["d"] / 2, B["fd"] / 2, z_top - B["ft"], B["ft"])

def pinion(D):
    g = ext_gear(D, D["z_enc_pinion"], D["h_pin0"], D["pin_face"])
    hub = cyl(D["pinion_hub_d"] / 2, D["h_brg_top"], D["h_pin0"] - D["h_brg_top"])
    return (g + hub) - cyl(D["enc_shaft_d"] / 2, D["h_brg_top"], D["h_pin1"] - D["h_brg_top"])

def wheel(D):
    hd, hl = D["big_hub"]; zb, zt = D["h_big_bot"], D["h_big_top"]
    # v0.16 [Ed]: plain disc, no teeth (nothing ever meshed with the old big-gear teeth: the wheel is driven by its own
    # shaft from the 14T pinion in the bottom ring); the vertical slotted rim is all the EE-SX1131 needs
    g = cyl(D["disc_r"], zb, D["big_face"]) + cyl(hd / 2, zb - hl, hl)
    g -= cyl(D["enc_shaft_d"] / 2, zb - hl, D["big_face"] + hl)
    h = zt - zb + 0.2
    lt = cyl(D["wheel_ring_r0"], zb - 0.1, h) - cyl(D["boss_r"], zb - 0.1, h)
    for k in range(D["n_spokes"]):
        lt -= Rot(0, 0, 360.0 * k / D["n_spokes"]) * Pos(D["wheel_ring_r0"] / 2 + 1.0, 0, zb - 0.1) * Box(D["wheel_ring_r0"] + 2.0, D["spoke_w"], h, align=A)
    g -= lt
    hr = D["rim_top"] - zt
    rim = tube(D["rim_r0"], D["rim_r1"], zt, hr)
    ww = D["win_pitch"] / 2
    cut = Box(ww, D["rim_t"] + 1.0, D["win_z1"] - D["win_z0"], align=A)
    wins = [Rot(0, 0, 360.0 * k / D["n_win"] - 90.0) * Pos(D["sens_r"], 0, D["win_z0"]) * cut for k in range(D["n_win"])]
    return g + (rim - Compound(children=wins))

def sensor(D):
    S = D["sens"]; bx, by, bh = S["body_y"], S["body_x"], S["body_h"]; z0 = D["z_sens_open"]
    b = Pos(0, 0, z0) * Box(bx, by, bh, align=A) - Pos(0, 0, z0) * Box(bx, S["slot_w"], S["slot_d"], align=A)
    for sy in (-1, 1):
        for k in (-1, 0, 1):
            b += Pos(k * S["term_pitch"], sy * (by / 2 + S["term_t"] / 2), D["z_pcb_back"] - S["term_h"]) * Box(S["term_w"], S["term_t"], S["term_h"], align=A)
    return Pos(0, -D["sens_r"], 0) * b

def build(D):
    T = Pos(*D["enc_xy"], 0)
    return {"encoder bearing 1 (cradle+PCB)": T * bearing(D, D["h_brg_top"]),
            "encoder pinion": T * Rot(0, 0, ring_phase(D, D["enc_ang"])) * pinion(D),
            "encoder shaft": T * cyl(D["enc_shaft_d"] / 2, D["h_b2_bot"], D["h_pin1"] - D["h_b2_bot"]),
            "encoder bearing 2 (back panel)": T * bearing(D, D["h_b2_top"]),
            "encoder disc + slotted rim": T * wheel(D),
            "encoder sensor EE-SX1131": T * sensor(D)}
