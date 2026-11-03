"""Joystick v0.4/v0.5 checks. The switch is the only stop. The bezel floats on four compression
springs, preloaded by grub screws that are reached on the sub-assembly. The four hold-down
springs are unchanged in kind from v0.3."""
import math, itertools
from build123d import Pos, Rot
from .parts import cyl as cyl_, DB_NAME, CC_NAME, GK_NAME

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
    cradle_on = D.get("base") == "cradle"
    case_on = D.get("base") == "case"   # v0.7 layout v4: top board on the spring contacts, cradle captured by the case
    plate = (P[CC_NAME] if case_on else P["joystick cradle (printed, glued)"] if cradle_on
             else P["seat plate (printed, glued)"])   # v0.5: the cradle carries the seats; v0.7: the case cradle does
    stem = P["SW1 SKRHADE010 stem"]
    db = P[DB_NAME] if case_on else P["joystick daughterboard"]
    pcb = P["main PCB (proxy, local patch)"]
    fpc = P["screen FPC [A]"] if "screen FPC [A]" in P else P["screen jumper FPC [A]"]
    scr = [P[n] for n in P if n.startswith("top screen")][0]
    hdrs = [P[n] for n in P if n.startswith("header ") and "long pin" in n]
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
    pegs = [P[n] for n in P if n.startswith("press peg grub")]
    pg = stem.distance_to(pegs[0] if pegs else bez)
    row("peg tip to stem top (rest)", pg, f"{D['press_gap']:.2f}", abs(pg - D["press_gap"]) <= 0.03,
        "nominal; the M2 grub peg is set to this gap with a feeler before the glass goes on" if pegs else
        "one SLA tolerance. The peg is part of the bezel, not a separate plunger")
    if pegs:
        row("press peg thread in the roof insert", D["p_engage"], ">= 2.0", D["p_engage"] >= 2.0 - 1e-6,
            f"{D['peg']['part']}, M2x{D['p_len']:.0f}; tip z {D['z_peg']:.2f}")
        row("press peg adjustment (down / up, keeping 2 mm of thread)", min(D["p_adjust"]), ">= 0.3", min(D["p_adjust"]) >= 0.3 - 1e-6,
            f"down {D['p_adjust'][0]:.2f}, up {D['p_adjust'][1]:.2f}: covers the printed-part and glue stack")
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
    fp = P["faceplate (case proxy, UTR-8100)"]
    gap_fp = bez.distance_to(fp)
    row("bezel lip above the faceplate", D["z_bz0"] - D["z_fp1"], "0.02",
        abs(D["z_bz0"] - D["z_fp1"] - D["up_gap"]) < 1e-6 and gap_fp > 0.05,
        f"vertical gap {D['up_gap']:.2f}. The rebate is wider than the lip by {D['tol_sla']:.2f}, "
        f"so the closest solid is {gap_fp:.2f} mm. Overlap {D['fp_overlap']:.2f} mm")
    gh = D["z_bz1"] - D["z_bz0"]
    row("grip block height (bezel underside to rim)", gh, f">= {D['grip_h']:.1f}", gh >= D["grip_h"] - 1e-9,
        f"[Ed 2 Nov] at least 5 mm to hold; glass top {D['scr_top'] - D['z_fp1']:.2f} above the faceplate, "
        f"{D['z_glass'] - D['scr_top']:.2f} under the knob screen. Walls {D['bz_lip']:.2f}, outer {2*D['half_w']:.2f} x {2*D['half_h']:.2f}")
    cl_ = D["z_bz0"] - D["press_travel"] - D["z_fp1"]
    row("block clear of the flat faceplate at full press", cl_, f">= {D['tol_sla']:.2f}", cl_ >= D["tol_sla"] - 1e-9,
        f"the case face has no rebate: the block floats {D['up_gap']:.2f} above it and the switch bottoms first")
    fpp = P["faceplate (case proxy, UTR-8100)"]
    dg = min((Pos(D["slide"] * math.cos(math.radians(a)), D["slide"] * math.sin(math.radians(a)), 0) * car).distance_to(fpp)
             for a in range(0, 360, 45))
    row("carrier clear of the rounded faceplate opening at full slide", dg, f">= {D['tol_sla']:.2f}", dg >= D["tol_sla"] - 1e-6,
        f"carrier floor corners R{D.get('corner_r', 0):g} like the opening; checked every 45°")
    cu = D["z_bz0"] - D["z_floor1"]
    row("carrier floor under the bezel (it rises into the faceplate hole)", cu, ">= 0.2", cu >= 0.2 - 1e-9,
        f"v0.5: 30 mm riser. Carrier floor z {D['z_c0']:.2f}-{D['z_floor1']:.2f} inside the faceplate {D['z_fp0']:.2f}-{D['z_fp1']:.2f}; "
        f"bezel underside z {D['z_bz0']:.2f}")
    fits = (D["car_hw"] + D["slide"] + D["tol_sla"] <= D["hole_hw"] + 1e-9
            and D["car_hh"] + D["slide"] + D["tol_sla"] <= D["hole_hh"] + 1e-9)
    row("carrier drops through the faceplate hole", 1.0 if fits else 0.0, "fits", fits,
        f"carrier ±{D['car_hw']:.2f} x ±{D['car_hh']:.2f}, hole ±{D['hole_hw']:.2f} x ±{D['hole_hh']:.2f}, slide {D['slide']:.2f}")
    row("bezel lip bigger than the hole", D["half_w"] - D["hole_hw"], ">= 0.6",
        D["half_w"] - D["hole_hw"] >= 0.6, "the lip cannot fall through. It is fitted from the front")
    if case_on:
        _case_rows(D, P, row, car, bez, plate, db)
    gaps = []
    for deg in range(0, 360, 45):
        a = math.radians(deg)
        dx = D["slide"] * math.cos(a); dy = D["slide"] * math.sin(a)
        moved = Pos(dx, dy, 0) * car
        gaps.append(min(moved.distance_to(plate), moved.distance_to(db)))   # v0.5: the daughterboard tab passes the skirt notch
    gmin = min(gaps)
    if case_on:   # v0.7: no skirt. The carrier slides inside the lip ring, which is also the anti-rotation stop
        row("carrier clear of the cradle's lip ring at full slide (every 45°)", gmin, f">= {D['tol_sla']:.2f}", gmin >= D["tol_sla"] - 1e-4,
            f"carrier ±{D['car_hw']:.2f} × ±{D['car_hh']:.2f} (v0.6 ±20.46 × ±13.02: narrowed {D['car_narrow']:.2f} by the lip and its "
            f"clearance), lip inner face ±{D['lip_in_hw']:.2f} × ±{D['lip_in_hh']:.2f}; gaps " + ", ".join(f"{v:.3f}" for v in gaps))
        rot = (Rot(0, 0, 3) * car).distance_to(plate)
        row("3° carrier rotation meets the lip ring (anti-rotation stop)", rot, "< 0.05", rot < 0.05,
            "the lip ring replaces the v0.6 skirt as the anti-rotation stop. It is not the tilt stop (the switch is)")
    else:
        row("skirt clear at switch end of travel", gmin, f">= {D['tol_mjf']:.2f}", gmin >= D["tol_mjf"] - 1e-4,
            f"skirt gap {D['skirt_gap']:.2f}, slide {D['slide']:.2f}, remaining {D['tol_mjf']:.2f}. "
            "gaps " + ", ".join(f"{v:.3f}" for v in gaps))
        rot = min((Rot(0, 0, 3) * car).distance_to(plate), (Rot(0, 0, 3) * car).distance_to(db))
        row("3° carrier rotation hits the rectangular skirt", rot, "< 0.05", rot < 0.05,
            "the skirt is the anti-rotation stop. It is not the tilt stop")
    # 4 grub screws: on the sub-assembly only. No hole in the plate or the daughterboard
    if cradle_on or case_on:   # v0.5: the press springs sit inside the corner balls; the grubs stay reachable from underneath
        from build123d import Pos as _P
        hits, who = 0.0, "none"
        grub_names = [n for n in P if n.startswith("grub screw")]
        for (x, y), gname in zip(D["cs_xy"], grub_names):
            g_bb = P[gname].bounding_box()
            line = cyl_(D["grub_access_d"] - 0.3, -12.0, g_bb.min.Z - 0.05, x, y)   # a 1.3 hex-key line from behind the PCB
            for n, s_ in P.items():
                if n.startswith(("grub screw", "faceplate (case proxy")):
                    continue
                try:
                    v = (line & s_).volume
                except Exception:
                    v = 1e9
                if v > 1e-3 and v > hits:
                    hits, who = v, n
        row("press-spring grubs reachable from behind the main PCB (key line clear, mm³)", hits, "0", hits <= 1e-3,
            f"[Ed 13:23] stations (±{D['cs_x']:.2f}, ±{D['cs_y']:.2f}) inside the cradle ring; Ø{D['grub_access_d']:g} holes in "
            f"the main PCB and the joystick board; worst: {who}. Before the back cover goes on")
    else:
        outside = all(abs(x) - D["cs_bore_r"] > D["board_x1"] or abs(y) - D["cs_bore_r"] > D["board_y1"] for x, y in D["cs_xy"])
        row("spring pilots outside the plate", 1.0 if outside else 0.0, "outside", outside,
            "no access hole and no keep-out. The hex is reached before the plate is fitted")
    row("hex proud of the insert", D["hex_proud"], ">= 0.40", D["hex_proud"] >= 0.40,
        f"{D['grub']['part']} in {D['ins']['part']}. {D['hex_proud']:.2f} mm of screw below the insert at {D['cs_turns']:g} turn")
    row("insert hangs in free air under the floor", D["z_c0"] - D["z_ins0"], "0.3-3.0",
        0.3 <= D["z_c0"] - D["z_ins0"] <= 3.0,
        f"insert bottom z {D['z_ins0']:.2f}, carrier underside z {D['z_c0']:.2f}. Modelled as a slip fit")
    row("grub screw modelled clear of the insert", min(g.distance_to(i) for g, i in zip(grubs, inserts)),
        ">= 0.05", min(g.distance_to(i) for g, i in zip(grubs, inserts)) >= 0.05,
        "real thread engages; the solid is the clearance pin")
    # 5 cable
    fc = min(fpc.distance_to(car), fpc.distance_to(bez))
    row("FPC vs carrier and bezel", fc, f">= {T['cable_min']}", fc >= T["cable_min"] - 1e-4,
        f"FPC {D['fpc_w']:g} wide [A], slot {D['slot_x'][1] - D['slot_x'][0]:.2f} x {2 * D['slot_hy']:.2f}")
    if "win_x" not in D:   # v0.5: the panel's own tail bent round the glass edge
        bend = D["scr"]["w"] / 2 - D["slot_x"][1]
        row("FPC bend room under the glass", bend, ">= 1.2", bend >= 1.2,
            f"screen +x edge to the slot end. Exit side and pin-out are still open")
    fb = fpc.distance_to(pcb)
    row("FPC vs PCB slot at full slide", fb - D["slide"], ">= 0.2", fb - D["slide"] >= 0.2 - 1e-6,
        f"hole x {D['hole_x0']:.1f}-{D['hole_x1']:.1f}, ±{D['hole_hy']:.2f}")
    row("FPC vs daughterboard" if not case_on else "FPC vs the top board", fpc.distance_to(db), ">= 1.0", fpc.distance_to(db) >= 1.0)
    if case_on:   # v0.7: the jumper's S1 leg (x 18.5) runs beside the +x hanger of the case cradle (no moving part between them)
        fp_ = fpc.distance_to(plate)
        row("FPC vs the case cradle (hanger beside the S1 leg)", fp_, f">= {T['cable_min']:.2f}", fp_ >= T["cable_min"] - 1e-6,
            f"S1 leg at x {D['jmp_xv']:g}, hanger inner face x {D['nest_hw']:.2f}; both fixed (the leg's moving end is above the "
            "cradle, inside the lip ring)")
    else:
        row("FPC vs seat plate", fpc.distance_to(plate), ">= 1.0", fpc.distance_to(plate) >= 1.0)
    # 6 hold-down springs, kept
    sm = D["spr_bore"] / 2 - D["spr_d"] / 2 - D["slide"]
    row("hold-down spring vs bore at full slide", sm, f">= {T['spring_min']}", sm >= T["spring_min"],
        f"Ø{D['spr_d']:g} in Ø{D['spr_bore']:g}; {len(sprs)} x {D['spr_f']:g} N, installed {D['spr_len']:.1f} mm "
        f"(was {D['spr_len_was']:.1f} to the back panel). Free {D['spr_free']:.1f}, stretch {D['spr_ext']:.1f}")
    sg = min(s.distance_to(plate) for s in sprs)
    row("hold-down spring vs plate (rest)", sg, ">= 0.3", sg >= 0.3 - 1e-6, "hook boss is slotted so the eye can be swapped")
    row("compression spring clear of the hold-downs", min(c.distance_to(s) for c in css for s in sprs),
        ">= 1.0", min(c.distance_to(s) for c in css for s in sprs) >= 1.0,
        "the two spring sets do not share a job")
    row("compression spring clear of the plate", min(c.distance_to(plate) for c in css), ">= 1.0",
        min(c.distance_to(plate) for c in css) >= 1.0)
    # 7 daughterboard, headers, standoffs, plate
    row("top board on the cradle shoulders (glued, faces touch)" if case_on else "daughterboard vs plate (glued, faces touch)",
        db.distance_to(plate), "<= 0.02", db.distance_to(plate) <= 0.02,
        f"board {D['db'][0]:.2f} x {D['db'][1]:.2f} x {D['db_t']:g}" + (f" at y {D['board_y0']:.2f}..{D['board_y1']:.2f}; the spring "
        "contacts push it up against the shoulders" if case_on else ". The v0.3 -y stop tab is gone"))
    row("switch opening in the plate", body.distance_to(plate), f">= {T['board_min']}",
        body.distance_to(plate) >= T["board_min"] - 1e-6,
        f"opening Ø{2 * D['cut_r']:.2f} over the land extent {D['sw_ext']:.2f}")
    if hdrs:
        hb = min(h.distance_to(car) for h in hdrs)
        row("header body vs carrier", hb, ">= 1.0", hb >= 1.0, "headers are on the underside; trim the 2.79 mm tails flush")
        row("switch body vs headers", min(body.distance_to(h) for h in hdrs), ">= 0.3",
            min(body.distance_to(h) for h in hdrs) >= 0.3, "the switch is on top, the headers underneath")
    bots = [P[n] for n in P if n.startswith("M2 socket screw bottom")]
    tops = [P[n] for n in P if n.startswith("M2 socket screw top")]
    if cradle_on:
        C = D["cradle"]
        row("cradle replaces the standoffs (none modelled)", len(stands), "0", len(stands) == 0 and not bots and not tops,
            f"[Ed 2 Nov] {C['part']}, {C['h']:g} mm; board glued on a {C['land']:.1f} mm land; two {C['pin']['part']} locate it on the PCB")
        foot = D["cr_out_y1"] <= D["y_pcb"] - D["pcb_edge"] + 1e-9 and D["cr_out_x"] <= D["pcb_w"] / 2 - D["pcb_edge"]
        row("cradle ring glued inside the main-PCB outline", D["y_pcb"] - D["pcb_edge"] - D["cr_out_y1"], ">= 0", foot,
            f"ring ±{D['cr_out_x']:.2f} x {D['cr_out_y0']:.2f}..{D['cr_out_y1']:.2f}; PCB top edge local y {D['y_pcb']:.2f}. "
            f"The top towers start at z {C['tower_z0']:g}, above the case's top corner posts, and hang off the ring")
        bt_ = min(math.hypot(abs(x) - D["board_x1"] if abs(x) > D["board_x1"] else 0.0,
                             abs(y) - D["board_y1"] if abs(y) > D["board_y1"] else 0.0) - D["boss_r"] for x, y in D["balls"])
        row("joystick board clear of the cradle towers", bt_, f">= {D['tol_mjf']:.2f}", bt_ >= D["tol_mjf"] - 1e-6,
            f"towers r {D['boss_r']:.2f} at (±{D['bx']:.2f}, +{D['by_top']:.2f} / −{D['by_bot']:.2f}); board ±{D['board_x1']:.2f} × ±{D['board_y1']:.2f}")
        cb_ = min(D["car_hw"] - (abs(x) + D["boss_r"]) for x, _ in D["balls"])
        cby = min(D["car_hh"] - (abs(y) + D["boss_r"]) for _, y in D["balls"])
        row("carrier cup bosses inside the carrier outline", min(cb_, cby), ">= 0", min(cb_, cby) >= -1e-6,
            f"the bosses sit inside the faceplate hole with the carrier floor")
        pins = [P[n] for n in P if n.startswith("cradle locating dowel")]
        row("cradle locating dowels in the PCB", len(pins), "2", len(pins) == 2 and all(p_.distance_to(plate) <= 0.06 for p_ in pins),
            ", ".join(f"({x:.1f}, {y:.1f})" for x, y in D["cr_pins"]))
    if stands:
        row("standoff count", len(stands), "4", len(stands) == 4, "one in each quadrant, all GND")
        sd = min(s.distance_to(db) for s in stands)
        row("standoffs meet the daughterboard", sd, "0.01-0.05", 0.01 <= sd <= 0.05,
            "round body 0.02 short of the daughterboard. An M2 socket screw passes through the plate")
    if bots: row("bottom screw head under the PCB", min(s.distance_to(pcb) for s in bots), "0.005-0.05",
        0.005 <= min(s.distance_to(pcb) for s in bots) <= 0.05,
        f"{D['shcs']['part']} M2×{D['shcs']['bot']:.0f}, head Ø{D['shcs']['head_d']:.1f} × {D['shcs']['head_h']:.1f}. "
        f"{D['engage_bot']:.2f} mm of thread in the pillar")
    if tops: row("top screw head on the plate", min(s.distance_to(plate) for s in tops), "0.005-0.05",
        0.005 <= min(s.distance_to(plate) for s in tops) <= 0.05,
        f"M2×{D['shcs']['top']:.0f} through the plate and the board, {D['engage_top']:.2f} mm in the pillar")
    if stands: row("screw thread engagement", min(D["engage_bot"], D["engage_top"]), ">= 2.0",
        D["engage_bot"] >= 2.0 and D["engage_top"] >= 2.0, "both ends, female-female pillar")
    if bots: row("bottom screw clear of the hold-downs", min(s.distance_to(h) for s in bots for h in sprs), ">= 1.0",
        min(s.distance_to(h) for s in bots for h in sprs) >= 1.0)
    ra = P["rear spring anchor (printed)"]
    pins = [P[n] for n in P if n.startswith("cross pin")]
    row("rear anchor glued to the PCB back", ra.distance_to(pcb), "0.01-0.05",
        0.01 <= ra.distance_to(pcb) <= 0.05,
        f"bond outline {D['ra_bond']:.0f} mm², wall {D['ra_wall']:.1f}, volume {ra.volume/1000:.2f} cm³")
    if bots: row("rear anchor clear of the bottom screws", min(ra.distance_to(s) for s in bots), ">= 1.0",
        min(ra.distance_to(s) for s in bots) >= 1.0,
        "the anchor stops inboard of the screws. The heads stay reachable")
    row("lower hooks just behind the PCB", -D["pcb_t"] - D["z_pin"], "1.5-4.0",
        1.5 <= -D["pcb_t"] - D["z_pin"] <= 4.0,
        f"pin axis z {D['z_pin']:.2f}, PCB back z {-D['pcb_t']:.2f}")
    row("hold-down force per spring (sized by tipping)", D["spr_f"], f">= {D['spr_f_need']:.2f}", D["spr_f"] >= D["spr_f_need"] - 1e-9,
        f"Rate {D['spr_rate']:.3f} N/mm over {D['spr_ext']:.1f} mm stretch, installed {D['spr_len']:.1f} mm. "
        f"Cups at the full slide: {D['cup_angle']:.1f}°, push back {D['f_cup']:.2f} N")
    for nm, v, note in (("push on the glass top, up the panel", D["sf_up"], f"top balls at +{D['by_top']:.2f}"),
                        ("push on the glass top, toward the knob", D["sf_down"], f"knob-side balls at -{D['by_bot']:.2f}"),
                        ("push on the glass top, left/right", D["sf_x"], f"balls ±{D['bx']:.2f}"),
                        ("push on the block side, up the panel", D["sf_up_mid"], "")):
        row(f"tipping safety at the worst-case click ({nm})", v, f">= {D['tip_margin']:g}", v >= D["tip_margin"] - 1e-6,
            f"restoring / overturning moment; push to click {D['f_click']:.2f} N worst ({D['f_click_nom']:.2f} nominal) = switch + cups. {note}")
    row("two pins, each through a pair", len(pins), "2", len(pins) == 2 and len(sprs) == 4,
        f"Ø{D['pin_d']:.2f} x {D['pin_x1'] - D['pin_x0']:.1f} mm, along X, at y ±{D['spr_y']:.2f}")
    row("pin slides in the bore", min(p.distance_to(ra) for p in pins), ">= 0.10",
        min(p.distance_to(ra) for p in pins) >= 0.10,
        f"bore Ø{D['pin_bore']:.2f} over pin Ø{D['pin_d']:.2f}")
    row("pin clears the hook eye", min(p.distance_to(s) for p in pins for s in sprs), ">= 0.10",
        min(p.distance_to(s) for p in pins for s in sprs) >= 0.10,
        f"eye wire Ø{D['eye_wire']:.2f}, radial gap {D['eye_clear']:.2f}. Pull the hook on, then push the pin")
    mouth_open = not ra.is_inside((D["ra_x1"] - 0.15, D["spr_y"], D["z_pin"]))
    blind = ra.is_inside((D["ra_x0"] + 0.4, D["spr_y"], D["z_pin"]))
    row("pin mouth open, far end stopped", 1.0 if mouth_open and blind else 0.0, "open",
        mouth_open and blind, "push in from +x. The -x end is a 1 mm wall")
    if stands: row("screw clears the PCB hole", (D["drill_m2"] - D["screw_d_model"]) / 2, ">= 0.15",
        (D["drill_m2"] - D["screw_d_model"]) / 2 >= 0.15,
        f"Ø{D['screw_d_model']:.2f} screw in the Ø{D['drill_m2']:.1f} hole")
    if stands:
        row("standoff vs plate (screw through both)", min(s.distance_to(plate) for s in stands), ">= 0.5",
            min(s.distance_to(plate) for s in stands) >= 0.5, "the screw, not the standoff, passes through the plate")
        row("standoff vs switch body", min(s.distance_to(body) for s in stands), ">= 0.8",
            min(s.distance_to(body) for s in stands) >= 0.8)
        row("standoff vs header", min(min(s.distance_to(h) for h in hdrs) for s in stands), ">= 0.6",
            min(min(s.distance_to(h) for h in hdrs) for s in stands) >= 0.6)
        row("stock standoff is the riser", D["riser_h"], f"{D['riser_catalog']:.2f}",
            abs(D["riser_h"] - D["riser_catalog"]) <= 0.05,
            f"{D['standoff']['part']} ({D['standoff']['lcsc']}), Ø{D['standoff_d']:.1f} female-female brass")
    elif case_on:
        row("top board underside at its set height", D["riser_h"], f"{D['riser_catalog']:.2f}", abs(D["riser_h"] - D["riser_catalog"]) <= 0.05,
            "v0.7: tb_z0, the v0.6 daughterboard height (the switch, carrier and bezel stack is unchanged); electronics "
            "vb.top_board_z must match (assembly cross-check)")
    else:
        row("cradle height is the riser", D["riser_h"], f"{D['riser_catalog']:.2f}", abs(D["riser_h"] - D["riser_catalog"]) <= 0.05,
            "printed, so any height works; 30 keeps the v0.5 lift")
    pg = D["z_glass"] - D["z_fp1"]   # v0.18 knob_proud is measured to the knob screen glass
    row("knob_proud (to the glass) in the accepted window", pg, "16-20",
        16.0 - 1e-6 <= pg <= 20.0 + 1e-6,
        f"faceplate front z {D['z_fp1']:.2f} = knob top {D['z_knob_top']:.2f} − {D['knob_proud']:.2f}. "
        f"Parameter was {D['knob_proud_in']:.2f}"
        f"{'' if not D['knob_proud_live'] else ' from knob-param'}")
    if case_on:
        gone = [n for n in P if n.startswith(("header ", "socket ", "cradle locating", "joystick cradle (printed", "brass standoff"))]
        row("no H11 sockets, long-pin headers, dowels or glued cradle (layout v4)", len(gone), "0", not gone,
            "[Ed 3 Nov] the vertical boards carry the signals (spring contacts under the top board); the H7B0 sits where the sockets were")
    else:
      row("header mates the H11 socket", D["mate_in"], f"{T['mate_min']}-{T['mate_max']}",
        T["mate_min"] <= D["mate_in"] <= T["mate_max"],
        f"{D['hdr']['part']} pin {D['hdr']['mate']:.2f} into {D['sock']['part']} ({D['sock']['lcsc']}); "
        f"air {D['mate_air']:.2f}, derived riser {D['riser_h']:.2f} mm, pin tip z {D['z_hdr_tip']:.2f}. "
        + ("" if cradle_on else f"Catalog {D['standoff']['part']} body is {D['riser_catalog']:.0f} mm"))
      row("socket count matches the headers", len(socks), "2", len([n for n in P if n.startswith("socket ") and "H11" in n]) == 2 and len(hdrs) == 2,
        f"two {D['hdr'].get('rows', 1)}x{D['hdr']['n']}, one each side of the switch: "
        f"{2 * D['hdr'].get('rows', 1) * D['hdr']['n']} pins: 10 signals, 3.3 V and grounds" + ("" if cradle_on else "; the standoffs are GND too"))
    # 8 centring and symmetry
    off = math.hypot(*D["sw_xy"])
    row("switch on the carrier axis", off, "0", off <= 1e-6, "dead centre")
    xmir = lambda pts: {(round(-x, 4), round(y, 4)) for x, y in pts} == {(round(x, 4), round(y, 4)) for x, y in pts}
    sym = (_mirror_ok(D["standoff_xy"]) and _mirror_ok(D["hdr_xy"])
           and (xmir(D["balls"]) if (cradle_on or case_on) else _mirror_ok(D["balls"]))   # v0.5: the top ball row is set by the rail strip
           and _mirror_ok(D["springs"]) and _mirror_ok(D["cs_xy"]))
    row("standoffs, headers, balls and both spring sets symmetric", 1.0 if sym else 0.0, "mirror", sym,
        f"standoffs (±{D['sx']:.2f}, ±{D['sy']:.2f}), compression springs (±{D['cs_x']:.2f}, ±{D['cs_y']:.2f})")
    # 9 balls
    bt = min(b.distance_to(car) for b in balls)
    bp = min(b.distance_to(plate) for b in balls)
    row("ball seated in the upper cup", bt, "<= 0.02", bt <= 0.02, f"four Ø{D['ball_d']:g}, cup Ø{2*D['cup_r']:.2f}")
    row("ball seated in the lower cup", bp, "<= 0.02", bp <= 0.02, "matching cup in the seat post")
    row("cup radius / ball radius", D["cup_ratio"], "1.05-3.0", 1.05 <= D["cup_ratio"] <= 3.0,
        f"Rc {D['cup_r']:.3f} mm, rim radius {D['cup_rim_r']:.3f} mm" + (" [Ed 2 Nov: gentle cups, option B]" if D.get("cup_ratio_set") else ""))
    row("cup depth / ball diameter", D["cup_depth_frac"], "0.15-0.40", 0.15 <= D["cup_depth_frac"] <= 0.40,
        f"depth {D['cup_depth']:.3f} mm on Ø{D['ball_d']:g}")
    row("full slide stays inside the cups", D["cup_travel_margin"], f">= {D['cup_margin']:.2f}",
        D["cup_travel_margin"] + 1e-6 >= D["cup_margin"],
        f"slide {D['slide']:.2f} mm, cups still hold to {D['cup_s_max']:.2f} mm. "
        f"Ball centres move to (±{D['bx']:.2f}, ±{D['by']:.2f})")
    # 10 knob clearance — both faces are MJF, so the gap is 2 x 0.25
    for name, od in (("live knob-param", D["knob_od_live"]), ("design Ø41.7", D["knob_od_design"])):
        kg = min(_gap_at(D, od, x, y) for x, y in ((0.0, -D["half_h"]), (D["half_w"], -D["half_h"])))
        row(f"bezel (full slide toward the knob) vs {name}", kg, f">= {T['knob_min']}", kg >= T["knob_min"] - 1e-6,
            f"Ø{od:.2f}. Bezel lip {D['bz_lip']:.2f} mm, outer ±{D['half_h']:.2f}")
    # 11 screws and sockets on the main PCB
    def on_board(x, y, pad=0.0):
        fy = y   # v0.5: local; y_pcb is the main-PCB top edge (the case nest) above the joystick axis
        return (abs(x) + pad <= D["pcb_w"] / 2 - D["pcb_edge"]) and (fy + pad <= D["y_pcb"] - D["pcb_edge"])
    holes = D["standoff_xy"] + D["hdr_xy"] + D["springs"]
    holes_ok = all(on_board(x, y, D["pad_m2"] / 2 if (x, y) in D["standoff_xy"] or (x, y) in D["hdr_xy"] else D["spr_bore"] / 2)
                   for x, y in holes)
    nuts_on = all(on_board(x, y, D["shcs"]["head_d"] / 2) for x, y in D["standoff_xy"]) and all(
        on_board(x, y, D["cradle"]["pin"]["d"] / 2) for x, y in D.get("cr_pins", []))
    row("standoff, socket and spring holes on the main PCB", 1.0 if holes_ok else 0.0, "on", holes_ok,
        f"hold-down hooks at x ±{D['spr_x']:.2f} (the corner formula wanted ±{D['spr_x_raw']:.2f}, past the PCB)")
    row("socket-screw heads / cradle dowels on the main PCB", 1.0 if nuts_on else 0.0, "on", nuts_on,
        (f"two Ø{D['cradle']['pin']['d']:g} dowels" if cradle_on else
         f"head Ø{D['shcs']['head_d']:.1f} needs the screws at y ±{D['sy']:.2f} (the pad alone would have allowed ±{D['sy_pad']:.2f})"))
    if D.get("skirt", True):
        row("carrier skirt above the rail", D["z_skirt0"] - D["rail_z"], ">= 0", D["z_skirt0"] >= D["rail_z"],
            f"skirt bottom z {D['z_skirt0']:.2f}, rail z {D['rail_z']:g} [A]")
    # 12 walls, floor, volumes
    row("bezel lip", D["bz_lip"], "1.0-1.5", 1.0 - 1e-9 <= D["bz_lip"] <= 1.5 + 1e-9,
        f"matches the other bezel. Glue gap around the glass is {D['glue']:.2f}")
    row("carrier floor", D["car_floor"], f">= {D['print_min']}", D["car_floor"] >= D["print_min"] - 1e-9,
        f"floor is the print minimum. Derived riser {D['riser_h']:.2f} mm. Screen top {D['scr_top']:.2f}")
    if not cradle_on and not case_on:
        row("plate frame outside the switch opening", D["db_half_h"] - D["cut_r"], f">= {D['print_min']}",
            D["db_half_h"] - D["cut_r"] + 1e-9 >= D["print_min"], "thinnest on the axis, where the land is widest")
    if D.get("skirt", True):
        row("skirt wall", D["car_skirt"], f">= {D['print_min']}", D["car_skirt"] + 1e-9 >= D["print_min"],
            "anti-rotation skirt")
    z_well = (max(D["z_roof"], D["z_scr0"]) + D["z_bz1"]) / 2   # v0.5: the glass pocket band, above the roof plate
    x_wall = (D["half_h"] + D["pocket"][1] / 2) / 2
    y_wall = (D["half_h"] + D["pocket"][1] / 2) / 2
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
    row("screen in the bezel", scr.distance_to(bez), "0.01-0.30",
        0.01 <= scr.distance_to(bez) <= 0.30,
        f"side glue gap {D['glue']:.2f}. Glass sits 0.02 above the spring pads. Top z {D['scr_top']:.2f}")
    row("no printed base, spider or round stop", 0.0, "0 parts",
        not any(n.startswith("joystick base") or n.startswith("screen spider") for n in P),
        "removed from v0.3: spider, plunger, round stop. Hold-down springs stay")
    # 12 v0.5: finger room, rail strip, guides, flex socket
    row("finger gap: knob glass to the bezel (plan, rest)", D["finger_gap"], f">= {D['finger_min']:.1f}",
        D["finger_gap"] >= D["finger_min"] - 1e-6,
        f"[Ed 2 Nov] place_y {D['place_y']:.2f} ({D['place_rule']} rule; v0.4 knob rule gave {D['place_y_knob']:.2f})")
    if D["y_rail"] < 90:
        from build123d import Box, Align
        y0 = D["y_rail"] - D["rail_margin"]
        zone = Pos(0, y0 + 20.0, D["z_fp0"] - 30.0) * Box(80, 40, 30 - 0.001, align=(Align.CENTER, Align.CENTER, Align.MIN))
        worst, who = 0.0, "none"
        for n, s_ in P.items():
            if n.startswith(("main PCB (proxy", "faceplate (case proxy")):
                continue
            b_ = s_.bounding_box()
            if b_.max.Y <= y0 or b_.min.Z >= D["z_fp0"]:
                continue
            try:
                v = (s_ & zone).volume
            except Exception:
                v = 1e9   # review fix: a failed intersection fails the check instead of passing silently
            if v > worst:
                worst, who = v, n
        row("nothing behind the panel in the rail strip (mm³)", worst, "0", worst <= 1e-3,
            f"rail strip from local y {D['y_rail']:.2f} (less {D['rail_margin']:.1f} air), behind z {D['z_fp0']:.2f}; worst: {who}")
    gs = [P[n] for n in P if n.startswith("guide screw")]
    sl = [P[n] for n in P if n.startswith("guide sleeve")]
    row("guide screw thread in the roof insert", D["g_engage"], ">= 2.0", D["g_engage"] >= 2.0 - 1e-6,
        f"{D['guide']['part']}; M2x{D['g_len']:.0f}, tip z {D['g_tip']:.2f} under the glass seat {D['z_scr0']:.2f}")
    row("guide length in the carrier / sleeve OD", D["g_guide_len"] / D["guide"]["sleeve_od"], ">= 0.9",
        D["g_guide_len"] / D["guide"]["sleeve_od"] >= 0.9 - 1e-6,
        f"reamed Ø{D['g_bore']:.2f} bore {D['g_guide_len']:.2f} long; sleeve {D['g_sleeve_len']:.2f} long, clamped head to insert")
    hc = D["g_head0"] - D["press_travel"] - D["g_under"]
    row("guide head clears what is under it at full press", hc, f">= {D['tol_mjf']:.2f}", hc >= D["tol_mjf"] - 1e-6,
        f"guides at ({D['g_xy'][0][0]:.1f}, {D['g_xy'][0][1]:.1f}) and mirror; head z {D['g_head0']:.2f}-{D['g_z0']:.2f} at rest "
        f"(the up-stop); under it z {D['g_under']:.2f} (board top + solder, or the switch)")
    gp = D["g_gap_press"] - D["press_travel"]
    row("roof bosses clear the carrier floor at full press", gp, f">= {D['tol_sla']:.2f}", gp >= D["tol_sla"] - 1e-6,
        f"roof boss bottom z {D['g_ins_bot']:.2f}, floor top z {D['z_floor1']:.2f}, press {D['press_travel']:.2f}")
    if gs and sl:
        gb = min(s_.distance_to(car) for s_ in sl)
        row("guide sleeve slides in its bore", gb, "0.01-0.10", 0.01 <= gb <= 0.10, "ream to size after printing")
        gsw = min(g_.distance_to(body) for g_ in gs)
        row("guide head vs switch body (rest)", gsw, f">= {D['tol_mjf']:.2f}", gsw >= D["tol_mjf"] - 1e-6)
    if D["fpc_to_db"]:
        sock = P["screen FPC socket AXE530127 (daughterboard)"]
        row("screen socket clear of the seat plate / cradle", sock.distance_to(plate), ">= 0.3", sock.distance_to(plate) >= 0.3,
            f"socket at x {D['db_sock_x']:.2f} on a tab to x {D['tab_x1']:.2f}, ±{D['tab_hy']:.2f}")
        tops = [P[n] for n in P if n.startswith("M2 socket screw top")]
        if tops:
            row("screen socket clear of the standoff screw heads", min(sock.distance_to(t_) for t_ in tops), ">= 0.3",
                min(sock.distance_to(t_) for t_ in tops) >= 0.3)
        hs = [P[n] for n in P if n.startswith("hold-down spring")]
        row("screen socket clear of the hold-down springs", min(sock.distance_to(h_) for h_ in hs), ">= 0.3",
            min(sock.distance_to(h_) for h_ in hs) >= 0.3)
        sc_ = min((Pos(D["slide"] * math.cos(math.radians(a)), D["slide"] * math.sin(math.radians(a)), 0) * car).distance_to(sock)
                  for a in range(0, 360, 45))
        row("screen socket clear of the carrier at full slide", sc_, f">= {D['tol_mjf']:.2f}", sc_ >= D["tol_mjf"] - 1e-6,
            "skirt notched over the tab")
    if "win_x" in D:   # v0.6: the DO0164FMST02 in the roof, and the custom jumper [Ed 16:14-16:31]
        from build123d import Box, Align
        pm = D["print_min"]
        back = scr & (Pos(0, 0, D["z_scr0"] - 5.0) * Box(80, 60, 5.0 - 0.005, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        bk = back.distance_to(bez)
        row("screen back clear of its roof pockets (mm)", bk, ">= 0.10", bk >= 0.10 - 1e-6,
            f"[S] FMST02 back from Waveshare's STEP: sheet 0.20, flex 0.45, fold 0.70, parts to 1.20, connector plate 1.50, "
            f"B2B header 2.15; pockets {D['back_side']:g} round, {D['back_clear']:g} under")
        pads = [P[n] for n in P if n.startswith("screen foam pad")]
        if pads:
            pa = sum(f.area for f in pads[0].faces() if f.normal_at().Z > 0.99)
            ok = pads[0].distance_to(scr) <= 0.02 and pads[0].distance_to(bez) <= 0.02
            fz = sorted({round(D["z_scr0"] - b_[5], 2) for b_ in D["scr_back"] if b_[0] not in D["scr_window"]})
            row("foam pads under the panel's back (press goes into the roof), mm²", pa, ">= 300", ok and pa >= 300,
                f"{D['foam_t']:g} thick [A] at {len(fz)} levels, touching the panel and the pocket floors; the connector is windowed")
        land = bez & (Pos(0, 0, D["z_scr0"] - 0.01) * Box(D["scr"]["w"], D["scr"]["h"], 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        la = sum(f.area for f in land.faces() if f.normal_at().Z > 0.99)
        row("glass glue land on the roof top (mm²)", la, ">= 200", la >= 200,
            "the glass margin clear of the back: mostly the +x end, plus strips along both long edges")
        rk = D["roof_t"] - D["back_deep"]
        row("roof under the deepest back pocket", rk, f">= {pm:g}", rk >= pm - 1e-6,
            f"roof {D['roof_t']:.2f} thick (v0.5 {D['roof_t_in']:g}); deepest pocket {D['back_deep']:.2f}; underside z {D['z_roof']:.2f}")
        st = D["z_plate_floor"] - D["z_step"]
        row("roof step under the connector plate", st, f">= {pm:g}", st >= pm - 1e-6,
            f"x {D['step_x'][0]:.2f}-{D['step_x'][1]:.2f}, ±{D['step_hy']:.2f}; carries the +x guide boss; no jumper there")
        js = P["screen jumper B2B socket (top, on the panel header) [A]"]
        jf = P["screen jumper FPC [A]"]
        near = [(js.distance_to(P[n]), n) for n in P if n.startswith(("compression spring", "guide insert", "guide screw", "press peg"))]
        near += [(min(js.distance_to(bez), jf.distance_to(bez)), "screen carrier (window, step, roof)")]
        dmin, who = min(near)
        row("jumper top end clear of the springs, guides, peg and roof (mm)", dmin, f">= {D['tol_mjf']:.2f}", dmin >= D["tol_mjf"] - 1e-6,
            f"socket {D['db_fpc_sock'][0]:g} x {D['db_fpc_sock'][1]:g} [A] at x {D['jmp_x']:g} (all move together with the block); nearest: {who}")
        seat = (D["cs_y"] - D["cs"]["od"] / 2) - D["win_hy"]
        row("press-spring seats on solid roof beside the socket window", seat, ">= 0", seat >= -1e-6,
            f"coil inner edge y {D['cs_y'] - D['cs']['od'] / 2:.2f}, window ±{D['win_hy']:.2f}. [C] decided on the real socket length: "
            "if it is longer than 8.4, all four springs go to y ±6.0 [Ed 16:31]")
        sm = min((D["slot_x"][1] - D["slot_x"][0] - D["jmp_stiff"][0]) / 2, D["slot_hy"] - D["db_fpc_sock"][0] / 2)
        row("carrier slot passes the jumper's bottom plug (assembly)", sm, ">= 0.2", sm >= 0.2 - 1e-6,
            f"slot x {D['slot_x'][0]:.2f}-{D['slot_x'][1]:.2f}, ±{D['slot_hy']:.2f}; plug end {D['jmp_stiff'][0]:g} x {D['db_fpc_sock'][0]:g} [A]")
        mg, fat = D["jmp_margin"], D["jmp_fatigue"]
        L = D["jmp_L"]
        for k, legs, what in (("x", "V1 + S1", f"slide ±{D['slide']:.2f}"), ("y", "S2 + S3", f"slide ±{D['slide']:.2f}"),
                              ("z", "R", f"press {D['press_travel']:.2f}")):
            e = D["jmp_eps"][k]
            row(f"jumper copper strain, {'press' if k == 'z' else k + ' slide'} (%)", 100 * e, f"<= {100 * fat / mg:.2f}", e <= fat / mg + 1e-9,
                f"{fat / e:.1f}x under {100 * fat:.1f}% [A]; legs {legs} " + ", ".join(f"{g} {L[g]:.2f}" for g in legs.split(" + "))
                + f"; {what}; copper {1000 * D['jmp_cu_c']:.0f} µm off the neutral axis [A]")
        from build123d import Pos as _Pos
        mv = [n for n in P if n.startswith(("joystick carrier", "brass insert", "grub screw", "guide screw", "guide sleeve",
                                            "compression spring", "screen carrier"))]
        fx_ = [n for n in P if n.startswith(("joystick daughterboard", "joystick cradle", "hold-down spring", "screen FPC socket",
                                             "SW1", "header", "cradle locating", "joystick top board", "joystick case cradle"))]
        low = jf & (_Pos(0, 0, D["z_c0"] - 0.01) * Box(80, 60, 30, align=(Align.CENTER, Align.CENTER, Align.MAX)))   # the loop under the carrier
        worst = min([(low.distance_to(P[n]), n) for n in fx_]
                    + [(low.distance_to(_Pos(dx, dy, 0) * P[n]), n + f" at ({dx:+.2f},{dy:+.2f})") for n in mv
                       for dx, dy in ((D["slide"], 0), (-D["slide"], 0), (0, D["slide"]), (0, -D["slide"]))])
        row("jumper loop clear at the full slide (carrier moved, loop at rest)", worst[0], f">= {D['tgt']['cable_min']:.2f}",
            worst[0] >= D["tgt"]["cable_min"] - 1e-6,
            f"loop z {D['z_leg'][0]:.2f}-{D['z_leg'][1]:.2f}, {D['fpc_w']:g} wide, about {D['jmp_len']:.0f} mm long; nearest: {worst[1]}. "
            "Daughterboard parts under it must stay under 0.6 mm [C]")
    # silence a lint-level unused local if the wall probe x is kept only as documentation
    _ = x_wall
    return rows

def _case_rows(D, P, row, car, bez, plate, db):
    """v0.7 [Ed 3 Nov 11:03] the case cradle: lip in the faceplate cutout, flange on a gasket, top board in its nest."""
    cc, gk, sla = D["cc"], D["gasket"], D["tol_sla"]
    fp = P["faceplate (case proxy, UTR-8100)"]
    gas = P[GK_NAME]
    d = plate.distance_to(fp)
    row("case cradle lip to the faceplate cutout (each side)", d, f">= {cc['lip_c'] - 0.01:.2f}", d >= cc["lip_c"] - 0.01,
        f"lip ±{D['lip_out_hw']:.2f} × ±{D['lip_out_hh']:.2f} in the ±{D['hole_hw']:.2f} × ±{D['hole_hh']:.2f} cutout; flange "
        f"{D['z_fp0'] - D['z_fl1']:.2f} under the faceplate. [A] 0.2 is one SLA tolerance: with the case and the cradle both at ±0.20 "
        "the lip can bind. Fit-check and sand the lip")
    row("case cradle lip in the cutout (engagement)", D["lip_engage"], ">= 1.0", D["lip_engage"] >= 1.0 - 1e-9,
        f"lip z {D['z_fp0']:.2f}→{D['z_lip1']:.2f} inside the {D['fp_t']:g} faceplate; it locates the cradle in x and y")
    row("case cradle walls ≥ SLA minimum (lip, flange, hangers, shoulders)", min(cc["lip_t"], cc["flange_t"], cc["wall"], cc["shoulder"]),
        ">= 0.80", min(cc["lip_t"], cc["flange_t"], cc["wall"], cc["shoulder"]) >= 0.8 - 1e-9,
        f"{cc['part']}: lip {cc['lip_t']:g}, flange {cc['flange_t']:g}, hangers {cc['wall']:g}, shoulders {cc['shoulder']:g} [S SLA 0.8]")
    row("grip block covers the cutout (and the lip in it) at full slide", D["block_cover_slide"], f">= {sla:.2f}",
        D["block_cover_slide"] >= sla - 1e-9,
        f"cover {D['block_cover_rest']:.2f} at rest (fp_overlap, unchanged: the cutout keeps its size), {D['block_cover_slide']:.2f} at the "
        f"{D['slide']:.2f} slide; the lip is {cc['lip_c']:.2f}..{cc['lip_c'] + cc['lip_t']:.2f} inside the cutout edge")
    row("grip block clear of the lip top at full press", D["block_lip_press"], f">= {sla:.2f}", D["block_lip_press"] >= sla - 1e-9,
        f"block underside z {D['z_bz0']:.2f} − press {D['press_travel']:.2f}; lip top z {D['z_lip1']:.2f}")
    lo, hi = gk["comp_lo"], gk["comp_hi"]
    row("gasket compression at nominal inside its working band", gk["comp_nom"], f"{lo:.2f}-{hi:.2f}", lo <= gk["comp_nom"] <= hi,
        f"{gk['part']}: {gk['t']:g} free, {D['gk_nom']:.2f} at nominal; the band is {D['gk_range'][0]:.2f}-{D['gk_range'][1]:.2f} "
        f"(±{(D['gk_range'][1] - D['gk_range'][0]) / 2:.2f} of cradle height). The spring contacts set the force, not the stack")
    dg = max(gas.distance_to(fp), gas.distance_to(plate))
    row("gasket between the flange and the faceplate back", dg, "<= 0.02", dg <= 0.02,
        f"flange top z {D['z_fl1']:.2f}, faceplate back z {D['z_fp0']:.2f}; −y and ±x sides only (the +y side is over the rail strip)")
    row("gasket land under the faceplate (narrowest)", D["gk_land_min"], f">= {gk['land_min']:.2f}", D["gk_land_min"] >= gk["land_min"] - 1e-9,
        f"±x sides {D['gk_land_x']:.2f} (flange edge x {D['fl_x1']:.2f}: case side-wall glow coat), knob side {D['gk_land_y']:.2f} "
        f"(flange edge to the knob collar + {cc['collar_air']:g}). Tight on the sides")
    bx = D["board_x1"] - D["vb_contact_x"] - D["tb_pad"] / 2 - D["tb_tol"]
    by = D["tb_y_over"]
    row("top board covers the spring-contact pads (copper to the edge)", min(bx, by + 0.6), f">= {D['cu_edge']:.2f}",
        min(bx, by + 0.6) >= D["cu_edge"] - 1e-9,
        f"board ±{D['board_x1']:.2f} × {D['board_y0']:.2f}..{D['board_y1']:.2f}; contact line x ±{D['vb_contact_x']:g} [A mirror of "
        f"electronics], pads Ø{D['tb_pad']:g} ± {D['tb_tol']:g}; the board runs {by:g} past each end of the vertical boards")
    row("top board edges clear of the nest walls", cc["nest_c"], f">= {sla:.2f}", cc["nest_c"] >= sla - 1e-9,
        f"nest ±{D['nest_hw']:.2f} × {D['nest_y0']:.2f}..{D['nest_y1']:.2f}")
    sg = D["z_seat0"] - D["z_db1"]
    row("lower ball seats clear of the top board", sg, ">= 1.0", sg >= 1.0 - 1e-9,
        f"seat bosses from z {D['z_seat0']:.2f}, board top z {D['z_db1']:.2f}: top-board parts under the seats stay under "
        f"{sg - 0.3:.1f} mm [C]; balls at (±{D['bx']:.2f}, +{D['by_top']:.2f} / −{D['by_bot']:.2f}) (v0.6 ±17.80, +8.45 / −10.30)")
    row("top board flex at a worst-case click (on the contact lines)", D["tb_flex"], "<= 0.10", D["tb_flex"] <= 0.10,
        f"{D['push_hi']:.2f} N at the centre, {D['db_t']:g} FR4 spanning {2 * D['vb_contact_x']:g} [A E 18 GPa]; adds to the "
        f"{D['press_travel']:.2f} press. A 1.6 board would flex about {D['tb_flex'] / (1.6 / D['db_t']) ** 3:.3f}")
    cb_ = min(D["car_hw"] - (abs(x) + D["boss_r"]) for x, _ in D["balls"])
    cby = min(D["car_hh"] - (abs(y) + D["boss_r"]) for _, y in D["balls"])
    row("carrier cup bosses inside the carrier outline", min(cb_, cby), ">= 0", min(cb_, cby) >= -1e-6,
        f"v0.7: the balls follow the narrower carrier's corners in ([Ed] 'as far out as the carrier allows'): "
        f"(±{D['bx']:.2f}, +{D['by_top']:.2f} / −{D['by_bot']:.2f}), cup boss r {D['boss_r']:.2f}")
    fits = D["car_hw"] + D["slide"] + sla <= D["lip_in_hw"] + 1e-9 and D["car_hh"] + D["slide"] + sla <= D["lip_in_hh"] + 1e-9
    row("carrier drops through the lip ring", 1.0 if fits else 0.0, "fits", fits,
        f"carrier ±{D['car_hw']:.2f} × ±{D['car_hh']:.2f} + slide {D['slide']:.2f} + {sla:.2f} inside the lip ±{D['lip_in_hw']:.2f} × "
        f"±{D['lip_in_hh']:.2f}: the joystick goes in from the front after the cradle is in from the back")


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
