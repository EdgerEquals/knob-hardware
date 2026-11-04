# v0.27 [Ed 4 Nov 11:46] dial item 3 in the model: six Ø1 x 0.5 N52 cartridge magnet pairs at 0/30/120/150/240/270°, 0.30 bore gap.
#   cart-magnets-v027.png  1: plan through both magnets of each pair (z between the dial magnet and the bezel magnet), every part;
#                          2: straight-on cut through the knob axis and the 0° pair, every part
# Run from cad/knob-param:  PYTHONPATH=. xvfb-run -a python tools/studies/cart_mag6_v027_fig.py <out dir>
import os, sys, math
sys.path.insert(0, ".")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from js_v025_fig import load

OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from PIL import Image, ImageDraw
    from knobparam.assembly.plan_sheet import _cut_faces
    from knobparam.assembly.colours import colour, see_through
    D, JD, parts = load()
    bz = D["bz"]; d, h = bz["mag"]
    bez = [s for n, s in parts.items() if n.startswith("cartridge bezel")][0]
    bb = bez.bounding_box(); cx, cy = (bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2
    mags = {n: s for n, s in parts.items() if n.startswith("cartridge magnet")}
    def ctr(s):
        b = s.bounding_box(); return ((b.min.X + b.max.X) / 2, (b.min.Y + b.max.Y) / 2, (b.min.Z + b.max.Z) / 2)
    zd = min(ctr(s)[2] for s in mags.values()); zs = max(ctr(s)[2] for s in mags.values())
    zc = (zd + zs) / 2
    k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    outs = []

    def draw(ax, axis, at, keep):
        for n, s in parts.items():
            try:
                b = s.bounding_box()
            except Exception:
                continue
            if not keep(b):
                continue
            t = _cut_faces(s, axis, at)
            if t:
                ax.add_collection(PolyCollection(t, facecolors=colour(n), edgecolors="none", alpha=0.55 if see_through(n) else 1.0))

    # ---- 1: plan at z between the two magnets of a pair ----
    fig = plt.figure(figsize=(8.6, 8.6), dpi=125); ax = fig.add_axes([0.09, 0.08, 0.88, 0.85])
    near = lambda b: b.min.Z <= zc <= b.max.Z and b.max.X > cx - 23 and b.min.X < cx + 23 and b.max.Y > cy - 23 and b.min.Y < cy + 23
    draw(ax, "z", zc, near)
    for n, s in mags.items():
        x, y, z = ctr(s)
        if "bezel" in n:
            a = math.degrees(math.atan2(y - cy, x - cx))
            ax.annotate(f"{a % 360:.0f}°", (x, y), (cx + 23.6 * math.cos(math.radians(a)) - 1.2, cy + 23.6 * math.sin(math.radians(a)) - 0.4),
                        fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.6))
    for i, a in enumerate(bz["rib_angs"]):
        t = math.radians(a + 0.0)
        ax.annotate("key" if i == 0 else "seat rib", (cx + 19.0 * math.cos(t), cy + 19.0 * math.sin(t)),
                    (cx + 13.0 * math.cos(t) - 2.0, cy + 13.0 * math.sin(t)), **k)
    ax.set_xlim(cx - 26, cx + 26); ax.set_ylim(cy - 26, cy + 26); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm, up the panel)")
    ax.set_title(f"1. Plan at z = {zc:.2f} (through both magnets of every pair), from the front", fontsize=10, loc="left")
    f = os.path.join(OUT, "_cm27_1.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    # ---- 2: straight-on cut through the axis and the 0° pair ----
    m0 = [s for n, s in mags.items() if n.endswith(" 0°") and "bezel" in n][0]
    x0, y0, _ = ctr(m0)
    along_x = abs(y0 - cy) < abs(x0 - cx)          # the 0° pair lies along x from the axis: cut the plane y = cy
    axis, at = ("y", cy) if along_x else ("x", cx)
    u0 = x0 if along_x else y0; uc = cx if along_x else cy; sg = 1 if u0 > uc else -1
    fig = plt.figure(figsize=(8.6, 8.6), dpi=125); ax = fig.add_axes([0.11, 0.08, 0.86, 0.85])
    near2 = (lambda b: b.min.Y <= cy <= b.max.Y) if along_x else (lambda b: b.min.X <= cx <= b.max.X)
    draw(ax, axis, at, lambda b: near2(b) and b.max.Z > zc - 8 and b.min.Z < zc + 8)
    ax.annotate(f"bezel magnet Ø{d:g} x {h:g}, {bz['mag_dz']:g} above", (u0, zs + 0.2), (u0 - sg * 9, zs + 4.0), **k)
    ax.annotate(f"dial magnet Ø{d:g} x {h:g}", (u0 - sg * (h + D['cm_gap']), zd - 0.2), (u0 - sg * 9, zd - 3.5), **k)
    ax.annotate(f"{D['cm_gap']:.2f} gap (slip fit)", (u0 - sg * (h / 2 + D['cm_gap'] / 2), zc), (u0 - sg * 9, zc + 1.6), **k)
    ax.annotate(f"skirt skin {D['cm_skin_out']:.2f}", (u0 + sg * (h / 2 + 0.5), zs), (u0 + sg * 0.6, zs + 5.0), **k)
    ax.set_xlim(*(sorted((u0 + sg * 4.0, u0 - sg * 11.0))))
    ax.set_ylim(zc - 7.5, zc + 7.5); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel(f"{'x' if along_x else 'y'} (mm)"); ax.set_ylabel("z (mm, out of the panel)")
    ax.set_title(f"2. Straight-on cut through the axis and the 0° pair, every part", fontsize=10, loc="left")
    f = os.path.join(OUT, "_cm27_2.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    ims = [Image.open(f) for f in outs]
    H = max(i.height for i in ims); ims = [i.resize((int(i.width * H / i.height), H)) for i in ims]
    cv = Image.new("RGB", (sum(i.width for i in ims), H + 50), "white"); x = 0
    for i in ims:
        cv.paste(i, (x, 50)); x += i.width
    W = D["cm_mass_g"] * 9.81e-3
    ImageDraw.Draw(cv).text((20, 15), f"Knob v0.27 ([Ed 4 Nov 11:46], dial item 3): six Ø{d:g} x {h:g} N52 pairs at "
                            f"{', '.join(f'{a:g}' for a in bz['mag_angs'])}°, {D['cm_gap']:.2f} gap; {D['cm_hold']:.2f} N down in all "
                            f"({D['cm_hold'] / W:.1f}x the ~{D['cm_mass_g']:g} g cartridge), skirt skin {D['cm_skin_out']:.2f}.", fill="black")
    out = os.path.join(OUT, "cart-magnets-v027.png"); cv.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out)


if __name__ == "__main__":
    main()
