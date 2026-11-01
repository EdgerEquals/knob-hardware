# Shortlist decisions (Ed, from 2026-10-30 12:47 AWST)
Going through the 15 shortlist items in brainstorm-shortlist.md one at a time: my recommendation, then Ed's accept / throw / park.

## Global rule (Ed, 13:09 AWST)
All shortlisted ideas are accepted in principle. None are separate modes or pre-show steps: they all run live at once, called on by the music. No soundcheck sweep: the room is mapped on the fly. Each behaviour triggers only when the energy flows through its ratio threshold (e.g. into a room resonance), holds while it stays there, and the result is fed back via the room. Thresholds are ratios, never fixed values.

1. Room balance layer: ACCEPT (live, always-on, energy-triggered; no soundcheck sweep).
2. Tuned to the building + room-adaptive crossover: ACCEPT WITH CHANGE (13:17 AWST).
   - One "room dial": damp <-> crank. Default leans damped: nullify/quieten nasty resonant modes (e.g. tin warehouse roof/walls) as much as possible.
   - Room modes never dictate where the music goes. Crowd/people feedback steers the music.
   - Exception, by Ed's choice on the dial: in a build or solo, crank it to pull the music tight into the hard modes and play the room, then bring it back.
   - Crossover moves slowly, in small steps.
3. Room's tail + acoustic shadow: ACCEPT, EXPANDED (13:21 AWST).
   - Not limited to the back wall: use all reflections.
   - Background (low priority, possibly its own Raspberry Pi) builds a 3D model of the room from room-mic spectral data, refined live through the night.
   - Echoes/tail draw on the model; on the room dial.
   - New branch: the room model feeds visuals and augmented reality.
   - Note: one mic gives a rough model (reflection distances, resonances); a second mic or the camera can sharpen it later.
4. Duet with the machine (follow the hand, hand back on bezel touch, knob suggestions, shadow layer later): ACCEPT (13:23 AWST). Plus a dial for how much the machine may do (off to fully playing along). Touch always wins instantly.
5. Branching re-performance: ACCEPT (13:27 AWST). Storage: a hard drive plugged into one of the Raspberry Pis (audio is the only heavy data; control logs are tiny). One hardware record button, lit red while recording; press to start/stop. Only recorded when armed; nothing logged otherwise.
6. Memory across nights: ACCEPT, REDESIGNED (13:28 AWST). No live memory feature in the rig. The memory lives in this conversation: after several gigs or a tour, Ed and the bot review recordings (what the engine put out vs what Ed tweaked), then the bot suggests gestures/changes and pushes them as software updates, or Ed makes physical hardware changes. Rig just records; nothing else needed. Per-venue room models are still kept on the drive as data.
7. Silence amplifier: ACCEPT (13:30 AWST). Room mic source, hub VCAs, hardware ceiling; wakes when music energy drops below a ratio threshold; on the room dial.
8. CV-driven light + silent drop: ACCEPT (13:30 AWST). CV-to-DMX converter on the CV bus; silent drop is a button/gesture Ed calls, not automatic.
9. Glass box (camera view of knobs with overlays on stream/screens): ACCEPT (13:31 AWST). IR feed is mono; a colour camera may be added for a nicer picture. Ties into room model / AR branch.
10. EEG: ACCEPT, REFOCUSED ON THE DROP (13:33 AWST).
   - Step 1: Ed wears it. Record EEG alongside dial moves and the build/drop; review together whether the build and the drop moment are visible in his brain data.
   - Step 2: a crowd member wears it, used only for the drop.
   - Mapping and which data to use evolve between Ed and the bot over time (review loop). Hardware just needs the infrastructure: EEG stream timestamped into the same recording log as dials/MIDI/CV/audio. Bluetooth link question still open.
   - Caveat: the drop moment likely coincides with movement and jaw/muscle bursts; motion sensor + seated tests help separate real EEG from movement.
11. Performer flow state on generative range: FOLDED INTO EEG work (13:35 AWST); add later via the review loop if recordings show something reliable.
12. φ structure on a steady clock (Fibonacci phrases/polyrhythms, slow structural clock): ACCEPT AS SOFTWARE (13:35 AWST). Hardware only needs the global clock. Resets each phrase.
13. Glass chop: ACCEPT AS ONE OPTION (13:58 AWST). It ties up a lot of gear: full chain in the studio when recording a single stem; live, it gets only what's free. General rule: gear allocation is a sliding scale with the scale of the performance (studio stem vs live set).
14. Compression as orchestra -> VARIATION ACCEPTED (14:00 AWST): a digitally controlled ANALOG switching patchbay. Audio stays analog (relays/analog switches); control is digital and it's just another node on the bus. Lets the engine re-route gear (compressors, effects, inserts) itself, e.g. in AUTOPILOT / ghost mode: an autopilot switch where the machine performs on its own in Ed's style while he's away. Hardware concept must exist before hardware/software design; behaviour comes after.
15. Guarded feedback: ACCEPT, built last (14:04 AWST). Amount of feedback on a dial; the system always keeps it under threshold; hardware ceiling first.
   - New: cone excursion sensing on Ed's own stack: camera + retroreflective dot on each cone (same IR camera approach) to measure excursion and limit it.
   - New: cone breakup on a dial: deliberately allow a controlled amount of breakup as a sound, within safe excursion limits.
   - Note: high-frequency breakup and fast excursion exceed normal camera frame rates; a high-speed camera or per-driver laser/IR distance sensor may be needed; camera fine for slow sub excursion.

## Shortlist pass complete (14:04 AWST): all 15 decided.

## Harmonics decisions (Ed accepted my filter, 14:25 AWST): see scope-notes "Harmonics: final-round reviewer replies filtered" (keep + leave-behind lists).

## Musical <-> clinical dial (Ed, 14:25 AWST)
Every piece of hardware, and each of its parameters, gets a tag for where it sits on a measurement/clinical <-> artistic/musical spectrum (e.g. Behringer SPL measurement mic = clinical; ribbon mic = musical; condensers in between). One dial / digital switching touch bar shifts the whole architecture (hardware routing via the analog switching patchbay + software settings) towards musical when it sounds too clinical, or towards clinical/rigid to build tension. Ed owns a Behringer measurement mic (model TBC, e.g. ECM8000) - measurement/analysis duty regardless of the dial.

## Main unit (Ed, 14:39 AWST)
Bela REJECTED: cost, and its hardware-design rights (CC BY-NC, commercial licence needed) clash with Ed's rule that he owns everything he develops. Direction: own-design board = Raspberry Pi CM5 no-wireless (CM50xxxx) as the brain + STM32 G4/H5 (native CAN-FD) as the real-time clock/bus/CV master on bare-metal firmware + own audio codec (mics, amp V/I sensing) + own CV DAC. CAN-FD bus + a dedicated clock line. RP2350 ruled out (no CAN-FD). Lost vs Bela: a ready-made, tested sample-synced I/O platform; design and test time. Research in scope/main-unit-bela-vs-cm5.md.
Update (Ed, 14:42 AWST): CM5 WITH wireless is fine (easier supply). Radio off by default; switched on briefly as a top-layer sync/check-in, then off again; hardware switch to cut it fully. Wireless is housekeeping only: clock and live control always on the wired bus.
- 2026-10-30: Decision 7 (silence amplifier) merged into decision 1 (room balance): one energy detector for up and down threshold crossings.
- 2026-10-30: EEG receiver and IR camera are sensor-node front ends, not separate modules.
- 2026-10-30: NEW collaboration layer: player displays for guest musicians showing chords and the next 4-8 bars per instrument. Details in layer-map.md.
- 2026-10-30: Player stations = Ed's own small-board display + dials, with saved per-player profiles (no tablets).
- 2026-10-30: ACCEPTED engine lookahead commit when guests play (software, for MIDI Bot).
- 2026-10-30: Correction: no solo switch; lookahead is automatic from active player stations.
- 2026-10-30: Hot-swap mid-gig accepted; Ed's own isolated multi-rail PSU (9/12/15/18/24/48 V) folded in, wireless-power-ready input.
- 2026-10-30: Ed designs his own switching patchbay alongside his own PSU.
- 2026-10-30: First build = standalone motorised knob MIDI/CV controller, sellable early; grows into the system node.
- 2026-10-30: Knob v1 spec logged in knob-module-v1.md (two units per 8HP Eurorack module, AU$400+).
- 2026-10-30: Crowd themes layer added (set layer, background Pi, themes only, never records); orbit radius merged into involvement dial.
- 2026-10-30: Knob v1 = Plan B (one unit + optical panel in 8HP).

## 2026-10-31 — Knob hand feel: electronic clutch
No mechanical clutch. Motor assists the hand's direction via encoder; gearbox backlash lets intent register first; resistance set by the motor. Current sensing plus a new thermal probe drop the motor into freewheel on a sustained stall (e.g. held at the end stop), with a screen message. Bezel spring stiffness planned for now, final call after the test motors arrive.

## 2026-10-31 — Knob screens
Three screens: 0.7" round TFT in the button (flex out the back to the PCB); smaller top screen on the tilting carriage, sized for finger clearance; full-size TFT under the optical panel filling the remaining space.

## 2026-10-31 — Knob panel order
Top to bottom: top screen on carriage, dial + bezel, optical panel with big TFT, six jacks in two rows of three at the bottom with USB-C beside them. To-scale layout drawing to follow for finger-clearance check.

## 2026-10-31 — Sixth jack
J6 is a dedicated motor-voice audio in; CV in stays CV-only. J3 remains the only role-switching jack.

## 2026-10-31 — Market position
Report: https://cursor.com/canvas/store-62beeca5-62c3-4b43-ae3a-5b389d2a9db1/f7f00689-a84e-41a2-81d1-e5d41564e7b3 — suggested launch A$649–799 (start A$699) for 1" 8HP; main rival subMatrix BeetTweek; key risk is geared-motor feel vs brushless.

## 2026-10-31 — Big TFT
0.96" TFT locked for v1; bigger screens come with the larger knob sizes.

## 2026-10-31 — Module width 10HP
Ed: no crowding. Module goes from 8HP to 10HP (~50.5 mm) to keep the 1" knob with clear space around the 35 mm bezel. Bezel stays 35 mm. Layout v2 to be redrawn.

## 2026-10-31 — Big TFT on the PCB (overrides 0.96" lock)
Ed: the 0.96" looks dinky. The bottom TFT mounts on the main PCB and fills the whole lower zone, including behind the jacks. Jacks and USB-C mount through the clear optical panel in front of it, wired back. Layout v3 in progress; depth stack to check.

## 2026-10-31 — Layout v3 accepted
2" PCB-mounted TFT behind the clear panel with the jacks in front; shorter panel jacks plus a black mask around each jack. Open: source jacks with a body of 6 mm or less, and check the motor depth.

## 2026-10-31 — Two TRS jacks + USB-C
Ed: go to two stereo (TRS) jacks and one USB-C, switchable. TRS MIDI out dropped (USB-C and later the rear bus carry MIDI). J1: tip dial CV, ring bezel CV / motor texture (menu). J2: tip CV in / motor-voice audio in (menu), ring button gate out. Used with TRS-to-2xTS splitters. Supersedes the six-jack set. Layout v4 being drawn.

## 2026-10-31 — USB-C power
Ed: power from USB-C too. Dual input: Eurorack bus or USB-C PD (9–15 V); automatic switch-over that prefers the bus when racked; ground isolation for audio.

## 2026-10-31 — Layout v5 direction
2" TFT bonded to the back of the clear panel (no air gap). Top screen carriage moved up as far as the rail allows. Three TRS jacks plus a vertical USB-C: J1 dial CV / bezel CV; J2 CV in / gate out; J3 motor voice (tip audio in, ring texture out). No jack switches role.
- CORRECTION (Ed, 2026-10-31 11:13): the 2" TFT is NOT bonded to the clear panel. It stays assembled on the main PCB, with the air gap behind the clear panel.
- Ed (11:15): move the dial up together with the top screen and use the gained height for a bigger bottom TFT if one fits.

## 2026-10-31 — Motor sizes and first CAD
The N30 and 1220 are both Ø12 × ~38 mm and fit end-on on a bracket behind the panel. The RK-370 (Ø24, 50–69 mm) won't fit axially. Draw the 1220 coreless first (smoother haptics, no cogging); the N30 is a parameter swap. CAD is in build123d, with STEP, DXF and PNG output.

## 2026-10-31: Motor mounting
Ed: there is no hole in the PCB. The motor solders directly to the main PCB by its rear tabs, with its axis perpendicular to the board on the dial centre. This replaces the earlier idea of a bracket with the motor passing through a PCB hole. Depth fit still needs checking in the assembly.

## 2026-10-31: Motor offset, hollow fixed shaft
Ed: the motor is OFFSET from the dial axis (it was never meant to be on it). On the axis there is a fixed hollow shaft attached to the PCB, carrying the centre-screen cable down to a connector on the back of the PCB. The current CAD assembly (motor on axis) needs correcting. Proposed (awaiting Ed): an adapter board behind the 0.7" screen, with 8 x 36 AWG PTFE wires down a 2 mm bore in a ~4 mm OD stainless tube.

## 2026-10-31: Shaft cable LOCKED
Ed chose: an adapter board behind the 0.7" screen, then 8 x 36 AWG PTFE wires (twisted) down a 2 mm bore in a 4 mm OD fixed stainless tube on the dial axis, landing on a connector on the back of the PCB. No slip ring (the shaft does not rotate).

## 2026-10-31: Fixed shaft v2 (two-piece, printed)
Ed: print it in CF-ASA or PETG (clear PETG is an option for lights), not resin. Two pieces: a base with a square flange the width of the PCB (49 x 49), glued to the PCB, poking up through the PCB, plus a top piece. 6 mm OD (around 6-7, maybe less), 2 mm bore. Joint: spigot and socket with a flat key, epoxy bonded. The knob top glues on. Supersedes the 4 mm stainless tube.

## 2026-10-31: Screen MCU, 4 wires
Ed: only the centre-screen wires go down the bore (the motor is wired directly to the PCB). Put a microcontroller on a small adapter board behind the 0.7" screen, which leaves 4 wires (power, ground, 2 data) down the bore. The shaft can now shrink to about 4 mm OD printed with a 1.2-1.5 mm bore (TBC). Adapter board target is 18 mm diameter or less.

## 2026-10-31: Shaft v3 one piece
Ed: the shaft is ONE piece (no joint), thinner, with a spline at the top for the knob to glue onto. Drawn at 4 mm OD, 1.5 mm bore, with the square flange. Supersedes the 6 mm two-piece shaft.

## 2026-10-31: Shaft v4 metal
Ed: a 2.5 mm+ bore with a 1-1.5 mm wall, in metal (brass or bearing stock / sintered bronze). Proposed: brass tube 5 OD x 3 ID (stock), a knurl or flats at the top for the knob epoxy (a spline is not practical on tube), and a printed square flange bonded on. Sintered bronze is suggested for the dial bush running on the brass. PCB hole to change to 5.2 mm.

## 2026-10-31: Shaft v4 approved, custom flange
Ed approved the brass 5x3 stock tube, cut to length and knurled at the dial end only. Flange is now custom: smaller and thicker, clear of the motor tabs (drawing 20x20x4 [A], clearance to be checked).

## 2026-10-31: Knob gear train (to draw)
Ed: the knob carries an internal ring gear driven by a pinion on the offset motor's shaft, plus a ring gear at the knob bottom that takes rotation off to the encoder. Knob runs on the fixed brass tube (sintered bronze bush suggested).

## 2026-10-31 — Dial-centre link: data over power (supersedes 4-wire bore)
- One PTFE wire down the brass tube carries power plus data. The brass tube is the ground return.
- The main board puts data on the supply line, and the CH32V003 behind the screen filters it off (a 1-Wire / LIN-style single-wire serial link).
- Wireless was considered and rejected: a radio inside a metal-cored 48 mm dial would detune, and it breaks the wireless-off-by-default rule.
- To do: choose the coupling circuit and bitrate; the adapter board's power filter and data tap.
