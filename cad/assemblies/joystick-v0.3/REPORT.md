# Joystick v0.3

The carrier floor is no longer the stack. v0.2 filled the 26 mm between a low switch and the screen with solid plastic (carrier **33.53 cm³**). v0.3 raises the daughterboard until the switch sits just under a thin shell, and deletes the printed base.

Screen top stays at **z 47.50** (knob top 52.5 − 5). The round stop, the spider flexure and the Ø2 balls are unchanged in behaviour. The press is still **3.09 N** (switch 2.35 + spider 0.74).

## What changed

- Carrier floor **26.05 → 2.05 mm**. The shell's screen-well wall is **1.00 mm** (v0.2 was 0.80: 1.0 wall minus 0.20 air). PCBWay's published minimum is 0.8 mm for SLA resin and 1.0 mm for SLS nylon, so the wall is sized for nylon. The spider plate stays 0.6 mm: it is the flexure, and thickening it would change the 0.74 N.
- Riser **11 → 35 mm**, four standoffs instead of two, both ends GND.
- The 2×3 header beside the switch is gone. The switch is on the carrier axis. Two 1×3 headers are on the **underside**, mirrored, pins along x.
- The brown base (pins, walls, cavity) is gone. A 1.0 mm plate is glued on the daughterboard. It has the four ball-seat bosses and the round stop. The same screws pass through the plate and the board into the standoffs.
- Daughterboard **31.88 × 17.52 mm** (v0.2 was 19.2 × 13.8; v0.1 was 16.6 × 12). The size falls out of the land pattern, a 1 mm frame, the headers and the stop. Ed's "about 32 × 18" is this.
- No LEDs.

## Parts

| Where | Part | LCSC | Role |
|---|---|---|---|
| Main PCB, two | hanxia HX PM2.54-1x3P ZC H11 | C41427518 | 1×3 socket, insulation 11 mm. In stock when checked |
| Daughterboard, two, bottom | Samtec TSW-103-20-T-S | consigned | 1×3 header, insulator 2.54, mating pin **25.91**, tail 2.79. Samtec had it in stock. LCSC lists the same lead as C3345998 (that one is 2-row) and C3334257 (1×25). Do not fit the 2-row part |
| Between the boards, four | XHHD STTZ2032, hex H3 × M2 × 35, female-female brass | C50377216 | The riser. Same family as v0.2's STTZ2008. Shown out of stock on 1 Nov 2026; the round F-F of the same length is STTZ1032 (C50378480) |
| Hand-fit | eight M2×6 pan-head screws | — | Four down through the plate and the daughterboard, four up through the main PCB |

The mating pin enters the 11 mm socket by **4.45 mm**. Air between the header plastic and the socket top is 21.46 mm; the pin crosses it.

Header nets, inner pin toward the switch: J1 (+x) RIGHT, DOWN, GND. J2 (−x) LEFT, CENTER, UP. Frame tabs 7 and 8 are GND. Directions are still confirmed at first power.

## Carrier volume and mass

| | v0.2 | v0.3 |
|---|---|---|
| Carrier volume | 33.53 cm³ | **4.41 cm³** |
| Seat plate / base | base 3.47 cm³ | plate **0.59 cm³** |
| Mass, PA12 at 1.01 g/cm³ | carrier ~34 g | carrier **4.4 g**, plate 0.6 g |
| Mass, resin at 1.30 g/cm³ | carrier ~44 g | carrier **5.7 g**, plate 0.8 g |

v0.2's quoted 34–43 g was this density range on the 33.5 cm³ carrier. The new carrier is about an eighth of that.

## Clearances

| Check | Value | Target |
|---|---|---|
| Carrier vs design knob Ø41.7, full slide | **0.60 mm** | ≥ 0.55 (v0.2 was 0.55) |
| Carrier vs live knob Ø40.85 | 1.03 mm | ≥ 0.55 |
| Stem vs cup, radial | 0.075 mm | ≥ 0.05 |
| Round-stop gap at rest | 0.40 mm | 0.32–0.50 |
| Overtravel, every direction including diagonals | 0.075 mm | ≤ 0.15 |
| Screen-well wall | 1.00 mm | ≥ 1.0 |
| Carrier floor | 2.05 mm | ≥ 1.0 |
| Header into the H11 socket | 4.45 mm | 3.5–6.5 |
| FPC vs carrier | 0.70 mm | ≥ 0.5 |
| Screen top | 47.50 mm | unchanged |

## Checks

`cad/joystick-param/build.py`: **44/44 PASS, 0 clashes.** New rows cover switch centring (offset 0), mirror symmetry of the standoffs, headers, balls and springs, standoff count = 4, and the well / floor / skirt walls.

Daughterboard KiCad (`make_project.py`): **ERC 0, DRC 0** (all severities), schematic parity 0, 0 unconnected. Fab pack `joystick-daughterboard/fab/` is READY TO QUOTE. J1 and J2 are the consigned Samtec lines.

`cad/knob-param/build.py --contract` is OK. `--sub electronics` is 2/2 PASS. The main PCB was not edited.

## Main PCB, not edited

Carrier centre moves to board **(25.25, 16.48)**. Coordinates are main-PCB millimetres, y down.

- Two 1×3 sockets, 11 mm, at carrier-local **(±9.75, 0)**.
- Four Ø2.4 PTH to GND, pad Ø3.2, at **(±14.04, ±4.08)** local. They are one per quadrant. They are not on the outline's top edge: the main PCB ends 5.98 mm above the switch, and the pad needs 0.30 mm of edge clearance, so ±4.08 is as far out as the screws can go.
- Four Ø3.4 spring holes out near the carrier sides. No base-pin holes.
- FPC slot grows with the drop, which now sits just clear of the skirt. Exit side, pin count, pitch and pin-out are still open.
- The daughterboard outline overhangs the main PCB's top edge. Nothing is screwed down in that overhang, and the board is at z 35, above the assumed rail at z 10.

## Open

- DO0164FMST05 FPC exit side, pin count, pitch and pin-out.
- Back-panel depth. The spring length is the hook (z 41.75) plus the PCB plus the v0.2 allowance of 22.65 mm, so **66 mm**. The 42 mm figure was the low v0.2 hook; it does not reach this one.
- STTZ2032 stock. The length and the thread are right; the bin was empty on the day it was picked.
- Rail front height, if it is taller than z 10.
- Knob v0.17 is still not in this tree. The plan is sized to Ø41.7 with 0.60 mm to spare. A larger knob means `place_y` moves again.
