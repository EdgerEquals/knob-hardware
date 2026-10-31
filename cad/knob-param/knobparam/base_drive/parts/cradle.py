"""Base cradle on the PCB front: plate, motor collar (trimmed on the far side), encoder bearing seat, idler pockets, Hall window."""
from build123d import *
from ...common.util import A, cyl, thrust_groove
from . import hall_slot
SRC_DEPS = [hall_slot]

def build(D):
    pt, ro, mx = D["plate_t"], D["r_out"], D["offset"]
    c = cyl(ro, 0, pt)
    c += cyl(D["motor_collar_od"] / 2, 0, D["motor_collar_top"], mx)
    ex, ey = D["enc_xy"]
    c += cyl(D["dowel_pad_d"] / 2, 0, D["cr_floor"], ex, ey)
    c -= cyl(D["cr_bore_d"] / 2, 0, pt)
    c -= cyl(D["pad_cb"][0] / 2, 0, D["pad_cb"][1])
    c -= cyl(D["motor_bore_d"] / 2, 0, D["motor_collar_top"], mx)
    c -= cyl(D["enc_pocket_d"] / 2, D["cr_floor"], pt, ex, ey)
    c -= cyl(D["brg"]["D"] / 2, 0, D["cr_floor"], ex, ey)
    for x, y in D["idler_xy"]:
        c -= cyl(D["enc_pocket_d"] / 2, D["idler_floor"], D["idler_pocket_top"] - D["idler_floor"], x, y)
        c -= cyl(D["pin_d"] / 2, 0, D["idler_floor"], x, y)
    h = D["motor_collar_top"] - pt
    c -= cyl(D["dial_clear_d"] / 2, pt, h)
    c -= Pos(0, 0, pt) * Box(mx - D["motor_bore_d"] / 2 + 1.0, D["dial_clear_d"], h, align=(Align.MIN, Align.CENTER, Align.MIN))
    c -= thrust_groove(D["tb_pcd"], D["tb_groove_r"], D["tb_z_ball"])   # control_dial export: thrust-ball ring
    c -= Pos(mx + D["collar_trim"], 0, pt) * Box(20, 40, D["motor_collar_top"], align=(Align.MIN, Align.CENTER, Align.MIN))
    c -= hall_slot.window(D)
    return {"base cradle": c & cyl(ro, 0, 40)}
