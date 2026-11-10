# Manufacturing plan (PCBWay)

## Plan
- Send the design **straight to PCBWay**. Order kits in batches of **1, 5 and 10**.
- **PCBWay builds as many sub-assemblies as possible:**
  - **Assembled PCBs: three boards** — the main PCB, the screen adapter and the joystick daughterboard.
    (The dial TMAG5273 board was dropped in v0.16b with the relative-angle sensor, and there is no USB-C panel
    board.) Turnkey parts are sourced by MPN; every BOM line also carries an LCSC number.
  - **Printed parts** in the process each one suits:
    - MJF/SLS nylon for structural parts: the knob, control dial, cradle, saddle and carriers.
    - Resin for small precise or visible parts.
    - Metal where strength or wear needs it.
  - **Bought parts:** brass tube 5×3, gears/pinions (m0.5, brass where available), balls (Ø1 and Ø1.5 steel,
    race balls), springs (detent, extension, spider if not printed), screws and grub screws (M1, M1.6, M2),
    bearings (F682ZZ), magnets, and the 1220 and 716 motors.
- **Ed does final assembly:** pressing in the magnets, the balls and detents, the springs, gluing the base and
  flange, the knob stack, and calibration.
- **Cost:** no fixed target [Ed, 1 Nov 2026]; get PCBWay quotes at 1, 5 and 10 kits.

## What to send
- KiCad PCBWay packs (Gerber+drill zip, BOM with MPN/LCSC, CPL, ERC/DRC reports, README status) in
  `cad/knob-param/knobparam/electronics/kicad/<board>/fab/` (`fab_export.py`).

| Board | Rev | Status (10 Nov 2026) |
|---|---|---|
| Main board | v2.0 | **READY TO QUOTE**: 6 layers, routed, KiCad DRC 0 / 0, fab pack in `knob-main-pcb/v2/fab/` (Gerbers, drill, BOM with LCSC numbers and datasheet links, CPL). |
| USB-C board, jack board, jack power board (upper / lower) | see each `fab/README.txt` | their own packs (`fab_export.py`). |

Superseded and archived on 10 Nov in `superseded/` (**do not quote**): main PCB v0.11, screen adapter v0.4 (replaced by the
rod-link board in v0.24), joystick daughterboard v0.4 (replaced by the joystick top board on the vertical boards).

- Joystick switch: Alps SKRHADE010 (C202415); **only approved alternate SKRHABE010** (C139794); E-Switch
  JS1400BFQ is **no auto-substitute**. The joystick carrier slides in-plane (it never tilts).
- STEP files per printed part from the parametric model, with the material and process for each.
- A purchased-parts BOM with quantities per kit.
- An assembly drawing showing which sub-assemblies PCBWay builds and which Ed builds.

## Open questions for the reviewer
1. Which printed parts should be MJF nylon, which resin, and which metal? In particular: the 0.8 mm lip wall,
   the detent bosses, the M2 threads for the grub screws (tapped or a heat-set insert), and the gear teeth if
   any gears are printed.
2. Can PCBWay hold the tolerances the model assumes: the Ø1.6 detent bores, the Ø1 ball track grooves, the
   0.05 mm pin clearance and the 0.3 mm running gaps? Should any of these be reamed or post-machined?
3. Can PCBWay source or make m0.5 brass gears (75T internal ring, 24T, 22T, 19T, 14T), or should they be printed
   or cut?
4. Can PCBWay press the magnets in (with polarity marked) and fit the balls and springs, or are those Ed-only
   steps?
5. Spring sourcing: non-magnetic stainless 316 or phosphor-bronze extension and compression springs at these
   small sizes. Stock or custom?
6. Is the cost target realistic at 1, 5 and 10 kits? What are the main cost drivers, and where would a design
   change save the most?
7. What test-point and programming access do they need for the assembled boards: CH32V003 on the screen
   adapter, the STM32, and the TMAG I²C?
8. Packaging and kitting: sub-assemblies bagged per dial, with spares of the small parts (balls, springs,
   magnets).
