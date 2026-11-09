# Main-board pass: plan (7 Nov 2026, for Ed's OK)

Picture: `docs/img/main-board-inventory-v050.png` (the board's outline and windows from model v0.50, and what sits on it now).

## Where it stands
- The KiCad main board is still the **v0.11 layout from v0.18 inputs** (`cad_constraints.json`): rod clamp, 1220 pads, the Hall row,
  the EE-SX1321, J2 (joystick socket), a J10 placeholder for the MCU, and the 716 driver (left out from now on, Q27). No MCU, flash,
  power, motor driver, emitters, link flex pads, post pads or vertical-board headers.
- The model (v0.50) has moved on 30 versions: the mechanism turned, the H7B0 on the front under the joystick, the 12 RGB + 12 VCSEL
  emitter ring on the back, vertical boards L (power) and R (CAN + joystick lines), the clear OLED over window D, the jack unit's
  posts (15 V, GND) and the link flex pads in the bottom strip, the windows A-E. Re-exporting the constraints changes 3318 values.
- The 2 Nov H7B0 signal plan (`docs/pcb-h7b0-plan-2026-11-02.md`) predates step 2: since then USB data, the CV / audio / MIDI and the
  clear OLED's SPI come up the link flex, power arrives at 15 V on the posts (the PD sink is on the jack power board), and the 716 is gone.

## The plan
1. **Signal plan refresh** (on paper): the 2 Nov budget updated for step 2 (link flex: USB D+/D-, SPI SCK / MOSI / CS_DAC / CS_OLED /
   OLED_DC / OLED_RES, I2C SCL / SDA + IO_INT, MIDI TX, CV in 1-3 on the ADC, audio out and in), no PD sink, no 716. A pin map from
   ST's own pin data (their open data on GitHub if the licence fits, else the datasheet's tables) in place of CubeMX.
2. **Circuit**, written up with values and LCSC parts like the jack power board's: 15 V to 5 V and 3.3 V, the 1220 driver, the
   emitter drivers (VCSELs one at a time through a decoder, RGB chain), the MCU's crystal / SWD / USB, flash, ESD, and the back
   AMOLEDs' power if they are on this board. Shown to Ed before the board.
3. **Board**: constraints re-exported from v0.50; fixed parts where the model puts them; the rest placed with the placer and routed
   (router4 or Freerouting) to KiCad DRC 0 / 0; fab pack; CAD check against the model.
4. **Model**: the board proxy from the new KiCad board, full build and assembly check.

## Decisions
- **Q31 [Ed 7 Nov 18:58] = A: everything in the model goes on the first main board**: both back AMOLEDs with their power, the
  joystick screen, the flash, the VCSEL and RGB rings, CAN to the vertical boards (not B, knob first; not C, screens drawn but unfitted).

- **Step 1 done on paper** (`docs/main-board-signals-2026-11-07.md`): 77 nets on the LQFP100's 82 I/O, 5 spare. Finding: the
  LQFP100 has one fast quad port (Octo-SPI port 1 only), and the LQFP144 does not fit. Q32 first round (screen or flash on the
  port) [Ed 19:11]: not this compromise. **Q32 second round (open):** the two share the port and take turns; A keeps the H7B0 with
  a 74LVC1G19 selector, B swaps to an STM32U5A5 (picture `docs/img/qspi-shared-bus-q32.png`). [Ed 19:18] "a band-aid? zoom out":
  **fresh look** in `docs/architecture-fresh-look-2026-11-07.md`. **Q33 (open):** local drawing (each screen place has its own
  ESP32-S3, the main chip sends commands, like the dial through the rod) or central drawing with the shared port. [Ed 19:29]
  "remove things": **Q33 restated** [Ed 19:34 "Okay"] **= A: subtract** (back screens to their own board later, STM32H743VIT6 in the same land,
  no flash; 64 nets, 18 spare) or B keep the back screens with local drawing.

Expected next, one at a time as they come up:
1. The 1220 driver and its supply (15 V direct or a lower rail). **[Ed 8 Nov 12:38] the 1220 is the 6 V version** (his AliExpress
   listing: "Mini 12mm 1220 Coreless Planetary Gearbox Gear Motor DC 3V-12V 6V"). **Q34 [Ed 12:39 "5v"] = A: from the 5 V rail.** (A from the 5 V rail (it can never
   see more than 5 V; less PWM ripple in a coreless motor [S maxon]) or B from 15 V with PWM capped at 40 %, `docs/img/motor-supply-q34.png`.)
   **[Ed 8 Nov 15:31] bench, stall: 0.144 A at 1 V, 0.299 A at 2 V** (corrects 15:28's "1.44 A"). Line through the two: **6.45 Ω**
   with the meter and leads, brushes 0.07 V, so held still at 5 V about **0.76 A** (3.8 W), at 6 V 0.92 A [arithmetic].
   **Q37 [Ed 15:36] = A: TI DRV8213.** (A TI DRV8213 (1.65-11 V, 4 A peak, 0.24 Ω, current sense out (IPROPI → MOT_SENSE) and a current limit set by
   one pin (VREF), PWM to 100 kHz, WSON-8 2 x 2, LCSC C22407186 US$0.68, 3,698 in stock [S]) or B the DRV8837 (no current sense),
   `docs/img/motor-driver-q37.png`.) The motor can never draw more than about 0.76 A from 5 V, so the 5 V supply is sized
   without waiting for torque per amp; that number only sets VREF (the limit, at or under 0.76 A). Torque per amp still to measure (lever force at the same stalls).
   Then the driver needs Ed's bench numbers (the "Motor bench test sheet" doc is
   still empty): which voltage version, no-load current at 5 / 9 / 12 V, stall current at 5 / 9 V (pulses of 1-2 s).
2. The power tree on vertical board L (15 V to 5 V and 3.3 V). **Q38 = A [Ed 8 Nov 16:04]** (`docs/img/power-tree-q38.png`): A two TPS62933 bucks
   straight from 15 V (the jack power board's part; 5 V switched by the H743 per the Q6 rule, 3.3 V always on), or B one buck to 5 V
   and an LDO to 3.3 V (the 3 Nov plan; 0.4-0.85 W in the LDO). Loads [A except the bench]: 5 V 1.8 A worst (1220 0.76 held still,
   24 RGB 0.86 full white, dial 0.12, CAN 0.07), about 1.3 A with the LED cap; 3.3 V 0.5 A worst. Worst draw from 15 V about 12 W
   (0.9 A), inside the eFuse's 3 A. No second input limit on board L (the jack power board's eFuse already limits VSYS) [A].
   **Paused for the noise sweep [Ed 15:45]** (`docs/noise-sweep-2026-11-08.md`, `docs/img/noise-sweep.png`): both of board L's
   bucks would sit in light-load mode (PFM) most of the time. **Q39 (open):** A TPS62933F (fixed frequency at every load) on all
   three bucks, B TPS62933O (out-of-audio). Then Q38 again. Then Q40 (the ADC's reference) and Q41 (a ground-sense line on the
   flex), one at a time.
   **Q39 = A [Ed 15:59 "Yeah, that's perfect"]:** TPS62933F (LCSC C5219272) on all three bucks, about 1-2 MHz, set apart; the
   1220's PWM at 100 kHz. The jack board's U6 swapped (same footprint). **Q38 asked again** with the F part: **A [Ed 16:04]**, two TPS62933F straight from 15 V. **Q40 = A [Ed 16:07]:** a TI REF3430 3.0 V reference on VREF+ (`docs/img/adc-reference-q40.png`); the jack board's ranges
   re-set to fit. **Q41 = A [Ed 16:11]:** flex pin 24 becomes AGND_SENSE (`docs/img/ground-sense-q41.png`), read on PC0 (ADC2) with each CV
   in; pin map re-solved (61 nets, 21 spare). Then **Q42 = A [Ed 16:35]**: a quiet ground (QGND) for the sleeves and the CV circuits, on its own stack pins, joined to GND
   once on the lower board (`docs/img/quiet-ground-q42.png`). The three jack boards rebuilt and re-routed.
   **Q43 = A [Ed 18:58 "A if it will fit"]:** the rod link is a bias tee at each end with a Manchester code; it fits on the
   fixed rod-link board (measured in the model). Next: place the main board (step 3), then the layer count.
3. The RGB emitter part; the VCSEL driver. **Hole found 8 Nov:** the red VCSEL is top-emitting, so it cannot fire through the
   board from the back. RGB: SK6812MINI-E recessed in cut-outs. **Q35 (open):** A drop the red VCSELs, B keep them on the front
   under a thicker race (`docs/main-board-circuit-2026-11-07.md`, `docs/img/ring-lights-q35.png`).
4. Layer count (after a first placement shows the density).
(The back AMOLEDs' power chip is gone with Q33 = A.)

## Step 3: placing the main board (8 Nov, Ed 19:02 "Go")
Room map from the model, v0.52 (`tools/studies/main_board_room.py`, slices 0.05-2.2 mm off each face): the board is 2,866 mm²
with its windows; the front has 985 mm² free (the knob drive, the clear OLED, the case's side ledges and the chip take the rest),
the back 2,451 mm² (the 24 LEDs, the encoder sensor and the rim of its disc, the joystick's rear spring anchor, the back
cover's rim). Plan: `docs/img/main-board-plan.png` (`tools/studies/main_board_plan_fig.py`, every block fitted into free room).
- Front: the H743 under the joystick (fixed since layout v4), Tag-Connect pads beside it, the screen's 22 Ω and the link SPI's
  33 Ω, the power light (fixed).
- Back: behind the chip the REF3430 and the ADC input filters; inside the LED ring the DRV8213 by the motor, the rod link's
  main end by the rod, the ring LEDs' own 5 V branch, the I2C pull-ups; the encoder's resistors by its sensor; pads for the
  later cover board at the top. No part under the encoder disc's rim (it comes within 2.2 mm of the board).
- The tight spot: window D leaves a 2.8 mm strip each side, and the LED cut-outs leave only 0.6 mm outside the ring at the
  sides, so every track from the bottom (link flex, the 15 V post) to the top (the chip, boards L and R) threads between two
  cut-outs (1.76 mm webs, about 5 tracks a layer at 0.1 / 0.1 mm, 0.3 off each cut-out [A]) into the ring and out again.
  About 40 tracks plus three rails and ground: 4 layers at least; the count is settled after placing.
- **Netlist done** (`knob-main-pcb/v2/design.py`, 180 parts, 131 nets with 24 ring LEDs; doc part 2 in `docs/main-board-circuit-2026-11-07.md`).
- **Q44 (open), found while setting up the placement** (`docs/img/ring-pads-q44.png`, `tools/studies/ring_pads_q44_sketch.py`):
  the SK6812MINI-E's leads leave its two short ends, so its pads sit 2.0-3.4 mm out from its centre along the 3.2 mm body
  (Keebio-Parts and marbastlib agree [S]). The model points that axis along the radius, so the outer pads land in windows A, B,
  C, E or off the board edge at 3 and 9 o'clock: **36 of the 96 pads**. Turned along the ring they all fit under the race:
  **A** 12 LEDs, 30° apart, 3.1 mm between neighbours, and the gaps between cut-outs open from 1.8 to about 7 mm (the ~40
  tracks crossing the ring get easier); **B** 16 LEDs, 22.5° apart, 0.6 mm between neighbours (tight), tracks cross on the inner
  layers only. Either way the model's cut-outs and the race's two locating pegs turn with the LEDs.
  **Q44 = A [Ed 19:37 "12"]:** 12 LEDs every 30°, turned along the ring. Model v0.53: `em_n` 6, `em_phase` 15 (the panel's 3 and
  9 o'clock, where the side tracks pass window D, fall in the middle of a web), cut-outs 3.0 radial x 3.4 tangential, the pegs
  follow. Netlist: 12 LEDs (156 parts, 119 nets). Full white is now 0.43 A on the ring's 5 V [S 12 mA a colour].
- **First placement** (8 Nov evening; `knob-main-pcb/v2/make_board.py`, picture `knob-main-pcb/v2/placement.png`): the model's
  fixed parts where the model has them (the H743's centre, the five Halls, the 12 ring LEDs with their pads along the ring, the
  EE-SX1321 with its slot on the rim's tangent, the power-light VCSEL, the posts, the link flex pads, board L and R headers, the
  rod clamp, the 1220's tabs); the rest by the annealing placer, each part in its block's zone on the free room of its face.
  Wirelength 3,881 mm; KiCad DRC 0 (unrouted). Two things found and fixed on the way [A]:
  - **Window B** (model v0.53): it still had the notch of the old encoder riser (gone since Q27), and the EE-SX1321's pads sat
    0.08 mm off its edge. Regenerated with the sensor and its pads + 0.5 as the obstacle: B 107.3 → 114.3 mm², A, C, D, E
    unchanged; checks 335 / 335.
  - **Stale holes:** the model still reads the old v0.11 board's joystick holes (Ø3.4 at x ±10.8, y 25.2 and 38.4) back from
    its proxy; nothing passes through them now, so the new board fills them in (16.9 mm² of board back).
  The Tag-Connect pads went where both faces are free (its locating holes go through): (-11.0, 31.2), turned 90°.
- **Pin map re-solved** against the placement (each net to its nearest pin; chip turned 0°; straight-line 1,841 mm, was 2,143)
  and placed again: wirelength 3,497 mm, DRC 0 unrouted.
- **Q45 (open), the layer count** (`docs/img/layers-q45.png`, `tools/studies/layers_q45_sketch.py`; `make_board.py --trial`):
  the placed board routed twice by Freerouting 1.9.0, 12 passes each, ground left to the planes with a via at every ground pad.
  **A, 4 layers** (front, In1 ground plane, In2, back): 41 connections left (8 of them ground pads still without a via), 262 vias.
  **B, 6 layers, two ground planes** (front, In1 ground, In2, In3, In4 ground, back): 27 left (8 ground), 280 vias. Both have
  ~90 rule errors where the router kept 0.15 mm from windows and holes instead of 0.25 (fixable on either). What is left is mostly
  the link flex's lines going up to the chip: they all squeeze up the 2.5 mm strip beside window D on the right. Neither finishes
  on the router alone; B leaves about half as much to finish by hand and gives the analog lines ground on both sides.
  [C] PCBWay to price both in the pre-quote. (A first pair of trials had the router routing ground too: 43 / 21 left.)
  **Q45 = B [Ed 9 Nov 09:24]: 6 layers**, front, In1 ground plane, In2, In3, In4 ground plane, back (four signal layers, the
  analog lines between two grounds). [C] PCBWay prices it in the pre-quote.

## Step 3: routing the main board (9 Nov)
- **The ribbon** [Ed 09:31 "Y"] (`docs/img/flex-corridor.png`): the link flex's lines laid first and locked, the analog ones on
  In3 with In2 kept clear above them (a rule area), I2C / MIDI / USB on the back, both up the right strip beside windows D and
  C, in between two LEDs and out again; the SPI lines on the front up the left side. Then ground: a via beside every ground pad
  (one in the middle of an exposed pad; C12 by the edge has no room, so a 1.2 mm track joins it to C9's). Then Freerouting
  1.9.0 with ground left to the two planes, a pass with the first result fixed, KiCad's DRC.
- **What the router left** (third run, then five passes with rip-up from that result): 11 connections, every ground pad joined,
  no rule errors. One by one they were three knots: the flex pads (0.3 mm apart, every line to a via, the ground vias placed
  first boxing pads in), board L's 15 V feed (75 mm from the post at the bottom to J2 at the top left, by the end walled in
  by the router's own tracks on every layer) and the USB pair into the chip.
- **So those three are laid before the router too** [A] (`make_board.py`: `flex_fanout`, `preroute`):
  - Flex pads: each pad a short front stub to its own via, odd pads up and even down, each row staggered 0.3 (vias 0.2 mm
    apart); the right ribbon now starts under the pads, its lines in the order their vias come, so no line crosses another;
    the SPI lines start at their pads and step up into the left ribbon. Tight, said plainly: next to the pads the analog
    lines keep 0.16 mm from the neighbouring pads (their rule is 0.15; the pads' own pitch sets it). The USB pair now runs at
    the two edges of its 6-line ribbon, 1.5 mm apart (fine for full-speed USB [A]); the flex's pinout is unchanged.
  - 15 V (VSYS): one 0.4 mm track on In2 from the post to J2, found by the patch router (below) on the empty board.
  - USB: the ribbon's ends into the chip on the back and front.
- **Patch router** (`electronics/kicad/patch_router.py`): joins what the router leaves, one net at a time, on a 0.05 mm grid
  around the copper already there (router4's search in C), each path checked exactly against the clearances and searched
  again around anything it comes too close to; it may take up the router's own tracks of other nets at a price and join
  those again, two levels deep at most.
- **Fourth run** (fan-out, VSYS and USB laid first): the router left 12, no rule errors; the patch router joined 4 more
  (8 left, `docs/img/main-board-routed-8-left.png`, `docs/img/main-board-last-8.png`). The 8 sit in two crowded spots: where the
  right ribbon comes out at the top (walled in by J3's through-hole pins, the encoder sensor's large back pads, window B's notch
  and the ADC filters' tight cluster on the back) with the chip's right-side pins 54-58 next to it, and the 7 mm neck between
  windows A and B under the chip.
- Tried and left out, said plainly: taking up the router's tracks to force the 8 through (two levels deep) moved the jam onto
  about 30 other lines, and the router then ran out of time rejoining them (17 left); carrying the analog lines on west along
  window B's notch left their last hop to the ADC filters with no via room. A 0.003 mm track the router itself left made it
  hang reading the board back ("normalization of net failed"): such slivers are now dropped first.
- **Ed 9 Nov 16:4x "A: plan the top end"**: the pins it could not reach get a short stub to their own via before the router
  (`ESCAPES`: chip pins 54-58 and 44, ADC filter pads R4.1 and R5.2; three of the chip's sit under its body, tented), then the
  full route again. If the corner still does not close, the next step is moving a couple of the filter resistors to open via
  room (a placement change; asked first).
- **Routed: KiCad DRC 0 / 0** (9 Nov evening; `docs/img/main-board-routed.png`). With the escape vias the router left 3
  (from 12); the patch router joined two, and MOSI_L after taking up two of the router's lines (CAN_STBY, JOY_PWR_EN), which it
  then joined again. Trimming now cuts a track at every T before dropping a stub, so a stub's trim no longer breaks the line it
  hangs off. 347 vias; track 1,397 mm front, 1,222 In2, 1,269 In3, 1,098 back; both ground planes filled.
- Said plainly about the finished routing [A]:
  - The analog lines run in their In3 ribbon (86-131 mm of each), USB in its back ribbon, SPI in its front ribbon; VSYS one
    0.4 mm track on In2.
  - The four slow back lines (I2C SCL / SDA, IO_INT, MIDI TX) left their ribbon lines near the flex pads and go round on the
    inner layers instead: 100-160 mm each. Fine for 400 kHz I2C, an interrupt and 31.25 kbit/s MIDI, but untidy; a later
    tidy-up could bring them back into the ribbon.
  - MOSI_L (the link flex's SPI to the screen boards) joins its 33 ohm resistor by a 57 mm way round.
  - Three escape vias sit under the H743's body (pins 54, 56, 58), tented.
- Next: check the routed board against the model (step 4, the proxy from this board), then the fab pack.

## Step 4: the model against the routed board (9 Nov evening, Ed 17:30 "Go") — model v0.54
- `knob-main-pcb/v2/export_proxy.py` writes `knob-main-pcb/pcb_proxy.json` from the routed board (panel frame): the 9 holes its
  footprints drill beyond the headers' legs, every part the model does not already have as a part of its own as a body box
  (fab outline with its pads, the package's datasheet maximum height [A]) on both faces (100 back, 26 front), the rod clamp's
  back pad (a ring of radius 2.2 round the rod; the model's Ø9.7 pad was a stand-in), and where the parts the model places
  itself sit on the board.
- Model: `kicad_frame` "panel"; the board proxy now carries the front parts too; the old board's made-up Hall decouplers and the
  stale v0.16 joystick holes are gone with it; the rod pad follows the board. New check: the chip, the power light and the 12
  ring LEDs on the board are where the model has them (largest 0.05 mm, the chip, by the placer's grid).
- **v0.54: 336 / 336 gap checks pass, no clashes** (the known v0.53 clash of the old board's back parts with the USB-C key is
  gone). Nearest board-related margins: ring LED bodies to the back parts 0.79 (target 0.5), rod pad to the back parts 0.64
  (0.29), parts behind the board to the back AMOLEDs 5.6 (1.0).
- Not done, said plainly: the section sheet's render fails on its encoder inset (an empty picture, before this change too), so
  v0.54 has the check file only; and `--full` still loads the old v0.11 board's STEP (the v2 STEP is 5 MB with every via, not
  committed; `kicad-cli pcb export step --board-only --user-origin 100x100mm` makes it in the panel frame).
- Next: the fab pack for PCBWay (Gerbers, drill, BOM with LCSC and datasheet links, placement), then the pre-quote.
- **Fab pack v2.0** (`knob-main-pcb/v2/fab/`, `fab_export.py knob-main-pcb`): 6-layer Gerbers (both ground planes filled), PTH /
  NPTH Excellon with maps, pick-and-place for 145 parts on both faces, BOM (47 lines, with each part's datasheet link [Ed]),
  KiCad DRC 0 / 0 in `reports/`. README says NOT READY TO ORDER until the passives get LCSC numbers (values and packages are
  set; choosing the parts is the next step), and flags J2 / J3 [C]: fitted here by PCBA (design.py) or with the vertical boards.
  Hand-fit and pad-only parts (J1, J4, J5, JP1, H1, M1, MP1, MP2) and the unfitted R10, R11, R31 are out of the BOM and CPL.
