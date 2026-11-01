"""INTERFACE params - owned by the ASSEMBLY agent. Everything that crosses a sub-assembly boundary and is an independent
input lives here: frame/axis, gear standard + tooth counts + centres + angles, motor envelope, knob size chain (knob OD), mating
heights, the 45 deg cone-bearing definition, the screen choice envelope (SCREENS table), the Hall layout, and the check targets.
Frame: dial axis = Z, Z = height above the main-PCB FRONT, motor at +X (0 deg), encoder H2 at 270 deg (-Y).
Board coords (KiCad, mm): frame x = bx - axis_bx, frame y = -(by - axis_by).
Tags: [Ed] Ed's value, [K] KiCad, [S] datasheet/spec, [M] motor drawing, [A] assumed.
Sub-assemblies may READ every key of derive_interface() but never write one. Changing a value here is an interface change:
assembly agent only (see AGENTS.md)."""
import math
from ..common.util import tooth_tip

P = dict(
    # ---- main PCB [K] ----
    pcb_t=1.6,   # [K] KiCad board thickness (the KiCad STEP export is 1.51; --full uses it)
    axis_bx=25.25,   # [K] H1 = dial axis in board coords
    axis_by=52.9,   # [K] H1 = dial axis in board coords
    # ---- gears [Ed/A] ----
    # v0.18: printed ring + encoder/idler pinions are 25° herringbone (module derived, coarsest that fits).
    # Only the two motor shafts carry bought straight pinions, meshing straight printed gears.
    module=0.5,   # [A] legacy spur module; the herringbone normal module (hb_mn) and hub_mod replace it. Kept so a --set still parses.
    pressure=20.0,   # [A] spur pressure angle (RW and Tempero catalogue pinions are 20°)
    backlash=0.1,   # [A] leftover spur default; herringbone uses hb_backlash, nylon spur meshes use brass_backlash (name kept)
    motor_offset=10.75,   # [Ed/K] dial axis to the 1220 motor axis (KiCad). The mesh centre distance is hub_cd.
    z_motor_pinion=12,   # unused in v0.18 (the pinion is the RW catalogue tooth count hub_z_pin)
    hub_gear_min=True,   # unused in v0.18; the hub tooth count is the one in hub_ratio closest to motor_offset
    z_enc_pinion=14,   # overwritten: herringbone pinion tooth count (encoder, both idlers, the compound's small gear)
    # ---- v0.18 printed herringbone [Ed] ----
    hb_beta=25.0,   # [Ed] helix angle. The internal ring is split so the herringbone can be assembled.
    hb_pressure=20.0,   # [A] normal pressure angle. 25° points a 12T tip under the MJF tooth floor; Ed's 12-tooth interference floor is hb_z_min.
    hb_addendum=0.80,   # [A] stub addendum (both printed members) so the pinion tip stays above hb_tooth_min after backlash
    hb_dedendum=1.25,   # [A] standard dedendum: root clearance for unsintered powder
    hb_backlash=0.10,   # [A] total circumferential play of the printed pair (each member takes half)
    hb_z_min=12,   # [Ed] minimum pinion teeth inside the ring (interference at 25° helix; classical spur undercut is ~17 virtual teeth)
    hb_tooth_min=0.50,   # [A] MJF tooth-tip floor, mm (HP min wall 0.5; PCBWay general tolerance is ±0.25, which a gear tooth cannot absorb)
    hb_wall_min=1.0,   # [A] ring wall outside the tooth root (recommended; the process floor is 0.5)
    hb_gap=0.40,   # [A] axial split between the two ring halves (MJF parts that assemble want about this)
    hb_ratio_target=15.6,   # [Ed] feel train, Tempero 12T × printed gear × (ring / pinion)
    # ---- v0.18 bought pinions [Ed] ----
    hub_mod=0.6,   # [Ed] RW pinion module. The printed hub gear matches it and is straight, not herringbone.
    hub_z_pin=14,   # [Ed] RW0614, 3 mm bore. 15T (RW0615) is the other catalogue option; 14T is the one whose mesh sits on the KiCad motor.
    hub_ratio=(1.4, 1.6),   # [Ed] hub gear / pinion
    brass_backlash=0.10,   # [A] total pitch backlash of a nylon spur mesh, split half and half. Every gear is PA-12 [Ed].
    spur_addendum=0.80,   # [A] stub addendum on printed spur gears (hub, feel wheel) so the tip is as thick as this module allows
    spur_dedendum=1.25,   # [A] full dedendum; both members of a nylon spur mesh use the stub addendum
    # ---- v0.18 clear-resin caps [Ed]: UTR-8100, separate from the nylon gear, only where a face is free ----
    cap_t=0.40,   # [A] Fresnel disk thickness
    cap_step_h=0.16,   # [A] ring step height (SLA fine, still a real feature)
    cap_step_w=0.42,   # [A] ring step width
    cap_rings=3,   # [A]
    cap_fit_gap=0.04,   # [A] radial press clearance in the model (the real part is a press or a snap)
    cap_seat_gap=0.02,   # [A] axial seat gap in the model so the cap is not a clash with its gear
    cap_root_inset=0.25,   # [A] cap outside diameter sits this far inside the tooth root
    spur_tooth_min=0.30,   # [A] short-feature floor for those catalogue-module teeth (MJF can form ~0.3 mm in XY; 0.5 is the preferred wall)
    enc_ang=270.0,   # [K] encoder pinion / H2 angle (90 deg from the motor)
    idler2_from_enc=-120.0,   # [A] idler 2 = encoder angle - 120 = 150 deg
    # ---- 1220 motor [M] ----
    motor=dict(title="Motor 1220 coreless planetary", body_d=12.0, motor_len=20.0, gearbox_len=17.0, boss_d=4.0, boss_len=1.0, shaft_d=3.0, shaft_flat=2.5, shaft_len=5.5, flat_len=4.5, seam_groove=0.3, endcap_len=1.5, endcap_d=11.0, rear_boss_d=3.0, rear_boss_len=0.6, term_w=1.2, term_t=0.3, term_len=2.5, term_pitch=6.0, mount_holes=None, ratio="1:144 (3-stage)", version="v0.1"),
    # ---- knob [Ed/A] ----
    skirt_clear=1.0,   # [Ed/A] old motor-can preference. A root wall of knob_wall cannot keep this inside the fixed OD.
    ring_can_clear=0.5,   # [A] 1220 can to the ring tips after the band thickens inward. Same clearance as the cradle.
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
    travel_deg=5.5,   # overwritten in derive [Ed]: hard-stop angle. v0.17 = det_deg + the ball's bore play (see det_stop_clear)
    det_deg=10.0,   # [Ed] v0.17: dial latches at the centre and at both ends, ±10° (v0.16 was ±5°)
    det_stop_clear=0.10,   # [A] mm arc at the detent radius: hard stop past the seated end detent (ball bore play; the closest the ball allows)
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
    ha_body=(1.3, 2.92),   # [S] DRV5055 body, used only when hall_layout is not vernier
    ha_gap=1.2,
    ha_arm=(4.4, 1.5, 3.0, 3.0),
    ha_win_clear=0.5,
    # ---- idler 1 (v0.16: the 716 is no longer on this shaft) [A] ----
    idler1_ang=54.0,   # [A] idler 1 stays at the v0.13 angle (45.5 overlapped the Ø48 wheel)
    # ---- feel motor on the PCB top, inside the cradle [A] ----
    # Axial 716, its own pinion meshing the bottom internal ring. Angle and tooth count are derived
    # (the bisector of the idler gap that clears the 1220, the Hall arm and the skirt by the most).
    feel=dict(part="coreless Ø2", can_d=7.0, can_len=16.0, end_boss=1.0, end_boss_d=4.0, shaft_d=2.0,
              can_gap=0.3, clear=0.5, clip_frac=0.5, pad=(1.8, 1.8), pad_pitch=5.2, pad_hole=1.0, pad_t=0.15,
              saddle_rad=0.7),   # [Ed] shaft Ø2 for the Tempero pinion. Can is the 716 envelope [A]. saddle_rad = glue + band so the strap stays inside the skirt.
    # ---- screen holder + adapter ----
    adapter_t=1.0,   # [K]/[A] (cord room over the nut [Ed])
    cord_clear=3.0,   # [K]/[A] (cord room over the nut [Ed])
    # ---- screen [S] (table below) ----
    screen="rm69330-1.39",
    z_glass=56.8,   # [A] glass flush with the dial top (v0.12). This is the knob top the faceplate is measured from.
    knob_proud=18.0,   # [Ed] knob screen top above the faceplate front face
    faceplate_t=2.5,   # [Ed] faceplate thickness. Same resin wall as the one-piece case (sub/case-v01)
    z_holder0=54.9,   # [A] holder plate bottom (= v0.12 screen seat: cord room kept)
    cof_bend=None,   # [A] override the screen-table COF bend (radial), e.g. --set cof_bend=0.26
    # ---- v0.15: Hall vernier (arm down through the cradle slot, 5 magnets x 5 sensors, arcs crossing) ----
    hall_layout="vernier",   # [Ed] 'vernier' (v0.15) or 'sector' (v0.14)
    hv_n=5,   # [Ed] magnets = sensors per row
    hv_pitch=2.5,   # [Ed/A] v0.16: radial pitch of both rows spread out (v0.15: 2.2 = X2SON 1.4 + 0.8 copper gap)
    hv_cross_travel=None,   # [A] dial angle at which the crossing reaches the end pair (sets the arc curvature); None = travel_deg
    hv_mag=(1.5, 1.0),   # [A] Ø1.5 x 1.0 N52 axial, alternating poles (see hv_pol)
    hv_pol=(1, -1, 1, -1, 1),   # [Ed] v0.16b: magnet polarity, inner -> outer: +1 = N face down (toward the sensors), -1 = S: N/S/N/S/N
    hv_br=1.45,   # [S] N52 Br (T)
    hv_wall=0.4,   # [A] bar wall round each magnet pocket
    hv_gap=1.2,   # [A] sensor package top -> magnet face (air gap; 56 mT peak = 70% of BA3 range)
    hv_sensor=dict(part="TMAG5253BA3 (TI) X2SON-4", l=1.4, w=1.1, h=0.4, elem=0.13, bw_khz=15.0, s_mv_mt=15.0, range_mt=80.0, nd_nt=220.0, vcc=3.3),   # [S] datasheet; elem = Hall element below the package top [S]
    hv_ring_clear=0.5,   # [A] bar to the ring tips
    # v0.16b [Ed]: the MIDDLE row sensor is a 3D TMAG5273 (I2C; reads Bx/By/Bz of the middle magnet -> dial angle cross-check
    # in 3D); the other four stay TMAG5253 linear. Keep the 2.5 pitch. SOT-23-6 (DBV) is much taller than the X2SON, so the
    # magnet bar sits at max(5253 top + hv_gap, 5273 top + hv_gap_mid).
    hv_mid=dict(idx=2, part="TMAG5273A2 (TI) SOT-23-6 DBV", l=2.9, w=1.6, lead_w=2.8, h=1.45, elem_z=0.65, range_mt=133.0, lead_h=0.45, lead_inset=0.2),   # [S] body l×w, lead span, max height; elem_z = Hall element above the PCB [A]; lead_h / lead_inset = gull-wing proxy; A2 ±133/±266 mT (A1 ±40/±80 would saturate: Bz 84 mT at 1.10)
    hv_gap_mid=0.3,   # [A] TMAG5273 package top -> magnet face (min air gap; dial lift is stopped at 0.3 by the adapter board)
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
    sl_ang=296.0,   # [Ed] lever angle, between the detent ear and the 1220 collar at ±10.7°
    sl_r=7.4,   # [A] lever end radius. Kept short of the 1220 collar.
    sl_w=1.6,   # [Ed] v0.17: lever width. 2.4 swung into the 1220 collar at ±10°; 1.6 stays 0.3 clear.
    sl_z0=4.0,   # [A] lever end-block bottom (the bar near the hub stays above the thrust cage)
    sl_top=6.8,   # [A] lever + stop-block top; springs run above it
    sl_pin_r=7.0,   # [A] spring hook pin on the lever top
    sl_pin_d=0.8,   # [A]
    sl_spring=(1.2, 2.6, 0.15),   # [Ed] v0.17: OD, hook-to-hook, wire. Shorter than the v0.16 4.5 so the anchors clear the detent ears (non-magnetic: phosphor bronze / 316)
    sl_spring_gap=0.40,   # [A] v0.17: coil above the lever. The anchors sit 0.3 above the lever so ±travel sweeps under them.
    cu_on=False,   # [Ed] v0.17: cushion magnets removed (v0.16 had three Ø1.5×0.5 repelling cushions)
    cu_mag=(1.5, 0.5),   # [Ed/A] unused when cu_on is False (kept so a --set cu_on=True rebuilds v0.16)
    cu_mag_r=7.8,   # [A] cushion magnet radius on the lever end
    cu_stray_max=0.03,   # [A] cushion stray field at the nearest Hall-row sensor / sensor range
    # ---- v0.17 Hall-arm rib [Ed]: tapered spine on the sweeping arm, PA12 ----
    ha_rib_w0=3.0,   # [Ed] rib width at the hub
    ha_rib_w1=5.2,   # [Ed] rib width at the hammerhead (fan_r0) and on out to ha_rib_r1
    ha_rib_r1=17.0,   # [Ed] rib continues to this radius
    ha_rib_load=2.0,   # [Ed] N, tangential (in-plane) tip load for the deflection check
    ha_rib_rload=15.5,   # [Ed] radius of that load
    ha_rib_E=1700.0,   # [Ed] PA12 Young's modulus, N/mm² (1.7 GPa)
    ha_rib_defl=0.07,   # [Ed] mm, max in-plane deflection at ha_rib_rload
    # ---- outer thrust [Ed]: cageless, tracks only. Load balls Ø2 stainless; cheap glass spacers 1.5–1.6 ----
    ot_ball_d=2.0,   # [Ed] load ball, 316 or 440C stainless
    ot_spacer_min=1.5,   # [Ed] cheap loose glass, small end of the sieve (Cospheric P-BSGS 1.50 is the stock floor)
    ot_spacer_max=1.6,   # [Ed] large end. 1.588 is the other stock size and still sits inside this window
    ot_spacer_alt=1.588,   # [Ed] alternate stock glass, checked but not the modelled size
    ot_play=0.03,   # [A] extra chord at the LARGE spacer so it cannot jam
    ot_play_max=0.12,   # [A] largest chord gap still called "touching" at the SMALL spacer
    ot_ruby_n=4,   # [Ed] synthetic ruby accents, same diameter as the load balls
    ot_ruby_d=2.0,   # [Ed] ruby diameter (2.0 carries load; set equal to the spacer to accent a spacer)
    ot_seat_gap=0.05,   # [A] groove radius over the load-ball radius
    ot_land_min=1.0,   # [Ed] clear resin under the bottom track (groove bottom to the PCB front). The laser comes up through it; not a metal insert.
    ot_blank_clear=0.15,   # [A] keep-out blank stays this far off the ball, top and bottom
    ot_track_extra=0.4,   # [A] bottom track annulus past the groove, each side
    ot_axial_gap=0.30,   # [A] bottom track stays this far under the knob face if it would otherwise meet it
    ot_keep_ang=(124.0, 137.0),   # [Ed] C20–C22 / U20. A cageless ring cannot skip this; a printed blank fills it
    ot_keep_r=(18.0, 20.5),   # [Ed] radial band of that keep-out
    # ---- v0.18 feel stage [Ed]: 12T into a printed spur on the compound idler. Both nylon, tooth form of the Tempero 0.5M-12T. ----
    fg_mod=0.5,   # [Ed] module of that mesh. The herringbone stage is separate.
    fg_z_pin=12,   # [Ed] 0.5 module 12T
    fg_pinion=dict(part="nylon 0.5M-12T", vendor="printed PA-12", material="PA-12 MJF", bore=2.04, face=5.0, hub_d=0.0, hub_w=5.0, od=6.8,
                   note="tooth form of the Tempero 0.5M-12T (was the brass reference). Stub addendum, press on the Ø2 shaft. Straight spur, 20°."),
    fg_back_h=0.8,   # [K] tallest PCB-back part the big gear can sit over (U20 / C22)
    fg_clear=0.30,   # [A] big gear below those parts, and the encoder rim below the gear
    fg_hole=1.8,   # [A] PCB NPTH for the compound idler pin (Ø1.5 pin + clearance). KiCad still to add
    fm_shaft_hole=2.4,   # [A] PCB NPTH for the Ø2 feel shaft. KiCad still to add
    # ---- v0.16 knob size [Ed]: the least OD that clears the AMOLED ledge + COF bend with a printable lip wall all round ----
    nozzle=0.4,   # [A] printer nozzle (line width)
    lip_wall_lines=3,   # [Ed] v0.17: lip wall 3 lines = 1.2 mm, thickened outward (v0.16 was 2 lines / 0.8)
    print_wall_min=1.0,   # [Ed] v0.17: printed walls (lip far side and outside the bend pocket) at least this
    bend_clear=0.1,   # [A] COF bend / ledge to the lip pocket wall
    knob_od_step=0.01,   # [A] knob OD rounded up to this
    rel_sensor=False,   # [Ed] v0.16b: knob ring magnet + dial TMAG5273 REMOVED (duplicate of the encoder + Hall row). True = v0.16
    # ---- v0.16 relative knob-vs-dial angle [Ed] (only when rel_sensor): diametric ring magnet in the knob (blue), 3D TMAG5273 on a sensor board in the
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


def _place_hub(D):
    """RW m0.6 pinion, printed straight hub gear. Tooth count is the one inside hub_ratio whose mesh is closest to the KiCad motor."""
    m, zp = D["hub_mod"], D["hub_z_pin"]
    r_bore = D["dial_tube_id"] / 2 + D["dial_tube_wall"] + D["kb_clear"]
    z_lo = int(math.ceil(2 * (r_bore + D["tgt"]["race_wall"]) / m + 2 * D["spur_dedendum"] - 1e-9))
    lo, hi = D["hub_ratio"]
    best = None
    for z in range(max(z_lo, int(math.ceil(lo * zp - 1e-9))), int(math.floor(hi * zp + 1e-9)) + 1):
        cd = (z + zp) * m / 2
        key = (abs(cd - D["motor_offset"]), abs(z / zp - 0.5 * (lo + hi)))
        if best is None or key < best[0]:
            best = (key, z, cd)
    _, z, cd = best
    D["z_pinion"] = zp
    D["z_hub_gear"] = z
    D["hub_cd"] = cd
    D["offset"] = D["motor_offset"]                 # the motor stays on the KiCad axis
    D["hub_cd_err"] = D["offset"] - cd              # negative: mesh is tight of the KiCad axis
    D["ratio_knob_motor"] = z / zp
    D["hub_tip_th"] = tooth_tip(z, m, D["pressure"], D["brass_backlash"] / 2, D["spur_addendum"])
    D["hub_pin_tip_r"] = zp * m / 2 + D["spur_addendum"] * m


def _motor_room(enc, ang, cd, tip_r, D):
    """Best radial clearance of the feel can placed `cd` from the idler at (enc, ang). Ignores the Hall arm (not laid out yet)."""
    ix = enc * math.cos(math.radians(ang)); iy = enc * math.sin(math.radians(ang))
    can_r = D["feel"]["can_d"] / 2
    best = -1e9
    for k in range(0, 360, 3):
        x = ix + cd * math.cos(math.radians(k)); y = iy + cd * math.sin(math.radians(k))
        r = math.hypot(x, y)
        worst = min(tip_r - r - can_r, r - can_r - D["dial_tube_od"] / 2,
                    math.hypot(x - D["motor_offset"], y) - D["can_r"] - can_r)
        if worst > best: best = worst
    return best


def _place_herringbone(D, R):
    """Coarsest normal module whose 25° herringbone keeps the root-to-skin wall at least the main knob wall
    (a bit thicker when the race seat allows), clears the 1220 by the cradle clearance, keeps hb_z_min teeth,
    and whose feel train can reach hb_ratio_target. The outer radius R is fixed: the teeth move inward."""
    beta, pa = D["hb_beta"], D["hb_pressure"]
    ha, ded = D["hb_addendum"], D["hb_dedendum"]
    cosb = math.cos(math.radians(beta))
    rg = D["ot_ball_d"] / 2 + D["ot_seat_gap"]
    D["ot_groove_depth"] = 2 * rg                                          # full radial depth of the race groove
    # a bit thicker than the main wall; the extra fraction is the race seat gap over the ball (no new millimetre)
    D["ring_wall_ratio"] = 1.0 + D["ot_seat_gap"] / D["ot_ball_d"]
    D["ring_wall_req"] = D["knob_wall"] * D["ring_wall_ratio"]
    D["ring_wall_race_req"] = D["knob_wall"] + D["ot_groove_depth"]        # main wall plus the full groove depth
    # the 1.0 mm skirt clearance cannot coexist with that wall inside the fixed OD; the floor is the cradle clearance
    tip_min = D["motor_offset"] + D["can_r"] + D["ring_can_clear"]
    dial_r = D["dial_tube_od"] / 2
    keep = 2.5 + D["feel"]["clear"]
    idler_ang = max((D["idler1_ang"], (D["enc_ang"] + D["idler2_from_enc"]) % 360),
                    key=lambda a: min((a - 0.0) % 360.0, (0.0 - a) % 360.0))
    cands = []
    for mn_i in range(120, 49, -1):               # 1.20 mm down to 0.50, 0.01 mm
        mn = mn_i / 100
        mt = mn / cosb
        pitch_max = R - D["ring_wall_req"] - ded * mn
        pitch_min = tip_min + ha * mn
        if pitch_max < pitch_min:
            continue
        for zp in range(D["hb_z_min"], D["hb_z_min"] + 12):
            if tooth_tip(zp, mn, pa, D["hb_backlash"] / 2, ha, beta) < D["hb_tooth_min"]:
                continue
            zr_lo = int(math.ceil(2 * pitch_min / mt - 1e-9))
            zr_hi = int(math.floor(2 * pitch_max / mt + 1e-9))
            for zr in range(max(zr_lo, zp + 8), zr_hi + 1):
                pr = zr * mt / 2
                tip_r, root_r = pr - ha * mn, pr + ded * mn
                wall = R - root_r
                if tip_r < tip_min or wall < D["ring_wall_req"]:
                    continue
                pp = zp * mt / 2
                enc = pr - pp
                if enc - (pp + ha * mn) - dial_r < 0.4:
                    continue
                zmax = int(math.floor((enc - keep) / (D["fg_mod"] / 2) - 2 * D["spur_addendum"] + 1e-9))
                if zmax < D["fg_z_pin"] + 8:
                    continue
                zbig = min(range(max(D["fg_z_pin"] + 4, zmax - 8), zmax + 1),
                           key=lambda z: abs(z / D["fg_z_pin"] * zr / zp - D["hb_ratio_target"]))
                total = (zbig / D["fg_z_pin"]) * (zr / zp)
                cd = (zbig + D["fg_z_pin"]) * D["fg_mod"] / 2
                if _motor_room(enc, idler_ang, cd, tip_r, D) < D["feel"]["clear"]:
                    continue
                cands.append((mn, total, zp, zr, zbig, wall, enc, tip_r, root_r, mt))
    # prefer a band that also holds the full race groove; otherwise the thickest wall that is still past the main wall
    full = [c for c in cands if c[5] >= D["ring_wall_race_req"] - 1e-9]
    pool = full or cands
    near = [c for c in pool if abs(c[1] - D["hb_ratio_target"]) <= 0.5]
    pool = near or pool
    if not pool:
        raise ValueError("no herringbone module fits the fixed OD, the main wall and the feel ratio")
    # coarsest module, then the thickest root wall, then the ratio closest to the target
    best = max(pool, key=lambda c: (c[0], c[5], -abs(c[1] - D["hb_ratio_target"])))
    mn, total, zp, zr, zbig, wall, enc, tip_r, root_r, mt = best
    D["hb_mn"] = mn
    D["hb_mt"] = mt
    D["z_enc_pinion"] = zp
    D["z_ring"] = zr
    D["fg_z_gear"] = zbig
    D["hb_wall"] = wall
    D["hb_tip_r"] = tip_r
    D["hb_root_r"] = root_r
    D["hb_tip_th"] = tooth_tip(zp, mn, pa, D["hb_backlash"] / 2, ha, beta)
    D["hb_virtual"] = zp / math.cos(math.radians(beta)) ** 3
    D["skirt_id"] = 2 * tip_r
    D["enc_cd"] = enc
    D["d_pin_tip"] = 2 * (zp * mt / 2 + ha * mn)
    D["fm_ratio"] = total
    D["fg_ratio"] = total
    D["module"] = mn


def _place_feel(D):
    """2 mm-shaft motor: its Tempero pinion meshes the printed spur on the compound idler (the one farther from the 1220).
    The motor orbits that idler at the catalogue centre distance and sits where the can clears the skirt, the dial, the 1220 and the Hall arm."""
    F = D["feel"]
    angs = D["idler_angs"]
    i = max(range(len(angs)), key=lambda k: min((angs[k] - 0.0) % 360.0, (0.0 - angs[k]) % 360.0))
    ix, iy = D["idler_xy"][i]
    cd = (D["fg_z_gear"] + D["fg_z_pin"]) * D["fg_mod"] / 2
    can_r = F["can_d"] / 2
    pin_tip = D["fg_z_pin"] * D["fg_mod"] / 2 + D["spur_addendum"] * D["fg_mod"]   # nylon stub addendum
    best = None
    for k in range(360):
        x = ix + cd * math.cos(math.radians(k))
        y = iy + cd * math.sin(math.radians(k))
        r = math.hypot(x, y)
        parts = {
            "skirt": D["skirt_id"] / 2 - r - can_r - F["saddle_rad"],
            "dial_can": r - can_r - D["dial_tube_od"] / 2,
            "body_can": math.hypot(x - D["offset"], y) - D["can_r"] - can_r,
        }
        # the nylon pinion is under the PCB and the can is above the ring pinions, so a plan overlap is not a hit
        parts["gear"] = 1e9
        parts["hall"] = _hall_clear(D, x, y, can_r)
        worst = min(parts.values())
        if best is None or worst > best[0]:
            best = (worst, x, y, r, parts)
    _, x, y, r, parts = best
    ang = math.degrees(math.atan2(y, x)) % 360.0
    p = F["pad_pitch"] / 2
    tx, ty = -math.sin(math.radians(ang)), math.cos(math.radians(ang))
    D["fg_idler"] = i
    D["fg_ang"] = angs[i]
    D["fg_xy"] = (ix, iy)
    D["fg_cd"] = cd
    D["fg_cd_nom"] = cd
    D["fg_cd_err"] = 0.0
    D["fg_tip"] = D["fg_z_gear"] * D["fg_mod"] / 2 + D["spur_addendum"] * D["fg_mod"]
    D["fg_pin_tip"] = pin_tip
    D["z_feel"] = D["z_enc_pinion"]
    D["fm_ang"] = ang
    D["fm_cd"] = r
    D["fm_xy"] = (x, y)
    D["fm_tip"] = pin_tip
    D["fm_clear"] = parts
    D["fm_pad_xy"] = [(x + tx * p, y + ty * p), (x - tx * p, y - ty * p)]
    face = D["fg_pinion"]["face"]
    hub_extra = max(0.0, D["fg_pinion"]["hub_w"] - face)
    D["fg_z_top"] = D["z_pcb_back"] - D["fg_back_h"] - D["fg_clear"]
    D["fg_z_bot"] = D["fg_z_top"] - face - hub_extra
    D["fg_face"] = face
    half = D["brass_backlash"] / 2
    D["spur_tip_th"] = min(
        tooth_tip(D["z_hub_gear"], D["hub_mod"], D["pressure"], half, D["spur_addendum"]),
        tooth_tip(D["z_pinion"], D["hub_mod"], D["pressure"], half, D["spur_addendum"]),
        tooth_tip(D["fg_z_gear"], D["fg_mod"], D["pressure"], half, D["spur_addendum"]),
        tooth_tip(D["fg_z_pin"], D["fg_mod"], D["pressure"], half, D["spur_addendum"]))


def _det_r_nom(D):
    """Detent radius inboard of the bottom-ring pinion tips.

    At ±10° the old fan-wing seat (between the Hall window and the pinion angle) has no overlap: the window grows
    with travel and the fan edge shrinks with it. Inboard of the tips the ear can be as wide as the travel needs."""
    r_in = D["enc_cd"] - D["d_pin_tip"] / 2 - D["fan_clear"]
    return r_in - (D["bt_rows"] - 1) / 2 * D["bt_row_pitch"] - D["bt_ball"] / 2 - D["fan_clear"]


def _set_travel(D):
    """[Ed] hard stop just past ±det_deg, by the ball's bore play at the detent radius. Overwrites travel_deg."""
    D["det_r_nom"] = _det_r_nom(D)
    D["travel_deg"] = D["det_deg"] + math.degrees(D["det_stop_clear"] / D["det_r_nom"])


def _ot_gaps(r, n_pairs, free_deg, d_load, d_spacer):
    """Chord between a load ball and the next spacer, and how much air is left."""
    ang = free_deg / (2 * n_pairs)
    chord = 2 * r * math.sin(math.radians(ang) / 2.0)
    return ang, chord, chord - (d_load + d_spacer) / 2.0


def _place_outer_thrust(D):
    """Cageless Ø2 load balls between a top track (knob) and a bottom track (cradle). No carrier.
    Glass spacers alternate and must touch both neighbours and clear both tracks from ot_spacer_min to ot_spacer_max.
    The C20–C22/U20 sector cannot be left empty, so a printed blank fills it."""
    d_load = D["ot_ball_d"]
    dmin, dmax = D["ot_spacer_min"], D["ot_spacer_max"]
    rb = d_load / 2.0
    rg = rb + D["ot_seat_gap"]
    root_r, R = D["hb_root_r"], D["R"]
    # Groove bottom sits ot_land_min above the PCB. The ball equator stays on the knob underside,
    # so the underside rises with the land. Radial ring band and cradle clearance are not moved.
    z_ball = max(D["h_skirt0"], D["ot_land_min"] + rg)
    if z_ball > D["h_skirt0"]:
        D["h_skirt0"] = z_ball
        D["h_pin0"] = z_ball + D["pin_above_skirt"]
        D["h_pin1"] = D["h_pin0"] + D["pin_face"]
    half_w = rg
    span = R - root_r
    if span > 2 * half_w:
        land = (span - 2 * half_w) / 2.0
        r = root_r + land + half_w
    else:
        r = min(max((root_r + R) / 2.0, root_r + half_w), R - half_w)
    land_in, land_out = r - half_w - root_r, R - (r + half_w)
    a0, a1 = D["ot_keep_ang"]
    keep = (a1 - a0) % 360.0
    free = 360.0 - keep
    # keep a load-ball radius clear of the printed blank that fills the keep-out
    margin = math.degrees(math.asin(min(0.999, rb / r))) + D["ot_seat_gap"]
    usable = free - 2 * margin
    best = None
    for n in range(6, 90):
        ang = usable / (2 * n - 1)
        chord = 2 * r * math.sin(math.radians(ang) / 2.0)
        gap_max = chord - (d_load + dmax) / 2.0
        gap_min = chord - (d_load + dmin) / 2.0
        if gap_max < D["ot_play"] or gap_min > D["ot_play_max"] or gap_min <= 0:
            continue
        if best is None or gap_max < best[0]:
            best = (gap_max, n, ang, chord, gap_min)
    if best is None:
        raise ValueError("no cageless ball count fits the spacer window")
    _g, n, ang, chord, gap_min = best
    angs = []
    a = (a1 + margin) % 360.0
    for _i in range(2 * n):
        angs.append(a % 360.0)
        a += ang
    D["ot_rg"] = rg
    D["ot_z"] = z_ball
    D["ot_r"] = r
    D["ot_half_w"] = half_w
    D["ot_land"] = min(land_in, land_out)
    D["ot_land_in"] = land_in
    D["ot_land_out"] = land_out
    D["ot_n"] = n                                 # load balls (ruby accents are some of these)
    D["ot_n_spacer"] = n
    D["ot_angs"] = angs[0::2]                     # load
    D["ot_spacer_angs"] = angs[1::2]
    D["ot_chord"] = chord
    D["ot_gap_max"] = best[0]                     # air at the large spacer
    D["ot_gap_min"] = gap_min                     # air at the small spacer
    D["ot_play_total"] = 2 * n * best[0]          # whole ring, large spacers
    D["ot_track_clear_max"] = (d_load - dmax) / 2.0
    D["ot_track_clear_min"] = (d_load - dmin) / 2.0
    D["ot_track_clear_alt"] = (d_load - D["ot_spacer_alt"]) / 2.0
    D["ot_gap_alt"] = chord - (d_load + D["ot_spacer_alt"]) / 2.0
    D["ot_light_gap"] = best[0]                  # slit between a load ball and a max spacer
    ruby = min(D["ot_ruby_n"], n)
    D["ot_ruby_idx"] = list(range(ruby))
    D["ot_z_top"] = z_ball                        # bottom track stops at the equator (not a cage)
    D["ot_floor"] = z_ball - rb                   # resin under the ball's lowest point
    D["ot_land_th"] = z_ball - rg                 # clear resin under the groove bottom, PCB front = 0


def _place_det_columns(D):
    """One support column per detent, the shortest link that clears the sweeping arm and the feel saddle."""
    R2D = math.degrees
    fm = D["fm_xy"]
    can = D["feel"]["can_d"] / 2 + D["feel"]["saddle_rad"]
    col_r, need, link_hw = 0.8, 0.5, 0.7
    det_r = D["det_r"]
    ear = D["travel_deg"] + R2D((D["det_ball"] / 2) / det_r)
    T = D["travel_deg"]
    pad0 = min(D["bt_rs"]) - D["bt_groove_r"] - D["fan_clear"]

    def ad(a, b):
        return min((a - b) % 360.0, (b - a) % 360.0)

    def seg(x0, y0, x1, y1):
        vx, vy = x1 - x0, y1 - y0
        L2 = vx * vx + vy * vy
        t = 0.0 if L2 < 1e-9 else max(0.0, min(1.0, ((fm[0] - x0) * vx + (fm[1] - y0) * vy) / L2))
        return math.hypot(x0 + t * vx - fm[0], y0 + t * vy - fm[1]) - can - link_hw - need

    pts = []
    for a in D["det_angs"]:
        dx = det_r * math.cos(math.radians(a)); dy = det_r * math.sin(math.radians(a))
        best = None
        for ir in range(22, 90):
            r = ir / 5.0
            for ang in range(0, 360, 2):
                if ad(ang, a) < 8:
                    continue
                x = r * math.cos(math.radians(ang)); y = r * math.sin(math.radians(ang))
                if math.hypot(x - fm[0], y - fm[1]) < can + col_r + need:
                    continue
                if r + col_r > D["skirt_id"] / 2 - 0.4 or r - col_r < D["dial_tube_od"] / 2 + 0.4:
                    continue
                if any(math.hypot(x - px, y - py) < D["d_pin_tip"] / 2 + col_r + 0.4
                       for px, py in (D["enc_xy"], *D["idler_xy"], (D["offset"], 0.0))):
                    continue
                hit = False
                for ea in D["det_angs"]:
                    dd = ad(ang, ea)
                    if (r + col_r > pad0 - need and r - col_r < 9.2 + need
                            and dd < ear + T + R2D((col_r + need) / max(r, 1.0))):
                        hit = True
                    if r < pad0 + col_r + need and dd < T + R2D((0.8 + col_r + need) / max(r, 1.0)):
                        hit = True
                if hit or (ad(ang, D["ha_ang0"]) < T + R2D((2.6 + col_r + need) / max(r, 1.0)) and r < 17.5):
                    continue
                if r < D["sl_r"] + col_r + 1 and ad(ang, D["sl_ang"]) < T + R2D((0.8 + col_r + need) / max(r, 1.0)):
                    continue
                if seg(dx, dy, x, y) < 0:
                    continue
                L = math.hypot(x - dx, y - dy)
                if best is None or L < best[0]:
                    best = (L, x, y)
        if best is None:
            raise ValueError("no detent column clears the arm and the feel saddle")
        pts.append((best[1], best[2]))
    D["det_col_xy"] = pts
    D["det_col_r"] = col_r
    D["det_link_w"] = 2 * link_hw


def _place_mech(D):
    """Fan wings + detents. v0.17: detents sit inboard of the pinion tips (det_r_nom) so ±travel still clears the Hall window."""
    R2D = math.degrees; T = D["travel_deg"]; c = D["fan_clear"]
    D["cr_r_out"] = D["skirt_id"] / 2 - 0.5                                 # (= base_drive r_out with cr_clear 0.5)
    D["fan_r1"] = D["skirt_id"] / 2 - D["fan_ring_clear"]
    D["fan_r0"] = D["fan_r0_frac"] * D["cr_r_out"]
    D["fan_z0"] = D["plate_t"] + 2 * D["bt_up"]
    gap = min(min((a - D["ha_ang0"]) % 360, (D["ha_ang0"] - a) % 360) for a in (D["enc_ang"], *D["idler_angs"]))
    pin_half = R2D(math.asin(min((D["d_pin_tip"] / 2 + c) / D["enc_cd"], 1)))
    D["fan_w1"] = gap - pin_half - T                                        # fan sector edge (swept clear of the pinions)
    D["fan_half"] = D["fan_w1"]
    D["det_r"] = D["det_r_nom"]
    n = D["bt_rows"]; D["bt_rs"] = [D["det_r"] + (i - (n - 1) / 2) * D["bt_row_pitch"] for i in range(n)]
    rmin = min(D["bt_rs"]); rmax = max(D["bt_rs"])
    D["bt_half"] = T / 2 + R2D((D["bt_ball"] / 2 + D["det_stop_clear"]) / rmin)   # the ball rolls travel/2
    # window half-angle at the detent radius: only the bar that actually crosses this radius, swept ±travel
    clr = D["ha_win_clear"]; win = 0.0
    if D["hall_layout"] == "vernier":
        pr = D["hv_pad_r"]
        for r, a in zip(D["hv_r"], D["hv_phi_m"]):
            if r + pr + clr < rmin - 1e-6 or r - pr - clr > rmax + 1e-6: continue
            win = max(win, abs(a - D["ha_ang0"]) + T + R2D(math.asin(min((pr + clr) / rmin, 1))))
    # far limit: the fixed groove's outer edge stays clear of the nearest pinion tip
    def _pin_clear(off, rad):
        a = math.radians(D["ha_ang0"] + off)
        x, y = rad * math.cos(a), rad * math.sin(a)
        worst = 1e9
        for pa, pr, tip in ((D["enc_ang"], D["enc_cd"], D["d_pin_tip"] / 2),
                            *[(aa, D["enc_cd"], D["d_pin_tip"] / 2) for aa in D["idler_angs"]],
                            (D["fm_ang"], D["fm_cd"], D["feel"]["shaft_d"] / 2 + c)):
            px, py = pr * math.cos(math.radians(pa)), pr * math.sin(math.radians(pa))
            worst = min(worst, math.hypot(x - px, y - py) - tip)
        return worst
    # det_hi: largest offset whose groove (and the ear, which sweeps ±travel above the pinions) keeps fan_clear
    hi = win
    for off in [win + i * 0.5 for i in range(int((180 - win) * 2))]:
        if _pin_clear(off + D["bt_half"], rmax) < c: break
        hi = off
    ear = T + R2D(D["det_ball"] / 2 / D["det_r"])
    lever_off = min((D["sl_ang"] - D["ha_ang0"]) % 360.0, (D["ha_ang0"] - D["sl_ang"]) % 360.0)
    # ears must not meet each other or the centring lever
    D["det_lo"] = win + R2D((clr + D["bt_groove_r"]) / rmin) + D["bt_half"]
    D["det_hi"] = min(hi, 90.0 - ear, lever_off - ear - c)
    D["det_off"] = D["det_lo"] if D["det_lo"] <= D["det_hi"] else (D["det_lo"] + D["det_hi"]) / 2
    D["det_angs"] = [D["ha_ang0"] - D["det_off"], D["ha_ang0"] + D["det_off"]]
    D["hall_win_out"] = win
    D["bt_z"] = D["plate_t"] + D["bt_up"]
    D["sl_pin_top"] = D["sl_top"] + D["sl_spring_gap"] + D["sl_spring"][0] + 0.4
    D["cu_z"] = (D["sl_z0"] + D["sl_top"]) / 2
    # rib section (shared with the deflection check and the arm solid)
    D["ha_rib_r_head"] = D["fan_r0"]                                        # hammerhead (13.85 in v0.16b; follows the fan)
    D["ha_rib_r_hub"] = D["dial_tube_od"] / 2
    D["ha_rib_z_top"] = D["sl_top"]                                         # up to the lever top
    D["ha_rib_z_low"] = D["plate_t"] + D["bt_up"] + 0.05                  # just over the plate so the swept corner stays ≥ 0.3
    # ha_rib_z_cage (over the thrust cage) is hv_spoke_z0, set by control_dial once the cage is known
    _place_det_columns(D)


def derive(D):
    """Interface-derived values (pure function of the interface params). Adds keys to D in place."""
    R2D = math.degrees
    # ---- motor + knob size chain ----
    M = D["motor"]; D["can_r"] = M["body_d"] / 2
    D["dial_tube_od"] = D["dial_tube_id"] + 2 * D["dial_tube_wall"]
    _place_hub(D)   # v0.18: RW m0.6 pinion, hub tooth count inside 1.4–1.6, motor stays at motor_offset
    # v0.16: the screen sets the knob OD (closed lip ring, lip_wall_lines x nozzle outside the panel AND outside the COF bend)
    D["lip_wall_min"] = D["lip_wall_lines"] * D["nozzle"]
    D["tgt"] = dict(D["tgt"], lip_wall=D["lip_wall_min"])
    D["scr_off_opt"], D["knob_od_min"] = _screen_knob(dict(SCREENS[D["screen"]], **({} if D["cof_bend"] is None else {"bend": D["cof_bend"]})),
                                                      D["lip_wall_min"], D["bend_clear"])
    st = D["knob_od_step"]
    screen_od = math.ceil(D["knob_od_min"] / st - 1e-9) * st
    # OD stays the screen lip. The ring band and the race grow inward; the teeth and the cradle follow.
    D["knob_od"] = screen_od
    _place_herringbone(D, D["knob_od"] / 2)
    D["skirt_wall"] = (D["knob_od"] - D["skirt_id"]) / 2
    D["R"] = D["knob_od"] / 2
    _set_travel(D)   # v0.17: ±det_deg latch, hard stop a ball-clearance past it (hall arc and the fan follow this)
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
    # Faceplate front is the knob screen top, set back by knob_proud. PCB front is z = 0.
    # sub/case-v01 reads faceplate_z and faceplate_t from cad_constraints.json.
    D["faceplate_z"] = D["z_top"] - D["knob_proud"]
    D["faceplate_z_back"] = D["faceplate_z"] - D["faceplate_t"]
    D["z_board_top"] = D["z_holder0"] - D["nut_m"] - D["cord_clear"]      # adapter board top (50.60)
    D["z_floor"] = D["z_board_top"] - D["adapter_t"]                       # 49.60 = brass tube top = adapter seat
    D["z_rod_top"] = D["z_board_top"] + D["nut_m"]
    D["z_pcb_back"] = -D["pcb_t"]
    D["h_pin0"] = D["h_skirt0"] + D["pin_above_skirt"]; D["h_pin1"] = D["h_pin0"] + D["pin_face"]   # pinion band in the bottom ring
    # ---- dial tube + 45 deg cone bearing (shared by main_knob and control_dial) ----
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
        mid = D["hv_mid"] if (D["hv_mid"] and 0 <= D["hv_mid"]["idx"] < n) else None
        D["hv_z_mag0"] = max(sw["h"] + D["hv_gap"], (mid["h"] + D["hv_gap_mid"]) if mid else 0.0)
        D["hv_elem_gap"] = D["hv_z_mag0"] - D["hv_z_elem"]
        # per-sensor package + element height (v0.16b: one TMAG5273 in the row)
        D["hv_dims"] = [(mid["lead_w"], mid["l"], mid["h"]) if (mid and i == mid["idx"]) else (sw["w"], sw["l"], sw["h"]) for i in range(n)]   # radial, tangential, height
        D["hv_z_elems"] = [mid["elem_z"] if (mid and i == mid["idx"]) else D["hv_z_elem"] for i in range(n)]
        D["hv_parts"] = [mid["part"] if (mid and i == mid["idx"]) else sw["part"] for i in range(n)]
        D["hv_mid_elem_gap"] = (D["hv_z_mag0"] - mid["elem_z"]) if mid else None
    _place_feel(D)
    _place_mech(D)
    _place_outer_thrust(D)
    # ---- v0.16 knob ring magnet / dial sensor ----
    D["tm_r"] = (D["tm_ring"][0] + D["tm_ring"][1]) / 4                  # sensor element over the ring mid radius
    D["tm_xy"] = (D["tm_r"] * math.cos(math.radians(D["tm_ang"])), D["tm_r"] * math.sin(math.radians(D["tm_ang"])))
    return D
