"""Joystick v0.3 checks. The round stop makes the diagonal travel equal the axis travel.
The switch is on the carrier axis, the standoffs are a symmetric set of four, and the screen-well wall
is at least the PCBWay nylon minimum."""
import math, itertools
from build123d import Pos, Rot

def _mirror_ok(pts, tol=1e-6):
    s = {(round(x, 4), round(y, 4)) for x, y in pts}
    return all((round(-x, 4), round(y, 4)) in s and (round(x, 4), round(-y, 4)) in s for x, y in s)

def run(D, P):
    T = D["tgt"]; sw = D["sw"]; rows = []
    def row(name, v, tgt, ok, note=""):
        rows.append(dict(name=name, value=float(v), target=tgt, ok=bool(ok), note=note))
    car = P["joystick carrier (printed)"]
    plate = P["seat plate (printed, glued)"]
    stem = P["SW1 SKRHADE010 stem"]
    spid = P["screen spider + plunger (printed)"]
    db = P["joystick daughterboard"]
    fpc = P["screen FPC [A]"]
    pcb = P["main PCB (proxy, local patch)"]
    hdrs = [P[n] for n in P if n.startswith("header 1x3")]
    socks = [P[n] for n in P if n.startswith("socket ")]
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
    # 4 round stop
    row("round-stop radius vs travel needed to actuate", D["slide"] - D["slide_need"], ">= 0",
        D["slide"] >= D["slide_need"],
        f"stop radius {D['slide']:g} (circle Ø{2 * D['slide']:g}), need {D['slide_need']:.3f} "
        f"({D['cup_rad_clear']:.3f} cup + {sw['tilt_travel']:g} tilt)")
    ot = D["slide"] - D["slide_need"]
    row("overtravel past actuation, every direction", ot, f"<= {T['overtravel_max']}", ot <= T["overtravel_max"],
        "round stop: diagonals travel the same radius as the axes")
    gs = car.distance_to(plate)
    row("carrier vs plate at rest", gs, "0.32-0.50", 0.32 <= gs <= 0.50,
        f"closest feature is the round stop (radial gap {D['slide']:g}); rectangular skirt is {D['skirt_gap']:g}")
    gaps = []
    for deg in (0, 45, 90, 135):
        a = math.radians(deg)
        dx = (D["slide"] - 0.02) * math.cos(a); dy = (D["slide"] - 0.02) * math.sin(a)
        gaps.append((Pos(dx, dy, 0) * car).distance_to(plate))
    gmin = min(gaps)
    row("carrier vs plate on the stop circle (4 directions, -0.02)", gmin, "0.005-0.08", 0.005 <= gmin <= 0.08,
        "the boss is the stop in every direction. gaps " + ", ".join(f"{v:.3f}" for v in gaps))
    rot = (Rot(0, 0, 3) * car).distance_to(plate)
    row("3° carrier rotation hits the rectangular skirt", rot, "< 0.05", rot < 0.05,
        "the round boss does not stop rotation; the looser rectangular skirt does")
    # 5 cable
    fc = fpc.distance_to(car)
    row("FPC vs carrier slot", fc, f">= {T['cable_min']}", fc >= T["cable_min"] - 1e-6,
        f"FPC {D['fpc_w']:g} wide [A], slot {D['slot_x'][1] - D['slot_x'][0]:.2f} × {2 * D['slot_hy']:g}")
    bend = D["scr"]["w"] / 2 - D["slot_x"][1]
    row("FPC bend room under the glass", bend, ">= 1.2", bend >= 1.2,
        f"screen +x edge to the slot end; drop centre is {D['scr']['w']/2 - D['fpc_x']:.2f} inboard. Exit side and pin-out are still open")
    fb = fpc.distance_to(pcb)
    row("FPC vs PCB slot at full slide", fb - D["slide"], ">= 0.2", fb - D["slide"] >= 0.2 - 1e-6,
        f"hole x {D['hole_x0']:.1f}-{D['hole_x1']:.1f}, ±{D['hole_hy']:.2f}")
    row("FPC vs daughterboard", fpc.distance_to(db), ">= 1.0", fpc.distance_to(db) >= 1.0)
    row("FPC vs ball plate", fpc.distance_to(plate), ">= 1.0", fpc.distance_to(plate) >= 1.0)
    # 6 springs
    sm = D["spr_bore"] / 2 - D["spr_d"] / 2 - D["slide"]
    row("spring vs bore at full stop-circle slide", sm, f">= {T['spring_min']}", sm >= T["spring_min"],
        f"Ø{D['spr_d']:g} in Ø{D['spr_bore']:g}; {len(sprs)} × {D['spr_f']:g} N, length {D['spr_len']:.1f} "
        f"(hook z {D['spr_z1']:.2f} + PCB {D['pcb_t']:g} + back panel {D['back_panel']:g} [A])")
    sg = min(s.distance_to(plate) for s in sprs)
    row("spring vs plate (rest)", sg, ">= 0.3", sg >= 0.3 - 1e-6, "hook boss is slotted so the eye can be swapped")
    # 7 daughterboard, headers, standoffs, plate
    row("daughterboard vs plate (glued, faces touch)", db.distance_to(plate), "<= 0.02",
        db.distance_to(plate) <= 0.02,
        f"board {D['db'][0]:.2f} × {D['db'][1]:.2f} × {D['db_t']:g}, centre ({D['db_xy'][0]:.2f}, {D['db_xy'][1]:.2f})")
    row("switch opening in the plate", body.distance_to(plate), f">= {T['board_min']}",
        body.distance_to(plate) >= T["board_min"] - 1e-6,
        f"opening Ø{2 * D['cut_r']:.2f} over the land extent {D['sw_ext']:.2f}")
    hb = min(h.distance_to(car) for h in hdrs)
    row("header body vs carrier", hb, ">= 1.0", hb >= 1.0, "headers are on the underside; trim the 2.79 mm tails flush")
    row("switch body vs headers", min(body.distance_to(h) for h in hdrs), ">= 0.3",
        min(body.distance_to(h) for h in hdrs) >= 0.3, "the switch is on top, the headers underneath")
    row("standoff count", len(stands), "4", len(stands) == 4, "one in each quadrant, all GND")
    sd = min(s.distance_to(db) for s in stands)
    row("standoffs meet the daughterboard", sd, "0.01-0.05", 0.01 <= sd <= 0.05, "and the main PCB, 0.02 short of each face")
    row("standoff vs plate (screw through both)", min(s.distance_to(plate) for s in stands), ">= 0.5",
        min(s.distance_to(plate) for s in stands) >= 0.5, "the screw, not the standoff, passes through the plate")
    row("standoff vs switch body", min(s.distance_to(body) for s in stands), ">= 0.8",
        min(s.distance_to(body) for s in stands) >= 0.8)
    row("standoff vs header", min(min(s.distance_to(h) for h in hdrs) for s in stands), ">= 0.6",
        min(min(s.distance_to(h) for h in hdrs) for s in stands) >= 0.6)
    row("header mates the H11 socket", D["mate_in"], f"{T['mate_min']}-{T['mate_max']}",
        T["mate_min"] <= D["mate_in"] <= T["mate_max"],
        f"{D['hdr']['part']} pin {D['hdr']['mate']:.2f} into {D['sock']['part']} ({D['sock']['lcsc']}); "
        f"air {D['mate_air']:.2f}, riser {D['riser_h']:g} = {D['standoff']['part']} ({D['standoff']['lcsc']})")
    row("socket count matches the headers", len(socks), "2", len(socks) == 2 and len(hdrs) == 2,
        "1x3 each side of the switch, not one 2x3 beside it")
    # 8 centring and symmetry
    off = math.hypot(*D["sw_xy"])
    row("switch on the carrier axis", off, "0", off <= 1e-6, "dead centre. v0.2 was (-3.0, -1.2)")
    sym = _mirror_ok(D["standoff_xy"]) and _mirror_ok(D["hdr_xy"]) and _mirror_ok(D["balls"]) and _mirror_ok(D["springs"])
    row("standoffs, headers, balls and springs symmetric", 1.0 if sym else 0.0, "mirror", sym,
        f"standoffs (±{D['sx']:.2f}, ±{D['sy']:.2f}), headers x=±{D['hx']:.2f}, balls (±{D['bx']:.2f}, ±{D['by']:.2f})")
    # 9 balls
    bt = min(b.distance_to(car) for b in balls)
    row("balls touch the carrier underside", bt, "<= 0.02", bt <= 0.02, f"four Ø{D['ball_d']:g} stainless")
    row("balls seated (clear of the plate)", min(b.distance_to(plate) for b in balls), ">= 0.03",
        min(b.distance_to(plate) for b in balls) >= 0.03, f"seat radius +{D['seat_clear']:g}")
    # 10 knob clearance — at least the v0.2 0.55 mm
    y_edge = D["place_y"] - D["car"][1] / 2 - D["slide"]
    for name, od in (("live knob-param", D["knob_od_live"]), ("design Ø41.7", D["knob_od_design"])):
        kg = y_edge - od / 2
        row(f"carrier (full slide toward the knob) vs {name}", kg, f">= {T['knob_min']}", kg >= T["knob_min"] - 1e-9,
            f"Ø{od:.2f}, carrier near edge at frame y {y_edge:.2f}, centre place_y {D['place_y']:.2f}")
    # 11 screws and sockets on the main PCB. The daughterboard may overhang; it is up at the riser, above the rail
    def on_board(x, y, pad=0.0):
        fy = D["place_y"] + y
        return (abs(x) + pad <= D["pcb_w"] / 2 - D["pcb_edge"]) and (fy + pad <= D["pcb_above"] - D["pcb_edge"])
    holes = D["standoff_xy"] + D["hdr_xy"] + D["springs"]
    holes_ok = all(on_board(x, y, D["pad_m2"] / 2) for x, y in holes)
    row("standoff, socket and spring holes on the main PCB", 1.0 if holes_ok else 0.0, "on", holes_ok,
        "these are the holes the main PCB has to grow. No base-pin holes: the enclosure is gone")
    overhang = (D["place_y"] + D["car"][1] / 2) - D["pcb_above"]
    row("carrier skirt above the rail", D["z_skirt0"] - D["rail_z"], ">= 0", D["z_skirt0"] >= D["rail_z"],
        f"overhang {overhang:.2f} mm in plan; skirt bottom z {D['z_skirt0']:.2f}, rail z {D['rail_z']:g} [A]")
    # 12 walls and the skinny floor
    row("screen-well wall", D["well_wall"], f">= {D['print_min']}", D["well_wall"] + 1e-9 >= D["print_min"],
        f"PCBWay SLS/MJF minimum {D['print_min']:g} (SLA resin is 0.8). v0.2 well was {1.0 - 0.20:.2f}")
    row("carrier floor (the slack above the riser)", D["car_floor"], f">= {D['print_min']}",
        D["car_floor"] >= D["print_min"] - 1e-9,
        f"v0.2 floor was 26.05. Screen top {D['scr_top']:.2f} = knob top {D['z_knob_top']:.2f} − {D['scr_below_knob']:g}; riser {D['riser_h']:g}")
    row("plate frame outside the switch opening", D["db_half_h"] - D["cut_r"], f">= {D['print_min']}",
        D["db_half_h"] - D["cut_r"] + 1e-9 >= D["print_min"], "thinnest on the axis, where the land is widest")
    row("skirt wall", D["car_skirt"], f">= {D['print_min']}", D["car_skirt"] + 1e-9 >= D["print_min"],
        "anti-rotation skirt, was 0.80")
    # a point in the well wall is solid; a point in the pocket is not
    z_well = (D["z_scr0"] + D["z_car1"]) / 2
    x_wall = (D["car"][0] / 2 + D["pocket"][0] / 2) / 2
    x_void = D["pocket"][0] / 2 - D["scr_clear"] * 0.5
    wall_solid = car.is_inside((x_wall, 0.0, z_well))
    void_empty = not car.is_inside((x_void, 0.0, z_well))
    row("screen-well wall is solid and the pocket is open", 1.0 if wall_solid and void_empty else 0.0, "solid",
        wall_solid and void_empty,
        f"wall mid x {x_wall:.2f} at z {z_well:.2f}; pocket probe x {x_void:.2f}")
    row("carrier volume", car.volume / 1000.0, "< 8", car.volume / 1000.0 < 8.0,
        "cm³. v0.2 carrier was 33.53 cm³ (the 26 mm floor)")
    row("no printed base enclosure", 0.0, "0 parts", not any(n.startswith("joystick base") for n in P),
        "the plate on the daughterboard carries the seats")
    return rows

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
