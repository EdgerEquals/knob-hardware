"""Assembly merge: builds every sub-assembly's part modules (per-part cache, each module sees only its sub-assembly scope)
in the fixed global order, so part names / pair names are stable."""
import importlib, os, time
from ..common.cache import build_module, CACHE
from ..common import model

ORDER = [("optics", "scanner"), ("optics", "ring_lights"), ("electronics", "pcb"), ("base_drive", "motor"), ("base_drive", "brass"), ("base_drive", "cradle"),
         ("control_dial", "thrust"), ("main_knob", "knob"), ("control_dial", "dial"), ("control_dial", "hall_arm"),
         ("electronics", "hall_sensors"), ("under_pcb", "encoder"), ("base_drive", "idlers"), ("base_drive", "feel"), ("base_drive", "mech"),
         ("control_dial", "screen"), ("control_dial", "holder"), ("electronics", "adapter"),
         ("case", "shell")]
PATHS = {}
NATIVE = {}   # native brep path per part (mechanism parts in the mechanism frame, the rest in the panel frame)
FRAME = {}    # part -> "mech" | "panel"
# modules built in the panel frame. The PCB proxy turns its own mechanism features into the panel frame.
FIXED = {("case", "shell"), ("electronics", "pcb"), ("optics", "scanner")}


def view(parts, keys, D, which):
    """v0.19 mech_rot. which = "mech": panel-frame parts turned by -mech_rot (gap checks and clashes, where the
    mechanism checks build their own solids from D in the mechanism frame); "panel": mechanism parts turned by
    +mech_rot (renders and exports). Sets PATHS for the worker pools and returns (parts, keys)."""
    rot = float(D.get("mech_rot", 0.0))
    PATHS.clear(); PATHS.update(NATIVE)
    if not rot:
        return parts, keys
    turn = (lambda n: FRAME.get(n) == "panel") if which == "mech" else (lambda n: FRAME.get(n) == "mech")
    a = -rot if which == "mech" else rot
    p2, k2 = dict(parts), dict(keys)
    for n in parts:
        if not turn(n):
            continue
        o, pth, k = _turn({n: parts[n]}, {n: NATIVE.get(n)}, keys[n], a)
        p2[n] = o[n]; PATHS[n] = pth[n]; k2[n] = k
    return p2, k2


def _turn(out, paths, key, rot):
    from build123d import Rot, export_brep
    tag = f"_r{rot:g}"
    o2, p2 = {}, {}
    for n, solid in out.items():
        o2[n] = Rot(0, 0, rot) * solid
        src = paths.get(n)
        import hashlib
        dst = (src[:-5] if src and src.endswith(".brep") else os.path.join(CACHE, hashlib.sha1((key + n).encode()).hexdigest()[:20])) + tag + ".brep"
        if not os.path.exists(dst): export_brep(o2[n], dst)
        p2[n] = dst
    return o2, p2, key + tag


def _merge_pcb(el_pcb, case_pcb, key):
    from build123d import export_brep
    import hashlib
    dst = os.path.join(CACHE, "pcb_merged_" + hashlib.sha1(key.encode()).hexdigest()[:16] + ".brep")
    merged = el_pcb & case_pcb
    if not os.path.exists(dst): export_brep(merged, dst)
    return merged, dst

def build_all(D, full_pcb=False, only=None):
    """only: list of sub-assembly names (None = all). Returns parts, stats, keys, owner{part: sub}."""
    global PATHS
    parts, stats, keys, owner = {}, [], {}, {}
    PATHS.clear(); NATIVE.clear(); FRAME.clear()
    for s, modname in ORDER:
        if only and s not in only: continue
        mod = importlib.import_module(f"knobparam.{s}.parts.{modname}")
        assert mod in model.sub(s).PART_MODULES, f"{modname} not registered in {s}.PART_MODULES"
        out, key, paths = build_module(mod, model.view(D, s), stats)
        for n in out: FRAME[n] = "panel" if (s, modname) in FIXED else "mech"
        if s == "case" and "PCB" in out and "PCB" in parts:
            # the case gives the board outline (10HP nest + corner notches); electronics gives every hole and cut-out
            out = dict(out); paths = dict(paths)
            out["PCB"], paths["PCB"] = _merge_pcb(parts["PCB"], out["PCB"], keys["PCB"] + key)
        for n in out: keys[n] = (keys[n] + key + n) if (n == "PCB" and n in keys) else key + n; owner[n] = owner.get(n, s)
        PATHS.update(paths); parts.update(out)
    if full_pcb and (not only or "electronics" in only):
        from build123d import export_brep
        el = model.sub("electronics")
        t = time.time(); parts["PCB"] = el.pcb_full(model.view(D, "electronics")); keys["PCB"] = "full%.0f" % os.path.getmtime(el.kicad_step_path())
        PATHS["PCB"] = os.path.join(CACHE, "pcb_full.brep"); export_brep(parts["PCB"], PATHS["PCB"]); FRAME["PCB"] = "panel"
        stats.append(("pcb_full (KiCad STEP)", "built", time.time() - t))
    NATIVE.update(PATHS)
    return parts, stats, keys, owner
