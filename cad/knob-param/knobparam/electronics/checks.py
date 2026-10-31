"""electronics LOCAL checks (own parts + interface values only)."""
import itertools
from ..common.checks import Rows

def checks(D, parts):
    T = D["tgt"]; r = Rows("electronics")
    if D["hall_layout"] == "vernier":
        sens = [parts[n] for n in parts if n.startswith("hall sensor")]
        sg = min(a.distance_to(b) for a, b in itertools.combinations(sens, 2))
        r.row("Hall sensor body spacing on the PCB", sg, T["sensor_gap"], f"{D['hv_n']} × {D['hv_sensor']['part']} at pitch {D['hv_pitch']:g}")
    return r
