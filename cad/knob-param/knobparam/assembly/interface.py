"""INTERFACE params - owned by the ASSEMBLY agent. Everything that crosses a sub-assembly boundary and is an independent
input lives here: frame/axis, gear standard + tooth counts + centres + angles, motor envelope, knob size chain (knob OD), mating
heights, the 45 deg cone-bearing definition, the screen choice envelope (SCREENS table), the Hall layout, and the check targets.
Frame: dial axis = Z, Z = height above the main-PCB FRONT, motor at +X (0 deg), encoder H2 at 270 deg (-Y).
Board coords (KiCad, mm): frame x = bx - axis_bx, frame y = -(by - axis_by).
Tags: [Ed] Ed's value, [K] KiCad, [S] datasheet/spec, [M] motor drawing, [A] assumed.
Sub-assemblies may READ every key of derive_interface() but never write one. Changing a value here is an interface change:
assembly agent only (see AGENTS.md)."""
import math

P = dict(
    # ---- main PCB [K] ----
    pcb_t=1.6,   # [K] KiCad board thickness (the KiCad STEP export is 1.51; --full uses it)
    axis_bx=25.25,   # [K] H1 = dial axis in board coords
    axis_by=52.9,   # [K] H1 = dial axis in board coords
    # ---- gears [Ed/A] ----
    module=0.5,   # [Ed] m0.5 everywhere
    pressure=20.0,   # [A]
    backlash=0.1,   # [A] tooth thinning (pinions) / space widening (rings)
    motor_offset=10.75,   # [Ed/K] dial axis to the 1220 motor axis; hub-gear teeth derived from it (snapped to whole teeth)
    z_motor_pinion=12,   # [A] 12T on the motor shaft (used when hub_gear_min is False)
    hub_gear_min=True,   # [Ed] v0.15d: smallest hub (sun) gear with tgt.race_wall over the knob bore; pinion = the rest of the centre distance
    z_enc_pinion=14,   # [A] 14T encoder pinion and idlers in the bottom ring
    enc_ang=270.0,   # [K] encoder pinion / H2 angle (90 deg from the motor)
    idler2_from_enc=-120.0,   # [A] idler 2 = encoder angle - 120 = 150 deg
    # ---- 1220 motor [M] ----
    motor=dict(title="Motor 1220 coreless planetary", body_d=12.0, motor_len=20.0, gearbox_len=17.0, boss_d=4.0, boss_len=1.0, shaft_d=3.0, shaft_flat=2.5, shaft_len=5.5, flat_len=4.5, seam_groove=0.3, endcap_len=1.5, endcap_d=11.0, rear_boss_d=3.0, rear_boss_len=0.6, term_w=1.2, term_t=0.3, term_len=2.5, term_pitch=6.0, mount_holes=None, ratio="1:144 (3-stage)", version="v0.1"),
    # ---- knob [Ed/A] ----
    skirt_clear=1.0,   # [Ed/A] motor can to the skirt ID / ring tips (v0.12: 1.0)
    knob_wall=2.0,   # [A] skirt wall (ring root to OD is what is left: flagged)
    skirt_gap=2.0,   # [Ed] bottom ring underside above the PCB front
    knob_run=0.3,   # [A] knob <-> dial running gap
    knob_hub_z0=39.6,   # [A] knob hub / hub-gear bottom
    hub_gear_face=4.4,   # [A] hub gear face (pinion 3.0 inside it)
    # ---- knob top bearing: opposed 45 deg faces, ball track grooved into both [Ed] ----
    kb_race="chamfer",   # [Ed] v0.15c: balls on the 45° dial-gusset / knob-chamfer faces ("tube" = v0.15 cone race at the dial tube)
    kb_race_at=0.5,   # [Ed] ball circle at this fraction along the 45° face (0.5 = the middle)
    kb_ball_d=1.0,   # [Ed] Ø1 steel balls
    kb_seat_r=0.52,   # [Ed] track groove radius (single-radius seat, centre on the 45° contact line); same in both faces
    kb_clear=0.25,   # [A] knob <-> dial radial elsewhere ("tube" race)
    kb_play=0.06,   # [A] minimum chord play for a full ring
    # ---- control dial [Ed/A] ----
    dial_tube_id=5.12,   # [Ed] dial tube Ø5.12/Ø8.12
    dial_tube_wall=1.5,   # [Ed] dial tube Ø5.12/Ø8.12
    travel_deg=5.5,   # [Ed/A] v0.16: dial ±5.5° = detent latch det_deg + overtravel onto the magnet cushions (v0.15: ±10)
    det_deg=5.0,   # [Ed] v0.16: dial latches ("cocked") at ±5° by the spring-ball detents
    # ---- brass tube, rod ----
    rod_d=1.6,   # [S]/[A]
    rod_pad_t=0.035,   # [K] v0.16: B.Cu VBUS pad under the bottom rod nut (1 oz); no washer [Ed]
    nut_m=1.3,   # [S]/[A]
    # ---- base cradle [A] ----
    plate_t=3.5,
    cr_floor=1.0,
    # ---- encoder take-off [A] ----
    pin_face=2.6,
    pinion_hub_d=3.5,
    pin_above_skirt=0.2,
    brg=dict(d=2.0, D=5.0, B=2.3, fd=6.1, ft=0.6),   # [S] F682ZZ envelope
    # ---- Hall array on the dial [Ed/A] ----
    ha_ang0=210.0,
    ha_ring_clear=0.5,
    ha_n=5,
    ha_mag=(2.0, 1.0),
    ha_mag_wall=0.4,
    ha_mag_edge=0.5,
    ha_pitch=12.0,
    ha_sens_h=1.12,
    ha_gap=1.2,
    ha_arm=(4.4, 1.5, 3.0, 3.0),
    ha_win_clear=0.5,
    # ---- idler 1 (v0.16: the 716 is no longer on this shaft) [A] ----
    idler1_ang=54.0,   # [A] idler 1 stays at the v0.13 angle (45.5 overlapped the Ø48 wheel)
    # ---- feel motor on the PCB top, inside the cradle [A] ----
    # Axial 716, its own pinion meshing the bottom internal ring. Angle and tooth count are derived
    # (the bisector of the idler gap that clears the 1220, the Hall arm and the skirt by the most).
    feel=dict(part="716 coreless", can_d=7.0, can_len=16.0, end_boss=1.0, end_boss_d=4.0, shaft_d=1.0,
              can_gap=0.3, clear=0.5, clip_frac=0.5, pad=(1.8, 1.8), pad_pitch=5.2, pad_hole=1.0, pad_t=0.15),
    # ---- screen holder + adapter ----
    adapter_t=1.0,   # [K]/[A] (cord room over the nut [Ed])
    cord_clear=3.0,   # [K]/[A] (cord room over the nut [Ed])
    # ---- screen [S] (table below) ----
    screen="rm69330-1.39",
    z_glass=56.8,   # [A] glass flush with the dial top (v0.12)
    z_holder0=54.9,   # [A] holder plate bottom (= v0.12 screen seat: cord room kept)
    cof_bend=None,   # [A] override the screen-table COF bend (radial), e.g. --set cof_bend=0.26
    # ---- v0.15: Hall vernier (arm down through the cradle slot, 5 magnets x 5 sensors, arcs crossing) ----
    hall_layout="vernier",   # [Ed] 'vernier' (v0.15) or 'sector' (v0.14)
    hv_n=5,   # [Ed] magnets = sensors per row
    hv_pitch=2.5,   # [Ed/A] v0.16: radial pitch of both rows spread out (v0.15: 2.2 = X2SON 1.4 + 0.8 copper gap)
    hv_cross_travel=None,   # [A] dial angle at which the crossing reaches the end pair (sets the arc curvature); None = travel_deg
    hv_mag=(1.5, 1.0),   # [A] Ø1.5 x 1.0 N52 axial, alternating poles
    hv_br=1.45,   # [S] N52 Br (T)
    hv_wall=0.4,   # [A] bar wall round each magnet pocket
    hv_gap=1.2,   # [A] sensor package top -> magnet face (air gap; 56 mT peak = 70% of BA3 range)
    hv_sensor=dict(part="TMAG5253BA3 (TI) X2SON-4", l=1.4, w=1.1, h=0.4, elem=0.13, bw_khz=15.0, s_mv_mt=15.0, range_mt=80.0, nd_nt=220.0, vcc=3.3),   # [S] datasheet; elem = Hall element below the package top [S]
    hv_ring_clear=0.5,   # [A] bar to the ring tips
    # ---- v0.16 dial mechanics [Ed]: fan arm off the dial hub, top-loaded spring-ball detents latching at ±det_deg on the fan
    # wings, a Ø1 ball track under each detent, two tangential extension springs centring the dial, tiny magnet end cushions ----
    fan_top=5.9,   # [A] fan / arm top (= v0.15 arm top)
    fan_r0_frac=0.78,   # [A] fan wing sector inner radius as a fraction of the cradle radius (wings at the perimeter)
    fan_ring_clear=1.0,   # [A] fan outer edge to the ring tips
    fan_clear=0.3,   # [A] fan wing (swept) to the pinion tips / detent legs
    det_ball=1.5,   # [Ed/A] detent ball (a bit bigger than the Ø1 race balls)
    det_dimple=0.25,   # [A] dimple depth in the wing top (spherical seat) at ±det_deg
    det_gap=0.3,   # [A] detent block underside above the fan top
    det_r_frac=0.5,   # [A] detent radius at this fraction across the wing (0 = inner edge, 1 = outer)
    bt_ball=1.0,   # [Ed] Ø1 balls in the track under each detent
    bt_up=0.3,   # [A] ball centre above the cradle plate (fan underside another bt_up above it)
    bt_groove_r=0.55,   # [A] groove radius in the plate and in the wing underside
    bt_rows=2,   # [A] concentric track rows under each detent (one ball per row)
    bt_row_pitch=1.4,   # [A] radial pitch of the rows (groove 1.1 + 0.3 land)
    sl_ang=276.0,   # [A] spring lever angle (clear of the Hall window, 1220 collar and encoder pocket)
    sl_r=8.6,   # [A] lever end radius
    sl_w=2.4,   # [A] lever width
    sl_z0=4.0,   # [A] lever end-block bottom (the bar near the hub stays above the thrust cage)
    sl_top=6.8,   # [A] lever + stop-block top; springs run above it
    sl_pin_r=7.0,   # [A] spring hook pin on the lever top
    sl_pin_d=0.8,   # [A]
    sl_spring=(1.2, 4.5, 0.15),   # [A] extension spring OD, hook-to-hook length, wire (non-magnetic: phosphor bronze / 316)
    sl_spring_gap=0.2,   # [A] spring coil above the lever / blocks
    cu_mag=(1.5, 0.5),   # [Ed/A] tiny weak N52 cushion magnets (repelling), axis tangential
    cu_mag_r=7.8,   # [A] cushion magnet radius on the lever end
    cu_stray_max=0.03,   # [A] cushion stray field at the nearest Hall-row sensor / sensor range
    # ---- v0.16 knob size [Ed]: the least OD that clears the AMOLED ledge + COF bend with a printable lip wall all round ----
    nozzle=0.4,   # [A] printer nozzle (line width)
    lip_wall_lines=2,   # [Ed] thinnest lip wall = 2 lines (0.8): far side AND outside the COF-bend pocket (lip is a closed ring)
    bend_clear=0.1,   # [A] COF bend / ledge to the lip pocket wall
    knob_od_step=0.01,   # [A] knob OD rounded up to this
    # ---- v0.16 relative knob-vs-dial angle [Ed]: diametric ring magnet in the knob (blue), 3D TMAG5273 on a sensor board in the
    # control dial (purple), so the sensor reads the knob angle relative to the dial (v0.15: Ø3×1 dial magnet under a fixed U3) ----
    tm_ring=(19.0, 21.0, 0.5),   # [A] tiny N52 ring (0.24 g) ID, OD, thickness, magnetised DIAMETRICALLY (any 360° knob angle), top flush in the knob under-web
    tm_ang=0.0,   # [A] sensor angle on the dial (+X: clear of the fold window, strap and carrier pin/magnet)
    tm_floor=0.4,   # [A] dial floor under the sensor (one printed layer stack); air gap = floor + knob_run + element height
    tm_pkg=(1.6, 2.9, 1.45, 0.8),   # [S] SOT-23-6 w, l, h, Hall element above the package face (sensor face-down on the board underside)
    tm_range_mt=80.0,   # [S] TMAG5273A1 ±40 / ±80 mT: ±80 used
    # ---- check targets (minimum gaps) [A] ----
    tgt=dict(knob_od_vs_screen=0.0, tab_vs_rim=0.5, hall_vs_pinions=0.3, race_wall=1.0, lip_wall=0.4, back_panel_max=26.0, clash_mm3=1e-3, idler_motor=0.5, motor_dial_tube=0.5, arm_vs_cradle=0.3, arm_vs_ring=0.3, sensor_gap=0.2, sensor_vs_cradle=0.2, strap_vs_parts=0.2, seat_vs_knob=0.2, carrier_vs_cup=0.2, race_ball_tube=0.05, race_land=0.2),
)

# screens table (screen choice envelope; library SPECs): od = round outline, r_edge = ledge/chin edge from the panel centre,
# rigid = chin cannot fold
SCREENS = {
    "gc9a01-1.28": dict(spec="screens/gc9a01-1.28/SPEC.md", od=35.6, r_edge=20.30, ledge_w=15.0, t=1.55, bend=0.3,
                        fold=(20.0, 11.4, 0.7), b2b=None, rigid=True, iface="4-wire SPI, 3.3 V"),   # chin rigid glass [S]
    "gc9c01-1.32": dict(spec="screens/gc9c01-1.32/SPEC.md", od=35.98, r_edge=20.55, ledge_w=12.0, t=1.66, bend=0.3,
                        fold=(23.85, 14.0, 0.7), b2b=(5.0, 2.6, 0.9), rigid=True, iface="QSPI (Osptek) / SPI"),
    "rm69330-1.39": dict(spec="screens/rm69330-1.39/SPEC.md", od=38.21, r_edge=19.725, ledge_w=12.0, t=0.664, bend=0.30,
                         fold=(25.11, 14.0, 1.10), b2b=(5.0, 2.6, 0.9), rigid=False, iface="4-wire SPI (+MIPI 1-lane), VDDIO 1.8 V",
                         stack=(0.134, 0.20, 0.20, 0.13), d_pol=37.71, encap_flat=37.79, d_tape=37.61),
}


def bend_reach(S, off, n=48):
    """Furthest point of the screen ledge + COF bend from the dial axis, panel centre offset `off` AWAY from the FPC exit.
    Bend = band r_edge..r_edge+bend over |y| <= ledge_w/2 - 2 (cof_inset); ledge corners on the r_edge arc at |y| = ledge_w/2."""
    pts = [(S["r_edge"], S["ledge_w"] / 2)]
    if not S["rigid"]:
        h = S["ledge_w"] / 2 - 2.0
        pts += [(S["r_edge"] + S["bend"], -h + 2 * h * i / n) for i in range(n + 1)]
    return max(math.hypot(math.sqrt(max(rho * rho - y * y, 0)) - off, y) for rho, y in pts)


def _screen_knob(S, wall, clear, step=0.0005):
    """Panel offset that balances the far-side lip wall against the wall outside the bend pocket, and the knob OD it needs."""
    best = None
    for i in range(int(3.0 / step)):
        off = i * step
        R = max(S["od"] / 2 + off, bend_reach(S, off) + clear) + wall
        if best is None or R < best[1] - 1e-12: best = (off, R)
    return best[0], 2 * best[1]


def _hall_clear(D, x, y, rad):
    """Plan clearance of a circle to the Hall arm swept over ±travel. The spoke width lives in control_dial, so the
    spoke is padded by feel.clear on top of the pad radius (conservative versus the real 3 mm spoke)."""
    worst = 1e9
    T = D["travel_deg"]
    def eat(px, py, rr):
        nonlocal worst
        worst = min(worst, math.hypot(x - px, y - py) - rr - rad)
    if D["hall_layout"] == "vernier":
        pr = D["hv_pad_r"]; spoke = pr + D["feel"]["clear"]
        for th in (-T, 0.0, T):
            pts = []
            for r, a in zip(D["hv_r"], D["hv_phi_m"]):
                px, py = r * math.cos(math.radians(a + th)), r * math.sin(math.radians(a + th))
                pts.append((px, py)); eat(px, py, pr)
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                for i in range(1, 8):
                    t = i / 8.0; eat(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, pr)
            a0 = math.radians(D["hv_phi_m"][0] + th)
            r_in, r_out = D["dial_tube_od"] / 2, D["hv_r"][0]
            for i in range(9):
                r = r_in + (r_out - r_in) * i / 8.0
                eat(r * math.cos(a0), r * math.sin(a0), spoke)
    else:
        r0, r1, half = D["ha_pad_r0"], D["ha_pad_r1"], D["ha_pad_half"] + T
        for i in range(7):
            r = r0 + (r1 - r0) * i / 6.0
            for j in range(9):
                a = math.radians(D["ha_ang0"] - half + 2 * half * j / 8.0)
                eat(r * math.cos(a), r * math.sin(a), D["feel"]["clear"])
    return worst


def _feel_clearance(D, z, ang):
    """Running clearances for an axial feel motor whose pinion (z teeth) meshes the bottom internal ring at angle ang.
    All inputs are interface values. Returns (worst, parts, xy, centre distance, tip radius)."""
    F = D["feel"]; m = D["module"]; can_r = F["can_d"] / 2
    tip = (z + 2) * m / 2
    cd = (D["z_ring"] - z) * m / 2
    x, y = cd * math.cos(math.radians(ang)), cd * math.sin(math.radians(ang))
    dial_r, skirt_r, body_r = D["dial_tube_od"] / 2, D["skirt_id"] / 2, D["can_r"]
    d_body = math.hypot(x - D["offset"], y)
    parts = {
        "skirt": skirt_r - cd - can_r,
        "dial_can": cd - can_r - dial_r,
        "dial_pin": cd - tip - dial_r,
        "body_can": d_body - body_r - can_r,
        "body_pin": d_body - body_r - tip,
    }
    gear = 1e9
    for a in (D["enc_ang"], *D["idler_angs"]):
        px, py = D["enc_cd"] * math.cos(math.radians(a)), D["enc_cd"] * math.sin(math.radians(a))
        gear = min(gear, math.hypot(x - px, y - py) - D["d_pin_tip"] / 2 - tip)
    parts["gear"] = gear
    parts["hall"] = _hall_clear(D, x, y, tip)
    return min(parts.values()), parts, (x, y), cd, tip


def _place_feel(D):
    """Axial 716 on the PCB-top side, pinion meshing the bottom ring (one mesh, torque into the knob).

    The three bottom-ring pinions (two idlers + encoder) split the circle into three gaps. In a gap between two
    equal pinions the clearance-balancing angle is the bisector. Pick the bisector whose best whole-tooth pinion
    maximises the worst running clearance (skirt, dial tube, 1220 can, the other pinion tips, the Hall arm).
    Ties break toward fewer pinion teeth (more reduction)."""
    angs = sorted({D["enc_ang"], *D["idler_angs"]})
    gaps = list(zip(angs, angs[1:] + [angs[0] + 360.0]))
    best = None
    for a0, a1 in gaps:
        ang = ((a0 + a1) / 2.0) % 360.0
        for z in range(8, 42):
            mn, parts, xy, cd, tip = _feel_clearance(D, z, ang)
            key = (mn, -z)
            if best is None or key > best[0]:
                best = (key, ang, z, parts, xy, cd, tip)
    _, ang, z, parts, xy, cd, tip = best
    p = D["feel"]["pad_pitch"] / 2.0
    tx, ty = -math.sin(math.radians(ang)), math.cos(math.radians(ang))
    D["z_feel"] = z
    D["fm_ang"] = ang
    D["fm_cd"] = cd
    D["fm_xy"] = xy
    D["fm_tip"] = tip
    D["fm_ratio"] = D["z_ring"] / z
    D["fm_clear"] = parts
    D["fm_pad_xy"] = [(xy[0] + tx * p, xy[1] + ty * p), (xy[0] - tx * p, xy[1] - ty * p)]


def _place_mech(D):
    """v0.16 fan wings + detents (angles from the Hall window and the pinions, so they follow any layout change)."""
    R2D = math.degrees; T = D["travel_deg"]; c = D["fan_clear"]
    D["cr_r_out"] = D["skirt_id"] / 2 - 0.5                                 # (= base_drive r_out with cr_clear 0.5)
    D["fan_r1"] = D["skirt_id"] / 2 - D["fan_ring_clear"]
    D["fan_r0"] = D["fan_r0_frac"] * D["cr_r_out"]
    D["fan_z0"] = D["plate_t"] + 2 * D["bt_up"]
    # Hall window edge at the wing radii (outer pads, swept +-travel, slot clear 0.5 [base_drive default])
    win = 0.0
    if D["hall_layout"] == "vernier":
        for r, a in zip(D["hv_r"], D["hv_phi_m"]):
            if r + D["hv_pad_r"] < D["fan_r0"] - 1e-6: continue
            r0 = r - D["hv_pad_r"] - 0.5
            win = max(win, abs(a - D["ha_ang0"]) + T + R2D(math.asin(min((D["hv_pad_r"] + 0.5) / r0, 1))))
    # nearest bottom-ring pinion either side of the Hall arm
    gap = min(min((a - D["ha_ang0"]) % 360, (D["ha_ang0"] - a) % 360) for a in (D["enc_ang"], *D["idler_angs"]))
    rm = (D["fan_r0"] + D["fan_r1"]) / 2
    pin_half = R2D(math.asin(min((D["d_pin_tip"] / 2 + c) / D["enc_cd"], 1)))
    D["fan_w1"] = gap - pin_half - T                                        # fan sector edge (swept clear of the pinions)
    D["fan_half"] = D["fan_w1"]
    D["det_r"] = D["fan_r0"] + D["det_r_frac"] * (D["fan_r1"] - D["fan_r0"])
    n = D["bt_rows"]; D["bt_rs"] = [D["det_r"] + (i - (n - 1) / 2) * D["bt_row_pitch"] for i in range(n)]
    rmin = min(D["bt_rs"])
    D["bt_half"] = T / 2 + R2D((D["bt_ball"] / 2 + 0.1) / rmin)             # groove half-span: the ball rolls travel/2
    # detent angle: track groove (plate) clear of the Hall window by 0.5 wall, plunger + ball inside the fan at -travel
    D["det_lo"] = win + R2D((0.5 + D["bt_groove_r"]) / rmin) + D["bt_half"]
    D["det_hi"] = D["fan_half"] - T - R2D(D["det_ball"] / 2 / D["det_r"])
    D["det_off"] = (D["det_lo"] + D["det_hi"]) / 2
    D["det_angs"] = [D["ha_ang0"] - D["det_off"], D["ha_ang0"] + D["det_off"]]
    D["hall_win_out"] = win
    D["bt_z"] = D["plate_t"] + D["bt_up"]
    D["sl_pin_top"] = D["sl_top"] + D["sl_spring_gap"] + D["sl_spring"][0] + 0.4   # spring coil above the lever, pin a bit above
    D["cu_z"] = (D["sl_z0"] + D["sl_top"]) / 2                                     # cushion magnet centre height (lever end block)


def derive(D):
    """Interface-derived values (pure function of the interface params). Adds keys to D in place."""
    m = D["module"]; R2D = math.degrees
    # ---- motor + knob size chain ----
    M = D["motor"]; D["can_r"] = M["body_d"] / 2
    zsum = int(round(2 * D["motor_offset"] / m))                        # hub + pinion teeth at this centre distance
    if D["hub_gear_min"]:   # hub gear pushed in to the axle: root wall over the knob bore (dial tube + kb_clear) >= tgt.race_wall
        r_bore = D["dial_tube_id"] / 2 + D["dial_tube_wall"] + D["kb_clear"]
        D["z_hub_gear"] = int(math.ceil(2 * (r_bore + D["tgt"]["race_wall"]) / m + 2.5 - 1e-9))
        D["z_pinion"] = zsum - D["z_hub_gear"]
    else:
        D["z_pinion"] = D["z_motor_pinion"]
        D["z_hub_gear"] = zsum - D["z_pinion"]
    D["offset"] = (D["z_hub_gear"] + D["z_pinion"]) * m / 2        # snapped to whole teeth
    need_id = 2 * (D["offset"] + D["can_r"] + D["skirt_clear"])
    # v0.16: the screen sets the knob OD (closed lip ring, lip_wall_lines x nozzle outside the panel AND outside the COF bend)
    D["lip_wall_min"] = D["lip_wall_lines"] * D["nozzle"]
    D["tgt"] = dict(D["tgt"], lip_wall=D["lip_wall_min"])
    D["scr_off_opt"], D["knob_od_min"] = _screen_knob(dict(SCREENS[D["screen"]], **({} if D["cof_bend"] is None else {"bend": D["cof_bend"]})),
                                                      D["lip_wall_min"], D["bend_clear"])
    z_scr = int(math.floor((D["knob_od_min"] - 2 * D["knob_wall"]) / m + 2 + 1e-9))   # biggest ring that keeps knob_wall
    D["z_ring"] = max(int(math.ceil(need_id / m + 2 - 1e-9)), z_scr)    # bottom internal ring: tip Ø = skirt ID
    D["skirt_id"] = (D["z_ring"] - 2) * m
    st = D["knob_od_step"]
    D["knob_od"] = max(D["skirt_id"] + 2 * D["knob_wall"], math.ceil(D["knob_od_min"] / st - 1e-9) * st)
    D["skirt_wall"] = (D["knob_od"] - D["skirt_id"]) / 2
    D["R"] = D["knob_od"] / 2
    D["enc_cd"] = (D["z_ring"] - D["z_enc_pinion"]) * m / 2
    D["ratio_knob_motor"] = D["z_hub_gear"] / D["z_pinion"]
    D["d_pin_tip"] = (D["z_enc_pinion"] + 2) * m
    D["h_skirt0"] = D["skirt_gap"]
    D["h_band1"] = D["knob_hub_z0"] + D["hub_gear_face"]
    # ---- angles / gear centres ----
    D["idler_angs"] = [D["idler1_ang"], (D["enc_ang"] + D["idler2_from_enc"]) % 360]
    xy = lambda a, r=None: ((D["enc_cd"] if r is None else r) * math.cos(math.radians(a)), (D["enc_cd"] if r is None else r) * math.sin(math.radians(a)))
    D["enc_xy"] = xy(D["enc_ang"]); D["idler_xy"] = [xy(a) for a in D["idler_angs"]]
    D["spacing"] = sorted([(D["idler_angs"][0] - D["enc_ang"]) % 360, (D["idler_angs"][1] - D["idler_angs"][0]) % 360, (D["enc_ang"] - D["idler_angs"][1]) % 360])
    # ---- screen envelope ----
    S = dict(SCREENS[D["screen"]]); D["S"] = S
    if D["cof_bend"] is not None: S["bend"] = D["cof_bend"]
    # ---- mating heights ----
    D["z_top"] = D["z_glass"]
    D["z_board_top"] = D["z_holder0"] - D["nut_m"] - D["cord_clear"]      # adapter board top (50.60)
    D["z_floor"] = D["z_board_top"] - D["adapter_t"]                       # 49.60 = brass tube top = adapter seat
    D["z_rod_top"] = D["z_board_top"] + D["nut_m"]
    D["z_pcb_back"] = -D["pcb_t"]
    D["h_pin0"] = D["h_skirt0"] + D["pin_above_skirt"]; D["h_pin1"] = D["h_pin0"] + D["pin_face"]   # pinion band in the bottom ring
    # ---- dial tube + 45 deg cone bearing (shared by main_knob and control_dial) ----
    D["dial_tube_od"] = D["dial_tube_id"] + 2 * D["dial_tube_wall"]
    D["kb_rt"] = D["dial_tube_od"] / 2
    # the ball circle itself (kb_rc, kb_zc, kb_n, faces kb_c_dial / kb_c_knob, grooves) is derived by control_dial, which owns the
    # dial face the balls run on, and EXPORTED to main_knob (v0.15c: the 45° face is the dial gusset under the web)
    # ---- Hall layout (dial magnets / cradle slot / PCB sensors) ----
    D["ha_r_tip"] = D["skirt_id"] / 2
    D["ha_pad_r1"] = D["ha_r_tip"] - D["ha_ring_clear"]
    D["ha_r_m"] = D["ha_pad_r1"] - D["ha_mag_wall"] - D["ha_mag"][0] / 2
    D["ha_pad_r0"] = D["ha_r_m"] - D["ha_mag"][0] / 2 - D["ha_mag_wall"] - 0.1
    D["ha_z_mag0"] = D["ha_sens_h"] + D["ha_gap"]
    D["ha_arm_z1"] = D["ha_arm"][0] + D["ha_arm"][1]
    D["ha_mag_angs"] = [(i - (D["ha_n"] - 1) / 2) * D["ha_pitch"] for i in range(D["ha_n"])]
    D["ha_sens_angs"] = [D["ha_ang0"] - 0.75 * D["ha_pitch"], D["ha_ang0"] + 0.75 * D["ha_pitch"]]
    D["ha_pad_half"] = D["ha_mag_angs"][-1] + R2D((D["ha_mag"][0] / 2 + D["ha_mag_edge"]) / D["ha_r_m"])
    D["ha_win_half"] = D["ha_pad_half"] + D["travel_deg"] + R2D(D["ha_win_clear"] / D["ha_pad_r0"])
    D["ha_win_r0"] = D["ha_pad_r0"] - D["ha_win_clear"]
    if D["hall_layout"] == "vernier":
        n, p = D["hv_n"], D["hv_pitch"]; md, mh = D["hv_mag"]; sw = D["hv_sensor"]
        D["hv_pad_r"] = md / 2 + D["hv_wall"]
        D["hv_r_out"] = D["skirt_id"] / 2 - D["hv_ring_clear"] - D["hv_pad_r"]   # outer magnet as far out as the ring allows
        D["hv_r"] = [D["hv_r_out"] - (n - 1 - i) * p for i in range(n)]
        D["hv_r_mid"] = sum(D["hv_r"]) / n
        span = (n - 1) / 2 * p
        D["hv_cross"] = D["travel_deg"] if D["hv_cross_travel"] is None else D["hv_cross_travel"]
        D["hv_g"] = D["hv_cross"] / (2 * span) if span else 0.0       # deg/mm: magnets +g, sensors -g (arcs cross)
        D["hv_phi_m"] = [D["ha_ang0"] + D["hv_g"] * (r - D["hv_r_mid"]) for r in D["hv_r"]]
        D["hv_phi_s"] = [D["ha_ang0"] - D["hv_g"] * (r - D["hv_r_mid"]) for r in D["hv_r"]]
        D["hv_z_elem"] = sw["h"] - sw["elem"]
        D["hv_z_mag0"] = sw["h"] + D["hv_gap"]
        D["hv_elem_gap"] = D["hv_z_mag0"] - D["hv_z_elem"]
    _place_feel(D)
    _place_mech(D)
    # ---- v0.16 knob ring magnet / dial sensor ----
    D["tm_r"] = (D["tm_ring"][0] + D["tm_ring"][1]) / 4                  # sensor element over the ring mid radius
    D["tm_xy"] = (D["tm_r"] * math.cos(math.radians(D["tm_ang"])), D["tm_r"] * math.sin(math.radians(D["tm_ang"])))
    return D
