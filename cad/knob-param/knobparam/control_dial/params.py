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
    dial_mag=(3.0, 1.0),   # [A] Ø3×1 N52 under the TMAG5273
    dial_mag_press=0.05,   # [A] Ø3×1 N52 under the TMAG5273
    # ---- thrust bearing under the dial ----
    tb_ball_d=1.0,
    tb_pcd=6.8,
    tb_groove_r=0.55,
    tb_ball_up=0.3,
    tb_pocket_d=1.1,
    tb_web_min=0.65,
    tb_cage=(5.3, 8.6, 0.4),   # [A] cage ID, OD, thickness
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
    carrier_run=0.3,   # [A] rotating carrier plate above the fixed adapter cup
    adapter_cup=True,   # [A] fixed adapter cup on the tube (False = none: adapter board sits on the brass tube end, clamped by the rod nut)
    b2b_flip=True,   # [A] B2B on the far side of the axis from J1 -> diametral FPC strap through the axis
    strap_t=0.12,   # [A] 2-layer PI flex, clear over the rod/nut, % dynamic limit
    strap_clear=0.3,   # [A] 2-layer PI flex, clear over the rod/nut, % dynamic limit
    strap_lines=14,   # [A] 2-layer PI flex, clear over the rod/nut, % dynamic limit
    strap_strain_max=0.3,   # [A] 2-layer PI flex, clear over the rod/nut, % dynamic limit
    dial_spring=0.4,   # [A] centring spring rate N*mm/deg (torque = k*theta)
    # ---- v0.15: Hall vernier (arm down through the cradle slot, 5 magnets x 5 sensors, arcs crossing) ----
    hv_bar_top=5.9,   # [A] arm spoke top (= v0.14 arm top)
    hv_spoke_w=3.0,   # [A] spoke width; spoke bottom this far above the thrust balls / cage
    hv_spoke_clear=0.3,   # [A] spoke width; spoke bottom this far above the thrust balls / cage
)

IMPORTS = {"electronics": ["adapter_d", "adapter_fps", "adapter_env"]}
EXPORTS = ["z_hub0", "z_lip0", "z_web0", "dial_hub_od", "r_web", "gusset", "lip_fillet",   # -> main_knob
           "tb_pcd", "tb_groove_r", "tb_z_ball",                                                     # -> base_drive (cradle groove)
           "kb_rc", "kb_zc", "kb_pcd", "kb_n", "kb_gap", "kb_c_dial", "kb_c_knob", "kb_r_collar",   # -> main_knob (ball circle + faces)
           "kb_seat_c_knob", "kb_groove_h"]                                                  # -> base_drive (cradle groove)


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
    D["z_well"] = D["z_cup0"] - D["knob_run"]
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
    D["scr_reach"] = reach - D["scr_off"]                                  # outermost screen point from the dial axis (tail side)
    D["scr_far"] = D["scr_r"] + D["scr_off"]                               # panel edge, far side
    D["tail_ang"] = 180.0                                                  # [A] FPC exit toward -X (away from the motor)
    if D["screen_on_dial"]:   # bonded: lip ID centred on the panel (eccentric by scr_off), no running gap
        D["lip_id"] = 2 * (D["scr_r"] + D["lip_bond_gap"]); D["lip_ctr_off"] = D["scr_off"]
    else:
        D["lip_id"] = 2 * (D["scr_far"] + D["run_gap"]); D["lip_ctr_off"] = 0.0
    D["lip_wall"] = D["R"] - (D["lip_id"] / 2 + D["lip_ctr_off"])          # thinnest lip (far side)
    D["lip_wall_near"] = D["R"] - (D["lip_id"] / 2 - D["lip_ctr_off"])
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
    # ---- hub magnet under the TMAG5273 (U3 on the adapter board) ----
    u3 = D["adapter_fps"]["U3"]; D["mag_xy"] = (u3[1], u3[2])
    D["z_mag1"] = D["z_well"]; D["z_mag0"] = D["z_mag1"] - D["dial_mag"][1]
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
    return D
