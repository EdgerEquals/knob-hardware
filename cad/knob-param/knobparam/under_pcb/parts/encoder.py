"""Encoder take-off at H2: F682ZZ x2, Ø2 shaft, 14T pinion in the bottom ring, plain disc + slotted rim behind the PCB,
Omron EE-SX1321 on the PCB back. All built in the encoder frame, moved to enc_xy."""
import math
from build123d import *
from ...common import util
from ...common.util import A, cyl, tube, ext_herringbone, ring_phase, fresnel_cap
SRC_DEPS = [util]   # ring_phase / herringbone live in util; the part hash has to follow them

def bearing(D, z_top):
    B = D["brg"]; z0 = z_top - B["B"]
    return tube(B["d"] / 2, B["D"] / 2, z0, B["B"]) + tube(B["d"] / 2, B["fd"] / 2, z_top - B["ft"], B["ft"])

def seat2(D):
    """v0.19: cup glued to the PCB back round H2. Floor under the downward flange, a counterbore for the flange,
    a bore for the body up to the board; the shaft passes the floor."""
    B = D["brg"]; z0, z1 = D["brg2_seat_z0"], D["z_pcb_back"] - 0.02
    zf = D["h_b2_bot"]                        # flange underside (flange faces down)
    cup = cyl(B["fd"] / 2 + D["brg2_seat_wall"], z0, z1 - z0)
    cup -= cyl(B["d"] / 2 + 0.6, z0 - 0.1, zf - z0 + 0.2)          # shaft through the floor
    cup -= cyl(B["fd"] / 2 + 0.05, zf, B["ft"] + 0.02)             # flange counterbore
    cup -= cyl(B["D"] / 2 + 0.02, zf + B["ft"], z1 - zf - B["ft"] + 0.1)   # body bore
    return cup

def pinion(D):
    g = ext_herringbone(D, D["z_enc_pinion"], D["h_pin0"], D["pin_face"], D["hb_mid"])
    hub = cyl(D["pinion_hub_d"] / 2, D["h_brg_top"], D["h_pin0"] - D["h_brg_top"])
    g = (g + hub) - cyl(D["enc_shaft_d"] / 2, D["h_brg_top"], D["h_pin1"] - D["h_brg_top"])
    pip_r = D["enc_pip_r"]
    g += cyl(pip_r, D["h_pin1"], D["enc_pip_h"]) - cyl(D["enc_shaft_d"] / 2 + 0.02, D["h_pin1"] - 0.02, D["enc_pip_h"] + 0.10)
    tip = D["d_pin_tip"] / 2
    g -= cyl(tip + 0.05, D["h_pin0"] - 0.02, 0.55) - cyl(tip - D["enc_tip_relief"], D["h_pin0"] - 0.04, 0.6)
    return g

def wheel(D):
    hd, hl = D["big_hub"]; zb, zt = D["h_big_bot"], D["h_big_top"]
    # v0.16 [Ed]: plain disc, no teeth (nothing ever meshed with the old big-gear teeth: the wheel is driven by its own
    # shaft from the 14T pinion in the bottom ring); the vertical slotted rim is all the EE-SX1321 needs
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
    # pins stop on the daughterboard (the near face of the sensor), not on the main PCB
    z_pin = z0 + bh
    for sy in (-1, 1):
        for k in (-1, 0, 1):
            b += Pos(k * S["term_pitch"], sy * (by / 2 + S["term_t"] / 2), z_pin - S["term_h"]) * Box(S["term_w"], S["term_t"], S["term_h"], align=A)
    return Pos(0, -D["sens_r"], 0) * b

def daughterboard(D):
    """Small riser under the EE-SX1321. Header + two standoffs stand it off the main PCB. KiCad for this board is not drawn."""
    S = D["sens"]; bx, by = S["body_y"], S["body_x"]; m = D["enc_db_clear"]
    z_near = D["z_sens_open"] + S["body_h"]          # sensor's PCB-side face, where the daughterboard's outer face is
    z0 = z_near
    board = Pos(0, -D["sens_r"], z0) * Box(bx + 2 * m, by + 2 * m, D["enc_db_t"], align=A)
    # header: 1×6 on the board centreline, pins from the board up to 0.05 short of the main PCB (solder pads, no clash)
    z_pin0 = z0 + D["enc_db_t"]
    z_pin1 = D["z_pcb_back"] - D["enc_pin_gap"]
    pins = []
    n = D["enc_header_n"]; pitch = D["enc_header_pitch"]
    z_tht1 = D["z_pcb_back"] + D["pcb_t"] + D.get("enc_tht_tail", 1.0)   # v0.24: through the main board to a tail past its front
    for k in range(n):
        tht = k in D.get("enc_header_tht", ())
        z1 = z_tht1 if tht else z_pin1
        pins.append(cyl(D["enc_header_d"] / 2, z_pin0, max(z1 - z_pin0, 0.2), (k - (n - 1) / 2) * pitch, -D["sens_r"]))
    # standoffs either side of the header, same span, stopped 0.05 short of the PCB (v0.17-v0.23; none since v0.24 [Ed 13:39])
    so = []
    if D.get("enc_standoffs", True):
        for s in (-1, 1):
            so.append(tube(D["enc_header_d"] / 2, D["enc_standoff_d"] / 2, z_pin0, max(z_pin1 - z_pin0, 0.2), 0, -D["sens_r"] + s * (by / 2 + m * 0.3)))
    return board, Compound(children=pins), (Compound(children=so) if so else None)

def build(D):
    T = Pos(*D["enc_xy"], 0)
    S = Rot(0, 0, D["sens_dir"] - 270.0)   # v0.19: sensor round the wheel (built at -Y, i.e. 270)
    board, header, stands = daughterboard(D)
    return {"encoder bearing 1 (cradle+PCB)": T * bearing(D, D["h_brg_top"]),
            "encoder pinion": T * Rot(0, 0, ring_phase(D, D["enc_ang"])) * pinion(D),
            "encoder pinion cap": T * fresnel_cap(
                2 * (D["z_enc_pinion"] * D["hb_mt"] / 2 - D["hb_dedendum"] * D["hb_mn"] - D["cap_root_inset"]),
                2 * D["enc_pip_r"] + 2 * D["cap_fit_gap"], D["h_pin1"] + D["cap_seat_gap"],
                D["cap_t"], D["cap_rings"], D["cap_step_h"], D["cap_step_w"]),
            "encoder shaft": T * cyl(D["enc_shaft_d"] / 2, D["enc_shaft_bot"], D["h_pin1"] - D["enc_shaft_bot"]),
            "encoder bearing 2" + (" (seat on the PCB back)" if D["brg2_on_pcb"] else " (back panel)"):
                T * (Rot(180, 0, 0) * Pos(0, 0, -D["h_b2_bot"] - D["h_b2_top"]) * bearing(D, D["h_b2_top"]) if D["brg2_on_pcb"] else bearing(D, D["h_b2_top"])),
            **({"encoder bearing 2 seat (printed, glued)": T * seat2(D)} if D["brg2_on_pcb"] else {}),
            "encoder disc + slotted rim": T * wheel(D),
            "encoder sensor EE-SX1321": T * S * sensor(D),
            "encoder daughterboard": T * S * board,
            "encoder header": T * S * header,
            **({"encoder standoff": T * S * stands} if stands is not None else {})}
