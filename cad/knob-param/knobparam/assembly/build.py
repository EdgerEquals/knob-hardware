"""Assembly merge: builds every sub-assembly's part modules (per-part cache, each module sees only its sub-assembly scope)
in the fixed global order, so part names / pair names are stable."""
import importlib, os, time
from ..common.cache import build_module, CACHE
from ..common import model

ORDER = [("optics", "scanner"), ("optics", "ring_lights"), ("electronics", "pcb"), ("base_drive", "motor"), ("base_drive", "brass"), ("base_drive", "cradle"),
         ("control_dial", "thrust"), ("main_knob", "knob"), ("control_dial", "dial"), ("control_dial", "hall_arm"),
         ("electronics", "hall_sensors"), ("under_pcb", "encoder"), ("base_drive", "idlers"), ("base_drive", "feel"), ("base_drive", "mech"),
         ("control_dial", "screen"), ("control_dial", "holder"), ("control_dial", "cartridge"),   # cartridge: v0.24 dial screen
         ("electronics", "adapter"), ("electronics", "vboards"),
         ("case", "shell")]
PATHS = {}
NATIVE = {}   # native brep path per part (mechanism parts in the mechanism frame, the rest in the panel frame)
FRAME = {}    # part -> "mech" | "panel"
# modules built in the panel frame. The PCB proxy turns its own mechanism features into the panel frame.
FIXED = {("case", "shell"), ("electronics", "pcb"), ("optics", "scanner"), ("electronics", "vboards")}   # vboards: v4, panel frame


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
        import hashlib
        dst = os.path.join(CACHE, "turn_" + hashlib.sha1((key + "|" + n).encode()).hexdigest()[:24] + tag + ".brep")
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

def _fuse_cradle(case, key):
    """v0.25 [Ed 18:35]: the joystick cradle (lip ring, hangers, end walls, ball seats on their brackets, top-board shoulders) is printed
    into the case: one UTR-8100 print. The cradle comes from cad/joystick-param (read as data, assembly/joystick.py) with a 0.02 overlap into
    the faceplate so the two solids fuse into one. Cached like the merged PCB. Returns (case, brep path, joystick key)."""
    from build123d import export_brep, import_brep
    import hashlib
    from . import joystick as js
    cr, ck = js.cradle_for_case()
    if cr is None:
        return case, None, ""
    dst = os.path.join(CACHE, "case_cradle_" + hashlib.sha1((key + "|" + ck).encode()).hexdigest()[:16] + ".brep")
    if os.path.exists(dst):
        return import_brep(dst), dst, ck
    fused = (case + cr).clean()
    if len(fused.solids()) == 1:
        fused = fused.solids()[0]   # one print, one solid (the assembly row "printed into the case: one solid" checks it)
    export_brep(fused, dst)
    return fused, dst, ck


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
        ck = ""
        if s == "case" and "case" in out:   # v0.25 [Ed 18:35]: the joystick cradle is printed into the case (one print)
            out = dict(out); paths = dict(paths)
            out["case"], p_, ck = _fuse_cradle(out["case"], key)
            if p_: paths["case"] = p_
        for n in out: keys[n] = (keys[n] + key + n) if (n == "PCB" and n in keys) else key + n; owner[n] = owner.get(n, s)
        if ck: keys["case"] += "|cradle" + ck
        PATHS.update(paths); parts.update(out)
    if full_pcb and (not only or "electronics" in only):
        from build123d import export_brep
        el = model.sub("electronics")
        t = time.time(); parts["PCB"] = el.pcb_full(model.view(D, "electronics")); keys["PCB"] = "full%.0f" % os.path.getmtime(el.kicad_step_path())
        PATHS["PCB"] = os.path.join(CACHE, "pcb_full.brep"); export_brep(parts["PCB"], PATHS["PCB"]); FRAME["PCB"] = "panel"
        stats.append(("pcb_full (KiCad STEP)", "built", time.time() - t))
    NATIVE.update(PATHS)
    return parts, stats, keys, owner
