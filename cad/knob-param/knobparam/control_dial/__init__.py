"""control_dial sub-assembly: dial tube + lip (+ ball seating groove), thrust carrier + balls, hub magnet, Hall arm + magnet row,
screen panel + FPC fold/B2B + diametral service strap, screen carrier (on the dial) + fixed adapter cup.
Owner: control_dial agent. Public helpers for the assembly cross-checks: arm(D, travel), strap_bent(D, travel)."""
from . import params
from .parts import dial, thrust, hall_arm, screen, holder
PART_MODULES = [thrust, dial, hall_arm, screen, holder]
from .parts.hall_arm import arm
from .parts.screen import strap_bent
from .checks import checks
