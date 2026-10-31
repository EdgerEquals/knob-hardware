"""base_drive LOCAL checks (own parts + interface values only)."""
from ..common.checks import Rows

def checks(D, parts):
    T = D["tgt"]; r = Rows("base_drive")
    r.row("1220 can vs dial tube", D["offset"] - D["can_r"] - D["dial_tube_od"] / 2, T["motor_dial_tube"])
    return r
