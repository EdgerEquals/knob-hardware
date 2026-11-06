"""v0.19 section sheet: plan cuts looking down at every layer, plus vertical cuts, all in the panel frame.

Each cut intersects every part with a thin slab and fills the cut faces in the part colour.
Run from cad/knob-param:  python -m knobparam.assembly.plan_sheet"""
import math, os, sys, time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch

def colour(n):
    """v0.19b: real colour by material (assembly/colours.py)."""
    from .colours import colour as _c, legend as _l
    return _l(n), _c(n)


def _edge(hexc, k=0.55):
    h = hexc.lstrip("#"); r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % tuple(int(v * k) for v in (r, g, b))


def _cut_faces(solid, axis, at, eps=0.002):
    """Faces of solid cut by a thin slab normal to axis ('z' | 'x' | 'y') at 'at'. Returns a list of 2D triangle lists."""
    from build123d import Box, Pos, Align
    big = 400.0
    if axis == "z":
        slab = Pos(0, 0, at) * Box(big, big, eps, align=(Align.CENTER, Align.CENTER, Align.MIN))
    elif axis == "x":
        slab = Pos(at, 0, 0) * Box(eps, big, big, align=(Align.MIN, Align.CENTER, Align.CENTER))
    else:
        slab = Pos(0, at, 0) * Box(big, eps, big, align=(Align.CENTER, Align.MIN, Align.CENTER))
    try:
        x = solid & slab
    except Exception:
        return []
    if x is None:
        return []
    tris = []
    for f in x.faces():
        c = f.center()
        if axis == "z" and abs(c.Z - at) > eps / 4:
            continue
        if axis == "x" and abs(c.X - at) > eps / 4:
            continue
        if axis == "y" and abs(c.Y - at) > eps / 4:
            continue
        try:
            vs, ts = f.tessellate(0.05)
        except Exception:
            continue
        P = [(v.X, v.Y, v.Z) for v in vs]
        for t in ts:
            if axis == "z":
                tris.append([(P[i][0], P[i][1]) for i in t])
            elif axis == "x":
                tris.append([(P[i][1], P[i][2]) for i in t])
            else:
                tris.append([(P[i][0], P[i][2]) for i in t])
    return tris


def _spans(bb, axis, at):
    lo, hi = {"z": (bb.min.Z, bb.max.Z), "x": (bb.min.X, bb.max.X), "y": (bb.min.Y, bb.max.Y)}[axis]
    return lo - 1e-6 <= at <= hi + 1e-6


def cut(parts, axis, at):
    out = []   # (name, legend, colour, tris)
    for n, s in parts.items():
        try:
            bb = s.bounding_box()
        except Exception:
            continue
        if not _spans(bb, axis, at):
            continue
        tris = _cut_faces(s, axis, at)
        if tris:
            leg, c = colour(n)
            out.append((n, leg, c, tris))
    return out


def draw(ax, layer, title, xlim, ylim, xlabel="x (mm)", ylabel="y (mm)"):
    used = {}
    for n, leg, c, tris in layer:
        ax.add_collection(PolyCollection(tris, facecolors=c, edgecolors=c, linewidths=0.15))
        used.setdefault(leg, c)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect("equal")
    ax.set_title(title, fontsize=8.5, loc="left")
    ax.tick_params(labelsize=6); ax.set_xlabel(xlabel, fontsize=7); ax.set_ylabel(ylabel, fontsize=7)
    ax.grid(True, lw=0.2, alpha=0.4)
    return used


def main():
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, here)
    from knobparam.common import model
    from knobparam.assembly.build import build_all, view
    t0 = time.time()
    D = model.derive(model.default_params())
    parts, stats, keys, owner = build_all(D)
    parts, keys = view(parts, keys, D, "panel")
    from knobparam.assembly import joystick as js   # v0.19b: the joystick stack sits in the sheet too
    jp, JD = js.placed(); parts = dict(parts); parts.update(jp)
    zfp = (D["z_fp0"] + D["z_fp1"]) / 2
    levels = [
        (zfp, "faceplate: knob, joystick opening, jack bushings, USB-C"),
        (30.5, "under the plate: joystick top board on the vertical boards, case cradle, knob shell, collar"),
        (20.0, "jack bodies, knob shell, corner posts below the jacks"),
        (12.0, "inside the knob: 1220 and 716 cans, brass tube" if D["feel_on"] else "inside the knob: 1220 can, brass tube"),
        (D["hb_mid"], "ring band: herringbone ring, encoder and idler pinions"),
        (5.0, "Hall arm, single detent, lever"),
        (0.5, "PCB front: Hall sensors, cradle plate, motor tabs, clear OLED over window D, H7B0 and the vertical-board headers"),
        (D["z_pcb_back"] / 2, "main PCB: windows A B C E + D (clear OLED, whole), corner notches, holes"),
        (D["z_pcb_back"] - 0.6, "PCB back: emitters, bearing 2 seat, joystick rear anchor"),
        ((D["fg_z_top"] + D["fg_z_bot"]) / 2, "feel compound gear (under the PCB)" if D["feel_on"] else "under the PCB: encoder sensor"),
        ((D["h_big_top"] + D["h_big_bot"]) / 2 if "h_big_top" in D else -11.2, "encoder disc, sensor (top, under the joystick)"),
        (D["amo_lower_z"][0] + D["amo_t"] / 2, "lower (front) AMOLED on its pad"),
        (D["amo_upper_z"][0] + D["amo_t"] / 2, "upper (rear) AMOLED on the cover floor"),
    ]
    xl = (-27, 27)
    yl = (D["panel_y0"] - 2, D["panel_y1"] + 2)
    zl = (D["z_cover_out"] - 2, D["z_top"] + 2)
    ncol = 7
    fig = plt.figure(figsize=(ncol * 3.6, 2 * 8.4 + 9.0), dpi=110)
    gs = fig.add_gridspec(3, ncol, height_ratios=[8.4, 8.4, 9.0], hspace=0.28, wspace=0.18)
    legend = {}
    for i, (z, what) in enumerate(levels):
        ax = fig.add_subplot(gs[i // ncol, i % ncol])
        layer = cut(parts, "z", z)
        import textwrap
        legend.update(draw(ax, layer, f"z {z:+.2f} mm\n" + "\n".join(textwrap.wrap(what, 34)), xl, yl))
        print(f"  plan z {z:+.2f}: {len(layer)} parts  ({time.time() - t0:.0f} s)", flush=True)
    # legend in the last plan slot
    lax = fig.add_subplot(gs[1, ncol - 1]); lax.axis("off")
    lax.legend(handles=[Patch(fc=c, ec="k", lw=0.3, label=l) for l, c in sorted(legend.items())], loc="upper left", fontsize=6.5, frameon=False)
    # vertical cuts
    axv1 = fig.add_subplot(gs[2, 0:3])
    lay = cut(parts, "x", 0.0)
    draw(axv1, lay, "vertical cut x = 0 (front to back, through the knob, joystick, jacks and USB-C); y up the panel, z out of the panel",
         yl, zl, xlabel="y (mm)", ylabel="z (mm, PCB front = 0)")
    axv2 = fig.add_subplot(gs[2, 3:5])
    lay = cut(parts, "y", 0.0)
    draw(axv2, lay, "vertical cut y = 0 (across, through the knob axis)", xl, zl, xlabel="x (mm)", ylabel="z (mm)")
    ex, ey = D["enc_xy"]; a = math.radians(D["mech_rot"]); py = math.sin(a) * ex + math.cos(a) * ey
    axv3 = fig.add_subplot(gs[2, 5:7])
    lay = cut(parts, "y", py)
    draw(axv3, lay, f"vertical cut y = {py:.1f} (across, through the encoder wheel; glass, cap and seal ring at the sides)", xl, zl, xlabel="x (mm)", ylabel="z (mm)")
    fig.suptitle(f"Knob stack {D['version']}: section sheet, panel frame (looking at the panel face for the plan cuts). "
                 f"1220 at the bottom, encoder at the top, cover depth {D['cover_depth']:.1f} mm.", fontsize=13, x=0.01, ha="left")
    out = os.path.join(os.path.dirname(here), "assemblies", f"knob-stack-{D['version']}", f"knob-stack-{D['version']}-section-sheet.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    print("wrote", out, f"{time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
