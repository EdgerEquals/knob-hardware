# Top screen joystick

The top screen (1.14" 240×135 IPS, landscape) is also the main navigation control. It moves left, right,
up and down, and presses in.
- Press down: enter the dial's menu.
- Press up: back to the top-screen menu. Up again escapes.

## Mechanism
- **Switch:** an Alps **SKRHADE010** 5-way SMD switch on a small daughterboard, raised on risers above the main
  PCB.
  - The SKRH directions are at 45° to the body, so the **footprint is rotated 45°** to line them up with the
    screen axes.
  - **Firmware diagonals:** two directions closed together read as a diagonal. That gives 8 directions plus
    centre press.
- **Base:** a printed base glued to the main PCB, located by **4 pins**. It carries **4 hemispherical ball
  seats**.
- **Carrier:** a printed carrier riding on 4 balls in those seats. It **slides in-plane and never tilts**.
  - **4 extension springs** run through holes in the PCB to the back panel and hold the carrier down onto the
    balls.
  - The switch stem engages a cup on the back of the carrier and **centres it**. The springs supply only the
    hold-down force, not the centring.
- **Screen mount:** the screen sits on a **printed spider spring** inside the carrier, with about 0.3–0.5 mm of
  press travel. The spider only gives travel. **The switch takes the full press force**: the press goes
  through the stem, and the balls and spider never bottom out first.
- **Cable:** a hole in the carrier and base for the screen FPC, with a service loop sized for the full
  slide and press travel.

## Design notes for the cup and stem
- Use a Ø3.1–3.2 round cup over the Ø3 stem, with a lead-in chamfer and a light flat face on the stem top.
  A tight square peg in the □1.95 keytop socket would bind.
- Because the carrier slides rather than tilts, the cup moves the stem in its operating directions only.
  Nothing loads the stem sideways at rest (the datasheet warns against side force).
- The stem top is 5.0 mm above the daughterboard. Set the riser height to suit, or add a printed extender cap
  in the keytop socket instead of making the risers longer.
- The force tolerance is ±0.69 N. Buy a strip and sort them for a consistent feel.
- The spring hold-down adds to the 2.35 N centre push. Keep it light.

## Switch shortlist (researched 1 Nov 2026; recheck prices and stock before ordering)

| # | Part | Size W×D, body / stem top | Stem tilt force (switch spec) | Centre force | Travel stem tilt / centre | Life | Notes |
|---|---|---|---|---|---|---|---|
| 1 | **Alps SKRHADE010** (chosen) | 7.45×7.5, 1.85 / 5.0 | 1.2 ±0.69 N | 2.35 ±0.69 N | 0.25 / 0.15 mm | 1M per direction, 100 mΩ | Tactile in all 5 actions. Guide bosses. Ø3 stem, □1.95 keytop socket. Directions at 45°. LCSC C202415 |
| 2 | Alps SKRHACE010 | same | 1.2 N | 2.35 N | 0.25 / 0.15 | 1M | As #1 without the bosses |
| 3 | Alps SKRHABE010 | 7.35×7.5, 1.8 / 5.0 | 1.23 ±0.69 N | 2.35 ±0.69 N | 0.25 / 0.15 | 200k, 500 mΩ | **Only approved alternate** (same footprint, deep stock). LCSC C139794 |
| 4 | E-Switch JS1400BFQ | 7.4×7.7 | ~1.57 N | ~3.53 N | 5° / 0.25 | 100k | **No auto-substitute**: higher forces, land pattern unverified. Only with Ed's approval after a footprint check |
| 5 | Korean Hroparts K1-1506SN-01 | 10×10 | ~1.57 N | ~2.94 N | n/s | 100k | LCSC C145910 |
| 6 | C&K TPA511G | subminiature | 1.85 N | 4.0 N | 0.35 / 0.25 | 200k | Reported obsolete |

- **Approved for the BOM:** SKRHADE010, with **SKRHABE010 as the only approved alternate**. JS1400BFQ is marked
  "no auto-substitute" (PCBWay must not swap it in). The switch spec quotes "tilt" for the stem; the carrier itself only slides.
- **Rejected:** Alps SKRV (NRND), SKQUCAA010 (snap-in, NRND), SKQUDBE010 (old), E-Switch JS5208 (12.4 mm
  body), Swiclick KAN0741A (50k life).
- **Sources:** Alps product page and SKRH catalogue (tech.alpsalpine.com), E-Switch JS1400 datasheet, and LCSC
  product pages.

## v0.1 build (1 Nov 2026)
Model: `cad/joystick-param/` (run `build.py --render`). Image: `cad/assemblies/joystick-v0.1/joystick-v0.1.png`.
**21/22 checks PASS, 0 clashes.** The miss is the carrier against the live knob Ø41.65 (0.275 mm, target 0.5).
`place_y` is still the v0.1 value sized to Ø40.85, and the main PCB was not moved. KiCad:
`cad/knob-param/knobparam/electronics/kicad/joystick-daughterboard/` (ERC 0, DRC 0, parity 0).

The screen top is the faceplate front from the knob interface: **38.80** (`z_glass` 56.8 − `knob_proud` 18).
The J2 socket stays 8.5 mm, soldered on the PCB. A printed extender makes up the riser.

**Stack** (z measured from the main-PCB front face; the carrier centre is board (25.25, 21.1)):

| Item | z (mm) | Notes |
|---|---|---|
| J2 2×3 2.54 female socket on the main PCB | 0–8.5 | Soldered. Male J1 on the daughterboard, plastic on top and pins down |
| Printed riser extender | 8.5–27.10 | Same footprint as the socket. The v0.1 header pins do not span this gap |
| Daughterboard | 27.10–28.10 | 16.6×12.0×1.0 FR4. Rests on a Ø4 printed post under the switch, which takes the press |
| SKRHADE010 | body top 29.95, stem top 33.10 | x −2.9, footprint −45°; tilt reference height 32.40 |
| Cup | 31.90–34.45 | Bore Ø3.15 (0.075 radial on the Ø3 stem), OD 5 |
| Balls Ø2 at (±14, ±7) | centre 33.45 = base top | Hemisphere seats in the base |
| Carrier | underside 34.45 | 33.6×20.6, 0.8 skirt |
| Spider | 36.05–36.65 | t 0.6, 4 arms, pad 18×8, free travel 0.4, land 0.6 |
| Screen | 37.25–38.80 | Screen top = faceplate front |

- **Slide:** stop ±0.40 per axis. Actuation needs 0.325 (0.075 cup clearance + 0.25 tilt), which leaves 0.075
  overtravel. The rectangular stop gives **0.57 radial on the diagonals**, so the stem over-tilts by about 0.24.
  A round stop (Ø0.8) would fix that.
- **Press path:** screen → spider pad → plunger (0.05 above the stem) → stem. The spider adds about **0.74 N**
  (k ≈ 3.7 N/mm, PA12 estimate), for a total press of about **3.1 N**. The switch's own stop takes the full force.
- **Hold-down:** 4 × Ø2 extension springs in Ø3.4 bores at (±10.8, ±6.6), 0.5 N each [A], about 60 mm long to the
  back panel (was about 42 mm when the screen sat at 20.2). Clearance at the full diagonal slide is 0.134.
- **FPC:** 8 wide [A] at local x 15. The carrier slot is x 13.6–15.6 at ±4.75. The base notch and main-PCB slot are x 13.0–16.2 at ±5.35.

**Main-PCB requirements** (not yet in the main KiCad project):
- J2: a 2×3 2.54 female socket (8.5 tall) at local (5.6, 0): FG FG-PM2.54-2-03P-H8.5 (LCSC C42391433; alt SHOU HAN
  PM2.54-2x3PZZ-H8.5, C54876739), main PCB v0.11.
- 4 × Ø3.4 spring holes at (±10.8, ±6.6).
- 4 × Ø1.3 base-pin holes at (±6, ±8.5).
- An FPC slot 3.2×10.7 at local x 13.0–16.2.
- A keep-out for the base footprint (31.2×18.2).

**Daughterboard:**
- SW1 SKRHADE010, J1 2×3 male.
- Nets: UP, CENTER, RIGHT, LEFT, DOWN and GND, each routed individually; the common goes to GND.
- J1 pinout: 1 UP, 2 CENTER, 3 RIGHT, 4 LEFT, 5 GND, 6 DOWN.
- ESD and pull-ups go on the MCU (main-PCB) side.
- The direction map (a→UP, b→RIGHT, c→LEFT, d→DOWN at −45°) needs **checking on the bench**.
