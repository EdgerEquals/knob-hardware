# Main board: signal plan and H7B0 pin map (7 Nov 2026, main-board pass step 1)

Tags: [S] source read, [A] estimate or my choice, [C] open check, [Ed] Ed's decision. Replaces the budget in
`docs/pcb-h7b0-plan-2026-11-02.md` (that file stays as the record of the 2 Nov plan).

Picture: `docs/img/qspi-port-choice-q32.png`.

## Sources and tools
- ST's pin data: **STM32_open_pin_data** (github.com/STMicroelectronics/STM32_open_pin_data, BSD-3-Clause, (c) 2020
  STMicroelectronics), commit 7d1f1514ed5583ec5007ad91236b4e1d377295b1, files `mcu/STM32H7B0VBTx.xml` (LQFP100) and
  `mcu/STM32H7B0ZBTx.xml` (LQFP144). Not copied into this repo; the pin maps below are derived from it [S].
- Solver: `tools/main_board_pinmap.py`, Google OR-Tools CP-SAT (Apache-2.0). Every net gets one pin that offers its function,
  one net per pin, one pin per peripheral signal, each SPI / I2C / UART / FDCAN / timer serves one group, and the interrupt inputs
  sit on different EXTI lines. Two pin rules on top [A]: PC13-PC15 (backup domain, 3 mA, 2 MHz) take only slow inputs, and the
  ADC-switch pads (PC2_C, PC3_C) take only analog or slow GPIO.
  `python3 tools/main_board_pinmap.py <STM32_open_pin_data> [--profile lqfp100|lqfp100-flashquad|lqfp144 --part ...]`
- Outputs: `cad/knob-param/knobparam/electronics/kicad/knob-main-pcb/pinmap/h7b0-lqfp100-q32A.{json,txt}` and `...-q32B.*`.
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
4. **Both ways round fit on the LQFP100: 77 nets on 82 I/O pins, 5 spare.** Tight. Relief valve if more pins are needed later:
   a 16-bit I2C expander on the existing bus for the slow enables and resets (about 10 pins back).

## Q32: who gets the quad port (open, for Ed)
| | A (recommended) | B |
|---|---|---|
| Quad port | joystick screen | flash |
| Joystick screen | QSPI as its jumper is drawn now; full 456 x 280 frame about **98 / s** at 50 MHz [S: CO5300 write clock >= 20 ns] | 1-bit SPI: about **24 / s**; the jumper changes (mode straps to 4-wire SPI, a D/C line) |
| Flash | 1-bit SPI on SPI1-3: about 6-10 MB/s at 50-80 MHz [A], a screen-sized frame (255 KB) 24-39 times a second | memory-mapped quad: about 4x that |
| Program | a small loader in the H7B0's own 128 KB flash copies the main program from the flash into RAM at power-up (about 0.05 s for 0.5 MB) [A] | runs straight from the flash, no 128 KB limit |
| Pins | 77 used, 5 spare | 77 used, 5 spare |

Numbers: 456 x 280 x 16 bit = 2.04 Mbit a frame; quad at 50 MHz = 200 Mbit/s; 1-bit at 50 MHz = 50 Mbit/s.

## Signal list (77 nets, map A)
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
- 5 spare pins of 82.
- The back AMOLEDs on 1-bit SPI at 50 MHz: 450 x 600 x 16 bit = 4.32 Mbit, so about **12 full frames / s** each. Fine for a UI
  that redraws what changes; not for full-screen video. Nothing faster is free on the LQFP100 (the FMC bus needs 16 pins) [A].
- The LQFP100's land is 0.5 mm from the joystick's holes (finding 2).
