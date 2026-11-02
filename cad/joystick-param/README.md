# joystick-param — top-screen joystick sub-assembly (v0.6)

Parametric build123d model of the top-screen 5-way joystick. An Alps SKRHADE010 sits on the carrier axis, on a daughterboard
glued on a printed cradle (MJF PA-12, 30 mm) that is glued to the main PCB on two dowels; two 2×5 long-post headers carry the
signals down. Four Ø2 balls on cradle towers at the extreme corners carry the carrier; four hold-down springs (0.9 N) keep it
on them. The screen is glued on the roof of a 5 mm grip block (the bezel), which floats on four Lee Spring CI 008B 01 M
compression springs (grub-screw preload, reset after assembly through Ø1.6 holes in the main PCB) and is tied to the carrier by two guide screws in brass
sleeves; their heads are the up-stop. The case places it: as high as the top rail screws allow.
v0.6: the DO0164FMST02 screen in a pocketed 2.35 roof with foam pads, the guides turned to (±6.5, ±3.0), and a custom jumper
from the panel's B2B header to the daughterboard socket. Studies: `fmst02_fit.py`, `fmst02_route.py`, `fmst02_guide_study.py`
(they read Waveshare's STEP, not committed); sections: `section_v06.py`.
Design notes: `docs/top-screen-joystick.md` (v0.5 and v0.6 sections). Decisions: `docs/case-decisions-2026-11-02.md`. v0.4 is kept in
`cad/assemblies/joystick-v0.4/` (outputs only; the v0.4 code is in git history before `asm/v020-layout`).

```
python build.py              # build + checks + pairwise clashes
python build.py --preview    # low-res isometric PNG
python build.py --render     # colour sheet, plan, clean view, and views/
```

Run it with the knob-param venv: `cad/knob-param/.venv/bin/python build.py`.

- `jsparam/params.py`: `P` (tags: [A] assumed, [Ed] from Ed, [S] datasheet) and `derive()`.
- `jsparam/parts.py`: parts, all in the local frame. z is measured from the main-PCB front face. The origin is the carrier centre.
- `jsparam/checks.py`: stem/cup, spring preload and press force, captive bezel, switch centring, symmetry, four standoffs, wall thickness, knob clearance.
- `jsparam/render.py`: the colour PNG and the views.

The KiCad daughterboard is at `cad/knob-param/knobparam/electronics/kicad/joystick-daughterboard/`. `build.py` writes
`geom.json` there; `make_project.py` (system `python3`, with pcbnew) turns that into the board. The fab pack is
`joystick-daughterboard/fab/`.
