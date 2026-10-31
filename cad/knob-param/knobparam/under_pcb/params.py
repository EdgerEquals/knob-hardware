"""under_pcb own params + derive (encoder pinion/shaft/bearings, big gear + slotted rim, EE-SX1131, feel motor + clip,
back-panel depth). Reads: interface + own + IMPORTS (electronics board outline)."""
import math

P = dict(
    # ---- main PCB [K] ----
    pcb_margin=0.5,   # [A] big gear tip to the board edge
    # ---- encoder take-off [A] ----
    enc_shaft_d=2.0,
    sens=dict(body_x=5.0, body_y=4.0, body_h=4.0, slot_w=2.0, slot_d=2.8, axis_from_open=1.0, ap_w=0.3, ap_h=1.0, ap_pitch=0.8, term_w=1.0, term_t=0.2, term_h=1.0, term_pitch=1.4),   # [S] Omron EE-SX1131
    n_win=119,
    rim_t=1.2,
    rim_in=0.6,
    gear_sensor_gap=0.3,
    big_face=1.5,
    big_hub=(5.0, 1.5),
    wheel_ring_in=0.4,
    n_spokes=6,
    spoke_w=2.4,
    boss_r=3.0,
    back_panel=25.0,   # [A] PCB back to the back panel inner face (bearing 2 seat)
    panel_clear=1.0,   # [A] lowest part to the back panel
    # ---- feel motor [A] ----
    feel=dict(part="716 coreless", can_d=7.0, can_len=16.0, end_boss=1.0, shaft_d=1.0, can_gap=0.3, clip_od=9.0, clip_len=3.4, gearhead_len=7.5),
)

IMPORTS = {"electronics": ["pcb_w", "pcb_above", "pcb_below"]}
EXPORTS = ["d_big_tip"]   # -> electronics (J2 pads below the wheel)


def derive(D):
    m = D["module"]; B = D["brg"]
    D["h_brg_top"] = D["cr_floor"] + B["ft"]; D["h_brg_bot"] = D["h_brg_top"] - B["B"]
    sn = D["sens"]
    D["win_pitch"] = sn["ap_pitch"] / 0.75; D["sens_r"] = D["n_win"] * D["win_pitch"] / (2 * math.pi)
    D["rim_r0"], D["rim_r1"] = D["sens_r"] - D["rim_t"] / 2, D["sens_r"] + D["rim_t"] / 2
    D["z_sens_open"] = D["z_pcb_back"] - sn["body_h"]
    D["z_slot_bot"] = D["z_sens_open"] + sn["slot_d"]
    D["z_axis"] = D["z_sens_open"] + sn["axis_from_open"]
    D["rim_top"] = D["z_slot_bot"] - D["rim_in"]
    D["h_big_top"] = D["z_sens_open"] - D["gear_sensor_gap"]; D["h_big_bot"] = D["h_big_top"] - D["big_face"]
    D["h_hub_bot"] = D["h_big_bot"] - D["big_hub"][1]
    D["win_z0"], D["win_z1"] = D["z_axis"] - sn["ap_h"] / 2 - 0.6, D["z_axis"] + sn["ap_h"] / 2 + 0.3
    D["h_panel"] = D["z_pcb_back"] - D["back_panel"]
    D["h_b2_top"] = D["h_panel"] + B["ft"]; D["h_b2_bot"] = D["h_b2_top"] - B["B"]
    ex, ey = D["enc_xy"]
    r_avail = min(ex + D["pcb_w"] / 2, D["pcb_w"] / 2 - ex, ey + D["pcb_below"], D["pcb_above"] - ey) - D["pcb_margin"]
    D["z_big"] = int(math.floor(2 * r_avail / m + 1e-9)) - 2
    D["d_big_tip"] = (D["z_big"] + 2) * m
    D["wheel_ring_r0"] = D["rim_r0"] - D["wheel_ring_in"]
    D["counts_knob"] = 4 * D["n_win"] * D["z_ring"] / D["z_enc_pinion"]
    D["sens_xy"] = (ex, ey - D["sens_r"])
    # ---- feel motor ----
    F = D["feel"]
    D["fm_z_can_top"] = D["z_pcb_back"] - F["can_gap"]; D["fm_z_can_bot"] = D["fm_z_can_top"] - F["can_len"]
    D["fm_z_end"] = D["fm_z_can_bot"] - F["end_boss"]
    D["depth_direct"] = -D["fm_z_end"] + D["panel_clear"] + D["z_pcb_back"]
    D["depth_geared"] = D["depth_direct"] + F["gearhead_len"]
    D["depth_encoder"] = -(D["h_hub_bot"] - 0.5 - B["ft"]) - D["pcb_t"]
    D["depth_min"] = max(D["depth_direct"], D["depth_encoder"])
    return D
