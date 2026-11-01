# joystick-param — top-screen joystick sub-assembly (v0.4)

Parametric build123d model of the top-screen 5-way joystick. An Alps SKRHADE010 sits on the carrier axis,
on a daughterboard raised by four M2×35 brass standoffs and two 1×3 headers. A flat plate glued on that
board carries the four ball seats. The screen is glued to a separate bezel, which floats on four Lee Spring
CI 008B 01 M compression springs. An M2 grub screw under each spring sets the preload, from under the
carrier, before the stack is assembled. Four hold-down extension springs still hold the carrier on the balls.
There is no spider, no plunger, no round stop and no printed base.
Design notes: `docs/top-screen-joystick.md`. Report: `cad/assemblies/joystick-v0.4/REPORT.md`. v0.3 is kept beside it.

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
