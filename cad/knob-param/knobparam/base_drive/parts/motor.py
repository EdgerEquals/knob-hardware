"""1220 coreless planetary motor (library builder, dims from params) + 12T D-bore pinion; hub-gear centre distance = offset."""
from build123d import *
from ...common.util import A, ext_gear, cyl
from . import motor_gearbox as mg   # vendored copy of cad/motors/1220-coreless-planetary/motor_gearbox.py
SRC_DEPS = [mg]

def build(D):
    M = D["motor"]
    motor = Pos(D["offset"], 0, 0) * Rot(0, 0, -90) * Rot(0, -90, 0) * mg.build(M)
    f = D["motor_pinion_face"]; r = (M["shaft_d"] + D["motor_bore_clear"]) / 2; fl = M["shaft_flat"] + D["motor_bore_clear"]
    g = ext_gear(D, D["z_motor_pinion"], 0, f)
    bore = Cylinder(r, f, align=A) & Pos(0, fl / 2 - r, 0) * Box(2 * r, fl, f, align=A)
    pin = Pos(D["offset"], 0, D["h_pinion0"]) * (g - bore)
    return {"motor": motor, "pinion": pin}
