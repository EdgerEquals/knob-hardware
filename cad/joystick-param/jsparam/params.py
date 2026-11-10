"""Top-screen joystick stack v0.9 — params + derive.

v0.9 (3 Nov 2026 evening, Ed 18:35 / 19:12): the cradle is printed into the case (one UTR-8100 print with the faceplate: lip ring,
hangers, end walls, the four lower ball seats on their brackets, the top-board shoulders). No bead, no top-edge step, no gap between
cradle and case. The pins take the stack (decision (c)): the vertical boards' end tabs clear the top board; taller (4.5) sockets. The top
board goes in from the back on its own, up under the printed shoulders, glued [A]; small top-corner notches let it pass the top corner
posts' bases. The pin rows move 0.3 inboard [Ed 19:12 (4)] and 2.5 toward the knob [A] so the sockets and the male headers pass the posts.

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

The stack now (v0.9): the switch is on the carrier axis, on the top board. The top board hangs in the cradle printed into the case
(glued up under its shoulders); the vertical boards' male pins slide in the two 1.27 sockets under it. Four Ø2 balls between the
carrier and the cradle's lower seats carry the carrier, and four hold-down extension springs from a rear anchor behind the main PCB
keep it on them. The screen is glued on the roof of the grip block (the bezel); the cup over the stem is printed into the bezel and
sits on the stem, so the switch's own end of travel is the only stop for tilt and for the centre press. Two guide screws in brass
sleeves tie the bezel to the carrier; their heads hang a float below the carrier's guide bosses, on a cushion ring (the up-stop).
The screen flex reaches the top board through the custom jumper (v0.6). The parts the history above mentions and the stack no longer
has (standoffs, seat plate, glued cradle, 2x5 headers and H11 sockets, press springs, grubs, inserts, press peg, spring contacts,
the v0.7 gasket, the PCB slot for the flex) are in git history only (up to commit 3238bb9).
"""
import math
import os
import sys

P = dict(
    version="v0.9",
    # ---- placement. place_y is derived so the notched edge clears the knob ----
    knob_od_design=41.70,   # [Ed] size the plan to the v0.17 knob. The live knob-param OD is checked too
    knob_extra=0.0,         # nominal gap is the process stack itself (v0.4 rule only)
    place_rule="rail",      # [Ed] 2 Nov v0.5: "rail" = as high as the top rail screw keep-out allows (the case owns the rule
                            # and publishes place_y); "knob" = v0.4, as close to the knob as the process stack allows
    finger_min=5.0,         # [Ed] 2 Nov: plan gap from the knob glass to the bezel at rest, at least this (finger room)
    pcb_edge=0.30,          # [A] a PTH pad stays this far inside the main-PCB copper edge
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
                            # goes into the roof, not into bending the panel
    step_t=1.0,             # [A] roof step under the connector plate (no jumper there), carries the +x guide boss
    scr_below_knob=5.0,     # [Ed] old screen target. knob_proud now places the faceplate; the screen follows the bezel
    knob_proud=16.45,       # [Ed] adopted value. derive() recomputes it from the 25 mm riser; 16–20 is the accepted window
    knob_proud_window=(16.0, 22.4),   # [Ed] faceplate to the knob glass: 16–20 (v0.18); knob +4.4 accepted [Ed 3 Nov 12:28/12:41] -> 22.4
    print_min=1.0,          # [S] PCBWay SLS nylon minimum wall (SLA resin is 0.8). Structural walls use this
    # FPC: v0.6 the custom jumper [Ed 16:22]. Width / thickness [A] until it is drawn.
    fpc_w=3.0,              # [Ed 17:13] no touch: 13 lines (QSPI CLK, CS, D0-D3, RESET, TE, PWR_EN, 3V3, three GND) at 0.2 pitch [A]
    fpc_t=0.12,             # [A]
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
    jmp_y2=-4.0, jmp_y3=-3.2,   # [A] planes of S2 and S3 (clear of the hold-down spring at y -1.5; v0.6 also cleared the grub key
                                # line at y -5.6, gone since v0.8)
    jmp_xa=9.0, jmp_xb=14.0,    # [A] S2 runs from jmp_xv to jmp_xa; S3 back from jmp_xa to jmp_xb, then down onto the plug
    # ---- carrier / bezel ----
    car_top_below=0.3,      # [A] glass stands this far proud of the bezel top
    bz_lip=1.2,             # [Ed] bezel lip (side wall of the grip block), same as the other bezel. 1.5 mm is the maximum
    grip_h=5.0,             # [Ed] 2 Nov v0.5: the bezel is a grip block at least 5 mm tall, glass on top; the faceplate tucks in behind its edge
    glass_proud=0.6,        # [A] glass top above the block rim (as v0.4: 1.5 glass on 0.3 pads in a 1.2 bezel)
    roof_t=1.6,             # [A] roof plate under the glass: the cup column and the guide bosses hang from it, the glass is glued on
                            # top. v0.6: derive() raises it so the deepest back pocket keeps print_min of roof
    # guides (v0.5, Ed 2 Nov): two screws through brass sleeves tie the bezel to the carrier. The sleeve slides in a reamed
    # bore in the carrier; the screw head under the carrier boss is the up-stop (v0.4 had none).
    guide=dict(part="ISO 7984 M2 A2 low-head socket screw (length from derive) + brass tube sleeve OD 3.0 / ID 2.1, cut to length",
               d=2.0, sleeve_od=3.0, head_d=3.8, head_k=1.6, bore_fit=0.03, boss_wall=1.0,
               ins=dict(part="M2x3x3.2 brass heat-set (bezel roof)", od=3.2, length=3.0, hole=3.0)),   # [S] DIN 7984 M2 head Ø3.8 × 1.6 max [A]
    guide_xy=(6.5, 3.0),    # [Ed 16:31] turned pair (+6.5, +3.0) / (-6.5, -3.0): clear of the FMST02 header window (v0.5: (±8.5, 0))
    corner_r=1.2,           # [A] carrier floor corners = the case opening's corner radius (case hole_corner_r)
    fp_t=2.5,               # [A] faceplate of the one-piece case. UTR-8100 clear resin, wall ~2.5 mm
    fp_overlap=0.90,        # [A] how far the lip covers the faceplate at rest, before the slide
    # ---- cup (printed into the bezel, v0.8). The bore is derived: stem diameter plus one SLA tolerance per side ----
    cup_engage=1.2,         # [A]
    stem_below=1.10,        # [Ed] 2 Nov: carrier underside above the stem top
    # [Ed] 2 Nov: the screen flex plugs into a socket on the joystick board (top board since v0.7); no slot in the main PCB
    db_fpc_sock=(8.4, 3.0, 0.9),   # [S/A] AXE530127 30-pin 0.4 mm socket: long side (along y, the flex width), short side (x), mated height
    # ---- switch ----
    sw=dict(part="Alps SKRHADE010", w=7.45, d=7.5, h=1.85, stem_d=3.0, stem_top=5.0, pivot=0.49, ref_h=4.3,
            tilt_travel=0.25, push_travel=0.15, tilt_f=1.2, push_f=2.35, f_tol=0.69,   # [S]
            pad_x=3.575, pad_y=1.425, pad=(1.35, 1.0), tab_y=4.05, tab=(2.0, 1.8)),    # [S] land pattern
    sw_rot=-45.0,           # [Ed] directions line up with the screen axes
    # ---- daughterboard. Outline is derived. Thickness is the fab stack, not the print minimum ----
    db_t=1.0,               # [A] 2-layer FR4
    cu_edge=0.30,           # [A] copper-to-outline, same rule as the KiCad board
    pitch=2.54,             # [S] (geom.json "pitch": the v0.4 header pitch, kept as published)
    base="case",   # [Ed 3 Nov 11:03] v0.7 layout v4: the top board on the vertical boards, nested in a cradle captured by (v0.9: printed
                   # into) the case. The only base left; the v0.4 standoffs + seat plate and the v0.5/v0.6 glued cradle are in git history
    # ---- v0.7 [Ed 3 Nov] top board on the vertical boards, case cradle ----
    tb_z0=30.0,             # [A] top board underside, kept at the v0.6 daughterboard height so the switch / carrier / bezel stack does
                            # not move. electronics vb.top_board_z must match (assembly cross-check)
    vb_y_panel=(26.5, 48.4),   # [Ed 09:47] the vertical boards' y span, panel frame (mirror of electronics vb.y; assembly cross-check)
    tb_y_over=0.40,         # [A] top board past each end of the vertical boards
    cc=dict(part="joystick case cradle, UTR-8100 clear resin (SLA), lip in the faceplate cutout, flange behind the faceplate",
            lip_c=0.20,     # [A] lip to the cutout wall, each side ("about 0.2 a side"; SLA case ±0.20 and SLA cradle ±0.20: fit-check)
            lip_t=1.0,      # [A] lip wall (SLA minimum 0.8 [S])
            lip_below=0.5,  # [A] lip top this far under the faceplate front (the grip block covers the cutout, so it is never seen)
            flange_t=1.2,   # [A] flange behind the faceplate
            wall=1.0,       # [A] hangers / end walls round the top board
            nest_c=0.20,    # [A] top board edge to the nest walls
            shoulder=1.0,   # [A] shoulder over the top board's edge (the board is glued up under it)
            seat_above=1.0, # [A] lower ball-seat bosses start this far above the top board's top face (parts under them stay lower)
            collar_air=0.5, # [A] flange −y edge to the knob collar (case collar_r)
            glow_air=0.20,  # [A] flange ±x edge to the case side-wall glow coat (the coat is modelled 0.3 off the wall, 0.35 thick)
            top_air=0.20),  # [A] flange +y end to the case top wall inner face (no contact: the lip ring locates in y)
    # ---- v0.8 [Ed 3 Nov 13:09–14:08] step-1 follow-ups: the cup over the stem is printed into the bezel (grip block) and its ceiling
    # sits on the stem (no gap), so the switch's own click is the press [Ed 13:09]; no press springs, grubs, inserts or press peg
    # [Ed 13:16/13:18] ----
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
                         seats=0.20,       # [S] SLA: top-board shoulder to the lower ball seats (tol_sla). v0.9: both are printed in the
                                           # case now; it is still one SLA dimension inside one print, so the term stays (v0.8 "cradle")
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
    # ---- v0.9 [Ed 18:35 / 19:12] the cradle printed into the case ----
    cradle_in_case=True,    # [Ed 18:35] one UTR-8100 print with the faceplate: the lip ring is the cutout wall thickened below the front
                            # (the 0.2 lip slot is filled; its inner face stays, so the carrier and the balls do not move), the flange sits
                            # on the faceplate back (no gasket gap), no bead, no top-edge step. False = v0.8 (separate cradle on a bead)
    tb_sock9=dict(part="1.27 mm single-row female socket, 4.5 tall, SMT, 13 way [A] (part to pick; 1.27 single-row sockets 4.3 / 4.6 tall "
                       "exist: XFCN PM127V-11-xx-H43 / -H46, LCSC C2917342 / C2689177, through-hole [S]; SMT 1.27 single-row socket strips: "
                       "Mill-Max 853 series, 1-50 ways, pins Ø0.38-0.53, pads alternate sides [S], height to confirm [C])",
                  pitch=1.27, n=13, w=2.0, h=4.5, pad_hw=1.45, len_extra=0.40,
                  ins=(1.83, 4.10)),   # [Ed 19:12 (7)] ~4.5 tall; insertion [S] 1.83 min (Samtec FLE class), [A] max 0.4 short of the body
    vb_pin_x9=17.2,         # [Ed 19:12 (4)] the pin rows 0.3 inboard (v0.8 17.5): mirror of electronics vb_top_x (assembly cross-check)
    sock_y_shift=-2.5,      # [A, needs Danny's OK] the pin rows (sockets and the male headers) 2.5 toward the knob, so the sockets clear the
                            # top corner posts' bases by >= 0.3 on the way in from the back (mirror of electronics vb_pin.y_shift)
    notch_air=0.30,         # [A] top-board corner notch: this far round the top corner posts (case corners, Ø6.5) on the way in from the back
    glue9=dict(part="epoxy fillet, top board glued up under the printed shoulders [A]",
               peak=3.0,    # [A] peak / average line load along the glue line (peel at the shoulders' inner edge)
               peel=2.0),   # [A] N/mm: a cautious peel strength for a rigid epoxy on SLA resin / FR4 solder mask (not sourced)
    # ---- balls, hold-down springs (kept from v0.3) ----
    ball_d=2.0,             # [Ed]
    cup_depth_frac=0.30,    # [A] cup depth / ball diameter. Shallow: a hemisphere would be ~0.5
    cup_margin=0.20,        # [A] mm the contact stays short of the rim at full slide
    spr_d=2.0,              # [A]
    spr_bore=3.4,           # [A]
    spr_boss=(2.6, 0.6),    # [A] hook boss under the carrier: Ø, height
    spr_xy=(12.5, 1.5),     # [A] v0.5 hold-down springs at (±x, ±y), inside the balls. y 1.5 is left over from the v0.5-v0.7 press-spring
                            # grub-access holes (it made room for them); the holes went in v0.8 and the springs have not moved since.
                            # Whether to move them is open [C, Danny]
    spr_f=0.90,             # [Ed 2 Nov 13:08] N each (option B; v0.4 0.5). Sized so a sideways push on the glass top that clicks the
                            # worst-case switch against the cup spring-back still has a 1.3 tipping safety
    cup_ratio_set=2.5,      # [Ed 2 Nov 13:08] option B: gentle ball cups, radius 2.5 × the ball radius (v0.4 1.4: 35° at the full
                            # slide, 1.8 N of push-back). 8.6° at the full slide; ~0.5 N spring-back to centre
    tip_margin=1.3,         # [A] tipping force / worst-case switch tilt force
    spr_ext=8.0,            # [A] extension at rest, mm. Free length is installed length minus this
    pin_d=1.2,              # [A] push-in cross pin, stainless or music wire
    pin_clear=0.30,         # [A] bore diameter over the pin, so it slides while pliers hold the hook
    eye_wire=0.70,          # [A] hook wire diameter
    eye_clear=0.20,         # [A] radial gap from the pin to the hook wire
    ra_wall=1.0,            # [S] rear-anchor wall, the print minimum
    # ---- check targets. derive() overwrites the ones that are process tolerances ----
    tgt=dict(stem_cup_min=0.20, gap_min=0.20, cable_min=0.25, spring_min=0.10, knob_min=0.50),
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
              "rail_keep_d", "rail_x_top", "x_in1", "glow_gap", "glow_t", "collar_r", "z_fp0",   # v0.7: the case cradle's limits
              "corners", "screw_boss_r", "z_rim", "z_seat"):   # v0.9: the top corner posts (the top board's corner notches)
        if k in D:
            out["case_" + k] = D[k]
    return out


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
    if D.get("base") != "case":   # the v0.4 standoffs + seat plate and the v0.5/v0.6 glued cradle are in git history (up to 3238bb9)
        raise ValueError(f"joystick base={D.get('base')!r}: only 'case' is modelled")
    if not D.get("scr_back"):     # the v0.4 PCB slot and the v0.5 flex route are in git history; the v0.6 jumper needs the panel's back
        raise ValueError("joystick scr_back is empty: the screen jumper and the roof pockets are derived from it")
    K = _knob_data()
    D.update(K)
    if D.get("cradle_in_case"):   # v0.9 [Ed 18:35 / 19:12]: taller sockets, the pin rows 0.3 inboard
        D["tb_sock"] = dict(D["tb_sock9"])
        D["vb_pin_x"] = D["vb_pin_x9"]
    D["knob_od_live"] = K["knob_od"]
    sw, S = D["sw"], D["scr"]
    pm = D["print_min"]
    sla, mjf = D["tol_sla"], D["tol_mjf"]
    # clearances are the process tolerances. A looser v0.3 number is tightened; a tighter one is raised.
    D["scr_clear"] = sla
    D["glue"] = sla
    D["tgt"] = dict(D["tgt"])
    D["tgt"]["stem_cup_min"] = sla
    D["tgt"]["knob_min"] = 2 * mjf          # carrier and knob are both MJF
    D["tgt"]["cable_min"] = mjf
    D["tgt"]["gap_min"] = sla
    D["wall"] = pm
    D["well_wall"] = pm
    D["part_gap"] = pm * 0.65               # air between neighbouring parts; keeps the two courtyards apart
    # the cup clears the stem by one SLA tolerance. Slide is that plus the tilt travel, so the switch is the stop.
    D["cup_bore"] = sw["stem_d"] + 2 * sla
    D["cup_rad_clear"] = sla
    D["slide"] = D["cup_rad_clear"] + sw["tilt_travel"]
    D["slide_need"] = D["slide"]
    # v0.8 [Ed 13:09]: the bezel's cup ceiling sits on the stem (no gap); the press is the switch's own travel. The case face is one flat
    # plane (no rebate): the block floats up_gap above it
    D["press_gap"] = 0.0
    D["press_travel"] = D["press_gap"] + sw["push_travel"]
    D["up_gap"] = D["up_gap_set"]   # [A] block, screen and case stay where v0.7 had them
    D["snap"] = D["fp_overlap"]
    D["half_w"] = S["w"] / 2 + D["bz_lip"]
    D["half_h"] = S["h"] / 2 + D["bz_lip"]
    D["h_mid"] = D["half_h"]
    D["x_notch"] = D["half_w"]
    D["hole_hw"] = D["half_w"] - D["fp_overlap"]
    D["hole_hh"] = D["half_h"] - D["fp_overlap"]
    # v0.7 [Ed 11:03]: the cradle's lip shares the cutout with the carrier. The cutout cannot grow (the grip block's 0.9 cover over
    # it would go: a 1.2 growth leaves −0.3 at rest), so the carrier narrows by lip clearance + lip wall and keeps the same
    # tol_sla to the lip's inner face at the full slide that it had to the cutout.
    cc = D["cc"]
    D["lip_out_hw"], D["lip_out_hh"] = D["hole_hw"] - cc["lip_c"], D["hole_hh"] - cc["lip_c"]
    D["lip_in_hw"], D["lip_in_hh"] = D["lip_out_hw"] - cc["lip_t"], D["lip_out_hh"] - cc["lip_t"]
    D["car_hw"] = D["lip_in_hw"] - D["slide"] - sla
    D["car_hh"] = D["lip_in_hh"] - D["slide"] - sla
    D["car_narrow"] = cc["lip_c"] + cc["lip_t"]
    if D.get("cradle_in_case"):   # v0.9 [Ed 18:35]: the lip ring is printed with the cutout wall; the 0.2 slot is filled, the inner face
        D["lip_out_hw"], D["lip_out_hh"] = D["hole_hw"], D["hole_hh"]   # stays where it was (carrier, balls and tipping unchanged)
    D["car"] = (2 * D["half_w"], 2 * D["half_h"])
    D["pocket"] = (S["w"] + 2 * D["glue"], S["h"] + 2 * D["glue"])
    # The top board sits at tb_z0. Everything above it — stem slack, carrier, faceplate, bezel — stacks on that height. knob_proud is
    # then the gap from the faceplate front up to the knob top, which is what the knob and the case adopt.
    D["knob_proud_live"] = "knob_proud" in K
    D["knob_proud_in"] = D["knob_proud"]
    D["z_db0"] = D["tb_z0"]   # v0.7: the top board sits where the v0.6 daughterboard was
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
    D["z_roof"] = D["z_scr0"] - D["roof_t"]          # roof plate underside: the cup column and the guide bosses hang from it
    D["scr_drop"] = D["z_knob_top"] - D["scr_top"]
    D["fp_rebate"] = D["tol_sla"] + 0.15 + 0.20   # filled in after press_travel exists; placeholder
    D["knob_proud"] = D["z_knob_top"] - D["z_fp1"]
    # v0.8: the knob's own lens top when knob-param publishes it (61.2 since the bezel cartridge); else the v0.18 rule
    D["z_glass"] = float(K["z_glass"]) if "z_glass" in K else D["z_knob_top"] + 4.3   # [A] v0.18: 56.8 = shell top 52.5 + 4.3
    D["riser_h"] = D["z_db0"]
    D["riser_catalog"] = D["tb_z0"]
    D["z_cup0"] = D["z_stem_top"] - D["cup_engage"]
    # v0.8: the cup is a column hanging from the bezel roof through a hole in the carrier floor; bore over the stem, ceiling on it
    D["cup_col_od"] = D["cup_bore"] + 2 * pm                       # print-minimum wall round the SLA-clearance bore
    D["car_cup_hole"] = D["cup_col_od"] + 2 * mjf                  # carrier floor hole round the column (they slide together)
    D["stack_h"] = D["scr_top"]
    D["fp_rebate"] = D["press_travel"] + sla          # v0.4 faceplate proxy: the lip could drop this far into a rebate (none now)
    D["z_car1"] = D["z_floor1"]
    # the switch's centre-push band (Alps 2.35 ± 0.69 N [S])
    lo = sw["push_f"] - sw["f_tol"]
    hi = sw["push_f"] + sw["f_tol"]
    D["push_lo"] = lo
    D["push_hi"] = hi
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
    # switch on the carrier axis
    D["sw_xy"] = (0.0, 0.0)
    D["body_r"] = math.hypot(sw["w"], sw["d"]) / 2
    # v0.7 top board: as long as the vertical boards (local y); v0.8: wide enough for the sockets' pads on the underside (pin row ± pad
    # half-width). No round stop: the board is symmetric in x
    D["tb_hw"] = D["vb_pin_x"] + D["tb_sock"]["pad_hw"] + D["cu_edge"]
    D["vb_y"] = (D["vb_y_panel"][0] - D["place_y"], D["vb_y_panel"][1] - D["place_y"])
    D["db_half_w"] = D["tb_hw"]
    D["board_x0"], D["board_x1"] = -D["tb_hw"], D["tb_hw"]
    D["board_y0"], D["board_y1"] = D["vb_y"][0] - D["tb_y_over"], D["vb_y"][1] + D["tb_y_over"]
    D["db_half_h"] = max(-D["board_y0"], D["board_y1"])
    D["db"] = (D["board_x1"] - D["board_x0"], D["board_y1"] - D["board_y0"], D["db_t"])
    D["db_xy"] = (0.0, (D["board_y0"] + D["board_y1"]) / 2)
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
    # v0.7: [Ed] balls at the extreme corners, as far out as the (narrower) carrier allows: the carrier corner less the cup boss. The
    # top row also stays under the rail strip
    D["by_top"] = min(D["y_rail"] - D["rail_margin"] - D["boss_r"], D["car_hh"] - D["boss_r"])
    D["by_bot"] = D["car_hh"] - D["boss_r"]
    D["by"] = D["by_top"]
    D["bx"] = D["car_hw"] - D["boss_r"]
    D["balls"] = [(bx, by) for bx in (D["bx"], -D["bx"]) for by in (D["by_top"], -D["by_bot"])]
    # hold-downs stay inboard of the FPC drop and under the bezel. The old pair at x=±22.5
    # stood outside the lip; that is the yellow tube Ed circled.
    D["spr_x"], D["spr_y"] = D["spr_xy"]   # v0.5: inside the ball cups (y: see spr_xy)
    D["springs"] = [(sx, sy) for sx in (D["spr_x"], -D["spr_x"]) for sy in (D["spr_y"], -D["spr_y"])]
    # [Ed 2 Nov] the screen flex plugs into a socket on the top board, beyond the +x hold-down bores. Its long side runs along y (the
    # flex width), so the flex drops straight onto it. (tab_x1: v0.5 put it on a tab past the board edge; it is inside the board now)
    edge = S["w"] / 2
    sl_, ss_, sz_ = D["db_fpc_sock"]
    D["db_sock_x"] = D["spr_xy"][0] + D["spr_bore"] / 2 + 0.3 + ss_ / 2
    D["tab_x1"] = D["db_sock_x"] + ss_ / 2 + D["cu_edge"]
    D["tab_hy"] = sl_ / 2 + D["cu_edge"]
    D["fpc_x"] = D["db_sock_x"]
    D["fpc_bend"] = edge - D["fpc_x"]
    # v0.6 [Ed 16:22] jumper: a B2B socket on the panel's header (same part as the daughterboard socket), the flex on a stiffener
    # behind it, a run under the roof to the drop at fpc_x, and a plug into the daughterboard socket. The roof is windowed
    # round the socket; a step of roof under the connector plate (where there is no jumper) carries the +x guide boss.
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
    # ---- v0.5 guides: screw + brass sleeve, bezel to carrier; sleeve in a reamed bore. v0.8: the head hangs a float + cushion below
    # the carrier boss (the up-stop)
    G = D["guide"]; gi = G["ins"]
    gx_, gy_ = D["guide_xy"]
    D["g_xy"] = [(gx_, gy_), (-gx_, -gy_)] if gy_ else [(gx_, 0.0), (-gx_, 0.0)]
    D["g_boss_r"] = G["sleeve_od"] / 2 + G["boss_wall"]
    D["g_bore"] = G["sleeve_od"] + 2 * G["bore_fit"]
    # v0.6: insert top flush with the deepest back pocket over either guide (brass flush with the pocket floor); [A] at least 0.6 of
    # roof left under the glass over the insert
    D["g_pk"] = max(_pk_depth(D, x, y, gi["od"] / 2 + 0.3) for x, y in D["g_xy"])
    D["g_ins_top"] = D["z_scr0"] - max(D["g_pk"], 0.6)
    D["g_ins_bot"] = D["g_ins_top"] - gi["length"]
    D["g_rboss_r"] = gi["od"] / 2 + 1.0
    # head clears what is under it at full press: the switch body, or the top board's keep-out under each head.
    # v0.6: tested on the switch's real 45° outline (v0.5 used its land radius, which pushed any head inside x ±7.2 over the body)
    D["g_sw_dist"] = min(_rect_dist(x, y, sw["w"], sw["d"], D["sw_rot"]) for x, y in D["g_xy"])
    over_sw = D["g_sw_dist"] < G["head_d"] / 2 + mjf
    under = D["z_sw1"] if over_sw else D["z_db1"] + D["guide_keepout"]   # v0.8 [A]: a keep-out on the top board under each head
    D["g_under"] = under
    _upstop(D, G)                                           # v0.8: the head hangs a float + cushion below the boss
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
    # v0.8: any preload on the stem comes straight off the hold-downs' restoring moment (the stem pushes up at the axis, where the
    # hold-downs pull down): sf(F) = sf(0)·(fhd − F)/fhd. The largest preload that keeps every row >= tip_margin
    sf0 = min(D["sf_up"], D["sf_down"], D["sf_x"], D["sf_up_mid"])
    D["preload_max"] = max(fhd * (1 - D["tip_margin"] / sf0), 0.0)
    D["preload_lim"] = min(D["preload_max"], D["push_frac"] * D["push_lo"])
    _upstop_options(D)
    D["board_xy"] = (D["axis_bx"], D["axis_by"] - D["place_y"])
    _case_cradle(D, K)   # v0.7: no skirt; the lip ring round the carrier is the anti-rotation stop
    return D


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
    Flange behind the faceplate (−y, +x, −x sides: the +y side is over the rail strip; v0.8 on a bead, v0.9 printed with the case), a lip
    ring up into the cutout (closed across +y inside the cutout only), hangers and end walls round the top board with shoulders over its
    edge, and the four lower ball seats on brackets from the hangers."""
    cc = D["cc"]
    D["z_fp0_case"] = float(K.get("case_z_fp0", D["z_fp0"]))
    # v0.8 [Ed 14:03]: a form-in-place bead; the boards (posts) set its squeeze, not a force. The flange gap (gk_nom) still comes from it
    B = D["bead"]
    D["gk_nom"] = B["h0"] * (1 - B["c_nom"])                       # flange top to faceplate back, nominal
    D["gk_range"] = (B["h0"] * (1 - B["c_hi"]), B["h0"] * (1 - B["c_lo"]))   # gaps that keep the bead inside its 15–45 % band
    D["bead_band"] = (D["gk_range"][1] - D["gk_range"][0]) / 2                # ± of gap the bead takes (before its own tolerance)
    D["bead_band_net"] = D["bead_band"] - B["disp"]                          # less its own ±0.1 dispensed height
    if D.get("cradle_in_case"):   # v0.9 [Ed 18:35]: printed with the case. The flange keeps its v0.8 height [A] (the carrier's cup bosses keep
        D["fl_drop"] = D["gk_nom"]   # 0.62 over it inside the lip) and a riser outboard of the lip's inner face fuses it to the faceplate back
    D["z_fl1"] = D["z_fp0"] - D["gk_nom"]            # flange top (bead underside in v0.8)
    D["z_fl0"] = D["z_fl1"] - cc["flange_t"]          # flange underside
    D["z_lip1"] = D["z_fp1"] - cc["lip_below"]        # lip top, inside the cutout
    D["z_lipb"] = D["z_fp0"] + (0.0 if D.get("cradle_in_case") else 0.02)   # where the lip ring is not over a flange (+y), it starts in the cutout
    D["lip_engage"] = D["z_lip1"] - D["z_fp0"]        # lip height inside the faceplate
    D["lip_corner_r"] = max(D.get("corner_r", 0.0) - cc["lip_c"], 0.2)
    # nest round the top board
    D["nest_hw"] = D["board_x1"] + cc["nest_c"]                       # hanger inner face (x)
    D["nest_y0"], D["nest_y1"] = D["board_y0"] - cc["nest_c"], D["board_y1"] + cc["nest_c"]
    D["z_nest0"] = D["z_db0"] - 0.2                                   # hangers reach just under the board's underside
    D["z_sh0"], D["z_sh1"] = D["z_db1"], D["z_db1"] + cc["shoulder"]  # shoulder over the board edge (the board is glued up under it)
    D["sh_in"] = cc["shoulder"]                                        # shoulder overlap onto the board
    # v0.8 [Ed 13:46]: SMT sockets under the top board, centred on the boards' span (local y)
    S = D["tb_sock"]
    yc = (D["vb_y"][0] + D["vb_y"][1]) / 2
    span = (S["n"] - 1) * S["pitch"]
    if D.get("cradle_in_case"):   # v0.9 [A]: the rows move toward the knob so the sockets pass the top corner posts' bases
        yc += D["sock_y_shift"]
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
    # bead land under the faceplate: ±x sides from the cutout edge to the flange edge, −y side from the cutout edge to the flange edge
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
    # top board flex at a worst-case click, v0.8: on the posts (board planes ±16), glued along both edges under the shoulders, simply
    # supported, whole board width [A]. v0.9 (_printed9) replaces it with the plate glued under the shoulders on four edges
    E, t, b = 18000.0, D["db_t"], D["board_y1"] - D["board_y0"]   # [A] FR4 flexural modulus 18 GPa
    I = b * t ** 3 / 12.0
    D["tb_span"] = 2 * D["vb_plane_x"]
    D["tb_flex"] = D["push_hi"] * D["tb_span"] ** 3 / (48 * E * I)
    if D.get("cradle_in_case"):
        _printed9(D, K)
    else:
        _top_step(D, K)


def _printed9(D, K):
    """v0.9 [Ed 18:35 / 19:12]: the cradle is printed into the case. The pins take the stack, so the top board hangs from the printed
    shoulders by its glue line: a press goes stem -> top board -> glue -> shoulders -> case. Corner notches let the board pass the top corner
    posts' bases on its way in from the back. Local frame."""
    cc = D["cc"]
    # top-board corner notches: round each top corner post (case corners, +y pair) by notch_air, squared off up to the board's +y edge
    r = float(K.get("case_screw_boss_r", 3.25)) + D["notch_air"]
    D["tb_notch"] = [(float(x), float(y) - D["place_y"], r) for x, y in K.get("case_corners", ()) if float(y) > D["place_y"]]
    D["tb_notch_size"] = (0.0, 0.0)
    if D["tb_notch"]:
        x, y, r = D["tb_notch"][0]
        dx = abs(x) - D["board_x1"]                                   # post centre past the board edge
        x_in = abs(x) - r                                              # notch's deepest point (|x|)
        y_lo = y - (r * r - dx * dx) ** 0.5 if dx < r else D["board_y1"]
        D["tb_notch_x"] = x_in
        D["tb_notch_y0"] = y_lo
        D["tb_notch_size"] = (D["board_x1"] - x_in, D["board_y1"] - y_lo)   # depth into the board (x), length along its edge (y)
    # top board on its shoulders: a plate glued along the shoulders' inner edges (four edges, simply supported [A]); the switch at its middle
    E, t, nu = 18000.0, D["db_t"], 0.15                               # [A] FR4
    sh = D["sh_in"]
    ax = 2 * (D["board_x1"] - sh); ay = (D["board_y1"] - sh) - (D["board_y0"] + sh)
    a, b = min(ax, ay), max(ax, ay)
    tab = ((1.0, 0.01160), (1.2, 0.01353), (1.4, 0.01484), (1.6, 0.01570), (1.8, 0.01620), (2.0, 0.01651), (3.0, 0.01690), (99.0, 0.01695))
    q = b / a
    alpha = next(a0 + (a1 - a0) * (q - q0) / (q1 - q0) for (q0, a0), (q1, a1) in zip(tab, tab[1:]) if q0 <= q <= q1)   # [S] Timoshenko, SS plate, centre load
    Dp = E * t ** 3 / (12 * (1 - nu * nu))
    D["tb_plate"] = (a, b, alpha)
    D["tb_flex"] = alpha * D["push_hi"] * a * a / Dp
    D["tb_k"] = D["push_hi"] / D["tb_flex"]                            # N/mm at the switch
    # overpress: past the switch's bottom the force goes into the top board until the grip block lands on the faceplate
    D["op_gap"] = D["z_bz0"] - D["press_travel"] - D["z_fp1"]
    D["op_f"] = D["tb_k"] * D["op_gap"]
    # glue line under the shoulders: the board's four edges, less the +x shoulder notch at the screen socket and the corner notches
    hy = D["db_fpc_sock"][0] / 2 + 0.6
    y0, y1 = D["board_y0"], D["board_y1"]
    L_side = (y1 - y0)                                                  # -x side
    cut_px = [(-hy, hy)]
    if D["tb_notch"]:
        cut_px.append((D["tb_notch_y0"], y1))
    cut_px.sort(); merged = []
    for c0, c1 in cut_px:
        if merged and c0 <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], c1))
        else:
            merged.append((c0, c1))
    L_px = (y1 - y0) - sum(min(c1, y1) - max(c0, y0) for c0, c1 in merged)
    L_mx = L_side - ((y1 - D["tb_notch_y0"]) if D["tb_notch"] else 0.0)
    L_ends = 2 * (2 * D["board_x1"]) - (2 * D["tb_notch_size"][0] if D["tb_notch"] else 0.0)
    D["glue_len"] = L_px + L_mx + L_ends
    G = D["glue9"]
    D["glue_q_click"] = G["peak"] * D["push_hi"] / D["glue_len"]       # N/mm, peak, worst-case click
    D["glue_q_op"] = G["peak"] * D["op_f"] / D["glue_len"]             # N/mm, peak, at the overpress stop
    # tipping at the worst-case corner of the up-stop stack (the cushion preloads the stem; sf scales by (F_hd - F) / F_hd)
    fhd = len(D["springs"]) * D["spr_f"]
    ch = D.get("us_choice")
    if ch:
        D["sf_up_wc"] = (D["sf_up"] * (fhd - ch["f_wc"][2]) / fhd, D["sf_up"] * (fhd - ch["f_wc"][0]) / fhd)   # (worst, best) in that corner


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
