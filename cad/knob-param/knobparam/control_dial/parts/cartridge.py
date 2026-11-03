"""v0.24 [Ed 3 Nov 12:28-12:58]: the dial screen as a drop-in bezel cartridge (knob +4.4).

Cartridge (lifts out from the top with a suction cup): printed bezel = the whole outside of the dial (laps the lens step, glass seat,
bore below the glass, magnet / pin bosses), Waveshare Z132A2441 panel proxy (lens, panel, its own flex: three parts patches, bottom COF
bend, top tab, free tail with its U-turn and lower leg, 24-pin 0.4 mm plug facing down), printed plug pad glued to an arm off the bezel.
In the dial: dial board (PCBA; receptacle on top; ESP32-S3-PICO-1, LDO, PHY, 405 nm diode and five LED sites underneath), the dial-side
magnets and the locating pins. Strap loop from the fixed rod-link board up to the dial board.
Everything is drawn in the PANEL frame and turned into the mechanism frame (to_mech), like the rest of control_dial."""
import math
from build123d import *
from ...common.util import A, rev, cyl, tube
from .dial import ring_sector, to_mech
from . import dial
SRC_DEPS = [dial]


def box(x0, x1, y0, y1, z0, z1):
    return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=(Align.MIN, Align.MIN, Align.MIN))


def bezel(D):
    zp, bz = D["zp"], D["bz"]; R, c = D["R"], D.get("sleeve_top_cout", 0.0)
    z0, zt, zb = D["z_lip0"], D["z_top"], D["lens_back"]
    rb, rs, rl = D["bz_bore_r"], D["bz_seat_r"], D["bz_lap_r"]
    # outside as today's lip: flat underside to R - c, 45° chamfer, OD up to the lens top; inside: lap over the lens step, glass seat, bore
    b = rev([(rb, z0), (R - c, z0), (R, z0 + c), (R, zt), (rl, zt), (rl, D["lens_step_z"]), (rs, D["lens_step_z"]), (rs, zb), (rb, zb)])
    bz0, bz1 = D["bz_boss_z"]
    for k, a, _, (x, y) in D["cart_holes"]:
        h = D["boss_half"][k]
        b += ring_sector(bz["boss_r"][0], rb + 0.3, a - h, a + h, bz0, bz1 - bz0)
    for k, a, _, (x, y) in D["cart_holes"]:
        if k == "magnet":
            b -= cyl((bz["mag"][0] + bz["mag_press"]) / 2, bz0 - 0.01, bz["mag"][1] + 0.01, x, y)
        else:
            b -= cyl(bz["pin"][0] / 2 + bz["pin_clear"], bz0 - 0.01, bz["pin"][2] + 0.11, x, y)
    return b


def lens(D):
    zp = D["zp"]
    return cyl(zp["lens_d"] / 2, D["lens_back"], zp["lens_t"] - zp["step_t"]) + cyl(zp["step_d"] / 2, D["lens_step_z"], zp["step_t"])


def flex(D):
    """The panel's own flex: parts patches behind the panel, bottom COF bend, top tab, the free tail (U-turn, lower leg)."""
    zp = D["zp"]; t = zp["flex_t"]; rl = zp["lcm_d"] / 2; z1 = D["lcm_z0"]
    s = None
    for x0, x1, y0, y1 in zp["patches"]:
        p = box(x0, x1, y0, y1, D["patch_z0"], z1) & cyl(zp["patch_r"], D["patch_z0"] - 0.1, 3.0)
        s = p if s is None else s + p
    bz0, bz1 = D["bend_z"]; tz0, tz1 = D["tab_z"]
    s += tube(rl, zp["bend_r"], bz0, bz1 - bz0) & box(-zp["bend_hx"], zp["bend_hx"], -30, 0, bz0 - 1, bz1 + 1)
    s += tube(rl, zp["tab_r"], tz0, tz1 - tz0) & box(-zp["tab_hx"], zp["tab_hx"], 0, 30, tz0 - 1, tz1 + 1)
    # tail: leaves the panel's back at tail_x0, U-turns at the rim (outer face uturn_x) from the panel back down to the lower leg
    y0, y1 = zp["tail_y"]; ro = (z1 - D["leg_z0"]) / 2; zc = (z1 + D["leg_z0"]) / 2; xc = zp["uturn_x"] + ro
    loop = Pos(xc, y0, zc) * Rot(-90, 0, 0) * (Cylinder(ro, y1 - y0, align=A) - Cylinder(ro - t, y1 - y0, align=A))
    s += loop & box(xc - ro - 1, xc, y0 - 1, y1 + 1, zc - ro - 1, zc + ro + 1)
    s += box(xc, zp["tail_x0"], y0, y1, z1 - t, z1)                                        # upper leg, under the panel back
    s += box(xc, zp["leg_x1"], y0, y1, D["leg_z0"], D["leg_z0"] + t)                       # lower leg, 3.5 behind the lens back
    return s


def plug_end(D):
    """24-pin 0.4 mm plug facing down, with the flex end over it and the joggle up from the lower leg (one mated-connector solid).
    Only the part above the receptacle is solid: the plug's mating face (plug_face_z) is plug_engage inside the receptacle."""
    zp = D["zp"]; t = zp["flex_t"]; x0, x1, y0, y1 = zp["plug"]; ty0, ty1 = zp["tail_y"]; zf = D["plug_flex_z"]
    xj = zp["leg_x1"] + 0.5
    s = box(x0, x1, y0, y1, D["rec_z1"], zf)                                               # plug body above the receptacle
    s += box(xj, x1, y0, y1, zf, zf + t)                                                   # flex end (+ stiffener) over the plug
    s += box(zp["leg_x1"], xj, ty0, ty1, D["leg_z0"], zf + t)                              # joggle from the lower leg
    return s


def pad(D):
    """Printed plug pad on the plug's flex, arm out to the bezel bore at arm_ang (glued with the cartridge seated on its dial)."""
    zp, bz = D["zp"], D["bz"]; x0, x1, y0, y1 = zp["plug"]; p0, p1 = D["pad_z"]
    p = box(x0, x1, y0, y1, p0, p1)
    r0 = math.hypot(*D["plug_xy"]) + 1.0   # arm starts inside the pad, its corners on the pad
    arm = Pos(0, 0, p1 - bz["arm_t"]) * Rot(0, 0, bz["arm_ang"]) * Box(D["bz_bore_r"] + 1 - r0, bz["arm_w"], bz["arm_t"],
                                                                            align=(Align.MIN, Align.CENTER, Align.MIN))
    arm = Pos(*(r0 * math.cos(math.radians(bz["arm_ang"])), r0 * math.sin(math.radians(bz["arm_ang"])), 0)) * arm
    arm &= cyl(D["bz_bore_r"] - bz["arm_glue"], p0 - 1, 5)
    return p + arm


def board(D):
    db = D["db"]; z0, z1 = D["db_z0"], D["db_z1"]; a0, a1, rl = db["lobe"]
    b = cyl(D["db_r"], z0, z1 - z0) + ring_sector(D["db_r"] - 0.5, rl, a0, a1, z0, z1 - z0)
    out = {"dial board (PCBA, under the screen)": b}
    x, y, w, l, h = db["rec"]
    out["dial board receptacle, 24-pin 0.4 B2B (faces up)"] = box(x - w / 2, x + w / 2, y - l / 2, y + l / 2, z1, z1 + h)
    for nm, x, y, w, l, h in db["parts"]:
        out[f"dial board part {nm}"] = box(x - w / 2, x + w / 2, y - l / 2, y + l / 2, z0 - h, z0)
    x, y, d, h = db["diode"]
    out["dial board 405 nm laser diode (TO-38 class, facing down)"] = cyl(d / 2, z0 - h, h, x, y)
    r, angs, w, l, h = db["led"]
    for a in angs:
        x, y = r * math.cos(math.radians(a)), r * math.sin(math.radians(a))
        out[f"dial board LED site {a:g}° (facing down)"] = Pos(x, y, z0 - h) * Rot(0, 0, a) * Box(w, l, h, align=A)
    return out


def strap_local(D, theta=0.0, n=16):
    """The strap loop: a 2-layer PI ribbon standing on edge in the vertical plane through its ends, local frame (x along the
    ribbon from the fixed end, y = its thickness). theta (deg): the dial end has turned; the ribbon is cut into n slabs shifted
    sideways by the clamped-guided deflection (see params._cart), the dial-end foot turns rigidly with the board."""
    ls = D["ls"]; w, t, L = ls["w"], D["strap_t"], D["ls_L"]; r0, r1 = D["ls_run_z"]; za, zb = D["ls_z_a"], D["ls_z_b"]
    rib = box(-w / 2, w / 2, -t / 2, t / 2, za + t, r1) + box(-w / 2, L + w / 2, -t / 2, t / 2, r0, r1) + box(L - w / 2, L + w / 2, -t / 2, t / 2, r0, zb - t)
    foot_a = box(-w / 2, w / 2, -ls["foot"] / 2, ls["foot"] / 2, za, za + t)
    foot_b = box(L - w / 2, L + w / 2, -ls["foot"] / 2, ls["foot"] / 2, zb - t, zb)
    if not theta:
        return rib + foot_a + foot_b, None
    th = math.radians(theta); c2, c3 = D["ls_c"]
    def dfl(s):
        s = max(0.0, s)
        if s <= L: return th * (c2 * s * s + c3 * s ** 3)
        return th * (c2 * L * L + c3 * L ** 3) + th * (s - L)
    s0, s1 = -w / 2, L + w / 2; out = foot_a
    for i in range(n):
        a, b = s0 + (s1 - s0) * i / n, s0 + (s1 - s0) * (i + 1) / n
        sl = rib & box(a - 1e-4, b + 1e-4, -1, 1, za - 1, zb + 1)
        out = out + Pos(0, dfl((a + b) / 2), 0) * sl
    return out, foot_b


def strap(D, theta=0.0):
    """Strap loop in the mechanism frame at dial angle theta (deg)."""
    (ax, ay), (bx, by) = D["ls"]["a"], D["ls"]["b"]; ang = math.degrees(math.atan2(by - ay, bx - ax))
    s, foot_b = strap_local(D, theta)
    s = Pos(ax, ay, 0) * Rot(0, 0, ang) * s
    if foot_b is not None:
        s = s + Rot(0, 0, theta) * (Pos(ax, ay, 0) * Rot(0, 0, ang) * foot_b)
    return to_mech(D, s)


def build(D):
    if not D.get("cart"):
        return {}
    bz = D["bz"]; out = {}
    out["dial bezel (printed cartridge ring)"] = bezel(D)
    out["dial screen Z132A2441 lens (cover glass)"] = lens(D)
    out["dial screen Z132A2441 panel (AMOLED)"] = cyl(D["zp"]["lcm_d"] / 2, D["lcm_z0"], D["zp"]["lcm_t"])
    out["dial screen Z132A2441 flex (parts, bends, tail)"] = flex(D)
    out["dial screen Z132A2441 plug end, 24-pin 0.4 B2B (faces down)"] = plug_end(D)
    out["dial cartridge plug pad + arm (printed, glued)"] = pad(D)
    md, mh = bz["mag"]
    for k, a, _, (x, y) in D["cart_holes"]:
        if k == "magnet":
            out[f"cartridge magnet {md:g}x{mh:g} N52 (bezel) {a:g}°"] = cyl(md / 2, D["bz_boss_z"][0], mh, x, y)
            out[f"cartridge magnet {md:g}x{mh:g} N52 (dial) {a:g}°"] = cyl(md / 2, D["db_z1"] - mh, mh, x, y)
        else:
            pd, pp, pe = bz["pin"]
            out[f"cartridge locating pin Ø{pd:g} {a:g}°"] = cyl(pd / 2, D["db_z1"] - pp, pp + bz["boss_gap"] + pe, x, y)
    out.update(board(D))
    out["dial strap loop, 2 lines + 2 spares [A]"] = strap(D)
    return {n: to_mech(D, s) if not n.startswith("dial strap") else s for n, s in out.items()}
