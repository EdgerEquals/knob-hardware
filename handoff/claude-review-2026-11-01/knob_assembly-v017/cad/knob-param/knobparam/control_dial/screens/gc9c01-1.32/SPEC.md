# 1.32" round IPS TFT, GC9C01, 360x360 — bare panel

Status: research spec for build123d. No CAD drawn yet. Candidate "next size up" from the 1.28" GC9A01.
Legend: **S** = sourced (cited drawing/datasheet/listing), **[A]** = assumed / scaled off a not-to-scale drawing.

## Sources
1. Osptek (Shenzhen Osprey) **YDP132H002-V3** spec + 1:1 mechanical drawing (rev B, 2022-04-07). QSPI, 24-pin board-to-board FPC.
   https://admin.osptek.com/uploads/YDP_132_H002_V3_e9bc0e8a53.pdf  (200 OK via curl; local copy `ref/YDP132H002-V3.pdf`)
2. Ronbo **RB0132Y1201A** listing: SPI, **12 pin @ 0.7 mm, FPC soldering type, 10.0 mm FPC length**, 35.98 × 38.49/38.54 × 1.56/1.6
   https://ronboelectronics.en.made-in-china.com/product/IUgrHDZAORkP/China-1-32-Inch-Qspi-Interface-Round-Screen-Resolution-360X360-Gc9c01-Driver-Round-Screen.html
   (page lists interface as "SPI" in the spec table but "QSPI" in the range table: confirm before ordering)
3. Chance Display **W132C002-A**: 4-wire SPI, 35.98 × 38.49 × 1.59, 24-pin pinout published
   https://chance-display.com/product/1-32-inch-360360-gc9c01-driver-ic-ips-round-tft-lcd-display/
4. Huaxianjing **TFT132H001**: GC9C01, SPI4W, 35.98 × 38.54 × 1.56 https://huaxianjinglcd.com/pages/product-list
5. Youritech **ET013CR02-H**: SPI, 35.88 × 38.44 https://www.youritech.com/products/1-32-inch-circular-display-360x360-spi-ips-round-lcd-display-for-wearable.html
6. Toppop **TT132TFN21A**: QSPI, 21-pin plug-in FPC https://www.toppoplcd.com/productdetails_5636713.html
7. GC9C01 driver datasheet V1.1 https://admin.osptek.com/uploads/GC_9_C01_Data_Sheet_V1_1_20201109_1_eec08fbd0f.pdf

Reference crops in `ref/`: drawing_front_tail_unfolded.png, drawing_tail_folded.png, drawing_chin_detail.png.
NOTE: the PDF render is stretched ~7% vertically (horizontal 35.68 vs vertical 38.44 scale). Use the numbers, not the pixels.

## Coordinate frame (proposed, same as gc9a01-1.28)
- Origin = centre of active area, on the FRONT face of the polarizer. +Z toward viewer, panel body in −Z.
- +Y = away from the FPC tail ("top"). Chin and tail at −Y.

## Outline (plan view)
| Item | Value | Src |
|---|---|---|
| LCM width (X), = round OD | 35.88 ±0.1 (drawing) / 35.98 (feature tables, Ronbo, Chance, Toppop) | S (1–6) |
| → design envelope OD | **35.98** | S |
| LCM height (Y), circle + chin | 38.44 ±0.1 (drawing) / 38.49 (Chance, Ronbo) / 38.54 (tables) | S |
| → design envelope height | **38.54** | S |
| TFT glass | 35.68 (X) × 38.23 (Y) | S (1) |
| CF glass | Ø35.68 | S (1) |
| Polarizer | 35.28 ±0.2 (X) × 35.18 ±0.2 (Y) | S (1) |
| Active area | **Ø33.48** | S |
| AA edge to LCM top / to LCM sides | 1.20 / 1.20 | S (1) |
| → AA centre to LCM top | 1.20 + 16.74 = **17.94** → round outline concentric with AA | S (derived) |
| Chin: LCM chin edge below AA centre | 38.44 − 17.94 = **20.50** (20.55 for 38.54 envelope) | S (derived) |
| Chin height beyond round outline | 38.44 − 35.88 = **2.56** | S (derived) |
| Chin shape | glass continues as a shallow arc past the Ø35.88 circle, cut by a straight FPC-bond edge; GC9C01 COG on the ledge, 2 silver-paste dots at the ends | S (drawing) |
| Chin straight-edge width | ≈ 11–12 [A] (scaled) | [A] |
| Chin corner radius from AA centre | ≈ √(6² + 20.5²) ≈ 21.4 [A] | [A] |
| Pixel pitch | 0.093 × 0.093 (360 × 0.093 = 33.48) | S |

The chin is rigid glass (COG ledge with the driver IC). It **cannot fold**. Only the FPC tail folds.

## Thickness (side view)
| Item | Value | Src |
|---|---|---|
| Module | **1.56 ±0.1** (Osptek) / 1.59 (Chance) / 1.6 (Ronbo table) → design 1.66 max | S |
| Protective tape on front (remove) | ≤0.15 | S (1) |
| FPC bend bulge above backlight frame at solder/LED-wire zone | H ≤0.45 | S (1) |
| Component zone on folded FPC | T = 0.7 +0.05 | S (1) |
| Steel stiffener (BTB variant) | T = 0.2, grounded | S (1) |
| Back envelope with tail folded | 1.56 + ~0.7 ≈ 2.3 [A] (12-pin solder variant not drawn) | [A] |

## Backlight backing
- **2 white LEDs in parallel**, If 40 mA, Vf 2.8–3.0 V (Osptek) / 3.2 V (Ronbo). S
- No mounting holes or tabs on the drawing. Mount by adhesive or by clamping the glass rim. S (none drawn)
- Vendor note "请注意机壳避空": keep housing clear of the FPC bend. S (1)

## FPC tail
| Item | Value | Src |
|---|---|---|
| Exit position | centre of the chin edge, on the Y axis | S (1) |
| **12-pin solder variant (Ronbo RB0132Y1201A)** | 12 pins @ 0.70, soldering type, **FPC length 10.0** | S (2) |
| 12-pin variant: width, pad size, fold height, pinout | not published | [A] → assume same as 1.28" (11.4 wide, 0.35 × 2.0 pads) until datasheet |
| 24-pin BTB variant (Osptek): unfolded length beyond chin edge | 25.84 ±0.3 | S (1) |
| 24-pin BTB variant: folded, connector end above chin edge | 23.85 ±0.5 | S (1) |
| Bend protrusion beyond chin edge when folded | **≤0.75** | S (1) |
| BTB connector | OK-14GM024-04 (24 pin) | S (1) |

Osptek 24-pin pinout (QSPI): 1 RST, 2 GND, 3 TE, 4 CS, 5 CLK, 6 SIO1, 7 SIO0, 8 GND, 9–10 NC, 11–12 LEDA, 13–14 LEDK, 15 VDD, 16–20 TP (unused), 21 GND, 22 SIO3, 23 SIO2, 24 NC. S (1)
Chance W132C002-A 24-pin pinout (4-wire SPI): 1–2 LEDK, 3–4 GND, 5 RS(D/C), 6 SDA, 7 SDO, 8 SCL, 9 CS, 10 RESET, 11–12 VDDIO, 13–14 VDD, 15–16 GND, 17–21 TP, 22 NC, 23–24 LEDA. S (3)

## Electrical
| Item | Value | Src |
|---|---|---|
| Driver | GalaxyCore **GC9C01** (COG) | S |
| Driver interfaces | 3/4-line SPI, 2-lane SPI, QSPI, 8080 MCU, RGB, MIPI 1-lane; selected by IM[4:0] **strapped on the panel FPC**, so the interface is fixed per part number | S (7) |
| Panel interface | 4-wire SPI (Chance W132C002-A, Huaxianjing TFT132H001, Youritech ET013CR02-H); QSPI (Osptek, Toppop); Ronbo 12-pin listing ambiguous | S |
| VDD / VDDI | 2.5–3.3 V / 1.65–3.3 V | S (1,7) |
| Colour | 262K over SPI; 16.7M with dither on QSPI only | S (7) |
| Frame bandwidth | 360×360×16 bit = 2.07 Mbit/frame → ~19 fps @40 MHz SPI, ~38 fps @80 MHz (2.25× the 1.28" GC9A01's 0.92 Mbit) | derived |

## Price (Oct 2026, bare panel)
- Ronbo RB0132Y1201A (12-pin solder): US$2.50 (2–99), US$2.20 (100–999), US$2.00 (1000+). S (2)
- Toppop TT132TFN21A (QSPI): US$3.40. https://www.alibaba.com/product-detail/In-Stock-Cheap-round-lcd-display_1600450589615.html
- MKTechnic 1.32" GC9C01, 12-pin 0.7 mm (listed as "MIPI", likely mislabelled): US$3.99. https://mktechnic.com/product/ips-lcd-tft-circular-mipi-1-32-inch-360x360-display-module/
- Taobao 中景园 (ZJY) 1.32" GC9C01 MIPI/QSPI: ¥16.40 (≈US$2.30). https://www.taobao.com/list/item/blVZbnA4d0JwcjlsTU5BekdHckpZUT09.htm

## Fit in the Ø39.5 knob (v0.12)
- Round part: Ø35.98 → **1.76 mm lip per side** (1.81 using the drawing's 35.88). Under the Ø37.5 limit by 1.52. **Fits.**
- Chin: edge 20.50–20.55 from AA centre vs knob radius 19.75 → **pokes 0.75–0.80 past the knob OD on the centreline**, ≈1.6 at the corners [A].
- Same issue exists for the 1.28" GC9A01 (chin edge 19.94–20.30 → 0.19–0.55 past on the centreline, ≈1.5 at the corners [A]). The chin was not yet modelled in v0.12.
