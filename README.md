# knob-hardware

This repo holds the hardware for Ed's motorised knob and its Eurorack module (10HP).

- `cad/` is the parametric parts library. Each part folder has a build123d script, STEP, DXF and drawing PNG. The parts index is in `cad/README.md`.
- PCBs live in KiCad projects under `cad/pcbs/`, which are the single source of truth. Board STEPs are exported from KiCad and feed the mechanical assemblies.
- Dimensions marked [A] are assumed and need checking with calipers.
- `cad/knob-param/` (branch `param-dev`) is the sub-assembly-split parametric model of the whole knob stack, set up for parallel cloud-agent work. Start with `cad/knob-param/AGENTS.md`.

## Docs

- [Design notes](docs/design-notes.md): the current knob-module design (CAD v0.16), check status and open items.
- [Top screen joystick](docs/top-screen-joystick.md): the sliding screen carrier on the Alps SKRHADE010 and the switch shortlist.
- [Manufacturing (PCBWay)](docs/manufacturing-pcbway.md): the kit plan, what PCBWay builds, the cost target and reviewer questions.

The software engine lives in EdgerEquals/dad-page.
