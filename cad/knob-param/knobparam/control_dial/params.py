"""control_dial own params + derive (dial, thrust balls, hub magnet, Hall arm + magnets, screen, carrier, FPC strap, fixed
adapter cup). Reads: interface + own + IMPORTS (electronics adapter-board envelope)."""
import math

P = dict(
    # ---- knob top bearing: opposed 45 deg cones [Ed] ----
    kb_seat_depth=0.10,   # [A] "tube" race only: seating groove depth into the dial cone (0 = plain cone, v0.14)
    kb_ball_tube=0.1,   # [A] "tube" race only: ball to the plain tube
    kb_zc_tube=41.45,   # [A] "tube" race only: ball centre height
    # ---- control dial [Ed/A] ----
    lip_t=4.0,   # [Ed] about 4 at the top
    dial_hub_wall=2.0,   # [A]
    web_in_t=2.0,   # [A]
    well_clear=0.2,   # [A]
    gusset=1.5,   # [A]
    lip_fillet=1.0,   # [A]
    dial_hub_z0=43.6,   # [A] "tube" race only: hub bottom (chamfer race: derived, see dial_hub_below_gusset)
    dial_hub_below_gusset=0.0,   # [Ed] v0.15d: hub straight face below the 45° gusset (0 = hub bottom at the gusset start; v0.15c had 1.4)
    dial_bore_floor=0.5,   # [A] dial material kept under the cup-boss bore, above the hub bottom
    dial_collar_d=9.2,   # [A] "tube" race only (v0.15c chamfer race: no collar)
    dial_collar_h=0.3,   # [A] "tube" race only
    r_web=14.0,   # [A] web/lip junction radius
    boss_bore_clear=0.15,   # [A] dial bore round the holder boss
    cup_clear=0.2,   # [A] dial round the holder cup
    dial_screen_gap=0.3,   # [A] dial below the holder plate
    dial_mag_press=0.05,   # [A] press-fit oversize for magnet pockets
    tm_board=(4.0, 6.0, 0.6),   # [A] dial sensor board: radial, tangential, thickness (TMAG5273 face-down on its underside)
    tm_pocket_clear=0.6,   # [Ed/A] generous room round the sensor board for easy assembly (drops in from the top, carrier off)
    # ---- thrust bearing under the dial ----
    tb_on=False,   # [Ed] 2 Nov: no bearing under the dial tube, just an air gap. The 45° race on the knob carries the dial and the
                   # adapter board stops it lifting; a second axial support here only fought the tolerance stack.
                   # The tb_* numbers below stay as the height datum (dial tube end, Hall spoke) so nothing else moves.
    dial_air_min=0.5,   # [A] tube end over the cradle top with no thrust bearing: room for the stack (printed hub, glued glass, race)
    tb_ball_d=1.0,
    tb_pcd=6.8,
    tb_groove_r=0.55,
    tb_ball_up=0.3,
    tb_pocket_d=1.1,
    tb_web_min=0.65,
    tb_cage=(5.3, 8.58, 0.4),   # [A] cage ID, OD, thickness. OD 8.58 leaves the inner Hall pad 0.30 mm clear (8.60 was 0.295).
    # ---- screen holder + adapter ----
    hold_z0_socket=5.0,   # [A] socket engagement on the tube
    socket_d=5.2,   # [A]
    boss_d=7.0,   # [A]
    hold_od=21.92,   # [A]
    floor_t=0.8,   # [A]
    well_wall=0.8,   # [A]
    hold_step=51.8,   # [A]
    adapter_clear=0.2,   # [K]/[A] (cord room over the nut [Ed])
    # ---- screen [S] (table below) ----
    run_gap=0.15,   # [A] panel -> rotating dial lip
    edge_margin=0.0,   # [A] outermost screen point to the knob OD (>= 0: nothing past the OD)
    offset_step=0.005,   # [A] screen offset rounded up to this (v0.14: 0.05)
    fpc_clear=0.15,   # [A] folded FPC corners inside the lip ID
    cof_inset=2.0,   # [A] COF bend band = ledge width - 2*cof_inset
    b2b_at="J1",   # [A] B2B placed over this adapter connector (jumper straight down onto it)
    jumper_t=0.15,   # [A]
    # ---- v0.15: screen turns with the dial ----
    screen_on_dial=True,   # [Ed] panel bonded to a carrier bonded on the dial (False = v0.14 fixed holder + running gap)
    lip_bond_gap=0.0,   # [A] panel edge -> lip ID (bonded, no running gap; lip ID centred on the panel)
    # ---- v0.16 screen carrier cartridge [Ed]: locating pin sets its angle, a small magnet in the dial pulls a steel disc in the
    # carrier down; lift off with a suction cup for service (then undo the centre bolt and the whole stack comes apart) ----
    carr_r=15.0,   # [A] pin + magnet radius on the dial shoulder (outside the fold window, far from the dial TMAG5273)
    carr_mag_ang=90.0,   # [A] magnet angle (opposite side of the fold from the pin)
    carr_pin_ang=270.0,   # [A] locating-pin angle
    carr_mag=(3.0, 1.0),   # [Ed] v0.17: Ø3×1 N52 in the dial shoulder (the base), at 90°, opposite the Ø1 pin
    carr_mate=(3.0, 1.0),   # [Ed] v0.17: Ø3×1 N52 in the carrier, facing the base magnet (attracting)
    carr_steel=(2.0, 0.5),   # unused in v0.17 (v0.16 was a steel disc pulled by a Ø2×1 magnet)
    carr_pin=(1.0, 1.5, 0.8),   # [A] Ø1 steel dowel: pressed depth in the dial, engagement in the carrier
    carr_mag_gap=0.0,   # [A] carrier magnet top below the dial shoulder (0 = flush, touching the steel disc)
    carr_pin_clear=0.05,   # [A] carrier hole over the pin
    carr_stray_max=0.02,   # [A] carrier-magnet field at the dial TMAG5273 / range (dipole estimate)
    lip_closed=True,   # [Ed] v0.16: lip is a full ring (COF bend in a blind pocket inside the lip, no through-slot)
    carrier_run=0.3,   # [A] rotating carrier plate above the fixed adapter cup
    adapter_cup=False,   # [Ed] v0.16: brown cup removed - the centre bolt clamps the stack, the adapter board is the dial up-stop (was True) fixed adapter cup on the tube (False = none: adapter board sits on the brass tube end, clamped by the rod nut)
    b2b_flip=True,   # [A] B2B on the far side of the axis from J1 -> diametral FPC strap through the axis
    strap_t=0.12,   # [A] 2-layer PI flex, clear over the rod/nut, % dynamic limit
    strap_clear=0.3,   # [A] 2-layer PI flex, clear over the rod/nut, % dynamic limit
    strap_lines=14,   # [A] 2-layer PI flex, clear over the rod/nut, % dynamic limit
    strap_strain_max=0.3,   # [A] 2-layer PI flex, clear over the rod/nut, % dynamic limit
    dial_spring=0.4,   # [A] centring spring rate N*mm/deg (torque = k*theta)
    # ---- v0.15: Hall vernier (arm down through the cradle slot, 5 magnets x 5 sensors, arcs crossing) ----
    fan_on=True,   # [Ed] v0.16 fan arm + lever (False = v0.15 bar only)
    hv_spoke_w=3.0,   # [A] spoke width; spoke bottom this far above the thrust balls / cage
    hv_spoke_clear=0.31,   # [A] spoke bottom above the thrust balls / cage. 0.30 left the solid 0.295 mm clear.
    # ---- v0.21 [Ed 2 Nov]: the single spring-ball detent moves OUT to the end of the arm, on the arc (more room for the three
    # dimples at 0 and ±det_deg), and the arm rides on three small ball tracks with alternating big and small balls.
    # Hard limit: the Hall bar's slot takes the cradle plate under the middle of the arc and the pinions bound its ends, so
    # under the arc itself there is no room for a ball train that rolls ±travel/2. The tracks hug the slot on both sides at
    # the largest radius the pinion tips allow. arm_det="ear" rebuilds v0.20 (inboard ear, one two-row track). ----
    arm_det="arc",   # [Ed] "arc" (v0.21) or "ear" (v0.20)
    ad_off=0.0,   # [A] detent angle from the Hall arm centreline (0 = on the rib line, between the two outer tracks)
    ad_r_frac=0.5,   # [A] detent radius across the fan band (0 = fan_r0, 1 = fan_r1)
    ad_land_edge=0.4,   # [A] raised land past the ball footprint: radially, and along the arc at the hard stop
    ad_land_min=0.75,   # [A] flat land wanted between neighbouring dimple rims (the ball radius: it rides flat between latches)
    tk_tracks=((-1, 0), (-1, 1), (1, 0)),   # [A] (side of the Hall slot: -1 encoder side, +1 lever side; row 0 outer, 1 next in).
                                            # The lever side has room for one row only (the 1220 collar), so the third goes in on the encoder side.
    tk_n_big=2,   # [A] load balls per track (Ø bt_ball, [Ed] Ø1); one separator between each pair: big, small, big
    tk_small=0.8,   # [A] separator ball Ø. Stock 0.8 (1/32" = 0.794 also fits). Non-magnetic (316, ZrO2 or ruby): the Hall magnets are ~2 mm away.
    tk_seat_min=0.05,   # [A] separator below both races: (big - small)/2 at least this (the load balls' seat gap)
    tk_land=0.4,   # [A] arm web / plate land round each groove (radial) and past each groove end (arc)
    tk_bar_clear=1.3,   # [A] groove end to the Hall bar's swept edge, along the arc (base_drive slot clearance 0.5 + land; the slot edge slants, so 1.0 left only 0.21 of plate)
    tk_row_pitch=1.5,   # [A] radial pitch of two rows on one side (groove 1.1 + land 0.4)
    tk_end_clear=0.10,   # [A] groove end past the end ball at full travel, mm of arc (same as det_stop_clear)
)

IMPORTS = {"electronics": ["adapter_d", "adapter_fps", "adapter_env"]}
EXPORTS = ["z_hub0", "z_lip0", "z_web0", "dial_hub_od", "r_web", "gusset", "lip_fillet",   # -> main_knob
           "tb_on", "tb_pcd", "tb_groove_r", "tb_z_ball",                                                   # -> base_drive (cradle groove)
           "kb_rc", "kb_zc", "kb_pcd", "kb_n", "kb_gap", "kb_c_dial", "kb_c_knob", "kb_r_collar",   # -> main_knob (ball circle + faces)
           "kb_seat_c_knob", "kb_groove_h",                                                  # -> base_drive (cradle groove)
           "arm_det", "ad_r", "ad_ang", "ad_z_land", "tk", "tk_webs"]                       # -> base_drive (v0.21 arc detent + ball tracks)


def derive(D):
    S = D["S"]
    # ---- holder / adapter cup heights ----
    D["z_cup0"] = D["z_floor"] - D["floor_t"]                              # 48.80
    D["pocket_lo_d"] = D["adapter_d"] + 2 * D["adapter_clear"]             # 15.90
    D["well_od"] = D["pocket_lo_d"] + 2 * D["well_wall"]                   # 17.50
    # ---- control dial ----
    D["z_lip0"] = D["z_top"] - D["lip_t"]
    D["r_cup"] = D["hold_od"] / 2 + D["cup_clear"]
    D["z_web1"] = D["hold_step"] - D["knob_run"]
    D["r_well"] = D["well_od"] / 2 + D["well_clear"]
    D["z_well"] = D["z_cup0"] - D["knob_run"]                              # web datum (unchanged from v0.15d: race + hub stay put)
    # v0.16 no cup: the well floor rises to carrier_run under the adapter board, which is clamped by the rod nut -> the board is the
    # dial (and, through the 45° race, the knob) up-stop; centre bolt clamps everything [Ed]
    D["z_well_top"] = D["z_well"] if D["adapter_cup"] else D["z_floor"] - D["carrier_run"]
    D["dial_lift"] = D["z_floor"] - D["z_well_top"]                        # free lift of the dial before it meets the board
    D["z_web0"] = D["z_well"] - D["web_in_t"]
    D["dial_bore_d"] = D["boss_d"] + 2 * D["boss_bore_clear"]
    D["dial_hub_od"] = D["dial_bore_d"] + 2 * D["dial_hub_wall"]
    if D["kb_race"] == "chamfer":   # v0.15d: hub bottom at the gusset start (no straight hub face under the race)
        D["z_hub0"] = D["z_web0"] - D["gusset"] - D["dial_hub_below_gusset"]
        D["hold_z0"] = max(D["z_floor"] - D["hold_z0_socket"], D["z_hub0"] + D["knob_run"] + D["dial_bore_floor"])   # boss stays above the hub
    else:
        D["z_hub0"] = D["dial_hub_z0"]
        D["hold_z0"] = D["z_floor"] - D["hold_z0_socket"]                  # 44.60
    D["hold_socket_len"] = D["z_floor"] - D["hold_z0"]                     # actual socket engagement on the tube
    D["z_bore0"] = D["hold_z0"] - D["knob_run"]
    D["z_hubf"] = D["z_hub0"] + D["dial_collar_h"]
    # ---- thrust bearing ----
    D["tb_z_ball"] = D["plate_t"] + D["tb_ball_up"]
    D["dial_z_base"] = D["tb_z_ball"] + D["tb_ball_up"]
    D["tb_n"] = int(math.pi * D["tb_pcd"] / (D["tb_pocket_d"] + D["tb_web_min"]))
    D["tb_cage_z0"] = D["tb_z_ball"] - D["tb_cage"][2] / 2
    # ---- knob top bearing: ball circle + track grooves (opposed 45° faces) ----
    kR = D["kb_ball_d"] / 2; k = kR / math.sqrt(2); rho_s = D["kb_seat_r"]; e = rho_s - kR; s2 = math.sqrt(2)
    if D["kb_race"] == "chamfer":   # v0.15c [Ed]: balls in the middle of the 45° gusset face under the dial web, track in both faces
        rh, g, run = D["dial_hub_od"] / 2, D["gusset"], D["knob_run"]
        f = D["kb_race_at"]; d = run / 2                                    # ball centre midway between the faces (normal gap = knob_run)
        D["kb_rc"] = rh + f * g + d / s2; D["kb_zc"] = D["z_web0"] - g + f * g - d / s2
        D["kb_c_dial"] = rh - (D["z_web0"] - g)                             # dial face: r - z = c (normal (1,-1)/√2 points to the knob)
        D["kb_c_knob"] = D["kb_c_dial"] + run * s2                          # knob chamfer = dial face offset by knob_run
        D["kb_groove_h"] = rho_s - (d + e)                                  # groove depth below each face (ball touches both groove bottoms)
        D["kb_r_collar"] = None
        D["kb_face_len"] = g * s2
        D["kb_land"] = min(f, 1 - f) * D["kb_face_len"] - math.sqrt(max(rho_s ** 2 - (d + e) ** 2, 0))   # groove rim to the face end
        dface = d                                                           # ball centre to each face
    else:   # v0.15 cone race at the dial tube
        D["kb_rc"] = D["kb_rt"] + kR + D["kb_ball_tube"]; D["kb_zc"] = D["kb_zc_tube"]
        D["kb_c_dial"] = D["kb_rc"] - D["kb_zc"] - 2 * k; D["kb_c_knob"] = D["kb_rc"] - D["kb_zc"] + 2 * k
        D["kb_r_collar"] = D["kb_rc"] + kR + 0.15 - D["kb_clear"]
        D["kb_groove_h"] = D["kb_seat_depth"]
        dface = kR - D["kb_seat_depth"]
    D["kb_pcd"] = 2 * D["kb_rc"]
    D["kb_n"] = int(math.pi / math.asin((D["kb_ball_d"] + D["kb_play"]) / D["kb_pcd"]))
    D["kb_gap"] = D["kb_pcd"] * math.sin(math.pi / D["kb_n"]) - D["kb_ball_d"]
    zc = D["kb_zc"]; h = D["kb_groove_h"]
    D["kb_c_dial_face"] = D["kb_c_dial"] + (h * s2 if D["kb_race"] != "chamfer" else 0.0)
    D["kb_seat_c"] = (D["kb_rc"] + e / s2, zc - e / s2)                    # dial groove centre: beyond the ball centre, away from the dial
    D["kb_seat_c_knob"] = (D["kb_rc"] - e / s2, zc + e / s2)               # knob groove centre (chamfer race): mirror image
    D["kb_seat_w"] = math.sqrt(max(rho_s ** 2 - (dface + e) ** 2, 0)) if h > 0 else 0.0   # groove half-width at the face
    D["kb_ball_cap_w"] = math.sqrt(max(kR ** 2 - dface ** 2, 0)) if h > 0 else 0.0       # ball half-chord at the face
    D["kb_seat_contact"] = (D["kb_rc"] - k, zc + k)                         # 45° contact point on the dial (groove bottom)
    if D["kb_race"] != "chamfer":
        D["kb_zd0"], D["kb_zd1"] = D["kb_rt"] - D["kb_c_dial_face"], D["kb_r_collar"] - D["kb_c_dial_face"]
    # ---- screen (offset away from the FPC exit so nothing pokes past the knob OD) ----
    D["scr_r"] = S["od"] / 2
    reach = S["r_edge"] + (0 if S["rigid"] else S["bend"])
    # exact: points on an arc of radius rho (panel centre), |y| <= yh, stay inside R - margin when offset o >= rho*cos - sqrt(Rm^2 - y^2)
    Rm = D["R"] - D["edge_margin"]; D["cof_half"] = S["ledge_w"] / 2 - D["cof_inset"]
    cand = [(S["r_edge"], S["ledge_w"] / 2)] + ([] if S["rigid"] else [(S["r_edge"] + S["bend"], D["cof_half"])])
    raw = max([0.0] + [math.sqrt(rho * rho - yh * yh) - math.sqrt(max(Rm * Rm - yh * yh, 0)) for rho, yh in cand])
    D["scr_off"] = 0.0 if raw == 0 else math.ceil(raw / D["offset_step"] - 1e-9) * D["offset_step"]
    if D["screen_on_dial"] and D["lip_closed"]:   # v0.16 [Ed]: closed lip ring - offset balances far wall vs the wall outside the bend pocket
        D["scr_off"] = D["scr_off_opt"]
    D["scr_reach"] = reach - D["scr_off"]                                  # outermost screen point from the dial axis (tail side)
    D["scr_far"] = D["scr_r"] + D["scr_off"]                               # panel edge, far side
    D["tail_ang"] = 180.0                                                  # [A] FPC exit toward -X (away from the motor)
    if D["screen_on_dial"]:   # bonded: lip ID centred on the panel (eccentric by scr_off), no running gap
        D["lip_id"] = 2 * (D["scr_r"] + D["lip_bond_gap"]); D["lip_ctr_off"] = D["scr_off"]
    else:
        D["lip_id"] = 2 * (D["scr_far"] + D["run_gap"]); D["lip_ctr_off"] = 0.0
    D["lip_wall"] = D["R"] - (D["lip_id"] / 2 + D["lip_ctr_off"])          # thinnest lip (far side)
    D["lip_wall_near"] = D["R"] - (D["lip_id"] / 2 - D["lip_ctr_off"])
    # v0.16 wall outside the ledge + COF-bend pocket (same rule as interface.bend_reach; pocket = band + bend_clear)
    pts = [(S["r_edge"], S["ledge_w"] / 2)] + ([] if S["rigid"] else [(S["r_edge"] + S["bend"], -D["cof_half"] + 2 * D["cof_half"] * i / 48) for i in range(49)])
    D["bend_reach_ax"] = max(math.hypot(math.sqrt(max(r * r - y * y, 0)) - D["scr_off"], y) for r, y in pts)
    D["lip_wall_bend"] = D["R"] - D["bend_reach_ax"] - D["bend_clear"]
    D["z_back"] = D["z_top"] - S["t"]
    D["z_fpc0"] = D["z_back"] - S["fold"][2]
    D["z_screen_cut"] = D["z_holder0"] - D["dial_screen_gap"]
    if D["screen_on_dial"]:
        D["z_screen_cut"] = D["z_holder0"]                                 # carrier bonded on the dial shoulder
        D["lip_slot_w"] = S["ledge_w"] + 1.0                               # no travel widening: panel turns with the lip
        W = S["fold"][1]; rlim = D["lip_id"] / 2 - D["fpc_clear"]
        D["fold_x_outer"] = math.sqrt(max(rlim ** 2 - (W / 2) ** 2, 0)) - D["scr_off"]   # lip ID is panel-centred
        D["z_cup_top"] = D["z_holder0"] - D["carrier_run"]                 # fixed adapter cup stops under the carrier
    else:
        D["lip_slot_w"] = S["ledge_w"] + 2 * (D["R"] * math.radians(D["travel_deg"])) + 1.0
        W = S["fold"][1]; rlim = D["lip_id"] / 2 - D["fpc_clear"]           # fold corners inside the lip ID
        D["fold_x_outer"] = math.sqrt(max(rlim ** 2 - (W / 2) ** 2, 0))      # from the axis toward the tail
        D["z_cup_top"] = D["z_holder0"]
    ad = D["adapter_fps"][D["b2b_at"]]
    D["j1_xy"] = (ad[1], ad[2])
    D["b2b_xy"] = (-ad[1], -ad[2]) if (D["screen_on_dial"] and D["b2b_flip"]) else (ad[1], ad[2])
    # ---- v0.16 dial sensor (TMAG5273 face-down on a small board in a pocket through the dial web) over the knob ring magnet ----
    D["tm_z_floor"] = D["z_web0"] + D["tm_floor"]                          # package face rests on the pocket floor
    D["tm_z_elem"] = D["tm_z_floor"] + D["tm_pkg"][3]
    D["tm_z_board0"] = D["tm_z_floor"] + D["tm_pkg"][2]
    D["tm_gap"] = D["tm_z_elem"] - (D["z_web0"] - D["knob_run"])           # element -> ring top (knob under-web face)
    D["tm_gap_min"] = D["tm_gap"] - D["dial_lift"]
    # ---- v0.16 carrier retention ----
    pol = lambda r, a: (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
    D["carr_mag_xy"] = pol(D["carr_r"], D["carr_mag_ang"]); D["carr_pin_xy"] = pol(D["carr_r"], D["carr_pin_ang"])
    def _dip(d, h):
        return D["hv_br"] / (4e-7 * math.pi) * math.pi * (d / 2e3) ** 2 * (h / 1e3)   # A·m²
    md_, mh_ = D["carr_mag"]; m_dip = _dip(md_, mh_) + _dip(*D["carr_mate"])   # attracting pair, moments add [Ed]
    if D["rel_sensor"]:
        d_u3 = math.dist(D["carr_mag_xy"], D["tm_xy"]) / 1e3                               # to the dial TMAG5273 (co-rotating)
        D["carr_stray_to"], D["carr_stray_rng"] = "dial TMAG5273", D["tm_range_mt"]
    else:   # v0.16b: nearest 3D sensor is the Hall-row TMAG5273 on the PCB (fixed); carrier magnet z ~ holder base
        k = D["hv_mid"]["idx"]; r, a = D["hv_r"][k], math.radians(D["hv_phi_s"][k])
        d_u3 = math.dist((*D["carr_mag_xy"], D["z_holder0"] - D["carr_mag"][1] / 2), (r * math.cos(a), r * math.sin(a), D["hv_mid"]["elem_z"])) / 1e3
        D["carr_stray_to"], D["carr_stray_rng"] = "Hall-row TMAG5273 (H3)", D["hv_mid"]["range_mt"]
    D["carr_stray_mt"] = 1e3 * 1e-7 * 2 * m_dip / d_u3 ** 3                                  # on-axis dipole (worst case)

    # ---- v0.15 diametral FPC strap (rotating B2B end <-> stationary J1 end) ----
    b2b_h = S["b2b"][2] if S["b2b"] else 0.0
    D["z_b2b0"] = D["z_fpc0"] - b2b_h
    tallest = max(D["z_rod_top"], D["z_board_top"] + max(h for (_, _, h) in D["adapter_env"].values()))
    D["strap_z0"] = tallest + D["strap_clear"]; D["strap_z1"] = D["z_b2b0"]
    D["strap_L"] = math.hypot(D["b2b_xy"][0] - D["j1_xy"][0], D["b2b_xy"][1] - D["j1_xy"][1])
    th = math.radians(D["travel_deg"])
    D["strap_kappa"] = th / D["strap_L"] if D["strap_L"] > 0 else 0.0     # clamped-clamped, ends on a diameter: uniform curvature
    D["strap_R"] = 1 / D["strap_kappa"] if D["strap_kappa"] else float("inf")
    D["strap_strain_pct"] = 100 * D["strap_t"] / 2 * D["strap_kappa"]
    D["strap_end_move"] = math.hypot(*D["b2b_xy"]) * th
    # ---- Hall arm (vernier) ----
    if D["hall_layout"] == "vernier":
        D["hv_bar_z0"] = D["hv_z_mag0"]
        D["hv_spoke_z0"] = max(D["tb_z_ball"] + D["tb_ball_d"] / 2, D["tb_cage_z0"] + D["tb_cage"][2]) + D["hv_spoke_clear"]
        # v0.17 rib: over the thrust cage the bottom stays at the spoke; past the cage OD + a web it drops to ha_rib_z_low
        D["ha_rib_z_cage"] = D["hv_spoke_z0"]
        D["ha_rib_r_step"] = D["tb_cage"][1] / 2 + D["tb_web_min"]   # 4.95 at the v0.16 cage (Ø8.6 + 0.65 web)
    _arc_mech(D)
    return D


def bar_samples(D, n=8):
    """Centreline of the Hall magnet bar (pads + the links between them), as (r, angle) points. Same sampling as the
    cradle slot (base_drive hall_slot), which cuts hv_pad_r + its own clearance round these points swept ±travel."""
    rs, ps = D["hv_r"], D["hv_phi_m"]
    pts = []
    for i, (r, a) in enumerate(zip(rs, ps)):
        if i:
            r0, a0 = rs[i - 1], ps[i - 1]
            pts += [(r0 + (r - r0) * k / n, a0 + (a - a0) * k / n) for k in range(1, n)]
        pts.append((r, a))
    return pts


def bar_edge(D, r, side):
    """Angle where the Hall bar's swept envelope (pads radius hv_pad_r, ±travel) starts at radius r, on side -1 (low angles,
    toward the encoder) or +1 (high angles, toward the lever). None if the bar does not reach this radius."""
    pr, T = D["hv_pad_r"], D["travel_deg"]
    best = None
    for rs, a in bar_samples(D):
        if abs(r - rs) >= pr:
            continue
        c = (r * r + rs * rs - pr * pr) / (2 * r * rs)
        e = a + side * (T + math.degrees(math.acos(max(-1.0, min(1.0, c)))))
        best = e if best is None else (min(best, e) if side < 0 else max(best, e))
    return best


def _arc_mech(D):
    """v0.21 [Ed 2 Nov]: one spring-ball detent on the arc at the arm's end, three ball tracks (big, small, big) under the arm.
    Everything is in the mechanism frame; angles in degrees. The tracks roll θ/2 against both races, so each groove spans the
    train plus ±travel/2 plus the end clearance; the groove end on the slot side sits tk_bar_clear off the bar's swept edge."""
    R2D = math.degrees
    on = D["arm_det"] == "arc" and D["hall_layout"] == "vernier" and D["fan_on"]
    D["ad_r"] = D["ad_ang"] = D["ad_z_land"] = None
    D["tk"], D["tk_webs"] = [], []
    if not on:
        return
    T = D["travel_deg"]; rb = D["det_ball"] / 2
    # ---- detent on the arc: a raised land on the fan, flush with the rib top, so the ball path can cross the rib ----
    D["ad_r"] = D["fan_r0"] + D["ad_r_frac"] * (D["fan_r1"] - D["fan_r0"])
    D["ad_ang"] = D["ha_ang0"] + D["ad_off"]
    D["ad_z_land"] = D["ha_rib_z_top"]
    D["ad_land_r0"] = D["ad_r"] - rb - D["ad_land_edge"]
    D["ad_land_r1"] = D["ad_r"] + rb + D["ad_land_edge"]
    D["ad_land_half"] = T + R2D((rb + D["ad_land_edge"]) / D["ad_r"])
    D["ad_rim"] = math.sqrt(max(rb * rb - (rb - D["det_dimple"]) ** 2, 0.0))          # dimple rim half-width on the land top
    D["ad_pitch"] = 2 * D["ad_r"] * math.sin(math.radians(D["det_deg"]) / 2)          # chord between neighbouring dimples
    D["ad_flat"] = D["ad_pitch"] - 2 * D["ad_rim"]
    D["ad_stop_off"] = D["ad_r"] * math.radians(T - D["det_deg"])                    # ball off the end-dimple centre at the hard stop
    # ---- ball tracks ----
    b, s, nb = D["bt_ball"], D["tk_small"], D["tk_n_big"]
    g, land = D["bt_groove_r"], D["tk_land"]
    # web edge keeps the pinion-tip gap (+0.02 so the swept check does not sit on its target)
    r_top = D["enc_cd"] - D["d_pin_tip"] / 2 - D["tgt"]["hall_vs_pinions"] - 0.02 - g - land
    seq = [b if i % 2 == 0 else s for i in range(2 * nb - 1)]
    tk = []
    for k, (side, row) in enumerate(D["tk_tracks"], 1):
        r = r_top - row * D["tk_row_pitch"]
        step = R2D(2 * math.asin((b + s) / 2 / (2 * r)))                                # big-to-small centre angle (touching)
        offs = [(i - (len(seq) - 1) / 2) * step for i in range(len(seq))]
        half = T / 2 + offs[-1] + R2D((b / 2 + D["tk_end_clear"]) / r)                   # groove half-span, the same in both races
        edge = bar_edge(D, r, side)
        ang = edge + side * (R2D(D["tk_bar_clear"] / r) + half)
        land_a = R2D(land / r)
        lo, hi = (ang - half - land_a, D["ha_ang0"]) if side < 0 else (D["ha_ang0"], ang + half + land_a)
        tk.append(dict(k=k, side=side, row=row, r=r, ang=ang, half=half, offs=offs, dias=seq, edge=edge))
        D["tk_webs"].append((r - g - land, r + g + land, lo, hi))   # arm web carrying this track's groove, joined to the rib
    D["tk"] = tk
    D["tk_r_top"] = r_top
    D["tk_web_z0"], D["tk_web_z1"] = D["fan_z0"], D["fan_top"]
    lo_side = [w for w, t in zip(D["tk_webs"], tk) if t["side"] < 0]
    # one spoke from the dial tube to the free end of the encoder-side web (the lever-side web hangs off the rib and the lever)
    if lo_side:
        r0 = min(w[0] for w in lo_side)
        D["tk_spoke_ang"] = min(w[2] for w in lo_side) + R2D(D["sl_w"] / 2 / r0)
        D["tk_spoke_r1"] = r0 + 0.01
    else:
        D["tk_spoke_ang"] = D["tk_spoke_r1"] = None
