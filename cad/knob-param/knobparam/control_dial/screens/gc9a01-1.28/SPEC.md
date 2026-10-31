# 1.28" round TFT, GC9A01, 240x240 — bare panel (12-pin solder FPC)

Status: research spec for build123d. No CAD drawn yet.
Legend: **S** = sourced (cited drawing/datasheet), **[A]** = assumed / scaled off a not-to-scale drawing.

## Sources
1. EastRising / Buydisplay **ER-TFT1.28-1** datasheet (rev Dec-2019, drawing ER-TFT1.28-A1 Feb-2025)
   https://www.buydisplay.com/download/manual/ER-TFT1.28-1_Datasheet.pdf  (resolves in browser/WebFetch; blocks curl with 403)
2. Generic 1.28" GC9A01 module spec with full mechanical drawing (same panel family as LH128R-IG01, sold on AliExpress), hosted by Electrokit
   https://www.electrokit.com/upload/quick/d8/f0/de53_1.28_LCD.pdf  (200 OK; local copy in ref/)
3. LH128R-IG01 spec (lcddisplay.co) — same numbers: 35.6 x 38.1 x 1.5, tail fold 10.24±0.5, bend ≤0.45/0.50
   https://lcddisplay.co/wp-content/uploads/2023/02/1.28-LCD-spec.pdf (bot-protected; content seen via search index)
4. Shineworld LH128R-IF04 (ZIF variant, 15-pin 0.3 mm) https://swicn.com/products/color-tft
5. Retail bare panel listings: https://electropeak.com/1-28-inch-spi-tft-lcd-with-gc9a01-driver (US$2.75),
   https://www.icshop.com.tw/products/368030101119 (12P 0.7 mm solder, 3.3 V, 20 mA)

Reference crops in `ref/`: drawing_front_tail_unfolded.png, drawing_back_tail_folded.png, drawing_fpc_detail.png.
NOTE: the vendor drawings are marked N.T.S. and the PDF is stretched ~8% vertically — use the numbers, not the pixels.

## Coordinate frame (proposed)
- Origin = centre of active area, on the FRONT face of the polarizer. +Z toward viewer, panel body in −Z.
- +Y = away from the FPC tail ("top"). Tail exits at −Y.
- Knob convention: put tail at whichever angle the assembly wants; panel is symmetric about the Y axis.

## Outline (plan view)
| Item | Value | Src |
|---|---|---|
| LCM width (X), = round OD | 35.60 ±0.1 | S (1,2) |
| LCM height (Y), circle + bottom "chin" (COG ledge) | 37.74 ±0.1 (EK) / 37.80 ±0.1 (ER) / 38.10 (LH128R BL) | S |
| → design envelope height | **38.10** (use max) | S/[A] |
| LCD glass | 35.20 ±0.15 (X) × 37.24 ±0.15 (Y) | S (1,2) |
| Polarizer | 34.74 ±0.2 (X) × 34.32 ±0.2 (Y) | S (1,2) |
| Visual area | Ø33.4 (ER) — recommended bezel window Ø33.0 (AA +0.3/side) | S (1,3) |
| Active area | **Ø32.40** | S |
| AA top edge below LCM top | 1.60 ; AA centred in X (1.60 each side) | S (1,2) |
| → AA centre to LCM top | 17.80 → round outline is Ø35.6 concentric with AA | S (derived) |
| Chin: LCM bottom flat below AA centre | 37.74−17.80 = **19.94** (use 20.30 for 38.10 envelope) | S (derived) |
| Chin bottom flat width | ≈15 [A] (scaled) | [A] |
| Chin flanks | straight chamfers tangent-ish to the Ø35.6 circle, meeting bottom flat; ~45–55° [A] | [A] |
| Dot pitch | 0.135 × 0.135 (240 × 0.135 = 32.4) | S |

Build hint: `Circle(17.8)` ∪ trapezoid (top width = chord of circle at y≈−14 [A], bottom width 15 [A], bottom at y=−19.94), all extruded.

## Thickness (side view)
| Item | Value | Src |
|---|---|---|
| Module (pol face to backlight back) | **1.55 ±0.1** (ER/EK); vendors round to 1.5 | S |
| Protective tape on front (remove) | ≤0.15 | S |
| FPC thickness | 0.13 ±0.03 | S |
| FPC bend bulge above backlight frame at LED/wire zone | H ≤0.45 (LH128R) | S |
| Glass stack / backlight split | ~0.6 glass+pol / ~0.95 backlight [A] | [A] |
| Folded tail on back incl. 2 small caps on FPC | +0.13 FPC, caps ~0.5 tall [A] → **back envelope 1.55+0.7 ≈ 2.3** [A] | [A] |

## Backlight backing
- Edge-lit, **2 white LEDs in parallel** at the chin (bottom) end. S
- Back is a flat sheet (white/silver reflector tape over a thin plastic frame) following the same outline as the LCM: Ø35.6 round + chin. S (drawing back view) / material [A]
- No mounting holes or tabs: mount by adhesive tape on the back or by clamping the glass rim. S (none on drawing)
- Keep ≥0.5 clearance around the FPC bend at the chin (vendor note "please avoid housing"). S (3)

## FPC tail
| Item | Value | Src |
|---|---|---|
| Exit position | Centre of the chin (bottom flat), on Y axis, from the glass COG ledge | S |
| Width | **11.4 ±0.2** | S |
| Length unfolded, beyond LCM bottom edge | **12.24 ±0.3** (ER) / 12.60 ±0.3 (EK) | S |
| Pin count / pitch | **12 pins @ 0.70**, span 0.7×11 = 7.70 | S |
| Pad width / length | 0.35 / 2.00 ±0.2 | S |
| Connector type | **Solder ("hollow-out" open-window pads)**, no ZIF | S |
| Tooling holes | 2 × Ø1.0 ±0.05, 10.00 apart, ~1.0 from tail edge, just above pads | S |
| Stiffener / pad zone | 1.70 ±0.2 [S, ER] ; single-side bend zone 2.00 (LH128R) | S |
| Normal install | Tail folded 180° behind backlight. Pad row end then lies **10.24 ±0.5 (ER) / 9.88 ±0.5 (EK)** above LCM bottom edge, pads facing away from the panel | S |
| Bend protrusion below LCM bottom when folded | **≤0.50 (ER) / ≤0.86 max (EK)** | S |

Pinout (pin 1 → 12): GND, LEDK, LEDA, VDD, GND, GND, D/C, CS, SCL, SDA, RESET, GND. S (1,2)

## Variants / short tail
- The 12-pin solder version above **is the short-tail part**: folded, it adds only ≤0.5–0.86 mm beyond the outline. S
- Plug-in (ZIF) variants exist with longer tails: Buydisplay ER-TFT1.28-3 (35.59 × 37.74 × 1.6, plug-in FPC, 15 pin 0.5 mm ZIF offered, optional CTP) and Shineworld LH128R-IF04 (15 pin 0.3 mm). Tail lengths not published on product pages. S (variant exists) / length unknown.

## Electrical
| Item | Value | Src |
|---|---|---|
| Interface | 4-wire SPI (SCL, SDA, CS, D/C) + RESET; read-back via SDA (3-wire bidir) | S |
| VDD | 2.5 – 3.3 V (typ 2.8 ER; vendors sell as 3.3 V); abs max 4.6 V | S |
| IDD (logic) | 8.5 typ / 10.5 max mA; sleep 15–30 µA | S (1) |
| Backlight | 2 LEDs parallel, Vf 2.9–3.1 V, **If 30 mA typ / 40 mA max** (no on-panel resistor → current limit/PWM on host) | S (1,2) |

## Price (Oct 2026, bare panel)
- Electropeak: US$2.75 (1 pc), US$2.44 @1000
- Buydisplay ER-TFT1.28-1: US$5.61; ER-TFT1.28-3 (plug-in): US$4.67
- AliExpress/Taobao: ≈ ¥12.5 (≈US$1.75) to ≈US$6 depending on seller
