"""base_drive: slot through the cradle plate for the dial's Hall arm (from the INTERFACE Hall layout + own hv_slot_clear)."""
import math
from build123d import *
from ...common.util import A, cyl, sector

def _vern(D): return D["hall_layout"] == "vernier"

def _bar_samples(D, n=8):
    """Centreline of the magnet bar (pads + the links between them)."""
    rs, ps = D["hv_r"], D["hv_phi_m"]
    pts = []
    for i, (r, a) in enumerate(zip(rs, ps)):
        if i:
            r0, a0 = rs[i - 1], ps[i - 1]
            for k in range(1, n):
                t = k / n
                pts.append((r0 + (r - r0) * t, a0 + (a - a0) * t))
        pts.append((r, a))
    return pts

def window(D):
    """v0.17 [Ed]: one smooth slot, an even clearance off the arm's swept envelope (not the stepped per-pad zig-zag).
    v0.18: the sweep is an annular sector, not three disks. Disks at ±travel left the ±10° pose 0.2 mm closer to the web."""
    if not _vern(D): return sector(D["ha_win_r0"], D["ha_pad_r1"] + 3.0, D["ha_win_half"], -0.1, 10.0, D["ha_ang0"])
    pr, c, T = D["hv_pad_r"], D["hv_slot_clear"], D["travel_deg"]
    rad = pr + c
    w = None
    for r, a in _bar_samples(D):
        q = sector(max(r - rad, 0.2), r + rad, T, -0.1, D["plate_t"] + 0.3, a)
        for th in (-T, T):   # round end caps; the sector's radial edge stops at the pad centre
            x = r * math.cos(math.radians(a + th)); y = r * math.sin(math.radians(a + th))
            q += cyl(rad, -0.1, D["plate_t"] + 0.3, x, y)
        w = q if w is None else w + q
    # sensors are fixed; open the slot over each body too so the bar's sweep is not the only cut
    for i, (r, a) in enumerate(zip(D["hv_r"], D["hv_phi_s"])):
        sl = D["hv_dims"][i][1]
        x, y = r * math.cos(math.radians(a)), r * math.sin(math.radians(a))
        w += cyl(max(sl, D["hv_dims"][i][0]) / 2 + c, -0.1, D["plate_t"] + 0.3, x, y)
    return w



# ---- v0.30 [Ed 4 Nov 15:15] (cc_on): compression centring springs in arc pockets, and the hard stop in this slot ----
def _band(r0, r1, a0, a1, z0, z1):
    lo, hi = min(a0, a1), max(a0, a1)
    return sector(r0, r1, (hi - lo) / 2, z0, z1 - z0, (lo + hi) / 2, n=48)

def spring_pockets(D):
    """Two arc pockets at cc_r, from each spring's seat in the arm (at rest) to the pocket end, Ø cc_od + 2 cc_pocket_clear,
    from just under the spring up through the plate top (open: the springs drop in before the dial's lower part)."""
    R, w = D["cc_r"], D["cc_od"] / 2 + D["cc_pocket_clear"]
    z0 = D["cc_z"] - w
    out = None
    for s in (-1, 1):
        q = _band(R - w, R + w, D["cc_seat_ang"][s], D["cc_pocket_ang"][s], z0, D["plate_t"] + 0.3)
        out = q if out is None else out + q
    return out

def stop_faces(D):
    """The two stop faces: blocks on the slot's end walls whose faces are the bar's link faces at exactly ±travel."""
    out = None
    for s, j, r0, r1, poly in D["cc_stop_polys"]:
        a = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]))
        pts = poly if a > 0 else poly[::-1]
        q = Pos(0, 0, D["cc_stop_z0"]) * extrude(Face(Wire.make_polygon([Vector(x, y, 0) for x, y in pts], close=True)),
                                                  D["plate_t"] - D["cc_stop_z0"])
        out = q if out is None else out + q
    return out

def springs(D):
    """The springs at rest (arm centred): from the pocket end to the seat (cc_gap short of it), as plain arc tubes (OD, ID = OD -
    2 wire), 0.02 short at each end so they do not read as clashes with the pocket end and the seat."""
    R, ro, ri = D["cc_r"], D["cc_od"] / 2, D["cc_od"] / 2 - D["cc_wire"]
    out = []
    for s in (-1, 1):
        a_end = D["cc_pocket_ang"][s] - s * math.degrees(0.02 / R)
        a_free = D["cc_free_ang"][s] + s * math.degrees(0.02 / R)
        lo, hi = min(a_end, a_free), max(a_end, a_free)
        cut = sector(R - 1.0, R + 1.0, (hi - lo) / 2, D["cc_z"] - 1.0, 2.0, (lo + hi) / 2, n=48)
        tube = (Pos(0, 0, D["cc_z"]) * Torus(R, ro)) - (Pos(0, 0, D["cc_z"]) * Torus(R, ri))
        out.append(tube & cut)
    return out
