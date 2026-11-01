"""Top-screen joystick stack parts, v0.2: build(D) -> {name: solid}. Reads D only.

The carrier is a deep tub: the screen is up near the knob top and the switch stays on the 11 mm socket,
so the floor takes the difference. The slide stop is a round boss (equal travel on the diagonals). A looser
rectangular skirt only stops the carrier rotating on that boss.
"""
from build123d import *

A = (Align.CENTER, Align.CENTER, Align.MIN)

def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=A)

def cbox(w, h, z0, z1, x=0.0, y=0.0):
    return box(x - w / 2, x + w / 2, y - h / 2, y + h / 2, z0, z1)

def cyl(d, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, z0) * Cylinder(d / 2, z1 - z0, align=A)

def pcb(D):
    t = D["pcb_t"]
    # local patch of the main PCB: wide enough for the base, cut off at the real board edges
    x0, x1 = -D["pcb_w"] / 2, D["pcb_w"] / 2
    y1 = D["pcb_above"] - D["place_y"]
    y0 = -D["place_y"] - 8.0
    p = box(x0, x1, y0, y1, -t, 0)
    for x, y in D["springs"]:
        p -= cyl(D["spr_bore"], -t - 1, 1, x, y)
    for x, y in D["pins"]:
        p -= cyl(D["pin"][0] + 0.1, -t - 1, 1, x, y)
    for x, y in D["standoff_xy"]:
        p -= cyl(2.4, -t - 1, 1, x, y)          # M2 clearance, PTH to GND on the real board
    p -= box(D["hole_x0"], D["hole_x1"], -D["hole_hy"], D["hole_hy"], -t - 1, 1)
    return p

def base(D):
    x0, x1, y0, y1 = D["base_x0"], D["base_x1"], D["base_y0"], D["base_y1"]
    cx0, cx1, cy0, cy1 = D["cav"]
    z1, zt0, zf = D["z_base1"], D["z_base_top0"], D["base_floor"]
    b = box(x0, x1, y0, y1, 0, z1) - box(cx0, cx1, cy0, cy1, zf, zt0)
    wx0, wx1, wy0, wy1 = D["win"]
    b -= box(wx0, wx1, wy0, wy1, zt0 - 0.01, z1 + 0.01)
    hx, hy = D["hdr_xy"]
    sw, sh, _ = D["sock"]
    b -= cbox(sw + 0.4, sh + 0.4, -0.01, zf + 0.01, hx, hy)
    sx, sy = D["sw_xy"]
    b += cyl(D["post_d"], zf - 0.01, D["z_db0"], sx, sy)
    for x, y in D["springs"]:
        b += cyl(D["spr_bore"] + 0.8, zf - 0.01, zt0 + 0.01, x, y)
    for x, y in D["springs"]:
        b -= cyl(D["spr_bore"], -0.1, z1 + 0.1, x, y)
    r = D["ball_d"] / 2 + D["seat_clear"]
    for x, y in D["balls"]:
        b -= Pos(x, y, z1) * Sphere(r)
    b -= box(D["hole_x0"], D["hole_x1"], -D["hole_hy"], D["hole_hy"], -0.1, z1 + 0.1)
    for x, y in D["pins"]:
        b += cyl(D["pin"][0], -D["pin"][1], 0.01, x, y)
    for x, y in D["standoff_xy"]:
        b -= cyl(D["standoff_d"] + 0.8, -0.1, zf + 0.8, x, y)   # the standoff stands on the PCB, not on the base floor
    # round stop: the boss rises off the base top and into a bore in the carrier floor
    qx, qy = D["stop_xy"]
    b += cyl(D["stop_d"], z1 - 0.01, D["z_c0"] + 0.55, qx, qy)
    return b

def carrier(D):
    cw, ch = D["car"]
    g = D["skirt_gap"]
    pw, ph = D["pocket"]
    c = cbox(cw, ch, D["z_skirt0"], D["z_car1"])
    # loose rectangular skirt: anti-rotation only (the round boss is the travel stop)
    c -= box(D["base_x0"] - g, D["base_x1"] + g, D["base_y0"] - g, D["base_y1"] + g,
             D["z_skirt0"] - 0.01, D["z_c0"])
    # glass well, then air under the glass down to the spider plate so only the land touches the screen
    c -= cbox(pw, ph, D["z_scr0"], D["z_car1"] + 0.01)
    c -= cbox(pw, ph, D["z_sp1"], D["z_scr0"] + 0.01)
    # spider frame sits on the ledge at z_sp0; the inner opening is the free travel
    c -= box(D["sp_x"][0], D["sp_x"][1], -D["sp_hy"], D["sp_hy"], D["z_sp0"], D["z_sp1"] + 0.01)
    c -= box(D["sp_in_x"][0], D["sp_in_x"][1], -D["sp_in_hy"], D["sp_in_hy"], D["z_floor1"], D["z_sp0"] + 0.01)
    sx, sy = D["sw_xy"]
    c += cyl(D["cup_od"], D["z_cup0"], D["z_c0"] + 0.01, sx, sy)
    c -= cyl(D["cup_bore"], D["z_cup0"] - 0.01, D["z_floor1"] + 0.01, sx, sy)
    for x, y in D["springs"]:
        c += cyl(D["spr_boss"][0], D["spr_z1"], D["z_c0"] + 0.01, x, y)
        # side slot so the spring eye slides off (easy to swap once the back-panel depth is known)
        c -= box(x - 0.65, x + 0.65, y - 2.2, y + 0.2, D["spr_z1"] - 0.01, D["z_c0"] + 0.02)
    # round-stop bore in the floor. Deeper than the boss, and wider by the travel radius
    qx, qy = D["stop_xy"]
    c -= cyl(D["stop_bore"], D["z_c0"] - 0.2, D["z_c0"] + 1.20, qx, qy)
    # FPC slot through the floor, plus a channel under the glass so the tail can bend [A]
    c -= box(D["slot_x"][0], D["slot_x"][1], -D["slot_hy"], D["slot_hy"], D["z_c0"] - 0.01, D["z_scr0"] + 0.01)
    bay = D["fpc_w"] / 2 + 0.7
    c -= box(D["slot_x"][0] - 0.3, pw / 2 + 0.01, -bay, bay, D["z_sp1"] - 1.8, D["z_scr0"] + 0.01)
    return c

def spider(D):
    """Same flexure as v0.1 (pad, arm width, plate thickness). The frame does not grow with the screen."""
    z0, z1 = D["z_sp0"], D["z_sp1"]
    x0, x1 = D["sp_x"]; hy = D["sp_hy"]; ix0, ix1 = D["sp_in_x"]; ihy = D["sp_in_hy"]
    px0, px1 = D["pad_x"]; phy = D["sp_pad"][1] / 2; w = D["sp_arm_w"]
    s = box(x0, x1, -hy, hy, z0, z1) - box(ix0, ix1, -ihy, ihy, z0 - 0.01, z1 + 0.01)
    s += box(px0, px1, -phy, phy, z0, z1)
    yb = (phy + ihy) / 2
    xm = D["sw_xy"][0]
    for sy in (1, -1):
        for (xa, xb) in ((px0 + w / 2 + 0.2, xm - 0.6 - w / 2), (px1 - w / 2 - 0.2, xm + 0.6 + w / 2)):
            lo, hi = sorted((xa, xb))
            ys = sorted((sy * phy, sy * yb)); s += box(xa - w / 2, xa + w / 2, ys[0] - 0.01, ys[1] + 0.01, z0, z1)
            s += box(lo - w / 2, hi + w / 2, sy * yb - w / 2, sy * yb + w / 2, z0, z1)
            ys = sorted((sy * yb, sy * ihy)); s += box(xb - w / 2, xb + w / 2, ys[0] - 0.01, ys[1] + 0.01, z0, z1)
    s += box(px0, px1, -phy, phy, z1 - 0.01, z1 + D["sp_land"])
    s += cyl(D["plunger_d"], D["z_plunger0"], z0 + 0.01, xm, D["sw_xy"][1])
    return s

def switch(D):
    sw = D["sw"]; x, y = D["sw_xy"]; z = D["z_db1"]
    body = Pos(x, y, z) * Rot(0, 0, D["sw_rot"]) * Box(sw["w"], sw["d"], sw["h"], align=A)
    stem = cyl(sw["stem_d"], z + sw["h"], D["z_stem_top"], x, y)
    return body, stem

def build(D):
    out = {}
    out["main PCB (proxy, local patch)"] = pcb(D)
    hx, hy = D["hdr_xy"]
    out["J2 socket 2x3 2.54 female 11 (main PCB)"] = cbox(*D["sock"][:2], 0, D["sock"][2], hx, hy)
    dx, dy = D["db_xy"]; dw, dh, dt = D["db"]
    db = cbox(dw, dh, D["z_db0"], D["z_db1"], dx, dy)
    for x, y in D["standoff_xy"]:
        db -= cyl(2.4, D["z_db0"] - 0.1, D["z_db1"] + 0.1, x, y)
    out["joystick daughterboard"] = db
    hw, hh, ht = D["hdr_body"]
    out["J1 header 2x3 2.54 male (body on top)"] = cbox(hw, hh, D["z_db1"], D["z_db1"] + ht, hx, hy)
    for i, (x, y) in enumerate(D["standoff_xy"]):
        # 0.02 short of each board so the contact is not a boolean sliver
        out[f"brass standoff M2x11 {i + 1}"] = cyl(D["standoff_d"], 0.02, D["z_db0"] - 0.02, x, y)
    body, stem = switch(D)
    out["SW1 SKRHADE010 body (45°)"] = body
    out["SW1 SKRHADE010 stem"] = stem
    out["joystick base (printed, glued)"] = base(D)
    for i, (x, y) in enumerate(D["balls"]):
        out[f"ball {i + 1} Ø{D['ball_d']:g} stainless"] = Pos(x, y, D["z_ball"]) * Sphere(D["ball_d"] / 2)
    out["joystick carrier (printed)"] = carrier(D)
    out["screen spider + plunger (printed)"] = spider(D)
    S = D["scr"]
    out["top screen " + S["part"]] = cbox(S["w"], S["h"], D["z_scr0"], D["scr_top"])
    t = D["fpc_t"]; fx = D["fpc_x"]
    # vertical drop, then a bend in the channel under the glass. Exit side is still [A]
    x_end = S["w"] / 2 + D["scr_clear"] - 0.7
    z_bend = D["z_sp1"] - 1.05
    out["screen FPC [A]"] = (
        box(fx - t / 2, fx + t / 2, -D["fpc_w"] / 2, D["fpc_w"] / 2, -D["pcb_t"] - 3.0, z_bend + t)
        + box(fx - t / 2, x_end, -D["fpc_w"] / 2, D["fpc_w"] / 2, z_bend, z_bend + t)
    )
    for i, (x, y) in enumerate(D["springs"]):
        out[f"hold-down spring {i + 1}"] = cyl(D["spr_d"], -D["pcb_t"] - 6.0, D["spr_z1"], x, y)
    return out
