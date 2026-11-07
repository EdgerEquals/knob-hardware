# H7B0 pin maps (main-board pass step 1, 7 Nov 2026)

Solved by `tools/main_board_pinmap.py` (Google OR-Tools CP-SAT, Apache-2.0) from ST's STM32_open_pin_data
(BSD-3-Clause, (c) 2020 STMicroelectronics, commit 7d1f1514ed5583ec5007ad91236b4e1d377295b1). Pin names, positions and signal
names here are derived from that data [S]; ST's files themselves are not in this repo.

- `h7b0-lqfp100-q32A.*`: the joystick screen on the quad port (Octo-SPI port 1), the flash on SPI. Recommended.
- `h7b0-lqfp100-q32B.*`: the flash on the quad port, the joystick screen on 4-wire SPI.

Q32 picks one (`docs/main-board-signals-2026-11-07.md`). Not placement-aware yet.
