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
    if D.get("clear_oled"):   # v0.19b: the 42.04 clear OLED is wider than the gap between the side ledges; relieve them where it sits
        w, h, t = D["clear_oled"]; cx, cy = D["clear_oled_xy"]; g = 0.2
        case = _sub(case, _box(cx - w / 2 - g, cx + w / 2 + g, cy - h / 2 - g, cy + h / 2 + g, z0 - sl, t + 0.3))
    # v0.19: the v0.18 knob base (cradle r 20.9, knob land r 21.0) is wider than the gap between the side ledges.
    # The ledge is cut back round the knob; the PCB is still seated above and below it.
    case = _sub(case, _cyl_z(D["knob_hole_r"] + D["ledge_knob_clear"], z0 - sl, z1 + sl, D["ox"], D["oy"]))
    if D["tft_on_front"]:
        # Side ledges would cross a front window. Pull only that ledge band back.
        eps = 0.02
        ky0, ky1 = D["win_y0"] - D["tft_gap"], D["win_y1"] + D["tft_gap"]
        case = _sub(case, _box(D["pcb_x1"] - lw - eps, min(D["x_in1"], D["win_x1"] + D["tft_gap"]),
                               ky0, ky1, z0 - eps, z1 + eps))
        case = _sub(case, _box(max(D["x_in0"], D["win_x0"] - D["tft_gap"]), -D["pcb_x1"] + lw + eps,
                               ky0, ky1, z0 - eps, z1 + eps))
    # corner posts beside the PCB. The thread is the lower part; the post stops under the jack pins
    # and is fused to the side wall, so it does not need to reach the plate.
    for x, y in D["corners"]:
        case = _add(case, _cyl_z(D["screw_boss_r"], D["z_rim"], D["z_post_top"], x, y))
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
    # [Ed 4 Nov 10:03] the cutout starts just behind the faceplate (z_joy_cut0), so the top wall, the top ledge and the top corner posts stay
    # whole (v0.25 first cut: from z_seat - cut_slop, through the case's whole depth)
    joy = _plate(D["joy_hole"][0], D["joy_hole"][1], D["hole_corner_r"], D["z_joy_cut0"], D["z_fp1"] + sl,
                 D["ox"], D["place_y"])
    case = _sub(case, joy)
    if D.get("vb") and D.get("joy_cut_to") is not None:   # 4 Nov: the restored top ledge, notched right through round each vertical board
        V, a = D["vb"], D["vb_ledge_air"]
        for sx in (-1.0, 1.0):
            x0, x1 = sx * V["x"] - V["t"] / 2 - a, sx * V["x"] + V["t"] / 2 + a
            case = _sub(case, _box(x0, x1, D["pcb_y1"] - D["ledge_w"] - sl, min(D["pcb_y1"] + sl, D["y_in1"]),
                                   D["z_ledge0"] - sl, D["z_ledge1"] + sl))
    if D.get("joy_step"):   # v0.24 [Ed 14:02] top-edge seal: a rebate in the cutout wall from the faceplate back (top edge and the long sides
        # above where the joystick cradle's flange ends); the cradle's dam sits in it with the bead on its front face. None since v0.25 [Ed 18:35]:
        # the joystick cradle is printed into the case (assembly/build.py fuses it in)
        rw, rh = D["joy_reb"]; st = D["joy_step"]
        reb = _plate(rw, rh, D["hole_corner_r"] + st["w"], D["z_fp0"] - sl, D["z_fp0"] + st["d"], D["ox"], D["place_y"])
        reb = reb & _box(-60.0, 60.0, D["joy_step_y0"], D["panel_y1"] + 5.0, D["z_fp0"] - 2 * sl, D["z_fp0"] + st["d"] + sl)
        case = _sub(case, reb)
    # rail holes through the flat face. No rebate, no light-pipe step, no thinned bridge.
    if D["rail_top_ok"]:
        for x in D["rail_x_top"]:
            case = _sub(case, _cyl_z(D["rail_hole_d"] / 2, D["z_fp0"] - sl, D["z_fp1"] + sl, x, D["rail_y_top"]))
    for x in D["rail_x_std"]:
        case = _sub(case, _cyl_z(D["rail_hole_d"] / 2, D["z_fp0"] - sl, D["z_fp1"] + sl, x, D["rail_y_bot"]))
    # seal ring: a short thin collar standing up around the knob opening
    ring = _cyl_z(D["lab_ring_r"], D["z_fp1"] - fu, D["lab_ring_z1"], D["ox"], D["oy"])
    ring = _sub(ring, _cyl_z(D["knob_hole_r"], D["z_fp1"] - fu - sl, D["lab_ring_z1"] + sl, D["ox"], D["oy"]))
    if D.get("lab_ring_slope", 0) > 0:   # v0.19b: top falls outward (drips run away from the knob hole)
        z1, s, r0, r1 = D["lab_ring_z1"], D["lab_ring_slope"], D["knob_hole_r"], D["lab_ring_r"] + 0.01
        cut = revolve(Face(Wire.make_polygon([Vector(r0, 0, z1 + sl), Vector(r0, 0, z1), Vector(r1, 0, z1 - s), Vector(r1, 0, z1 + sl)], close=True)), Axis.Z, 360)
        ring = _sub(ring, Pos(D["ox"], D["oy"], 0) * cut)
    case = _add(case, ring)
    # printed threads
    for x, y in D["corners"]:
        if D["insert_od"]:
            # [Ed] M3 brass insert epoxied in the boss bottom; plain clearance above it for the screw tip
            case = _sub(case, _cyl_z(D["insert_od"] / 2 + D["insert_glue"], D["z_rim"] - sl, D["z_insert1"], x, y))
            case = _sub(case, _cyl_z(D["screw_d"] / 2 + 0.2, D["z_insert1"] - sl, D["z_tip"] + D["tip_hole"], x, y))
        else:
            case = _sub(case, _at(x, y, _tap(D, D["z_thread0"], D["tap_len"])))
    for x, y in D["knob_bolts"]:
        case = _sub(case, _at(x, y, _tap(D, D["z_bolt0"], D["tap_len"])))
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
        glow = _sub(glow, _cyl_z(D["screw_boss_r"] + D["glow_gap"], D["z_rim"] - sl, D["z_post_top"] + D["glow_gap"], x, y))
    glow = _sub(glow, _cyl_z(D["collar_r"] + D["glow_gap"], D["z_collar0"] - sl, D["z_fp1"], D["ox"], D["oy"]))
    if D["tft_on_front"]:
        glow = _sub(glow, _box(D["win_x0"], D["win_x1"], D["win_y0"], D["win_y1"], D["tft_z0"], D["tft_z1"]))

    # PETG cover. Outer skin is the same rectangle as the shell, so the side faces are one line.
    # The pocket is inside that skin. A tongue captures the PCB edge; the PCB never reaches the outside.
    ov = D["clamp_overlap"]
    cover = _box(D["x_out0"], D["x_out1"], D["body_y0"], D["body_y1"], D["z_cover_out"], D["z_rim_seat"])
    cover = _sub(cover, _box(D["void_x0"], D["void_x1"], D["void_y0"], D["void_y1"], D["z_cover_in"], D["z_rim_seat"] + sl))
    tubes = D["cover_clamp"] == "tubes"
    ovt = 0.0 if tubes else ov   # [Ed] 2 Nov: with corner tubes the tongue stays outside the board outline
    tongue = _box(D["void_x0"] - fu, D["void_x1"] + fu, D["void_y0"] - fu, D["void_y1"] + fu, D["z_flange_out"], D["z_rim_seat"])
    tongue = _sub(tongue, _box(-D["pcb_x1"] + ovt, D["pcb_x1"] - ovt, D["pcb_y0"] + ovt, D["pcb_y1"] - ovt,
                               D["z_flange_out"] - sl, D["z_rim_seat"] + sl))
    cover = _add(cover, tongue)
    # v0.19: the feel compound gear under the PCB reaches 0.3 past the board edge; relieve the tongue round it
    a = math.radians(D["mech_rot"]); fx, fy = D["fg_xy"]
    gx, gy = math.cos(a) * fx - math.sin(a) * fy, math.sin(a) * fx + math.cos(a) * fy
    cover = _sub(cover, _cyl_z(D["fg_tip"] + 0.3, D["z_cover_in"] + 0.5, D["z_rim_seat"] + sl, gx, gy))
    if tubes and D["cover_screw"] == "back":
        # v0.19b: slim solid column (clearance hole only) through the screen layer, 45° flare to the ring that bears on the board
        # round its notch; the screw head sits in a counterbore in the floor, right under the column
        for x, y in D["corners"]:
            t = _cyl_z(D["col_r"], D["z_cover_in"] - fu, D["col_z1"], x, y)
            if D["col_z2"] > D["col_z1"]:
                t = _add(t, Pos(x, y, D["col_z1"]) * Cone(D["col_r"], D["col_ring_r"], D["col_z2"] - D["col_z1"], align=A))
            t = _add(t, _cyl_z(D["col_ring_r"], D["col_z2"] - fu, D["z_pcb_land"], x, y))
            t = t & _box(D["void_x0"] - fu, D["void_x1"] + fu, D["void_y0"] - fu, D["void_y1"] + fu, D["z_cover_in"] - 2 * fu, D["z_pcb_land"] + fu)
            t = _sub(t, _cyl_z(D["notch_r"], D["z_pcb_land"] - 0.3, D["z_pcb_land"] + sl, x, y))   # relief: bears on the board only
            if D["back_screens"] == "amoled2" and D.get("amo_drop_air"):
                # v0.25 [Ed 19:12 (5)]: trim the flare and the ring where a screen drops in from above (its plan + amo_drop_air, from the
                # screen's own face up through the ring), so it goes straight down onto the floor; the slim column stays (col_screen_air)
                a_ = D["amo_drop_air"]
                for (sx0, sx1, sy0, sy1), (sz0, _sz1) in ((D["amo_upper"], D["amo_upper_z"]), (D["amo_lower"], D["amo_lower_z"])):
                    t = _sub(t, _box(sx0 - a_, sx1 + a_, sy0 - a_, sy1 + a_, sz0 + 0.01, D["z_pcb_land"] + sl))
            cover = _add(cover, t)
            cover = _sub(cover, _cyl_z(D["hole_r"], D["z_cover_out"] - sl, D["z_pcb_land"] + sl, x, y))
            cover = _sub(cover, _cyl_z(D["cbore_r"], D["z_cover_out"] - sl, D["z_cover_out"] + D["cbore_depth"], x, y))
    elif tubes:
        # PETG corner tubes from the cover floor up to the PCB back; each bears on the board round its corner notch
        for x, y in D["corners"]:
            t = _cyl_z(D["notch_r"] + D["tube_press"], D["z_cover_in"] - fu, D["z_pcb_land"], x, y)
            t = t & _box(D["void_x0"] - fu, D["void_x1"] + fu, D["void_y0"] - fu, D["void_y1"] + fu, D["z_cover_in"] - 2 * fu, D["z_pcb_land"] + fu)
            cover = _add(cover, _sub(t, _cyl_z(D["notch_r"], D["z_cover_in"] + D["cover_t"] * 0 + 1.0, D["z_pcb_land"] + sl, x, y)))   # bore = notch: bears on the board only
            cover = _sub(cover, _cyl_z(D["hole_r"], D["z_cover_in"] - sl, D["z_pcb_land"] + sl, x, y))
    else:
        land = _box(-D["pcb_x1"], D["pcb_x1"], D["pcb_y0"], D["pcb_y1"], D["z_rim_seat"], D["z_pcb_land"])
        land = _sub(land, _box(-D["pcb_x1"] + ov, D["pcb_x1"] - ov, D["pcb_y0"] + ov, D["pcb_y1"] - ov,
                               D["z_rim_seat"] - sl, D["z_pcb_land"] + sl))
        cover = _add(cover, land)
    for x, y in (D["corners"] if D["cover_screw"] != "back" else ()):
        cover = _add(cover, _cyl_z(D["pad_r"], D["z_pad_out"], D["z_flange_out"] + fu, x, y))
        cover = _sub(cover, _cyl_z(D["cbore_r"], D["z_pad_out"] - sl, D["z_pad_out"] + D["cbore_depth"], x, y))
        cover = _sub(cover, _cyl_z(D["hole_r"], D["z_pad_out"] - sl, D["z_rim_seat"] + sl, x, y))
    if not D["tft_on_front"] and D["back_screens"] != "amoled2":
        cover = _sub(cover, _box(D["win_x0"], D["win_x1"], D["win_y0"], D["win_y1"],
                                 D["z_cover_out"] - sl, D["z_cover_in"] + sl))
    screws = {}
    for i, (x, y) in enumerate(D["corners"]):
        z_head = (D["z_cover_out"] if D["cover_screw"] == "back" else D["z_pad_out"]) + D["head_below"]
        screws[f"corner screw {i + 1}"] = _at(x, y, _screw(D, z_head, D["z_screw_under"], D["z_screw_under"], D["screw_thread"]))
    for i, (x, y) in enumerate(D["knob_bolts"]):
        screws[f"knob bolt {i + 1}"] = _at(x, y, _screw(
            D, D["z_bolt0"] - D["bolt_head_k"], D["z_bolt0"], D["z_bolt0"], D["tap_len"],
            head_k=D["bolt_head_k"], hex_s=D["bolt_hex"]))

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
    amo = {}
    if D["back_screens"] == "amoled2":
        window = None; module = None
        g = 0.02
        x0, x1, y0, y1 = D["amo_upper"]; z0, z1 = D["amo_upper_z"]
        amo["back AMOLED upper (rear, on the cover floor)"] = _box(x0, x1, y0, y1, z0 + g, z1)
        x0, x1, y0, y1 = D["amo_lower"]; z0, z1 = D["amo_lower_z"]
        amo["back AMOLED lower (front, on a 1 mm pad)"] = _box(x0, x1, y0, y1, z0, z1)
        # the pad: a frame under the lower screen where it is not over the upper one
        oy = D["amo_upper"][2]
        if y0 < oy:
            amo[f"lower screen pad ({D['cover_mat']})"] = _box(x0, x1, y0, min(oy, y1) - g, D["z_cover_in"] + g, z0 - g)
    elif D["tft_on_front"]:
        window = _box(D["win_x0"], D["win_x1"], D["win_y0"], D["win_y1"], D["tft_z0"], D["tft_z1"])
        module = None
    else:
        window = _box(D["win_x0"] + D["nest_gap"], D["win_x1"] - D["nest_gap"],
                      D["win_y0"] + D["nest_gap"], D["win_y1"] - D["nest_gap"], D["back_z0"], D["back_z1"])
        module = _box(D["mod_x0"], D["mod_x1"], D["mod_y0"], D["mod_y1"], D["tft_z0"], D["tft_z1"])
    # [Ed] 2 Nov: four PJ366ST jacks and the USB-C on its own board behind the plate (no glow coat behind them)
    for x, y in D["jack_xy"]:
        glow = _sub(glow, _box(x - D["jack_w"] / 2 - 0.5, x + D["jack_w"] / 2 + 0.5, y - D["jack_h"] / 2 - 0.5, y + D["jack_h"] / 2 + 0.5,
                               D["jack_depth_z0"] - D["jack_pin_len"] - 1, D["z_fp1"] + 1))
    for x, y in D["jack_xy"]:
        case = _sub(case, _cyl_z(D["jack_hole"] / 2, D["z_fp0"] - sl, D["z_fp1"] + sl, x, y))
    ux, uy = D["usb_xy"]; uw, uh, ud = D["usb_rcpt"]
    case = _sub(case, _box(ux - uw / 2 - 0.15, ux + uw / 2 + 0.15, uy - uh / 2 - 0.15, uy + uh / 2 + 0.15, D["z_fp0"] - sl, D["z_fp1"] + sl))
    jacks = {}
    for i, (x, y) in enumerate(D["jack_xy"], 1):
        g = 0.02
        body = _box(x - D["jack_w"] / 2, x + D["jack_w"] / 2, y - D["jack_h"] / 2, y + D["jack_h"] / 2, D["jack_depth_z0"], D["z_fp0"] - g)
        pins = _box(x - 2.0, x + 2.0, y - 3.0, y + 3.0, D["jack_depth_z0"] - D["jack_pin_len"], D["jack_depth_z0"])
        bush = _cyl_z(D["jack_bush_d"] / 2, D["z_fp0"], D["z_fp1"] + D["jack_nut_t"], x, y)
        nut = _sub(_cyl_z(D["jack_nut_d"] / 2, D["z_fp1"] + g, D["z_fp1"] + D["jack_nut_t"], x, y), _cyl_z(D["jack_bush_d"] / 2 + 0.01, D["z_fp1"], D["z_fp1"] + D["jack_nut_t"] + 1, x, y))
        jacks[f"jack {i} PJ366ST body + pins [S]"] = _add(body, pins)
        jacks[f"jack {i} bushing"] = bush
        jacks[f"jack {i} nut"] = nut
    bw, bh, bt = D["usb_board"]
    jacks["USB-C receptacle [S]"] = _box(ux - uw / 2, ux + uw / 2, uy - uh / 2, uy + uh / 2, D["z_fp1"] - ud, D["z_fp1"] - 0.02)
    jacks["USB-C PD board"] = _box(ux - bw / 2, ux + bw / 2, uy - bh / 2, uy + bh / 2, D["z_fp1"] - ud - bt, D["z_fp1"] - ud)
    out = {"case": case, f"back cover ({D['cover_mat']})": cover, "glow coat (inside walls)": glow, "PCB": pcb}   # glow trimmed above
    if window is not None:
        out["back TFT window"] = window
    out.update(amo)
    if module is not None:
        out["back TFT module (placeholder)"] = module
    if D["scanner_enabled"]:
        out.update({"scanner motor (assumed)": motor, "scanner mirror (assumed)": mirror,
                    "grating film": film, "VCSEL 665 nm": vcsel})
    out.update(screws)
    if D["insert_od"]:
        for i, (x, y) in enumerate(D["corners"], 1):
            out[f"corner insert {i} M{D['screw_d']:g} brass"] = _sub(_cyl_z(D["insert_od"] / 2, D["z_rim"] + 0.02, D["z_insert1"], x, y),
                                                     _cyl_z(D["screw_d"] / 2, D["z_rim"] - 0.1, D["z_insert1"] + 0.1, x, y))
    out.update(jacks)
    return out
