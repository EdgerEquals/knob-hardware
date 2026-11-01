"""Top-screen joystick stack parts, v0.4: build(D) -> {name: solid}. Reads D only.

The carrier is a thin shell. The screen is glued to a separate bezel that floats on four catalog
compression springs. Each spring sits on an M2 grub screw in the carrier, set before the stack is
assembled. A flat plate glued on the daughterboard carries the ball seats. There is no spider,
no plunger, no round stop and no printed base.
"""
import math
from build123d import *

A = (Align.CENTER, Align.CENTER, Align.MIN)

def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=A)

def cbox(w, h, z0, z1, x=0.0, y=0.0):
    return box(x - w / 2, x + w / 2, y - h / 2, y + h / 2, z0, z1)

def cyl(d, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, z0) * Cylinder(d / 2, z1 - z0, align=A)

def cyl_x(d, x0, x1, y=0.0, z=0.0):
    """Cylinder along X, from x0 to x1."""
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(d / 2, abs(x1 - x0))

def hex_at(af, z0, z1, x=0.0, y=0.0):
    """Hex prism, across-flats `af`. A flat faces +y so the wrench flat is parallel to the PCB edge."""
    r = (af / 2) / math.cos(math.radians(30))
    return Pos(x, y, z0) * Rot(0, 0, 30) * extrude(RegularPolygon(radius=r, side_count=6), z1 - z0)

def notched(D, z0, z1):
    """Full corner rectangle, with the middle of each long side cut back to h_mid.

    The knob faces that middle edge. The four corners stay tall enough for a spring
    outside the glass, and they sit outside the knob's plan.
    """
    s = cbox(2 * D["half_w"], 2 * D["half_h"], z0, z1)
    if D["half_h"] > D["h_mid"] + 1e-6:
        s -= box(-D["x_notch"], D["x_notch"], D["h_mid"], D["half_h"] + 1.0, z0 - 0.05, z1 + 0.05)
        s -= box(-D["x_notch"], D["x_notch"], -(D["half_h"] + 1.0), -D["h_mid"], z0 - 0.05, z1 + 0.05)
    return s

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
    """Flat stiffener glued on the daughterboard. Ball seats stand on it.
    The standoff screws pass through the plate and the board together.
    No round stop, and no hole for the grub screws: those are outside this outline."""
    x0, x1, y0, y1 = D["board_x0"], D["board_x1"], D["board_y0"], D["board_y1"]
    p = box(x0, x1, y0, y1, D["z_plate0"], D["z_plate1"])
    p -= cyl(2 * D["cut_r"], D["z_plate0"] - 0.01, D["z_plate1"] + 0.01)
    for x, y in D["standoff_xy"]:
        p -= cyl(D["drill_m2"], D["z_plate0"] - 0.01, D["z_plate1"] + 0.01, x, y)
    for x, y in D["springs"]:
        p -= cyl(D["spr_bore"], D["z_plate0"] - 0.2, D["z_plate1"] + 0.2, x, y)
    for x, y in D["balls"]:
        p += cyl(2 * D["boss_r"], D["z_plate1"] - 0.01, D["z_rim_lo"], x, y)
        p -= Pos(x, y, D["z_sc_lo"]) * Sphere(D["cup_r"])
    for x, y in D["springs"]:
        p -= cyl(D["spr_bore"], D["z_plate0"] - 0.2, D["z_rim_lo"] + 0.2, x, y)
    return p

def _fpc_slot(D, z0, z1):
    """Vertical drop for the FPC, plus the in-plane run under the glass edge."""
    return box(D["slot_x"][0], D["slot_x"][1], -D["slot_hy"], D["slot_hy"], z0, z1)

def carrier(D):
    """Thin floor under the faceplate. Spring seats, cup, hold-down hooks, skirt. It fits through the faceplate hole."""
    c = cbox(2 * D["car_hw"], 2 * D["car_hh"], D["z_c0"], D["z_floor1"])
    for x, y in D["cs_xy"]:
        c -= cyl(2 * D["cs_bore_r"], D["z_seat"], D["z_floor1"] + 0.02, x, y)
        c += cyl(D["boss_d"], D["z_ins0"], D["z_c0"] + 0.01, x, y)
        c -= cyl(D["ins_hole"], D["z_ins0"] - 0.02, D["z_seat"] + 0.01, x, y)
    for x, y in D["balls"]:
        c += cyl(2 * D["boss_r"], D["z_rim_hi"], D["z_c0"] + 0.01, x, y)
        c -= Pos(x, y, D["z_sc_hi"]) * Sphere(D["cup_r"])
    c += cyl(D["cup_od"], D["z_cup0"], D["z_c0"] + 0.01)
    c -= cyl(D["cup_bore"], D["z_cup0"] - 0.01, D["z_floor1"] + 0.02)
    hook_w = D["spr_d"] * 0.325
    hook_reach = D["spr_d"] * 1.1
    for x, y in D["springs"]:
        c += cyl(D["spr_boss"][0], D["spr_z1"], D["z_c0"] + 0.01, x, y)
        c -= box(x - hook_w, x + hook_w, y - hook_reach, y + D["spr_boss"][1], D["spr_z1"] - 0.01, D["z_c0"] + 0.02)
    c -= box(D["slot_x"][0] - 0.5, D["slot_x"][1] + 0.5, -(D["slot_hy"] + 0.4), D["slot_hy"] + 0.4,
             D["z_c0"] - 0.5, D["z_floor1"] + 0.5)
    g, t = D["skirt_gap"], D["car_skirt"]
    x0, x1 = D["board_x0"] - g, D["board_x1"] + g
    y0, y1 = D["board_y0"] - g, D["board_y1"] + g
    skirt = box(x0 - t, x1 + t, y0 - t, y1 + t, D["z_skirt0"], D["z_c0"] + 0.01)
    skirt -= box(x0, x1, y0, y1, D["z_skirt0"] - 0.01, D["z_c0"] + 0.02)
    return c + skirt

def screen_carrier(D):
    """1.2 mm bezel. A lip around the glass, corner pads the springs push on, and the press peg."""
    b = cbox(2 * D["half_w"], 2 * D["half_h"], D["z_bz0"], D["z_bz1"])
    # glass opening. Corner pads stay, so the springs have a face and the glass has something to sit on.
    b -= cbox(D["pocket"][0], D["pocket"][1], D["z_roof"], D["z_bz1"] + 0.05)
    for x, y in D["cs_xy"]:
        b += cyl(2 * D["cs_bore_r"] + 1.2, D["z_bz0"], D["z_roof"], x, y)
        b -= cyl(2 * D["cs_bore_r"], D["z_bz0"] - 0.02, D["z_roof"], x, y)
    b += cyl(D["peg_d"], D["z_peg"], D["z_scr0"] - 0.05)
    b -= box(D["slot_x"][0] - 0.4, D["half_w"] + 0.2, -(D["slot_hy"] + 0.3), D["slot_hy"] + 0.3,
             D["z_bz0"] - 0.05, D["z_bz1"] + 0.05)
    return b

def faceplate(D):
    """Proxy for the one-piece case face, clear resin UTR-8100. Thickness is the ~2.5 mm wall.
    The lip overlaps the plate. A rebate lets the lip drop for the press without the switch being blocked."""
    m = 10.0
    p = cbox(2 * (D["half_w"] + m), 2 * (D["half_h"] + m), D["z_fp0"], D["z_fp1"])
    p -= cbox(2 * D["hole_hw"], 2 * D["hole_hh"], D["z_fp0"] - 0.05, D["z_fp1"] + 0.05)
    p -= cbox(2 * (D["half_w"] + D["tol_sla"]), 2 * (D["half_h"] + D["tol_sla"]),
              D["z_fp1"] - D["fp_rebate"], D["z_fp1"] + 0.05)
    return p

def rear_anchor(D):
    """Printed bar glued to the PCB back. Two pin bores along X, open on +x, each through one pair of hooks.
    A slot over each spring lets the hook be pulled down onto the pin with pliers."""
    b = box(D["ra_x0"], D["ra_x1"], D["ra_y0"], D["ra_y1"], D["ra_z0"], D["ra_z1"])
    sw = D["ra_slot"]
    for y in D["pin_y"]:
        b -= cyl_x(D["pin_bore"], D["ra_x0"] + D["ra_wall"], D["ra_x1"] + 0.05, y, D["z_pin"])
        for x in (D["spr_x"], -D["spr_x"]):
            b -= box(x - sw / 2, x + sw / 2, y - sw / 2, y + sw / 2, D["z_pin"] - D["eye_ro"], D["ra_z1"] + 0.05)
    return b

def hold_down(D, x, y):
    """Spring body plus the lower hook eye. The eye clears the cross pin so the pin can be pushed through."""
    top = D["z_pin"] + D["eye_major"]
    body = cyl(D["spr_d"], top - 0.05, D["spr_z1"], x, y)
    eye = Pos(x, y, D["z_pin"]) * Rot(0, 90, 0) * Torus(D["eye_major"], D["eye_minor"])
    return body + eye

def cross_pin(D, y):
    """Shaft along X through both hooks at this y, with a head outside the +x mouth."""
    shaft = cyl_x(D["pin_d"], D["pin_x0"], D["pin_x1"], y, D["z_pin"])
    head = cyl_x(D["pin_head_d"], D["ra_x1"] + 0.25, D["ra_x1"] + 0.25 + D["pin_head_t"], y, D["z_pin"])
    return shaft + head

def insert(D, x, y):
    """Slip-fit model of the heat-set insert. The real one is an interference fit; that is not a solid overlap."""
    s = cyl(D["ins_od_model"], D["z_ins0"], D["z_seat"] - 0.02, x, y)
    s -= cyl(D["ins_id_model"], D["z_ins0"] - 0.04, D["z_seat"], x, y)
    return s

def switch(D):
    sw = D["sw"]; x, y = D["sw_xy"]; z = D["z_db1"]
    body = Pos(x, y, z) * Rot(0, 0, D["sw_rot"]) * Box(sw["w"], sw["d"], sw["h"], align=A)
    stem = cyl(sw["stem_d"], z + sw["h"], D["z_stem_top"], x, y)
    return body, stem

def build(D):
    out = {}
    out["main PCB (proxy, local patch)"] = pcb(D)
    out["faceplate (case proxy, UTR-8100)"] = faceplate(D)
    dx0, dx1, dy0, dy1 = D["board_x0"], D["board_x1"], D["board_y0"], D["board_y1"]
    db = box(dx0, dx1, dy0, dy1, D["z_db0"], D["z_db1"])
    for x, y in D["standoff_xy"]:
        db -= cyl(D["drill_m2"], D["z_db0"] - 0.1, D["z_db1"] + 0.1, x, y)
    for x, y in D["springs"]:
        db -= cyl(D["spr_bore"], D["z_db0"] - 0.1, D["z_db1"] + 0.1, x, y)
    out["joystick daughterboard"] = db
    hw, hh, ht = D["hdr_len"], D["hdr_wid"], D["hdr"]["ins"]
    pin_d = D["pitch"] * 0.25
    wall = D["part_gap"]
    for i, (x, y) in enumerate(D["hdr_xy"]):
        out[f"header 1x3 long pin {i + 1} (underside)"] = cbox(hw, hh, D["z_db0"] - ht, D["z_db0"], x, y)
        sock = cbox(hw, hh, 0, D["sock"]["h"], x, y)
        sock -= cbox(hw - 2 * wall, hh - 2 * wall, D["sock"]["h"] - D["mate_in"] - wall, D["sock"]["h"] + 0.02, x, y)
        out[f"socket 1x3 H11 {i + 1} (main PCB)"] = sock
        z_tip = D["z_db0"] - ht - D["hdr"]["mate"]
        for k in (-1, 0, 1):
            out[f"header pin {i + 1}.{k + 2}"] = cyl(pin_d, z_tip, D["z_db0"] - ht, x + k * D["pitch"], y)
    for i, (x, y) in enumerate(D["standoff_xy"]):
        # hex body is the derived riser. The catalog stud continues down through the main PCB.
        body = cyl(D["standoff_d"], 0.02, D["z_db0"] - 0.02, x, y)
        stud = cyl(D["stud_d"], D["z_stud0"], 0.04, x, y)
        out[f"brass standoff M2x{D['riser_h']:.2f} {i + 1}"] = body + stud
        nut = hex_at(D["nut"]["af"], D["z_nut0"], D["z_nut1"], x, y)
        nut -= cyl(D["stud_d"] + 0.30, D["z_nut0"] - 0.04, D["z_nut1"] + 0.04, x, y)
        out[f"M2 nut {i + 1}"] = nut
    body, stem = switch(D)
    out["SW1 SKRHADE010 body (45°)"] = body
    out["SW1 SKRHADE010 stem"] = stem
    out["seat plate (printed, glued)"] = plate(D)
    for i, (x, y) in enumerate(D["balls"]):
        out[f"ball {i + 1} Ø{D['ball_d']:g} stainless"] = Pos(x, y, D["z_ball"]) * Sphere(D["ball_d"] / 2)
    out["joystick carrier (printed)"] = carrier(D)
    out["screen carrier (printed)"] = screen_carrier(D)
    for i, (x, y) in enumerate(D["cs_xy"]):
        out[f"brass insert {i + 1}"] = insert(D, x, y)
        out[f"grub screw {i + 1}"] = cyl(D["grub_d_model"], D["z_tip"] - D["grub"]["length"], D["z_tip"], x, y)
        out[f"compression spring {i + 1}"] = cyl(D["cs"]["od"], D["z_tip"] + 0.02, D["z_roof"] - 0.02, x, y)
    S = D["scr"]
    glass = cbox(S["w"], S["h"], D["z_scr0"] + 0.02, D["scr_top"])
    for x, y in D["cs_xy"]:
        glass -= cyl(2 * D["cs_bore_r"] + 1.4, D["z_scr0"] - 0.05, D["z_roof"] + 0.05, x, y)
    out["top screen " + S["part"]] = glass
    t = D["fpc_t"]
    fx = D["fpc_x"]
    z_run = D["z_scr0"] - 0.55 + D["tol_mjf"]
    out["screen FPC [A]"] = (
        box(fx - t / 2, fx + t / 2, -D["fpc_w"] / 2, D["fpc_w"] / 2, -D["pcb_t"] - 3.0, z_run + t)
        + box(min(fx, S["w"] / 2 - 0.4) - t / 2, max(fx, S["w"] / 2 - 0.2), -D["fpc_w"] / 2, D["fpc_w"] / 2, z_run, z_run + t)
    )
    out["rear spring anchor (printed)"] = rear_anchor(D)
    for i, y in enumerate(D["pin_y"]):
        out[f"cross pin {i + 1}"] = cross_pin(D, y)
    for i, (x, y) in enumerate(D["springs"]):
        out[f"hold-down spring {i + 1}"] = hold_down(D, x, y)
    return out
