"""main_knob sub-assembly: knob body + skirt, hub gear, 45 deg cone race (knob half) + balls, bottom internal ring.
Owner: main_knob agent. Folder-local: params.py, parts/, checks.py."""
from . import params
from .parts import knob
PART_MODULES = [knob]
from .checks import checks
