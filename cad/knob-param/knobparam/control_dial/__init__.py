"""control_dial sub-assembly: the dial's lower part (tube, Hall arm + magnet row, detent spoke, spring column) and dish, the
v0.24 bezel cartridge (dial screen, bezel, dial board, plug pad), the strap loop. Older options still built by their flags: the
thrust carrier (tb_on), the v0.16 screen panel / carrier and the adapter cup.
Owner: control_dial agent. Public helpers for the assembly cross-checks: arm(D, travel), strap_bent(D, travel)."""
from . import params
from .parts import dial, thrust, hall_arm, screen, holder, cartridge
PART_MODULES = [thrust, dial, hall_arm, screen, holder, cartridge]   # cartridge: v0.24 [Ed 3 Nov 12:41] bezel cartridge (screen + holder empty then)
from .parts.hall_arm import arm
from .parts.screen import strap_bent
from .parts.cartridge import strap as strap_loop
from .checks import checks
