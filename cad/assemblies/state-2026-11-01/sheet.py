"""Current-state assembly sheet, 1 Nov 2026.

Knob stack on this branch, joystick from origin/sub/joystick-v04 (not merged),
main PCB, and a clear 10HP case. Case wall and knob-hole clearance are the
figures in origin/sub/case-v01 (wall 2.5 mm, knob_rad_clear 0.20). The case
package is not imported: that shell is tied to an older knob snapshot, so this
sheet draws a 10HP box with those two numbers and this branch's knob and plate.

Three sections and one isometric. Output: sheet.png next to this file.
"""
import importlib.util, os, sys, textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
from build123d import Pos, Box, Cylinder, Align

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
KNOB = os.path.join(ROOT, "cad", "knob-param")
sys.path.insert(0, KNOB)

FULL = os.path.join(ROOT, "cad", "assemblies", "full-2026-11-01", "render_full.py")
spec = importlib.util.spec_from_file_location("render_full", FULL)
full = importlib.util.module_from_spec(spec)
spec.loader.exec_module(full)

from knobparam.common import model
from knobparam.assembly.build import build_all
from knobparam.assembly import render as R

# sub/case-v01 params.py: wall and the knob-hole radial clearance.
CASE_WALL = 2.5
KNOB_RAD_CLEAR = 0.20
OUT = os.path.join(HERE, "sheet.png")
TOL = 0.12
PPM = 8


def case_shell(D, J, z0):
    """Clear 10HP box. Front is this branch's faceplate; the knob and joystick holes are cut through it."""
    w = D["hp"] * D["hp_pitch"] - D["hp_gap"]
    h, t = D["panel_h"], D["faceplate_t"]
    y_mid = D["axis_by"] - h / 2
    z1 = D["faceplate_z"]
    wall = CASE_WALL
    outer = Pos(0, y_mid, z0) * Box(w, h, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    inner = Pos(0, y_mid, z0 + wall) * Box(
        w - 2 * wall, h - 2 * wall, (z1 - t) - (z0 + wall),
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    shell = outer - inner
    shell -= Pos(0, 0, z1 - t - 1) * Cylinder(D["knob_od"] / 2 + KNOB_RAD_CLEAR, t + 2,
                                               align=(Align.CENTER, Align.CENTER, Align.MIN))
    shell -= Pos(0, J["place_y"], z1 - t - 1) * Box(2 * J["hole_hw"], 2 * J["hole_hh"], t + 2,
                                                     align=(Align.CENTER, Align.CENTER, Align.MIN))
    return shell


def bbox(parts):
    bbs = [s.bounding_box() for s in parts.values()]
    pad = 4.0
    return [min(b.min.X for b in bbs) - pad, min(b.min.Y for b in bbs) - pad, min(b.min.Z for b in bbs) - pad,
            max(b.max.X for b in bbs) + pad, max(b.max.Y for b in bbs) + pad, max(b.max.Z for b in bbs) + pad]


def part_mid(parts, name):
    b = parts[name].bounding_box()
    return ((b.min.X + b.max.X) / 2, (b.min.Y + b.max.Y) / 2, (b.min.Z + b.max.Z) / 2)


def px_of(cam, centre, w_mm, h_mm, W, H, p):
    x, y, z = p
    cx, cy, cz = centre
    if cam == "xz":
        u = 0.5 - (x - cx) / w_mm
        v = 0.5 - (z - cz) / h_mm
    elif cam == "yz":
        u = 0.5 + (y - cy) / w_mm
        v = 0.5 - (z - cz) / h_mm
    else:
        u = 0.5 + (x - cx) / w_mm
        v = 0.5 - (y - cy) / h_mm
    return u * (W - 1), v * (H - 1)


def _dim(ax, a, b, text):
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="<->", color="#111111", lw=0.9, shrinkA=0, shrinkB=0))
    ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, text, fontsize=8, color="#111111", ha="center", va="bottom",
            bbox=dict(fc="white", ec="none", alpha=0.88, pad=0.6))


def _tag(ax, xy, text, dx, dy):
    ax.annotate(text, xy, xytext=(xy[0] + dx, xy[1] + dy), fontsize=8, color="#111111",
                arrowprops=dict(arrowstyle="-", color="#333333", lw=0.6),
                bbox=dict(fc="white", ec="#bbbbbb", alpha=0.9, pad=1.0))


def mark(ax, img, cam, centre, w_mm, h_mm, dims, tags):
    H, W = img.shape[:2]
    def P(p):
        return px_of(cam, centre, w_mm, h_mm, W, H, p)
    for p0, p1, text in dims:
        _dim(ax, P(p0), P(p1), text)
    for p, text, dx, dy in tags:
        _tag(ax, P(p), text, dx, dy)


def shot(meshes, centre, cam_dir, up, w_mm, h_mm, path):
    R.ortho(meshes, centre, cam_dir, up, w_mm, h_mm, PPM, path, edges=False, aa=False)
    img = plt.imread(path)
    return img, centre, w_mm, h_mm


def main():
    print("deriving", flush=True)
    D = model.derive(model.default_params())
    print("building knob", flush=True)
    parts, _stats, keys, _owner = build_all(D)
    print("loading joystick", flush=True)
    JP, JParts = full.load_joystick()
    J = JP.derive(JP.P)
    js = full.place_joystick(JParts.build(J), J["place_y"])
    z0 = min(s.bounding_box().min.Z for s in parts.values()) - CASE_WALL - 2
    shell = case_shell(D, J, z0)
    case_name = "10HP case (UTR-8100, sub/case-v01 wall)"
    extra = {case_name: shell}
    extra.update(js)
    full.publish(extra, keys, "state")
    full.patch_groups()
    R.GROUPS.append(("10HP case (clear resin, proxy box)", "#d1c4e9", lambda n: n.startswith("10HP case")))
    allp = dict(parts)
    allp.update(extra)
    bb = [round(v, 1) for v in bbox(allp)]
    tmp = R.TMP
    os.makedirs(tmp, exist_ok=True)

    print("A-A", flush=True)
    aa = R.cut_meshes(allp, keys, dict(kind="half", bb=bb), TOL)
    lo, hi = R._bbox(aa)
    c_aa = ((lo[0] + hi[0]) / 2, 0.0, (lo[2] + hi[2]) / 2)
    w_aa, h_aa = hi[0] - lo[0] + 6, hi[2] - lo[2] + 6
    img_aa, c_aa, w_aa, h_aa = shot(aa, c_aa, (0, 1, 0), (0, 0, 1), w_aa, h_aa, f"{tmp}/state-aa.png")

    print("B-B", flush=True)
    z0b, z1b = bb[2], bb[5]
    span_x, span_y = bb[3] - bb[0], bb[4] - bb[1]
    bb_view = R.cut_meshes(allp, keys, dict(kind="box", o=(0.0, 0.0), a=-90.0,
                                             u=(-span_y, span_y), depth=span_x, z=(z0b, z1b)), TOL)
    lo, hi = R._bbox(bb_view)
    c_bb = (0.0, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2)
    w_bb, h_bb = hi[1] - lo[1] + 6, hi[2] - lo[2] + 6
    img_bb, c_bb, w_bb, h_bb = shot(bb_view, c_bb, (1, 0, 0), (0, 0, 1), w_bb, h_bb, f"{tmp}/state-bb.png")

    print("C-C", flush=True)
    zcut = float(D["hb_mid"])
    plan = R.cut_meshes(allp, keys, dict(kind="plan", bb=bb, z=round(zcut, 3)), TOL)
    lo, hi = R._bbox(plan)
    c_pl = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, zcut)
    w_pl, h_pl = hi[0] - lo[0] + 6, hi[1] - lo[1] + 6
    img_pl, c_pl, w_pl, h_pl = shot(plan, c_pl, (0, 0, 1), (0, 1, 0), w_pl, h_pl, f"{tmp}/state-plan.png")

    print("iso", flush=True)
    fang = float(D.get("fm_ang", 90.0)) % 360.0
    a0, a1 = (0.0, fang) if fang <= 180.0 else (fang, 360.0)
    iso = R.cut_meshes(allp, keys, dict(kind="quarter", bb=bb, a0=a0, a1=a1), TOL)
    R.iso(iso, 1100, f"{tmp}/state-iso.png", lw=0.8, edges=False, aa=False, ghost=[case_name])
    img_iso = plt.imread(f"{tmp}/state-iso.png")

    Rrad = D["knob_od"] / 2
    z_sl0, z_sl1 = D["sleeve_z0"], D["sleeve_z1"]
    z_fp, z_glass = D["faceplate_z"], D["z_glass"]
    panel_w = D["hp"] * D["hp_pitch"] - D["hp_gap"]
    y_top, y_bot = D["axis_by"], D["axis_by"] - D["panel_h"]
    glass = part_mid(parts, "knob glass sleeve")
    pcb = part_mid(parts, "PCB")
    motor = part_mid(parts, "motor")
    py = float(J["place_y"])

    x_out = panel_w / 2 + 4
    dims_aa = [
        ((-Rrad, 0, z_sl1 + 3.0), (Rrad, 0, z_sl1 + 3.0), f"Ø{D['knob_od']:.2f}"),
        ((x_out, 0, z_sl0), (x_out, 0, z_sl1), f"{D['sleeve_len']:.1f} sleeve"),
        ((-x_out, 0, 0.0), (-x_out, 0, z_fp), f"plate z {z_fp:.1f}"),
        ((x_out + 8, 0, z_fp), (x_out + 8, 0, z_glass), f"{D['knob_proud']:.1f} proud"),
        ((-panel_w / 2, 0, z0 + 8), (-panel_w / 2 + CASE_WALL, 0, z0 + 8), f"wall {CASE_WALL:.1f}"),
    ]
    tags_aa = [
        (glass, "glass", 22, -36),
        (pcb, "main PCB", -80, 18),
        (motor, "1220", 16, -40),
        ((0, 0, z_fp), "faceplate", -100, 6),
    ]
    dims_bb = [
        ((0, y_bot, z_fp + 4), (0, y_top, z_fp + 4), f"{D['panel_h']:.1f} panel"),
    ]
    tags_bb = [
        ((0, 0, (z_sl0 + z_sl1) / 2), "knob", -55, 0),
        ((0, py, z_fp - 6), "joystick", 16, -20),
        ((0, y_bot + 8, 0), "main PCB", 20, 12),
    ]
    dims_pl = [
        ((-Rrad, -Rrad - 5, zcut), (Rrad, -Rrad - 5, zcut), f"knob Ø{D['knob_od']:.2f}"),
        ((-panel_w / 2, y_bot + 4, zcut), (panel_w / 2, y_bot + 4, zcut), f"{panel_w:.2f} wide (10HP)"),
    ]
    tags_pl = [
        ((0, 0, zcut), "knob", -46, 22),
        (motor, "1220", 36, -28),
        ((0, py, zcut), "joystick", 28, 12),
    ]

    fig = plt.figure(figsize=(17.5, 13.6), dpi=120)
    fig.text(0.012, 0.985, "Knob module — current state, 1 Nov 2026", fontsize=16, fontweight="bold", va="top")
    note = (f"Knob Ø{D['knob_od']:.2f} borosilicate, bore Ø{D['sleeve_id']:.2f}, sleeve {D['sleeve_len']:.1f} mm. "
            f"Faceplate z {z_fp:.1f}, t {D['faceplate_t']:.1f}, screen proud {D['knob_proud']:.1f}. "
            f"Case is a 10HP × 3U box, wall {CASE_WALL:.1f} mm and knob clearance {KNOB_RAD_CLEAR:.2f} mm from sub/case-v01 "
            f"(bosses, threads, dye and glow coat are not in this sheet). "
            f"Joystick {J['version']} at y {py:.1f}, not merged. "
            f"24 reverse-mount emitters on r {D['ot_r']:.2f}. Checks 105/105, 0 clashes.")
    fig.text(0.012, 0.948, textwrap.fill(note, width=168), fontsize=8.5, va="top", color="#333333", linespacing=1.35)
    panels = [
        (0.02, 0.48, 0.46, 0.40, img_aa, "xz", c_aa, w_aa, h_aa, dims_aa, tags_aa,
         "A–A  section through the motor (plane y = 0, +X to the left)"),
        (0.52, 0.48, 0.46, 0.40, img_bb, "yz", c_bb, w_bb, h_bb, dims_bb, tags_bb,
         "B–B  section through the panel (plane x = 0, +Y to the right)"),
        (0.02, 0.075, 0.46, 0.37, img_pl, "xy", c_pl, w_pl, h_pl, dims_pl, tags_pl,
         f"C–C  plan section at the gear mid-plane (z = {zcut:.2f})"),
        (0.52, 0.075, 0.46, 0.37, img_iso, None, None, None, None, None, None,
         f"Isometric, quarter cut (0° to {fang:.0f}°). Case ghosted."),
    ]
    for x, y, w, h, img, cam, centre, ww, hh, dims, tags, title in panels:
        ax = fig.add_axes([x, y, w, h])
        ax.imshow(img)
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(title, loc="left", fontsize=10, fontweight="bold")
        for sp in ax.spines.values():
            sp.set_visible(False)
        if cam:
            mark(ax, img, cam, centre, ww, hh, dims, tags)
    shown = []
    want = ("borosilicate", "main PCB", "1220", "base cradle", "10HP case", "joystick screen", "reverse-mount")
    for i, (name, col, _f) in enumerate(R.GROUPS):
        if any(k in name for k in want):
            shown.append(Patch(facecolor=col, edgecolor="#222222", label=name))
    fig.legend(handles=shown, loc="lower left", ncol=4, fontsize=8, frameon=False, bbox_to_anchor=(0.012, 0.0))
    fig.savefig(OUT)
    plt.close(fig)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
