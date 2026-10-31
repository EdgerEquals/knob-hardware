"""under_pcb sub-assembly: encoder pinion/shaft/bearings, big gear + slotted rim (trimmed), EE-SX1131, feel motor + clip
(+ optional gearhead envelope), back-panel depth. Owner: under_pcb agent. Public helper: gearhead(D)."""
from . import params
from .parts import encoder, feel
PART_MODULES = [encoder, feel]
from .parts.feel import gearhead
from .checks import checks
