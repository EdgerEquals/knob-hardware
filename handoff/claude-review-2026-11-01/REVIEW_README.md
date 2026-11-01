# Knob module: parametric CAD code for review

Hi Claude. This bundle is the Python CAD for Ed's motorised Eurorack knob module. Please review the code, not the
renders. Renders, STEP/STL, KiCad board files and other binaries are left out to keep it small. Everything in here is
generated from the Python.

Source: https://github.com/EdgerEquals/knob-hardware (public). Bundle made 1 Nov 2026 (Perth, UTC+8).

| folder | branch | commit | what it holds |
|---|---|---|---|
| `knob_assembly-v017/` | `sub/assembly-v017` | `0050274` (2026-11-01 21:03 UTC+8) | the knob model `cad/knob-param/` (v0.17), docs, v0.17 plan script + check.json |
| `joystick-v04/` | `sub/joystick-v04` | `bce854b` (2026-11-01 21:38 UTC+8) | the joystick model `cad/joystick-param/` (v0.4), its KiCad daughterboard generator, joystick doc + check.json |

The two branches split from `param-dev` at `ac74dba` and have not been merged yet. The joystick branch's copy of
`knob-param` is older for the knob, so only its joystick files are included. The copy of
`electronics/kicad/joystick-daughterboard/make_project.py` and `make_joystick_footprints.py` under
`knob_assembly-v017/` is the OLDER one; use the copy under `joystick-v04/`.

Not in the bundle yet: the case (`sub/case-v01`) and the lighting PCB (`sub/pcb-lighting-v01`). Those builds are
starting now and have not pushed a branch. The older one-off versioned scripts in the repo (`cad/knob/knob-v0.x`,
`cad/assemblies/knob-stack-v0.1..0.11`, and so on) are also left out because the parametric packages replace them.

## What the product is

A 10HP Eurorack (or desktop) control module built around one big motorised knob:

- **Main knob** (about Ø41.65, see-through printed shell). It rides on a **clear-resin ball-bearing carrier** that is
  edge-lit from below by **12 red 665 nm VCSELs** alternating with **12 addressable RGB LEDs**.
- **Control dial** on top of the knob, with a **1.32" round AMOLED** (DWO DO0132FMST01). The v0.17 model still uses
  the older 1.39" RM69330 screen; the switch is queued for the next round. The dial turns ±10° with spring-ball
  detents and is read by a Hall vernier row (TMAG5273).
- **Risley-prism scanner**: one **405 nm violet 1 mW laser** sent through two spinning wedge prisms, each on its own
  small motor. The beam draws on a **glow coat** (strontium aluminate) inside the dial lid and on the case walls.
- **Drive**: a 1220 coreless planetary motor turns the knob through **nylon gears**. A 716 "feel" motor works
  through a compound idler (11.43:1 overall) to give haptic feel. A slotted-disc encoder (EE-SX1321) reads position.
  Every gear that has room will get a printed **clear-resin prism cap** for light effects.
- **Joystick**: a top-screen 5-way joystick (Alps SKRHADE010) under a **1.64" AMOLED** (DWO DO0164FMST05). It sits on
  a daughterboard raised on M2×35 stud standoffs, and its bezel rests on the faceplate.
- **MCU**: **STM32G474** ("G4", LQFP100 STM32G474VET6) on the bottom/main board. It has FDCAN, USB-C PD and
  Quad-SPI and drives every laser, LED and motor directly.
- **Case**: one-piece **clear resin, dyed light purple (Pantone 2577C)**, printed with the faceplate. A "nightclub"
  scanner (a 13th red VCSEL, diffraction grating film and a spinning mirror) lights it from one end.

**Important:** the optics (lasers, prisms, glow coat, resin caps), the 1.32" dial screen swap and the case are
decided but **not modelled yet**. v0.17 covers the mechanics, the screens, the Hall sensing and the PCB envelopes.
See "Open items" in `knob_assembly-v017/docs/design-notes.md`.

## How the code is structured

Everything uses **build123d** (OCCT) and is driven by parameters.

```
params files  ->  part builders  ->  sub-assemblies  ->  interface contract  ->  checks  ->  renders
```

Knob (`knob_assembly-v017/cad/knob-param/`, start with `AGENTS.md`, the real spec):

- `knobparam/assembly/interface.py`: the **INTERFACE** params shared by all subs (gear module, axis positions,
  motor, screen, ball sizes and so on) plus `derive_interface()`.
- 5 sub-assemblies: `main_knob/`, `control_dial/`, `base_drive/`, `under_pcb/`, `electronics/`. Together with
  `assembly/` that makes 6 packages. Each sub has the same files:
  - `params.py`: `P` holds the sub's own params, tagged `[A]` for assumed or `[Ed]` for Ed's decision. It also has
    `IMPORTS`, `EXPORTS` and `derive(D)`.
  - `parts/*.py`: `build(D) -> {name: solid}`. These read only `D`.
  - `checks.py`: `local(D, parts, rows)`, the checks that need only this sub.
- `knobparam/common/`: the harness. `model.py` handles scoping and derive order, so reading outside your scope raises
  `ScopeError`. `cache.py` caches each part, keyed on the params it read and its source. `checks.py` and `util.py`
  are shared helpers.
- `knobparam/assembly/`: `build.py` (merge order), `checks.py` (cross checks and all-pairs clashes), `render.py`
  (section and iso PNGs), `report.py` and `hall_dyn.py` (Hall vernier dynamics).
- `build.py --contract` does an AST lint that blocks imports between subs. Data crosses only through INTERFACE or
  EXPORTS.
- `electronics/kicad/`: generators for KiCad projects (pcbnew, system python3). Flow:
  `export_cad_constraints.py` -> `make_*_footprints.py` -> `<board>/kicad/make_board.py` -> `export_pcb_proxy.py`
  -> `fab_export.py`. The CAD uses a proxy board, or the committed STEP with `--full`.
- v0.17 status: 62/62 checks PASS, 0 clashes (`cad/assemblies/knob-stack-v0.17/check.json`).

Joystick (`joystick-v04/cad/joystick-param/`): a smaller, single-package version of the same pattern.
`jsparam/params.py` holds `P` plus `derive()` (it reads the knob OD from knob-param, as data only). Then come
`parts.py`, `checks.py` and `render.py`. `build.py` also writes `geom.json` for the KiCad daughterboard generator.
v0.4 status: 65/65 checks PASS.

## How to run it

The bundle is a code snapshot. To run it, clone the repo and check out the branch so the paths line up. The joystick
reads `../knob-param` from beside itself.

```bash
git clone https://github.com/EdgerEquals/knob-hardware && cd knob-hardware
git checkout sub/assembly-v017              # or sub/joystick-v04
bash cad/knob-param/setup.sh                # venv + pinned requirements (Python 3.11+, build123d 0.13.0)
PY=cad/knob-param/.venv/bin/python

$PY cad/knob-param/build.py --contract      # must print "contract: OK"
$PY cad/knob-param/build.py                 # all parts + local + cross checks + clashes
$PY cad/knob-param/build.py --render        # sections PNG -> cad/assemblies/knob-stack-<version>/
$PY cad/knob-param/build.py --sub control_dial --preview
$PY cad/knob-param/build.py --set knob_wall=1.8 --set feel.can_d=6   # override any param
$PY cad/knob-param/build.py --dump          # every value with its owner
$PY cad/knob-param/build.py --full --render # real KiCad main-PCB STEP instead of the proxy
$PY cad/knob-param/report.py                # engineering report

# joystick (on sub/joystick-v04)
cd cad/joystick-param && ../knob-param/.venv/bin/python build.py [--preview|--render|--step]
```

If rendering fails with an OpenGL error, prefix `xvfb-run -a`. A cold full build plus render takes about 30–40 s on
4 cores, and about 10 s cached.

## Design rules (Ed's)

1. **Everything parametric.** No hard-coded dimensions. Sizes come from params or ratios, each tagged and
   commented, with one owner per param.
2. **As light as possible.** Thin printable walls (1.2 mm lip = three 0.4 mm lines), no extra parts.
3. **KiCad is the source of truth for PCBs.** The CAD reads board geometry from KiCad (proxy JSON or STEP) and
   never the other way round.
4. **No radio on the knob boards.** No Wi-Fi or Bluetooth. Comms are FDCAN, USB-C, and the data-over-power line down
   the brass tube.
5. **Every subsystem off by default.** Each laser, LED chain, motor and screen can be switched by the G4. Lasers
   are ≤1 mW (Class 1/2) with a stall cut-off, and every beam ends on a glow or diffusing surface.
6. Sub-assembly isolation: a sub edits only its own folder, and interface changes go through the assembly layer.

## Questions for you

1. **Structure.** Is the params -> derive -> parts -> checks split with the scope guard sound? Is anything
   over-engineered or fragile in `common/model.py` and `common/cache.py`? Should the joystick move onto the same
   harness as a 6th sub?
2. **Parametric gaps.** Can you find hard-coded numbers in `parts/*.py`, `render.py` or `interface.py` that
   should be params or ratios? Are there any derived values that silently diverge if an input changes (for example,
   the knob OD, gear centre distances, the joystick placement)?
3. **Missing checks.** What should we add? Ideas: printability (minimum wall and feature sizes per material:
   nylon, PETG, clear SLA), gear mesh (contact ratio, undercut, backlash at m0.5), clearance swept over the full
   ±10° dial travel and the whole knob rotation rather than one pose, assembly order, centre of mass and weight
   budget, and laser beam-path clearance once the optics land.
4. **Geometry risks.** Known thin spots: 0.48–0.51 mm thrust-race lands under steel balls, and the 716 shaft
   length. What else looks risky, for example the brittle clear-resin parts, the joystick spring preload or the
   standoff stack?
5. **Speed.** How can builds go faster? Options: smarter caching, parallel part builds, cheaper clash detection
   (bounding-box prefilter before boolean intersection), lighter render meshes.
6. **Optics round prep.** What is the cleanest way to add the lasers, wedge prisms, resin gear caps and glow
   surfaces as a new sub, including a simple ray or beam-path check?
7. **Exports.** Is there a clean way to emit USDZ (for iPhone AR Quick Look) plus STEP/STL per assembly from this
   pipeline?
