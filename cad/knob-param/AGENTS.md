# knob-param — agent guide (parallel work by sub-assembly)

Parametric build123d model of the motorised Eurorack knob (10HP, knob OD Ø42.0, the measured
borosilicate sleeve; the screen still needs at least Ø41.641).
Default params are **v0.18**. v0.17 is kept in `cad/assemblies/knob-stack-v0.17/`. v0.18: 25° herringbone
(module 0.67, 51T ring split in two halves, 12T pinions), every gear PA-12 (the motor pinions use the Tempero
0.5M-12T and RW m0.6 14T tooth forms, printed), feel train 15.58:1, hub 1.571:1, and UTR-8100 Fresnel caps on the
four gears with a free face. Output: `cad/assemblies/knob-stack-v0.18/` (preview, clean section + iso, plan, check.json).
Design notes: `docs/design-notes.md`.

## Branch model

```
main                      (released snapshots — agents never touch it)
└── param-dev             (integration branch; assembly agent owns merges)
    ├── sub/main_knob-<topic>      one cloud agent  → PR into param-dev
    ├── sub/control_dial-<topic>   one cloud agent  → PR into param-dev
    ├── sub/base_drive-<topic>     ...
    ├── sub/under_pcb-<topic>
    ├── sub/electronics-<topic>
    └── asm/<topic>                assembly agent (interface changes, cross-checks, render)
```

* **One cloud agent per sub-assembly**, each on its own branch off `param-dev`.
* A sub agent edits **only** `cad/knob-param/knobparam/<its sub>/`. Nothing else (not `common/`,
  not `assembly/`, not another sub, not `cad/assemblies/`).
* Open a PR into `param-dev`. Put the output of `python build.py --sub <name>` (local summary)
  in the PR description.
* The **assembly agent** merges sub PRs, runs the full build + cross-checks, renders the PNG, writes the
  report, and commits `cad/assemblies/knob-stack-<version>/`. Only the assembly agent changes
  `assembly/` (incl. the INTERFACE params) and `common/`.
* Need an interface change (e.g. a new shared dimension, a different gear module)? Ask for it in the PR
  / an issue for the assembly agent; don't edit `assembly/interface.py` from a sub branch.

## Layout

```
cad/knob-param/
  build.py            ONE CLI (full assembly or --sub)
  report.py           engineering report (assembly agent)
  setup.sh            fresh-VM setup (venv + pinned requirements + headless GL libs)
  requirements.txt
  knobparam/
    common/           harness: model.py (scope/derive), cache.py (per-part cache, scope guard), util.py, checks.py
    assembly/         interface.py (INTERFACE params + derive), params.py (version, ...), build.py (merge order),
                      checks.py (cross-checks + clashes), render.py, report.py, hall_dyn.py
    main_knob/        knob body + skirt, hub gear, cone race + balls, bottom ring, diametric ring magnet
    control_dial/     dial tube + lip, screen, carrier cartridge + FPC strap, dial TMAG5273 board, Hall arm + fan + lever, thrust balls
    base_drive/       cradle, brass tube, rod + sleeve, 1220 motor + pinion, idlers, 716 feel motor + open saddle,
                      mech (detents, ball track, cushion stops, centring springs)
    under_pcb/        encoder disc (slotted rim, no teeth), EE-SX1321
    electronics/      main PCB (proxy + committed STEP), adapter, Hall sensor row, rod VBUS pad, connectors;
                      kicad/ = KiCad projects (knob-main-pcb, screen-adapter), footprints, footprint generators
```

Each sub folder has the same shape:

| file | role |
|---|---|
| `params.py` | `P` (own params, each tagged `[A]` assumed / `[Ed]` Ed's decision), `IMPORTS`, `EXPORTS`, `derive(D)` |
| `parts/*.py` | one module per part group: `build(D) -> {name: solid}` (reads `D` only) |
| `checks.py` | `local(D, parts, rows)` — checks that need only this sub's scope |
| `__init__.py` | `PART_MODULES` + any public helpers |

## The contract (enforced by the harness)

* **Scope.** A sub's `derive()` and part builders see only: INTERFACE params + interface-derived values,
  its own `P` and own derived values, and the keys it lists in `IMPORTS`. Reading anything else raises
  `ScopeError` (`... is outside this sub-assembly's scope`).
* **Imports.** `IMPORTS = {"<other sub>": [keys]}` — each key must be in that sub's `EXPORTS`.
  Interface and imported values are read-only (writes are detected and rejected).
  Derive order: interface → electronics → control_dial → main_knob → base_drive → under_pcb
  (exports flow forward; under_pcb's `d_big_tip` is consumed by electronics at *build* time only).
* **No code imports across subs.** Code in `knobparam/<sub>/` may import only `knobparam.common` and its
  own folder. `python build.py --contract` checks this statically (AST) and fails on any cross-sub import.
  Cross-boundary data goes through interface params or exported envelopes (EXPORTS), never internals.
* **Unique owners.** Every param name has exactly one owner (interface / assembly / one sub).
  `python build.py --dump` prints every value with its owner.
* **Don't hard-code — derive.** New dimensions become params in your `P` with a `[A]`/`[Ed]` tag and a comment.
* **Keep exports stable.** Changing the meaning of an exported key is an interface change → assembly agent.

Current contract (`python build.py --contract`):

* INTERFACE params: `pcb_t, axis_bx, axis_by, module, pressure, backlash, motor_offset, z_motor_pinion, z_enc_pinion,
  enc_ang, idler2_from_enc, motor, skirt_clear, knob_wall, skirt_gap, knob_run, knob_hub_z0, hub_gear_face, kb_ball_d,
  kb_ball_tube, kb_clear, kb_zc, kb_play, dial_tube_id, dial_tube_wall, travel_deg, rod_d, nut_m, plate_t, cr_floor,
  pin_face, pinion_hub_d, pin_above_skirt, brg, ha_ang0, ha_ring_clear, ha_n, ha_mag, ha_mag_wall, ha_mag_edge,
  ha_pitch, ha_sens_h, ha_gap, ha_arm, ha_win_clear, idler1_ang, feel, adapter_t, cord_clear, screen, z_glass, z_holder0,
  cof_bend, hall_layout, hv_n, hv_pitch, hv_cross_travel, hv_mag, hv_br, hv_wall, hv_gap, hv_sensor, hv_ring_clear, tgt`
* electronics — EXPORTS `pcb_w, pcb_above, pcb_below, adapter_d, adapter_fps, adapter_env`; IMPORTS under_pcb `d_big_tip`
* control_dial — EXPORTS `dial_hub_z0, z_lip0, z_web0, dial_hub_od, r_web, gusset, lip_fillet, tb_pcd, tb_groove_r, tb_z_ball`;
  IMPORTS electronics `adapter_d, adapter_fps, adapter_env`
* main_knob — EXPORTS `h_bi1`; IMPORTS control_dial `dial_hub_z0, z_lip0, z_web0, dial_hub_od, r_web, gusset, lip_fillet`
* base_drive — IMPORTS control_dial `tb_pcd, tb_groove_r, tb_z_ball`; main_knob `h_bi1`
* under_pcb — EXPORTS `d_big_tip`; IMPORTS electronics `pcb_w, pcb_above, pcb_below`

## Running

```bash
bash cad/knob-param/setup.sh                 # once per VM -> cad/knob-param/.venv
PY=cad/knob-param/.venv/bin/python

# sub-assembly agent
$PY cad/knob-param/build.py --contract                  # must print "contract: OK"
$PY cad/knob-param/build.py --sub control_dial          # its parts + LOCAL checks + internal clashes
$PY cad/knob-param/build.py --sub control_dial --preview  # + preview PNG -> cad/knob-param/out/control_dial-<ver>/
$PY cad/knob-param/build.py --sub control_dial --set cof_bend=0.26  # try a value (any param, dotted for dicts)

# assembly agent
$PY cad/knob-param/build.py --render         # all subs, local + cross checks, clashes, sections PNG
                                             # -> cad/assemblies/knob-stack-<version>/
$PY cad/knob-param/report.py                 # report-<version>.txt / .json (Hall vernier dynamics etc.)
$PY cad/knob-param/build.py --full --render  # real main-PCB STEP instead of the proxy board
```

* `--sub` builds only that sub's parts against the full derived parameter set (so interface + imports are
  real), runs that sub's local checks and clashes between its own parts. Cross-checks and cross-sub
  clashes run in the assembly build only.
* Cache: `cad/knob-param/.cache/` (override with `KNOBPARAM_CACHE=/path`). Each part is keyed on the
  exact params it read + its source, so only changed parts rebuild. `--clear-cache` wipes it.
* Cold full build + render ≈ 30–40 s on 4 cores; cached re-render ≈ 10 s.

### Checks

* **Local** (`<sub>/checks.py`): main_knob 17, control_dial 17, base_drive 18, under_pcb 2, electronics 2, plus 49 cross
  rows (`assembly`) = **105 total**. These counts come from `cad/assemblies/knob-stack-v0.18/check.json` (`rows[].owner`);
  re-count from that file whenever checks are added or removed, rather than editing numbers by hand.
* **Cross** (`assembly/checks.py`) + all-pairs clashes; `KNOWN` lists accepted clashes (none in v0.18).
* **v0.18 glass sleeve: 105/105 gap checks PASS, 0 clashes** on the proxy. v0.17 was 62/62. v0.16b was 54/54.
  The old PCB / motor proxy clash (4.24 mm³) is gone: the proxy reads the M1 Ø3.2 relief from `pcb_proxy.json`.
* History: v0.16 had 41/42 (dial lip wall far side 0.36 < 0.4, fixed by the closed 0.8 lip); v0.15d also failed
  "geared feel motor depth 25.8 > 25" (removed in v0.16: the 716 is no longer under the board).
* A sub PR must not turn any other row red; the assembly agent re-runs everything before merging.

## KiCad

* On `param-dev`, `knobparam/electronics/kicad/` is the **source of truth** for the main PCB and the
  screen adapter (newer than the v0.11 snapshot in `cad/pcbs/`, which is left untouched for `main`).
* **Not needed** for anything in `build.py` / `report.py`. The proxy board is built from params;
  `--full` imports the committed `knobparam/electronics/kicad/knob-main-pcb/knob-main-pcb.step`.
* kicad-cli (KiCad 9) is needed only by the **electronics** agent to regenerate boards / STEP / footprints
  (`apt install kicad` or the KiCad PPA). After regenerating the STEP, commit it.
* `kicad/*/knob_main_pcb.py` and `screen_adapter.py` are legacy generators that need `cad/tools/sheet`;
  they are not used by the parametric build.
* v0.16b boards (main PCB v0.11, screen adapter v0.4, joystick daughterboard v0.1) are **generated**: `cad_constraints.json`
  (`export_cad_constraints.py`, cadenv) -> `make_v016_footprints.py` -> `<board>/kicad/make_board.py`
  (`/usr/bin/python3`, pcbnew; one netlist -> schematic + board, DRC schematic parity; main board
  `--route` = Freerouting 2.1.0 on Java 21, retried until 0 unconnected) -> `export_pcb_proxy.py`
  (`pcb_proxy.json`: extra holes / back-side parts for the proxy) -> `fab_export.py` (PCBWay pack in `<board>/fab/`).
  Re-running `make_board.py` without `--route` leaves the main board unrouted.

## Deliverable conventions (assembly agent)

* Sections PNG: A-A on the left, iso quarter cut on the right, insets along the bottom; clashes are
  reported as text only (no red overlays). No GLB/USDZ.
* Knob OD: the old Ø39.5 rule is relaxed [Ed]; it grows by the minimum the lip wall needs (Ø41.65 in v0.17, was Ø40.85 in v0.16b).
* Bump `version` in `assembly/params.py` for a new release; outputs land in `cad/assemblies/knob-stack-<version>/`.
