"""main_knob own params + derive. Reads: interface + own + IMPORTS (control_dial dial-underside envelope)."""
import math

P = dict(
    # ---- knob [Ed/A] ----
    bot_face=3.0,   # [A] bottom internal ring face
    tm_press=0.0,   # [A] ring-magnet pocket radial oversize (0 = line-to-line, glued)
    # ---- v0.19b upper cap [Ed 2 Nov]: glass runs up under the dial; the cap is a thin dished web with a shoulder on the glass top ----
    glass_to_dial=True,   # [Ed] glass runs up under the dial lip (False = v0.19: glass stops at the hub-gear top, solid cone above)
    cap_top="chamfer",   # [Ed 2 Nov] glass right up to knob_run under the dial, top edges chamfered in and out; the cap's cone seats
                         # on the inner chamfer. "shoulder" = the earlier idea: glass a shoulder short, 2 mm cap shoulder on its top face
    cap_shoulder_t=2.0,   # [Ed] "shoulder" only: shoulder on the glass top face, same OD as the glass
    cap_shoulder_glue=0.05,   # [A] bond line between the shoulder and the glass top face
    seal_ring=True,   # [Ed 2 Nov] spill seal on the glass above the faceplate ring (case lab_ring_*)
    seal_type="oring",   # [Ed 2 Nov] "oring": silicone O-ring stretched on the glass as a drip ring, no contact with the case (no drag on
                         # the feel). "petg": bonded PETG ring with a skirt over the faceplate ring (clashed the joystick bezel and screen)
    seal_oring=(40.0, 1.0),   # [S] metric silicone O-ring ID x CS; ~5% stretch onto the Ø42 glass, held by the stretch plus a dab of RTV
    seal_oring_z_air=0.5,   # [A] O-ring underside above the faceplate ring top (also ~0.3 over the joystick bezel lip at rest)
    seal_glue=0.15,   # [A] radial bond on the measured glass OD (print the bore to the measured tube, like the caps)
    seal_wall=1.2,   # [A] skirt wall, 3 lines
    seal_top_t=1.2,   # [A] flange over the faceplate ring
    cap_shape="cone",   # [Ed 2 Nov] v0.21: cap top and underside are straight cones parallel to the dial ("dished": v0.20)
    cap_cone_t=3.5,   # [Ed 13:44] cap wall (normal) under the cone; underside flat at the hub-gear top until the cone rises off it
    cap_web_rim=1.5,   # [A] web thickness at the dial cup wall (2.2 at the hub gear); the flare out to the plug keeps it
)

IMPORTS = {"control_dial": ["z_hub0", "z_lip0", "z_web0", "dial_hub_od", "r_web", "gusset", "lip_fillet",   # the knob follows the dial underside
                            "kb_rc", "kb_zc", "kb_pcd", "kb_n", "kb_gap", "kb_c_dial", "kb_c_knob", "kb_r_collar",   # ball circle + 45° faces
                            "kb_seat_c_knob", "kb_groove_h",
                            "dial_shape", "cone_deg", "cone_under_r0", "cone_lip_r"],   # v0.21 cone top
            # seal shoulder: a skirt that drops over the case ring. Placed by the case after this
            # sub derives, so the solids here do not use it yet. bore radius lab_shoulder_r,
            # skirt from lab_shoulder_z0 up past lab_shoulder_z1 (the top of the ring).
            "case": ["lab_ring_r", "lab_ring_z0", "lab_ring_z1",
                     "lab_shoulder_r", "lab_shoulder_z0", "lab_shoulder_z1"]}
EXPORTS = ["h_bi1", "hb_mid"]   # ring top -> base_drive; herringbone apex -> the pinions


def derive(D):
    D["hb_mid"] = D["h_skirt0"] + D["bot_face"] / 2          # apex the two ring halves and the pinions share
    D["ring_root_d"] = 2 * D["hb_root_r"]
    D["ring_wall"] = D["cap_r"] - D["hb_root_r"]
    D["d_hg_root"] = (D["z_hub_gear"] - 2 * D["spur_dedendum"]) * D["hub_mod"]
    D["d_hg_tip"] = (D["z_hub_gear"] + 2 * D["spur_addendum"]) * D["hub_mod"]
    D["h_bi1"] = D["h_skirt0"] + D["bot_face"]
    D["sleeve_z0"] = D["h_bi1"]
    D["z_knob_top"] = D["z_lip0"] - D["knob_run"]
    if D["glass_to_dial"] and D["cap_top"] == "chamfer":   # glass top knob_run under the dial lip; cap cone on the inner chamfer
        D["sleeve_z1"] = D["z_knob_top"]
        ci, g = D["sleeve_top_cin"], D["sleeve_seat_glue"]
        D["cap_seat_r_top"] = D["sleeve_id"] / 2 + ci - g                       # cap cone meets the cap top (flush with the glass top)
        D["cap_seat_z_foot"] = D["sleeve_z1"] - ci - (D["sleeve_id"] / 2 - D["sleeve_spigot_r"]) + g   # cone meets the plug OD
        D["glass_top_flat"] = D["sleeve_wall"] - ci - D["sleeve_top_cout"]
    elif D["glass_to_dial"]:   # the shoulder top runs knob_run under the dial lip; the glass stops a shoulder + bond line below it
        D["cap_sh_z1"] = D["z_knob_top"]
        D["cap_sh_z0"] = D["cap_sh_z1"] - D["cap_shoulder_t"]
        D["sleeve_z1"] = D["cap_sh_z0"] - D["cap_shoulder_glue"]
    else:
        D["sleeve_z1"] = D["h_band1"]
    D["sleeve_len"] = D["sleeve_z1"] - D["sleeve_z0"]
    D["sleeve_insert"] = min(D["sleeve_wall"] * D["sleeve_insert_k"], 0.25 * D["sleeve_len"])
    # A 1 mm nylon hoop ties the teeth. It stops under the glass; the clear land outboard of it is the light path.
    D["sleeve_nylon_r"] = min(D["cap_r"] - D["cap_seat_gap"], D["hb_root_r"] + D["hb_wall_min"])
    D["sleeve_land_ri"] = D["sleeve_nylon_r"] + D["cap_seat_gap"]
    D["knob_hub_top"] = D["z_hub0"] - D["knob_run"]
    D["r_bore_hi"] = D["dial_hub_od"] / 2 + D["knob_run"]
    if D["kb_race"] == "chamfer":   # v0.15d: track in the knob's 45° top chamfer; the hub fills down to the dial tube (no annular gap)
        D["r_knob_bore"] = D["kb_rt"] + D["kb_clear"]                       # running bore round the plain dial tube
        D["r_chamfer0"] = D["kb_c_knob"] + D["knob_hub_top"]                # chamfer foot (r - z = c_knob at the hub top)
        D["race_wall"] = D["d_hg_root"] / 2 - D["r_knob_bore"]              # hub-gear root over the bore
    else:
        D["kb_r_up"] = D["kb_r_collar"] + D["kb_clear"]; D["kb_r_lo"] = D["kb_rt"] + D["kb_clear"]
        D["kb_zk0"], D["kb_zk1"] = D["kb_r_lo"] - D["kb_c_knob"], D["kb_r_up"] - D["kb_c_knob"]
        D["race_wall"] = D["d_hg_root"] / 2 - D["kb_r_up"]                 # hub-gear root over the knob race
    D["z_under_web"] = D["z_web0"] - D["knob_run"]
    if D["glass_to_dial"]:   # dished web: flat top under the dial web, bottom tapers 2.2 -> cap_web_rim, then a flare to the plug foot
        D["cap_r_s"] = D["r_web"] + D["knob_run"]                       # dial cup wall + running gap
        D["cap_z_rim_bot"] = D["z_under_web"] - D["cap_web_rim"]
        D["cap_z_plug0"] = D["sleeve_z1"] - D["sleeve_insert"]
        dz, dr = D["cap_z_plug0"] - D["cap_z_rim_bot"], D["sleeve_spigot_r"] - D["cap_r_s"]
        D["cap_flare_slope"] = math.degrees(math.atan2(dz, dr))
        D["cap_flare_wall"] = D["cap_web_rim"] * math.cos(math.radians(D["cap_flare_slope"]))   # normal wall of the flare
        D["cap_z_flare_top"] = D["z_under_web"] + (D["sleeve_lip_r"] - D["cap_r_s"]) * dz / dr
    if D["cap_shape"] == "cone" and D["glass_to_dial"] and D["cap_top"] == "chamfer" and D["kb_race"] == "chamfer":
        # v0.21 [Ed 2 Nov]: top = the race top, then one straight cone (parallel to the dial underside, knob_run under it) up to
        # the glass top; a flat ring flush with the glass top out to the chamfer seat. Underside flat at the hub-gear top (over the
        # 1220 pinion) until the parallel cone cap_cone_t below the top rises off it, then up to the plug in the bore.
        T = math.tan(math.radians(D["cone_deg"])); c = math.cos(math.radians(D["cone_deg"]))
        o = D["knob_run"] * math.sqrt(2)
        D["cap_cone_r0"] = D["dial_hub_od"] / 2 + D["gusset"] + o + (D["z_under_web"] - D["z_web0"])   # race top (cap side)
        D["cap_cone_r1"] = D["cap_cone_r0"] + (D["sleeve_z1"] - D["z_under_web"]) / T                # cone top meets the glass-top flat
        v = D["cap_cone_t"] / c
        under_z = lambda r: D["z_under_web"] + (r - D["cap_cone_r0"]) * T - v
        D["cap_flat_r1"] = D["cap_cone_r0"] + (D["h_band1"] - D["z_under_web"] + v) / T                # flat underside ends here
        D["cap_plug_z0"] = under_z(D["sleeve_spigot_r"])
        D["cap_plug_len"] = D["cap_seat_z_foot"] - D["cap_plug_z0"]
        # running gap to the dial underside cone (normal), and the neck: hub corner (hub-gear root, h_band1) to the cap top
        dial_z = lambda r: D["z_web0"] + (r - D["cone_under_r0"]) * T
        D["cap_cone_run"] = (dial_z(D["cap_cone_r0"]) - D["z_under_web"]) * c
        top = [(D["r_knob_bore"], D["knob_hub_top"]), (D["r_chamfer0"], D["knob_hub_top"]), (D["cap_cone_r0"], D["z_under_web"]),
               (D["cap_cone_r1"], D["sleeve_z1"])]
        def _seg(p, a, b):
            (px, py), (ax, ay), (bx, by) = p, a, b; dx, dy = bx - ax, by - ay
            t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
            return math.hypot(px - ax - t * dx, py - ay - t * dy)
        D["cap_neck"] = min(_seg((D["d_hg_root"] / 2, D["h_band1"]), top[i], top[i + 1]) for i in range(3))
    return D
