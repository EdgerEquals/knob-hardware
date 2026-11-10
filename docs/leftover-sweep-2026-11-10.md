# Leftover sweep (10 Nov 2026, model v0.55)

[Ed 12:05: "check that we haven't got anything left over ... from things we've changed"]. Four read-only sweeps (dial
mechanism; knob, case and assembly code; electronics and the KiCad boards; joystick) plus a scan for parameters nothing reads.
Nothing was changed by the sweep. Main findings were re-checked by hand (marked ✔).

## A. Physical leftovers (in a made part or board): Ed's call, one at a time

1. **Joystick hold-down spring holes overlap** ✔. The springs sit at y ±1.5 (`cad/joystick-param/jsparam/params.py:308`,
   `spr_xy`), moved from ±3.0 on 2 Nov 13:23 only to make room for the press-spring grub access holes. The grubs went in
   joystick v0.8; the springs stayed. The two Ø3.4 bores per side are 3.0 apart, so each pair is one figure-8 cut-out
   (3.4 × 6.4, 1.6 neck) on main board v2 (KiCad x 110.8–114.2, y 56.17–62.57, and the mirror) and on the joystick top board.
   The jumper's S2/S3 legs were also placed against the old grub line. Fix: springs to y ±2.0 (0.6 web) and move `jmp_y3`,
   or keep the slot.
2. **Knob collar under the faceplate** ✔. A Ø47.4 × 7.5 tube round the knob hole (`case/parts/shell.py:235`,
   `case/params.py:241`, `collar_h_mult` × the corner-screw Ø). Added in v0.1 for the labyrinth and the knob bolts; both
   gone (knob bolts removed 2 Nov, `knob_bolt_n=0`). The glass now runs 10 mm (not the faceplate's 2.5) through a bore with
   0.20 radial air. It also sets the joystick cradle flange's −y edge (`jsparam/params.py:1071`). Fix: `collar_h_mult=0`.
   Related: two hole clearances (`knob_rad_clear` 0.20 built; `knob_hole_clear` 0.4 exported, read by nothing).
3. **Dial detent pedestal grub and its Ø1.6 hole through the main board.** v0.22b job: "turn until the detent spoke just
   lifts off the knob race". The v0.25 dial split removed that ("the train-vs-race stack the pedestal grub was set against
   no longer fights the race"). Left: a ±0.25 height trim before bonding. Fix if unwanted: fixed pedestal, drop the grub,
   tapped hole, board hole (`sp_access_d`) and four rows.
4. **Hall rib root still stepped round the removed thrust cage** ✔ (`tb_on=False` since 2 Nov). r 4.06–4.94 the rib's
   underside stays at z 4.61 (`ha_rib_z_cage`). Run it at z 3.85 like the rest: stiffness 2.17x → 2.29x. The v0.15 Hall
   spoke is now inside the rib bar a 1.1 mm³ sliver; it can go too.
5. **Detent spoke step-up** at r 8.7 still clears centring-spring anchor post 2 (gone since v0.31). Harmless.
6. **Joystick cradle in the case** takes its height from the v0.8 bead (a 0.42 riser) and its plan from gasket-era rules;
   it leaves a 0.85 slot between the flange and the case's side wall. Unsure; Ed decides whether the flange joins the wall.
7. **Joystick top board length** still from the vertical boards' span + `tb_y_over`; the sockets end at y +2.78, the
   board at +8.17. Unsure (the switch and shoulder may need about +6.6).
8. **Glow coat** is cut over the whole joystick-hole outline from `z_ledge0` (from before the 4 Nov partial cut); the top
   lip has none. Bottom lip keeps a 0.10 sliver between two cuts.

## B. Model mistakes that can hide a problem (no made part changes)

- **Dial travel ±10.74° is computed from the v0.17 ear detent's radius** ✔ (`interface.py:629-641`): changing any of its
  dead inputs (`bt_rows`, `bt_row_pitch`, `fan_clear`, `bt_ball`) moves the stops, magnets and Hall sensors. Pin it at
  10.7388 [Ed 4 Nov 15:46 kept ±10.74].
- **Glue-gap row compares the loose-side gap with itself** ✔ (`main_knob/checks.py:34`): 0.45 against itself; the band is
  0.20–0.30. Needs a loose-side limit from Ed.
- **Three real caps missing from the board proxy** (C20–C22, skipped as the old 716 driver, `electronics/parts/pcb.py:77-83`).
- **Jack power board → lower board stacks drawn at x ±1.3, not ±11.15** ✔ (`case/parts/shell.py:529` reuses `hx`); their
  keep-outs in both boards' part envelopes are in the wrong place too.
- **BOM / colours:** the dial's lower part matches `r"spring"` ✔ → listed as a bought spring, no print STEP, steel in the
  viewer; the jack lower board listed as jacks; "PCB front parts" matches no BOM rule; the EE-SX1321 listed as the old
  encoder daughterboard; stale descriptions (link flex, spring contacts).
- **`build.py --full` imports the v0.11 board STEP**; the old `kicad/export_pcb_proxy.py` writes the same
  `pcb_proxy.json` the model reads (old board, old frame).
- **KNOWN clash list** still accepts two v0.11/v0.13 clashes (would hide a recurrence).
- **Case preview** reads `parts["back TFT window"]` (not built): `build.py --sub case --preview` should crash.
- The case still reads the old `cad_constraints.json` (v0.18): knob top (still right) and the 716 pads / old rod pad as
  back keep-outs (harmless today).

## C. Superseded files still wired in

- Screen adapter v0.4 (replaced by the Ø12 rod-link board in v0.24) is still in `fab_export.py` BOARDS.
- Joystick daughterboard v0.1/v0.4 pack (standoffs, 1x3 headers) and main board v0.11 pack: both say READY TO QUOTE.
  `docs/manufacturing-pcbway.md:28,35-37` too. Keep `joystick-daughterboard/geom.json` (the model reads it).

## D. Code tidy (no geometry)

- Unread params (scan): interface `z_motor_pinion, hub_gear_min, skirt_clear, det_r_frac, ot_keep_r`; electronics
  `hall_z`; control_dial `carr_steel`; base_drive `fm_ear, saddle_later`; optics `rl_phase_deg`; case `joystick_commit,
  resin_face_rough, finish_front, finish_other, scr_t, scr_below_knob, bz_max, roof_pad, mirror_tilt, cover_rho, rear_clear,
  jack_nut`; assembly `vb_buckle_margin`.
- Dead options: the lever `sl_*` (still read by `stop_blocks()` which returns None), cushions `cu_*` (now broken: TypeError),
  the v0.30 hanger `dt_hang_*`, the ear/fan placement and detent-column search (can raise for a part that doesn't exist),
  cradle pegs, `fm_keepout`, press springs / grubs / inserts / standoffs / 2x5 headers / v0.7 contacts in the joystick,
  the encoder riser, TFT / scanner aliases, PETG seal and ring-magnet branches, `drv_*`.
- Rows that can't fail or test removed parts: "split detent: train centred" (0 ≤ 0), "material under the cup-boss bore",
  "cradle web after the bridge cut" (vs itself), "cover depth" (vs itself), knob bolt tip (0 bolts), "post stands above the
  thread" (inserts), top light strip, two rows on the v0.36 link lane, about 15 case rows equal by construction, and in the
  joystick: FPC vs PCB slot, switch opening in the plate, socket-screw heads / dowels (empty lists), standoff symmetry, and
  the "no removed part" rows. Misnamed: "fan vs detent springs / grubs", "Hall arm / fan vs cradle, detent blocks, track".
- 18 BOM rules match no part; assembly steps back2, feel, feel-strap, feel-pin are empty; `^encoder (daughterboard|header)`
  in step "back".
- Stale text: comments and docstrings for the lever, cushions, thrust carrier, hanger, "springs lifted above the detent
  block" (they are at z 10.5 beside it), "H7B0", "716 strap", AGENTS.md, `docs/top-screen-joystick.md` (no v0.8/v0.9).

## Checked and clean

Main board v2: every hole and cut has its mating part in v0.55 (hold-down spring slots, H1 rod, H2 encoder bearing, M1
relief and tabs, MP1/MP2 posts, J2/J3 legs, 12 LED cut-outs, windows A–E, J4 Tag-Connect); no grub, standoff, dowel, riser
or encoder-slot holes; rule areas current; one single-pad net (RING_DOUT, expected); BOM has no removed parts. Link flex
pin map matches on all three boards. Jack unit and USB-C boards match the model. Built parts: no hanger, stop blocks,
plate-level posts, cushion or compression-spring pockets, thrust groove, cradle track grooves, fan, ears, TFT pocket or
scanner shelf; every case cut-out has a part in or through it; every part sits in exactly one assembly step.
