"""Top-screen joystick stack parts: build(D) -> {name: solid}. Reads D only."""
import math
from build123d import *

A = (Align.CENTER, Align.CENTER, Align.MIN)

def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=A)

def cbox(w, h, z0, z1, x=0.0, y=0.0):
    return box(x - w / 2, x + w / 2, y - h / 2, y + h / 2, z0, z1)

def cyl(d, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, z0) * Cylinder(d / 2, z1 - z0, align=A)

def quad(xy):
    x, y = xy; return [(sx * x, sy * y) for sx in (1, -1) for sy in (1, -1)]

def pcb(D):
    t = D["pcb_t"]; p = box(-20.0, 20.0, -12.5, 12.5, -t, 0)
    for x, y in quad(D["spr_xy"]): p -= cyl(D["spr_bore"], -t - 1, 1, x, y)
    p -= box(D["hole_x0"], D["hole_x1"], -D["hole_hy"], D["hole_hy"], -t - 1, 1)
    py = D["base_h"] / 2 - D["base_wall"] / 2
    for x, y in quad((D["pin_xy"], py)): p -= cyl(D["pin"][0] + 0.1, -t - 1, 1, x, y)
    return p

def base(D):
    bw, bh = D["base_w"], D["base_h"]; cw, ch = D["cav"]; z1 = D["z_base1"]; zt0 = D["z_base_top0"]; zf = D["base_floor"]
    b = cbox(bw, bh, 0, z1) - cbox(cw, ch, zf, zt0)
    b -= cbox(D["win"][0], D["win"][1], zt0 - 0.01, z1 + 0.01)                     # daughterboard drops in from the top
    sw, sh, _ = D["sock"]; b -= cbox(sw + 0.4, sh + 0.4, -0.01, zf + 0.01, D["hdr_x"], 0)   # socket through the floor
    b += cyl(D["post_d"], zf - 0.01, D["z_db0"], D["sw_x"], 0)                      # riser post under the switch
    for x, y in quad(D["spr_xy"]):
        b += cyl(D["spr_bore"] + 0.8, zf - 0.01, zt0 + 0.01, x, y)                  # spring pillars
    for x, y in quad(D["spr_xy"]): b -= cyl(D["spr_bore"], -0.1, z1 + 0.1, x, y)
    r = D["ball_d"] / 2 + D["seat_clear"]
    for x, y in quad(D["ball_xy"]): b -= Pos(x, y, z1) * Sphere(r)                  # hemispherical ball seats
    b -= box(D["hole_x0"], D["hole_x1"] + 2, -D["hole_hy"], D["hole_hy"], -0.1, z1 + 0.1)   # FPC notch at the +x end
    py = bh / 2 - D["base_wall"] / 2
    for x, y in quad((D["pin_xy"], py)): b += cyl(D["pin"][0], -D["pin"][1], 0.01, x, y)
    return b

def carrier(D):
    cw, ch = D["car"]; s = D["car_skirt"]; pw, ph = D["pocket"]
    c = cbox(cw, ch, D["z_skirt0"], D["z_car1"])
    c -= cbox(cw - 2 * s, ch - 2 * s, D["z_skirt0"] - 0.01, D["z_c0"])                # skirt round the base top
    c -= cbox(pw, ph, D["z_sp0"], D["z_car1"] + 0.01)                               # screen + spider pocket (spider frame sits on the ledge)
    c -= box(D["sp_in_x"][0], D["sp_in_x"][1], -D["sp_in_hy"], D["sp_in_hy"], D["z_floor1"], D["z_sp0"] + 0.01)   # free travel under pad + arms
    c += cyl(D["cup_od"], D["z_cup0"], D["z_c0"] + 0.01, D["sw_x"], 0)               # cup over the stem
    for x, y in quad(D["spr_xy"]): c += cyl(D["spr_boss"][0], D["spr_z1"], D["z_c0"] + 0.01, x, y)
    c -= cyl(D["cup_bore"], D["z_cup0"] - 0.01, D["z_floor1"] + 0.01, D["sw_x"], 0)   # stem / plunger bore
    c -= box(D["slot_x"][0], D["slot_x"][1], -D["slot_hy"], D["slot_hy"], D["z_c0"] - 0.01, D["z_sp0"] + 0.01)   # FPC slot
    return c

def spider(D):
    z0, z1 = D["z_sp0"], D["z_sp1"]; x0, x1 = D["sp_x"]; hy = D["sp_hy"]; ix0, ix1 = D["sp_in_x"]; ihy = D["sp_in_hy"]
    px0, px1 = D["pad_x"]; phy = D["sp_pad"][1] / 2; w = D["sp_arm_w"]
    s = box(x0, x1, -hy, hy, z0, z1) - box(ix0, ix1, -ihy, ihy, z0 - 0.01, z1 + 0.01)
    s += box(px0, px1, -phy, phy, z0, z1)
    yb = (phy + ihy) / 2                                         # arm band mid-line
    xm = D["sw_x"]
    for sy in (1, -1):
        # two U arms per side: pad corner -> band -> run toward the middle -> frame (rotationally balanced)
        for (xa, xb) in ((px0 + w / 2 + 0.2, xm - 0.6 - w / 2), (px1 - w / 2 - 0.2, xm + 0.6 + w / 2)):
            lo, hi = sorted((xa, xb))
            ys = sorted((sy * phy, sy * yb)); s += box(xa - w / 2, xa + w / 2, ys[0] - 0.01, ys[1] + 0.01, z0, z1)
            s += box(lo - w / 2, hi + w / 2, sy * yb - w / 2, sy * yb + w / 2, z0, z1)
            ys = sorted((sy * yb, sy * ihy)); s += box(xb - w / 2, xb + w / 2, ys[0] - 0.01, ys[1] + 0.01, z0, z1)
    s += box(px0, px1, -phy, phy, z1 - 0.01, z1 + D["sp_land"])                  # land
    s += cyl(D["plunger_d"], D["z_plunger0"], z0 + 0.01, D["sw_x"], 0)            # plunger to the stem top
    return s

def switch(D):
    sw = D["sw"]; x = D["sw_x"]; z = D["z_db1"]
    body = Pos(x, 0, z) * Rot(0, 0, D["sw_rot"]) * Box(sw["w"], sw["d"], sw["h"], align=A)
    stem = cyl(sw["stem_d"], z + sw["h"], D["z_stem_top"], x, 0)
    return body, stem

def build(D):
    out = {}
    out["main PCB (proxy, local patch)"] = pcb(D)
    out["J2 socket 2x3 2.54 female 8.5 (main PCB)"] = cbox(*D["sock"][:2], 0, D["sock"][2], D["hdr_x"], 0)
    dw, dh, dt = D["db"]
    db = cbox(dw, dh, D["z_db0"], D["z_db1"])
    out["joystick daughterboard"] = db
    hw, hh, ht = D["hdr_body"]
    out["J1 header 2x3 2.54 male (body on top)"] = cbox(hw, hh, D["z_db1"], D["z_db1"] + ht, D["hdr_x"], 0)
    body, stem = switch(D)
    out["SW1 SKRHADE010 body (45°)"] = body
    out["SW1 SKRHADE010 stem"] = stem
    out["joystick base (printed, glued)"] = base(D)
    for i, (x, y) in enumerate(quad(D["ball_xy"])):
        out[f"ball {i + 1} Ø{D['ball_d']:g}"] = Pos(x, y, D["z_ball"]) * Sphere(D["ball_d"] / 2)
    out["joystick carrier (printed)"] = carrier(D)
    out["screen spider + plunger (printed)"] = spider(D)
    S = D["scr"]
    out["top screen " + S["part"]] = cbox(S["w"], S["h"], D["z_scr0"], D["scr_top"])
    t = D["fpc_t"]
    out["screen FPC [A]"] = box(D["fpc_x"] - t / 2, D["fpc_x"] + t / 2, -D["fpc_w"] / 2, D["fpc_w"] / 2, -D["pcb_t"] - 3.0, D["z_scr0"] - 0.1)
    for i, (x, y) in enumerate(quad(D["spr_xy"])):
        out[f"hold-down spring {i + 1}"] = cyl(D["spr_d"], -D["pcb_t"] - 6.0, D["spr_z1"], x, y)
    return out
