"""optics sub-assembly (v0.18 prep, OFF by default): 405 nm laser + Risley wedge pair, the 12 VCSEL + 12 RGB ring under the
clear-resin race carrier, resin prism caps on gears, glow targets. Owner: optics agent.
Public helpers for the assembly cross-checks: rays(D) and beam_rows(D, parts, row)."""
from . import params
from .parts import scanner, ring_lights
PART_MODULES = [scanner, ring_lights]
from .checks import checks
from .beam import rays, beam_rows
