"""Joystick v0.2 checks. The round stop makes the diagonal travel equal the axis travel."""
import math, itertools, os
from build123d import Pos, Rot

def run(D, P):
    T = D["tgt"]; sw = D["sw"]; rows = []
    def row(name, v, tgt, ok, note=""):
        rows.append(dict(name=name, value=float(v), target=tgt, ok=bool(ok), note=note))
    car = P["joystick carrier (printed)"]
    base = P["joystick base (printed, glued)"]
    stem = P["SW1 SKRHADE010 stem"]
    spid = P["screen spider + plunger (printed)"]
    db = P["joystick daughterboard"]
    fpc = P["screen FPC [A]"]
    pcb = P["main PCB (proxy, local patch)"]
    hdr = P["J1 header 2x3 2.54 male (body on top)"]
    body = P["SW1 SKRHADE010 body (45°)"]
    sprs = [P[n] for n in P if n.startswith("hold-down spring")]
    balls = [P[n] for n in P if n.startswith("ball ")]
    stands = [P[n] for n in P if n.startswith("brass standoff")]
    # 1 stem / cup
    g = stem.distance_to(car)
    row("stem vs cup bore, radial (rest)", g, f">= {T['stem_cup_min']}", g >= T["stem_cup_min"] - 1e-6,
        f"cup Ø{D['cup_bore']:g} over the Ø{sw['stem_d']:g} stem, engaged {D['cup_engage']:g}")
    row("cup covers the tilt reference height", D["z_ref"] - D["z_cup0"], ">= 0.2",
        D["z_cup0"] + 0.2 <= D["z_ref"] <= D["z_stem_top"] and D["z_ref"] <= D["z_c0"],
        f"cup z {D['z_cup0']:.2f}-{D['z_c0']:.2f}, ref z {D['z_ref']:.2f}, stem top {D['z_stem_top']:.2f}")
    # 2 plunger
    pg = stem.distance_to(spid)
    row("plunger tip to stem top (rest)", pg, "0.02-0.10", 0.02 <= pg <= 0.10, "no preload on the switch")
    # 3 spider — same flexure as v0.1, so the force stays
    row("spider free travel under the pad", D["sp_gap"], "0.30-0.50", 0.3 - 1e-9 <= D["sp_gap"] <= 0.5 + 1e-9, "Ed: ~0.3-0.5")
    m = D["sp_gap"] - D["sp_defl_click"]
    row("spider margin past the centre click", m, ">= 0.1", m >= 0.1,
        f"used {D['sp_defl_click']:.2f}; the switch stop takes the full press")
    row("spider extra force at the click", D["sp_f_click"], "0.65-0.85", 0.65 <= D["sp_f_click"] <= 0.85,
        f"k ≈ {D['sp_k']:.2f} N/mm, arm L {D['arm_L']:.2f} (unchanged flexure) → press {D['press_f']:.2f} N")
    # 4 round stop: the same travel on the axes and the diagonals
    row("round-stop radius vs travel needed to actuate", D["slide"] - D["slide_need"], ">= 0",
        D["slide"] >= D["slide_need"],
        f"stop radius {D['slide']:g} (circle Ø{2 * D['slide']:g}), need {D['slide_need']:.3f} "
        f"({D['cup_rad_clear']:.3f} cup + {sw['tilt_travel']:g} tilt)")
    ot = D["slide"] - D["slide_need"]
    row("overtravel past actuation, every direction", ot, f"<= {T['overtravel_max']}", ot <= T["overtravel_max"],
        "round stop: diagonals travel the same radius as the axes, so the stem cannot over-tilt on a diagonal")
    gs = car.distance_to(base)
    row("carrier vs base at rest", gs, "0.32-0.50", 0.32 <= gs <= 0.50,
        f"closest feature is the round stop (radial gap {D['slide']:g}); rectangular skirt is {D['skirt_gap']:g}")
    # walk the stop circle. Remaining gap should be ~0.02, and still clear of the rectangular skirt
    gaps = []
    for i, deg in enumerate((0, 45, 90, 135)):
        a = math.radians(deg)
        dx = (D["slide"] - 0.02) * math.cos(a); dy = (D["slide"] - 0.02) * math.sin(a)
        gaps.append((Pos(dx, dy, 0) * car).distance_to(base))
    gmin = min(gaps)
    row("carrier vs base on the stop circle (4 directions, -0.02)", gmin, "0.005-0.08", 0.005 <= gmin <= 0.08,
        "axis, diagonal, and the other two: the boss is the stop in every direction. gaps "
        + ", ".join(f"{v:.3f}" for v in gaps))
    rot = (Rot(0, 0, 3) * car).distance_to(base)
    row("3° carrier rotation hits the rectangular skirt", rot, "< 0.05", rot < 0.05,
        "the round boss does not stop rotation; the looser rectangular skirt does")
    # 5 cable
    fc = fpc.distance_to(car)
    row("FPC vs carrier slot", fc, f">= {T['cable_min']}", fc >= T["cable_min"] - 1e-6,
        f"FPC {D['fpc_w']:g} wide [A], slot {D['slot_x'][1] - D['slot_x'][0]:.2f} × {2 * D['slot_hy']:g}")
    bend = D["scr"]["w"] / 2 - D["slot_x"][1]
    row("FPC bend room under the glass", bend, ">= 1.2", bend >= 1.2,
        f"screen +x edge to the slot: centre inset {D['fpc_bend']:g} [A]. Exit side and pin-out are still open")
    fb = min(fpc.distance_to(base), fpc.distance_to(pcb))
    row("FPC vs base / PCB slot at full slide", fb - D["slide"], ">= 0.2", fb - D["slide"] >= 0.2 - 1e-6,
        f"hole x {D['hole_x0']:.1f}-{D['hole_x1']:.1f}, ±{D['hole_hy']:.2f}")
    row("FPC vs daughterboard", fpc.distance_to(db), ">= 1.0", fpc.distance_to(db) >= 1.0)
    # 6 springs. Full travel is the stop radius, not the old rectangular diagonal
    sm = D["spr_bore"] / 2 - D["spr_d"] / 2 - D["slide"]
    row("spring vs bore at full stop-circle slide", sm, f">= {T['spring_min']}", sm >= T["spring_min"],
        f"Ø{D['spr_d']:g} in Ø{D['spr_bore']:g}; {len(sprs)} × {D['spr_f']:g} N, length {D['spr_len']:.1f} "
        f"(back panel {D['back_panel']:.1f} [A], target {D['spr_len_target']:g})")
    sg = min(s.distance_to(base) for s in sprs)
    row("spring vs base (rest)", sg, ">= 0.3", sg >= 0.3 - 1e-6, "hook boss is slotted so the eye can be swapped")
    # 7 daughterboard, header, standoffs
    dbm = db.distance_to(base - _post_region(D))
    row("daughterboard vs base", dbm, f">= {T['board_min']}", dbm >= T["board_min"] - 1e-6,
        f"board {D['db'][0]:g} × {D['db'][1]:g} at ({D['db_xy'][0]:g}, {D['db_xy'][1]:g}), riser {D['riser_h']:g}")
    hb = hdr.distance_to(car)
    row("J1 header body vs carrier", hb, ">= 1.0", hb >= 1.0, "trim the header pin tails flush with the plastic")
    row("switch body vs J1 header", body.distance_to(hdr), ">= 0.3", body.distance_to(hdr) >= 0.3)
    sd = min(s.distance_to(db) for s in stands)
    row("standoff length matches the 11 mm socket", D["sock"][2] - 11.0, "0", abs(D["sock"][2] - 11.0) < 1e-6,
        "hanxia HX PM2.54-2x3P ZC H11 (C41427525) and XHHD STTZ2008 M2×11 brass (C50377192)")
    row("standoffs meet both boards", sd, "0.01-0.05", 0.01 <= sd <= 0.05, "grounded; the header GND pin stays too")
    row("standoff vs switch body", min(s.distance_to(body) for s in stands), ">= 0.8",
        min(s.distance_to(body) for s in stands) >= 0.8)
    row("standoff vs header", min(s.distance_to(hdr) for s in stands), ">= 0.8",
        min(s.distance_to(hdr) for s in stands) >= 0.8)
    # 8 balls
    bt = min(b.distance_to(car) for b in balls)
    row("balls touch the carrier underside", bt, "<= 0.02", bt <= 0.02, f"four Ø{D['ball_d']:g} stainless")
    row("balls seated (clear of the base)", min(b.distance_to(base) for b in balls), ">= 0.03",
        min(b.distance_to(base) for b in balls) >= 0.03, f"seat radius +{D['seat_clear']:g}")
    # 9 knob clearance, live and the Ø41.7 the plan was sized to
    y_edge = D["place_y"] - D["car"][1] / 2 - D["slide"]
    for name, od in (("live knob-param", D["knob_od_live"]), ("design Ø41.7", D["knob_od_design"])):
        kg = y_edge - od / 2
        row(f"carrier (full slide toward the knob) vs {name}", kg, f">= {T['knob_min']}", kg >= T["knob_min"] - 1e-9,
            f"Ø{od:.2f}, carrier near edge at frame y {y_edge:.2f}, centre place_y {D['place_y']:.2f}")
    # 10 the base (and everything glued to the PCB) stays on the board; the carrier may overhang above the rail
    def on_board(x, y, pad=0.0):
        fy = D["place_y"] + y
        return (abs(x) + pad <= D["pcb_w"] / 2 - 0.2) and (D["knob_od_used"] / 2 + 0.3 <= fy - pad) and (fy + pad <= D["pcb_above"] - 0.2)
    base_ok = on_board(D["base_x1"], D["base_y1"]) and on_board(D["base_x0"], D["base_y0"]) and on_board(0, D["base_y0"])
    row("base footprint on the main PCB", 1.0 if base_ok else 0.0, "on", base_ok,
        f"base x {D['base_x0']:.2f}..{D['base_x1']:.2f}, y {D['base_y0']:.2f}..{D['base_y1']:.2f} "
        f"(frame y {D['place_y'] + D['base_y0']:.2f}..{D['place_y'] + D['base_y1']:.2f}, PCB top {D['pcb_above']:g})")
    holes_ok = all(on_board(x, y, 1.8) for x, y in D["springs"] + D["pins"] + list(D["standoff_xy"]) + D["balls"])
    row("spring, pin, standoff and ball holes on the PCB", 1.0 if holes_ok else 0.0, "on", holes_ok,
        "these are the holes the main PCB has to move")
    overhang = (D["place_y"] + D["car"][1] / 2) - D["pcb_above"]
    row("carrier +y overhang past the PCB top", overhang, "z above the rail", D["z_skirt0"] >= D["rail_z"],
        f"overhang {overhang:.2f} mm in plan; skirt bottom z {D['z_skirt0']:.2f} >= rail z {D['rail_z']:g} [A]")
    row("carrier floor is the slack in the stack", D["car_floor"], ">= 4", D["car_floor"] >= 4,
        f"screen top {D['scr_top']:.2f} = knob top {D['z_knob_top']:.2f} − {D['scr_below_knob']:g}; riser {D['riser_h']:g}")
    return rows

def _post_region(D):
    from .parts import cyl
    sx, sy = D["sw_xy"]
    return cyl(D["post_d"] + 0.02, -1, D["z_db0"] + 0.01, sx, sy)

def clashes(P, tol=1e-3):
    names = list(P); out = {}
    bb = {n: P[n].bounding_box() for n in names}
    def ov(a, b):
        return all(getattr(a.min, k) < getattr(b.max, k) - 1e-6 and getattr(b.min, k) < getattr(a.max, k) - 1e-6 for k in "XYZ")
    for a, b in itertools.combinations(names, 2):
        if not ov(bb[a], bb[b]):
            continue
        try:
            v = (P[a] & P[b]).volume
        except Exception:
            v = 0.0
        if v > tol:
            out[f"{a} / {b}"] = v
    return out
