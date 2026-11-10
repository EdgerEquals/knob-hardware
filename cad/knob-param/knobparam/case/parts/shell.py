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


def _arc(cy, cz, r, a0, a1, n=16):
    return [(cy + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)), cz + r * math.sin(math.radians(a0 + (a1 - a0) * k / n)))
            for k in range(n + 1)]


def _link_flex(D):
    """Q29 [Ed 7 Nov] = A: the link flex on its J path (params._link_flex) and its stiffener, as solids. The y-z outline is the
    centreline offset to both faces, the bends as 16-segment arcs; extruded over the flex's width in x."""
    L = D["link_flex"]; t = L["t"]
    y0, y1 = L["pad_y"]; z0 = D["lf_z0"]; rb, rt = D["lf_rb"], D["lf_rt"]; yi = D["lf_y_in"]
    zbc, ztc, ye = D["lf_zbc"], D["lf_ztc"], D["lf_y_end"]
    inner = ([(y1, z0 + t), (y0, z0 + t)] + _arc(y0, zbc, rb, 270, 180)[1:] + [(yi, ztc)]
             + _arc(yi + rt, ztc, rt, 180, 90)[1:] + [(ye, ztc + rt)])
    outer = ([(y1, z0), (y0, z0)] + _arc(y0, zbc, rb + t, 270, 180)[1:] + [(yi - t, ztc)]
             + _arc(yi + rt, ztc, rt + t, 180, 90)[1:] + [(ye, ztc + rt + t)])
    pts = inner + outer[::-1]
    x0, x1 = D["lf_x"]
    face = Polygon(*[(y, z) for y, z in pts], align=None)
    fl = Pos(x0, 0, 0) * extrude(Plane.YZ * face, amount=x1 - x0)
    zt = ztc + rt   # the flex's underside on the top run; the stiffener goes under it
    st = _box(x0 + 0.07, x1 - 0.07, ye - L["stiff"], ye, zt - (L["t_end"] - t), zt)   # [S Hirose] (0.07) inside each edge
    return fl, st


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
    for i, (x, y) in enumerate(D["corners"]):
        post = _cyl_z(D["screw_boss_r"], D["z_rim"], D["z_post_top"], x, y)
        if i < 2 and D.get("post_clip_y") is not None:   # [Ed 4 Nov 20:12] bottom pair: cut flat under the jacks' path, kept inside the body
            post = post & _box(x - 2 * D["screw_boss_r"], x + 2 * D["screw_boss_r"], D["body_y0"], D["post_clip_y"], D["z_rim"] - 1.0,
                               D["z_post_top"] + 1.0)
        case = _add(case, post)
    if D.get("jb_tongue_y") is not None:   # v0.39 [Ed 15:53 Q15 = A]: the bottom ledge notched round each jack-board tongue
        n_ = D["jack_ledge_notch"]
        for tx0, tx1 in D["jb_tongue_x"]:
            case = _sub(case, _box(tx0 - n_, tx1 + n_, D["jb_tongue_y"] - n_, D["pcb_y0"] + D["ledge_w"] + sl,
                                   z0 - sl, z1 + sl))
    if D.get("jack_lip_notch") is not None:   # [Ed 4 Nov 20:12] side ledges notched along the jack row: jacks 1 and 4 pass from behind
        ny0, ny1 = D["jack_notch_y"]
        case = _sub(case, _box(D["x_in0"], -D["pcb_x1"] + lw + sl, ny0, ny1, z0 - sl, z1 + sl))
        case = _sub(case, _box(D["pcb_x1"] - lw - sl, D["x_in1"], ny0, ny1, z0 - sl, z1 + sl))
    if D["collar_h"] > 0:   # collar under the knob opening (none since 10 Nov, collar_h_mult 0)
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
    if D.get("joy_cut_to") is not None:   # 4 Nov: the top ledge stays cut where the joystick top board passes up from the back
        h = D["joy_tb_pass"]
        case = _sub(case, _box(-h + D["ox"], h + D["ox"], D["pcb_y1"] - D["ledge_w"] - sl, min(D["pcb_y1"] + sl, D["y_in1"]),
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
    if D.get("jb_tongue_y") is not None:   # v0.39: and where the jack board's tongues pass
        for tx0, tx1 in D["jb_tongue_x"]:
            m_ = D["jack_ledge_notch"] + 0.35
            glow = _sub(glow, _box(tx0 - m_, tx1 + m_, D["pcb_y0"] - 1.0, D["jack_bot_y"], D["z_rim"] - sl, D["z_fp1"]))
    if D.get("jb_on") and D.get("jb_post_xy"):   # v0.34 [Ed 22:21] the bottom lip's coat stays off where the jack unit's posts and ears pass
        for x, _y in D["jb_post_xy"]:
            glow = _sub(glow, _box(x - 1.6, x + 1.6, D["pcb_y0"] - 1.0, D["jack_bot_y"], D["z_rim"] - sl, D["z_fp1"]))
    if "lf_x" in D:   # Q29 [A]: and along the link flex's lane, where its bottom bend comes out towards the ledge (the coat stood 0.35 in)
        glow = _sub(glow, _box(D["lf_x"][0] - 0.5, D["lf_x"][1] + 0.5, D["pcb_y0"] - 1.0, D["jack_bot_y"], D["z_rim"] - sl, D["z_fp1"]))
    if D.get("jack_lip_notch") is not None:   # [Ed 4 Nov 20:12] no side coat along the jacks' path (it stood 0.15 into jacks 1 and 4)
        ny0, ny1 = D["jack_notch_y"]
        glow = _sub(glow, _box(D["x_in0"] - sl, D["x_in0"] + g0 + gt + sl, ny0, ny1, D["z_rim"] - sl, D["z_fp1"]))
        glow = _sub(glow, _box(D["x_in1"] - g0 - gt - sl, D["x_in1"] + sl, ny0, ny1, D["z_rim"] - sl, D["z_fp1"]))
    if D["collar_h"] > 0:
        glow = _sub(glow, _cyl_z(D["collar_r"] + D["glow_gap"], D["z_collar0"] - sl, D["z_fp1"], D["ox"], D["oy"]))
    else:   # no collar: the coat only stays out of the knob hole
        glow = _sub(glow, _cyl_z(D["knob_hole_r"] + D["glow_gap"], D["z_ledge0"] - sl, D["z_fp1"], D["ox"], D["oy"]))
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
    # v0.19: the feel compound gear under the PCB reaches 0.3 past the board edge; relieve the tongue round it (Q27: only with it)
    if D["feel_on"]:
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
        glow = _sub(glow, _box(x - D["jack_w"] / 2 - 0.5, x + D["jack_w"] / 2 + 0.5, D["jack_bot_y"] - 0.5, D["jack_top_y"] + 0.5,
                               D["jack_depth_z0"] - D["jack_pin_len"] - 1, D["z_fp1"] + 1))
    for x, y in D["jack_xy"]:
        case = _sub(case, _cyl_z(D["jack_hole"] / 2, D["z_fp0"] - sl, D["z_fp1"] + sl, x, y))
    ux, uy = D["usb_xy"]; uw, uh, ud = D["usb_rcpt"]
    zr0 = D["usb_z1"] - 0.01 if D.get("usb_slot") else D["z_fp0"] - sl   # [Ed 20:15] the receptacle's pocket runs back through the wall
    case = _sub(case, _box(ux - uw / 2 - 0.15, ux + uw / 2 + 0.15, uy - uh / 2 - 0.15, uy + uh / 2 + 0.15, zr0, D["z_fp1"] + sl))
    key = None
    if D.get("usb_slot"):
        # [Ed 4 Nov 20:15] channel through the bottom wall and the bottom ledge, from the back edge to the board's front face; the wall
        # left in front of the board is its ledge. A printed key fills the channel behind the board (and restores the ledge strip), held
        # in by the back cover alone.
        hw = D["usb_ch_hw"]
        chan = _box(ux - hw, ux + hw, D["body_y0"] - sl, D["pcb_y0"] + D["ledge_w"] + sl, D["z_rim"] - sl, D["usb_z1"])
        case = _sub(case, chan)
        glow = _sub(glow, chan)
        # v0.36b: the bottom lip's coat stays off across the channel width, up past the board's top edge (the v0.36 assembly check: the
        # board, and the jack board's tab as the shell comes down, passed a 0.15 sliver of it left above the channel cut)
        glow = _sub(glow, _box(ux - hw, ux + hw, D["pcb_y0"] - 1.0, D["usb_board_y1"] + 0.6, D["z_rim"] - sl, D["z_fp1"]))
        kw, kg = hw - D["usb_key_gap"], 0.02
        key = _box(ux - kw, ux + kw, D["body_y0"], D["y_in0"] - D["usb_key_gap"], D["z_rim_seat"] + kg, D["usb_z0"] - kg)
        for _n, a, b, c, d, h in D.get("usb_prot") or ():   # v0.37 [Ed 5 Nov 11:24]: pockets for the board's TVS and ESD
            pc = D["usb_pocket_clear"]
            key = _sub(key, _box(a - pc, b + pc, c - pc, d + pc, D["usb_z0"] - h - pc, D["usb_z0"] + 0.1))
        if D.get("usb_pwr_tab") and D.get("jb_on") and D.get("usb_key_tab_step"):   # v0.41 [Ed 5 Nov 17:36 Q16 = A]: a step along the tab's path
            kt = D["y_in0"] - D["usb_key_gap"]
            key = _sub(key, _box(ux - kw - sl, ux + kw + sl, kt - D["usb_key_tab_step"], kt + sl, D["z_rim_seat"] - sl, D["jb_z1"] + 0.3))
        if not D.get("usb_pwr_tab"):   # v0.32-v0.34: the key's tab restored the bottom ledge in the channel (v0.35: the jack board's tab passes there)
            key = _add(key, _box(ux - kw, ux + kw, D["y_in0"] - D["usb_key_gap"] - D["fuse"], D["pcb_y0"] + D["ledge_w"], D["z_ledge0"],
                                 D["z_ledge1"]))
    jacks = {}
    for i, (x, y) in enumerate(D["jack_xy"], 1):
        g = 0.02
        body = _box(x - D["jack_w"] / 2, x + D["jack_w"] / 2, D["jack_bot_y"], D["jack_top_y"], D["jack_depth_z0"], D["z_fp0"] - g)
        if D.get("jack_pins"):   # v0.39: tip, ring, sleeve at their published positions [S-lib]; the sleeve pin hangs below the body
            pins = None
            for _n, y0, _y1, _w in D["jack_pins"]:
                p_ = _cyl_z(D["jack_pin_d"] / 2, D["jack_depth_z0"] - D["jack_pin_len"], D["jack_depth_z0"] + 0.01, x, y + y0)
                if y + y0 < D["jack_bot_y"]:   # its lug up to the body
                    p_ = _add(p_, _box(x - D["jack_pin_d"] / 2, x + D["jack_pin_d"] / 2, y + y0, D["jack_bot_y"] + 0.01, D["jack_depth_z0"],
                                       D["jack_depth_z0"] + 1.0))
                pins = p_ if pins is None else _add(pins, p_)
        else:
            px, py = D["jack_pin_box"]
            pins = _box(x - px / 2, x + px / 2, y - py / 2, y + py / 2, D["jack_depth_z0"] - D["jack_pin_len"], D["jack_depth_z0"])
        bush = _cyl_z(D["jack_bush_d"] / 2, D["z_fp0"], D["z_fp1"] + D["jack_nut_t"], x, y)
        nut = _sub(_cyl_z(D["jack_nut_d"] / 2, D["z_fp1"] + g, D["z_fp1"] + D["jack_nut_t"], x, y), _cyl_z(D["jack_bush_d"] / 2 + 0.01, D["z_fp1"], D["z_fp1"] + D["jack_nut_t"] + 1, x, y))
        jacks[f"jack {i} PJ366ST body + pins [S]"] = _add(body, pins)
        jacks[f"jack {i} bushing"] = bush
        jacks[f"jack {i} nut"] = nut
    if D.get("jb_on"):   # v0.33 [Ed 4 Nov 21:30] option B: the jack board on the jacks' backs, the jack power board under it
        bx0, bx1 = D["jb_x"]; by0, by1 = D["jack_bot_y"], D["jack_top_y"]; a = D["jb_air"]; px, py = D["jack_pin_box"]
        hw, hl, hx = D["jb_hdr"]
        holes = None
        for x, y in D["jack_xy"]:
            if D.get("jack_pins"):   # v0.39 [Ed Q14 = B]: a plated slot over every published position of each pin; the parts keep jb_air off
                for _n, y0, y1, w in D["jack_pins"]:   # the pins down to their tips
                    h = _box(x - w / 2 - a, x + w / 2 + a, y + min(y0, y1) - w / 2 - a, y + max(y0, y1) + w / 2 + a, D["jb2_z1"] - 0.01,
                             D["jb_z1"] + 0.01)
                    holes = h if holes is None else _add(holes, h)
            else:
                h = _box(x - px / 2 - a, x + px / 2 + a, y - py / 2 - a, y + py / 2 + a, D["jb2_z1"] - 0.01, D["jb_z1"] + 0.01)
                holes = h if holes is None else _add(holes, h)
        hdrs = None
        for sx in (-1, 1):
            h = _box(sx * hx - hw / 2, sx * hx + hw / 2, (by0 + by1) / 2 - hl / 2, (by0 + by1) / 2 + hl / 2, D["jb2_z1"] + 0.02, D["jb_z0"] - 0.02)
            hdrs = h if hdrs is None else _add(hdrs, h)
        hkeep = None
        for sx in (-1, 1):
            h = _box(sx * hx - hw / 2 - a, sx * hx + hw / 2 + a, (by0 + by1) / 2 - hl / 2 - a, (by0 + by1) / 2 + hl / 2 + a, D["jb2_z0"] - 1.0, D["jb_z1"])
            hkeep = h if hkeep is None else _add(hkeep, h)
        jbb = _box(bx0, bx1, by0, by1, D["jb_z0"], D["jb_z1"] - 0.02)
        if D.get("jb_tongue_y") is not None:   # v0.39 [Ed 15:53 Q15 = A]: a tongue down to each sleeve pin
            for tx0, tx1 in D["jb_tongue_x"]:
                jbb = _add(jbb, _box(tx0, tx1, D["jb_tongue_y"], by0 + D["fuse"], D["jb_z0"], D["jb_z1"] - 0.02))
        if D.get("jb_plug_hole"):   # v0.45 [Ed 5 Nov 20:46 Q20 = A]: a hole under each jack axis for a plug's tip
            for x, y in D["jack_xy"]:
                jbb = _sub(jbb, _cyl_z(D["jb_plug_hole"] / 2, D["jb_z0"] - 1.0, D["jb_z1"] + 1.0, x, y))
        if D.get("jb_tip_bump"):   # v0.43 [Ed 5 Nov 17:59 Q18 = A]: a bump on the top edge round each tip slot
            bw_, bh_ = D["jb_tip_bump"]
            for x, _y in D["jack_xy"]:
                jbb = _add(jbb, _box(x - bw_ / 2, x + bw_ / 2, by1 - D["fuse"], by1 + bh_, D["jb_z0"], D["jb_z1"] - 0.02))
        if D.get("usb_pwr_tab"):   # v0.35 [Ed 22:36] tab into the USB-C channel with the power spring contacts on its front face
            tw, ty = D["usb_pwr_tab"]
            jbb = _add(jbb, _box(-tw, tw, ty, by0 + D["fuse"], D["jb_z0"], D["jb_z1"] - 0.02))
            for i, (x, y) in enumerate(D["usb_pwr_contacts"], 1):
                nm = D["usb_pwr_names"][i - 1] if D.get("usb_pwr_names") else ('15 V' if i <= 2 else 'GND')
                jacks[f"USB spring contact {i} ({nm}) [A]"] = _cyl_z(D["usb_pwr_d"] / 2, D["jb_z1"],
                                                                                                   D["usb_z0"] - 0.02, x, y)
        jacks["jack board (FR-4, the four jacks soldered on) [A]"] = _sub(jbb, holes)
        jacks["jack board underside parts (envelope) [A]"] = _sub(_sub(_box(bx0 + 0.3, bx1 - 0.3, by0 + 0.3, by1 - 0.3, D["jb_under_z0"],
                                                                         D["jb_z0"] - 0.02), holes), hkeep)
        jacks["jack board headers (2 x 2x6 1.27, SMD) [A]"] = hdrs
        pb = _box(bx0, bx1, by0, by1, D["jb2_z0"], D["jb2_z1"])
        if D.get("jb_post_xy"):   # v0.34 [Ed 22:21] the tab down over the posts in the main board's strip
            tx, ty = D["jb_tab"]   # 10 Nov sweep: was `hx`, which overwrote the headers' x for the lower stacks below
            for x, y in D["jb_post_xy"]:
                pb = _add(pb, _box(x - tx, x + tx, ty, by0 + D["fuse"], D["jb2_z0"], D["jb2_z1"]))
            pin = D.get("jb_post_pin")
            for i, (x, y) in enumerate(D["jb_post_xy"], 1):
                post = _cyl_z(D["jb_post_d"] / 2, 0.02, D["jb2_z0"] - 0.02, x, y)
                if pin:   # v0.48 [Ed 6 Nov Q24 = A]: a Ø1.0 pin through a plated hole in the ear, the board on the Ø2 shoulder
                    post = _add(post, _cyl_z(pin[0] / 2, D["jb2_z0"] - 0.03, D["jb2_z1"] + pin[3], x, y))
                    pb = _sub(pb, _cyl_z(pin[1] / 2, D["jb2_z0"] - 0.5, D["jb2_z1"] + 0.5, x, y))
                jacks[f"jack unit post {i} (Ø{D['jb_post_d']:g} brass, {'GND' if i == 1 else '15 V'}) [A]"] = post
            if D.get("link_lane"):   # v0.36 [Ed 22:52]: the two flexes, drawn as straight risers from the strip up to their ZIFs
                oy0 = D["clear_oled_xy"][1] - D["clear_oled"][1] / 2; ft = D["flex_t"]; zt = D["zif_z0"] - 0.02
                jacks["clear OLED flex (36.0 [S], plugged on the bench)"] = _box(-6.25, 6.25, oy0 - 0.05 - ft, oy0 - 0.05, D["clear_oled"][2] / 2, zt)
                if "lf_rb" in D:   # Q29 [Ed 7 Nov] = A: the J path, contacts up into the FH26W and down onto the strip's pads
                    fl, st = _link_flex(D)
                    jacks["link flex (main board to the jack lower board, single-sided PI, 25 at 0.3) [A]"] = fl
                    jacks["link flex stiffener (PI, to 0.20 at the contacts) [A]"] = st
                else:
                    lx0, lx1, _ly = D["link_lane"]
                    jacks["link flex (main board to the jack power board) [A]"] = _box(lx0, lx1, oy0 - 0.45 - ft, oy0 - 0.45, 0.02, zt)
        lower = bool(D.get("jb3_on"))
        jacks["jack power board (FR-4, 4 layers: PD sink, eFuse, ±12 V LDOs, jack switching, I/O expander) [A]" if lower else
              "jack power board (FR-4: ZIFs, PD sink, ±12 V, the OLED's 12.5 V) [A]"] = pb
        jacks["jack power board parts (envelope) [A]"] = _sub(_box(bx0 + 0.3, bx1 - 0.3, by0 + 0.3, by1 - 0.3, D["jb2_z1"] + 0.02,
                                                                 D["jb2_parts_z1"]), hkeep)
        zb = D["jb3_z0"] if lower else D["jb2_z0"]
        if lower:   # v0.47 [Ed 6 Nov Q23 = A]: the lower board on two more 2x6 stacks, the flex connectors under it
            hdr2, keep2 = None, None
            for sx in (-1, 1):
                h = _box(sx * hx - hw / 2, sx * hx + hw / 2, (by0 + by1) / 2 - hl / 2, (by0 + by1) / 2 + hl / 2, D["jb3_z1"] + 0.02,
                         D["jb2_z0"] - 0.02)
                hdr2 = h if hdr2 is None else _add(hdr2, h)
                k = _box(sx * hx - hw / 2 - a, sx * hx + hw / 2 + a, (by0 + by1) / 2 - hl / 2 - a, (by0 + by1) / 2 + hl / 2 + a,
                         D["jb3_z1"], D["jb2_z0"])
                keep2 = k if keep2 is None else _add(keep2, k)
            jacks["jack lower board (FR-4, 4 layers: DAC, op-amps, boost, 3.3 V, the OLED's parts, both flex connectors) [A]"] = \
                _box(bx0, bx1, by0, by1, D["jb3_z0"], D["jb3_z1"])
            jacks["jack power board to lower board stacks (2 x 2x6 1.27, SMD) [A]"] = hdr2
            jacks["jack power board underside parts (envelope) [A]"] = _sub(_box(bx0 + 0.3, bx1 - 0.3, by0 + 0.3, by1 - 0.3,
                                                                              D["jb2_under_z0"], D["jb2_z0"] - 0.02), keep2)
            jacks["jack lower board parts (envelope) [A]"] = _sub(_box(bx0 + 0.3, bx1 - 0.3, by0 + 0.3, by1 - 0.3, D["jb3_z1"] + 0.02,
                                                                    D["jb3_parts_z1"]), keep2)
        brd = "jack lower board" if lower else "jack power board"
        for nm, (w, dd, hh, xc) in ((f"{brd} ZIF, 24-pin 0.5 (clear OLED flex)", D["zif_oled"]),
                                    (f"{brd} FPC connector, 25-pin 0.3 (link flex)", D["zif_link"])):
            jacks[nm] = _box(xc - w / 2, xc + w / 2, by0 + D["zif_y_off"], by0 + D["zif_y_off"] + dd, zb - hh, zb - 0.02)
            if "link flex" in nm and "lf_rb" in D:   # Q29: the FPC slot (7.83 wide [S Hirose D], 0.2 ± 0.03 FPC) so the flex can sit in it
                L = D["link_flex"]; zc = D["lf_zcf"] - L["t_end"] / 2; sw = 7.83
                jacks[nm] = _sub(jacks[nm], _box(xc - sw / 2, xc + sw / 2, D["lf_mouth"] - 0.1, D["lf_y_end"] + 0.05,
                                                 zc - L["t_end"] / 2 - 0.03, zc + L["t_end"] / 2 + 0.03))
    bw, bh, bt = D["usb_board"]
    jacks["USB-C receptacle [S]"] = _box(ux - uw / 2, ux + uw / 2, uy - uh / 2, uy + uh / 2, D["z_fp1"] - ud, D["z_fp1"] - 0.02)
    jacks["USB-C board (socket, TVS, ESD)"] = _box(ux - bw / 2, ux + bw / 2, uy - bh / 2, uy + bh / 2, D["z_fp1"] - ud - bt, D["z_fp1"] - ud)
    for n, a, b, c, d, h in D.get("usb_prot") or ():   # v0.37 [Ed 5 Nov 11:24] on its back face, in pockets in the printed key
        jacks[f"USB-C board {n}"] = _box(a, b, c, d, D["z_fp1"] - ud - bt - h, D["z_fp1"] - ud - bt - 0.01)
    out = {"case": case, f"back cover ({D['cover_mat']})": cover, "glow coat (inside walls)": glow, "PCB": pcb}   # glow trimmed above
    if key is not None:
        out["USB-C key (printed, held by the back cover)"] = key
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
