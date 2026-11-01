# Knob module v1 (phase one product), Ed 2026-10-30

Standalone MIDI + CV controller, Eurorack. Two units stacked vertically in a ~40 mm wide (8HP) module, i.e. each unit in half the 3U height. Target price at least AU$400.

Per unit:
- Big motorised dial; separate gear drives the position encoder.
- Bezel dial around it, sensed by a Hall sensor.
- Centre button with a small OLED/TFT screen inside it.
- Top screen above, on a 3D-printed carrier floating on four ball bearings over a base piece glued to the PCB (located by four pins). Four extension springs pass through PCB holes to the back panel and hold it down. A cup on the back of the carrier sits over a five-way joystick, so the whole screen tilts left/right/up/down and presses.
- Navigation: top screen menus; press down moves into the dial's menu; press up returns to top screen menu; up again escapes.
Phase one = bare minimum; iterate later as other modules come online.

## 2026-10-30 additions (Ed)
- Option B if two-up in 8HP is too tight: keep one unit and use the freed space (move the stack up or down) for an optical front panel with a TFT under it.
- Optical front panel: glass, tinted glass, or layered/stratified cast epoxy acting as an analogue optical layer, with adjustable tint/colour; phosphorescent, fluorescent or luminescent layers excited by UV LEDs built into the faceplate; a TFT can sit under the stack. Sent to reviewers for speculation.
- Displays show the ANALOGY of the parameter being changed: a capacitor, an inductor, a body, brain or heart for biological analogies, then zoom in to the parameter. Must stay coherent with the Unified Theory (cavities, Q, pumps, mixing classes product/threshold/motion/ensemble) and feed back into it. Data cascades up and down, builds up inside, meets a threshold, moves elsewhere and lets go.

## Optical panel reviewer filter (2026-10-30)
Keep: bonded laminate stack (AR glass front, laser-etched semi-transparent "analogy mask", thin optical adhesive/LOCA or silicone layer with phosphor zones, TFT/OLED bonded behind, no air gap); strontium aluminate phosphor as decay/release/Q "memory" (e.g. threshold strip that glows and fades after a crossing); fluorescent for active pumping/threshold ignition; 365 nm UV LEDs recessed and shielded; linear constant-current LED drive, no PWM; AR coating + circular polariser + dark tinted top for stage and daylight; dichroic film for colour shift with zero electronics; rotatable polariser pair as optional mechanical dimmer; electrochromic only as slow mood tint, edge-sealed; lenticular sheet using the floating screen's tilt to cross-fade states; heat path to chassis; OLED preferred for true black.
Drop/correct: thick cast epoxy for production (prototype art only; laminates for product); PDLC (scatters, AC drive); TFT backlight as the UV source (visible light only charges phosphor weakly, blue at best); RC-filtered PWM; "12 h afterglow" is dark-adapted only, visible decay is minutes; reviewer 2 mixed panel width with stack thickness.
- 2026-10-30 ACCEPTED: Knob v1 = Plan B, one unit per 8HP plus optical front panel with TFT. Two-up version later.
- 2026-10-30 ACCEPTED I/O: front USB-C MIDI (+firmware), TRS MIDI out, CV out x2 (dial, bezel), gate out (button), CV in (motor follows external voltage); rear bus+clock connector for the system later.
- 2026-10-30 ACCEPTED (Ed): Motor backbone = cheap surplus geared DC motors (N30 planetary, 1220 coreless planetary, RK-370 planetary; one of each on order for feel/backlash/quality testing). Design is motor-agnostic since surplus supply changes: standard swappable mount, slip clutch so hand always wins, encoder reads the DIAL (not the motor), boot calibration learns each motor's backlash and speed as ratios. Brushless gimbal stays as a later option. Brushed motors: filter at the motor, keep PWM above hearing and off at target.
- 2026-10-30 ACCEPTED (Ed): Motor noise is switchable, problem turned into an effect. Mode A: filtered/quiet. Mode B: "motor voice" - audio modulated onto the motor drive, recorded back via back-EMF sense and a tiny contact/close mic at the motor, including brush noise, gear grit and magnetic saturation, as an analogue texture source. Needs: bypassable motor filter (relay or analogue switch), audio-in to motor driver path, back-EMF sense amp, mic preamp input, level ceiling to protect motor and ears, and isolation so the effect path never leaks into the clean audio ground when off.
- 2026-10-30 ACCEPTED: Motor texture out shares the bezel CV jack (jack 2) when motor-voice mode is on; switched via the screen/joystick menu, jack's role shown on the screen. Only one jack ever switches role. Audio in for motor voice comes over the CV in jack.

## Hand feel and clutch (2026-10-31, Ed)
- No mechanical slip clutch. The clutch is electronic and always on: motor current sensing plus a thermal probe on the motor.
- Normal play: the motor always assists the direction the hand is moving. Encoder (on the dial) plus the small gearbox backlash lets the hand move the knob slightly first; the encoder picks it up and the motor follows. The dial's resistance/impedance is set by the motor, not by a fixed mechanical drag.
- Protection: if someone holds against an end stop (e.g. 7 o'clock) long enough that current or temperature climbs past threshold (ratio of the motor's own calibrated values), the motor goes into freewheel and the screen shows what happened.
- Bezel ring stiffness comes from the springs at the bottom; may turn out unnecessary. Planned for now, revisited once the three test motors arrive and Ed can feel the real backlash.
- Supersedes the earlier "slip clutch" line in the motor backbone section.

## Screens (2026-10-31, Ed)
- Button screen: 0.7" round TFT (not OLED) inside the centre button, with its flex cable running out the back down to the main PCB.
- Top screen (on the 3-DOF ball-bearing carriage, also the joystick/navigation): kept smaller than full 8HP width so there's finger room between it and the dial/panel edge when it tilts. Exact size set by the finger-clearance check in the panel layout.
- Lower screen: full-size TFT under the clear optical panel, using all remaining panel area.

## Panel layout v1 (2026-10-31)
Drawing: scope/knob-panel-layout/knob-panel-layout-v1.svg / .png (generator make.py). All mm, y from panel top, x from left edge; everything centred on x = 20.15 unless stated.
- Panel: Doepfer A-100 3U, 128.5 tall; 8HP actual width 40.30 (doepfer.de/a100_man/a100m_e.htm). Mount holes Ø3.2 at y 3.0 and 125.5 (122.5 c/c); top hole x 7.5, bottom hole x 32.9 (7.5 + 5 HP, assumed; oval slots OK). Rail zones 0-10 and 118.5-128.5 kept clear (PCB max ~110 tall, sdiy.info Eurorack panel components).
- Top screen: 0.85" 128x128 IPS TFT (GC9107), module 17.58 x 20.82, active 15.21 sq. Carriage 20.6 x 23.8 (y 11.3-35.1, centre 23.2); panel cut-out 22.2 x 25.4 (y 10.5-35.9) for tilt. Side gaps 9.85 each = 19.7 total (assumed fingertip need 15-18).
- Dial: centre 56.4. Hall bezel ring Ø35 (y 38.9-73.9, 2.65 to each panel edge), motor dial Ø29, button cap Ø23, 0.71" round IPS TFT (GC9D01) glass 20.1 x 22.3, active Ø18.
- Optical window: 36.3 x 15.2 (x 2.0-38.3, y 75.4-90.6). Big TFT under it: 0.96" 160x80 IPS (ST7735S) landscape, 27.95 x 13.5, active 21.7 x 10.8, centre y 83.0. About 4 mm strips each side for UV/phosphor zones.
- Jacks: Thonkiconn PJ398SM, Ø6.0 hole, Ø7.8 nut, body ~9 wide x ~10.5 tall behind panel. Columns x 8.15 / 20.15 / 32.15 (12.0 pitch), rows y 96.0 / 107.0 (11.0 pitch). Row 1: J1 TRS MIDI out, J2 CV out 1 (dial), J3 CV out 2 (bezel / motor-texture out, the one switching jack). Row 2: J4 gate out (button), J5 CV in (motor follows / motor-voice audio in), J6 SPARE.
- USB-C: centre y 115.0, cut-out 9.5 x 3.8 (y 113.1-116.9); max plug overmold 12.35 x 6.5 (USB-IF) reaches y 118.25.
- Assumptions: patch plug bodies Ø7; playable jack pitch >= 11; 3.8 gap carriage-to-bezel, 1.5 bezel-to-window.
- Conflicts / Ed to decide:
  1. Only five jacks are named in the spec; J6 drawn as spare.
  2. Big TFT gets only ~15 mm height, so 0.96" class, not 1.47" (1.47" landscape needs ~20 mm).
  3. USB-C does not fit beside the jacks at a playable pitch (would need ~10 mm pitch and nuts ~1 mm from panel edge). Placed in its own slot under the jacks; cable drops straight down. Moving it beside the jacks would free ~8 mm for a bigger TFT.
  4. Bezel Ø35 nearly fills the 40.3 width; grip is top/bottom, neighbouring modules may crowd the sides.
  5. Behind the panel: jack row 2 body ends ~113.0 and the USB-C body starts ~113.4. USB-C needs a raised or vertical receptacle so its mouth meets the panel above the jack-height PCB.

## Sixth jack (2026-10-31, Ed) — locked
J6 = dedicated motor-voice audio in. CV in (J5) is CV only (motor follows external voltage) and no longer doubles as audio in. Supersedes the earlier "Audio in for motor voice comes over the CV in jack" line. J3 (bezel CV / motor texture out) remains the only jack that switches role.

## Big TFT size (2026-10-31, Ed) — locked
v1 keeps the 0.96" 160x80 TFT (landscape) under the ~36.3 x 15.2 mm optical window. Optical layers carry the visual weight; larger knob sizes (1.5", 2") get a bigger screen. Jacks and dial are not squeezed to gain space.

## Panel layout v2 (10HP, 2026-10-31)
SUPERSEDES "Panel layout v1" above (kept for history). Ed moved the module from 8HP to 10HP to avoid crowding. Drawing: scope/knob-panel-layout/knob-panel-layout-v2.svg / .png (generator make_v2.py). All mm, y from panel top, x from left edge; centre line x = 25.25.
- Panel: Doepfer A-100 3U, 128.5 tall; 10HP actual width 50.50 (Doepfer table). Mount holes Ø3.2, 3.0 from top/bottom (122.5 c/c), x 7.5 and 43.06 (7.5 + 7 HP). Drawn as four holes; two (one top, one bottom) are enough up to 10HP per Doepfer/sdiy.info. Rail zones 0-10 and 118.5-128.5 kept clear.
- Top screen: 1.14" 240x135 IPS TFT (ST7789V), landscape, module 31.0 x 17.6, active 24.9 x 14.9. Carriage 33.6 x 20.6 (y 11.3-31.9, centre 21.6); panel cut-out 35.2 x 22.2 (y 10.5-32.7). Side gaps 8.45 each = 16.9 total.
- Dial: centre 54.4 (x 25.25). Hall bezel Ø35 (y 36.9-71.9), 7.75 clear to each panel edge; motor dial Ø29; button cap Ø23; 0.71" round IPS TFT (GC9D01), glass 20.1 x 22.3, active Ø18. Gap carriage-to-bezel 5.0.
- Optical window: 46.5 x 19.1 (x 2.0-48.5, y 74.4-93.5). Big TFT (locked for v1): 0.96" 160x80 IPS (ST7735S) landscape, 27.95 x 13.5, active 21.7 x 10.8, centre y 84.0. UV/phosphor margins about 9.3 each side and 2.8 above/below.
- Jacks: Thonkiconn PJ398SM (Ø6.0 hole, Ø7.8 nut). Columns x 6.75 / 19.75 / 32.75 (13.0 pitch), rows y 98.5 / 111.5 (13.0 pitch). Row 1: J1 TRS MIDI out, J2 CV out 1 (dial), J3 CV out 2 (bezel / motor-texture audio out, the only role-switching jack). Row 2: J4 gate out (button), J5 CV in (motor follows, CV only), J6 motor-voice audio in (dedicated).
- USB-C: now fits beside the jacks. Vertical slot 3.8 x 9.5, centre x 43.0, y 105.0 (between the rows); max plug overmold 6.5 x 12.35 (USB-IF) spans x 39.75-46.25, y 98.8-111.2. That leaves 3.5 to the J3/J6 plug bodies (Ø7 assumed) and 4.25 to the panel edge.
- Behind panel: USB-C body about x 41.4-44.6; J3/J6 bodies end x 37.25, so 4.1 clear. The v1 row-2/USB-C clash is fixed. Row 2 jack bodies end at about y 117.5, 1.0 inside the rail line.
- Remaining conflicts / Ed to decide:
  1. Top screen finger room is 16.9 total: inside the 15-18 target, not above it. Fallback is the 0.85" 128x128 (about 29 total). A 1.3" 240x240 is too tall for the vertical budget.
  2. The jack grid sits left of centre to make room for the USB-C.
  3. USB-C needs a vertical (top-mount) receptacle, rotated so the slot is upright, tall enough or on a spacer so its mouth meets the panel at jack height (about 9 mm body + 2 mm panel).
  4. Row 2 jack bodies come within about 1 mm of the bottom rail line. That's OK, but don't push the jacks lower.

## Panel layout v3 (10HP, big PCB TFT, 2026-10-31)
SUPERSEDES "Panel layout v2" and the "0.96in big TFT locked" decision (Ed overrode it: the small screen looked dinky). Drawing with front view + side section: scope/knob-panel-layout/knob-panel-layout-v3.svg / .png (generator make_v3.py). All mm; y from panel top, x from left edge, z = depth behind the panel front face.
- Unchanged from v2: 10HP panel 50.50 x 128.5, holes x 7.5 / 43.06 at y 3.0 / 125.5; top screen 1.14" 240x135 on its carriage (centre y 21.6, finger room 8.45 each side); dial centre y 54.4 (bezel Ø35, dial Ø29, button Ø23 with 0.71" round TFT).
- Lower zone y 73.9-118.5 is the clear layered optical panel (aluminium frame elsewhere).
- Big TFT: 2.0" 240x320 IPS, ST7789V (e.g. TST020QVHS-07 / FW020TFT-V22A03), datasheet outline 34.6 x 47.8 x 1.9, active 30.6 x 40.8. Mounted landscape on the main PCB: 47.8 W x 34.6 H, y 78.9-113.5 (centre 96.2), x 1.35-49.15. Active 40.8 x 30.6 = 1248 mm², about 5.3x the old 0.96". FPC on the right short edge, folded to the PCB. Rejected: 2.4" (42.72 x 59.46: too tall portrait, too wide landscape), 2.3" 320x240 (50.8 x 45.8: wider than the panel), 1.9" 170x320 (25.8 x 49.72: less area).
- Jacks (panel-mounted through the clear panel, wired/flex to the PCB): same grid as v2. Columns x 6.75 / 19.75 / 32.75, rows y 98.5 / 111.5; J1 TRS MIDI out, J2 CV out 1, J3 CV out 2 / motor-texture out (only switching jack), J4 gate out, J5 CV in, J6 motor-voice audio in. USB-C at x 43.0, y 105.0 on a small panel-mounted board (~10 x 16), wired to the PCB.
- Occlusion: each jack hides about 9 x 10.45 of screen straight on (body behind the Ø7.8 nut); the USB-C board hides about 10 x 16. Seen from 30° above, each shadow grows about 8.9 downward. Clean screen above the jacks is y 78.9-~94 (full width), plus ~4-5 wide slots between jack columns.
- Depth stack: clear laminate 0-2.5; jack body to 12.5, pins to 16.2, wires ~17.7; TFT glass 18.0-19.9; main PCB 20.2-21.8; power header + ribbon to ~36. No collision: 15.5 air gap from laminate rear to TFT glass, with ~1.8 spare behind the jack pins. Screen zone depth ~36, under the 45.5 Intellijel Palette skiff limit (37.4 at its edges). Motor/gearbox depth not yet counted.
- Thonkiconn thread is M6 x 4.5, so the clear panel must be <= 2.5 thick at the jacks (panel + ~2 nut).
- UV/phosphor: strips above (73.9-78.9) and below (113.5-118.5) the TFT, plus patterned phosphor between the jack nuts. UV LEDs edge-light the laminate from under the bezel. The laminate is no longer bonded to the TFT (air gap), so AR-coat both faces and print a black mask on the rear around the nuts.
- Remaining conflicts / Ed to decide:
  1. The 15.5 air gap gives a deep light-box look with strong parallax: shadows shift ~9 at 30°. Options: source a shorter panel jack (body <= ~6) to bring the gap to ~10; a black mask plus firmware that draws around the jack shadows; a fibre-optic faceplate (costly, not advised). A TFT can't have holes, so the jacks must stay in front.
  2. The main PCB moves back to z ~20 (v2 ~12), so the carriage base, encoder and motor mounts need standoffs about 8 taller. That does give the motor more room.
  3. USB-C can't come from the PCB at this depth, so it needs the separate panel board, wired back (keep it short; ESD protection on that board).
  4. The clear panel takes jack torque and the bottom screws: use an aluminium frame with the laminate bonded in, or a polycarbonate carrier; no acrylic at the screw holes.
  5. The TFT edge is 1.35 from each panel edge; the PCB must be >= ~48 wide.

## Layout v3 accepted (2026-10-31, Ed) — locked
2.0" 320x240 IPS TFT on the main PCB behind the clear panel (landscape, 47.8 x 34.6 mm). Jacks and USB-C mount through the clear panel in front. Fixes: source shorter panel jacks (body <=6 mm) to cut the air gap from ~15.5 to ~10 mm; printed black mask on the back of the clear panel around each jack, with firmware drawing around jack shadows. Main board moves back ~8 mm (taller standoffs for carriage, encoder, motor; more motor room). USB-C on its own small board behind the clear panel, wired back, ESD protected. Clear panel needs an aluminium frame or polycarbonate carrier (no acrylic at screw holes). UV edge-lit from under the bezel; phosphor in strips and between jacks; anti-glare both faces. Main board >=48 mm wide.

## Panel layout v4 (2 TRS + USB-C, 2026-10-31)
SUPERSEDES v3's six-jack set, the J6 "spare" entry, and the earlier jack-role entries (2026-10-30 I/O list, "Motor texture out shares the bezel CV jack (jack 2)", and the v2/v3 J1-J6 mapping). Everything else in v3 stands (10HP, upper half, 2.0" TFT on the main PCB behind the clear panel). Drawing: scope/knob-panel-layout/knob-panel-layout-v4.svg / .png (generator make_v4.py). mm; y from panel top, x from left edge, z behind the panel front face.
- I/O is now two 3.5 mm TRS (stereo) jacks plus one USB-C. TRS MIDI out is dropped: MIDI goes over USB-C now, and over the rear bus later.
  - J1 (outputs only): TIP = CV out 1 (dial). RING = CV out 2 (bezel), or motor-texture audio OUT when motor-voice mode is on (MENU-SWITCHED).
  - J2 (mixed): TIP = CV in (motor follows), or motor-voice audio IN (MENU-SWITCHED). RING = gate out (button).
  - The menu-switched roles are J1 ring and J2 tip only; the screen shows the current role. Use standard TRS-to-2xTS splitter cables.
- Jack part: stereo Thonkiconn WQP419GR (old name PJ366ST). M6x0.5 thread 4.5, Ø6.0 panel hole, Ø7.8 nut, body 10 incl. tab, ~1 wider than the mono (~10), same footprint, pins ~3.7.
  - No verified short-body (<= 6) stereo panel jack found: Kycon STPX-3501-3C-1 body is 9.0; Switchcraft 35FM3 is 35.5 long. With the jacks below the picture the body length no longer matters.
- Positions: one row at y 112.3: J1 x 8.5, J2 x 21.5 (13.0 pitch), USB-C x 38.0 (horizontal, cut-out 9.5 x 3.8, max overmold 12.35 x 6.5, on a ~16 x 9 panel board). Clear panel zone y 72.9-118.5.
- TFT is PCB-MOUNTED, NOT BONDED to the clear panel (Ed, 2026-10-31): it stays assembled on the main PCB behind the clear panel with the 15.5 air gap, as in v3. Moved up: outline y 72.0-106.6, with its 2 mm inactive top border tucked behind the aluminium edge (clear zone starts y 72.9). Active y 74.0-104.6 (40.8 x 30.6 = 1248 mm²). Jack bodies clear the TFT outline by 1.25 in y; this extra ~1 mm costs nothing. Check that the TFT top edge (y 72.0, z 18) clears the dial motor/gear space.
  - Straight on, 100% of the active area is unobstructed (jack bodies start y 107.85, USB board y 107.8), and cables hang down away from it. Seen from 30° above: no shadow.
  - Seen from 30° below (desk use), shadows climb ~8.9 into three bands, hiding ~16% of the active area.
- Depth: clear laminate <= 2.5 (thread 4.5 minus ~2 nut). Jack body to 12.5, pins to 16.2. TFT glass 18.0-19.9, PCB 20.2-21.8, power header + ribbon to ~36, power block <= 8 behind the PCB. Total ~36, under the 45.5 skiff limit.
  - No bonding option: the TFT stays on the PCB and the air gap stays (Ed's correction).
- Power (Ed 2026-10-31: standalone desk use from front USB-C):
  - Dual input: Eurorack bus or USB-C PD. Negotiate 9-15 V; plain 5 V/3 A (15 W) is marginal for motor surges.
  - Ideal-diode OR-ing / power mux, with priority to the bus when racked.
  - ±12 V for CV in/out on USB only: buck/boost to +12, an inverting buck-boost or 1-2 W isolated dual-output DC-DC for -12, then LDOs. Size impact about 20 x 15 mm of PCB rear, <= 8 tall (fits the existing depth).
  - USB ground isolation: USB data isolator, common-mode choke on VBUS/GND, star ground so USB noise stays out of the audio path. Fully isolated PD power would need a ~25 x 25 x 10 converter (Ed to decide).
  - USB-C socket and its panel board rated >= 3 A for PD; VBUS/GND wiring back to the main board >= 24 AWG or doubled; CC lines to a PD sink (STM32G4 UCPD or a dedicated sink chip).
- Conflicts / Ed to decide:
  1. J2 mixes an input (tip) and an output (ring) on one jack. Gate edges can couple into CV in through the shared sleeve and cable. Slew-limit the gate, keep returns separate, 1k series on outputs.
  2. A mono TS plug in either jack shorts the ring to ground (CV out 2 or the gate), so ring outputs must be short-proof (1k + clamp).
  3. The module depends on splitter cables, and the tip/ring pinout is ours, not a Eurorack standard; print it on the panel/screen.
  4. Without TRS MIDI out, hardware synths need a USB host until the rear bus exists.
  5. The power options above (isolation level, PD voltage) need a decision before the PCB layout.

## Panel layout v5 (2026-10-31)
SUPERSEDES v4's jack set and jack roles (the v4 power notes still stand). Drawing: scope/knob-panel-layout/knob-panel-layout-v5.svg / .png (generator make_v5.py). mm; y from panel top, x from left edge.
- The 2.0" TFT is PCB-MOUNTED on the main PCB, NOT bonded to the clear panel; the 15.5 air gap and the v4 depth stack are kept.
- NO JACK SWITCHES ROLE NOW (the menu-switched roles from v4 are gone).
- Top screen: the carriage cut-out top moved from y 10.5 to 10.0, the rail-zone line, so only 0.5 is gained. Carriage now y 10.8-31.4, centre 21.1.
  - Option (not chosen): the carriage could overhang the panel front up to y ~7.0 (+3.8) between the top screws. Screw heads (Ø~5.5) reach y 5.75 at x 7.5 and 43.06. Only the part in front of the panel can go there: the rails sit behind the top/bottom 10 mm (sdiy.info: leave 10 mm clear behind the panel). Risks: screwdriver access, case lids or 1U rows, and tilt clearance at the lip.
- Dial moved up with it: the carriage-to-bezel gap tightened from 5.0 to 4.0 (sensible, not generous). Dial centre 52.9, bezel y 35.4-70.4.
- Big TFT: all the height gained (1.5) went to the TFT zone, which now runs from y 70.5 (top border behind the aluminium edge) to the jack bodies at 107.85, ~36.4 usable with 1 mm clearance and <= ~49 wide.
  - Largest real part that fits: still the 2.0" 240x320 used landscape (TST020QVHS-07 / FW020TFT-V22A03, 47.8 x 34.6 x 1.9, active 40.8 x 30.6).
  - Shortfalls: 2.2" 240x320 portrait (40.1-41.04 x 55.2-56.45, e.g. CH220QV06A / DF-TFN0222FW-M1) is short ~19; 2.4" portrait (42.72 x 59.46) short ~23; 2.3" 320x240 (50.8 x 45.8) is 0.3 wider than the panel and short ~9.4; 2.0" portrait (34.6 x 47.8) short ~11.4 and gives the same area anyway.
  - Picture area before = after = 1248 mm². The TFT now sits at y 70.5-105.1 (active 72.5-103.1), and jack clearance grew to 2.75. The jacks were not moved into the rail zone.
- Jacks: 3 x stereo Thonkiconn WQP419GR (old name PJ366ST): Ø6.0 hole, Ø7.8 nut, M6x0.5 thread 4.5, body 10 deep incl. tab, ~10 wide. One row at y 112.3: J1 x 7.0, J2 x 20.0, J3 x 33.0 (13.0 pitch, playable, same as v4).
  - J1: tip = CV out (dial), ring = CV out (bezel).
  - J2: tip = CV in (motor follows), ring = gate out (button).
  - J3 (motor voice): tip = motor-voice audio in, ring = motor-texture audio out.
- USB-C (MIDI + PD power), upright slot 3.8 x 9.5 at x 43.5, y 112.0 (10.5 from J3). Max plug overmold 6.5 x 12.35 (x 40.25-46.75) leaves 3.75 to the J3 plug body (Ø7 assumed) and 3.75 to the panel edge. Panel board <= 8 x 12.5 (x 39.5-47.5, y 105.75-118.25) sits 1.5 behind-panel from the J3 body. PD-rated (>= 3 A) socket and wiring as in v4.
- Hidden-area overlay: the red squares are gone. Pale dashed bands are labelled "hidden when viewed from 30° below"; thin dashed outlines show the jack/USB bodies behind the panel.
  - Straight on, 100% of the active area is clear. From 30° below, ~14% is hidden. From above, none.
- Conflicts / Ed to decide:
  1. The carriage front-overhang option above.
  2. J2 (CV in + gate out) and J3 (audio in + texture out) still mix an input and an output on one TRS: crosstalk risk, so slew-limit the gate and use separate returns. Ring outputs must be short-proof (1k + clamp) because mono TS plugs short them.
  3. Splitter-cable dependence, with our own pinout; print it on the panel/screen.
  4. The USB-C board is tight behind J3 (1.5 gap); needs a slim vertical receptacle.
  5. A bigger picture than 2.0" needs a custom/bar TFT, or letting the TFT run behind the jacks (2.0" portrait would fit to y ~118 but adds no area and more gets hidden).
