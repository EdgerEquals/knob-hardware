# Top screen joystick

The top screen is also the main navigation control. It moves left, right, up and down, and presses in.
v0.2 uses a DWO **DO0164FMST05** 1.64" 456×280 AMOLED, mounted landscape (v0.1 was a 1.14" 240×135 IPS).
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
**20/20 checks PASS, 0 clashes.** KiCad: `cad/knob-param/knobparam/electronics/kicad/joystick-daughterboard/`
(ERC 0, DRC 0, parity 0).

**Stack** (z measured from the main-PCB front face; the carrier centre is board (25.25, 21.1)):

| Item | z (mm) | Notes |
|---|---|---|
| J2 2×3 2.54 female socket on the main PCB (the riser) | 0–8.5 | Male J1 on the daughterboard, plastic on top and pins down; trim the top pin tails |
| Daughterboard | 8.5–9.5 | 16.6×12.0×1.0 FR4. Rests on a Ø4 printed post under the switch, which takes the press |
| SKRHADE010 | body top 11.35, stem top 14.5 | x −2.9, footprint −45°; tilt reference height 13.8 |
| Cup | 13.3–15.85 | Bore Ø3.15 (0.075 radial on the Ø3 stem), OD 5 |
| Balls Ø2 at (±14, ±7) | centre 14.85 = base top | Hemisphere seats in the base |
| Carrier | underside 15.85 | 33.6×20.6, 0.8 skirt |
| Spider | 17.45–18.05 | t 0.6, 4 arms, pad 18×8, free travel 0.4, land 0.6 |
| Screen | 18.65–20.2 | Screen top 20.2 [A] = panel front |

- **Slide:** stop ±0.40 per axis. Actuation needs 0.325 (0.075 cup clearance + 0.25 tilt), which leaves 0.075
  overtravel. The rectangular stop gives **0.57 radial on the diagonals**, so the stem over-tilts by about 0.24.
  A round stop (Ø0.8) would fix that.
- **Press path:** screen → spider pad → plunger (0.05 above the stem) → stem. The spider adds about **0.74 N**
  (k ≈ 3.7 N/mm, PA12 estimate), for a total press of about **3.1 N**. The switch's own stop takes the full force.
- **Hold-down:** 4 × Ø2 extension springs in Ø3.4 bores at (±10.8, ±6.6), 0.5 N each [A], about 42 mm long to the
  back panel. Clearance at the full diagonal slide is 0.134.
- **FPC:** 8 wide [A] at local x 15. The carrier slot is x 13.6–15.6 at ±4.75. The base notch and main-PCB slot are x 13.0–16.2 at ±5.35.

**Main-PCB requirements** for v0.1 (superseded by the v0.2 list below; the main KiCad project is still v0.11 and has not been edited):
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
- The direction map (a→UP, b→RIGHT, c→LEFT, d→DOWN at −45°) is **confirmed at first-power calibration** [Ed]. No hardware change.

## v0.2 build (1 Nov 2026)
Model: `cad/joystick-param/` (`build.py`, `build.py --render`). Image: `cad/assemblies/joystick-v0.2/joystick-v0.2.png` and `-plan.png`.
**32/32 checks PASS, 0 clashes.** KiCad daughterboard: `cad/knob-param/knobparam/electronics/kicad/joystick-daughterboard/`
(ERC 0, DRC 0, schematic parity 0, 0 unconnected). Fab pack: `joystick-daughterboard/fab/` (READY TO QUOTE).
The main PCB KiCad project was **not** edited. It still carries the v0.1 holes.

Screen: DWO **DO0164FMST05**, landscape. Outline 41.62 × 26.74 × 1.5 mm, no cover lens; active area 35.57 × 21.84; driver ICNA3311/CO5300 over QSPI; FT3168 touch fitted and unused [S, the published mechanical table]. The 2D drawing (FPC exit side, pin count, pitch, pin-out) could not be downloaded from dwo.net.cn, so the FPC is modelled [A]: 8 mm wide, leaving the +x end, turning down 2.6 mm inboard of the glass in a channel under the screen. **Pin-out is open.**

**Stack** (z from the main-PCB front; carrier centre is board **(25.25, 16.73)**, knob-frame y **36.17**):

| Item | z (mm) | Notes |
|---|---|---|
| J2 2×3 2.54 female socket, **11 mm** (the riser) | 0–11 | hanxia HX PM2.54-2x3P ZC H11, LCSC C41427525. Replaces the 8.5 mm FG part |
| Two M2×11 brass standoffs | 0–11 | XHHD STTZ2008, LCSC C50377192. Same height as the socket, both ends GND. Four M2×4 screws, hand-fit |
| Daughterboard | 11–12 | 19.2 × 13.8 × 1.0 FR4, centre local (0.2, −3.2). J1 is LXWCONN 254PZ-2x3P-V, C53055678, 6 mm mating pin |
| SKRHADE010 | body top 13.85, stem top 17.0 | local (−3.0, −1.2), footprint −45°. Frame tabs (pads 7, 8) tied to GND |
| Cup | 15.8–18.35 | Bore Ø3.15 over the Ø3 stem |
| Balls, four × Ø2 stainless | centre 17.35 = base top | Hemisphere seats. Ed confirmed Ø2 stainless; four seats stay so the carrier cannot tilt |
| Carrier underside | 18.35 | Outline **43.62 × 28.74** (screen + 1 mm wall each side). Floor is 26.05 thick: that is the slack that lets the 11 mm riser land the screen |
| Round stop | boss into the floor | Ø4.6 boss, bore Ø5.4, travel radius 0.40 (circle Ø0.80) in every direction, diagonals included |
| Spider | 44.8–45.4 | Same flexure as v0.1: +0.74 N, press **3.09 N**. Free travel 0.40 |
| Screen | 46.0–47.5 | Top is knob top 52.5 − 5 mm [Ed]. Knob top read from knob-param |

- **Slide:** round stop, radius 0.40. Actuation needs 0.325, so overtravel is 0.075 on the axes **and** on the diagonals. A looser rectangular skirt (gap 0.75) only stops the carrier rotating on the boss.
- **Hold-down:** 4 × 0.5 N, installed length **42 mm**. The derived back-panel depth is 22.65 mm [A]; the real depth is still unknown. Each hook boss is slotted so the spring eye slides off.
- **Plan:** the carrier is sized to clear a **Ø41.7** knob (the v0.17 growth) by 0.55 mm at full slide toward the knob, and the live knob-param OD (Ø40.85) by 0.98 mm. The carrier's far edge overhangs the current PCB top by **8.14 mm**. The skirt bottom is at z 16.6, above an assumed rail height of z 10 [A], so the overhang is in front of the rail rather than in it. The base, balls, springs, pins and standoffs all stay on the PCB.
- **Base:** 40.52 × 18.65, local x −20.26…20.26, y −12.82…5.83. Board keep-out from (4.99, 10.90) to (45.51, 29.55).

### What the main PCB KiCad needs to change
Coordinates are main-PCB millimetres (origin at the panel top-left, y down). Carrier centre moves from (25.25, 21.1) to **(25.25, 16.73)**. Do not treat the v0.1 holes as still valid.

- **J2** moves to **(31.15, 17.73)** and grows from 8.5 mm to **11 mm**: hanxia **HX PM2.54-2x3P ZC H11**, LCSC **C41427525** (2×3, 2.54 mm, top entry). The v0.1 part FG-PM2.54-2-03P-H8.5 (C42391433) is no longer the riser. Pin-out is unchanged: 1 UP, 2 CENTER, 3 RIGHT, 4 LEFT, 5 GND, 6 DOWN.
- **Two standoff holes**, new: Ø2.4 PTH, pad about Ø3.2, **net GND**, at **(17.75, 24.73)** and **(32.45, 24.33)**. An M2 screw comes through each from the back of the board into the female standoff.
- **Spring holes** Ø3.4, four, move to **(37.65, 15.90), (11.05, 13.40), (38.25, 25.05), (11.05, 25.15)**.
- **Base-pin holes** Ø1.3, four, move to **(40.75, 12.60), (9.05, 12.60), (40.75, 27.85), (9.05, 27.85)**.
- **FPC slot** moves and grows. Carrier-frame x 16.41–20.01, ±5.70, which is board x **41.66–45.26**, y **11.03–22.43** (about 3.6 × 11.4). The v0.1 slot does not cover it.
- **Base keep-out** becomes 40.52 × 18.65, board rectangle **(4.99, 10.90)–(45.51, 29.55)**. J2 and the two standoff pads sit in the window and are exempt.
- The carrier outline overhangs the current PCB top edge by 8.14 mm toward the panel top. No new holes are in that overhang. Whether the rail is actually clear of the skirt (z 16.6 vs an assumed rail front at z 10) is open.

### Open
- DO0164FMST05 FPC: exit side, pin count, pitch and pin-out. The product page and the sister part DO0164FMST02 advertise a 2D drawing; the files did not come down (the site returned 429, and the only PDF retrieved was a demo-board schematic, not the module drawing).
- Back-panel depth. Springs are 42 mm [A] until it is known.
- Rail front height. The 8.14 mm carrier overhang is only safe if the rail stays below z 10.
- Knob v0.17 is not in this tree yet (live OD is still Ø40.85). The plan is sized to Ø41.7. If the knob grows past that, `place_y` has to move again.
