"""v0.15: fixed adapter cup (socket on the tube, adapter well) + screen carrier bonded on the dial (turns with it).
v0.14: Screen holder (fixed, bonded on the brass tube): socket boss, adapter well (cord room over the nut), plate under the panel
(follows the screen offset) with a window for the folded FPC, B2B and COF bend."""
from build123d import *
from ...common.util import A, rev, cyl
from . import screen
SRC_DEPS = [screen]

def build(D):
    rs, rb, rl, ro, rw = D["socket_d"] / 2, D["boss_d"] / 2, D["pocket_lo_d"] / 2, D["hold_od"] / 2, D["well_od"] / 2
    z0, zc, zs, zh = D["hold_z0"], D["z_cup0"], D["hold_step"], D["z_holder0"]
    zt = D["z_cup_top"]   # v0.15: the fixed cup stops carrier_run under the rotating carrier
    h = rev([(rs, z0), (rb, z0), (rb, zc), (rw, zc), (rw, zs), (ro, zs), (ro, zt), (rl, zt), (rl, D["z_floor"]), (rs, D["z_floor"])])
    S = D["S"]; L, W, H = S["fold"]; xo = screen.fold_outer_local(D)
    plate = cyl((D["lip_id"] / 2 if D["screen_on_dial"] else S["od"] / 2), zh, D["z_back"] - zh)
    win = Pos(xo + 0.3, 0, zh - 1) * Box(L + 0.6, W + 0.6, 5, align=(Align.MAX, Align.CENTER, Align.MIN))
    win += Pos(S["r_edge"], 0, zh - 1) * Box(3.0, S["ledge_w"] + 0.6, 5, align=A)
    carrier = screen.place(D, plate) - screen.place(D, win)
    extra = {}
    if D["screen_on_dial"]:   # v0.17 [Ed]: Ø3×1 N52 in the carrier facing Ø3×1 in the dial; Ø1 pin at 270°
        (sx, sy), (px, py) = D["carr_mag_xy"], D["carr_pin_xy"]; pd, pp, pe = D["carr_pin"]
        cd, ch = D["carr_mate"]
        carrier -= cyl(cd / 2, zh - 0.01, ch + 0.01, sx, sy)
        carrier -= cyl(pd / 2 + D["carr_pin_clear"], zh - 0.01, pe + 0.11, px, py)
        md, mh = D["carr_mag"]
        extra = {f"screen carrier magnet (carrier) {cd:g}x{ch:g}": cyl(cd / 2, zh, ch, sx, sy),
                 f"screen carrier magnet (dial base) {md:g}x{mh:g}": cyl(md / 2, zh - D["carr_mag_gap"] - mh, mh, sx, sy),
                 "screen carrier locating pin": cyl(pd / 2, zh - pp, pp + pe, px, py)}
    if D["screen_on_dial"]:   # carrier bonded on the dial shoulder, panel bonded on the carrier: turns with the dial
        return ({"adapter cup (fixed)": h} if D["adapter_cup"] else {}) | {"screen carrier (on dial)": carrier} | extra
    return {"screen holder": h + carrier}
