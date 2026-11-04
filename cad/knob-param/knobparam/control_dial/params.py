"""control_dial own params + derive (dial, thrust balls, hub magnet, Hall arm + magnets, screen, carrier, FPC strap, fixed
adapter cup). Reads: interface + own + IMPORTS (electronics adapter-board envelope)."""
import math

P = dict(
    # ---- knob top bearing: opposed 45 deg cones [Ed] ----
    kb_seat_depth=0.10,   # [A] "tube" race only: seating groove depth into the dial cone (0 = plain cone, v0.14)
    kb_ball_tube=0.1,   # [A] "tube" race only: ball to the plain tube
    kb_zc_tube=41.45,   # [A] "tube" race only: ball centre height
    # ---- control dial [Ed/A] ----
    lip_t=4.0,   # [Ed] about 4 at the top
    dial_hub_wall=2.0,   # [A]
    web_in_t=2.0,   # [A]
    well_clear=0.2,   # [A]
    gusset=1.5,   # [A]
    lip_fillet=1.0,   # [A]
    dial_hub_z0=43.6,   # [A] "tube" race only: hub bottom (chamfer race: derived, see dial_hub_below_gusset)
    dial_hub_below_gusset=0.0,   # [Ed] v0.15d: hub straight face below the 45° gusset (0 = hub bottom at the gusset start; v0.15c had 1.4)
    dial_bore_floor=0.5,   # [A] dial material kept under the cup-boss bore, above the hub bottom
    dial_collar_d=9.2,   # [A] "tube" race only (v0.15c chamfer race: no collar)
    dial_collar_h=0.3,   # [A] "tube" race only
    r_web=14.0,   # [A] web/lip junction radius ("stepped" dial only)
    # ---- v0.21 [Ed 2 Nov 13:31-13:51]: the top of the knob as straight cones, no steps ----
    dial_shape="cone",   # [Ed] "cone": dial underside and top are parallel cones at cone_deg; "stepped": v0.20 web + cup + well
    cone_deg=30.0,   # [Ed] cone angle from the panel plane. Dial underside, dial top, cap top and cap underside are all parallel.
    race_out=2.5,   # [Ed 13:51] the gap and the ball race moved out this far, and up race_out*tan(cone_deg), along the cone, so the
                    # cone faces stay put while the cap neck and the dial under the adapter-board corner both grow to ~2.1
    cone_well_clear=0.3,   # [A] dial well wall round the adapter board edge ("cone" dial)
    carr_seat_wall=0.6,   # [A] the flat carrier seat starts this far inside the carrier-magnet pocket ("cone" dial)
    boss_bore_clear=0.15,   # [A] dial bore round the holder boss
    cup_clear=0.2,   # [A] dial round the holder cup
    dial_screen_gap=0.3,   # [A] dial below the holder plate
    dial_mag_press=0.05,   # [A] press-fit oversize for magnet pockets
    tm_board=(4.0, 6.0, 0.6),   # [A] dial sensor board: radial, tangential, thickness (TMAG5273 face-down on its underside)
    tm_pocket_clear=0.6,   # [Ed/A] generous room round the sensor board for easy assembly (drops in from the top, carrier off)
    # ---- thrust bearing under the dial ----
    tb_on=False,   # [Ed] 2 Nov: no bearing under the dial tube, just an air gap. The 45° race on the knob carries the dial and the
                   # adapter board stops it lifting; a second axial support here only fought the tolerance stack.
                   # The tb_* numbers below stay as the height datum (dial tube end, Hall spoke) so nothing else moves.
    dial_air_min=0.5,   # [A] tube end over the cradle top with no thrust bearing: room for the stack (printed hub, glued glass, race)
    tb_ball_d=1.0,
    tb_pcd=6.8,
    tb_groove_r=0.55,
    tb_ball_up=0.3,
    tb_pocket_d=1.1,
    tb_web_min=0.65,
    tb_cage=(5.3, 8.58, 0.4),   # [A] cage ID, OD, thickness. OD 8.58 leaves the inner Hall pad 0.30 mm clear (8.60 was 0.295).
    # ---- screen holder + adapter ----
    hold_z0_socket=5.0,   # [A] socket engagement on the tube
    socket_d=5.2,   # [A]
    boss_d=7.0,   # [A]
    hold_od=21.92,   # [A]
    floor_t=0.8,   # [A]
    well_wall=0.8,   # [A]
    hold_step=51.8,   # [A]
    adapter_clear=0.2,   # [K]/[A] (cord room over the nut [Ed])
    # ---- screen [S] (table below) ----
    run_gap=0.15,   # [A] panel -> rotating dial lip
    edge_margin=0.0,   # [A] outermost screen point to the knob OD (>= 0: nothing past the OD)
    offset_step=0.005,   # [A] screen offset rounded up to this (v0.14: 0.05)
    fpc_clear=0.15,   # [A] folded FPC corners inside the lip ID
    cof_inset=2.0,   # [A] COF bend band = ledge width - 2*cof_inset
    b2b_at="J1",   # [A] B2B placed over this adapter connector (jumper straight down onto it)
    jumper_t=0.15,   # [A]
    # ---- v0.15: screen turns with the dial ----
    screen_on_dial=True,   # [Ed] panel bonded to a carrier bonded on the dial (False = v0.14 fixed holder + running gap)
    lip_bond_gap=0.0,   # [A] panel edge -> lip ID (bonded, no running gap; lip ID centred on the panel)
    # ---- v0.16 screen carrier cartridge [Ed]: locating pin sets its angle, a small magnet in the dial pulls a steel disc in the
    # carrier down; lift off with a suction cup for service (then undo the centre bolt and the whole stack comes apart) ----
    carr_r=15.0,   # [A] pin + magnet radius on the dial shoulder (outside the fold window, far from the dial TMAG5273)
    carr_mag_ang=90.0,   # [A] magnet angle (opposite side of the fold from the pin)
    carr_pin_ang=270.0,   # [A] locating-pin angle
    carr_mag=(3.0, 1.0),   # [Ed] v0.17: Ø3×1 N52 in the dial shoulder (the base), at 90°, opposite the Ø1 pin
    carr_mate=(3.0, 1.0),   # [Ed] v0.17: Ø3×1 N52 in the carrier, facing the base magnet (attracting)
    carr_steel=(2.0, 0.5),   # unused in v0.17 (v0.16 was a steel disc pulled by a Ø2×1 magnet)
    carr_pin=(1.0, 1.5, 0.8),   # [A] Ø1 steel dowel: pressed depth in the dial, engagement in the carrier
    carr_mag_gap=0.0,   # [A] carrier magnet top below the dial shoulder (0 = flush, touching the steel disc)
    carr_pin_clear=0.05,   # [A] carrier hole over the pin
    carr_stray_max=0.02,   # [A] carrier-magnet field at the dial TMAG5273 / range (dipole estimate)
    lip_closed=True,   # [Ed] v0.16: lip is a full ring (COF bend in a blind pocket inside the lip, no through-slot)
    carrier_run=0.3,   # [A] rotating carrier plate above the fixed adapter cup
    adapter_cup=False,   # [Ed] v0.16: brown cup removed - the centre bolt clamps the stack, the adapter board is the dial up-stop (was True) fixed adapter cup on the tube (False = none: adapter board sits on the brass tube end, clamped by the rod nut)
    b2b_flip=True,   # [A] B2B on the far side of the axis from J1 -> diametral FPC strap through the axis
    strap_t=0.12,   # [A] 2-layer PI flex, clear over the rod/nut, % dynamic limit
    strap_clear=0.3,   # [A] 2-layer PI flex, clear over the rod/nut, % dynamic limit
    strap_lines=14,   # [A] 2-layer PI flex, clear over the rod/nut, % dynamic limit
    strap_strain_max=0.3,   # [A] 2-layer PI flex, clear over the rod/nut, % dynamic limit
    dial_spring=0.4,   # [A] centring spring rate N*mm/deg (torque = k*theta)
    cc_chamfer=0.3,   # [A] v0.30 (cc_on): 45° lead-in on the Hall bar's two lower side edges over its first link (pads 1-2), so the
                      # bar going down the slot pushes a spring end back if a print leaves it standing proud of the arm's face
    # ---- v0.15: Hall vernier (arm down through the cradle slot, 5 magnets x 5 sensors, arcs crossing) ----
    fan_on=True,   # [Ed] v0.16 fan arm + lever (False = v0.15 bar only)
    hv_spoke_w=3.0,   # [A] spoke width; spoke bottom this far above the thrust balls / cage
    hv_spoke_clear=0.31,   # [A] spoke bottom above the thrust balls / cage. 0.30 left the solid 0.295 mm clear.
    # ---- v0.21 [Ed 2 Nov]: the single spring-ball detent moves OUT to the end of the arm, on the arc (more room for the three
    # dimples at 0 and ±det_deg), and the arm rides on three small ball tracks with alternating big and small balls.
    # Hard limit: the Hall bar's slot takes the cradle plate under the middle of the arc and the pinions bound its ends, so
    # under the arc itself there is no room for a ball train that rolls ±travel/2. The tracks hug the slot on both sides at
    # the largest radius the pinion tips allow. arm_det="ear" rebuilds v0.20 (inboard ear, one two-row track). ----
    arm_det="split",   # [Ed 2 Nov 15:27] "split" (v0.22), "arc" (v0.21 study branch) or "ear" (v0.20)
    ad_off=0.0,   # [A] detent angle from the Hall arm centreline (0 = on the rib line, between the two outer tracks)
    ad_r_frac=0.5,   # [A] detent radius across the fan band (0 = fan_r0, 1 = fan_r1)
    ad_land_edge=0.4,   # [A] raised land past the ball footprint: radially, and along the arc at the hard stop
    ad_land_min=0.75,   # [A] flat land wanted between neighbouring dimple rims (the ball radius: it rides flat between latches)
    tk_tracks=((-1, 0), (-1, 1), (1, 0)),   # [A] (side of the Hall slot: -1 encoder side, +1 lever side; row 0 outer, 1 next in).
                                            # The lever side has room for one row only (the 1220 collar), so the third goes in on the encoder side.
    tk_n_big=2,   # [A] load balls per track (Ø bt_ball, [Ed] Ø1); one separator between each pair: big, small, big
    tk_small=0.8,   # [A] separator ball Ø. Stock 0.8 (1/32" = 0.794 also fits). Non-magnetic (316, ZrO2 or ruby): the Hall magnets are ~2 mm away.
    tk_seat_min=0.05,   # [A] separator below both races: (big - small)/2 at least this (the load balls' seat gap)
    tk_land=0.4,   # [A] arm web / plate land round each groove (radial) and past each groove end (arc)
    tk_bar_clear=1.3,   # [A] groove end to the Hall bar's swept edge, along the arc (base_drive slot clearance 0.5 + land; the slot edge slants, so 1.0 left only 0.21 of plate)
    tk_row_pitch=1.5,   # [A] radial pitch of two rows on one side (groove 1.1 + land 0.4)
    tk_end_clear=0.10,   # [A] groove end past the end ball at full travel, mm of arc (same as det_stop_clear)
    # ---- v0.22 [Ed 2 Nov 15:27] split arm: the Hall bar keeps its own spoke (ha_ang0, now 224) and the single detent moves to a
    # second spoke over solid plate. A ball train (big, small, big) sits on a fixed pedestal directly under the detent ball, so
    # the spring load runs spring -> ball -> flange -> train -> pedestal -> plate with no bending (Ed: support right under the
    # spring). Numbers from the split-spoke study (docs/img/dial-split-study.png). ----
    # sp_ang / sp_r (detent spoke angle, radius) are INTERFACE params since v0.22b: the PCB needs the pedestal grub position
    sp_flange_z0=5.75,   # [A] flange underside: 0.32 over the idler-pinion caps (top 5.43) as it sweeps; checked in the assembly
    sp_w_lo=(6.0, 5.0),   # [A] low spoke width at the dial tube / at sp_r_join (z fan_z0..fan_top, under the pinion caps' level)
    sp_w_hi=5.0,   # [A] high spoke width (z flange underside..land top)
    sp_r_join=9.0,   # [A] the low spoke runs to sp_r_join + 0.2
    sp_r_hi0=8.7,   # [A] the step up to the flange level starts here (past the centring-spring anchor post)
    sp_core=1.0,   # [A] flange material between the top of the train groove and the bottom of a dimple
    # ---- v0.24 [Ed 3 Nov 12:28-12:58] the dial screen as a drop-in bezel cartridge, knob +4.4 (screen "z132a2441-1.32", interface
    # cart=True). Spec: docs/handover-2026-11-03.md "Job 1"; concept docs/img/dial-concept-2-cartridge.png. Every (x, y) and angle
    # below is in the PANEL frame (+x right, +y up the panel, dial axis at the origin, angles from +x); the parts are built there and
    # turned into the mechanism frame by -mech_rot. "behind" = below the lens back (z_top - lens_t). [S] = Waveshare
    # ESP32-S3-Touch-AMOLED-1.32 STEP/drawing rev 2025-10-21 (not committed; numbers from the doc's "Dial fit study").
    zp=dict(lens_d=36.40, lens_t=1.30,       # [S] cover glass Ø36.40 x 1.30
            step_d=34.30, step_t=0.55,       # [S] its top step Ø34.30 x 0.55 (the bezel laps the shoulder)
            lcm_d=35.4, lcm_t=1.0,           # [A] panel (LCM) behind the lens: ~1.0 [S: lens + LCM 2.29]; Ø between the Ø33.75 view and the lens
            patch_back=2.15, patch_r=17.6,   # [S] parts on the panel's own flex: to 2.15 behind the lens back, out to r 17.6
            patches=((11.5, 17.0, -9.4, 3.3), (11.5, 16.0, 3.7, 7.4), (-11.0, -6.5, 9.5, 13.7)),   # [S] x0, x1, y0, y1
            bend_hx=4.5, bend_r=18.97,       # [S] bottom COF bend (-y): |x| <= 4.5, out to r 18.97
            tab_hx=2.2, tab_r=18.53,         # [S] top tab (+y): |x| <= 2.2, out to r 18.53
            bend_top=0.3,                    # [A] bend and tab start this far behind the lens back (the panel substrate, not the lens)
            bend_back=1.35, tab_back=1.0,    # [S fit-study depth plot] bend reaches 1.35 behind the lens back; the tab [A] 1.0
            flex_t=0.1,                      # [A] tail flex
            tail_y=(-11.6, -7.5),            # [S] free tail, 4.1 wide
            tail_x0=-13.9,                   # [S] leaves the panel's back here heading -x
            uturn_x=-15.25,                  # [S] U-turn outer face (corner r 19.2); the U-turn runs from the LCM back down to the lower leg
            leg_back=3.5,                    # [S] lower leg underside 3.5 behind the lens back
            leg_x1=6.6,                      # [A] lower leg ends here and rises (joggle, x 6.6-7.1) onto the plug's flex end
            plug=(7.2, 10.7, -13.4, -5.7),   # [S] 24-pin 0.4 mm board-to-board plug, x0, x1, y0, y1; faces down
            plug_face=3.82,                  # [S] plug mating face this far behind the lens back
            mated=0.8),                      # [S] mated height (board top to the plug's flex)
    db=dict(t=0.8,                          # [A] dial board (PCBA) thickness
            behind=4.0,                      # [S] board top 4.0 behind the lens back (Waveshare's board front) -> 55.9
            d=33.6,                          # [A] Ø33.6, so its rim sits 0.5 on the ledge. Concept Ø32.4 [Ed 12:58]: its edge (r 16.2) stopped
                                             # 0.1 short of the ledge (r 16.3), so only the lobe would have rested on the dial
            lobe=(290.0, 330.0, 18.0),       # [Ed 12:58] lobe to r 18.0 over 290-330° round the receptacle
            rec=(8.95, -9.55, 3.6, 8.6, 0.55),   # [Ed 12:58] receptacle on top: centre x, y; size x, y; height (24-pin 0.4 mm)
            parts=(("ESP32-S3-PICO-1-N8R8", 0.0, 10.5, 7.0, 7.0, 0.96),   # [S] 7 x 7 x 0.96, 8 MB flash + 8 MB PSRAM, crystal inside
                   ("LDO 3.3 V", 4.6, 9.2, 1.6, 1.6, 0.6),           # [Ed 12:58] place; [A] 1.6 x 1.6 body (DFN-6): 0.3 off the ESP32
                   ("rod-link PHY", -4.6, 11.4, 1.6, 1.6, 0.6)),     # [Ed 12:58] place; [A] 1.6 x 1.6 body (a 3 x 3 QFN here hits the ESP32)
            diode=(-9.5, 2.5, 3.8, 2.5),     # [Ed 12:58] 405 nm laser diode, TO-38 class can Ø3.8 x 2.5, facing down
            led=(13.5, (30.0, 150.0, 210.0, 270.0, 330.0), 2.0, 2.0, 0.9)),   # [Ed 12:58] 5 LED sites at r 13.5; [A] 2020 body
    ct=dict(wall=2.0,                       # [Ed 12:58] pocket floor = max(well floor, 2.0 normal wall over the 30° cone underside)
            pocket_r=16.3,                   # [Ed 12:58] pocket to r 16.3, ledge (board underside) to r 17.3, land (board top) to the outside
            ledge_w=1.0,
            outer_r=19.2,                    # [Ed 12:58] dial body outer radius
            lobe_clear=0.3,                  # [A] land cut to the ledge round the board's lobe, this clear of it
            parts_clear=0.3),                # [A] board-underside parts to the pocket floor (check target)
    bz=dict(h=8.4,                          # [Ed 12:41] bezel from the v0.23 dial/main-knob joint (lip underside 52.8, unchanged) to the lens top
            bore_d=39.0,                     # [Ed 12:58] bore below the glass (wall 1.5 at OD 42); the panel is glued in from underneath
            seat_d=36.50,                    # [Ed 12:58] glass seat, from the lens back up the lens's 0.75 shoulder
            lap_d=34.40,                     # [Ed 12:58] lap over the lens step, ID 34.40, 0.55 deep: no glass edge or gap shows
            # v0.25 [Ed 18:26]: no bosses, no pins; the bezel is a plain ring with a key rib (+ two seat ribs [A]) and the sideways
            # magnets in its skirt. Sketch docs/img/cart-side-magnets-v024.png.
            mag=(1.0, 0.5),                  # [Ed 4 Nov 11:46] N52 Ø1 x 0.5: leaves 1.00 of skirt skin outside it (PCBWay MJF wall 1.0);
                                             # v0.25 was Ø1 x 0.8 (skin 0.70)
            mag_angs=(0.0, 30.0, 120.0, 150.0, 240.0, 270.0),   # [Ed 4 Nov 11:46] six pairs, two sets of three 120° apart (each set's
                                             # sideways pulls cancel); clear of the key and seat ribs (180, 60, 340°) and the plug lobe
                                             # and pad arm (290-330°, 305°); the bends, tab and U-turn are all above the land, 2+ mm over
                                             # the magnets. The 0.30 bore gap stays (slip fit for MJF ±0.25 a part) [Ed 11:46]
            mag_dz=+0.4,                     # [A, Ed 18:26 "~0.4 lower"] skirt magnet this far ABOVE the dial magnet, poles attracting:
                                             # an attracting partner 0.4 lower pulls the cartridge UP; above, it pulls it down
            mag_press=0.05,                  # [A] pocket oversize (glued)
            rib_angs=(180.0, 60.0, 340.0),   # [Ed 18:26] key (first) + [Ed 4 Nov 12:12] two seat ribs: one rib cannot seat a Ø42 ring without tilting
                                             # onto the plug; uneven spacing so the cartridge goes on one way only
            rib_w=1.2,                       # [A] rib width (tangential)
            rib_r_in=18.6,                   # [Ed 18:26 "nothing inside r 18.5 below the glass"] rib inner face
            rib_clear=(0.05, 0.50),          # [A] key / [Ed 4 Nov 12:12] seat ribs, tangential clearance a side: the key sets the
                                             # angle; the seat ribs only seat, 0.50 so an MJF error (±0.25) never has them fight the key
            slot_depth=2.0,                  # [A] slot floor this far under the land top = the axial seat [Ed 19:12 item 2]
            slot_r_clear=0.3,                # [Ed 4 Nov 12:12] slot's inner face this far inside the rib's (r 18.3 in the dial; was 0.1):
                                             # as the 0.30 bore gap, so the ribs never centre the cartridge tighter than the bore
            plug_standoff=0.0,               # [Ed 4 Nov 12:37] plug fully mated with the ribs seated: the pad is glued to the arm with
                                             # both home at once (no shim), so the lock clicks and the contacts are as designed; the plug
                                             # shares a press on the glass with the ribs (v0.25-v0.28: 0.10 short, [Ed 19:12 item 2])
            pad_top=1.6,                     # [Ed 12:58] printed plug pad 56.8-58.3: from the plug's flex up to 1.6 behind the lens back
            arm_ang=305.0, arm_w=2.0, arm_t=1.0,   # [Ed 12:58] arm from the pad to the bezel at ~305°; [A] 2.0 wide, 1.0 thick under the pad top
            arm_glue=0.05),                  # [A] glue line between the arm end and the bezel bore
    # ---- v0.25 [Ed 3 Nov 18:12] the dial in two MJF PA-12 parts, split at the top of the tube (the dish's underside, z_hub0, 0.3
    # over the knob's upper cap): the lower part (tube, Hall and detent spokes, lever) goes in first, the cap goes on over the
    # tube, then the balls, then the dish is bonded on: the tube end runs up a through socket in the dish's hub, a flat keys it.
    # The dish sits on the balls (the race centres it) and the lower part on the train, so the bond takes up their height
    # difference: the stack the pedestal grub used to set no longer fights the race. Cartridge dial only (cart). ----
    dsp=dict(on=True,                       # [Ed 18:12]
             glue=0.10,                     # [A] radial bond line in the socket (as the v0.25 hub-gear ring)
             top_below=0.10,                # [A] tube end this far under the well floor, so it never takes the 0.3 lift gap to the rod-link board
             flat=0.30,                     # [A] key flat this deep into the tube OD over the socket length (tube wall at the flat 1.20)
             flat_ang=None,                 # [A] flat facing the Hall spoke (None = ha_ang0, mechanism frame)
             engage_min=2.5,                # [A] check: tube engagement in the socket ("~3" [Ed 18:12])
             T_design=241.0,                # [A] dial design torque, mNm: a hand twisting the bezel at the hard stop, taken as the knob's
                                            # 241 (v0.25 gears: the 85 mNm limit x 1.417 x SF 2 = the knob's break torque)
             bond_allow=3.0),               # [A] epoxy on MJF PA-12 (bead-blasted), shear allowable MPa (PA-12 bonds poorly)
    ls=dict(a=(0.0, -4.6), b=(0.0, 4.0),    # [Ed 12:58] strap from the rod-link board (fixed) to the dial board underside (turns with the dial)
            lines=4,                         # [Ed 12:58] 2 lines (rod = VBUS + data, tube = GND) + 2 spares
            w=2.0,                           # [A] ribbon width (4 traces)
            over_nut=0.5,                    # [A] the run passes this far over the nut top
            foot=1.2),                       # [A] soldered foot (bent flat) at each end, across the ribbon
)

IMPORTS = {"electronics": ["adapter_d", "adapter_fps", "adapter_env"]}
EXPORTS = ["z_hub0", "z_lip0", "z_web0", "dial_hub_od", "r_web", "gusset", "lip_fillet",   # -> main_knob
           "tb_on", "tb_pcd", "tb_groove_r", "tb_z_ball",                                                   # -> base_drive (cradle groove)
           "kb_rc", "kb_zc", "kb_pcd", "kb_n", "kb_gap", "kb_c_dial", "kb_c_knob", "kb_r_collar",   # -> main_knob (ball circle + faces)
           "kb_seat_c_knob", "kb_groove_h",                                                  # -> base_drive (cradle groove)
           "arm_det", "ad_r", "ad_ang", "ad_z_land", "tk", "tk_webs", "sp_ped", "sp_hw", "ad_land_half",   # -> base_drive (arc / split detent + tracks)
           "dial_shape", "cone_deg", "cone_under_r0", "cone_lip_r",                          # -> main_knob (v0.21 cone top)
           "dial_spring"]                                                                    # -> base_drive (v0.30 compression springs)


def derive(D):
    S = D["S"]
    # ---- holder / adapter cup heights ----
    D["z_cup0"] = D["z_floor"] - D["floor_t"]                              # 48.80
    D["pocket_lo_d"] = D["adapter_d"] + 2 * D["adapter_clear"]             # 15.90
    D["well_od"] = D["pocket_lo_d"] + 2 * D["well_wall"]                   # 17.50
    # ---- control dial ----
    # v0.24 [Ed 12:41]: the bezel's underside is the old lip underside, so the dial/main-knob joint does not move (52.8)
    D["z_lip0"] = D["z_top"] - (D["bz"]["h"] if D["cart"] else D["lip_t"])
    D["r_cup"] = D["hold_od"] / 2 + D["cup_clear"]
    D["z_web1"] = D["hold_step"] - D["knob_run"]
    D["r_well"] = D["well_od"] / 2 + D["well_clear"]
    D["z_well"] = D["z_cup0"] - D["knob_run"]                              # web datum (unchanged from v0.15d: race + hub stay put)
    # v0.16 no cup: the well floor rises to carrier_run under the adapter board, which is clamped by the rod nut -> the board is the
    # dial (and, through the 45° race, the knob) up-stop; centre bolt clamps everything [Ed]
    D["z_well_top"] = D["z_well"] if D["adapter_cup"] else D["z_floor"] - D["carrier_run"]
    D["dial_lift"] = D["z_floor"] - D["z_well_top"]                        # free lift of the dial before it meets the board
    D["z_web0"] = D["z_well"] - D["web_in_t"]
    D["dial_bore_d"] = D["boss_d"] + 2 * D["boss_bore_clear"]
    D["dial_hub_od"] = D["dial_bore_d"] + 2 * D["dial_hub_wall"]
    if D["dial_shape"] == "cone":   # v0.21 [Ed 13:51]: gap + race slide out and up along the cone (the cone faces stay where they were)
        D["race_up"] = D["race_out"] * math.tan(math.radians(D["cone_deg"]))
        D["z_web0"] += D["race_up"]
        D["dial_hub_od"] += 2 * D["race_out"]
    if D["kb_race"] == "chamfer":   # v0.15d: hub bottom at the gusset start (no straight hub face under the race)
        D["z_hub0"] = D["z_web0"] - D["gusset"] - D["dial_hub_below_gusset"]
        D["hold_z0"] = max(D["z_floor"] - D["hold_z0_socket"], D["z_hub0"] + D["knob_run"] + D["dial_bore_floor"])   # boss stays above the hub
    else:
        D["z_hub0"] = D["dial_hub_z0"]
        D["hold_z0"] = D["z_floor"] - D["hold_z0_socket"]                  # 44.60
    D["hold_socket_len"] = D["z_floor"] - D["hold_z0"]                     # actual socket engagement on the tube
    D["z_bore0"] = D["hold_z0"] - D["knob_run"]
    D["z_hubf"] = D["z_hub0"] + D["dial_collar_h"]
    # ---- thrust bearing ----
    D["tb_z_ball"] = D["plate_t"] + D["tb_ball_up"]
    D["dial_z_base"] = D["tb_z_ball"] + D["tb_ball_up"]
    D["tb_n"] = int(math.pi * D["tb_pcd"] / (D["tb_pocket_d"] + D["tb_web_min"]))
    D["tb_cage_z0"] = D["tb_z_ball"] - D["tb_cage"][2] / 2
    # ---- knob top bearing: ball circle + track grooves (opposed 45° faces) ----
    kR = D["kb_ball_d"] / 2; k = kR / math.sqrt(2); rho_s = D["kb_seat_r"]; e = rho_s - kR; s2 = math.sqrt(2)
    if D["kb_race"] == "chamfer":   # v0.15c [Ed]: balls in the middle of the 45° gusset face under the dial web, track in both faces
        rh, g, run = D["dial_hub_od"] / 2, D["gusset"], D["knob_run"]
        f = D["kb_race_at"]; d = run / 2                                    # ball centre midway between the faces (normal gap = knob_run)
        D["kb_rc"] = rh + f * g + d / s2; D["kb_zc"] = D["z_web0"] - g + f * g - d / s2
        D["kb_c_dial"] = rh - (D["z_web0"] - g)                             # dial face: r - z = c (normal (1,-1)/√2 points to the knob)
        D["kb_c_knob"] = D["kb_c_dial"] + run * s2                          # knob chamfer = dial face offset by knob_run
        D["kb_groove_h"] = rho_s - (d + e)                                  # groove depth below each face (ball touches both groove bottoms)
        D["kb_r_collar"] = None
        D["kb_face_len"] = g * s2
        D["kb_land"] = min(f, 1 - f) * D["kb_face_len"] - math.sqrt(max(rho_s ** 2 - (d + e) ** 2, 0))   # groove rim to the face end
        dface = d                                                           # ball centre to each face
    else:   # v0.15 cone race at the dial tube
        D["kb_rc"] = D["kb_rt"] + kR + D["kb_ball_tube"]; D["kb_zc"] = D["kb_zc_tube"]
        D["kb_c_dial"] = D["kb_rc"] - D["kb_zc"] - 2 * k; D["kb_c_knob"] = D["kb_rc"] - D["kb_zc"] + 2 * k
        D["kb_r_collar"] = D["kb_rc"] + kR + 0.15 - D["kb_clear"]
        D["kb_groove_h"] = D["kb_seat_depth"]
        dface = kR - D["kb_seat_depth"]
    D["kb_pcd"] = 2 * D["kb_rc"]
    D["kb_n"] = int(math.pi / math.asin((D["kb_ball_d"] + D["kb_play"]) / D["kb_pcd"]))
    D["kb_gap"] = D["kb_pcd"] * math.sin(math.pi / D["kb_n"]) - D["kb_ball_d"]
    zc = D["kb_zc"]; h = D["kb_groove_h"]
    D["kb_c_dial_face"] = D["kb_c_dial"] + (h * s2 if D["kb_race"] != "chamfer" else 0.0)
    D["kb_seat_c"] = (D["kb_rc"] + e / s2, zc - e / s2)                    # dial groove centre: beyond the ball centre, away from the dial
    D["kb_seat_c_knob"] = (D["kb_rc"] - e / s2, zc + e / s2)               # knob groove centre (chamfer race): mirror image
    D["kb_seat_w"] = math.sqrt(max(rho_s ** 2 - (dface + e) ** 2, 0)) if h > 0 else 0.0   # groove half-width at the face
    D["kb_ball_cap_w"] = math.sqrt(max(kR ** 2 - dface ** 2, 0)) if h > 0 else 0.0       # ball half-chord at the face
    D["kb_seat_contact"] = (D["kb_rc"] - k, zc + k)                         # 45° contact point on the dial (groove bottom)
    if D["kb_race"] != "chamfer":
        D["kb_zd0"], D["kb_zd1"] = D["kb_rt"] - D["kb_c_dial_face"], D["kb_r_collar"] - D["kb_c_dial_face"]
    # ---- v0.21 cone dial [Ed]: underside from the race top up at cone_deg to the lip; top parallel, from the well round the adapter
    # board up to a flat carrier seat that starts carr_seat_wall inside the carrier-magnet pocket ----
    T = math.tan(math.radians(D["cone_deg"])); c = math.cos(math.radians(D["cone_deg"]))
    D["cone_under_r0"] = D["dial_hub_od"] / 2 + D["gusset"]                 # race top (dial side), z_web0
    D["cone_lip_r"] = D["cone_under_r0"] + (D["z_lip0"] - D["z_web0"]) / T   # underside meets the flat lip underside
    # ---- v0.16 dial sensor (TMAG5273 face-down on a small board in a pocket through the dial web) over the knob ring magnet ----
    D["tm_z_floor"] = D["z_web0"] + D["tm_floor"]                          # package face rests on the pocket floor
    D["tm_z_elem"] = D["tm_z_floor"] + D["tm_pkg"][3]
    D["tm_z_board0"] = D["tm_z_floor"] + D["tm_pkg"][2]
    D["tm_gap"] = D["tm_z_elem"] - (D["z_web0"] - D["knob_run"])           # element -> ring top (knob under-web face)
    D["tm_gap_min"] = D["tm_gap"] - D["dial_lift"]
    if D["cart"]:   # v0.24 [Ed 3 Nov 12:41]: dial screen in a drop-in bezel cartridge
        _cart(D)
    else:
        _screen_v023(D, S, T, c)
    # ---- Hall arm (vernier) ----
    if D["hall_layout"] == "vernier":
        D["hv_bar_z0"] = D["hv_z_mag0"]
        D["hv_spoke_z0"] = max(D["tb_z_ball"] + D["tb_ball_d"] / 2, D["tb_cage_z0"] + D["tb_cage"][2]) + D["hv_spoke_clear"]
        # v0.17 rib: over the thrust cage the bottom stays at the spoke; past the cage OD + a web it drops to ha_rib_z_low
        D["ha_rib_z_cage"] = D["hv_spoke_z0"]
        D["ha_rib_r_step"] = D["tb_cage"][1] / 2 + D["tb_web_min"]   # 4.95 at the v0.16 cage (Ø8.6 + 0.65 web)
    _arc_mech(D)
    _split_mech(D)
    return D


def _screen_v023(D, S, T, c):
    """v0.15-v0.23 screen on the dial: Kingtech RM69330 panel on a printed carrier bonded on the dial shoulder, closed lip ring,
    diametral FPC service strap to J1 on the fixed adapter board."""
    # ---- screen (offset away from the FPC exit so nothing pokes past the knob OD) ----
    D["scr_r"] = S["od"] / 2
    reach = S["r_edge"] + (0 if S["rigid"] else S["bend"])
    # exact: points on an arc of radius rho (panel centre), |y| <= yh, stay inside R - margin when offset o >= rho*cos - sqrt(Rm^2 - y^2)
    Rm = D["R"] - D["edge_margin"]; D["cof_half"] = S["ledge_w"] / 2 - D["cof_inset"]
    cand = [(S["r_edge"], S["ledge_w"] / 2)] + ([] if S["rigid"] else [(S["r_edge"] + S["bend"], D["cof_half"])])
    raw = max([0.0] + [math.sqrt(rho * rho - yh * yh) - math.sqrt(max(Rm * Rm - yh * yh, 0)) for rho, yh in cand])
    D["scr_off"] = 0.0 if raw == 0 else math.ceil(raw / D["offset_step"] - 1e-9) * D["offset_step"]
    if D["screen_on_dial"] and D["lip_closed"]:   # v0.16 [Ed]: closed lip ring - offset balances far wall vs the wall outside the bend pocket
        D["scr_off"] = D["scr_off_opt"]
    D["scr_reach"] = reach - D["scr_off"]                                  # outermost screen point from the dial axis (tail side)
    D["scr_far"] = D["scr_r"] + D["scr_off"]                               # panel edge, far side
    D["tail_ang"] = 180.0                                                  # [A] FPC exit toward -X (away from the motor)
    if D["screen_on_dial"]:   # bonded: lip ID centred on the panel (eccentric by scr_off), no running gap
        D["lip_id"] = 2 * (D["scr_r"] + D["lip_bond_gap"]); D["lip_ctr_off"] = D["scr_off"]
    else:
        D["lip_id"] = 2 * (D["scr_far"] + D["run_gap"]); D["lip_ctr_off"] = 0.0
    D["lip_wall"] = D["R"] - (D["lip_id"] / 2 + D["lip_ctr_off"])          # thinnest lip (far side)
    D["lip_wall_near"] = D["R"] - (D["lip_id"] / 2 - D["lip_ctr_off"])
    # v0.16 wall outside the ledge + COF-bend pocket (same rule as interface.bend_reach; pocket = band + bend_clear)
    pts = [(S["r_edge"], S["ledge_w"] / 2)] + ([] if S["rigid"] else [(S["r_edge"] + S["bend"], -D["cof_half"] + 2 * D["cof_half"] * i / 48) for i in range(49)])
    D["bend_reach_ax"] = max(math.hypot(math.sqrt(max(r * r - y * y, 0)) - D["scr_off"], y) for r, y in pts)
    D["lip_wall_bend"] = D["R"] - D["bend_reach_ax"] - D["bend_clear"]
    D["z_back"] = D["z_top"] - S["t"]
    D["z_fpc0"] = D["z_back"] - S["fold"][2]
    D["z_screen_cut"] = D["z_holder0"] - D["dial_screen_gap"]
    if D["screen_on_dial"]:
        D["z_screen_cut"] = D["z_holder0"]                                 # carrier bonded on the dial shoulder
        D["lip_slot_w"] = S["ledge_w"] + 1.0                               # no travel widening: panel turns with the lip
        W = S["fold"][1]; rlim = D["lip_id"] / 2 - D["fpc_clear"]
        D["fold_x_outer"] = math.sqrt(max(rlim ** 2 - (W / 2) ** 2, 0)) - D["scr_off"]   # lip ID is panel-centred
        D["z_cup_top"] = D["z_holder0"] - D["carrier_run"]                 # fixed adapter cup stops under the carrier
    else:
        D["lip_slot_w"] = S["ledge_w"] + 2 * (D["R"] * math.radians(D["travel_deg"])) + 1.0
        W = S["fold"][1]; rlim = D["lip_id"] / 2 - D["fpc_clear"]           # fold corners inside the lip ID
        D["fold_x_outer"] = math.sqrt(max(rlim ** 2 - (W / 2) ** 2, 0))      # from the axis toward the tail
        D["z_cup_top"] = D["z_holder0"]
    D["cone_well_r"] = D["adapter_d"] / 2 + D["cone_well_clear"]
    D["cone_seat_r"] = D["carr_r"] - D["carr_mag"][0] / 2 - D["carr_seat_wall"]
    D["cone_top_z_well"] = D["z_screen_cut"] - (D["cone_seat_r"] - D["cone_well_r"]) * T
    D["cone_dial_wall"] = (D["cone_top_z_well"] - (D["z_web0"] + (D["cone_well_r"] - D["cone_under_r0"]) * T)) * c   # normal, everywhere
    def _seg(p, a, b):
        (px, py), (ax, ay), (bx, by) = p, a, b; dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        return math.hypot(px - ax - t * dx, py - ay - t * dy)
    under = [(D["dial_tube_od"] / 2, D["z_hub0"]), (D["dial_hub_od"] / 2, D["z_hub0"]), (D["cone_under_r0"], D["z_web0"]),
             (D["cone_lip_r"], D["z_lip0"])]
    D["cone_dial_corner"] = min(_seg((D["cone_well_r"], D["z_well_top"]), under[i], under[i + 1]) for i in range(3))   # under the board edge
    ad = D["adapter_fps"][D["b2b_at"]]
    D["j1_xy"] = (ad[1], ad[2])
    D["b2b_xy"] = (-ad[1], -ad[2]) if (D["screen_on_dial"] and D["b2b_flip"]) else (ad[1], ad[2])
    # ---- v0.16 carrier retention ----
    pol = lambda r, a: (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
    D["carr_mag_xy"] = pol(D["carr_r"], D["carr_mag_ang"]); D["carr_pin_xy"] = pol(D["carr_r"], D["carr_pin_ang"])
    def _dip(d, h):
        return D["hv_br"] / (4e-7 * math.pi) * math.pi * (d / 2e3) ** 2 * (h / 1e3)   # A·m²
    md_, mh_ = D["carr_mag"]; m_dip = _dip(md_, mh_) + _dip(*D["carr_mate"])   # attracting pair, moments add [Ed]
    if D["rel_sensor"]:
        d_u3 = math.dist(D["carr_mag_xy"], D["tm_xy"]) / 1e3                               # to the dial TMAG5273 (co-rotating)
        D["carr_stray_to"], D["carr_stray_rng"] = "dial TMAG5273", D["tm_range_mt"]
    else:   # v0.16b: nearest 3D sensor is the Hall-row TMAG5273 on the PCB (fixed); carrier magnet z ~ holder base
        k = D["hv_mid"]["idx"]; r, a = D["hv_r"][k], math.radians(D["hv_phi_s"][k])
        d_u3 = math.dist((*D["carr_mag_xy"], D["z_holder0"] - D["carr_mag"][1] / 2), (r * math.cos(a), r * math.sin(a), D["hv_mid"]["elem_z"])) / 1e3
        D["carr_stray_to"], D["carr_stray_rng"] = "Hall-row TMAG5273 (H3)", D["hv_mid"]["range_mt"]
    D["carr_stray_mt"] = 1e3 * 1e-7 * 2 * m_dip / d_u3 ** 3                                  # on-axis dipole (worst case)

    # ---- v0.15 diametral FPC strap (rotating B2B end <-> stationary J1 end) ----
    b2b_h = S["b2b"][2] if S["b2b"] else 0.0
    D["z_b2b0"] = D["z_fpc0"] - b2b_h
    tallest = max(D["z_rod_top"], D["z_board_top"] + max(h for (_, _, h) in D["adapter_env"].values()))
    D["strap_z0"] = tallest + D["strap_clear"]; D["strap_z1"] = D["z_b2b0"]
    D["strap_L"] = math.hypot(D["b2b_xy"][0] - D["j1_xy"][0], D["b2b_xy"][1] - D["j1_xy"][1])
    th = math.radians(D["travel_deg"])
    D["strap_kappa"] = th / D["strap_L"] if D["strap_L"] > 0 else 0.0     # clamped-clamped, ends on a diameter: uniform curvature
    D["strap_R"] = 1 / D["strap_kappa"] if D["strap_kappa"] else float("inf")
    D["strap_strain_pct"] = 100 * D["strap_t"] / 2 * D["strap_kappa"]
    D["strap_end_move"] = math.hypot(*D["b2b_xy"]) * th


def pol(r, a):
    """(x, y) of radius r at angle a (degrees)."""
    return (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))


def _seg_d(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b; dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def _poly_d(p, P):
    return min(_seg_d(p, P[i], P[i + 1]) for i in range(len(P) - 1))


def _rdp(P, tol):
    """Ramer-Douglas-Peucker: drop points within tol of the chord."""
    if len(P) < 3: return list(P)
    d = [_seg_d(q, P[0], P[-1]) for q in P[1:-1]]; i = max(range(len(d)), key=d.__getitem__)
    if d[i] <= tol: return [P[0], P[-1]]
    return _rdp(P[:i + 2], tol)[:-1] + _rdp(P[i + 1:], tol)


def cart_under(D):
    """Dial underside (unchanged, Danny's 30° cone) as an (r, z) polyline, tube to the outer wall."""
    rh, g = D["dial_hub_od"] / 2, D["gusset"]
    hub = [(D["dial_tube_od"] / 2, D["z_hub0"]), (rh, D["z_hub0"])] + ([(rh, D["z_web0"] - g)] if D["z_hub0"] < D["z_web0"] - g - 1e-6 else [])
    return hub + [(D["cone_under_r0"], D["z_web0"]), (D["cone_lip_r"], D["z_lip0"]), (D["ct"]["outer_r"], D["z_lip0"])]


def _cart(D):
    """v0.24 [Ed 3 Nov 12:28-12:58]: the Waveshare Z132A2441 is glued up into a printed bezel (the whole outside of the dial) that drops
    onto the dial, plugging in on the way down; the dial board (PCBA, receptacle on top, ESP32 and lights underneath) sits in a pocket
    in the dial top at Waveshare's depth; a short strap loop joins it to the fixed rod-link board. Panel frame for x, y and angles."""
    zp, db, ct, bz, ls = D["zp"], D["db"], D["ct"], D["bz"], D["ls"]
    T = math.tan(math.radians(D["cone_deg"]))
    # ---- heights (lens back = the datum Waveshare's numbers hang off) ----
    zb = D["lens_back"] = D["z_top"] - zp["lens_t"]                       # 59.90
    D["lens_step_z"] = D["z_top"] - zp["step_t"]                          # 60.65: the bezel laps the shoulder here
    D["lcm_z0"] = zb - zp["lcm_t"]                                         # 58.90
    D["patch_z0"] = zb - zp["patch_back"]                                  # 57.75
    D["bend_z"] = (zb - zp["bend_back"], zb - zp["bend_top"])              # 58.55-59.60
    D["tab_z"] = (zb - zp["tab_back"], zb - zp["bend_top"])
    D["leg_z0"] = zb - zp["leg_back"]                                      # 56.40 lower leg underside
    D["db_z1"] = zb - db["behind"]                                         # 55.90 board top = the dial land
    D["db_z0"] = D["db_z1"] - db["t"]                                      # 55.10 board underside = the ledge
    D["rec_z1"] = D["db_z1"] + db["rec"][4]                                # 56.45 receptacle top
    # v0.25 [Ed 19:12 item 2]: the ribs seat the cartridge; the plug stands plug_standoff off full mate (v0.29 [Ed 4 Nov 12:37]: 0,
    # fully mated, the pad glued with the ribs seated and the plug home)
    D["plug_flex_z"] = D["db_z1"] + zp["mated"] + bz["plug_standoff"]      # 56.80 plug's flex (56.70 at full mate)
    D["plug_face_z"] = zb - zp["plug_face"] + bz["plug_standoff"]          # 56.18 plug mating face (56.08 [S] at full mate)
    D["plug_engage"] = D["rec_z1"] - D["plug_face_z"]                      # plug inside the receptacle
    D["plug_xy"] = ((zp["plug"][0] + zp["plug"][1]) / 2, (zp["plug"][2] + zp["plug"][3]) / 2)
    D["plug_align"] = math.dist(D["plug_xy"], db["rec"][:2])               # plan offset plug vs receptacle (glued in place seated)
    # ---- bezel ----
    D["bz_bore_r"], D["bz_seat_r"], D["bz_lap_r"] = bz["bore_d"] / 2, bz["seat_d"] / 2, bz["lap_d"] / 2
    D["bz_wall"] = D["R"] - D["bz_bore_r"]                                 # 1.5
    D["pad_z"] = (D["plug_flex_z"] + zp["flex_t"], zb - bz["pad_top"])     # 56.8-58.3
    D["bz_lap"] = (zp["lens_d"] - bz["lap_d"]) / 2                         # lens shoulder under the lap (radial)
    uturn_corner = max(math.hypot(zp["uturn_x"], y) for y in zp["tail_y"])
    D["cart_reach"] = {"U-turn corner": uturn_corner, "bottom COF bend": zp["bend_r"], "top tab": zp["tab_r"], "lens": zp["lens_d"] / 2}
    D["cart_reach_max"] = max(D["cart_reach"].values())
    D["bz_bore_clear"] = D["bz_bore_r"] - D["cart_reach_max"]
    D["ct_bore_clear"] = D["bz_bore_r"] - ct["outer_r"]                    # bezel bore over the dial's outer wall
    _cart_mag_key(D)   # v0.25 [Ed 18:26]: sideways magnet pairs, key + seat ribs (no bosses, no pins)
    # ---- dial top: well floor, then the pocket on a 2.0 normal wall over the unchanged underside, ledge, land ----
    U = cart_under(D); w = ct["wall"]
    D["ct_land_r"] = ct["pocket_r"] + ct["ledge_w"]                        # 17.30
    pts = [(U[i][0] + (U[i + 1][0] - U[i][0]) * k / 200, U[i][1] + (U[i + 1][1] - U[i][1]) * k / 200) for i in range(len(U) - 1) for k in range(201)]
    def z_floor(r):   # top of the union of the w-discs round the underside at radius r (the 2.0 offset), never under the well floor
        return max([D["z_well_top"]] + [z + math.sqrt(w * w - (r - q) ** 2) for q, z in pts if abs(r - q) < w])
    ri = D["dial_tube_id"] / 2; n = int((ct["pocket_r"] - ri) / 0.05)
    top = [(ri + (ct["pocket_r"] - ri) * i / n, z_floor(ri + (ct["pocket_r"] - ri) * i / n)) for i in range(n + 1)]
    D["ct_top"] = [(round(r, 4), round(z, 4)) for r, z in _rdp(top, 0.002)]   # (r, z) from the tube ID out to the pocket edge
    # minimum wall of the pocket floor over the underside, and where
    wall = [(_poly_d(p, U), p) for p in top if p[1] > D["z_well_top"] + 1e-6]
    D["ct_wall"], at = min(wall)
    near = [p[0] for d, p in wall if d < D["ct_wall"] + 0.005]
    D["ct_wall_at"] = (min(near), max(near))
    D["ct_floor_edge"] = top[-1][1]                                        # pocket floor at the pocket edge (54.09)
    D["ct_land_w"] = ct["outer_r"] - D["ct_land_r"]                        # 1.9
    D["db_r"] = db["d"] / 2
    D["db_on_ledge"] = min(D["db_r"], D["ct_land_r"]) - ct["pocket_r"]     # board rim resting on the ledge
    D["db_to_step"] = D["ct_land_r"] - D["db_r"]                           # board edge to the land step
    # ---- strap loop: a ribbon standing on edge in the vertical plane through its two ends ----
    (ax_, ay_), (bx_, by_) = ls["a"], ls["b"]
    L = math.hypot(bx_ - ax_, by_ - ay_); ux, uy = (bx_ - ax_) / L, (by_ - ay_) / L
    D["ls_L"], D["ls_u"] = L, (ux, uy)
    D["ls_run_z"] = (D["z_rod_top"] + ls["over_nut"], D["z_rod_top"] + ls["over_nut"] + ls["w"])   # 52.4-54.4 over the nut
    D["ls_z_a"], D["ls_z_b"] = D["z_board_top"], D["db_z0"]                # fixed foot on the rod-link board top, moving foot under the board
    # the end on the dial board turns θ about the axis: it moves sideways (out of the ribbon plane) by its lever arm x θ and turns θ.
    # Clamped at the fixed end: w = c2 s^2 + c3 s^3, w(L) = δ, w'(L) = θ -> curvature at the two ends; strain = t/2 x κ.
    s_ax = -(ax_ * ux + ay_ * uy)                                          # axis position along the ribbon from the fixed end
    th = math.radians(D["travel_deg"]); dlt = (L - s_ax) * th
    c3 = (th * L - 2 * dlt) / L ** 3; c2 = (3 * dlt - th * L) / L ** 2
    D["ls_c"] = (c2 / th, c3 / th)                                         # per radian (bent shape for the swept checks)
    D["strap_kappa"] = max(abs(2 * c2), abs(2 * c2 + 6 * c3 * L))
    D["strap_R"] = 1 / D["strap_kappa"] if D["strap_kappa"] else float("inf")
    D["strap_strain_pct"] = 100 * D["strap_t"] / 2 * D["strap_kappa"]
    D["strap_end_move"] = dlt
    D["strap_L"] = L; D["strap_z0"], D["strap_z1"] = D["ls_run_z"]; D["strap_lines"] = ls["lines"]
    # ---- magnet stray field at the Hall row (dipoles; the magnets turn with the dial over a fixed sensor row) ----
    # v0.25: the pairs face sideways (radial moments, both pointing out: attracting across the gap)
    m = D["hv_br"] / (4e-7 * math.pi) * math.pi * (bz["mag"][0] / 2e3) ** 2 * (bz["mag"][1] / 1e3)   # A·m² each, radial (out)
    mags = []
    for a, (rd, zd), (rs, zs) in D["cart_mags"]:
        am = a - D["mech_rot"]                                             # mechanism frame
        mags += [(rd, am, zd), (rs, am, zs)]
    def field(p, th_deg):
        b = [0.0, 0.0, 0.0]
        for r, a, z in mags:
            t = math.radians(a + th_deg); u = (math.cos(t), math.sin(t), 0.0)
            q = (r * u[0], r * u[1], z)
            v = [(p[i] - q[i]) / 1e3 for i in range(3)]; rr = math.sqrt(sum(x * x for x in v)); n_ = [x / rr for x in v]
            mn = sum(u[i] * n_[i] for i in range(3)); f = 1e-7 * m / rr ** 3
            for i in range(3): b[i] += f * (3 * mn * n_[i] - u[i])
        return tuple(x * 1e3 for x in b)                                   # mT
    res = []
    for i, (r, a) in enumerate(zip(D["hv_r"], D["hv_phi_s"])):
        p = (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), D["hv_z_elems"][i])
        Bs = [field(p, t) for t in (-D["travel_deg"], 0.0, D["travel_deg"])]
        bmax = max(math.sqrt(sum(x * x for x in b)) for b in Bs)
        dB = max(math.dist(Bs[0], Bs[1]), math.dist(Bs[2], Bs[1]))      # change over ±travel: what the Hall row could read as angle
        rng = D["hv_mid"]["range_mt"] if (D["hv_mid"] and i == D["hv_mid"]["idx"]) else D["hv_sensor"]["range_mt"]
        res.append((bmax / rng, bmax, i, rng, dB))
    _, D["carr_stray_mt"], k_, D["carr_stray_rng"], D["cart_stray_dB"] = max(res)
    D["carr_stray_to"] = f"Hall-row sensor H{k_ + 1} ({D['hv_parts'][k_].split()[0]})"
    D["cart_stray_n"] = len(mags)
    # ---- v0.25 [Ed 18:12] dial split at the top of the tube ----
    s = D["dsp"]
    if s["on"]:
        rt, ri = D["dial_tube_od"] / 2, D["dial_tube_id"] / 2
        D["dsp_z0"] = D["z_hub0"]                                          # the dish's underside = the split
        D["dsp_z1"] = D["z_well_top"] - s["top_below"]                     # tube end
        D["dsp_engage"] = D["dsp_z1"] - D["dsp_z0"]
        D["dsp_r_sock"] = rt + s["glue"]
        D["dsp_flat_d"] = rt - s["flat"]                                   # flat's distance from the axis
        D["dsp_flat_ang"] = D["ha_ang0"] if s["flat_ang"] is None else s["flat_ang"]
        D["dsp_tube_wall_flat"] = D["dsp_flat_d"] - ri
        D["dsp_dish_wall"] = D["dial_hub_od"] / 2 - D["dsp_r_sock"]       # thinnest: at the dish's underside, hub OD to the socket
        D["dsp_bond_area"] = 2 * math.pi * rt * D["dsp_engage"]
        D["dsp_bond_tau"] = s["T_design"] / (2 * math.pi * rt * rt * D["dsp_engage"])   # MPa (N·mm over mm³)
    # ---- names the v0.23 renders / report read ----
    D["scr_off"] = 0.0; D["lip_wall"] = D["bz_wall"]; D["lip_id"] = bz["bore_d"]; D["scr_r"] = zp["lens_d"] / 2
    D["z_back"] = D["lcm_z0"]; D["z_screen_cut"] = D["db_z0"]


def _pair_force(d, h, gap, dz, br, dy=0.0, n_r=8, n_t=32):
    """Two Ø d x h magnets on one axis (x), faces gap apart, the second centred dz higher, poles attracting. Surface-charge
    model (uniform M = Br/µ0, µr = 1; each end face a sheet ±M, discretised into rings x sectors). Returns the force on the
    second magnet (Fx along the axis, away from the first; Fy sideways, for a dy offset; Fz up), N."""
    pts, w = [], []
    for i in range(n_r):
        r0, r1 = d / 2 * i / n_r, d / 2 * (i + 1) / n_r; rm = (r0 + r1) / 2
        for k in range(n_t):
            t = 2 * math.pi * (k + 0.5) / n_t
            pts.append((rm * math.cos(t), rm * math.sin(t))); w.append(math.pi * (r1 * r1 - r0 * r0) / n_t)
    import numpy as np
    P = np.array(pts); W = np.array(w)
    def faces(cx, cy, cz):
        out = []
        for fx, sg in ((cx + h / 2, 1.0), (cx - h / 2, -1.0)):
            out.append((np.column_stack([np.full(len(P), fx), cy + P[:, 0], cz + P[:, 1]]), sg * W))
        return out
    A = faces(-h / 2, 0.0, 0.0); B = faces(gap + h / 2, dy, dz)
    F = np.zeros(3)
    for pb, qb in B:
        for pa, qa in A:
            dd = (pb[:, None, :] - pa[None, :, :]) * 1e-3
            r3 = np.linalg.norm(dd, axis=2) ** 3
            F += ((qb[:, None] * qa[None, :])[:, :, None] * dd / r3[:, :, None]).sum(axis=(0, 1))
    F *= br ** 2 / (4 * math.pi * 4e-7 * math.pi) * 1e-12
    return float(F[0]), float(F[1]), float(F[2])


def _cart_mag_key(D):
    """v0.25 [Ed 18:26]: one magnet in the dial's outer wall facing out, its partner in the bezel skirt facing in across the 0.3
    gap, mag_dz above it (attracting); a key rib on the skirt's inside in a slot in the dial wall, plus two seat ribs [A]; the rib
    bottoms are the axial seat [Ed 19:12 item 2]. Panel frame."""
    bz, ct, zp = D["bz"], D["ct"], D["zp"]
    d, h = bz["mag"]; dp = d + bz["mag_press"]; ro, rb = ct["outer_r"], D["bz_bore_r"]
    zd = (D["z_lip0"] + D["db_z1"]) / 2; zs = zd + bz["mag_dz"]           # dial magnet centred in the outer wall
    rd, rs = ro - h / 2, rb + h / 2
    D["cart_mags"] = [(a, (rd, zd), (rs, zs)) for a in bz["mag_angs"]]
    D["cm_gap"] = rb - ro
    D["cm_skin_out"] = D["R"] - (rb + h)                                   # skirt skin outside the bezel magnet
    D["cm_skin_dial"] = min(D["db_z1"] - (zd + dp / 2), zd - dp / 2 - D["z_lip0"])   # dial wall over / under its pocket
    fr, _fy, fz = _pair_force(d, h, D["cm_gap"], bz["mag_dz"], D["hv_br"])
    D["cm_F_pair"] = (fr, fz)                                              # on the bezel magnet: fr < 0 = pulled in, fz < 0 = down
    n = len(bz["mag_angs"]); D["cm_hold"] = -fz * n
    # radial and tangential stiffness of one pair (finite differences), then the ring of n pairs (n >= 3, even spacing): K = n/2 (kx + ky)
    e = 0.02
    kx = (_pair_force(d, h, D["cm_gap"] + e, bz["mag_dz"], D["hv_br"])[0] - _pair_force(d, h, D["cm_gap"] - e, bz["mag_dz"], D["hv_br"])[0]) / (2 * e)
    ky = (_pair_force(d, h, D["cm_gap"], bz["mag_dz"], D["hv_br"], dy=e)[1] - _pair_force(d, h, D["cm_gap"], bz["mag_dz"], D["hv_br"], dy=-e)[1]) / (2 * e)
    D["cm_k_pair"] = (kx, ky)
    D["cm_K_ring"] = n / 2 * (kx + ky)                                     # dF/dx of the ring, N/mm: > 0 = de-centring (attracting pairs)
    D["cm_mass_g"] = 8.0                                                   # [A, v0.24 doc] cartridge (bezel, glass, panel, flex, pad) ~8 g
    # ---- key + seat ribs, slots in the dial's outer wall ----
    D["rib_z0"] = D["db_z1"] - bz["slot_depth"]                            # rib bottom = slot floor = the axial seat
    D["cart_ribs"] = [(a, bz["rib_clear"][0 if i == 0 else 1], "key" if i == 0 else "seat") for i, a in enumerate(bz["rib_angs"])]
    D["rib_slot_r0"] = bz["rib_r_in"] - bz["slot_r_clear"]
    D["rib_engage_r"] = ro - bz["rib_r_in"]                                # rib inside the slot, radially
    D["rib_floor_wall"] = D["rib_z0"] - D["z_lip0"]                        # dial material under the slot floor
    rc = (bz["rib_r_in"] + ro) / 2
    D["rib_F"] = D["dsp"]["T_design"] / rc                                 # N on the key at the dial design torque
    D["rib_bearing"] = D["rib_F"] / (bz["slot_depth"] * D["rib_engage_r"])
    D["rib_inner_min"] = bz["rib_r_in"]


def bar_samples(D, n=8):
    """Centreline of the Hall magnet bar (pads + the links between them), as (r, angle) points. Same sampling as the
    cradle slot (base_drive hall_slot), which cuts hv_pad_r + its own clearance round these points swept ±travel."""
    rs, ps = D["hv_r"], D["hv_phi_m"]
    pts = []
    for i, (r, a) in enumerate(zip(rs, ps)):
        if i:
            r0, a0 = rs[i - 1], ps[i - 1]
            pts += [(r0 + (r - r0) * k / n, a0 + (a - a0) * k / n) for k in range(1, n)]
        pts.append((r, a))
    return pts


def bar_edge(D, r, side):
    """Angle where the Hall bar's swept envelope (pads radius hv_pad_r, ±travel) starts at radius r, on side -1 (low angles,
    toward the encoder) or +1 (high angles, toward the lever). None if the bar does not reach this radius."""
    pr, T = D["hv_pad_r"], D["travel_deg"]
    best = None
    for rs, a in bar_samples(D):
        if abs(r - rs) >= pr:
            continue
        c = (r * r + rs * rs - pr * pr) / (2 * r * rs)
        e = a + side * (T + math.degrees(math.acos(max(-1.0, min(1.0, c)))))
        best = e if best is None else (min(best, e) if side < 0 else max(best, e))
    return best


def _arc_mech(D):
    """v0.21 [Ed 2 Nov]: one spring-ball detent on the arc at the arm's end, three ball tracks (big, small, big) under the arm.
    Everything is in the mechanism frame; angles in degrees. The tracks roll θ/2 against both races, so each groove spans the
    train plus ±travel/2 plus the end clearance; the groove end on the slot side sits tk_bar_clear off the bar's swept edge."""
    R2D = math.degrees
    on = D["arm_det"] == "arc" and D["hall_layout"] == "vernier" and D["fan_on"]
    D["ad_r"] = D["ad_ang"] = D["ad_z_land"] = None
    D["tk"], D["tk_webs"] = [], []
    if not on:
        return
    T = D["travel_deg"]; rb = D["det_ball"] / 2
    # ---- detent on the arc: a raised land on the fan, flush with the rib top, so the ball path can cross the rib ----
    D["ad_r"] = D["fan_r0"] + D["ad_r_frac"] * (D["fan_r1"] - D["fan_r0"])
    D["ad_ang"] = D["ha_ang0"] + D["ad_off"]
    D["ad_z_land"] = D["ha_rib_z_top"]
    D["ad_land_r0"] = D["ad_r"] - rb - D["ad_land_edge"]
    D["ad_land_r1"] = D["ad_r"] + rb + D["ad_land_edge"]
    D["ad_land_half"] = T + R2D((rb + D["ad_land_edge"]) / D["ad_r"])
    D["ad_rim"] = math.sqrt(max(rb * rb - (rb - D["det_dimple"]) ** 2, 0.0))          # dimple rim half-width on the land top
    D["ad_pitch"] = 2 * D["ad_r"] * math.sin(math.radians(D["det_deg"]) / 2)          # chord between neighbouring dimples
    D["ad_flat"] = D["ad_pitch"] - 2 * D["ad_rim"]
    D["ad_stop_off"] = D["ad_r"] * math.radians(T - D["det_deg"])                    # ball off the end-dimple centre at the hard stop
    # ---- ball tracks ----
    b, s, nb = D["bt_ball"], D["tk_small"], D["tk_n_big"]
    g, land = D["bt_groove_r"], D["tk_land"]
    # web edge keeps the pinion-tip gap (+0.02 so the swept check does not sit on its target)
    r_top = D["enc_cd"] - D["d_pin_tip"] / 2 - D["tgt"]["hall_vs_pinions"] - 0.02 - g - land
    seq = [b if i % 2 == 0 else s for i in range(2 * nb - 1)]
    tk = []
    for k, (side, row) in enumerate(D["tk_tracks"], 1):
        r = r_top - row * D["tk_row_pitch"]
        step = R2D(2 * math.asin((b + s) / 2 / (2 * r)))                                # big-to-small centre angle (touching)
        offs = [(i - (len(seq) - 1) / 2) * step for i in range(len(seq))]
        half = T / 2 + offs[-1] + R2D((b / 2 + D["tk_end_clear"]) / r)                   # groove half-span, the same in both races
        edge = bar_edge(D, r, side)
        ang = edge + side * (R2D(D["tk_bar_clear"] / r) + half)
        land_a = R2D(land / r)
        lo, hi = (ang - half - land_a, D["ha_ang0"]) if side < 0 else (D["ha_ang0"], ang + half + land_a)
        tk.append(dict(k=k, side=side, row=row, r=r, ang=ang, half=half, offs=offs, dias=seq, edge=edge))
        D["tk_webs"].append((r - g - land, r + g + land, lo, hi))   # arm web carrying this track's groove, joined to the rib
    D["tk"] = tk
    D["tk_r_top"] = r_top
    D["tk_web_z0"], D["tk_web_z1"] = D["fan_z0"], D["fan_top"]
    lo_side = [w for w, t in zip(D["tk_webs"], tk) if t["side"] < 0]
    # one spoke from the dial tube to the free end of the encoder-side web (the lever-side web hangs off the rib and the lever)
    if lo_side:
        r0 = min(w[0] for w in lo_side)
        D["tk_spoke_ang"] = min(w[2] for w in lo_side) + R2D(D["sl_w"] / 2 / r0)
        D["tk_spoke_r1"] = r0 + 0.01
    else:
        D["tk_spoke_ang"] = D["tk_spoke_r1"] = None


def _split_mech(D):
    """v0.22 [Ed 2 Nov 15:27]: one detent on its own spoke (sp_ang, sp_r) with a big/small/big ball train directly under the
    detent ball, between a fixed pedestal (base_drive) and the flange underside. Reuses the arc keys the base_drive and the
    checks already read (ad_r, ad_ang, ad_z_land, tk); tk entries carry their own z."""
    D["sp_ped"] = D["sp_hw"] = None
    D.setdefault("ad_land_half", None)
    if not (D["arm_det"] == "split" and D["hall_layout"] == "vernier" and D["fan_on"]):
        return
    R2D = math.degrees; T = D["travel_deg"]; rb = D["det_ball"] / 2; g = D["bt_groove_r"]; land = D["tk_land"]
    r, a = D["sp_r"], D["sp_ang"]
    D["ad_r"], D["ad_ang"], D["ad_off"] = r, a, 0.0
    z_fu = D["sp_flange_z0"]; z_ball = z_fu - D["bt_up"]; z_ped = z_ball - D["bt_up"]
    z_land = z_ball + g + D["sp_core"] + D["det_dimple"]
    D["sp_z_fu"], D["sp_z_ball"], D["sp_z_ped"], D["ad_z_land"] = z_fu, z_ball, z_ped, z_land
    D["ad_rim"] = math.sqrt(max(rb * rb - (rb - D["det_dimple"]) ** 2, 0.0))
    D["ad_pitch"] = 2 * r * math.sin(math.radians(D["det_deg"]) / 2)
    D["ad_flat"] = D["ad_pitch"] - 2 * D["ad_rim"]
    D["ad_stop_off"] = r * math.radians(T - D["det_deg"])
    # train: balls touching, centred under the detent; both races move θ apart, so the balls roll θ/2
    b, sm, nb = D["bt_ball"], D["tk_small"], D["tk_n_big"]
    seq = [b if i % 2 == 0 else sm for i in range(2 * nb - 1)]
    pos = [0.0]
    for i in range(1, len(seq)):
        pos.append(pos[-1] + (seq[i - 1] + seq[i]) / 2)
    c = (pos[0] + pos[-1]) / 2; pos = [q - c for q in pos]
    offs = [R2D(2 * math.asin(q / (2 * r))) for q in pos]
    half_g = T / 2 + offs[-1] + R2D((seq[-1] / 2 + D["tk_end_clear"]) / r)   # same rule as the v0.21 tracks
    hw = max(rb + D["ad_land_edge"], g + land)
    land_half = T + R2D((rb + D["ad_land_edge"]) / r)
    D["sp_hw"] = hw
    D["ad_land_half"] = max(land_half, half_g + R2D(land / r))       # flange half-angle (land + groove web)
    D["ad_land_r0"], D["ad_land_r1"] = r - hw, r + hw
    D["sp_ped"] = (r - g - land, r + g + land, half_g + R2D(land / r))   # pedestal r0, r1, half-angle (base_drive builds it)
    D["tk"] = [dict(k=1, side=0, row=0, r=r, ang=a, half=half_g, offs=offs, dias=seq, edge=None, z=z_ball)]
    D["tk_webs"] = []
    D["tk_spoke_ang"] = D["tk_spoke_r1"] = None
    D["tk_web_z0"], D["tk_web_z1"] = D["fan_z0"], D["fan_top"]
