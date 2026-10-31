"""electronics: Hall sensor row on the main-PCB front (vernier: hv_n x TMAG5253 X2SON on the mirror arc; v0.14: 2 x DRV5055),
positions from the INTERFACE Hall layout."""
import math
from build123d import *
from ...common.util import A, cyl

def _vern(D): return D["hall_layout"] == "vernier"

def _pt(r, a): return r * math.cos(math.radians(a)), r * math.sin(math.radians(a))

def sensors(D):
    s = D["hv_sensor"]; out = []
    for r, a in zip(D["hv_r"], D["hv_phi_s"]):
        x, y = _pt(r, a)
        out.append(Pos(x, y, 0) * Rot(0, 0, a) * Box(s["w"], s["l"], s["h"], align=A))   # long side tangential [A]
    return out

def build(D):
    out = {}
    if _vern(D):
        for i, s in enumerate(sensors(D)): out[f"hall sensor H{i + 1} {D['hv_sensor']['part'].split()[0]}"] = s
        return out
    for i, a in enumerate(D["ha_sens_angs"]):
        t = math.radians(a)
        out[f"hall sensor U{4 + i}"] = Pos(D["ha_r_m"] * math.cos(t), D["ha_r_m"] * math.sin(t), 0) * Rot(0, 0, a) * Box(1.3, 2.92, D["ha_sens_h"], align=A)
    return out
