# knob-hardware

This repo holds the hardware for Ed's motorised knob and its Eurorack module (10HP).

- `cad/` is the parametric parts library. Each part folder has a build123d script, STEP, DXF and drawing PNG. The parts index is in `cad/README.md`.
- PCBs live in KiCad projects under `cad/pcbs/`, which are the single source of truth. Board STEPs are exported from KiCad and feed the mechanical assemblies.
- Dimensions marked [A] are assumed and need checking with calipers.

The software engine lives in EdgerEquals/dad-page.
