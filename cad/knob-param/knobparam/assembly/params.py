"""Assembly-agent own params (not geometry of any sub-assembly): output version, cross-check inputs, report densities."""
P = dict(
    # ---- 1220 motor [M] ----
    tab_solder=0.1,   # [A] solder fillet past the motor tab tip on the PCB back
    # ---- v0.15: screen turns with the dial ----
    version="v0.47",   # output -> assemblies/knob-stack-<version>/  (panel size is owned by the case sub since v0.19)
                       # v0.47 [Ed 6 Nov 11:27 Q23 = A]: a second board under the jack power board (the parts need 839 mm² of footprint, it had
                       #   603 free); both flex connectors move to its underside
                       # v0.46 [A, no decision]: the 2x6 stacks turned back to pins along y (their feet clear the plug holes by 0.4)
                       # v0.45 [Ed 5 Nov 20:46 Q20 = A]: a Ø3.6 hole through the jack board under each jack for a plug's tip
                       # v0.44 [A, no decision]: the outer two jack-board tongues 0.5 wider on their inner side (the sleeve's ground could
                       # not be routed out past the ring slot's pad); the bottom ledge notch follows
                       # v0.43 [Ed 5 Nov 17:59 Q18 = A]: a 2.7 x 0.55 bump on the jack board's top edge round each tip slot
                       # v0.42 [Ed 5 Nov 17:48 Q17 = A]: middle jacks out to x ±5.8, the D+/D- spring contacts in to x ±4.0; [A] the 2x6
                       # board-to-board stacks move between the jacks (x ±11.15, rotated)
                       # v0.41 [Ed 5 Nov 17:36 Q16 = A]: the jack board's tab ±5.85 down to y -53.90 (its lower contact pads met its edge);
                       # the key's top stepped down 0.25 along the tab's path
                       # v0.40 (5 Nov, no decision): the USB-C board laid out in KiCad; the key's pockets round its TVS and ESD grow from
                       # 0.1 to 0.2 so they also clear the ESD's land pattern (its pads reach 0.125 past the part)
                       # v0.39 [Ed 5 Nov 15:42 Q14 = B, 15:53 Q15 = A]: the real PJ366ST: body off-centre on its bushing (-4.5..+6.0), pins
                       # T/R/S at their published positions (slots on the jack board cover them all), sleeve pins down, a jack-board tongue to
                       # each sleeve pin, the bottom ledge notched round the tongues, jacks at 11.0 pitch (x ±5.5, ±16.5)
                       # v0.38 [Ed 5 Nov 15:34 Q12 = A]: the real vertical USB-C footprint: socket and USB-C board 0.25 up, board 6.0 tall,
                       # the 8 contacts laid round its shell legs and posts (Harwin P70-5100045), jacks 0.25 up; [C] contact gap (Q13)
                       # v0.37 [Ed 5 Nov 11:17 Q4, 11:24 Q5]: USB data on the same socket; the PD sink chip moves to the jack power board;
                       # 8 spring contacts (15 V x2, GND x2, D+, D-, CC1, CC2) Ø0.7 in two rows; the USB-C board keeps the socket, a TVS and
                       # an ESD chip, in pockets in the printed key
                       # v0.36 [Ed 4 Nov 22:52] step 2, decision 6, option A: the right post moves in to x 8; the link flex gets the lane
                       # x 9.5-18.5 (signals only); the posts carry 15 V and GND (soldered both ends); jack holes Ø6.6 for the float;
                       # the two flexes are drawn
                       # v0.35 [Ed 4 Nov 22:36] step 2, decision 5, option A: the USB-C board's 15 V and GND reach the jack unit through 4
                       # spring contacts on a tab of the jack board, landing on its back face as the stack goes home; the key's ledge tab goes
                       # v0.34 [Ed 4 Nov 22:21] step 2, decision 4, option 1A: the jack unit rides in with the board stack on two Ø2 posts
                       # in the main board's strip under the clear OLED (power board ears over them); both flexes plugged on the bench;
                       # the clear OLED's ZIF is the real ER-CON24HT-1 (17.65 x 4.5 x 2.0), centred on its flex
                       # v0.33 [Ed 4 Nov 21:30] step 2, decision 3, option B: the jack board on the jacks' backs and the jack power board
                       # 5 below it on two headers (both ZIFs and the power parts), one unit on the jack row's outline
                       # v0.32 [Ed 4 Nov 20:12-20:15] step 2, decisions 1-2: jacks 4.95 lower, USB-C 4.35 lower (board 5.5, edge on the
                       # bottom face); side PCB ledges notched along the jack row, bottom corner screws 1.0 lower and their posts cut flat
                       # under the jacks; the USB-C board in a channel through the bottom wall, a printed key behind it held by the cover
                       # v0.31 [Ed 4 Nov 16:35] dial item 6: the centring springs lifted above the detent block: two extension springs at
                       # z 10.5 from a pin on a column on the Hall arm's rib (the lever goes) to two posts printed up from the cradle plate.
                       # The hard stop stays in the Hall slot (v0.30); v0.30's post-2 hanger goes
                       # v0.30 [Ed 4 Nov 15:46] dial item 6, option A: the hard stop in the Hall slot (two stop faces the Hall bar meets
                       # at ±travel; the r 7 stop blocks gone), anchor post 2 + its pin on an arm from the detent block (the lever and the
                       # two extension springs stay). Option B (compression springs, cc_on) is in the model, switched off
                       # v0.29 [Ed 4 Nov 12:37]: the screen's plug fully mated with the cartridge's ribs seated (was 0.10 short)
                       # v0.28 [Ed 4 Nov 12:12]: cartridge seat ribs kept; their slots 0.50 a side (was 0.25), every slot's inner
                       # face 0.3 inside its rib (was 0.1)
                       # v0.27 [Ed 4 Nov 11:46]: cartridge magnets: six Ø1 x 0.5 pairs at 0/30/120/150/240/270 (were three
                       # Ø1 x 0.8), 0.30 bore gap kept; skirt skin 1.00
                       # v0.26 [Ed 4 Nov 10:03]: the joystick cutout starts 1.40 behind the faceplate (top wall and top posts back;
                       # the top ledge only at its ends: the top board passes up from the back over ±18.15)
                       # v0.25 [Ed 3 Nov evening]: review decisions: spur gears + hub m0.75 12/17 nylon in a split clear cap,
                       # cradle printed into the case, dial split, detent block, cartridge sideways magnets + key
                       # v0.24 [Ed 3 Nov]: dial bezel cartridge (+4.4, job 1) + joystick v0.8 step-1 follow-ups (job 2)
                       # v0.23 [Ed 3 Nov]: layout v4 step 1 (H7B0 on the front under the joystick, vertical boards, case cradle)
    # ---- [Ed 3 Nov] layout v4 step 1: cross-check inputs for the vertical boards' spring contacts under the joystick top board ----
    # v0.24 [Ed 14:08]: the boards are the posts, so this stack (main board -> faceplate back) goes into the form-in-place bead
    # v0.25 [Ed 18:35]: the cradle is printed into the case, so the PCB ledge to the top-board shoulders is ONE SLA dimension (the
    # faceplate and cradle terms of v0.24 merge: "loses the cradle-to-faceplate term"); the pins take this stack (decision (c))
    vb_stack_tol=dict(vb_seat=0.15,      # [A] ± vertical board seated on the main board (header solder + seating)
                      vb_height=0.10,    # [A] ± vertical board: bottom edge to the tabs' top edges (routed outline)
                      case=0.20,         # [A] ± case (SLA, one print): main-board ledge to the printed top-board shoulders
                      top_board=0.10),   # [A] ± top board thickness (1.0 FR4), glued up under the shoulders
    # v0.24 [Ed 13:46] pins into sockets: engagement (vertical-axis) and lateral alignment budgets [A]
    vb_pin_tol=dict(header_z=0.10,       # [A] right-angle header placed on the vertical board (z, from its bottom edge)
                    socket_h=0.10),      # [A] socket body height (v0.25: the tab_edge term went: the tabs no longer hold the top board)
    vb_pin_margin=0.30,      # [A] engagement kept inside the socket's insertion range at each end
    vb_tab_margin=0.30,      # [A] v0.25: end tabs (and the male header body under the socket) clear of the top board / socket at the worst case
    path_min=0.30,           # [A] v0.25: parts going in from the back (top board, vertical boards' headers) clear the case by this
    topwall_air=0.30,        # [A] 4 Nov [Ed 10:03]: the restored case top wall's top clears the lowest joystick part over it by this
    # v0.25 [Ed 18:35]: no separate cradle (its 0.2 lip float and its lip-to-nest term are gone); the top board floats in its printed
    # nest (0.2 a side) while its glue is wet [A], so the pins centre it as the board stack goes in, then the glue sets
    vb_lat_tol=dict(main_board=0.20,     # [A] ± main board in the case (y; x)
                    case=0.20,           # [A] ± case (SLA, one print): PCB nest / corner posts to the printed top-board nest
                    socket=0.05,         # [A] ± socket placed on the top board
                    pins=0.10),          # [A] ± male pins on the vertical board (placement and the board's lean)
    vb_capture=dict(lead_in=0.25,        # [A] socket entry funnel over the 0.4 pin (radial capture)
                    board_float=0.20),   # [A] v0.25: the top board in its nest (0.2 a side) while the glue is still wet (v0.24: the cradle's lip float)
    vb_buckle_margin=3.0,    # [A] Euler load / post load, each board
    knob_hole_clear=0.4,   # [A] faceplate hole radius over the knob radius
    faceplate_z_v023=38.8,   # [Ed 3 Nov 12:41] faceplate front in v0.23: only the knob grows (+4.4), so it must stay here (check row)
    rho=dict(glass=2.5e-3, pol=1.2e-3, tape=1.0e-3, petg=1.27e-3, ndfeb=7.5e-3, steel=7.85e-3, fpc_g=0.35),   # [A] g/mm3; FPC+B2B mass g
)
