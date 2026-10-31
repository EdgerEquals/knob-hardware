"""Per-part build cache. A part builder gets a TrackingDict; the keys it reads are recorded. The cache key is a hash of the part
module source + the values of exactly those keys, so a param change only rebuilds the parts that read it."""
import hashlib, json, os, pickle, time
from build123d import Compound, Shape, export_brep, import_brep

from .util import PKG
CACHE = os.environ.get("KNOBPARAM_CACHE", os.path.join(PKG, ".cache"))

class TrackingDict(dict):
    """Records the keys a part builder reads. D is already restricted to the sub-assembly's scope (interface + own + declared
    imports), so reading anything else raises ScopeError."""
    def __init__(self, d): super().__init__(d); self.used = set()
    def __getitem__(self, k):
        self.used.add(k)
        try: return super().__getitem__(k)
        except KeyError: raise ScopeError(f"{k!r} is outside this sub-assembly's scope (interface + own + declared IMPORTS)") from None
    def get(self, k, default=None): self.used.add(k); return super().get(k, default)

class ScopeError(KeyError): pass

def _h(obj): return hashlib.sha1(json.dumps(obj, sort_keys=True, default=repr).encode()).hexdigest()[:16]

def src_hash(mod):
    import inspect
    srcs = [inspect.getsource(mod)]
    for dep in getattr(mod, "SRC_DEPS", []): srcs.append(inspect.getsource(dep))
    return _h(srcs)

def part_hash(mod, D, used): return _h([src_hash(mod), {k: D[k] for k in sorted(used)}])

def build_module(mod, D, stats):
    """mod.build(D) -> {name: shape}. Returns (shapes, key)."""
    os.makedirs(CACHE, exist_ok=True)
    idx_path = os.path.join(CACHE, mod.__name__.split(".")[-1] + ".json")
    if os.path.exists(idx_path):
        idx = json.load(open(idx_path))
        if idx.get("src") == src_hash(mod) and all(k in D for k in idx["used"]):
            key = part_hash(mod, D, idx["used"])
            pk = os.path.join(CACHE, f"{key}.pkl")
            if os.path.exists(pk):   # any earlier build with these values (switching back is free)
                names = pickle.load(open(pk, "rb"))
                paths = {n: os.path.join(CACHE, f"{key}_{i}.brep") for i, n in enumerate(names)}
                out = {n: import_brep(paths[n]) for n in names}
                stats.append((mod.__name__, "cached", 0.0)); return out, key, paths
    t = time.time(); TD = TrackingDict(D)
    out = mod.build(TD)
    used = sorted(TD.used); key = part_hash(mod, D, used)
    paths = {}
    for i, (n, s) in enumerate(out.items()):
        paths[n] = os.path.join(CACHE, f"{key}_{i}.brep"); export_brep(s, paths[n])
    pickle.dump(list(out.keys()), open(os.path.join(CACHE, f"{key}.pkl"), "wb"))
    json.dump(dict(src=src_hash(mod), used=used, key=key), open(idx_path, "w"))
    stats.append((mod.__name__, "built", time.time() - t)); return out, key, paths

# ---- worker pool (SPAWN, not fork: forking after OCC has run its thread pool deadlocks the children) ----
_POOL = None
_SHAPES = {}
def pool(n=8):
    global _POOL
    if _POOL is None:
        from multiprocessing import get_context
        _POOL = get_context("spawn").Pool(n)
    return _POOL
def load(path):
    if path not in _SHAPES: _SHAPES[path] = import_brep(path)
    return _SHAPES[path]
