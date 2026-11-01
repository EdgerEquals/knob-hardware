"""main_knob own params + derive. Reads: interface + own + IMPORTS (control_dial dial-underside envelope)."""
import math

P = dict(
    # ---- knob [Ed/A] ----
    bot_face=3.0,   # [A] bottom internal ring face
    tm_press=0.0,   # [A] ring-magnet pocket radial oversize (0 = line-to-line, glued)
)

IMPORTS = {"control_dial": ["z_hub0", "z_lip0", "z_web0", "dial_hub_od", "r_web", "gusset", "lip_fillet",   # the knob follows the dial underside
                            "kb_rc", "kb_zc", "kb_pcd", "kb_n", "kb_gap", "kb_c_dial", "kb_c_knob", "kb_r_collar",   # ball circle + 45° faces
                            "kb_seat_c_knob", "kb_groove_h"]}
EXPORTS = ["h_bi1", "hb_mid"]   # ring top -> base_drive; herringbone apex -> the pinions


def derive(D):
    D["hb_mid"] = D["h_skirt0"] + D["bot_face"] / 2          # apex the two ring halves and the pinions share
    D["ring_root_d"] = 2 * D["hb_root_r"]
    D["ring_wall"] = D["cap_r"] - D["hb_root_r"]
    D["d_hg_root"] = (D["z_hub_gear"] - 2 * D["spur_dedendum"]) * D["hub_mod"]
    D["d_hg_tip"] = (D["z_hub_gear"] + 2 * D["spur_addendum"]) * D["hub_mod"]
    D["h_bi1"] = D["h_skirt0"] + D["bot_face"]
    D["sleeve_z0"] = D["h_bi1"]
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
    D["z_knob_top"] = D["z_lip0"] - D["knob_run"]
    D["z_under_web"] = D["z_web0"] - D["knob_run"]
    return D
