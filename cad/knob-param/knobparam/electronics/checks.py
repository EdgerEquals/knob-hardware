"""electronics LOCAL checks (own parts + interface values only)."""
import itertools
from ..common.checks import Rows

def _area(p):
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(p, p[1:] + p[:1]))) / 2

def _ledge(D):
    # window D (or every window whose key starts with D, if it is ever split): the OLED rests on the board round all of them
    w, h, _ = D["clear_oled"]; cx, cy = D["clear_oled_xy"]
    P = [pt for k, v in D["pcb_windows"].items() if k.startswith("D") for pt in v]
    xs, ys = [x for x, _ in P], [y for _, y in P]
    return min(min(xs) - (cx - w / 2), (cx + w / 2) - max(xs), min(ys) - (cy - h / 2), (cy + h / 2) - max(ys))

def _seg_d(px, py, a, b):
    (x0, y0), (x1, y1) = a, b; dx, dy = x1 - x0, y1 - y0
    t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy or 1e-12)))
    return ((x0 + t * dx - px) ** 2 + (y0 + t * dy - py) ** 2) ** 0.5

def _court_to_windows(D):
    """board left between the MCU courtyard (square) and the nearest window edge (negative = the courtyard runs into a window)."""
    (mx, my), c = D["mcu"]["xy"], D["mcu"]["court"] / 2
    sq = [(mx - c, my - c), (mx + c, my - c), (mx + c, my + c), (mx - c, my + c)]
    best = 1e9
    for poly in D["pcb_windows"].values():
        for p, q in zip(poly, poly[1:] + poly[:1]):
            best = min(best, min(_seg_d(x, y, p, q) for x, y in sq))                                # courtyard corners to window edges
        for x, y in poly:
            if mx - c < x < mx + c and my - c < y < my + c:
                return -1.0
            best = min(best, min(_seg_d(x, y, a, b) for a, b in zip(sq, sq[1:] + sq[:1])))         # window corners to the courtyard
    return best

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
              ", ".join(f"{k} {a:.0f}" for k, a in areas.items()) + "; KiCad back parts to move off the windows / MCU site: " +
              (", ".join(D["pcb_win_displaced"]) or "none") + " (left out of the proxy)")
        if oled:
            dk = [k for k in D["pcb_windows"] if k.startswith("D")]
            r.row(f"clear OLED rests on the board round window{'s' if len(dk) > 1 else ''} {' + '.join(dk)} (narrowest ledge)", _ledge(D), 1.0,
                  f"{D['clear_oled'][0]:g} x {D['clear_oled'][1]:g} on the PCB front at ({D['clear_oled_xy'][0]:g}, {D['clear_oled_xy'][1]:g})")
        if D.get("mcu"):   # [Ed 18:34] H7B0 LQFP100 at the low middle, notched into the bottom of D
            M = D["mcu"]
            r.row(f"MCU {M['pkg']} courtyard ({M['court']:g} □ [A]) to the nearest window edge", _court_to_windows(D), M["margin"] - 0.01,
                  f"{M['part']} on the board back at ({M['xy'][0]:g}, {M['xy'][1]:g}); D is notched at exactly this margin; D {sum(areas.get(k, 0) for k in areas if k.startswith('D')):.0f} mm²")
            mp = [parts[n] for n in parts if n.startswith("MCU ")]
            if mp and bp is not None:
                r.row(f"MCU {M['pkg']} body vs the other back-side parts (KiCad proxy)", mp[0].distance_to(bp), D["rod_pad_clear"] - 0.01,
                      "the KiCad parts under the courtyard are left out above (they move when the board is regenerated)")
    pad = [parts[n] for n in parts if n.startswith("PCB rod pad")]
    if pad:
        r.row("rod VBUS pad (B.Cu) vs back-side parts / pads", pad[0].distance_to(parts["PCB back parts (Hall decouplers, J10, DRV8837, passives)"]), D["rod_pad_clear"] - 0.01,
              f"pad Ø{2 * D['rod_pad_r']:.2f} (was the Ø4 washer footprint); nut clamps straight on it, no washer")
    return r
