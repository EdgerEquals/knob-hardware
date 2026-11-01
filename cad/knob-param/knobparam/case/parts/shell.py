"""Case v0.1 shell. build(D) -> parts. Every size comes from D (see params.py).

The print is one solid, open at the back. Reference parts (motor, mirror, film, VCSEL)
are not part of the print; they exist so the clearance checks have something to measure.
"""
import math
from build123d import *

A = (Align.CENTER, Align.CENTER, Align.MIN)
C = (Align.CENTER, Align.CENTER, Align.CENTER)


def _box(x0, x1, y0, y1, z0, z1):
    if x1 <= x0 or y1 <= y0 or z1 <= z0:
        return None
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=A)


def _add(a, b):
    if b is None:
        return a
    if a is None:
        return b
    return a + b


def _sub(a, b):
    if a is None or b is None:
        return a
    try:
        r = a - b
    except Exception:
        return a
    return a if r is None or not r.solids() else r


def _plate(w, h, r, z0, z1, x, y):
    return Pos(x, y, z0) * extrude(RectangleRounded(w, h, r), z1 - z0)


def _round_box(w, h, r, z0, z1, x, y):
    """Outside of the plain box. r is the plan-corner radius."""
    rr = min(r, w / 4.0, h / 4.0)
    return Pos(x, y, z0) * extrude(RectangleRounded(w, h, rr), z1 - z0)


def _cyl_z(r, z0, z1, x, y):
    if z1 <= z0 or r <= 0:
        return None
    return Pos(x, y, z0) * Cylinder(r, z1 - z0, align=A)


def _bead_y(x, z, y0, y1, r):
    """Fillet bead whose axis runs along Y. Three quarters bury in the joint; one fills the corner."""
    return Pos(x, y1, z) * Rot(90, 0, 0) * Cylinder(r, y1 - y0, align=A)


def _one(shape):
    sols = list(shape.solids())
    if len(sols) <= 1:
        return shape
    acc = sols[0]
    for s in sols[1:]:
        acc = acc.fuse(s)
    return acc


def _thread_groove(D, z0, length, internal):
    """One true 60° metric helix. internal=True is the void cut into a boss; False is the screw tooth."""
    p = D["screw_p"]
    d = D["screw_d"]
    fit = D["thread_fit"]
    if internal:
        r_in = (d - D["thread_int_k"] * p) / 2.0 + fit
        r_out = d / 2.0 + fit
        w_in = p * D["thread_root"]
        w_out = p * D["thread_crest"]
    else:
        r_in = (d - D["thread_ext_k"] * p) / 2.0
        r_out = d / 2.0 - fit
        w_in = p * D["thread_crest"] * (1.0 - D["thread_fit"])
        w_out = p * D["thread_root"] * (1.0 - D["thread_fit"])
    rp = (r_in + r_out) / 2.0
    hr = r_out - r_in
    path = Helix(pitch=p, height=length, radius=rp)
    s0 = path @ 0
    radial = Vector(s0.X, s0.Y, 0).normalized()
    pl = Plane(origin=s0, x_dir=Vector(0, 0, 1), y_dir=radial)
    pts = ((-w_in / 2.0, -hr / 2.0), (w_in / 2.0, -hr / 2.0), (w_out / 2.0, hr / 2.0), (-w_out / 2.0, hr / 2.0))
    return Pos(0, 0, z0) * sweep(pl * Polygon(*pts), path)


def _pilot(D, z0, z1, internal):
    p = D["screw_p"]
    d = D["screw_d"]
    if internal:
        r = (d - D["thread_int_k"] * p) / 2.0 + D["thread_fit"]
    else:
        r = (d - D["thread_ext_k"] * p) / 2.0
    return _cyl_z(r, z0, z1, 0.0, 0.0)


def _at(x, y, shape):
    if shape is None:
        return None
    return Pos(x, y, 0) * shape


def _tap(D, z0, length):
    """Printed internal thread: pilot hole plus the helical groove."""
    pilot = _pilot(D, z0 - D["screw_p"], z0 + length + D["screw_p"], internal=True)
    groove = _thread_groove(D, z0, length, internal=True)
    return _add(pilot, groove)


def _screw(D, z_head, z_shank1, z_th0, length, head_k=None, hex_s=None):
    """Socket head. z_head is the outer face of the head. Thread runs toward +Z from z_th0.

    A full-thread screw passes z_shank1 = z_th0 = the bearing face, so there is no plain shank.
    """
    d = D["screw_d"]
    k = D["head_k"] if head_k is None else head_k
    s = D["screw_hex"] if hex_s is None else hex_s
    head = _cyl_z(D["screw_dk"] / 2.0, z_head, z_head + k, 0.0, 0.0)
    shank = _cyl_z(d / 2.0 - D["thread_fit"], z_head + k, max(z_shank1, z_head + k), 0.0, 0.0)
    core = _pilot(D, z_th0, z_th0 + length, internal=False)
    tooth = _thread_groove(D, z_th0, length, internal=False)
    sock_r = (s / 2.0) / math.cos(math.radians(30.0))
    sock = Pos(0, 0, z_head) * Rot(0, 0, 30) * extrude(RegularPolygon(sock_r, 6), min(D["screw_socket"], k))
    return _sub(_add(_add(head, shank), _add(core, tooth)), sock)


def beam_solid(D):
    """Swept fan: along the inner left wall, along the inner bottom wall, and up to the rim."""
    t = D["beam_t"]
    x = D["beam_x"]
    y = D["beam_y"]
    z = D["z_mirror"]
    # along the left wall, from the mirror height, the full inner length
    side = _box(x - t / 2, x + t / 2, D["y_mot"], D["y_in1"] - D["fillet_r"], z - t / 2, z + t / 2)
    # up that wall to the underside of the faceplate (the edge strip)
    rise = _box(x - t / 2, x + t / 2, D["y_in0"] + D["fillet_r"], D["y_beam"] + D["mirror_r"],
                z, D["beam_z1"])
    # along the bottom wall
    bot = _box(D["x_mot"], D["x_in1"] - D["fillet_r"], y - t / 2, y + t / 2, z - t / 2, z + t / 2)
    return _add(_add(side, rise), bot)


def knob_envelope(D):
    """Cylinder the knob and the control dial both stay inside (same OD)."""
    return _cyl_z(D["knob_r"], D["z_seat"], D["z_knob_snap"], D["ox"], D["oy"])


def joy_envelope(D):
    """Carrier below the plate plus the bezel lip above it. Everything but the lip is below the plate."""
    below = _box(-D["car_hw"], D["car_hw"], D["place_y"] - D["car_hh"], D["place_y"] + D["car_hh"],
                 D["z_seat"], D["z_fp0"])
    lip = _box(-D["half_w"], D["half_w"], D["bezel_y_near"], D["bezel_y_far"], D["z_fp1"], D["z_bz1"])
    return _add(below, lip)


def build(D):
    sl = D["cut_slop"]
    fu = D["fuse"]
    # ---- one faceplate, full HP × 3U, one flat front at z_fp1 ----
    case = _round_box(D["panel_w"], D["panel_h"], D["edge_r"], D["z_fp0"], D["z_fp1"], D["ox"], D["panel_yc"])
    # body behind the rails: same width, inset in Y, radiused vertical corners. Hollow.
    bw, bh = D["panel_w"], D["body_y1"] - D["body_y0"]
    outer = _round_box(bw, bh, D["edge_r"], D["z_rim"], D["z_fp0"] + fu, D["ox"], D["body_yc"])
    ir = min(max(D["edge_r"] * 0.5, 0.05), (bw - 2 * D["wall"]) / 4.0, (bh - 2 * D["wall"]) / 4.0)
    inner = _round_box(bw - 2 * D["wall"], bh - 2 * D["wall"], ir, D["z_rim"] - sl, D["z_fp0"], D["ox"], D["body_yc"])
    case = _add(case, _sub(outer, inner))
    # ledge the PCB front sits against, inboard of the board edge
    lw, z0, z1 = D["ledge_w"], D["z_ledge0"], D["z_ledge1"]
    case = _add(case, _box(-D["pcb_x1"], D["pcb_x1"], D["pcb_y0"], D["pcb_y0"] + lw, z0, z1))
    case = _add(case, _box(-D["pcb_x1"], D["pcb_x1"], D["pcb_y1"] - lw, D["pcb_y1"], z0, z1))
    case = _add(case, _box(D["x_in0"], -D["pcb_x1"] + lw, D["pcb_y0"], D["pcb_y1"], z0, z1))
    case = _add(case, _box(D["pcb_x1"] - lw, D["x_in1"], D["pcb_y0"], D["pcb_y1"], z0, z1))
    # Side ledges run the full board height and would sit inside the TFT keep-out
    # (active area plus tft_gap). Pull only that ledge band back. Bosses are added
    # after this, on the safe side of the same gap. The faceplate over the window stays.
    eps = 0.02
    ky0, ky1 = D["win_y0"] - D["tft_gap"], D["win_y1"] + D["tft_gap"]
    case = _sub(case, _box(D["pcb_x1"] - lw - eps, min(D["x_in1"], D["win_x1"] + D["tft_gap"]),
                           ky0, ky1, z0 - eps, z1 + eps))
    case = _sub(case, _box(max(D["x_in0"], D["win_x0"] - D["tft_gap"]), -D["pcb_x1"] + lw + eps,
                           ky0, ky1, z0 - eps, z1 + eps))
    # corner posts beside the PCB. The thread is the lower part; the post runs up into the plate.
    for x, y in D["corners"]:
        case = _add(case, _cyl_z(D["screw_boss_r"], D["z_rim"], D["z_fp0"] + fu, x, y))
    # collar under the knob opening; the knob module slides down through it
    case = _add(case, _cyl_z(D["collar_r"], D["z_collar0"], D["z_fp0"] + fu, D["ox"], D["oy"]))
    for x, y in D["knob_bolts"]:
        case = _add(case, _cyl_z(D["screw_boss_r"], D["z_bolt0"], D["z_fp0"] + fu, x, y))
    if D["scanner_enabled"]:
        shelf = _box(D["shelf_x0"], D["shelf_x1"], D["shelf_y0"] - fu, D["shelf_y1"], D["shelf_z0"], D["shelf_z1"])
        cheek = _box(D["shelf_x0"], D["shelf_x1"], D["pcb_y0"], D["pcb_y0"] + lw, D["z_ledge1"] - fu, D["shelf_z1"])
        case = _add(case, _add(shelf, cheek))
    # ---- openings. The knob bore continues through the collar. ----
    case = _sub(case, _cyl_z(D["knob_hole_r"], D["z_collar0"] - sl, D["z_fp1"] + sl, D["ox"], D["oy"]))
    joy = _plate(D["joy_hole"][0], D["joy_hole"][1], D["hole_corner_r"], D["z_seat"] - sl, D["z_fp1"] + sl,
                 D["ox"], D["place_y"])
    case = _sub(case, joy)
    # rail holes through the flat face. No rebate, no light-pipe step, no thinned bridge.
    if D["rail_top_ok"]:
        for x in D["rail_x_top"]:
            case = _sub(case, _cyl_z(D["rail_hole_d"] / 2, D["z_fp0"] - sl, D["z_fp1"] + sl, x, D["rail_y_top"]))
    for x in D["rail_x_std"]:
        case = _sub(case, _cyl_z(D["rail_hole_d"] / 2, D["z_fp0"] - sl, D["z_fp1"] + sl, x, D["rail_y_bot"]))
    # seal ring: a short thin collar standing up around the knob opening
    ring = _cyl_z(D["lab_ring_r"], D["z_fp1"] - fu, D["lab_ring_z1"], D["ox"], D["oy"])
    ring = _sub(ring, _cyl_z(D["knob_hole_r"], D["z_fp1"] - fu - sl, D["lab_ring_z1"] + sl, D["ox"], D["oy"]))
    case = _add(case, ring)
    # printed threads
    for x, y in D["corners"]:
        case = _sub(case, _at(x, y, _tap(D, D["z_thread0"], D["tap_len"])))
    for x, y in D["knob_bolts"]:
        case = _sub(case, _at(x, y, _tap(D, D["z_bolt0"], D["tap_len"])))
    # cross-pin access, one hole through each side wall
    # the corner posts stand outboard of the wall, so the hole has to cross the post as well as the wall
    case = _sub(case, _box(D["x_out0"] - D["cross_pin_d"] - sl, D["x_in0"] + sl,
                           D["place_y"] - D["pin_hole_r"], D["place_y"] + D["pin_hole_r"],
                           D["pin_z"] - D["pin_hole_r"], D["pin_z"] + D["pin_hole_r"]))
    case = _sub(case, _box(D["x_in1"] - sl, D["x_out1"] + D["cross_pin_d"] + sl,
                           D["place_y"] - D["pin_hole_r"], D["place_y"] + D["pin_hole_r"],
                           D["pin_z"] - D["pin_hole_r"], D["pin_z"] + D["pin_hole_r"]))
    if D["scanner_enabled"]:
        case = _sub(case, _box(D["slot_x0"], D["slot_x1"], D["slot_y0"], D["slot_y1"], D["slot_z0"], D["slot_z1"]))
    # radius only the outside front edges, not the openings
    try:
        front = []
        for e in case.edges():
            c = e.center()
            if abs(c.Z - D["z_fp1"]) > 0.05:
                continue
            on_rim = (abs(abs(c.X) - D["panel_w"] / 2.0) < 0.3 or abs(c.Y - D["panel_y0"]) < 0.3
                      or abs(c.Y - D["panel_y1"]) < 0.3)
            if on_rim:
                front.append(e)
        if front:
            case = fillet(front, D["edge_r"])
    except Exception:
        pass
    case = _one(case)

    # ---- glow coat on the inside faces Ed brushes: the side walls, and the ledge lips ----
    g0, gt = D["glow_gap"], D["glow_t"]
    er = D["edge_r"]
    z_glow1 = D["z_fp0"] - er - g0
    glow = _box(D["x_in0"] + g0, D["x_in0"] + g0 + gt, D["y_in0"] + er, D["y_in1"] - er, D["z_ledge1"], z_glow1)
    glow = _add(glow, _box(D["x_in1"] - g0 - gt, D["x_in1"] - g0, D["y_in0"] + er, D["y_in1"] - er, D["z_ledge1"], z_glow1))
    # keep the lip coat inboard of the side ledges, which run the full board height
    gx0 = -D["pcb_x1"] + lw + g0
    gx1 = D["pcb_x1"] - lw - g0
    glow = _add(glow, _box(gx0, gx1, D["pcb_y0"] + lw + g0, D["pcb_y0"] + lw + g0 + gt, D["z_ledge0"], D["z_ledge1"]))
    glow = _add(glow, _box(gx0, gx1, D["pcb_y1"] - lw - g0 - gt, D["pcb_y1"] - lw - g0, D["z_ledge0"], D["z_ledge1"]))
    glow = _sub(glow, _plate(D["joy_hole"][0] + gt, D["joy_hole"][1] + gt, D["hole_corner_r"],
                             D["z_ledge0"] - sl, D["z_fp1"], D["ox"], D["place_y"]))
    if D["scanner_enabled"]:
        glow = _sub(glow, _box(D["shelf_x0"] - sl, D["shelf_x1"] + sl, D["shelf_y0"] - sl, D["shelf_y1"] + sl,
                               D["shelf_z0"] - sl, D["shelf_z1"] + sl))
    for x, y in D["corners"]:
        glow = _sub(glow, _cyl_z(D["screw_boss_r"] + D["glow_gap"], D["z_rim"] - sl, D["z_fp1"], x, y))
    glow = _sub(glow, _cyl_z(D["collar_r"] + D["glow_gap"], D["z_collar0"] - sl, D["z_fp1"], D["ox"], D["oy"]))
    glow = _sub(glow, _box(D["win_x0"], D["win_x1"], D["win_y0"], D["win_y1"], D["tft_z0"], D["tft_z1"]))

    # PETG cover. Outer skin is the same rectangle as the shell, so the side faces are one line.
    # The pocket is inside that skin. A tongue captures the PCB edge; the PCB never reaches the outside.
    ov = D["clamp_overlap"]
    cover = _box(D["x_out0"], D["x_out1"], D["body_y0"], D["body_y1"], D["z_cover_out"], D["z_rim_seat"])
    cover = _sub(cover, _box(D["void_x0"], D["void_x1"], D["void_y0"], D["void_y1"], D["z_cover_in"], D["z_rim_seat"] + sl))
    tongue = _box(D["void_x0"] - fu, D["void_x1"] + fu, D["void_y0"] - fu, D["void_y1"] + fu, D["z_flange_out"], D["z_rim_seat"])
    tongue = _sub(tongue, _box(-D["pcb_x1"] + ov, D["pcb_x1"] - ov, D["pcb_y0"] + ov, D["pcb_y1"] - ov,
                               D["z_flange_out"] - sl, D["z_rim_seat"] + sl))
    cover = _add(cover, tongue)
    land = _box(-D["pcb_x1"], D["pcb_x1"], D["pcb_y0"], D["pcb_y1"], D["z_rim_seat"], D["z_pcb_land"])
    land = _sub(land, _box(-D["pcb_x1"] + ov, D["pcb_x1"] - ov, D["pcb_y0"] + ov, D["pcb_y1"] - ov,
                           D["z_rim_seat"] - sl, D["z_pcb_land"] + sl))
    cover = _add(cover, land)
    for x, y in D["corners"]:
        cover = _add(cover, _cyl_z(D["pad_r"], D["z_pad_out"], D["z_flange_out"] + fu, x, y))
        cover = _sub(cover, _cyl_z(D["cbore_r"], D["z_pad_out"] - sl, D["z_pad_out"] + D["cbore_depth"], x, y))
        cover = _sub(cover, _cyl_z(D["hole_r"], D["z_pad_out"] - sl, D["z_rim_seat"] + sl, x, y))
    screws = {}
    for i, (x, y) in enumerate(D["corners"]):
        z_head = D["z_pad_out"] + D["head_below"]
        screws[f"corner screw {i + 1}"] = _at(x, y, _screw(D, z_head, D["z_screw_under"], D["z_screw_under"], D["screw_thread"]))
    for i, (x, y) in enumerate(D["knob_bolts"]):
        screws[f"knob bolt {i + 1}"] = _at(x, y, _screw(
            D, D["z_bolt0"] - D["bolt_head_k"], D["z_bolt0"], D["z_bolt0"], D["tap_len"],
            head_k=D["bolt_head_k"], hex_s=D["bolt_hex"]))
    pins = {}
    for i, x0, x1 in ((1, D["x_out0"] - D["cross_pin_d"], D["x_in0"]), (2, D["x_in1"], D["x_out1"] + D["cross_pin_d"])):
        pins[f"cross pin {i}"] = _box(x0, x1, D["place_y"] - D["cross_pin_d"] / 2.0, D["place_y"] + D["cross_pin_d"] / 2.0,
                                      D["pin_z"] - D["cross_pin_d"] / 2.0, D["pin_z"] + D["cross_pin_d"] / 2.0)

    motor = mirror = film = vcsel = None
    if D["scanner_enabled"]:
        motor = _cyl_z(D["motor_r"], D["z_mot0"], D["z_mot1"], D["x_mot"], D["y_mot"])
        mirror = _cyl_z(D["mirror_r"], D["z_mirror"] + fu, D["z_mirror"] + fu + D["mirror_t"], D["x_mot"], D["y_mot"])
        film = _box(D["x_beam"] - D["film_w"] / 2, D["x_beam"] + D["film_w"] / 2,
                    D["y_beam"] - D["film_w"] / 2, D["y_beam"] + D["film_w"] / 2,
                    D["shelf_z"] - D["film_t"] / 2, D["shelf_z"] + D["film_t"] / 2)
        vcsel = _box(D["x_vc"] - D["vcsel_l"] / 2, D["x_vc"] + D["vcsel_l"] / 2,
                     D["y_vc"] - D["vcsel_w"] / 2, D["y_vc"] + D["vcsel_w"] / 2, D["z_vc0"], D["z_vc1"])
    pcb = _box(-D["pcb_x1"], D["pcb_x1"], D["pcb_y0"], D["pcb_y1"], D["z_pcb_back"], 0.0)
    for x, y in D["corners"]:
        pcb = _sub(pcb, _cyl_z(D["notch_r"], D["z_pcb_back"] - sl, sl, x, y))
    # clear column over the bottom TFT: not a cutout, the resin here stays plain
    window = _box(D["win_x0"], D["win_x1"], D["win_y0"], D["win_y1"], D["tft_z0"], D["tft_z1"])
    lasers = {}
    for i, (x, y) in enumerate(D["lasers"]):
        lasers[f"laser placeholder {i + 1}"] = _box(
            x - D["laser_w"] / 2.0, x + D["laser_w"] / 2.0,
            y - D["laser_d"] / 2.0, y + D["laser_d"] / 2.0, D["tft_air"], D["tft_air"] + D["laser_h"])
    out = {"case": case, "back cover (PETG)": cover, "glow coat (inside walls)": glow,
           "PCB": pcb, "bottom TFT window": window}
    if D["scanner_enabled"]:
        out.update({"scanner motor (assumed)": motor, "scanner mirror (assumed)": mirror,
                    "grating film": film, "VCSEL 665 nm": vcsel})
    out.update(screws)
    out.update(pins)
    out.update(lasers)
    return out
