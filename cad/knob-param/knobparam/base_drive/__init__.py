"""base_drive sub-assembly: base cradle (+ Hall slot, thrust groove, feel-motor rib), brass tube, M1.6 rod + sleeve/nuts/washer,
1220 motor + pinion, idler pinions + pins, 716 feel motor + clip. Owner: base_drive agent."""
from . import params
from .parts import cradle, brass, motor, idlers, feel, hall_slot
PART_MODULES = [motor, brass, cradle, idlers, feel]
from .checks import checks
