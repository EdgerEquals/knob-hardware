"""under_pcb sub-assembly: encoder pinion/shaft/bearings, big gear + slotted rim (trimmed), EE-SX1321, back-panel depth.
The 716 feel motor moved to base_drive in v0.16 (PCB top, inside the cradle). Owner: under_pcb agent."""
from . import params
from .parts import encoder
PART_MODULES = [encoder]
from .checks import checks
