"""Brass tube (fixed dial shaft, soldered on the PCB ring) + M1.6 rod, sleeve, nuts, washer."""
import math
from build123d import *
from ...common.util import A, cyl, tube

def _nut(D, z0):
    hexa = Pos(0, 0, z0) * extrude(RegularPolygon(D["nut_s"] / math.sqrt(3), 6), D["nut_m"])
    return hexa - cyl(D["rod_d"] / 2, z0, D["nut_m"])

def build(D):
    L = D["z_floor"]
    t = tube(D["brass_id"] / 2, D["brass_od"] / 2, 0, L)
    ends = [e for e in t.edges().filter_by(GeomType.CIRCLE) if abs(e.radius - D["brass_id"] / 2) < 1e-6]
    t = chamfer(ends, D["brass_deburr"])
    wi, wo, _ = D["washer"]; wt = D["nut_seat_t"]; si, so = D["sleeve"]; zb = D["z_pcb_back"]
    return {"brass tube": t,
            "rod M1.6 (VBUS_DATA)": cyl(D["rod_d"] / 2, D["z_rod_bot"], D["z_rod_top"] - D["z_rod_bot"]),
            "rod sleeve": tube(si / 2, so / 2, 0, L),
            "rod nut top": _nut(D, D["z_board_top"]),
            "rod nut bottom": _nut(D, zb - wt - D["nut_m"])} | ({"rod washer bottom": tube(wi / 2, wo / 2, zb - wt, wt)} if D["use_washer"] else {})
