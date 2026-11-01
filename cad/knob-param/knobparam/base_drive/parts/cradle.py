"""Base cradle on the PCB front: plate, motor collar (trimmed on the far side), encoder bearing seat, idler pockets,
Hall window, feel-motor rib + pinion pocket + lead holes."""
import math
from build123d import *
from ...common.util import A, cyl, thrust_groove
from . import hall_slot, mech
SRC_DEPS = [hall_slot, mech]

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
    # feel motor: rib the clip foot lands on, pocket for its pinion, holes for the two leads
    ang = math.radians(D["fm_ang"]); r0, r1 = D["fm_rib_r0"], D["fm_rib_r1"]
    if r1 > r0:
        mid, L = (r0 + r1) / 2, r1 - r0
        c += Pos(mid * math.cos(ang), mid * math.sin(ang), 0) * Rot(0, 0, D["fm_ang"]) * Box(L, D["fm_rib_w"], D["fm_z_rib1"], align=A)
    fx, fy = D["fm_xy"]
    c -= cyl(D["fm_pocket_r"], D["idler_floor"], D["idler_pocket_top"] - D["idler_floor"], fx, fy)
    for px, py in D["fm_pad_xy"]:
        c -= cyl(D["fm_lead_r"], -0.1, D["plate_t"] + 0.2, px, py)
    h = D["motor_collar_top"] - pt
    c -= cyl(D["dial_clear_d"] / 2, pt, h)
    c -= Pos(0, 0, pt) * Box(mx - D["motor_bore_d"] / 2 + 1.0, D["dial_clear_d"], h, align=(Align.MIN, Align.CENTER, Align.MIN))
    c -= thrust_groove(D["tb_pcd"], D["tb_groove_r"], D["tb_z_ball"])   # control_dial export: thrust-ball ring
    c -= Pos(mx + D["collar_trim"], 0, pt) * Box(20, 40, D["motor_collar_top"], align=(Align.MIN, Align.CENTER, Align.MIN))
    c -= hall_slot.window(D)
    c += mech.cradle_add(D)     # v0.16 detent blocks, cushion stops, spring posts
    c -= mech.cradle_cut(D)     # v0.16 ball-track grooves, detent bores, anchor-pin holes
    return {"base cradle": c & cyl(ro, 0, 40)}
