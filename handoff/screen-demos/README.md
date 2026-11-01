# Screen demo animations (1 Nov 2026)

All clips are seamless loops at 30 fps, rendered at the panel's native resolution, H.264 MP4 tagged sRGB (BT.709 primaries, sRGB transfer), with GIF previews in gif/.

## Screens used (from EdgerEquals/knob-hardware)
- **Round knob screen:** Kingtech PV13904PY24G-V01, 1.39" round AMOLED, RM69330, **454x454**, active area **Ø35.41 mm** (78 µm pitch), about 450 nit typical.
  Source: `cad/knob-param/knobparam/control_dial/screens/rm69330-1.39/SPEC.md` (param-dev). Note that `docs/design-notes.md` on sub/review-v017 lists the DWO DO0132FMST01 (1.32", 466x466, CO5300, QSPI) as a candidate for the next knob round.
- **"Square" screen:** the only second display in the repo is the joystick top screen, the **DWO DO0164FMST05, 1.64" AMOLED, 280x456, mounted landscape as 456x280**, active area **35.57 x 21.84 mm**, 78 µm pitch, ICNA3311/CO5300 driver, SPI/QSPI/MIPI.
  Source: `cad/joystick-param/jsparam/params.py` (sub/joystick-v04), checked against the DWO datasheet listing. It is rectangular with rounded corners, not square, and the corner radius is not masked in these clips.
  Brightness isn't in the DWO sheet; comparable ICNA3311 1.64" modules are rated 500 nit [A].
- The bottom "screen on the PCB shining up through the case" has no part in the repo yet. `joy_d_curl_flow_IPS-sim.mp4` shows how it would look on an IPS panel (about 1000:1, so black is lifted to about code 11 of 255).

## Colour assumptions
- AMOLED: true black (code 0). Highlights roll off with a soft knee instead of clipping.
- Everything stays inside sRGB. The panels' native gamut is wider (roughly DCI-P3), so the real screens can show everything here, and nothing is pushed past what they can display.
- The iPhone displays P3 and colour-manages tagged sRGB video correctly. Panel peak is about 450–500 nit, so set the iPhone to about 50–60% brightness with True Tone and Night Shift off for a fair match.

## Actual size on iPhone
`iphone-actual-size/*` are 1180x2556 portrait frames, assuming **460 ppi** (iPhone 15/15 Pro/16 class, which is 1179 px wide; H.264 needs an even width, so the frame is 1 px wider, a 0.08% difference).
- Round: 35.41 mm x 460/25.4 = **642x642 px**
- Joystick screen: **644x396 px**

Play them full-screen without zooming. On a 1206-px-wide iPhone 16 Pro they show about 2% larger.

## Clips
| File | Screen | What it is |
|---|---|---|
| round_a_mandelbrot_knob_zoom.mp4 | round | Zoom into Seahorse Valley to about x800,000 and back out, one full rotation per loop with 24 detent ticks turning with it (the knob "drives" the zoom), smooth colouring and a live zoom readout |
| round_b_liquid_morph.mp4 | round | Liquid curl-noise morph nebula → iris → flower → Earth → nebula, all generated procedurally (no third-party images, nothing to credit) |
| round_c_fifths_radar.mp4 | round | Circle-of-fifths radar sequencer: a laser-green beam with phosphor afterglow plays Cmaj7 → Am9 → Fmaj7#11 → G13. Notes sit by pitch (angle) and octave (ring) and flash, ripple and get labelled as the beam passes, echoing the case light-show laser |
| joy_d_curl_flow.mp4 | joystick | 5,000 particles in a curl-noise flow; the simulated joystick puck stirs a vortex and warms the colours around it, with CC1/CC2 readouts |
| joy_e_julia_stick.mp4 | joystick | Julia set whose c follows the joystick round the Mandelbrot cardioid edge (a minimap shows where c is), morphing through seahorse, rabbit and dendrite shapes |
| showcase_module_both_screens.mp4 | both | 30 s, both screens at true relative scale on a dark module face: radar + flow, then Mandelbrot + Julia, then morph + flow |

Sources are in src/ (common.py, a_*.py … e_*.py, post.py). Run time is about 1–2 min per clip on the box.
