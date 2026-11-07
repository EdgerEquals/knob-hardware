# Main board: signal plan and H7B0 pin map (7 Nov 2026, main-board pass step 1)

Tags: [S] source read, [A] estimate or my choice, [C] open check, [Ed] Ed's decision. Replaces the budget in
`docs/pcb-h7b0-plan-2026-11-02.md` (that file stays as the record of the 2 Nov plan).

Pictures: `docs/img/qspi-port-choice-q32.png` (first round), `docs/img/qspi-shared-bus-q32.png` (second round).

## Sources and tools
- ST's pin data: **STM32_open_pin_data** (github.com/STMicroelectronics/STM32_open_pin_data, BSD-3-Clause, (c) 2020
  STMicroelectronics), commit 7d1f1514ed5583ec5007ad91236b4e1d377295b1, files `mcu/STM32H7B0VBTx.xml` (LQFP100) and
  `mcu/STM32H7B0ZBTx.xml` (LQFP144). Not copied into this repo; the pin maps below are derived from it [S].
- Solver: `tools/main_board_pinmap.py`, Google OR-Tools CP-SAT (Apache-2.0). Every net gets one pin that offers its function,
  one net per pin, one pin per peripheral signal, each SPI / I2C / UART / FDCAN / timer serves one group, and the interrupt inputs
  sit on different EXTI lines. Two pin rules on top [A]: PC13-PC15 (backup domain, 3 mA, 2 MHz) take only slow inputs, and the
  ADC-switch pads (PC2_C, PC3_C) take only analog or slow GPIO.
  `python3 tools/main_board_pinmap.py <STM32_open_pin_data> [--profile lqfp100|lqfp100-flashquad|lqfp144 --part ...]`
- Outputs: `cad/knob-param/knobparam/electronics/kicad/knob-main-pcb/pinmap/h7b0-lqfp100-shared.{json,txt}` (Q32 second round A)
  and `u5a5-lqfp100-mux.*` (B). The first-round maps (screen or flash on the port) are in git history (de1e376).
  Not placement-aware yet: re-solved with pin preferences once the chip's neighbours are placed (step 3).

## Findings
1. **The LQFP100 has one fast quad port.** The H7B0 has two Octo-SPI controllers, but on LQFP100 only port 1's pins are bonded
   out (CLK, NCS, IO0-7, DQS, NCLK; no port 2 pins at all) [S]. One port = one clock and one chip select, so **one quad device**:
   the joystick screen or the flash, not both. The 2 Nov plan assumed both [corrected here].
2. **The LQFP144 (two ports, 114 I/O) does not fit.** Its land is 23.2 mm square; centred where the MCU sits (0, 37) it overlaps
   the board's top edge, the joystick's screw and spring holes and the top of the window. The LQFP100's land clears the nearest
   cut-out by **0.5 mm** (tight; its 1 mm courtyard touches the joystick holes, so the fan-out on those sides is checked in step 3).
3. Not offered: the BGA versions (UFBGA169, 7 x 7, 0.5 mm pitch; UFBGA176, 10 x 10, 0.65 mm). They fit and have both ports,
   but need finer board rules (microvias at 0.5 mm) and X-ray inspection at assembly.
4. **Both ways round fit on the LQFP100: 77 nets on 82 I/O pins, 5 spare.** Tight. With the shared port (second round): 74 nets,
   8 spare. Relief valve if more pins are needed later: a 16-bit I2C expander on the existing bus for the slow enables and resets
   (about 10 pins back).

## Q32, first round: who gets the quad port
A: the screen (flash on 1-bit SPI, 6-10 MB/s); B: the flash (screen on 1-bit SPI, 24 frames / s). 77 nets, 5 spare.
[Ed 7 Nov 19:11] not this compromise: find the workaround, more board room if needed.

## Q32, second round: share the port (open, for Ed)
The screen and the flash share the port's clock and four data lines and take turns; only the chip selects are separate, so one
listens at a time. Both get full quad speed. No board room needed.

| | A (recommended) | B |
|---|---|---|
| Chip | STM32H7B0VBT6 as now (LCSC C730227, US$5.38, 916 in stock, 7 Nov [S]) | STM32U5A5VJT6, same LQFP100 footprint; price, stock [C] |
| How the port is shared | one Octo-SPI controller; its chip select through a **74LVC1G19** (1-of-2 selector, 6 pins, 1.8 ns [S Nexperia]), a spare pin picks screen or flash | two controllers in ST's **multiplexed mode**: CLK / IO shared, port 1 NCS to the screen, port 2 NCS to the flash (needs both NCS pins [S ST forum]; LQFP100 bonds out port 2 NCS [S pin data]) |
| Program | small loader in the 128 KB copies it from the flash into RAM at power-up (about 0.01 s at quad speed) [A] | 4 MB flash on the chip, runs in place; 2.5 MB RAM |
| Core | Cortex-M7, 280 MHz | Cortex-M33, 160 MHz |
| SPI ports | 6 (3 used after this) | 3 (3 used: exactly enough) |
| Pins | 74 nets, **8 spare** | 74 nets, **8 spare** |

Speed (same either way): a full 456 x 280 frame (255 KB) from the flash to the joystick screen = read 6.4 ms (quad, 80 MHz [A])
+ write 10.2 ms (quad, 50 MHz) = 16.6 ms, **about 60 full frames / s** (first round: 24-39). Redraws from RAM: about 98 / s.

Said plainly for A: the shared lines branch to the flash and to the joystick jumper. The flash sits right by the MCU, series
resistors at the MCU, the flash run at 50-80 MHz to start (it can go to about 133) [A]. The screen and flash both release their
data lines when not selected [A, check both datasheets in step 2 [C]].

Considered and dropped: the LQFP144 (no room, first round); the STM32H7A3VIT6 (pin-identical to the H7B0 by ST's pin data, 2 MB
flash, but US$25.62 with 4 in stock at LCSC (C730222), 7 Nov [S]); a BGA (not needed now).

Later, if DisplayModule's tail pin list shows the back AMOLEDs' QSPI pins: the same trick with a 1-of-4 selector could put them on
the shared lines too (up to about 46 full frames / s each when the bus is theirs, against about 12 on their own SPI) [A][C].

## Signal list (first round, 77 nets; second round: the flash's SPI and CS become one select pin, 74 nets)
| Group | Nets | Pins | Notes |
|---|---|---|---|
| Joystick screen (CO5300) | QSPI CLK, NCS, IO0-3 (port 1); RST, TE, PWR_EN | 9 | [S] screens doc; jumper 13 lines |
| Flash (NOR, animations + program) | SCK, MOSI, MISO (SPI1-3), CS | 4 | part open [C] |
| Back AMOLEDs x2 (RM690B0) | per screen SCK, MOSI (own SPI), CS, D/C, TE; shared RESX, power enable | 12 | 4-wire SPI [A] until DisplayModule's tail pin list [C] |
| Link flex SPI | SCK, MOSI, CS_DAC, CS_OLED, OLED_DC, OLED_RES | 6 | DAC80504 + clear OLED on the jack lower board |
| I2C | SCL, SDA; IO_INT, HALL3D_INT | 4 | TMAG5273 here; TCA9535 on the jack unit over the link; one bus [A] |
| MIDI out | UART TX | 1 | link flex |
| Dial link | half-duplex UART TX on VBUS | 1 | [A] |
| USB | DM, DP (PA11 / PA12, internal FS PHY) | 2 | link flex |
| CAN | FDCAN TX, RX; STBY | 3 | transceiver on vertical board R |
| Analog in | CV_IN1-3, AUDIO_IN, HALL1/2/4/5, MOT_SENSE, MOT_VOICE, NTC, JOY_LADDER | 12 | ADC1 / ADC2 |
| Audio out | DAC1_OUT1 | 1 | link flex |
| Encoder (EE-SX1321, two channels) | ENC_A, ENC_B (timer CH1 / CH2) | 2 | |
| 1220 driver | IN1, IN2 (one timer), nSLEEP; HALL_EN | 4 | driver part open (expected decision) |
| VCSELs x12 | decoder A0-A3, LASER_EN (PWM) | 5 | one at a time by hardware |
| RGB ring | DIN (timer + DMA), RGB_EN; VIOLET_EN | 3 | |
| Risley motors x2 | PWM x2 (one timer) | 2 | reserved [A] |
| 15 V present | BUS_PRESENT | 1 | |
| Clock, debug | HSE in / out; SWDIO, SWCLK, SWO | 5 | |
| **Total** | | **77** | of 82 I/O |

Changes from 2 Nov: no FMC 8080 bus (the back AMOLEDs on SPI, the clear OLED on the link SPI), no 716 (Q27), no PD sink pins
(on the jack power board), CV outs through the DAC80504 on the link, USB data, MIDI and three CV ins added, the flash on SPI
(finding 1).

## Tight, said plainly
- 5 spare pins of 82 in the first round; 8 with the shared port.
- The back AMOLEDs on 1-bit SPI at 50 MHz: 450 x 600 x 16 bit = 4.32 Mbit, so about **12 full frames / s** each. Fine for a UI
  that redraws what changes; not for full-screen video. Nothing faster is free on the LQFP100 (the FMC bus needs 16 pins) [A].
- The LQFP100's land is 0.5 mm from the joystick's holes (finding 2).
