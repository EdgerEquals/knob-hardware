# Superseded boards and tools (archived 10 Nov 2026)

Kept for the record only. **Nothing here is current, nothing here should be quoted or ordered**, and the scripts are not
run by the model (their relative paths broke when they moved here). See `docs/leftover-sweep-2026-11-10.md`.

| Folder | What it was | Replaced by |
|---|---|---|
| `knob-main-pcb-v0.11/` | main board v0.11 (generator, KiCad files, fab pack, STEP, DXF, drawing) | `../knob-main-pcb/v2/` (6 layers, routed, fab pack v2.0) |
| `screen-adapter-v0.4/` | screen adapter v0.4 (Ø15.5, CH32V003, FPC14) | the Ø12 rod-link board (v0.24) |
| `joystick-daughterboard-v0.4/` | joystick daughterboard v0.1/v0.4 (four M2 standoffs, 1x3 long headers) | the joystick top board on the vertical boards (layout v4); its `geom.json` stays in `../joystick-daughterboard/` because the model reads it |
| `v016-pipeline/` | the v0.16b board pipeline: `export_cad_constraints.py` → `cad_constraints.json` → `make_v016_footprints.py`, the old `export_pcb_proxy.py` (it wrote the same `pcb_proxy.json` the model reads, from the v0.11 board), `joystick_stack_v016.json` | `../knob-main-pcb/v2/design.py`, `make_board.py`, `export_proxy.py` |

`cad/pcbs/` (outside the model) is the separate v0.11 snapshot kept for `main`, untouched.
