# Knob module: design notes (current: CAD v0.18, 1 Nov 2026)

A short summary of the current design. The parametric model in `cad/knob-param/` is the source of truth for
dimensions. Values marked [A] are assumptions that still need checking with calipers or on a prototype.
Renders: `cad/assemblies/knob-stack-v0.18/` (preview, clean section + iso, plan view, `check.json`); v0.17 kept in
`cad/assemblies/knob-stack-v0.17/`. Top-screen joystick stack: `cad/assemblies/joystick-v0.1/` (see
`docs/top-screen-joystick.md`).

## Faceplate (Ed)

`knob_proud = 18.0` mm is the height of the knob screen top above the faceplate front. The screen top is `z_glass`
(56.8). The faceplate front is **38.8 mm** above the main-PCB front (z = 0). Thickness is **2.5 mm**, the case
resin wall, so the back face is at 36.3. Both are in `cad_constraints.json` (`faceplate_z`, `faceplate_t`) for
`sub/case-v01`. The knob shell top stays at 52.5, which is 13.7 mm above the plate.

The old layout constant put the panel front at 20.2. This plate is 18.6 mm further from the PCB. On joystick
v0.4 the plate was derived at 45.98 (bezel under a screen 5 mm below the knob shell). Measured to the screen
top, that plate left the glass 10.82 mm proud. The new plate is **7.18 mm closer to the PCB** than that one.

Joystick v0.1 in this tree follows the plate: screen top 38.8, daughterboard at 27.10 (was 8.5). The soldered
J2 socket stays the 8.5 mm FG part. A printed extender of 18.6 mm fills up to the board, and the stem keeps
its 1.35 mm of air under the carrier. Hold-down springs grow from about 42 mm to about **60 mm**.

The 35 mm standoff does not fit the new plate. Joystick v0.4 raises the daughterboard on four **XHHD DTTZ3033**
male-female standoffs, hex H3 × M2 × **35+4**, LCSC C50377642. The 35 mm body is the riser. Keeping the same
1.28 mm of air under the carrier, the body has to be **27.82 mm**. The 35 mm part is 7.18 mm too long: the
stem would stand 5.9 mm through the carrier. A 30 mm body is still about 2.2 mm long. The Samtec TSW-103-20-T-S
mating pin (25.91 mm) enters the 11 mm H11 socket by 4.45 mm at a 35 mm riser, which is inside the 3.5–6.5 mm
window, and by 11.63 mm at 27.82 mm, which is not. The 35 mm body and the -20 pin are a pair. No replacement
catalogue number is assigned here. The main PCB was not edited.

## v0.18 gear train (Ed, 1 Nov 2026)

PCBWay makes the parts: MJF PA-12 for every gear, SLA clear resin for the caps. The Kingtech 1.39" screen is unchanged in this pass, so the knob stays **Ø41.65**.

- **All gears are nylon** (PA-12 MJF). The two motor pinions keep the Tempero 0.5M-12T and RW m0.6 14T tooth forms, printed rather than bought in brass. Spur backlash is 0.10 mm total, split half on each member. Herringbone backlash is 0.10 mm shared.
- **25° herringbone**, normal module **0.67 mm** (the coarsest that still clears the 1220, keeps a 12-tooth pinion, and a ≥1.0 mm ring wall). Transverse module 0.739. Normal pressure angle 20°. Stub addendum 0.80 so the 12T tip stays above the MJF floor. Internal ring **51T**, split into two axial halves with a 0.40 mm gap at the apex (z 3.5); a herringbone cannot drop in axially. Pinion tip thickness **0.626 mm** (floor 0.50). Ring wall **1.14 mm**. Virtual teeth 16.1; the floor Ed set is 12, and 12 meets it. MJF ±0.25 mm is larger than the 0.10 backlash, so the mesh is tuned on the part.
- **Centres.** Encoder / idler centre distance **14.42 mm** (was 15.25, the KiCad H2 press). Skirt ID Ø36.63. The committed STEP's H2 is drilled at the new axis in `--full` only; the KiCad board still has the old hole.
- **Feel train.** Nylon 12T m0.5 × printed 44T m0.5 on the 150° idler, then 51/12. Overall **(44/12)×(51/12) = 15.58:1**. The 716 stays shaft-down; the pinion is under the PCB. Thinnest nylon spur tip **0.384 mm** (the 12T; floor 0.30).
- **Hub.** Nylon 14T m0.6 × 22T, ratio **1.571**, centre distance 10.80 against the KiCad motor at 10.75 (0.05 mm tight, inside the 0.10 backlash). Tip Ø9.36 on the pinion, Ø14.16 on the hub gear.
- **Axial load** stays on the flat outer thrust race. The pinions locate the knob radially.
- **Clear resin caps** (PCBWay UTR-8100), separate prints, stepped Fresnel rings (disk 0.40 mm, up to 3 rings 0.16 mm high by 0.42 mm wide). They press or snap on a free face or hub. The model leaves 0.04 mm radial and 0.02 mm axial so the press is not a clash. Nearest cap-to-neighbour gap **0.43 mm** (feel-pinion cap vs the 44T).

| Gear | Teeth | Tip Ø | Shaft / pin | Cap |
| --- | --- | --- | --- | --- |
| Hub gear | 22T m0.6 straight | 14.16 | dial tube, bore Ø8.62 | no — the top face is the knob web |
| Motor pinion | 14T m0.6 straight, nylon | 9.36 | Ø3 with a flat (1220) | no — 0.50 mm under the web, less than a cap plus 0.30 clearance |
| Internal ring | 51T 25° herringbone, two halves | 36.63 inner | — | no — the knob body sits on the top face |
| Encoder pinion | 12T 25° herringbone | 9.94 | Ø2 shaft | yes, Ø6.70 on a Ø2.7 pip on the top face |
| Idler 1 | 12T 25° herringbone | 9.94 | Ø1.5 pin, head Ø3.5×0.5 | yes, Ø6.70, bore clears the head |
| Idler 2 (compound small gear) | 12T 25° herringbone | 9.94 | same pin | yes, Ø6.70 |
| Compound spur | 44T m0.5 | 22.80 | Ø1.5 pin | no — 0.30 mm to the PCB parts above and to the encoder rim below |
| Feel pinion | 12T m0.5 straight, nylon | 6.80 | Ø2 shaft | yes, Ø4.35 on the free underside |

Eight toothed wheels. Four take a cap. The two Risley motors are not in this pass; their caps are the wedge prisms in the optics round.

## v0.17 changes (Ed, 1 Nov 2026)

Ed's markup of the v0.16b plan (yellow) was the skinny cradle around the top gears. The cuts below only open those ligaments.

- **Lip wall 1.2 mm** [Ed], three 0.4 mm nozzle lines, thickened outward. Knob OD derives to **Ø41.65** (minimum 41.641). Far-side wall 1.205, wall outside the COF-bend pocket 1.205, near side 2.24. A check requires printed lip walls ≥ 1.0 mm.
- The bottom ring stays **75T** [Ed: clear the existing ring; the encoder stays on the H2 press]. The extra OD is skirt wall (2.58 mm from tip to OD). Skirt ID Ø36.50.
- **Dial travel ±10°** at the detents [Ed]. The hard stop is derived a ball-bore-play past that: **±10.61°**. Hall curvature follows: g = 1.06 °/mm, radial pitch stays 2.5, magnet radii 6.6–16.6. Poles stay N/S/N/S/N. Middle sensor stays the TMAG5273A2, the other four TMAG5253BA3. Fields still pass: TMAG5253 peak |Bz| 46.0 mT (≤ 72), TMAG5273 worst axis 83.9 mT (≤ 119.7), angle noise 0.004° rms.
- **Cushion magnets removed.** Spring-ball detents latch at the centre and at both ends. They sit inboard of the pinion tips (r 9.45, ±40° from the Hall arm): at ±10° the old fan-wing seat between the Hall window and the pinions has no overlap. Hard stops kept.
- **Hall-arm rib** [Ed]: width 3.0 at the hub to 5.2 at the hammerhead (r 13.85), on to r 17. Top at the lever top (z 6.8). Bottom stays z 4.6 over the thrust cage and drops to z 3.8 beyond r 4.95. In-plane tip deflection under 2 N at r 15.5, PA12 E 1.7 GPa: **0.060 mm** (limit 0.07).
- **Cradle:** no big cut. The ligaments where the 54° and 150° idler pockets break the OD are opened at the narrowest point with R0.5 fillets, leaving a 1.2 mm web round each pin. The feel pinion is no longer in that plane (it moved under the PCB), so that bridge went away with the pocket. The Hall window is one smooth offset of the swept bar, even clearance, not the old stepped zig-zag.
- **Outer thrust** [Ed]: flat horizontal race, no 45° faces. Ø1.5 steel balls on r 19.54, between a torus groove in the skirt underside and a carrier printed as part of the cradle (located on the centre-tube clamp and the existing encoder Ø5 press; no new PCB holes). The carrier skips 124–137°, the C20–C22/U20 keep-out. Floor under the seat is 1.0 mm. Radial land in the skirt wall is **0.51 mm** — see open items. The 45° cone race between knob and dial is unchanged; this race takes the vertical clamp load, and the pinions locate the knob radially.
- **Screen carrier** [Ed]: the Ø2×1 magnet and steel disc are two Ø3×1 N52 magnets facing each other (attracting), one in the carrier and one in the dial shoulder, at 90°, opposite the Ø1 pin at 270°. Stray field at H3 is 0.016 mT.
- **Feel second stage** [Ed], no extra shaft. The 716 stays at 102°, shaft down. The 150° idler (the one away from the 1220) is a compound gear: its 14T stays in the 75T ring, and a printed 32T m0.5 gear on the same pin, under the PCB, is driven by a **KHK DS0.5-15** POM pinion (Duracon, bore Ø2, face 3, hub Ø4.5×4). Brass alternate: KHK BSS0.5-15A, bore Ø3. Overall ratio **(32/15)×(75/14) = 11.43:1**. Centre distance is 0.015 mm tight of nominal, inside the tooth-backlash relief. The 716 shaft stick-out to the bottom of the pinion is **12.2 mm**.
- **Encoder:** the compound gear occupies the old disc depth, so the disc and the EE-SX1321 drop **3.6 mm**. The sensor sits on a small daughterboard (0.8 mm) on a header and two standoffs. CAD proxy only. KiCad is not done: see open items.

## v0.16b changes (Ed, 1 Nov 2026)
- **Relative knob-vs-dial sensor removed** (duplicate of the encoder + Hall row): no ring magnet in the knob, no
  TMAG5273 board or pocket in the dial. The code is kept behind `rel_sensor` (False).
- **Middle Hall-row sensor (H3) is now a 3D TMAG5273A2** (SOT-23-6), the other four stay TMAG5253. Pitch 2.5 kept.
- **Hall magnets alternate N/S/N/S/N** (`hv_pol`, face down toward the sensors).
- The SOT-23-6 is 1.45 tall against 0.4 for the X2SON, so the magnet bar went up 0.15 (faces at z 1.75):
  0.30 air gap over the TMAG5273, 1.35 over the TMAG5253s.
- Fields: TMAG5253 peak |Bz| 45.7 mT (57% of ±80; was 57.6). TMAG5273 at a 1.10 element gap: |Bz| ≤ 83.6,
  |Bx|,|By| ≤ 29.0 mT. That saturates the ±80 mT A1, so the **A2 (±133 mT)** is specified (63%).
  Angle noise is still 0.002° rms worst case.

## Product
- A standalone motorised-knob MIDI + CV controller in Eurorack, **10HP** (50.5 mm), one knob unit in the upper
  half of the 3U panel. It grows into a node of a larger system later (rear bus + clock connector reserved).
- Panel, top to bottom: the top screen on its joystick carrier, then the dial (bezel/control dial around the big
  motorised knob, a round screen in the centre), then a clear layered optical panel with a 2.0" 320×240 IPS TFT
  mounted on the main PCB behind it (air gap, not bonded), then three stereo jacks and a USB-C in one row.
- Jacks (Thonkiconn stereo): J1 tip dial CV out / ring bezel CV out; J2 tip CV in (the motor follows it) / ring
  gate out (button); J3 tip motor-voice audio in / ring motor-texture audio out. No jack switches role.
- USB-C carries MIDI and PD power (9–15 V negotiated). Dual input with the Eurorack bus (the bus has priority
  when racked), ±12 V generated for CV on USB power, and USB ground isolation away from the audio path.
- Optical panel: a laminate (AR glass, etched mask, phosphor zones) edge-lit by recessed 365 nm UV LEDs, driven
  by linear constant-current (no PWM). The screens show an *analogy* of the parameter being changed.

## Motor, feel and sensing
- **Main motor:** a 1220 coreless planetary (N30 as a parameter swap), offset from the dial axis and soldered to
  the main PCB by its tabs. Its 19T pinion drives the 24T knob hub gear (m0.5, ratio 1.263).
  The design is motor-agnostic: the encoder reads the dial, not the motor, and boot calibration learns
  backlash and speed as ratios.
- **Electronic clutch (no mechanical slip clutch):** the motor assists the direction the hand moves, using
  the encoder plus gearbox backlash, so the hand can lead. Current sensing plus a thermal probe drop it to
  freewheel on a sustained stall, and the screen says why.
- **Motor voice:** a switchable mode in which audio is modulated onto the motor drive and recorded back through
  back-EMF sensing and a contact mic. A bypassable filter keeps the normal mode quiet.
- **Feel motor (v0.16):** a 716 coreless, axial and inverted (shaft down) inside the base cradle at 102°,
  between the bottom-ring idlers at 54° and 150°. It has its own 22T pinion into the 75T bottom internal ring
  (ratio 3.41). It is held by an **open saddle clamp**: an inboard seat (2 bands + spine onto a cradle rib) and an
  outboard strap (2 × 1.2 mm C-bands, ears + M1 screw). Most of the can stays open for airflow.
- **Position encoder:** a 14T pinion in the bottom ring drives a shaft (2 × F682ZZ) through the PCB to a plain
  disc with a vertical slotted rim, read by an Omron **EE-SX1321** on the PCB back (main PCB v0.11, 1 Nov 2026; it
  replaces the discontinued EE-SX1131). The old big-gear rim teeth were removed in v0.16 because nothing meshed with them.
  - EE-SX1321 (datasheet): body 5.1 × 4 × 4, slot 2.0 ±0.2 wide and 2.8 deep, optical axis 1.0 below the open face, two
    0.3 × 1.0 detector apertures 0.8 apart along the slot. Pins: 1 anode, 2 + 3 cathode, 4 E2, 5 E1, 6 collector
    (common). Net map: 1 ENC_LED (220R to 3V3, IF ≈ 10 mA), 2/3 GND, 6 +3V3, 5 ENC_A, 4 ENC_B (10k loads to GND).
  - Fit: the 1.2 rim sits in the 2.0 slot with 0.4 a side (0.3 at the slot's −0.2 tolerance), its tip 0.6 short of the
    slot floor; 119 windows at 1.067 pitch put the 0.8 aperture spacing at 3/4 period (quadrature). The disc face
    clears the sensor's open face by 0.30. The model uses the 1321 body (`under_pcb` `sens.body_x` 5.1).

## Stack (centre)
- **Fixed centre:** a brass 5×3 stock tube on the dial axis, knurled at the dial end. A printed square flange
  is bonded to the PCB. An M1.6 rod with a sleeve and nuts down the middle is the **centre bolt**: it clamps the
  stack (adapter board → tube → PCB).
- **Rod VBUS pad (v0.16):** the bottom nut clamps straight onto an enlarged B.Cu pad, Ø11.48 sized from the
  clearances in the model. There is no washer. In KiCad (main PCB v0.11, H1 B.Cu ring).
- **Dial-centre link:** one PTFE wire down the tube carries power and data (single-wire, LIN/1-Wire style),
  with the brass tube as the ground return. A CH32V003 on the adapter board behind the centre screen splits
  them. No slip ring, no wireless.
- **Adapter cup removed (v0.16):** the centre bolt clamps the adapter board directly. The board doubles as the
  dial's up-stop with 0.3 mm of free lift. The 45° ball race carries the knob's up-load into the dial. The race
  and hub did not move.

## Knob size (v0.16)
- The knob grows only as much as it has to: it must clear the AMOLED FPC/COF bend and leave a printable lip wall
  of **0.8 mm (2 × 0.4 nozzle lines)** all round.
  - Minimum Ø40.841, rounded up to **Ø40.85**.
  - The bottom ring goes 73T → **75T**.
- The screen sits 0.515 mm off-centre to balance the walls.
  - Lip wall: 0.805 far side, 0.805 outside the bend pocket, 1.84 near side.
  - The lip is a **closed ring**. The bend sits in a blind pocket that is open to the top.

## Screen carrier cartridge (v0.16)
- The centre screen and carrier lift out as one cartridge.
- Location: a Ø1 locating pin at 270°.
- Hold-down: a Ø2×1 N52 magnet in the dial at 90° (r 15) pulls on a Ø2×0.5 steel disc in the carrier.
- Removal: a suction cup.
- v0.16b: with the dial TMAG5273 gone, the nearest 3D sensor is H3 on the PCB, about 50 mm away. The stray field
  there is 0.004 mT, which is negligible.

## Control dial: Hall arm, detents, centring (v0.16)
- **Travel:** ±5°, latching. Overtravel of 0.5° runs onto magnet cushions, so the hard stop is at ±5.5°.
- **Hall vernier:** the arm comes straight off the dial hub through a wide cradle window.
  - 5 magnets (N/S/N/S/N) over 4 TMAG5253 + 1 TMAG5273A2 (middle, H3) on the PCB at **2.5 mm pitch**, r 6.6–16.6.
  - Peak field 45.7 mT against ±80 mT at the TMAG5253s; 83.6 mT against ±133 mT at the TMAG5273A2 (v0.16b).
- **Fan:** the arm widens into a sector toward the perimeter (r 13.85–17.25, ±38°). This spreads the detents.
- **Detents:** two top-loaded spring-ball detents at ±26.8° from the arm (r 15.55). Each is a Ø1.5 ball,
  a 1.4×3 spring (0.8 preload) and an M2×2 grub screw (±0.6 adjustment). They sit in bosses bridged over the fan
  and latch into dimples in the arm at 0 / ±5°.
- **Ball track:** Ø1 balls (2 per detent) in grooves in both the cradle plate and the underside of the arm.
  They take the detent press-down load.
- **Centring:** two tangential **non-magnetic extension springs** on a lever at 276°, on the side away from the
  Hall window, hooked to posts on the cradle. The old Ø10 centring magnet is gone.
- **Cushions:** 3 × Ø1.5×0.5 N52 magnets, set to repel, give a soft end before the flush hard stop. Stray field
  at the nearest Hall sensor is ≤ 1.67 mT (2.1% of range).

## Relative knob-vs-dial sensor (v0.16, REMOVED in v0.16b)
- A diametric N52 ring magnet, Ø21/Ø19×0.5 (0.24 g), sits flush in the underside of the **main knob** web.
- A TMAG5273 3D Hall sensor faces down on a 4×6×0.6 board that **turns with the control dial**. The board sits
  in a generous pocket through the dial web at r 10 so it is easy to assemble.
- The sensor reads the relative angle of the knob against the dial.
  - At the nominal 1.50 mm element gap the field is 34 mT (42% of ±80 mT).
  - With the dial lifted to its stop (1.20 mm gap) it is 48 mT (60%).
- The board needs its signals carried over the screen service strap. The screen-adapter board no longer
  carries U3.

## Check status (v0.18)
- **69/69 gap checks PASS, 0 clashes** on the proxy and on `--full` (committed STEP, with H2 re-drilled at the new centre distance). Owner split: main_knob 4, control_dial 17, base_drive 14, under_pcb 2, electronics 2, assembly 30. The AGENTS.md tally is taken from `cad/assemblies/knob-stack-v0.18/check.json`.
- Swept samples are −10.75°, −10°, 0, +10°, +10.75°.

## Check status (v0.17)
- **62/62 gap checks PASS, 0 clashes** on the proxy and on `--full` (committed main-PCB STEP). Owner split: main_knob 3, control_dial 17, base_drive 11, under_pcb 2, electronics 2, assembly 27. The AGENTS.md tally is taken from `cad/assemblies/knob-stack-v0.17/check.json`.
- Swept samples are −10.61°, −10°, 0, +10°, +10.61°. Centring springs follow the lever pin; track balls roll at half the dial angle.
- The contract check passes.
- `--full` drills the two new NPTHs into the committed STEP so the 716 shaft and the compound pin are not a false clash; the KiCad board does not have those holes yet.

## Check status (v0.16b)
- 54/54 gap checks PASS (the two dial-TMAG5273 rows are replaced by the TMAG5273 air-gap and field rows).
- The contract check passes.
- No known clashes: the PCB / motor proxy clash (4.24 mm³) is gone now that the proxy carries the KiCad M1 Ø3.2 relief
  (`electronics/kicad/knob-main-pcb/pcb_proxy.json`). `build.py` and `build.py --full` both give 54/54 PASS.

## Open items
- **Optics and materials round is next** (gear round is in v0.18). No laser bodies, mounts, or coats are in the CAD yet. The Risley caps will be the printed wedges, each no wider than its motor.
  - **Lasers, two types only. No green lasers.**
    1. One Civillaser 405 nm violet 1 mW dot module, body **Φ8×31 mm**, 2.8–5.2 V, under 55 mA, no TTL pin. A second module is a bench spare and is not modelled. The G4 pulses the fitted module with one supply MOSFET. The Risley scanner is that one beam through two wedge prisms, each prism spun by its own small motor. The beam lands on Shimicoat green strontium aluminate (Bibra Lake, Perth): a light coat on the dial lid, a heavier coat on the enclosure walls.
    2. Twelve 665 nm red SMD VCSELs under the clear SLA bearing carrier (JNJOPTO JNJ-V-2835CW-665003-S-D1, LCSC C42375664), alternating with 12 addressable RGB LEDs (one chain, one data pin). One red VCSEL on at a time, shared hardware current limit, one low-side MOSFET each, driven directly by the G4. LCSC lists Vf 2.5–2.8 V, threshold 4 mA, 16% efficiency, and no optical-power curve, so the first articles have to be measured and the set current dropped if the output is over 1 mW.
  - Knob shells stay see-through. The carrier is clear SLA, standard finish, not frosted and not polished. Every beam ends on a glow, fluorescent, or diffusing surface. Class 1/2 at ≤1 mW, default off, stall cut-off. When the round starts, the one fitted violet module and its mount are modelled at Φ8×31 mm. The spare is not.
  - **Race vs clear resin.** Seat floor under the Ø1.5 balls is 1.0 mm. Radial land is 0.48 mm a side, under a clear-resin wall. Thicken the land to at least 1.0 mm, or fit a hard insert that still lets light through to the balls, before that race is resin.
- **MCU (decided, board not changed).** The module MCU is the shared STM32 G4 on the bottom board (FDCAN, spine clock, USB-C PD on UCPD). The CH32V003 on the screen adapter only bridges the one data-over-power line down the brass tube. No lighting MCU and no selector chip. One violet supply MOSFET, so the pin list is **62** including SWD. STM32G474 LQFP64 has 52 I/O and does not fit. **STM32G474VET6, LQFP100, 86 I/O** does (Quad-SPI, 3× FDCAN, USB, UCPD, 512 KB flash, 128 KB SRAM), with about 24 pins spare. The panels have their own GRAM, so the G4 is not short of RAM.
  - **Power, every load switchable and off by default** (motor currents still assumed). Idle, loads off: about **8 mA**. Typical, one screen modest, Hall and encoder on, one red VCSEL, LED chain dim, motors and the violet module off: about **110 mA**. Peak, both screens bright, main motor moving, feel and both Risley motors spinning, one red VCSEL, the one violet module on (under 55 mA), LEDs under a firmware cap: about **0.65 A**. The 1220 stall and a full-white LED chain (about 0.7 A by itself) are what the firmware and the motor driver have to keep down.
  - **Race vs clear resin.** The seat floor under the Ø1.5 thrust balls is 1.0 mm (`ot_floor`, set by `print_wall_min`). The radial land beside that groove is **0.48 mm** a side (`ot_land`). PCBWay SLA is usually held to about a 0.8 mm wall, with 1.0 mm the comfortable figure; their clear-resin page does not publish a separate number. The 1.0 mm floor is on that line. The 0.48 mm land is not. Clear resin is also brittle and wears under a steel ball, so the rolling surface should not be bare resin at this land. Next round: thicken the land to at least 1.0 mm, or drop in a hard insert (steel or PA12) that leaves a clear path so the light still reaches the balls. Until one of those is done, the race is not a clear-resin part.
- **Dial screen, next knob round (not switched yet).** Kingtech 1.39" RM69330 stays the model in this pass. Next: DWO DO0132FMST01, 1.32" round AMOLED, 466×466, CO5300, QSPI (IM1 high, IM0 low), one 3.3 V rail and PWR_EN, no 1.8 V regulator or level shifters. FPC header Panasonic AXE630124, 30-pin 0.4 mm, same as the joystick's DO0164FMST05; socket AXE530127 (LCSC C425103). DWO's page also lists touch (FT3168) and 600 nit; touch is not adopted here. Outline about Ø36.35 and active area about Ø33.55 are Ed's figures — the 2D drawing is not in the tree. With the current 1.2 mm lip, a 0.8 mm bend and an assumed 12 mm ledge, the lip balancer lands near **Ø39.7**, so Ø39.5 is only there if the bend or the ledge is smaller. **Assumed until the drawing is in:** FPC tail length, width, thickness and stiffener, where the 0.8 mm bend is measured, ledge width, and module thickness.
- **KiCad for v0.17 (not done):**
  - Main PCB: NPTH for the 716 shaft at the 102° axis (Ø1.6) and for the compound idler pin at 150° (Ø1.8). The proxy and the `--full` STEP have these holes as a CAD drill only.
  - Replace the EE-SX1321 footprint with a header for the encoder daughterboard. New board: small riser, 0.8 mm, the EE-SX1321, a 1×6 2.54 mm header and two standoffs, dropped 3.6 mm so the slot meets the rim. Schematic, footprint, fab pack.
  - Hall row pitch and the 2.5 mm spacing are unchanged; no Hall footprint move.
- **716 shaft:** the catalogue pinion needs **12.2 mm** of shaft below the can. A stock 716 shaft is shorter. Needs a long-shaft variant or a pressed extension. The pinion bore is Ø2, so the Ø1 shaft also needs a Ø2/Ø1 sleeve.
- **Thrust land:** the Ø1.5 groove in the 75T skirt wall has **0.51 mm** of radial land each side. The lip wall is 1.2 mm; this land is not. A smaller ball or a local skirt thickening would fix it.
- **Centring hardware moved** so ±10° fits: lever at 296° (was 276°), spring hook-to-hook 2.6 mm (was 4.5), lever width 1.6 mm (was 2.4), anchors above the lever. Worth a check on the real spring.
- **Detents** are inboard (r 9.45) because the fan wings cannot hold ±10°. Confirm the feel is what Ed wants there.
- **KiCad (1 Nov 2026, v0.16b, still the boards in the tree):** main PCB v0.11 and screen adapter v0.4 match v0.16b (Hall row, rod pad, 716 lead pads +
  DRV8837, joystick J2/holes/slot/keep-out; U3 removed from the adapter). Main PCB v0.11 is **READY TO QUOTE**: U2 is
  now the EE-SX1321 (LCSC C469128) and J2 the FG FG-PM2.54-2-03P-H8.5 (LCSC C42391433); routed, ERC 0 / DRC 0, every
  BOM line has an LCSC part. Still open: the MCU section (J10 is a placeholder test-pad field with an assumed pin-out),
  the 1220 driver, and the adapter's display-tail wiring / VCC regulator (adapter is placed, not routed).
- TMAG5273 Hall-element height (0.65 above the PCB) is assumed. Check it against the TI drawing.
- v0.17 puts the dial back to ±10° (hard stop ±10.61°). The old ±5.5° question is closed.
- Inside the closed lip, about 0.9 mm of the bend pocket shows at −X.
- Spring sourcing: the detent springs and the extension springs must be non-magnetic (stainless 316 or
  phosphor bronze).
- Motor depth and the final feel come from tests with the real motors.

## Top-screen joystick v0.1 (1 Nov 2026)
See `docs/top-screen-joystick.md` and `cad/joystick-param/`. The carrier centre is board (25.25, 21.1) and knob frame (0, 31.8).
The carrier slid toward the knob clears the live knob OD (Ø41.65) by 0.275, short of the 0.5 target. `place_y` is still the v0.1 figure that cleared Ø40.85 by 0.675, and it was not moved. The main PCB v0.11 carries the J2 socket (FG FG-PM2.54-2-03P-H8.5),
the spring/pin holes, the FPC slot and the base keep-out (listed in that doc).
