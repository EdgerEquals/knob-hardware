"""Enclosure (case) v0.1 — own params + derive.

One-piece SLA shell in PCBWay UTR-8100 clear resin. The faceplate is the Eurorack panel
(integrated; no separate plate, no acrylic). Knob frame: dial axis = Z, Z above the main-PCB
front, +X = motor, +Y = panel top.

Geometry that belongs to the other two open branches is snapshotted here, not imported
(those trees are not on param-dev, and this sub cannot edit them):

* Joystick v0.4 bezel / faceplate contract — commit bce854b54acdef8a2a4c86b35ff4460e1a8e460a
  (origin/sub/joystick-v04). Screen DWO DO0164FMST05, 1.2 mm lip, 0.90 mm overlap,
  place_y from the same clearance rule as jsparam.derive.
* Knob v0.17 OD — commit 00502746fa2fb2aaef44580e1b9edbcc907f73e7 (origin/sub/assembly-v017).
  Design notes: minimum Ø41.641, drawn Ø41.65. The joystick sizes the plan to Ø41.70.
  z_knob_top is 52.5 on both that branch and param-dev (z_glass 56.8 − lip 4.0 − knob_run 0.3).
  Faceplate: since 2 Nov the case reads the interface faceplate_z / faceplate_z_back (v0.18,
  knob_proud 18.0 from the screen top), not its own knob_proud.

The live interface knob_od (v0.16b Ø40.85 on param-dev) is read as well; the opening uses
whichever is larger, so a later merge cannot make the hole smaller than the knob.

Tags: [Ed] Ed's decision, [L] module scope (knob-module-v1 panel layout), [S] datasheet / PCBWay,
[K] KiCad, [A] assumed, [J] joystick v0.4 snapshot, [N] knob v0.17 snapshot.
"""
import json
import math
import os

P = dict(
    case_rev="v0.1",
    joystick_commit="bce854b54acdef8a2a4c86b35ff4460e1a8e460a",   # [J] sub/joystick-v04
    knob_commit="00502746fa2fb2aaef44580e1b9edbcc907f73e7",       # [N] sub/assembly-v017
    # ---- Eurorack panel, from the module scope unless a wall will not fit ----
    # 10HP actual width in the scope is 50.50 = 10 × 5.08 − 0.30 (Doepfer table, layout v2+).
    # 3U height 128.5. Rail zones are the outer 10 mm behind the panel (sdiy.info).
    hp_scope=10,            # [L] locked module width, kept as the preference
    hp_pitch=5.08,          # [L] mm per HP
    hp_gap=0.30,            # [L] Doepfer panel is n × pitch − this (10 HP → 50.50)
    panel_h=128.5,         # [L] 3U
    rail_clear=10.0,       # [L] keep the body out of the rail strips
    lab_ring_slope=0.3,    # [A] v0.19b: faceplate ring top falls this much outward, so drips off the O-ring run away from the hole
    rail_inset=7.5,        # [L] screw station, 7.5 from the panel edge (layout v5)
    rail_edge=3.0,         # [L] screw centre from the panel top / bottom
    rail_hole_d=3.2,       # [L] Ø3.2
    rail_keep_d=6.0,       # [Ed 2 Nov] keep-out round each rail screw on the face: ISO 7092 M3 nylon washer Ø6 × 0.5 (small series)
                           # under an ISO 7045 M3 pan head (Ø5.6). Protects the polished resin face; costs no finger room vs a Ø6 head
    rail_washer="ISO 7092 M3 nylon washer, small series, Ø6.0 × 0.5",   # [Ed 2 Nov]
    rail_float=0.20,       # [A] review fix: M3 screw in the Ø3.2 hole plus washer on the screw
    # ---- resin ----
    # UTR-8100: tensile 41.6 MPa, elongation 9%, density 1.3 g/cm³. SLA min wall 0.8.
    # Plain clear resin, no tint [Ed]. Only the front face is polished; every other face is as-printed.
    wall=2.5,              # [Ed] nominal wall, about 2.5
    sla_min=0.8,           # [S] PCBWay SLA minimum wall
    case_rho=1.3e-3,       # [S] g/mm³ (1.3 g/cm³)
    resin_rgb=(236, 240, 242),  # [Ed] untinted clear; a faint cool grey so it reads on white
    resin_opacity=0.20,   # [A] Quick Look / render opacity, no dye
    resin_rough=0.55,     # [Ed] as-printed faces. The front face alone is polished (resin_face_rough).
    resin_face_rough=0.08,# [Ed] polished front face only
    finish_front="polished",     # [Ed]
    finish_other="as-printed",   # [Ed]
    glow_rgb=(188, 240, 170),  # [A] Shimicoat strontium aluminate, green, drawn heavier than the real film
    glow_t=0.35,           # [A] drawn coat thickness so the brushed faces show; the real coat is a film
    glow_gap=0.30,         # [A] air between the drawn coat and the wall (keeps the solids apart)
    # ---- knob opening (v0.17 / joystick plan) ----
    knob_od_design=42.0,   # [Ed] glass + caps, about Ø42. Opening uses the larger of this and the live knob.
    z_knob_snap=52.5,      # [N] z_knob_top on v0.16b and v0.17, until cad_constraints carries it
    knob_rad_clear=0.20,   # [A] = one SLA tolerance, radial, dial and knob share this hole
    # ---- joystick bezel (v0.4 snapshot; formulas match jsparam.derive) ----
    scr_w=41.62,           # [J] DO0164FMST05 landscape width
    scr_h=26.74,           # [J]
    scr_t=1.5,             # [J]
    scr_below_knob=5.0,    # [J][Ed] screen top 5 mm under the knob top, before the 0.30 pad
    bz_lip=1.2,            # [J][Ed] lip, max 1.5
    bz_t=1.2,              # [J][Ed] bezel thickness
    bz_max=1.5,            # [Ed] lip and bezel thickness must not exceed this
    fp_overlap=0.90,       # [J] lip covers the faceplate at rest
    up_gap=0.55,           # [J] review fix 2 Nov: the face is one flat plane (no rebate), so the joystick block floats press travel
                           # (0.35) + one SLA tolerance above it (v0.4: 0.02 over a rebate the case never had)
    roof_pad=0.30,         # [J] glass sits on the spring pads; raises the glass 0.30
    sw_tilt=0.25,          # [J][S] SKRHADE010 tilt travel
    sw_push=0.15,          # [J][S] centre press
    grip_h=5.0,            # [Ed 2 Nov] joystick bezel is a grip block at least 5 mm tall (replaces the 1.2 mm bezel thickness)
    joy_rule="rail",       # [Ed 2 Nov] "rail": the joystick sits as high as the top rail screw keep-out allows; "knob": v0.4,
                           # as close to the knob as the process stack allows
    finger_min=5.0,        # [Ed 2 Nov] plan gap from the knob glass to the joystick bezel at rest, at least this
    tol_sla=0.20,          # [J][S] SLA, wide end of PCBWay ±0.1–0.2
    tol_mjf=0.25,          # [J][S] carrier and knob are MJF; joystick's knob clearance is 2 × this
    hole_corner_r=1.2,     # [A] rounded joystick opening (material left in the corners)
    edge_r_ratio=0.16,     # [Ed] outside edge radius / wall; the only break in the plain box
    fp_corner_r=2.0,       # [A] replaced in derive by edge_r_ratio × wall
    fillet_r=1.2,          # [A] kept for the scanner bead; the plain box has no bead when the scanner is off
    # ---- scanner (665 nm). Parked: nothing is built or checked while this is false. ----
    scanner_enabled=False, # [Ed] off until there is room beside the bottom TFT
    scan_motor_d=8.0,      # [A] FLAG: assumed small coreless / coin-style can, no catalogue part
    scan_motor_len=12.0,   # [A] FLAG
    scan_motor_clear=0.80, # [A] air from the can to the nearest wall or shelf
    mirror_d=16.0,         # [A] FLAG: disc on the motor shaft, large enough to catch the beam
    mirror_t=0.40,         # [A]
    mirror_tilt=45.0,      # [A] degrees, sends the +Z beam out across the walls
    vcsel_l=3.5,           # [S] 2835 body, JNJ-V-2835CW-665003-S-D1 (the 665 nm part named on v0.17)
    vcsel_w=2.8,           # [S]
    vcsel_h=0.80,          # [S]
    film_w=4.5,            # [A] grating film square
    film_t=0.12,           # [A]
    slot_clear=0.20,       # [A] film to the slot, each side
    shelf_t=2.2,           # [A] grating ledge; lips above and below the slot stay ≥ sla_min
    shelf_z=4.5,           # [A] ledge centre height above the PCB front
    film_gap=1.0,          # [A] film edge to the motor can
    beam_t=0.80,           # [A] thickness of the check volume for the swept fan
    beam_gap=0.40,         # [A] fan stops this far short of the wall and the faceplate
    beam_reach=1.2,        # [A] the fan must come at least this close (it is the light)
    # ---- printed metric thread + ISO 4762 / DIN 912 M3 socket head (corner screws) ----
    # Ed: standard full-height knurled cylindrical head, not the DIN 7984 low head.
    # Head Ø5.5 × 3.0, hex 2.5, socket depth t min 1.3. Stainless A2.
    # ISO 4762 M3 thread length b = 18, and the thread runs to the head for l ≤ 20.
    # M3×10 is that full-thread length: it fills the printed tap (grip is only the
    # 1.5 mm under the head plus the seat gap) and stays inside the 3×d thread.
    # Flat-bottom counterbore, head just below the face. No 90° countersink.
    # Bosses are tapped in the resin. No inserts. The knob bolts are not these screws.
    # v0.19b [Ed 2 Nov]: M2.5 Torx cheese head (ISO 14580), in from the BACK of the cover, head in a counterbore in the floor
    # under a slim corner column, so nothing round the head reaches the screens. v0.19 was M3 ISO 4762 on a pad inside each tube.
    cover_screw="back",    # [Ed] "back" = through the cover floor; "pad" = v0.19 head on a pad up inside the corner tube
    screw_d=2.5,           # [Ed] M2.5 (v0.19: M3)
    screw_p=0.45,          # [S] ISO coarse pitch for M2.5
    screw_dk=4.5,          # [S] ISO 14580 M2.5 head diameter (max)
    head_k=1.85,           # [S] ISO 14580 M2.5 head height (max)
    screw_drive="T8",      # [Ed][S] Torx (hexalobular) T8; modelled as a round-ish recess
    screw_hex=2.3,         # [S] T8 point-to-point, stands in for the recess in the model
    screw_socket=0.8,      # [A] T8 recess depth
    screw_lens=(3, 4, 5, 6, 8, 10, 12, 16, 20, 25),   # [S] ISO 14580 M2.5 stock lengths
    col_wall=1.2,          # [A] PETG round the clearance hole in the slim corner column (screen layer)
    col_screen_air=0.5,    # [A] screen edge to a corner column, and column flare above the screen tops
    screw_len=10.0,        # [S] standard length, mm under the head
    screw_b=18.0,          # [S] ISO 4762 M3 reference thread length, used when l > screw_full_to
    screw_full_to=25.0,    # [S] ISO 14580 M2.5 is threaded to the head up to this length
    screw_mat="A2",        # [Ed] stainless
    head_below=0.10,       # [A] head sits this far below the cover face
    bolt_head_k=2.0,       # [A] knob-bolt head, not the cover screw
    bolt_hex=2.0,          # [A] knob-bolt socket, not the cover screw
    cbore_clear=0.25,      # [A] counterbore radius over the head radius (v0.20: 0.25 for FDM ASA-CF; 0.30 would crowd the upper screen)
    thread_int_k=1.082532, # [S] internal minor D1 = d − this × pitch
    thread_ext_k=1.226869, # [S] external minor d3 = d − this × pitch
    thread_crest=0.125,    # [S] crest flat, fraction of pitch (P/8)
    thread_root=0.25,      # [S] root flat, fraction of pitch (P/4)
    thread_fit=0.22,       # [A] radial air so the screw and the printed thread do not occupy the same solid
    engage_min=2.0,        # [Ed] engagement / diameter, minimum
    engage_mult=3.0,       # [Ed] used when there is room past the minimum
    boss_wall_mult=1.0,    # [Ed] resin around the thread, in diameters
    screw_hole_ratio=0.08, # [A] clearance hole over the screw, as a fraction of the diameter
    tip_clear_ratio=0.5,   # [A] screw tip stays this many diameters off the PCB and off rear parts
    # ---- back cover: transparent smoky-grey PETG, as shallow as the countersink allows ----
    # Depth behind the PCB is a placeholder until sub/assembly-v017 reports the bearing-retainer
    # plate. Today the tallest back-side part is encoder bearing 2, seated on under_pcb's back panel.
    rear_panel_snap=25.0,  # [A] under_pcb back_panel (not exported). Bearing 2 sits here.
    cover_clear_ratio=0.08,# [A] extra depth past that stack, as a fraction of the stack
    pocket_wall=2.14,      # [A] pocket back and tub wall; not the local screw pad
    cover_under_mult=0.5,  # [Ed] PETG left under the screw head, in screw diameters
    notch_gap=0.30,        # [A] air, printed boss to the PCB corner notch
    # ---- v0.3 case [Ed, 2 Nov] ----
    knob_drop=4.0,         # [Ed] knob, joystick and clear OLED sit this much lower on the panel so all four rail screws fit
    knob_drop2=5.2,        # [Ed 2 Nov 11:33] the knob alone goes this much further down (finger room under the joystick); the
                           # joystick follows the rail rule instead, and the clear OLED goes down oled_drop (electronics clear_oled_xy)
    oled_drop=3.8,         # [Ed 2 Nov] clear OLED, same size, this much lower on the panel (bottom posts moved into the wall)
    bot_posts_in_wall=True,   # [Ed 2 Nov] bottom corner posts sit in the bottom wall, as they already sit in the side walls
                              # (screws from the back since v0.19b), so the clear OLED can come down
    top_corners=True,      # [Ed] top bolts at the top corners, mirroring the bottom pair (v0.2: between the knob and the joystick)
    insert_od=3.5,         # [A] stock M2.5 knurled brass insert, epoxied in the resin boss (v0.19: M3, Ø4.6 × 5.7)
    insert_len=4.0,        # [A] insert length (1.6 d of thread)
    insert_glue=0.1,       # [A] radial epoxy gap round the insert
    tip_hole=0.5,          # [A] clearance hole runs this far past the screw tip
    insert_engage_min=1.5, # [A] steel M3 in a brass insert: 1.5 x d (the printed-resin rule was 2 x d)
    insert_wall=1.5,       # [A] resin round the insert; boss radius = insert_od/2 + this (was Ø9 printed-thread boss)
    back_screens="amoled2",   # [Ed] two 2.4" AMOLEDs facing forward on the cover floor, overlapped behind the knob (v0.2: 2.0" TFT on the back)
    amo_w=38.72,           # [S] 2.4" 450x600 RM690B0 panel outline (TOH240XVT-01 / Gesight B024JMV-N50-6DP0)
    amo_h=51.56,           # [S]
    amo_t=0.5,             # [S] panel thickness (flex tail and stiffener not modelled yet)
    amo_pad=1.0,           # [Ed] the lower (front) screen sits on a 1 mm pad over the upper one
    amo_lower_y_up=19.5,   # [Ed 2 Nov] lower screen bottom edge above the panel bottom; 4 mm lower now the corner screws come in from the back (v0.19: 23.5)
    amo_upper_top_up=109.0,   # [Ed 2 Nov] upper screen top edge above the panel bottom; 4 mm higher, same reason (v0.19: 105.0); overlap ~13.6
    screen_air=1.0,        # [Ed] minimum air from any part behind the PCB to a screen; the cover depth is worked back from it
    ledge_knob_clear=0.3,  # [A] side ledge cut back this far past the knob hole radius round the knob base
    joy_board_z=30.0,      # [A] v0.25: no joystick part is over the top posts' plan any more (the top board is notched round them, the
                           # vertical boards' male headers and the sockets sit 0.3+ off them, assembly path rows): the lowest part over them
                           # is the top board's underside (30.0). v0.24: 24.3, the male header body; v0.23: 26.6, the spring-contact strip
    joy_cut_to=1.40,       # [Ed 4 Nov 10:03] joystick item 5: the joystick cutout runs only this far behind the faceplate back (z_fp0), not
                           # the case's whole depth, so the top wall and the two top corner posts come back (the top ledge only at its ends, joy_tb_pass)
                           # (v0.25 first cut: from z_seat - cut_slop, -0.42, the wall was open 42.2 wide). 1.40 (wall top z 34.90) = the
                           # cradle's two Ø2 balls reach 1.05 under z_fp0 over the wall (joystick v0.9 [J]) + 0.35 air [A]; assembly row
                           # "case top wall back under the joystick" measures the real parts. None = the v0.25 full-depth cut
    joy_tb_pass=18.15,     # [J][A] 4 Nov: the restored top ledge stays cut over x ±this, where the joystick top board passes up from the back
                           # to its printed nest (it goes in before the board stack): the board is ±18.95 less its 1.30 corner notches round the
                           # top posts = ±17.65 over the ledge's band (joystick v0.9 [J]) + 0.50 air [A]. The vertical boards (x ±16) stand
                           # inside it. The ledge comes back only at its ends (to the posts and the side ledges); assembly path row
    joy_step=None,         # [Ed 18:35] v0.25: no top-edge step (the joystick cradle is printed into the case: nothing to seal). v0.24 [Ed 14:02]:
                           # dict(w=1.20, d=1.45, y_in=0.20), a rebate in the cutout wall from the faceplate back with the cradle's dam in it
    amo_drop_air=0.45,     # [A] v0.25 [Ed 19:12 (5)]: the corner columns' flare and ring are trimmed this far round each back screen's plan, so
                           # the screen drops straight onto the cover floor (v0.24: the upper AMOLED caught a top flare by 0.48)
    joy_lip=1.20,          # [J] v0.7 joystick snapshot: the case cradle's lip (0.20 clearance + 1.0 wall; v0.25: printed with the case, the
                           # slot filled, one 1.2 wall) sits in the cutout, so the
                           # carrier is this much narrower each side than the cutout rule alone (the cutout itself is unchanged)
    cover_clamp="tubes",   # [Ed] PETG corner tubes press the PCB back (no perimeter land under the emitters)
    tube_press=1.0,        # [A] width of the tube ring that bears on the PCB round the corner notch
    jack_w=10.0,           # [S] PJ366ST body width (x) — clacktronics/AudioJacks STEP, MIT, credit Barwise; untested vs a real part
    jack_h=10.5,           # [S] body height (y)
    jack_bush_d=6.0,       # [S] threaded bushing; panel hole jack_hole
    jack_nut_d=8.0,        # [S] knurled nut across flats/round
    jack_nut_t=2.0,        # [A] nut thickness on the plate front
    jack_xs=(-16.5, -5.8, 5.8, 16.5),   # v0.42 [Ed 5 Nov 17:48 Q17 = A]: the middle jacks out to ±5.8 (were ±5.5) so their sleeve slots clear the
                                        # D+/D- contact pads on the tab (spacing 10.7 / 11.6 / 10.7). v0.39 [Ed 5 Nov 15:53 Q15 = A]: 11.0 pitch
                                        # (was ±17.25, ±5.75 at 11.5) so the outer jack-board tongues
                                        # clear the round bottom corner posts
    jack_y_up=22.0,        # v0.38 [Ed 5 Nov 15:34 Q12 = A]: 0.25 up so the taller USB-C board keeps 0.75 below the jacks. Was 21.75: [Ed 4 Nov 10:07, 20:12] jack centre above the panel bottom edge: 5.45 lower than 26.7 (jack tops on the clear
                           # OLED's lit-area edge), then 0.5 back up (option B: room at the bottom corner posts, ~97-98% of the lit area seen)
    usb_y_up=13.0,         # v0.38 [Ed 5 Nov 15:34 Q12 = A]: 0.25 up so the real socket's shell-leg pads sit 0.3 from the 6.0 board's edges. Was 12.75: [Ed 4 Nov 11:09] USB-C centre above the panel bottom edge: 4.35 lower than 17.1, so the 5.5 board's bottom
                           # edge is on the bottom face (y -56.4, the rail line), through the bottom wall
    usb_rcpt=(8.94, 3.16, 6.8),    # v0.38 [Ed 5 Nov 15:40 Q13 = A]: SHOU HAN TYPE-C 16P LTH6.8 (LCSC C5187468): shell 8.94 x 3.16 [S-lib], 6.8 tall
                                   # from the board to its face, flush with the plate front [S-dist]. Was (8.94, 3.26, 7.35) [S, typical mid-mount]
    usb_board=(12.0, 6.0, 1.6),    # v0.38 [Ed 5 Nov 15:34 Q12 = A]: 6.0 tall (was 5.5) for the real socket's legs; [Ed 15:40 Q13 = A]: 1.6 thick
                                   # (was 1.0) so the spring-contact gap is 4.10 (Harwin P70: 3.85-4.20). [Ed 4 Nov 11:09] small USB-C board behind the faceplate: w, h (was 6), t. v0.37 [Ed 5 Nov 11:24]: socket,
                                   # VBUS TVS and data ESD only (the PD sink chip moved to the jack power board)
    bot_post_drop=1.0,     # [Ed 4 Nov 20:12] the bottom corner screws (inserts, posts, cover columns, PCB notches) 1.0 lower: the
                           # posts stay out of the jacks' straight path from behind
    post_jack_air=0.4,     # [Ed 4 Nov 20:25 "Go"] the bottom posts are cut flat this far below the jack bodies (their path from behind); 0.4 leaves 1.2 of
                           # resin both sides of the insert (0.7 would leave 0.9 on the jack side)
    jack_lip_notch=0.5,    # [A] the side PCB ledges are notched along the jack row (jacks 1 and 4 pass them from behind) this far past the
                           # jack bodies; the side glow coat stays off the same strip [Ed 4 Nov 20:12]
    usb_slot=True,         # [Ed 4 Nov 20:15] option C: the USB-C board slides in from behind along a channel through the bottom wall onto
                           # a ledge (the wall left in front of it); a printed key fills the channel behind it, held only by the back cover
    usb_slot_clear=0.15,   # [A] channel side clearance round the board
    usb_key_gap=0.05,      # [A] key to the channel walls; 0.02 to the board's back face and to the back cover
    boss_gap=0.40,         # [A] air, boss to the knob hole and to the joystick opening
    cover_mat="ASA-CF",    # [Ed 2 Nov] back cover and lower screen pad: carbon-filled ASA, FDM (was PETG). Stiffer (~4.2 GPa),
                           # HDT ~100 °C, so the corner-column clamp does not creep. Print floor-down; thin PET/Kapton film under the screens
    cover_rho=1.12e-3,     # [A] ASA-CF, g/mm³
    cover_rgb=(40, 42, 45),  # [A] black, as printed
    cover_opacity=0.55,    # [A] render only (the real part is opaque)

    # ---- knob collar under the plate, bolts up into the shell ----
    # The seal itself is the thin ring on the front face (interface lab_ring_*).
    collar_h_mult=3.0,     # [A] collar length / screw diameter
    collar_wall=2.5,       # [A] radial wall of the tube the knob slides through
    knob_bolt_n=0,         # [Ed] 2 Nov: knob bolts removed (v0.2 had 4)
    seat_gap=0.08,         # [A] air so the cover, the shell and the PCB do not fuse in the model
    nest_gap=0.05,         # [A] air, PCB front face to the ledge stop (solids stay apart)
    ledge_ratio=0.60,      # [A] ledge width / wall, inboard of the PCB edge
    preload_ratio=0.04,    # [A] shell-rim seat recessed by this fraction of the cover field; the PCB land touches first
    clamp_t_ratio=0.45,    # [A] clamp tongue / cover field, thin enough to close the preload
    clamp_keep=0.45,       # [A] clamp overlap uses this fraction of the nearest B-side edge clearance
    cover_pocket=0.40,     # [A] air, pocket wall to the rear envelope (d_big_tip)
    pcb_clear=0.60,        # [A] air, PCB edge to the inner side wall
    rear_clear=0.80,       # [A] air, d_big_tip envelope to the inner side wall
    fuse=0.02,             # [A] overlap so adjacent walls fuse into one solid
    cut_slop=0.50,         # [A] cutters run this far past the face they open
    edge_w=2.2,            # [A] light-pipe band at the faceplate rim
    edge_t=1.2,            # [A] thinned rim (≥ sla_min, thinner than the 2.5 plate so it lights)
    ligament_t=1.2,        # [A] bridge between the knob hole and the joystick hole
    web_min=0.80,          # [A] smallest plan web, = sla_min
    pad_extra=1.0,         # [A] full-thickness pad past the rail-hole radius
    # ---- 2.0" TFT. Off the front; a placeholder module on the back cover [Ed] ----
    # Active area from the 2.0" diagonal. The module itself is not chosen: an [A] border
    # around that active area is the placeholder outline.
    tft_on_front=False,    # [Ed]
    tft_in=2.0,            # [L] inch
    tft_px=(320, 240),     # [L]
    tft_border=2.0,        # [A] bezel around the active area, each side
    tft_mod_t=3.2,         # [A] placeholder module thickness, into the pocket
    tft_gap=0.80,          # [A] air from the module to the pocket wall
    # ---- front jacks, only counted. Thonkiconn PJ398SM [S], body width [A] ----
    jack_hole=6.6,         # [Ed 4 Nov 22:52] panel hole for the 6.0 bushing (was 6.2 [S]): ±0.3 float, since the jack unit's posts are
                           # soldered at both ends; the Ø8 nut still covers it
    jack_nut=7.8,          # [S] knurled nut
    jack_body=10.5,        # [S] PJ366ST body (was 12.0 assumed)
    jack_air=0.80,         # [A] air between bodies, and off the knob
    # PJ366ST (stereo Thonkiconn), from the community STEP model clacktronics/AudioJacks (MIT, Barwise).
    # The library lists it untested against a real part: measure one before ordering.
    jack_depth=10.0,       # [S] body depth behind the panel
    jack_pin_len=3.5,      # [S] solder pins below the body
    jack_pin_box=(4.0, 6.0),   # v0.33-v0.38 placeholder (no longer used for the pins)
    # v0.39 [Ed 5 Nov 15:42 Q14 = B, 15:53 Q15 = A]: the real PJ366ST [S-lib: KiCad QingPu PJ398SM (Thonk: same footprint), 4ms, GuavTek,
    # westlicht, clacktronics, requencer]. Body off-centre on its bushing, sleeve side down (the sleeve pin about 2 mm outside the body).
    jack_body_y=(-4.5, 6.0),   # [S-lib] body extent in y from the axis (sleeve side down)
    jack_pins=(("T", 4.92, 5.21, 1.43), ("R", -3.38, -3.35, 1.42), ("S", -6.48, -5.715, 1.22)),   # [S-lib] (pin, y range of the published
                               # positions, hole Ø): the jack board's plated slots cover each range [Ed Q14 = B]; the model's pins sit at the first value
    jack_pin_d=0.9,            # [A] pin drawn as a Ø0.9 rod
    jack_slot_ring=0.35,       # [A] annular ring round each slot
    jb_tongue_edge=0.3,        # [A] board outline round the sleeve pad
    jb_plug_hole=3.6,          # v0.45 [Ed 5 Nov 20:46 Q20 = A]: a hole through the jack board under each jack axis for a plug's tip (it comes out
                               #   of the back of the body; Thonk: drill 3 mm [S]); 3.6 lets a long 17 mm plug's full tip through
    jb_tongue_inner=0.5,       # v0.44 [A]: the outer two jack-board tongues this much wider on their inner side (room for the sleeve's ground)
    jb_tip_bump=(2.7, 0.55),   # v0.43 [Ed 5 Nov 17:59 Q18 = A]: a bump (width, height) on the jack board's top edge round each tip slot (its pad
                               #   reached axis +6.28, past the edge at the jack tops, axis +6.0): pad 0.25 from the edge
    jack_ledge_notch=0.4,      # [A] bottom ledge notched this far round each tongue
    # v0.33 [Ed 4 Nov 21:30] step 2, decision 3, option B: two boards with the jack row's own outline (its path from behind). The jack
    # board sits on the jacks' backs (jacks soldered on, the small analog parts between the pins underneath); the jack power board hangs
    # jb2_gap under it on two SMD headers, with both ZIFs on its underside and the power parts (±12 V, the clear OLED's 12.5 V).
    jb_on=True,            # [Ed 4 Nov 21:30]
    jb_t=1.6,              # [A] jack board FR-4
    jb_under=2.0,          # [A] parts envelope under the jack board (between the pins)
    jb2_gap=4.9,           # [Ed 4 Nov 21:30] jack board underside to the power board's top face. v0.39: 4.9 [A], the XFCN 1.27 pair's stack
    jb2_t=1.6,             # [A] power board FR-4
    jb2_parts=2.0,         # [A] parts envelope on the power board's top face
    jb_hdr=(7.7, 3.4, 11.15),  # v0.42 [A]: between the jacks (x ±11.15), pins along x: KiCad's land pattern for these stacks [S-lib] has its
                               # feet out to ±3.15 across the rows, so at x ±19.6 (v0.39) they ran off the board's end onto jack 1/4's slots.
                               # v0.39 [S-dist/A]: two 2x6 1.27 mm SMD stacks (XFCN PZ127VS-12-12-H16 male C2840009 + PM127VS-12-12-H34 female
                               # C2840010, stack about 4.9): width (x), length (y), x centre (±). Was two 1x8 (the female had 29 in stock)
    zif_oled=(16.9, 5.2, 2.0, 0.0),    # v0.39 [S-lib]: 24-pin 0.5 mm flip-lock, 2.0 tall, XUNPU FPC-05F-24PH20 (LCSC C2856805) footprint incl. its
                                       # mounting pads (a dual-contact equal, HC-FPC-0.5-24P-FHH20 C19273940, if the flex's contact side needs it).
                                       # Was ER-CON24HT-1 17.65 x 4.5 [S] (not on LCSC). w, d, h; x centre on the
                                       # flex, which leaves the middle of the OLED's long edge [S]; on the power board's underside
    zif_link=(9.0, 3.7, 1.0, 14.1),    # v0.39 [S]: Hirose FH26W-25S-0.3SHW(60) (LCSC C2904698), 25 positions at 0.3 (no 24 exists; the 25th is a
                                       # ground), 9.0 long, footprint 3.7 deep, 1.0 tall: w, d, h, x centre (over its lane)
    zif_y_off=0.75,        # [A] ZIFs start this far above the boards' bottom edge (0.3 clear of the posts)
    # v0.34 [Ed 4 Nov 22:21] step 2, decision 4, option 1A: the jack unit rides in with the board stack, held on two posts standing in the
    # main board's strip under the clear OLED; both flexes are plugged into its ZIFs on the bench. The power board gets a tab down over them.
    jb_post_xy=((-16.5, -50.45), (8.0, -50.45)),    # [Ed 22:21, 22:52] post centres: 0.65 from the OLED's edge, 0.35 from the bottom ledge;
                           # v0.36 the right post moves in to x 8 (between the OLED's flex and the link flex's lane)
    jb_post_d=2.0,         # [Ed 4 Nov 22:21] Ø2 posts; [Ed 22:52] brass, soldered at both ends, they carry 15 V and GND to the main board
    link_lane=(9.5, 18.5, -50.6),   # [Ed 22:52 / A] the link flex's lane: x from, x to, and its pads' lowest y in the strip (clear of the
                           # board's corner notch); ~16 lines at 0.5 mm, signals only
    flex_t=0.15,           # [A] flex thickness (drawn as a straight riser from the strip to its ZIF)
    jb_tab=(1.3, -51.5),   # [A] power board ears down over the posts: half width round each post, bottom edge y (0.3 above the bottom
                           # ledge); the bottom lip's glow coat is left off 1.6 either side of each post (the shell's lip passes the ears)
    oled_flex_len=36.0,    # [S] the clear OLED's flex, from the panel edge (36.0 ± 0.5)
    # v0.35 [Ed 4 Nov 22:36] step 2, decision 5, option A: the USB-C board (in the shell first) reaches the jack unit (in with the stack)
    # through spring contacts: a tab on the jack board's bottom edge reaches into the USB-C channel and carries them; they land on gold pads
    # on the USB-C board's back face in the stack's last ~1 mm. The key's ledge tab goes (the jack board's tab passes there).
    usb_pwr_tab=(5.85, -53.9),  # v0.41 [Ed 5 Nov 17:36 Q16 = A]: ±5.85 down to -53.90 (was ±5.8 to -53.6, where the lower pads Ø1.2 met the
                                #   tab's edge): pads 0.30 from the bottom, 0.25 from the sides, 0.30 to the channel walls.
                                # v0.38: half width 5.5 -> 5.8 for the contacts at x ±5.0.   # [Ed 22:36 / A] jack board tab: half width, bottom edge y (0.35 above the key, inside the channel)
    # v0.37 [Ed 5 Nov 11:17 Q4 = A, 11:24 Q5 = B]: USB data on the same socket and the PD chip on the jack power board: 8 contacts,
    # two rows of 4 at 1.6 pitch, clear of the socket's shell legs [A]: 15 V x2, GND x2 (top row), D+, D-, CC1, CC2 (bottom row)
    # v0.38 [Ed 5 Nov 15:34 Q12 = A]: laid round the real socket's shell legs and locating posts (≥ 0.3 from their pads/holes and the edges)
    # v0.42 [Ed 5 Nov 17:48 Q17 = A]: D+/D- in to x ±4.0 (were ±4.6, on the middle jacks' sleeve slots); 0.325 to the socket's leg pads
    usb_pwr_contacts=((-0.8, -51.4), (0.8, -51.4), (-0.8, -53.0), (0.8, -53.0), (-4.0, -51.4), (4.0, -51.4), (-5.0, -53.0), (5.0, -53.0)),
    usb_pwr_names=("15 V", "15 V", "GND", "GND", "D+", "D-", "CC1", "CC2"),
    usb_pwr_pad=1.2,       # [S-dist] Harwin P70-5100045 pad Ø (the contact found that fits 1.6 spacing)
    usb_pwr_d=1.03,        # [S-dist, unconfirmed] Harwin P70-5100045 body Ø (plunger Ø0.60); free 4.8, working 4.00 (3.85-4.20), 2 A
    usb_shell_legs=((-2.4, -2.15), (2.4, -2.15), (-2.4, 2.15), (2.4, 2.15)),   # [S-lib] vertical 16-pin USB-C shell legs (x, dy from the centre)
    usb_leg_pad=(1.35, 1.10),   # [S-lib] their plated-slot pads
    usb_posts=((-3.75, 0.0), (3.75, 0.0)),   # [S-lib] locating posts (x, dy); holes about Ø0.8
    usb_post_hole=0.8,
    # v0.37 [Ed 11:24]: the two protection parts on the USB-C board's back face, in pockets in the printed key: (name, x0, x1, y0, y1, h)
    usb_prot=(("VBUS TVS (DFN1610) [A]", -1.4, 0.2, -56.05, -55.05, 0.55), ("data ESD (SOT-5X3) [A]", 3.4, 5.0, -56.05, -54.45, 0.6)),
    usb_key_tab_step=0.25,  # v0.41 [Ed 5 Nov 17:36 Q16 = A]: the key's top stepped down this much along the tab's path (behind z of the
                            #   tab's face + 0.3), so the longer tab keeps 0.30 to it; full height where the key presses the USB-C board
    usb_pocket_clear=0.2,  # [A] key pocket round each part (v0.40: 0.2, was 0.1, so it also clears the ESD's pads, 1.85 across)
    jb_air=0.3,            # [A] clearance round the pins / headers in the boards and envelopes
    post_jack_clear=1.0,   # [A] air from the top of a corner post to the jack pin tips
    usb_w=12.0,            # [A] upright USB-C, plug keep-out width
    mass_max=140.0,        # [A] g, resin shell only (the PETG cover is separate)
    stl_tol=0.08,          # [A] STL chord tolerance, mm
    stl_ang=0.3,           # [A] STL angular tolerance, rad
    usdz_tol=0.15,         # [A] Quick Look mesh chord, mm
    scan_clear=0.50,       # [A] swept beam to the knob and to the joystick envelope
)

IMPORTS = {"electronics": ["pcb_w", "pcb_above", "pcb_below", "clear_oled", "clear_oled_xy"],
           "under_pcb": ["d_big_tip", "z_rear_min", "h_big_bot"]}
EXPORTS = ["panel_w", "panel_h", "hp", "place_y", "knob_hole_r",
           "joy_hole", "z_fp0", "z_fp1", "z_foot", "fp_to_pcb",
           "z_joy_cut0", "joy_tb_pass",   # 4 Nov: the restored top wall's top and the top-ledge gap (assembly rows)
           "lab_ring_r", "lab_ring_z0", "lab_ring_z1",
           "lab_shoulder_r", "lab_shoulder_z0", "lab_shoulder_z1"]


def _clear_rect(cx, cy, r, x0, y0, x1, y1):
    """Air between a circle and an axis-aligned rectangle. Negative means they overlap."""
    dx = max(x0 - cx, 0.0, cx - x1)
    dy = max(y0 - cy, 0.0, cy - y1)
    return math.hypot(dx, dy) - r


def _place_for(x, y_edge, rc):
    """place_y that puts (x, y_edge) on a circle of radius rc about the knob. Joystick v0.4 rule."""
    if abs(x) >= rc - 1e-9:
        return -y_edge
    return -y_edge + math.sqrt(rc * rc - x * x)


def _json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except OSError:
        return {}


def _data_files():
    here = os.path.dirname(os.path.abspath(__file__))
    kicad = os.path.normpath(os.path.join(here, "..", "electronics", "kicad"))
    return (os.path.join(kicad, "cad_constraints.json"),
            os.path.join(kicad, "knob-main-pcb", "pcb_proxy.json"))


def _knob_top(cons, fallback):
    """Knob-top z from cad_constraints when the knob branch writes it; else the snapshot."""
    for key in ("z_knob_top", "knob_top"):
        if key in cons and isinstance(cons[key], (int, float)):
            return float(cons[key]), "cad_constraints"
    return float(fallback), "placeholder"


def _pcb_outline(cons, pcb_w, above, below):
    pcb = cons.get("pcb")
    if isinstance(pcb, (list, tuple)) and len(pcb) == 3:
        return float(pcb[0]), float(pcb[1]), float(pcb[2]), "cad_constraints"
    return float(pcb_w), float(above), float(below), "interface"


def _bside_clear(parts, pcb_w, above, below):
    """Smallest plan gap from a B-side box to the PCB outline. Negative means the box crosses the edge."""
    x1 = pcb_w / 2.0
    y0, y1 = -below, above
    best = min(x1, y1 - y0)
    hit = ""
    for p in parts:
        hx, hy = p["w"] / 2.0, p["l"] / 2.0
        d = min((p["x"] - hx) + x1, x1 - (p["x"] + hx), (p["y"] - hy) - y0, y1 - (p["y"] + hy))
        if d < best:
            best, hit = d, p.get("ref", "")
    return best, hit


def derive(D):
    sla = D["sla_min"]
    # opening uses the larger of the live knob and the v0.17 / joystick design size
    D["knob_od_used"] = max(D["knob_od"], D["knob_od_design"])
    D["knob_r"] = D["knob_od_used"] / 2
    D["half_w"] = D["scr_w"] / 2 + D["bz_lip"]
    D["half_h"] = D["scr_h"] / 2 + D["bz_lip"]
    D["slide"] = D["tol_sla"] + D["sw_tilt"]
    D["knob_rc"] = D["knob_r"] + 2 * D["tol_mjf"] + D["slide"]
    D["place_y_knob"] = max(_place_for(0.0, -D["half_h"], D["knob_rc"]),
                            _place_for(D["half_w"], -D["half_h"], D["knob_rc"]))
    D["place_y"] = D["place_y_knob"]   # v0.4 rule; the rail rule replaces it once the panel is placed (below)
    D["hole_hw"] = D["half_w"] - D["fp_overlap"]
    D["hole_hh"] = D["half_h"] - D["fp_overlap"]
    D["car_hw"] = D["hole_hw"] - D.get("joy_lip", 0.0) - D["slide"] - D["tol_sla"]   # v0.23: inside the joystick cradle's lip
    D["car_hh"] = D["hole_hh"] - D.get("joy_lip", 0.0) - D["slide"] - D["tol_sla"]
    D["joy_hole"] = (2 * D["hole_hw"], 2 * D["hole_hh"])
    if D.get("joy_step"):   # v0.24 top-edge step (rebate); none since v0.25 [Ed 18:35]
        D["joy_reb"] = (2 * (D["hole_hw"] + D["joy_step"]["w"]), 2 * (D["hole_hh"] + D["joy_step"]["w"]))
    # press rebate, same stack as the joystick proxy
    D["press_travel"] = D["tol_sla"] + D["sw_push"]
    D["fp_rebate"] = D["press_travel"] + D["tol_sla"]
    # Faceplate from the knob top. The bezel still rests on the plate; the plate is no longer
    # parked 5 mm under the knob. Knob top comes from cad_constraints when that key lands.
    cons_path, proxy_path = _data_files()
    cons = _json(cons_path)
    D["knob_top_used"], D["knob_top_src"] = _knob_top(cons, D["z_knob_snap"])
    # [Ed] 2 Nov: the v0.18 interface faceplate wins (faceplate_z = z_top - knob_proud 18.0).
    D["z_fp1"] = D["faceplate_z"]
    D["z_fp0"] = D["faceplate_z_back"]
    D["fp_t"] = D["wall"]
    D["edge_r"] = D["edge_r_ratio"] * D["wall"]
    D["fp_corner_r"] = D["edge_r"]
    D["fp_to_pcb"] = D["z_fp1"]
    D["z_bz0"] = D["z_fp1"] + D["up_gap"]
    D["z_bz1"] = D["z_bz0"] + D["grip_h"]   # [Ed 2 Nov] grip block (v0.4: + bz_t 1.2)
    # 10HP panel. The box behind the rail ears is one rectangle: shell and cover share it.
    # The PCB is inset from that rectangle by the wall plus the drop-in clearance, on all four sides.
    _, above, below, src = _pcb_outline(cons, D["pcb_w"], D["pcb_above"], D["pcb_below"])
    D["pcb_live_above"] = above
    D["pcb_live_below"] = below
    D["pcb_src"] = src
    D["hp"] = int(D["hp_scope"])
    D["panel_w"] = D["hp"] * D["hp_pitch"] - D["hp_gap"]
    D["panel_w_scope"] = D["panel_w"]
    D["panel_x0"] = -D["panel_w"] / 2.0
    D["panel_x1"] = D["panel_w"] / 2.0
    D["panel_y1"] = D["axis_by"] + D["knob_drop"] + D["knob_drop2"]   # [Ed] 2 Nov: knob sits knob_drop (+ knob_drop2) lower on the panel
    # [Ed 2 Nov] joystick: as high as the top rail screw keep-out (washer) allows, at the full slide toward it
    D["rail_y_top"] = D["panel_y1"] - D["rail_edge"]
    if D["joy_rule"] == "rail":
        D["place_y"] = D["rail_y_top"] - D["rail_keep_d"] / 2 - D["slide"] - D["tol_mjf"] - D["rail_float"] - D["half_h"]
    D["finger_gap"] = D["place_y"] - D["half_h"] - D["knob_r"]
    D["panel_y0"] = D["panel_y1"] - D["panel_h"]
    D["panel_yc"] = (D["panel_y0"] + D["panel_y1"]) / 2.0
    D["body_y1"] = D["panel_y1"] - D["rail_clear"]
    D["body_y0"] = D["panel_y0"] + D["rail_clear"]
    D["body_yc"] = (D["body_y0"] + D["body_y1"]) / 2.0
    D["x_out1"] = D["panel_w"] / 2.0
    D["x_out0"] = -D["x_out1"]
    D["x_in1"] = D["x_out1"] - D["wall"]
    D["x_in0"] = -D["x_in1"]
    D["y_in1"] = D["body_y1"] - D["wall"]
    if D.get("joy_step"):   # v0.24 [Ed 14:02]: the rebate runs from here up the long sides and across the top
        D["joy_step_y0"] = D["y_in1"] - D["joy_step"]["y_in"]
    D["y_in0"] = D["body_y0"] + D["wall"]
    D["pcb_x1"] = D["x_in1"] - D["pcb_clear"]
    D["pcb_y1"] = D["y_in1"] - D["pcb_clear"]
    D["pcb_y0"] = D["y_in0"] + D["pcb_clear"]
    D["nest_w"] = 2.0 * D["pcb_x1"]
    D["nest_above"] = D["pcb_y1"]
    D["nest_below"] = -D["pcb_y0"]
    D["pcb_max_w"] = D["nest_w"]
    # The PCB drops in from the back. Its back face is flush with the shell rim; the ledge
    # stops the front face. nest_gap keeps the two solids from fusing.
    D["z_rim"] = D["z_pcb_back"]
    D["z_ledge0"] = D["nest_gap"]
    D["z_ledge1"] = D["z_ledge0"] + D["wall"]
    D["ledge_w"] = D["ledge_ratio"] * D["wall"]
    D["screw_boss_r"] = D["insert_od"] / 2 + D["insert_wall"]   # [Ed] brass insert in a resin boss (v0.2: printed thread, Ø9)
    D["pad_r"] = D["screw_boss_r"]
    D["hole_r"] = D["screw_d"] * (0.5 + D["screw_hole_ratio"])
    D["tip_clear"] = D["tip_clear_ratio"] * D["screw_d"]
    # Boss axis is inside the PCB; the post uses the wall for its outer half and the board is notched.
    br = D["screw_boss_r"]
    D["boss_x"] = D["x_out1"] - D["web_min"] - br
    D["hp_need_w"] = D["panel_w"]
    D["z_seat"] = D["seat_gap"]
    # [Ed 4 Nov 10:03] where the joystick cutout prism starts (z): just behind the faceplate, so the top wall, top ledge and top posts stay whole
    jc = D.get("joy_cut_to")
    D["z_joy_cut0"] = (D["z_fp0"] - jc) if jc is not None else (D["z_seat"] - D["cut_slop"])
    # Placeholder rear stack: bearing 2 bottom behind the PCB back. Same arithmetic as under_pcb
    # (back panel seat + flange − bearing width). The retainer plate on sub/assembly-v017 replaces
    # rear_panel_snap when it reports a depth; the cover cavity then moves with it. The cavity
    # depth itself is not changed here.
    B = D["brg"]
    D["rear_stack"] = D["rear_panel_snap"] - B["ft"] + B["B"]
    D["z_bearing_bot"] = D["z_pcb_back"] - D["rear_stack"]
    if D["back_screens"] == "amoled2":
        # [Ed] 2 Nov: worked backwards. Deepest part behind the PCB, then screen_air, then the two-screen stack.
        em_h = 1.0   # [A] emitter bodies on the PCB back (VCSEL 0.8, RGB 0.9) + gap
        D["z_rear_parts"] = min(D["z_rear_min"], D["fg_z_bot"], D["z_pcb_back"] - em_h)
        D["amo_stack"] = D["amo_pad"] + D["amo_t"]
        # Per screen: the encoder hub/shaft (deepest) sits over the upper screen only (encoder at the top); over the lower
        # screen the deepest parts are the disc face, the compound gear and the emitters. The 3D check confirms it.
        z_lower = min(D["h_big_bot"], D["fg_z_bot"], D["z_pcb_back"] - em_h)
        D["z_cover_in"] = min(D["z_rear_parts"] - D["screen_air"] - D["amo_t"], z_lower - D["screen_air"] - D["amo_stack"])
        D["cover_depth"] = D["z_pcb_back"] - D["z_cover_in"]
    else:
        D["cover_depth"] = D["rear_stack"] * (1.0 + D["cover_clear_ratio"])
        D["z_cover_in"] = D["z_pcb_back"] - D["cover_depth"]
    D["cbore_depth"] = D["head_k"] + D["head_below"]
    D["cbore_r"] = D["screw_dk"] / 2.0 + D["cbore_clear"]
    D["cover_t"] = D["pocket_wall"]
    D["z_cover_out"] = D["z_cover_in"] - D["cover_t"]
    # Clamping rim. The PCB land is seat_gap off the board; the shell-rim seat is recessed a
    # further preload_gap so the screws clamp the PCB before the cover bottoms on the rim.
    # The tongue is thinner than the pocket wall so it can close that gap.
    D["preload_gap"] = D["preload_ratio"] * D["cover_t"]
    D["z_pcb_land"] = D["z_pcb_back"] - D["seat_gap"]
    D["z_rim_seat"] = D["z_pcb_land"] - D["preload_gap"]
    D["clamp_t"] = D["clamp_t_ratio"] * D["cover_t"]
    D["z_flange_out"] = D["z_rim_seat"] - D["clamp_t"]
    D["cover_under"] = D["cover_under_mult"] * D["screw_d"]
    D["pad_h"] = max(0.0, D["cover_under"] + D["cbore_depth"] - D["clamp_t"])
    D["z_pad_out"] = D["z_flange_out"] - D["pad_h"]
    D["cover_skin"] = D["clamp_t"] + D["pad_h"] - D["cbore_depth"]
    if D["cover_screw"] == "back":   # v0.19b: no pad; the head sits in the floor, the column above it is the material over the head
        D["pad_h"] = 0.0
        D["z_pad_out"] = D["z_flange_out"]
    D["z_foot"] = min(D["z_pad_out"], D["z_cover_out"])
    D["z_wall0"] = D["z_rim"]
    avail = (D["z_fp0"] - D["tip_clear"]) - D["z_rim"]
    D["engage"] = min(D["engage_mult"] * D["screw_d"], avail)
    D["knob_hole_r"] = D["knob_r"] + D["knob_rad_clear"]
    # bridge between the two openings, along +Y
    D["joy_y_near"] = D["place_y"] - D["hole_hh"]
    D["joy_y_far"] = D["place_y"] + D["hole_hh"]
    D["bezel_y_near"] = D["place_y"] - D["half_h"]
    D["bezel_y_far"] = D["place_y"] + D["half_h"]
    D["web_knob_joy"] = D["joy_y_near"] - D["knob_hole_r"]
    D["edge_top_w"] = D["panel_y1"] - D["bezel_y_far"]
    # carrier corner vs the rounded opening (local to the joystick centre)
    r = D["hole_corner_r"]
    cx, cy = D["hole_hw"] - r, D["hole_hh"] - r
    D["car_corner_dist"] = math.hypot(D["car_hw"] - cx, D["car_hh"] - cy)
    D["car_in_hole"] = D["hole_corner_r"] - D["car_corner_dist"]
    # side clearances the HP choice is supposed to buy
    D["side_air"] = (D["x_in1"] - D["x_in0"] - D["nest_w"]) / 2
    D["rear_air"] = (D["x_in1"] - D["x_in0"]) / 2 - D["d_big_tip"] / 2
    # B-side keep-out: KiCad proxy boxes plus the pad courtyards written into cad_constraints.
    boxes = list(_json(proxy_path).get("back_parts") or [])
    feel = cons.get("feel") or {}
    pw, pl = (feel.get("pad") or (1.8, 1.8))[:2]
    for xy in cons.get("fm_pad_xy") or []:
        boxes.append({"ref": "feel pad", "x": xy[0], "y": xy[1], "w": pw, "l": pl})
    rod_r = cons.get("rod_pad_r")
    if isinstance(rod_r, (int, float)) and rod_r > 0:
        boxes.append({"ref": "rod pad", "x": 0.0, "y": 0.0, "w": 2.0 * rod_r, "l": 2.0 * rod_r})
    D["bside_clear"], D["bside_ref"] = _bside_clear(boxes, D["nest_w"], D["nest_above"], D["nest_below"])
    D["clamp_overlap"] = max(D["sla_min"], D["clamp_keep"] * D["bside_clear"])
    # Outer skin matches the shell. On X the rear envelope sets how thick that skin can be;
    # it stays at least the SLA minimum and never outside the shell line.
    ex, ey = D["enc_xy"]
    if D["back_screens"] == "amoled2":
        D["cover_side"] = D["wall"]   # v0.19: the encoder is no longer a box-sized envelope; the screen rule is checked in 3D
    else:
        D["cover_side"] = min(D["wall"], max(D["sla_min"], D["x_out1"] - (abs(ex) + D["d_big_tip"] / 2.0 + D["cover_pocket"])))
    D["void_x1"] = D["x_out1"] - D["cover_side"]
    D["void_x0"] = -D["void_x1"]
    D["void_y0"] = D["y_in0"]
    D["void_y1"] = D["y_in1"]
    D["pocket_gap"] = min(ex - D["void_x0"], D["void_x1"] - ex, ey - D["void_y0"], D["void_y1"] - ey) - D["d_big_tip"] / 2.0
    # rail screws. Bottom stations stay on the Doepfer 7.5 mm grid.
    # Top stations move outboard of the joystick opening: the bezel crosses the usual columns,
    # and a Eurorack rail takes the nut anywhere along its slot.
    x_std0 = D["panel_x0"] + D["rail_inset"]
    x_std1 = D["panel_x0"] + D["rail_inset"] + (D["hp"] - 3) * D["hp_pitch"]
    D["rail_x_std"] = (x_std0, x_std1)
    push = D["hole_hw"] + D["rail_hole_d"] / 2 + D["web_min"]
    limit = D["panel_w"] / 2 - D["rail_hole_d"] / 2 - D["web_min"]

    def _station(x):
        if abs(x) >= push:
            return x
        out = math.copysign(push, x if x else 1.0)
        return out if abs(out) <= limit else x

    D["rail_x_top"] = (_station(x_std0), _station(x_std1))
    D["rail_y_bot"] = D["panel_y0"] + D["rail_edge"]
    D["rail_pad_r"] = D["rail_hole_d"] / 2 + D["pad_extra"]
    # scanner, bottom-left inner corner (−X, −Y). Motor axis inset so the fillet bead is clear.
    mr = D["scan_motor_d"] / 2
    D["motor_r"] = mr
    D["mirror_r"] = D["mirror_d"] / 2
    # far enough in that the mirror disc clears both walls; the can is smaller than the disc
    D["x_mot"] = D["x_in0"] + D["mirror_r"] + D["scan_motor_clear"]
    D["y_mot"] = D["y_in0"] + D["mirror_r"] + D["scan_motor_clear"]
    D["z_mot0"] = D["z_seat"]
    D["z_mot1"] = D["z_mot0"] + D["scan_motor_len"]
    D["z_mirror"] = D["z_mot1"]
    # film just outside the can, on the +X side, still under the mirror disc
    D["x_beam"] = D["x_mot"] + mr + D["film_gap"] + D["film_w"] / 2
    D["y_beam"] = D["y_mot"]
    D["beam_off"] = D["x_beam"] - D["x_mot"]
    # shelf tied to the bottom wall, clear of the can
    lip = D["sla_min"]
    D["shelf_x0"] = D["x_mot"] + mr + D["scan_motor_clear"]
    D["shelf_x1"] = D["x_beam"] + D["film_w"] / 2 + lip
    D["shelf_y0"] = D["y_in0"]
    D["shelf_y1"] = D["y_beam"] + D["film_w"] / 2 + lip
    D["shelf_z0"] = D["shelf_z"] - D["shelf_t"] / 2
    D["shelf_z1"] = D["shelf_z"] + D["shelf_t"] / 2
    # groove, open toward +Y (into the cavity) so the film slides in before the PCB
    sc = D["slot_clear"]
    D["slot_x0"] = D["x_beam"] - D["film_w"] / 2 - sc
    D["slot_x1"] = D["x_beam"] + D["film_w"] / 2 + sc
    D["slot_y0"] = D["y_beam"] - D["film_w"] / 2 - sc
    D["slot_y1"] = D["shelf_y1"] + D["cut_slop"]
    D["slot_z0"] = D["shelf_z"] - D["film_t"] / 2 - sc
    D["slot_z1"] = D["shelf_z"] + D["film_t"] / 2 + sc
    D["slot_lip"] = (D["shelf_t"] - (D["slot_z1"] - D["slot_z0"])) / 2
    # VCSEL on the PCB, under the film, emitting +Z
    D["x_vc"] = D["x_beam"]
    D["y_vc"] = D["y_beam"]
    D["z_vc0"] = D["nest_gap"]
    D["z_vc1"] = D["vcsel_h"]
    # swept fan: along the inner left wall and the inner bottom wall, then up to the rim
    D["beam_x"] = D["x_in0"] + D["beam_gap"] + D["beam_t"] / 2
    D["beam_y"] = D["y_in0"] + D["beam_gap"] + D["beam_t"] / 2
    D["beam_z1"] = D["z_fp0"] - D["beam_gap"]
    # 2.0" active area. On the back cover unless tft_on_front.
    diag = D["tft_in"] * 25.4
    aspect = D["tft_px"][0] / D["tft_px"][1]
    D["tft_w"] = diag * aspect / math.hypot(aspect, 1.0)
    D["tft_h"] = D["tft_w"] / aspect
    gap = D["tft_gap"]
    D["tft_mod_w"] = D["tft_w"] + 2.0 * D["tft_border"]
    D["tft_mod_h"] = D["tft_h"] + 2.0 * D["tft_border"]
    if D["tft_on_front"]:
        D["win_x0"] = -D["tft_w"] / 2.0
        D["win_x1"] = D["tft_w"] / 2.0
        D["win_y0"] = D["pcb_y0"] + D["ledge_w"] + gap
        if D["scanner_enabled"]:
            scan_x1 = max(D["shelf_x1"], D["x_mot"] + D["mirror_r"]) + gap
            D["win_x1"] = min(D["x_in1"], D["pcb_x1"] - D["ledge_w"]) - gap
            D["win_x0"] = max(scan_x1, D["win_x1"] - D["tft_w"])
        D["win_y1"] = D["win_y0"] + D["tft_h"]
        if D["win_y1"] > -D["knob_hole_r"] - gap:
            D["win_y1"] = -D["knob_hole_r"] - gap
            D["win_y0"] = D["win_y1"] - D["tft_h"]
        D["tft_z0"] = D["nest_gap"]
        D["tft_z1"] = D["z_fp0"] - gap
    elif D["back_screens"] == "amoled2":
        y0 = D["panel_y0"] + D["amo_lower_y_up"]
        D["amo_lower"] = (-D["amo_w"] / 2, D["amo_w"] / 2, y0, y0 + D["amo_h"])
        y1 = D["panel_y0"] + D["amo_upper_top_up"]
        D["amo_upper"] = (-D["amo_w"] / 2, D["amo_w"] / 2, y1 - D["amo_h"], y1)
        D["amo_overlap"] = D["amo_lower"][3] - D["amo_upper"][2]
        D["amo_upper_z"] = (D["z_cover_in"], D["z_cover_in"] + D["amo_t"])
        D["amo_lower_z"] = (D["z_cover_in"] + D["amo_pad"], D["z_cover_in"] + D["amo_pad"] + D["amo_t"])
        # older code reads win_* / mod_* / tft_*: point them at the lower screen (no window cut in the cover)
        D["mod_x0"], D["mod_x1"], D["mod_y0"], D["mod_y1"] = D["amo_lower"]
        D["win_x0"], D["win_x1"], D["win_y0"], D["win_y1"] = D["amo_lower"]
        D["tft_z0"], D["tft_z1"] = D["amo_lower_z"]
        D["back_z0"], D["back_z1"] = D["amo_lower_z"]
    else:
        # bottom of the cover pocket, centred in X. Active window is the border inset.
        D["mod_x0"] = -D["tft_mod_w"] / 2.0
        D["mod_x1"] = D["tft_mod_w"] / 2.0
        D["mod_y0"] = D["void_y0"] + gap
        D["mod_y1"] = D["mod_y0"] + D["tft_mod_h"]
        D["win_x0"] = D["mod_x0"] + D["tft_border"]
        D["win_x1"] = D["mod_x1"] - D["tft_border"]
        D["win_y0"] = D["mod_y0"] + D["tft_border"]
        D["win_y1"] = D["mod_y1"] - D["tft_border"]
        D["tft_z0"] = D["z_cover_in"] + D["nest_gap"]
        D["tft_z1"] = D["tft_z0"] + D["tft_mod_t"]
        D["back_z0"] = D["z_cover_out"] + D["nest_gap"]
        D["back_z1"] = D["z_cover_in"] - D["nest_gap"]
    D["win_w"] = D["win_x1"] - D["win_x0"]
    D["win_h"] = D["win_y1"] - D["win_y0"]
    D["tft_short_w"] = max(0.0, D["tft_w"] - D["win_w"])
    # collar under the knob opening. The seal ring stands on the front face.
    D["collar_h"] = D["collar_h_mult"] * D["screw_d"]
    D["z_collar0"] = D["z_fp0"] - D["collar_h"]
    D["collar_r"] = D["knob_hole_r"] + D["collar_wall"]
    D["lab_ring_r"] = D["knob_hole_r"] + D["lab_ring_t"]
    D["lab_ring_z0"] = D["z_fp1"]
    D["lab_ring_z1"] = D["z_fp1"] + D["lab_ring_h"]
    # Knob shoulder: bore just outside the ring, skirt overlapping the ring from above.
    D["lab_shoulder_r"] = D["lab_ring_r"] + D["lab_gap"]
    D["lab_shoulder_z1"] = D["lab_ring_z1"]
    D["lab_shoulder_z0"] = D["lab_ring_z1"] - D["lab_overlap"]
    D["z_bolt0"] = D["z_fp0"] - D["engage"]
    # Cover screws. The axis is inside the PCB outline; a notch in the board lets the
    # resin post occupy the corner and the wall. Upper pair sits in the gap between the
    # knob and the joystick opening. With the scanner parked, the lower pair moves up
    # against the knob so two collar bolts still fit above the full TFT window.
    bx = D["boss_x"]
    gap = D["boss_gap"]
    dmin = D["knob_hole_r"] + br + gap
    y_knob = math.sqrt(max(0.0, dmin * dmin - bx * bx))
    y_joy = D["joy_y_near"] - br - gap
    D["boss_y_room"] = y_joy - y_knob
    y_hi = (y_knob + y_joy) / 2.0 if y_joy >= y_knob else y_knob
    y_scan = D["y_mot"] + D["mirror_r"] + br + gap
    y_floor = D["pcb_y0"] + br + gap
    if D["bot_posts_in_wall"]:   # [Ed 2 Nov] bottom pair into the bottom wall, like boss_x into the side wall
        y_floor = D["body_y0"] + D["web_min"] + br
    if D["scanner_enabled"]:
        y_floor = max(y_scan, y_floor)
    if D["tft_on_front"]:
        y_above = D["win_y1"] + br + D["tft_gap"]
        y_lo = y_above if (not D["scanner_enabled"] or y_above <= -y_knob) else (
            y_floor if y_floor <= -y_knob else -y_knob)
    else:
        y_above = y_floor
        y_lo = y_floor if y_floor <= -y_knob else -y_knob

    def _y_for(x):
        y = y_lo
        if D["tft_on_front"] and _clear_rect(x, y, br, D["win_x0"], D["win_y0"], D["win_x1"], D["win_y1"]) < D["tft_gap"]:
            if y_above <= -y_knob:
                y = y_above
        return y

    if D["top_corners"]:
        y_hi = D["pcb_y1"] - br - gap   # [Ed] mirror of the bottom pair (pcb_y0 + br + gap)
    dr = D["bot_post_drop"] if D["bot_posts_in_wall"] else 0.0   # [Ed 4 Nov 20:12] bottom pair lower, out of the jacks' path
    D["corners"] = ((-bx, _y_for(-bx) - dr), (bx, _y_for(bx) - dr), (-bx, y_hi), (bx, y_hi))
    # jacks and USB-C (panel frame, from the panel bottom edge)
    D["jack_y"] = D["panel_y0"] + D["jack_y_up"]
    D["jack_xy"] = tuple((x, D["jack_y"]) for x in D["jack_xs"])
    D["usb_xy"] = (0.0, D["panel_y0"] + D["usb_y_up"])
    D["jack_depth_z0"] = D["z_fp0"] - D["jack_depth"]
    # step 2 [Ed 4 Nov 20:12]: the jacks' straight path from behind. The bottom posts are cut flat post_jack_air under the jack bodies;
    # the side ledges are notched (and the side glow coat left off) along the jack row.
    jby = D.get("jack_body_y") or (-D["jack_h"] / 2, D["jack_h"] / 2)   # v0.39: the real body sits off-centre on its bushing
    D["jack_bot_y"] = D["jack_y"] + jby[0]
    D["jack_top_y"] = D["jack_y"] + jby[1]
    if D.get("jack_pins"):   # v0.39 [Ed 15:53 Q15 = A]: the jack board reaches down to each sleeve pin (a tongue)
        _n, s0, s1, sw = [p for p in D["jack_pins"] if p[0] == "S"][0]
        D["jb_tongue_hw"] = sw / 2 + D["jack_slot_ring"] + D["jb_tongue_edge"]
        D["jb_tongue_y"] = D["jack_y"] + min(s0, s1) - sw / 2 - D["jack_slot_ring"] - D["jb_tongue_edge"]
        # v0.44 [A]: the outer two tongues 0.5 wider on their inner side (toward x 0), so the sleeve's ground can leave the tongue past
        # the ring slot's pad (0.63 between pad and the tongue's inside corner was too tight to route); (x0, x1) per jack
        ti = D.get("jb_tongue_inner", 0.0); xo0, xo1 = min(D["jack_xs"]), max(D["jack_xs"]); hw_ = D["jb_tongue_hw"]
        D["jb_tongue_x"] = tuple((x - hw_, x + hw_ + ti) if x == xo0 else (x - hw_ - ti, x + hw_) if x == xo1 else (x - hw_, x + hw_)
                                 for x in D["jack_xs"])
    D["post_clip_y"] = D["jack_bot_y"] - D["post_jack_air"] if dr else None
    D["jack_notch_y"] = (D["jack_bot_y"] - D["jack_lip_notch"], D["jack_top_y"] + D["jack_lip_notch"])
    yb = D["corners"][0][1]; ri = D["insert_od"] / 2 + D["insert_glue"]
    D["post_insert_wall_jack"] = (D["post_clip_y"] - (yb + ri)) if dr else None   # resin, insert hole to the flat
    D["post_insert_wall_out"] = (yb - ri) - D["body_y0"]                          # resin, insert hole to the bottom face
    D["jack_post_air"] = D["jack_bot_y"] - (D["post_clip_y"] if dr else yb + br)
    # v0.33 [Ed 21:30] the jack boards: the jack row's outline, z from the jacks' backs down
    D["jb_x"] = (min(D["jack_xs"]) - D["jack_w"] / 2, max(D["jack_xs"]) + D["jack_w"] / 2)
    D["jb_z1"] = D["jack_depth_z0"]; D["jb_z0"] = D["jb_z1"] - D["jb_t"]
    D["jb_under_z0"] = D["jb_z0"] - D["jb_under"]
    D["jb2_z1"] = D["jb_z0"] - D["jb2_gap"]; D["jb2_z0"] = D["jb2_z1"] - D["jb2_t"]
    D["jb2_parts_z1"] = D["jb2_z1"] + D["jb2_parts"]
    D["jb_env_air"] = D["jb_under_z0"] - D["jb2_parts_z1"]                 # between the two parts envelopes
    D["jb_pin_tip_air"] = (D["jack_depth_z0"] - D["jack_pin_len"]) - D["jb2_parts_z1"]   # jack pin tips to the power board's parts
    D["jb_pin_out"] = D["jb_z0"] - (D["jack_depth_z0"] - D["jack_pin_len"])   # pins through the jack board
    D["zif_z0"] = D["jb2_z0"] - max(D["zif_oled"][2], D["zif_link"][2])
    # [Ed 4 Nov 20:15] USB-C: channel through the bottom wall from the back edge to the board's front face, a ledge in front, a key behind
    uw, uh, ud = D["usb_rcpt"]; bw, bh, bt = D["usb_board"]
    D["usb_z1"] = D["z_fp1"] - ud            # board front face (bears on the ledge)
    D["usb_z0"] = D["usb_z1"] - bt           # board back face (the key bears on it)
    D["usb_board_y0"] = D["usb_xy"][1] - bh / 2
    D["usb_board_y1"] = D["usb_xy"][1] + bh / 2
    D["usb_ch_hw"] = bw / 2 + D["usb_slot_clear"]
    D["usb_pocket_hw"] = uw / 2 + 0.15        # as the faceplate opening
    D["usb_pocket_y0"] = D["usb_xy"][1] - uh / 2 - 0.15
    D["usb_ledge_side"] = bw / 2 - D["usb_pocket_hw"]                  # board edge over the ledge, each side of the receptacle pocket
    D["usb_ledge_below"] = D["usb_pocket_y0"] - max(D["usb_board_y0"], D["body_y0"])   # under the pocket
    D["usb_board_out"] = D["body_y0"] - D["usb_board_y0"]             # board edge past the bottom face (0 = flush)
    D["usb_jack_air"] = D["jack_bot_y"] - D["usb_board_y1"]
    # Knob bolts: on the bolt circle outside the collar, lower arc only (the bezel
    # occupies +Y). Placed after the corners so a bolt is not spent on a post it hits.
    D["bolt_r"] = D["collar_r"] + D["seat_gap"] + br
    limit_x = D["panel_w"] / 2.0 - br - D["web_min"]
    sep = 2.0 * br + gap

    def _bolt_ok(x, y, chosen):
        if abs(x) > limit_x or y - br < D["body_y0"] or y + br > D["body_y1"]:
            return False
        if abs(x) + br + D["seat_gap"] > D["x_in1"]:
            return False
        dx = max(abs(x) - D["hole_hw"], 0.0)
        dy = max(abs(y - D["place_y"]) - D["hole_hh"], 0.0)
        if math.hypot(dx, dy) < br + D["seat_gap"]:
            return False
        if D["tft_on_front"] and _clear_rect(x, y, br, D["win_x0"], D["win_y0"], D["win_x1"], D["win_y1"]) < D["tft_gap"] - 1e-9:
            return False
        if any(math.hypot(x - cx, y - cy) < sep - 1e-6 for cx, cy in D["corners"]):
            return False
        if any(math.hypot(x - px, y - py) < sep - 1e-6 for px, py in chosen):
            return False
        return True

    bolts = []
    if D["tft_on_front"]:
        y_bolt = y_above
        disc = D["bolt_r"] * D["bolt_r"] - y_bolt * y_bolt
        if disc > 0.0:
            x_bolt = math.sqrt(disc)
            for x in (x_bolt, -x_bolt):
                if _bolt_ok(x, y_bolt, bolts):
                    bolts.append((x, y_bolt))
    if len(bolts) < D["knob_bolt_n"]:
        steps = 180
        for i in range(steps):
            ang = math.pi * (1.0 + (i + 0.5) / steps)   # π .. 2π, away from the bezel
            x = D["bolt_r"] * math.cos(ang)
            y = D["bolt_r"] * math.sin(ang)
            if _bolt_ok(x, y, bolts):
                bolts.append((x, y))
            if len(bolts) >= D["knob_bolt_n"]:
                break
    D["knob_bolts"] = tuple(bolts)
    D["notch_r"] = br + D["notch_gap"]
    D["boss_knob_clear"] = min(math.hypot(x, y) - D["knob_hole_r"] - br for x, y in D["corners"])
    D["boss_joy_clear"] = min(
        _clear_rect(x, y, br, -D["hole_hw"], D["joy_y_near"], D["hole_hw"], D["joy_y_far"]) for x, y in D["corners"])
    D["boss_scan_clear"] = min(math.hypot(x - D["x_mot"], y - D["y_mot"]) - D["mirror_r"] - br for x, y in D["corners"])
    D["boss_win_clear"] = min(
        _clear_rect(x, y, br, D["win_x0"], D["win_y0"], D["win_x1"], D["win_y1"]) for x, y in D["corners"])
    D["z_thread0"] = D["z_rim"]
    D["tap_len"] = D["engage"] - D["screw_p"]
    D["z_thread1"] = D["z_thread0"] + D["tap_len"]
    D["z_insert1"] = D["z_rim"] + D["insert_len"]
    # Corner posts stop under the jack pins. The thread is only the lower ~7 mm; the post is fused to the side wall,
    # so it does not need to reach the plate, and a full-height post would run into the jack bodies.
    D["z_jack_pins"] = D["z_fp0"] - D["jack_depth"] - D["jack_pin_len"]
    D["z_post_top"] = D["z_jack_pins"] - D["post_jack_clear"]
    # ISO 4762 length is under the head. M3×10 is fully threaded, so the thread
    # starts at the bearing face and the tip lands inside the printed tap.
    D["z_screw_under"] = D["z_pad_out"] + D["cbore_depth"]
    if D["cover_screw"] == "back":
        D["z_screw_under"] = D["z_cover_out"] + D["cbore_depth"]
        need = D["z_rim"] + D["insert_engage_min"] * D["screw_d"] - D["z_screw_under"]
        top = D["z_post_top"] - D["wall"] - D["tip_hole"] - D["z_screw_under"]
        fits = [L for L in D["screw_lens"] if need <= L <= top]
        D["screw_len"] = float(fits[0] if fits else max(L for L in D["screw_lens"] if L <= top))
        # slim column through the screen layer, then a 45° flare to the ring that bears on the board round its notch
        D["col_r"] = max(D["hole_r"] + D["col_wall"], D["cbore_r"] + 0.3)
        D["col_ring_r"] = D["notch_r"] + D["tube_press"]
        scr_top = max(D["amo_lower_z"][1], D["amo_upper_z"][1]) if D["back_screens"] == "amoled2" else D["z_cover_in"]
        D["col_z1"] = scr_top + D["col_screen_air"]
        D["col_z2"] = D["col_z1"] + max(0.0, D["col_ring_r"] - D["col_r"])
        D["cover_skin"] = D["col_z1"] - D["z_screw_under"]   # solid PETG over the head before the flare
        if D["back_screens"] == "amoled2":   # how far each screen could still move toward its end before a column
            ra, half = D["col_r"] + D["col_screen_air"], D["amo_w"] / 2
            dx = min(abs(x) for x, _ in D["corners"]) - half
            dy = math.sqrt(max(ra * ra - dx * dx, 0.0)) if dx < ra else 0.0
            yb = min(y for _, y in D["corners"]); yt = max(y for _, y in D["corners"])
            D["amo_room_lower"] = D["amo_lower"][2] - (yb + dy)
            D["amo_room_upper"] = (yt - dy) - D["amo_upper"][3]
    D["screw_grip"] = D["z_thread0"] - D["z_screw_under"]
    D["screw_thread"] = D["screw_len"] if D["screw_len"] <= D["screw_full_to"] else D["screw_b"]
    D["screw_engage"] = D["screw_thread"] - D["screw_grip"]
    D["z_tip"] = D["z_screw_under"] + D["screw_len"]
    D["z_bolt_tip"] = D["z_bolt0"] + D["tap_len"]
    D["edge_t"] = D["fp_t"]
    D["ligament_t"] = D["fp_t"]
    D["edge_depth"] = 0.0
    D["lig_depth"] = 0.0
    D["scope_short"] = D["pcb_w"] - D["pcb_max_w"]
    D["bezel_w"] = 2.0 * D["half_w"]
    D["bezel_margin"] = (D["panel_w"] - D["bezel_w"]) / 2.0
    D["bezel49_margin"] = (D["panel_w"] - 49.0) / 2.0
    D["collar_od"] = 2.0 * D["collar_r"]
    D["collar_margin"] = (D["panel_w"] - D["collar_od"]) / 2.0
    # top rail screws: room beside the joystick opening, inside the panel, with an SLA web both sides
    top_span = (D["panel_w"] - D["joy_hole"][0]) / 2.0
    # v0.20: the web is measured in plan from each top rail hole to the joystick opening (v0.19 measured x only, so the
    # holes were never cut once the knob_drop put them above the opening)
    D["rail_top_web"] = min(_clear_rect(x, D["rail_y_top"], D["rail_hole_d"] / 2, -D["hole_hw"], D["joy_y_near"],
                                        D["hole_hw"], D["joy_y_far"]) for x in D["rail_x_top"])
    D["rail_top_ok"] = 1.0 if D["rail_top_web"] >= D["sla_min"] else 0.0
    # the washer under each rail screw vs the bezel slid all the way toward it
    s_ = D["slide"]
    D["rail_head_clear"] = min(_clear_rect(x, D["rail_y_top"], D["rail_keep_d"] / 2, -D["half_w"] - s_, D["bezel_y_near"] - s_,
                                           D["half_w"] + s_, D["bezel_y_far"] + s_) for x in D["rail_x_top"])
    # clear OLED (electronics, knob frame) vs the bottom corner posts
    w_, h_, _t = D["clear_oled"]; cx_, cy_ = D["clear_oled_xy"]
    D["oled_post_clear"] = min(_clear_rect(x, y, D["screw_boss_r"], cx_ - w_ / 2, cy_ - h_ / 2, cx_ + w_ / 2, cy_ + h_ / 2)
                               for x, y in D["corners"][:2])
    # Front face freed below the knob, above the rail zone. Jack bodies must stay
    # inside the panel; the pitch is the body plus air, and also the 3 HP column.
    D["face_y0"] = D["panel_y0"] + D["rail_clear"]
    D["face_y1"] = -D["knob_hole_r"]
    D["face_free_h"] = D["face_y1"] - D["face_y0"]
    D["face_free_w"] = D["panel_w"]
    half = D["jack_body"] / 2.0
    D["jack_x_lim"] = D["panel_w"] / 2.0 - half - D["jack_air"]
    D["jack_pitch"] = D["jack_body"] + D["jack_air"]
    D["jack_pitch_hp"] = 3.0 * D["hp_pitch"]
    pitch = max(D["jack_pitch"], D["jack_pitch_hp"])
    usb_gap = half + D["usb_w"] / 2.0 + D["jack_air"]
    span = 2.0 * D["jack_x_lim"]
    k = 0
    while k < 8 and (k * pitch + usb_gap) <= span + 1e-9:
        k += 1
    D["jack_n"] = k
    D["jack_pitch_used"] = pitch
    D["usb_gap"] = usb_gap
    D["ox"] = 0.0
    D["oy"] = 0.0
    return D
