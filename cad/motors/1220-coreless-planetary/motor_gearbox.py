"""
Parametric geared-motor model (motor + 12 mm planetary gearbox), build123d.
Knob module v1, EdgerEquals. v0.1, 2026-10-31.

Every dimension lives in one PARAMS dict per variant. The N30 variant is a parameter swap.
Source tags: [S] = from a listing/datasheet (see scope/motor-dimensions.md), [A] = assumed, measure it.

Axis convention: motor axis along +X, output shaft points +X, rear of motor can at X=0.
The D-flat faces +Z (up). Terminals sit side by side along Y.
Drawing: THIRD-ANGLE projection. Front view (looking along +Y from the -Y side) in the centre,
plan/top view above it, right-side view (looking at the shaft end) to its right.

Run:  python motor_gearbox.py           -> builds 1220 and N30 into ./out_<name>/
"""
import math, os, sys
from build123d import *

VARIANTS = {
    "motor-1220": dict(
        title="Motor 1220 coreless planetary",
        body_d=12.0,          # [S] 12 mm can and gearbox (RobotDoo, NFP-D1220)
        motor_len=20.0,       # [S] motor body 20 (RobotDoo); bare can 20.8+/-0.2 (NFP)
        gearbox_len=17.0,     # [S/derived] 38 total - 20 motor = 18, minus boss_len
        boss_d=4.0,           # [A] output bearing collar dia, typical but not sourced
        boss_len=1.0,         # [A] collar height (counted inside the 38 total)
        shaft_d=3.0,          # [S] 3 mm D-shaft (RobotDoo)
        shaft_flat=2.5,       # [S] 2.5 across the flat (RobotDoo)
        shaft_len=5.5,        # [S] exposed shaft length (RobotDoo)
        flat_len=4.5,         # [A] flat runs from tip back this far
        seam_groove=0.3,      # [A] tiny groove depth marking motor/gearbox joint
        endcap_len=1.5,       # [A] plastic end cap, part of motor_len
        endcap_d=11.0,        # [A] end cap slightly undersize vs can
        rear_boss_d=3.0,      # [A] rear bearing bump on end cap
        rear_boss_len=0.6,    # [A]
        term_w=1.2,           # [A] solder tab width
        term_t=0.3,           # [A] tab thickness
        term_len=2.5,         # [A] tab protrusion behind end cap
        term_pitch=6.0,       # [A] tab spacing centre to centre (along Y)
        mount_holes=None,     # [unknown] no source shows the face pattern -> plain face, TBC
        ratio="1:144 (3-stage)",
        version="v0.1, 2026-10-31",
    ),
}
# N30 variant: parameter swap only
VARIANTS["motor-n30"] = dict(VARIANTS["motor-1220"],
    title="Motor N30 planetary",
    motor_len=20.0,       # [S] N30 can ~20 (spur datasheets); 37.5 total - 17.5 gearbox
    gearbox_len=16.5,     # [S/derived] 17.5 gearbox (ROYIHOME listing) minus boss_len
    boss_len=1.0,         # [A]
    shaft_d=2.5,          # [S] 2.5 shaft (ROYIHOME listing)
    shaft_flat=2.2,       # [S] 2.2 flat (ROYIHOME listing)
    shaft_len=8.0,        # [S] ~8 (ROYIHOME listing)
    flat_len=7.0,         # [A]
    ratio="~1:80 (3-stage, unstated)",
)


def build(p):
    r = p["body_d"] / 2
    x_gb0 = p["motor_len"]
    x_boss0 = x_gb0 + p["gearbox_len"]
    x_sh0 = x_boss0 + p["boss_len"]
    ax = Plane.YZ  # normal +X

    can = Plane.YZ.offset(p["endcap_len"]) * Cylinder(r, p["motor_len"] - p["endcap_len"],
                                   align=(Align.CENTER, Align.CENTER, Align.MIN))
    cap = Cylinder(p["endcap_d"] / 2, p["endcap_len"], align=(Align.CENTER, Align.CENTER, Align.MIN))
    cap = Plane.YZ * cap
    rboss = Plane.YZ.offset(-p["rear_boss_len"]) * Cylinder(p["rear_boss_d"] / 2, p["rear_boss_len"],
                                   align=(Align.CENTER, Align.CENTER, Align.MIN))
    motor = can + cap + rboss

    gb = Plane.YZ.offset(x_gb0) * Cylinder(r, p["gearbox_len"], align=(Align.CENTER, Align.CENTER, Align.MIN))
    # seam groove at motor/gearbox joint
    g = p["seam_groove"]
    groove = Plane.YZ.offset(x_gb0 - 0.2) * (Cylinder(r + 1, 0.4, align=(Align.CENTER, Align.CENTER, Align.MIN))
                                           - Cylinder(r - g, 0.4, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    boss = Plane.YZ.offset(x_boss0) * Cylinder(p["boss_d"] / 2, p["boss_len"], align=(Align.CENTER, Align.CENTER, Align.MIN))

    sr = p["shaft_d"] / 2
    shaft = Plane.YZ.offset(x_sh0) * Cylinder(sr, p["shaft_len"], align=(Align.CENTER, Align.CENTER, Align.MIN))
    # D-flat: remove material above z = flat - r (flat faces +Z)
    zcut = p["shaft_flat"] - sr
    cut = Box(p["flat_len"], p["shaft_d"] * 2, p["shaft_d"],
              align=(Align.MAX, Align.CENTER, Align.MIN))
    cut = Pos(x_sh0 + p["shaft_len"] + 0.001, 0, zcut) * cut
    shaft = shaft - cut

    tabs = []
    for s in (-1, 1):
        t = Box(p["term_len"], p["term_t"], p["term_w"], align=(Align.MAX, Align.CENTER, Align.CENTER))
        tabs.append(Pos(0, s * p["term_pitch"] / 2, 0) * t)
    model = motor + gb - groove + boss + shaft + tabs[0] + tabs[1]
    return model


def edges2d(shape, origin, up):
    vis, hid = shape.project_to_viewport(origin, up, (0, 0, 0))
    def pts(es):
        out = []
        for e in es:
            n = 2 if e.geom_type == GeomType.LINE else 48
            out.append([((e @ (i / (n - 1))).X, (e @ (i / (n - 1))).Y) for i in range(n)])
        return out
    return pts(vis), pts(hid)


def main(name, p, outdir):
    os.makedirs(outdir, exist_ok=True)
    m = build(p)
    export_step(m, os.path.join(outdir, f"{name}.step"))

    L_total = p["motor_len"] + p["gearbox_len"] + p["boss_len"]
    # views: (origin, up) -> 2D in viewport coords
    far = 500
    front = edges2d(m, (0, -far, 0), (0, 0, 1))      # x right, z up
    plan = edges2d(m, (0, 0, far), (0, 1, 0))        # x right, y up (front of part at bottom)
    side = edges2d(m, (far, 0, 0), (0, 0, 1))        # looking at shaft end: horiz=+Y? check below

    # layout offsets (model mm). third-angle: plan above front, right view right of front
    gap = 14
    xmin = -p["term_len"] - p["rear_boss_len"]
    xmax = L_total + p["shaft_len"]
    off = {
        "front": (0, 0),
        "plan": (0, p["body_d"] + gap),
        "side": (xmax + gap + p["body_d"] / 2, 0),
    }
    views = {"front": front, "plan": plan, "side": side}

    # ---------- DXF ----------
    import ezdxf
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4  # mm
    doc.layers.add("VISIBLE", color=7)
    doc.layers.add("HIDDEN", color=8, linetype="DASHED")
    doc.layers.add("CENTER", color=1, linetype="CENTER")
    doc.layers.add("DIMS", color=3)
    doc.layers.add("TEXT", color=7)
    msp = doc.modelspace()
    for v, (vis, hid) in views.items():
        ox, oy = off[v]
        for layer, es in (("VISIBLE", vis), ("HIDDEN", hid)):
            for pl in es:
                msp.add_lwpolyline([(x + ox, y + oy) for x, y in pl], dxfattribs={"layer": layer})
    # centre lines
    r = p["body_d"] / 2
    for v in ("front", "plan"):
        ox, oy = off[v]
        msp.add_line((xmin - 2 + ox, oy), (xmax + 2 + ox, oy), dxfattribs={"layer": "CENTER"})
    sx, sy = off["side"]
    msp.add_line((sx - r - 2, sy), (sx + r + 2, sy), dxfattribs={"layer": "CENTER"})
    msp.add_line((sx, sy - r - 2), (sx, sy + r + 2), dxfattribs={"layer": "CENTER"})
    ds = dict(dimstyle="EZDXF", override={"dimtxt": 1.2, "dimasz": 0.9, "dimexe": 0.6, "dimexo": 0.5, "dimdec": 1}, dxfattribs={"layer": "DIMS"})
    xg = p["motor_len"]; xb = xg + p["gearbox_len"]; xs = xb + p["boss_len"]
    msp.add_linear_dim(base=(0, -r - 8), p1=(0, -r), p2=(L_total, -r), **ds).render()
    msp.add_linear_dim(base=(0, -r - 4), p1=(0, -r), p2=(xg, -r), **ds).render()
    msp.add_linear_dim(base=(0, -r - 4), p1=(xg, -r), p2=(L_total, -r), **ds).render()
    msp.add_linear_dim(base=(0, -r - 4), p1=(xs, -p["shaft_d"] / 2), p2=(xs + p["shaft_len"], -p["shaft_d"] / 2), **ds).render()
    msp.add_linear_dim(base=(-6, 0), p1=(0, -r), p2=(0, r), angle=90, **ds).render()
    msp.add_linear_dim(base=(sx + r + 3, 0), p1=(sx, -p["shaft_d"] / 2), p2=(sx, p["shaft_d"] / 2), angle=90, **ds).render()
    msp.add_linear_dim(base=(xmax + 4, 0), p1=(xmax, -p["shaft_d"] / 2), p2=(xmax, p["shaft_flat"] - p["shaft_d"] / 2), angle=90, **ds).render()
    for v, lab in (("front", "FRONT VIEW"), ("plan", "PLAN (TOP) VIEW"), ("side", "RIGHT SIDE VIEW (shaft end)")):
        ox, oy = off[v]
        msp.add_text(lab, height=1.4, dxfattribs={"layer": "TEXT"}).set_placement((ox + (0 if v != "side" else -r), oy + r + 2.5))
    note_y = -r - 16
    for i, line in enumerate([
        f"{p['title']} - {p['version']} - dims from listings, verify with calipers",
        "THIRD-ANGLE PROJECTION. Units: mm. Mounting holes TBC (measure) - no source shows the face pattern.",
        f"Ratio {p['ratio']}. Overall body {L_total:.1f} excl. shaft; +{p['shaft_len']} shaft.",
    ]):
        msp.add_text(line, height=1.2, dxfattribs={"layer": "TEXT"}).set_placement((xmin, note_y - i * 2.2))
    doc.saveas(os.path.join(outdir, f"{name}.dxf"))

    # ---------- PNG sheet ----------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    fig = plt.figure(figsize=(16.54, 11.69), dpi=150)  # A3 landscape
    ax_ = fig.add_axes([0.03, 0.03, 0.94, 0.94])
    ax_.set_aspect("equal"); ax_.axis("off")
    for v, (vis, hid) in views.items():
        ox, oy = off[v]
        for pl in hid:
            ax_.plot([x + ox for x, y in pl], [y + oy for x, y in pl], color="0.45", lw=0.6, ls=(0, (3, 2)))
        for pl in vis:
            ax_.plot([x + ox for x, y in pl], [y + oy for x, y in pl], color="black", lw=1.1)
    cl = dict(color="0.3", lw=0.4, ls=(0, (8, 2, 1, 2)))
    for v in ("front", "plan"):
        ox, oy = off[v]
        ax_.plot([xmin - 2 + ox, xmax + 2 + ox], [oy, oy], **cl)
    ax_.plot([sx - r - 2, sx + r + 2], [sy, sy], **cl); ax_.plot([sx, sx], [sy - r - 2, sy + r + 2], **cl)

    def hdim(x1, x2, y, yref, txt, fs=8):
        for x in (x1, x2):
            ax_.plot([x, x], [yref, y - 0.6 * (1 if y < yref else -1)], color="black", lw=0.4)
        ax_.annotate("", (x1, y), (x2, y), arrowprops=dict(arrowstyle="<->", lw=0.6, shrinkA=0, shrinkB=0))
        ax_.text((x1 + x2) / 2, y + 0.35, txt, ha="center", va="bottom", fontsize=fs)

    def vdim(y1, y2, x, xref, txt, fs=8, side="left"):
        for y in (y1, y2):
            ax_.plot([xref, x + (0.6 if x < xref else -0.6)], [y, y], color="black", lw=0.4)
        ax_.annotate("", (x, y1), (x, y2), arrowprops=dict(arrowstyle="<->", lw=0.6, shrinkA=0, shrinkB=0))
        ax_.text(x + (-0.4 if side == "left" else 0.4), (y1 + y2) / 2, txt, ha="right" if side == "left" else "left",
                 va="center", fontsize=fs, rotation=90)

    hdim(0, L_total, -r - 9, -r, f"{L_total:.1f} overall body (excl. shaft)")
    hdim(0, xg, -r - 4.5, -r, f"{p['motor_len']:.1f} motor")
    hdim(xg, L_total, -r - 4.5, -r, f"{p['gearbox_len'] + p['boss_len']:.1f} gearbox incl. collar")
    hdim(xs, xs + p["shaft_len"], -r - 4.5, -p["shaft_d"] / 2, f"{p['shaft_len']:.1f}", fs=7)
    hdim(-p["term_len"] - p["rear_boss_len"], 0, r + 3.5, r * 0.1, f"{p['term_len']:.1f} tabs [A]", fs=6.5)
    vdim(-r, r, -7, 0, f"Ø{p['body_d']:.1f}")
    vdim(-p["shaft_d"] / 2, p["shaft_flat"] - p["shaft_d"] / 2, xmax + 3.5, xmax, f"{p['shaft_flat']:.1f} D-flat", fs=7, side="right")
    # shaft diameter dimensioned on the round in the end view
    vdim(-p["shaft_d"] / 2, p["shaft_d"] / 2, sx + r + 3, sx, f"Ø{p['shaft_d']:.1f} shaft", fs=7, side="right")
    vdim(-r, r, sx - r - 3, sx - r, f"Ø{p['body_d']:.1f}", fs=7)
    # plan view callouts
    px, py = off["plan"]
    ax_.text(xs + p["shaft_len"] / 2 + px, py + r + 1.2, f"flat {p['flat_len']:.1f} long [A]", ha="center", fontsize=6.5)
    ax_.text(xb + p["boss_len"] / 2 + px, py - r - 1.8, f"collar Ø{p['boss_d']:.0f}×{p['boss_len']:.0f} [A]", ha="center", fontsize=6.5)
    ax_.text(px - p["term_len"] - 1, py + p["term_pitch"] / 2 + 1.5, f"tabs {p['term_pitch']:.0f} c/c [A]", ha="center", fontsize=6.5)
    # side view callout
    ax_.text(sx, sy - r - 2.8, "face: mounting holes TBC (measure)", ha="center", fontsize=7, style="italic")
    for v, lab in (("front", "FRONT VIEW"), ("plan", "PLAN (TOP) VIEW"), ("side", "RIGHT SIDE VIEW (shaft end)")):
        ox, oy = off[v]
        ax_.text(ox + (xmin if v != "side" else 0), oy + r + (5.5 if v != "side" else 3), lab,
                 fontsize=9, weight="bold", ha="left" if v != "side" else "center")
    # scale bar 10 mm
    sbx, sby = sx - 5, -r - 13
    for i in range(10):
        ax_.add_patch(Rectangle((sbx + i, sby), 1, 0.5, facecolor="black" if i % 2 == 0 else "white", edgecolor="black", lw=0.4))
    ax_.text(sbx, sby - 0.4, "0", ha="center", va="top", fontsize=6.5)
    ax_.text(sbx + 5, sby - 0.4, "5", ha="center", va="top", fontsize=6.5)
    ax_.text(sbx + 10, sby - 0.4, "10 mm", ha="center", va="top", fontsize=6.5)
    # title block
    tbx0, tby0 = sx - r - 3, -r - 25
    tbw, tbh = 2 * r + 30, 9.5
    ax_.add_patch(Rectangle((tbx0, tby0), tbw, tbh, fill=False, lw=0.9))
    ax_.plot([tbx0, tbx0 + tbw], [tby0 + 5.5, tby0 + 5.5], color="black", lw=0.5)
    ax_.text(tbx0 + 0.8, tby0 + 7.6, f"{p['title']} — {p['version']}", fontsize=9, weight="bold", va="center")
    ax_.text(tbx0 + 0.8, tby0 + 4.1, "Dims from listings, verify with calipers.", fontsize=7, va="center")
    ax_.text(tbx0 + 0.8, tby0 + 2.4, f"Third-angle projection · mm · ratio {p['ratio']}", fontsize=7, va="center")
    ax_.text(tbx0 + 0.8, tby0 + 0.8, "[A] = assumed, measure. Knob module v1 · EdgerEquals", fontsize=7, va="center")
    # third-angle symbol (cone): small circle pair + trapezoid
    tsx, tsy = tbx0 + tbw - 5, tby0 + 2.6
    ax_.plot([tsx - 3.2, tsx - 3.2, tsx - 1.0, tsx - 1.0, tsx - 3.2], [tsy - 0.6, tsy + 0.6, tsy + 1.3, tsy - 1.3, tsy - 0.6], color="black", lw=0.5)
    th = [i * 2 * math.pi / 60 for i in range(61)]
    for rr in (1.3, 0.6):
        ax_.plot([tsx + 1.5 + rr * math.cos(t) for t in th], [tsy + rr * math.sin(t) for t in th], color="black", lw=0.5)
    ax_.set_xlim(xmin - 12, sx + r + 30)
    ax_.set_ylim(tby0 - 3, off["plan"][1] + r + 9)
    fig.savefig(os.path.join(outdir, f"{name}-drawing.png"), facecolor="white")
    plt.close(fig)
    bb = m.bounding_box()
    print(name, "bbox", round(bb.min.X, 2), round(bb.max.X, 2), round(bb.size.Y, 2), round(bb.size.Z, 2), "vol", round(m.volume, 1))


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    for name in (sys.argv[1:] or VARIANTS):
        main(name, VARIANTS[name], here if name == "motor-1220" else os.path.join(here, name))
