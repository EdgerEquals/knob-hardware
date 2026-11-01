"""optics: 12 VCSELs alternating with 12 RGB LEDs on one circle under the clear race carrier (envelopes only)."""
import math
from build123d import *

def build(D):
    if not D["optics_on"]: return {}
    out = {}; V, G = D["vcsel"], D["rgb"]; z0 = D["z_glass"] - 60   # [A] placeholder z until IMPORTS bring the carrier z
    for i in range(2 * D["rl_n"]):
        a = D["rl_phase_deg"] + i * D["rl_pitch_deg"]; p = V if i % 2 == 0 else G
        x, y = D["rl_r"] * math.cos(math.radians(a)), D["rl_r"] * math.sin(math.radians(a))
        out[f"{'VCSEL' if i % 2 == 0 else 'RGB'} {i // 2 + 1}"] = Pos(x, y, z0) * Rot(0, 0, a) * Box(p["x"], p["y"], p["h"], align=(Align.CENTER, Align.CENTER, Align.MIN))
    return out
