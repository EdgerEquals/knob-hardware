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
from build123d import Face, Wire, Vector

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
    if D["fan_on"]:   # v0.16 [Ed]: fan widening to the perimeter + lever; v0.17 adds the tapered rib and detent ears
        s += sector(D["fan_r0"], D["fan_r1"], D["fan_half"], D["fan_z0"], z1 - D["fan_z0"], D["ha_ang0"], n=48)
        s += lever(D)
        s += rib(D)
        s += ears(D) if D["arm_det"] != "arc" else arc_adds(D)
    md, mh = D["hv_mag"]
    for r, a in zip(rs, ps):   # pockets open from below, top flush with the magnet top (press / glue fit)
        x, y = _pt(r, a); s -= cyl(md / 2, D["hv_z_mag0"] - 0.1, mh + 0.1, x, y)
    if D["fan_on"]:
        s -= wing_cuts(D) if D["arm_det"] != "arc" else arc_cuts(D)
    s -= cyl(D["dial_tube_id"] / 2 + 0.01, 0, 20)
    return Rot(0, 0, travel) * s

def _trap(r0, r1, w0, w1, z0, h, ang):
    """Plan trapezoid (width w0 at r0, w1 at r1) extruded from z0, centred on world angle ang."""
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a); px, py = -sa, ca
    def p(r, w, s): return (r * ca + s * px * w / 2, r * sa + s * py * w / 2)
    # CCW from +Z so extrude goes upward
    pts = [p(r0, w0, -1), p(r1, w1, -1), p(r1, w1, 1), p(r0, w0, 1)]
    return Pos(0, 0, z0) * extrude(Face(Wire.make_polygon([Vector(x, y, 0) for x, y in pts], close=True)), h)

def _rib_w(D, r):
    r0, rh = D["ha_rib_r_hub"], D["ha_rib_r_head"]
    if r <= rh:
        return D["ha_rib_w0"] + (D["ha_rib_w1"] - D["ha_rib_w0"]) * (r - r0) / max(rh - r0, 1e-6)
    return D["ha_rib_w1"]

def rib(D):
    """v0.17 [Ed]: tapered spine on the Hall arm. Width 3.0 at the hub to 5.2 at the hammerhead, on to ha_rib_r1.
    Top at the lever top. Bottom stays over the thrust cage and drops to ha_rib_z_low beyond ha_rib_r_step."""
    ang = D["ha_ang0"]
    r_hub, r_step = D["ha_rib_r_hub"], D["ha_rib_r_step"]
    r_head, r1 = D["ha_rib_r_head"], D["ha_rib_r1"]
    z_top = D["ha_rib_z_top"]
    s = _trap(r_hub, r_step, _rib_w(D, r_hub), _rib_w(D, r_step), D["ha_rib_z_cage"], z_top - D["ha_rib_z_cage"], ang)
    if r_head > r_step:
        s += _trap(r_step, r_head, _rib_w(D, r_step), _rib_w(D, r_head), D["ha_rib_z_low"], z_top - D["ha_rib_z_low"], ang)
    if r1 > r_head:
        s += _trap(r_head, r1, D["ha_rib_w1"], D["ha_rib_w1"], D["ha_rib_z_low"], z_top - D["ha_rib_z_low"], ang)
    return s

def ears(D):
    """Inboard pads the detent balls ride on (wide enough for ±travel) plus a spoke back to the dial tube."""
    T = D["travel_deg"]
    half = T + math.degrees((D["det_ball"] / 2) / D["det_r"])
    r0 = min(D["bt_rs"]) - D["bt_groove_r"] - D["fan_clear"]
    r_pin = D["enc_cd"] - D["d_pin_tip"] / 2 - D["tgt"]["hall_vs_pinions"]
    r1 = min(max(D["bt_rs"]) + D["bt_groove_r"] + D["fan_clear"], r_pin)
    z0, z1 = D["fan_z0"], D["fan_top"]
    r_hub, r_step = D["ha_rib_r_hub"], D["ha_rib_r_step"]
    zc = D["ha_rib_z_cage"]
    s = None
    for a in D["det_angs"]:
        q = sector(r0, r1, half, z0, z1 - z0, a, n=32)
        # over the thrust cage the spoke stays high; it drops only once it is clear of the cage
        if r_step < r0:
            q += _trap(r_hub, r_step, D["sl_w"], D["sl_w"], zc, z1 - zc, a)
            q += _trap(r_step, r0, D["sl_w"], D["sl_w"], z0, z1 - z0, a)
        else:
            q += _trap(r_hub, r0, D["sl_w"], D["sl_w"], zc, z1 - zc, a)
        s = q if s is None else s + q
    return s

def arc_adds(D):
    """v0.21 [Ed 2 Nov]: raised land on the arc for the single detent (flush with the rib top, so the ball path crosses the rib),
    the webs that carry the three ball-track grooves (joined to the rib, the lever-side one also to the lever) and a spoke from
    the dial tube to the free end of the encoder-side web."""
    s = sector(D["ad_land_r0"], D["ad_land_r1"], D["ad_land_half"], D["fan_top"] - 0.01, D["ad_z_land"] - D["fan_top"] + 0.01, D["ad_ang"], n=48)
    z0, z1 = D["tk_web_z0"], D["tk_web_z1"]
    for r0, r1, a0, a1 in D["tk_webs"]:
        s += sector(r0, r1, (a1 - a0) / 2, z0, z1 - z0, (a0 + a1) / 2, n=48)
    if D["tk_spoke_ang"] is not None:
        r_hub, r_step, zc = D["ha_rib_r_hub"], D["ha_rib_r_step"], D["ha_rib_z_cage"]
        a, r1 = D["tk_spoke_ang"], D["tk_spoke_r1"]
        s += _trap(r_hub, min(r_step, r1), D["sl_w"], D["sl_w"], zc, z1 - zc, a)   # over the (old) thrust cage the spoke stays high
        if r1 > r_step:
            s += _trap(r_step, r1, D["sl_w"], D["sl_w"], z0, z1 - z0, a)
    return s

def track_groove(D, t, z):
    """One ball-track groove (torus ∩ sector): the same span in the arm underside and in the cradle plate (the balls roll θ/2)."""
    r = t["r"]
    return (Pos(0, 0, z) * Torus(r, D["bt_groove_r"])) & sector(r - 1.0, r + 1.0, t["half"], z - 1, 2, t["ang"])

def arc_cuts(D):
    """Track grooves in the web undersides + the three latch dimples (0, ±det_deg) in the land top."""
    out = None
    for t in D["tk"]:
        g = track_groove(D, t, D["bt_z"])
        out = g if out is None else out + g
    rb = D["det_ball"] / 2; r = D["ad_r"]
    for th in (-D["det_deg"], 0.0, D["det_deg"]):
        a = math.radians(D["ad_ang"] - th)
        out += Pos(r * math.cos(a), r * math.sin(a), D["ad_z_land"] + rb - D["det_dimple"]) * Sphere(rb)
    return out

def lever(D):
    """Radial lever on the dial tube at sl_ang: bar above the thrust cage, end block, spring pin on top.
    v0.17: no cushion-magnet pocket unless cu_on."""
    a, r1, w = D["sl_ang"], D["sl_r"], D["sl_w"]; r0 = D["dial_tube_od"] / 2 - 0.3
    rb = D["sl_pin_r"]
    bar = Pos((r0 + r1) / 2, 0, D["hv_spoke_z0"]) * Box(r1 - r0, w, D["sl_top"] - D["hv_spoke_z0"], align=A)
    end = Pos((rb + r1) / 2, 0, D["sl_z0"]) * Box(max(r1 - rb, 0.2), w, D["sl_top"] - D["sl_z0"], align=A)
    pin = cyl(D["sl_pin_d"] / 2, D["sl_top"] - 0.01, D["sl_pin_top"] - D["sl_top"] + 0.01, D["sl_pin_r"], 0)
    body = bar + end + pin
    if D["cu_on"]:
        md, mh = D["cu_mag"]
        body -= Pos(D["cu_mag_r"], 0, D["cu_z"]) * Rot(90, 0, 0) * Cylinder(md / 2 + 0.025, mh + 0.01)
    return Rot(0, 0, a) * body

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
        for th in (-D["det_deg"], 0.0, D["det_deg"]):   # v0.17 [Ed]: latch at the centre and at both ends
            t = math.radians(a - th); r = D["det_r"]
            out += Pos(r * math.cos(t), r * math.sin(t), D["fan_top"] + D["det_ball"] / 2 - D["det_dimple"]) * Sphere(D["det_ball"] / 2)
    return out

def magnets(D, travel=0.0):
    if not _vern(D): return _mag_sector(D, travel)
    md, mh = D["hv_mag"]; out = []
    for r, a in zip(D["hv_r"], D["hv_phi_m"]):
        x, y = _pt(r, a + travel); out.append(cyl(md / 2, D["hv_z_mag0"], mh, x, y))
    return out

def build(D):
    pol = D["hv_pol"] if _vern(D) else [1] * len(magnets(D))
    out = {f"hall magnet {i + 1} {'N' if pol[i] > 0 else 'S'}-down": m for i, m in enumerate(magnets(D))}   # v0.16b [Ed]: N/S/N/S/N
    if _vern(D) and D["fan_on"] and D["cu_on"]:
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
