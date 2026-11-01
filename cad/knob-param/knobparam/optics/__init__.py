"""optics sub-assembly (off by default): 405 nm laser + Risley wedge pair, the VCSEL + RGB ring, glow targets.
Owner: optics. Public helpers for the assembly cross-checks: rays(D) and beam_rows(D, parts, row).
Wedge angle, module and centre distance in this file are assumptions for the check. They are not a design change."""
from . import params
from .parts import scanner, ring_lights
PART_MODULES = [scanner, ring_lights]
from .checks import checks
from .beam import rays, beam_rows
