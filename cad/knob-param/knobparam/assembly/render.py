"""(assembly) Colour sections PNG. Full: A-A (left), iso quarter cut (right), insets B-B / C-C / D / E along the bottom (~3000 px).
Preview: low-res A-A + iso only (~1500 px). Cut meshes are computed in parallel and cached per (part hash, region, tolerance)."""
import hashlib, json, math, os, time
from multiprocessing import get_context
import numpy as np
from build123d import *
from ..common.cache import CACHE

GROUPS = [  # (legend, colour, match)
    ("clear resin cap (UTR-8100, Fresnel)", "#80deea", lambda n: n.endswith(" cap")),
    ("rod VBUS pad, B.Cu (enlarged, no washer)", "#d4883a", lambda n: n.startswith("PCB rod pad")),
    ("main PCB (proxy; --full = KiCad STEP)", "#2e7d32", lambda n: n.startswith("PCB")),
    ("1220 motor", "#9e9e9e", lambda n: n == "motor"),
    ("motor pinion", "#ff7043", lambda n: n == "pinion"),
    ("brass tube", "#c9a227", lambda n: n == "brass tube"),
    ("M1.6 rod + sleeve, nuts, washer", "#5c6bc0", lambda n: n.startswith("rod")),
    ("base cradle", "#8d6e63", lambda n: n == "base cradle"),
    ("big knob body + hub gear", "#1e88e5", lambda n: n.startswith("knob body")),
    ("bottom internal ring", "#42a5f5", lambda n: n.startswith("bottom internal ring")),
    ("knob balls (opposed 45° cones)", "#bdbdbd", lambda n: n.startswith("knob balls")),
    ("control dial (+ Hall arm)", "#ab47bc", lambda n: n == "control dial"),
    ("magnets (Hall row N/S/N/S/N, carrier pair) N52", "#e53935", lambda n: n.startswith(("dial magnet", "hall magnet", "knob ring magnet", "cushion magnet", "screen carrier magnet"))),
    ("dial TMAG5273 sensor board (turns with the dial)", "#2f6b2f", lambda n: n.startswith(("dial sensor board", "dial TMAG5273"))),
    ("detent balls, track balls, steel pins + disc", "#cfd8dc", lambda n: (n.startswith("detent") and " ball" in n) or n.startswith(("track ball", "spring anchor pin", "screen carrier steel", "screen carrier locating"))),
    ("detent springs, grub screws, centring springs (non-magnetic)", "#fdd835", lambda n: n.startswith(("detent", "centring spring"))),
    ("Hall sensors on the PCB front", "#212121", lambda n: n.startswith("hall sensor")),
    ("thrust carrier + balls", "#78909c", lambda n: n.startswith("thrust") or n.startswith("outer thrust")),
    ("encoder bearings + shaft", "#607d8b", lambda n: n.startswith(("encoder bearing", "encoder shaft"))),
    ("encoder pinion", "#ffa726", lambda n: n == "encoder pinion"),
    ("encoder disc + slotted rim (no teeth)", "#26a69a", lambda n: n.startswith("encoder disc")),
    ("encoder sensor EE-SX1321 + riser", "#37474f", lambda n: n.startswith(("encoder sensor", "encoder daughter", "encoder header", "encoder standoff"))),
    ("idler pinions + pin 2", "#ff8a65", lambda n: n.startswith("idler")),
    ("feel motor + shaft [A]", "#00838f", lambda n: (n.startswith("feel motor") or n.startswith("feel compound") or n.startswith("feel pinion")) and "saddle" not in n),
    ("feel motor open saddle (seat + strap) [A]", "#80deea", lambda n: n.startswith("feel motor saddle")),
    ("screen holder (fixed, plate under the panel)", "#6d4c41", lambda n: n == "screen holder"),
    ("adapter cup (fixed, on the tube)", "#6d4c41", lambda n: n == "adapter cup (fixed)"),
    ("screen carrier (bonded on the dial, turns with it)", "#ce93d8", lambda n: n == "screen carrier (on dial)"),
    ("screen panel", "#101828", lambda n: n.startswith("screen ") and n.endswith(" panel")),
    ("screen FPC fold + B2B + service strap / jumper [A]", "#ffb300", lambda n: n.startswith("screen ") and ("FPC" in n)),
    ("screen adapter board + parts", "#558b2f", lambda n: n.startswith("adapter")),
]
def group_of(n):
    for i, (_, c, f) in enumerate(GROUPS):
        if f(n): return i
    return len(GROUPS) - 1
def lighten(hexc, k=0.45):
    h = hexc.lstrip("#"); r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % tuple(int(v + (255 - v) * k) for v in (r, g, b))

# ---- regions: box in a local frame (origin o, angle a about Z); keep local v in [-depth, 0]; cut plane local v = 0 ----
def region_solid(spec):
    if spec["kind"] == "whole":   # no cut (parts lying wholly in a cut-away region, --clean)
        x0, y0, z0, x1, y1, z1 = spec["bb"]
        return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=(Align.MIN,) * 3)
    if spec["kind"] == "half":
        x0, y0, z0, x1, y1, z1 = spec["bb"]
        if spec.get("opp"): return Pos(x0, 0, z0) * Box(x1 - x0, y1, z1 - z0, align=(Align.MIN,) * 3)
        return Pos(x0, y0, z0) * Box(x1 - x0, -y0, z1 - z0, align=(Align.MIN,) * 3)
    if spec["kind"] == "quarter":
        # wedge between A-A (angle a0, the 1220) and the feel-motor radial plane (a1), so the iso cuts the 716 on its axis
        x0, y0, z0, x1, y1, z1 = spec["bb"]
        allb = Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=(Align.MIN,) * 3)
        a0, a1 = spec.get("a0", 0.0), spec.get("a1", 90.0)
        if spec.get("opp"): a0, a1 = a0 + 180.0, a1 + 180.0
        r = max(math.hypot(x, y) for x in (x0, x1) for y in (y0, y1)) + 2.0
        n = 64
        pts = [(r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
        pts.append((0.0, 0.0))
        wedge = Pos(0, 0, z0) * extrude(Face(Wire.make_polygon([Vector(x, y, 0) for x, y in pts], close=True)), z1 - z0)
        return allb - wedge
    o, a, (u0, u1), depth, (z0, z1) = spec["o"], spec["a"], spec["u"], spec["depth"], spec["z"]
    return Pos(o[0], o[1], z0) * Rot(0, 0, a) * Pos(u0, -depth, 0) * Box(u1 - u0, depth, z1 - z0, align=(Align.MIN,) * 3)

def cut_planes(spec):
    if spec["kind"] == "whole": return []
    if spec["kind"] == "half": return [((0, 0, 0), (0, 1, 0))]
    if spec["kind"] == "quarter":
        def _n(a):
            a = math.radians(a); return (-math.sin(a), math.cos(a), 0.0)
        return [((0, 0, 0), _n(spec.get("a0", 0.0))), ((0, 0, 0), _n(spec.get("a1", 90.0)))]
    a = math.radians(spec["a"]); return [((spec["o"][0], spec["o"][1], 0), (-math.sin(a), math.cos(a), 0))]

def _solids(s):
    if s is None: return []
    if isinstance(s, (list, ShapeList)): return [x for i in s for x in _solids(i)]
    return [x for x in s.solids()] if hasattr(s, "solids") else []

def _mesh(solids, planes, tol):
    out = {True: ([], []), False: ([], [])}
    for so in solids:
        for f in so.faces():
            try: vs, tris = f.tessellate(tol, 0.3)
            except Exception: continue
            if not tris: continue
            is_cut = False
            if f.geom_type == GeomType.PLANE:
                c = f.center(); nrm = f.normal_at(c)
                for o, nv in planes:
                    nv = Vector(*nv)
                    if abs((c - Vector(*o)).dot(nv)) < 1e-3 and abs(abs(nrm.dot(nv)) - 1) < 1e-6: is_cut = True; break
            P, T = out[is_cut]; off = len(P)
            P += [(v.X, v.Y, v.Z) for v in vs]; T += [(off + a, off + b, off + d) for a, b, d in tris]
    return {k: (np.array(P, float), np.array(T, np.int64)) for k, (P, T) in out.items() if P}

def _cut_work(job):
    from ..common.cache import load
    name, path, spec, tol = job
    s = load(path); reg = region_solid(spec)
    bs, br = s.bounding_box(), reg.bounding_box()
    if not all(tuple(bs.min)[i] < tuple(br.max)[i] and tuple(br.min)[i] < tuple(bs.max)[i] for i in range(3)): return name, {}
    try: r = _solids(s.intersect(reg))
    except Exception: r = []
    return name, (_mesh(r, cut_planes(spec), tol) if r else {})

def cut_meshes(parts, keys, spec, tol, procs=8):
    """{name: {True: (P,T) cut faces, False: (P,T) other faces}} for every part meeting the region (cached)."""
    d = os.path.join(CACHE, "mesh"); os.makedirs(d, exist_ok=True)
    sk = hashlib.sha1(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:10]
    res, todo = {}, []
    for n in parts:
        f = os.path.join(d, hashlib.sha1(f"{keys[n]}|{sk}|{tol}".encode()).hexdigest()[:20] + ".npz")
        if os.path.exists(f):
            z = np.load(f); m = {}
            for k in (True, False):
                if f"P{int(k)}" in z: m[k] = (z[f"P{int(k)}"], z[f"T{int(k)}"])
            if m: res[n] = m
        else: todo.append((n, f))
    if todo:
        from .build import PATHS
        from ..common.cache import pool
        ft = dict(todo)
        for n, m in pool(procs).imap_unordered(_cut_work, [(n, PATHS[n], spec, tol) for n, _ in todo]):
            np.savez(ft[n], **{f"{a}{int(k)}": v for k, (P, T) in m.items() for a, v in (("P", P), ("T", T))})
            if m: res[n] = m
    return res

# ---- pyvista ----
def _pv():
    import pyvista as pv; pv.OFF_SCREEN = True; return pv
def _poly(pv, P, T): return pv.PolyData(P, np.hstack([np.full((len(T), 1), 3), T]).ravel())

def _add(pl, pv, meshes, lw=1.4, edges=True, ghost=()):
    for n, m in meshes.items():
        col = GROUPS[group_of(n)][1]
        if False in m:
            pm = _poly(pv, *m[False])
            pl.add_mesh(pm, color=col, smooth_shading=False, specular=0.1, ambient=0.3, diffuse=0.75, opacity=0.45 if n in ghost else 1.0)
            if edges:
                fe = pm.clean().extract_feature_edges(feature_angle=35, boundary_edges=False, non_manifold_edges=False, manifold_edges=False)
                if fe.n_points: pl.add_mesh(fe, color="#303030", line_width=lw * 0.7)
        if True in m:
            pm = _poly(pv, *m[True]); pl.add_mesh(pm, color=lighten(col), smooth_shading=False, ambient=0.5, diffuse=0.6)
            be = pm.clean().extract_feature_edges(boundary_edges=True, feature_edges=False, non_manifold_edges=False, manifold_edges=False)
            if be.n_points: pl.add_mesh(be, color="#101010", line_width=lw)

def _shot(pl, path, aa=True):
    if aa: pl.enable_anti_aliasing("ssaa")
    pl.screenshot(path); pl.close(); return path

def _bbox(meshes):
    P = np.vstack([p for m in meshes.values() for (p, _) in m.values()]); return P.min(0), P.max(0)

def ortho(meshes, centre, cam_dir, up, w_mm, h_mm, ppm, path, extra=None, lw=1.4, edges=True, aa=True):
    pv = _pv(); W, H = max(int(w_mm * ppm), 50), max(int(h_mm * ppm), 50)
    pl = pv.Plotter(off_screen=True, window_size=(W, H)); pl.set_background("white")
    _add(pl, pv, meshes, lw, edges)
    if extra: extra(pl, pv)
    c = np.array(centre, float); d = np.array(cam_dir, float); d /= np.linalg.norm(d)
    pl.camera.position = tuple(c + 500 * d); pl.camera.focal_point = tuple(c); pl.camera.up = up
    pl.enable_parallel_projection(); pl.camera.parallel_scale = h_mm / 2; pl.camera.clipping_range = (1, 2000)
    return _shot(pl, path, aa)

def iso(meshes, size, path, lw=1.6, edges=True, aa=True, ghost=(), opp=False):
    pv = _pv(); pl = pv.Plotter(off_screen=True, window_size=(size, size)); pl.set_background("white")
    if ghost: pl.enable_depth_peeling(number_of_peels=8)
    _add(pl, pv, meshes, lw, edges, ghost)
    lo, hi = _bbox(meshes); c = (lo + hi) / 2; d = np.array([-1.0, -1.0, 0.9] if opp else [1.0, 1.0, 0.9]); d /= np.linalg.norm(d)
    pl.camera.position = tuple(c + 500 * d); pl.camera.focal_point = tuple(c); pl.camera.up = (0, 0, 1)
    pl.enable_parallel_projection(); pl.reset_camera(); pl.camera.zoom(1.25)
    return _shot(pl, path, aa)

def _trim(img, m=12):
    a = img[..., :3]; mask = (a < 0.97).any(axis=2); ys, xs = np.where(mask)
    return img[max(ys.min() - m, 0):ys.max() + m, max(xs.min() - m, 0):xs.max() + m]

import tempfile
TMP = os.path.join(tempfile.gettempdir(), "knobparam-render")

def render(D, parts, keys, out_png, preview=False, tmp=TMP, clash_lines=(), gap_lines=(), title="", clean=False, note=None, opposite=False):
    OPP = dict(opp=True) if opposite else {}
    os.makedirs(tmp, exist_ok=True); T0 = time.time(); tm = {}
    bbs = [s.bounding_box() for s in parts.values()]
    pad = 5.0
    BB = [min(b.min.X for b in bbs) - pad, min(b.min.Y for b in bbs) - pad, min(b.min.Z for b in bbs) - pad,
          max(b.max.X for b in bbs) + pad, max(b.max.Y for b in bbs) + pad, max(b.max.Z for b in bbs) + pad]
    BB = [round(v, 1) for v in BB]
    tol = 0.08 if preview else 0.02
    t = time.time(); MA = cut_meshes(parts, keys, dict(kind="half", bb=BB, **OPP), tol); tm["A-A cut"] = time.time() - t
    lo, hi = _bbox(MA)
    t = time.time()
    rawA = ortho(MA, ((lo[0] + hi[0]) / 2, 0, (lo[2] + hi[2]) / 2), (0, -1, 0) if opposite else (0, 1, 0), (0, 0, 1), hi[0] - lo[0] + 2, hi[2] - lo[2] + 2,
                 9 if preview else (40 if clean else 30), f"{tmp}/aa.png", edges=not preview, aa=not preview)
    tm["A-A render"] = time.time() - t
    fang = float(D.get("fm_ang", 90.0)) % 360.0
    a0, a1 = (0.0, fang) if fang <= 180.0 else (fang, 360.0)
    t = time.time(); MQ = cut_meshes(parts, keys, dict(kind="quarter", bb=BB, a0=a0, a1=a1, **OPP), tol); tm["iso cut"] = time.time() - t
    hidden = []
    if clean:   # parts lying wholly in the cut-away quadrant (idler 1, feel motor + clip) are drawn whole in the iso view
        hidden = [n for n in parts if n not in MQ]
        if hidden: MQ.update(cut_meshes({n: parts[n] for n in hidden}, keys, dict(kind="whole", bb=BB), tol))
    t = time.time(); rawI = iso(MQ, 1100 if preview else (3400 if clean else 2600), f"{tmp}/iso.png", edges=not preview, aa=not preview, ghost=hidden, opp=opposite); tm["iso render"] = time.time() - t
    if clean:   # two views + colour legend only
        t = time.time(); compose_clean(D, parts, rawA, rawI, out_png, title, hidden, note, opposite); tm["compose"] = time.time() - t
        tm["total"] = time.time() - T0
        return tm
    insets = []
    if not preview:
        t = time.time()
        # B-B: plane through H2 and the EE-SX1321 (radial from the dial axis through H2)
        ex, ey = D["enc_xy"]; a = D["enc_ang"]; ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        rs = D["enc_cd"] + D["sens_r"]; sx, sy = rs * ca, rs * sa
        zb0, zb1 = D["h_hub_bot"] - 0.3, 0.6
        spB = dict(kind="box", o=(round(sx, 4), round(sy, 4)), a=a, u=(-5.5, 4.5), depth=30.0, z=(zb0, zb1))
        MB = cut_meshes(parts, keys, spB, 0.01)
        nB = (-math.sin(math.radians(spB["a"])), math.cos(math.radians(spB["a"])), 0)
        uB = np.array([math.cos(math.radians(spB["a"])), math.sin(math.radians(spB["a"]))])
        cB = (sx + uB[0] * (-0.5), sy + uB[1] * (-0.5), (zb0 + zb1) / 2)
        rawB = ortho(MB, cB, nB, (0, 0, 1), 10.0, zb1 - zb0, 120, f"{tmp}/bb.png", lw=2.0)
        th = D["ha_ang0"]
        if D["hall_layout"] == "vernier":   # C-C: radial plane through the axis at ang0 (middle magnet over the middle sensor)
            u0, u1, zc0, zc1 = D["dial_tube_id"] / 2 - 0.5, D["skirt_id"] / 2 + D["knob_wall"] + 0.3, -D["pcb_t"] - 0.3, 6.6
            spC = dict(kind="box", o=(0.0, 0.0), a=th, u=(round(u0, 3), round(u1, 3)), depth=2.0, z=(round(zc0, 3), zc1))
            MC = cut_meshes(parts, keys, spC, 0.01)
            nC = (-math.sin(math.radians(th)), math.cos(math.radians(th)), 0); uc = (u0 + u1) / 2
            rawC = ortho(MC, (uc * math.cos(math.radians(th)), uc * math.sin(math.radians(th)), (zc0 + zc1) / 2), nC, (0, 0, 1),
                         u1 - u0, zc1 - zc0, 80, f"{tmp}/cc.png", lw=2.0)
        else:   # C-C: tangent plane at the Hall radius, ang0
            r = D["ha_r_m"]; tw, zc0, zc1 = 11.5, -0.3, 6.4
            o = (r * math.cos(math.radians(th)), r * math.sin(math.radians(th)))
            spC = dict(kind="box", o=(round(o[0], 4), round(o[1], 4)), a=th - 90.0, u=(-tw, tw), depth=5.0, z=(zc0, zc1))
            MC = cut_meshes(parts, keys, spC, 0.01)
            nC = (math.cos(math.radians(th)), math.sin(math.radians(th)), 0)
            rawC = ortho(MC, (o[0], o[1], (zc0 + zc1) / 2), nC, (0, 0, 1), 2 * tw, zc1 - zc0, 90, f"{tmp}/cc.png", lw=2.0)
        # D: cone race on A-A at +x
        bx, bz = D["kb_rc"], D["kb_zc"]; xd0, xd1, zd0, zd1 = bx - 1.9, bx + 1.5, bz - 1.4, bz + 1.6
        spD = dict(kind="box", o=(0.0, 0.0), a=0.0, u=(xd0, xd1), depth=12.0, z=(zd0, zd1))
        MD = cut_meshes(parts, keys, spD, 0.005)
        k = D["kb_ball_d"] / 2 / math.sqrt(2)
        def lines(pl, pv):
            A_ = np.array([bx - 2.2 * k, 0.3, bz + 2.2 * k]); B_ = np.array([bx + 2.2 * k, 0.3, bz - 2.2 * k])
            pl.add_lines(np.array([A_, B_]), color="#d50000", width=6)
            for q in (-1, 1): pl.add_mesh(pv.Sphere(radius=0.07, center=(bx + q * k, 0.35, bz - q * k)), color="#d50000")
            pl.add_mesh(pv.Sphere(radius=0.04, center=(bx, 0.35, bz)), color="black")
            if D["kb_groove_h"] > 0:   # groove centre + R0.52 arc (blue)
                cr, cz = D["kb_seat_c"]; rs = D["kb_seat_r"]
                pl.add_mesh(pv.Sphere(radius=0.03, center=(cr, 0.4, cz)), color="#0d47a1")
                ang = np.radians(np.linspace(100, 170, 40)); arc = np.c_[cr + rs * np.cos(ang), np.full(40, 0.4), cz + rs * np.sin(ang)]
                pl.add_lines(np.repeat(arc, 2, axis=0)[1:-1], color="#00b0ff", width=7)
        rawD = ortho(MD, ((xd0 + xd1) / 2, 0, (zd0 + zd1) / 2), (0, 1, 0), (0, 0, 1), xd1 - xd0, zd1 - zd0, 260, f"{tmp}/d.png", extra=lines, lw=2.0)
        # E: radial plane through the feel-motor axis (shaft down into its pinion)
        angE = D["fm_ang"]; ze0, ze1 = -D["pcb_t"] - 0.4, D["fm_z_can1"] + D["feel"]["end_boss"] + 0.6
        s0, s1 = round(-D["dial_tube_od"] / 2 - 1.0, 3), round(D["fm_cd"] + D["fm_tip"] + 1.5, 3)
        spE = dict(kind="box", o=(0.0, 0.0), a=angE, u=(s0, s1), depth=8.0, z=(round(ze0, 3), round(ze1, 3)))
        ME = cut_meshes(parts, keys, spE, 0.01)
        nE = (-math.sin(math.radians(angE)), math.cos(math.radians(angE)), 0)
        uc = (s0 + s1) / 2
        cE = (uc * math.cos(math.radians(angE)), uc * math.sin(math.radians(angE)), (ze0 + ze1) / 2)
        rawE = ortho(ME, cE, nE, (0, 0, 1), s1 - s0, ze1 - ze0, 40, f"{tmp}/ee.png", lw=2.0)
        insets = [rawB, rawC, rawD, rawE]
        if D["hall_layout"] == "vernier": insets.append(hall_plot(D, f"{tmp}/hh.png"))
        tm["insets"] = time.time() - t
    t = time.time(); compose(D, parts, rawA, rawI, insets, out_png, preview, clash_lines, gap_lines, title); tm["compose"] = time.time() - t
    tm["total"] = time.time() - T0
    return tm

def hall_plot(D, path):
    """Inset H: plan of the vernier rows at -T / 0 / +T + field at each sensor vs dial angle (charged-disc model)."""
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from . import hall_dyn as H
    a = H.analyse(D); T = D["travel_deg"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.6, 3.2), dpi=200, gridspec_kw=dict(width_ratios=[1.0, 1.25]))
    a0 = math.radians(D["ha_ang0"]); rot = lambda x, y: (x * math.cos(-a0 + math.pi / 2) - y * math.sin(-a0 + math.pi / 2), x * math.sin(-a0 + math.pi / 2) + y * math.cos(-a0 + math.pi / 2))
    s = D["hv_sensor"]
    for r, ph in zip(D["hv_r"], D["hv_phi_s"]):
        x, y = rot(r * math.cos(math.radians(ph)), r * math.sin(math.radians(ph)))
        ax1.add_patch(plt.Rectangle((x - s["l"] / 2, y - s["w"] / 2), s["l"], s["w"], color="#212121"))
    for th, c in ((-T, "#1e88e5"), (0, "#e53935"), (T, "#43a047")):
        pts = [rot(r * math.cos(math.radians(ph + th)), r * math.sin(math.radians(ph + th))) for r, ph in zip(D["hv_r"], D["hv_phi_m"])]
        for i, (x, y) in enumerate(pts):
            ax1.add_patch(plt.Circle((x, y), D["hv_mag"][0] / 2, fill=False, ec=c, lw=1.6, ls="-" if i % 2 == 0 else "--"))
        ax1.plot([p[0] for p in pts], [p[1] for p in pts], color=c, lw=0.8, label=f"magnets θ={th:+g}°")
    ax1.set_aspect("equal"); ax1.set_xlim(-4, 4); ax1.set_ylim(D["hv_r"][0] - 2, D["hv_r"][-1] + 2)
    ax1.set_xlabel("tangential (mm)", fontsize=7); ax1.set_ylabel("radius (mm)", fontsize=7); ax1.tick_params(labelsize=6)
    ax1.legend(fontsize=5.5, loc="lower left"); ax1.set_title("plan (black = sensors)", fontsize=7.5)
    for j in range(D["hv_n"]): ax2.plot(a["theta"], a["B"][:, j], lw=1.2, label=f"H{j + 1} r{D['hv_r'][j]:.1f}")
    rng = D["hv_sensor"]["range_mt"]; ax2.axhline(rng, color="grey", ls=":", lw=0.8); ax2.axhline(-rng, color="grey", ls=":", lw=0.8)
    ax2.axvspan(-T, T, color="#f5f5f5", zorder=-1)
    ax2.set_xlabel("dial angle θ (deg)", fontsize=7); ax2.set_ylabel("Bz at element (mT)", fontsize=7); ax2.tick_params(labelsize=6)
    ax2.legend(fontsize=5.5, ncol=1, loc="upper right"); ax2.grid(alpha=0.3)
    ax2.set_title(f"field (disc model); σθ ≤ {a['s_theta_worst'] * 1e3:.1f} m° rms (noise-limited)", fontsize=7.5)
    fig.tight_layout(); fig.savefig(path); plt.close(fig); return path

def compose(D, parts, rawA, rawI, insets, out, preview, clash_lines, gap_lines, title):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; from matplotlib.patches import Patch
    S = D["S"]
    if preview:
        fig = plt.figure(figsize=(15, 8.4), dpi=100)
        fig.text(0.01, 0.965, title + "  —  PREVIEW (low-res, no insets)", fontsize=14, weight="bold")
        rects = ([0.01, 0.27, 0.47, 0.66], [0.5, 0.27, 0.49, 0.66])
    else:
        fig = plt.figure(figsize=(20, 15.5), dpi=150)
        fig.text(0.012, 0.978, title, fontsize=17, weight="bold")
        if D["version"] == "v0.15":
            fig.text(0.012, 0.950, f"v0.15 (knob-param): ball seating groove R{D['kb_seat_r']:g}×{D['kb_seat_depth']:g} in the dial cone (45° line kept); screen bonded to the dial (carrier on the dial, lip wall {D['lip_wall']:.2f}, no running gap),\n"
                     f"diametral FPC service strap B2B→J1 (±{D['travel_deg']:g}°, strain {D['strap_strain_pct']:.2f}%); Hall vernier: arm down through a cradle slot, {D['hv_n']} magnets × {D['hv_n']} {D['hv_sensor']['part'].split()[0]} on crossing arcs (±{D['hv_g']:.2f}°/mm). Cut faces = lighter tint; clashes listed only.", fontsize=10.5)
        else:
            fig.text(0.012, 0.950, f"{D['version']}: rebuilt from ONE parameter file (knob-param/knobcad/params.py). Screen offset {D['scr_off']:.2f} away from the FPC exit, FPC fold inside the lip ID.\n"
                     f"Cut faces = lighter tint, black outline. Clash volumes not drawn (listed bottom right).", fontsize=10.5)
        rects = ([0.01, 0.42, 0.47, 0.51], [0.50, 0.42, 0.49, 0.51])
    def put(rect, path, ttl, sub=None, frame=False, fs=9.5):
        ax = fig.add_axes(rect); ax.imshow(_trim(plt.imread(path))); ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values(): sp.set_visible(frame); sp.set_edgecolor("#555555")
        ax.set_title(ttl, fontsize=12, weight="bold", loc="left")
        if sub: ax.text(0, -0.02, sub, transform=ax.transAxes, fontsize=fs, va="top")
    put(rects[0], rawA, "SECTION A-A, straight on (through the dial and motor axes)",
        f"Motor (+X) on the LEFT; FPC tail on the right. Knob Ø{D['knob_od']:.2f}, height {D['z_knob_top'] - D['h_skirt0']:.1f}; glass {D['z_top']:.2f}; dial lip wall {D['lip_wall']:.2f}.")
    put(rects[1], rawI, "ISO QUARTER CUT-AWAY (A-A + the plane through the dial axis at 90° to it)")
    if insets:
        y0, hh = 0.195, 0.17
        if D["hall_layout"] == "vernier":
            put([0.005, y0, 0.15, hh], insets[0], "B-B  encoder (~8x)", f"EE-SX1321, {D['rim_t']:.1f} rim in its {D['sens']['slot_w']:.1f} slot;\ntrimmed wheel, top {D['h_big_top']:.2f} ({D['z_sens_open'] - D['h_big_top']:.2f} under).", frame=True, fs=8)
            put([0.162, y0, 0.20, hh], insets[1], f"C-C  Hall bar, radial at {D['ha_ang0']:g}° (~5x)", f"Arm down through the cradle slot; {D['hv_n']} × Ø{D['hv_mag'][0]:g}×{D['hv_mag'][1]:g} N52 " + "/".join("N" if p > 0 else "S" for p in D['hv_pol']) + f"\nover 4 × TMAG5253 X2SON + TMAG5273 (H3, 3D), magnets z {D['hv_z_mag0']:.2f}\n(element {D['hv_elem_gap']:.2f}); pitch {D['hv_pitch']:g}, r {D['hv_r'][0]:.1f}-{D['hv_r'][-1]:.1f}.", frame=True, fs=8)
            put([0.372, y0, 0.15, hh], insets[2], "D  45° cone race + seat (~17x)", f"{D['kb_n']} × Ø{D['kb_ball_d']:g}, PCD Ø{D['kb_pcd']:.2f}; red = 45° line.\nSeat groove R{D['kb_seat_r']:g} (blue) × {D['kb_seat_depth']:g} deep in the\nDIAL cone, ±{D['kb_seat_w']:.2f} wide, centre on the 45° line.\nASSEMBLY: dial lip-down, grease the groove,\ndrop the {D['kb_n']} balls in (they sit + stay),\nlower the knob on axially, flip, fit.", frame=True, fs=7.5)
            put([0.53, y0, 0.25, hh], insets[4], "H  Hall vernier: plan at ±travel + field", f"Magnet arc +{D['hv_g']:.3f}°/mm, sensor arc -{D['hv_g']:.3f}°/mm (cross at r{D['hv_r_mid']:.1f}, θ=0);\ncrossing moves {1 / (2 * D['hv_g']):.2f} mm/deg -> end pair at ±{D['hv_cross_travel']:g}°.", frame=True, fs=8)
            put([0.79, y0, 0.12, hh], insets[3], "E  feel motor (~3x)", f"{D['feel']['part']} Ø{D['feel']['can_d']:g}×{D['feel']['can_len']:g} [A]\naxial at {D['fm_ang']:.0f}°, {D['fg_pinion']['part']}\n× {D['fg_z_gear']}T compound, overall {D['fm_ratio']:.2f}:1.", frame=True, fs=8)
        else:
            put([0.005, y0, 0.20, hh], insets[0], "B-B  encoder (~8x)", f"EE-SX1321, {D['rim_t']:.1f} rim in its {D['sens']['slot_w']:.1f} slot;\ntrimmed wheel, top {D['h_big_top']:.2f} ({D['z_sens_open'] - D['h_big_top']:.2f} under).", frame=True)
            put([0.215, y0, 0.25, hh], insets[1], "C-C  Hall array (~6x)", f"{D['ha_n']} × Ø{D['ha_mag'][0]:g}×{D['ha_mag'][1]:g} N52 alternating over\n2 × DRV5055A3, gap {D['ha_gap']:.1f}.", frame=True)
        if D["hall_layout"] != "vernier":
          put([0.475, y0, 0.20, hh], insets[2], "D  top 45° cone race (~11x)", f"{D['kb_n']} × Ø{D['kb_ball_d']:g}, PCD Ø{D['kb_pcd']:.2f}; red = 45° contact line\n(dial cone up-in, knob cone down-out).\nAssemble: dial lip-down, grease the ring in,\nlower the knob on axially, flip, fit.", frame=True)
          put([0.69, y0, 0.14, hh], insets[3], "E  feel motor (~3x)", f"Radial plane through its axis.\n{D['feel']['part']} Ø{D['feel']['can_d']:g}×{D['feel']['can_len']:g} [A]\naxial at {D['fm_ang']:.0f}°, {D['z_feel']}T into the {D['z_ring']}T ring\n(ratio {D['fm_ratio']:.2f}).", frame=True)
    shown = sorted({group_of(n) for n in parts})
    hand = [Patch(facecolor=GROUPS[i][1], edgecolor="#222222", label=GROUPS[i][0]) for i in shown]
    fig.legend(handles=hand, loc="lower left", ncol=3, fontsize=9.5 if not preview else 8, frameon=True, bbox_to_anchor=(0.005, 0.0), title="PARTS", title_fontsize=11)
    txt = list(clash_lines) + ([""] if gap_lines else []) + list(gap_lines)
    fig.text(0.62 if not preview else 0.62, 0.118 if not preview else 0.18, "\n".join(txt[:22]), fontsize=8.5 if not preview else 7.5, va="top", color="#7a0000", family="monospace")
    fig.savefig(out, dpi=fig.dpi)


def compose_clean(D, parts, rawA, rawI, out, title, hidden=(), note=None, opposite=False):
    """--clean: A-A straight on (left) + iso quarter cut (right) + a part-colour legend. No insets, tables or clash text."""
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; from matplotlib.patches import Patch
    A, I = _trim(plt.imread(rawA), 4), _trim(plt.imread(rawI), 4)
    FW, FH = 22.5, 16.0
    fig = plt.figure(figsize=(FW, FH), dpi=150)
    feel_line = ""
    if "z_feel" in D:
        feel_line = (f" Feel motor: {D['feel']['part']} axial at {D['fm_ang']:.0f}°, "
                     f"{D['fg_pinion']['part']} × {D['fg_z_gear']}T compound, overall {D['fm_ratio']:.2f}:1.")
    fig.text(0.012, 0.985, title, fontsize=26, weight="bold", va="top")
    fig.text(0.012, 0.952, f"Knob Ø{D['knob_od']:.2f}, 10HP module. " + (note or "Default parameters (no overrides).") + feel_line + " "
             "Cut faces are drawn in a lighter tint of the part colour." +
             (f"\nIn the iso view, parts lying wholly inside the cut-away quarter ({', '.join(sorted({GROUPS[group_of(n)][0].split(' (')[0] for n in hidden}))}) are drawn whole, semi-transparent." if hidden else ""), fontsize=14, wrap=True, va="top", color="#333333", linespacing=1.4)
    y0, y1, gap, mx = 0.235, 0.865, 0.03, 0.012
    ra, ri = A.shape[1] / A.shape[0], I.shape[1] / I.shape[0]          # width/height
    h = y1 - y0; k = FH / FW
    if (ra + ri) * h * k + gap + 2 * mx > 1: h = (1 - gap - 2 * mx) / ((ra + ri) * k)
    wa, wi = ra * h * k, ri * h * k; x0 = (1 - wa - wi - gap) / 2
    for (x, w), img, ttl in [((x0, wa), A, "SECTION A-A, straight on" + (" from -Y" if opposite else "") + "\n(dial + motor axes; motor on the " + ("right)" if opposite else "left)")),
                             ((x0 + wa + gap, wi), I, "ISOMETRIC QUARTER CUT-AWAY\n(A-A + the plane through the feel-motor axis)")]:
        ax = fig.add_axes([x, y1 - h, w, h]); ax.imshow(img, interpolation="lanczos"); ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values(): sp.set_visible(False)
        fig.text(x, y1 + 0.006, ttl, fontsize=17, weight="bold", va="bottom")
    shown = sorted({group_of(n) for n in parts})
    hand = [Patch(facecolor=GROUPS[i][1], edgecolor="#222222", label=GROUPS[i][0]) for i in shown]
    fig.legend(handles=hand, loc="lower center", ncol=4, fontsize=12, frameon=True, bbox_to_anchor=(0.5, 0.008),
               title="PART COLOURS", title_fontsize=16, handlelength=2.2, handleheight=1.3, columnspacing=1.6, labelspacing=0.5)
    fig.savefig(out, dpi=fig.dpi)
