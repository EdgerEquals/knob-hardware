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
    peg_d_ratio=0.46,   # [A] locating peg diameter / plate thickness (~Ø1.6 on the 3.5 plate)
    peg_r_ratio=0.55,   # [A] peg radius / cradle radius
    peg_len_k=0.6,   # [A] peg engagement / PCB thickness
    peg_slot_k=0.5,   # [A] extra slot length / peg diameter (one hole is slotted)
    cradle_glue_k=0.03,   # [A] glue-line thickness / plate thickness
    cradle_land_k=0.35,   # [A] glue-land width / plate thickness
    cradle_foot_k=1.0,   # [A] future stiffener = this × cradle radius. The solid stays at r_out.
    cr_web_min=1.2,   # [Ed] v0.17: webs left round every support after the skinny-bridge cuts
    cr_bridge_fillet=0.5,   # [Ed] v0.17: fillet on those cuts (cut at the narrowest point)
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
    stop_len=0.8,   # [A] stop face thickness. The block sits above the ear, so the thickness grows away from the lever.
    stop_bias=0.1,   # [A] deg. Parks the stop face a hair out so the at-rest gap stays ≥ 0.3 mm and contact is still at ±travel..
    stop_over=0.2,   # [A] stop block past the lever end
    sl_post_d=1.8,   # [A] spring anchor post
    # ---- v0.16 feel-motor open saddle clamp [Ed] ----
    fm_band_t=0.6,   # [A] band radial thickness (light load)
    fm_band_h=1.2,   # [A] band height (two narrow contact bands)
    fm_band_in=0.5,   # [A] band in from the grip ends
    fm_split=100.0,   # [A] split plane angle from the outboard direction (ears at the can sides, clear of the skirt)
    fm_ear=(1.6, 0.8),   # [A] ear radial length, tangential thickness (each half)
    fm_screw_d=0.0,   # overwritten: can_d * saddle_k_small (M1.2 on the Ø7 feel motor)
    saddle_k_small=1.2 / 7.0,   # [A] screw / can, small motors (feel, and later the Risley / mirror hooks)
    saddle_k_main=1.4 / 12.0,   # [A] screw / can, the 1220
    saddle_ear_k=2.0,   # [Ed] ear thickness / screw diameter
    saddle_edge_k=1.0,   # [Ed] material past the hole / screw diameter
    saddle_later=("risley prism 1", "risley prism 2", "scanner mirror"),   # hooks only; not placed until the optics round
    fm_spine_w=2.0,   # [A] seat spine width (rib to bands)
    fm_pip_r=1.15,   # [A] cap boss on the feel pinion
    fm_pip_z0=-0.55,   # [A] boss start, below the tooth bottom
    fm_pip_h=0.55,   # [A] boss height
    fm_cap_inset=0.20,   # [A] cap OD inside the tooth root
    fg_web=0.8,   # [A] compound-gear web thickness
    fg_hub_wall=0.9,   # [A] compound hub radius past the pin
    fg_tip_relief=0.9,   # [A] idler tooth-tip underside opened this far in
    fg_web_pocket=0.3,   # [A] web pocket stops this far inside the tooth root
    fg_web_land=0.2,   # [A] web disk stops this far inside the tooth root
)

IMPORTS = {"control_dial": ["tb_on", "tb_pcd", "tb_groove_r", "tb_z_ball"],
           "main_knob": ["h_bi1", "hb_mid"]}   # feel-motor can sits above the bottom ring; herringbone apex
EXPORTS = []


def _place_pegs(D):
    """Two locating pegs on the cradle. One PCB hole is round, one is slotted along the radius."""
    peg_r = D["r_out"] * D["peg_r_ratio"]
    need = D["peg_d"] / 2 + D["cr_clear"]
    blocks = [(0.0, 0.0, D["brass_od"] / 2 + D["peg_d"]),
              (D["offset"], 0.0, D["motor_bore_d"] / 2 + D["peg_d"]),
              (*D["enc_xy"], D["brg"]["D"] / 2 + D["peg_d"]),
              (*D["fm_xy"], D["feel"]["can_d"] / 2)]
    for x, y in D["idler_xy"]:
        blocks.append((x, y, D["enc_pocket_d"] / 2 + D["peg_d"] / 2))
    for r, a in zip(D["hv_r"], D["hv_phi_s"]):
        blocks.append((r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), 2.0))
    def clear(a):
        x, y = peg_r * math.cos(math.radians(a)), peg_r * math.sin(math.radians(a))
        return min(math.hypot(x - bx, y - by) - br for bx, by, br in blocks)
    best = None
    for a in range(0, 360, 5):
        for b in range(a + 90, a + 270, 5):
            c = min(clear(a), clear(b % 360))
            if best is None or c > best[0]:
                best = (c, a, b % 360)
    _c, a, b = best
    def xy(ang):
        return (peg_r * math.cos(math.radians(ang)), peg_r * math.sin(math.radians(ang)))
    D["peg_xy"] = [xy(a), xy(b)]
    D["peg_ang"] = [a, b]
    D["peg_r"] = peg_r


def derive(D):
    R2D = math.degrees; M = D["motor"]
    D["fm_screw_d"] = D["feel"]["can_d"] * D["saddle_k_small"]
    D["main_screw_d"] = M["body_d"] * D["saddle_k_main"]
    D["h_motor_front"] = M["motor_len"] + M["gearbox_len"] + M["boss_len"]
    D["h_shaft_tip"] = D["h_motor_front"] + M["shaft_len"]
    D["h_pinion0"] = D["h_shaft_tip"] - D["motor_pinion_face"]
    # ---- cradle ----
    D["r_out"] = D["skirt_id"] / 2 - D["cr_clear"]
    D["cradle_foot_r"] = D["r_out"] * D["cradle_foot_k"]   # exported; not drawn past r_out
    D["cradle_glue"] = D["plate_t"] * D["cradle_glue_k"]
    D["cradle_land"] = D["plate_t"] * D["cradle_land_k"]
    D["peg_d"] = D["plate_t"] * D["peg_d_ratio"]
    D["peg_len"] = D["pcb_t"] * D["peg_len_k"]
    D["peg_slot"] = D["peg_d"] * (1.0 + D["peg_slot_k"])
    D["cr_bore_d"] = D["brass_od"] + 2 * D["glue_gap"]
    D["motor_bore_d"] = M["body_d"] + 2 * D["motor_glue"]
    D["motor_collar_od"] = D["motor_bore_d"] + 2 * D["motor_collar_wall"]
    D["enc_pocket_d"] = D["d_pin_tip"] + 2 * D["pocket_clear"]
    D["dial_clear_d"] = D["dial_tube_od"] + 2 * D["dial_tube_clear"]
    _place_pegs(D)
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
    # v0.17: foot stops below the moving ear; the bridge and boss stay above the ear (det_z0)
    ear_r0 = min(D["bt_rs"]) - D["bt_groove_r"] - D["fan_clear"]
    D["det_leg_r1"] = max(D["dial_tube_od"] / 2 + D["det_leg_len"], ear_r0 - D["fan_clear"])
    D["det_leg_r0"] = D["det_leg_r1"] - D["det_leg_len"]
    D["det_foot_z1"] = D["fan_z0"] - D["fan_clear"]
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
    D["fm_pocket_r"] = D["feel"]["shaft_d"] / 2 + D["motor_bore_clear"]   # v0.17: shaft only; the pinion is under the PCB
    D["fg_shaft_len"] = D["fm_z_can0"] - D["fg_z_bot"]                    # 716 shaft stick-out down through the catalogue pinion
    D["fm_rib_r0"] = D["dial_tube_od"] / 2 + F["clear"]                 # outside the dial tube
    D["fm_rib_r1"] = D["fm_cd"] - D["fm_pocket_r"] - D["motor_glue"]    # inside the pinion pocket
    D["fm_rib_w"] = F["can_d"] / 2                                      # [A] tangential width, half the can
    D["fm_z_rib1"] = D["fm_z_can0"] - D["motor_glue"]                    # glue gap under the clip foot
    D["fm_lead_r"] = F["pad_hole"] / 2 + D["motor_glue"]
    return D
