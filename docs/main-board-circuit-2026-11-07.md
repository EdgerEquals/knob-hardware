# Main board circuit, part 1: the groups that need no decision (7 Nov 2026)

Main-board pass step 2 [Ed 19:36 "Yes"]. Tags: [S] source read, [A] my choice or estimate, [C] open check, [Ed] Ed's decision.
Architecture: Q33 = A (`docs/architecture-fresh-look-2026-11-07.md`): STM32H743VIT6, the joystick screen on its quad port, no
flash, the back screens later on their own board. Picture: `docs/img/main-board-circuit-part1.png`.
Still to come, one decision at a time: the 1220 driver and its supply (needs Ed's bench numbers), the power tree on board L, the
RGB part and the VCSEL driver, **the rod link circuit** (new on the list: the main-board end of the dial's one-wire power + data,
designed with the dial board), then the layer count after a first placement.

## Pin map
`tools/main_board_pinmap.py` on ST's pin data (STM32_open_pin_data, BSD-3-Clause, (c) 2020 STMicroelectronics, commit 7d1f151):
`cad/knob-param/knobparam/electronics/kicad/knob-main-pcb/pinmap/h743-lqfp100-simple.{json,txt}`. **64 nets on 82 I/O, 18 spare**
(15 general; PC2_C and PC3_C analog only; PC15 a slow input only). Rules: PC13-PC15 take slow inputs only (backup domain), the
ADC-switch pads take analog only, each SPI / I2C / UART / FDCAN / timer serves one job, the interrupt inputs on different EXTI lines
(IO_INT 14, HALL3D_INT 13, JOY_TE 6). The map is re-solved with pin preferences once the neighbours are placed (step 3).

| Group | Nets (pin) |
|---|---|
| Joystick screen, QUADSPI | CLK PB2, NCS PB6, IO0 PD11, IO1 PD12, IO2 PE2, IO3 PD13; RST PC0, TE PE6, PWR_EN PE5 |
| Link flex SPI3 | SCK PC10, MOSI PC12; CS_DAC PD8, CS_OLED PD15, OLED_DC PD14, OLED_RES PD9 |
| I2C3 | SCL PA8, SDA PC9; IO_INT PC14, HALL3D_INT PC13 |
| MIDI, dial link | MIDI_TX PE1 (UART8), DIAL_DATA PD5 (USART2, half duplex) |
| USB FS | DM PA11, DP PA12 |
| CAN (FDCAN2) | TX PB13, RX PB12, STBY PE15 |
| ADC1 | CV_IN1 PC4, CV_IN2 PA0, CV_IN3 PA5, AUDIO_IN PA7, HALL1 PA6, HALL2 PB0, HALL4 PB1, HALL5 PC1, MOT_SENSE PC5, MOT_VOICE PA1, NTC PA3, JOY_LADDER PA2 |
| DAC1 | AUDIO_OUT PA4 |
| Encoder (TIM3) | ENC_A PB4, ENC_B PB5 |
| 1220 (TIM2), Halls | MOT_IN1 PB10, MOT_IN2 PB11, MOT_nSLEEP PE14; HALL_EN PE13 |
| VCSELs | A0-A3 PE12, PE11, PE10, PE9; LASER_EN PB9 (TIM17) |
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
- **VREF+:** from VDDA through 47 Ω, with 1 µF + 100 nF [S AN4938 2.2]. [C] Whether the CV inputs want a precision reference
  here instead (1 V/oct pitch CV): with the CV in circuit on the jack board, later.
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
16-18 CV_IN1-3, 19 GND, 20 AOUT, 21 GND, 22 AIN, 23-25 GND [S jack board circuit, 6 Nov].
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
| Hall, linear | TI TMAG5253BA3IQDMRR | C22401868 | 4 |
| Hall, 3D | TI TMAG5273A2QDBVR | C3715882 | 1 |
| Encoder sensor | Omron EE-SX1321 | C469128 | 1 |
| Capacitors | 100 nF X7R 0402 (5 VDD, VDDA, VREF+, VBAT, NRST, 5 Halls); 2.2 µF X7R 0603 x2 (VCAP); 10 µF 0603; 1 µF 0402 x2; 15 pF C0G 0402 x2; 1 nF C0G 0402 x4 | generic | |
| Resistors | 10 kΩ (BOOT0, HALL3D_INT, encoder x2); 220 Ω; 47 Ω; 22 Ω x6; 33 Ω x2; 100 Ω x4 (0402) | generic | |

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
