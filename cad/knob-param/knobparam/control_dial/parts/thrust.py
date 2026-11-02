"""Dial thrust bearing: caged Ø1 balls between the cradle plate top and the dial tube end (ball count from PCD and cage web)."""
import math
from build123d import *
from ...common.util import A, cyl, tube, thrust_groove

def groove(D): return thrust_groove(D["tb_pcd"], D["tb_groove_r"], D["tb_z_ball"])
def ball_xy(D, i): a = 2 * math.pi * i / D["tb_n"]; return (D["tb_pcd"] / 2 * math.cos(a), D["tb_pcd"] / 2 * math.sin(a))

def build(D):
    if not D["tb_on"]:   # v0.19b [Ed]: air gap, no bearing
        return {}
    ci, co, ct = D["tb_cage"]; z0 = D["tb_cage_z0"]
    c = tube(ci / 2, co / 2, z0, ct)
    for i in range(D["tb_n"]): c -= cyl(D["tb_pocket_d"] / 2, z0, ct, *ball_xy(D, i))
    balls = Compound(children=[Pos(*ball_xy(D, i), D["tb_z_ball"]) * Sphere(D["tb_ball_d"] / 2) for i in range(D["tb_n"])])
    return {"thrust carrier": c, f"thrust balls {D['tb_n']} x Ø{D['tb_ball_d']:g}": balls}
