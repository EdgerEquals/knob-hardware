"""electronics sub-assembly: main PCB (proxy; --full = committed KiCad STEP) + back-side parts, adapter board + parts (TMAG5273,
J1, U1 ...), Hall sensor row; KiCad projects in electronics/kicad/. Owner: electronics agent."""
from . import params
from .parts import pcb, adapter, hall_sensors, vboards
PART_MODULES = [pcb, hall_sensors, adapter, vboards]   # vboards: [Ed 3 Nov] layout v4 vertical boards under the joystick
from .parts.pcb import pcb_full, kicad_step_path
from .checks import checks
