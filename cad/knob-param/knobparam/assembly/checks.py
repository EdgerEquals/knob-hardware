"""Checks runner. LOCAL checks live in each sub-assembly (checks.py, own parts + scope only); the CROSS checks below need parts
or values from more than one sub-assembly and are owned by the assembly agent. Plus pairwise solid clashes (bbox prefilter,
OCC intersection volume, parallel spawn pool, cached per part-hash pair)."""
import hashlib, itertools, json, math, os, time
from build123d import *
from ..common.cache import CACHE
from ..common.checks import Rows
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
    from .. import control_dial as cd, under_pcb as up
    from . import hall_dyn
    T = D["tgt"]; r = Rows("assembly"); row = r.row
    TR = (-D["travel_deg"], 0, D["travel_deg"]); on = D["screen_on_dial"]
    Dc = model.view(D, "control_dial")
    if on:
        stat = {n: parts[n] for n in parts if n.startswith("adapter part") and not n.endswith(D["b2b_at"])}
        stat["rod + nut"] = cyl(D["nut_s"] / math.sqrt(3), D["z_board_top"], D["nut_m"])
        stat["adapter cup (fixed)"] = parts["adapter cup (fixed)"]
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
        arm = cd.arm(Dc, t)
        for n, s in tips.items():
            d = arm.distance_to(s)
            if d < hmin: hmin, hwho = d, n
    row("Hall arm vs pinions / motor collar (±travel)", hmin, T["hall_vs_pinions"], f"nearest: {hwho}")
    if D["hall_layout"] == "vernier":
        cr = parts["base cradle"]; sens = [parts[n] for n in parts if n.startswith("hall sensor")]
        row("Hall arm vs cradle slot walls (±travel)", min(cd.arm(Dc, t).distance_to(cr) for t in TR), T["arm_vs_cradle"], f"slot r {D['hv_slot_r0']:.2f}-{D['hv_slot_r1']:.2f}")
        row("Hall bar / magnets vs sensor tops (air gap, ±travel)", min(cd.arm(Dc, t).distance_to(s_) for t in TR for s_ in sens), D["hv_gap"] - 0.01, f"element gap {D['hv_elem_gap']:.2f}")
        row("Hall sensors vs cradle", min(s_.distance_to(cr) for s_ in sens), T["sensor_vs_cradle"])
        H = hall_dyn.analyse(D)
        row("Hall peak field vs sensor range (mT)", H["B_peak"], 0.9 * D["hv_sensor"]["range_mt"], f"{D['hv_sensor']['part']} ±{D['hv_sensor']['range_mt']:g} mT", higher_ok=False)
        row("Hall angle noise, worst over ±travel (deg rms)", H["s_theta_worst"], 0.01, f"min |dB/dθ| {H['slope_min']:.1f} mT/deg, noise {H['noise_mT'] * 1e3:.0f} µT rms", higher_ok=False)
    if D["kb_seat_depth"] > 0:
        kb = [parts[n] for n in parts if n.startswith("knob") and "ball" not in n]
        row("seat: dial vs knob (race region)", min(parts["control dial"].distance_to(q) for q in kb), T["seat_vs_knob"])
    row("idler 1 / feel motor vs 1220 can", math.hypot(D["idler_xy"][0][0] - D["offset"], D["idler_xy"][0][1]) - D["can_r"] - D["d_pin_tip"] / 2, T["idler_motor"])
    return r

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
