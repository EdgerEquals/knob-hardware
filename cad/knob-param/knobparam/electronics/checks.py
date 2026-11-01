"""electronics LOCAL checks (own parts + interface values only)."""
import itertools
from ..common.checks import Rows

def checks(D, parts):
    T = D["tgt"]; r = Rows("electronics")
    if D["hall_layout"] == "vernier":
        sens = [parts[n] for n in parts if n.startswith("hall sensor")]
        sg = min(a.distance_to(b) for a, b in itertools.combinations(sens, 2))
        r.row("Hall sensor body spacing on the PCB", sg, T["sensor_gap"], f"{D['hv_n']} sensors at pitch {D['hv_pitch']:g}: " + ", ".join(f"H{i + 1} {p.split()[0]}" for i, p in enumerate(D['hv_parts'])))
    pad = [parts[n] for n in parts if n.startswith("PCB rod pad")]
    if pad:
        r.row("rod VBUS pad (B.Cu) vs back-side parts / pads", pad[0].distance_to(parts["PCB back parts (Hall decouplers, J2)"]), D["rod_pad_clear"] - 0.01,
              f"pad Ø{2 * D['rod_pad_r']:.2f} (was the Ø4 washer footprint); nut clamps straight on it, no washer")
    return r
