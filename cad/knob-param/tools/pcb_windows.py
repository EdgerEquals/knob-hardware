# Run from cad/knob-param:  PYTHONPATH=. python tools/pcb_windows.py out.json [--keep 22] [--margin 0.5] [--web 6] [--ab-top Y] [--table]
#   (then paste the polygons into electronics pcb_windows; --table prints the keep-out / margin trade-off and writes nothing)
"""PCB see-through windows A, B, C, E (+ D under the clear OLED, notched for the LQFP100), panel frame.

Windows v2 ([Ed] 2 Nov: "these windows can be much bigger"): every window goes out to the REAL limits, each with a margin M
(default 0.5; v0.20 used 1.0 and a 24.1 knob keep-out):
  free = (screen behind) ∩ (board inside the 1.5 rail) − (each obstacle grown by M) − (the A/B web)
Obstacles (panel frame):
  knob        circle r KEEP (default 22.0). Under it: emitter bodies on the board back (VCSEL corners r ~21.3, also cut
              as their own boxes + M), the base_drive cradle's bottom track (r ot_r + ot_rg + ot_track_extra) and the glass.
  posts       the cover's corner-column ring that bears on the board round each notch (r notch_r + tube_press) + M
  encoder     convex hull of the encoder daughterboard, its header and its standoff (their pins land on the main PCB) + M
  bearing 2   the printed seat round H2 + M (inside the knob keep-out at present)
  joystick    the printed cradle's footprint on the PCB (section of the real part at z 0.05: ring + the knob-side ball towers)
              ∪ geom.json cradle_ring outer ∪ geom.json main_pcb_holes (hold-down bores, dowel NPTHs), all + M
  J10         KiCad J10 pad field if it lands on the board (stale v0.11 position, outside the board now)
  clear OLED  D = OLED inset by its 1.6 ledge [Ed v0.19b]; C and E stop M short of the OLED's top edge
  MCU         [Ed 18:34] electronics mcu (LQFP100 + caps, court 17.2 [A]) at the low middle: court + margin is notched out of
              the bottom of D. --no-mcu leaves D whole.
  A/B web     a board strip of width WEB on x = 0 from the knob keep-out up to the joystick cradle, so A (left) and B
              (right) stay two windows and the knob region keeps a direct link to the top of the board [A]."""
import math, json, sys, argparse, os
from shapely.geometry import box, Point, Polygon, MultiPoint
from shapely.ops import unary_union
from shapely import affinity
from knobparam.common import model

ap = argparse.ArgumentParser()
ap.add_argument("out", nargs="?", default="/dev/stdout")
ap.add_argument("--keep", type=float, default=22.0, help="knob keep-out radius (v0.20: 24.06)")
ap.add_argument("--margin", type=float, default=0.5, help="board left round every obstacle (v0.20: 1.0)")
ap.add_argument("--rail", type=float, default=1.5, help="board kept inside the outline")
ap.add_argument("--web", type=float, default=6.0, help="A/B web width on x = 0 [A]")
ap.add_argument("--ab-top", type=float, default=None, help="cap A and B at this y (e.g. 26.06, the joystick grip block's shadow) [A]")
ap.add_argument("--table", action="store_true", help="print the keep-out / margin trade-off table only")
ap.add_argument("--no-mcu", action="store_true", help="leave D whole (ignore electronics mcu, the LQFP100 column)")
a = ap.parse_args()

D = model.derive(model.default_params())
RAIL, LEDGE = a.rail, 1.6   # LEDGE: board strip the clear OLED rests on, all round window D [Ed v0.19b]
x0, x1, y0, y1 = -D["pcb_x1"], D["pcb_x1"], D["pcb_y0"], D["pcb_y1"]
board = box(x0 + RAIL, y0 + RAIL, x1 - RAIL, y1 - RAIL)
lower, upper = box(*[D["amo_lower"][i] for i in (0, 2, 1, 3)]), box(*[D["amo_upper"][i] for i in (0, 2, 1, 3)])
rot = math.radians(D["mech_rot"])

def to_panel(x, y):
    return math.cos(rot) * x - math.sin(rot) * y, math.sin(rot) * x + math.cos(rot) * y

# ---- hard bodies (no margin yet): (name, polygon) ----
HARD = []
for h in D["em_holes"]:   # emitter bodies on the board back (mechanism frame, turned into the panel frame)
    bx, by, _ = D["em_vcsel"] if h["kind"] == "VCSEL" else D["em_rgb"]
    r = affinity.rotate(box(-bx / 2, -by / 2, bx / 2, by / 2), h["ang"] + D["mech_rot"], origin=(0, 0))
    HARD.append(("emitter", affinity.translate(r, *to_panel(h["x"], h["y"]))))
r_em = max(math.hypot(*c) for n, g in HARD for c in g.exterior.coords)
r_track = D["ot_r"] + D["ot_rg"] + D["ot_track_extra"]   # base_drive cradle bottom track on the PCB front
HARD.append(("cradle track", Point(0, 0).buffer(max(r_track, D["knob_od"] / 2), 256)))
for x, y in D["corners"]:   # cover corner column: ring bearing on the board round the notch
    HARD.append(("corner post", Point(x, y).buffer(D["notch_r"] + D.get("tube_press", 1.0), 128)))
for p in D["pcb_kicad"].get("back_parts", []):
    if p["ref"] == "J10" and math.hypot(p["x"], p["y"]) > 23:
        HARD.append(("J10", box(p["x"] - p["w"] / 2, p["y"] - p["l"] / 2, p["x"] + p["w"] / 2, p["y"] + p["l"] / 2)))
pex, pey = to_panel(*D["enc_xy"])
HARD.append(("bearing 2 seat", Point(pex, pey).buffer(D["brg"]["D"] / 2 + D["brg2_seat_wall"], 128)))
from knobparam.under_pcb.parts import encoder   # encoder daughterboard + header + standoff (pins land on the main PCB)
from build123d import Rot
_ps = encoder.build(model.view(D, "under_pcb"))
for _n in ("encoder header", "encoder daughterboard", "encoder standoff"):
    if _n in _ps:
        _s = Rot(0, 0, D["mech_rot"]) * _ps[_n]
        HARD.append((_n, MultiPoint([(v.X, v.Y) for v in _s.vertices()]).convex_hull))
# joystick: cradle footprint on the PCB (real part, cut at z 0.05) + geom.json ring and main-PCB holes
from knobparam.assembly import joystick as _js
sys.path.insert(0, _js._jsdir())
from jsparam import params as _jp, parts as _jparts
from knobparam.assembly.plan_sheet import _cut_faces
JD = _jp.derive(_jp.P); py = JD["place_y"]
tris = _cut_faces(_jparts.cradle(JD), "z", 0.05)
cr = unary_union([Polygon(t).buffer(1e-4) for t in tris if Polygon(t).area > 1e-9])
HARD.append(("joystick cradle", affinity.translate(cr, 0, py)))
G = json.load(open(os.path.join("knobparam", "electronics", "kicad", "joystick-daughterboard", "geom.json")))
ox_, oy0_, oy1_ = G["cradle_ring"]["outer"]
HARD.append(("joystick cradle ring (geom.json)", box(-ox_, py + oy0_, ox_, py + oy1_)))
for h in G["main_pcb_holes"]:
    HARD.append((h["what"], Point(h["x"], h["y"]).buffer(h["d"] / 2, 64)))
ow, oh, _ = D["clear_oled"]; ox, oy = D["clear_oled_xy"]
oled = box(ox - ow / 2, oy - oh / 2, ox + ow / 2, oy + oh / 2)


def windows(keep, M, web, ab_top=None):
    blk = unary_union([g.buffer(M, 64) for _, g in HARD] + [Point(0, 0).buffer(keep, 256)])
    ytop = (py + oy0_) + M   # the web runs from the knob up into the cradle ring
    blk = blk.union(box(-web / 2, 0, web / 2, ytop)) if web > 0 else blk
    if ab_top is not None:   # option: A and B stop at a fixed height (board above it kept)
        blk = blk.union(box(-50, ab_top, 50, 80))
    Z = {}
    Z["A"] = (upper & board).difference(blk) & box(-50, 0, 0, 80)
    Z["B"] = (upper & board).difference(blk) & box(0, 0, 50, 80)
    y_ce = oy + oh / 2 + M   # C and E stop M short of the clear OLED's top edge (v0.20: 1.6)
    Z["E"] = (lower & board).difference(blk) & box(-50, y_ce, 0, 0)
    Z["C"] = (lower & board).difference(blk) & box(0, y_ce, 50, 0)
    Z["D"] = (oled.buffer(-LEDGE, join_style=2) & board & lower).difference(blk)
    if D.get("mcu") and not a.no_mcu:   # [Ed 18:34] LQFP100 at the low middle: its courtyard + margin notched out of D
        (mx, my), hc = D["mcu"]["xy"], D["mcu"]["court"] / 2 + D["mcu"]["margin"]
        Z["D"] = Z["D"].difference(box(mx - hc, my - hc, mx + hc, my + hc))
    out, area = {}, {}
    for k in sorted(Z):
        g = Z[k]
        gs = [g] if g.geom_type == "Polygon" else [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon"]
        gs = [p for p in gs if p.area > 4.0]
        if not gs:
            continue
        p = max(gs, key=lambda q: q.area)
        # open slightly: drop slivers narrower than 2 mm and round the inside corners to r 1 (routable), then simplify
        q = p.buffer(-1.0, join_style=1).buffer(1.0, join_style=1).simplify(0.05)
        if q.is_empty or q.area < 4.0:
            continue
        if q.geom_type != "Polygon":
            q = max(q.geoms, key=lambda r: r.area)
        out[k] = q; area[k] = q.area
    return out, area


if a.table:
    print(f"hard limits: emitter bodies r {r_em:.2f}, cradle track r {r_track:.2f}, glass r {D['knob_od'] / 2:.2f}; web {a.web:g}, A/B top {a.ab_top}")
    print("keep  M    " + "  ".join(f"{k:>6s}" for k in "ABCE") + "  D(all)   A+B+C+E     all")
    for keep, M in ((24.06, 1.0), (23.0, 1.0), (22.5, 0.5), (22.0, 1.0), (22.0, 0.75), (22.0, 0.5), (21.8, 0.5), (21.8, 0.3)):
        _, ar = windows(keep, M, a.web, a.ab_top)
        s = sum(ar.get(k, 0) for k in "ABCE"); sd = sum(v for k, v in ar.items() if k.startswith("D"))
        print(f"{keep:5.2f} {M:4.2f} " + "  ".join(f"{ar.get(k, 0):6.1f}" for k in "ABCE") + f"  {sd:6.1f}   {s:7.1f} {s + sd:7.1f}")
    sys.exit(0)

print("pcb", x0, x1, y0, y1, "corners", D["corners"], "notch_r", D["notch_r"])
print(f"keep-out r {a.keep:g} (emitter bodies r {r_em:.2f}, cradle track r {r_track:.2f}), margin {a.margin:g}, rail {RAIL:g}, A/B web {a.web:g}")
W, _ = windows(a.keep, a.margin, a.web, a.ab_top)
out = {}
for k, q in W.items():
    pts = [(round(x, 2), round(y, 2)) for x, y in q.exterior.coords[:-1]]
    mnx, mny, mxx, mxy = q.bounds
    print(f"{k}: area {q.area:.1f} mm²  x {mnx:.1f}..{mxx:.1f}  y {mny:.1f}..{mxy:.1f}  ({len(pts)} pts)")
    out[k] = pts
json.dump(out, open(a.out, "w"))
