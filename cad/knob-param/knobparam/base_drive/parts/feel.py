"""Feel motor (716 coreless [A]) on the PCB top, inside the cradle: axial can, shaft down through the PCB
into a catalogue pinion. v0.17 [Ed]: that pinion meshes the compound gear on the idler, not the knob ring."""
import math
from build123d import *
from ...common.util import overlay, A, cyl, ext_gear, fresnel_cap
from ...common.saddle import clamp

def build(D):
    if not D["feel_on"]:   # Q27 [Ed 6 Nov 19:33]: no feel motor
        return {}
    F = D["feel"]; x, y = D["fm_xy"]; ang = D["fm_ang"]
    can_r = F["can_d"] / 2; z0, grip, wall = D["fm_z_can0"], D["fm_grip"], D["fm_wall"]
    glue = D["motor_glue"]
    can = cyl(can_r, z0, F["can_len"], x, y) + cyl(F["end_boss_d"] / 2, z0 + F["can_len"], F["end_boss"], x, y)
    P = D["fg_pinion"]; face = D["fg_face"]; z1 = D["fg_z_top"]; zb = z1 - face
    shaft = cyl(F["shaft_d"] / 2, z1, z0 - z1, x, y)   # can bottom to the pinion face; the press-fit bore is the pinion's
    Dm = overlay(D, module=D["fg_mod"])   # tracked view; dict(D) hid backlash and pressure from the cache
    half = D["brass_backlash"] / 2
    tooth = ext_gear(Dm, D["fg_z_pin"], 0, face, dthick=-half, addendum=D["spur_addendum"], dedendum=D["spur_dedendum"])
    bore_r = F["shaft_d"] / 2 + 0.02
    pip_r = D["fm_pip_r"]
    tooth = tooth - cyl(bore_r, -0.01, face + 0.02) + cyl(pip_r, D["fm_pip_z0"], D["fm_pip_h"]) - cyl(bore_r, D["fm_pip_z0"] - 0.05, D["fm_pip_h"] + 0.10)
    pin = Pos(x, y, zb) * tooth
    root_r = D["fg_z_pin"] * D["fg_mod"] / 2 - D["spur_dedendum"] * D["fg_mod"]
    cap = Pos(x, y, zb - D["cap_seat_gap"]) * Rot(0, 180, 0) * fresnel_cap(
        2 * (root_r - D["fm_cap_inset"]), 2 * pip_r + 2 * D["cap_fit_gap"], 0.0,
        D["cap_t"], D["cap_rings"], D["cap_step_h"], D["cap_step_w"])
    # v0.16 [Ed]: OPEN saddle clamp instead of the full wrap-around clip - two narrow bands (light load), open between them for
    # airflow round the can. Inboard half = seat (bands + spine) on the cradle rib; outboard half = strap (two C-bands) that
    # screws to the seat through paired ears at the can sides (M1 self-tapping [A]).
    seat, strap, screws = saddle(D)
    return {f"feel motor {F['part']} [A]": can,
            f"feel motor shaft Ø{F['shaft_d']:g} [A]": shaft,
            f"feel motor pinion {P['part']} {D['fg_z_pin']}T": pin,
            f"feel motor pinion cap": cap,
            "feel motor saddle seat [A]": seat,
            "feel motor saddle strap [A]": strap,
            "feel motor saddle screw": screws}


def _arc(r0, r1, a0, a1, z0, h, n=36):
    pts = [(r1 * math.cos(math.radians(a0 + (a1 - a0) * i / n)), r1 * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    pts += [(r0 * math.cos(math.radians(a1 - (a1 - a0) * i / n)), r0 * math.sin(math.radians(a1 - (a1 - a0) * i / n))) for i in range(n + 1)]
    return Pos(0, 0, z0) * extrude(Face(Wire.make_polygon([Vector(x, y, 0) for x, y in pts], close=True)), h)

def saddle(D):
    """Shared clamp in the can frame (+x outboard), then placed at fm_xy / fm_ang. Spine stays feel-specific."""
    F = D["feel"]; can_r = F["can_d"] / 2; g = D["motor_glue"]
    seat, strap, screws, _d = clamp(can_r, D["fm_z_can0"], D["fm_grip"], D["fm_screw_d"], glue=g,
                                    band_t=D["fm_band_t"], band_h=D["fm_band_h"], split_deg=D["fm_split"],
                                    band_in=D["fm_band_in"], ear_k=D["saddle_ear_k"], edge_k=D["saddle_edge_k"])
    ri, ro = can_r + g, can_r + g + D["fm_band_t"]
    cd = D["fm_cd"]; r0 = D["fm_rib_r0"]
    sp_len = cd - ro - D["cr_clear"] - r0
    seat += Pos(-(ro - 0.05) - sp_len / 2, 0, D["fm_z_can0"]) * Box(max(sp_len, 0.2), D["fm_spine_w"], D["fm_grip"], align=A)
    seat -= cyl(ri, D["fm_z_can0"] - 0.2, D["fm_grip"] + 0.4)
    x, y = D["fm_xy"]; P = Pos(x, y, 0) * Rot(0, 0, D["fm_ang"])
    seat = P * seat
    # The 1220 collar reaches this saddle. Cut the seat back so the two parts do not meet.
    seat -= cyl(D["motor_collar_od"] / 2 + D["cr_clear"], -0.1, D["motor_collar_top"] + 1, D["offset"], 0)
    return seat, P * strap, P * screws
