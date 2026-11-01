"""optics: 405 nm laser body + the two Risley wedges (posed at angle 0; the beam check rotates them mathematically)."""
import math
from build123d import *
from ...common.util import cyl

def wedge(D, z0, rot_deg):
    """Disc of diameter rp_d, flat bottom at z0, top face tilted by the wedge angle about an axis at rot_deg."""
    d, a = D["rp_d"], math.radians(D["rp_wedge_deg"])
    blank = cyl(d / 2, z0, D["rp_t_max"] + 0.01)
    # cut with a big box tilted by alpha, its bottom face through the thin edge height on one side
    cut = Pos(0, 0, z0 + D["rp_t_min"] + d / 2 * math.tan(a)) * Rot(0, D["rp_wedge_deg"], 0) * Box(4 * d, 4 * d, 4 * d, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return Rot(0, 0, rot_deg) * (blank - cut)

def build(D):
    if not D["optics_on"]: return {}
    x, y = D["las_xy"]
    return {"laser 405 nm": Pos(x, y, 0) * cyl(D["las_d"] / 2, D["las_z_ap"] - D["las_len"], D["las_len"]),
            "Risley wedge 1": Pos(x, y, 0) * wedge(D, D["rp1_z0"], 0.0),
            "Risley wedge 2": Pos(x, y, 0) * wedge(D, D["rp2_z0"], 180.0)}
