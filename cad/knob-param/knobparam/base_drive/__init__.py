"""base_drive sub-assembly: base cradle (+ Hall slot, thrust groove), brass tube, M1.6 rod + sleeve/nuts/washer, 1220 motor +
pinion, idler pinions + pin. Owner: base_drive agent."""
from . import params
from .parts import cradle, brass, motor, idlers, hall_slot
PART_MODULES = [motor, brass, cradle, idlers]
from .checks import checks
