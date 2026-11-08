# Main board circuit, part 1: the groups that need no decision (7 Nov 2026)

Main-board pass step 2 [Ed 19:36 "Yes"]. Tags: [S] source read, [A] my choice or estimate, [C] open check, [Ed] Ed's decision.
Architecture: Q33 = A (`docs/architecture-fresh-look-2026-11-07.md`): STM32H743VIT6, the joystick screen on its quad port, no
flash, the back screens later on their own board. Picture: `docs/img/main-board-circuit-part1.png`.
Still to come, one decision at a time: the 1220 driver and its supply (needs Ed's bench numbers), the power tree on board L, the
RGB part and the VCSEL driver, **the rod link circuit** (new on the list: the main-board end of the dial's one-wire power + data,
designed with the dial board), then the layer count after a first placement.

## Pin map
`tools/main_board_pinmap.py` on ST's pin data (STM32_open_pin_data, BSD-3-Clause, (c) 2020 STMicroelectronics, commit 7d1f151):
`cad/knob-param/knobparam/electronics/kicad/knob-main-pcb/pinmap/h743-lqfp100-simple.{json,txt}`. **62 nets on 82 I/O, 20 spare**
(17 general; PC2_C and PC3_C analog only; PC15 a slow input only). Re-solved 8 Nov keeping every other net on its pin: AGND_SENSE
[Q41], PWR_LIGHT in place of the VCSEL decoder [Q36]. Rules: PC13-PC15 take slow inputs only (backup domain), the
ADC-switch pads take analog only, each SPI / I2C / UART / FDCAN / timer serves one job, the interrupt inputs on different EXTI lines
(IO_INT 14, HALL3D_INT 13, JOY_TE 6). The map is re-solved with pin preferences once the neighbours are placed (step 3).

| Group | Nets (pin) |
|---|---|
| Joystick screen, QUADSPI | CLK PB2, NCS PB6, IO0 PD11, IO1 PD12, IO2 PE2, IO3 PD13; RST PE9, TE PE6, PWR_EN PE5 |
| Link flex SPI3 | SCK PC10, MOSI PC12; CS_DAC PD8, CS_OLED PD15, OLED_DC PD14, OLED_RES PD9 |
| I2C3 | SCL PA8, SDA PC9; IO_INT PC14, HALL3D_INT PC13 |
| MIDI, dial link | MIDI_TX PE1 (UART8); rod link [Q43 = A] DIAL_TX PA10 (TIM1_CH3), DIAL_RX PE11 (TIM1_CH2), Manchester by timer + DMA |
| USB FS | DM PA11, DP PA12 |
| CAN (FDCAN2) | TX PB13, RX PB12, STBY PE15 |
| ADC1 | CV_IN1 PC4, CV_IN2 PA0, CV_IN3 PA5, AUDIO_IN PA7, HALL1 PA6, HALL2 PB0, HALL4 PB1, HALL5 PC1, MOT_SENSE PC5, MOT_VOICE PA1, NTC PA3, JOY_LADDER PA2 |
| ADC2, ground sense [Q41] | AGND_SENSE PC0 (ADC2_INP10): sampled by ADC2 at the same instant as ADC1's CV in / audio in (dual simultaneous mode), subtracted in firmware [A] |
| DAC1 | AUDIO_OUT PA4 |
| Encoder (TIM3) | ENC_A PB4, ENC_B PB5 |
| 1220 (TIM2), Halls | MOT_IN1 PB10, MOT_IN2 PB11, MOT_nSLEEP PE14; HALL_EN PE13 |
| Power light [Q36] | PWR_LIGHT PB9 (TIM17_CH1, PWM into one transistor); the ring's VCSEL decoder is gone |
| RGB, violet | RGB_DIN PB8 (TIM16 + DMA), RGB_EN PE8, VIOLET_EN PE7 |
| Risley (reserved) | PB14, PB15 (TIM12) |
| Cover board (later) | COVER_TX PC6, COVER_RX PC7 (USART6), COVER_EN PE3 |
| System | BUS_PRESENT PE4; HSE PH0 / PH1; SWDIO PA13, SWCLK PA14, SWO PB3 |

## H743 core [S AN4938 rev, ST: "Getting started with STM32H74xI/G and STM32H75xI/G MCU hardware development"]
- **STM32H743VIT6** (LCSC C114409, US$7.86, 5,931 in stock, 7 Nov [S]). LQFP100 power pins from ST's pin data [S]: VDD 11, 27,
  50, 75, 100; VSS 10, 26, 49, 74, 99; VCAP 48, 73; VDDA 21; VREF+ 20; VSSA 19; VBAT 6; NRST 14; BOOT0 94. LQFP100 has no PDR_ON,
  no VDDLDO and no VDD33USB pin [S pin data], so **VDD must be 3.0-3.6 V for USB** [S AN4938 2.1.2]: 3.3 V.
- **VDD:** 100 nF X7R 0402 at each of the 5 VDD pins, plus 4.7 µF for the package [S AN4938 2.2, 7.4]; I fit 10 µF 0603 [A].
- **VCAP:** 2.2 µF ceramic, ESR < 100 mΩ, on each VCAP pin, and **VCAP1 tied to VCAP2** [S AN4938 2.2, figure 18]. LDO supply
  (the default on LQFP100).
- **VDDA:** from 3.3 V through a ferrite bead (TAI-TECH **FCM1608KF-601T03**, the part AN4938 table 9 names; LCSC C141723; 600 Ω at
  100 MHz, 350 mA, 0.5 Ω [S]), then 1 µF + 100 nF [S AN4938 2.2].
- **VREF+:** **TI REF3430IDBVR, 3.0 V** (LCSC C2156866; ±0.05 %, 6 ppm/°C, dropout 0.1 V max at no load [S TI]) from the 3.3 V,
  with 1 µF + 100 nF at the pin [Ed 8 Nov Q40 = A, noise sweep; was VDDA through 47 Ω]. [C] the REF34's output-capacitor range.
  The ADC and the DAC now span 0-3.0 V; the jack board's scaling is re-set to fit. The Halls, the switch ladder and the NTC stay
  on the 3.3 V: the firmware reads the 3.3 V on the VBAT channel (VBAT tied to VDD) and corrects them [A].
- **VBAT:** to VDD with 100 nF (no battery) [S AN4938 2.2, table 9].
- **NRST:** 100 nF to ground (AN4938 figure 18 shows 100 nF in the reset circuit [S]); to the debug pads.
- **BOOT0:** 10 kΩ to ground [S AN4938 table 9, "typical example"]; a test pad to pull it high for the ROM bootloader [A].
- **HSE crystal 25 MHz**: YXC **X322525MOB4SI** (LCSC C9006: 3225, CL 12 pF, ±10 ppm, ±20 ppm over temperature, ESR 50 Ω,
  US$0.05, 212,285 in stock [S]). 25 MHz gives 480 MHz on the PLL (25 / 5 x 192 / 2) [A]. Load capacitors **15 pF C0G** each
  [A: CL 12 = C/2 + about 4.5 pF of pin and board; AN4938 4.1.2 gives 5-25 pF typical [S]]. [C] Measure the frequency on the
  first boards and trim the capacitors if needed. No 32 kHz crystal (no clock-of-day needed); PC14 / PC15 are slow inputs.

## Debug: Tag-Connect pads, no connector fitted [A]
- **TC2030-IDC-NL footprint** (pads and locating holes only; nothing is placed, so it costs nothing per board). Pads [S Tag-Connect
  TC2030-CTX sheet]: 1 VCC (3.3 V), 2 SWDIO, 3 nRESET, 4 SWCLK, 5 GND, 6 SWO. Cable TC2030-CTX-NL to a 10-pin Cortex debugger.
- On the main board's front beside the H743. It sits under the top board, so it is for bring-up and repairs with the stack open.
- Firmware updates in the field go over USB (the H743's ROM bootloader does USB DFU [A, ST AN2606]) or a USB bootloader of ours.

## USB (full speed, from the USB-C on the jack unit, up the link flex)
- D+ / D- (flex pins 13 / 14) straight to PA12 / PA11; the H743 has the 1.5 kΩ pull-up and the PHY inside [A]. ESD is at the
  connector: TI TPD2E2U06 on the USB-C board [S step-2 parts]. Routed as a 90 Ω pair on the main board [A].
- No VBUS sensing: the module's only power is that USB-C, so when the H743 runs, VBUS is there [A].

## Joystick screen (CO5300 on the DO0164FMST02, QSPI)
- 22 Ω in series at the H743 on CLK, NCS and IO0-IO3 [A]; RST, PWR_EN out, TE in (EXTI6).
- Path: H743 → vertical board R (bottom header) → R's 13-pin top header → the top board's socket → the 13-line jumper (unchanged:
  CLK, CS, D0-D3, RESET, TE, PWR_EN, 3V3, three GND; IM straps on the jumper) → the screen.
- **Board R's 13 top pins carry only the screen's signals and grounds** [A]: 1 GND, 2 CLK, 3 GND, 4 CS, 5 IO0, 6 IO1, 7 GND, 8 IO2,
  9 IO3, 10 GND, 11 RESET, 12 TE, 13 PWR_EN. The clock has ground on both sides; every data pair sits next to a ground. The screen's
  3.3 V comes up board L's top pins (with the switch ladder and grounds), which frees R's pins for the four grounds.
- **The switch ladder** (SW1 and the joystick's switches as one resistor ladder, on the top board [S floorplan 3 Nov]) comes down
  board L as one line, JOY_LADDER into ADC1 (PA2) with 100 Ω + 1 nF at the pin [A]. Board L's 13 top pins then carry 3.3 V, the
  ladder and grounds; the order is set with board L's power circuit.
- Said plainly: these lines cross two joints (R's header pins in the top board's socket, and the jumper). If they turn out
  marginal, the clock comes down: 50 MHz is about 98 full frames a second, 25 MHz about 49 [A arithmetic].

## Hall row and encoder (as main PCB v0.11, unchanged parts)
- Four **TI TMAG5253BA3IQDMRR** linear Halls (LCSC C22401868) to ADC1 (HALL1/2/4/5), the middle one a **TI TMAG5273A2QDBVR** 3D Hall
  on I2C (LCSC C3715882; A2 ±133 mT, A1 would saturate). 100 nF at each. HALL_EN drives the TMAG5253s' enable pins; HALL3D_INT with
  10 kΩ to 3.3 V [v0.11 design.py].
- **Omron EE-SX1321** (LCSC C469128): LED through 220 Ω (9-10 mA), emitters E1 / E2 with 10 kΩ to ground into ENC_A / ENC_B on
  TIM3 CH1 / CH2 (encoder mode) [v0.11 design.py, values checked there against the datasheet].

## CAN (to vertical board R)
- FDCAN2 TX, RX and STBY to board R's bottom header; the transceiver sits on R [Ed floorplan 3 Nov]. The transceiver part and where
  the bus leaves the module are picked with board R [C].

## Link flex, main-board end (Hirose FH26W pins as on the jack lower board's J6)
1 SCK, 2 GND, 3 MOSI, 4 CS_DAC, 5 CS_OLED, 6 OLED_DC, 7 OLED_RES, 8 SCL, 9 SDA, 10 IO_INT, 11 MIDI_TX, 12 GND, 13 D+, 14 D-, 15 GND,
16-18 CV_IN1-3, 19 GND, 20 AOUT, 21 GND, 22 AIN, 23 GND, **24 AGND_SENSE**, 25 GND [S jack board circuit, 6 Nov; pin 24 Ed 8 Nov
Q41 = A].
- **AGND_SENSE** (pin 24): the jack unit's quiet ground QGND (the sleeves and the CV circuits' ground, Q42 = A), joined to its power
  ground at one 0R on the jack lower board and carrying no current. At the H743: 100 Ω + 1 nF C0G to ground like the other ADC pins, and 1 MΩ to ground so it reads 0 with the flex out [A].
  Firmware: ADC1 (CV in / audio in) and ADC2 (AGND_SENSE) in dual simultaneous mode, difference taken per sample [A].
- SCK and MOSI: 33 Ω in series at the H743 [A]. CS, D/C, RES straight.
- I2C: the 4.7 kΩ pull-ups and IO_INT's 10 kΩ are on the jack board already [S]; the main board keeps pull-up pads **not fitted**
  (v0.11's R20 / R21 become DNP) [A]. One bus: TMAG5273, TCA9535 (0x20), HUSB238 (0x08) [S].
- CV_IN1-3 and AIN arrive scaled on the jack board; at each ADC pin 100 Ω + 1 nF C0G to ground [A: keeps the ADC's sampling kicks
  off the flex; corner 1.6 MHz].
- AOUT from DAC1_OUT1 straight to the flex; the buffer and gain are on the jack board [S].

## Later cover board (back screens, Q33 = A)
- Pads only, nothing fitted: COVER_TX, COVER_RX, COVER_EN, 3.3 V, 5 V, GND, on the main board's back near where the upper screen's
  flex would land [A, placed in step 3].

## Small parts list for part 1
| Part | Value / MPN | LCSC | Qty |
|---|---|---|---|
| MCU | STM32H743VIT6 | C114409 | 1 |
| Crystal | YXC X322525MOB4SI, 25 MHz 12 pF | C9006 | 1 |
| Ferrite | TAI-TECH FCM1608KF-601T03 | C141723 | 1 |
| Reference, 3.0 V | TI REF3430IDBVR (Q40 = A) | C2156866 | 1 |
| Hall, linear | TI TMAG5253BA3IQDMRR | C22401868 | 4 |
| Hall, 3D | TI TMAG5273A2QDBVR | C3715882 | 1 |
| Encoder sensor | Omron EE-SX1321 | C469128 | 1 |
| Capacitors | 100 nF X7R 0402 (5 VDD, VDDA, VREF+, VBAT, NRST, 5 Halls); 2.2 µF X7R 0603 x2 (VCAP); 10 µF 0603; 1 µF 0402 x2; 15 pF C0G 0402 x2; 1 nF C0G 0402 x5 | generic | |
| Resistors | 10 kΩ (BOOT0, HALL3D_INT, encoder x2); 220 Ω; 22 Ω x6; 33 Ω x2; 100 Ω x5; 1 MΩ (AGND_SENSE) (0402); the 47 Ω on VREF+ is gone (Q40) | generic | |

## Sources
- AN4938, Getting started with STM32H74xI/G and STM32H75xI/G MCU hardware development (ST): sections 2.1.2, 2.2, 4.1.2, 7.4, table 9,
  figure 18. https://www.st.com/resource/en/application_note/an4938-getting-started-with-stm32h74xig-and-stm32h75xig-mcu-hardware-development-stmicroelectronics.pdf
- ST pin data (STM32_open_pin_data), BSD-3-Clause.
- LCSC: C114409 (STM32H743VIT6), C9006 (X322525MOB4SI), C141723 (FCM1608KF-601T03).
- Tag-Connect TC2030-CTX sheet: https://www.tag-connect.com/wp-content/uploads/bsk-pdf-manager/TC2030-CTX_1.pdf
- Our own: `docs/step2-power-board-circuit-2026-11-06.md` (flex pins, jack-board pull-ups, audio out), `docs/step2-parts-2026-11-05.md`
  (USB ESD), main PCB v0.11 `design.py` (Halls, encoder).

## Ring lights: a hole found, Q35 (8 Nov)
Picture: `docs/img/ring-lights-q35.png`. The model has 24 emitters on the main board's back on the thrust pitch (r 19.84, every 15°),
12 red VCSELs and 12 RGB alternating, firing forward through Ø0.62 holes into the clear race ("reverse-mounted", design notes 2 Nov).
- **The RGB part exists for that:** **SK6812MINI-E** (OPSCO, LCSC C5149201, US$0.045, 104,360 in stock [S]): body 3.2 x 2.8 x 1.78,
  flat leads halfway up the side, made to sit recessed in a board cut-out and shine through it (Adafruit sells it as "reverse mount",
  used in keyboards; Hackaday: "designed to be mounted recessed within a PCB hole" [S]). 5 V (3.7-5.5), 12 mA per colour, 800 kbit/s,
  pins VDD, DOUT, GND, DIN [S datasheet]. In a 1.6 mm board its front face sits about 0.7 mm below the front [A], so the race still
  sits flat. Each RGB site becomes a cut-out of about 3.4 x 3.0 [A, to set from the footprint drawing], leaving about 1.8 mm of board
  between neighbours.
- **The red VCSEL (JNJOPTO JNJ-V-2835CW-665003-S-D1) is not a reverse-mount part.** JNJ's VCSEL sheet (the 5730 sibling) has the lens
  on the package top and the heat path through the pads [S]; the 2835 is the same kind of package [A]. Soldered on the back, it shines
  backward and the hole above it stays dark. Reverse-mount parts turn up only as ordinary LEDs (Broadcom HSMH-C265, Dialight 599, Würth
  WL-SMRW, the SK6812MINI-E) [S search]; no red VCSEL.
- **Q35 (open):** A drop the 12 red VCSELs (the violet module and the Risley prisms stay as the laser), the RGB ring on SK6812MINI-E
  in cut-outs; B keep the red VCSELs on the board's front in pockets under the race, with the race redrawn thicker (its floor under a
  ball is 1.0 mm, and the land was already flagged thin, design notes 2 Nov).
- With A: the decoder, the shared current limit, the 12 VCSEL switches and 5 pins (VCSEL_A0-A3, LASER_EN) go; 23 pins spare.

## The clear race, a closer look (8 Nov, after [Ed 13:00, 13:06])
[Ed 13:06] "let's do the change, but make it wider where it can be ... have a little look before you run it." Pictures:
`docs/img/race-section-v050.png` (the race now, cut through a ball), `docs/img/race-widen-proposal.png` (free space all round and
the proposal). Studies: `tools/studies/race_section_sketch.py`, `race_envelope.py` (every part cut every 4° round the axis),
`race_widen_sketch.py`.
- **Now:** the clear race (the bottom track, part of the printed cradle) is a ring about 2.2 mm wide (r 18.75-20.93), floor 1.0 under
  the groove, its tops at the groove edge about 0.05 thick and up to 0.06 under the knob. The knob's own track beside the ball is
  0.10 / 0.11 a side (ring-gear teeth inside, the cap edge = glass OD outside).
- **Taller, tried:** `build.py --set ot_land_min=2.0` (floor 2.0): 332 / 334 pass. The knob rises 1 mm, the idler pinions with it,
  and their caps meet the control dial's detent arm (0.328 → 0, needs 0.3) and Hall arm (0.547 → 0). The detent arm has 0.028 mm
  spare today, so the knob cannot rise unless the control dial rises with it (which lifts its Hall magnets off the TMAG5253s).
- **Wider, proposed [A]:** foot r 17.5 → 21.2 (3.7 wide), top 0.3 under the knob (z 1.75), same groove and floor. Lips 1.33 inside,
  0.36 outside. Measured clearances: encoder bearing 0.50, knob parts 0.32, case 0.32, clear OLED 0.42, the rest ≥ 0.52. Nothing else
  moves. With the RGB recessed in the board, the floor can be solid (no hole over each light).

## Smaller balls? (8 Nov, [Ed 13:18] "if we can get them all in the smaller ball size, make it smaller; if not, keep it and widen")
- **Ring with Ø1.5 load balls** (same solver as the model, band between the ring-gear root 18.69 and the cap edge 21.0): the glass
  spacers must be ≤ 1.40 to clear the tracks, and the window must be narrow. Cospheric's precision soda-lime **1.21 mm (±0.02)** gives
  **44 pairs** on r 19.84, gaps 0.051-0.071, track clearance 0.135 [A arithmetic]. (1.01 mm also fits: 48 pairs.) Cheap sieved glass
  no longer works at this size; the spacers have to be precision balls.
- **All three kinds are sold at the smaller size [S]:** 316 stainless Ø1.50 (123bearing BA-1.50-316-INOX); synthetic ruby Ø1.5
  Grade 25 (Thermo / Alfa Aesar via Fisher, AA42077KJ; Edmund Optics 1.5 mm ruby ball lens); glass 1.21 mm (Cospheric soda-lime
  precision, 1 g ≈ 400 spheres, US$282.08, in stock; 1.01 mm US$67.14 / 100).
- **Trial build** (`--set ot_ball_d=1.5 ot_ruby_d=1.5 ot_spacer_min=1.19 ot_spacer_max=1.23 ot_spacer_alt=1.21`): 333 / 334 pass.
  The knob's side walls 0.10 → 0.35 a side; the clear floor 1.0 → 1.2 (the ball sits lower, the knob drops 0.05); the detent arm's
  slack 0.328 → 0.377. The one fail: "race web beside a pin hole" (-0.006, needs 0.05): the two Ø1.71 locating pins no longer fit in
  the narrower ring. The wider foot (r 17.5-21.2) fixes it.

**[Ed 13:26 "Yes"] done in the model as v0.51**: Ø1.5 balls (40 + 4 ruby), 1.21 glass, clear race foot r 17.5-21.2 with its top 0.3
under the knob; checks 334 / 334 (`docs/design-notes.md`, "Thrust race v0.51"). Q35 (the red VCSELs) is still open.

## Ring lights decided, and a home for one red VCSEL (8 Nov)
- **[Ed 13:35] Q35:** the RGB LEDs stay **upside down on the board's back and shine up through holes in the board** (SK6812MINI-E
  recessed in cut-outs); **no gaps in the bearing race**: its floor is solid clear resin, the light goes through it. The red VCSELs
  come out of the race; "put at least one somewhere else".
- **Where one red VCSEL could go** (`tools/studies/vcsel_spot_study.py` slices every part every 0.5 mm and follows a straight-up beam
  from each free spot on the board front; clear parts let it through; picture `docs/img/vcsel-spots.png`):
  - Inside the knob on the main board: only just fits, and the control dial's underside is 4.3 mm above it. Not offered.
  - **B:** main board front between the knob and the joystick, about (1.3, 26.5): the beam goes straight up through the clear case;
    it needs a frosted spot on the faceplate's inside to end on (a red glowing dot in the panel). The main chip drives it.
  - **A:** the dial board's underside, shining down into the knob: [Ed 3 Nov 11:50] kept room there "for LEDs shining down into the
    knob and the violet source"; the grey PA-12 dial under it needs a window or a clear section (optics round). The dial's own chip
    drives it.
- **Q36 (open):** A or B. Open after that: whether the 12 old VCSEL sites become RGB (24 in the ring) or close.
- **[Ed 13:51] Q36 = B, as the power light** ("we could have it as the power LED; we have a laser instead"). One red VCSEL
  (JNJ-V-2835CW-665003-S-D1) on the main board front at about (1.3, 26.5) [A, set in placement]: 12 o'clock above the knob, about
  5.5 mm outside the knob's edge, between the knob and the joystick. Straight up, nothing opaque meets the beam; the clear case is
  solid over it from z 29.8 to 38.8 (the faceplate between the knob hole and the joystick opening) [model column check]. About 39 mm
  from the VCSEL to the panel front; at the JNJ sheet's 20° divergence that is a spot about 12 mm across at the case's underside [A].
  So the dot needs a target: a small frosted (matte) disc printed on the case's inside face over it [A, case print feature], and a
  low current (just over the 4 mA threshold, PWM) for a power light. Drive: one GPIO and one transistor; the decoder and LASER_EN
  go (5 pins → 1).
- **[Ed 13:54] all 24 ring sites get the reverse-mount RGB** (SK6812MINI-E), "we won't power them all at once": brightness is capped in
  firmware. Full white would be about 0.86 A at 5 V for 24 [S 12 mA per colour]; the 5 V converter is sized for the firmware cap,
  not that. Checked: no reverse-mount RGBW (with a white chip) turned up (only RGB: SK6812MINI-E, MINI-EA) [S search, 8 Nov].

## The rod link, Q43 (8 Nov): **A [Ed 18:58 "A if it will fit"]**
**It fits** [model v0.52, measured]: the dial-end bias tee goes on the fixed rod-link board (Ø12, z 49.6-50.6, nut on top, does not
turn). Above its top face, from r 2.5 to r 6.0 and up to the dial board's lowest part (z 54.1), the ring is empty but for the
strap (1.8 of 325 mm³): about 70 mm² of board and 3.5 mm of height for a choke, a capacitor, a comparator and three or four
0402s (about 15 mm²). So the choke can be a 3 x 3 mm part (more inductance and less drop than a 2 x 2) [A, C part]. The strap's
four lines become 5 V, ground, data out, data in; the 'rod-link PHY' box on the dial board goes. Main end on the main board.
Pin map re-solved (`--keep`): DIAL_DATA (PD5) gives way to DIAL_TX PA10 and DIAL_RX PE11 on TIM1. [C] the bit rate against the
chokes: at 2 Mbit/s the code's energy reaches down to about 0.5 MHz, where 22 µH is only about 70 Ω, so either 47 µH or more
at each end, or a faster code (4 Mbit/s); set with the parts [A].
Picture: `docs/img/rod-link-q43.png`. The dial (ESP32-S3, its screen, LEDs, the mic) gets 5 V and the data both ways on the M1.6
rod; the brass tube is the return; about 0.12 A, 0.6 W [A, layout v4].
- **A (recommended):** a bias tee at each end: the DC through a small choke, the data through a small capacitor as a DC-free
  (Manchester) code at about 2 Mbit/s; a small comparator receives. The dial's draw stays steady, so nothing on the 5 V follows
  the data, and the data's energy is at 1-4 MHz [A]. ESP32-S3: its RMT pulse peripheral; H743: a timer + DMA (two pins from the
  spares, replacing DIAL_DATA). Enough for the commands, the mic's sound back (about 0.8 Mbit/s raw) and a firmware update in
  about a minute [A]. [C] the dial-end choke: 0.2 A in about 2 x 2 mm.
- **B:** the supply level is the data: the main end switches the rod 5.0 / 4.4 V (down), the dial switches a small load (up),
  a plain UART to about 1 Mbit/s, no chokes. Noise: the dial's hold-up capacitor recharges in step with the data, so packet
  bursts (60 a second) put 60 Hz and harmonics on the 5 V and ground unless the link sends filler all the time [A].
- Not offered: a power+data chip of the MAX22088 class: 200 kbit/s, 4 x 4 mm at both ends [S Analog Devices].
