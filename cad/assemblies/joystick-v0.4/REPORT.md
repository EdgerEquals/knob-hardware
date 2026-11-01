# Joystick v0.4

## 25 mm brass riser (1 Nov 2026)

Ed asked for a stocked brass M2 standoff near 1 inch, held by socket-head screws, no glue. Prefer 25 mm, then 25.4 mm. `knob_proud` may sit up to 20 mm.

**Chosen:** XHHD **STTZ1022**, round female-female, M2×**25** brass, LCSC **C50378470**. 870 in stock, **$0.0354** at qty 10 ($0.0269 at 10k). OD 3.2 mm is the usual knurled round M2 body; LCSC does not print it. ISO 4762 M2×6 through the seat plate and the daughterboard (4.0 mm of thread in the pillar). ISO 4762 M2×4 under the main PCB (2.4 mm of thread). Head Ø3.8 × 2.0.

The riser is that 25.00 mm body. Knob top stays z 52.50, so the faceplate front is z **36.05** and **knob_proud = 16.45 mm**. That is the number for the knob and the case. It is inside 16–20. The figure 25 − 5.45 = 19.55 adds the old 5.45 mm the other way; a longer riser lifts the faceplate, so proud falls, and 19.55 would leave the bezel 3.1 mm above the faceplate.

No brass M2 at 25.4 mm turned up in stock. Hex female-female H3×M2×25 (STTZ2022, C50377206) and the male-female 25 mm parts (DTTZ2025 25+3, DTTZ3024 25+4, DTTZ3131 25+5) are all out of stock on LCSC.

| Part | Style | Length | Stock | Price |
|---|---|---|---|---|
| **STTZ1022** C50378470 | round F-F brass M2 | **25** | **870** LCSC | **$0.0354** (10+) |
| STTZ2022 C50377206 | hex F-F brass H3×M2 | 25 | 0 LCSC | $0.0236 listed |
| DTTZ2025 C50377594 | hex M-F brass 25+3 | 25 | 0 LCSC | — |
| DTTZ3024 C50377632 | hex M-F brass 25+4 | 25 | 0 LCSC | — |
| DTTZ3131 C50377663 | hex M-F brass 25+5 | 25 | 0 LCSC | — |
| Essentra 301125040050 | hex F-F nickel brass, AF 4 | 25 | 450 Essentra UK | £1.184 (50+) |
| RS PRO 224-0414 | hex M-F nickel brass, stud 20 | 25 body | 890 RS | £7.63 listed; stud is too long |
| HIROSUGI ASB-2025E / BSB-2025E | hex F-F / M-F brass, stud 5 on the M-F | 25 | pre-order | — |

Header is Samtec **TSW-103-17-T-S** (post 15.74 mm, tail 2.79, consigned). Engagement **4.28 mm**. Pin tip z **6.72**, above the main PCB. Glass top z **37.87**. Daughterboard **31.61 × 13.87**, standoffs at (±13.91, ±3.83). ERC 0, DRC 0.

Checks: **79/79 PASS, 0 clashes.** Section preview only.

The four hold-down springs stop just behind the main PCB. Installed length **34.0 mm** (45.4 mm before the faceplate moved, 65.9 mm when they reached the back panel). Free length **26.0 mm**, stretch **8.0 mm**, force still **0.50 N** each (0.062 N/mm). A printed rear anchor, **18.3 × 12.0 × 4.65 mm**, **0.83 cm³**, bond outline **220 mm²**, is glued to the PCB back. Two Ø1.20 mm cross pins, shaft 16.7 mm, run along X at y ±3.50. Each pin passes both hooks on that row. The bore is Ø1.50, open on +x, stopped by a 1 mm wall on −x. The anchor clears the M2 nuts by **2.4 mm**.

Each Ø2 ball sits in a pair of shallow spherical cups, one in the seat post and one in the carrier. Cup radius **1.396 mm** (1.396 × the ball radius), depth **0.60 mm** (0.30 × the diameter). The cups still hold the ball out to **0.65 mm** of carrier travel; the slide is 0.45 mm, so the margin is **0.20 mm**. The wider posts put the balls at **(±9.51, ±4.14)**.

The module rests on the case faceplate. The bezel is a 1.2 mm lip (44.02 × 29.14) on a 2.5 mm faceplate proxy. The carrier, springs, switch, daughterboard and standoffs are below that plate.

The carrier assembly is simpler. The printed spider and plunger are gone, and so is the round stop. The switch's own end of travel is the only stop, for tilt and for the centre press. The screen is glued to a separate bezel. Four catalog compression springs sit between that bezel and the carrier, and an M2 grub screw under each one sets the preload.

Ed dials that preload on the carrier-and-bezel sub-assembly, from underneath, before the rest goes together. The screws are not reachable once the stack is built, and nothing was added so they could be. No access hole, no keep-out on the daughterboard.

The four hold-down extension springs are unchanged in kind from v0.3. They still hold the carrier down on the balls. They do not touch the new springs.

The switch stays on the carrier axis. Four grounded standoffs. The riser length follows the faceplate, above.

## What was removed

- The printed nylon spider and its plunger (one part).
- The round stop: the boss on the plate, the bore in the carrier, and the daughterboard tab that existed only to carry that boss.
- The spider pocket, the plunger gap and the stop-circle checks.

## What was added

- A screen carrier (the bezel the glass is glued into), with a centre peg that meets the stem.
- Four Lee Spring **CI 008B 01 M** compression springs.
- Four **ISO 4026 / DIN 913 M2×3 A2** flat-point grub screws.
- Four **M2×2×3.2** brass heat-set inserts, in the carrier floor.

The bezel snaps down over a shoulder on each spring pilot. A rectangular bezel in a 0.20 mm guide cannot turn, so it is a push-down snap rather than a bayonet. The lip overlap is 0.40 mm. At rest the lip is 0.02 mm under the shoulder (the solid model leaves 0.01 mm so the two faces do not fuse). Pressing the screen moves the lip down, away from the shoulder. The switch bottoms first; 0.20 mm of clearance remains above the carrier floor.

## Parts

| Where | Part | Number | Role |
|---|---|---|---|
| Four, between bezel and carrier | Lee Spring CI 008B 01 M | catalog | Music wire, tinned. Wire Ø0.20, OD 2.24, free length 3.18, solid height 1.07, rate 5.5 lbf/in = **0.963 N/mm** |
| Four, in the carrier | ISO 4026 M2×3 A2 flat point | DIN 913. A stocked example when this was picked: PTS A9130203. Accu SSF-M2-3-A2 was listed discontinued | Pitch 0.40 mm, hex 0.9. The hex hangs under the carrier |
| Four, in the carrier | M2×2×3.2 brass heat-set | common "M2*2*3.2" | Thread M2, length 2.0, OD 3.2, hole Ø3.0. The insert hangs down from the floor. The model is a slip fit; the real insert is an interference fit |
| Kept | hanxia HX PM2.54-1x3P ZC H11 | C41427518 | Two sockets on the main PCB |
| Kept | Samtec TSW-103-20-T-S | consigned | Two headers, underside. Same −20 lead as LCSC C3345998 (that one is 2-row) |
| Between the boards, four | XHHD STTZ1022, round female-female M2×25 brass | C50378470 | The riser. 870 in stock. Socket screws at both ends |
| Under the main PCB, four | ISO 4032 M2 hex nut | hand-fit | On the 4 mm stud. Across flats 4, thickness 1.6 |
| Kept | four hold-down extension springs | — | 0.5 N each, length 66 mm (hook z 41.75 + PCB 1.6 + back panel 22.65 [A]) |

## Preload

Nominal set-point is **half a turn** (0.20 mm), dialled on the sub-assembly.

| | One spring | All four |
|---|---|---|
| Per turn (pitch 0.40 mm) | **0.385 N** | **1.54 N** |
| At 0.5 turn, bezel on the up-stop | 0.193 N | **0.77 N** |
| At 0.5 turn, switch at the bottom of its press | 0.530 N | **2.12 N** |

The centre-push band is 2.35 ± 0.69 N, so **1.66 to 3.04 N**. 2.12 N is inside it. The 0.77 N preload is under 1.66 N, so the switch is not already clicked at rest, and it is about ten times the assumed 8 g screen weight (0.078 N).

Useful window, the turns that keep the press inside that band, keep the preload under a click, and still beat five times the screen weight: **0.25 to 1.08 turns** (0.10 to 0.43 mm). The hex is still 0.40 mm proud of the insert out to **1.50 turns**, so the whole window is reachable. At zero turns the press only reaches 1.35 N, which is under the 1.66 N minimum, so the useful range does not include a completely slack screw. Do not wind on toward solid: at the nominal set-point, full press still leaves 1.56 mm before the spring goes solid.

## Clearances

Process numbers used as the gaps: SLA ±0.20 (the wide end of PCBWay's ±0.1–0.2), MJF/SLS ±0.25, FDM ±0.20. A v0.3 gap that was looser than that was tightened. The cup clearance was tighter than SLA can hold, so it was raised.

| Check | v0.3 | v0.4 | Why |
|---|---|---|---|
| Carrier vs design knob Ø41.7, full slide | 0.60 mm | **0.50 mm** | both faces MJF: 2 × 0.25. The extra 0.05 mm hair is gone |
| Carrier vs live knob Ø40.85 | 1.03 mm | **0.93 mm** | same placement rule |
| Stem vs cup, radial | 0.075 mm | **0.20 mm** | was under the SLA tolerance; raised to it |
| Tilt stop | round stop, 0.40 mm radius, 0.075 overtravel | **the switch**. Slide 0.45 = 0.20 cup + 0.25 tilt. No added overtravel | the stop boss is gone |
| Skirt gap, at rest | larger than the stop | **0.70 mm** | slide 0.45 + one MJF tolerance, so the skirt is not the tilt stop. 0.25 mm remains when the switch has stopped. A 3° rotation still hits the skirt |
| Press gap, peg to stem | plunger 0.02–0.10 | **0.20 mm** | one SLA tolerance, then the switch's own 0.15 mm |
| FPC vs plastic | ≥ 0.50 (measured 0.70) | **0.25 mm** | one MJF tolerance. Slot side clearance was 1.05 |
| Bezel guide, radial | — | **0.20 mm** | SLA, pilot body in the lip |
| Glue gap around the glass | 0.20 | **0.20 mm** | SLA. The glass sits on the ledge |
| Screen-well wall | 1.00 | **1.00 mm** | PCBWay SLS/MJF minimum. The well is in the bezel now |
| Carrier floor | 2.05 | **1.00 mm** | the print minimum. The riser is the 25 mm STTZ1022 body |
| Up-stop, lip under the shoulder | — | 0.02 mm design | captive without another spring |

The knob-facing edge is the middle of the long side, at ±14.57 mm. The four spring corners stand out to ±21.41 mm, outside the knob's plan, so they do not push the module off the main-PCB screws. Bounding box of that outline is 57.70 × 42.82 mm. v0.3 was a plain 44.02 × 29.14 rectangle.

## Volume and mass

| | v0.3 | v0.4 |
|---|---|---|
| Carrier | 4.41 cm³ | **2.79 cm³** |
| Screen carrier (bezel) | — (the well was part of the carrier) | **3.77 cm³** |
| Seat plate | 0.59 cm³ | **0.44 cm³** (the stop tab and the stop boss are gone) |
| Carrier + bezel + plate | 5.00 cm³ | **7.00 cm³** |
| Mass, PA12 at 1.01 g/cm³ | carrier 4.4 g, plate 0.6 g | carrier **2.8 g**, bezel **3.8 g**, plate **0.4 g** |
| Mass, resin at 1.30 g/cm³ | carrier 5.7 g, plate 0.8 g | carrier **3.6 g**, bezel **4.9 g**, plate **0.6 g** |

The carrier floor got thinner. The new mass is the bezel and the four corner towers the springs live in. Printed total is about 2 cm³ above v0.3.

## Standoff

XHHD **STTZ1022**, LCSC **C50378470**: round female-female M2×25 brass. The body is the 25 mm riser. An ISO 4762 M2×4 socket screw (head Ø3.8 × 2.0) sits under the main PCB, with 2.40 mm of thread in the pillar. An M2×6 socket screw goes through the seat plate and the daughterboard, with 4.00 mm of thread in the pillar. The screw head, not a nut, sets the PCB inset: the screws are at **y ±3.83**. The Ø2.4 hole is unchanged. Pairwise clash check: **none**.

## Daughterboard

**31.61 × 13.87 mm** (v0.3 was 31.88 × 17.52). The −y tab is gone, so the outline is symmetric about the switch. Headers stay at x = ±9.75. Standoffs are at **(±13.91, ±3.83)** (the Ø3.8 screw head, not the Ø3.2 pad, sets y). They stay one per quadrant and on the main PCB.

KiCad (`make_project.py`, rev v0.4): **ERC 0, DRC 0** (all severities), schematic parity 0, 0 unconnected. The bottom GND bus moved from y = −7.4 / −8.6 (on the old tab) to **y = −6.30**, inboard of the new edge and clear of the Ø3.2 pads. Fab pack `joystick-daughterboard/fab/` is READY TO QUOTE. J1 and J2 stay the consigned Samtec lines.

## Sub-assembly order

1. Heat-set the four inserts into the carrier, from below.
2. Run a grub into each one until the flat tip is flush with the seat (zero turns).
3. Stand a spring on each tip.
4. Press the bezel down until the four lips snap under the pilot shoulders.
5. Dial the preload from underneath. Half a turn is the nominal.
6. Then sit that sub-assembly on the balls. The hexes are buried. There is no hole in the plate or the daughterboard for them: the springs are outside the plate.

## Checks

`cad/joystick-param/build.py --section`: **79/79 PASS, 0 clashes.** Daughterboard KiCad: ERC 0, DRC 0.

`cad/knob-param/build.py --contract` is OK. `--sub electronics` is 2/2 PASS. The main PCB KiCad project was not edited.

## Main PCB, not edited

Carrier centre is board **(25.25, 16.53)** (v0.3 was 16.48). Knob-frame `place_y` is **36.37**.

- Two 1×3 sockets at carrier-local **(±9.75, 0)**, unchanged.
- Four Ø2.4 PTH to GND, pad Ø3.2, at **(±13.91, ±3.83)**. An ISO 4762 M2×4 socket screw holds the pillar under the board.
- Four Ø3.4 hold-down holes at **(±22.50, ±4.03)**. The corner formula would have put them at x = ±27.35, which is off the 49 mm PCB, so they stop at the copper-edge limit. v0.3 was about (±20.5, ±4.0).
- No grub-screw holes and no new keep-outs.
- FPC slot at local x 16.4–20.1, ±4.95. Exit side, pin count, pitch and pin-out are still open.

## Open

- DO0164FMST05 FPC exit side, pin count, pitch and pin-out.
- Screen mass. 8 g is assumed. The preload check uses five times that weight; a heavier module still fits inside the 0.77 N preload until it reaches about 15 g.
- Back-panel depth. Hold-down length is still **66 mm**.
- Round pillar OD is 3.2 mm by the usual knurled M2 size. LCSC does not publish it. A hex 25 mm body (STTZ2022) would be preferable with a wrench and is out of stock.
- `knob_proud` 16.45 mm is for the knob and the case to adopt. It is not on `sub/assembly-v017` yet.
- Rail front height, if it is taller than z 10. Skirt bottom is z 35.25.
- Knob v0.17 is still not in this tree. The plan is sized to Ø41.7 with 0.50 mm to spare.
