"""control_dial LOCAL checks (own parts + interface values only)."""
import math
from build123d import Rot
from ..common.checks import Rows, min_dist, posed, maxr
from .parts import hall_arm as hall

def _rib_defl(D):
    """In-plane tip deflection (mm) of the tapered rib as a cantilever, load at ha_rib_rload, root at the dial tube."""
    F, E = D["ha_rib_load"], D["ha_rib_E"]
    r0, rh, rF = D["ha_rib_r_hub"], D["ha_rib_r_head"], D["ha_rib_rload"]
    w0, w1 = D["ha_rib_w0"], D["ha_rib_w1"]
    z1, zc, zl, rs = D["ha_rib_z_top"], D["ha_rib_z_cage"], D["ha_rib_z_low"], D["ha_rib_r_step"]
    def w(r):
        return w0 + (w1 - w0) * (r - r0) / (rh - r0) if r <= rh else w1
    def h(r):
        return z1 - (zc if r < rs else zl)
    def I(r):
        return h(r) * w(r) ** 3 / 12.0   # bending in the plane of the sweep
    n = 2000
    s = 0.0
    for i in range(n):
        r = r0 + (rF - r0) * (i + 0.5) / n
        s += F * (rF - r) ** 2 / (E * I(r))
    return s * (rF - r0) / n

def _arc_rows(D, row):
    """v0.21 [Ed 2 Nov]: the single detent on the arc (three dimples on a raised land) and the three ball tracks
    (big, small, big) under the arm. Analytic rows; the swept solids are checked in the assembly cross-checks."""
    T, rb, r = D["travel_deg"], D["det_ball"] / 2, D["ad_r"]
    old = 2 * D["det_r"] * math.sin(math.radians(D["det_deg"]) / 2) - 2 * D["ad_rim"]
    row("arc detent: flat land between neighbouring dimple rims (mm)", D["ad_flat"], D["ad_land_min"],
        f"dimples at 0, ±{D['det_deg']:g}° on r {r:.2f} (v0.20 inboard r {D['det_r']:.2f}: {old:.2f}); pitch {D['ad_pitch']:.2f}, "
        f"rim Ø{2 * D['ad_rim']:.2f} (Ø{2 * rb:g} ball, {D['det_dimple']:g} deep)")
    row("arc detent: land left past the ball at the hard stop (mm of arc)",
        r * math.radians(D["ad_land_half"] - T) - rb, D["tgt"]["arm_vs_cradle"],
        f"land r {D['ad_land_r0']:.2f}–{D['ad_land_r1']:.2f}, ±{D['ad_land_half']:.1f}° about {D['ad_ang']:.0f}°, top z {D['ad_z_land']:.2f} (rib top)")
    row("arc detent: ball still in the end dimple at the hard stop (rim - offset, mm)", D["ad_rim"] - D["ad_stop_off"], D["det_stop_clear"],
        f"hard stop ±{T:.2f}° (unchanged) is {D['ad_stop_off']:.2f} mm of arc past the ±{D['det_deg']:g}° dimple at r {r:.2f}")
    ang_in = r * math.radians(D["fan_half"] - abs(D["ad_off"]) - D["ad_land_half"])
    row("arc detent: land inside the fan (radial and along the arc, mm)", min(D["ad_land_r0"] - D["fan_r0"], D["fan_r1"] - D["ad_land_r1"], ang_in),
        D["tgt"]["arm_vs_cradle"], f"fan r {D['fan_r0']:.2f}–{D['fan_r1']:.2f}, ±{D['fan_half']:.1f}°; {ang_in:.2f} along the arc")
    b, s = D["bt_ball"], D["tk_small"]
    row("ball tracks: separator below both races ((big - small)/2, mm)", (b - s) / 2, D["tk_seat_min"],
        f"Ø{b:g} load balls, Ø{s:g} separators (1/32\" = 0.794 also fits); groove R{D['bt_groove_r']:g}")
    slit = D["fan_z0"] - D["plate_t"]
    row("ball tracks: separator cannot leave through the plate-to-web slit (Ø - slit, mm)", s - slit, 0.1, f"slit {slit:.2f}")
    row("ball tracks: separator cannot pass a load ball in the groove (big + small - groove Ø, mm)", b + s - 2 * D["bt_groove_r"], 0.1)
    for t in D["tk"]:
        left = t["r"] * math.radians(t["half"] - T / 2 - t["offs"][-1]) - b / 2
        row(f"ball track {t['k']}: groove left past the end ball at ±travel, both races (mm of arc)", left, D["tk_end_clear"] - 1e-6,
            f"{'encoder' if t['side'] < 0 else 'lever'} side of the Hall slot, row {t['row']}: r {t['r']:.2f}, groove {t['ang']:.1f}° ±{t['half']:.1f}°, "
            f"balls " + "/".join(f"{d:g}" for d in t["dias"]) + f" at ±{t['offs'][-1]:.1f}°, rolled ±{T / 2:.2f}°; "
            f"groove end {D['tk_bar_clear']:g} off the bar's swept edge ({t['edge']:.1f}°)")

def _split_rows(D, row):
    """v0.22 [Ed 2 Nov 15:27]: detent on its own spoke, ball train under the ball. Analytic rows; swept solids in the assembly."""
    T, rb, r = D["travel_deg"], D["det_ball"] / 2, D["ad_r"]
    row("split detent: flat land between neighbouring dimple rims (mm)", D["ad_flat"], D["ad_land_min"],
        f"dimples at 0, ±{D['det_deg']:g}° on r {r:.2f} at {D['ad_ang']:.0f}°; pitch {D['ad_pitch']:.2f}, rim Ø{2 * D['ad_rim']:.2f}")
    row("split detent: flange left past the ball at the hard stop (mm of arc)", r * math.radians(D["ad_land_half"] - T) - rb,
        D["tgt"]["arm_vs_cradle"], f"flange r {D['ad_land_r0']:.2f}-{D['ad_land_r1']:.2f}, ±{D['ad_land_half']:.1f}°, z {D['sp_z_fu']:.2f}-{D['ad_z_land']:.2f}")
    row("split detent: ball still in the end dimple at the hard stop (rim - offset, mm)", D["ad_rim"] - D["ad_stop_off"], D["det_stop_clear"],
        f"hard stop ±{T:.2f}° is {D['ad_stop_off']:.2f} mm of arc past the ±{D['det_deg']:g}° dimple")
    row("split detent: train centred under the detent ball (mm)", 0.0, 0.0, "load path spring > ball > flange > train > pedestal > plate", higher_ok=False)
    b, s = D["bt_ball"], D["tk_small"]
    row("ball train: separator below both races ((big - small)/2, mm)", (b - s) / 2, D["tk_seat_min"])
    row("ball train: separator cannot pass a load ball in the groove (big + small - groove Ø, mm)", b + s - 2 * D["bt_groove_r"], 0.1)
    slit = D["sp_z_fu"] - D["sp_z_ped"]
    row("ball train: separator cannot leave through the pedestal-to-flange slit (Ø - slit, mm)", s - slit, 0.1, f"slit {slit:.2f}")
    for t in D["tk"]:
        left = t["r"] * math.radians(t["half"] - T / 2 - t["offs"][-1]) - b / 2
        row(f"ball train {t['k']}: groove left past the end ball at ±travel, both races (mm of arc)", left, D["tk_end_clear"] - 1e-6,
            f"r {t['r']:.2f}, {t['ang']:.0f}° ±{t['half']:.1f}°, balls " + "/".join(f"{d:g}" for d in t["dias"]) + f", z {t['z']:.2f}")
    d = _rib_defl(D)
    row("Hall rib deflection margin (limit / deflection, x)", D["ha_rib_defl"] / max(d, 1e-9), 2.0,
        f"{d:.4f} mm at r {D['ha_rib_rload']:g} under {D['ha_rib_load']:g} N; rib top z {D['ha_rib_z_top']:.2f} [Ed 2x rule]")

def _dist(a, b):
    """min distance between two lists of solids, and the pair."""
    best = (1e9, "", "")
    for na, sa in a.items():
        for nb, sb in b.items():
            d = sa.distance_to(sb)
            if d < best[0]: best = (d, na, nb)
    return best


def _short(n):
    return n.replace("dial screen Z132A2441 ", "").replace("dial board part ", "").replace("dial board ", "").replace(" (printed cartridge ring)", "")


def _cart_rows(D, parts, row):
    """v0.24 [Ed 3 Nov 12:28-12:58] bezel cartridge: the reworked rows of the v0.23 screen (Kingtech panel, printed carrier, strap)."""
    T = D["tgt"]; zp, db, ct, bz = D["zp"], D["db"], D["ct"], D["bz"]
    P = lambda *pre: {n: s for n, s in parts.items() if n.startswith(pre)}
    bezel = P("dial bezel"); dial = P("control dial"); pad = P("dial cartridge plug pad")
    panel = P("dial screen Z132A2441 panel", "dial screen Z132A2441 flex", "dial screen Z132A2441 lens")
    flex = P("dial screen Z132A2441 flex"); plug = P("dial screen Z132A2441 plug")
    board = P("dial board (PCBA"); top = P("dial board receptacle")
    under = {n: s for n, s in P("dial board ").items() if n not in board and n not in top}
    from ..common.util import tube
    ring = tube(D["R"], D["R"] + 3.0, D["z_lip0"], D["z_top"] - D["z_lip0"])       # exact: distance out to the knob OD
    reach = D["R"] - min(s.distance_to(ring) for s in list(panel.values()) + list(plug.values()))
    row("knob OD vs the cartridge panel (R - outermost panel point)", D["R"] - reach, T["knob_od_vs_screen"],
        f"Z132A2441 [S] reaches r {reach:.2f} (" + ", ".join(f"{k} {v:.2f}" for k, v in D["cart_reach"].items()) + f"); knob Ø{D['knob_od']:.2f}")
    row("bezel wall below the glass (OD - bore)", D["bz_wall"], D["print_wall_min"],
        f"bore Ø{bz['bore_d']:g}, OD {D['knob_od']:g} [Ed 12:58]; bezel z {D['z_lip0']:.2f}-{D['z_top']:.2f} (outside = the v0.23 lip)")
    row("bezel bore past the panel's outermost point (radial; the panel is glued in from underneath)", D["bz_bore_clear"], 0.3,
        f"U-turn corner r {D['cart_reach']['U-turn corner']:.2f} [S], bottom bend r {zp['bend_r']:g}, top tab r {zp['tab_r']:g}; bore r {D['bz_bore_r']:.2f}")
    d, a, b = _dist(flex, bezel)
    row("panel flex (bends, tab, tail, patches) vs the bezel", d, 0.3 - 1e-6,
        f"nearest: {_short(a)} / bezel; TIGHT: bends and tab start {zp['bend_top']:g} behind the lens back [A], right under the glass seat ring")
    lap = D["bz_lap"]; glue = min(D["bz_seat_r"] - zp["lens_d"] / 2, D["bz_lap_r"] - zp["step_d"] / 2)
    row("bezel laps the lens step: lens shoulder under the lap (radial)", lap, 0.5,
        f"lap ID Ø{bz['lap_d']:g} over the Ø{zp['lens_d']:g} lens, 0.55 deep (step Ø{zp['step_d']:g}): no glass edge shows; glue gap {glue:.2f} round the lens")
    d, a, b = _dist(panel, {**board, **top})
    row("panel (lens, AMOLED, flex) vs the dial board and receptacle", d, 0.3, f"nearest: {_short(a)} / {_short(b)}; the mated plug end is not counted")
    d, a, b = _dist(panel, dial)
    row("panel vs the dial body (they turn together)", d, 0.3, f"nearest: {_short(a)}; land z {D['db_z1']:.2f}, lower leg z {D['leg_z0']:.2f}")
    d, a, b = _dist(bezel, {**board, **top})
    row("bezel (ribs) vs the dial board", d, 0.3, f"nearest: {_short(b)}")
    row("bezel bore over the dial's outer wall (radial)", D["ct_bore_clear"], 0.3 - 1e-6,
        f"dial r {ct['outer_r']:g} [Ed 12:58] in the r {D['bz_bore_r']:.2f} bore, TIGHT (exactly the target)")
    _cart_v025_rows(D, parts, row, bezel, dial, panel, P)
    d, a, b = _dist(pad, {**panel, **P("dial screen Z132A2441 flex")})
    row("plug pad + arm vs the panel (not the plug end it is glued to)", d, 0.3, f"nearest: {_short(b)}; pad z {D['pad_z'][0]:.2f}-{D['pad_z'][1]:.2f}")
    d, a, b = _dist(pad, {**board, **top, **dial})
    row("plug pad + arm vs the dial board, receptacle and dial", d, 0.3, f"nearest: {_short(b)}")
    row("plug pad arm to the bezel bore (glue line)", list(pad.values())[0].distance_to(list(bezel.values())[0]), bz["arm_glue"] + 0.01,
        f"arm at {bz['arm_ang']:g}° [Ed 12:58], {bz['arm_w']:g} x {bz['arm_t']:g} [A]; glued with the cartridge seated on its dial", higher_ok=False)
    row("plug / receptacle alignment in plan (centre offset)", D["plug_align"], 0.1,
        f"plug ({D['plug_xy'][0]:.2f}, {D['plug_xy'][1]:.2f}) [S] over the receptacle ({db['rec'][0]:g}, {db['rec'][1]:g}); set by gluing the pad seated", higher_ok=False)
    row("plug engagement: receptacle top - plug mating face", D["plug_engage"], 0.2,
        f"mating face {zp['plug_face']:g} behind the lens back at full mate [S], here {bz['plug_standoff']:g} off it (key seated) = z {D['plug_face_z']:.2f}; "
        f"receptacle top {D['rec_z1']:.2f}; mated height {zp['mated']:g} [S]")
    lo, hi = D["ct_wall_at"]
    row("dial wall over the 30° cone underside (pocket floor, min normal)", D["ct_wall"], ct["wall"] - 0.005,
        f"min at r {lo:.1f}-{hi:.1f} (the whole cone run: the floor is the 2.0 offset [Ed 12:58]); well floor {D['z_well_top']:.2f}, pocket edge z {D['ct_floor_edge']:.2f}")
    import itertools
    sp = min(((under[a].distance_to(under[b]), a, b) for a, b in itertools.combinations(under, 2)), default=(9.9, "", ""))
    row("dial-board underside parts: spacing (min)", sp[0], 0.2, f"{_short(sp[1])} / {_short(sp[2])}; places from the concept [Ed 12:58], bodies [A] except the ESP32 [S]")
    d, a, b = _dist(under, dial)
    row("dial-board underside parts vs the pocket floor", d, ct["parts_clear"],
        f"nearest: {_short(a)}; ESP32 7 x 7 x 0.96 [S] at (0, 10.5), diode Ø3.8 x 2.5, LEDs at r 13.5 [A 2020]")
    row("dial board rim resting on the ledge (radial)", D["db_on_ledge"], 0.4,
        f"board Ø{db['d']:g} [A] on the ledge r {ct['pocket_r']:g}-{D['ct_land_r']:.1f} at z {D['db_z0']:.2f}; edge {D['db_to_step']:.2f} from the land step, lobe {ct['lobe_clear']:g} in its cut")
    row("cartridge magnets: stray field at the Hall row (worst sensor) / range", D["carr_stray_mt"] / D["carr_stray_rng"], D["carr_stray_max"],
        f"{D['carr_stray_to']}: {D['carr_stray_mt'] * 1e3:.1f} µT of ±{D['carr_stray_rng']:g} mT ({D['cart_stray_n']} x Ø{bz['mag'][0]:g}x{bz['mag'][1]:g} N52 "
        f"~54 mm above, radial dipoles, v0.25 sideways pairs); it changes {D['cart_stray_dB'] * 1e3:.3f} µT over ±travel", higher_ok=False)
    row("strap loop bend strain at ±travel (%)", D["strap_strain_pct"], D["strap_strain_max"],
        f"ribbon on edge, {D['ls_L']:.1f} between the ends, t {D['strap_t']:g}; dial end moves {D['strap_end_move']:.2f} sideways and turns ±{D['travel_deg']:.1f}°; "
        f"R {D['strap_R']:.0f} mm", higher_ok=False)


def checks(D, parts):
    T = D["tgt"]; r = Rows("control_dial"); row = r.row
    if D.get("cart"):
        return _cart_tail(D, parts, r)
    scr = [s for n, s in parts.items() if n.startswith("screen ") and "jumper" not in n]
    r_max = max([D["scr_far"]] + [maxr(s) for s in scr])
    row("knob OD vs screen (R - outermost screen point)", D["R"] - r_max, T["knob_od_vs_screen"], f"knob Ø{D['knob_od']:.2f}, screen offset {D['scr_off']:.2f} from the FPC exit")
    on = D["screen_on_dial"]; TR = (-D["travel_deg"], 0, D["travel_deg"])
    if on:
        row("dial lip wall (far side, lip bonded round the panel)", D["lip_wall"], T["lip_wall"],
            f"lip ID Ø{D['lip_id']:.2f} = panel Ø{D['S']['od']:.2f} + 2×bond {D['lip_bond_gap']:.2f}, centred on the panel (offset {D['scr_off']:.3f}); near side {D['lip_wall_near']:.2f}; {D['lip_wall_lines']} lines × {D['nozzle']:g}")
        if D["lip_closed"]:
            row("dial lip wall outside the COF-bend pocket (closed ring)", D["lip_wall_bend"], T["lip_wall"],
                f"bend reaches r {D['bend_reach_ax']:.3f} + clear {D['bend_clear']:g}; knob Ø{D['knob_od']:.2f} (min {D['knob_od_min']:.3f})")
            row("printed walls (lip far side and outside the bend pocket)", min(D["lip_wall"], D["lip_wall_bend"]), D["print_wall_min"],
                f"v0.17 floor {D['print_wall_min']:g}; designed lip {D['lip_wall_lines']}×{D['nozzle']:g} mm = {D['lip_wall_min']:.2f}")
            row("dial up-stop: free lift to the adapter board (no cup)", D["dial_lift"], 0.1, "board clamped by the rod nut; 45° race carries the knob up-load into the dial")
            row("dial up-stop: free lift (max)", D["dial_lift"], 0.5, "", higher_ok=False)
    else:
        row("dial lip wall (far side of the offset panel)", D["lip_wall"], T["lip_wall"], f"lip ID Ø{D['lip_id']:.2f} = panel Ø{D['S']['od']:.2f} + 2×(offset {D['scr_off']:.2f} + run {D['run_gap']:.2f})")
    dial = parts["control dial"]
    fp = [n for n in parts if n.endswith("FPC + B2B")][0]
    dmin = min(parts[fp].distance_to(Rot(0, 0, t) * dial) for t in ((0,) if on else TR))
    row("FPC fold / COF bend vs dial" + ("" if on else " (±travel)"), dmin, 0.1, "fold corners inside the lip ID, bend in the lip slot" + (" (turn together)" if on else ""))
    pn = [n for n in parts if n.endswith(" panel")][0]
    if on:
        row("panel vs dial lip (bond gap, turns with the dial)", parts[pn].distance_to(dial), max(D["lip_bond_gap"] - 0.01, 0.0), "no running gap [Ed]")
        row("FPC strap bend strain at ±travel (%)", D["strap_strain_pct"], D["strap_strain_max"],
            f"L {D['strap_L']:.1f}, R {D['strap_R']:.0f} mm, t {D['strap_t']:g}, end moves {D['strap_end_move']:.2f}", higher_ok=False)
        b2b = parts[fp]
        if "adapter cup (fixed)" in parts:
          bmin = min((Rot(0, 0, t) * b2b).distance_to(parts["adapter cup (fixed)"]) for t in TR)
          row("rotating B2B / fold vs fixed adapter cup (±travel)", bmin, T["carrier_vs_cup"])
          row("screen carrier vs fixed adapter cup", parts["screen carrier (on dial)"].distance_to(parts["adapter cup (fixed)"]), T["carrier_vs_cup"], f"carrier_run {D['carrier_run']:g}")
    else:
        row("panel vs dial lip (running gap)", parts[pn].distance_to(dial), D["run_gap"] - 0.01)
    row(f"screen carrier magnet: stray field at the {D['carr_stray_to']} / range", D["carr_stray_mt"] / D["carr_stray_rng"], D["carr_stray_max"],
        f"{D['carr_stray_mt']:.3f} mT on-axis dipole worst case" + ("; co-rotates with the sensor -> fixed offset, calibrated out" if D["rel_sensor"] else "; turns ±travel over a fixed sensor -> tiny, calibrated"), higher_ok=False)
    return _tail(D, parts, r)


def _split_dial_rows(D, parts, row):
    """v0.25 [Ed 18:12]: the dial in two parts, split at the dish's underside; the tube end bonded up a socket in the dish."""
    s = D["dsp"]
    lo = [q for n, q in parts.items() if n.startswith("control dial lower part")]
    di = [q for n, q in parts.items() if n.startswith("control dial dish")]
    row("dial split: tube end engaged up the dish's socket (mm)", D["dsp_engage"], s["engage_min"],
        f"split at the dish's underside z {D['dsp_z0']:.2f} (0.3 over the cap top {D['dsp_z0'] - D['knob_run']:.2f}); tube end z {D['dsp_z1']:.2f}, "
        f"{s['top_below']:g} under the well floor {D['z_well_top']:.2f} (the rod-link board up-stop keeps its {D['dial_lift']:.2f})")
    row("dial split: dish wall round the socket (radial, at the dish's underside, mm)", D["dsp_dish_wall"], D["print_wall_min"],
        f"socket Ø{2 * D['dsp_r_sock']:.2f} (tube Ø{D['dial_tube_od']:.2f} + {s['glue']:g} bond) in the hub Ø{D['dial_hub_od']:.2f}; MJF PA-12")
    row("dial split: tube wall at the key flat (mm)", D["dsp_tube_wall_flat"], D["print_wall_min"],
        f"flat {s['flat']:g} deep at {D['dsp_flat_ang']:.0f}° (mech), tube Ø{D['dial_tube_id']:.2f}/Ø{D['dial_tube_od']:.2f}; TIGHT-ish: MJF wall {D['print_wall_min']:g}")
    row("dial split: bond shear at the dial design torque vs epoxy on PA-12 / 2 (MPa)", D["dsp_bond_tau"], s["bond_allow"] / 2,
        f"{s['T_design']:g} mNm [A] over {D['dsp_bond_area']:.0f} mm² of socket (r {D['dial_tube_od'] / 2:.2f} x {D['dsp_engage']:.2f}); "
        f"allowable {s['bond_allow']:g} MPa [A]; the flat keys the angle, the bond carries the torque", higher_ok=False)
    if lo and di:
        d = lo[0].distance_to(di[0])
        row("dial split: lower part vs dish (bond gap, not touching elsewhere)", d, s["glue"] - 0.01,
            "the tube in the socket; axial position set by the bond (the dish on the balls, the lower part on the train)")

def _cart_v025_rows(D, parts, row, bezel, dial, panel, P):
    """v0.25 [Ed 18:26, 19:12 item 2]: plain bezel with a key (+ two seat ribs), sideways magnet pairs; the ribs seat it."""
    from ..common.util import cyl
    from ..common.process import PROCESS
    bz, ct = D["bz"], D["ct"]; mjf = PROCESS["mjf"]
    bzs = list(bezel.values())[0]
    # nothing inside r 18.5 below the glass: the lens's path (a Ø36.4 cylinder up to the lens back) vs the bezel
    zb = D["lens_back"]
    below = bzs & cyl(30.0, D["z_lip0"] - 1.0, zb - 0.05 - (D["z_lip0"] - 1.0))   # the bezel under its glass seat (lens back z zb)
    rin = 0.01 + below.distance_to(cyl(0.01, D["z_lip0"] - 2.0, 20.0))
    row("bezel: innermost radius below the glass seat (the glass and panel go straight up)", rin, 18.5,
        f"key + seat ribs' inner face r {bz['rib_r_in']:g} [Ed 18:26 'nothing inside r 18.5']; lens edge r {D['zp']['lens_d'] / 2:.2f}; no bosses")
    mv = [q for n, q in parts.items() if n.startswith(("dial screen Z132A2441 lens", "dial screen Z132A2441 panel", "dial screen Z132A2441 flex"))]
    from build123d import Pos
    sw = min(bzs.distance_to(Pos(0, 0, -dz) * q) for q in mv for dz in (1.0, 2.0, 3.5, 5.0, 7.0))
    row("glass + panel + flex swept up into the bezel from underneath (1-7 mm short of home)", sw, 0.1,
        "the bends, top tab and U-turn pass the ribs; the magnets sit in the skirt (r ≥ the bore); the last 1 mm is the lens into "
        "its seat (0.05 glue gaps)")
    # magnets
    fr, fz = D["cm_F_pair"]; n = len(bz["mag_angs"]); W = D["cm_mass_g"] * 9.81e-3
    row("cartridge magnets: hold-down of the sideways pairs vs the cartridge's weight (x)", D["cm_hold"] / W, 2.0,
        f"{n} pairs Ø{bz['mag'][0]:g}x{bz['mag'][1]:g} N52 at {', '.join(f'{a:g}' for a in bz['mag_angs'])}°, faces {D['cm_gap']:.2f} apart, "
        f"bezel magnet {bz['mag_dz']:+g} above its partner, attracting: {-fz:.3f} N down and {-fr:.3f} N in a pair, {D['cm_hold']:.2f} N down "
        f"in all vs {W:.3f} N (~{D['cm_mass_g']:g} g); surface-charge model, Br {D['hv_br']:g} T [method]; the plug's retention comes on top")
    row("cartridge magnets: skirt skin outside the bezel magnet (radial, mm)", D["cm_skin_out"], mjf["feature"],
        f"bezel OD r {D['R']:g}, bore r {D['bz_bore_r']:g}, magnet {bz['mag'][1]:g} deep; "
        + (f"TIGHT: under PCBWay's {mjf['wall']:g} MJF wall " if D["cm_skin_out"] < mjf["wall"] - 1e-6 else
           f"meets PCBWay's {mjf['wall']:g} MJF wall exactly (no margin over the wall rule) ")
        + f"(a skin over a Ø{bz['mag'][0] + bz['mag_press']:g} pocket, held by the {mjf['feature']:g} feature floor) [A]")
    row("cartridge magnets: dial wall over and under the dial magnet (mm)", D["cm_skin_dial"], mjf["feature"],
        f"pocket Ø{bz['mag'][0] + bz['mag_press']:g} centred in the outer wall z {D['z_lip0']:.2f}-{D['db_z1']:.2f}, {bz['mag'][1]:g} deep from r {ct['outer_r']:g}")
    row("cartridge magnets: ring de-centring stiffness (attracting pairs; dF/dx, N/mm)", D["cm_K_ring"], 0.3,
        f"pair gradients {D['cm_k_pair'][0]:+.3f} along the axis / {D['cm_k_pair'][1]:+.3f} sideways; at the 0.3 bore gap the pull to one side "
        f"is ≤ {D['cm_K_ring'] * D['cm_gap']:.3f} N, under the seat friction (~{0.3 * (D['cm_hold'] + W):.2f} N at µ 0.3): the key and the "
        "plug locate the cartridge in plan, the magnets only hold it down", higher_ok=False)
    # key + seat ribs
    key = [c for a, c, k in D["cart_ribs"] if k == "key"][0]; seat = [c for a, c, k in D["cart_ribs"] if k == "seat"]
    row("cartridge key: rib in its slot, tangential clearance a side (key)", key, 0.05 - 1e-6,
        f"key at {bz['rib_angs'][0]:g}° [Ed 18:26], {bz['rib_w']:g} wide; seat ribs at {', '.join(f'{a:g}' for a in bz['rib_angs'][1:])}° [A] "
        f"{min(seat):g} a side (seat only, the key sets the angle); MJF ±0.25 a part: fit the key on the parts")
    row("cartridge key: rib inner face to its slot's inner face (radial)", D["bz"]["slot_r_clear"], 0.1 - 1e-6,
        f"rib r {bz['rib_r_in']:g}-{D['bz_bore_r']:g}, slot from r {D['rib_slot_r0']:g} out through the dial wall (r {ct['outer_r']:g})")
    gaps = []
    for a, cl, k in D["cart_ribs"]:
        from .parts.dial import rib_box, to_mech
        floor = to_mech(D, rib_box(D["rib_slot_r0"] + 0.05, ct["outer_r"] - 0.05, bz["rib_w"], D["rib_z0"] - 0.2, D["rib_z0"], a))
        gaps.append(bzs.distance_to(floor))
    row("cartridge key: ribs bottom in their slots (axial seat gap, max of three)", max(gaps), 0.001,
        f"rib bottoms = slot floors z {D['rib_z0']:.2f} ({bz['slot_depth']:g} under the land) [Ed 19:12 item 2]; three-point seat", higher_ok=False)
    row("cartridge key: bearing at the dial design torque vs PA-12 (MPa)", D["rib_bearing"], D["pa12_uts"] / 2,
        f"{D['dsp']['T_design']:g} mNm [A] -> {D['rib_F']:.1f} N on the key at r {(bz['rib_r_in'] + ct['outer_r']) / 2:.2f}, over "
        f"{bz['slot_depth']:g} x {D['rib_engage_r']:.2f}; PA-12 {D['pa12_uts']:g} MPa / 2", higher_ok=False)
    row("cartridge key: dial under the slot floor (MJF wall)", D["rib_floor_wall"], mjf["wall"],
        f"slot floor z {D['rib_z0']:.2f} over the flat underside z {D['z_lip0']:.2f}")
    row("plug / receptacle with the key seated: stand-off over full mate (the plug never carries the cartridge)", bz["plug_standoff"], 0.05,
        f"plug's flex z {D['plug_flex_z']:.2f} = board top {D['db_z1']:.2f} + mated {D['zp']['mated']:g} [S] + {bz['plug_standoff']:g} [A]; "
        f"still {D['plug_engage']:.2f} into the receptacle (≥ 0.2); pad glued with a {bz['plug_standoff']:g} shim, cartridge seated")
    row("plug / receptacle with the key seated: stand-off not over the contact wipe (mm)", bz["plug_standoff"], 0.15,
        "[A] 24-pin 0.4 B2B effective mating length ~0.3 class [C: the chosen part's]", higher_ok=False)


def _cart_tail(D, parts, r):
    row = r.row
    _cart_rows(D, parts, row)
    if D["dsp"]["on"]:
        _split_dial_rows(D, parts, row)
    row("dial up-stop: free lift to the rod-link board", D["dial_lift"], 0.1, "board clamped by the rod nut; 45° race carries the knob up-load into the dial")
    row("dial up-stop: free lift (max)", D["dial_lift"], 0.5, "", higher_ok=False)
    return _tail(D, parts, r)


def _tail(D, parts, r):
    T = D["tgt"]; row = r.row; TR = (-D["travel_deg"], 0, D["travel_deg"])
    if D["hall_layout"] == "vernier":
        row("Hall bar vs ring tips (radial)", D["skirt_id"] / 2 - D["hv_r_out"] - D["hv_pad_r"], T["arm_vs_ring"], f"outer magnet r {D['hv_r_out']:.2f}")
        tc = [parts[n] for n in parts if n.startswith("thrust")]
        if not D["tb_on"]:   # v0.19b [Ed 2 Nov]: no thrust bearing under the dial tube, just air
            row("dial tube end: air gap over the cradle (no thrust bearing)", D["dial_z_base"] - D["plate_t"], D["dial_air_min"],
                f"tube end z {D['dial_z_base']:.2f} over the cradle top {D['plate_t']:.2f}; the 45° race on the knob carries the dial, the adapter board stops the lift ({D['dial_lift']:.2f})")
        if tc:
            row("Hall spoke vs thrust balls / cage (±travel)", min_dist(list(posed(lambda t: hall.arm(D, t), TR).values()), tc), 0.3)
        row("Hall arm rib tip deflection at the load radius (mm)", _rib_defl(D), D["ha_rib_defl"],
            f"PA12 E {D['ha_rib_E']/1000:.1f} GPa, {D['ha_rib_load']:g} N in-plane at r {D['ha_rib_rload']:g}; "
            f"rib {D['ha_rib_w0']:g}→{D['ha_rib_w1']:g} wide, z {D['ha_rib_z_cage']:.1f} over the cage / {D['ha_rib_z_low']:.1f} beyond r {D['ha_rib_r_step']:.2f}, top {D['ha_rib_z_top']:.1f}",
            higher_ok=False)
    else:
        row("Hall paddle vs ring tips (radial)", D["ha_r_tip"] - D["ha_pad_r1"], 0.3)
    if D["hall_layout"] == "vernier" and D["fan_on"] and D["ad_r"] is not None:
        (_split_rows if D["arm_det"] == "split" else _arc_rows)(D, row)
    if D["kb_groove_h"] > 0:
        cr_, cz_ = D["kb_seat_c"]; px, pz = D["kb_seat_contact"]
        ang = math.degrees(math.atan2(cz_ - pz, px - cr_)) % 180          # contact -> groove centre direction
        row("seat: 45° contact line kept (|angle - 45|, deg)", abs(ang - 135.0) if ang > 90 else abs(ang - 45.0), 0.01,
            f"groove R{D['kb_seat_r']:g} centred {D['kb_seat_r'] - D['kb_ball_d'] / 2:.2f} past the ball centre on the 45° line", higher_ok=False)
        row("seat: groove rim half-width - ball chord at the cone face", D["kb_seat_w"] - D["kb_ball_cap_w"], 0.0,
            f"depth {D['kb_groove_h']:.3g}: groove ±{D['kb_seat_w']:.3f}, ball ±{D['kb_ball_cap_w']:.3f}")
        if D["kb_race"] == "chamfer" and D["dial_shape"] == "cone" and D.get("cart"):   # v0.24: the cone wall row is in _cart_rows
            row("dial: hub between the gap face and the well floor", D["z_well_top"] - D["z_hub0"], 1.5)
            row("dial: cone underside meets the flat underside inside the outer wall", D["ct"]["outer_r"] - D["cone_lip_r"], 1.0,
                f"cone to r {D['cone_lip_r']:.2f}, flat at z {D['z_lip0']:.2f} to r {D['ct']['outer_r']:g} (the v0.23 lip underside)")
        elif D["kb_race"] == "chamfer" and D["dial_shape"] == "cone":   # v0.21 [Ed 2 Nov]: straight parallel cones, no steps
            row("dial: cone wall (normal), parallel faces", D["cone_dial_wall"], 1.5,
                f"{D['cone_deg']:g}°; underside r {D['cone_under_r0']:.2f}–{D['cone_lip_r']:.2f}, top r {D['cone_well_r']:.2f}–{D['cone_seat_r']:.2f}")
            row("dial: material under the adapter-board corner (well floor to the underside)", D["cone_dial_corner"], 1.5,
                f"well Ø{2 * D['cone_well_r']:.2f}, floor z {D['z_well_top']:.2f}; race moved out {D['race_out']:g}, up {D['race_up']:.2f}")
            row("dial: hub between the gap face and the well floor", D["z_well_top"] - D["z_hub0"], 1.5)
            row("dial: cone underside meets the lip inside its outer chamfer", D["knob_od"] / 2 - D.get("sleeve_top_cout", 0.0) - D["cone_lip_r"], 1.0)
            row("dial: flat carrier seat under the carrier magnet pocket (inner wall)", D["carr_r"] - D["carr_mag"][0] / 2 - D["cone_seat_r"],
                D["carr_seat_wall"] - 1e-6, f"seat r {D['cone_seat_r']:.2f} out to the screen cut")
        if D["kb_race"] == "chamfer":
            row("dial: material under the cup-boss bore (above the hub bottom)", D["z_bore0"] - D["z_hub0"], D["dial_bore_floor"] - 1e-6,
                f"socket on the tube {D['hold_socket_len']:.2f}" if D["adapter_cup"] else "no cup: plain tube ID")
            row("seat: groove land to the 45° face ends (min)", D["kb_land"], T["race_land"],
                f"track at {D['kb_race_at']:g} of the {D['kb_face_len']:.2f} gusset face, both faces grooved")
        else:
            row("seat: ball vs dial plain tube (radial)", D["kb_ball_tube"], T["race_ball_tube"])
    return r
