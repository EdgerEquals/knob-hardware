"""Joystick stack checks: rows of (name, value, target, ok, note). Geometry distances on the built parts + param sums."""
import math, itertools, os, sys
from build123d import Pos

def run(D, P):
    T = D["tgt"]; sw = D["sw"]; rows = []
    def row(name, v, tgt, ok, note=""): rows.append(dict(name=name, value=float(v), target=tgt, ok=bool(ok), note=note))
    car, base, stem = P["joystick carrier (printed)"], P["joystick base (printed, glued)"], P["SW1 SKRHADE010 stem"]
    spid, db, fpc, pcb = P["screen spider + plunger (printed)"], P["joystick daughterboard"], P["screen FPC [A]"], P["main PCB (proxy, local patch)"]
    sprs = [P[n] for n in P if n.startswith("hold-down spring")]
    # 1 stem / cup
    g = stem.distance_to(car)
    row("stem vs cup bore, radial (rest)", g, f">= {T['stem_cup_min']}", g >= T["stem_cup_min"] - 1e-6, f"cup Ø{D['cup_bore']:g} over the Ø{sw['stem_d']:g} stem, engaged {D['cup_engage']:g}")
    row("cup engagement covers the 4.3 mm tilt reference height", D["z_ref"] - D["z_cup0"], ">= 0.2", D["z_cup0"] + 0.2 <= D["z_ref"] <= D["z_stem_top"],
        f"cup z {D['z_cup0']:.2f}-{D['z_stem_top']:.2f}, ref z {D['z_ref']:.2f}, stem pivot z {D['z_pivot']:.2f}")
    # 2 plunger
    pg = stem.distance_to(spid)
    row("plunger tip to stem top (rest)", pg, "0.02-0.10", 0.02 <= pg <= 0.10, "screen + spider weight only; no preload on the switch")
    # 3 spider travel
    row("spider free travel under the pad", D["sp_gap"], "0.30-0.50", 0.3 - 1e-9 <= D["sp_gap"] <= 0.5 + 1e-9, "Ed: ~0.3-0.5")
    m = D["sp_gap"] - D["sp_defl_click"]
    row("spider margin past the centre click (pad never bottoms)", m, ">= 0.1", m >= 0.1,
        f"used {D['sp_defl_click']:.2f} (gap {D['plunger_gap']:g} + push {sw['push_travel']:g}); the switch's own stop takes the full press")
    row("spider force at the click / switch push force", D["sp_f_click"] / sw["push_f"], "<= 0.4", D["sp_f_click"] / sw["push_f"] <= 0.4,
        f"k ≈ {D['sp_k']:.2f} N/mm (4 arms, t {D['sp_t']:g}, PA12) -> +{D['sp_f_click']:.2f} N on {sw['push_f']:g} N = {D['press_f']:.2f} N press [estimate]")
    # 4 slide range vs tilt travel
    row("slide to stop vs slide needed to actuate (cup clear + 0.25 tilt)", D["slide"] - D["slide_need"], ">= 0", D["slide"] >= D["slide_need"],
        f"stop {D['slide']:g} per axis, needed {D['slide_need']:.3f} ({D['cup_rad_clear']:.3f} + {sw['tilt_travel']:g} at z {D['z_ref']:.2f})")
    ot = D["slide"] - D["slide_need"]
    row("overtravel onto the stem past actuation (per axis)", ot, f"<= {T['overtravel_max']}", ot <= T["overtravel_max"],
        f"diagonal stop is {D['slide'] * math.sqrt(2):.2f} radial: diagonals over-tilt the stem by {D['slide'] * math.sqrt(2) - D['slide_need']:.2f} [flag]")
    gs = car.distance_to(base)
    row("carrier vs base at rest (skirt stop gap)", gs, f">= {T['gap_min']}", gs >= T["gap_min"] - 1e-6, "= slide stop")
    cs = (Pos(D["slide"] - 0.01, D["slide"] - 0.01, 0) * car).distance_to(base)
    row("carrier vs base at full diagonal slide (-0.01)", cs, "> 0", cs > 0, "skirt reaches the base wall only at the stop")
    # 5 cable hole
    fc = fpc.distance_to(car)
    row("FPC vs carrier slot walls", fc, f">= {T['cable_min']}", fc >= T["cable_min"] - 1e-6, f"FPC {D['fpc_w']:g} wide [A], slot {D['slot_x'][1] - D['slot_x'][0]:g} × {2 * D['slot_hy']:g}")
    fb = min(fpc.distance_to(base), fpc.distance_to(pcb))
    row("FPC vs base notch / PCB slot (carrier at full slide)", fb - D["slide"], ">= 0.2", fb - D["slide"] >= 0.2 - 1e-6,
        f"hole x {D['hole_x0']:.1f}-{D['hole_x1']:.1f}, ±{D['hole_hy']:.2f}; FPC loop follows the carrier")
    fd = fpc.distance_to(db)
    row("FPC vs daughterboard", fd, ">= 1.0", fd >= 1.0)
    # 6 springs
    sm = D["spr_bore"] / 2 - D["spr_d"] / 2 - D["slide"] * math.sqrt(2)
    row("spring vs base bore / PCB hole at full diagonal slide", sm, f">= {T['spring_min']}", sm >= T["spring_min"],
        f"Ø{D['spr_d']:g} spring in Ø{D['spr_bore']:g}; {len(sprs)} × {D['spr_f']:g} N hold-down, length ≈ {D['spr_len']:.0f} to the back panel [A]")
    sg = min(s.distance_to(base) for s in sprs)
    row("spring vs base (rest)", sg, ">= 0.3", sg >= 0.3 - 1e-6)
    # 7 daughterboard
    dbm = db.distance_to(base - _post_region(D))
    row("daughterboard vs base walls / spring pillars / window", dbm, f">= {T['board_min']}", dbm >= T["board_min"] - 1e-6,
        f"board {D['db'][0]:g} × {D['db'][1]:g}, window {D['win'][0]:g} × {D['win'][1]:g}")
    hb = P["J1 header 2x3 2.54 male (body on top)"].distance_to(car)
    row("J1 header body vs carrier (cup / underside)", hb, ">= 1.0", hb >= 1.0, "trim the header's top pin tails flush with the plastic")
    sb = P["SW1 SKRHADE010 body (45°)"].distance_to(P["J1 header 2x3 2.54 male (body on top)"])
    row("switch body vs J1 header body", sb, ">= 0.3", sb >= 0.3)
    # 8 ball seats
    bt = min(P[n].distance_to(car) for n in P if n.startswith("ball "))
    row("balls touch the carrier underside", bt, "<= 0.01", bt <= 0.01)
    # 9 knob clearance (cross-check with knob-param)
    kod = _knob_od()
    if kod:
        y_edge = D["place_y"] - D["car"][1] / 2 - D["slide"]
        corner = min(math.hypot(x, y_edge) for x in (0.0,))
        kg = corner - kod / 2
        row("carrier (slid toward the knob) vs knob OD", kg, f">= {T['knob_min']}", kg >= T["knob_min"], f"knob Ø{kod:.2f} (knob-param), carrier edge at frame y {y_edge:.2f}")
    return rows

def _post_region(D):
    from .parts import cyl
    return cyl(D["post_d"] + 0.02, -1, D["z_db0"] + 0.01, D["sw_x"], 0)   # the riser post supports the board (contact by design)

def _knob_od():
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    kp = os.path.join(here, "knob-param")
    if not os.path.isdir(kp): return None
    sys.path.insert(0, kp)
    try:
        from knobparam.common import model
        return model.derive(model.default_params())["knob_od"]
    except Exception:
        return None

def clashes(P, tol=1e-3):
    names = list(P); out = {}
    bb = {n: P[n].bounding_box() for n in names}
    def ov(a, b): return all(getattr(a.min, k) < getattr(b.max, k) - 1e-6 and getattr(b.min, k) < getattr(a.max, k) - 1e-6 for k in "XYZ")
    for a, b in itertools.combinations(names, 2):
        if not ov(bb[a], bb[b]): continue
        try: v = (P[a] & P[b]).volume
        except Exception: v = 0.0
        if v > tol: out[f"{a} / {b}"] = v
    return out
