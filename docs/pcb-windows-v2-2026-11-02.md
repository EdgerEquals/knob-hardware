# PCB windows v2 (2 Nov 2026)

Tags: [Ed] Danny's decision, [A] assumption or open choice, [C] open check, [S] source read.
Branch `sub/electronics-windows-v2` from param-dev 3188b50 (v0.20). Picture: `docs/img/pcb-windows-v2.png`.

## What changed
[Ed] "these windows can be much bigger". `tools/pcb_windows.py` now cuts each window out to the real limits with a 0.5 margin
(v0.20: 1.0, knob keep-out 24.1), and electronics `pcb_windows` holds the result (`--keep 22 --margin 0.5 --web 6`):
- **Knob keep-out r 22.0.** Under it: emitter bodies on the board back reach r 21.28 (VCSEL corners; also cut as their own boxes + 0.5),
  the base cradle's bottom track r 21.26, the glass r 21.0.
- Corner posts: the cover column ring that bears on the board (r 4.55) + 0.5 (v0.20 added a further 1.0).
- Encoder daughterboard, header and standoff (pins on the main PCB): hull + 0.5 (was 1.5). Bearing 2 seat + 0.5 (inside the keep-out).
- Joystick: the printed cradle's real footprint on the PCB (ring and the two knob-side ball towers) and the geom.json `cradle_ring` and
  `main_pcb_holes`, + 0.5. v0.20 used the whole grip-block outline.
- 1.5 board rail; screen edges ±19.36. **D** = clear OLED less its 1.6 ledge [Ed], so D now reaches the screen edges (ledge 1.66 at the sides,
  1.60 at the top). **C, E** stop 0.5 short of the OLED's top edge (v0.20: 1.6).
- **A/B web [A]:** with these limits A and B would meet at x = 0 and cut the board between the knob and the joystick. A 6 mm web on x = 0
  keeps them as two windows and keeps a direct link from the knob area to the top of the board.

| window | v0.20 (mm²) | v2 (mm²) |
|---|---|---|
| A (rear AMOLED, left of the knob top) | 71.7 | 202.8 |
| B (rear AMOLED, right, round the encoder board) | 22.3 | 159.1 |
| C (front AMOLED, right of the knob bottom) | 11.6 | 45.1 |
| D (under the clear OLED) | 900.8 | 917.5 |
| E (front AMOLED, left) | 11.6 | 45.2 |

Trade-off (6 mm web), `pcb_windows.py --table`:

| keep-out / margin | A | B | C | D | E | A+B+C+E |
|---|---|---|---|---|---|---|
| 24.06 / 1.0 | 152.4 | 105.0 | 15.2 | 910.2 | 15.2 | 287.9 |
| 23.0 / 1.0 | 173.1 | 125.8 | 26.3 | 917.5 | 26.3 | 351.5 |
| 22.0 / 1.0 | 187.8 | 140.5 | 35.6 | 917.5 | 35.7 | 399.5 |
| 22.0 / 0.75 | 197.6 | 152.2 | 42.0 | 917.5 | 42.0 | 433.8 |
| **22.0 / 0.5** (chosen) | 202.8 | 159.1 | 45.1 | 917.5 | 45.2 | 452.1 |
| 21.8 / 0.5 | 206.9 | 163.2 | 48.5 | 917.5 | 48.5 | 467.0 |
| 21.8 / 0.3 | 210.7 | 167.1 | 51.1 | 917.5 | 51.1 | 479.9 |

Other shapes: web 14 → A 160.8, B 116.5. A/B capped at y 26.06 (the joystick grip block's shadow) → A 128.2, B 107.3.
Seen straight on, 74 mm² of A and 51 of B sit behind the opaque grip block (PA-12).

## Routing room [A] (estimates from the model; no KiCad run)
- Board left (outline less windows and holes): **3310 → 2957 mm²** (−11%); about 1520 of it is under the knob.
- Room for parts (0.5 from a milled edge, 0.3 from holes, nothing within 1.7 mm behind or 2 mm in front): back **2206 → 1821 mm²**,
  front 1123 → 750 (the front is mostly the base cradle and the clear OLED anyway).
- Narrow strips: beside D 2.95 → 2.79 mm each (about 7 tracks per layer at 0.15/0.15), between C/E and D 3.2 → 2.1 (about 5), A/B web 6.0 (about 18;
  v0.20 had about 18 mm of board there). The bottom strip (14-way, power, PD sink) still reaches the rest of the board only past D.
- **H7B0:** an LQFP100 needs a 17.2 mm courtyard plus decoupling, about 20 mm square. The largest clear square on the board back is
  13.2 mm with the v0.20 windows, 10.3 now, and 14.0 even with no A/B. The knob mechanism and emitter ring, the joystick rear anchor
  (x ±15, y 35–46 on the back) and its sockets block it. Only D's area is big enough. So the LQFP100 had no site before this change either.
- **Proposed spot [A]:** STM32H7B0AB in **UFBGA169, 7 × 7** ([S] the H7B0 datasheet lists it) on the board back at about **(0, 27)** with a
  **14 mm A/B web** (12.7 mm clear square; A 161, B 117). It sits behind the grip block's shadow, next to the joystick sockets (QSPI) and the encoder
  header, and the bus runs down the web. [C] 0.5 mm pitch needs via-in-pad / HDI at PCBWay. [C] Redo the CubeMX pin map (more I/O than the LQFP100).
  With the 6 mm web, the only BGA spot is under the knob at about (−11, −3) (10.3 mm), beside the Hall row and the motor drivers.
- **AMOLED connectors:** a 45-pin FPC socket is about 16.5 × 4.6. With v2 there are only two places for one: the bottom strip (the 14-way and power plugs need that
  strip too) and under the knob at about (−10, −6). Capping A/B at y 26.06 adds a third place at about (−8, 29). [C] The flex exit sides are still unknown.

## Open choices for Danny [A]
1. A/B web: 6 mm (committed) or 14 mm (makes room for the H7B0 as a BGA at the top centre).
2. A/B top: at the joystick cradle (committed, per the brief) or at the grip-block shadow, y 26.06 (nothing lost seen straight on).
3. H7B0: UFBGA169 at (0, 27), or keep the LQFP100 and give it part of D.
4. Keep-out 22.0 (0.72 over the emitter bodies) or 21.8 (+15 mm²).
5. C/E to the OLED edge 0.5 (v0.20: 1.6). D out to the screen edges, ±19.36 (v0.20: ±19.2).

KiCad (later job): R20–R22 and R30–R32 still sit inside D on the stale board. The v0.16 MH1 joystick holes and FPC slot in
`pcb_proxy.json` are stale.

## Rechecked 2 Nov, 17:40, against knob v0.22b and joystick v0.6
- The windows regenerate identically (A 202.9, B 159.1, C 45.1, D 917.4, E 45.2 mm² with the 6 mm web): the cone top, split arm,
  pedestal key hole (inside the keep-out) and joystick v0.6 change nothing the windows see.
- Board back, room for the H7B0 (parts within 1.7 mm behind the PCB; 0.3 round them):
  - 6 mm web: largest clear square **10.0** at (−9.65, −7.3) (was 10.3 in v0.20; the Hall row turned 16°). UFBGA169 + caps (9 □):
    one spot, under the knob at (−7.6, −9.8). LQFP100 (17.2 □): none.
  - 14 mm web (A 160.8, B 116.5): largest square **12.7** at (−0.15, 28.2); UFBGA169 at (−1.6, 26.2) or (−7.6, −9.8);
    UFBGA176+25 + caps (12 □) at (−0.1, 27.7). LQFP100: none.
  - No A/B at all: 14.3 □; still no LQFP100. Only window D's area takes an LQFP100.
  - Picture: `docs/img/h7b0-site-options.png`.
- [S] STM32H7B0 packages: LQFP64, LQFP100, LQFP144, LQFP176, UFBGA169 (7 × 7), UFBGA176+25 (10 × 10). The UFBGA169 part
  (STM32H7B0ABI6Q) lists 121 I/O (LQFP100: 80); LCSC shows it out of stock on 2 Nov.

## [Ed 17:37] H7B0 stays LQFP100; it takes part of window D
Where in D (search: a 17.2 □ for the LQFP100 + decoupling [A] inside the free board back, 0.3 round parts, clear of the corner
columns; D keeps 0.5 round the chip). The OLED's lit area is 35.05 × 15.32, 3.0 in from the long edge away from its flex [S];
its flex is taken to leave the bottom edge [A]. Picture: `docs/img/lqfp100-in-window-d.png`.

| Chip site (centre) | D left (now 917 mm²) | See-through behind the OLED's lit area |
|---|---|---|
| A low centre (−0.15, −43.95): bottom strip + lower D | 698 | 83% |
| B low left (−12.9, −39.2): as low as the corner column allows | 656 | 75% |
| C centre, full height (two windows) | 486 | 48% |
| D left end, full height | 498 | 55% |

A and B take part of the bottom strip, where the 14-way and power plugs (and probably the clear OLED's connector) were going [C].

## [Ed 18:13] LQFP100 confirmed (stock and board cost; see the 18:12 notes); top middle of D asked about
- [S] 2 Nov: STM32H7B0VBT6 (LQFP100) 916 in stock at LCSC from US$5.38; STM32H7B0ABI6Q (UFBGA169) out of stock at LCSC, ST eStore
  lists US$12.83; STM32H7B0IBK6Q (UFBGA176+25) out of stock at the broker checked. The 0.5 mm BGA also needs via-in-pad and X-ray.
- Top middle (highest fit near x 0: chip centre (−2.0, −30.15), its top at y −21.55 under the emitter ring): D 625 mm², see-through
  behind the OLED's lit area **50%** with the OLED's flex at the bottom, **70%** with the OLED turned over (flex at the top, which then
  runs into the knob's emitter ring and cradle: no connector room there [C]). Low middle (A): 698 mm², **83%**.
  Picture: `docs/img/lqfp100-top-vs-low.png`.
