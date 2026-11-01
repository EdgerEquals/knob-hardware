"""base_drive: slot through the cradle plate for the dial's Hall arm (from the INTERFACE Hall layout + own hv_slot_clear)."""
import math
from build123d import *
from ...common.util import A, cyl, sector

def _vern(D): return D["hall_layout"] == "vernier"

def window(D):   # through the cradle plate: per-pad swept sectors (+-travel, + clearance), merged
    if not _vern(D): return sector(D["ha_win_r0"], D["ha_pad_r1"] + 3.0, D["ha_win_half"], -0.1, 10.0, D["ha_ang0"])
    pr, c, T = D["hv_pad_r"], D["hv_slot_clear"], D["travel_deg"]; w = None
    rs = D["hv_r"]
    for i, (r, am, as_) in enumerate(zip(rs, D["hv_phi_m"], D["hv_phi_s"])):
        r0 = r - pr - c; r1 = (r + pr + c) if i < len(rs) - 1 else D["hv_slot_r1"]
        half_m = T + math.degrees(math.asin(min((pr + c) / r0, 1)))
        sl = D["hv_dims"][i][1]   # v0.16b: tangential length per sensor (TMAG5273 in the middle)
        lo = min(am - half_m, as_ - math.degrees((sl / 2 + c) / r0))
        hi = max(am + half_m, as_ + math.degrees((sl / 2 + c) / r0))
        q = sector(r0, r1, (hi - lo) / 2, -0.1, 10.0, (hi + lo) / 2)
        w = q if w is None else w + q
    return w

