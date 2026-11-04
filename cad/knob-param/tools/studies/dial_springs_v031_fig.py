# v0.31 [Ed 4 Nov 16:35] dial item 6 in the model: the centring springs lifted onto a column on the Hall arm, two posts from the
# cradle plate, the hard stop in the Hall slot (v0.30).
#   dial-springs-v031.png  1: 3D from above (cradle + posts grey, detent block yellow, the dial's lower part blue with its column,
#                          springs brown); 2: plan at the springs' height, the dial at rest and at ±travel; 3: plan at z 2.6 through
#                          the plate: the Hall bar and the two stop faces (green). Mechanism frame.
# Run from cad/knob-param:  PYTHONPATH=. xvfb-run -a python tools/studies/dial_springs_v031_fig.py <out dir>
import os, sys, math
sys.path.insert(0, ".")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from js_v025_fig import to_pv, labels

OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def main():
    import pyvista as pv
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Polygon, Circle
    from PIL import Image, ImageDraw
    from build123d import Box, Pos, Rot, Align
    from knobparam.common import model
    from knobparam.assembly.build import build_all
    from knobparam.assembly.plan_sheet import _cut_faces
    from knobparam.base_drive.parts.mech import es_springs_at, es_pins
    D = model.derive(model.default_params())
    Db = model.view(D, "base_drive")
    parts, *_ = build_all(D)
    cr = parts["base cradle"]
    dl = [s for n, s in parts.items() if n.startswith("control dial lower part")][0]
    blk = [s for n, s in parts.items() if n.startswith("detent block (")][0]
    springs = [s for n, s in parts.items() if n.startswith("centring spring")]
    pins = [s for n, s in parts.items() if n.startswith(("spring anchor pin", "spring pin on"))]
    T = D["travel_deg"]; zs = D["es_z"]
    pol = lambda r, a: (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
    outs = []
    # ---- 1: 3D ----
    reg = Pos(-15, -15, 0.0) * Box(27, 23, 13.0, align=(Align.MIN, Align.MIN, Align.MIN))
    pl = pv.Plotter(off_screen=True, window_size=(1100, 1000)); pl.set_background("white")
    def add(s, c, op=1.0, edges=True):
        try:
            q = s & reg
        except Exception:
            return
        m = to_pv(q)
        if m is None:
            return
        pl.add_mesh(m, color=c, opacity=op, smooth_shading=False, specular=0.15)
        if edges and op > 0.9:
            pl.add_mesh(m.extract_feature_edges(40), color="#37474f", line_width=0.8)
    add(cr, "#c9cfd4"); add(blk, "#f2c14e", 0.9, False); add(dl, "#5c8fd6", 0.75, False)
    for s in springs:
        add(s, "#8d6e63")
    for s in pins:
        add(s, "#455a64")
    P, Qs = es_pins(Db, 0.0)
    lab = [((P[0], P[1], zs + 1.0), "column on the Hall arm (pin)"), ((*Qs[0], zs + 1.0), "post 1"), ((*Qs[1], zs + 1.0), "post 2"),
           ((*pol(D["ad_r"], D["ad_ang"]), D["det_z1"]), "detent block")]
    labels(pl, lab)
    c = np.array([-1.0, -3.0, 5.0])
    pl.camera.position = tuple(c + np.array([10.0, -32.0, 38.0])); pl.camera.focal_point = tuple(c); pl.camera.up = (0, 0, 1)
    pl.add_text("1. From above: cradle + posts grey, detent block yellow, dial's lower part blue, springs brown", position="upper_left",
                font_size=9, color="black")
    f = os.path.join(OUT, "_sp_1.png"); pl.screenshot(f); pl.close(); outs.append(f)
    k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    # ---- 2: plan at the springs ----
    fig = plt.figure(figsize=(7.6, 7.6), dpi=125); ax = fig.add_axes([0.11, 0.09, 0.86, 0.84])
    zc = zs - 0.3
    for s, col, al in ((cr, "#c9cfd4", 1), (blk, "#f2c14e", 1)):
        t = _cut_faces(s, "z", zc)
        if t: ax.add_collection(PolyCollection(t, facecolors=col, edgecolors="none", alpha=al))
    for th, al in ((-T, 0.15), (0.0, 0.7), (T, 0.15)):
        t = _cut_faces(Rot(0, 0, th) * dl, "z", zc)
        if t: ax.add_collection(PolyCollection(t, facecolors="#1565c0", edgecolors="none", alpha=al))
        P_, Qs_ = es_pins(Db, th)
        for Q in Qs_:
            ax.plot([P_[0], Q[0]], [P_[1], Q[1]], color="#8d6e63", lw=3.0 if th == 0 else 1.0, alpha=1 if th == 0 else 0.5)
    for Q in Qs:
        ax.add_patch(Circle(Q, D["es_pin_d"] / 2, fc="#455a64"))
    for sp in D["es_springs"]:
        q = sp["Q"]
        ax.annotate(f"post {sp['k']} Ø{sp['post_d']:g}: spring {sp['L']:.1f} pin to pin,\nfree {sp['L_free']:.2f}, "
                    f"{sp['F_min']:.2f}-{sp['F_max']:.2f} N", q, (q[0] - 9.5 if sp["k"] == 1 else q[0] - 2.0, q[1] + 2.0 if sp["k"] == 1 else q[1] - 4.5), **k)
    ax.annotate(f"column on the Hall arm's rib, pin at r {D['es_rp']:g}\n(pale: the dial at ±{T:.1f}°)", P, (-14.0, -12.5), **k)
    ax.set_xlim(-15, 12); ax.set_ylim(-16, 8); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("x (mm, mechanism frame)"); ax.set_ylabel("y (mm)")
    ax.set_title(f"2. Plan at z {zc:g}: the springs (axis z {zs:g}), dial at rest and ±travel", fontsize=10, loc="left")
    f = os.path.join(OUT, "_sp_2.png"); fig.savefig(f); plt.close(fig); outs.append(f)
    # ---- 3: plan through the plate: stop faces ----
    fig = plt.figure(figsize=(7.6, 7.6), dpi=125); ax = fig.add_axes([0.11, 0.09, 0.86, 0.84])
    zp = 2.6
    ax.add_collection(PolyCollection(_cut_faces(cr, "z", zp), facecolors="#c9cfd4", edgecolors="none"))
    t = _cut_faces(dl, "z", zp)
    ax.add_collection(PolyCollection(t, facecolors="#1565c0", edgecolors="none", alpha=0.8))
    for sg in (-1, 1):
        ca, sa = math.cos(math.radians(sg * T)), math.sin(math.radians(sg * T))
        ax.add_collection(PolyCollection([[(x * ca - y * sa, x * sa + y * ca) for x, y in p] for p in t], facecolors="#1565c0",
                                         edgecolors="none", alpha=0.15))
    for s, j, r0, r1, poly in D["hs_stop_polys"]:
        ax.add_patch(Polygon(poly, closed=True, fc="#2e7d32", ec="none"))
        x, y = (poly[0][0] + poly[1][0]) / 2, (poly[0][1] + poly[1][1]) / 2
        ax.annotate(f"stop face {'-' if s < 0 else '+'}: met flush at {s * T:+.2f}°", (x, y), (-19.5, -17.5) if s < 0 else (-7.0, -19.2), **k)
    ax.set_xlim(-20, 3); ax.set_ylim(-20, 3); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("x (mm, mechanism frame)"); ax.set_ylabel("y (mm)")
    ax.set_title(f"3. Plan at z {zp:g} through the plate: the Hall bar and the stop faces (green)", fontsize=10, loc="left")
    f = os.path.join(OUT, "_sp_3.png"); fig.savefig(f); plt.close(fig); outs.append(f)
    ims = [Image.open(f) for f in outs]
    H = max(i.height for i in ims); ims = [i.resize((int(i.width * H / i.height), H)) for i in ims]
    cv = Image.new("RGB", (sum(i.width for i in ims), H + 50), "white"); x = 0
    for i in ims:
        cv.paste(i, (x, 50)); x += i.width
    ImageDraw.Draw(cv).text((20, 15), f"Knob {D['version']} ([Ed 4 Nov 16:35], dial item 6): two extension springs at z {zs:g} from a pin on a column "
                            "on the Hall arm (no lever) to two posts printed up from the cradle plate; the hard stop is two faces in the Hall slot.",
                            fill="black")
    out = os.path.join(OUT, "dial-springs-v031.png"); cv.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out)


if __name__ == "__main__":
    main()
