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

def _hole_desc(D, key):
    kind, i = key.split(); K = D["pcb_kicad"]
    h = K["holes" if kind == "hole" else "slots"][int(i)]
    return f"{h.get('ref', '?')} {kind} at ({h['x']:g}, {h['y']:g})"


def _vb_rows(D, parts, r):
    """[Ed 3 Nov] v4 local rows for the vertical boards: contact count and working point, pads vs windows / joystick holes, chip room."""
    V, H, G = D["vb"], D["vb_hdr"], D["vb_pogo"]
    n = D["vb_n_contacts"]
    r.row("vertical boards: spring contacts to the top board (total)", n, 16,
          f"{n // 2} per board at {G['pitch']:g} along the {V['y'][1] - V['y'][0]:.1f} top edge, y {D['vb_contact_y'][0]:.2f}..{D['vb_contact_y'][-1]:.2f}; "
          f"doc: about 16-20 [Ed 11:25]. 2.0 pitch would give {2 * (int((V['y'][1] - V['y'][0] - 2.0) / 2.0) + 1)}")
    comp = G["free"] - (V["top_board_z"] - D["vb_z1"])
    r.row("vertical-board contacts: compression at the nominal stack (mid travel)", min(comp, G["travel"] - comp), 0.3,
          f"board top edge z {D['vb_z1']:.2f}, tips {G['free']:g} above it free, top board underside z {V['top_board_z']:g}: "
          f"{comp:.2f} of {G['travel']:g} [A]; the tolerance band is the assembly row")
    # header pads vs windows and the joystick's main-PCB holes (spring bores, grub access)
    rp = H["pad"] / 2; best, who = 9e9, ""
    for sx in (-1, 1):
        x = sx * D["vb_pin_x"]
        for y in D["vb_pins"][sx]:
            for k, poly in D["pcb_windows"].items():
                d = min(_seg_d(x, y, p, q) for p, q in zip(poly, poly[1:] + poly[:1])) - rp
                if d < best: best, who = d, f"window {k}"
            for h in D.get("js_pcb_holes", []):
                d = ((x - h["x"]) ** 2 + (y - h["y"]) ** 2) ** 0.5 - h["d"] / 2 - rp
                if d < best: best, who = d, h["what"]
    L, R_ = D["vb_pins"][-1], D["vb_pins"][1]
    r.row("vertical-board header pads vs the windows and the joystick holes in the main PCB", best, 0.5,
          f"legs at x ±{D['vb_pin_x']:.2f} (pad Ø{H['pad']:g}, {H['pitch']:g} pitch): L {len(L)} at y {L[0]:.2f}..{L[-1]:.2f}, R {len(R_)} at y "
          f"{R_[0]:.2f}..{R_[-1]:.2f} (R skips the encoder daughterboard's standoff behind the board); nearest: {who}")
    M = D.get("mcu")
    if M:
        (mx, my), c = M["xy"], M["court"] / 2
        dx = min(D["vb_face_in"], D["vb_pin_x"] - rp) - (abs(mx) + c)
        r.row("MCU courtyard to the vertical boards (inner faces less their parts envelope)", dx - V["env"], 1.0,
              f"courtyard x ±{abs(mx) + c:.2f}; inner faces x ±{D['vb_face_in']:.2f}, parts envelope {V['env']:g} [A]")
    so = parts.get("vertical boards' standoff (M2 F-F brass, joins L and R) [A]")
    mp = [parts[n] for n in parts if n.startswith("MCU ")]
    if so is not None and mp:
        r.row("vertical boards' standoff clear of the MCU", so.distance_to(mp[0]), 1.0,
              f"standoff at y {D['vb_standoff']['y']:g}, z {D['vb_standoff']['z']:g} (panel), Ø{D['vb_standoff']['od']:g}, "
              f"{2 * D['vb_face_in']:.1f} long between the inner faces")


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
        if D.get("mcu"):
            M = D["mcu"]; front = M.get("side", "back") == "front"
            r.row(f"MCU {M['pkg']} courtyard ({M['court']:g} □ [A]) to the nearest window edge", _court_to_windows(D), M["margin"] - 0.01,
                  f"{M['part']} on the board {'front' if front else 'back'} at ({M['xy'][0]:g}, {M['xy'][1]:g})" +
                  (f" [Ed 3 Nov] under the joystick; no window is cut round it; D {sum(areas.get(k, 0) for k in areas if k.startswith('D')):.0f} mm² (whole)"
                   if front else f"; D is notched at exactly this margin; D {sum(areas.get(k, 0) for k in areas if k.startswith('D')):.0f} mm²"))
            mp = [parts[n] for n in parts if n.startswith("MCU ")]
            if mp and front:   # [Ed 3 Nov] v4: the other front-side parts of this sub (vertical boards and their parts, the clear OLED)
                fr = {n: q for n, q in parts.items() if n.startswith(("vertical board", "clear OLED"))}
                dd, who = min(((mp[0].distance_to(q), n) for n, q in fr.items()), default=(9.9, "none"))
                r.row(f"MCU {M['pkg']} body vs the other front-side parts", dd, 1.0,
                      f"nearest: {who}. KiCad holes left out of the proxy (stale v0.16 joystick MH1 set, under the chip or the vertical "
                      f"boards): " + (", ".join(_hole_desc(D, h) for h in D.get("pcb_hole_displaced", [])) or "none"))
            elif mp and bp is not None:
                r.row(f"MCU {M['pkg']} body vs the other back-side parts (KiCad proxy)", mp[0].distance_to(bp), D["rod_pad_clear"] - 0.01,
                      "the KiCad parts under the courtyard are left out above (they move when the board is regenerated)")
    if D.get("vb"):   # [Ed 3 Nov 09:47-11:32] layout v4: vertical boards under the joystick
        _vb_rows(D, parts, r)
    pad = [parts[n] for n in parts if n.startswith("PCB rod pad")]
    if pad:
        r.row("rod VBUS pad (B.Cu) vs back-side parts / pads", pad[0].distance_to(parts["PCB back parts (Hall decouplers, J10, DRV8837, passives)"]), D["rod_pad_clear"] - 0.01,
              f"pad Ø{2 * D['rod_pad_r']:.2f} (was the Ø4 washer footprint); nut clamps straight on it, no washer")
    return r
