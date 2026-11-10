"""base_drive sub-assembly: base cradle (+ Hall slot and stop faces, spring posts), brass tube, M1.6 rod + sleeve/nuts/washer,
1220 motor + pinion, idler pinions + pins, the detent block and train (mech). The 716 feel motor + clip only with feel_on
(Q27, parked). Owner: base_drive agent."""
from . import params
from .parts import cradle, brass, motor, idlers, feel, hall_slot, mech
PART_MODULES = [motor, brass, cradle, idlers, feel, mech]
from .checks import checks
