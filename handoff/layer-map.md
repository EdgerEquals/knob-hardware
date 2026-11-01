# Layer map (draft, 2026-10-30)

Golden-ratio cascade: layers from fastest/highest-Q to slowest/widest. Each layer talks only to its neighbours; the step between layers is a ratio (phi powers), not a fixed number.

| Layer | Time scale | Decisions living here |
|---|---|---|
| 1 Signal | µs–ms, analogue | 16 harmonics (stage, all-pass phase, damping), 15 guarded feedback + cone sensing + breakup, 14 patchbay audio path, 2 mode nulling, V/I sensing |
| 2 Control | ms | motorised knobs, hub VCAs, relay switching, global clock, "touch always wins", 17 dial execution |
| 3 Gesture/phrase | s | 1 room balance (energy thresholds), 7 silence amplifier, 4 duet + involvement dial, 8 CV-to-DMX + silent drop, 9 glass box, 10 EEG logging |
| 4 Set/night | min–hr | 3 room model Pi, 5 record drive + button, 14 autopilot/ghost, 17 musical-clinical dial position, 12 phi structure (software), 13 glass chop (software option) |
| 5 Review | days–months | 6 review loop, venue room models, EEG mapping evolution (11 folded in) |

## Proposed merges
- 7 silence amplifier merges into 1: same energy detector, threshold crossed downward.
- 11 already folded into 10.
- 12 and 13 are software only: no hardware module.

## Module types (only five)
1. Spine: main unit (CM5 + STM32), clock line, CAN-FD, power/ground standard
2. Hub: VCAs, relays, CV/gate, MIDI per device
3. Knob: motorised smart knob
4. Sensor node: mics, V/I, IR camera, cone sensing, EEG receiver
5. Recorder/model Pi: drive, record button, room model

Everything leans on the Spine, so it is first.
- 2026-10-30: ACCEPTED. Silence amplifier (7) merged into room balance (1): one energy detector, up and down crossings.
- 2026-10-30: ACCEPTED. EEG receiver and IR camera live on sensor nodes (one module type, different front ends).

## Collaboration layer (added 2026-10-30, Ed)
Guest musicians (guitar, trombone, mallets, anyone playing pitched parts) get a player display: current chord, the next 4 or 8 bars, key/scale, bar and beat count, all transposed and range-checked for their instrument from the instrument library. They play acoustic, miked into the mix; optional MIDI back from them later. Ed prefers jamming with others to playing alone.
Architecture impact: the engine must commit its harmony a few bars ahead (a lookahead buffer), and displays run off the global clock. Display hardware is still open (tablet vs own display node, wired by default).
Spans gesture and set layers; touch/humans still win.
- 2026-10-30 (Ed): Player stations are Ed's own hardware, not tablets: a small-board version of his displays and dials, on the shared core. Guests navigate and fine-tune it themselves before the set, on the fly, or anytime; they enter their name and their setup (instrument, transposition, view, lookahead) is saved as a player profile.
- 2026-10-30: ACCEPTED. Engine commits harmony/melody a ratio-set number of bars ahead (4/8+) when guests play; free when Ed is solo. Software item for MIDI Bot.
- 2026-10-30 (Ed correction): No solo switch. Guests come and go freely (human layer). Lookahead follows automatically: engine commits ahead whenever a player station is active/logged in, free when none are.

## Shared core review filter (2026-10-30)
Both reviewers: accept shared STM32 G4 core as default.
Kept:
- Exceptions: IR camera gets its own compute module (reports results on CAN); motor driver on a separate power front end with its own power entry and ground return; recorder Pi separate.
- Audio-rate sensing (mics, V/I, cone): external ADC on the front end over I2S; core handles control data.
- Standard core-to-front-end connector with split power (3.3 V digital, 3.3 V clean analog, +/-12/15 V, motor power separate), DGND/AGND tied once on core, SPI, I2C, I2S, GPIO, reset/fault/present, ID EEPROM.
- Separate spine-to-core connector (CAN-FD, clock, power, grounds, present).
- One firmware image that detects its front end at boot and self-calibrates.
- Limp mode: on bus or clock loss knobs go limp, hubs hold or mute safely; heartbeat, watchdog, bus-off isolation.
- Motor driver must truly tristate while encoder/back-EMF is read.
- Clock distribution board on spine with low-skew fanout; single-ended first, LVDS if runs are long.
- CAN-FD bootloader plus SWD header; isolation boundary to synth grounds; EMC and thermal plan near valve amps; bench test rig.
Dropped/changed:
- ESP32-S3 / Pi Zero 2 W for camera (always-on radios; use radio-off Pi or CM5 path).
- Fixed numbers (500 ms calibration, 48 kHz/1 kHz/10 Hz rates): keep as ratios of one master clock, bounded by real hardware limits.
- Export classification note (not relevant).
Open: hot-swap or power-down swap.
- 2026-10-30 ACCEPTED (Ed): Hot-swap mid-gig. Ed will build his own isolated power supply, a self-contained, robust module of the system with rails 9/12/15/18/24/48 V (rails set by the gear, an external standard). Future-proof the input side for his wireless power projects but keep it simple now. Ed also wants to design "his own switch" (meaning to confirm).
- 2026-10-30: 'Own switch' = the switching patchbay (decision 14), Ed designs it himself; it shares the PSU and power-up/hot-swap design.
- 2026-10-30 ACCEPTED (Ed): FIRST BUILD = the motorised knob as a standalone MIDI + CV controller (USB MIDI, DIN/TRS MIDI, CV/gate out, Eurorack-friendly), playable on its own and sellable early to fund development. It later joins the bus as a node and gains features iteratively. Built on the shared core so it carries the bus and clock from day one.

## Crowd themes layer (Ed, 2026-10-30) + reviewer filter
Idea: local language model listens to the room mic, extracts aggregate THEMES only (artists, places, ideas), steers engine style via artist and geography databases and feeds the vocal/spoken-word chop layer (MX-1 style chop/scatter/filter).
Lives in the SET layer (minutes), so slow STT latency is fine.
Keep: runs on a dedicated background Pi, offline; audio in RAM ring buffer only, never written; transcripts discarded in seconds; only aggregate theme counts kept; signage; mic aimed at the open floor, not booths or bathrooms; subtract our own playback (we know what we're playing) so the system doesn't hear its own samples; slow averaging + hysteresis + ratio thresholds; crowd energy (room mic) confirms or reverts a theme change; Ed's touch always wins; themes decay like ghosts; semantic map with the engine orbiting the crowd's centre, orbit radius set by hand; original spoken-word recorded with local voices as the rights-clean option; get WA legal advice (Surveillance Devices Act 1998, Privacy Act 1988) before public gigs; live samples a grey area, released sets need clearance; Australian copyright life+70.
Drop: playing the crowd's own words back (breaks no-recording); parabolic mic aimed at the bar (eavesdropping); fixed numbers (EMA 0.01, 3 mentions/10 min, 0.7 confidence, 3.2 min) become ratios; unverified model benchmark claims (Moonshine/IMBE figures) need checking before relying on them.
- 2026-10-30 ACCEPTED: Orbit-tightness merged into the machine-involvement dial (decision 4): one dial for machine + crowd vs Ed.
