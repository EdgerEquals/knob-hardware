"""optics LOCAL checks (own parts + interface values only). Beam vs the whole stack is a CROSS check (assembly/checks.py
calls optics.beam_rows(D, parts, row) with every part)."""
import math
from ..common.checks import Rows
from .beam import risley_dir

def checks(D, parts):
    r = Rows("optics"); row = r.row
    if not D["optics_on"]: return r
    # no total internal reflection anywhere in the sweep (exact Snell)
    bad = sum(risley_dir(D, 360 * i / 36, 360 * j / 36) is None for i in range(36) for j in range(36))
    row("Risley: rays lost to total internal reflection", bad, 0, f"wedge {D['rp_wedge_deg']}°, n {D['rp_n']}", higher_ok=False)
    row("Risley wedge thin edge vs SLA minimum (mm)", D["rp_t_min"], D["print_wall_min"] * 0.8, "SLA 0.8 per the joystick process table")
    # alternating ring: emitter-to-emitter gap on the circle
    V, G = D["vcsel"], D["rgb"]; chord = 2 * D["rl_r"] * math.sin(math.radians(D["rl_pitch_deg"]) / 2)
    row("ring lights: gap between neighbouring VCSEL and RGB (mm)", chord - (V["y"] + G["y"]) / 2, 0.5, f"{2 * D['rl_n']} emitters on r {D['rl_r']:.2f}")
    return r
