"""v0.16 dial mechanics on the cradle side [Ed]: top-loaded spring-ball detent blocks over the fan wings (ball, spring, grub
screw in a threaded bore: the grub sets the feel), the Ø1 ball track under each detent, the centring-spring anchor posts and
the magnet cushion stop blocks either side of the dial lever. Angles / radii come from the INTERFACE (_place_mech).
v0.21 [Ed 2 Nov] (arm_det "arc", control_dial EXPORTS): ONE detent out on the arc at the arm's end, its boss on a bridge
over the arm from two columns; three ball tracks (big, small, big) whose layout control_dial owns."""
import math
from build123d import *
from ...common.util import A, cyl, sector

def _pol(r, a): return r * math.cos(math.radians(a)), r * math.sin(math.radians(a))

def _local(D, x0, x1, y0, y1, z0, z1, a):   # box in the lever frame (x radial along sl_ang, y tangential), rotated by a
    return Rot(0, 0, a) * Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=A)

def _arc(D): return D["arm_det"] == "arc" and D["ad_r"] is not None

def arc_bridge(D):
    """v0.21: two columns on the plate (one each side of the arm sweep), a link from each to the boss over the detent.
    Links start at det_z0 (above the land and the rib top by det_gap) and run up to the boss top."""
    x, y = D["det_xy"][0]; z0, z1, zl = D["det_z0"], D["det_z1"], D["ad_z_link"]
    rr, w = D["ad_col_r"], D["ad_link_w"]
    s = cyl(D["det_boss_d"] / 2, z0, z1 - z0, x, y)
    for cx, cy in D["ad_col_xy"]:
        s += cyl(rr, D["plate_t"] - 0.01, z1 - D["plate_t"] + 0.01, cx, cy)
        L = math.hypot(cx - x, cy - y)
        s += Pos((x + cx) / 2, (y + cy) / 2, zl) * Rot(0, 0, math.degrees(math.atan2(cy - y, cx - x))) * Box(L, w, z1 - zl, align=A)
    return s

def det_block(D, a):
    """Leg on the plate inboard of the fan wing, bridge over the wing, boss with the plunger bore."""
    x, y = _pol(D["det_r"], a); w = D["det_leg_w"]; z0, z1 = D["det_z0"], D["det_z1"]
    # column site comes from the interface: clear of the arm sweep and the feel saddle
    i = min(range(len(D["det_angs"])), key=lambda k: abs((D["det_angs"][k] - a + 180) % 360 - 180))
    cx, cy = D["det_col_xy"][i]
    # the Hall rib tops out at sl_top and sweeps under this bridge, so the bridge starts above the rib
    z_b = max(z0, D["sl_pin_top"] + D["tgt"]["arm_vs_cradle"])   # above the spring pin; the link can cross the lever in plan
    col = cyl(D["det_col_r"], D["plate_t"] - 0.01, z_b - D["plate_t"] + 0.01, cx, cy)
    bridge = Rot(0, 0, a) * Pos((D["det_leg_r0"] + D["det_r"]) / 2, 0, z_b) * Box(max(D["det_r"] - D["det_leg_r0"], 0.2), w, z1 - z_b, align=A)
    link = Pos((x + cx) / 2, (y + cy) / 2, z_b) * Rot(0, 0, math.degrees(math.atan2(cy - y, cx - x))) * Box(math.hypot(cx - x, cy - y), D["det_link_w"], z1 - z_b, align=A)
    boss = cyl(D["det_boss_d"] / 2, z0, z1 - z0, x, y)
    return col + bridge + link + boss

def det_bore(D, a):
    x, y = _pol(D["ad_r"], D["ad_ang"]) if _arc(D) else _pol(D["det_r"], a)
    return cyl(D["det_bore_d"] / 2, D["det_z0"] - 0.01, D["det_z_thread0"] - D["det_z0"] + 0.02, x, y) + \
           cyl(D["det_thread_d"] / 2, D["det_z_thread0"], D["det_z1"] - D["det_z_thread0"] + 0.01, x, y)

def track_grooves(D):
    out = None
    if _arc(D):   # v0.21: control_dial owns the layout; same groove span as the arm web above (the balls roll θ/2)
        for t in D["tk"]:
            r = t["r"]
            g = (Pos(0, 0, D["bt_z"]) * Torus(r, D["bt_groove_r"])) & sector(r - 1.0, r + 1.0, t["half"], D["bt_z"] - 1, 2, t["ang"])
            out = g if out is None else out + g
        return out
    for a in D["det_angs"]:
        for r in D["bt_rs"]:
            g = (Pos(0, 0, D["bt_z"]) * Torus(r, D["bt_groove_r"])) & sector(r - 1.0, r + 1.0, D["bt_half"], D["bt_z"] - 1, 2, a)
            out = g if out is None else out + g
    return out

def stop_blocks(D):
    """Hard stops: faces parallel to the lever sides at ±travel (flush at the end of travel), plus the spring anchor posts.
    v0.17: no cushion-magnet pockets. The stop is as close past the end detent as the ball's bore play allows (travel_deg)."""
    a, w, T = D["sl_ang"], D["sl_w"], D["travel_deg"]; L = D["stop_len"]
    # the ear and its spoke fill the radii below the lever tip, so the face meets the lever and the block sits above the ear
    x1 = D["sl_r"] + D["stop_over"]
    x0 = max(D["sl_pin_r"] - 0.4, D["dial_tube_od"] / 2 + 0.6)
    T = T + D["stop_bias"]
    z0 = D["fan_top"] + D["tgt"]["arm_vs_cradle"]   # ear tops at fan_top; this keeps ≥ 0.3 mm under the block at every angle
    z1 = D["sl_top"]
    s = _local(D, x0, x1, w / 2, w / 2 + L, z0, z1, a + T) + _local(D, x0, x1, -w / 2 - L, -w / 2, z0, z1, a - T)
    # anchors stand above the lever; the ±travel sweep passes underneath
    z_post = D["sl_top"] + D["tgt"]["arm_vs_cradle"] + 0.15   # corner distance stays ≥ the 0.3 mm arm gap
    for (px, py) in D["sl_anchor_xy"]:
        s += cyl(D["sl_post_d"] / 2, z_post, max(D["sl_pin_top"] - z_post, 0.4), px, py)
    if D["cu_on"]:
        md, mh = D["cu_mag"]
        for sg, aa in ((1, a + T), (-1, a - T)):
            s -= Rot(0, 0, aa) * (Pos(D["cu_mag_r"], sg * (w / 2 + mh / 2), D["cu_z"]) * Rot(90, 0, 0) * Cylinder(md / 2 + 0.025, mh + 0.01))
    return s

def cradle_add(D):
    s = stop_blocks(D)
    if _arc(D): return s + arc_bridge(D)
    for a in D["det_angs"]: s += det_block(D, a)
    return s

def cradle_cut(D):
    s = track_grooves(D)
    for a in (D["det_angs"] if not _arc(D) else [D["ad_ang"]]): s += det_bore(D, a)
    for (px, py) in D["sl_anchor_xy"]:
        z_post = D["sl_top"] + D["tgt"]["arm_vs_cradle"] + 0.15   # corner distance stays ≥ the 0.3 mm arm gap
        s += cyl(D["sl_pin_d"] / 2, z_post, D["sl_pin_top"] - z_post + 0.01, px, py)   # anchor pin press hole
    return s

def springs_at(D, theta):
    """Centring springs with the lever pin rotated by `theta` (anchors stay put)."""
    od, _L, wire = D["sl_spring"]; zc = D["sl_top"] + D["sl_spring_gap"] + od / 2
    px, py = _pol(D["sl_pin_r"], D["sl_ang"] + theta)
    out = []
    for ax, ay in D["sl_anchor_xy"]:
        ang = math.degrees(math.atan2(ay - py, ax - px))
        # cylinder is centred on the midpoint, so the subtracted length is shared by the two ends
        Ls = math.hypot(ax - px, ay - py) - D["sl_pin_d"] / 2 - D["sl_post_d"] / 2 - 0.7
        out.append(Pos((ax + px) / 2, (ay + py) / 2, zc) * Rot(0, 0, ang) * Rot(0, 90, 0) * (Cylinder(od / 2, max(Ls, 0.2)) - Cylinder(max(od / 2 - wire, 0.05), max(Ls, 0.2) + 0.02)))
    return out

def track_ball_list(D, theta=0.0):
    """v0.21: [(name, diameter, x, y, z)] for every ball in the three tracks, rolled θ/2 (both races move θ apart)."""
    out = []
    for t in D["tk"]:
        nb = ns = 0
        for off, d in zip(t["offs"], t["dias"]):
            big = d >= D["bt_ball"] - 1e-9
            if big: nb += 1
            else: ns += 1
            nm = f"track {t['k']} ball {nb} Ø{d:g}" if big else f"track {t['k']} separator ball {ns} Ø{d:g}"
            out.append((nm, d, *_pol(t["r"], t["ang"] + off + theta / 2), D["bt_z"]))
    return out

def track_balls_at(D, theta):
    """Track balls roll at half the dial angle (trapped between the fixed plate groove and the ear)."""
    if _arc(D):
        return [Pos(x, y, z) * Sphere(d / 2) for _n, d, x, y, z in track_ball_list(D, theta)]
    out = []
    for a in D["det_angs"]:
        for r in D["bt_rs"]:
            out.append(Pos(*_pol(r, a + theta / 2), D["bt_z"]) * Sphere(D["bt_ball"] / 2))
    return out

def build(D):
    out = {}; db = D["det_ball"]; so, sl, sw = D["det_spring"]
    z_seat = D["det_z_ball"] - D["det_dimple"]   # rest pose is the centre latch: the ball sits in the dimple
    spring_l = max(D["det_spring_inst"] - D["det_dimple"], sw * 2)
    for i, (x, y) in enumerate(D["det_xy"], 1):
        out[f"detent {i} ball Ø{db:g}"] = Pos(x, y, z_seat) * Sphere(db / 2)
        out[f"detent {i} spring"] = cyl(so / 2, z_seat + db / 2, spring_l, x, y) - cyl(so / 2 - sw, z_seat + db / 2 - 0.01, spring_l + 0.02, x, y)
        out[f"detent {i} grub M{D['det_thread_d']:g}x{D['det_grub_len']:g}"] = cyl(D["det_thread_d"] / 2 - 0.01, D["det_z_grub0"], D["det_grub_len"], x, y)
        if _arc(D): continue
        for j, r in enumerate(D["bt_rs"], 1):
            bx, by = _pol(r, D["det_angs"][i - 1])
            out[f"track ball {i}.{j} Ø{D['bt_ball']:g}"] = Pos(bx, by, D["bt_z"]) * Sphere(D["bt_ball"] / 2)
    if _arc(D):
        for nm, d, bx, by, bz in track_ball_list(D):
            out[nm] = Pos(bx, by, bz) * Sphere(d / 2)
    if D["cu_on"]:
        md, mh = D["cu_mag"]; a, w, T = D["sl_ang"], D["sl_w"], D["travel_deg"]
        for k, (sg, aa) in enumerate(((1, a + T), (-1, a - T)), 1):
            out[f"cushion magnet stop {k} {md:g}x{mh:g}"] = Rot(0, 0, aa) * (Pos(D["cu_mag_r"], sg * (w / 2 + mh / 2), D["cu_z"]) * Rot(90, 0, 0) * Cylinder(md / 2, mh))
    for k, coil in enumerate(springs_at(D, 0.0), 1):
        out[f"centring spring {k} (non-magnetic)"] = coil
    for k, (ax, ay) in enumerate(D["sl_anchor_xy"], 1):
        z_post = D["sl_top"] + D["tgt"]["arm_vs_cradle"] + 0.15   # corner distance stays ≥ the 0.3 mm arm gap
        out[f"spring anchor pin {k}"] = cyl(D["sl_pin_d"] / 2, z_post, D["sl_pin_top"] - z_post, ax, ay)
    return out
