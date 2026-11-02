"""electronics LOCAL checks (own parts + interface values only)."""
import itertools
from ..common.checks import Rows

def _area(p):
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(p, p[1:] + p[:1]))) / 2

def _ledge(D):
    w, h, _ = D["clear_oled"]; cx, cy = D["clear_oled_xy"]; P = D["pcb_windows"]["D"]
    xs, ys = [x for x, _ in P], [y for _, y in P]
    return min(min(xs) - (cx - w / 2), (cx + w / 2) - max(xs), min(ys) - (cy - h / 2), (cy + h / 2) - max(ys))

def checks(D, parts):
    T = D["tgt"]; r = Rows("electronics")
    if D["hall_layout"] == "vernier":
        sens = [parts[n] for n in parts if n.startswith("hall sensor")]
        sg = min(a.distance_to(b) for a, b in itertools.combinations(sens, 2))
        r.row("Hall sensor body spacing on the PCB", sg, T["sensor_gap"], f"{D['hv_n']} sensors at pitch {D['hv_pitch']:g}: " + ", ".join(f"H{i + 1} {p.split()[0]}" for i, p in enumerate(D['hv_parts'])))
    em = [parts[n] for n in parts if n.startswith("emitter ")]
    bp = parts.get("PCB back parts (Hall decouplers, J10, DRV8837, passives)")
    if em and bp is not None:   # v0.19b [Ed 2 Nov]: no keep-out; the 716 driver sits inboard of the even emitter ring
        r.row("emitter bodies vs back-side parts (716 driver moved inboard)", min(e.distance_to(bp) for e in em), 0.5,
              f"{len(em)} emitters every {360 / len(em):g}°; U20 at ({D['drv_xy'][0]:.1f}, {D['drv_xy'][1]:.1f}) turned {D['drv_rot']:g}° (mechanism frame)")
    if D.get("pcb_windows"):   # v0.19b [Ed 2 Nov]
        areas = {k: _area(p) for k, p in D["pcb_windows"].items()}
        oled = [parts[n] for n in parts if n.startswith("clear OLED")]
        r.row("PCB windows: smallest window (mm²)", min(areas.values()), 10.0,
              ", ".join(f"{k} {a:.0f}" for k, a in areas.items()) + "; KiCad back parts to move off the windows: " +
              (", ".join(D["pcb_win_displaced"]) or "none") + " (left out of the proxy)")
        if oled:
            r.row("clear OLED rests on the board round window D (narrowest ledge)", _ledge(D), 1.0,
                  f"{D['clear_oled'][0]:g} x {D['clear_oled'][1]:g} on the PCB front at ({D['clear_oled_xy'][0]:g}, {D['clear_oled_xy'][1]:g})")
    pad = [parts[n] for n in parts if n.startswith("PCB rod pad")]
    if pad:
        r.row("rod VBUS pad (B.Cu) vs back-side parts / pads", pad[0].distance_to(parts["PCB back parts (Hall decouplers, J10, DRV8837, passives)"]), D["rod_pad_clear"] - 0.01,
              f"pad Ø{2 * D['rod_pad_r']:.2f} (was the Ø4 washer footprint); nut clamps straight on it, no washer")
    return r
