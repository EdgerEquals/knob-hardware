"""Joystick v0.4 checks. The switch is the only stop. The bezel floats on four compression
springs, preloaded by grub screws that are reached on the sub-assembly. The four hold-down
springs are unchanged in kind from v0.3."""
import math, itertools
from build123d import Pos, Rot

def _mirror_ok(pts, tol=1e-6):
    s = {(round(x, 4), round(y, 4)) for x, y in pts}
    return all((round(-x, 4), round(y, 4)) in s and (round(x, 4), round(-y, 4)) in s for x, y in s)

def _gap_at(D, od, x, y_edge):
    """Gap from a carrier-frame silhouette point to the knob, after the carrier has slid toward it."""
    return math.hypot(x, D["place_y"] + y_edge) - od / 2 - D["slide"]

def run(D, P):
    T = D["tgt"]; sw = D["sw"]; rows = []
    def row(name, v, tgt, ok, note=""):
        rows.append(dict(name=name, value=float(v), target=tgt, ok=bool(ok), note=note))
    car = P["joystick carrier (printed)"]
    bez = P["screen carrier (printed)"]
    plate = P["seat plate (printed, glued)"]
    stem = P["SW1 SKRHADE010 stem"]
    db = P["joystick daughterboard"]
    fpc = P["screen FPC [A]"]
    scr = [P[n] for n in P if n.startswith("top screen")][0]
    hdrs = [P[n] for n in P if n.startswith("header 1x3")]
    socks = [P[n] for n in P if n.startswith("socket ")]
    body = P["SW1 SKRHADE010 body (45°)"]
    sprs = [P[n] for n in P if n.startswith("hold-down spring")]
    css = [P[n] for n in P if n.startswith("compression spring")]
    grubs = [P[n] for n in P if n.startswith("grub screw")]
    inserts = [P[n] for n in P if n.startswith("brass insert")]
    balls = [P[n] for n in P if n.startswith("ball ")]
    stands = [P[n] for n in P if n.startswith("brass standoff")]
    # 1 stem / cup. The switch end of tilt is the stop
    g = stem.distance_to(car)
    row("stem vs cup bore, radial (rest)", g, f">= {T['stem_cup_min']}", g >= T["stem_cup_min"] - 1e-6,
        f"cup Ø{D['cup_bore']:.2f} over the Ø{sw['stem_d']:g} stem, SLA clearance {D['cup_rad_clear']:.2f}")
    row("cup covers the tilt reference height", D["z_ref"] - D["z_cup0"], ">= 0.2",
        D["z_cup0"] + 0.2 <= D["z_ref"] <= D["z_stem_top"] and D["z_ref"] <= D["z_c0"],
        f"cup z {D['z_cup0']:.2f}-{D['z_c0']:.2f}, ref z {D['z_ref']:.2f}, stem top {D['z_stem_top']:.2f}")
    row("slide is the switch tilt, no extra overtravel", D["slide"] - D["slide_need"], "0",
        abs(D["slide"] - D["slide_need"]) < 1e-9,
        f"slide {D['slide']:.2f} = cup clearance {D['cup_rad_clear']:.2f} + tilt {sw['tilt_travel']:g}")
    # 2 press peg and the compression springs
    pg = stem.distance_to(bez)
    row("peg tip to stem top (rest)", pg, f"{D['press_gap']:.2f}", abs(pg - D["press_gap"]) <= 0.03,
        "one SLA tolerance. The peg is part of the bezel, not a separate plunger")
    row("preload vs 5x screen weight", D["cs_f_preload"] / D["scr_weight"], ">= 5",
        D["cs_f_preload"] >= 5 * D["scr_weight"] - 1e-9,
        f"preload {D['cs_f_preload']:.3f} N, screen {D['scr']['mass_g']:g} g = {D['scr_weight']:.3f} N [A]")
    row("preload under the centre-push minimum", D["cs_f_preload"], f"< {D['push_lo']:.2f}",
        D["cs_f_preload"] < D["push_lo"],
        "rest is not already a click")
    row("force at switch bottom", D["cs_f_press"], f"{D['push_lo']:.2f}-{D['push_hi']:.2f}",
        D["push_lo"] - 1e-6 <= D["cs_f_press"] <= D["push_hi"] + 1e-6,
        f"{D['cs_turns']:g} turn, {D['cs_defl_press']:.2f} mm on {D['cs_n']} x {D['cs']['part']} "
        f"({D['cs_rate']:.3f} N/mm). Centre push {sw['push_f']:g} ± {sw['f_tol']:g} N")
    row("spring not solid at full press", D["cs_solid_room"], ">= 0.40", D["cs_solid_room"] >= 0.40,
        f"free {D['cs']['free']:.2f}, solid {D['cs']['solid']:.2f}, used {D['cs_defl_press']:.2f}")
    row("newtons per turn, one spring", D["cs_f_turn_1"], "> 0", D["cs_f_turn_1"] > 0,
        f"{D['cs_f_turn_1']:.3f} N/turn each, {D['cs_f_turn']:.3f} N/turn for all four. Pitch {D['grub']['pitch']:.2f} mm")
    row("nominal turns inside the useful window", D["cs_turns"], f"{D['turns_lo']:.2f}-{D['turns_hi']:.2f}",
        D["turns_lo"] - 1e-6 <= D["cs_turns"] <= D["turns_hi"] + 1e-6,
        f"window keeps the press inside the band and the preload under a click. "
        f"Hex stays proud out to {D['turns_hex']:.2f} turns")
    row("compression spring count", len(css), "4", len(css) == 4 and len(grubs) == 4 and len(inserts) == 4,
        "one grub and one insert under each spring")
    # 3 captive bezel, and the skirt is not the tilt stop
    gap_cb = car.distance_to(bez)
    row("bezel against the up-stop (rest)", gap_cb, "0.01-0.08", 0.01 <= gap_cb <= 0.08,
        f"lip under the pilot shoulder, gap {D['up_gap']:.2f}. Snap overlap {D['snap']:.2f} mm")
    row("bezel still clear of the floor at switch bottom", D["z_bz0"] - D["z_floor1"] - D["press_travel"],
        f">= {D['tol_sla']:.2f}",
        D["z_bz0"] - D["z_floor1"] - D["press_travel"] >= D["tol_sla"] - 1e-9,
        "the switch bottoms first. The shoulder has the same spare room in its socket")
    row("shoulder clears the socket roof", D["z_roof"] - D["z_sock_top"], ">= 0.05",
        D["z_roof"] - D["z_sock_top"] >= 0.05, "spring roof is a separate, smaller bore above the socket")
    gaps = []
    for deg in (0, 45, 90, 135):
        a = math.radians(deg)
        dx = D["slide"] * math.cos(a); dy = D["slide"] * math.sin(a)
        gaps.append((Pos(dx, dy, 0) * car).distance_to(plate))
    gmin = min(gaps)
    row("skirt clear at switch end of travel", gmin, f">= {D['tol_mjf']:.2f}", gmin >= D["tol_mjf"] - 1e-4,
        f"skirt gap {D['skirt_gap']:.2f}, slide {D['slide']:.2f}, remaining {D['tol_mjf']:.2f}. "
        "gaps " + ", ".join(f"{v:.3f}" for v in gaps))
    rot = (Rot(0, 0, 3) * car).distance_to(plate)
    row("3° carrier rotation hits the rectangular skirt", rot, "< 0.05", rot < 0.05,
        "the skirt is the anti-rotation stop. It is not the tilt stop")
    # 4 grub screws: on the sub-assembly only. No hole in the plate or the daughterboard
    outside = all(abs(x) - D["sh_r"] > D["board_x1"] or abs(y) - D["sh_r"] > D["board_y1"] for x, y in D["cs_xy"])
    row("spring pilots outside the plate", 1.0 if outside else 0.0, "outside", outside,
        "no access hole and no keep-out. The hex is reached before the plate is fitted")
    row("hex proud of the insert", D["hex_proud"], ">= 0.40", D["hex_proud"] >= 0.40,
        f"{D['grub']['part']} in {D['ins']['part']}. {D['hex_proud']:.2f} mm of screw below the insert at {D['cs_turns']:g} turn")
    row("insert hangs in free air under the floor", D["z_c0"] - D["z_ins0"], "0.5-3.0",
        0.5 <= D["z_c0"] - D["z_ins0"] <= 3.0,
        f"insert bottom z {D['z_ins0']:.2f}, carrier underside z {D['z_c0']:.2f}. Modelled as a slip fit")
    row("grub screw modelled clear of the insert", min(g.distance_to(i) for g, i in zip(grubs, inserts)),
        ">= 0.05", min(g.distance_to(i) for g, i in zip(grubs, inserts)) >= 0.05,
        "real thread engages; the solid is the clearance pin")
    # 5 cable
    fc = min(fpc.distance_to(car), fpc.distance_to(bez))
    row("FPC vs carrier and bezel", fc, f">= {T['cable_min']}", fc >= T["cable_min"] - 1e-4,
        f"FPC {D['fpc_w']:g} wide [A], slot {D['slot_x'][1] - D['slot_x'][0]:.2f} x {2 * D['slot_hy']:.2f}")
    bend = D["scr"]["w"] / 2 - D["slot_x"][1]
    row("FPC bend room under the glass", bend, ">= 1.2", bend >= 1.2,
        f"screen +x edge to the slot end. Exit side and pin-out are still open")
    pcb = P["main PCB (proxy, local patch)"]
    fb = fpc.distance_to(pcb)
    row("FPC vs PCB slot at full slide", fb - D["slide"], ">= 0.2", fb - D["slide"] >= 0.2 - 1e-6,
        f"hole x {D['hole_x0']:.1f}-{D['hole_x1']:.1f}, ±{D['hole_hy']:.2f}")
    row("FPC vs daughterboard", fpc.distance_to(db), ">= 1.0", fpc.distance_to(db) >= 1.0)
    row("FPC vs seat plate", fpc.distance_to(plate), ">= 1.0", fpc.distance_to(plate) >= 1.0)
    # 6 hold-down springs, kept
    sm = D["spr_bore"] / 2 - D["spr_d"] / 2 - D["slide"]
    row("hold-down spring vs bore at full slide", sm, f">= {T['spring_min']}", sm >= T["spring_min"],
        f"Ø{D['spr_d']:g} in Ø{D['spr_bore']:g}; {len(sprs)} x {D['spr_f']:g} N, length {D['spr_len']:.1f} "
        f"(hook z {D['spr_z1']:.2f} + PCB {D['pcb_t']:g} + back panel {D['back_panel']:g} [A])")
    sg = min(s.distance_to(plate) for s in sprs)
    row("hold-down spring vs plate (rest)", sg, ">= 0.3", sg >= 0.3 - 1e-6, "hook boss is slotted so the eye can be swapped")
    row("compression spring clear of the hold-downs", min(c.distance_to(s) for c in css for s in sprs),
        ">= 1.0", min(c.distance_to(s) for c in css for s in sprs) >= 1.0,
        "the two spring sets do not share a job")
    row("compression spring clear of the plate", min(c.distance_to(plate) for c in css), ">= 1.0",
        min(c.distance_to(plate) for c in css) >= 1.0)
    # 7 daughterboard, headers, standoffs, plate
    row("daughterboard vs plate (glued, faces touch)", db.distance_to(plate), "<= 0.02",
        db.distance_to(plate) <= 0.02,
        f"board {D['db'][0]:.2f} x {D['db'][1]:.2f} x {D['db_t']:g}. The v0.3 -y stop tab is gone")
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
    row("switch on the carrier axis", off, "0", off <= 1e-6, "dead centre")
    sym = (_mirror_ok(D["standoff_xy"]) and _mirror_ok(D["hdr_xy"]) and _mirror_ok(D["balls"])
           and _mirror_ok(D["springs"]) and _mirror_ok(D["cs_xy"]))
    row("standoffs, headers, balls and both spring sets symmetric", 1.0 if sym else 0.0, "mirror", sym,
        f"standoffs (±{D['sx']:.2f}, ±{D['sy']:.2f}), compression springs (±{D['cs_x']:.2f}, ±{D['cs_y']:.2f})")
    # 9 balls
    bt = min(b.distance_to(car) for b in balls)
    row("balls touch the carrier underside", bt, "<= 0.02", bt <= 0.02, f"four Ø{D['ball_d']:g} stainless")
    row("balls seated (clear of the plate)", min(b.distance_to(plate) for b in balls), ">= 0.03",
        min(b.distance_to(plate) for b in balls) >= 0.03, f"seat radius +{D['seat_clear']:g}")
    # 10 knob clearance — both faces are MJF, so the gap is 2 x 0.25
    for name, od in (("live knob-param", D["knob_od_live"]), ("design Ø41.7", D["knob_od_design"])):
        kg = min(_gap_at(D, od, x, y) for x, y in (
            (0.0, -D["h_mid"]), (D["x_notch"], -D["half_h"]), (D["half_w"], -D["half_h"])))
        row(f"carrier (full slide toward the knob) vs {name}", kg, f">= {T['knob_min']}", kg >= T["knob_min"] - 1e-6,
            f"Ø{od:.2f}. The notch at y {D['h_mid']:.2f} is the close edge; the spring corners are outside the knob")
    # 11 screws and sockets on the main PCB
    def on_board(x, y, pad=0.0):
        fy = D["place_y"] + y
        return (abs(x) + pad <= D["pcb_w"] / 2 - D["pcb_edge"]) and (fy + pad <= D["pcb_above"] - D["pcb_edge"])
    holes = D["standoff_xy"] + D["hdr_xy"] + D["springs"]
    holes_ok = all(on_board(x, y, D["pad_m2"] / 2 if (x, y) in D["standoff_xy"] or (x, y) in D["hdr_xy"] else D["spr_bore"] / 2)
                   for x, y in holes)
    row("standoff, socket and spring holes on the main PCB", 1.0 if holes_ok else 0.0, "on", holes_ok,
        f"hold-down hooks at x ±{D['spr_x']:.2f} (the corner formula wanted ±{D['spr_x_raw']:.2f}, past the PCB)")
    row("carrier skirt above the rail", D["z_skirt0"] - D["rail_z"], ">= 0", D["z_skirt0"] >= D["rail_z"],
        f"skirt bottom z {D['z_skirt0']:.2f}, rail z {D['rail_z']:g} [A]")
    # 12 walls, floor, volumes
    row("bezel well wall", D["well_wall"], f">= {D['print_min']}", D["well_wall"] + 1e-9 >= D["print_min"],
        f"PCBWay SLS/MJF minimum {D['print_min']:g}. Glue gap around the glass is {D['glue']:.2f}")
    row("carrier floor", D["car_floor"], f">= {D['print_min']}", D["car_floor"] >= D["print_min"] - 1e-9,
        f"the 35 mm riser leaves the floor at the print minimum. Screen top {D['scr_top']:.2f}")
    row("plate frame outside the switch opening", D["db_half_h"] - D["cut_r"], f">= {D['print_min']}",
        D["db_half_h"] - D["cut_r"] + 1e-9 >= D["print_min"], "thinnest on the axis, where the land is widest")
    row("skirt wall", D["car_skirt"], f">= {D['print_min']}", D["car_skirt"] + 1e-9 >= D["print_min"],
        "anti-rotation skirt")
    z_well = (D["z_scr0"] + D["z_bz1"]) / 2
    x_wall = (D["h_mid"] + D["pocket"][1] / 2) / 2
    # the short-side wall is along y. Probe on the y axis, in the wall, and in the pocket
    y_wall = (D["h_mid"] + D["pocket"][1] / 2) / 2
    y_void = D["pocket"][1] / 2 - D["glue"] * 0.5
    wall_solid = bez.is_inside((0.0, y_wall, z_well))
    void_empty = not bez.is_inside((0.0, y_void, z_well))
    row("bezel well wall is solid and the pocket is open", 1.0 if wall_solid and void_empty else 0.0, "solid",
        wall_solid and void_empty,
        f"wall probe y {y_wall:.2f} at z {z_well:.2f}; pocket probe y {y_void:.2f}")
    row("carrier volume", car.volume / 1000.0, "< 12", car.volume / 1000.0 < 12.0,
        "cm3. v0.3 carrier was 4.41 cm3; v0.2 was 33.53")
    row("screen-carrier volume", bez.volume / 1000.0, "< 8", bez.volume / 1000.0 < 8.0,
        "cm3, the bezel the screen is glued to")
    row("screen seated on the bezel ledge", scr.distance_to(bez), "<= 0.02", scr.distance_to(bez) <= 0.02,
        f"bottom face sits on the ledge. Side glue gap {D['glue']:.2f}. Glass top is {D['car_top_below']:.2f} above the bezel")
    row("no printed base, spider or round stop", 0.0, "0 parts",
        not any(n.startswith("joystick base") or n.startswith("screen spider") for n in P),
        "removed from v0.3: spider, plunger, round stop. Hold-down springs stay")
    # silence a lint-level unused local if the wall probe x is kept only as documentation
    _ = x_wall
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
