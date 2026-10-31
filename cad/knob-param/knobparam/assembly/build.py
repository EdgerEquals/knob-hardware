"""Assembly merge: builds every sub-assembly's part modules (per-part cache, each module sees only its sub-assembly scope)
in the fixed global order, so part names / pair names are stable."""
import importlib, os, time
from ..common.cache import build_module, CACHE
from ..common import model

ORDER = [("electronics", "pcb"), ("base_drive", "motor"), ("base_drive", "brass"), ("base_drive", "cradle"),
         ("control_dial", "thrust"), ("main_knob", "knob"), ("control_dial", "dial"), ("control_dial", "hall_arm"),
         ("electronics", "hall_sensors"), ("under_pcb", "encoder"), ("base_drive", "idlers"), ("under_pcb", "feel"),
         ("control_dial", "screen"), ("control_dial", "holder"), ("electronics", "adapter")]
PATHS = {}

def build_all(D, full_pcb=False, only=None):
    """only: list of sub-assembly names (None = all). Returns parts, stats, keys, owner{part: sub}."""
    global PATHS
    parts, stats, keys, owner = {}, [], {}, {}
    PATHS.clear()
    for s, modname in ORDER:
        if only and s not in only: continue
        mod = importlib.import_module(f"knobparam.{s}.parts.{modname}")
        assert mod in model.sub(s).PART_MODULES, f"{modname} not registered in {s}.PART_MODULES"
        out, key, paths = build_module(mod, model.view(D, s), stats)
        for n in out: keys[n] = key + n; owner[n] = s
        PATHS.update(paths); parts.update(out)
    if full_pcb and (not only or "electronics" in only):
        from build123d import export_brep
        el = model.sub("electronics")
        t = time.time(); parts["PCB"] = el.pcb_full(model.view(D, "electronics")); keys["PCB"] = "full%.0f" % os.path.getmtime(el.kicad_step_path())
        PATHS["PCB"] = os.path.join(CACHE, "pcb_full.brep"); export_brep(parts["PCB"], PATHS["PCB"])
        stats.append(("pcb_full (KiCad STEP)", "built", time.time() - t))
    return parts, stats, keys, owner
