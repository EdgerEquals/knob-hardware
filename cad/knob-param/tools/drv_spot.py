# Run from cad/knob-param:  PYTHONPATH=. python tools/drv_spot.py
"""Free spot for the 716 driver cluster (U20 + C20-C22) on the PCB back, inside the emitter ring, mechanism frame."""
import math, sys
from shapely.geometry import box, Point
from shapely.affinity import rotate
from shapely.ops import unary_union
from knobparam.common import model
D = model.derive(model.default_params())
F = D["feel"]; K = D["pcb_kicad"]
def rect(x, y, w, l, a=0):
    return rotate(box(x - w/2, y - l/2, x + w/2, y + l/2), a, origin=(x, y))
obs = []
R = D["ot_r"]
for i in range(24):
    obs.append(("em", rotate(box(R - 1.4, -1.75, R + 1.4, 1.75), i * 15.0 + 7.5 * (len(sys.argv) > 1), origin=(0, 0))))
for r, a in zip(D["hv_r"], D["hv_phi_s"]):
    obs.append(("hallC", rect(r*math.cos(math.radians(a)), r*math.sin(math.radians(a)), 1.1, 0.6, a)))
pw, pl = F["pad"]
for px, py in D["fm_pad_xy"]:
    obs.append(("fmpad", rect(px, py, pl, pw, D["fm_ang"] + 90)))
obs.append(("fmshaft", Point(*D["fm_xy"]).buffer(D["fm_shaft_hole"]/2 + 0.3)))
obs.append(("fghole", Point(*D["fg_xy"]).buffer(D["fg_hole"]/2 + 0.3)))
obs.append(("fg gear plan", Point(*D["fg_xy"]).buffer(D["fg_tip"] + 0.3)))
ex, ey = D["enc_xy"]; obs.append(("brg2seat", Point(ex, ey).buffer(D["brg"]["D"]/2 + D["brg2_seat_wall"] + 0.2)))
obs.append(("rodpad", Point(0, 0).buffer(D["rod_pad_r"] + 0.3)))
M = D["motor"]
for s in (-1, 1):
    obs.append(("tab", rect(D["offset"] + s*M["term_pitch"]/2, 0, M["term_t"] + 0.6, M["term_w"] + 0.6)))
for h in K.get("holes", []):
    if math.hypot(h["x"], h["y"]) < 23: obs.append(("khole", Point(h["x"], h["y"]).buffer(h["d"]/2 + 0.3)))
for p in K.get("back_parts", []):
    if p["ref"] in ("U20", "C20", "C21", "C22") or (p["ref"].startswith("C1") and len(p["ref"]) == 3): continue
    if math.hypot(p["x"], p["y"]) < 23: obs.append(("kpart " + p["ref"], rect(p["x"], p["y"], p["w"], p["l"])))
for x, y in D.get("peg_xy", []) or []:
    obs.append(("peg", Point(x, y).buffer(D["peg_d"]/2 + 0.3)))
print("obstacles:", sorted(set(n for n, _ in obs)), "pad", F["pad"], "pegs", D.get("peg_xy"))
CL = [("U20", 0, 0, 2.95, 2.55), ("C20", 0, 2.2, 1.91, 0.99), ("C21", -2.9, 1.0, 0.99, 1.91), ("C22", -4.7, 1.0, 1.55, 3.05)]
def cluster(x, y, rot):
    out = []
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    for ref, dx, dy, w, l in CL:
        cx, cy = x + c*dx - s*dy, y + s*dx + c*dy
        out.append((ref, rotate(box(cx - w/2, cy - l/2, cx + w/2, cy + l/2), rot, origin=(cx, cy))))
    return out
pads = D["fm_pad_xy"]; pc = ((pads[0][0]+pads[1][0])/2, (pads[0][1]+pads[1][1])/2)
best = []
for rot in range(0, 360, 15):
    for xi in range(-170, 171, 5):
        for yi in range(-170, 171, 5):
            x, y = xi/10, yi/10
            u = unary_union([g for _, g in cluster(x, y, rot)])
            gs = [u] if u.geom_type == "Polygon" else list(u.geoms)
            rmax = max(math.hypot(px, py) for g in gs for px, py in g.exterior.coords)
            if rmax > 17.6: continue
            dmin = min(u.distance(g) for _, g in obs)
            if dmin < 0.6: continue
            best.append((math.hypot(x - pc[0], y - pc[1]), x, y, rot, rmax, dmin))
best.sort()
for b in best[:10]: print("trace %.2f at (%.1f, %.1f) rot %d  rmax %.2f  clear %.2f" % b)
print("pads centre (%.2f, %.2f), old U20 (-10.25, 12.96) r 16.5" % pc)
