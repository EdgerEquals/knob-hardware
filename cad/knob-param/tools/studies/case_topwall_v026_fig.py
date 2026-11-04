# v0.26 [Ed 4 Nov 10:03] joystick item 5 in the model: the joystick cutout starts 1.40 behind the faceplate back, so the case's top wall,
# the main board's top ledge and the two top corner posts are whole again; the ledge is notched round the vertical boards.
#   case-topwall-v026.png  1: the case alone from behind and above (as case-topwall-v025.png panel 1); 2: straight-on cut at x = 0, every
#                          part; 3: plan at z = mid-ledge over the top ledge, the vertical boards in their notches
# Run from cad/knob-param:  PYTHONPATH=. xvfb-run -a python tools/studies/case_topwall_v026_fig.py <out dir>
import os, sys
sys.path.insert(0, ".")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from js_v025_fig import load, region_parts, labels, to_pv

OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def main():
    import pyvista as pv
    from PIL import Image, ImageDraw
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from knobparam.assembly.plan_sheet import _cut_faces
    from knobparam.assembly.colours import colour, see_through
    D, JD, parts = load()
    z0c = D["z_joy_cut0"]
    outs = []
    # ---- 1: the case from behind and above ----
    pl = pv.Plotter(off_screen=True, window_size=(1100, 1000)); pl.set_background("white")
    for n, q in region_parts(D, JD, {"case": parts["case"]}, -30, 30, 18, D["panel_y1"] + 1, -3, D["z_fp1"] + 1):
        m = to_pv(q)
        pl.add_mesh(m, color="#b9cdd6", smooth_shading=False, specular=0.2)
        pl.add_mesh(m.extract_feature_edges(40), color="#37474f", line_width=1.0)
    labels(pl, [((8.0, D["body_y1"], 14.0), f"top wall whole, z {D['z_rim']:.1f} to {z0c:.2f}")])
    c = np.array([0.0, 44.0, 15.0])
    pl.camera.position = tuple(c + np.array([45.0, 90.0, -75.0])); pl.camera.focal_point = tuple(c); pl.camera.up = (0, 0, 1)
    pl.add_text(f"1. v0.26: the case alone from behind and above the top wall", position="upper_left", font_size=10, color="black")
    f = os.path.join(OUT, "_tw26_1.png"); pl.screenshot(f); pl.close(); outs.append(f)
    # ---- 2: straight-on cut at x = 0, every part ----
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
    k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    ax.annotate(f"top wall (case), to z {z0c:.2f}", (D["body_y1"] - 1.2, 18), (52.8, 22), **k)
    ax.annotate(f"{D['z_fp0'] - z0c:.2f} slit under the faceplate\n(over the cradle's Ø2 balls)", (D["body_y1"] - 1.2, z0c + 0.6),
                (52.8, 30.5), **k)
    ax.annotate("top ledge (case)", (D["pcb_y1"] - 0.7, D["z_ledge1"] - 0.5), (52.8, 5), **k)
    ax.annotate("main board", (40, -0.8), (52.8, -3.5), **k)
    ax.set_xlim(28, 64); ax.set_ylim(-7, 46); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("y (mm, up the panel)"); ax.set_ylabel("z (mm, out of the panel)")
    ax.set_title("2. Straight-on cut at x = 0 (through the joystick), every part", fontsize=10, loc="left")
    f = os.path.join(OUT, "_tw26_2.png"); fig.savefig(f); plt.close(fig); outs.append(f)
    # ---- 3: plan through the top ledge ----
    zl = (D["z_ledge0"] + D["z_ledge1"]) / 2
    fig = plt.figure(figsize=(8.0, 9.1), dpi=125); ax = fig.add_axes([0.10, 0.08, 0.86, 0.84])
    for n, s in parts.items():
        try:
            bb = s.bounding_box()
        except Exception:
            continue
        if bb.min.Z > zl or bb.max.Z < zl or bb.max.Y < 38:
            continue
        t = _cut_faces(s, "z", zl)
        if t:
            ax.add_collection(PolyCollection(t, facecolors=colour(n), edgecolors="none", alpha=0.55 if see_through(n) else 1.0))
    V, a = D["vb"], D["vb_ledge_air"]
    for sx in (-1, 1):
        ax.annotate(f"vertical board {'L' if sx < 0 else 'R'} in its notch\n({V['t'] + 2 * a:.1f} wide, {a:.2f} a side)",
                    (sx * V["x"], D["pcb_y1"] - 0.75), (sx * V["x"] - (12 if sx < 0 else 2), 43.0), **k)
    ax.annotate("top ledge (back over the joystick's width)", (0, D["pcb_y1"] - 0.75), (-12, 54.5), **k)
    ax.annotate("top wall", (-8, D["body_y1"] - 1.2), (-20, 56.5), **k)
    ax.annotate("top corner post, whole", (21.2, 45.35), (8, 39.5), **k)
    ax.set_xlim(-26, 26); ax.set_ylim(38, 58); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm, up the panel)")
    ax.set_title(f"3. Plan at z = {zl:.2f} (through the top ledge), from the front", fontsize=10, loc="left")
    f = os.path.join(OUT, "_tw26_3.png"); fig.savefig(f); plt.close(fig); outs.append(f)
    ims = [Image.open(f) for f in outs]
    H = max(i.height for i in ims); ims = [i.resize((int(i.width * H / i.height), H)) for i in ims]
    W = sum(i.width for i in ims)
    cv = Image.new("RGB", (W, H + 50), "white"); x = 0
    for i in ims:
        cv.paste(i, (x, 50)); x += i.width
    ImageDraw.Draw(cv).text((20, 15), f"Knob v0.26 ([Ed 4 Nov 10:03], joystick item 5): the joystick cutout starts at z {z0c:.2f}, "
                            f"{D['joy_cut_to']:g} behind the faceplate back: the top wall, the main board's top ledge and the top corner posts "
                            "are whole again; the ledge is notched round the two vertical boards.", fill="black")
    out = os.path.join(OUT, "case-topwall-v026.png"); cv.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out)


if __name__ == "__main__":
    main()
