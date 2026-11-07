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

## Second look: take things out instead (7 Nov, after [Ed 19:29])
[Ed 19:29] "It's still a compromise. We keep adding things. Maybe there's a way we can remove things and get it done."
Picture: `docs/img/subtraction-q33.png`.

Every round so far added parts (a selector, then two screen chips). What forces the additions is one item: **the two back
screens**. They are the second and third colour screens on the main chip, they need their own power chips and two connectors, the
lower one's lines run through the tightest channel on the board (the 2.3 mm strips beside D), and their flex pin-out is still
unknown (DisplayModule silent since 2 Nov). On 3 Nov they were "aesthetics, can come later" [Ed 11:37], on their own cover board.

**Subtract:**
- **Back screens off the first build**, back to the 3 Nov plan: a cover board with its own chip, later. The model keeps them as
  "later" parts; no geometry changes. The main board keeps 3 pins (a UART and an enable) and pads for that board's link.
  Out with them: their power chips, both connectors, 12 main-chip pins, their lines past window D.
- **The animation flash, the selector and the loader**: the **STM32H743VIT6** fits the same LQFP100 land and has **2 MB program
  flash, 1 MB RAM, 480 MHz** (US$7.86, 5,931 in stock at LCSC (C114409), 7 Nov [S]; the H7B0 is US$5.38). Its one quad port
  (QUADSPI) takes the joystick screen, the program and the joystick screen's pictures live in the chip.
  (The STM32H723VGT6, 1 MB, also fits but LCSC has none in stock and it costs US$13.87-17.16 [S].)
- **No extra screen chips** beyond the dial's (decided 3 Nov, fed through the rod).

Pin map (ST's pin data, `.../pinmap/h743-lqfp100-simple.*`): **64 nets of 82, 18 spare**. The same list also fits the H7B0 and
the H723 with 18 spare.

Said plainly:
- The joystick screen's quad lines still pass board R, the pins and sockets and the jumper. Ground pins sit between them in the
  sockets [A]. If the signals are marginal the clock comes down rather than the screen failing: 50 MHz is about 98 full frames a
  second, 25 MHz about 49.
- The 2 MB holds the program and drawn pictures (gauges, text, icons), not long full-screen video clips [A].
- This revises Q31 (back screens on the first board) back to the 3 Nov plan.
- The H743's power, VCAP and BOOT pins differ from the H7B0's. No schematic is drawn yet, so that costs nothing now.

**Q33, restated (open):** A, subtract (recommended); B, keep the back screens on the first build with local drawing.
