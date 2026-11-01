"""under_pcb own params + derive (encoder pinion/shaft/bearings, big gear + slotted rim, EE-SX1321, back-panel depth).
The 716 feel motor is a base_drive part as of v0.16. Reads: interface + own + IMPORTS (electronics board outline)."""
import math

P = dict(
    # ---- main PCB [K] ----
    pcb_margin=0.5,   # [A] big gear tip to the board edge
    # ---- encoder take-off [A] ----
    enc_shaft_d=2.0,
    sens=dict(body_x=5.1, body_y=4.0, body_h=4.0, slot_w=2.0, slot_d=2.8, axis_from_open=1.0, ap_w=0.3, ap_h=1.0, ap_pitch=0.8, term_w=1.0, term_t=0.2, term_h=1.0, term_pitch=1.4),   # [S] Omron EE-SX1321 datasheet p3 (2026-11-01; was EE-SX1131 5.0 wide): 1.55 arm + 2.0 slot + 1.55 arm, slot 2.8 deep, axis 1.0 below the open face, 2 apertures 0.3 x 1.0 along the slot, terminal pitch 1.4
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
    back_panel=25.0,   # [A] v0.18 only: PCB back to the back panel inner face (bearing 2 seat)
    sens_dir=180.0,   # [A] v0.19: sensor direction from the wheel centre, mechanism frame (180 + mech_rot -90 = panel up, under the joystick). v0.18: 270
    brg2_on_pcb=True,   # [Ed] 2 Nov: the back screens sit behind the wheel, so bearing 2 moves up to a printed seat on the PCB back
    brg2_seat_wall=1.2,   # [A] printed seat wall round bearing 2 (glued to the PCB back round H2)
    brg2_seat_floor=0.6,   # [A] seat floor under bearing 2
    # ---- v0.17 encoder daughterboard [Ed]: the EE-SX1321 moves off the main PCB so its slot meets the rim at the new depth ----
    enc_db_t=0.8,   # [A] daughterboard thickness
    enc_db_clear=0.6,   # [A] board margin past the sensor body
    enc_header_pitch=2.54,   # [S] pin header pitch
    enc_header_n=6,   # [S] EE-SX1321 has 6 pins; the header stands in for them on the riser
    enc_header_d=0.64,   # [A] header pin diameter
    enc_standoff_d=2.5,   # [A] printed standoff OD
    enc_pip_r=1.35,   # [A] cap boss on the pinion top face
    enc_pip_h=0.60,   # [A] that boss height
    enc_tip_relief=0.9,   # [A] tooth-tip underside opened this far in, clear of the thrust balls
    enc_pin_gap=0.05,   # [A] header and standoffs stop this short of the main PCB
)

IMPORTS = {"electronics": ["pcb_w", "pcb_above", "pcb_below"],
           "main_knob": ["hb_mid"]}
EXPORTS = ["d_big_tip", "z_rear_min"]   # -> electronics (J2 pads below the wheel)


def derive(D):
    B = D["brg"]
    D["h_brg_top"] = D["cr_floor"] + B["ft"]; D["h_brg_bot"] = D["h_brg_top"] - B["B"]
    sn = D["sens"]
    D["win_pitch"] = sn["ap_pitch"] / 0.75; D["sens_r"] = D["n_win"] * D["win_pitch"] / (2 * math.pi)
    D["rim_r0"], D["rim_r1"] = D["sens_r"] - D["rim_t"] / 2, D["sens_r"] + D["rim_t"] / 2
    # nominal (sensor on the main PCB) then drop so the rim clears the compound gear where they overlap in plan
    z_open0 = D["z_pcb_back"] - sn["body_h"]
    rim0 = z_open0 + sn["slot_d"] - D["rim_in"]
    ix, iy = D["fg_xy"]; ex, ey = D["enc_xy"]
    dist = math.hypot(ix - ex, iy - ey)
    overlap = dist < D["sens_r"] + D["rim_t"] / 2 + D["fg_tip"] + D["fg_clear"]
    drop = max(0.0, rim0 - (D["fg_z_bot"] - D["fg_clear"])) if overlap else 0.0
    # the riser is at least the daughterboard; a shorter drop still gets the board
    D["enc_drop"] = max(drop, D["enc_db_t"])
    D["z_sens_open"] = z_open0 - D["enc_drop"]
    D["z_slot_bot"] = D["z_sens_open"] + sn["slot_d"]
    D["z_axis"] = D["z_sens_open"] + sn["axis_from_open"]
    D["rim_top"] = D["z_slot_bot"] - D["rim_in"]
    D["enc_standoff_h"] = D["enc_drop"] - D["enc_db_t"]
    D["h_big_top"] = D["z_sens_open"] - D["gear_sensor_gap"]; D["h_big_bot"] = D["h_big_top"] - D["big_face"]
    D["h_hub_bot"] = D["h_big_bot"] - D["big_hub"][1]
    D["win_z0"], D["win_z1"] = D["z_axis"] - sn["ap_h"] / 2 - 0.6, D["z_axis"] + sn["ap_h"] / 2 + 0.3
    D["h_panel"] = D["z_pcb_back"] - D["back_panel"]
    if D["brg2_on_pcb"]:
        # bearing 2 straight under bearing 1, flange down, in a seat on the PCB back; the shaft stops in the disc hub
        D["h_b2_top"] = D["z_pcb_back"]; D["h_b2_bot"] = D["h_b2_top"] - B["B"]
        D["brg2_seat_z0"] = D["h_b2_bot"] - D["brg2_seat_floor"]
        D["enc_shaft_bot"] = D["h_hub_bot"]
    else:
        D["h_b2_top"] = D["h_panel"] + B["ft"]; D["h_b2_bot"] = D["h_b2_top"] - B["B"]
        D["brg2_seat_z0"] = D["h_b2_bot"]
        D["enc_shaft_bot"] = D["h_b2_bot"]
    # deepest under-PCB part, for the case cover depth (v0.19)
    D["z_rear_min"] = min(D["h_hub_bot"], D["enc_shaft_bot"], D["brg2_seat_z0"], D["z_sens_open"] - D["enc_db_t"])
    ex, ey = D["enc_xy"]
    r_avail = min(ex + D["pcb_w"] / 2, D["pcb_w"] / 2 - ex, ey + D["pcb_below"], D["pcb_above"] - ey) - D["pcb_margin"]
    D["disc_r"] = D["rim_r1"]                                            # plain disc out to the slotted rim (no teeth)
    D["z_big"] = 0
    D["d_big_tip"] = 2 * D["disc_r"]                                     # the disc is the envelope; the old phantom tooth count followed the spur module
    D["wheel_ring_r0"] = D["rim_r0"] - D["wheel_ring_in"]
    D["counts_knob"] = 4 * D["n_win"] * D["z_ring"] / D["z_enc_pinion"]
    D["sens_xy"] = (ex + D["sens_r"] * math.cos(math.radians(D["sens_dir"])), ey + D["sens_r"] * math.sin(math.radians(D["sens_dir"])))
    return D
