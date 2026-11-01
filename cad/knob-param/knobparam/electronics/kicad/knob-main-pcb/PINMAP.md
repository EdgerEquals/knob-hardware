# STM32G474VET6 pin map (main PCB v0.12)

LQFP100, 86 I/O. The "before" column is the 62-pin list from the 1 Nov 2026 MCU note (including SWD and the one violet supply MOSFET). This round adds 19 gates. **5 I/O spare** after that (PC13, PC14, PC15, PD6, PD7). PC14/PC15 are left for a later 32 kHz crystal. PC13 is the RTC pin; do not load it.

QSPI bank 1 is the top-screen AMOLED (DO0164, connector is pads until the folded FPC is frozen). The bottom 2.0" TFT is SPI (one QSPI peripheral). The dial-screen QSPI stays on the CH32V003; the G4 only has the single data-over-power line (`VBUS_DATA` on LPUART1_TX, PA2).

Firmware: only one of the 13 VCSEL gates (VCS1–VCS12 and VCS_SCAN) may be high at a time. The shared sink still limits the sum if two are on. `LASER_EN` must be high as well; it powers the anode rail and is pulled off. RGB, violet, 1220, 716, Risley and the mirror motor are each pulled off and stay off until firmware turns them on.

| Pin | Port | Net | Group | Round |
|---|---|---|---|---|
| 1 | PE2 | LASER_EN | laser | v012 |
| 2 | PE3 | RGB_EN | rgb | v012 |
| 3 | PE4 | VCS_SCAN | laser | v012 |
| 4 | PE5 | BUS_PRESENT | sense | before |
| 5 | PE6 | MIC_EN | audio | before |
| 6 | VBAT | +3V3 | power | before |
| 7 | PC13 | — spare | spare | spare |
| 8 | PC14 | — spare | spare | spare |
| 9 | PC15 | — spare | spare | spare |
| 10 | PF9 | VCS1 | laser | v012 |
| 11 | PF10 | VCS2 | laser | v012 |
| 12 | PF0 | OSC_IN | clock | before |
| 13 | PF1 | OSC_OUT | clock | before |
| 14 | NRST | NRST | reset | before |
| 15 | PC0 | HALL1 | hall | before |
| 16 | PC1 | HALL2 | hall | before |
| 17 | PC2 | HALL4 | hall | before |
| 18 | PC3 | HALL5 | hall | before |
| 19 | PF2 | VCS3 | laser | v012 |
| 20 | PA0 | ENC_A | enc | before |
| 21 | PA1 | ENC_B | enc | before |
| 22 | PA2 | VBUS_DATA | link | before |
| 23 | VSS | GND | power | before |
| 24 | VDD | +3V3 | power | before |
| 25 | PA3 | M1220_SENSE | m1220 | before |
| 26 | PA4 | CV_OUT1 | cv | before |
| 27 | PA5 | AUD_OUT | audio | before |
| 28 | PA6 | CV_OUT2 | cv | before |
| 29 | PA7 | MIRROR | scan | v012 |
| 30 | PC4 | VCS4 | laser | v012 |
| 31 | PC5 | VCS5 | laser | v012 |
| 32 | PB0 | CV_IN | cv | before |
| 33 | PB1 | AUD_IN | audio | before |
| 34 | PB2 | HALL_EN | hall | before |
| 35 | VSSA | GND | power | before |
| 36 | VREF+ | +3V3 | power | before |
| 37 | VDDA | +3V3 | power | before |
| 38 | PE7 | LCD_RST | qspi | before |
| 39 | PE8 | LCD_TE | qspi | before |
| 40 | PE9 | LCD_PWR | qspi | before |
| 41 | PE10 | QSPI_CLK | qspi | before |
| 42 | PE11 | QSPI_NCS | qspi | before |
| 43 | PE12 | QSPI_IO0 | qspi | before |
| 44 | PE13 | QSPI_IO1 | qspi | before |
| 45 | PE14 | QSPI_IO2 | qspi | before |
| 46 | PE15 | QSPI_IO3 | qspi | before |
| 47 | PB10 | HALL3D_INT | hall | before |
| 48 | VSS | GND | power | before |
| 49 | VDD | +3V3 | power | before |
| 50 | PB11 | NTC | sense | before |
| 51 | PB12 | VCS6 | laser | v012 |
| 52 | PB13 | VCS7 | laser | v012 |
| 53 | PB14 | M1220_IN1 | m1220 | before |
| 54 | PB15 | M1220_IN2 | m1220 | before |
| 55 | PD8 | SW_UP | joy | before |
| 56 | PD9 | SW_DOWN | joy | before |
| 57 | PD10 | SW_LEFT | joy | before |
| 58 | PD11 | SW_RIGHT | joy | before |
| 59 | PD12 | SW_CENTER | joy | before |
| 60 | PD13 | FEEL_nSLEEP | feel716 | before |
| 61 | PD14 | M1220_nSLEEP | m1220 | before |
| 62 | PD15 | MOT_VOICE_EN | audio | before |
| 63 | VSS | GND | power | before |
| 64 | VDD | +3V3 | power | before |
| 65 | PC6 | FEEL_IN1 | feel716 | before |
| 66 | PC7 | FEEL_IN2 | feel716 | before |
| 67 | PC8 | I2C_SCL | hall | before |
| 68 | PC9 | I2C_SDA | hall | before |
| 69 | PA8 | GATE_OUT | cv | before |
| 70 | PA9 | VCS8 | laser | v012 |
| 71 | PA10 | VCS9 | laser | v012 |
| 72 | PA11 | USB_DM | usb | before |
| 73 | PA12 | USB_DP | usb | before |
| 74 | VSS | GND | power | before |
| 75 | VDD | +3V3 | power | before |
| 76 | PA13 | SWDIO | swd | before |
| 77 | PA14 | SWCLK | swd | before |
| 78 | PA15 | TFT_CS | spi | before |
| 79 | PC10 | RGB_DIN | rgb | v012 |
| 80 | PC11 | TFT_DC | spi | before |
| 81 | PC12 | TFT_RST | spi | before |
| 82 | PD0 | CAN_RX | can | before |
| 83 | PD1 | CAN_TX | can | before |
| 84 | PD2 | TFT_BL | spi | before |
| 85 | PD3 | VCS10 | laser | v012 |
| 86 | PD4 | VCS11 | laser | v012 |
| 87 | PD5 | VCS12 | laser | v012 |
| 88 | PD6 | — spare | spare | spare |
| 89 | PD7 | — spare | spare | spare |
| 90 | PB3 | TFT_SCK | spi | before |
| 91 | PB4 | UCPD_CC2 | usb | before |
| 92 | PB5 | TFT_MOSI | spi | before |
| 93 | PB6 | UCPD_CC1 | usb | before |
| 94 | PB7 | RISLEY2 | risley | v012 |
| 95 | PB8 | BOOT0 | boot | before |
| 96 | PB9 | RISLEY1 | risley | v012 |
| 97 | PE0 | CAN_RS | can | before |
| 98 | PE1 | VIOLET_EN | violet | before |
| 99 | VSS | GND | power | before |
| 100 | VDD | +3V3 | power | before |

Before: **62**. This round: **19**. Spare: **5**. I/O total: **86**.

## Open, re-check when the other rounds land

- `sub/case-v01` is not on the remote. The scanner VCSEL is at board (8, 110), the bottom end. Move it when the case scan position exists.
- The base cradle is glued to the PCB front. Locating features are two NPTH holes, one round and one slot along the radius, not screws. Assembly `fee6c60` still exports `cad_constraints.json` as v0.16b and does not list `peg_xy` / `peg_d` / `peg_slot` yet, so the holes are not drilled. They are read from that file when the keys appear. Cradle keep-out is still v0.16b. The Fab circle is Ø41.65 from `00502746`. The ring gear moving inward will change both.
- The clear bottom thrust race gets its own locating pins: one round NPTH and one slot, drilled beside the cradle pins. Assembly `fee6c60` does not export them yet (`thrust_pegs` or `thrust_xy` / `thrust_d` / `thrust_slot`). When it does, the ring placer treats them as obstacles and each hole gets a 0.8 mm keep-out with no tracks, vias, pads, or parts. Re-run DRC after that export.
- The cradle later grows into a glued stiffener over as much of the PCB front as it can. New electronics are on the back. Tall front-side parts that a full-front plate cannot cover:
  - J2 and J3, 11 mm joystick sockets, with the four M2 studs H10–H13, clustered at board y 12–21. They have to stay there to mate with the daughterboard.
  - M1, the 1220, body in the cradle bore at (36.0, 52.9). H1, the brass tube, at the dial axis. H2, the F682ZZ flange, at (25.25, 68.15).
  - The 24 ring emitters are only 0.8 mm tall, but they have to stay in the clear-carrier window. A solid plate over them blocks the beams.
  - LD13, the scanner VCSEL, is 0.8 mm at (8, 110). A stiffener over that corner blocks the scan.
  - Hall sensors U11–U15 are on the front and under 1.2 mm, already in the cradle Hall slot.
  - J13 and J14 are flat pad rows on the front (y 28.2 and the right edge at y 46). They are not tall. A plate glued over them covers the solder joints. A connector body fitted later would stand proud.
- Joystick holes are from `bce854b` REPORT.md, not from a regenerated main-board file (that agent did not edit this PCB).
- Ring centres at the bottom (about y 70.5–70.9) cross the 2.0" TFT outline (y 70.5) by about 2 mm. That is the inactive top border of the TFT in the panel notes. Confirm before the glass is ordered.
- No Risley or mirror motor is specified in the repo. Drivers are unidirectional AO3400A low-side PWM from +5 V. Reverse the leads if the prism must spin the other way. A geared 1220-class part will not fit; these assume a small coreless, stall under 300 mA.
- STM32G474VET6 LCSC C431632 had 0 stock on 1 Nov 2026. No other LQFP100 VET6 bin was found. PCBWay has to consign it.
- Dial-screen QSPI is not on this MCU. Top screen QSPI and the bottom TFT SPI come out to pad rows, because the FPC drawings are still open.
