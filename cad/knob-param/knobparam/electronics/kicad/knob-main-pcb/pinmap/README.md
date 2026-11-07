# H7B0 pin maps (main-board pass step 1, 7 Nov 2026)

Solved by `tools/main_board_pinmap.py` (Google OR-Tools CP-SAT, Apache-2.0) from ST's STM32_open_pin_data
(BSD-3-Clause, (c) 2020 STMicroelectronics, commit 7d1f1514ed5583ec5007ad91236b4e1d377295b1). Pin names, positions and signal
names here are derived from that data [S]; ST's files themselves are not in this repo.

- `h7b0-lqfp100-shared.*`: Q32 second round A. The joystick screen and the flash share Octo-SPI port 1; a 74LVC1G19 steers the
  chip select (FLASH_SEL). Recommended. 74 nets, 8 spare.
- `u5a5-lqfp100-mux.*`: Q32 second round B. STM32U5A5VJT6, Octo-SPI multiplexed mode (port 2 NCS for the flash). 74 nets, 8 spare.

The first-round maps (screen or flash alone on the port) are in git history (de1e376). Q32 picks one
(`docs/main-board-signals-2026-11-07.md`). Not placement-aware yet.
