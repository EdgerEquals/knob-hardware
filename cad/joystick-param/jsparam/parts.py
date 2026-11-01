"""Top-screen joystick stack parts, v0.3: build(D) -> {name: solid}. Reads D only.

The carrier is a thin shell. The screen stays up near the knob top and the switch is raised on the
35 mm riser so it sits just under that shell. A flat plate glued on the daughterboard carries the
four ball seats and the round stop. There is no printed base enclosure.
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
    x0, x1 = -D["pcb_w"] / 2, D["pcb_w"] / 2
    y1 = D["y_pcb"]
    y0 = -D["place_y"] - D["scr"]["h"] / 2
    p = box(x0, x1, y0, y1, -t, 0)
    for x, y in D["springs"]:
        p -= cyl(D["spr_bore"], -t - 1, 1, x, y)
    for x, y in D["standoff_xy"]:
        p -= cyl(D["drill_m2"], -t - 1, 1, x, y)
    p -= box(D["hole_x0"], D["hole_x1"], -D["hole_hy"], D["hole_hy"], -t - 1, 1)
    return p

def plate(D):
    """Flat stiffener glued on the daughterboard. Ball seats and the round stop stand on it.
    The standoff screws pass through the plate and the board together."""
    x0, x1, y0, y1 = D["board_x0"], D["board_x1"], D["board_y0"], D["board_y1"]
    p = box(x0, x1, y0, y1, D["z_plate0"], D["z_plate1"])
    p -= cyl(2 * D["cut_r"], D["z_plate0"] - 0.01, D["z_plate1"] + 0.01)
    for x, y in D["standoff_xy"]:
        p -= cyl(D["drill_m2"], D["z_plate0"] - 0.01, D["z_plate1"] + 0.01, x, y)
    for x, y in D["balls"]:
        p += cyl(2 * D["boss_r"], D["z_plate1"] - 0.01, D["z_ball"], x, y)
        p -= Pos(x, y, D["z_ball"]) * Sphere(D["seat_r"])
    qx, qy = D["stop_xy"]
    # stop short of the bore roof so the closest approach is the radial gap, not a coplanar face
    p += cyl(D["stop_d"], D["z_plate1"] - 0.01, D["z_c0"] + D["stop_engage"] - D["part_gap"], qx, qy)
    return p

def carrier(D):
    cw, ch = D["car"]
    g, t = D["skirt_gap"], D["car_skirt"]
    pw, ph = D["pocket"]
    c = cbox(cw, ch, D["z_c0"], D["z_car1"])
    # glass well, then air under the glass down to the spider plate so only the land touches the screen
    c -= cbox(pw, ph, D["z_scr0"], D["z_car1"] + 0.01)
    c -= cbox(pw, ph, D["z_sp1"], D["z_scr0"] + 0.01)
    c -= box(D["sp_x"][0], D["sp_x"][1], -D["sp_hy"], D["sp_hy"], D["z_sp0"], D["z_sp1"] + 0.01)
    c -= box(D["sp_in_x"][0], D["sp_in_x"][1], -D["sp_in_hy"], D["sp_in_hy"], D["z_floor1"], D["z_sp0"] + 0.01)
    sx, sy = D["sw_xy"]
    c += cyl(D["cup_od"], D["z_cup0"], D["z_c0"] + 0.01, sx, sy)
    c -= cyl(D["cup_bore"], D["z_cup0"] - 0.01, D["z_floor1"] + 0.01, sx, sy)
    hook_w = D["spr_d"] * 0.325
    hook_reach = D["spr_d"] * 1.1
    for x, y in D["springs"]:
        c += cyl(D["spr_boss"][0], D["spr_z1"], D["z_c0"] + 0.01, x, y)
        c -= box(x - hook_w, x + hook_w, y - hook_reach, y + D["spr_boss"][1], D["spr_z1"] - 0.01, D["z_c0"] + 0.02)
    qx, qy = D["stop_xy"]
    c -= cyl(D["stop_bore"], D["z_c0"] - D["part_gap"], D["z_c0"] + D["stop_engage"], qx, qy)
    c -= box(D["slot_x"][0], D["slot_x"][1], -D["slot_hy"], D["slot_hy"], D["z_c0"] - 0.01, D["z_scr0"] + 0.01)
    bay = D["fpc_w"] / 2 + D["scr_clear"] * 3.5
    c -= box(D["slot_x"][0] - D["scr_clear"] * 1.5, pw / 2 + 0.01, -bay, bay, D["z_sp1"] - D["sp_t"] * 3, D["z_scr0"] + 0.01)
    # skirt: a print-minimum wall around the plate, only as tall as the plate. The floor above it is thin
    x0, x1 = D["board_x0"] - g, D["board_x1"] + g
    y0, y1 = D["board_y0"] - g, D["board_y1"] + g
    skirt = box(x0 - t, x1 + t, y0 - t, y1 + t, D["z_skirt0"], D["z_c0"] + 0.01)
    skirt -= box(x0, x1, y0, y1, D["z_skirt0"] - 0.01, D["z_c0"] + 0.02)
    return c + skirt

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
    dx0, dx1, dy0, dy1 = D["board_x0"], D["board_x1"], D["board_y0"], D["board_y1"]
    db = box(dx0, dx1, dy0, dy1, D["z_db0"], D["z_db1"])
    for x, y in D["standoff_xy"]:
        db -= cyl(D["drill_m2"], D["z_db0"] - 0.1, D["z_db1"] + 0.1, x, y)
    out["joystick daughterboard"] = db
    hw, hh, ht = D["hdr_len"], D["hdr_wid"], D["hdr"]["ins"]
    pin_d = D["pitch"] * 0.25          # 0.025 inch square post, drawn round
    wall = D["part_gap"]
    for i, (x, y) in enumerate(D["hdr_xy"]):
        out[f"header 1x3 long pin {i + 1} (underside)"] = cbox(hw, hh, D["z_db0"] - ht, D["z_db0"], x, y)
        # the H11 body is a shell: the pin enters mate_in and stops short of the floor
        sock = cbox(hw, hh, 0, D["sock"]["h"], x, y)
        sock -= cbox(hw - 2 * wall, hh - 2 * wall, D["sock"]["h"] - D["mate_in"] - wall, D["sock"]["h"] + 0.02, x, y)
        out[f"socket 1x3 H11 {i + 1} (main PCB)"] = sock
        z_tip = D["z_db0"] - ht - D["hdr"]["mate"]
        for k in (-1, 0, 1):
            out[f"header pin {i + 1}.{k + 2}"] = cyl(pin_d, z_tip, D["z_db0"] - ht, x + k * D["pitch"], y)
    for i, (x, y) in enumerate(D["standoff_xy"]):
        out[f"brass standoff M2x35 {i + 1}"] = cyl(D["standoff_d"], 0.02, D["z_db0"] - 0.02, x, y)
    body, stem = switch(D)
    out["SW1 SKRHADE010 body (45°)"] = body
    out["SW1 SKRHADE010 stem"] = stem
    out["seat plate (printed, glued)"] = plate(D)
    for i, (x, y) in enumerate(D["balls"]):
        out[f"ball {i + 1} Ø{D['ball_d']:g} stainless"] = Pos(x, y, D["z_ball"]) * Sphere(D["ball_d"] / 2)
    out["joystick carrier (printed)"] = carrier(D)
    out["screen spider + plunger (printed)"] = spider(D)
    S = D["scr"]
    out["top screen " + S["part"]] = cbox(S["w"], S["h"], D["z_scr0"], D["scr_top"])
    t = D["fpc_t"]; fx = D["fpc_x"]
    x_end = S["w"] / 2 + D["scr_clear"] - D["scr_clear"] * 3.5
    z_bend = D["z_sp1"] - D["sp_t"] * 1.75
    out["screen FPC [A]"] = (
        box(fx - t / 2, fx + t / 2, -D["fpc_w"] / 2, D["fpc_w"] / 2, -D["pcb_t"] - 3.0, z_bend + t)
        + box(fx - t / 2, x_end, -D["fpc_w"] / 2, D["fpc_w"] / 2, z_bend, z_bend + t)
    )
    for i, (x, y) in enumerate(D["springs"]):
        out[f"hold-down spring {i + 1}"] = cyl(D["spr_d"], -D["pcb_t"] - 6.0, D["spr_z1"], x, y)
    return out
