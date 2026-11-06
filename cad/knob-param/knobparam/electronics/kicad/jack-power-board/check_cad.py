"""Jack power board and jack lower board vs the knob model (step 2, 6 Nov 2026): the KiCad boards (upper/placement.json and
lower/placement.json, written by make_boards.py) must match the model (case/params.py, case/parts/shell.py): outlines (the jack row,
the power board's ears), the posts' pins [Q24], both pairs of 2x6 stacks (and that each pair's pins line up: the jack board's H1/H2
over the power board's H1/H2, the power board's H3/H4 over the lower board's H5/H6, net for net), the flex connectors on the lower
board's underside where the model has them, every pad 0.25 from the edge, and nothing on the faces taller than the model's envelope.
Run from cad/knob-param:  PYTHONPATH=. .venv/bin/python knobparam/electronics/kicad/jack-power-board/check_cad.py
Writes check_cad.txt next to this file and exits 1 on any FAIL."""
import json, math, os, sys
sys.path.insert(0, ".")
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union
from knobparam.common import model

HERE = os.path.dirname(os.path.abspath(__file__))
TOL = 0.005


def main():
    D = model.derive(model.default_params())
    rows = []

    def row(name, ok, detail):
        rows.append(("PASS" if ok else "FAIL", name, detail))
    up = json.load(open(os.path.join(HERE, "upper", "placement.json")))
    lo = json.load(open(os.path.join(HERE, "lower", "placement.json")))
    jb = json.load(open(os.path.join(HERE, "..", "jack-board", "placement.json")))
    bx0, bx1 = D["jb_x"]; by0, by1 = D["jack_bot_y"], D["jack_top_y"]
    hx, ty = D["jb_tab"]
    m_up = unary_union([box(bx0, by0, bx1, by1)] + [box(x - hx, ty, x + hx, by0) for x, _y in D["jb_post_xy"]])
    m_lo = box(bx0, by0, bx1, by1)
    for nm, pl, m in (("power board", up, m_up), ("lower board", lo, m_lo)):
        k = Polygon(pl["outline"])
        d = m.symmetric_difference(k).area
        row(f"{nm} outline = the model's", d < 1e-3, f"area {k.area:.2f} vs model {m.area:.2f}; difference {d:.4f} mm²")
        row(f"{nm} thickness", abs(pl["thickness"] - (D["jb2_t"] if nm == "power board" else D["jb3_t"])) < 1e-6, f"{pl['thickness']}")
        edge = k.exterior
        dmin, worst = 9e9, ""
        for p in pl["pads"]:
            x, y = p["xy"]; w, h = p["size"]
            if abs(round(p.get("rot", 0)) % 180) == 90:
                w, h = h, w
            s = Point(x, y).buffer(w / 2) if p["drill"][0] > 0 else box(x - w / 2, y - h / 2, x + w / 2, y + h / 2)
            dd = s.distance(edge) if s.within(k) else -1.0
            if dd < dmin:
                dmin, worst = dd, f"{p['ref']}.{p['num']}"
        row(f"{nm}: every pad at least 0.25 from the edge", dmin >= 0.25 - 1e-6, f"nearest {dmin:.3f} ({worst})")
    # posts [Q24]
    pin = D.get("jb_post_pin")
    for i, (x, y) in enumerate(D["jb_post_xy"], 1):
        p = [q for q in up["pads"] if q["ref"] == f"MP{i}"]
        ok = len(p) == 1 and math.dist(p[0]["xy"], (x, y)) <= TOL and abs(p[0]["drill"][0] - pin[1]) <= TOL and abs(p[0]["size"][0] - pin[2]) <= TOL
        row(f"post {i} pin pad at the model's post ({x:g}, {y:.2f})", ok,
            f"{p[0]['net']} drill Ø{p[0]['drill'][0]:g} pad Ø{p[0]['size'][0]:g} (model Ø{pin[1]:g} / Ø{pin[2]:g}, Q24 = A)" if p else "missing")
    # stacks line up, net for net
    def pins_of(pl, ref):
        return [(q["xy"], q["net"]) for q in pl["pads"] if q["ref"] == ref]

    def column_rows(pads, cx):
        out = {}
        ys = sorted({round(xy[1], 3) for xy, _n in pads}, reverse=True)
        for xy, n in pads:
            out[("in" if abs(xy[0]) < abs(cx) else "out", ys.index(round(xy[1], 3)))] = n
        return out
    hw, hl, hdx = D["jb_hdr"]
    for a_pl, a_ref, b_pl, b_ref, what in ((jb, "H1", up, "H1", "jack board H1 / power board H1"), (jb, "H2", up, "H2", "jack board H2 / power board H2"),
                                           (up, "H3", lo, "H5", "power board H3 / lower board H5"), (up, "H4", lo, "H6", "power board H4 / lower board H6")):
        A, B = pins_of(a_pl, a_ref), pins_of(b_pl, b_ref)
        ca = a_pl["parts"][a_ref]["xy"]; cb = b_pl["parts"][b_ref]["xy"]
        ma, mb = column_rows(A, ca[0]), column_rows(B, cb[0])
        same = ma == mb and len(ma) == 12
        row(f"{what}: same place, same nets pin for pin", same and math.dist(ca, cb) <= TOL and abs(abs(ca[0]) - hdx) <= TOL,
            f"centres ({ca[0]:.3f}, {ca[1]:.3f}) / ({cb[0]:.3f}, {cb[1]:.3f}); {sum(1 for k in ma if ma.get(k) == mb.get(k))}/12 nets agree")
    # flex connectors on the lower board's underside, where the model has them, opening toward the bottom edge
    for ref, (w, d, h, xc), nm in (("J5", D["zif_oled"], "clear OLED ZIF"), ("J6", D["zif_link"], "link flex connector")):
        p = lo["parts"].get(ref)
        pads = [q for q in lo["pads"] if q["ref"] == ref]
        if not p:
            row(f"{nm} on the lower board", False, "missing"); continue
        xs = [q["xy"][0] for q in pads]; ys = [q["xy"][1] for q in pads]
        inside = by0 + D["zif_y_off"] - 0.7 <= min(ys) and max(ys) <= by0 + D["zif_y_off"] + d + 1.6 and \
            xc - w / 2 - 0.5 <= min(xs) and max(xs) <= xc + w / 2 + 0.5
        row(f"{nm} under the lower board at the model's place", p["side"] == "B" and inside,
            f"pads x {min(xs):.2f}..{max(xs):.2f}, y {min(ys):.2f}..{max(ys):.2f}; model x {xc - w / 2:.2f}..{xc + w / 2:.2f}, "
            f"y {by0 + D['zif_y_off']:.2f}..{by0 + D['zif_y_off'] + d:.2f}")
    out = [f"Jack power board {up['pcb_version']} + jack lower board {lo['pcb_version']} vs knob model {up['cad_version']} (tolerance {TOL} mm)"]
    out += [f"  {s}  {n}: {d}" for s, n, d in rows]
    nf = sum(1 for s, *_ in rows if s == "FAIL")
    out.append(f"{len(rows) - nf}/{len(rows)} PASS")
    txt = "\n".join(out) + "\n"
    open(os.path.join(HERE, "check_cad.txt"), "w").write(txt)
    print(txt)
    return 1 if nf else 0


if __name__ == "__main__":
    sys.exit(main())
