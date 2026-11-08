"""Room for a silkscreen logo on each laid-out board face (8 Nov 2026, Ed 16:47: "I wanna use all of them so tell me how many I have
and what size"). For each board and face: the outline less 0.3 at the edge, every pad on that face (and every through pad and hole on
both), every footprint's courtyard on that face (its body would hide the logo), then the free pieces and the biggest rectangle in each.
Silkscreen may cross tracks and pours (they are under the solder mask); PCBWay clips it at pads and vias. Run with KiCad's python:
  /usr/bin/python3 tools/studies/board_logo_spots.py <out.json> <board.kicad_pcb> [...]"""
import json, sys
import numpy as np
import pcbnew
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union, polygonize
from matplotlib.path import Path

MM = 1e-6


def outline(b):
    segs = []
    for d in b.GetDrawings():
        if d.GetLayer() != pcbnew.Edge_Cuts:
            continue
        sh = d.GetShape()
        if sh == pcbnew.SHAPE_T_SEGMENT:
            segs.append([(d.GetStart().x * MM, d.GetStart().y * MM), (d.GetEnd().x * MM, d.GetEnd().y * MM)])
        elif sh == pcbnew.SHAPE_T_ARC:
            c = d.GetCenter(); r = d.GetRadius() * MM
            a0 = np.arctan2(d.GetStart().y - c.y, d.GetStart().x - c.x); a1 = np.arctan2(d.GetEnd().y - c.y, d.GetEnd().x - c.x)
            am = np.arctan2(d.GetArcMid().y - c.y, d.GetArcMid().x - c.x)
            # go from a0 to a1 through am
            def norm(a): return (a - a0) % (2 * np.pi)
            sweep = norm(a1) if norm(am) < norm(a1) else norm(a1) - 2 * np.pi
            t = np.linspace(0, sweep, 24)
            segs.append([(c.x * MM + r * np.cos(a0 + u), c.y * MM + r * np.sin(a0 + u)) for u in t])
        elif sh == pcbnew.SHAPE_T_CIRCLE:
            c = d.GetCenter(); r = d.GetRadius() * MM
            segs.append([(c.x * MM + r * np.cos(u), c.y * MM + r * np.sin(u)) for u in np.linspace(0, 2 * np.pi, 49)])
        elif sh == pcbnew.SHAPE_T_RECT:
            s, e = d.GetStart(), d.GetEnd()
            segs.append([(s.x * MM, s.y * MM), (e.x * MM, s.y * MM), (e.x * MM, e.y * MM), (s.x * MM, e.y * MM), (s.x * MM, s.y * MM)])
        elif sh == pcbnew.SHAPE_T_POLY:
            pts = [(p.x * MM, p.y * MM) for p in d.GetPolyPoints()]
            segs.append(pts + pts[:1])
    from shapely.geometry import LineString
    lines = []
    for sg in segs:
        for a, c in zip(sg[:-1], sg[1:]):
            lines.append(LineString([a, c]))
    polys = list(polygonize(unary_union(lines)))
    polys.sort(key=lambda p: -p.area)
    outer = polys[0]
    for p in polys[1:]:   # inner cut-outs
        if outer.contains(p.representative_point()):
            outer = outer.difference(p)
    return outer


def rect_of_bbox(bb, grow=0.0):
    return box(bb.GetX() * MM - grow, bb.GetY() * MM - grow, bb.GetRight() * MM + grow, bb.GetBottom() * MM + grow)


def biggest_rect(poly, g=0.05):
    x0, y0, x1, y1 = poly.bounds
    xs = np.arange(x0, x1, g) + g / 2; ys = np.arange(y0, y1, g) + g / 2
    if len(xs) < 2 or len(ys) < 2:
        return None
    XX, YY = np.meshgrid(xs, ys); P = np.c_[XX.ravel(), YY.ravel()]
    inside = Path(np.array(poly.exterior.coords)).contains_points(P)
    for r in poly.interiors:
        inside &= ~Path(np.array(r.coords)).contains_points(P)
    M = inside.reshape(len(ys), len(xs)); hgt = np.zeros(len(xs), int); best = (0, None)
    for j in range(len(ys)):
        hgt = np.where(M[j], hgt + 1, 0); st = []
        for i in range(len(xs) + 1):
            hh = hgt[i] if i < len(xs) else 0; s = i
            while st and st[-1][1] >= hh:
                s, h0 = st.pop(); a = h0 * (i - s)
                if a > best[0]:
                    best = (a, (xs[s] - g / 2, ys[j - h0 + 1] - g / 2, xs[i - 1] + g / 2, ys[j] + g / 2))
            st.append((s, hh))
    return best[1]


out = {}
for path in sys.argv[2:]:
    b = pcbnew.LoadBoard(path)
    name = path.split("/")[-1].replace(".kicad_pcb", "")
    brd = outline(b).buffer(-0.3, join_style=2)
    res = {}
    for side, cu, crt in (("front", pcbnew.F_Cu, pcbnew.F_CrtYd), ("back", pcbnew.B_Cu, pcbnew.B_CrtYd)):
        obs = []
        for f in b.GetFootprints():
            on_side = (f.GetLayer() == cu)
            if on_side:
                cy = f.GetCourtyard(crt)
                if cy.OutlineCount():
                    for k in range(cy.OutlineCount()):
                        ol = cy.Outline(k)
                        pts = [(ol.CPoint(i).x * MM, ol.CPoint(i).y * MM) for i in range(ol.PointCount())]
                        if len(pts) >= 3:
                            obs.append(Polygon(pts).buffer(0.1))
                else:
                    obs.append(rect_of_bbox(f.GetBoundingBox(False, False), 0.1))
            for p in f.Pads():
                through = p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
                if through or p.IsOnLayer(cu):
                    obs.append(rect_of_bbox(p.GetBoundingBox(), 0.15))
        for t in b.GetTracks():
            if t.Type() == pcbnew.PCB_VIA_T:
                c = t.GetPosition(); obs.append(Point(c.x * MM, c.y * MM).buffer(t.GetWidth() * MM / 2 + 0.1, 16))
        free = brd.difference(unary_union(obs)) if obs else brd
        free = free.buffer(-0.6, join_style=2).buffer(0.6, join_style=2)   # drop slivers under 1.2 mm
        spots = []
        for g in getattr(free, "geoms", [free]):
            if g.area < 6:
                continue
            r = biggest_rect(g)
            if r is None:
                continue
            w, h = r[2] - r[0], r[3] - r[1]
            if min(w, h) < 2.0 or w * h < 8:
                continue
            spots.append(dict(w=round(w, 1), h=round(h, 1), at=(round((r[0] + r[2]) / 2 - 100, 1), round((r[1] + r[3]) / 2 - 100, 1))))
        spots.sort(key=lambda s: -s["w"] * s["h"])
        res[side] = spots
    bb = brd.bounds
    out[name] = dict(size=(round(bb[2] - bb[0] + 0.6, 1), round(bb[3] - bb[1] + 0.6, 1)), **res)
    print(name, out[name]["size"])
    for side in ("front", "back"):
        print("  ", side, [(s["w"], s["h"]) for s in res[side]][:6])
json.dump(out, open(sys.argv[1], "w"), indent=1)
