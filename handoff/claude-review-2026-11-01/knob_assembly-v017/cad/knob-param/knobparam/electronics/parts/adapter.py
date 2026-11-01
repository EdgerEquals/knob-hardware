"""Screen adapter board (Ø15.5, on the tube end, clamped by the rod nut) + component envelopes [K positions]."""
from build123d import *
from ...common.util import A, cyl

def build(D):
    out = {"adapter board": cyl(D["adapter_d"] / 2, D["z_floor"], D["adapter_t"]) - cyl(D["rod_d"] / 2 + 0.1, D["z_floor"], D["adapter_t"])}
    for ref, (fp, x, y, rot) in D["adapter_fps"].items():
        w, l, h = D["adapter_env"][fp]
        if rot % 180: w, l = l, w
        out[f"adapter part {ref}"] = Pos(x, y, D["z_board_top"]) * Box(w, l, h, align=A)
    return out
