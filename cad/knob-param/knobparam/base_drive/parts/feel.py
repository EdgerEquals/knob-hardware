"""Feel motor (716 coreless [A]) on the PCB top, inside the cradle: axial can, shaft down into its own pinion
meshing the bottom internal ring, clip collar with an inboard foot that lands on the cradle rib."""
import math
from build123d import *
from ...common.util import A, cyl, tube, ext_gear, ring_phase

def build(D):
    F = D["feel"]; x, y = D["fm_xy"]; ang = D["fm_ang"]
    can_r = F["can_d"] / 2; z0, grip, wall = D["fm_z_can0"], D["fm_grip"], D["fm_wall"]
    glue = D["motor_glue"]
    can = cyl(can_r, z0, F["can_len"], x, y) + cyl(F["end_boss_d"] / 2, z0 + F["can_len"], F["end_boss"], x, y)
    shaft = cyl(F["shaft_d"] / 2, D["h_pin0"], z0 - D["h_pin0"], x, y)
    bore = F["shaft_d"] / 2 + D["motor_bore_clear"]
    pin = Pos(x, y, 0) * Rot(0, 0, ring_phase(D, ang, D["z_feel"])) * (
        ext_gear(D, D["z_feel"], D["h_pin0"], D["pin_face"]) - cyl(bore, D["h_pin0"], D["pin_face"]))
    clip = tube(can_r + glue, can_r + glue + wall, z0, grip, x, y)
    # inboard foot: from the cradle rib up to the collar, clear of the can bore
    r0, cd, w = D["fm_rib_r0"], D["fm_cd"], D["fm_rib_w"]
    mid, L = (r0 + cd) / 2, cd - r0
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    clip += Pos(mid * ux, mid * uy, z0) * Rot(0, 0, ang) * Box(L, w, grip, align=A)
    clip -= cyl(can_r + glue, z0 - 0.2, grip + 0.4, x, y)
    return {f"feel motor {F['part']} [A]": can,
            f"feel motor shaft Ø{F['shaft_d']:g} [A]": shaft,
            f"feel motor pinion {D['z_feel']}T [A]": pin,
            "feel motor clip [A]": clip}
