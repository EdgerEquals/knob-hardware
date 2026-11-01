"""Base cradle on the PCB front: plate, motor collar (trimmed on the far side), encoder bearing seat, idler pockets,
Hall window, feel-motor rib + shaft hole, outer-thrust flange, skinny-bridge relief."""
import math
from build123d import *
from ...common.util import A, cyl, sector, thrust_groove
from . import hall_slot, mech
SRC_DEPS = [hall_slot, mech]

def _breakout_relief(D, cx, cy, hole_r):
    """Sever the feather where a pocket breaks the cradle OD. The cut is only the ligament thinner than cr_web_min,
    and it stops cr_web_min outside the pin hole. Ends are radiused cr_bridge_fillet."""
    ro, wmin, fr = D["r_out"], D["cr_web_min"], D["cr_bridge_fillet"]
    d = math.hypot(cx, cy)
    if d + hole_r <= ro - wmin:
        return None
    ang = math.atan2(cy, cx)
    thin = []
    for i in range(-90, 91):
        a = ang + math.radians(i * 0.5)
        ux, uy = math.cos(a), math.sin(a)
        cu = cx * ux + cy * uy
        disc = cu * cu - (d * d - hole_r * hole_r)
        if disc < 0: continue
        t = cu + math.sqrt(disc)
        thick = 0.0 if t >= ro else ro - t
        if thick < wmin: thin.append(a)
    if len(thin) < 2: return None
    a0, a1 = min(thin), max(thin)
    r_keep = d + D["pin_d"] / 2 + wmin
    r_in = max(ro - wmin, r_keep)
    if r_in >= ro - 0.05: return None
    mid = math.degrees((a0 + a1) / 2)
    half = math.degrees((a1 - a0) / 2) + math.degrees(fr / max(ro, 1.0))
    cut = sector(r_in, ro + 0.8, half, -0.05, D["plate_t"] + 0.1, mid)
    for a in (a0, a1):
        cut += cyl(fr, -0.05, D["plate_t"] + 0.1, r_in * math.cos(a), r_in * math.sin(a))
    return cut

def _thrust_flange(D):
    """Printed ball carrier, one part with the cradle, on the centre-tube clamp (the cradle bore) and the existing
    encoder Ø5 press (no new PCB holes). Flat seat; the keep-out sector over C20–C22/U20 is left open."""
    r0 = D["r_out"] - 0.3
    r1 = D["ot_r"] + D["ot_rg"] + D["ot_land_out"]
    if r1 <= r0 + 0.2: return None
    z1 = D["ot_z_top"]
    fl = cyl(r1, 0, z1) - cyl(r0, -0.05, z1 + 0.1)
    a0, a1 = D["ot_keep_ang"]
    fl -= sector(r0 - 0.1, r1 + 0.3, (a1 - a0) / 2 + 0.6, -0.1, z1 + 0.2, (a0 + a1) / 2)
    fl -= Pos(0, 0, D["ot_z"]) * Torus(D["ot_r"], D["ot_rg"])
    # the encoder bearing's outer flange reaches into this annulus
    ex, ey = D["enc_xy"]
    fl -= cyl(D["brg"]["fd"] / 2 + D["fg_clear"], -0.1, D["ot_z_top"] + 0.3, ex, ey)
    return fl

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
    c -= cyl(D["fm_shaft_hole"] / 2, -0.1, pt + 0.2, fx, fy)   # 716 shaft down to the pinion under the PCB
    for px, py in D["fm_pad_xy"]:
        c -= cyl(D["fm_lead_r"], -0.1, D["plate_t"] + 0.2, px, py)
    h = D["motor_collar_top"] - pt
    c -= cyl(D["dial_clear_d"] / 2, pt, h)
    c -= Pos(0, 0, pt) * Box(mx - D["motor_bore_d"] / 2 + 1.0, D["dial_clear_d"], h, align=(Align.MIN, Align.CENTER, Align.MIN))
    c -= thrust_groove(D["tb_pcd"], D["tb_groove_r"], D["tb_z_ball"])   # control_dial export: thrust-ball ring
    c -= Pos(mx + D["collar_trim"], 0, pt) * Box(20, 40, D["motor_collar_top"], align=(Align.MIN, Align.CENTER, Align.MIN))
    c -= hall_slot.window(D)
    c += mech.cradle_add(D)     # detent blocks, hard stops, spring posts
    c -= mech.cradle_cut(D)     # ball-track grooves, detent bores, anchor-pin holes
    for (x, y) in D["idler_xy"]:
        rel = _breakout_relief(D, x, y, D["enc_pocket_d"] / 2)
        if rel is not None: c -= rel
    rel = _breakout_relief(D, fx, fy, D["fm_shaft_hole"] / 2)
    if rel is not None: c -= rel
    fl = _thrust_flange(D)
    if fl is not None: c += fl
    balls = Compound(children=[Pos(D["ot_r"] * math.cos(math.radians(a)), D["ot_r"] * math.sin(math.radians(a)), D["ot_z"]) * Sphere(D["ot_ball_d"] / 2) for a in D["ot_angs"]])
    return {"base cradle": c & cyl(max(ro, D["ot_r"] + D["ot_rg"] + D["ot_land_out"] + 0.2), -0.01, 40.01),
            f"outer thrust balls {D['ot_n']} x Ø{D['ot_ball_d']:g}": balls}
