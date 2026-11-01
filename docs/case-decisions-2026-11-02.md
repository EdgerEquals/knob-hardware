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
