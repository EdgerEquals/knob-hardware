"""The parameter model harness (owned by the assembly agent). Merges the INTERFACE params, the assembly params and the
sub-assembly params files into ONE flat dict D (same keys/values as the pre-split v0.15 params.derive()) and records each
sub-assembly's SCOPE = interface keys + its own params + its own derived keys + its declared IMPORTS.
Rules enforced here:
  * every param key has exactly one owner (no duplicates across params files),
  * a sub-assembly derive() only sees its scope (KeyError otherwise) and may not change an interface/import value,
  * every IMPORT names a key that the source sub-assembly lists in its EXPORTS."""
import copy, importlib

SUBS = ["electronics", "control_dial", "main_knob", "base_drive", "under_pcb", "case"]   # derive order (exports flow forward)
ALL = ["main_knob", "control_dial", "base_drive", "under_pcb", "electronics", "case"]     # build / report order

def sub(name): return importlib.import_module(f"knobparam.{name}")
def sub_params(name): return importlib.import_module(f"knobparam.{name}.params")
def interface(): return importlib.import_module("knobparam.assembly.interface")
def asm_params(): return importlib.import_module("knobparam.assembly.params")

class Model(dict):
    """Flat D plus .scope {sub: set(keys)}, .owner {key: owner}, .ikeys (interface keys)."""
    scope = None; owner = None; ikeys = None

def owners():
    own = {}
    for o, P in [("interface", interface().P), ("assembly", asm_params().P)] + [(s, sub_params(s).P) for s in SUBS]:
        for k in P:
            if k in own: raise ValueError(f"param {k!r} defined by both {own[k]} and {o}")
            own[k] = o
    return own

def default_params():
    P = {}
    P.update(copy.deepcopy(interface().P)); P.update(copy.deepcopy(asm_params().P))
    for s in SUBS: P.update(copy.deepcopy(sub_params(s).P))
    owners(); return P

def validate():
    """Static contract check: imports are exported by their source."""
    errs = []
    for s in SUBS:
        for src, ks in sub_params(s).IMPORTS.items():
            ex = set(sub_params(src).EXPORTS)
            for k in ks:
                if k not in ex: errs.append(f"{s} imports {k!r} from {src}, which does not export it")
    return errs

def derive(p):
    errs = validate()
    if errs: raise ValueError("; ".join(errs))
    own = owners()
    I = {k: copy.deepcopy(p[k]) for k in interface().P}
    interface().derive(I)
    D = Model(I); D.ikeys = set(I); D.scope = {}; D.owner = {k: "interface" for k in I}
    for k in asm_params().P: D[k] = p[k]; D.owner[k] = "assembly"
    for s in SUBS:
        m = sub_params(s)
        view = {k: copy.deepcopy(D[k]) for k in D.ikeys}
        view.update({k: copy.deepcopy(p[k]) for k in m.P})
        imps = [k for ks in m.IMPORTS.values() for k in ks]
        for k in imps:
            if k in D: view[k] = copy.deepcopy(D[k])
        before = dict(view); m.derive(view)
        for k in D.ikeys | {k for k in imps if k in D}:
            if repr(view[k]) != repr(before[k]): raise ValueError(f"{s}.derive changed {k!r} (interface/import values are read-only)")
        new = set(view) - set(before)
        for k in list(m.P) + sorted(new):
            if k in D and D.owner.get(k) != s: raise ValueError(f"{s} redefines {k!r} owned by {D.owner.get(k)}")
            D[k] = view[k]; D.owner[k] = s
        D.scope[s] = D.ikeys | set(m.P) | new | set(imps)
    return D

def view(D, s):
    """The dict a sub-assembly's parts and local checks get: its scope only."""
    return {k: D[k] for k in D.scope[s] if k in D}

def parse_value(s):
    import ast
    try: return ast.literal_eval(s)
    except Exception: return s

def apply_overrides(p, sets):
    """sets: ['knob_wall=1.8', 'feel.can_d=6', 'tgt.lip_wall=0.3']"""
    q = copy.deepcopy(p)
    for s in sets or []:
        k, v = s.split("=", 1); v = parse_value(v)
        if "." in k:
            a, b = k.split(".", 1)
            if a not in q or not isinstance(q[a], dict): raise KeyError(f"unknown param {a}")
            q[a] = dict(q[a]); q[a][b] = v
        else:
            if k not in q: raise KeyError(f"unknown param {k} (see the params.py files / assembly/interface.py)")
            q[k] = v
    return q
