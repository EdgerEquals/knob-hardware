"""Top-screen joystick stack v0.8 — params + derive.

v0.8 (3 Nov 2026, step-1 follow-ups, Ed 13:09–14:08): the cup over the SKRHADE010 stem is printed into the bezel (grip block) and its
ceiling sits on the stem, so the switch's own click is the press: the carrier's cup, the press peg (grub + insert), the four Lee press
springs with their grubs and inserts, and the Ø1.6 grub-access holes through the main board and the top board all go. The guides stay;
their heads are the up-stop with a float band and a thin cushion ring under each carrier guide boss (comparison in derive: O-ring /
silicone sponge / PORON). The top board no longer rides on spring contacts: male 1.27 pins on the vertical boards' top edges plug
into single-row 1.27 sockets under the top board, and the boards' end tabs bear on the top board (the boards are the posts), so
closing the case clamps the cradle flange onto a form-in-place silicone bead. The top edge (over the rail strip) gets a step: a
rebate in the cutout wall and a dam on the lip ring, with the bead in it.

v0.7 (3 Nov 2026, layout v4 step 1, Ed 09:47–11:32): base "case". The printed cradle glued to the main PCB, its dowels, the two
2x5 H11 sockets and the long-pin headers go: the H7B0 takes their place on the main PCB, and two vertical boards (electronics sub,
x ±16) carry the signals up. The daughterboard becomes the TOP BOARD: it rests on the vertical boards' spring contacts and is glued
into a new clear SLA cradle that is captured by the case: a flange behind the faceplate (on a thin gasket) and a lip up into the
faceplate's joystick cutout. The lip shares the cutout with the carrier, so the carrier narrows by lip + clearance (the cutout and
the grip block keep their size, so the block still covers the cutout by fp_overlap); the balls follow the carrier corners in. The
carrier skirt goes: the lip ring is the anti-rotation stop. On the +y side the faceplate sits on the rail strip, so the flange
cannot get behind it there: the lip ring closes across the top inside the cutout only.

v0.6 (2 Nov 2026, Ed 16:14–16:33): the screen is the DWO DO0164FMST02 (geometry from Waveshare's STEP of the ESP32-S3-Touch-
AMOLED-1.64). Its flex leaves the -x end [Ed 16:18] and folds under the panel; a 30-pin 0.4 mm B2B header sits 2.15 behind the
glass at x +11.75. The roof is pocketed to the panel's back (and thickened so the deepest pocket keeps the print minimum), windowed
at the connector, with a foam pad over the back sheet so a press on the glass goes into the roof. A short custom jumper [Ed 16:22]:
a B2B socket on the panel header, a flex run under the roof to the existing drop at x 16, a plug into the daughterboard socket.
The guides turn to (+6.5, +3.0) / (-6.5, -3.0) [Ed 16:31]; their heads stay low (the switch test uses its real 45° outline).

v0.5 (2 Nov 2026, Ed): the bezel is a 5 mm grip block with the glass on top; the switch stack is lifted 2 mm on
M2x30 standoffs so the carrier rises into the faceplate hole; two guide screws in brass sleeves tie the bezel to the
carrier (no rocking on the press springs, and their heads are the up-stop v0.4 lacked); the joystick sits as high as
the top rail screws (ISO 7092 Ø6 washers) allow, and the knob moves down on the panel instead (finger room);
a printed cradle glued to the main PCB replaces the standoffs and the seat plate, with the balls at its extreme corners and
the springs inside them; two 2x5 board-to-board headers; the screen flex socket sits on a tab of the joystick board.
Review fixes (2 Nov): the block floats press-travel + one tolerance above the flat faceplate (the case has no rebate); the
press peg is an M2 grub set with a feeler; guides on the long axis; carrier corners rounded to the opening's radius.

Local frame: origin = carrier centre on the MAIN PCB FRONT (z = 0), +x right along the panel width, +y up the panel
(toward the panel top), +z out of the panel. Placement in the knob-param frame (dial axis = 0,0): (0, place_y).
Tags: [Ed] Ed's decision, [S] datasheet, [L] panel layout, [K] main-PCB KiCad, [A] assumed.
Every derived value is computed in derive(); parts and checks read only P + derived values.

The switch is on the carrier axis. Two 1x3 headers sit on the underside, one each side, and four standoffs
sit in the quadrants. There is no printed base, no nylon spider, no plunger and no round stop. The switch's
own end of travel is the only stop for tilt and for the centre press.

The screen is glued to a separate screen carrier (the bezel). Four catalog compression springs sit at the
top, between that bezel and the main carrier, outside the glass. Each spring stands on an M2 grub screw in a
brass insert in the carrier floor. Ed dials the preload on the carrier + bezel sub-assembly, from underneath,
before the rest of the stack goes together. Nothing is added so the screws can be reached later.
Four hold-down extension springs still hold the carrier down on the balls. They do not touch the new springs.

The bezel is taller at the four spring corners than along the middle of the long sides. The middle is what
faces the knob, so the corners can clear the glass without pushing the module off the main-PCB standoffs.

Screen: DWO DO0164FMST05, 1.64" 280x456 AMOLED, mounted landscape. The FPC exit side, pin count, pitch
and pin-out were not on the pages that could be fetched — the FPC is modelled [A] and the pin-out stays open.
"""
import math
import os
import sys

P = dict(
    version="v0.8",
    # ---- placement. place_y is derived so the notched edge clears the knob ----
    knob_od_design=41.70,   # [Ed] size the plan to the v0.17 knob. The live knob-param OD is checked too
    knob_extra=0.0,         # nominal gap is the process stack itself (v0.4 rule only)
    place_rule="rail",      # [Ed] 2 Nov v0.5: "rail" = as high as the top rail screw keep-out allows (the case owns the rule
                            # and publishes place_y); "knob" = v0.4, as close to the knob as the process stack allows
    finger_min=5.0,         # [Ed] 2 Nov: plan gap from the knob glass to the bezel at rest, at least this (finger room)
    pcb_edge=0.30,          # [A] a PTH pad stays this far inside the main-PCB copper edge
    rail_z=10.0,            # [A] Eurorack rail does not reach this far in front of the PCB
    # PCBWay process tolerances. A clearance is one of these, not a looser drawing gap.
    tol_sla=0.20,           # [S] SLA resin, the wide end of PCBWay's ±0.1–0.2 mm
    tol_mjf=0.25,           # [S] MJF/SLS nylon
    tol_fdm=0.20,           # [S] FDM, if a jig or a trial part is printed that way
    # ---- screen (landscape: datasheet portrait 26.74 W x 41.62 H) ----
    scr=dict(part="DWO DO0164FMST02 1.64\" 456x280 AMOLED", w=41.62, h=26.74, t=1.5, active=(35.57, 21.84),
             mass_g=8.0),  # [Ed 16:14] FMST02 (was FMST05: no drawing found). [S] outline/thickness; mass [A] until weighed
    # v0.6 [S] the FMST02's back, from Waveshare's STEP (esp32-s3-touch-amoled-1_64.stp, read with cad/joystick-param/fmst02_fit.py):
    # boxes (name, x0, x1, y0, y1, depth behind the glass back) in this frame, flex leaving -x [Ed 16:18]. Depths to ±0.025.
    scr_back=(("back sheet", -13.9, 11.9, -11.4, 11.4, 0.20),
              ("flex layer", -12.0, 3.4, -6.5, 11.3, 0.45),
              ("flex fold at the -x edge", -19.8, -12.1, -6.5, 8.8, 0.70),
              ("connector flex", -6.6, 11.8, -9.2, 3.6, 0.80),
              ("part B", -6.6, 5.4, -9.2, -0.2, 0.90),
              ("part A", -9.6, -4.6, 5.0, 10.0, 1.20),
              ("part C", -0.6, 3.4, 5.8, 10.0, 1.20),
              ("part D", 0.4, 4.1, -8.9, -5.2, 1.20),
              ("connector plate", 4.9, 13.7, -4.3, 4.3, 1.50),
              ("B2B header", 10.5, 13.0, -4.0, 4.0, 2.15)),
    scr_window=("connector plate", "B2B header"),   # the roof is windowed / stepped under these, not pocketed
    hdr_x=11.75,            # [S] B2B header centre (x); centred across the width
    back_side=0.20,         # [A] pocket margin round each back feature, in plan
    back_clear=0.15,        # [A] pocket floor below each back feature
    foam_t=0.15,            # [A] foam pad (PET-carrier foam tape) between the back sheet and its pocket floor: a press on the glass
                            # goes into the roof and the peg, not into bending the panel
    step_t=1.0,             # [A] roof step under the connector plate (no jumper there), carries the +x guide boss
    scr_below_knob=5.0,     # [Ed] old screen target. knob_proud now places the faceplate; the screen follows the bezel
    knob_proud=16.45,       # [Ed] adopted value. derive() recomputes it from the 25 mm riser; 16–20 is the accepted window
    knob_proud_window=(16.0, 22.4),   # [Ed] faceplate to the knob glass: 16–20 (v0.18); knob +4.4 accepted [Ed 3 Nov 12:28/12:41] -> 22.4
    print_min=1.0,          # [S] PCBWay SLS nylon minimum wall (SLA resin is 0.8). Structural walls use this
    # FPC: v0.6 the custom jumper [Ed 16:22]. Width / thickness [A] until it is drawn.
    fpc_w=3.0,              # [Ed 17:13] no touch: 13 lines (QSPI CLK, CS, D0-D3, RESET, TE, PWR_EN, 3V3, three GND) at 0.2 pitch [A]
    fpc_t=0.12,             # [A]
    fpc_bend=2.6,           # [A] screen +x edge to the slot centre, when the skirt allows it (v0.4)
    fpc_slot_l=2.3,         # [A] v0.5; v0.6 derives the slot from the jumper's bottom plug (it must pass on assembly)
    jmp_stiff=(4.0, 0.25),  # [A] jumper top end: stiffener (x) width and stiffener + flex thickness under the socket; its y length = the socket
    # [Ed 17:13-17:16] the jumper is narrow and long enough to flex: a loose loop under the carrier. Legs (envelopes): R under the
    # roof (takes the press), V1 down the carrier slot and S1 on edge along y (take x), S2 on edge along -x and, past a 180° crease,
    # S3 back along +x (take y), then down onto the plug. They run low, just over the plug, where there is length.
    jmp_t=0.10,             # [A] single-layer flex: PI 25 + RA copper 12 µm + coverlay 25 + adhesive
    jmp_cu_c=0.011,         # [A] copper distance from the neutral axis (12 µm centred, ±5 µm build tolerance: the cautious case)
    jmp_fatigue=0.003,      # [A] RA copper strain amplitude for ~1e6-1e7 cycles (switch: 1e6 per direction, Alps SKRH)
    jmp_margin=2.0,         # [A] working margin on that (Claude's number for Ed's "nothing close to its threshold")
    jmp_bend=0.3,           # [A] length taken by each fold or crease
    jmp_xv=18.5,            # [A] plane of V1 and S1 (inside the carrier slot, 0.8 from its edge)
    jmp_y2=-4.0, jmp_y3=-3.2,   # [A] planes of S2 and S3 (clear of the hold-down spring at y -1.5 and the grub key line at y -5.6)
    jmp_xa=9.0, jmp_xb=14.0,    # [A] S2 runs from jmp_xv to jmp_xa; S3 back from jmp_xa to jmp_xb, then down onto the plug
    # ---- carrier / bezel ----
    car_top_below=0.3,      # [A] glass stands this far proud of the bezel top
    bz_lip=1.2,             # [Ed] bezel lip (side wall of the grip block), same as the other bezel. 1.5 mm is the maximum
    bz_t=1.2,               # [Ed] v0.4 bezel thickness; v0.5 uses grip_h for the height (kept so old overrides parse)
    grip_h=5.0,             # [Ed] 2 Nov v0.5: the bezel is a grip block at least 5 mm tall, glass on top; the faceplate tucks in behind its edge
    glass_proud=0.6,        # [A] glass top above the block rim (as v0.4: 1.5 glass on 0.3 pads in a 1.2 bezel)
    roof_t=1.6,             # [A] roof plate under the glass: the springs push on its underside, the glass is glued on top.
                            # v0.6: derive() raises it so the deepest back pocket keeps print_min of roof
    # guides (v0.5, Ed 2 Nov): two screws through brass sleeves tie the bezel to the carrier. The sleeve slides in a reamed
    # bore in the carrier; the screw head under the carrier boss is the up-stop (v0.4 had none).
    guide=dict(part="ISO 7984 M2 A2 low-head socket screw (length from derive) + brass tube sleeve OD 3.0 / ID 2.1, cut to length",
               d=2.0, sleeve_od=3.0, head_d=3.8, head_k=1.6, bore_fit=0.03, boss_wall=1.0,
               ins=dict(part="M2x3x3.2 brass heat-set (bezel roof)", od=3.2, length=3.0, hole=3.0)),   # [S] DIN 7984 M2 head Ø3.8 × 1.6 max [A]
    guide_xy=(6.5, 3.0),    # [Ed 16:31] turned pair (+6.5, +3.0) / (-6.5, -3.0): clear of the FMST02 header window (v0.5: (±8.5, 0))
    solder_h=0.6,           # [A] header solder joints / trimmed tails above the joystick board top
    # press peg (review fix): an M2 grub in a roof insert at the centre, set to the press gap with a feeler before the glass goes on
    peg=dict(part="ISO 4026 M2 A2 flat-point grub (press peg, set with a 0.2 feeler, threadlocker)", d=2.0,
             ins=dict(part="M2x3x3.2 brass heat-set (bezel roof, centre)", od=3.2, length=3.0, hole=3.0)),
    corner_r=1.2,           # [A] carrier floor corners = the case opening's corner radius (case hole_corner_r)
    fp_t=2.5,               # [A] faceplate of the one-piece case. UTR-8100 clear resin, wall ~2.5 mm
    fp_overlap=0.90,        # [A] how far the lip covers the faceplate at rest, before the slide
    skirt_overlap=0.75,     # [A] skirt reaches this far below the plate
    # ---- return springs (Lee Spring instrument series, catalog) ----
    # 5.5 lbf/in = 0.963 N/mm. Short on purpose: the spring lives in the bezel, not in a thick floor.
    cs=dict(part="Lee Spring CI 008B 01 M", wire=0.20, od=2.24, free=3.18, rate_lb_in=5.5,
            solid=1.07, hole=2.38, rod=1.68),  # [S] music wire, tinned; hole/rod are Lee's machined sizes
    cs_turns=0.5,           # [A] nominal preload, in turns of the M2 grub, set on the sub-assembly
    # grub screw and the insert it runs in. The hex hangs under the carrier. No later access hole.
    grub=dict(part="ISO 4026 M2x3 A2 flat point", pitch=0.40, length=3.0, d=2.0, flat=1.0),  # [S] DIN 913, hex 0.9
    ins=dict(part="M2x2x3.2 brass heat-set", od=3.2, length=2.0, hole=3.0),  # [S] knurled insert, L x OD
    # ---- cup. The bore is derived: stem diameter plus one SLA tolerance per side ----
    cup_od=5.0,             # [A]
    cup_engage=1.2,         # [A]
    stem_below=1.10,        # [Ed] 2 Nov: carrier underside above the stem top
    fpc_to_db=True,         # [Ed] 2 Nov: the screen flex plugs into a socket on the joystick daughterboard (no slot in the main PCB;
                            # the old drop landed on the top-right corner bolt post). Signals go down through the board-to-board headers.
    db_fpc_sock=(8.4, 3.0, 0.9),   # [S/A] AXE530127 30-pin 0.4 mm socket: long side (along y, the flex width), short side (x), mated height
    db_fpc_x_in=3.0,        # [A] v0.4 only (socket under the plate)
    # ---- switch ----
    sw=dict(part="Alps SKRHADE010", w=7.45, d=7.5, h=1.85, stem_d=3.0, stem_top=5.0, pivot=0.49, ref_h=4.3,
            tilt_travel=0.25, push_travel=0.15, tilt_f=1.2, push_f=2.35, f_tol=0.69,   # [S]
            pad_x=3.575, pad_y=1.425, pad=(1.35, 1.0), tab_y=4.05, tab=(2.0, 1.8)),    # [S] land pattern
    sw_rot=-45.0,           # [Ed] directions line up with the screen axes
    # ---- daughterboard. Outline is derived. Thickness is the fab stack, not the print minimum ----
    db_t=1.0,               # [A] 2-layer FR4
    cu_edge=0.30,           # [A] copper-to-outline, same rule as the KiCad board
    pitch=2.54,             # [S]
    # male header, plastic on the UNDERSIDE, pin down into the socket. Lead style -17 is the
    # straight-pin post that mates a 25 mm riser (Samtec TSW chart: tail 2.79, post 15.74).
    # The -20 post (25.91) went through the main PCB. The 1x3 is consigned; LCSC's -20 line is 2-row.
    # v0.5: two 2x5 (20 pins), long side along y: 10 signals (QSPI CLK, CS, IO0-3, RST, TE, PWR_EN, switch ladder), three 3.3 V
    # and grounds between the QSPI lines. Room for them came with the cradle (no standoffs).
    hdr=dict(part="Samtec TSW-105-xx-T-D long-post 2x5 header, post about 21.5 mm for the 30 mm cradle (exact -xx code to pick)", lcsc="consigned", mate=21.5, ins=2.54, tail=2.79, n=5, rows=2, axis="y"),  # [Ed] 2 Nov v0.5
    sock=dict(part="2.54 mm 2x5 female socket, 11 mm (hanxia PM2.54 H11 family, 2x5 part to pick)", lcsc="TBC", h=11.0, tail=3.2, n=5, rows=2),  # [A] v0.5 (v0.4: 1x3 C41427518)
    # v0.5 base [Ed 2 Nov 12:17]: a printed cradle glued to the main PCB (two locating dowels) replaces the four standoffs and
    # the seat plate. The joystick board is glued on its rim. The lower ball seats stand on towers at its extreme corners.
    base="case",   # [Ed 3 Nov 11:03] v0.7 layout v4: "case" = top board on the vertical boards' spring contacts, nested in a cradle
                   # captured by the case (flange + lip). "cradle" = v0.5/v0.6 printed cradle glued to the main PCB (kept for history)
    cradle=dict(part="joystick cradle, MJF PA-12, glued to the main PCB and to the joystick board", h=30.0, wall=1.5, wall_top=1.0,
                land=0.7, tower_z0=22.5, pin=dict(part="ISO 8734 1.5x5 stainless dowel", d=1.5, len=5.0, in_pcb=1.6)),   # [A]
    # ---- v0.7 [Ed 3 Nov] top board on the vertical boards, case cradle ----
    tb_z0=30.0,             # [A] top board underside, kept at the v0.6 daughterboard height so the switch / carrier / bezel stack does
                            # not move. electronics vb.top_board_z must match (assembly cross-check)
    vb_y_panel=(26.5, 48.4),   # [Ed 09:47] the vertical boards' y span, panel frame (mirror of electronics vb.y; assembly cross-check).
                               # The top board covers their top edges so the spring contacts can run the whole length
    vb_contact_x=17.5,      # [A] mirror of electronics: the spring-contact plunger line (board plane ±16.0, outer face ±16.5, contact
                            # strip body 2.0 on the outer face, plungers on its middle). Outer face: the inner face is 2.0 from the
                            # hold-down springs. Assembly cross-check against electronics
    tb_pad=1.6,             # [A] ENIG pad Ø under the top board for each spring contact
    tb_tol=0.30,            # [A] contact position in plan (vertical-board solder position + cradle location in the cutout)
    tb_y_over=0.40,         # [A] top board past each end of the vertical boards
    cc=dict(part="joystick case cradle, UTR-8100 clear resin (SLA), lip in the faceplate cutout, flange on a gasket",
            lip_c=0.20,     # [A] lip to the cutout wall, each side ("about 0.2 a side"; SLA case ±0.20 and SLA cradle ±0.20: fit-check)
            lip_t=1.0,      # [A] lip wall (SLA minimum 0.8 [S])
            lip_below=0.5,  # [A] lip top this far under the faceplate front (the grip block covers the cutout, so it is never seen)
            flange_t=1.2,   # [A] flange behind the faceplate
            wall=1.0,       # [A] hangers / end walls round the top board
            nest_c=0.20,    # [A] top board edge to the nest walls
            shoulder=1.0,   # [A] shoulder over the top board's edge (the board is glued to it; the spring contacts push it up)
            seat_above=1.0, # [A] lower ball-seat bosses start this far above the top board's top face (parts under them stay lower)
            collar_air=0.5, # [A] flange −y edge to the knob collar (case collar_r)
            glow_air=0.20,  # [A] flange ±x edge to the case side-wall glow coat (the coat is modelled 0.3 off the wall, 0.35 thick)
            top_air=0.20),  # [A] flange +y end to the case top wall inner face (no contact: the lip ring locates in y)
    gasket=dict(part="closed-cell silicone sponge gasket, 0.8 thick, die-cut, adhesive one side [A]", t=0.80,
                comp_nom=0.25, comp_lo=0.10, comp_hi=0.50,   # [A] compression: nominal, and the working band of the sponge
                land_min=0.75),   # [A] narrowest gasket land under the faceplate that is still a die-cut strip
    # ---- v0.8 [Ed 3 Nov 13:09–14:08] step-1 follow-ups ----
    cup_in_bezel=True,      # [Ed 13:09] the cup over the stem is printed into the bezel (grip block); its ceiling sits on the stem (no
                            # gap), so the switch's own click is the press. False = v0.7 (cup in the carrier, peg over a 0.2 gap)
    press_springs=False,    # [Ed 13:16/13:18] no Lee press springs, no grubs, no inserts, no press peg (True = v0.7)
    up_gap_set=0.55,        # [A] bezel underside above the faceplate front, kept at v0.7's 0.55 so the block, the screen and the case do
                            # not move (the press is now 0.15, so the block clears the faceplate by 0.40 at full press)
    guide_boss_ratio=0.95,  # [A] carrier guide boss length / sleeve OD (v0.7 1.1; >= 0.9 is the check): 0.3 shorter to make room for the
                            # 1.59 cushion under it
    guide_keepout=0.05,     # [A] top board under each guide head: no parts, no tails (KiCad keep-out Ø head + 2 × 0.25); this is the
                            # height of what is left there (mask, silk). v0.7 used solder_h 0.6 (header tails, gone since v0.7)
    # up-stop [Ed 13:09 "guides stay"; Danny 13:21 suggested silicone]: a thin cushion ring glued under each carrier guide boss, round the
    # sleeve; the screw head meets it when the bezel is lifted off the stem. The gap is set so the cushion does NOT preload the stem over
    # the RSS band of the stack below (preload on the stem takes straight off the hold-downs' tipping moment, see derive).
    upstop=dict(part="BISCO HT-870 soft silicone sponge 1.59 ring OD 4.4 / ID 3.3, glued under each carrier guide boss [S thickness, CFD; A ring]",
                kind="foam", t=1.59, od=4.4, id=3.3, cfd25=(7.0, 26.0, 48.0),   # [S] Rogers BISCO HT-870 data sheet (1.59 min)
                area_k=1.3,   # [A] the Ø3.8 head presses the ring's inner annulus; the foam round it adds about 30 % (shear)
                # stack between the stem top (bezel at rest) and the head's bearing face vs the carrier boss underside, ± each [A]:
                tol=dict(switch=0.10,      # [A] SKRHADE010 stem top above its seat (Alps drawing tolerance not in hand)
                         switch_seat=0.05, # [A] SMT solder under the switch
                         cradle=0.20,      # [S] SLA: top-board shoulder to the lower ball seats (tol_sla)
                         carrier=0.25,     # [S] MJF: upper ball cup to the guide boss underside (tol_mjf)
                         bezel=0.25,       # [S] MJF: cup ceiling to the guide-insert seat (tol_mjf)
                         insert=0.05,      # [A] heat-set insert flush with the boss
                         sleeve=0.05)),    # [A] brass tube cut to length
    # comparison of compliant up-stops (Danny 13:21): kind, free thickness, ring / O-ring size, 25 % CFD (lo, typ, hi) kPa or Shore A
    upstop_options=(
        dict(name="solid silicone O-ring 3 × 1.0, 40 Shore A", kind="oring", t=1.0, id=3.0, shore=40, c_max=0.30,
             src="[A] metric O-ring; force from Lindley's rubber-cylinder law with E from Shore A (Gent)"),
        dict(name="closed-cell silicone sponge BISCO HT-800, 0.79", kind="foam", t=0.79, cfd25=(41.0, 67.0, 97.0), c_max=0.50,
             src="[S] Rogers HT-800 data sheet: 0.79 min, 25 % CFD 6–14 psi (typ 9.7); compression set 19–30 % at 100 °C"),
        dict(name="soft silicone sponge BISCO HT-870, 1.59", kind="foam", t=1.59, cfd25=(7.0, 26.0, 48.0), c_max=0.50,
             src="[S] Rogers HT-870 data sheet: 1.59 min, 25 % CFD 1–7 psi (typ 3.8); set < 10 %"),
        dict(name="extra-soft silicone foam BISCO BF-1000, 1.59", kind="foam", t=1.59, cfd25=(7.0, 16.5, 35.0), c_max=0.50,
             src="[S] Rogers BF-1000: 1.59 min, 25 % CFD typ 16.5 kPa (range read as 1–5 psi); set < 5 %"),
        dict(name="PORON 4701-30 (25 pcf), 0.79", kind="foam", t=0.79, cfd25=(35.0, 62.0, 83.0), c_max=0.50,
             src="[S] Rogers PORON 4701-30: 0.79–1.14 at 25 pcf, 25 % CFD 5–12 psi (typ 9); set ≤ 10 % at 70 °C"),
        dict(name="PORON 4701-30 (20 pcf), 1.57", kind="foam", t=1.57, cfd25=(21.0, 35.0, 55.0), c_max=0.50,
             src="[S] Rogers PORON 4701-30: 1.57–3.18 at 20 pcf, 25 % CFD 3–8 psi (typ 5)"),
    ),
    foam_n=1.5,             # [A] foam stress ~ (strain / 25 %)^n between 5 and 60 % (data sheets give the 25 % point only)
    push_frac=1 / 3,        # [A] "well under the switch's minimum push": the stack preload stays under this fraction of it
    # [Ed 13:46/14:08] sockets under the top board: male 1.27 pins on the vertical boards' top edges plug in; the boards' end tabs bear on
    # the top board beside the sockets (the boards are the posts)
    tb_sock=dict(part="1.27 mm single-row female socket, 3.4 tall, SMT, 13 way (part to pick) [A]; height of the XFCN PM127V-11-xxP-H34 "
                      "class [S]", pitch=1.27, n=13, w=2.0, h=3.4, pad_hw=1.45, len_extra=0.40,
                 ins=(1.83, 3.00)),   # [S] Samtec FLE (a 1.27 socket) gives 1.83 min insertion; [A] max 0.4 short of the 3.4 body
    top_joint="sockets",    # [Ed 13:46] "sockets": pins into sockets, the boards are the posts [Ed 14:08]; "contacts" = v0.7 spring contacts
    vb_plane_x=16.0,        # [Ed 09:47] mirror of electronics vb.x: the vertical boards' planes (the posts)
    vb_pin_x=17.5,          # [A] mirror of electronics: the male pin row (outer face ±16.5 + the right-angle header's 1.0 offset)
    # [Ed 14:03] gasket = a dispensed (form-in-place) silicone bead all round the flange and in the top-edge step
    bead=dict(part="form-in-place silicone bead, dispensed on the cradle flange and in the top-edge step [A]",
              w0=0.70,      # [A] dispensed width: +0.1 dispense tolerance still sits on the 0.99 flange top beside the lip
              h0=0.60,      # [S] height: Henkel CIPG guideline aspect 0.6–0.9 (0.86 here)
              c_nom=0.30,   # [A] nominal compression (middle of the band)
              c_lo=0.15, c_hi=0.45,   # [S] Henkel CIPG guideline: 15 % minimum for sealing, 45 % maximum (strain limit)
              disp=0.10,    # [S] Henkel: dispensing tolerance ±0.1 on width and height
              f_mm=0.28),   # [A] N per mm of bead at the nominal 30 %: Parker CHO-FORM ~4 N/cm for a 1 mm bead [S], scaled to 0.7
    # [Ed 14:02] top-edge seal: a rebate in the cutout wall (case) and a dam on the lip ring (cradle) with the bead between them,
    # along the top edge and down the long sides to where the flange starts (water goes down, across and back up)
    step=dict(w=1.20,       # [A] rebate width past the cutout wall (the bead land on the dam is w - c)
              d=1.45,       # [A] rebate depth into the faceplate back (2.5 wall: 1.05 left above it)
              c=0.20,       # [A] dam to the rebate's back wall (one SLA tolerance)
              dam_air=0.05),   # [A] dam underside above the faceplate back (nothing behind the panel in the rail strip)
    ball_x=17.8,            # [Ed 2 Nov 12:22] balls at the extreme corners: x as far out as the carrier allows (cup boss inside it)
    ball_y_bot=10.3,        # [Ed] knob-side row; the carrier outline (±13.02) less the cup boss is the limit. The top row: rail strip
    # round female-female brass. Body is the riser. An ISO 4762 screw goes in each end.
    # Hex H3×M2×25 (STTZ2022) and the male-female 25 mm parts were out of stock on LCSC, 1 Nov 2026.
    # OD 3.2 is the usual knurled round M2 pillar; LCSC does not publish it. [A]
    standoff=dict(part="M2x30 female-female brass standoff (stock size; printed spacer if none in stock)", lcsc="TBC", length=30.0, od=3.2, kind="female-female"),  # [Ed] 2 Nov v0.5: 30 mm lifts the switch 2 mm (was 28)
    shcs=dict(part="ISO 4762 M2 A2", head_d=3.8, head_h=2.0, socket=1.5, top=6.0, bot=4.0),  # [S] DIN 912. Top through plate+board, bottom through the PCB
    pad_m2=3.2,             # [A] Ø pad on the Ø2.4 M2 clearance (annular ring 0.4)
    drill_m2=2.4,           # [A]
    # ---- plate, balls, hold-down springs (kept from v0.3) ----
    ball_d=2.0,             # [Ed]
    cup_depth_frac=0.30,    # [A] cup depth / ball diameter. Shallow: a hemisphere would be ~0.5
    cup_margin=0.20,        # [A] mm the contact stays short of the rim at full slide
    seat_clear=0.05,        # [A] unused once the cups are spherical; kept so old overrides still parse
    spr_d=2.0,              # [A]
    spr_bore=3.4,           # [A]
    spr_boss=(2.6, 0.6),    # [A] hook boss under the carrier: Ø, height
    spr_xy=(12.5, 1.5),     # [A] v0.5 hold-down springs at (±x, ±y): inside the balls, outboard of the 2x5 headers (y 1.5: room
                            # for the press-spring grub access inside the cradle ring)
    spr_f=0.90,             # [Ed 2 Nov 13:08] N each (option B; v0.4 0.5). Sized so a sideways push on the glass top that clicks the
                            # worst-case switch against the cup spring-back still has a 1.3 tipping safety
    cup_ratio_set=2.5,      # [Ed 2 Nov 13:08] option B: gentle ball cups, radius 2.5 × the ball radius (v0.4 1.4: 35° at the full
                            # slide, 1.8 N of push-back). 8.6° at the full slide; ~0.5 N spring-back to centre
    cs_xy_v05=(11.5, 5.6),  # [Ed 2 Nov 12:22] press springs inside the balls (v0.4 had them at the carrier corners). y 5.6 [Ed 13:23]:
                            # inside the cradle ring, so each grub can be reached from behind the main PCB
    grub_access=True,       # [Ed 2 Nov 13:23] access holes through the main PCB and the joystick board under each press-spring grub
    grub_access_d=1.6,      # [A] hole Ø for a 0.9 hex key (ISO 4026 M2 grub) with clearance
    tip_margin=1.3,         # [A] tipping force / worst-case switch tilt force
    spr_ext=8.0,            # [A] extension at rest, mm. Free length is installed length minus this
    pin_d=1.2,              # [A] push-in cross pin, stainless or music wire
    pin_clear=0.30,         # [A] bore diameter over the pin, so it slides while pliers hold the hook
    eye_wire=0.70,          # [A] hook wire diameter
    eye_clear=0.20,         # [A] radial gap from the pin to the hook wire
    ra_wall=1.0,            # [S] rear-anchor wall, the print minimum
    back_panel=22.65,       # [A] old back-panel depth. The springs no longer reach it
    # ---- check targets. derive() overwrites the ones that are process tolerances ----
    tgt=dict(stem_cup_min=0.20, gap_min=0.20, cable_min=0.25, spring_min=0.10,
             knob_min=0.50, board_min=0.25, mate_min=3.5, mate_max=6.5),
)


def _knob_data():
    """Read knob-param as data only (do not modify it). Live OD and the knob top set the plan and the stack.
    knob_proud is included only once the assembly interface publishes it."""
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    kp = os.path.join(here, "knob-param")
    if kp not in sys.path:
        sys.path.insert(0, kp)
    from knobparam.common import model
    D = model.derive(model.default_params())
    out = dict(knob_od=float(D["knob_od"]), z_knob_top=float(D["z_knob_top"]),
               pcb_above=float(D["pcb_above"]), pcb_w=float(D["pcb_w"]), pcb_t=float(D["pcb_t"]),
               axis_bx=float(D["axis_bx"]), axis_by=float(D["axis_by"]))
    if "knob_proud" in D:
        out["knob_proud"] = float(D["knob_proud"])
    if "z_glass" in D:   # v0.8 (knob v0.24): the dial lens top, 61.2 since the bezel cartridge (+4.4)
        out["z_glass"] = float(D["z_glass"])
    # v0.5: the case owns the panel layout. It publishes the faceplate z, the joystick place_y (rail rule), the
    # rail strip and the main-PCB nest. Read as data; the joystick keeps its own copy only as a fallback.
    for k in ("faceplate_z", "place_y", "panel_y1", "rail_clear", "pcb_y1", "pcb_x1", "y_in1", "rail_y_top",
              "rail_keep_d", "rail_x_top", "x_in1", "glow_gap", "glow_t", "collar_r", "z_fp0"):   # v0.7: the case cradle's limits
        if k in D:
            out["case_" + k] = D[k]
    return out


def _rot(x, y, deg):
    """Same Z rotation as build123d Rot(0, 0, deg): positive is CCW, y up."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (x * c - y * s, x * s + y * c)


def _land_extent(sw, deg):
    """Radius of the rotated body and its land. The circular plate opening has to clear this."""
    pts = [_rot(sx * sw["w"] / 2, sy * sw["d"] / 2, deg) for sx in (-1, 1) for sy in (-1, 1)]
    px, py = sw["pad_x"], sw["pad_y"]
    pw, ph = sw["pad"]
    tw, th = sw["tab"]
    for x, y in ((px, py), (-px, py), (px, -py), (-px, -py), (px, 0.0), (-px, 0.0)):
        for sx in (-1, 1):
            for sy in (-1, 1):
                pts.append(_rot(x + sx * pw / 2, y + sy * ph / 2, deg))
    for y in (sw["tab_y"], -sw["tab_y"]):
        for sx in (-1, 1):
            for sy in (-1, 1):
                pts.append(_rot(sx * tw / 2, y + sy * th / 2, deg))
    return max(math.hypot(x, y) for x, y in pts)


def _box_circle(x0, x1, y0, y1, x, y, r):
    """True if the box [x0,x1]x[y0,y1] and the circle (x, y, r) overlap."""
    dx = max(x0 - x, 0.0, x - x1); dy = max(y0 - y, 0.0, y - y1)
    return dx * dx + dy * dy < r * r


def _pk_depth(D, x, y, r):
    """v0.6: deepest roof pocket (below the glass back) over the circle (x, y, r); 0 if none."""
    return max([pk[5] for pk in D["back_pk"] if _box_circle(pk[1], pk[2], pk[3], pk[4], x, y, r)] + [0.0])


def _rect_dist(px, py, w, d, deg):
    """Plan distance from point (px, py) to a w x d rectangle centred on the origin and turned deg (build123d sense)."""
    a = math.radians(-deg); c, s_ = math.cos(a), math.sin(a)
    x, y = px * c - py * s_, px * s_ + py * c
    dx = max(abs(x) - w / 2, 0.0); dy = max(abs(y) - d / 2, 0.0)
    return math.hypot(dx, dy)


def _place_for(x, y_edge, rc):
    """place_y that puts carrier-frame point (x, y_edge) exactly on a circle of radius rc about the knob."""
    if abs(x) >= rc - 1e-9:
        return -y_edge
    return -y_edge + math.sqrt(rc * rc - x * x)


def derive(P_):
    D = dict(P_)
    K = _knob_data()
    D.update(K)
    D["knob_od_live"] = K["knob_od"]
    sw, S, cs, grub, ins = D["sw"], D["scr"], D["cs"], D["grub"], D["ins"]
    pm = D["print_min"]
    sla, mjf = D["tol_sla"], D["tol_mjf"]
    # clearances are the process tolerances. A looser v0.3 number is tightened; a tighter one is raised.
    D["scr_clear"] = sla
    D["glue"] = sla
    D["tgt"] = dict(D["tgt"])
    D["tgt"]["stem_cup_min"] = sla
    D["tgt"]["knob_min"] = 2 * mjf          # carrier and knob are both MJF
    D["tgt"]["cable_min"] = mjf
    D["tgt"]["board_min"] = mjf
    D["tgt"]["gap_min"] = sla
    D["fpc_slot_side"] = mjf
    D["hole_extra"] = mjf
    D["wall"] = pm
    D["well_wall"] = pm
    D["car_skirt"] = pm
    D["part_gap"] = pm * 0.65               # air between neighbouring parts; keeps the two courtyards apart
    # the cup clears the stem by one SLA tolerance. Slide is that plus the tilt travel, so the switch is the stop.
    D["cup_bore"] = sw["stem_d"] + 2 * sla
    D["cup_rad_clear"] = sla
    D["slide"] = D["cup_rad_clear"] + sw["tilt_travel"]
    D["slide_need"] = D["slide"]
    D["skirt_gap"] = D["slide"] + mjf       # the skirt is still clear when the switch has already stopped
    # The bezel is a 1.2 mm lip around the glass, not a tower. Springs, the carrier and the
    # switch live under it, inside the faceplate hole.
    D["cs_bore_r"] = cs["od"] / 2 + sla
    D["pilot_r"] = D["cs_bore_r"]
    D["sh_r"] = D["cs_bore_r"]
    D["lip_r"] = D["cs_bore_r"]
    D["sock_r"] = D["cs_bore_r"]
    D["cs_outer_r"] = D["cs_bore_r"]
    D["lip_t"] = D["bz_t"]
    D["sh_t"] = 0.0
    # review fix: the case face is one flat plane (no rebate), so the block floats press travel + one SLA tolerance above it
    D["press_gap"] = sla
    if D.get("cup_in_bezel"):   # v0.8 [Ed 13:09]: the bezel's cup ceiling sits on the stem (no gap); the press is the switch's own travel
        D["press_gap"] = 0.0
        D.pop("peg", None)        # no press peg, no peg insert
    D["press_travel"] = D["press_gap"] + sw["push_travel"]
    D["up_gap"] = D["press_travel"] + sla
    if D.get("cup_in_bezel"):
        D["up_gap"] = D["up_gap_set"]   # [A] block, screen and case stay where v0.7 had them
    D["snap"] = D["fp_overlap"]
    D["peg_d"] = 1.80
    D["half_w"] = S["w"] / 2 + D["bz_lip"]
    D["half_h"] = S["h"] / 2 + D["bz_lip"]
    D["h_mid"] = D["half_h"]
    D["x_notch"] = D["half_w"]
    D["hole_hw"] = D["half_w"] - D["fp_overlap"]
    D["hole_hh"] = D["half_h"] - D["fp_overlap"]
    D["car_hw"] = D["hole_hw"] - D["slide"] - sla
    D["car_hh"] = D["hole_hh"] - D["slide"] - sla
    if D["base"] == "case":
        # v0.7 [Ed 11:03]: the cradle's lip shares the cutout with the carrier. The cutout cannot grow (the grip block's 0.9 cover over
        # it would go: a 1.2 growth leaves −0.3 at rest), so the carrier narrows by lip clearance + lip wall and keeps the same
        # tol_sla to the lip's inner face at the full slide that it had to the cutout.
        cc = D["cc"]
        D["lip_out_hw"], D["lip_out_hh"] = D["hole_hw"] - cc["lip_c"], D["hole_hh"] - cc["lip_c"]
        D["lip_in_hw"], D["lip_in_hh"] = D["lip_out_hw"] - cc["lip_t"], D["lip_out_hh"] - cc["lip_t"]
        D["car_hw"] = D["lip_in_hw"] - D["slide"] - sla
        D["car_hh"] = D["lip_in_hh"] - D["slide"] - sla
        D["car_narrow"] = cc["lip_c"] + cc["lip_t"]
    D["cs_x"] = D["car_hw"] - cs["od"] / 2 - sla
    D["cs_y"] = D["car_hh"] - cs["od"] / 2 - sla
    D["car"] = (2 * D["half_w"], 2 * D["half_h"])
    D["pocket"] = (S["w"] + 2 * D["glue"], S["h"] + 2 * D["glue"])
    D["cs_xy"] = [(sx, sy) for sx in (D["cs_x"], -D["cs_x"]) for sy in (D["cs_y"], -D["cs_y"])]
    # The stock body is the riser. Everything above it — stem slack, carrier, faceplate, bezel —
    # stacks on that length. knob_proud is then the gap from the faceplate front up to the knob top,
    # which is what the knob and the case adopt. A longer riser lifts the faceplate, so proud falls.
    so, hd, sk = D["standoff"], D["hdr"], D["sock"]
    D["knob_proud_live"] = "knob_proud" in K
    D["knob_proud_in"] = D["knob_proud"]
    D["z_db0"] = D["cradle"]["h"] if D["base"] == "cradle" else so["length"]   # v0.5: the cradle height is the riser
    if D["base"] == "case":   # v0.7: the top board sits where the v0.6 daughterboard was
        D["z_db0"] = D["tb_z0"]
    D["z_db1"] = D["z_db0"] + D["db_t"]
    D["z_sw1"] = D["z_db1"] + sw["h"]
    D["z_stem_top"] = D["z_db1"] + sw["stem_top"]
    D["z_pivot"] = D["z_db1"] + sw["pivot"]
    D["z_ref"] = D["z_db1"] + sw["ref_h"]
    D["car_floor"] = pm
    D["z_c0"] = D["z_stem_top"] + D["stem_below"]
    D["z_floor1"] = D["z_c0"] + D["car_floor"]
    # v0.5: the faceplate z is the knob's (interface faceplate_z, via the case). The 30 mm riser lifts the carrier
    # into the faceplate hole; v0.4 derived the faceplate from the stack (carrier floor + one SLA tolerance).
    if "case_faceplate_z" in K:
        D["z_fp1"] = float(K["case_faceplate_z"])
        D["z_fp0"] = D["z_fp1"] - D["fp_t"]
    else:
        D["z_fp0"] = D["z_floor1"] + sla
        D["z_fp1"] = D["z_fp0"] + D["fp_t"]
    D["z_bz0"] = D["z_fp1"] + D["up_gap"]
    # grip block: walls from just above the faceplate to the rim; glass on a roof plate, standing glass_proud above the rim
    D["z_bz1"] = D["z_bz0"] + D["grip_h"]
    D["scr_top"] = D["z_bz1"] + D["glass_proud"]
    D["z_scr0"] = D["scr_top"] - S["t"]
    # v0.6: the FMST02's back sits in pockets in the roof (plan margin back_side; floor back_clear under each feature, or the foam pad
    # under the back sheet). The roof is thick enough that the deepest pocket keeps print_min; under the connector it is windowed.
    win = set(D.get("scr_window", ()))
    D["back_pk"] = [(n, x0 - D["back_side"], x1 + D["back_side"], y0 - D["back_side"], y1 + D["back_side"],
                     d + (D["foam_t"] if n == "back sheet" else D["back_clear"])) for n, x0, x1, y0, y1, d in D.get("scr_back", ())]
    D["back_deep"] = max([pk[5] for pk in D["back_pk"] if pk[0] not in win] + [0.0])
    D["roof_t_in"] = D["roof_t"]
    D["roof_t"] = max(D["roof_t"], D["back_deep"] + pm)
    D["z_roof"] = D["z_scr0"] - D["roof_t"]          # roof plate underside: the press springs and the guide bosses hang from it
    D["scr_drop"] = D["z_knob_top"] - D["scr_top"]
    D["fp_rebate"] = D["tol_sla"] + 0.15 + 0.20   # filled in after press_travel exists; placeholder
    D["knob_proud"] = D["z_knob_top"] - D["z_fp1"]
    # v0.8: the knob's own lens top when knob-param publishes it (61.2 since the bezel cartridge); else the v0.18 rule
    D["z_glass"] = float(K["z_glass"]) if "z_glass" in K else D["z_knob_top"] + 4.3   # [A] v0.18: 56.8 = shell top 52.5 + 4.3
    D["riser_h"] = D["z_db0"]
    D["riser_catalog"] = D["cradle"]["h"] if D["base"] == "cradle" else (D["tb_z0"] if D["base"] == "case" else so["length"])
    D["z_hdr_tip"] = D["z_db0"] - hd["ins"] - hd["mate"]
    D["mate_air"] = D["riser_h"] - hd["ins"] - sk["h"]
    D["mate_in"] = hd["mate"] - D["mate_air"]
    D["standoff_d"] = so["od"]
    sc = D["shcs"]
    D["screw_d_model"] = 1.70            # slip in the Ø2.4 hole. The real thread engages the pillar
    D["z_head_bot1"] = -D["pcb_t"] - 0.01
    D["z_head_bot0"] = D["z_head_bot1"] - sc["head_h"]
    D["engage_bot"] = sc["bot"] - D["pcb_t"]
    D["plate_t"] = pm
    D["z_plate0"] = D["z_db1"]
    D["z_plate1"] = D["z_plate0"] + D["plate_t"]
    D["z_head_top0"] = D["z_plate1"] + 0.01
    D["z_head_top1"] = D["z_head_top0"] + D["shcs"]["head_h"]
    D["engage_top"] = D["shcs"]["top"] - D["plate_t"] - D["db_t"]
    D["z_ball"] = D["z_c0"] - D["ball_d"] / 2
    D["boss_h"] = D["z_ball"] - D["z_plate1"]
    D["seat_r"] = D["ball_d"] / 2 + D["seat_clear"]
    D["boss_r"] = D["seat_r"] + pm * 0.50
    D["z_cup0"] = D["z_stem_top"] - D["cup_engage"]
    # v0.8: the cup is a column hanging from the bezel roof through a hole in the carrier floor; bore over the stem, ceiling on it
    D["cup_col_od"] = D["cup_bore"] + 2 * pm                       # print-minimum wall round the SLA-clearance bore
    D["car_cup_hole"] = D["cup_col_od"] + 2 * mjf                  # carrier floor hole round the column (they slide together)
    D["z_skirt0"] = D["z_plate0"] - D["skirt_overlap"]
    if D["base"] == "cradle":   # no seat plate: the skirt engages the board edge only, above the cradle rim
        D["z_skirt0"] = D["z_db0"] + 0.3   # 0.3 over the cradle brackets; still 0.7 of the board edge to stop rotation
    D["stack_h"] = D["scr_top"]
    # press: the peg meets the stem after one SLA tolerance, then the switch travels its own 0.15 mm
    D["fp_rebate"] = D["press_travel"] + sla          # the lip can drop this far into the faceplate before it stops
    D["z_peg"] = D["z_stem_top"] + D["press_gap"]
    D["z_lip0"] = D["z_bz0"]
    D["z_lip1"] = D["z_bz1"]
    D["z_sh0"] = D["z_bz0"]
    D["z_sh1"] = D["z_bz0"]
    D["z_sock_top"] = D["z_bz0"]
    D["z_car1"] = D["z_floor1"]
    # nominal grub protrusion is the whole preload. The free spring just reaches the bezel.
    D["z_seat"] = D["z_roof"] - cs["free"]
    D["grub_protrude"] = D["cs_turns"] * grub["pitch"]
    D["z_tip"] = D["z_seat"] + D["grub_protrude"]
    D["z_ins0"] = D["z_seat"] - ins["length"]
    D["ins_hole"] = ins["hole"]
    D["ins_od_model"] = ins["od"] - 0.30     # slip in the model. The real insert is a heat-set interference
    D["ins_id_model"] = 1.70                 # under the M2 minor diameter, so the modelled screw does not clash
    D["grub_d_model"] = 1.50
    D["boss_d"] = ins["hole"] + 2 * pm
    D["hex_proud"] = grub["length"] - ins["length"] - D["grub_protrude"]
    # forces. 1 lbf/in = 0.175127 N/mm
    D["cs_rate"] = cs["rate_lb_in"] * 0.175127
    D["cs_n"] = 4
    nrate = D["cs_n"] * D["cs_rate"]
    D["cs_defl_preload"] = D["grub_protrude"]
    D["cs_defl_press"] = D["cs_defl_preload"] + D["press_travel"]
    D["cs_f_preload"] = nrate * D["cs_defl_preload"]
    D["cs_f_press"] = nrate * D["cs_defl_press"]
    D["cs_f_turn"] = nrate * grub["pitch"]
    D["cs_f_turn_1"] = D["cs_rate"] * grub["pitch"]
    D["scr_weight"] = S["mass_g"] * 9.81e-3
    D["cs_solid_room"] = (cs["free"] - cs["solid"]) - D["cs_defl_press"]
    lo = sw["push_f"] - sw["f_tol"]
    hi = sw["push_f"] + sw["f_tol"]
    D["push_lo"] = lo
    D["push_hi"] = hi

    def _turns_at(force):
        return (force / nrate - D["press_travel"]) / grub["pitch"]

    # useful window: press force inside the centre-push band, preload above 5x the screen weight,
    # and preload still under the bottom of that band so rest is not already a click
    D["turns_lo"] = max(_turns_at(lo), 5 * D["scr_weight"] / D["cs_f_turn"])
    D["turns_hi"] = min(_turns_at(hi), lo / D["cs_f_turn"])
    D["turns_hex"] = (grub["length"] - ins["length"] - 0.40) / grub["pitch"]
    D["press_f"] = D["cs_f_press"]
    # where the carrier sits. The knob sees the notched middle, not the tall corners
    design_od = max(D["knob_od_design"], D["knob_od_live"])
    D["knob_od_used"] = design_od
    rc = design_od / 2 + D["tgt"]["knob_min"] + D["knob_extra"] + D["slide"]
    D["knob_rc"] = rc
    silhouette = [(0.0, -D["half_h"]), (D["half_w"], -D["half_h"])]
    D["place_y_knob"] = max(_place_for(x, y, rc) for x, y in silhouette)   # v0.4 rule: as close to the knob as allowed
    if D["place_rule"] == "rail":
        miss = [k for k in ("case_place_y", "case_panel_y1", "case_rail_clear", "case_pcb_y1", "case_faceplate_z") if k not in K]
        if miss:   # review fix: no silent fallback to the v0.4 rule
            raise RuntimeError(f"joystick place_rule='rail' needs the case values {miss} from knob-param")
        D["place_y"] = float(K["case_place_y"])     # v0.5: the case's rail rule (joystick as high as the rail screws allow)
    else:
        D["place_y"] = D["place_y_knob"]
    D["finger_gap"] = D["place_y"] - D["half_h"] - design_od / 2   # knob glass to the bezel, plan, at rest
    # main-PCB top edge and the rail strip, local to the joystick axis
    D["y_pcb"] = (K["case_pcb_y1"] if "case_pcb_y1" in K else D["pcb_above"]) - D["place_y"]
    D["y_rail"] = ((K["case_panel_y1"] - K["case_rail_clear"]) - D["place_y"]) if "case_panel_y1" in K else 99.0
    D["rail_margin"] = 0.4   # [A] air kept between a part behind the panel and the 10 mm rail-strip line (itself conservative)
    # switch on the carrier axis. Land extent drives the plate opening and the board
    D["sw_xy"] = (0.0, 0.0)
    D["sw_ext"] = _land_extent(sw, D["sw_rot"])
    D["body_r"] = math.hypot(sw["w"], sw["d"]) / 2
    D["cut_r"] = D["sw_ext"] + D["part_gap"]
    n, pitch = hd["n"], D["pitch"]
    D["hdr_len"] = n * pitch
    D["hdr_wid"] = hd.get("rows", 1) * pitch
    D["hx"] = D["sw_ext"] + D["part_gap"] + D["hdr_len"] / 2
    if hd.get("axis") == "y":   # v0.5 2x5: pin rows along y; the inner pin pads clear the switch land
        rows = hd.get("rows", 1)
        D["hdr_len"], D["hdr_wid"] = rows * pitch, n * pitch          # x, y extents of the plastic body
        D["hx"] = D["sw_ext"] + 0.3 + 0.85 + (rows - 1) / 2 * pitch
        D["hdr_pins"] = [((r - (rows - 1) / 2) * pitch, (k - (n - 1) / 2) * pitch) for r in range(rows) for k in range(n)]
    else:
        D["hdr_pins"] = [((k - (n - 1) / 2) * pitch, (r - (hd.get("rows", 1) - 1) / 2) * pitch)
                         for r in range(hd.get("rows", 1)) for k in range(n)]
    inset = D["pad_m2"] / 2 + D["cu_edge"]
    D["db_half_w"] = D["hx"] + D["hdr_len"] / 2 + D["standoff_d"] / 2 + D["part_gap"]
    D["db_half_h"] = D["cut_r"] + pm
    if D["base"] == "cradle":
        # v0.5: the cradle ring keeps clear of the hold-down bores and the sockets; the board sits on its rim
        C = D["cradle"]
        D["cr_in_x"] = D["spr_xy"][0] + D["spr_bore"] / 2 + 0.3
        D["cr_in_y"] = max(D["hdr_wid"] / 2 + 0.3, D["spr_xy"][1] + D["spr_bore"] / 2 + 0.3, D["sw_ext"] + 0.3)
        D["cr_out_x"] = D["cr_in_x"] + C["wall"]
        D["cr_out_y1"] = D["cr_in_y"] + C["wall_top"]     # top side: the main-PCB edge is close
        D["cr_out_y0"] = -(D["cr_in_y"] + C["wall"])
        D["db_half_w"] = D["cr_in_x"] + C["land"]
        D["db_half_h"] = D["cr_in_y"] + C["wall_top"] / 2
    # no round stop: the board is symmetric. The v0.3 -y tab existed only for that stop
    D["board_x0"], D["board_x1"] = -D["db_half_w"], D["db_half_w"]
    D["board_y0"], D["board_y1"] = -D["db_half_h"], D["db_half_h"]
    if D["base"] == "case":
        # v0.7 top board: wide enough for the spring-contact pads on both vertical boards, and as long as the boards (local y)
        D["tb_hw"] = D["vb_contact_x"] + D["tb_pad"] / 2 + D["cu_edge"] + D["tb_tol"]
        if D.get("top_joint") == "sockets":   # v0.8: wide enough for the sockets' pads on the underside (pin row ± pad half-width)
            D["tb_hw"] = D["vb_pin_x"] + D["tb_sock"]["pad_hw"] + D["cu_edge"]
        D["vb_y"] = (D["vb_y_panel"][0] - D["place_y"], D["vb_y_panel"][1] - D["place_y"])
        D["db_half_w"] = D["tb_hw"]
        D["board_x0"], D["board_x1"] = -D["tb_hw"], D["tb_hw"]
        D["board_y0"], D["board_y1"] = D["vb_y"][0] - D["tb_y_over"], D["vb_y"][1] + D["tb_y_over"]
        D["db_half_h"] = max(-D["board_y0"], D["board_y1"])
    D["db"] = (D["board_x1"] - D["board_x0"], D["board_y1"] - D["board_y0"], D["db_t"])
    D["db_xy"] = (0.0, (D["board_y0"] + D["board_y1"]) / 2)
    D["sx"] = D["db_half_w"] - inset
    sy_corner = D["db_half_h"] - inset
    sy_pad = D["y_pcb"] - D["pcb_edge"] - D["pad_m2"] / 2
    # the nut is wider than the pad, so it sets how close the screw can sit to the PCB edge
    sy_head = D["y_pcb"] - D["pcb_edge"] - D["shcs"]["head_d"] / 2
    # v0.5: the 2x3 header bodies are 5.08 wide, so the standoffs sit just outside them in y
    D["sy_need"] = D["hdr_wid"] / 2 + D["part_gap"] + D["standoff_d"] / 2
    D["sy"] = max(D["sy_need"], 0.0) if hd.get("rows", 1) > 1 else min(sy_corner, sy_pad, sy_head)
    D["sy_corner"] = sy_corner
    D["sy_pad"] = sy_pad
    D["sy_head"] = sy_head
    D["standoff_xy"] = [] if D["base"] in ("cradle", "case") else [(sx, sy) for sx in (D["sx"], -D["sx"]) for sy in (D["sy"], -D["sy"])]
    D["hdr_xy"] = [] if D["base"] == "case" else [(D["hx"], 0.0), (-D["hx"], 0.0)]   # v0.7: no 2x5 headers / H11 sockets
    # shallow spherical cups, same above and below. The ratio is the smallest cup radius
    # that still keeps cup_margin at the full slide. A ratio near 1.05 only allows ~0.15 mm.
    Rb = D["ball_d"] / 2.0
    cd = D["cup_depth_frac"] * D["ball_d"]
    s_need = D["slide"] + D["cup_margin"]

    def _smax(Rc):
        a2 = 2.0 * Rc * cd - cd * cd
        if Rc <= Rb or a2 <= 0.0:
            return 0.0
        return 2.0 * (Rc - Rb) * math.sqrt(a2) / Rc

    lo, hi = Rb * 1.02, Rb * 4.0
    for _ in range(48):
        mid = 0.5 * (lo + hi)
        if _smax(mid) < s_need:
            lo = mid
        else:
            hi = mid
    if D.get("cup_ratio_set"):   # review option B: gentler cups (larger radius, same depth)
        hi = max(hi, D["cup_ratio_set"] * Rb)
    D["cup_r"] = hi
    D["cup_ratio"] = hi / Rb
    D["cup_depth"] = cd
    D["cup_rim_r"] = math.sqrt(max(2.0 * hi * cd - cd * cd, 0.0))
    D["cup_s_max"] = _smax(hi)
    D["cup_travel_margin"] = D["cup_s_max"] - D["slide"]
    D["z_ball"] = D["z_c0"] - Rb
    D["z_rim_lo"] = D["z_ball"] - (Rb - cd)
    D["z_rim_hi"] = D["z_ball"] + (Rb - cd)
    D["z_sc_lo"] = D["z_rim_lo"] + (hi - cd)
    D["z_sc_hi"] = D["z_rim_hi"] - (hi - cd)
    D["boss_r"] = D["cup_rim_r"] + pm
    D["boss_h"] = D["z_rim_lo"] - D["z_plate1"]
    D["by"] = D["db_half_h"] - D["boss_r"] - D["part_gap"]
    if D["base"] == "cradle":   # v0.5 [Ed]: balls at the extreme corners. Top row: as high as the rail strip allows
        D["by_top"] = D["y_rail"] - D["rail_margin"] - D["boss_r"]
        D["by_bot"] = D["ball_y_bot"]
        D["by"] = D["by_top"]
    if D["base"] == "case":   # v0.7: same [Ed] rule (extreme corners, as far out as the carrier allows), on the narrower carrier
        D["by_top"] = min(D["y_rail"] - D["rail_margin"] - D["boss_r"], D["car_hh"] - D["boss_r"])
        D["by_bot"] = D["car_hh"] - D["boss_r"]
        D["by"] = D["by_top"]
    need = D["cut_r"] + D["boss_r"] + D["part_gap"]
    bx_min = math.sqrt(max(need ** 2 - D["by"] ** 2, 0.0))
    bx_max = D["sx"] - D["standoff_d"] / 2 - D["part_gap"] - D["boss_r"]
    D["bx"] = bx_max          # as far toward the plate corners as the standoffs allow
    D["balls"] = [(bx, by) for bx in (D["bx"], -D["bx"]) for by in (D["by"], -D["by"])]
    if D["base"] in ("cradle", "case"):
        D["bx"] = D["ball_x"] if D["base"] == "cradle" else D["car_hw"] - D["boss_r"]   # v0.7: the carrier corner less the cup boss
        D["balls"] = [(bx, by) for bx in (D["bx"], -D["bx"]) for by in (D["by_top"], -D["by_bot"])]
        D["by_bot_s"] = -D["by_bot"]
        D["cr_pins"] = [(D["bx"], -D["by_bot"]), (-D["bx"], -D["by_bot"])] if D["base"] == "cradle" else []   # v0.7: no dowels
    else:
        D["by_top"] = D["by_bot"] = D["by"]
    # hold-downs stay inboard of the FPC drop and under the bezel. The old pair at x=±22.5
    # stood outside the lip; that is the yellow tube Ed circled.
    D["spr_x_raw"] = D["car_hw"] - D["spr_boss"][0] / 2 - sla
    D["spr_x"], D["spr_y"] = D["spr_xy"]   # v0.5: clear of the 2x3 header bodies (y ±2.54) and the ball cups
    D["springs"] = [(sx, sy) for sx in (D["spr_x"], -D["spr_x"]) for sy in (D["spr_y"], -D["spr_y"])]
    edge = S["w"] / 2
    skirt_outer = D["db_half_w"] + D["skirt_gap"] + D["car_skirt"]
    D["fpc_x"] = max(edge - D["fpc_bend"], skirt_outer + D["tgt"]["cable_min"] + D["fpc_t"] / 2 + sla)
    if D["fpc_to_db"]:
        # v0.5: the socket sits on a tab of the daughterboard past the +x standoffs, outside the seat plate. Its long side
        # runs along y (the flex width), so the flex drops straight onto it. The carrier skirt is notched over the tab.
        sl_, ss_, sz_ = D["db_fpc_sock"]
        D["db_sock_x"] = D["sx"] + D["standoff_d"] / 2 + D["part_gap"] + ss_ / 2
        if D["base"] in ("cradle", "case"):   # beyond the +x hold-down bores (v0.7: same place, now inside the top board)
            D["db_sock_x"] = D["spr_xy"][0] + D["spr_bore"] / 2 + 0.3 + ss_ / 2
        D["tab_x1"] = D["db_sock_x"] + ss_ / 2 + D["cu_edge"]
        D["tab_hy"] = sl_ / 2 + D["cu_edge"]
        D["fpc_x"] = D["db_sock_x"]
        D["fpc_bend"] = edge - D["fpc_x"]
    D["slot_x"] = (D["fpc_x"] - D["fpc_slot_l"] / 2, D["fpc_x"] + D["fpc_slot_l"] / 2)
    D["slot_hy"] = D["fpc_w"] / 2 + D["fpc_slot_side"]
    if D["back_pk"] and D["fpc_to_db"]:
        # v0.6 [Ed 16:22] jumper: a B2B socket on the panel's header (same part as the daughterboard socket), the flex on a stiffener
        # behind it, a run under the roof to the drop at fpc_x, and a plug into the daughterboard socket. The roof is windowed
        # round the socket; a step of roof under the connector plate (where there is no jumper) carries the +x guide boss.
        sl_, ss_, sz_ = D["db_fpc_sock"]
        stw, stt = D["jmp_stiff"]
        plate = next(b for b in D["scr_back"] if b[0] == "connector plate")
        D["jmp_x"] = D["hdr_x"]
        D["z_js1"] = D["z_scr0"] - plate[5] - 0.05                  # socket top, just under the connector plate
        D["z_js0"] = D["z_scr0"] - plate[5] - sz_                   # socket base = jumper flex top face (mated height from the plate)
        D["z_jst0"] = D["z_js0"] - D["jmp_t"] - stt                  # stiffener underside
        D["jmp_hw"] = max(ss_, stw) / 2                              # half width (x) of socket + stiffener
        D["win_x"] = (D["jmp_x"] - D["jmp_hw"] - mjf, D["jmp_x"] + D["jmp_hw"] + mjf)
        D["win_hy"] = sl_ / 2 + mjf
        ppk = next(pk for pk in D["back_pk"] if pk[0] == "connector plate")
        D["plate_pk"] = ppk
        D["z_plate_floor"] = D["z_scr0"] - ppk[5]
        D["step_x"] = (ppk[1], D["win_x"][0])
        D["step_hy"] = ppk[4]
        D["z_step"] = D["z_plate_floor"] - D["step_t"]
        D["z_run"] = D["z_roof"] - D["tgt"]["cable_min"] - D["jmp_t"]   # flex run under the roof, one MJF tolerance below it
        # carrier slot: passes the jumper's bottom plug (stiffener stw x sl_) on assembly, and keeps clear of the hold-down hook boss
        x0 = max(D["fpc_x"] - stw / 2 - mjf, D["spr_xy"][0] + D["spr_boss"][0] / 2 + 1.0)
        D["slot_x"] = (x0, x0 + stw + 2 * mjf)
        D["slot_hy"] = sl_ / 2 + mjf
        D["slot_cut"] = 0.0                                          # v0.6: the carrier cut is the slot itself
        # [Ed 17:16] the loop: legs just over the plug; free lengths, and the copper strain each direction puts on the legs that
        # face it (legs in series share the movement by compliance, L^3; fixed-guided ends: curvature 6δ/L²)
        cm, b, w = D["tgt"]["cable_min"], D["jmp_bend"], D["fpc_w"]
        D["z_leg"] = (D["z_db1"] + sz_ + 0.3 + cm, D["z_db1"] + sz_ + 0.3 + cm + w)
        xe = D["jmp_x"] + stw / 2
        L = dict(R=D["jmp_xv"] - xe - b, V1=D["z_run"] - D["z_leg"][1] - 2 * b, S1=(w / 2 - D["jmp_y2"]) - 2 * b,
                 S2=D["jmp_xv"] - D["jmp_xa"] - 2 * b, S3=D["jmp_xb"] - D["jmp_xa"] - 2 * b)
        D["jmp_L"] = L
        c = D["jmp_cu_c"]
        def _eps(legs, d):
            k = sum(L[g] ** 3 for g in legs)
            return max(6 * (d * L[g] ** 3 / k) / L[g] ** 2 * c for g in legs)
        D["jmp_eps"] = dict(x=_eps(("V1", "S1"), D["slide"]), y=_eps(("S2", "S3"), D["slide"]), z=_eps(("R",), D["press_travel"]))
        D["jmp_len"] = sum(L.values()) + 7 * b + (D["z_leg"][0] - D["z_db1"] - sz_)
    D["hole_x0"] = D["slot_x"][0] - D["slide"] - D["hole_extra"]
    D["hole_x1"] = D["slot_x"][1] + D["slide"] + D["hole_extra"]
    D["hole_hy"] = D["slot_hy"] + D["slide"] + D["hole_extra"]
    D["spr_z1"] = D["z_c0"] - D["spr_boss"][1]
    # lower hooks end just behind the PCB. Two pins run along X, one per Y pair.
    pr = D["pin_d"] / 2.0
    wr = D["eye_wire"] / 2.0
    major = pr + D["eye_clear"] + wr
    D["eye_major"] = major
    D["eye_minor"] = wr
    D["eye_ro"] = major + wr
    D["pin_bore"] = D["pin_d"] + D["pin_clear"]
    D["z_pin"] = -D["pcb_t"] - 0.02 - D["ra_wall"] - major
    D["spr_len"] = D["spr_z1"] - D["z_pin"]
    D["spr_len_was"] = D["spr_z1"] + D["pcb_t"] + D["back_panel"]
    D["spr_free"] = D["spr_len"] - D["spr_ext"]
    D["spr_rate"] = D["spr_f"] / D["spr_ext"]
    wall = D["ra_wall"]
    D["ra_x0"] = -D["spr_x"] - major - wall
    D["ra_x1"] = D["spr_x"] + major + 1.2   # v0.5: mouth extension 1.2 (was 2.0); the pin heads clear the cover's corner columns
    D["ra_y0"] = -D["spr_y"] - D["eye_ro"] - wall
    D["ra_y1"] = D["spr_y"] + D["eye_ro"] + wall
    D["ra_z1"] = -D["pcb_t"] - 0.02
    D["ra_z0"] = D["z_pin"] - D["eye_ro"] - wall
    D["pin_x0"] = D["ra_x0"] + wall + 0.3
    D["pin_x1"] = D["ra_x1"] - 0.25
    D["pin_head_d"] = D["pin_d"] * 1.8
    D["pin_head_t"] = 0.8
    D["pin_y"] = (D["spr_y"], -D["spr_y"])
    D["ra_slot"] = D["spr_d"] + 1.2
    D["ra_bond"] = (D["ra_x1"] - D["ra_x0"]) * (D["ra_y1"] - D["ra_y0"])
    # ---- v0.5 press-spring stations: inside the carrier outline (their insert bosses rise into the faceplate hole),
    # and below the rail strip if the boss still reaches behind the panel. With the guides they no longer stop the
    # bezel rocking, so they can come in from the corners.
    br_cs = D["boss_d"] / 2
    D["cs_bossr"] = br_cs
    D["cs_x"] = D["car_hw"] - br_cs - sla
    cs_y = D["car_hh"] - br_cs - sla
    if D["base"] in ("cradle", "case"):   # [Ed 2 Nov] press springs inside the corner balls (v0.7: unchanged)
        D["cs_x"], cs_y = D["cs_xy_v05"]
    if D["z_ins0"] < D["z_fp0"]:
        cs_y = min(cs_y, D["y_rail"] - D["rail_margin"] - br_cs)
    D["cs_y"] = cs_y
    D["cs_xy"] = [(sx, sy) for sx in (D["cs_x"], -D["cs_x"]) for sy in (D["cs_y"], -D["cs_y"])]
    if not D.get("press_springs", True):   # v0.8 [Ed 13:16/13:18]: no press springs, grubs or inserts
        D["cs_xy"] = []
    # skirt walls (±y only in v0.5) end this far out, short of the grubs hanging under the stations
    D["skirt_x"] = min(D["board_x1"] + D["skirt_gap"] + D["car_skirt"], D["cs_x"] - D["grub_d_model"] / 2 - 0.5)
    D["access_xy"] = list(D["cs_xy"]) if D.get("grub_access") else []   # [Ed 13:23] grub access holes (PCB + joystick board)
                                                                        # v0.8: no grubs, so cs_xy is empty and the holes go
    if D["base"] == "cradle":
        # two segments per wall: inside the grubs, and from past the grubs to short of the corner towers
        D["skirt_x_in"] = D["cs_x"] - D["grub_d_model"] / 2 - 0.5
        D["skirt_x0"] = D["cs_x"] + D["grub_d_model"] / 2 + 0.5
        D["skirt_x1"] = D["bx"] - D["boss_r"] - D["slide"] - mjf
        D["skirt_x"] = D["skirt_x1"]
        # grubs inside the skirt line (y): the walls can run full length
        D["skirt_split"] = D["cs_y"] + D["grub_d_model"] / 2 + 0.3 > D["board_y1"] + D["skirt_gap"]
    # ---- v0.5 guides: screw + brass sleeve, bezel to carrier. Head under a carrier boss = up-stop; sleeve in a reamed bore.
    G = D["guide"]; gi = G["ins"]
    gx_, gy_ = D["guide_xy"]
    D["g_xy"] = [(gx_, gy_), (-gx_, -gy_)] if gy_ else [(gx_, 0.0), (-gx_, 0.0)]
    D["g_boss_r"] = G["sleeve_od"] / 2 + G["boss_wall"]
    D["g_bore"] = G["sleeve_od"] + 2 * G["bore_fit"]
    D["g_ins_top"] = D["z_scr0"] - 0.6                    # [A] 0.6 of roof left under the glass over the insert
    if D["back_pk"]:   # v0.6: insert top flush with the deepest back pocket over either guide (brass flush with the pocket floor)
        D["g_pk"] = max(_pk_depth(D, x, y, gi["od"] / 2 + 0.3) for x, y in D["g_xy"])
        D["g_ins_top"] = D["z_scr0"] - max(D["g_pk"], 0.6)
    D["g_ins_bot"] = D["g_ins_top"] - gi["length"]
    D["g_rboss_r"] = gi["od"] / 2 + 1.0
    # head clears what is under it at full press: the switch body, the board top + solder off it.
    # v0.6: tested on the switch's real 45° outline (v0.5 used its land radius, which pushed any head inside x ±7.2 over the body)
    D["g_sw_dist"] = min(_rect_dist(x, y, sw["w"], sw["d"], D["sw_rot"]) for x, y in D["g_xy"])
    over_sw = D["g_sw_dist"] < G["head_d"] / 2 + mjf if D["back_pk"] else abs(gx_) < D["sw_ext"] + G["head_d"] / 2
    under = D["z_sw1"] if over_sw else D["z_db1"] + D["solder_h"]
    if D.get("cup_in_bezel") and not over_sw:   # v0.8 [A]: a keep-out on the top board under each head (no parts, no tails)
        under = D["z_db1"] + D["guide_keepout"]
    D["g_under"] = under
    zmin = under + D["press_travel"] + mjf + G["head_k"]
    best = None
    for L in (4.0, 5.0, 6.0, 8.0, 10.0):                   # ISO 7984 stock lengths
        z0 = max(zmin, D["g_ins_bot"] + 2.0 - L)            # at least 2 mm of thread in the insert
        if z0 + L <= D["g_ins_top"] - 0.2 + 1e-9 and z0 <= D["z_c0"] - 1.0:
            best = (L, z0)
    D["g_len"], D["g_z0"] = best if best else (6.0, zmin)
    D["g_boss0"] = D["g_z0"]                                # carrier guide boss underside (v0.7: the head sat on it, the up-stop)
    if D.get("cup_in_bezel"):
        _upstop(D, G)                                       # v0.8: the head hangs a float + cushion below the boss
    D["g_zmin"] = zmin
    D["g_tip"] = D["g_z0"] + D["g_len"]
    D["g_engage"] = D["g_tip"] - D["g_ins_bot"]
    D["g_sleeve_len"] = D["g_ins_bot"] - D["g_z0"]
    D["g_guide_len"] = D["z_floor1"] - D["g_boss0"]
    D["g_head0"] = D["g_z0"] - G["head_k"]
    D["g_gap_press"] = D["g_ins_bot"] - D["z_floor1"]       # roof boss bottom to the carrier floor top (must exceed the press)
    # ---- v0.5 tipping: a sideways push on the glass top, reacted by the stem at its tilt reference height, against
    # the hold-down springs about the far ball line. The ball rows are only 2·by apart up/down.
    tilt_max = sw["tilt_f"] + sw["f_tol"]
    D["tip_need"] = D["tip_margin"] * tilt_max
    D["tip_arm_top"] = D["scr_top"] - D["z_ref"]
    D["tip_arm_mid"] = (D["z_bz0"] + D["z_bz1"]) / 2 - D["z_ref"]
    fhd = len(D["springs"]) * D["spr_f"]
    D["tip_f_top_y"] = fhd * D["by_top"] / D["tip_arm_top"]       # push up the panel: tips about the top ball row
    D["tip_f_top_down"] = fhd * D["by_bot"] / D["tip_arm_top"]    # push toward the knob: tips about the bottom row
    D["tip_f_mid_y"] = fhd * D["by_top"] / D["tip_arm_mid"]
    D["tip_f_top_x"] = fhd * D["bx"] / D["tip_arm_top"]
    D["spr_f_need"] = D["tip_need"] * D["tip_arm_top"] / (len(D["springs"]) * min(D["by_top"], D["by_bot"]))
    # review fix: at the full slide each ball sits slide/2 off its cups, so the cups push back with F_hd·tanθ on top of the
    # switch. Moments about the far ball row (ball-centre height): the push on the glass top and the stem reaction below
    # both tip; the hold-downs (centroid on the axis) restore.
    th = math.asin(min(1.0, (D["slide"] / 2) / max(D["cup_r"] - Rb, 1e-6)))
    D["cup_angle"] = math.degrees(th)
    t_ = math.tan(th)
    D["cup_tan"] = t_
    D["f_cup"] = fhd * t_
    a_top = D["scr_top"] - D["z_ball"]; a_mid = (D["z_bz0"] + D["z_bz1"]) / 2 - D["z_ball"]; d_ref = D["z_ball"] - D["z_ref"]
    D["tip_a_top"], D["tip_a_mid"], D["tip_d_ref"] = a_top, a_mid, d_ref
    D["f_click"] = tilt_max + D["f_cup"]            # sideways push needed to click at the worst-case switch
    D["f_click_nom"] = sw["tilt_f"] + D["f_cup"]
    def _sf(lever, arm):
        return fhd * lever / ((tilt_max + D["f_cup"]) * arm + tilt_max * d_ref)
    D["sf_up"] = _sf(D["by_top"], a_top)
    D["sf_down"] = _sf(D["by_bot"], a_top)
    D["sf_x"] = _sf(D["bx"], a_top)
    D["sf_up_mid"] = _sf(D["by_top"], a_mid)
    n_ = len(D["springs"]); m_ = D["tip_margin"]; lev = min(D["by_top"], D["by_bot"])
    den = lev - m_ * t_ * a_top
    D["spr_f_need"] = (m_ * tilt_max * (a_top + d_ref) / den / n_) if den > 0 else float("inf")
    # ---- review fix: the press peg is an M2 grub in a roof insert at the centre, set to the press gap with a feeler
    if "peg" in D:   # v0.8: no peg (the bezel's cup ceiling sits on the stem)
        _peg(D)
    D["preload_max"] = 0.0
    if D.get("cup_in_bezel"):   # v0.8: any preload on the stem comes straight off the hold-downs' restoring moment (the stem pushes up
        # at the axis, where the hold-downs pull down): sf(F) = sf(0)·(fhd − F)/fhd. The largest preload that keeps every row >= tip_margin
        sf0 = min(D["sf_up"], D["sf_down"], D["sf_x"], D["sf_up_mid"])
        D["preload_max"] = max(fhd * (1 - D["tip_margin"] / sf0), 0.0)
        D["preload_lim"] = min(D["preload_max"], D["push_frac"] * D["push_lo"])
        _upstop_options(D)
    D["board_xy"] = (D["axis_bx"], D["axis_by"] - D["place_y"])
    D["skirt"] = D["base"] != "case"   # v0.7: no skirt; the lip ring round the carrier is the anti-rotation stop
    if D["base"] == "case":
        _case_cradle(D, K)
    return D


def _peg(D):
    """v0.5–v0.7 press peg: an M2 grub in a roof insert at the centre, set to the press gap with a feeler."""
    pg = D["peg"]; pi = pg["ins"]
    D["p_ins_top"] = D["z_scr0"] - 0.6
    if D["back_pk"]:   # v0.6: under the deepest back pocket at the centre; the highest stock-grub height with >= 0.3 both ways
        lim = D["z_scr0"] - _pk_depth(D, 0.0, 0.0, pi["od"] / 2 + 0.3)
        tops = [D["z_peg"] + L + 0.6 for L in (3.0, 4.0, 5.0, 6.0, 8.0, 10.0) if D["z_peg"] + L + 0.6 <= lim + 1e-9]
        D["p_ins_top"] = max(tops) if tops else lim
        D["p_lim"] = lim
    D["p_ins_bot"] = D["p_ins_top"] - pi["length"]
    D["p_rboss_r"] = pi["od"] / 2 + 1.0
    lo_, hi_ = D["p_ins_bot"] + 2.0, D["p_ins_top"] - 0.2
    D["p_len"] = next((L for L in (3.0, 4.0, 5.0, 6.0, 8.0, 10.0) if lo_ <= D["z_peg"] + L <= hi_), 6.0)
    D["p_top"] = D["z_peg"] + D["p_len"]
    D["p_engage"] = D["p_top"] - D["p_ins_bot"]
    D["p_adjust"] = (D["p_top"] - lo_, hi_ - D["p_top"])   # how far the grub can be set down / up and keep 2 mm of thread


def _rss(d):
    return math.sqrt(sum(v * v for v in d.values()))


def _upstop(D, G):
    """v0.8 [Ed 13:09]: the bezel rests on the stem; the guide heads hang below the carrier guide bosses with a float. A cushion ring under
    each boss quiets the stop. The gap is sized so the cushion just reaches the head at the RSS-tight end of the stack (no preload on the
    stem anywhere in the RSS band), with an ISO 7984 stock length keeping >= 2 mm in the insert and the tip 0.2 under its top."""
    U = D["upstop"]
    D["us_rss"] = _rss(U["tol"]); D["us_wc"] = sum(U["tol"].values())
    D["g_boss0"] = D["z_floor1"] - D["guide_boss_ratio"] * G["sleeve_od"]   # boss underside (its length / sleeve OD = ratio)
    D["us_gap"] = U["t"] + D["us_rss"]                                     # head top to boss underside, nominal
    zh = D["g_boss0"] - D["us_gap"]
    lo_, hi_ = D["g_ins_bot"] + 2.0, D["g_ins_top"] - 0.2
    Ls = [L for L in (4.0, 5.0, 6.0, 8.0, 10.0) if lo_ - 1e-9 <= zh + L <= hi_ + 1e-9]
    D["g_len"] = Ls[0] if Ls else 8.0
    D["g_z0"] = zh
    D["us_float"] = (D["us_gap"] - U["t"], D["us_gap"] - U["t"] - D["us_rss"], D["us_gap"] - U["t"] + D["us_rss"])   # nominal, RSS lo..hi
    D["us_wc_comp"] = U["t"] - (D["us_gap"] - D["us_wc"])                  # cushion squeeze at the worst-case tight end (rest)
    D["us_room"] = D["g_boss0"] - (D["g_under"] + D["press_travel"] + D["tol_mjf"] + G["head_k"])   # most gap the head can hang


def _foam_sigma(D, cfd25, eps):
    """kPa at strain eps from the 25 % CFD (power law, [A] foam_n); 0 below zero strain."""
    if eps <= 0:
        return 0.0
    return cfd25 * (eps / 0.25) ** D["foam_n"]


def _ring_area(od, id_):
    return math.pi / 4 * (od * od - id_ * id_)


def _force(D, o, comp):
    """N for TWO cushions squeezed by comp (mm) at rest. Foam: whole ring area (upper bound). O-ring: Lindley F/L = E d (1.25 e^1.5 + 50 e^6),
    E from Shore A (Gent), on the mean circumference. Returns (lo, typ, hi) for foams, (v, v, v) for the O-ring."""
    if comp <= 0:
        return (0.0, 0.0, 0.0)
    if o["kind"] == "oring":
        s = o["shore"]; E = 0.0981 * (56 + 7.62336 * s) / (0.137505 * (254 - 2.54 * s))   # MPa
        e = comp / o["t"]; fl = E * o["t"] * (1.25 * e ** 1.5 + 50 * e ** 6)
        v = 2 * fl * math.pi * (o["id"] + o["t"])
        return (v, v, v)
    U = D["upstop"]
    A = min(_ring_area(D["guide"]["head_d"], U["id"]) * U["area_k"], _ring_area(U["od"], U["id"])) * 1e-6
    e = comp / o["t"]
    return tuple(2 * _foam_sigma(D, c, e) * 1e3 * A for c in o["cfd25"])


def _upstop_options(D):
    """Comparison table (Danny 13:21): each cushion at its own gap (no preload over the RSS band), the float that leaves, whether the gap
    fits the room under the boss, the squeeze and force on the stem at the worst-case tight end, and the stop force at its c_max."""
    rows = []
    for o in D["upstop_options"]:
        gap = o["t"] + D["us_rss"]
        wc = o["t"] - (gap - D["us_wc"])
        f_wc = _force(D, o, wc)
        f_stop = _force(D, o, o["c_max"] * o["t"])
        rows.append(dict(name=o["name"], t=o["t"], gap=gap, fits=gap <= D["us_room"] + 1e-9, float_nom=D["us_rss"],
                         wc_comp=wc / o["t"], f_wc=f_wc, f_stop=f_stop, src=o["src"],
                         ok_wc=f_wc[2] <= D["preload_lim"] + 1e-9))
    D["us_table"] = rows
    me = next((r for r in rows if abs(r["t"] - D["upstop"]["t"]) < 1e-9 and "HT-870" in r["name"]), rows[-1])
    D["us_choice"] = me


def _case_cradle(D, K):
    """v0.7 [Ed 3 Nov 11:03] the case cradle, local frame (joystick axis at 0, 0; z from the main-PCB front).
    Flange behind the faceplate on a gasket (−y, +x, −x sides: the +y side is over the rail strip), a lip ring up into the cutout
    (closed across +y inside the cutout only), hangers and end walls round the top board with shoulders over its edge, and the four
    lower ball seats on brackets from the hangers."""
    cc, gk, sla = D["cc"], D["gasket"], D["tol_sla"]
    D["z_fp0_case"] = float(K.get("case_z_fp0", D["z_fp0"]))
    # gasket: compressed to comp_nom by the spring contacts (the band comp_lo..comp_hi is the sponge's working range)
    D["gk_nom"] = gk["t"] * (1 - gk["comp_nom"])
    D["gk_range"] = (gk["t"] * (1 - gk["comp_hi"]), gk["t"] * (1 - gk["comp_lo"]))
    if D.get("top_joint") == "sockets":   # v0.8 [Ed 14:03]: a form-in-place bead; the boards (posts) set its squeeze, not a force
        B = D["bead"]
        D["gk_nom"] = B["h0"] * (1 - B["c_nom"])                       # flange top to faceplate back, nominal
        D["gk_range"] = (B["h0"] * (1 - B["c_hi"]), B["h0"] * (1 - B["c_lo"]))   # gaps that keep the bead inside its 15–45 % band
        D["bead_band"] = (D["gk_range"][1] - D["gk_range"][0]) / 2                # ± of gap the bead takes (before its own tolerance)
        D["bead_band_net"] = D["bead_band"] - B["disp"]                          # less its own ±0.1 dispensed height
    D["z_fl1"] = D["z_fp0"] - D["gk_nom"]            # flange top (gasket underside)
    D["z_fl0"] = D["z_fl1"] - cc["flange_t"]          # flange underside
    D["z_lip1"] = D["z_fp1"] - cc["lip_below"]        # lip top, inside the cutout
    D["z_lipb"] = D["z_fp0"] + 0.02                   # where the lip ring is not over a flange (+y), it starts in the cutout
    D["lip_engage"] = D["z_lip1"] - D["z_fp0"]        # lip height inside the faceplate
    D["lip_corner_r"] = max(D.get("corner_r", 0.0) - cc["lip_c"], 0.2)
    # nest round the top board
    D["nest_hw"] = D["board_x1"] + cc["nest_c"]                       # hanger inner face (x)
    D["nest_y0"], D["nest_y1"] = D["board_y0"] - cc["nest_c"], D["board_y1"] + cc["nest_c"]
    D["z_nest0"] = D["z_db0"] - 0.2                                   # hangers reach just under the board's underside
    D["z_sh0"], D["z_sh1"] = D["z_db1"], D["z_db1"] + cc["shoulder"]  # shoulder over the board edge (glued, contacts push up)
    D["sh_in"] = cc["shoulder"]                                        # shoulder overlap onto the board
    if D.get("top_joint") == "sockets":   # v0.8 [Ed 13:46]: SMT sockets under the top board, centred on the boards' span (local y)
        S = D["tb_sock"]
        yc = (D["vb_y"][0] + D["vb_y"][1]) / 2
        span = (S["n"] - 1) * S["pitch"]
        D["sock_pin_y"] = [yc - span / 2 + k * S["pitch"] for k in range(S["n"])]
        D["sock_len"] = S["n"] * S["pitch"] + S["len_extra"]
        D["sock_y"] = (yc - D["sock_len"] / 2, yc + D["sock_len"] / 2)
        D["z_sock0"] = D["z_db0"] - S["h"]                                  # socket entry (bottom face)
        D["eng_nom"] = (S["ins"][0] + S["ins"][1]) / 2                      # [A] pins designed to the middle of the insertion range
    # flange plan limits from the case: side-wall glow coat (x), knob collar (−y), case top wall / rail strip (+y)
    xin = float(K.get("case_x_in1", 22.75)); gg, gt = float(K.get("case_glow_gap", 0.3)), float(K.get("case_glow_t", 0.35))
    D["fl_x1"] = xin - gg - gt - cc["glow_air"]
    D["fl_y0"] = (float(K.get("case_collar_r", 23.7)) + cc["collar_air"]) - D["place_y"]
    y_top_wall = float(K["case_y_in1"]) - D["place_y"] if "case_y_in1" in K else 99.0
    D["fl_y1"] = min(y_top_wall - cc["top_air"], D["y_rail"] - D["rail_margin"])
    # the hangers and the +y end wall are inside the case's joystick cut (|x| < hole_hw), so only the flange (out to fl_x1) has to
    # stop short of the case top wall; the end wall only has to stay under the rail strip (rail check)
    # gasket land under the faceplate: ±x sides from the cutout edge to the flange edge, −y side from the cutout edge to the flange edge
    D["gk_land_x"] = D["fl_x1"] - D["hole_hw"]
    D["gk_land_y"] = -D["hole_hh"] - D["fl_y0"]
    D["gk_land_min"] = min(D["gk_land_x"], D["gk_land_y"])
    # lower ball seats: bosses from just above the top board's top face up to the lower cup rim, bracketed to the hangers
    D["z_seat0"] = D["z_db1"] + cc["seat_above"]
    D["seat_gap_press"] = D["z_rim_hi"] - D["z_rim_lo"]               # carrier cup boss over the seat boss (carrier does not move in z)
    # the grip block over the lip and the cutout
    D["block_cover_rest"] = D["half_w"] - D["hole_hw"]                 # = fp_overlap
    D["block_cover_slide"] = D["block_cover_rest"] - D["slide"]
    D["block_lip_press"] = D["z_bz0"] - D["press_travel"] - D["z_lip1"]
    # top board flex at a worst-case click: simply supported on the contact lines (±vb_contact_x), whole board width [A]
    E, t, b = 18000.0, D["db_t"], D["board_y1"] - D["board_y0"]   # [A] FR4 flexural modulus 18 GPa
    L = 2 * D["vb_contact_x"]; I = b * t ** 3 / 12.0
    D["tb_flex"] = D["push_hi"] * L ** 3 / (48 * E * I)
    if D.get("top_joint") == "sockets":   # v0.8: on the posts (board planes ±16), glued along both edges under the shoulders [A]
        D["tb_span"] = 2 * D["vb_plane_x"]
        D["tb_flex"] = D["push_hi"] * D["tb_span"] ** 3 / (48 * E * I)
        _top_step(D, K)


def _top_step(D, K):
    """v0.8 [Ed 14:02] top-edge seal: a rebate in the faceplate back round the cutout (top edge + the long sides down to the flange's end,
    fl_y1) and a dam on the lip ring inside it; the bead sits on the dam's front face under the rebate ceiling (same squeeze as the
    flange bead: the posts push the cradle up into both). Local frame."""
    st = D["step"]
    D["st_y0"] = D["fl_y1"]                                   # the step runs from here up the long sides and across the top
    D["reb_hw"], D["reb_hh"] = D["hole_hw"] + st["w"], D["hole_hh"] + st["w"]
    D["z_reb1"] = D["z_fp0"] + st["d"]                        # rebate ceiling (faces the back)
    D["z_dam1"] = D["z_reb1"] - D["gk_nom"]                   # dam front face: same bead gap as the flange
    D["z_dam0"] = D["z_fp0"] + st["dam_air"]
    D["dam_hw"], D["dam_hh"] = D["reb_hw"] - st["c"], D["reb_hh"] - st["c"]
    D["dam_t"] = D["z_dam1"] - D["z_dam0"]
    D["fp_over_reb"] = D["z_fp1"] - D["z_reb1"]              # faceplate left over the rebate
    D["step_land"] = st["w"] - st["c"]                       # bead land on the dam under the ceiling (cutout wall to dam edge)
    D["reb_corner_r"] = D.get("corner_r", 0.0) + st["w"]


def board_xy(D, x, y):
    """Carrier-frame point → main-PCB coordinates (origin = panel top-left, y down)."""
    return (D["axis_bx"] + x, D["axis_by"] - D["place_y"] - y)
