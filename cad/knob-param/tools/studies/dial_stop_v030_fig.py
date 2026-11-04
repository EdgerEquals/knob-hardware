# v0.30 [Ed 4 Nov 15:46] dial item 6, option A in the model: the hard stop in the Hall slot, anchor post 2 on the detent block.
#   dial-stop-v030.png  1: 3D from above and outside (cradle, detent block with its arm and post 2, springs, lever; the dial's lower
#                       part see-through); 2: plan at z 2.6 through the plate: the Hall bar at rest and at ±travel, the two stop faces
#                       (green); 3: plan at z 8.0: the anchor posts, springs and the block's arm (post 2 hangs from it). Mechanism frame.
# Run from cad/knob-param:  PYTHONPATH=. xvfb-run -a python tools/studies/dial_stop_v030_fig.py <out dir>
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
    from matplotlib.patches import Polygon
    from PIL import Image, ImageDraw
    from build123d import Box, Pos, Align
    from knobparam.common import model
    from knobparam.assembly.build import build_all
    from knobparam.assembly.plan_sheet import _cut_faces
    from knobparam.assembly.colours import colour
    D = model.derive(model.default_params())
    parts, *_ = build_all(D)
    cr = parts["base cradle"]
    dl = [s for n, s in parts.items() if n.startswith("control dial lower part")][0]
    blk = [s for n, s in parts.items() if n.startswith("detent block (")][0]
    keep = {n: s for n, s in parts.items() if n.startswith(("centring spring", "spring anchor pin", "detent 1 ball", "detent train pedestal",
                                                             "detent block locating pin"))}
    T = D["travel_deg"]; h = D["dt_hang"]
    pol = lambda r, a: (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
    outs = []
    # ---- 1: 3D ----
    reg = Pos(-18, -18, 0.0) * Box(26, 21, 14.0, align=(Align.MIN, Align.MIN, Align.MIN))
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
    add(cr, "#c9cfd4"); add(blk, "#f2c14e")
    add(dl, "#7c8a96", 0.35, False)
    for n, s in keep.items():
        add(s, "#8d6e63" if "spring" in n else colour(n))
    sm = D["hs_stop_polys"]
    lab = [((h["post_xy"][0], h["post_xy"][1], h["z1"]), "post 2 on the block's arm"),
           ((*pol(D["ad_r"], D["ad_ang"]), D["det_z1"]), "detent block"),
           ((*pol(D["sl_r"] - 0.6, D["sl_ang"]), D["sl_top"]), "lever (springs only)")]
    for s, j, r0, r1, poly in sm:
        x, y = (poly[0][0] + poly[1][0]) / 2, (poly[0][1] + poly[1][1]) / 2
        lab.append(((x, y, D["plate_t"]), f"stop face {'-' if s < 0 else '+'}"))
    labels(pl, lab)
    c = np.array([-4.0, -9.0, 5.0])
    pl.camera.position = tuple(c + np.array([14.0, -34.0, 42.0])); pl.camera.focal_point = tuple(c); pl.camera.up = (0, 0, 1)
    pl.add_text("1. From above and outside: cradle grey, detent block yellow, dial's lower part see-through", position="upper_left",
                font_size=9, color="black")
    f = os.path.join(OUT, "_st_1.png"); pl.screenshot(f); pl.close(); outs.append(f)

    # ---- 2: plan through the plate ----
    fig = plt.figure(figsize=(7.6, 7.6), dpi=125); ax = fig.add_axes([0.11, 0.09, 0.86, 0.84])
    zp = 2.6
    ax.add_collection(PolyCollection(_cut_faces(cr, "z", zp), facecolors="#c9cfd4", edgecolors="none"))
    t = _cut_faces(dl, "z", zp)
    ax.add_collection(PolyCollection(t, facecolors="#1565c0", edgecolors="none", alpha=0.8))
    for sg in (-1, 1):
        ca, sa = math.cos(math.radians(sg * T)), math.sin(math.radians(sg * T))
        ax.add_collection(PolyCollection([[(x * ca - y * sa, x * sa + y * ca) for x, y in p] for p in t], facecolors="#1565c0",
                                         edgecolors="none", alpha=0.15))
    for s, j, r0, r1, poly in sm:
        ax.add_patch(Polygon(poly, closed=True, fc="#2e7d32", ec="none"))
    k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    for s, j, r0, r1, poly in sm:
        x, y = (poly[0][0] + poly[1][0]) / 2, (poly[0][1] + poly[1][1]) / 2
        ax.annotate(f"stop face {'-' if s < 0 else '+'}: the bar's link (pads {j + 1}-{j + 2})\nmeets it flush at {s * T:+.2f}°",
                    (x, y), (-19.5, -17.5) if s < 0 else (-7.0, -19.2), **k)
    ax.annotate("Hall bar at rest (pale: at ±travel)", pol(12.0, D["hv_phi_m"][2]), (-19.5, 1.5), **k)
    ax.set_xlim(-20, 3); ax.set_ylim(-20, 3); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("x (mm, mechanism frame)"); ax.set_ylabel("y (mm)")
    ax.set_title(f"2. Plan at z {zp:g} through the cradle plate (stop faces green)", fontsize=10, loc="left")
    f = os.path.join(OUT, "_st_2.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    # ---- 3: plan at the posts / springs ----
    fig = plt.figure(figsize=(7.6, 7.6), dpi=125); ax = fig.add_axes([0.11, 0.09, 0.86, 0.84])
    zq = 8.0
    for n, s, col in [("cr", cr, "#c9cfd4"), ("blk", blk, "#f2c14e"), ("dl", dl, "#7c8a96")] + [(n, s, None) for n, s in keep.items()]:
        b = s.bounding_box()
        if b.min.Z > zq or b.max.Z < zq:
            continue
        tt = _cut_faces(s, "z", zq)
        if tt:
            ax.add_collection(PolyCollection(tt, facecolors=col or ("#8d6e63" if "spring" in n else colour(n)), edgecolors="none",
                                             alpha=0.5 if n == "dl" else 1.0))
    # the arm above (outline, z h["z0"]-h["z1"])
    ta = _cut_faces(blk, "z", (h["z0"] + h["z1"]) / 2)
    ax.add_collection(PolyCollection(ta, facecolors="none", edgecolors="#b07d00", linewidths=0.4, linestyles="--"))
    ax.annotate(f"post 2 + pin, hanging from the block's arm\n(dashed, z {h['z0']:.1f}-{h['z1']:.1f}, over the springs)", h["post_xy"], (-19.5, -1.2), **k)
    ax.annotate("post 1 + pin, on the cradle", D["sl_anchor_xy"][0], (1.0, -1.2), **k)
    ax.annotate("detent block (glued on its seat)", pol(D["ad_r"], D["ad_ang"]), (-19.5, -18.5), **k)
    ax.set_xlim(-20, 9); ax.set_ylim(-20, 3); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("x (mm, mechanism frame)"); ax.set_ylabel("y (mm)")
    ax.set_title(f"3. Plan at z {zq:g}: springs and posts (the block's arm dashed above)", fontsize=10, loc="left")
    f = os.path.join(OUT, "_st_3.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    ims = [Image.open(f) for f in outs]
    H = max(i.height for i in ims); ims = [i.resize((int(i.width * H / i.height), H)) for i in ims]
    cv = Image.new("RGB", (sum(i.width for i in ims), H + 50), "white"); x = 0
    for i in ims:
        cv.paste(i, (x, 50)); x += i.width
    ImageDraw.Draw(cv).text((20, 15), f"Knob {D['version']} ([Ed 4 Nov 15:46], dial item 6, option A): the hard stop is two faces in the Hall slot "
                            "(the r 7 stop blocks are gone); anchor post 2 and its pin hang from the detent block; the lever and the two "
                            "extension springs stay.", fill="black")
    out = os.path.join(OUT, "dial-stop-v030.png"); cv.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out)


if __name__ == "__main__":
    main()
