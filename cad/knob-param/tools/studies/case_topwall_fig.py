# v0.25 study (3 Nov evening, joystick item 5; IN THE MODEL since v0.26 [Ed 4 Nov 10:03], see case_topwall_v026_fig.py): the case top wall is open behind the joystick.
# The joystick cutout prism (2 hole_hw x 2 hole_hh, centred on place_y) runs from z_seat - cut_slop to the front and reaches past the
# body's top wall (joy_y_far > body_y1), so the wall, the top PCB ledge and the two top corner posts are cut away over its width.
# What-if: the same prism starting at z_top (the lowest joystick part over the wall's slot - 0.3) instead of z_seat - cut_slop.
# The restored material (what-if case - v0.25 case with the cradle) is checked against every other part.
#   case-topwall-v025.png  1: now, the case from behind/above; 2: the what-if, same view; 3: straight-on cut at x = 0, every part,
#                          the restored material hatched
# Run from cad/knob-param:  PYTHONPATH=. xvfb-run -a python tools/studies/case_topwall_fig.py <out dir>
import os, sys
sys.path.insert(0, ".")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from js_v025_fig import load, region_parts, labels, to_pv

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
AIR = 0.3   # [A] restored wall top under the lowest joystick part over it


def slot_parts(D, parts):
    from build123d import Box, Pos, Align
    z0 = D["z_seat"] - D["cut_slop"]
    slot = Pos(-D["hole_hw"], D["y_in1"], z0) * Box(2 * D["hole_hw"], D["body_y1"] - D["y_in1"], D["z_fp0"] - z0,
                                                     align=(Align.MIN,) * 3)
    out = []
    for n, s in parts.items():
        if n == "case":
            continue
        try:
            q = s & slot
            if q is not None and q.volume > 1e-4:
                bb = q.bounding_box(); out.append((n, q.volume, bb.min.Z, bb.max.Z))
        except Exception:
            pass
    return out


def what_if(D, z_top):
    import knobparam.case.parts.shell as S
    orig = S._plate
    def patched(w, h, r, z0, z1, x, y):
        if abs(w - D["joy_hole"][0]) < 1e-9 and abs(h - D["joy_hole"][1]) < 1e-9 and abs(z0 - (D["z_seat"] - D["cut_slop"])) < 1e-9:
            z0 = z_top
        return orig(w, h, r, z0, z1, x, y)
    S._plate = patched
    try:
        return S.build(D)["case"]
    finally:
        S._plate = orig


def main():
    import pyvista as pv
    from PIL import Image, ImageDraw
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from knobparam.assembly.plan_sheet import _cut_faces
    from knobparam.assembly.colours import colour, see_through
    D, JD, parts = load()
    sp = slot_parts(D, parts)
    for r in sorted(sp, key=lambda r: r[2]):
        print(f"in the wall's slot: {r[0]:40s} {r[1]:7.3f} mm3  z {r[2]:6.2f}..{r[3]:6.2f}")
    z_low = min([r[2] for r in sp] + [D["z_fp0"]])
    z_top = z_low - AIR
    new = what_if(D, z_top)
    old = parts["case"]
    restored = new - old
    print(f"what-if prism from z {z_top:.2f}: restored {restored.volume:.1f} mm3")
    clash = []
    for n, s in parts.items():
        if n == "case":
            continue
        try:
            q = restored & s
            if q is not None and q.volume > 1e-3:
                clash.append((n, q.volume)); print(f"  CLASH restored x {n}: {q.volume:.3f} mm3")
        except Exception:
            pass
    if not clash:
        print("  restored material clashes with nothing")
    case2 = (old + new).clean()
    z0 = D["z_seat"] - D["cut_slop"]
    # ---- 1 and 2: the case from behind and above, now and what-if ----
    outs = []
    for tag, cs in (("now", old), ("what-if", case2)):
        pl = pv.Plotter(off_screen=True, window_size=(1100, 1000)); pl.set_background("white")
        reg = region_parts(D, JD, {"case": cs}, -30, 30, 18, D["panel_y1"] + 1, -3, D["z_fp1"] + 1)
        for n, q in reg:
            m = to_pv(q)
            pl.add_mesh(m, color="#b9cdd6", smooth_shading=False, specular=0.2)
            pl.add_mesh(m.extract_feature_edges(40), color="#37474f", line_width=1.0)
        if tag == "now":
            g = pv.Box(bounds=(-D["hole_hw"], D["hole_hw"], D["y_in1"], D["body_y1"], z0, D["z_fp0"]))
            pl.add_mesh(g, color="#e53935", opacity=0.30); pl.add_mesh(g.extract_feature_edges(10), color="#c62828", line_width=2)
            labels(pl, [((8.0, D["body_y1"], 14.0), f"open: {2 * D['hole_hw']:.1f} wide, from z {z0:.2f} to the faceplate"),
                        ((-21.2, 45.35, 14.0), "top post, cut back")])
            ttl = "1. NOW (v0.25): the case alone from behind and above the top wall. Red = the opening."
        else:
            rm = to_pv(restored)
            if rm is not None:
                pl.add_mesh(rm, color="#43a047", opacity=0.55)
            labels(pl, [((8.0, D["body_y1"], 14.0), f"wall back, z {z0:.2f}..{z_top:.1f}"), ((-21.2, 45.35, 14.0), "top post whole again")])
            ttl = "2. PROPOSED: the cutout starts just under the cradle. Green = material that comes back."
        c = np.array([0.0, 44.0, 15.0])
        pl.camera.position = tuple(c + np.array([45.0, 90.0, -75.0])); pl.camera.focal_point = tuple(c); pl.camera.up = (0, 0, 1)
        pl.add_text(ttl, position="upper_left", font_size=10, color="black")
        f = os.path.join(OUT, f"_tw_{tag}.png"); pl.screenshot(f); pl.close(); outs.append(f)
    # ---- 3: straight-on cut at x = 0, every part ----
    fig = plt.figure(figsize=(8.0, 9.1), dpi=125); ax = fig.add_axes([0.10, 0.08, 0.86, 0.84])
    for n, s in parts.items():
        try:
            bb = s.bounding_box()
        except Exception:
            continue
        if bb.min.X > 0 or bb.max.X < 0 or bb.max.Y < 28 or bb.min.Z > D["z_fp1"] + 6:
            continue
        t = _cut_faces(s, "x", 0.0)
        if t:
            ax.add_collection(PolyCollection(t, facecolors=colour(n), edgecolors="none", alpha=0.55 if see_through(n) else 1.0))
    t = _cut_faces(restored, "x", 0.0)
    ax.add_collection(PolyCollection(t, facecolors="none", edgecolors="#2e7d32", hatch="////", linewidths=0.0))
    ax.add_patch(plt.Rectangle((D["y_in1"], z0), D["body_y1"] - D["y_in1"], z_top - z0, fill=False, ec="#2e7d32", lw=1.6))
    ax.add_patch(plt.Rectangle((D["y_in1"], z0), D["body_y1"] - D["y_in1"], D["z_fp0"] - z0, fill=False, ec="#c62828", lw=1.0, ls="--"))
    k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    ax.annotate("top wall: open now (red dashed);\nproposed wall (green hatched)", (D["body_y1"], 18), (52.8, 22), **k)
    ax.annotate("faceplate", (58, D["z_fp0"] + 1.2), (56, 42.5), **k)
    ax.annotate("Ø2 balls in the cradle\n(the lowest thing over the wall)", (D["y_in1"] + 0.3, z_low + 0.5), (52.8, 31.5), **k)
    ax.annotate("main board", (40, -0.8), (52.8, 4), **k)
    ax.annotate(f"wall stub under the\ncutout (z to {z0:.2f})", (D["y_in1"] + 1.2, z0 - 0.5), (52.8, -4.5), **k)
    ax.set_xlim(28, 64); ax.set_ylim(-7, 46); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("y (mm, up the panel)"); ax.set_ylabel("z (mm, out of the panel)")
    ax.set_title("3. Straight-on cut at x = 0 (through the joystick), every part", fontsize=10, loc="left")
    f = os.path.join(OUT, "_tw_cut.png"); fig.savefig(f); plt.close(fig); outs.append(f)
    ims = [Image.open(f) for f in outs]
    H = max(i.height for i in ims); ims = [i.resize((int(i.width * H / i.height), H)) for i in ims]
    W = sum(i.width for i in ims)
    cv = Image.new("RGB", (W, H + 50), "white"); x = 0
    for i in ims:
        cv.paste(i, (x, 50)); x += i.width
    ImageDraw.Draw(cv).text((20, 15), f"Joystick item 5 (knob v0.25 / joystick v0.9): the joystick cutout runs the case's whole depth and reaches y "
                            f"{D['joy_y_far']:.1f}, past the top wall's outside face ({D['body_y1']:.1f}). Proposed: start the cutout at z "
                            f"{z_top:.1f}; restored material clashes with: {', '.join(n for n, _ in clash) or 'nothing'}.", fill="black")
    out = os.path.join(OUT, "case-topwall-v025.png"); cv.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out)


if __name__ == "__main__":
    main()
