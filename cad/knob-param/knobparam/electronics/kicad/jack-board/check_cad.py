"""Jack board vs the knob model (step 2, 5 Nov 2026): the KiCad board (placement.json, written by kicad/make_board.py) must match
the model's jack board (case/params.py and case/parts/shell.py): its outline (jack row, tip bumps, sleeve tongues, USB tab), the jack
slots, the 8 spring contacts and the two board-to-board stacks; and keep every pad 0.25 from the edge.
Run from cad/knob-param:  PYTHONPATH=. .venv/bin/python knobparam/electronics/kicad/jack-board/check_cad.py
Writes check_cad.txt next to this file and exits 1 on any FAIL."""
import json, math, os, sys
sys.path.insert(0, ".")
from shapely.geometry import Polygon, box, Point, LineString
from shapely.ops import unary_union
from knobparam.common import model

HERE = os.path.dirname(os.path.abspath(__file__))
TOL = 0.005
NET = {"15 V": "VBUS", "GND": "GND", "D+": "DP", "D-": "DN", "CC1": "CC1", "CC2": "CC2"}


def pad_shape(p):
    x, y = p["xy"]; w, h = p["size"]
    if abs(round(p.get("rot", 0)) % 180) == 90:
        w, h = h, w
    if p["ref"].startswith("J"):      # oval slot pads
        r = min(w, h) / 2
        return LineString([(x, y - (h / 2 - r)), (x, y + (h / 2 - r))]).buffer(r, 32) if h >= w else \
            LineString([(x - (w / 2 - r), y), (x + (w / 2 - r), y)]).buffer(r, 32)
    if p["ref"].startswith("P"):
        return Point(x, y).buffer(w / 2, 32)
    return box(x - w / 2, y - h / 2, x + w / 2, y + h / 2)


def main():
    D = model.derive(model.default_params())
    pl = json.load(open(os.path.join(HERE, "placement.json")))
    rows = []

    def row(name, ok, detail):
        rows.append(("PASS" if ok else "FAIL", name, detail))
    # the model's outline
    bx0, bx1 = D["jb_x"]; by0, by1 = D["jack_bot_y"], D["jack_top_y"]
    parts = [box(bx0, by0, bx1, by1)]
    for (x, _y), (tx0, tx1) in zip(D["jack_xy"], D["jb_tongue_x"]):
        parts.append(box(tx0, D["jb_tongue_y"], tx1, by0))
        if D.get("jb_tip_bump"):
            bw, bh = D["jb_tip_bump"]; parts.append(box(x - bw / 2, by1, x + bw / 2, by1 + bh))
    tw, ty = D["usb_pwr_tab"]; parts.append(box(-tw, ty, tw, by0))
    m_ol = unary_union(parts)
    k_ol = Polygon(pl["outline"])
    diff = m_ol.symmetric_difference(k_ol).area
    row("outline = the model's jack board (jack row, tip bumps, sleeve tongues, USB tab)", diff < 1e-3,
        f"area {k_ol.area:.3f} vs model {m_ol.area:.3f}; difference {diff:.4f} mm²; bounds {tuple(round(v, 2) for v in k_ol.bounds)}")
    row("board thickness", abs(pl["thickness"] - D["jb_t"]) < 1e-6, f"{pl['thickness']} vs model {D['jb_t']}")
    pads = pl["pads"]
    # jacks and their slots
    ring = D["jack_slot_ring"]
    for i, (x, y) in enumerate(D["jack_xy"], 1):
        part = pl["parts"].get(f"J{i}")
        row(f"jack J{i} at the model's jack x {x:g}", part is not None and math.dist(part["xy"], (x, y)) <= TOL and part["side"] == "F",
            f"J{i} at ({part['xy'][0]:.3f}, {part['xy'][1]:.3f}) side {part['side']}" if part else "missing")
        for n, y0, y1, w in D["jack_pins"]:
            p = [q for q in pads if q["ref"] == f"J{i}" and q["num"] == n]
            if not p:
                row(f"J{i} {n} slot", False, "missing"); continue
            p = p[0]; cy = y + (y0 + y1) / 2; L = abs(y1 - y0) + w
            ok = (math.dist(p["xy"], (x, cy)) <= TOL and abs(p["drill"][0] - w) <= TOL and abs(p["drill"][1] - L) <= TOL
                  and abs(p["size"][0] - (w + 2 * ring)) <= TOL and abs(p["size"][1] - (L + 2 * ring)) <= TOL)
            row(f"J{i} {n} slot over every published position", ok,
                f"slot {p['drill'][0]:.2f} x {p['drill'][1]:.2f} at y {p['xy'][1]:.3f}, pad {p['size'][0]:.2f} x {p['size'][1]:.2f} "
                f"(model: {w:g} x {L:.3f} at y {cy:.3f}, ring {ring:g})")
    # contacts
    for (x, y), nm in zip(D["usb_pwr_contacts"], D["usb_pwr_names"]):
        near = [p for p in pads if p["ref"].startswith("P") and math.dist(p["xy"], (x, y)) <= TOL]
        ok = len(near) == 1 and near[0]["net"] == NET[nm] and abs(near[0]["size"][0] - D["usb_pwr_pad"]) <= TOL
        row(f"spring contact {nm} at ({x:.1f}, {y:.1f})", ok,
            f"{near[0]['ref']} net {near[0]['net']}, pad Ø{near[0]['size'][0]}" if near else "no contact pad there")
    # headers
    hw, hl, hx = D["jb_hdr"]; hy = (by0 + by1) / 2
    for ref, sx in (("H1", -1), ("H2", 1)):
        part = pl["parts"].get(ref)
        hp = [p for p in pads if p["ref"] == ref]
        if not part or not hp:
            row(f"stack {ref}", False, "missing"); continue
        xs = [p["xy"][0] for p in hp]; ys = [p["xy"][1] for p in hp]
        ok = math.dist(part["xy"], (sx * hx, hy)) <= TOL and part["side"] == "B" and len(hp) == 12 and max(xs) - min(xs) < hw and max(ys) - min(ys) < 4.0
        row(f"stack {ref} at the model's x {sx * hx:g}, on the back, pins along x", ok,
            f"at ({part['xy'][0]:.3f}, {part['xy'][1]:.3f}) side {part['side']}; pins span x {max(xs) - min(xs):.2f} (model body {hw:g}), "
            f"rows {max(ys) - min(ys):.2f} apart")
    # every pad 0.25 from the edge; pads of different nets 0.15 apart on the same face
    edge = k_ol.exterior
    de = min(pad_shape(p).distance(edge) if pad_shape(p).within(k_ol) else -1 for p in pads if p["ref"] != "")
    row("every pad at least 0.25 from the board edge", de >= 0.25 - 1e-6, f"nearest {de:.3f}")
    face = lambda p: {"J": "FB", "P": "F", "H": "B"}[p["ref"][0]]
    dmin, worst = 9e9, ""
    for i in range(len(pads)):
        for j in range(i + 1, len(pads)):
            a, b = pads[i], pads[j]
            if a["net"] == b["net"] or not set(face(a)) & set(face(b)):
                continue
            d = pad_shape(a).distance(pad_shape(b))
            if d < dmin:
                dmin, worst = d, f"{a['ref']}.{a['num']} {a['net']} / {b['ref']}.{b['num']} {b['net']}"
    row("pads of different nets at least 0.2 apart", dmin >= 0.2 - 1e-6, f"nearest {dmin:.3f}: {worst}")
    out = [f"Jack board {pl['pcb_version']} vs knob model {pl['cad_version']} (tolerance {TOL} mm)"]
    out += [f"  {s}  {n}: {d}" for s, n, d in rows]
    nf = sum(1 for s, *_ in rows if s == "FAIL")
    out.append(f"{len(rows) - nf}/{len(rows)} PASS")
    txt = "\n".join(out) + "\n"
    open(os.path.join(HERE, "check_cad.txt"), "w").write(txt)
    print(txt)
    return 1 if nf else 0


if __name__ == "__main__":
    sys.exit(main())
