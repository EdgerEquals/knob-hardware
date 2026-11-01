"""Feel motor (716 coreless [A]) on the PCB top, inside the cradle: axial can, shaft down through the PCB
into a catalogue pinion. v0.17 [Ed]: that pinion meshes the compound gear on the idler, not the knob ring."""
import math
from build123d import *
from ...common.util import A, cyl, ext_gear, fresnel_cap

def build(D):
    F = D["feel"]; x, y = D["fm_xy"]; ang = D["fm_ang"]
    can_r = F["can_d"] / 2; z0, grip, wall = D["fm_z_can0"], D["fm_grip"], D["fm_wall"]
    glue = D["motor_glue"]
    can = cyl(can_r, z0, F["can_len"], x, y) + cyl(F["end_boss_d"] / 2, z0 + F["can_len"], F["end_boss"], x, y)
    P = D["fg_pinion"]; face = D["fg_face"]; z1 = D["fg_z_top"]; zb = z1 - face
    shaft = cyl(F["shaft_d"] / 2, z1, z0 - z1, x, y)   # can bottom to the pinion face; the press-fit bore is the pinion's
    Dm = dict(D); Dm["module"] = D["fg_mod"]
    half = D["brass_backlash"] / 2
    tooth = ext_gear(Dm, D["fg_z_pin"], 0, face, dthick=-half, addendum=D["spur_addendum"], dedendum=D["spur_dedendum"])
    bore_r = F["shaft_d"] / 2 + 0.02
    pip_r = 1.15
    tooth = tooth - cyl(bore_r, -0.01, face + 0.02) + cyl(pip_r, -0.55, 0.55) - cyl(bore_r, -0.6, 0.65)
    pin = Pos(x, y, zb) * tooth
    root_r = D["fg_z_pin"] * D["fg_mod"] / 2 - D["spur_dedendum"] * D["fg_mod"]
    cap = Pos(x, y, zb - D["cap_seat_gap"]) * Rot(0, 180, 0) * fresnel_cap(
        2 * (root_r - 0.20), 2 * pip_r + 2 * D["cap_fit_gap"], 0.0,
        D["cap_t"], D["cap_rings"], D["cap_step_h"], D["cap_step_w"])
    # v0.16 [Ed]: OPEN saddle clamp instead of the full wrap-around clip - two narrow bands (light load), open between them for
    # airflow round the can. Inboard half = seat (bands + spine) on the cradle rib; outboard half = strap (two C-bands) that
    # screws to the seat through paired ears at the can sides (M1 self-tapping [A]).
    seat, strap = saddle(D)
    return {f"feel motor {F['part']} [A]": can,
            f"feel motor shaft Ø{F['shaft_d']:g} [A]": shaft,
            f"feel motor pinion {P['part']} {D['fg_z_pin']}T": pin,
            f"feel motor pinion cap": cap,
            "feel motor saddle seat [A]": seat,
            "feel motor saddle strap [A]": strap}


def _arc(r0, r1, a0, a1, z0, h, n=36):
    pts = [(r1 * math.cos(math.radians(a0 + (a1 - a0) * i / n)), r1 * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    pts += [(r0 * math.cos(math.radians(a1 - (a1 - a0) * i / n)), r0 * math.sin(math.radians(a1 - (a1 - a0) * i / n))) for i in range(n + 1)]
    return Pos(0, 0, z0) * extrude(Face(Wire.make_polygon([Vector(x, y, 0) for x, y in pts], close=True)), h)

def saddle(D):
    """Built in the can frame (x = radially outward from the dial axis), then placed at fm_xy / fm_ang."""
    F = D["feel"]; can_r = F["can_d"] / 2; g = D["motor_glue"]; t = D["fm_band_t"]; hb = D["fm_band_h"]
    ri, ro = can_r + g, can_r + g + t; z0 = D["fm_z_can0"]; grip = D["fm_grip"]; split = D["fm_split"]
    zs = [z0 + D["fm_band_in"], z0 + grip - D["fm_band_in"] - hb]
    seat = strap = None
    for zb in zs:
        sb = _arc(ri, ro, split, 360 - split, zb, hb)                       # inboard band (faces the dial axis = local -x)
        tb = _arc(ri, ro, -split, split, zb, hb)                            # outboard band
        el, eh = D["fm_ear"]
        for sg in (1, -1):                                                  # ears either side of the split plane
            e_s = Rot(0, 0, sg * split) * Pos((ri + ri + el) / 2, sg * eh / 2, zb) * Box(el, eh, hb, align=A)
            e_t = Rot(0, 0, sg * split) * Pos((ri + ri + el) / 2, -sg * eh / 2, zb) * Box(el, eh, hb, align=A)
            hole = Rot(0, 0, sg * split) * Pos(ri + el / 2 + 0.2, 0, zb + hb / 2) * Rot(90, 0, 0) * Cylinder(D["fm_screw_d"] / 2, 2 * eh + 0.2)
            sb = sb + e_s - hole; tb = tb + e_t - hole
        seat = sb if seat is None else seat + sb
        strap = tb if strap is None else strap + tb
    # spine: inboard of the can from the cradle rib up to the top band (one narrow post, rest open)
    cd = D["fm_cd"]; r0 = D["fm_rib_r0"]
    sp_len = cd - ro + 0.05 - r0
    seat += Pos(-(ro - 0.05) - sp_len / 2, 0, z0) * Box(sp_len, D["fm_spine_w"], grip, align=A)
    seat -= cyl(ri, z0 - 0.2, grip + 0.4)
    x, y = D["fm_xy"]; P = Pos(x, y, 0) * Rot(0, 0, D["fm_ang"])
    return P * seat, P * strap
