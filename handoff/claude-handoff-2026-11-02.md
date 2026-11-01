# Knob MIDI Controller Module: Claude handoff (2026-11-02, Perth)

## Opening prompt for Claude (paste this first)
```
I'm Ed (Perth, AWST). I'm building a motorised-knob MIDI controller module, a 10HP x 3U
desktop unit that also fits a Eurorack case. Repo (public): https://github.com/EdgerEquals/knob-hardware
Working branch: param-dev. Nothing goes to main without my sign-off. Never commit keys or passwords.
CAD: build123d, parametric, in cad/knob-param (build.py). PCB: KiCad, which is the single source of truth.
I'll attach a handoff doc listing the locked decisions, the status of each sub-assembly and the next PCB tasks.
Rules: I own everything, so no restrictive licences. Everything is parametric (ratios and calibration;
the only fixed numbers come from datasheets). Keep it as light as possible. One decision at a time,
with your recommendation. Don't change anything I haven't asked for. Read the doc and tell me what you'd do first.
```

## Repo and branches
- Repo: https://github.com/EdgerEquals/knob-hardware
- `param-dev` is the working branch. Latest: Main PCB v0.11 (U2 EE-SX1321, J2 FG header, ERC/DRC 0, fab pack ready to quote).
- Open PRs (none merged; Ed signs off):
  - PR #7 Borosilicate knob sleeve + v0.17 review checks: `sub/review-v017`, https://github.com/EdgerEquals/knob-hardware/pull/7
  - PR #6 Case v0.1, 10HP flush box: `sub/case-v01`, https://github.com/EdgerEquals/knob-hardware/pull/6
  - PR #5 Joystick v0.4: `sub/joystick-v04`, https://github.com/EdgerEquals/knob-hardware/pull/5
  - PR #4 Knob stack v0.18 (herringbone gears, full assembly export, 1.0 mm thrust land): `sub/assembly-v017`, https://github.com/EdgerEquals/knob-hardware/pull/4
  - PR #2 and #3 (joystick v0.2/v0.3) are superseded by #5. PR #1 (v0.16, feel motor on the PCB top) is merged.
- There is no `sub/pcb-lighting-v01` branch on the remote. The paused PCB round's work was never pushed.

## How to build
```bash
git clone https://github.com/EdgerEquals/knob-hardware && cd knob-hardware/cad/knob-param
bash setup.sh                                   # creates .venv, installs requirements
.venv/bin/python build.py --render              # full assembly -> ../assemblies/knob-stack-v0.16/
.venv/bin/python build.py --sub main_knob       # one sub-assembly: main_knob | control_dial | base_drive | under_pcb | electronics
.venv/bin/python build.py --preview             # quick preview
.venv/bin/python build.py --clean [--opposite]  # clean A-A section + iso quarter cut + legend
.venv/bin/python build.py --set name=value      # override a param (dotted names for dict params)
# --full uses the committed KiCad STEP board (no KiCad needed); also --step, --dump, --contract, --no-check, --no-clash
```
- Workflow and contract: `cad/knob-param/AGENTS.md`. Checks: `knobparam/*/checks.py`; results go to `check.json`.
- The joystick has its own model in `cad/joystick-param`. The case lives on `sub/case-v01`.
- Ed's convention: each update is one colour PNG with section and iso views, plus clean and plan views. Send a preview before any full build.

## Status by sub-assembly
| Sub-assembly | Branch / PR | Checks | Open items |
|---|---|---|---|
| Main PCB | param-dev (v0.11) | ERC/DRC 0; CAD 54/54 | PCB round paused (see Next for PCB) |
| Knob stack | PR #4 | not stated in the PR | gear and optics rounds; motor-through-PCB study |
| Knob sleeve / review | PR #7 | 98/101, 3 fail, 5 clashes | fails: two glue-band rows, Hall spoke at 0.295 mm. Clashes: cradle, ring, blank and saddle contacts |
| Joystick v0.4 | PR #5 | 79/79, 0 clashes | none |
| Case v0.1 | PR #6 | 60/60, 0 clashes | screws to the true corners; jacks and USB-C not modelled; only 2 of 4 knob bolts fit; top rail screws left out (4.1 mm strip, a screw needs 4.8) |

## Current decisions (locked)
- 10HP (50.5 mm) x 3U, overall depth ~68.6 mm behind front face; faceplate-to-PCB 36.05; knob_proud 16.45 mm LOCKED via brass M2x25 F-F pillar (LCSC C50378470) riser; Samtec TSW-103-17-T-S header.
- Case: one-piece PLAIN CLEAR resin front shell (UTR-8100), only top/front face polished, rest as-printed; smoky grey PETG back cover; seamless flush outer box, PCB fully embedded. Four M3 ISO 4762/DIN 912 full-height socket head cap screws (partial thread OK) in flat-bottom counterbores, printed threads in resin bosses through holes/notches in PCB. Ed wants the screws in the TRUE CORNERS of the enclosure (open: bottom pair in corners notching the bottom TFT window corners, vs between the jacks). Jacks + USB-C are not yet modelled in the case.
- Bottom 2.0" 320x240 TFT on PCB, full clear window 40.64x30.48 mm.
- Case scanner (665 nm VCSEL/mirror/grating) REMOVED/parked (scanner_enabled=False).
- Light-show laser: 1 or 2 laser modules at top corners under joystick screen, firing down across PCB face onto clear walls/floor, small motor sweeps horizontally only. Placeholder bays only (the orange boxes).
- Study (not merged): feel motor dropping through a PCB cut-out to cut depth; mechanism rotated so big motor is at the bottom.
- Main knob see-through band: borosilicate 3.3 glass tube 42 OD, 2.0-2.3 wall, ~20 mm, supplier-cut finished ends (VY on Alibaba lead, Aohong backup); printed caps glued on glass ID with 0.2-0.3 gap; top cap inside glass, must not cover top rim; bottom cap carries ring gear + thrust race; resin thrust land >=1.0 mm.
- 12 VCSELs + 12 RGB LEDs reverse-mounted on back of main PCB firing through holes; clear resin race sits flat, its pins locate in emitter holes.
- Power: USB-C power ONLY (USB PD), no Eurorack bus connection. 3 TRS jacks: jacks 1-2 pure analogue (dial/bezel CV, CV in, gate), jack 3 (motor voice audio) switchable to TRS MIDI via a LATCHING SIGNAL RELAY only (no analogue switch ICs in audio path).
- MCU: STM32G474VET6 is the only main MCU. Wireless off by default, knob boards no radio.
- Screens: round 1.39" 454x454 AMOLED (RM69330) in knob, 1.64" 456x280 AMOLED (DWO DO0164FMST05) on joystick.
- Joystick v0.4: Alps SKRHADE010, 4 Lee Spring CI 008B 01 M springs.
- Ed's rules: Ed owns everything, no restrictive licences; everything parametric (ratios/calibration, no fixed values except datasheet data); as light as possible; KiCad is single source of truth; nothing to main without Ed's sign-off (work on param-dev); never commit secrets (public repo); Ed sends supplier quotes himself.

## Next for PCB (paused round, not started in the repo)
1. USB-C PD power-only input, sized for the full load (motors, AMOLEDs, TFT, VCSELs/LEDs, lasers). Report total watts and a recommended charger.
2. Remove the Eurorack power header.
3. Jack 3: latching signal relay switching between the motor-voice audio output and a TRS MIDI Type A circuit (G4 UART). It must power up in a safe state.
4. Reverse-mounted 12 VCSELs and 12 RGB LEDs firing through holes; race pin holes taken from cad_constraints.json; cradle NPTH holes.
5. Wait for the final 10HP outline and corner screw holes from the case (PR #6) before finalising the board.

## Other open items
- Case: move the screws to the true corners (Ed's call: corners or between the jacks); model the 3 TRS jacks and the USB-C; export the PCB outline and holes to cad_constraints.json; fit full-height M3 counterbores and check the back cover thickness.
- Knob: fix the 3 PR #7 fails and the 5 clashes; light-path check; export knob_od and the emitter hole positions to cad_constraints.json.
- Motor-through-PCB and rotated-layout study, on a throwaway branch: depth before and after, cut-out size and position, gear and encoder mesh, room for the laser. Keep that patch of PCB clear meanwhile.
- Light-show laser: pick the module(s) and the sweep motor.
- Ed is sending the glass tube quote request to VY himself.

## Parked for later (not built yet, add back when ready)
Cut on 2 Nov 2026 to save usage. Each is also listed in `cad/knob-param/PARKED.md` once the knob agent commits it.
- Apply Claude's review patch (`knob-param-review-v0.17.patch`: cache fix, gearcheck.py, process tolerances, optics sub, STEP/STL/USDZ export).
- Motor-through-PCB depth study (feel motor drops through a PCB cut-out, Hall/encoder moved to the side).
- Rotate the mechanism so the big feel motor sits at the bottom (frees the top for the light-show laser).
- Light-show laser: pick the module, sweep motor, beam line-of-sight check (placeholder bays only so far).
- Optics round: Risley prisms, VCSEL/405 nm, UV breathing.
- Knob mechanical refinements: thicker ring gear band, shared motor saddle clamp, cradle locating pins, bearing-retainer plate on standoffs, cageless Ø2 race with glass spacers and sieve.
- Case: screws into the true corners (decision open: bottom pair in corners notching the TFT window, or between the jacks); add the 3 jacks and USB-C to the case model.
- All PCB items under "Next for PCB" (the PCB round is paused; its lighting branch was never pushed).
- Case scanner (parked via `scanner_enabled=False`).

## Still running when this was written
- Knob: clean up the glass-sleeve PR #7 (3 fails, 5 clashes), then one full current-state assembly sheet (3 sections + iso).
- Case (PR #6): 3-section + iso sheet, identify the stray blue capsule shapes in the iso, switch to full-height ISO 4762 M3 screws.
