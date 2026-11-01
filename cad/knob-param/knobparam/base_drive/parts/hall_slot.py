"""base_drive: slot through the cradle plate for the dial's Hall arm (from the INTERFACE Hall layout + own hv_slot_clear)."""
import math
from build123d import *
from ...common.util import A, cyl, sector

def _vern(D): return D["hall_layout"] == "vernier"

def _bar_samples(D, n=8):
    """Centreline of the magnet bar (pads + the links between them)."""
    rs, ps = D["hv_r"], D["hv_phi_m"]
    pts = []
    for i, (r, a) in enumerate(zip(rs, ps)):
        if i:
            r0, a0 = rs[i - 1], ps[i - 1]
            for k in range(1, n):
                t = k / n
                pts.append((r0 + (r - r0) * t, a0 + (a - a0) * t))
        pts.append((r, a))
    return pts

def window(D):
    """v0.17 [Ed]: one smooth slot, an even clearance off the arm's swept envelope (not the stepped per-pad zig-zag)."""
    if not _vern(D): return sector(D["ha_win_r0"], D["ha_pad_r1"] + 3.0, D["ha_win_half"], -0.1, 10.0, D["ha_ang0"])
    pr, c, T = D["hv_pad_r"], D["hv_slot_clear"], D["travel_deg"]
    rad = pr + c
    w = None
    for r, a in _bar_samples(D):
        for th in (-T, 0.0, T):
            x = r * math.cos(math.radians(a + th)); y = r * math.sin(math.radians(a + th))
            q = cyl(rad, -0.1, D["plate_t"] + 0.3, x, y)
            w = q if w is None else w + q
    # sensors are fixed; open the slot over each body too so the bar's sweep is not the only cut
    for i, (r, a) in enumerate(zip(D["hv_r"], D["hv_phi_s"])):
        sl = D["hv_dims"][i][1]
        x, y = r * math.cos(math.radians(a)), r * math.sin(math.radians(a))
        w += cyl(max(sl, D["hv_dims"][i][0]) / 2 + c, -0.1, D["plate_t"] + 0.3, x, y)
    return w

