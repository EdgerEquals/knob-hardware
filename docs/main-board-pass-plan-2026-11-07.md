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
