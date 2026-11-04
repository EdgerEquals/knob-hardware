# Dial item 6 for Danny (4 Nov): the centring-spring anchor post 2 and the lever's hard-stop block 2 float in the base cradle (they
# are separate solids, attached to nothing) since the detent boss became the separate detent block (v0.25 [Ed 18:15]).
#   dial-post2-v029.png  1: 3D, the region from above (cradle body, stops + posts, detent block, springs, the dial's lower part);
#                        2: plan at the stop blocks' height; 3: plan at the anchor posts' height. Mechanism frame.
# Run from cad/knob-param:  PYTHONPATH=. xvfb-run -a python tools/studies/dial_post2_fig.py <out dir>
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
    from PIL import Image, ImageDraw
    from build123d import Box, Pos, Align
    from knobparam.common import model
    from knobparam.assembly.build import build_all
    from knobparam.assembly.plan_sheet import _cut_faces
    from knobparam.assembly.colours import colour, see_through
    D = model.derive(model.default_params())
    parts, _st, _k, _o = build_all(D)
    cr = parts["base cradle"]
    sols = sorted(cr.solids(), key=lambda q: -q.volume)
    body, floating = sols[0], [q for q in sols[2:]]
    keep = {n: s for n, s in parts.items() if n.startswith(("control dial lower part", "detent block (", "centring spring",
                                                             "spring anchor pin", "detent 1 ball", "detent train pedestal"))}
    T = D["travel_deg"] + D["stop_bias"]; a = D["sl_ang"]
    sxy = lambda r, ang: (r * math.cos(math.radians(ang)), r * math.sin(math.radians(ang)))
    outs = []
    # ---- 1: 3D from above, region clipped ----
    reg = Pos(-14, -18, 3.0) * Box(28, 18, 11.0, align=(Align.MIN, Align.MIN, Align.MIN))
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
    add(body, "#c9cfd4")
    for q in floating:
        add(q, "#e53935")
    for n, s in keep.items():
        if n.startswith("control dial lower part"):
            add(s, "#7c8a96", 0.35, False)
        elif n.startswith("detent block ("):
            add(s, "#f2c14e", 0.85, False)
        elif n.startswith("centring spring"):
            add(s, "#8d6e63")
        else:
            add(s, colour(n))
    ax_, ay_ = D["sl_anchor_xy"][1]; bx_, by_ = D["sl_anchor_xy"][0]
    s2 = sxy(6.9, a - T - 3.0); s1 = sxy(6.9, a + T + 3.0)
    bk = sxy(D["ad_r"], D["ad_ang"]); lv = sxy(D["sl_r"] - 0.6, a)
    labels(pl, [((ax_, ay_, 8.8), "post 2 (floating)"), ((s2[0], s2[1], 6.8), "stop 2 (floating)"),
                ((bx_, by_, 8.8), "post 1"), ((s1[0], s1[1], 6.8), "stop 1"),
                ((bk[0], bk[1], D["det_z1"]), "detent block"), ((lv[0], lv[1], D["sl_top"]), "lever (dial)")])
    c = np.array([0.0, -9.0, 7.0])
    pl.camera.position = tuple(c + np.array([12.0, -30.0, 40.0])); pl.camera.focal_point = tuple(c); pl.camera.up = (0, 0, 1)
    pl.add_text("1. From above and outside (mechanism frame): floating pieces red, detent block yellow, dial's lower part see-through",
                position="upper_left", font_size=9, color="black")
    f = os.path.join(OUT, "_p2_1.png"); pl.screenshot(f); pl.close(); outs.append(f)

    # ---- 2, 3: plans ----
    def plan(fn, z, title, notes):
        fig = plt.figure(figsize=(7.6, 7.6), dpi=125); ax = fig.add_axes([0.11, 0.09, 0.86, 0.84])
        items = [("base cradle body", body, "#c9cfd4")] + [("floating", q, "#e53935") for q in floating] + \
                [(n, s, None) for n, s in keep.items()]
        for n, s, col in items:
            b = s.bounding_box()
            if b.min.Z > z or b.max.Z < z:
                continue
            t = _cut_faces(s, "z", z)
            if t:
                fc = col or ("#f2c14e" if n.startswith("detent block (") else "#8d6e63" if "spring" in n else colour(n))
                ax.add_collection(PolyCollection(t, facecolors=fc, edgecolors="none",
                                                 alpha=0.5 if n.startswith("control dial lower") else 1.0))
        for ang in (a - T, a + T):   # the lever at ±travel (outline)
            p = [sxy(D["dial_tube_od"] / 2, ang), sxy(D["sl_r"], ang)]
            ax.plot([q[0] for q in p], [q[1] for q in p], color="#1565c0", lw=0.8, ls="--")
        k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
        for t, p, q in notes:
            ax.annotate(t, p, q, **k)
        ax.set_xlim(-12, 10); ax.set_ylim(-17, 1); ax.set_aspect("equal"); ax.grid(alpha=0.2)
        ax.set_xlabel("x (mm, mechanism frame)"); ax.set_ylabel("y (mm)")
        ax.set_title(title, fontsize=10, loc="left")
        f = os.path.join(OUT, fn); fig.savefig(f); plt.close(fig); outs.append(f)
    zs = (6.2 + D["sl_top"]) / 2
    plan("_p2_2.png", zs, f"2. Plan at z {zs:.2f} (the stop blocks), lever dashed at ±travel",
         [("stop 2: its end floats", s2, (-11, -2)), ("stop 1", s1, (4.5, -1.5)), ("lever", lv, (2.0, -14.5))])
    zp = 8.0
    plan("_p2_3.png", zp, f"3. Plan at z {zp:.2f} (the anchor posts, springs, detent block head)",
         [("post 2 (floating)", (ax_, ay_), (-11, -2)), ("post 1", (bx_, by_), (4.5, -1.5)),
          ("detent block", sxy(D["ad_r"], D["ad_ang"]), (-11.5, -16)), ("spring 2", ((ax_ + sxy(D['sl_pin_r'], a)[0]) / 2,
           (ay_ + sxy(D['sl_pin_r'], a)[1]) / 2), (2.0, -14.5))])
    ims = [Image.open(f) for f in outs]
    H = max(i.height for i in ims); ims = [i.resize((int(i.width * H / i.height), H)) for i in ims]
    cv = Image.new("RGB", (sum(i.width for i in ims), H + 50), "white"); x = 0
    for i in ims:
        cv.paste(i, (x, 50)); x += i.width
    ImageDraw.Draw(cv).text((20, 15), f"Knob {D['version']} dial item 6: centring-spring anchor post 2 and the lever's hard-stop block 2 are "
                            "attached to nothing in the base cradle (separate solids, red); they sit over the dial's lower part.", fill="black")
    out = os.path.join(OUT, "dial-post2-v029.png"); cv.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out, [round(q.volume, 2) for q in floating])


if __name__ == "__main__":
    main()
