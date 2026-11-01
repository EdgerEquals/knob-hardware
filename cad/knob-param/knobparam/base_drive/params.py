"""base_drive own params + derive (cradle, brass tube, rod/sleeve/nuts, 1220 motor + pinion, idlers).
Reads: interface + own + IMPORTS (control_dial thrust-ball ring for the cradle groove)."""
import math

P = dict(
    # ---- 1220 motor [M] ----
    motor_pinion_face=3.0,   # [A]
    motor_bore_clear=0.05,   # [A]
    # ---- brass tube, rod ----
    brass_od=5.0,   # [S]/[A]
    brass_id=3.0,   # [S]/[A]
    brass_deburr=0.3,   # [S]/[A]
    glue_gap=0.1,   # [S]/[A]
    nut_s=3.2,   # [S]/[A]
    washer=(1.7, 4.0, 0.3),   # [S]/[A]
    use_washer=False,   # [Ed] v0.16: no washer - the bottom nut clamps straight onto the enlarged B.Cu rod pad
    sleeve=(1.7, 2.6),   # [S]/[A]
    rod_proud=0.5,   # [S]/[A]
    # ---- base cradle [A] ----
    cr_clear=0.5,
    pad_cb=(7.0, 0.6),
    motor_glue=0.1,
    motor_collar_wall=1.4,
    motor_collar_top=12.0,
    collar_trim=3.0,
    dowel_pad_d=9.0,
    pocket_clear=0.5,
    dial_tube_clear=0.5,
    pin_d=1.5,
    # ---- encoder take-off [A] ----
    idler_bore=1.6,
    idler_hub_len=0.5,
    pin_head=(3.5, 0.5),
    pin_run=0.1,
    # ---- v0.15: Hall vernier (arm down through the cradle slot, 5 magnets x 5 sensors, arcs crossing) ----
    hv_slot_clear=0.5,   # [A] bar to the cradle slot walls over travel
    # ---- v0.16 detents (top-loaded: ball, spring, grub) [Ed] ----
    det_bore_clear=0.1,   # [A] bore over the ball
    det_thread_d=2.0,   # [A] M2 grub screw thread (tapped into the boss)
    det_grub_len=2.0,   # [A] M2x2 cup-point grub
    det_grub_adj=0.6,   # [A] grub top below the boss top at nominal (adjust both ways)
    det_spring=(1.4, 3.0, 0.2),   # [A] compression spring OD, free length, wire (non-magnetic: phosphor bronze / 316)
    det_preload=0.8,   # [A] spring compression on the flat (sets the feel; grub adjusts it)
    det_boss_wall=0.8,   # [A] wall round the thread (2 lines)
    det_leg_w=3.0,   # [A] leg / bridge width
    det_leg_len=2.4,   # [A] leg radial length inboard of the fan
    # ---- v0.16 centring springs + cushions ----
    stop_len=2.0,   # [A] stop block length beside the lever
    stop_over=0.2,   # [A] stop block past the lever end
    sl_post_d=1.8,   # [A] spring anchor post
    # ---- v0.16 feel-motor open saddle clamp [Ed] ----
    fm_band_t=0.6,   # [A] band radial thickness (light load)
    fm_band_h=1.2,   # [A] band height (two narrow contact bands)
    fm_band_in=0.5,   # [A] band in from the grip ends
    fm_split=100.0,   # [A] split plane angle from the outboard direction (ears at the can sides, clear of the skirt)
    fm_ear=(1.6, 0.8),   # [A] ear radial length, tangential thickness (each half)
    fm_screw_d=0.9,   # [A] M1 self-tapping through the paired ears
    fm_spine_w=2.0,   # [A] seat spine width (rib to bands)
)

IMPORTS = {"control_dial": ["tb_pcd", "tb_groove_r", "tb_z_ball"],
           "main_knob": ["h_bi1"]}   # feel-motor can sits above the bottom ring
EXPORTS = []


def derive(D):
    R2D = math.degrees; M = D["motor"]
    D["h_motor_front"] = M["motor_len"] + M["gearbox_len"] + M["boss_len"]
    D["h_shaft_tip"] = D["h_motor_front"] + M["shaft_len"]
    D["h_pinion0"] = D["h_shaft_tip"] - D["motor_pinion_face"]
    # ---- cradle ----
    D["r_out"] = D["skirt_id"] / 2 - D["cr_clear"]
    D["cr_bore_d"] = D["brass_od"] + 2 * D["glue_gap"]
    D["motor_bore_d"] = M["body_d"] + 2 * D["motor_glue"]
    D["motor_collar_od"] = D["motor_bore_d"] + 2 * D["motor_collar_wall"]
    D["enc_pocket_d"] = D["d_pin_tip"] + 2 * D["pocket_clear"]
    D["dial_clear_d"] = D["dial_tube_od"] + 2 * D["dial_tube_clear"]
    # ---- idlers ----
    D["idler_floor"] = D["h_pin0"] - D["idler_hub_len"]
    D["idler_pocket_top"] = D["h_pin1"] + D["cr_clear"]
    D["pin_z1"] = D["h_pin1"] + D["pin_run"] + D["pin_head"][1]
    # ---- rod ----
    D["nut_seat_t"] = D["washer"][2] if D["use_washer"] else D["rod_pad_t"]
    D["z_rod_bot"] = D["z_pcb_back"] - D["nut_seat_t"] - D["nut_m"] - D["rod_proud"]
    # ---- Hall slot through the cradle plate (vernier) ----
    if D["hall_layout"] == "vernier":
        D["hv_slot_r0"] = D["hv_r"][0] - D["hv_pad_r"] - D["hv_slot_clear"]
        D["hv_slot_r1"] = D["skirt_id"] / 2 + 0.5
        dev = max(abs(a - D["ha_ang0"]) for a in D["hv_phi_m"] + D["hv_phi_s"])
        D["hv_slot_half"] = dev + D["travel_deg"] + R2D((D["hv_pad_r"] + D["hv_slot_clear"]) / D["hv_slot_r0"])
    # ---- v0.16 detents ----
    db = D["det_ball"]
    D["det_z0"] = D["fan_top"] + D["det_gap"]                               # boss underside
    D["det_z_ball"] = D["fan_top"] + db / 2                                 # ball centre riding on the flat wing top
    D["det_bore_d"] = db + D["det_bore_clear"]
    D["det_spring_inst"] = D["det_spring"][1] - D["det_preload"]
    D["det_z_grub0"] = D["det_z_ball"] + db / 2 + D["det_spring_inst"]
    D["det_z_thread0"] = D["det_z_grub0"] - D["det_grub_adj"]
    D["det_z1"] = D["det_z_grub0"] + D["det_grub_len"] + D["det_grub_adj"]
    D["det_boss_d"] = D["det_thread_d"] + 2 * D["det_boss_wall"]
    D["det_leg_r1"] = D["fan_r0"] - D["fan_clear"] - 0.1                   # leg stays inboard of the swept fan wing
    D["det_leg_r0"] = D["det_leg_r1"] - D["det_leg_len"]
    # ---- v0.16 centring springs: anchors tangential from the lever pin, one hook-to-hook length each way ----
    a = math.radians(D["sl_ang"]); L = D["sl_spring"][1]
    px, py = D["sl_pin_r"] * math.cos(a), D["sl_pin_r"] * math.sin(a); tx, ty = -math.sin(a), math.cos(a)
    D["sl_anchor_xy"] = [(px + L * tx, py + L * ty), (px - L * tx, py - L * ty)]
    # ---- feel motor mount (axial, pinion in the bottom-ring band, can above the ring) ----
    F = D["feel"]
    D["fm_z_can0"] = max(D["h_pin1"] + F["can_gap"], D["h_bi1"] + F["clear"])
    D["fm_z_can1"] = D["fm_z_can0"] + F["can_len"]
    D["fm_grip"] = F["clip_frac"] * F["can_len"]   # [A] collar length = this fraction of the can, from the shaft end
    # wall uses whatever skirt margin the placement left, capped at the 1220 collar wall
    D["fm_wall"] = min(D["motor_collar_wall"], D["skirt_id"] / 2 - (D["fm_cd"] + F["can_d"] / 2 + D["motor_glue"]) - F["clear"])
    D["fm_pocket_r"] = D["fm_tip"] + D["pocket_clear"]
    D["fm_rib_r0"] = D["dial_tube_od"] / 2 + F["clear"]                 # outside the dial tube
    D["fm_rib_r1"] = D["fm_cd"] - D["fm_pocket_r"] - D["motor_glue"]    # inside the pinion pocket
    D["fm_rib_w"] = F["can_d"] / 2                                      # [A] tangential width, half the can
    D["fm_z_rib1"] = D["fm_z_can0"] - D["motor_glue"]                    # glue gap under the clip foot
    D["fm_lead_r"] = F["pad_hole"] / 2 + D["motor_glue"]
    return D
