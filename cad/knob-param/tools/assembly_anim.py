#!/usr/bin/env python3
"""Assembly animation, step sheet and insertion-path clash check for the knob module (panel frame).

The model is built ONCE (stage `cache`): every part's BREP path (panel frame), a tessellated mesh (npz) and an x <= 0
half-section mesh (cut faces capped, for the cutaway camera) go to $KNOBPARAM_CACHE/anim/. Every later stage reads only
that cache (the clash check also re-reads the BREPs for its exact confirm), so a rerun after a rule edit is cheap.

The sequence is data: tools/assembly_steps.py (STEPS = ordered steps; each matches parts by regex on the part name).

Stages
  cache   build the model (knob build_all + view "panel" + the joystick stack) and cache meshes          (the heavy one)
  seq     assign every part to exactly one step; print unassigned / doubly assigned parts and empty steps
  check   insertion-path clash check (mesh filter on the swept path, exact OCC common-volume confirm) + assembled state
  sheet   steps.png (one panel per step)
  video   assembly.mp4 (1280x720, 24 fps, H.264) + assembly.gif
  all     cache, seq, check, sheet, video  (in that order, one heavy job at a time)

Run from cad/knob-param (2-core box: one worker, own cache, low priority):
  KNOB_POOL=1 KNOBPARAM_CACHE=/path/.cache-knob nice -n 15 xvfb-run -a .venv/bin/python tools/assembly_anim.py all
Options: --out DIR (default cad/assemblies/assembly-anim-<date>/), --rules FILE, --quick (low-res video for a look),
         --rebuild (ignore the cached meshes)."""
import argparse, hashlib, importlib.util, json, math, os, re, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
KP = os.path.dirname(HERE)                         # cad/knob-param
sys.path.insert(0, KP)
REPO = os.path.dirname(os.path.dirname(KP))
TOL, ANG = 0.03, 0.25                              # tessellation: chord deviation (mm), angular (rad)
CUT_X = 0.0                                        # cutaway plane x = 0 (through the knob axis and the joystick axis)
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:7.1f} s]", *a, flush=True)


def cache_dir():
    from knobparam.common.cache import CACHE
    d = os.path.join(CACHE, "anim")
    os.makedirs(d, exist_ok=True)
    return d


def _sha(s):
    return hashlib.sha1(s.encode()).hexdigest()[:20]


# ----------------------------------------------------------------------------------------------------------- cache
def _face_tris(face_w):
    """(P, T) of one meshed TopoDS_Face (orientation-aware), or None when the face has no triangulation."""
    from OCP.BRep import BRep_Tool
    from OCP.TopLoc import TopLoc_Location
    from OCP.TopAbs import TopAbs_REVERSED
    loc = TopLoc_Location()
    tri = BRep_Tool.Triangulation_s(face_w, loc)
    if tri is None or tri.NbTriangles() == 0:
        return None
    trsf = loc.Transformation()
    P = np.empty((tri.NbNodes(), 3), np.float32)
    for i in range(1, tri.NbNodes() + 1):
        p = tri.Node(i).Transformed(trsf)
        P[i - 1] = (p.X(), p.Y(), p.Z())
    T = np.empty((tri.NbTriangles(), 3), np.int32)
    for i in range(1, tri.NbTriangles() + 1):
        T[i - 1] = tri.Triangle(i).Get()
    T -= 1
    if face_w.Orientation() == TopAbs_REVERSED:
        T = T[:, ::-1].copy()
    return P, T


def _mesh_faces(shape):
    """Mesh the whole shape once, then [(face, P, T)] for every face that got a triangulation."""
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from build123d import Compound
    if not hasattr(shape, "wrapped"):              # ShapeList from a boolean
        shape = Compound(children=list(shape))
    BRepMesh_IncrementalMesh(shape.wrapped, TOL, False, ANG, True)
    out = []
    for f in shape.faces():
        r = _face_tris(f.wrapped)
        if r is not None:
            out.append((f, r[0], r[1]))
    return out


def _stack(items):
    Ps, Ts, off = [], [], 0
    for P, T in items:
        Ps.append(P); Ts.append(T + off); off += len(P)
    if not Ps:
        return np.zeros((0, 3), np.float32), np.zeros((0, 3), np.int32)
    return np.vstack(Ps), np.vstack(Ts)


def _tess(shape):
    """(P float32 (n,3), T int32 (m,3)) of the whole shape, outward winding."""
    return _stack([(P, T) for _, P, T in _mesh_faces(shape)])


def _cut_mesh(shape, bb):
    """Half section: keep x <= CUT_X. Returns (P, T, cut) where cut marks triangles on the cut plane (or None)."""
    from build123d import Box, Pos, Align, GeomType
    x0, y0, z0, x1, y1, z1 = bb
    if x0 >= CUT_X - 1e-6:
        return None                                # wholly on the removed side
    if x1 <= CUT_X + 1e-6:
        P, T = _tess(shape)
        return P, T, np.zeros(len(T), bool)
    reg = Pos(x0 - 1, y0 - 1, z0 - 1) * Box(CUT_X - x0 + 1, y1 - y0 + 2, z1 - z0 + 2, align=(Align.MIN,) * 3)
    try:
        r = shape.intersect(reg)
    except Exception:
        r = None
    if r is None:
        return None
    items, Cs = [], []
    for f, P, T in _mesh_faces(r):
        on = False
        if f.geom_type == GeomType.PLANE:
            c = f.center()
            n = f.normal_at(c)
            on = abs(c.X - CUT_X) < 1e-3 and abs(abs(n.X) - 1) < 1e-6
        items.append((P, T)); Cs.append(np.full(len(T), on))
    if not items:
        return None
    P, T = _stack(items)
    return P, T, np.concatenate(Cs)


def stage_cache(rebuild=False):
    """Build the model once; write index.json + one npz per part (mesh + half-section)."""
    from build123d import export_brep
    from knobparam.common import model
    from knobparam.assembly.build import build_all, view, PATHS
    from knobparam.assembly import joystick as js
    cd = cache_dir()
    D = model.derive(model.default_params())
    log("building the knob model (cached per part) ...")
    parts, stats, keys, owner = build_all(D)
    nb = sum(1 for s in stats if s[1] == "built")
    log(f"knob: {len(parts)} parts, {nb} modules rebuilt")
    parts, keys = view(parts, keys, D, "panel")
    paths = dict(PATHS)
    log("building the joystick stack ...")
    jp, JD = js.placed()
    jsrc = "".join(open(os.path.join(js._jsdir(), "jsparam", f), encoding="utf-8").read() for f in ("params.py", "parts.py"))
    jkey = _sha(jsrc + repr(JD.get("place_y")))
    for n, s in jp.items():
        keys[n] = "js" + jkey + n
        paths[n] = os.path.join(cd, "js_" + _sha(keys[n]) + ".brep")
        if not os.path.exists(paths[n]) or rebuild:
            export_brep(s, paths[n])
        owner[n] = "joystick"
    parts = dict(parts); parts.update(jp)
    log(f"joystick: {len(jp)} parts at (0, {JD['place_y']:.2f})")
    idx = {}
    for i, (n, s) in enumerate(parts.items()):
        b = s.bounding_box()
        bb = [b.min.X, b.min.Y, b.min.Z, b.max.X, b.max.Y, b.max.Z]
        f = os.path.join(cd, "m_" + _sha(f"{keys[n]}|{TOL}|{ANG}|{CUT_X}") + ".npz")
        if rebuild or not os.path.exists(f):
            P, T = _tess(s)
            c = _cut_mesh(s, bb)
            z = dict(P=P, T=T)
            if c is not None:
                z.update(CP=c[0], CT=c[1], CC=c[2])
            np.savez_compressed(f, **z)
            log(f"  mesh {i + 1}/{len(parts)} {n}: {len(T)} tris" + (f", cut {len(c[1])}" if c is not None else ""))
        try:
            vol = float(sum(x.volume for x in s.solids()))
        except Exception:
            vol = 0.0
        idx[n] = dict(brep=paths[n], mesh=f, bb=bb, sub=owner.get(n, ""), vol=vol)
    meta = dict(version=D["version"], branch=_git("rev-parse", "--abbrev-ref", "HEAD"), commit=_git("rev-parse", "--short", "HEAD"),
                js_place_y=JD["place_y"], clash_mm3=float(D["tgt"]["clash_mm3"]), built=time.strftime("%Y-%m-%d %H:%M"), n=len(idx))
    json.dump(dict(meta=meta, parts=idx), open(os.path.join(cd, "index.json"), "w"), indent=1)
    log(f"cache: {len(idx)} parts -> {cd}/index.json")


def _git(*a):
    import subprocess
    try:
        return subprocess.check_output(["git", "-C", REPO] + list(a), text=True).strip()
    except Exception:
        return "?"


def load_index():
    p = os.path.join(cache_dir(), "index.json")
    if not os.path.exists(p):
        sys.exit("no mesh cache: run the `cache` stage first")
    return json.load(open(p))


# ------------------------------------------------------------------------------------------------------------- seq
DIRS = {"+x": (1, 0, 0), "-x": (-1, 0, 0), "+y": (0, 1, 0), "-y": (0, -1, 0), "+z": (0, 0, 1), "-z": (0, 0, -1)}
AXES = ["+x", "-x", "+y", "-y", "+z", "-z"]


def _unit(d):
    v = np.array(DIRS[d] if isinstance(d, str) else d, float)
    return v / np.linalg.norm(v)


def dir_label(v):
    for k, u in DIRS.items():
        if np.allclose(v, u, atol=1e-6):
            return k
    return "(" + ", ".join(f"{x:+.2f}" for x in v) + ")"


def load_rules(path):
    spec = importlib.util.spec_from_file_location("assembly_steps", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.STEPS


def _bb_off(bb, off):
    return [bb[0] + off[0], bb[1] + off[1], bb[2] + off[2], bb[3] + off[0], bb[4] + off[1], bb[5] + off[2]]


def _ov(a, b, pad=0.0):
    return all(a[i] - pad < b[i + 3] and b[i] - pad < a[i + 3] for i in range(3))


def _union(bbs):
    a = np.array(bbs)
    return list(a[:, :3].min(0)) + list(a[:, 3:].max(0))


def auto_travel(moving, fixed, d, BB, margin=4.0, smax=250.0):
    """Smallest travel that starts the group clear (bounding boxes, 0.5 pad) of every part already placed, + margin."""
    s_last = 0.0
    for f in fixed:
        for m in moving:
            for s in np.arange(smax, -0.01, -0.5):
                if _ov(_bb_off(BB[m], -s * d), BB[f], 0.5):
                    s_last = max(s_last, s)
                    break
    return float(max(8.0, math.ceil(s_last + margin)))


class Plan:
    """Resolved sequence: part assignment, sub-assembly membership, directions and travels."""

    def __init__(self, rules, idx):
        self.idx = idx
        self.BB = {n: p["bb"] for n, p in idx["parts"].items()}
        names = list(idx["parts"])
        hits = {n: [] for n in names}
        for i, st in enumerate(rules):
            inc = [re.compile(r, re.I) for r in st.get("parts", [])]
            exc = [re.compile(r, re.I) for r in st.get("exclude", [])]
            for n in names:
                if any(r.search(n) for r in inc) and not any(r.search(n) for r in exc):
                    hits[n].append(i)
        self.unassigned = [n for n in names if not hits[n]]
        self.double = {n: [rules[i]["id"] for i in h] for n, h in hits.items() if len(h) > 1}
        own = {i: [n for n in names if hits[n] and hits[n][0] == i] for i in range(len(rules))}
        self.steps, self.empty = [], []
        members, placed_by, joined = {}, {}, {}
        ids = [st["id"] for st in rules]
        assert len(set(ids)) == len(ids), "duplicate step ids"
        for i, st in enumerate(rules):
            sub = st.get("sub", "main")
            if st.get("join"):
                moving = list(members.get(st["join"], []))
                if not moving:
                    self.empty.append(st); continue
                joined[st["join"]] = st["id"]
            else:
                moving = own[i]
                if not moving:
                    self.empty.append(st); continue
            fixed = list(members.get(sub, []))
            base = bool(st.get("base")) or (not fixed and sub != "main")
            d = _unit(st.get("dir", "+z"))
            if base and sub != "main":
                travel = check_travel = 0.0
            else:
                # the check always starts clear of everything already placed (bounding boxes), so the whole way in is tested;
                # `travel` (rule) is only how far out the parts are drawn
                check_travel = auto_travel(moving, fixed, d, self.BB) if fixed else 0.0
                travel = check_travel if st.get("travel", "auto") == "auto" else float(st["travel"])
                check_travel = max(check_travel, travel)
            S = dict(st, k=len(self.steps), sub=sub, moving=moving, own=own[i], fixed=fixed, d=d, travel=travel,
                     check_travel=check_travel, base=base)
            self.steps.append(S)
            members.setdefault(sub, []).extend(moving)
            for n in moving:
                placed_by.setdefault(n, []).append(S["k"])
        self.members, self.joined = members, joined
        self.never_joined = [s for s in members if s != "main" and s not in joined]
        # chain of steps that move each part: its own step, then the joins of its sub, the sub's parent, ...
        self.chain = placed_by

    def offset(self, n, done, cur=None, frac=0.0):
        """Display offset of part n when steps < done are finished and step `cur` is `frac` of the way in."""
        o = np.zeros(3)
        for k in self.chain.get(n, []):
            S = self.steps[k]
            if S["base"] and S["sub"] != "main":
                continue
            if k < done:
                continue
            rem = (1.0 - frac) if k == cur else 1.0
            o -= rem * S["travel"] * S["d"]
        return o


def stage_seq(plan, quiet=False):
    print(f"\nSEQUENCE ({len(plan.steps)} steps, {len(plan.empty)} empty placeholders):")
    for S in plan.steps:
        tag = f"[{S['sub']}] " if S["sub"] != "main" else ""
        j = f" (moves sub-assembly '{S['join']}')" if S.get("join") else ""
        mv = "base" if S["base"] and S["sub"] != "main" else f"{dir_label(S['d'])} {S['travel']:.0f} mm (checked from {S['check_travel']:.0f})"
        print(f"  {S['k'] + 1:2d}. {tag}{S['name']}{j}: {len(S['moving'])} parts, {mv}")
    for st in plan.empty:
        print(f"  EMPTY  {st['id']}: {st['name']} (no part matches yet)")
    print(f"UNASSIGNED ({len(plan.unassigned)}): " + ("; ".join(plan.unassigned) if plan.unassigned else "none"))
    print(f"DOUBLY ASSIGNED ({len(plan.double)}): " + ("; ".join(f"{n} -> {v}" for n, v in plan.double.items()) if plan.double else "none"))
    if plan.never_joined:
        print("SUB-ASSEMBLIES NEVER JOINED:", plan.never_joined)
    return not plan.unassigned and not plan.double

# ----------------------------------------------------------------------------------------------------------- check
# Herringbone pairs: the 25° teeth cannot slide straight in; the pinions turn as the part goes down (a screw motion), so a
# straight-line hit between them is reported as "helical mesh", not as a blocked path.
HELICAL = re.compile(r"^bottom internal ring|^idler pinion \d$|^encoder pinion$", re.I)
NEAR, FINE, COARSE = 5.0, 0.25, 1.0       # last NEAR mm at FINE steps, further out at <= COARSE
N_EXACT = 2                               # exact OCC confirmations per (moving, fixed) pair: middle and last mesh hit
SCHED = "v2"
WORKERS = max(1, int(os.environ.get("KNOB_POOL", "2")))   # parallel pair checks (fork); the 2-core box: 2


class Geo:
    """Meshes (vtk) and BREPs (OCC) of the cached parts, loaded on demand."""

    def __init__(self, idx):
        self.P = idx["parts"]
        self._pd, self._br, self._pts = {}, {}, {}
        self.n_exact = 0
        self.t_exact = 0.0

    def pd(self, n):
        if n not in self._pd:
            import pyvista as pv
            z = np.load(self.P[n]["mesh"])
            P, T = z["P"].astype(float), z["T"]
            self._pd[n] = pv.PolyData(P, np.hstack([np.full((len(T), 1), 3), T]).ravel())
        return self._pd[n]

    def brep(self, n):
        if n not in self._br:
            from build123d import import_brep
            self._br[n] = import_brep(self.P[n]["brep"])
        return self._br[n]

    def exact(self, m, f, off):
        """Common volume (mm³) of m moved by off with f, and the smallest extent of the overlap (mm). -1 if OCC fails."""
        from build123d import Pos
        t = time.time()
        try:
            r = (Pos(*off) * self.brep(m)).intersect(self.brep(f))
            sol = [] if r is None else (list(r.solids()) if hasattr(r, "solids") else [x for i in r for x in i.solids()])
            v = float(sum(x.volume for x in sol))
            dmin = 0.0
            if sol and v > 0:
                from build123d import Compound
                b = Compound(children=sol).bounding_box()
                dmin = float(min(b.size.X, b.size.Y, b.size.Z))
        except Exception:
            v, dmin = -1.0, 0.0
        self.n_exact += 1
        self.t_exact += time.time() - t
        return v, dmin


def _ext(bb, d):
    return float(abs(d[0]) * (bb[3] - bb[0]) + abs(d[1]) * (bb[4] - bb[1]) + abs(d[2]) * (bb[5] - bb[2]))


def schedule(L, coarse):
    near = min(NEAR, L)
    s = list(np.arange(L, near, -coarse)) + list(np.arange(near, 0.0, -FINE))
    return [round(float(x), 4) for x in s if x > 1e-6]


class Checker:
    def __init__(self, idx, memo_path, thr):
        self.idx = idx
        self.geo = Geo(idx)
        self.BB = {n: p["bb"] for n, p in idx["parts"].items()}
        self.memo_path = memo_path
        self.memo = json.load(open(memo_path)) if memo_path and os.path.exists(memo_path) else {}
        self.thr = thr
        self.n_mesh = 0

    def save(self):
        if self.memo_path:
            tmp = self.memo_path + ".tmp"
            json.dump(self.memo, open(tmp, "w"))
            os.replace(tmp, self.memo_path)      # a restart mid-write keeps the last good memo

    def _key(self, *a):
        return _sha("|".join(str(x) for x in a))

    def pair_key(self, m, f, d, L):
        P = self.geo.P
        return self._key(SCHED, P[m]["mesh"], P[f]["mesh"], *np.round(d, 6), round(L, 3))

    def pair(self, m, f, d, L):
        """Insertion of m along d from L to 0 (mm) past fixed f. Returns {hits: [s...], exact: [[s, vol, depth]...]}."""
        k = self.pair_key(m, f, d, L)
        if k in self.memo:
            return self.memo[k]
        bm, bf = self.BB[m], self.BB[f]
        coarse = float(np.clip(0.45 * min(_ext(bm, d), _ext(bf, d)), FINE, COARSE))
        cand = [s for s in schedule(L, coarse) if _ov(_bb_off(bm, -s * d), bf, 0.02)]
        hits = []
        if cand:
            import vtk
            cf = vtk.vtkCollisionDetectionFilter()
            cf.SetInputData(0, self.geo.pd(m)); cf.SetInputData(1, self.geo.pd(f))
            tr = vtk.vtkTransform(); cf.SetTransform(0, tr); cf.SetMatrix(1, vtk.vtkMatrix4x4())
            cf.SetCollisionModeToFirstContact()
            for s in cand:
                tr.Identity(); tr.Translate(*(-s * d)); cf.Update(); self.n_mesh += 1
                if cf.GetNumberOfContacts() > 0:
                    hits.append(s)
        ex = []
        if hits:
            # the middle of the hit run (deepest for a part passing an obstacle) and the last hit (deepest for one seating into it)
            picks = sorted({hits[len(hits) // 2], hits[-1]}, reverse=True)
            for s in picks[:N_EXACT]:
                v, dm = self.geo.exact(m, f, list(-s * d))
                ex.append([s, round(v, 4), round(dm, 3)])
        r = dict(hits=hits, exact=ex)
        self.memo[k] = r
        return r

    def home(self, a, b, exact=False):
        """Assembled state: do a and b touch (mesh)? The exact common volume only on request: the knob build's own all-pairs
        clash check (exact, every part) already covers the assembled state, so this stage only lists the touching pairs."""
        P = self.geo.P
        k = self._key("home", P[a]["mesh"], P[b]["mesh"], exact)
        if k in self.memo:
            return self.memo[k]
        import vtk
        cf = vtk.vtkCollisionDetectionFilter()
        cf.SetInputData(0, self.geo.pd(a)); cf.SetInputData(1, self.geo.pd(b))
        cf.SetMatrix(0, vtk.vtkMatrix4x4()); cf.SetMatrix(1, vtk.vtkMatrix4x4())
        cf.SetCollisionModeToFirstContact(); cf.Update(); self.n_mesh += 1
        r = dict(touch=cf.GetNumberOfContacts() > 0, vol=0.0, depth=0.0)
        if r["touch"] and exact:
            r["vol"], r["depth"] = self.geo.exact(a, b, [0.0, 0.0, 0.0])
        self.memo[k] = r
        return r

    def step_tasks(self, moving, fixed, d, L):
        """(m, f, d, L, key) for every pair this step meets that is not in the memo yet."""
        out = []
        for m in moving:
            sw = _union([self.BB[m], _bb_off(self.BB[m], -L * d)])
            for f in fixed:
                if _ov(sw, self.BB[f], 0.05):
                    k = self.pair_key(m, f, d, L)
                    if k not in self.memo:
                        out.append((m, f, tuple(float(x) for x in d), float(L), k))
        return out

    def prefetch(self, tasks, label=""):
        """Run the pair checks in WORKERS forked processes (each its own meshes and BREPs); memo saved as results come in."""
        seen, todo = set(), []
        for t in tasks:
            if t[4] not in seen and t[4] not in self.memo:
                seen.add(t[4]); todo.append(t)
        if not todo:
            return
        t0 = time.time()
        log(f"  {label}{len(todo)} pair sweeps to run ({WORKERS} workers) ...")
        if WORKERS == 1:
            for i, (m, f, d, L, k) in enumerate(todo):
                self.pair(m, f, np.array(d), L)
                if (i + 1) % 25 == 0:
                    self.save(); log(f"    {i + 1}/{len(todo)} ({time.time() - t0:.0f} s)")
        else:
            import multiprocessing as mp
            bbv = lambda n: float(np.prod(np.array(self.BB[n][3:]) - np.array(self.BB[n][:3])))
            todo.sort(key=lambda t: -(bbv(t[0]) + bbv(t[1])))   # the big (slow) pairs first, so the pool ends evenly
            with mp.get_context("fork").Pool(WORKERS, _winit, (self.idx, self.thr)) as pool:
                for i, (k, r, nm, ne, te) in enumerate(pool.imap_unordered(_wpair, todo, chunksize=1)):
                    self.memo[k] = r
                    self.n_mesh += nm; self.geo.n_exact += ne; self.geo.t_exact += te
                    if (i + 1) % 25 == 0 or i + 1 == len(todo):
                        self.save(); log(f"    {i + 1}/{len(todo)} ({time.time() - t0:.0f} s)")
        self.save()

    def classify(self, m, f, res):
        if not res["hits"]:
            return None
        vols = [v for _, v, _ in res["exact"]]
        if any(v > self.thr for v in vols):
            return "helical" if (HELICAL.search(m) and HELICAL.search(f)) else "clash"
        if any(v < 0 for v in vols):
            return "occ-fail"
        return "contact"

    def step_events(self, moving, fixed, d, L, expect=()):
        """Every (moving, fixed) pair met on the way in. `expect` (from the step rule): [(rx moving, rx fixed, kind, why)]
        marks overlaps that are not a blocked path (a flex that bends on the way in, a screw cutting its thread)."""
        ev = []
        for m in moving:
            sw = _union([self.BB[m], _bb_off(self.BB[m], -L * d)])
            for f in fixed:
                if not _ov(sw, self.BB[f], 0.05):
                    continue
                res = self.pair(m, f, d, L)
                c = self.classify(m, f, res)
                if c:
                    why = ""
                    if c == "clash":
                        for rm, rf, kind, w in expect:
                            if re.search(rm, m, re.I) and re.search(rf, f, re.I):
                                c, why = kind, w
                                break
                    good = [e for e in res["exact"] if e[1] > self.thr]
                    vmax = max([e[1] for e in res["exact"]] + [0.0])
                    ev.append(dict(moving=m, fixed=f, kind=c, why=why, s_first=res["hits"][0], s_last=res["hits"][-1],
                                   n_hits=len(res["hits"]), vmax=vmax, s_confirmed=[e[0] for e in good],
                                   depth=max([e[2] for e in good] + [0.0])))
        return ev


_W = None


def _winit(idx, thr):
    global _W
    _W = Checker(idx, None, thr)


def _wpair(t):
    m, f, d, L, k = t
    n0, e0, t0 = _W.n_mesh, _W.geo.n_exact, _W.geo.t_exact
    r = _W.pair(m, f, np.array(d), L)
    return k, r, _W.n_mesh - n0, _W.geo.n_exact - e0, _W.geo.t_exact - t0


def _order_steps(plan, ck, order, dirs=None):
    """[(k, moving, fixed, d, L or None)] for a step order; travels re-derived (bbox clear)."""
    members, out = {}, []
    for k in order:
        S = plan.steps[k]
        moving = list(members.get(S["join"], [])) if S.get("join") else S["own"]
        fixed = list(members.get(S["sub"], []))
        d = dirs.get(k, S["d"]) if dirs else S["d"]
        L = None
        if fixed and not (S["base"] and S["sub"] != "main"):
            L = max(auto_travel(moving, fixed, d, ck.BB), S["travel"] if np.allclose(d, S["d"]) else 0.0)
        out.append((k, moving, fixed, d, L))
        members.setdefault(S["sub"], []).extend(moving)
    return out


def run_order(plan, ck, order, dirs=None, label=""):
    """Check a step order (list of step indices into plan.steps); returns {k: events}. The pair sweeps run in parallel first."""
    seq = _order_steps(plan, ck, order, dirs)
    ck.prefetch([t for k, mv, fx, d, L in seq if L is not None for t in ck.step_tasks(mv, fx, d, L)], label)
    return {k: (ck.step_events(mv, fx, d, L, plan.steps[k].get("expect", ())) if L is not None else [])
            for k, mv, fx, d, L in seq}


def _placed_in(plan, k, f):
    """The step that put part f into step k's sub-assembly (the join step for a part that came in with a sub)."""
    sub = plan.steps[k]["sub"]
    for j in plan.chain[f]:
        if plan.steps[j]["sub"] == sub and j < k:
            return j
    return None


def stage_check(plan, idx, out, alts_on=False):
    t0 = time.time()
    thr = float(idx["meta"].get("clash_mm3", 1e-3))
    ck = Checker(idx, os.path.join(cache_dir(), "check_memo.json"), thr)
    order = list(range(len(plan.steps)))
    log("insertion paths ...")
    ev = run_order(plan, ck, order)
    ck.save()
    for k in order:
        S = plan.steps[k]
        bad = [e for e in ev[k] if e["kind"] == "clash"]
        log(f"  {k + 1:2d}. {S['name'][:60]:60s} {len(ev[k]):3d} touching pairs, {len(bad)} clash")
    log("assembled state (every pair whose boxes overlap; touching only, the build's clash check has the volumes) ...")
    names = list(idx["parts"])
    home = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if not _ov(ck.BB[a], ck.BB[b], 0.01):
                continue
            r = ck.home(a, b)
            if r["touch"]:
                home.append(dict(a=a, b=b, vol=r["vol"], depth=r["depth"]))
    ck.save()
    home_clash = [h for h in home if h["vol"] > thr or h["vol"] < 0]
    log(f"  {len(home)} touching pairs at home, {len(home_clash)} with volume > {thr} mm³")
    # alternatives for blocked steps (--alts: every other axis, and the step moved before each blocker; slow)
    alts = {}
    for k in (order if alts_on else []):
        bad = [e for e in ev[k] if e["kind"] == "clash"]
        if not bad:
            continue
        S = plan.steps[k]
        A = dict(dirs={}, reorder={})
        for ax in AXES:
            d = _unit(ax)
            if np.allclose(d, S["d"]):
                continue
            r = run_order(plan, ck, _prefix(plan, k) + [k], {k: d}, f"step {k + 1} {ax}: ")[k]
            A["dirs"][ax] = sum(1 for e in r if e["kind"] == "clash")
        blockers = sorted({_placed_in(plan, k, e["fixed"]) for e in bad} - {None})
        for j in blockers:
            new = order[:j] + [k] + [x for x in order[j:] if x != k]
            r = run_order(plan, ck, new, None, f"step {k + 1} before {plan.steps[j]['id']}: ")
            span = new[j:k + 1]   # k itself, then the steps it jumped over
            n = sum(1 for x in span for e in r[x] if e["kind"] == "clash")
            A["reorder"][plan.steps[j]["id"]] = dict(clashes=n, which=[(plan.steps[x]["id"], e["moving"], e["fixed"])
                                                                     for x in span for e in r[x] if e["kind"] == "clash"][:6])
        alts[k] = A
        log(f"  alternatives for {k + 1}: dirs {A['dirs']}, reorder {{{', '.join(f'{a}: {b['clashes']}' for a, b in A['reorder'].items())}}}")
    ck.save()
    res = dict(meta=idx["meta"], thr=thr, steps=[dict(k=S["k"], id=S["id"], events=ev[S["k"]]) for S in plan.steps],
               home=home, alts={plan.steps[k]["id"]: v for k, v in alts.items()},
               stats=dict(mesh_tests=ck.n_mesh, exact=ck.geo.n_exact, t_exact=round(ck.geo.t_exact, 1), wall=round(time.time() - t0, 1)))
    os.makedirs(out, exist_ok=True)
    json.dump(res, open(os.path.join(cache_dir(), "check.json"), "w"), indent=1)
    json.dump(res, open(os.path.join(out, "check.json"), "w"), indent=1)
    open(os.path.join(out, "check.txt"), "w").write(report_text(plan, res))
    log(f"check done: {ck.n_mesh} mesh tests, {ck.geo.n_exact} exact OCC confirms ({ck.geo.t_exact:.0f} s)")
    return res


def report_text(plan, res):
    """Plain-text summary of the insertion-path check (the same facts the captions and the sheet show)."""
    m = res["meta"]
    L = [f"Assembly insertion-path check, knob {m['version']} ({m['branch']} @ {m['commit']}, cache built {m['built']}), "
         f"{len(plan.steps)} steps, {m['n']} parts. Clash = common volume > {res['thr']} mm³ (exact OCC) somewhere on the way in.",
         "Kinds: clash (blocked), helical (herringbone teeth: they screw in, a straight push is expected to hit), contact (touch, no volume).",
         ""]
    nclash = 0
    for st in res["steps"]:
        S = plan.steps[st["k"]]
        ev = st["events"]
        bad = [e for e in ev if e["kind"] == "clash"]
        nclash += len(bad)
        kinds = {}
        for e in ev:
            kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
        tag = "CLASH" if bad else ("ok" if not ev else "ok (" + ", ".join(f"{v} {k}" for k, v in kinds.items()) + ")")
        L.append(f"{S['k'] + 1:2d}. [{S['sub']}] {S['name']}: {dir_label(S['d'])}, {S['check_travel']:.0f} mm checked -> {tag}")
        for e in sorted(bad, key=lambda e: -e["vmax"]):
            L.append(f"      {e['moving']}  x  {e['fixed']}: up to {e['vmax']:.3f} mm³, depth {e['depth']:.2f}, "
                     f"from {e['s_first']:.2f} to {e['s_last']:.2f} mm before home")
        for e in ev:
            if e["kind"] not in ("clash", "contact"):
                L.append(f"      ({e['kind']}) {e['moving']}  x  {e['fixed']}: {e['vmax']:.3f} mm³"
                         + (f"; {e['why']}" if e.get("why") else ""))
        if S["id"] in res.get("alts", {}):
            A = res["alts"][S["id"]]
            L.append(f"      other directions (clashes): {A['dirs']}")
            for j, r in A["reorder"].items():
                L.append(f"      moved before '{j}': {r['clashes']} clashes {r['which'][:3]}")
    hc = [h for h in res["home"] if h["vol"] > res["thr"] or h["vol"] < 0]
    L += ["", f"Assembled state: {len(res['home'])} touching pairs, {len(hc)} with volume over {res['thr']} mm³"]
    L += [f"      {h['a']}  x  {h['b']}: {h['vol']:.3f} mm³" for h in hc]
    L += ["", f"TOTAL: {nclash} clash events on the insertion paths; stats {res['stats']}"]
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------------------------------------- sheet and video
VIEW_DIR = np.array([1.0, 0.32, 0.42])    # camera direction from the target: from +x (the cut face), a little above and in front
FOV = 30.0
CLEAR_OPACITY = 0.35


def _dark(hexc, k=0.6):
    h = hexc.lstrip("#"); r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % tuple(int(v * k) for v in (r, g, b))


class Scene:
    """Half-section (x <= 0) meshes of every part as pyvista actors; parts move by actor position, appear when their step starts."""

    def __init__(self, plan, idx, size):
        import pyvista as pv
        from knobparam.assembly.colours import colour, see_through
        self.plan, self.size = plan, size
        self.pl = pv.Plotter(off_screen=True, window_size=size)
        self.pl.set_background("white")
        try:
            pass  # depth peeling drops every translucent actor under xvfb here; plain alpha blending instead
        except Exception:
            pass
        self.actors, self.first, self.bb = {}, {}, {}
        for n, p in idx["parts"].items():
            z = np.load(p["mesh"])
            if "CP" not in z:
                continue                                   # wholly on the cut-away side
            P, T, C = z["CP"].astype(float), z["CT"], z["CC"].astype(bool)
            col, clear = colour(n), see_through(n)
            acts = []
            for sel, c, cut in ((~C, col, False), (C, _dark(col), True)):
                if not sel.any():
                    continue
                m = pv.PolyData(P, np.hstack([np.full((int(sel.sum()), 1), 3), T[sel]]).ravel())
                op = (0.75 if cut else CLEAR_OPACITY) if clear else 1.0
                a = self.pl.add_mesh(m, color=_dark(c, 0.8) if clear else c, opacity=op, smooth_shading=False,
                                     ambient=0.3, diffuse=0.75, specular=0.1)
                acts.append(a)
                if clear and not cut:   # clear parts: draw their feature edges so they read on a white background
                    fe = m.extract_feature_edges(35)
                    if fe.n_points:
                        acts.append(self.pl.add_mesh(fe, color="#5a7f8c", line_width=1.0, opacity=0.7))
            self.actors[n] = acts
            self.first[n] = min(plan.chain.get(n, [0]))
            self.bb[n] = np.array(p["bb"])
        self.cam = None

    def pose(self, done, cur=None, frac=0.0):
        """Show steps < done finished, step cur at frac. Returns the bounding box of what is visible."""
        lo, hi = np.full(3, 1e9), np.full(3, -1e9)
        upto = cur if cur is not None else done - 1
        for n, acts in self.actors.items():
            vis = self.first[n] <= upto
            o = self.plan.offset(n, done, cur, frac)
            for a in acts:
                a.SetVisibility(vis)
                a.SetPosition(*o)
            if vis:
                b = self.bb[n]
                lo = np.minimum(lo, np.minimum(b[:3], [min(b[0], 0.0), b[1], b[2]]) + o)
                hi = np.maximum(hi, np.array([min(b[3], 0.0), b[4], b[5]]) + o)
        return lo, hi

    def frame_cam(self, lo, hi):
        c = (lo + hi) / 2
        r = 0.5 * float(np.linalg.norm(hi - lo))
        aspect = self.size[0] / self.size[1]
        dist = 0.92 * r / math.sin(math.radians(FOV / 2)) / min(1.0, aspect) ** 0.5
        return np.concatenate([c, [max(dist, 60.0)]])

    def set_cam(self, cam):
        c, dist = cam[:3], cam[3]
        d = VIEW_DIR / np.linalg.norm(VIEW_DIR)
        self.pl.camera_position = [tuple(c + dist * d), tuple(c), (0, 1, 0)]
        self.pl.camera.view_angle = FOV

    def caption(self, lines, color="black", fs=None):
        fs = fs or max(9, int(self.size[0] / 95))
        for i in range(4):
            self.pl.remove_actor(f"cap{i}")
        y = self.size[1] - 8
        for i, (t, c) in enumerate(lines[:4]):
            y -= int(fs * (1.9 if i == 0 else 1.6))
            self.pl.add_text(t, position=(12, y), font_size=fs if i == 0 else int(fs * 0.85), color=c, name=f"cap{i}")

    def grab(self):
        return self.pl.screenshot(None, return_img=True)


def _events(plan):
    p = os.path.join(cache_dir(), "check.json")
    if not os.path.exists(p):
        log("no check results yet (run the `check` stage): captions show no clash status")
        return {}
    res = json.load(open(p))
    return {st["id"]: st["events"] for st in res["steps"]}


def _step_lines(S, n_steps, ev):
    bad = [e for e in ev.get(S["id"], []) if e["kind"] == "clash"]
    tag = f" [{S['sub']}]" if S["sub"] != "main" else ""
    L = [(f"Step {S['k'] + 1}/{n_steps}{tag}: {S['name']}", "black"), (S.get("note", ""), "#404040")]
    if bad:
        e = max(bad, key=lambda e: e["vmax"])
        L.append((f"CLASH on the way in: {e['moving'][:48]} x {e['fixed'][:48]} ({e['vmax']:.2f} mm³)"
                  + (f" +{len(bad) - 1} more" if len(bad) > 1 else ""), "#c00000"))
    elif S["id"] in ev:
        soft = sorted({(e["kind"], e.get("why", "")) for e in ev[S["id"]] if e["kind"] not in ("clash", "contact")})
        L.append(("insertion path clear" + (": " + "; ".join(f"{k}{' (' + w + ')' if w else ''}" for k, w in soft)[:110]
                                            if soft else ""), "#1a7f37"))
    return L


def _ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def stage_video(plan, idx, out, quick=False):
    import subprocess
    os.makedirs(out, exist_ok=True)
    size = (640, 360) if quick else (1280, 720)
    fps = 12 if quick else 24
    move, hold, blend = (14, 5, 5) if quick else (30, 10, 10)
    ev = _events(plan)
    sc = Scene(plan, idx, size)
    mp4 = os.path.join(out, "assembly.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}", "-r", str(fps),
           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", mp4]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = len(plan.steps)
    meta = idx["meta"]
    foot = f"knob {meta['version']} ({meta['branch']} @ {meta['commit']}) · cut at x = 0 · clear parts at {int(CLEAR_OPACITY * 100)} %"
    prev = None
    nf = 0
    for S in plan.steps:
        k = S["k"]
        lo0, hi0 = sc.pose(k, k, 0.0)
        lo1, hi1 = sc.pose(k + 1, None, 0.0)
        cam = sc.frame_cam(np.minimum(lo0, lo1), np.maximum(hi0, hi1))
        lines = _step_lines(S, n, ev) + [(foot, "#808080")]
        sc.caption(lines)
        still = S["base"] and S["sub"] != "main"
        frames = ([0.0] * hold) + ([] if still else [_ease(i / (move - 1)) for i in range(move)]) + [1.0] * hold
        for i, f in enumerate(frames):
            if f >= 1.0:
                sc.pose(k + 1, None, 0.0)
            else:
                sc.pose(k, k, f)
            t = min(1.0, i / blend) if prev is not None else 1.0
            sc.set_cam(prev + (cam - prev) * _ease(t) if prev is not None else cam)
            ff.stdin.write(np.ascontiguousarray(sc.grab()[:, :, :3]).tobytes()); nf += 1
        prev = cam
        log(f"  video step {k + 1}/{n}: {len(frames)} frames")
    for _ in range(fps * 2):
        ff.stdin.write(np.ascontiguousarray(sc.grab()[:, :, :3]).tobytes()); nf += 1
    ff.stdin.close(); ff.wait()
    gif = os.path.join(out, "assembly.gif")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-vf",
                    "fps=8,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer",
                    gif], check=True)
    log(f"video: {nf} frames -> {mp4}, {gif}")


def stage_sheet(plan, idx, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(out, exist_ok=True)
    ev = _events(plan)
    size = (560, 400)
    sc = Scene(plan, idx, size)
    n = len(plan.steps)
    cols = 6
    rows = int(math.ceil(n / cols))
    fig, axs = plt.subplots(rows, cols, figsize=(cols * 4.0, rows * 3.35), dpi=110)
    for ax in axs.ravel():
        ax.axis("off")
    for S in plan.steps:
        k = S["k"]
        still = S["base"] and S["sub"] != "main"
        lo0, hi0 = sc.pose(k, k, 0.0)
        lo1, hi1 = sc.pose(k + 1, None, 0.0)
        sc.set_cam(sc.frame_cam(np.minimum(lo0, lo1), np.maximum(hi0, hi1)))
        sc.pose(k + 1, None, 0.0) if still else sc.pose(k, k, 0.0)
        for i in range(4):
            sc.pl.remove_actor(f"cap{i}")
        img = sc.grab()
        ax = axs.ravel()[k]
        ax.imshow(img)
        bad = [e for e in ev.get(S["id"], []) if e["kind"] == "clash"]
        tag = f"[{S['sub']}] " if S["sub"] != "main" else ""
        mv = "" if still else f"  ({dir_label(S['d'])})"
        title = f"{k + 1}. {tag}{S['name']}{mv}"
        import textwrap
        ax.set_title("\n".join(textwrap.wrap(title, 52)[:3]), fontsize=7.5, color="#c00000" if bad else "black", loc="left")
        if bad:
            e = max(bad, key=lambda e: e["vmax"])
            ax.text(0.01, 0.02, "\n".join(textwrap.wrap(f"CLASH: {e['moving']} x {e['fixed']} {e['vmax']:.2f} mm³", 70)[:2]),
                    transform=ax.transAxes, fontsize=6.2, color="#c00000", va="bottom",
                    bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=1.5))
        log(f"  sheet step {k + 1}/{n}")
    meta = idx["meta"]
    fig.suptitle(f"Assembly sequence, knob {meta['version']} ({meta['branch']} @ {meta['commit']}): each panel shows the step's "
                 f"parts at the start of their move (cut at x = 0); red = a clash somewhere on the way in", fontsize=12, x=0.01,
                 ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    p = os.path.join(out, "steps.png")
    fig.savefig(p)
    log(f"sheet -> {p}")


def _prefix(plan, k):
    """Steps before k (same order)."""
    return list(range(k))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["cache", "seq", "check", "sheet", "video", "all"])
    ap.add_argument("--rebuild", action="store_true", help="re-tessellate every part")
    ap.add_argument("--rules", default=os.path.join(HERE, "assembly_steps.py"))
    ap.add_argument("--out", default=os.path.join(REPO, "cad", "assemblies", "assembly-anim-" + time.strftime("%Y-%m-%d")))
    ap.add_argument("--quick", action="store_true", help="low-res, low-fps video for a look")
    ap.add_argument("--alts", action="store_true", help="check: also try other directions / earlier slots for blocked steps (slow)")
    a = ap.parse_args()
    if a.stage in ("cache", "all"):
        stage_cache(a.rebuild)
    idx = load_index()
    plan = Plan(load_rules(a.rules), idx)
    ok = stage_seq(plan)
    if a.stage == "seq":
        sys.exit(0 if ok else 1)
    if not ok:
        sys.exit("fix the rules first: every part must be in exactly one step")
    if a.stage in ("check", "all"):
        stage_check(plan, idx, a.out, a.alts)
    if a.stage in ("sheet", "all"):
        stage_sheet(plan, idx, a.out)
    if a.stage in ("video", "all"):
        stage_video(plan, idx, a.out, a.quick)


if __name__ == "__main__":
    main()
