"""1220 coreless planetary motor (library builder, dims from params) + printed D-bore pinion (v0.25 [Ed 19:10]: PA-12 12T m0.75,
profile shift hub_x_pin); the mesh is cut for hub_cd and runs on the KiCad axis (offset)."""
import math
from build123d import *
from ...common.util import A, ext_gear, cyl
from . import motor_gearbox as mg   # vendored copy of cad/motors/1220-coreless-planetary/motor_gearbox.py
SRC_DEPS = [mg]

def build(D):
    M = D["motor"]
    motor = Pos(D["offset"], 0, 0) * Rot(0, 0, -90) * Rot(0, -90, 0) * mg.build(M)
    f = D["motor_pinion_face"]; r = (M["shaft_d"] + D["motor_bore_clear"]) / 2; fl = M["shaft_flat"] + D["motor_bore_clear"]
    half = D["brass_backlash"] / 2
    m, x = D["hub_mod"], D["hub_x_pin"]
    g = ext_gear(D, D["z_pinion"], 0, f, module=m, dthick=2 * x * m * math.tan(math.radians(D["pressure"])) - half,
                 addendum=D["spur_addendum"] + x, dedendum=D["spur_dedendum"] - x)
    bore = Cylinder(r, f, align=A) & Pos(0, fl / 2 - r, 0) * Box(2 * r, fl, f, align=A)
    pin = Pos(D["offset"], 0, D["h_pinion0"]) * (g - bore)
    return {"motor": motor, "pinion": pin}
