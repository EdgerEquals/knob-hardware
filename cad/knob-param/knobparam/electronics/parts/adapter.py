"""Fixed board on the brass tube end, clamped by the rod nut (the dial up-stop) + component envelopes [K positions].
v0.24 [Ed 3 Nov 12:41]: the rod-link board, Ø12, no parts (the strap's pad only). v0.23: the Ø15.5 screen adapter (J1, U1, C2)."""
from build123d import *
from ...common.util import A, cyl

def build(D):
    name = "rod-link board (fixed, nut on top)" if D.get("cart") else "adapter board"
    out = {name: cyl(D["adapter_d"] / 2, D["z_floor"], D["adapter_t"]) - cyl(D["rod_d"] / 2 + 0.1, D["z_floor"], D["adapter_t"])}
    for ref, (fp, x, y, rot) in D["adapter_fps"].items():
        w, l, h = D["adapter_env"][fp]
        if rot % 180: w, l = l, w
        out[f"adapter part {ref}"] = Pos(x, y, D["z_board_top"]) * Box(w, l, h, align=A)
    return out
