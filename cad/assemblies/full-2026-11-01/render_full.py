"""Full assembly render, 1 Nov 2026.

Knob stack is this branch (sub/assembly-v017, committed v0.18 plus the faceplate).
Joystick is origin/sub/joystick-v04 at the commit recorded below, extracted with
git archive into a temp tree and imported as jsparam. The branch is not merged.
The script lives outside knobparam, so it is not a cross-sub import.

The joystick commit already carries a local faceplate proxy around its opening.
This branch's plate (faceplate_z / faceplate_t, 10HP x 3U) is added beside it.
The 405 nm module, Risley wedges and prism motors are not in the CAD. The laser
view is the dial-axis plane those notes use, with the axis drawn on.
"""
import hashlib, os, shutil, subprocess, sys, math, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
KNOB = os.path.join(ROOT, "cad", "knob-param")
JS_COMMIT = "cbc75d43e27ea6a9320dcd782bd8c00cfb8daca8"  # origin/sub/joystick-v04
sys.path.insert(0, KNOB)

from build123d import Pos, Box, Cylinder, Align, export_brep
from knobparam.common import model
from knobparam.assembly.build import build_all, PATHS
from knobparam.assembly import render as R
from knobparam.common.cache import CACHE

OUT = HERE
TOL = 0.05


def load_joystick():
    """Import jsparam from a throwaway checkout of sub/joystick-v04. Not a merge."""
    tmp = tempfile.mkdtemp(prefix="js-v04-")
    proc = subprocess.Popen(["git", "archive", JS_COMMIT, "cad/joystick-param"], cwd=ROOT, stdout=subprocess.PIPE)
    subprocess.check_call(["tar", "-x", "-C", tmp], stdin=proc.stdout)
    proc.stdout.close()
    if proc.wait() != 0:
        raise RuntimeError("git archive of sub/joystick-v04 failed")
    src = os.path.join(tmp, "cad", "joystick-param")
    link = os.path.join(tmp, "cad", "knob-param")
    if not os.path.exists(link):
        os.symlink(KNOB, link)
    sys.path.insert(0, src)
    import jsparam.params as JP
    import jsparam.parts as JParts
    return JP, JParts


def faceplate_panel(D, J):
    """10HP x 3U plate at this branch's faceplate. Knob hole and the joystick opening."""
    w, h, t = 10 * 5.08 - 0.30, 128.5, D["faceplate_t"]
    z0, z1 = D["faceplate_z_back"], D["faceplate_z"]
    y1 = D["axis_by"]
    p = Pos(0, y1 - h / 2, z0) * Box(w, h, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    p -= Pos(0, 0, z0 - 1) * Cylinder(D["knob_od"] / 2 + 0.4, t + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    hw, hh = J["hole_hw"], J["hole_hh"]
    p -= Pos(0, J["place_y"], z0 - 1) * Box(2 * hw, 2 * hh, t + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return p


def place_joystick(parts, y):
    out = {}
    skip = "main PCB (proxy, local patch)"
    for n, s in parts.items():
        if n == skip or s is None:
            continue
        out["js " + n] = Pos(0, y, 0) * s
    return out


def publish(parts, keys, tag):
    """Write extra solids where the mesh cutter can read them."""
    d = os.path.join(CACHE, "full-asm")
    os.makedirs(d, exist_ok=True)
    for n, s in parts.items():
        h = hashlib.sha1(f"{tag}|{n}".encode()).hexdigest()[:16]
        path = os.path.join(d, h + ".brep")
        if not os.path.exists(path):
            export_brep(s, path)
        PATHS[n] = path
        keys[n] = tag + h


def colour_of(n):
    rules = (
        ("assembly faceplate", "#d1c4e9"),
        ("js faceplate", "#b39ddb"),
        ("js brass standoff", "#c9a227"),
        ("js M2 nut", "#8d6e63"),
        ("js top screen", "#101828"),
        ("js screen carrier", "#ce93d8"),
        ("js joystick carrier", "#a1887f"),
        ("js seat plate", "#8d6e63"),
        ("js rear spring", "#6d4c41"),
        ("js SW1", "#424242"),
        ("js header", "#616161"),
        ("js socket", "#455a64"),
        ("js compression", "#fdd835"),
        ("js hold-down", "#fbc02d"),
        ("js grub", "#5d4037"),
        ("js brass insert", "#c9a227"),
        ("js ball", "#eceff1"),
        ("js screen FPC", "#ffb300"),
        ("js cross pin", "#90a4ae"),
    )
    for pref, col in rules:
        if n.startswith(pref):
            return col
    return None


def patch_groups():
    extra = []
    seen = set()
    for pref, col in (
        ("assembly faceplate (10HP, this branch)", "#d1c4e9"),
        ("joystick faceplate proxy (v0.4, local opening)", "#b39ddb"),
        ("joystick standoffs, nuts, inserts", "#c9a227"),
        ("joystick screen + bezel", "#101828"),
        ("joystick printed carrier, plate, anchor", "#8d6e63"),
        ("joystick switch, headers, sockets", "#424242"),
        ("joystick springs", "#fdd835"),
        ("joystick balls", "#eceff1"),
    ):
        extra.append((pref, col, lambda n, p=pref: False))
    # matchers are by colour_of; group_of below does the real test
    R.GROUPS.extend(extra)
    base = R.group_of

    def group_of(n):
        col = colour_of(n)
        if col:
            for i, (_, c, _) in enumerate(R.GROUPS):
                if c == col and i >= len(R.GROUPS) - len(extra):
                    return i
            # fall through to a dedicated slot: find first extra with this colour
        return base(n)
    # rebuild extras with real matchers so the legend can name them
    R.GROUPS = R.GROUPS[:-len(extra)]
    specs = (
        ("assembly faceplate (10HP, this branch)", "#d1c4e9", lambda n: n.startswith("assembly faceplate")),
        ("joystick faceplate proxy (v0.4)", "#b39ddb", lambda n: n.startswith("js faceplate")),
        ("joystick standoffs / nuts / inserts", "#c9a227", lambda n: n.startswith(("js brass", "js M2", "js grub"))),
        ("joystick screen + bezel", "#101828", lambda n: n.startswith(("js top screen", "js screen carrier"))),
        ("joystick printed parts", "#8d6e63", lambda n: n.startswith(("js joystick carrier", "js seat plate", "js rear spring"))),
        ("joystick switch, headers, sockets", "#424242", lambda n: n.startswith(("js SW1", "js header", "js socket"))),
        ("joystick springs / FPC", "#fdd835", lambda n: n.startswith(("js compression", "js hold-down", "js screen FPC"))),
        ("joystick balls / pins", "#eceff1", lambda n: n.startswith(("js ball", "js cross"))),
    )
    R.GROUPS.extend(specs)

    def group_of(n):
        for i, (_, _, f) in enumerate(R.GROUPS):
            if f(n):
                return i
        return len(R.GROUPS) - 1
    R.group_of = group_of


def bb_of(parts):
    bbs = [s.bounding_box() for s in parts.values()]
    pad = 4.0
    return [min(b.min.X for b in bbs) - pad, min(b.min.Y for b in bbs) - pad, min(b.min.Z for b in bbs) - pad,
            max(b.max.X for b in bbs) + pad, max(b.max.Y for b in bbs) + pad, max(b.max.Z for b in bbs) + pad]


def label(path, title, note, src):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    img = R._trim(plt.imread(src), 6)
    fig = plt.figure(figsize=(16, 12), dpi=120)
    fig.text(0.02, 0.975, title, fontsize=18, weight="bold", va="top")
    fig.text(0.02, 0.935, note, fontsize=11, va="top", color="#333333", wrap=True)
    ax = fig.add_axes([0.02, 0.03, 0.96, 0.86])
    ax.imshow(img)
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    fig.savefig(path)
    plt.close(fig)


def ortho_save(meshes, centre, cam, up, w, h, ppm, raw, out, title, note):
    R.ortho(meshes, centre, cam, up, w, h, ppm, raw, edges=True, aa=True)
    label(out, title, note, raw)


def iso_cam(meshes, size, path, direction, up):
    pv = R._pv()
    pl = pv.Plotter(off_screen=True, window_size=(size, size))
    pl.set_background("white")
    R._add(pl, pv, meshes, 1.3, True)
    lo, hi = R._bbox(meshes)
    c = (lo + hi) / 2
    d = np.array(direction, float)
    d /= np.linalg.norm(d)
    pl.camera.position = tuple(c + 500 * d)
    pl.camera.focal_point = tuple(c)
    pl.camera.up = up
    pl.enable_parallel_projection()
    pl.reset_camera()
    pl.camera.zoom(1.15)
    R._shot(pl, path, True)
    return path


def main():
    os.makedirs(OUT, exist_ok=True)
    raw = os.path.join(OUT, "_raw")
    os.makedirs(raw, exist_ok=True)
    print("deriving knob", flush=True)
    D = model.derive(model.default_params())
    print("building knob", flush=True)
    parts, stats, keys, _ = build_all(D)
    print(f"knob parts {len(parts)}", flush=True)
    print("loading joystick", JS_COMMIT[:12], flush=True)
    JP, JParts = load_joystick()
    J = JP.derive(JP.P)
    js_local = JParts.build(J)
    js = place_joystick(js_local, J["place_y"])
    panel = faceplate_panel(D, J)
    extra = dict(js)
    extra["assembly faceplate (10HP x 3U)"] = panel
    publish(extra, keys, "asm")
    parts.update(extra)
    if D.get("hv_cross_travel") is None:
        D["hv_cross_travel"] = D["hv_cross"]
    patch_groups()
    BB = [round(v, 1) for v in bb_of(parts)]
    note_js = (f"Joystick {J['version']} from sub/joystick-v04 {JS_COMMIT[:12]}, placed at y {J['place_y']:.2f}, not merged. "
               f"Its own plate is z {J['z_fp0']:.2f}–{J['z_fp1']:.2f}. This branch's plate is z {D['faceplate_z_back']:.2f}–{D['faceplate_z']:.2f}.")
    # usual colour sheet (A-A + iso quarter + insets) and the clean sheet
    from knobparam.assembly.render import render
    colour = os.path.join(OUT, "full-2026-11-01-colour.png")
    clean = os.path.join(OUT, "full-2026-11-01-clean.png")
    print("colour render", flush=True)
    render(D, parts, keys, colour, preview=False, clash_lines=[note_js], gap_lines=[],
           title="Full assembly 2026-11-01 — knob v0.18 + joystick v0.4 + faceplate")
    print("clean render", flush=True)
    render(D, parts, keys, clean, clean=True, title="Full assembly 2026-11-01 — clean",
           note=note_js)
    # sections
    z0, z1 = BB[2], BB[5]
    span_x, span_y = BB[3] - BB[0], BB[4] - BB[1]
    span_z = z1 - z0
    print("section X (y = 0)", flush=True)
    mX = R.cut_meshes(parts, keys, dict(kind="half", bb=BB), TOL)
    lo, hi = R._bbox(mX)
    ortho_save(mX, ((lo[0] + hi[0]) / 2, 0, (lo[2] + hi[2]) / 2), (0, 1, 0), (0, 0, 1),
               hi[0] - lo[0] + 2, hi[2] - lo[2] + 2, 18, f"{raw}/sx.png",
               os.path.join(OUT, "full-2026-11-01-section-x.png"),
               "SECTION X through the centre (plane y = 0, viewed from +Y)",
               "Dial axis and the 1220 (+X, left in this view is +X). " + note_js)
    print("section Y (x = 0)", flush=True)
    mY = R.cut_meshes(parts, keys, dict(kind="box", o=(0.0, 0.0), a=-90.0, u=(-span_y, span_y), depth=span_x, z=(z0, z1)), TOL)
    lo, hi = R._bbox(mY)
    ortho_save(mY, (0, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2), (1, 0, 0), (0, 0, 1),
               hi[1] - lo[1] + 2, hi[2] - lo[2] + 2, 14, f"{raw}/sy.png",
               os.path.join(OUT, "full-2026-11-01-section-y.png"),
               "SECTION Y through the centre (plane x = 0, viewed from +X)",
               "Encoder is on -Y. The joystick sits on +Y. " + note_js)
    print("section joystick", flush=True)
    py = float(J["place_y"])
    # Stop short of the knob (the carrier centre is ~15 mm clear of the skirt) so the section is the joystick.
    mJ = R.cut_meshes(parts, keys, dict(kind="box", o=(0.0, py), a=0.0, u=(-40.0, 40.0), depth=12.0, z=(z0, z1)), TOL)
    lo, hi = R._bbox(mJ)
    ortho_save(mJ, ((lo[0] + hi[0]) / 2, py, (lo[2] + hi[2]) / 2), (0, 1, 0), (0, 0, 1),
               max(hi[0] - lo[0], 20) + 2, hi[2] - lo[2] + 2, 16, f"{raw}/sj.png",
               os.path.join(OUT, "full-2026-11-01-section-joystick.png"),
               f"SECTION through the joystick (plane y = {py:.2f}, viewed from +Y)",
               "Switch on the carrier axis, four M2 standoffs, screen and the v0.4 faceplate proxy. " + note_js)
    print("section laser axis", flush=True)
    def axis_line(pl, pv):
        pl.add_lines(np.array([[0, 0.4, D["z_pcb_back"]], [0, 0.4, D["z_top"] + 2]]), color="#d50000", width=4)
    R.ortho(mX, (0, 0, (D["z_pcb_back"] + D["z_top"]) / 2), (0, 1, 0), (0, 0, 1),
            D["knob_od"] + 18, D["z_top"] - D["z_pcb_back"] + 8, 22, f"{raw}/sl.png", extra=axis_line, edges=True, aa=True)
    label(os.path.join(OUT, "full-2026-11-01-section-laser.png"),
          "SECTION through the documented laser / Risley axis (plane y = 0)",
          "No Risley wedge, prism motor or 405 nm body is in the CAD (the optics round is not built). "
          "The red line is the dial axis those notes use for the down-firing beam. " + note_js,
          f"{raw}/sl.png")
    print("quarter isos", flush=True)
    fang = float(D.get("fm_ang", 90.0)) % 360.0
    a0, a1 = (0.0, fang) if fang <= 180.0 else (fang, 360.0)
    mQ = R.cut_meshes(parts, keys, dict(kind="quarter", bb=BB, a0=a0, a1=a1), TOL)
    hidden = [n for n in parts if n not in mQ]
    if hidden:
        mQ.update(R.cut_meshes({n: parts[n] for n in hidden}, keys, dict(kind="whole", bb=BB), TOL))
    above = f"{raw}/above.png"
    below = f"{raw}/below.png"
    iso_cam(mQ, 1600, above, (0.85, 0.85, 1.35), (0, 1, 0))
    iso_cam(mQ, 1600, below, (0.85, 0.85, -1.35), (0, 1, 0))
    label(os.path.join(OUT, "full-2026-11-01-iso-above.png"),
          "QUARTER CUT-AWAY, isometric from above",
          f"Wedge from the motor plane to the feel-motor plane ({fang:.0f}°). " + note_js, above)
    label(os.path.join(OUT, "full-2026-11-01-iso-below.png"),
          "QUARTER CUT-AWAY, isometric from below",
          "Same cut, camera under the PCB. Encoder stack and the joystick standoff studs are on this side. " + note_js, below)
    print("plan", flush=True)
    plan(D, J, parts, keys)
    print("exploded", flush=True)
    exploded = explode(parts, D, J)
    publish(exploded, keys, "expl")
    eBB = [round(v, 1) for v in bb_of(exploded)]
    mE = R.cut_meshes(exploded, keys, dict(kind="whole", bb=eBB), TOL)
    exp = f"{raw}/expl.png"
    iso_cam(mE, 1700, exp, (1.0, 1.0, 0.85), (0, 0, 1))
    label(os.path.join(OUT, "full-2026-11-01-exploded.png"),
          "EXPLODED (along Z; joystick shifted +Y as well)",
          "From the bottom: under-PCB, main PCB, cradle and gears, knob and dial, joystick, this branch's faceplate. " + note_js, exp)
    shutil.rmtree(raw, ignore_errors=True)
    print("done", flush=True)


def explode(parts, D, J):
    """Copies. Under-PCB drops, the knob lifts, the joystick steps out on +Y, the plate lifts clear."""
    out = {}
    py = float(J["place_y"])
    for n, s in parts.items():
        dz, dy = 0.0, 0.0
        if n.startswith("assembly faceplate"):
            dz = 55.0
        elif n.startswith("js "):
            dz, dy = 28.0, 18.0
        elif n.startswith(("knob", "bottom internal", "control dial", "dial ", "screen ", "adapter", "screen holder", "hall magnet")):
            dz = 36.0
        elif n.startswith(("PCB", "hall sensor", "PCB rod")):
            dz = 0.0
        elif n.startswith(("encoder disc", "encoder sensor", "encoder daughter", "encoder header", "encoder standoff", "encoder bearing 2")):
            dz = -22.0
        else:
            dz = 14.0
        out[n] = Pos(0, dy, dz) * s
    return out


def plan(D, J, parts, keys):
    """Three horizontal slices: PCB front, gear band, faceplate height."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection, LineCollection
    from matplotlib.patches import Patch, Circle
    from build123d import Pos, Box, Align
    from knobparam.common.cache import load
    zs = (0.4, 8.0, (D["faceplate_z_back"] + D["faceplate_z"]) / 2)
    titles = (
        f"PLAN at z = {zs[0]:.2f}: PCB front, Hall row, joystick sockets and standoff feet",
        f"PLAN at z = {zs[1]:.2f}: cradle, gears, feel motor",
        f"PLAN at z = {zs[2]:.2f}: this branch's faceplate (hole Ø{D['knob_od'] + 0.8:.1f}) and the joystick opening",
    )
    slices = {}
    for z in zs:
        cutter = Pos(-120, -40, z) * Box(240, 220, 1e-3, align=(Align.MIN, Align.MIN, Align.CENTER))
        slices[z] = {}
        for n in parts:
            s = load(PATHS[n])
            b = s.bounding_box()
            if not (b.min.Z < z < b.max.Z):
                continue
            try:
                r = s.intersect(cutter)
            except Exception:
                continue
            if r is None or not r.solids() and not r.faces():
                continue
            tris, segs = [], []
            faces = r.faces() if hasattr(r, "faces") else []
            for fc in faces:
                if abs(fc.normal_at(fc.center()).Z) < 0.9:
                    continue
                try:
                    vs, T = fc.tessellate(0.08, 0.3)
                except Exception:
                    continue
                P = np.array([(v.X, v.Y) for v in vs])
                tris += [P[list(t)] for t in T]
                for e in fc.edges():
                    pts = [(p.X, p.Y) for p in e.positions(np.linspace(0, 1, 12))]
                    segs.append(np.array(pts))
            if tris or segs:
                slices[z][n] = (tris, segs)
    fig, axs = plt.subplots(1, 3, figsize=(24, 12), dpi=110)
    py = J["place_y"]
    for ax, z, ttl in zip(axs, zs, titles):
        for n, (tris, segs) in slices[z].items():
            col = R.GROUPS[R.group_of(n)][1]
            if tris:
                ax.add_collection(PolyCollection(tris, facecolors=R.lighten(col, 0.3), edgecolors="none", linewidths=0))
            if segs:
                ax.add_collection(LineCollection(segs, colors="#202020", linewidths=0.4))
        ax.add_patch(Circle((0, 0), D["knob_od"] / 2, fill=False, ls=":", lw=1.0, ec="#1565c0"))
        ax.plot(0, 0, "k+", ms=8)
        ax.plot(0, py, "k+", ms=8)
        ax.set_aspect("equal")
        ax.set_xlim(-30, 30)
        ax.set_ylim(-30, py + 28)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(ttl, fontsize=11, loc="left", weight="bold")
    fig.suptitle(f"Full assembly plan, looking down +Z  ·  knob {D['version']}  ·  joystick at y {py:.1f}",
                 fontsize=16, weight="bold", x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.02, 1, 0.94))
    fig.savefig(os.path.join(OUT, "full-2026-11-01-plan.png"))
    plt.close(fig)


if __name__ == "__main__":
    main()
