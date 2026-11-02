# Case, display stack and connectors: decisions, 2 Nov 2026

Tags: [Ed] Danny's decision, [A] assumption to verify, [C] open check.
Status: sketched only (schematic from the case numbers). Nothing has been checked in CAD.

## Case
- [Ed] One-piece clear resin front shell (PCBWay UTR-8100), front face polished, other faces as-printed.
- [Ed] Back cover: smoky/black PETG, permanent, serviced by replacement.
- [Ed] No ledges, steps or tabs. The PCB sits in a recess in the front shell. The shell alone sets the datum.
- [Ed] Walls 2.9 mm (PCB plus 0.3 mm each side).
- [Ed] Four corner bolts from the back into brass sleeves epoxied in the resin bosses. PETG corner tubes in the cover press the PCB back.
- [Ed] Seam gap 0.3-0.5 mm with silicone or gasket (neutral-cure RTV, not acetoxy).
- [A] Sleeve epoxy shear ~500 N for a ~Ø4×8 mm sleeve. This is an estimate, not a datasheet figure. [C] check against the chosen epoxy.

## Display stack (front to back)
- [Ed] Four TRS jacks at x = -17.25, -5.75, 5.75, 17.25, y = -50 (11.5 mm pitch), over the bottom of the clear OLED.
- [Ed] Clear monochrome OLED, 42.0 x 27.2 mm, on the PCB front over a cut-away window. Position unchanged.
- [Ed] PCB cut away behind the OLED (window ~38.4 x 24).
- [Ed] Back AMOLED, 38.7 x 51.6 mm, full size, on the cover floor facing forward. Only the part below y ~ -21 is visible past the knob. The rest is deliberate, for glimpses at the top.
- [Ed] H7B0 drives both displays; firmware layers the visuals.
- Hard limit, stated once: a transparent OLED passes ~40-50% of light, so the back screen is dimmed. Accepted.

## Connectors
- [Ed] Jacks wired with twisted flying leads. Firmware detects mono/stereo (a mono plug grounds the ring). ~1 kOhm series resistor on outputs.
- [Ed] One 14-way signal plug plus a separate 2-pin power plug (>= 3 A), on the PCB back, reached through a notch in the bottom PCB edge.
- [Ed] USB-C is power-only (PD), on its own small board glued behind the faceplate, centred at x = 0, y = -58.5, between the bottom bolts. PD controller on the main PCB.

## Open checks
1. Outer jacks vs bottom bolt bosses: 0.67 mm with a 3.9 mm bezel, ~0 with a typical 8 mm hex nut. Needs the real jack part. Fix: move bottom bolts out ~1.5 mm or use a smaller nut.
2. Jack bodies vs USB-C board overlap ~2.5 mm (jack body assumed 12 mm tall). Fix: USB-C board ~6 mm tall.
3. AMOLED corner to bottom bolt boss 1.1 mm. AMOLED flex tail and connector side unknown. Needs datasheet.
4. AMOLED upper area sits behind the encoder gear and bearing. Cover clears them by ~2.1 mm. ~1.6 mm left after the screen. Do not shrink the cover depth.
5. Jack nuts hide the bottom ~4.8 mm of the clear OLED (visible height ~22 mm).
6. Clear OLED flex tail: place it so it reaches a PCB connector without crossing the window.
7. Resin boss root fillets and ribs. UV coupon and dark control shell. Sleeve epoxy selection.
8. Rear parts (encoder gear, feel gear) vs the bolt tubes.
9. H7B0 pin plan and power budget with two displays. USB-C PD sizing.
10. Jack part (PJ366ST unverified), panel holes, 14-way and 2-pin part numbers.

## Next
- PCB routing and slots: slots first, then route around them (to be agreed).
- Read sub/pcb-lighting-v01 (PR #8) before any PCB work.

## Update, 2 Nov 2026 (later): top bolts, lasers, joystick requirements
- [Ed] Laser placeholders removed from the case model (scanner is parked). Done on branch sub/case-v02 (not merged).
- [Ed] The case's side-access cross pins are removed too. The joystick v0.4 carries its own Ø1.2 cross pins in a rear anchor glued to the PCB back, so the case ones are obsolete. Done on sub/case-v02.
- [Ed] Top bolts go to the top corners (the bottom pair already sit at the bottom corners). The y position is a placeholder that mirrors the bottom pair (about y = 34.9). Not yet in the CAD.
- [Ed] Knob, joystick screen and OLED to move down on the panel so all four rail screws fit. The bezel lip, not the hole web, sets the amount: about 4 mm (the estimate of 3.4 mm earlier today was too small). Not yet in the CAD.
- [Ed] Back screen stays as the current AMOLED. A second layer in front of it is wanted for depth. Candidates: a small colour screen about 30 x 18 mm halfway back, or an edge-lit etched acrylic sheet (no driver, transparent). Not chosen.
- [C] Top-corner posts merge into the side wall and stop below the joystick slab (about z 30, read from the section picture, not measured).

### Requirements on the joystick redesign (PR #5), not applied
- The v0.4 carrier is 57.7 x 42.8 mm, wider than the 50.5 mm panel and the 44.7 mm cavity. It must fit inside about +/-21.4 mm in X.
- Keep clear of the top-corner post volume: x 15.45 to 24.45, y 30.4 to 39.4 (placeholder), below about z = 30.
- Nearest M2 riser to a Ø9 boss there is about 0.4 mm clear.

### Corrections to the open checks above
- The model's bosses are Ø9, not the Ø7 assumed in items 1 and 3. At Ø9 the outer jacks (7.8 mm nut) overlap the bottom bosses by about 0.3 mm. The brass-sleeve design may let the boss shrink. Not decided.
- The jack part in the model is the Thonkiconn PJ398SM (6.0 mm hole, 7.8 mm nut).

## Update, 2 Nov 2026 (early morning): mechanism, motors, screens, build plan

### Source of truth
- The latest CAD is **v0.18** on `sub/assembly-v017` (with `sub/review-v017` on top). It was never merged into `param-dev`, which still describes v0.16b. Several numbers above came from v0.16b and are redone on v0.18 in the merge.
- [Ed] Merge order: v0.18 (`sub/assembly-v017` + `sub/review-v017`) is the base, the parked review patch is applied, then the case work (`sub/case-v02`), then the joystick redesign, then the PCB regenerated for the H7B0. Everything lands in `param-dev`; nothing goes to `main` without Danny's sign-off.
- [Ed] Faceplate height: v0.18 wins (38.8 mm above the PCB front, from `knob_proud` 18). The case model follows it.

### Case and display
- [Ed] Knob bolts are removed from the case.
- [Ed] Four PJ366ST jacks; until a real part arrives, use the clacktronics/AudioJacks STEP dimensions (MIT, credit Barwise).
- [Ed] Back screens: two AMOLEDs overlapped, lower screen in front, upper behind on the cover floor. Screen order stays.
- [Ed] Minimum air gap from any part behind the PCB to a screen: **1.0 mm**. The cover depth is worked out backwards: deepest stack + 1.0 mm. No fixed number.
- [Ed] Claude picks a stock M3 brass sleeve and shrinks the Ø9 bosses to suit (also clears the outer jack nuts).
- [Ed] Joystick keeps the DWO DO0164FMST05. The bezel gets a finger chamfer. A smaller panel is parked (candidate: Gesight 1.47" E1473AC63.B).
- [Ed] See-through zones (sketch only, `zones_layers.png`): layer 1 = A to E, layer 2 = parts that may be printed clear, layer 3 = reserved board. Zone contents and the case cut-aways for strength are parked until the end.

### Control dial
- [Ed] Travel **±10°** (v0.18 already has it; hard stop ±10.61°).
- [Ed] **One** spring-ball detent with three dimples (0, ±10°). Position is free: place it where it packs best.
- [Ed] The arm sits on three small ball tracks (one under the detent, two about 120° round the hub) with **alternating big and small separator balls**.
- [Ed] Centre-screen cartridge hold-down: **two opposing magnets** (no steel disc), self-aligning. The Ø1 locating pin stays. Start from Ø2 × 1 N52 and size up only if the hold is weak. [C] Recompute the stray field at the Hall row.

### Drive and motors
- [Ed] The whole mechanism rotates so the **1220 main motor sits at the bottom (270°)**.
- [Ed] Encoder wheel at the **top**. Its pinion angle on the ring is chosen in CAD to keep it clear of the feel compound gear under the PCB. Keep the full-size wheel; the cover depth follows.
- [Ed] Drive stays geared: the 1220 planetary gives the torque. No direct-drive gimbal motor.
- [Ed] The 716 only takes up the gearbox slop and adds a little resistance. Target cost about $5; no premium motor.
- [Ed] The 716 keeps the v0.18 **two-stage** feel train (no planetary head on it, which would add slop). A shaft extension is accepted if needed. Rule: the compound gear under the PCB is **as big as the space allows**, and the motor pinion **as small as the gear check allows**.
  - Ballpark (assumed motor constants, to be replaced by the bench test): one stage gives about 0.7 mNm continuous at the knob; two stages about 2 mNm continuous and 8 mNm in bursts. An Alps RK09L pot is 2–25 mNm.
- [Ed] The 1220 (Industrial Pearl Store, 3–12 V, 30–123 RPM) and an N30 spare are on order. Danny bench-tests them; listing figures are not trusted. Test sheet: Claude Doc "Motor bench test sheet".
- [Ed] The 716's rear shaft (for a prism) is not a priority.

### Light show
- [Ed] Board light list: 12 red VCSELs + 12 RGB LEDs in the ring, one 405 nm Civillaser violet module, two Risley motors. **The spinning-mirror scanner, its 13th VCSEL and the grating are dropped.**
- [Ed] Risley: two cheap coreless motors spin two printed clear-resin wedge prisms. The beam scatters back up into the dial and out into the enclosure onto the Shimicoat glow coat. Claude finds the best fit in CAD. The prisms must overhang their motors so the beam clears the motor body. No speed sensors.
- [C] UTR-8100 transmission and yellowing at 405 nm: test with the UV coupon (405 nm module through a 2–3 mm coupon onto glow coat). Fallback: acrylic wedges.

### Screens (to verify)
- [C] Back AMOLED 38.7 × 51.6: best match is the 2.4" 450 × 600 RM690B0 family (e.g. Gesight B024JMV-N50-6DP0, 38.72 × 51.56 × 0.5). If confirmed: no QSPI (MIPI, SPI or 8-bit 8080), so drive both over the H7B0 FMC bus; it needs an ELVDD/ELVSS supply on the board; 45-pin flex.
- [C] Clear OLED 42.04 × 27.22: Waveshare 1.51" transparent 128 × 64 (SPI/I2C), lit area 35.05 × 15.32.

### Build plan approved (2 Nov, 05:20)
- [Ed] Claude may pick: sleeves, cartridge magnets, and materials from the existing recipe (MJF PA-12 gears and structure, SLA UTR-8100 clear parts, PETG cover), flagging any part without one.
- [Ed] Done means: STEP per part with material and process, a BOM, an assembly drawing, a pass/fail report, and a fresh-eyes review by a second agent. Claude may push to sub branches and `param-dev`; `main` only on Danny's sign-off.

## 2 Nov mid-morning (v0.19b)

### Knob glass and upper cap
- [Ed] The glass runs **right up under the dial** (top z 52.5, knob_run 0.3 under the dial lip). Both top edges get a **ground 45° chamfer**: inner 0.8 (the cap's cone seats on it, so the cap cannot go further down) and outer 0.6 (finished look). The **dial lip underside carries the same 0.6 chamfer** on its outer edge. Flat top face left: 0.75 nominal, 0.6 at the thin wall. The face stays open into the dial lip, so the emitter light still goes up the glass.
- [Ed] The upper cap is now a **thin dished web**: flat top under the dial web, underside tapering from 2.2 at the hub gear to 1.5 at the dial cup wall, then a flare (1.14 normal wall, 40°) out to the plug in the bore. It replaces the solid cone you could see through the glass.
- [C] The cap's height now follows the glass length and bore, through the chamfer seat. Print the caps to the measured tube (as already planned for the bore fit). The glass-to-dial gap is 0.3; a long or wide tube eats it.
- [C] Supplier: no glass supplier is recorded in the repo. Chinese borosilicate 3.3 makers (e.g. Fuxinag) cut to length and fire-polish (MOQ ~200, samples ~7 days, price on request). Ground inner/outer chamfers are a standard glass-machining step but are quoted separately. Fire polishing alone rounds the end and cannot make a crisp seat. Ask for: OD 42, wall 2.15 (2.0–2.3), length 47.45, one end ground with 0.8 × 45° inside and 0.6 × 45° outside (polished or frosted), other end fire-polished.
- Superseded the same morning: a 2 mm cap shoulder on a glass that stopped 2 mm short (still selectable: main_knob `cap_top="shoulder"`).

### Dial
- [Ed] **No thrust bearing under the dial tube**, just air (0.6 over the cradle). The 45° race on the knob carries the dial and the adapter board stops it lifting; the bottom bearing only fought the tolerance stack.

### Encoder bearings
- [Ed] Bearing bridge considered and dropped for now: forces are low and a bridge adds parts and probably cover depth (the wheel already sits 1 mm off the rear screen). Instead, bearing 2's printed seat gets a **locating spigot in the empty part of the H2 hole** (0.8 tall, between the bearings), so both bearings are coaxial with H2 by construction.

### Emitters and the thrust ring
- [Ed] The 716 driver (U20 DRV8837 + C20–C22) moves **inboard of the emitter ring** (mechanism frame U20 at (-8.5, 12.0), turned 45°, 3.6 mm from the 716 pads). The keep-out is gone: the outer thrust ring is a **closed cageless ring of 34 Ø2 load balls + 34 glass spacers**, and the **24 emitters sit every 15°** (pins in VCSELs 1 and 13, opposite). The balls roll past the emitters, so the old "emitter in a ball gap" rule no longer applies. KiCad: cad_constraints `drv` carries the new placement; design.py reads it.

### PCB windows
- [Ed] Cut now: **A, B** (rear screen, beside the knob top, ~5 × 5), **C, E** (front screen, beside the knob bottom, ~6 × 6) and **D** (38.4 × 23.5 under the clear OLED). Polygons are in electronics `pcb_windows` (panel frame; generator scratchpad `calc/windows.py`: 1.5 board rail, 1.0 round every obstacle). A 1.6 mm strip stays between C/E and D for the OLED ledge.
- [Ed] The **clear OLED** (42.04 × 27.22 × 1.25) sits on the PCB front over D, 1.6 mm ledge all round.
- [C] KiCad to follow: R20–R22 (I2C / INT pull-ups) and R30–R32 (encoder LED and pull-downs, which move to the top with the sensor anyway) sit inside D on the stale board and must move. Through A/B you will see the encoder wheel rim; through C, part of the feel compound gear.

### Labyrinth seal
- [Ed] An **opaque PETG ring bonded on the glass OD** closes the labyrinth: flange over the faceplate ring, skirt down outside it to the case's shoulder line (bore 22.05, 0.7 overlap). [C] It does not fit at the joystick: see the open question.

### Joystick in the knob assembly
- The joystick (cad/joystick-param) is now in the knob clash run and the section sheet. Its main-PCB holes (4 standoff screws, 4 hold-down springs) flow from the joystick build's geom.json into the PCB proxy and cad_constraints.
