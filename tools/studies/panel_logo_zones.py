"""Faceplate logo zones (8 Nov 2026, Ed 16:48: a logo impression in the panel; a brief and a file for the designer).
Reads the case's polished front face (one face at z_fp1, with its openings) from the model and lays out where an impression can go:
the face less a margin round every opening and edge, the rail washers, the jack nuts, the knob's O-ring, the joystick block's lip and
the clear OLED that shows through the panel. Writes a 1:1 template (SVG and DXF, mm), an A4 PDF at 1:1, a PNG, and a JSON of the zones.

  1. from cad/knob-param: tools/studies/panel_face_dump.py (model -> case.brep), then tools/studies/panel_face_extract.py (-> front.json:
     the face's outer wire and openings as polylines, panel frame mm)
  2. python3 tools/studies/panel_logo_zones.py <front.json> <out dir>
Panel frame: x across (+x = right seen from the front), y up, origin on the knob axis. Needs shapely, ezdxf, matplotlib."""
import json, math, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
import ezdxf

front_json, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
F = json.load(open(front_json))[0]
face = Polygon(F["outer"], [h for h in F["inner"]])
outer = Polygon(F["outer"])
holes = [Polygon(h) for h in F["inner"]]

# ---- what each opening is (by its size and place; model v0.52) ----
def kind(h):
    x0, y0, x1, y1 = h.bounds; w, ht = x1 - x0, y1 - y0; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if w > 40 and ht > 40: return "knob", (cx, cy)
    if w > 40: return "joystick", (cx, cy)
    if abs(w - 6.6) < 0.2: return "jack", (cx, cy)
    if w > 8: return "usb", (cx, cy)
    return "rail", (cx, cy)
OPEN = [(kind(h)[0], kind(h)[1], h) for h in holes]

# ---- keep-outs [A unless marked] ----
EDGE = 1.5                     # from the panel's outside edge
RAIL_R = 3.0 + 0.5             # [S case params] Ø6 nylon washer under each rail screw, + 0.5
NUT_R = 4.0 + 0.75             # [S model] jack nut 8 across (PJ366ST), + 0.75 so a plug's fingers and the nut never sit on the logo
KNOB_R = 22.0 + 1.0            # [S model] the knob's drip O-ring is Ø44 just over the face, + 1.0
JOY_LIP = 0.9 + 1.0            # [S case params] the joystick block's lip covers 0.9 of the face round its opening, + 1.0
USB_M = 1.0
OLED = box(-42.04 / 2, -35.19 - 27.22 / 2, 42.04 / 2, -35.19 + 27.22 / 2)   # [S electronics params] the clear OLED, seen through the panel
PWR = (0.6, 25.6); PWR_R = 3.0  # [S electronics params, Q36] the power light's frosted dot on the case's inside face, about Ø6 [A]
ko = []
for k, (cx, cy), h in OPEN:
    if k == "rail": ko.append(Point(cx, cy).buffer(RAIL_R, 64))
    elif k == "jack": ko.append(Point(cx, cy).buffer(NUT_R, 64))
    elif k == "knob": ko.append(Point(cx, cy).buffer(KNOB_R, 128))
    elif k == "joystick": ko.append(h.buffer(JOY_LIP, join_style=1))
    elif k == "usb": ko.append(h.buffer(USB_M, join_style=2))
KO = unary_union(ko)
usable = outer.buffer(-EDGE, join_style=2).difference(KO).difference(OLED)
NECK = 1.5   # [A] drop necks and slivers narrower than 3 mm (no logo fits there; it also splits the face into separate zones)
usable = usable.buffer(-NECK, join_style=2).buffer(NECK, join_style=2).intersection(usable)
power_dot = Point(*PWR).buffer(PWR_R, 64)

# ---- named zones: connected pieces, the larger ones ----
pieces = [g for g in getattr(usable, "geoms", [usable]) if g.area > 15]


def biggest_rect(poly, g=0.05):
    """Largest axis-aligned rectangle inside poly (raster, histogram method)."""
    x0, y0, x1, y1 = poly.bounds
    xs = np.arange(x0, x1, g) + g / 2; ys = np.arange(y0, y1, g) + g / 2
    from matplotlib.path import Path
    rings = [np.array(poly.exterior.coords)] + [np.array(r.coords) for r in poly.interiors]
    XX, YY = np.meshgrid(xs, ys); P = np.c_[XX.ravel(), YY.ravel()]
    inside = Path(rings[0]).contains_points(P)
    for r in rings[1:]:
        inside &= ~Path(r).contains_points(P)
    M = inside.reshape(len(ys), len(xs))
    hgt = np.zeros(len(xs), int); best = (0, None)
    for j in range(len(ys)):
        hgt = np.where(M[j], hgt + 1, 0)
        st = []
        for i in range(len(xs) + 1):
            hh = hgt[i] if i < len(xs) else 0
            s = i
            while st and st[-1][1] >= hh:
                s, h0 = st.pop()
                a = h0 * (i - s)
                if a > best[0]:
                    best = (a, (xs[s] - g / 2, ys[j - h0 + 1] - g / 2, xs[i - 1] + g / 2, ys[j] + g / 2))
            st.append((s, hh))
    return best[1]


def name(p):
    cx, cy = p.centroid.x, p.centroid.y
    if cy > 54: return "top, between the rail screws"
    if cy > 0 and abs(cx) < 3: return "crescent, knob to joystick"
    if cy > 0: return "beside the knob, upper " + ("left" if cx < 0 else "right")
    if cy > -50: return "beside the knob, lower " + ("left" if cx < 0 else "right")
    return "bottom, below the USB-C"


zones = []
for p in sorted(pieces, key=lambda q: -q.centroid.y):
    r = biggest_rect(p)
    if min(r[2] - r[0], r[3] - r[1]) < 2.5:
        continue
    zones.append(dict(name=name(p), area=round(p.area, 1), rect=[round(v, 2) for v in r], w=round(r[2] - r[0], 1), h=round(r[3] - r[1], 1),
                      poly=[(round(x, 3), round(y, 3)) for x, y in p.exterior.coords],
                      holes=[[(round(x, 3), round(y, 3)) for x, y in i.coords] for i in p.interiors]))
json.dump(dict(frame="panel, mm, origin on the knob axis, y up; panel 50.50 x 128.50", zones=zones,
               margins=dict(edge=EDGE, rail_r=RAIL_R, nut_r=NUT_R, knob_r=KNOB_R, joy_lip=JOY_LIP, usb=USB_M)),
          open(os.path.join(OUT, "panel-logo-zones.json"), "w"), indent=1)
for z in zones:
    print(f"{z['name']:32s} area {z['area']:6.1f} mm²   biggest rectangle {z['w']} x {z['h']} mm")

# ---- DXF (1:1 mm, layers) ----
doc = ezdxf.new("R2010", setup=True); doc.units = ezdxf.units.MM; msp = doc.modelspace()
for ln, col in (("PANEL_OUTLINE", 7), ("OPENINGS", 7), ("KEEPOUT", 1), ("SEEN_THROUGH", 5), ("LOGO_ZONES", 3), ("LOGO_RECTS", 3), ("POWER_LIGHT", 6)):
    doc.layers.add(ln, color=col)


def pl(coords, layer):
    msp.add_lwpolyline([(x, y) for x, y in coords], close=True, dxfattribs={"layer": layer})


pl(list(outer.exterior.coords)[:-1], "PANEL_OUTLINE")
for h in holes: pl(list(h.exterior.coords)[:-1], "OPENINGS")
for g in getattr(KO, "geoms", [KO]): pl(list(g.exterior.coords)[:-1], "KEEPOUT")
pl(list(OLED.exterior.coords)[:-1], "SEEN_THROUGH")
pl(list(power_dot.exterior.coords)[:-1], "POWER_LIGHT")
for z in zones:
    pl(z["poly"][:-1], "LOGO_ZONES")
    for i in z["holes"]:
        pl(i[:-1], "LOGO_ZONES")
    x0, y0, x1, y1 = z["rect"]; pl([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "LOGO_RECTS")
doc.saveas(os.path.join(OUT, "panel-logo-template.dxf"))

# ---- SVG (1:1 mm; y flipped for SVG) ----
X0, X1, Y0, Y1 = -25.25, 25.25, -66.4, 62.1


def sp(coords):
    return " ".join(f"{x - X0:.3f},{Y1 - y:.3f}" for x, y in coords)


svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{X1 - X0:.2f}mm" height="{Y1 - Y0:.2f}mm" viewBox="0 0 {X1 - X0:.2f} {Y1 - Y0:.2f}">',
       '<!-- Knob module faceplate, front view, 1:1 in mm. Layers as groups: outline, openings, keep-outs, seen through, logo zones. -->',
       '<g id="logo_zones" fill="#c8e6c9" stroke="#2e7d32" stroke-width="0.1">']
svg += [f'<polygon points="{sp(z["poly"])}"/>' for z in zones]
svg += ['</g><g id="logo_rects" fill="none" stroke="#2e7d32" stroke-width="0.12" stroke-dasharray="0.6,0.4">']
svg += [f'<rect x="{z["rect"][0] - X0:.3f}" y="{Y1 - z["rect"][3]:.3f}" width="{z["w"]}" height="{z["h"]}"/>' for z in zones]
svg += ['</g><g id="seen_through" fill="none" stroke="#1565c0" stroke-width="0.12" stroke-dasharray="0.3,0.3">',
        f'<polygon points="{sp(OLED.exterior.coords)}"/>', f'<polygon points="{sp(power_dot.exterior.coords)}"/>',
        '</g><g id="keepouts" fill="none" stroke="#c62828" stroke-width="0.1" stroke-dasharray="0.5,0.3">']
svg += [f'<polygon points="{sp(g.exterior.coords)}"/>' for g in getattr(KO, "geoms", [KO])]
svg += ['</g><g id="openings" fill="#ffffff" stroke="#000000" stroke-width="0.15">']
svg += [f'<polygon points="{sp(h.exterior.coords)}"/>' for h in holes]
svg += ['</g><g id="outline" fill="none" stroke="#000000" stroke-width="0.2">', f'<polygon points="{sp(outer.exterior.coords)}"/>', '</g></svg>']
open(os.path.join(OUT, "panel-logo-template.svg"), "w").write("\n".join(svg))


# ---- picture (PNG) and A4 PDF at 1:1 ----
def draw(ax, labels=True):
    ax.add_patch(plt.Polygon(np.array(outer.exterior.coords), fc="#eef3f5", ec="k", lw=0.8))
    for z in zones:
        ax.add_patch(plt.Polygon(np.array(z["poly"]), fc="#c8e6c9", ec="#2e7d32", lw=0.6))
    ax.add_patch(plt.Polygon(np.array(OLED.exterior.coords), fc="none", ec="#1565c0", lw=0.6, ls=":"))
    for g in getattr(KO, "geoms", [KO]):
        ax.add_patch(plt.Polygon(np.array(g.exterior.coords), fc="#ffebee", ec="#c62828", lw=0.5, ls="--"))
    for h in holes:
        ax.add_patch(plt.Polygon(np.array(h.exterior.coords), fc="white", ec="k", lw=0.6))
    ax.add_patch(plt.Polygon(np.array(power_dot.exterior.coords), fc="none", ec="#6a1b9a", lw=0.6, ls=":"))
    for k_, z in enumerate(zones):
        x0, y0, x1, y1 = z["rect"]
        ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fc="none", ec="#1b5e20", lw=0.8, ls="--"))
        if labels:
            ax.text((x0 + x1) / 2, (y0 + y1) / 2, f"{k_ + 1}\n{z['w']} x {z['h']}", ha="center", va="center", fontsize=6.5,
                    weight="bold", color="#1b5e20")
    if labels:
        ax.text(0, 0, "knob\n(stands 18 mm\nproud)", ha="center", va="center", fontsize=7, color="#555")
        ax.text(0, 40.6, "joystick", ha="center", va="center", fontsize=7, color="#555")
        ax.text(0, -30.5, "clear screen behind\nthe panel (keep clear)", ha="center", va="center", fontsize=6.5, color="#1565c0")
        ax.text(PWR[0] + 3.6, PWR[1] + 0.2, "power light", fontsize=5.5, color="#6a1b9a", va="center")
    ax.set_xlim(X0 - 1, X1 + 1); ax.set_ylim(Y0 - 1, Y1 + 1); ax.set_aspect("equal"); ax.axis("off")


fig = plt.figure(figsize=(12, 13.6), dpi=130)
ax = fig.add_axes([0.0, 0.02, 0.5, 0.9]); draw(ax)
fig.text(0.02, 0.97, "Faceplate: where a logo impression can go", fontsize=15, weight="bold", va="top")
fig.text(0.02, 0.945, "Polished front face of the clear resin panel, seen from the front, mm. Green: room for an impression; dashed "
         "green: the biggest rectangle in each.", fontsize=9.5, va="top")
tx = fig.add_axes([0.52, 0.05, 0.47, 0.86]); tx.axis("off")
lines = [("Zones (biggest rectangle, w x h mm)", True)] + [(f"{k + 1}. {z['name']}: {z['w']} x {z['h']}"
                                                          + (" (each upper corner)" if "crescent" in z["name"] else ""), False)
                                                         for k, z in enumerate(zones)] + [
    ("", False), ("Kept clear (red dashed)", True),
    (f"{EDGE} from the panel's edge", False), ("Ø6 washer round each rail screw, + 0.5", False),
    ("the jack nuts (8 across), + 0.75", False), ("the knob's O-ring (Ø44), + 1.0", False),
    ("the joystick block's lip (0.9 over the face), + 1.0", False), ("the USB-C opening, + 1.0", False),
    ("", False), ("Seen through the panel (blue dotted)", True),
    ("the clear screen under the knob: no logo over it", False),
    ("the power light's frosted dot (purple): keep it clear,", False), ("or make it part of the logo", False),
    ("", False), ("Impression (SLA clear resin)", True),
    ("lines and gaps at least 0.8 mm; depth 0.5-0.8 mm", False), ("(the panel is 2.5 mm thick)", False)]
y = 0.98
for t, b in lines:
    tx.text(0, y, t, fontsize=10.5 if b else 9.5, weight="bold" if b else None, va="top", transform=tx.transAxes); y -= 0.034
fig.savefig(os.path.join(OUT, "panel-logo-zones.png"))
with PdfPages(os.path.join(OUT, "panel-logo-template-1to1.pdf")) as pdf:   # A4 portrait, the panel at true size
    f2 = plt.figure(figsize=(8.27, 11.69))
    W, H = (X1 - X0 + 2) / 25.4 / 8.27, (Y1 - Y0 + 2) / 25.4 / 11.69
    a2 = f2.add_axes([0.5 - W / 2, 0.5 - H / 2, W, H]); draw(a2, labels=False)
    f2.text(0.5, 0.97, "Knob module faceplate, front, 1:1 (print at 100 %, no scaling). Panel 50.50 x 128.50 mm.", ha="center", fontsize=9)
    f2.text(0.5, 0.02, "Green: logo zones. Red dashed: keep clear. Blue dotted: the clear screen behind. Purple: the power light's dot.",
            ha="center", fontsize=8)
    pdf.savefig(f2)
