"""base_drive LOCAL checks (own parts + interface values only)."""
from ..common.checks import Rows

def checks(D, parts):
    T = D["tgt"]; r = Rows("base_drive")
    r.row("1220 can vs dial tube", D["offset"] - D["can_r"] - D["dial_tube_od"] / 2, T["motor_dial_tube"])
    m = D["module"]
    r.row("motor pinion tip vs skirt ID (radial)", D["skirt_id"] / 2 - D["offset"] - (D["z_pinion"] + 2) * m / 2, 1.0,
          f"{D['z_pinion']}T pinion / {D['z_hub_gear']}T hub gear, ratio {D['ratio_knob_motor']:.3f}")
    return r
