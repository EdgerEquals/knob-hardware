"""One saddle clamp, shared by every motor. Seat band(s) on the cradle side, screwed strap opposite.
Local frame: can axis at the origin, +x outboard. Ear thickness and the edge past the hole are ratios of the screw."""
import math
from build123d import *
from .util import A, cyl

def dims(screw_d, ear_k=2.0, edge_k=1.0, hole_k=1.08, head_k=1.8, head_h_k=0.55):
    """Ear thickness = ear_k × screw, edge past the hole = edge_k × screw. hole_k leaves a modelled clearance."""
    hole = hole_k * screw_d
    edge = edge_k * screw_d
    ear_t = ear_k * screw_d
    ear_len = edge + hole + edge
    return dict(hole=hole, edge=edge, ear_t=ear_t, ear_len=ear_len,
                head_d=head_k * screw_d, head_h=head_h_k * screw_d, screw_d=screw_d)

def clamp(can_r, z0, grip, screw_d, glue=0.0, band_t=0.6, band_h=1.2, n_bands=2, split_deg=100.0, band_in=0.5,
          ear_k=2.0, edge_k=1.0):
    """Seat, strap, and one screw per ear (compound). Screw axis is tangential so the head sits outside the strap."""
    d = dims(screw_d, ear_k, edge_k)
    ri, ro = can_r + glue, can_r + glue + band_t
    el, eh, hole = d["ear_len"], d["ear_t"], d["hole"]
    if n_bands <= 1:
        zs = [z0 + max(grip - band_h, 0) / 2]
    else:
        zs = [z0 + band_in, z0 + grip - band_in - band_h]
    seat = strap = screws = None
    for zb in zs:
        sb = _arc(ri, ro, split_deg, 360 - split_deg, zb, band_h)
        tb = _arc(ri, ro, -split_deg, split_deg, zb, band_h)
        for sg in (1, -1):
            e_s = Rot(0, 0, sg * split_deg) * Pos(ri + el / 2, sg * eh / 2, zb) * Box(el, eh, band_h, align=A)
            e_t = Rot(0, 0, sg * split_deg) * Pos(ri + el / 2, -sg * eh / 2, zb) * Box(el, eh, band_h, align=A)
            # hole axis along local Y of the ear (tangential), centred so `edge` remains past the outer end
            hx = ri + el - d["edge"] - hole / 2
            hole_s = Rot(0, 0, sg * split_deg) * Pos(hx, 0, zb + band_h / 2) * Rot(90, 0, 0) * Cylinder(hole / 2, eh * 2 + 0.4)
            sb = sb + e_s - hole_s
            tb = tb + e_t - hole_s
            # screw through the hole, head outside the strap ear
            head = Rot(0, 0, sg * split_deg) * Pos(hx, -sg * (eh + d["head_h"] / 2), zb + band_h / 2) * Rot(90, 0, 0) * Cylinder(d["head_d"] / 2, d["head_h"])
            shank = Rot(0, 0, sg * split_deg) * Pos(hx, 0, zb + band_h / 2) * Rot(90, 0, 0) * Cylinder(screw_d / 2 * 0.96, eh * 2)
            screws = head + shank if screws is None else screws + head + shank
        seat = sb if seat is None else seat + sb
        strap = tb if strap is None else strap + tb
    return seat, strap, screws, d

def _arc(r0, r1, a0, a1, z0, h, n=36):
    pts = [(r1 * math.cos(math.radians(a0 + (a1 - a0) * i / n)), r1 * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    pts += [(r0 * math.cos(math.radians(a1 - (a1 - a0) * i / n)), r0 * math.sin(math.radians(a1 - (a1 - a0) * i / n))) for i in range(n + 1)]
    return Pos(0, 0, z0) * extrude(Face(Wire.make_polygon([Vector(x, y, 0) for x, y in pts], close=True)), h)
