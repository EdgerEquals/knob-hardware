# Dial item 4 for Danny (4 Nov): the key rib + the two seat ribs [A] on the bezel cartridge, as in the model (knob v0.27).
#   cart-ribs-v027.png  1: the bezel alone from below (the three ribs); 2: the dial alone from above (the three slots);
#                       3: straight-on cut through the key (rib bottom on its slot floor = the seat)
# Run from cad/knob-param:  PYTHONPATH=. xvfb-run -a python tools/studies/cart_ribs_v027_fig.py <out dir>
import os, sys, math
sys.path.insert(0, ".")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from js_v025_fig import load, to_pv, labels

OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def main():
    import pyvista as pv
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from PIL import Image, ImageDraw
    from knobparam.assembly.plan_sheet import _cut_faces
    from knobparam.assembly.colours import colour, see_through
    D, JD, parts = load()
    bz = D["bz"]
    bezn = [n for n in parts if n.startswith("dial bezel")][0]
    bez = parts[bezn]
    bb = bez.bounding_box(); cx, cy = (bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2
    # the dial part that carries the slots: the one whose bounding box spans the land top and the outer wall
    dn = [n for n in parts if n.startswith("control dial dish")][0]; ds = parts[dn]
    rc = (bz["rib_r_in"] + D["bz_bore_r"]) / 2
    def at(a, r, z):
        t = math.radians(a); return (cx + r * math.cos(t), cy + r * math.sin(t), z)
    names = ["key (sets the angle)"] + ["seat rib"] * (len(bz["rib_angs"]) - 1)
    outs = []
    # ---- 1: bezel from below ----
    pl = pv.Plotter(off_screen=True, window_size=(1000, 1000)); pl.set_background("white")
    m = to_pv(bez); pl.add_mesh(m, color="#9aa4ab", smooth_shading=False, specular=0.2)
    pl.add_mesh(m.extract_feature_edges(40), color="#202529", line_width=1.0)
    labels(pl, [(at(a, rc, D["rib_z0"]), f"{nm} {a:g}°") for a, nm in zip(bz["rib_angs"], names)])
    c = np.array([cx, cy, D["rib_z0"] + 2])
    pl.camera.position = tuple(c + np.array([-26.0, -55.0, -92.0])); pl.camera.focal_point = tuple(c); pl.camera.up = (0, 1, 0)
    pl.add_text("1. The bezel (cartridge ring) alone, from below", position="upper_left", font_size=11, color="black")
    f = os.path.join(OUT, "_rb_1.png"); pl.screenshot(f); pl.close(); outs.append(f)
    # ---- 2: dial from above ----
    pl = pv.Plotter(off_screen=True, window_size=(1000, 1000)); pl.set_background("white")
    m = to_pv(ds); pl.add_mesh(m, color=colour(dn), smooth_shading=False, specular=0.2)
    pl.add_mesh(m.extract_feature_edges(40), color="#37474f", line_width=1.0)
    lab = [(at(a, D["ct"]["outer_r"] - 0.3, D["rib_z0"]), f"{'key slot' if i == 0 else 'seat slot'} {a:g}°")
           for i, a in enumerate(bz["rib_angs"])]
    labels(pl, lab)
    c = np.array([cx, cy, D["db_z1"] - 3])
    pl.camera.position = tuple(c + np.array([-30.0, -66.0, 86.0])); pl.camera.focal_point = tuple(c); pl.camera.up = (0, 0, 1)
    pl.add_text("2. The dial alone, from above (slots in its outer wall)", position="upper_left", font_size=11, color="black")
    f = os.path.join(OUT, "_rb_2.png"); pl.screenshot(f); pl.close(); outs.append(f)
    # ---- 3: straight-on cut through the key ----
    ka = bz["rib_angs"][0]
    along_x = abs(math.cos(math.radians(ka))) > 0.7
    axis, pos = ("y", cy) if along_x else ("x", cx)
    sg = 1 if (math.cos(math.radians(ka)) if along_x else math.sin(math.radians(ka))) > 0 else -1
    u0 = (cx if along_x else cy) + sg * rc
    fig = plt.figure(figsize=(8.0, 8.0), dpi=125); ax = fig.add_axes([0.12, 0.09, 0.85, 0.84])
    for n, s in parts.items():
        try:
            b = s.bounding_box()
        except Exception:
            continue
        inplane = (b.min.Y <= cy <= b.max.Y) if along_x else (b.min.X <= cx <= b.max.X)
        if not inplane or b.max.Z < D["rib_z0"] - 7 or b.min.Z > D["rib_z0"] + 8:
            continue
        t = _cut_faces(s, axis, pos)
        if t:
            ax.add_collection(PolyCollection(t, facecolors=colour(n), edgecolors="none", alpha=0.55 if see_through(n) else 1.0))
    k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    xr = u0 + sg * 2.4; ha = "left" if sg > 0 else "right"
    ax.annotate(f"key rib, {bz['rib_w']:g} wide (bezel)", (u0, D["rib_z0"] + 1.0), (xr, D["rib_z0"] + 4.2), ha=ha, **k)
    ax.annotate(f"rib bottom sits on the slot floor\n= the cartridge's height (z {D['rib_z0']:.2f},\n{bz['slot_depth']:g} under the land top)",
                (u0, D["rib_z0"]), (xr, D["rib_z0"] - 2.4), ha=ha, **k)
    ax.annotate(f"{bz['slot_r_clear']:g} rib to the slot's inner face", (u0 - sg * (rc - bz['rib_r_in']), D["rib_z0"] + 0.5),
                (xr, D["rib_z0"] + 1.6), ha=ha, **k)
    ax.annotate(f"dial: {D['rib_floor_wall']:.2f} under the slot floor", (u0 - sg * 0.3, D["rib_z0"] - 0.5),
                (xr, D["rib_z0"] - 4.6), ha=ha, **k)
    lo, hi = sorted((u0 - sg * 9.0, u0 + sg * 7.5))
    ax.set_xlim(lo, hi); ax.set_ylim(D["rib_z0"] - 6.5, D["rib_z0"] + 7.0); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel(f"{'x' if along_x else 'y'} (mm)"); ax.set_ylabel("z (mm, out of the panel)")
    ax.set_title(f"3. Straight-on cut through the key ({ka:g}°), every part", fontsize=10, loc="left")
    f = os.path.join(OUT, "_rb_3.png"); fig.savefig(f); plt.close(fig); outs.append(f)
    ims = [Image.open(f) for f in outs]
    H = max(i.height for i in ims); ims = [i.resize((int(i.width * H / i.height), H)) for i in ims]
    cv = Image.new("RGB", (sum(i.width for i in ims), H + 50), "white"); x = 0
    for i in ims:
        cv.paste(i, (x, 50)); x += i.width
    ImageDraw.Draw(cv).text((20, 15), f"Knob {D['version']} dial item 4: the key ({ka:g}°, [Ed 18:26]) plus two seat ribs "
                            f"({', '.join(f'{a:g}' for a in bz['rib_angs'][1:])}°, [A]); the three rib bottoms on their slot floors are "
                            f"the cartridge's three-point seat. Tangential clearance a side: key {bz['rib_clear'][0]:g}, seat ribs "
                            f"{bz['rib_clear'][1]:g}.", fill="black")
    out = os.path.join(OUT, "cart-ribs-v027.png"); cv.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out, "dial part:", dn)


if __name__ == "__main__":
    main()
