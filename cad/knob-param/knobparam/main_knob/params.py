"""main_knob own params + derive. Reads: interface + own + IMPORTS (control_dial dial-underside envelope)."""
import math

P = dict(
    # ---- knob [Ed/A] ----
    bot_face=3.0,   # [A] bottom internal ring face
)

IMPORTS = {"control_dial": ["dial_hub_z0", "z_lip0", "z_web0", "dial_hub_od", "r_web", "gusset", "lip_fillet"]}   # the knob follows the dial underside
EXPORTS = []


def derive(D):
    m = D["module"]
    D["ring_root_d"] = (D["z_ring"] + 2.5) * m
    D["ring_wall"] = (D["knob_od"] - D["ring_root_d"]) / 2
    D["d_hg_root"] = (D["z_hub_gear"] - 2.5) * m; D["d_hg_tip"] = (D["z_hub_gear"] + 2) * m
    D["h_bi1"] = D["h_skirt0"] + D["bot_face"]
    D["kb_r_up"] = D["kb_r_collar"] + D["kb_clear"]; D["kb_r_lo"] = D["kb_rt"] + D["kb_clear"]
    D["kb_zk0"], D["kb_zk1"] = D["kb_r_lo"] - D["kb_c_knob"], D["kb_r_up"] - D["kb_c_knob"]
    D["knob_hub_top"] = D["dial_hub_z0"] - D["knob_run"]
    D["race_wall"] = D["d_hg_root"] / 2 - D["kb_r_up"]                     # hub-gear root over the knob race
    D["z_knob_top"] = D["z_lip0"] - D["knob_run"]
    D["z_under_web"] = D["z_web0"] - D["knob_run"]
    D["r_bore_hi"] = D["dial_hub_od"] / 2 + D["knob_run"]
    return D
