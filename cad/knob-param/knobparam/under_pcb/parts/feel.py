"""Feel motor (716 coreless [A]) behind the PCB, direct drive on idler 1: can, Ø1 shaft through M2, clip collar."""
from build123d import *
from ...common.util import A, cyl, tube

def gearhead(D):
    F = D["feel"]; x, y = D["fm_xy"]
    return cyl(F["can_d"] / 2, D["fm_z_end"] - F["gearhead_len"], F["gearhead_len"], x, y)

def build(D):
    F = D["feel"]; x, y = D["fm_xy"]
    can = cyl(F["can_d"] / 2, D["fm_z_can_bot"], F["can_len"], x, y) + cyl(2.0, D["fm_z_end"], F["end_boss"], x, y)
    shaft = cyl(F["shaft_d"] / 2, D["fm_z_can_top"], D["h_pin1"] - D["fm_z_can_top"], x, y)
    clip = tube(F["can_d"] / 2 + 0.05, F["clip_od"] / 2, D["z_pcb_back"] - F["clip_len"], F["clip_len"], x, y)
    return {f"feel motor {F['part']} [A]": can, f"feel motor shaft Ø{F['shaft_d']:g} [A]": shaft, "feel motor clip [A]": clip}
