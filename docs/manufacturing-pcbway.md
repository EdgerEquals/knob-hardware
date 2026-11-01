# Manufacturing plan (PCBWay)

## Plan
- Send the design **straight to PCBWay**. Order kits in batches of **1, 5 and 10**.
- **PCBWay builds as many sub-assemblies as possible:**
  - **Assembled PCBs:** the main PCB, the screen adapter, the dial TMAG5273 board, the joystick daughterboard
    and the USB-C panel board. Turnkey parts are sourced by MPN (PCBWay has no fixed parts list).
  - **Printed parts** in the process each one suits:
    - MJF/SLS nylon for structural parts: the knob, control dial, cradle, saddle and carriers.
    - Resin for small precise or visible parts.
    - Metal where strength or wear needs it.
  - **Bought parts:** brass tube 5×3, gears/pinions (m0.5, brass where available), balls (Ø1 and Ø1.5 steel,
    race balls), springs (detent, extension, spider if not printed), screws and grub screws (M1, M1.6, M2),
    bearings (F682ZZ), magnets, and the 1220 and 716 motors.
- **Ed does final assembly:** pressing in the magnets, the balls and detents, the springs, gluing the base and
  flange, the knob stack, and calibration.
- **Cost target:** well under about **$400 per dial** (currency to confirm) in parts and assembly at the 5–10 kit level.

## What to send
- KiCad PCBWay packs (Gerber+drill zip, BOM with MPN/LCSC, CPL, ERC/DRC reports, README status) in
  `cad/knob-param/knobparam/electronics/kicad/<board>/fab/` (`fab_export.py`). Main PCB v0.10: routed, ERC/DRC clean,
  but J10 (MCU link) is a placeholder and U2/J2 have no LCSC part yet. Screen adapter v0.4: placed, not routed.
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
