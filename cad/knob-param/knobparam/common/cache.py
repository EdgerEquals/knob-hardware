"""Per-part build cache. A part builder gets a TrackingDict; the keys it reads are recorded. The cache key is a hash of the part
module source + the values of exactly those keys, so a param change only rebuilds the parts that read it."""
import hashlib, json, os, pickle, time
from build123d import Compound, Shape, export_brep, import_brep

from .util import PKG, overlay   # overlay lives in util so builders don't depend on cache.py
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
    def __contains__(self, k): self.used.add(k); return super().__contains__(k)
    # Anything that walks the whole dict (dict(D), {**D}, D.items()) would read keys without recording them.
    # Record everything instead: that one part over-invalidates, and it never goes stale. Prefer overlay(D, module=m).
    def _all(self): self.used.update(super().keys())
    def __iter__(self): self._all(); return super().__iter__()
    def keys(self): self._all(); return super().keys()
    def items(self): self._all(); return super().items()
    def values(self): self._all(); return super().values()
    def copy(self): self._all(); return dict(super().items())

class ScopeError(KeyError): pass

def _h(obj): return hashlib.sha1(json.dumps(obj, sort_keys=True, default=repr).encode()).hexdigest()[:16]

def src_closure(name, seen=None):
    """Every knobparam module that `name` imports, anywhere in its source, transitively. AST, so it also sees imports inside a function."""
    import ast, importlib.util
    seen = set() if seen is None else seen
    if name in seen: return seen
    try: spec = importlib.util.find_spec(name)
    except Exception: return seen
    if spec is None or not (spec.origin or "").endswith(".py"): return seen
    seen.add(name)
    pkg = name if spec.submodule_search_locations else name.rpartition(".")[0]
    for n in ast.walk(ast.parse(open(spec.origin, encoding="utf-8").read())):
        if isinstance(n, ast.Import): cands = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            base = importlib.util.resolve_name("." * n.level + (n.module or ""), pkg) if n.level else (n.module or "")
            cands = [base] + [f"{base}.{a.name}" for a in n.names]
        else: continue
        for c in cands:
            if c.split(".")[0] == "knobparam": src_closure(c, seen)
    return seen

_SRC = {}
def src_hash(mod):
    import importlib.util
    if mod.__name__ not in _SRC:
        names = set(src_closure(mod.__name__))
        for dep in getattr(mod, "SRC_DEPS", []): names |= src_closure(dep.__name__)
        names = sorted(names)
        _SRC[mod.__name__] = _h([[n, open(importlib.util.find_spec(n).origin, "rb").read().decode()] for n in names])
    return _SRC[mod.__name__]

_ABSENT = "<absent>"
def part_hash(mod, D, used): return _h([src_hash(mod), {k: D.get(k, _ABSENT) for k in sorted(used)}])

def build_module(mod, D, stats):
    """mod.build(D) -> {name: shape}. Returns (shapes, key)."""
    os.makedirs(CACHE, exist_ok=True)
    idx_path = os.path.join(CACHE, mod.__name__.split(".")[-1] + ".json")
    if os.path.exists(idx_path):
        idx = json.load(open(idx_path))
        if True:   # the key already hashes the source, so an old index is safe to try (reverting an edit is free)
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
        # each spawned worker loads OCC (~0.7 GB); cap by CPUs or KNOB_POOL so small VMs do not run out of memory
        n = int(os.environ.get("KNOB_POOL", min(n, os.cpu_count() or 2)))
        _POOL = get_context("spawn").Pool(max(1, n))
    return _POOL
def load(path):
    if path not in _SHAPES: _SHAPES[path] = import_brep(path)
    return _SHAPES[path]
