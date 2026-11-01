"""control_dial: Hall arm (printed in the dial) + its magnet row. Sensors -> electronics/parts/hall_sensors.py, cradle slot ->
base_drive/parts/hall_slot.py (both built from the interface Hall layout).
Hall array on the dial.
v0.15 'vernier' [Ed]: the dial arm comes DOWN through a slot in the base cradle; a bar carries hv_n magnets (alternating poles)
on an outward arc phi_m(r) = ang0 + g (r - r_mid); hv_n linear Hall sensors (TMAG5253 X2SON) sit on the PCB front on the
mirror arc phi_s(r) = ang0 - g (r - r_mid). Centred dial: middle magnet over middle sensor; at theta the crossing moves to
r_mid - theta/(2g) (vernier), reaching the end pair at +-hv_cross_travel.
v0.14 'sector': 5 magnets in a paddle, 2 x DRV5055 (kept for --set hall_layout='sector')."""
import math
from build123d import *
from ...common.util import A, cyl, sector

def _vern(D): return D["hall_layout"] == "vernier"

def _pt(r, a): return r * math.cos(math.radians(a)), r * math.sin(math.radians(a))

def arm(D, travel=0.0):
    if not _vern(D): return _arm_sector(D, travel)
    pr, z0, z1 = D["hv_pad_r"], D["hv_bar_z0"], D["fan_top"]
    rs, ps = D["hv_r"], D["hv_phi_m"]
    s = None
    for i, (r, a) in enumerate(zip(rs, ps)):   # pads + links along the magnet arc
        x, y = _pt(r, a); q = cyl(pr, z0, z1 - z0, x, y)
        if i:
            x0, y0 = _pt(rs[i - 1], ps[i - 1]); L = math.hypot(x - x0, y - y0); ang = math.degrees(math.atan2(y - y0, x - x0))
            q += Pos((x + x0) / 2, (y + y0) / 2, z0) * Rot(0, 0, ang) * Box(L, 2 * pr, z1 - z0, align=A)
        s = q if s is None else s + q
    sz0, sw = D["hv_spoke_z0"], D["hv_spoke_w"]; r_in = D["dial_tube_od"] / 2 - 0.3
    L = rs[0] - r_in
    s += Rot(0, 0, ps[0]) * Pos(r_in + L / 2, 0, sz0) * Box(L, sw, z1 - sz0, align=A)
    if D["fan_on"]:   # v0.16 [Ed]: fan widening to the perimeter + spring/cushion lever
        s += sector(D["fan_r0"], D["fan_r1"], D["fan_half"], D["fan_z0"], z1 - D["fan_z0"], D["ha_ang0"], n=48)
        # fill between the outer pads and the fan sector (the fan is one plate from the bar out to the wings)
        s += lever(D)
    md, mh = D["hv_mag"]
    for r, a in zip(rs, ps):   # pockets open from below, top flush with the magnet top (press / glue fit)
        x, y = _pt(r, a); s -= cyl(md / 2, D["hv_z_mag0"] - 0.1, mh + 0.1, x, y)
    if D["fan_on"]:
        s -= wing_cuts(D)
    s -= cyl(D["dial_tube_id"] / 2 + 0.01, 0, 20)
    return Rot(0, 0, travel) * s

def lever(D):
    """Radial lever on the dial tube at sl_ang: bar above the thrust cage, end block lower (cushion magnet), spring pin on top."""
    a, r1, w = D["sl_ang"], D["sl_r"], D["sl_w"]; r0 = D["dial_tube_od"] / 2 - 0.3
    rb = D["cu_mag_r"] - D["cu_mag"][0] / 2 - 0.6                          # end block from here out
    bar = Pos((r0 + r1) / 2, 0, D["hv_spoke_z0"]) * Box(r1 - r0, w, D["sl_top"] - D["hv_spoke_z0"], align=A)
    end = Pos((rb + r1) / 2, 0, D["sl_z0"]) * Box(r1 - rb, w, D["sl_top"] - D["sl_z0"], align=A)
    pin = cyl(D["sl_pin_d"] / 2, D["sl_top"] - 0.01, D["sl_pin_top"] - D["sl_top"] + 0.01, D["sl_pin_r"], 0)
    md, mh = D["cu_mag"]
    pocket = Pos(D["cu_mag_r"], 0, D["cu_z"]) * Rot(90, 0, 0) * Cylinder(md / 2 + 0.025, mh + 0.01)
    return Rot(0, 0, a) * (bar + end + pin - pocket)

def lever_magnet(D, travel=0.0):
    md, mh = D["cu_mag"]
    return Rot(0, 0, D["sl_ang"] + travel) * (Pos(D["cu_mag_r"], 0, D["cu_z"]) * Rot(90, 0, 0) * Cylinder(md / 2, mh))

def wing_cuts(D):
    """Ball-track grooves in the wing underside (over each detent) + the two latch dimples per detent in the wing top."""
    out = None
    for a in D["det_angs"]:
        for r in D["bt_rs"]:   # groove spans the ball roll relative to the wing (travel/2) - same half-span as the plate groove
            g = Pos(0, 0, D["bt_z"]) * Torus(r, D["bt_groove_r"])
            g = g & sector(r - 1.0, r + 1.0, D["bt_half"], D["bt_z"] - 1, 2, a)
            out = g if out is None else out + g
        for sgn in (-1, 1):    # dimple that sits under the plunger when the dial is at sgn*det_deg (wing frame: a - sgn*det)
            t = math.radians(a - sgn * D["det_deg"]); r = D["det_r"]
            out += Pos(r * math.cos(t), r * math.sin(t), D["fan_top"] + D["det_ball"] / 2 - D["det_dimple"]) * Sphere(D["det_ball"] / 2)
    return out

def magnets(D, travel=0.0):
    if not _vern(D): return _mag_sector(D, travel)
    md, mh = D["hv_mag"]; out = []
    for r, a in zip(D["hv_r"], D["hv_phi_m"]):
        x, y = _pt(r, a + travel); out.append(cyl(md / 2, D["hv_z_mag0"], mh, x, y))
    return out

def build(D):
    out = {f"hall magnet {i + 1}": m for i, m in enumerate(magnets(D))}
    if _vern(D) and D["fan_on"]:
        out[f"cushion magnet lever {D['cu_mag'][0]:g}x{D['cu_mag'][1]:g}"] = lever_magnet(D)
    return out

# ---- v0.14 sector layout ----
def _arm_sector(D, travel):
    a = D["ha_ang0"]; z0, t, w, r0 = D["ha_arm"]
    spoke = Rot(0, 0, a) * Pos((r0 + D["ha_pad_r0"] + 0.5) / 2, 0, z0) * Box(D["ha_pad_r0"] + 0.5 - r0, w, t, align=A)
    paddle = sector(D["ha_pad_r0"], D["ha_pad_r1"], D["ha_pad_half"], D["ha_z_mag0"], D["ha_arm_z1"] - D["ha_z_mag0"], a)
    s = spoke + paddle
    for mg in _mag_sector(D): s -= mg
    s -= cyl(D["dial_tube_id"] / 2 + 0.01, 0, 20)
    return Rot(0, 0, travel) * s

def _mag_sector(D, travel=0.0):
    out = []
    for da in D["ha_mag_angs"]:
        t = math.radians(D["ha_ang0"] + da + travel)
        out.append(cyl(D["ha_mag"][0] / 2, D["ha_z_mag0"], D["ha_mag"][1], D["ha_r_m"] * math.cos(t), D["ha_r_m"] * math.sin(t)))
    return out
