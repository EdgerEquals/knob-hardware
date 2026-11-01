"""base_drive LOCAL checks (own parts + interface values only)."""
from ..common.checks import Rows

def _one(parts, prefix):
    return parts[[n for n in parts if n.startswith(prefix)][0]]

def checks(D, parts):
    T = D["tgt"]; F = D["feel"]; r = Rows("base_drive")
    r.row("1220 can vs dial tube", D["offset"] - D["can_r"] - D["dial_tube_od"] / 2, T["motor_dial_tube"])
    m = D["module"]
    r.row("motor pinion tip vs skirt ID (radial)", D["skirt_id"] / 2 - D["offset"] - (D["z_pinion"] + 2) * m / 2, 1.0,
          f"{D['z_pinion']}T pinion / {D['z_hub_gear']}T hub gear, ratio {D['ratio_knob_motor']:.3f}")
    note = (f"{D['z_feel']}T at {D['fm_ang']:.1f}° into the {D['z_ring']}T ring, ratio {D['fm_ratio']:.2f}, "
            f"knob Ø{D['knob_od']:.2f}; " + ", ".join(f"{k} {v:.2f}" for k, v in sorted(D["fm_clear"].items(), key=lambda kv: kv[1])))
    r.row("feel placement (worst plan clearance)", min(D["fm_clear"].values()), F["clear"], note)
    r.row("feel clip wall", D["fm_wall"], F["clear"], f"collar grips {D['fm_grip']:.1f} of the Ø{F['can_d']:g}×{F['can_len']:g} can")
    r.row("feel mount rib (radial depth)", D["fm_rib_r1"] - D["fm_rib_r0"], F["clear"],
          f"r {D['fm_rib_r0']:.2f}-{D['fm_rib_r1']:.2f}, under the clip foot")
    can = _one(parts, "feel motor " + F["part"])
    pin = _one(parts, "feel motor pinion")
    r.row("feel can vs 1220 motor", can.distance_to(parts["motor"]), F["clear"])
    for i in (1, 2):
        r.row(f"feel pinion vs idler {i}", pin.distance_to(parts[f"idler pinion {i}"]), F["clear"])
    return r
