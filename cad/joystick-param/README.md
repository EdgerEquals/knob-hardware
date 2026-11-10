# joystick-param — top-screen joystick sub-assembly (v0.9)

v0.9 (3 Nov 2026 evening, [Ed 18:35 / 19:12]): the cradle is printed into the case (one UTR-8100 print with the faceplate: the lip ring
fills the cutout wall below the front, the flange is joined to the faceplate back by a riser; hangers, end walls, ball seats and shoulders as
v0.8). No bead, no top-edge step. The pins take the stack (the vertical boards' end tabs clear the top board); 4.5 tall sockets; the pin rows
0.3 inboard and 2.5 toward the knob [A]. The top board goes in from the back on its own, glued up under the printed shoulders [A], with
corner notches round the top corner posts. The knob model fuses `parts.case_cradle(D, ov=0.02)` into its `case` (assembly/build.py), so the
BOM and the per-part STEP have one printed part. Notes: `docs/layout-v4-2026-11-03.md` ("v0.25: joystick cradle in the case").

v0.8 (3 Nov 2026, step-1 follow-ups [Ed 13:09–14:08]): the cup over the stem is printed into the bezel and sits on the stem (the switch's
own click is the press); the press peg, the four press springs, their grubs and inserts and the grub-access holes are gone. The guide heads
hang a float below the carrier bosses with a soft silicone-sponge ring under each boss (comparison in `derive`, rows in `checks`). The top
board carries two 13-way 1.27 sockets underneath; the vertical boards' male pins plug in and their end tabs bear on the top board (the
boards are the posts). Form-in-place silicone bead on the flange and in a new top-edge step (rebate in the cutout wall, dam on the lip ring).
Notes: `docs/layout-v4-2026-11-03.md` ("Step 1 follow-ups in the model"). v0.7 text follows.

v0.7 (3 Nov 2026, layout v4 step 1): base `case`. The top board rests on the knob-param vertical boards' spring contacts and is glued
into a clear SLA cradle captured by the case (flange on a gasket behind the faceplate, lip ring in its cutout); the glued cradle,
dowels, H11 sockets and long-pin headers below are gone, and the carrier narrows to make room for the lip. (v0.6 and earlier, and the
v0.7 spring contacts, are in git history up to 3238bb9: the model now builds only `base="case"`.)
Notes: `docs/top-screen-joystick.md` (v0.7) and `docs/layout-v4-2026-11-03.md` ("Step 1 in the model"). The v0.6 text follows.

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
- `jsparam/checks.py`: the bezel's cup on the stem, the up-stop (guide heads on cushions), captive bezel, the case cradle (v0.9: printed
  with the case), the screen jumper, hold-down springs and tipping, switch centring, symmetry, wall thickness, knob clearance.
- `jsparam/render.py`: the colour PNG and the views.

The KiCad daughterboard folder is `cad/knob-param/knobparam/electronics/kicad/joystick-daughterboard/`. `build.py` writes
`geom.json` there: `main_pcb_holes` (the hold-down spring bores, read by the knob model's electronics) and what the top board's KiCad
generator will need (`top_joint`, `guide_keepout`, `corner_notches`). `make_project.py` there is the superseded v0.4 daughterboard
generator (headers, standoffs); it no longer matches `geom.json`.
