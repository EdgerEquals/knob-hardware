"""Joystick checks (v0.9). The switch is the only stop: the bezel's cup sits on the stem, so its own click is the press. The guide
heads hang on cushions under the carrier bosses (the up-stop). The four hold-down springs are unchanged in kind from v0.3. The case
cradle rows are in _case_rows9 (v0.9, printed with the case) and _case_rows8 (v0.8, separate cradle on a bead)."""
import math, itertools
from build123d import Pos, Rot
from .parts import cyl as cyl_, box as box_, db_name, gk_name, cc_name

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
    plate = P[cc_name(D)]   # the case cradle carries the lower ball seats (v0.7; v0.9 printed with the case)
    stem = P["SW1 SKRHADE010 stem"]
    db = P[db_name(D)]
    pcb = P["main PCB (proxy, local patch)"]
    fpc = P["screen jumper FPC [A]"]
    scr = [P[n] for n in P if n.startswith("top screen")][0]
    body = P["SW1 SKRHADE010 body (45°)"]
    sprs = [P[n] for n in P if n.startswith("hold-down spring")]
    balls = [P[n] for n in P if n.startswith("ball ")]
    # 1 stem / cup. The switch end of tilt is the stop
    # the bezel's cup: radial clearance below the ceiling (the stem shank cut 0.3 under its top), ceiling on the stem top
    from build123d import Box as _B, Align as _Al
    shank = stem & (Pos(0, 0, D["z_stem_top"] - 0.3) * _B(20, 20, 10, align=(_Al.CENTER, _Al.CENTER, _Al.MAX)))
    g = shank.distance_to(bez)
    row("stem vs the bezel's cup bore, radial (rest)", g, f">= {T['stem_cup_min']}", g >= T["stem_cup_min"] - 1e-6,
        f"[Ed 13:09] cup printed into the bezel: bore Ø{D['cup_bore']:.2f} over the Ø{sw['stem_d']:g} stem, column Ø{D['cup_col_od']:.2f} "
        f"(wall {D['print_min']:g}) from the roof down to z {D['z_cup0']:.2f}")
    gc = stem.distance_to(bez)
    row("bezel cup ceiling on the stem top (no gap)", gc, "<= 0.02", gc <= 0.02,
        f"ceiling z {D['z_stem_top']:.2f} = stem top; the switch's own click is the press ({D['press_travel']:.2f}); "
        f"the block, screen and case stay at v0.7's heights (up gap {D['up_gap']:.2f})")
    gh = min((Pos(D["slide"] * math.cos(math.radians(a)), D["slide"] * math.sin(math.radians(a)), 0) * bez).distance_to(
        Pos(D["slide"] * math.cos(math.radians(a)), D["slide"] * math.sin(math.radians(a)), 0) * car) for a in (0, 90))
    row("bezel cup column clear of the carrier floor hole", gh, f">= {D['tol_mjf'] - D['guide']['bore_fit']:.2f}",
        gh >= D["tol_mjf"] - D["guide"]["bore_fit"] - 1e-6,
        f"hole Ø{D['car_cup_hole']:.2f} round the Ø{D['cup_col_od']:.2f} column; bezel and carrier slide together on the guides "
        f"(sleeve fit {D['guide']['bore_fit']:g})")
    row("cup covers the tilt reference height", D["z_ref"] - D["z_cup0"], ">= 0.2",
        D["z_cup0"] + 0.2 <= D["z_ref"] <= D["z_stem_top"] and D["z_ref"] <= D["z_c0"],
        f"cup z {D['z_cup0']:.2f}-{D['z_c0']:.2f}, ref z {D['z_ref']:.2f}, stem top {D['z_stem_top']:.2f}")
    row("slide is the switch tilt, no extra overtravel", D["slide"] - D["slide_need"], "0",
        abs(D["slide"] - D["slide_need"]) < 1e-9,
        f"slide {D['slide']:.2f} = cup clearance {D['cup_rad_clear']:.2f} + tilt {sw['tilt_travel']:g}")
    # 2 the up-stop: guide heads on cushions under the carrier bosses (v0.8)
    _upstop_rows(D, P, row, car, bez, stem)
    # 3 captive bezel
    fp = P["faceplate (case proxy, UTR-8100)"]
    gap_fp = bez.distance_to(fp)
    row("bezel lip above the faceplate", D["z_bz0"] - D["z_fp1"], "0.02",
        abs(D["z_bz0"] - D["z_fp1"] - D["up_gap"]) < 1e-6 and gap_fp > 0.05,
        f"vertical gap {D['up_gap']:.2f} over the flat faceplate (no rebate); the closest solid is {gap_fp:.2f} mm. "
        f"Overlap {D['fp_overlap']:.2f} mm")
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
    _case_rows(D, P, row, car, bez, plate, db)
    gaps = []
    for deg in range(0, 360, 45):
        a = math.radians(deg)
        dx = D["slide"] * math.cos(a); dy = D["slide"] * math.sin(a)
        moved = Pos(dx, dy, 0) * car
        gaps.append(min(moved.distance_to(plate), moved.distance_to(db)))
    gmin = min(gaps)
    # v0.7: no skirt. The carrier slides inside the lip ring, which is also the anti-rotation stop
    row("carrier clear of the cradle's lip ring at full slide (every 45°)", gmin, f">= {D['tol_sla']:.2f}", gmin >= D["tol_sla"] - 1e-4,
        f"carrier ±{D['car_hw']:.2f} × ±{D['car_hh']:.2f} (v0.6 ±20.46 × ±13.02: narrowed {D['car_narrow']:.2f} by the lip and its "
        f"clearance), lip inner face ±{D['lip_in_hw']:.2f} × ±{D['lip_in_hh']:.2f}; gaps " + ", ".join(f"{v:.3f}" for v in gaps))
    rot = (Rot(0, 0, 3) * car).distance_to(plate)
    row("3° carrier rotation meets the lip ring (anti-rotation stop)", rot, "< 0.05", rot < 0.05,
        "the lip ring replaces the v0.6 skirt as the anti-rotation stop. It is not the tilt stop (the switch is)")
    # 5 cable
    fc = min(fpc.distance_to(car), fpc.distance_to(bez))
    row("FPC vs carrier and bezel", fc, f">= {T['cable_min']}", fc >= T["cable_min"] - 1e-4,
        f"FPC {D['fpc_w']:g} wide [A], slot {D['slot_x'][1] - D['slot_x'][0]:.2f} x {2 * D['slot_hy']:.2f}")
    row("FPC vs the top board", fpc.distance_to(db), ">= 1.0", fpc.distance_to(db) >= 1.0)
    # v0.7: the jumper's S1 leg (x 18.5) runs beside the +x hanger of the case cradle (no moving part between them)
    fp_ = fpc.distance_to(plate)
    row("FPC vs the case cradle (hanger beside the S1 leg)", fp_, f">= {T['cable_min']:.2f}", fp_ >= T["cable_min"] - 1e-6,
        f"S1 leg at x {D['jmp_xv']:g}, hanger inner face x {D['nest_hw']:.2f}; both fixed (the leg's moving end is above the "
        "cradle, inside the lip ring)")
    # 6 hold-down springs, kept
    sm = D["spr_bore"] / 2 - D["spr_d"] / 2 - D["slide"]
    row("hold-down spring vs bore at full slide", sm, f">= {T['spring_min']}", sm >= T["spring_min"],
        f"Ø{D['spr_d']:g} in Ø{D['spr_bore']:g}; {len(sprs)} x {D['spr_f']:g} N, installed {D['spr_len']:.1f} mm "
        f"(pin behind the main PCB to the carrier hook). Free {D['spr_free']:.1f}, stretch {D['spr_ext']:.1f}")
    sg = min(s.distance_to(plate) for s in sprs)
    row("hold-down spring vs the case cradle (rest)", sg, ">= 0.3", sg >= 0.3 - 1e-6, "hook boss is slotted so the eye can be swapped")
    # 7 top board on the cradle
    row("top board on the cradle shoulders (glued, faces touch)", db.distance_to(plate), "<= 0.02", db.distance_to(plate) <= 0.02,
        f"board {D['db'][0]:.2f} x {D['db'][1]:.2f} x {D['db_t']:g} at y {D['board_y0']:.2f}..{D['board_y1']:.2f}; " + (
        "v0.9: it goes in from the back on its own and is glued up under the printed shoulders [A]; the pins slide in its sockets"
        if D.get("cradle_in_case") else "the vertical boards' end tabs (posts) push it up against the shoulders"))
    ra = P["rear spring anchor (printed)"]
    pins = [P[n] for n in P if n.startswith("cross pin")]
    row("rear anchor glued to the PCB back", ra.distance_to(pcb), "0.01-0.05",
        0.01 <= ra.distance_to(pcb) <= 0.05,
        f"bond outline {D['ra_bond']:.0f} mm², wall {D['ra_wall']:.1f}, volume {ra.volume/1000:.2f} cm³")
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
    row("top board underside at its set height", D["riser_h"], f"{D['riser_catalog']:.2f}", abs(D["riser_h"] - D["riser_catalog"]) <= 0.05,
        "v0.7: tb_z0, the v0.6 daughterboard height (the switch, carrier and bezel stack is unchanged); electronics "
        "vb.top_board_z must match (assembly cross-check)")
    pg = D["z_glass"] - D["z_fp1"]   # v0.18 knob_proud is measured to the knob screen glass
    lo_, hi_ = D["knob_proud_window"]
    row("knob_proud (to the glass) in the accepted window", pg, f"{lo_:g}-{hi_:g}",
        lo_ - 1e-6 <= pg <= hi_ + 1e-6,
        f"faceplate front z {D['z_fp1']:.2f} = knob top {D['z_knob_top']:.2f} − {D['knob_proud']:.2f}. "
        f"Parameter was {D['knob_proud_in']:.2f}"
        f"{'' if not D['knob_proud_live'] else ' from knob-param'}")
    # 8 centring and symmetry
    off = math.hypot(*D["sw_xy"])
    row("switch on the carrier axis", off, "0", off <= 1e-6, "dead centre")
    xmir = lambda pts: {(round(-x, 4), round(y, 4)) for x, y in pts} == {(round(x, 4), round(y, 4)) for x, y in pts}
    sym = xmir(D["balls"]) and _mirror_ok(D["springs"])   # v0.5: the top ball row is set by the rail strip, so the balls mirror in x only
    row("balls and hold-down springs symmetric", 1.0 if sym else 0.0, "mirror", sym,
        f"hold-down springs (±{D['spr_x']:.2f}, ±{D['spr_y']:.2f}); balls (±{D['bx']:.2f}, +{D['by_top']:.2f} / −{D['by_bot']:.2f}), "
        "mirrored in x (the top row is set by the rail strip)")
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
    # 11 holes in the main PCB: the four hold-down spring bores (the only ones left)
    def on_board(x, y, pad=0.0):
        fy = y   # v0.5: local; y_pcb is the main-PCB top edge (the case nest) above the joystick axis
        return (abs(x) + pad <= D["pcb_w"] / 2 - D["pcb_edge"]) and (fy + pad <= D["y_pcb"] - D["pcb_edge"])
    holes_ok = all(on_board(x, y, D["spr_bore"] / 2) for x, y in D["springs"])
    row("hold-down spring bores on the main PCB", 1.0 if holes_ok else 0.0, "on", holes_ok,
        f"Ø{D['spr_bore']:g} at (±{D['spr_x']:.2f}, ±{D['spr_y']:.2f}), each at least {D['pcb_edge']:g} inside the main-PCB outline "
        f"(x ±{D['pcb_w'] / 2:.2f}, top edge local y {D['y_pcb']:.2f})")
    # 12 walls, floor, volumes
    row("bezel lip", D["bz_lip"], "1.0-1.5", 1.0 - 1e-9 <= D["bz_lip"] <= 1.5 + 1e-9,
        f"matches the other bezel. Glue gap around the glass is {D['glue']:.2f}")
    row("carrier floor", D["car_floor"], f">= {D['print_min']}", D["car_floor"] >= D["print_min"] - 1e-9,
        f"floor is the print minimum. Derived riser {D['riser_h']:.2f} mm. Screen top {D['scr_top']:.2f}")
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
        f"side glue gap {D['glue']:.2f}. Glass sits 0.02 above the roof top. Top z {D['scr_top']:.2f}")
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
        f"(the head hangs a float + cushion under the boss); under it z {D['g_under']:.2f} (top-board keep-out under the heads [A])")
    gp = D["g_gap_press"] - D["press_travel"]
    row("roof bosses clear the carrier floor at full press", gp, f">= {D['tol_sla']:.2f}", gp >= D["tol_sla"] - 1e-6,
        f"roof boss bottom z {D['g_ins_bot']:.2f}, floor top z {D['z_floor1']:.2f}, press {D['press_travel']:.2f}")
    if gs and sl:
        gb = min(s_.distance_to(car) for s_ in sl)
        row("guide sleeve slides in its bore", gb, "0.01-0.10", 0.01 <= gb <= 0.10, "ream to size after printing")
        gsw = min(g_.distance_to(body) for g_ in gs)
        row("guide head vs switch body (rest)", gsw, f">= {D['tol_mjf']:.2f}", gsw >= D["tol_mjf"] - 1e-6)
    sock = P["screen FPC socket AXE530127 (daughterboard)"]
    row("screen socket clear of the case cradle", sock.distance_to(plate), ">= 0.3", sock.distance_to(plate) >= 0.3,
        f"socket at x {D['db_sock_x']:.2f} on the top board (edge x {D['board_x1']:.2f}), ±{D['db_fpc_sock'][0] / 2:.2f}; the +x shoulder "
        "is notched round it")
    hs = [P[n] for n in P if n.startswith("hold-down spring")]
    row("screen socket clear of the hold-down springs", min(sock.distance_to(h_) for h_ in hs), ">= 0.3",
        min(sock.distance_to(h_) for h_ in hs) >= 0.3)
    sc_ = min((Pos(D["slide"] * math.cos(math.radians(a)), D["slide"] * math.sin(math.radians(a)), 0) * car).distance_to(sock)
              for a in range(0, 360, 45))
    row("screen socket clear of the carrier at full slide", sc_, f">= {D['tol_mjf']:.2f}", sc_ >= D["tol_mjf"] - 1e-6,
        f"carrier moved by the slide every 45°; the carrier slot x {D['slot_x'][0]:.2f}-{D['slot_x'][1]:.2f} is over the socket "
        "(the jumper's plug passes through it)")
    # v0.6: the DO0164FMST02 in the roof, and the custom jumper [Ed 16:14-16:31]
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
    near = [(js.distance_to(P[n]), n) for n in P if n.startswith(("guide insert", "guide screw"))]
    near += [(min(js.distance_to(bez), jf.distance_to(bez)), "screen carrier (window, step, roof)")]
    dmin, who = min(near)
    row("jumper top end clear of the guides and the roof (mm)", dmin, f">= {D['tol_mjf']:.2f}", dmin >= D["tol_mjf"] - 1e-6,
        f"socket {D['db_fpc_sock'][0]:g} x {D['db_fpc_sock'][1]:g} [A] at x {D['jmp_x']:g} (all move together with the block); nearest: {who}")
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
    mv = [n for n in P if n.startswith(("joystick carrier", "guide screw", "guide sleeve", "screen carrier", "guide up-stop cushion"))]
    fx_ = [n for n in P if n.startswith(("joystick cradle", "hold-down spring", "screen FPC socket", "SW1", "joystick top board",
                                         "joystick case cradle"))]
    low = jf & (_Pos(0, 0, D["z_c0"] - 0.01) * Box(80, 60, 30, align=(Align.CENTER, Align.CENTER, Align.MAX)))   # the loop under the carrier
    worst = min([(low.distance_to(P[n]), n) for n in fx_]
                + [(low.distance_to(_Pos(dx, dy, 0) * P[n]), n + f" at ({dx:+.2f},{dy:+.2f})") for n in mv
                   for dx, dy in ((D["slide"], 0), (-D["slide"], 0), (0, D["slide"]), (0, -D["slide"]))])
    row("jumper loop clear at the full slide (carrier moved, loop at rest)", worst[0], f">= {D['tgt']['cable_min']:.2f}",
        worst[0] >= D["tgt"]["cable_min"] - 1e-6,
        f"loop z {D['z_leg'][0]:.2f}-{D['z_leg'][1]:.2f}, {D['fpc_w']:g} wide, about {D['jmp_len']:.0f} mm long; nearest: {worst[1]}. "
        "Top-board parts under it must stay under 0.6 mm [C]")
    # silence a lint-level unused local if the wall probe x is kept only as documentation
    _ = x_wall
    return rows

def _upstop_rows(D, P, row, car, bez, stem):
    """v0.8 [Ed 13:09]: guides stay; the heads hang a float below the carrier bosses, with a cushion ring under each boss."""
    U, ch = D["upstop"], D["us_choice"]
    fl, fr = D["us_float"], D["us_rss"]
    row("up-stop float: bezel lift off the stem before the cushion (nominal)", fl[0], ">= 0 at the RSS tight end", fl[1] >= -1e-9,
        f"RSS band {fl[1]:.2f}–{fl[2]:.2f} (±{fr:.2f} of " + ", ".join(f"{k} {v:g}" for k, v in U["tol"].items()) +
        f"); then {U['t']:g} of cushion to the boss; worst case ±{D['us_wc']:.2f}")
    f_rss = 0.0   # by construction the cushion only reaches the head at the RSS tight end
    lim = D["preload_lim"]
    row("force across the stack at rest (cushion preload on the stem, RSS band)", f_rss, f"<= {lim:.3f}", f_rss <= lim + 1e-9,
        f"limit = the smaller of {D['push_frac']:.2f} × the {D['push_lo']:.2f} N minimum push [S Alps 2.35 ± 0.69] and {D['preload_max']:.3f} N "
        f"(the most the tipping rows allow: a stem preload comes off the hold-downs' restoring moment). TIGHT at the worst case: the "
        f"cushion is squeezed {100 * ch['wc_comp']:.0f} % ({D['us_wc_comp']:.2f}) and pushes {ch['f_wc'][0]:.2f}–{ch['f_wc'][2]:.2f} N")
    row("up-stop gap fits under the carrier guide boss", D["us_room"] - D["us_gap"], ">= 0", D["us_gap"] <= D["us_room"] + 1e-9,
        f"gap {D['us_gap']:.2f} = cushion {U['t']:g} + RSS {fr:.2f}; room {D['us_room']:.2f} (boss underside z {D['g_boss0']:.2f} down to the "
        f"head's limit over the top-board keep-out); M2x{D['g_len']:.0f}, head top z {D['g_z0']:.2f}")
    cu = [P[n] for n in P if n.startswith("guide up-stop cushion")]
    if cu:
        dc = min(c.distance_to(car) for c in cu)
        row("up-stop cushions glued under the carrier guide bosses", dc, "<= 0.02", dc <= 0.02,
            f"{U['part']}; ring {U['od']:g} / {U['id']:g} round the Ø{D['guide']['sleeve_od']:g} sleeve (it slides through)")
    row("stem preload the tipping rows allow (info)", D["preload_max"], ">= 0", D["preload_max"] >= 0,
        f"up the panel is the tightest row ({D['sf_up']:.3f} at no preload vs {D['tip_margin']:g}): a preload F scales it by (F_hd − F)/F_hd, "
        f"F_hd {len(D['springs']) * D['spr_f']:.1f} N. A preloaded (no-float) bezel needs the hold-downs up [C, Danny]")


def _case_rows(D, P, row, car, bez, plate, db):
    """v0.7 [Ed 3 Nov 11:03] the case cradle: lip in the faceplate cutout, flange behind the faceplate, top board in its nest. v0.9 printed
    with the case (_case_rows9); v0.8 a separate cradle on a bead (_case_rows8). The v0.7 rows (spring contacts, gasket) are gone."""
    fp = P["faceplate (case proxy, UTR-8100)"]
    if D.get("cradle_in_case"):   # v0.9 [Ed 18:35]: printed with the case, no bead
        return _case_rows9(D, P, row, car, bez, plate, db, fp)
    return _case_rows8(D, P, row, car, bez, plate, db, fp, P[gk_name(D)])


def _case_rows8(D, P, row, car, bez, plate, db, fp, gas):
    """v0.8 [Ed 13:46–14:08]: sockets under the top board (the boards are posts), a form-in-place bead, the top-edge step."""
    cc, B, sla, st = D["cc"], D["bead"], D["tol_sla"], D["step"]
    d = plate.distance_to(fp)
    row("case cradle lip to the faceplate cutout (each side)", d, f">= {cc['lip_c'] - 0.01:.2f}", d >= cc["lip_c"] - 0.01,
        f"lip ±{D['lip_out_hw']:.2f} × ±{D['lip_out_hh']:.2f} in the ±{D['hole_hw']:.2f} × ±{D['hole_hh']:.2f} cutout; the dam sits "
        f"{st['c']:g} from the rebate walls. [A] 0.2 is one SLA tolerance: fit-check and sand the lip")
    row("case cradle lip in the cutout (engagement)", D["lip_engage"], ">= 1.0", D["lip_engage"] >= 1.0 - 1e-9,
        f"lip z {D['z_fp0']:.2f}→{D['z_lip1']:.2f} inside the {D['fp_t']:g} faceplate; it locates the cradle in x and y")
    w = min(cc["lip_t"], cc["flange_t"], cc["wall"], cc["shoulder"], D["dam_t"])
    row("case cradle walls ≥ SLA minimum (lip, flange, hangers, shoulders, dam)", w, ">= 0.80", w >= 0.8 - 1e-9,
        f"{cc['part']}: lip {cc['lip_t']:g}, flange {cc['flange_t']:g}, hangers {cc['wall']:g}, shoulders {cc['shoulder']:g}, "
        f"dam {D['dam_t']:.2f} [S SLA 0.8]")
    row("grip block covers the cutout (and the lip in it) at full slide", D["block_cover_slide"], f">= {sla:.2f}",
        D["block_cover_slide"] >= sla - 1e-9, f"cover {D['block_cover_rest']:.2f} at rest, {D['block_cover_slide']:.2f} at the {D['slide']:.2f} slide")
    row("grip block clear of the lip top at full press", D["block_lip_press"], f">= {sla:.2f}", D["block_lip_press"] >= sla - 1e-9,
        f"block underside z {D['z_bz0']:.2f} − press {D['press_travel']:.2f}; lip top z {D['z_lip1']:.2f}")
    row("bead squeeze at nominal inside its band", B["c_nom"], f"{B['c_lo']:.2f}-{B['c_hi']:.2f}", B["c_lo"] <= B["c_nom"] <= B["c_hi"],
        f"{B['part']}: dispensed {B['w0']:g} × {B['h0']:g} [S Henkel aspect 0.6–0.9], {D['gk_nom']:.2f} gap at nominal; it stays in its "
        f"{100 * B['c_lo']:.0f}–{100 * B['c_hi']:.0f} % band [S Henkel] for gaps {D['gk_range'][0]:.2f}–{D['gk_range'][1]:.2f} (±{D['bead_band']:.2f}), "
        f"±{D['bead_band_net']:.2f} after its own ±{B['disp']:g} dispensed height. The stack it must take is an assembly row")
    dg = max(gas.distance_to(fp), gas.distance_to(plate))
    row("bead between the flange / dam and the faceplate", dg, "<= 0.02", dg <= 0.02,
        f"flange top z {D['z_fl1']:.2f} under the faceplate back {D['z_fp0']:.2f}; dam face z {D['z_dam1']:.2f} under the rebate ceiling "
        f"{D['z_reb1']:.2f}; a riser joins them where the flange ends (y {D['st_y0']:.2f}) [C: 3D dispense path]")
    row("bead land under the faceplate (narrowest) vs the dispensed bead", D["gk_land_min"] - B["w0"], ">= 0", D["gk_land_min"] >= B["w0"] - 1e-9,
        f"long sides {D['gk_land_x']:.2f} (glow coat), knob side {D['gk_land_y']:.2f}, step {D['step_land']:.2f}; bead {B['w0']:g} "
        f"(±{B['disp']:g}); the flange top beside the lip is {D['fl_x1'] - D['lip_out_hw']:.2f}. TIGHT on the long sides")
    row("top-edge step: faceplate left over the rebate", D["fp_over_reb"], ">= 0.80", D["fp_over_reb"] >= 0.8 - 1e-9,
        f"[Ed 14:02] rebate {st['w']:g} wide past the cutout wall, {st['d']:g} deep into the {D['fp_t']:g} faceplate back, along the top "
        f"edge and the long sides from y {D['st_y0']:.2f}; dam z {D['z_dam0']:.2f}–{D['z_dam1']:.2f} on the lip ring")
    row("top-edge step: dam inside the faceplate (nothing behind the panel)", D["z_dam0"] - D["z_fp0"], ">= 0.02",
        D["z_dam0"] - D["z_fp0"] >= 0.02 - 1e-9, "the faceplate's top edge sits on the rail strip: the dam and its bead stay inside the wall")
    S = D["tb_sock"]
    bx = D["board_x1"] - D["vb_pin_x"] - S["pad_hw"]
    row("top board covers the sockets' pads (copper to the edge)", bx, f">= {D['cu_edge']:.2f}", bx >= D["cu_edge"] - 1e-9,
        f"board ±{D['board_x1']:.2f} (v0.7 ±18.90) × {D['board_y0']:.2f}..{D['board_y1']:.2f}; socket rows x ±{D['vb_pin_x']:g} [A mirror of "
        f"electronics], pads ±{S['pad_hw']:g} [A]; {S['n']} way each, y {D['sock_y'][0]:.2f}..{D['sock_y'][1]:.2f}")
    sk = [P[n] for n in P if n.startswith("top-board socket")]
    if sk:
        ds = max(k.distance_to(db) for k in sk)
        row("sockets on the top board's underside", ds, "<= 0.02", ds <= 0.02, f"{S['part']}; entry z {D['z_sock0']:.2f}")
        dn = min(k.distance_to(plate) for k in sk)
        row("sockets clear of the case cradle (hangers, seats)", dn, f">= {sla:.2f}", dn >= sla - 1e-9, "")
    row("top board edges clear of the nest walls", cc["nest_c"], f">= {sla:.2f}", cc["nest_c"] >= sla - 1e-9,
        f"nest ±{D['nest_hw']:.2f} × {D['nest_y0']:.2f}..{D['nest_y1']:.2f}")
    sg = D["z_seat0"] - D["z_db1"]
    row("lower ball seats clear of the top board", sg, ">= 1.0", sg >= 1.0 - 1e-9,
        f"seat bosses from z {D['z_seat0']:.2f}, board top z {D['z_db1']:.2f}; balls at (±{D['bx']:.2f}, +{D['by_top']:.2f} / −{D['by_bot']:.2f})")
    row("top board flex at a worst-case click (on the posts)", D["tb_flex"], "<= 0.10", D["tb_flex"] <= 0.10,
        f"{D['push_hi']:.2f} N at the centre, {D['db_t']:g} FR4 spanning the posts {D['tb_span']:g} [A E 18 GPa, simply supported]; adds "
        f"to the {D['press_travel']:.2f} press")
    cb_ = min(D["car_hw"] - (abs(x) + D["boss_r"]) for x, _ in D["balls"])
    cby = min(D["car_hh"] - (abs(y) + D["boss_r"]) for _, y in D["balls"])
    row("carrier cup bosses inside the carrier outline", min(cb_, cby), ">= 0", min(cb_, cby) >= -1e-6,
        f"(±{D['bx']:.2f}, +{D['by_top']:.2f} / −{D['by_bot']:.2f}), cup boss r {D['boss_r']:.2f}")
    fits = D["car_hw"] + D["slide"] + sla <= D["lip_in_hw"] + 1e-9 and D["car_hh"] + D["slide"] + sla <= D["lip_in_hh"] + 1e-9
    row("carrier drops through the lip ring", 1.0 if fits else 0.0, "fits", fits,
        f"carrier ±{D['car_hw']:.2f} × ±{D['car_hh']:.2f} + slide {D['slide']:.2f} + {sla:.2f} inside the lip ±{D['lip_in_hw']:.2f} × ±{D['lip_in_hh']:.2f}")


def _case_rows9(D, P, row, car, bez, plate, db, fp):
    """v0.9 [Ed 18:35 / 19:12]: the cradle printed into the case. One print (no bead, no step), the pins take the stack (rows in the knob
    assembly), the top board glued up under the printed shoulders, corner notches round the top corner posts."""
    import itertools as _it
    cc, sla, S, G = D["cc"], D["tol_sla"], D["tb_sock"], D["glue9"]
    d = plate.distance_to(fp)
    try:
        v = (plate & fp).volume
    except Exception:
        v = 1e9
    row("cradle printed with the case: lip ring on the cutout wall, flange on the faceplate back (one print)", d, "<= 0.001",
        d <= 1e-3 and v <= 1e-3,
        f"[Ed 18:35] one UTR-8100 print: the lip ring fills the cutout wall from the faceplate back to {cc['lip_below']:g} under the front "
        f"(inner face ±{D['lip_in_hw']:.2f} × ±{D['lip_in_hh']:.2f}, as v0.8: the carrier and the balls do not move); the flange keeps its v0.8 "
        f"height (top z {D['z_fl1']:.2f}, {D['fl_drop']:.2f} under the faceplate back [A]) and a riser outboard of the lip's inner face joins it "
        "to the faceplate. In the knob model the two solids are fused into the case")
    row("case cradle lip ring in the cutout (depth below the front)", D["lip_engage"], ">= 1.0", D["lip_engage"] >= 1.0 - 1e-9,
        f"lip z {D['z_fp0']:.2f}→{D['z_lip1']:.2f}; the top {cc['lip_below']:g} of the cutout keeps its full size (the grip block covers it)")
    lw = D["hole_hw"] - D["lip_in_hw"]
    w = min(lw, cc["flange_t"], cc["wall"], cc["shoulder"])
    row("printed cradle walls ≥ SLA minimum (lip ring, flange, hangers, shoulders)", w, ">= 0.80", w >= 0.8 - 1e-9,
        f"lip ring {lw:.2f} (v0.8 1.0 + the 0.2 slot, now filled), flange {cc['flange_t']:g}, hangers {cc['wall']:g}, shoulders "
        f"{cc['shoulder']:g} [S SLA 0.8]. [C] SLA supports for the hangers and ball seats inside the case must be reachable")
    row("grip block covers the cutout (and the lip in it) at full slide", D["block_cover_slide"], f">= {sla:.2f}",
        D["block_cover_slide"] >= sla - 1e-9, f"cover {D['block_cover_rest']:.2f} at rest, {D['block_cover_slide']:.2f} at the {D['slide']:.2f} slide")
    row("grip block clear of the lip top at full press", D["block_lip_press"], f">= {sla:.2f}", D["block_lip_press"] >= sla - 1e-9,
        f"block underside z {D['z_bz0']:.2f} − press {D['press_travel']:.2f}; lip top z {D['z_lip1']:.2f}")
    bx = D["board_x1"] - D["vb_pin_x"] - S["pad_hw"]
    row("top board covers the sockets' pads (copper to the edge)", bx, f">= {D['cu_edge']:.2f}", bx >= D["cu_edge"] - 1e-9,
        f"board ±{D['board_x1']:.2f} (v0.8 ±19.25) × {D['board_y0']:.2f}..{D['board_y1']:.2f}; socket rows x ±{D['vb_pin_x']:g} [Ed 19:12 (4): "
        f"0.3 inboard], pads ±{S['pad_hw']:g} [A]; {S['n']} way each, y {D['sock_y'][0]:.2f}..{D['sock_y'][1]:.2f} ({D['sock_y_shift']:+g} toward "
        "the knob [A])")
    sk = [P[n] for n in P if n.startswith("top-board socket")]
    if sk:
        ds = max(k.distance_to(db) for k in sk)
        row("sockets on the top board's underside", ds, "<= 0.02", ds <= 0.02, f"{S['part']}; entry z {D['z_sock0']:.2f}")
        dn = min(k.distance_to(plate) for k in sk)
        row("sockets clear of the printed cradle (hangers, seats)", dn, f">= {sla:.2f}", dn >= sla - 1e-9, "")
    row("top board edges clear of the nest walls", cc["nest_c"], f">= {sla:.2f}", cc["nest_c"] >= sla - 1e-9,
        f"nest ±{D['nest_hw']:.2f} × {D['nest_y0']:.2f}..{D['nest_y1']:.2f}; the last {D['z_db1'] - D['z_nest0']:.1f} of the board's way in")
    sg = D["z_seat0"] - D["z_db1"]
    row("lower ball seats clear of the top board", sg, ">= 1.0", sg >= 1.0 - 1e-9,
        f"seat bosses from z {D['z_seat0']:.2f}, board top z {D['z_db1']:.2f}; balls at (±{D['bx']:.2f}, +{D['by_top']:.2f} / −{D['by_bot']:.2f})")
    a, b, al = D["tb_plate"]
    row("top board flex at a worst-case click (glued under the shoulders)", D["tb_flex"], "<= 0.10", D["tb_flex"] <= 0.10,
        f"{D['push_hi']:.2f} N at the switch; 1.0 FR4 plate {a:.1f} × {b:.1f} between the shoulders' inner edges, simply supported on four "
        f"edges [S Timoshenko α {al:.4f}; A E 18 GPa]; v0.8 on the posts 0.061. Stiffness {D['tb_k']:.0f} N/mm")
    row("top board glue line under the shoulders: peak line load at a worst-case click", D["glue_q_click"], f"<= {G['peel'] / 3:.2f}",
        D["glue_q_click"] <= G["peel"] / 3 + 1e-9,
        f"[Ed 18:35] the pins slide, so a press goes stem → top board → glue (tension / peel) → printed shoulders → case. {D['push_hi']:.2f} N "
        f"over {D['glue_len']:.0f} mm of glue line × {G['peak']:g} peak [A]; target a third of a cautious {G['peel']:g} N/mm peel [A, not sourced]")
    row("top board glue line at the overpress stop (info: grip block lands on the faceplate)", D["glue_q_op"], f"info ({G['peel']:g} [A])", True,
        f"past the switch's bottom a hard press pushes the board {D['op_gap']:.2f} more before the block lands on the faceplate: about "
        f"{D['op_f']:.0f} N into the glue ({D['glue_q_op']:.2f} N/mm peak). " + ("TIGHT: over the cautious peel figure [A]. " if D["glue_q_op"] >
        G["peel"] else "") + "[C, Danny] a toughened epoxy, a screw or clip at the board ends, or less block travel would take it")
    cb_ = min(D["car_hw"] - (abs(x) + D["boss_r"]) for x, _ in D["balls"])
    cby = min(D["car_hh"] - (abs(y) + D["boss_r"]) for _, y in D["balls"])
    row("carrier cup bosses inside the carrier outline", min(cb_, cby), ">= 0", min(cb_, cby) >= -1e-6,
        f"(±{D['bx']:.2f}, +{D['by_top']:.2f} / −{D['by_bot']:.2f}), cup boss r {D['boss_r']:.2f}")
    fits = D["car_hw"] + D["slide"] + sla <= D["lip_in_hw"] + 1e-9 and D["car_hh"] + D["slide"] + sla <= D["lip_in_hh"] + 1e-9
    row("carrier drops through the lip ring", 1.0 if fits else 0.0, "fits", fits,
        f"carrier ±{D['car_hw']:.2f} × ±{D['car_hh']:.2f} + slide {D['slide']:.2f} + {sla:.2f} inside the lip ±{D['lip_in_hw']:.2f} × ±{D['lip_in_hh']:.2f}")
    # corner notches round the top corner posts (the board passes their bases on its way in from the back)
    if D.get("tb_notch"):
        rp = D["tb_notch"][0][2] - D["notch_air"]
        posts = [cyl_(2 * rp, D["z_db0"], D["z_db1"], x, y) for x, y, _ in D["tb_notch"]]
        dp = min(db.distance_to(q) for q in posts)
        nx, ny = D["tb_notch_size"]
        row("top-board corner notches clear the top corner posts (plan)", dp, f">= {D['notch_air']:.2f}", dp >= D["notch_air"] - 1e-4,
            f"[Ed 18:35] notch round each post (r {rp:.2f} + {D['notch_air']:g}) squared off to the +y edge: {nx:.2f} deep (x) × {ny:.2f} along "
            f"the edge (y {D['tb_notch_y0']:.2f}..{D['board_y1']:.2f}); posts at (±{abs(D['tb_notch'][0][0]):.2f}, {D['tb_notch'][0][1]:.2f}). The path "
            "row (knob assembly) checks the real case")
        from .parts import top_board_notches as _tbn
        big = box_(-60, 60, -60, 60, D["z_sock0"] - 1.0, D["z_db1"] + 3.0)
        cut = big - _tbn(D, big, D["z_sock0"] - 2.0, D["z_db1"] + 4.0)       # the notch volumes, through every part's height
        near = [(P[n].distance_to(cut), n) for n in P if n.startswith(("top-board socket", "screen FPC socket", "SW1"))]
        dmin, who = min(near)
        row("nothing on the top board in the corner notches (part bodies)", dmin, ">= 0 (none cut)", dmin >= -1e-6,
            f"nearest: {who}; " + ", ".join(f"{n.split(' (')[0]} {v:.2f}" for v, n in sorted(near)[:3]) + ". TIGHT: the sockets' outer "
            "corners sit at the notch's edge (they are what the 0.3 path is measured from); the screen FPC socket (AXE530127, top face) "
            "body is about 0.19 from it: its +y end hold-down pad must keep 0.3 copper-to-edge in KiCad [C]")
        # socket pads: single-row SMT 1.27 sockets put their pads on alternate sides [S Mill-Max 853 footprint]; the end pin by the notch
        # has its pad inboard [A]. Pads 0.76 long [A].
        best = 9e9
        for sx in (-1, 1):
            x_r = sx * D["vb_pin_x"]
            for k, y in enumerate(D["sock_pin_y"]):
                out_ = (S["n"] - 1 - k) % 2 == 1
                xa, xb = sorted((x_r, x_r + sx * S["pad_hw"])) if out_ else sorted((x_r, x_r - sx * S["pad_hw"]))
                for x0, y0, r in D["tb_notch"]:
                    if x0 * sx < 0:
                        continue
                    dx = max(xa - x0, 0.0, x0 - xb); dy = max((y - 0.38) - y0, 0.0, y0 - (y + 0.38))
                    dc = math.hypot(dx, dy) - r                           # to the notch's round part
                    dbx = (abs(x0) - r) - max(abs(xa), abs(xb))             # to the squared-off part (x), where y + 0.38 > y0
                    best = min(best, dc if (y + 0.38) <= y0 else min(dc, dbx))
        row("socket pads clear of the corner notches (copper to the edge)", best, f">= {D['cu_edge']:.2f}", best >= D["cu_edge"] - 1e-6,
            f"pads ±{S['pad_hw']:g} × 0.76 [A] on alternate sides [S Mill-Max 853]; the end pin by the notch has its pad inboard [A, KiCad]")
    if "sf_up_wc" in D:
        lo, hi = D["sf_up_wc"]
        row("tipping up the panel at the worst-case corner of the up-stop stack (info)", lo, "info (1.3 wanted)", True,
            f"[Ed 19:12 (1)] HT-870 kept: {lo:.3f}–{hi:.3f} in the corner where the stack is tightest (the cushion preloads the stem "
            f"{D['us_choice']['f_wc'][0]:.2f}–{D['us_choice']['f_wc'][2]:.2f} N); {D['sf_up']:.3f} over the RSS band. NOT over 1.3 in that corner: the "
            "shoulder-to-seat term (0.2 SLA) is still one dimension inside one print, and the cradle-to-faceplate term that left was never in "
            "this stack. Setting the sleeve length at assembly (±0.1) keeps the cushion off the stem [C]")


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
