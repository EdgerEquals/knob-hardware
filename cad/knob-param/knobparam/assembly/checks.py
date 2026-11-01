"""Checks runner. LOCAL checks live in each sub-assembly (checks.py, own parts + scope only); the CROSS checks below need parts
or values from more than one sub-assembly and are owned by the assembly agent. Plus pairwise solid clashes (bbox prefilter,
OCC intersection volume, parallel spawn pool, cached per part-hash pair)."""
import hashlib, itertools, json, math, os, time
from build123d import *
from ..common.cache import CACHE
from ..common.checks import Rows, min_dist
from ..common.util import cyl
from ..common import model

KNOWN = {"PCB / motor": "1220 rear boss Ø3×0.6 into the PCB front: the KiCad M1 footprint has no Ø3.2 relief hole yet (v0.13 same)"}

def local(D, parts, owner, subs=None):
    rows = []
    for s in model.ALL:
        if subs and s not in subs: continue
        rows += model.sub(s).checks(model.view(D, s), {n: p for n, p in parts.items() if owner[n] == s})
    return rows

def cross(D, parts):
    from .. import control_dial as cd
    from . import hall_dyn
    T = D["tgt"]; r = Rows("assembly"); row = r.row
    Tdeg = D["travel_deg"]
    TR = (-Tdeg, -D["det_deg"], 0.0, D["det_deg"], Tdeg); on = D["screen_on_dial"]
    Dc = model.view(D, "control_dial")
    _arm0 = cd.arm(Dc, 0.0)                       # build once; arm(D, t) is that solid rotated about Z
    ARM = {t: Rot(0, 0, t) * _arm0 for t in TR}
    if on:
        stat = {n: parts[n] for n in parts if n.startswith("adapter part") and not n.endswith(D["b2b_at"])}
        stat["rod + nut"] = cyl(D["nut_s"] / math.sqrt(3), D["z_board_top"], D["nut_m"])
        if "adapter cup (fixed)" in parts: stat["adapter cup (fixed)"] = parts["adapter cup (fixed)"]
        smin, swho = 1e9, ""
        for t in TR:
            sb = cd.strap_bent(Dc, t)
            for n, q in stat.items():
                d = sb.distance_to(q)
                if d < smin: smin, swho = d, n
        row("FPC service strap vs U3 / nut / cup (±travel)", smin, T["strap_vs_parts"], f"nearest: {swho}; strap z {D['strap_z0']:.2f}-{D['strap_z1']:.2f}")
    else:
        row("jumper FPC vs TMAG5273 U3", parts["screen jumper FPC [A]"].distance_to(parts["adapter part U3"]), 0.3, f"B2B over {D['b2b_at']}")
    M = D["motor"]; ex, ey = D["enc_xy"]; worst = 9.9
    for s in (-1, 1):
        x = D["offset"] + s * M["term_pitch"] / 2; rr = math.hypot(x - ex, 0 - ey)
        tip = -M["term_len"] - D["tab_solder"]
        if D["rim_r0"] - 1.2 <= rr <= D["rim_r1"] + 1.2: worst = min(worst, tip - D["rim_top"])
    row("1220 tab + solder vs encoder rim (axial)", worst, T["tab_vs_rim"], "tab at r %.2f from H2, rim r %.2f-%.2f" % (math.hypot(D["offset"] + M["term_pitch"] / 2 - ex, ey), D["rim_r0"], D["rim_r1"]))
    tips = {}
    for a, nm in [(D["enc_ang"], "encoder pinion")] + [(a, f"idler {i + 1}") for i, a in enumerate(D["idler_angs"])]:
        x, y = D["enc_cd"] * math.cos(math.radians(a)), D["enc_cd"] * math.sin(math.radians(a))
        tips[nm] = cyl(D["d_pin_tip"] / 2, D["h_pin0"], D["pin_face"], x, y)
    tips["motor collar"] = cyl(D["motor_collar_od"] / 2, 0, 40, D["offset"])
    hmin, hwho = 1e9, ""
    for t in TR:
        arm = ARM[t]
        for n, s in tips.items():
            d = arm.distance_to(s)
            if d < hmin: hmin, hwho = d, n
    row("Hall arm vs pinions / motor collar (±travel)", hmin, T["hall_vs_pinions"], f"nearest: {hwho}")
    if D["hall_layout"] == "vernier":
        cr = parts["base cradle"]; sens = [parts[n] for n in parts if n.startswith("hall sensor")]
        from ..common.util import sector
        cr_far = cr - sector(0, D["sl_r"] + 3, 60, -1, 20, D["sl_ang"]) if D["fan_on"] else cr   # stop blocks checked separately
        row("Hall arm / fan vs cradle, detent blocks, track (±travel)", min_dist(list(ARM.values()), [cr_far]), T["arm_vs_cradle"], f"slot r {D['hv_slot_r0']:.2f}-{D['hv_slot_r1']:.2f}")
        if D["fan_on"]:
            stops = cr - cr_far
            lv = lambda t: ARM[t]
            row("dial lever vs hard stops at rest", lv(0).distance_to(stops), T["arm_vs_cradle"])
            row("dial lever vs hard stops when latched at ±det_deg", min(lv(t).distance_to(stops) for t in (-D["det_deg"], D["det_deg"])), 0.02,
                f"stop contact at ±{D['travel_deg']:.2f}° (past the ±{D['det_deg']:g}° end detent by {D['travel_deg'] - D['det_deg']:.2f}°, the ball's bore play)")
            row("dial lever meets the stop faces at ±travel (gap)", max(lv(t).distance_to(stops) for t in (-D["travel_deg"], D["travel_deg"])), 0.02, "flush contact = hard end stop", higher_ok=False)
            if D["cu_on"]:
                md, mh = D["cu_mag"]; m_dip = D["hv_br"] / (4e-7 * math.pi) * math.pi * (md / 2e3) ** 2 * (mh / 1e3)
                cus = [parts[n] for n in parts if n.startswith("cushion magnet")]
                dmin = min(c.distance_to(s_) for c in cus for s_ in sens) + md / 2
                bst = 1e3 * 2e-7 * m_dip / (dmin / 1e3) ** 3 * len(cus)
                row("cushion magnets: stray field at the nearest Hall-row sensor / range", bst / D["hv_sensor"]["range_mt"], D["cu_stray_max"],
                    f"{len(cus)} × Ø{md:g}×{mh:g}, nearest {dmin:.1f} mm, ≤ {bst:.2f} mT", higher_ok=False)
            fan_d = min(ARM[t].distance_to(parts[n]) for t in TR for n in parts if n.startswith("detent") and "ball" not in n)
            row("fan vs detent springs / grubs (±travel)", fan_d, T["arm_vs_cradle"])
        mi = D["hv_mid"]["idx"] if D["hv_mid"] else -1
        s53 = [parts[n] for n in parts if n.startswith("hall sensor") and "TMAG5273" not in n]
        s73 = [parts[n] for n in parts if n.startswith("hall sensor") and "TMAG5273" in n]
        row("Hall bar / magnets vs TMAG5253 tops (air gap, ±travel)", min_dist(list(ARM.values()), s53), D["hv_gap"] - 0.01, f"element gap {D['hv_elem_gap']:.2f}")
        if s73:
            row("Hall bar / magnets vs TMAG5273 (H3) top (air gap, ±travel)", min_dist(list(ARM.values()), s73), D["hv_gap_mid"] - 0.01,
                f"SOT-23-6 h {D['hv_mid']['h']:g}; element gap {D['hv_mid_elem_gap']:.2f}; magnet faces z {D['hv_z_mag0']:.2f}")
        row("Hall sensors vs cradle", min_dist(sens, [cr]), T["sensor_vs_cradle"])
        H = hall_dyn.analyse(D)
        pk53 = max(float(H["B_peak_j"][j]) for j in range(D["hv_n"]) if j != mi)
        row("Hall peak |Bz| at the TMAG5253s vs range (mT)", pk53, 0.9 * D["hv_sensor"]["range_mt"], f"{D['hv_sensor']['part']} ±{D['hv_sensor']['range_mt']:g} mT; poles " + "/".join("N" if p > 0 else "S" for p in D["hv_pol"]), higher_ok=False)
        if mi >= 0:
            import numpy as _np
            bv = hall_dyn.field_vec(D, mi, _np.linspace(-D["travel_deg"], D["travel_deg"], 23))
            pax = float(_np.abs(bv).max()); pxy = float(_np.abs(bv[:, :2]).max()); pz = float(_np.abs(bv[:, 2]).max())
            row("Hall peak field at the TMAG5273 (H3), worst axis vs range (mT)", pax, 0.9 * D["hv_mid"]["range_mt"],
                f"{D['hv_mid']['part']} ±{D['hv_mid']['range_mt']:g} mT/axis: |Bz| ≤ {pz:.1f}, |Bx|,|By| ≤ {pxy:.1f}; elem gap {D['hv_mid_elem_gap']:.2f}", higher_ok=False)
        row("Hall angle noise, worst over ±travel (deg rms)", H["s_theta_worst"], 0.01, f"min |dB/dθ| {H['slope_min']:.1f} mT/deg, noise {H['noise_mT'] * 1e3:.0f} µT rms", higher_ok=False)
    if D["kb_groove_h"] > 0:
        kb = [parts[n] for n in parts if n.startswith("knob") and "ball" not in n]
        row("seat: dial vs knob (race region)", min(parts["control dial"].distance_to(q) for q in kb), T["seat_vs_knob"])
    row("idler 1 vs 1220 can", math.hypot(D["idler_xy"][0][0] - D["offset"], D["idler_xy"][0][1]) - D["can_r"] - D["d_pin_tip"] / 2, T["idler_motor"])
    feel_names = [n for n in parts if n.startswith("feel motor")]
    feels = [parts[n] for n in feel_names]
    clip = parts["feel motor saddle seat [A]"].fuse(parts["feel motor saddle strap [A]"])
    can = [parts[n] for n in feel_names if "shaft" not in n and "saddle" not in n and "pinion" not in n][0]
    pin = [parts[n] for n in feel_names if "pinion" in n][0]
    knob = [parts[n] for n in parts if n.startswith("knob body")][0]
    rings = [parts[n] for n in parts if n.startswith("bottom internal ring")]
    ring = rings[0] if len(rings) == 1 else rings[0].fuse(*rings[1:])
    row("feel saddle vs knob skirt", clip.distance_to(knob), D["feel"]["clear"],
        f"can {can.distance_to(knob):.2f} inside the skirt; {D['fg_pinion']['part']} at {D['fm_ang']:.1f}°, overall {D['fm_ratio']:.2f}:1, knob Ø{D['knob_od']:.2f}")
    row("feel can/saddle vs bottom ring", min(can.distance_to(ring), clip.distance_to(ring)), D["feel"]["clear"])
    row("feel pinion vs encoder pinion", pin.distance_to(parts["encoder pinion"]), D["feel"]["clear"])
    row("feel motor vs dial tube", min(p.distance_to(parts["control dial"]) for p in feels), D["feel"]["clear"])
    row("feel motor vs Hall arm (±travel)", min_dist(list(ARM.values()), feels), T["hall_vs_pinions"])
    # v0.17 swept motion: springs follow the lever pin, track balls roll at half the dial angle
    from ..base_drive.parts.mech import springs_at, track_balls_at
    # coils seat on the anchor posts, so the cradle distance is ~0 there; check they stay clear of the drive
    obstacles = [parts["motor"], parts["encoder pinion"], *rings]
    spr_d = min(sp.distance_to(o) for th in TR for sp in springs_at(D, th) for o in obstacles)
    row("centring springs vs motor / encoder / ring across ±travel", spr_d, D["feel"]["clear"],
        f"lever pin at {D['sl_ang']:.0f}° + θ; sampled {', '.join(f'{t:+.1f}' for t in TR)}")
    roll_left = min(D["bt_half"] - abs(th) / 2 for th in TR)
    row("track balls stay in the groove across ±travel (deg of groove left)", roll_left,
        math.degrees((D["bt_ball"] / 2) / min(D["bt_rs"])),
        "ball rolls at θ/2 between the plate groove and the ear; end detents at ±%.2f°, hard stop ±%.2f°" % (D["det_deg"], D["travel_deg"]))
    gear = parts[f"feel compound gear {D['fg_z_gear']}T"]
    tb_d = min(b.distance_to(gear) for th in TR for b in track_balls_at(D, th))
    row("track balls vs compound gear across ±travel", tb_d, D["feel"]["clear"],
        "balls posed at θ/2 for each sample")
    row("printed spur stays on the feel side of the centre tube", D["enc_cd"] - D["fg_tip"] - 2.5, D["feel"]["clear"],
        f"{D['fg_z_gear']}T tip r {D['fg_tip']:.2f} at the idler r {D['enc_cd']:.2f}; tube Ø5")
    row("printed spur tooth tip vs MJF short-feature floor", D["spur_tip_th"], D["spur_tooth_min"],
        f"thinnest nylon spur (hub, motor pinion, {D['fg_z_gear']}T, feel pinion); preferred {D['hb_tooth_min']:.2f}")
    row("compound gear vs encoder rim (axial)", D["fg_z_bot"] - D["rim_top"], D["fg_clear"],
        f"gear z {D['fg_z_bot']:.2f} to {D['fg_z_top']:.2f}; rim top {D['rim_top']:.2f}; sensor dropped {D['enc_drop']:.2f} onto the daughterboard")
    ot_bits = [parts[n] for n in parts if n.startswith("outer thrust") and "blank" not in n]
    caps = [n for n in parts if n.endswith(" cap")]

    def _cap_mount(cap, other):
        if cap == "pinion cap":
            return other == "pinion"
        if cap == "encoder pinion cap":
            return other in ("encoder pinion", "encoder shaft")
        if cap.startswith("idler pinion ") and cap.endswith(" cap"):
            idx = cap.split()[2]
            return other in (f"idler pinion {idx}", f"idler pin {idx}")
        if cap == "feel motor pinion cap":
            return other.startswith("feel motor pinion")
        if cap == "hub gear cap":
            return other.startswith("knob body")
        return False

    if caps:
        cap_d, cap_who = 1e9, ""
        for n in caps:
            for m, s in parts.items():
                if m == n or _cap_mount(n, m):
                    continue
                d = parts[n].distance_to(s)
                if d < cap_d:
                    cap_d, cap_who = d, f"{n} / {m}"
        row("resin caps vs everything they do not mount on", cap_d, 0.3,
            f"nearest {cap_who}; UTR-8100 stepped Fresnel, press modelled at {D['cap_fit_gap']:.2f}")
    row("bottom thrust land, clear resin under the groove", D["ot_land_th"], D["ot_land_min"],
        f"groove bottom z {D['ot_z'] - D['ot_rg']:.2f}; ball centre {D['ot_z']:.2f}; underside was skirt_gap {D['skirt_gap']:.2f}, now {D['h_skirt0']:.2f}. UTR-8100, not an insert",
        procs=("sla", "sla"))
    row("outer thrust balls vs bottom ring", min(b.distance_to(ring) for b in ot_bits), 0.0,
        f"Ø{D['ot_ball_d']:g} load × {D['ot_n']}, glass {D['ot_spacer_min']:g}–{D['ot_spacer_max']:g} × {D['ot_n_spacer']}, ruby {len(D['ot_ruby_idx'])} on r {D['ot_r']:.2f}",
        procs=("buy", "mjf"))
    row("spacer clears both tracks at the large end", D["ot_track_clear_max"], D["ot_seat_gap"],
        f"{D['ot_track_clear_min']:.3f} at {D['ot_spacer_min']:g} mm, {D['ot_track_clear_alt']:.3f} at {D['ot_spacer_alt']:g} mm")
    row("spacer gap at the large end (no jam)", D["ot_gap_max"], D["ot_play_max"],
        f"chord {D['ot_chord']:.3f}; ring play {D['ot_play_total']:.2f}", higher_ok=False)
    row("spacer still touches at the small end (gap)", D["ot_gap_min"], D["ot_play_max"],
        f"1.588 mm gap {D['ot_gap_alt']:.3f}", higher_ok=False)
    row("spacer gap stays positive at the small end", D["ot_gap_min"], D["ot_play"])
    row("light path between a load ball and a spacer", D["ot_light_gap"], D["ot_play"],
        f"axial window beside a {D['ot_spacer_max']:g} spacer {D['ot_track_clear_max']:.3f}")
    # ---- v0.16 relative knob-vs-dial angle: diametric ring magnet in the knob under the dial TMAG5273 ----
    if D["rel_sensor"]:   # v0.16b [Ed]: removed by default
        B = ring_field(D)
        row("dial TMAG5273: peak |B| from the knob ring / range (nominal gap)", B["peak"] / D["tm_range_mt"], 0.3,
            f"ring Ø{D['tm_ring'][1]:g}/Ø{D['tm_ring'][0]:g}×{D['tm_ring'][2]:g} N52 diametric, element gap {D['tm_gap']:.2f}: |B| {B['peak']:.0f} mT, in-plane {B['bxy_min']:.0f}-{B['bxy_max']:.0f} mT")
        row("dial TMAG5273: peak |B| / range with the dial lifted to the stop", B["peak_lift"] / D["tm_range_mt"], 0.9,
            f"gap {D['tm_gap_min']:.2f}: {B['peak_lift']:.0f} mT", higher_ok=False)
    from ..common import gearcheck
    gearcheck.rows(D, row)          # contact ratio and backlash band; tooth counts are this stack's, not the old spur set
    from .. import optics
    optics.beam_rows(D, parts, row)  # no-op while optics_on is False
    return r

def ring_field(D):
    """Field of the diametric ring (dipole sum, Br from hv_br) at the dial TMAG5273 element, over a full knob turn."""
    import numpy as np
    ri, ro, th = D["tm_ring"]; Br = D["hv_br"]; M = Br / (4e-7 * np.pi)
    rr = np.linspace(ri / 2, ro / 2, 9)[:-1] + (ro - ri) / 32; ph = np.linspace(0, 2 * np.pi, 240, endpoint=False); zz = np.linspace(-th, 0, 5)[:-1] + th / 8
    R_, P_, Z_ = np.meshgrid(rr, ph, zz, indexing="ij"); dV = (ro - ri) / 2 / 8 * (2 * np.pi / 240) * R_ * th / 4 * 1e-9
    X, Y = R_ * np.cos(P_), R_ * np.sin(P_)
    sx, sy = D["tm_xy"]
    def field(gap):
        out = []
        for a in np.linspace(0, 2 * np.pi, 72, endpoint=False):
            mx, my = np.cos(a) * M * dV, np.sin(a) * M * dV
            rx, ry, rz = (sx - X) * 1e-3, (sy - Y) * 1e-3, (gap - Z_) * 1e-3
            r2 = rx * rx + ry * ry + rz * rz; r5 = r2 ** 2.5; md = mx * rx + my * ry
            b = 1e-7 * np.array([np.sum((3 * md * rx - mx * r2) / r5), np.sum((3 * md * ry - my * r2) / r5), np.sum(3 * md * rz / r5)]) * 1e3
            out.append(b)
        return np.array(out)
    b = field(D["tm_gap"]); bl = field(D["tm_gap_min"])
    nb = np.linalg.norm(b, axis=1); bxy = np.linalg.norm(b[:, :2], axis=1)
    return dict(peak=float(nb.max()), peak_lift=float(np.linalg.norm(bl, axis=1).max()), bxy_min=float(bxy.min()), bxy_max=float(bxy.max()))

def _bb(s):
    b = s.bounding_box(); return (b.min.X, b.min.Y, b.min.Z, b.max.X, b.max.Y, b.max.Z)
def _ov(A, B, t=1e-6): return all(A[i] < B[i + 3] - t and B[i] < A[i + 3] - t for i in range(3))

def _work(job):
    from ..common.cache import load
    pair, pa, pb = job
    try:
        s = load(pa).intersect(load(pb)); v = 0.0 if s is None else sum(c.volume for c in (s if isinstance(s, (list, ShapeList)) else [s]))
    except Exception:
        v = -1.0
    return pair, v

def clashes(parts, keys, thr=1e-3, procs=8):
    from .build import PATHS
    from ..common.cache import pool
    os.makedirs(CACHE, exist_ok=True); cp = os.path.join(CACHE, "clash.json")
    memo = json.load(open(cp)) if os.path.exists(cp) else {}
    bbs = {n: _bb(s) for n, s in parts.items()}
    todo, res, cand = [], {}, 0
    for a, b in itertools.combinations(parts, 2):
        if not _ov(bbs[a], bbs[b]): continue
        cand += 1
        k = hashlib.sha1((keys[a] + "|" + keys[b]).encode()).hexdigest()[:20]
        if k in memo: res[(a, b)] = memo[k]
        else: todo.append(((a, b), k))
    t = time.time()
    if todo:
        for (pair, v) in pool(procs).imap_unordered(_work, [(p, PATHS[p[0]], PATHS[p[1]]) for p, _ in todo]):
            res[pair] = v
        for pair, k in todo: memo[k] = res[pair]
        json.dump(memo, open(cp, "w"))
    out = {f"{a} / {b}": v for (a, b), v in res.items() if v > thr or v < 0}
    return out, cand, len(todo), time.time() - t
