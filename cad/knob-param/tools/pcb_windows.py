# Run from cad/knob-param:  PYTHONPATH=. python tools/pcb_windows.py out.json   (then paste the polygons into electronics pcb_windows)
"""PCB see-through windows A, B, C, E (+ D under the clear OLED), panel frame, from the 2 Nov zone sketch rules:
free = (screen behind) ∩ (board inside a rail) − (mechanism keep-out) − (joystick) − (corner posts) − (other board features)."""
import math, json, sys
from shapely.geometry import box, Point, Polygon
from shapely.ops import unary_union
from knobparam.common import model
D = model.derive(model.default_params())
M = 1.0     # board left round every obstacle
RAIL = 1.5  # board kept inside the outline
x0, x1, y0, y1 = -D["pcb_x1"], D["pcb_x1"], D["pcb_y0"], D["pcb_y1"]
print("pcb", x0, x1, y0, y1, "r_out", D["r_out"], "corners", D["corners"], "notch_r", D["notch_r"])
print("amo_lower", D["amo_lower"], "amo_upper", D["amo_upper"])
board = box(x0 + RAIL, y0 + RAIL, x1 - RAIL, y1 - RAIL)
lower, upper = box(*[D["amo_lower"][i] for i in (0, 2, 1, 3)]), box(*[D["amo_upper"][i] for i in (0, 2, 1, 3)])
r_keep = max(D["r_out"], D["ot_r"] + D["ot_rg"] + D["ot_track_extra"], D["ot_r"] + 1.75, D["knob_od"] / 2) + 2.5   # knob + cradle + emitter bodies, + the case knob ring
print("r_keep", r_keep)
obst = [Point(0, 0).buffer(r_keep, 128)]
py = D["place_y"]   # v0.20: joystick axis from the case (rail rule); carrier and screen carrier are opaque, so nothing to see under them
obst.append(box(-D["half_w"], py - D["half_h"], D["half_w"], py + D["half_h"]).buffer(M))
for x, y in D["corners"]:
    obst.append(Point(x, y).buffer(D["notch_r"] + D.get("tube_press", 1.0) + 1.0 + M))
K = D["pcb_kicad"]
for p in K.get("back_parts", []):
    if math.hypot(p["x"], p["y"]) > 23 and p["ref"] == "J10":
        obst.append(box(p["x"] - p["w"] / 2, p["y"] - p["l"] / 2, p["x"] + p["w"] / 2, p["y"] + p["l"] / 2).buffer(M))
ex, ey = D["enc_xy"]; a = math.radians(D["mech_rot"]); pex, pey = math.cos(a) * ex - math.sin(a) * ey, math.sin(a) * ex + math.cos(a) * ey
obst.append(Point(pex, pey).buffer(D["brg"]["D"] / 2 + D["brg2_seat_wall"] + M))
# v0.19b: encoder daughterboard + header under the PCB (their pins land on the main PCB): keep board round them
from knobparam.under_pcb.parts import encoder
from build123d import Rot
from shapely.geometry import MultiPoint
_ps = encoder.build(model.view(D, "under_pcb"))
for _n in ("encoder header", "encoder daughterboard", "encoder standoff"):
    if _n in _ps:
        _s = Rot(0, 0, D["mech_rot"]) * _ps[_n]
        _pts = [(v.X, v.Y) for v in _s.vertices()]
        obst.append(MultiPoint(_pts).convex_hull.buffer(1.5)); print("obstacle", _n, [round(v, 1) for v in obst[-1].bounds])
blk = unary_union(obst)
Z = {}
Z["A"] = (upper & board).difference(blk) & box(-50, 0, 0, 80)
Z["B"] = (upper & board).difference(blk) & box(0, 0, 50, 80)
ow, oh, _ = D["clear_oled"]; ox, oy = D["clear_oled_xy"]
LEDGE = 1.6   # board strip the clear OLED rests on, all round window D (v0.19b)
y_ce = oy + oh / 2 + LEDGE   # v0.20: C and E stop above the OLED and its ledge (was a fixed -21.8)
Z["E"] = (lower & board).difference(blk) & box(-50, y_ce, 0, 0)
Z["C"] = (lower & board).difference(blk) & box(0, y_ce, 50, 0)
cut = box(ox - 19.2, oy - 12.0, ox + 19.2, oy + 12.0)   # clear OLED cut-away 38.4 x 24, centred on the OLED (v0.20)
Z["D"] = (cut & board & lower).difference(blk)
out = {}
for k in "ABCDE":
    g = Z[k]
    gs = [g] if g.geom_type == "Polygon" else [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon"]
    gs = [p for p in gs if p.area > 4.0]
    if not gs:
        print(k, "empty"); continue
    p = max(gs, key=lambda q: q.area)
    # open slightly to drop slivers narrower than 2 mm, then simplify
    q = p.buffer(-1.0).buffer(1.0, join_style=1)
    q = q.simplify(0.05)
    if q.is_empty or q.area < 4.0:
        print(k, "too thin"); continue
    if q.geom_type != "Polygon":
        q = max(q.geoms, key=lambda r: r.area)
    pts = [(round(x, 2), round(y, 2)) for x, y in q.exterior.coords[:-1]]
    mnx, mny, mxx, mxy = q.bounds
    print(f"{k}: area {q.area:.1f} mm²  x {mnx:.1f}..{mxx:.1f}  y {mny:.1f}..{mxy:.1f}  ({len(pts)} pts)")
    out[k] = pts
json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else "/dev/stdout", "w"))
