# Fresh look at the electronics: who draws the screens (7 Nov 2026)

Tags: [S] source read, [A] estimate or my choice, [C] open check, [Ed] Ed's decision.
Asked [Ed 7 Nov 19:18]: "Are we adding a band-aid? ... zoom out and have a fresh look at the whole thing objectively", with the
single-wire feed in mind. Picture: `docs/img/architecture-fresh-look.png`.

## The answer: yes, the shared port is a band-aid
The geometry is settled, so the question is only how the electronics are split. Five screens sit in four places: the dial (in the
knob, reached through the rod), the joystick (on the top board, reached through vertical board R, pins and sockets and a jumper), two
back screens (behind the main board) and the clear OLED (on the jack unit). Every place except the dial is drawn by the main chip.
That one choice is the root of all three problems the last two rounds kept running into:
- **Ports and pins:** the H7B0 on LQFP100 has one quad port (finding 1 of `docs/main-board-signals-2026-11-07.md`); three colour
  screens and an animation flash want four. The shared port fixes the count, nothing else.
- **A fast bus through three joints:** the joystick screen's QSPI (50 MHz, 9 lines) runs from the main chip through vertical
  board R, the pin-and-socket joint, the top board and the jumper.
- **The back screens are slow:** 1-bit SPI each, about 12 full frames a second, because no quad port is left for them.
- And the main chip's program would carry the graphics as well as the real-time work, in 128 KB plus a loader.

How we got here: on 3 Nov [Ed 11:37] the plan was **local drawing**: the dial draws its own pictures (ESP32-S3 in the cartridge,
fed through the rod) and a cover board draws the back screens. Q31 [Ed 7 Nov 18:58] put the back screens on the first main board,
and I read that as "the main chip draws them". That is where it drifted.

## The single-wire feed is the right pattern
The rod carries one wire with power and data (the brass tube is the return), a few Mbit/s [A, design notes]. That only works
because the dial has its own chip: the wire carries short commands ("show page 3, needle at 212°, colour ..."), not pixels.
Read as a pattern, it answers the question: **each screen place gets its own small graphics chip with its own memory, and the
main chip sends it commands over a thin link.** The rod link stays as designed.

## Proposed: one brain, local painters
- **Main chip (H7B0, as now):** real-time work only: the 1220 motor and encoder, the Hall sensors, CV and audio, MIDI, USB, the
  LED and VCSEL rings, CAN, the jack unit (clear OLED and CV DAC on the link flex, unchanged). It sends the screen chips commands.
  Pin map solved from ST's pin data: **60 nets of 82, 22 spare** (`.../pinmap/h7b0-lqfp100-local.*`). No animation flash on the
  main board, no quad port in use. Its 128 KB holds a real-time program without graphics [A].
- **Three screen chips, all the same part:** ESP32-S3-PICO-1-N8R8 (7 x 7 mm, 8 MB flash and 8 MB RAM in the package, crystal
  inside [S, layout-v4 3 Nov]). The radio is not used.
  1. **Dial:** in the cartridge, as decided 3 Nov. Fed through the rod.
  2. **Joystick:** on the top board or vertical board R [C fit]. The QSPI stays on that board and the jumper; through the joints
     go power and 2 slow UART lines.
  3. **Back screens:** one chip on the main board's back by the upper AMOLED connector [C placement], short QSPI to each panel:
     about **46 full frames a second each** if DisplayModule's tail brings out the quad lines, 12 if it is SPI only [C, no reply
     since 2 Nov]. Q31 still holds: everything on the first main board.
- **Links:** a UART each (2 lines) to the joystick and back chips, plus a reset and a boot line each so the main chip can load
  their firmware; the dial on the rod. A frame tick from the main chip keeps animations across screens in step [A].
- **Dev kits:** Waveshare's ESP32-S3-Touch-AMOLED-1.32 (ESP32-S3-PICO-1-N8R8) and -1.64 (ESP32-S3R8, `docs/datasheets` schematic)
  boards drive these exact panels [S], so the screen program can start on bought boards before our boards exist.

## What it costs, said plainly
- Two more ESP32-S3 chips and their few capacitors (price to check [C]); PCBWay places them.
- About 0.2-0.3 W per screen chip [A], so roughly 0.4-0.6 W more for the two new ones, against the 4-5 W budget.
- Two programs instead of one: the main program and one screen program shared by all three screen chips.
- The joystick chip needs room on the top board or board R [C].

## What it does not change
The geometry, the H7B0 and its place, the link flex, the jack unit, the rod link, Q27-Q31.

## Decision
**Q33 (open):** A, local drawing (recommended); B, central drawing with the shared port (Q32 second round A).
If A: Q32 falls away (no quad port in use on the main chip).
