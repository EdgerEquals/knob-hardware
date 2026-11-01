# Knob module: design notes (current: CAD v0.16, 1 Nov 2026)

A short summary of the current design. The parametric model in `cad/knob-param/` is the source of truth for
dimensions. Values marked [A] are assumptions that still need checking with calipers or on a prototype.
Renders: `cad/assemblies/knob-stack-v0.16/` (clean section + iso, opposite side, plan view, `check.json`).

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
  disc with a vertical slotted rim, read by an Omron EE-SX1131 on the PCB back. The old big-gear rim teeth were
  removed in v0.16 because nothing meshed with them.

## Stack (centre)
- **Fixed centre:** a brass 5×3 stock tube on the dial axis, knurled at the dial end. A printed square flange
  is bonded to the PCB. An M1.6 rod with a sleeve and nuts down the middle is the **centre bolt**: it clamps the
  stack (adapter board → tube → PCB).
- **Rod VBUS pad (v0.16):** the bottom nut clamps straight onto an enlarged B.Cu pad, Ø11.48 sized from the
  clearances in the model. There is no washer. KiCad still needs this change.
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
- The magnet's stray field at the dial TMAG5273 is 0.12 mT. It turns with the sensor, so it is a fixed offset
  that calibration removes.

## Control dial: Hall arm, detents, centring (v0.16)
- **Travel:** ±5°, latching. Overtravel of 0.5° runs onto magnet cushions, so the hard stop is at ±5.5°.
- **Hall vernier:** the arm comes straight off the dial hub through a wide cradle window.
  - 5 magnets over 5 TMAG5253 on the PCB at **2.5 mm pitch**, r 6.6–16.6.
  - Peak field 57.6 mT against a ±80 mT range.
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

## Relative knob-vs-dial sensor (v0.16)
- A diametric N52 ring magnet, Ø21/Ø19×0.5 (0.24 g), sits flush in the underside of the **main knob** web.
- A TMAG5273 3D Hall sensor faces down on a 4×6×0.6 board that **turns with the control dial**. The board sits
  in a generous pocket through the dial web at r 10 so it is easy to assemble.
- The sensor reads the relative angle of the knob against the dial.
  - At the nominal 1.50 mm element gap the field is 34 mT (42% of ±80 mT).
  - With the dial lifted to its stop (1.20 mm gap) it is 48 mT (60%).
- The board needs its signals carried over the screen service strap. The screen-adapter board no longer
  carries U3.

## Check status (v0.16)
- 54/54 gap checks PASS.
- The contract check passes.
- One known clash remains, PCB / motor (4.24 mm³). It is a proxy artefact.

## Open items
- **KiCad:** the Hall row pitch (2.5), the enlarged rod pad, the feel motor pads, dropping U3 from the screen
  adapter, and the new dial sensor board.
- The ±5.5° travel was an interface change (from ±10°) and needs confirming.
- Inside the closed lip, about 0.9 mm of the bend pocket shows at −X.
- Spring sourcing: the detent springs and the extension springs must be non-magnetic (stainless 316 or
  phosphor bronze).
- Motor depth and the final feel come from tests with the real motors.
