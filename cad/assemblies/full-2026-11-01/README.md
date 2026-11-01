# Full assembly, 2026-11-01

Knob stack from `sub/assembly-v017` (v0.18, plus `knob_proud`). Joystick from
`sub/joystick-v04` at `cbc75d43`, read with `git archive` into a temp tree and
imported as `jsparam`. That branch is not merged. The script is outside
`knobparam`, so the cross-sub import rule does not apply. `jsparam` still
reads the knob OD and the knob top through its own `_knob_data()`.

The joystick commit includes a local faceplate proxy around its opening
(`z` about 43.5–46.0). This branch's plate is the 10HP × 3U slab at
`faceplate_z` 38.8, thickness 2.5. Both are in the pictures. They do not
land on the same face.

The 405 nm module, the Risley wedges and the prism motors are not in the CAD.
`full-2026-11-01-section-laser.png` is the dial-axis plane those notes use,
with the axis drawn in red.

| File | View |
|---|---|
| `full-2026-11-01-colour.png` | Colour section A-A + isometric quarter cut + insets |
| `full-2026-11-01-clean.png` | Clean section + isometric, legend only |
| `full-2026-11-01-plan.png` | Three plan slices down +Z |
| `full-2026-11-01-section-x.png` | Plane y = 0 |
| `full-2026-11-01-section-y.png` | Plane x = 0, joystick on +Y |
| `full-2026-11-01-section-joystick.png` | Plane through the joystick centre |
| `full-2026-11-01-section-laser.png` | Dial axis, documented laser / Risley path |
| `full-2026-11-01-iso-above.png` | Quarter cut-away from above |
| `full-2026-11-01-iso-below.png` | Quarter cut-away from below |
| `full-2026-11-01-exploded.png` | Exploded along Z |
