"""Main PCB PROXY: outline, holes (H1, H2, M2, 1220 tab slots + KiCad extras: M1 Ø3.2 relief, joystick spring / pin holes and FPC slot)
and the key back-side component boxes. KiCad is the source of truth: the extras and the back-side parts come from
kicad/knob-main-pcb/pcb_proxy.json (export_pcb_proxy.py, run after make_board.py; read by params.derive -> D['pcb_kicad']). Full KiCad STEP: pcb_full()."""
import math, os
from build123d import *
from ...common.util import A, cyl

def board_xy(D, bx, by): return (bx - D["axis_bx"], -(by - D["axis_by"]))

def _mr(D):
    return Rot(0, 0, D.get("mech_rot", 0.0))

def _mpt(D, x, y):
    """mechanism frame -> panel frame (v0.19 mech_rot)."""
    a = math.radians(D.get("mech_rot", 0.0)); c, s = math.cos(a), math.sin(a)
    return c * x - s * y, s * x + c * y

def _is_mech(D, x, y):
    # KiCad boards up to v0.12 are laid out in the mechanism frame (motor at +X). A board regenerated from the v0.19
    # cad_constraints.json is already in the panel frame: set electronics kicad_frame = "panel" and nothing is turned.
    return D.get("kicad_frame", "mech") == "mech" and math.hypot(x, y) < D.get("mech_rot_r", 23.0)

def build(D):
    t, w = D["pcb_t"], D["pcb_w"]
    yc = (D["pcb_above"] - D["pcb_below"]) / 2
    b = Pos(0, yc, -t) * Box(w, D["pcb_above"] + D["pcb_below"], t, align=A)
    b -= cyl(D["h1_hole"] / 2, -t - 1, t + 2)
    # v0.19: mechanism cutters are made in the mechanism frame and turned by mech_rot as one compound
    mc = []
    ex, ey = D["enc_xy"]; mc.append(cyl(D["brg"]["D"] / 2, -t - 1, t + 2, ex, ey))     # H2 press bore
    F = D["feel"]; pw, pl = F["pad"]   # (radial, tangential) copper around each lead hole
    for px, py in D["fm_pad_xy"]:
        mc.append(cyl(F["pad_hole"] / 2, -t - 1, t + 2, px, py))                     # M2 lead holes
    # v0.17: 716 shaft and the compound-idler pin pass the board. Holes are in the proxy; KiCad NPTHs are still to add.
    mc.append(cyl(D["fm_shaft_hole"] / 2, -t - 1, t + 2, *D["fm_xy"]))
    mc.append(cyl(D["fg_hole"] / 2, -t - 1, t + 2, *D["fg_xy"]))
    mc += _em_cutters(D, t, 1.0)
    M = D["motor"]
    for s in (-1, 1):                                                                 # M1 tab slots
        c = D["pcb_slot_clear"]
        mc.append(Pos(D["offset"] + s * M["term_pitch"] / 2, 0, -t - 1) * Box(M["term_t"] + c, M["term_w"] + c, t + 2, align=A))
    b -= _mr(D) * Compound(children=mc)
    K = D["pcb_kicad"]
    for h in K.get("holes", []):                                                       # M1 relief (turns), joystick springs / pins (fixed)
        hx, hy = (_mpt(D, h["x"], h["y"]) if _is_mech(D, h["x"], h["y"]) else (h["x"], h["y"]))
        b -= cyl(h["d"] / 2, -t - 1, t + 2, hx, hy)
    for sl in K.get("slots", []):                                                                       # joystick FPC slot (oval)
        dx, dy = sl["dx"], sl["dy"]; r = min(dx, dy) / 2
        b -= Pos(sl["x"], sl["y"], -t - 1) * extrude(SlotOverall(max(dx, dy), 2 * r, rotation=0 if dx >= dy else 90), t + 2)
    for h in D.get("js_pcb_holes", []):   # v0.19b: joystick standoff screws + hold-down springs (cad/joystick-param geom.json)
        b -= cyl(h["d"] / 2, -t - 1, t + 2, h["x"], h["y"])
    for k, poly in D["pcb_windows"].items():   # v0.19b [Ed 2 Nov]: see-through windows (panel frame, not turned)
        b -= Pos(0, 0, -t - 1) * extrude(Face(Wire.make_polygon([Vector(x, y, 0) for x, y in poly], close=True)), t + 2, dir=(0, 0, 1))
    # back-side parts: Hall decouplers behind each sensor [K positions follow the params]; the rest from KiCad (pcb_proxy.json)
    comps = []
    if D["hall_layout"] == "vernier":   # one 0402 decoupler behind each Hall sensor [A]
        pts = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), a) for r, a in zip(D["hv_r"], D["hv_phi_s"])]
    else:
        pts = [(D["ha_r_m"] * math.cos(math.radians(a)), D["ha_r_m"] * math.sin(math.radians(a)), a) for a in D["ha_sens_angs"]]
    mcomps = []
    for x, y, a in pts:
        cl, cw, ch = D["adapter_env"]["C_0402"]
        mcomps.append(Pos(x, y, -t - ch) * Rot(0, 0, a) * Box(cw, cl, ch, align=A))
    drv_refs = {c[0] for c in D["drv_cluster"]}
    for x, y, w, l, h, a in drv_boxes(D):   # v0.19b: the 716 driver cluster follows drv_xy / drv_rot (KiCad to follow)
        mcomps.append(Pos(x, y, -t - h) * Rot(0, 0, a) * Box(w, l, h, align=A))
    for p in K.get("back_parts", []):
        if p["ref"].startswith("C1") and len(p["ref"]) == 3: continue   # C11..C15 = the Hall decouplers above
        if p["ref"] in drv_refs: continue
        if p["ref"] in D["pcb_win_displaced"]: continue   # stale KiCad position inside a window: moves on regeneration
        box = Pos(p["x"], p["y"], -t - p["h"]) * Box(p["w"], p["l"], p["h"], align=A)
        (comps.append(_mr(D) * box) if _is_mech(D, p["x"], p["y"]) else comps.append(box))
    for px, py in D["fm_pad_xy"]:   # B.Cu pads [A] under the lead holes; wires drop from the 716's rear via the cradle pocket
        pad = Pos(px, py, -t - F["pad_t"]) * Rot(0, 0, D["fm_ang"] + 90) * Box(pl, pw, F["pad_t"], align=A)
        mcomps.append(pad - cyl(F["pad_hole"] / 2, -t - F["pad_t"] - 0.1, F["pad_t"] + 0.2, px, py))
    comps += [_mr(D) * c for c in mcomps]
    pad = cyl(D["rod_pad_r"], -t - D["rod_pad_t"], D["rod_pad_t"]) - cyl(D["h1_hole"] / 2, -t - 1, 2)
    out = {"PCB": b, "PCB back parts (Hall decouplers, J10, DRV8837, passives)": Compound(children=comps),
           f"PCB rod pad VBUS Ø{2 * D['rod_pad_r']:.1f} (B.Cu)": pad}
    out.update({k: _mr(D) * v for k, v in emitters(D).items()})
    w, h, th = D["clear_oled"]; cx, cy = D["clear_oled_xy"]
    out['clear OLED 1.51" SSD1309 (PCB front, over window D)'] = Pos(cx, cy, 0) * Box(w, h, th, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return out

def _in_poly(x, y, poly):
    inside = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside

def window_hits(D, K):
    """KiCad back parts (panel-frame ones) whose footprint box touches a window."""
    out = []
    for p in K.get("back_parts", []):
        if _is_mech(D, p["x"], p["y"]):
            continue
        hw, hl = p["w"] / 2, p["l"] / 2
        pts = [(p["x"] + sx * hw, p["y"] + sy * hl) for sx in (-1, 0, 1) for sy in (-1, 0, 1)]
        if any(_in_poly(x, y, poly) for poly in D["pcb_windows"].values() for x, y in pts):
            out.append(p["ref"])
    return out

STEP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kicad", "knob-main-pcb", "knob-main-pcb.step")

def pcb_full(D):
    """The real board (KiCad STEP export, committed in electronics/kicad/knob-main-pcb/), moved into the dial frame.
    Needs NO KiCad: only build123d's STEP import. Regenerate the STEP with kicad-cli after editing the board (see AGENTS.md)."""
    s = import_step(STEP); zf = s.bounding_box().max.Z
    s = Pos(-D["axis_bx"], D["axis_by"], -zf) * s
    # same NPTHs the proxy drills; the KiCad board does not have them yet (see design notes).
    # v0.18 moved H2 with the herringbone centre distance, so the committed STEP hole is drilled out at the new axis too.
    t = D["pcb_t"]
    mc = [cyl(D["fm_shaft_hole"] / 2, -t - 2, t + 4, *D["fm_xy"]),
          cyl(D["fg_hole"] / 2, -t - 2, t + 4, *D["fg_xy"]),
          cyl(D["brg"]["D"] / 2, -t - 2, t + 4, *D["enc_xy"])] + _em_cutters(D, t, 2.0)
    s -= _mr(D) * Compound(children=mc)
    return s

def _em_cutters(D, t, extra):
    """NPTH under the thrust race (mechanism frame). Bodies are reverse-mounted on the back; KiCad does not have the holes yet."""
    out = []
    for h in D["em_holes"]:
        if h["slot"]:
            out.append(Pos(h["x"], h["y"], -t - extra) * Rot(0, 0, h["ang"]) * extrude(
                SlotOverall(h["slot_l"], h["hole_d"]), t + 2 * extra))
        else:
            out.append(cyl(h["hole_d"] / 2, -t - extra, t + 2 * extra, h["x"], h["y"]))
    return out

def emitters(D):
    """VCSEL and RGB bodies on the PCB back, over their holes. Not pockets in the race."""
    out = {}
    gap = 0.02
    for h in D["em_holes"]:
        body = D["em_vcsel"] if h["kind"] == "VCSEL" else D["em_rgb"]
        bx, by, bh = body
        out[f"emitter {h['kind']} {h['i'] // 2 + 1}"] = (
            Pos(h["x"], h["y"], -D["pcb_t"] - bh - gap) * Rot(0, 0, h["ang"])
            * Box(bx, by, bh, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return out

def drv_boxes(D):
    """716 driver cluster (U20 + C20–C22) on B.Cu: (x, y, w, l, h, angle) in the mechanism frame."""
    X, Y = D["drv_xy"]; a = math.radians(D["drv_rot"]); c, s = math.cos(a), math.sin(a)
    return [(X + c * dx - s * dy, Y + s * dx + c * dy, w, l, h, D["drv_rot"]) for _r, _fp, dx, dy, _rot, w, l, h in D["drv_cluster"]]

def drv_place(D):
    """Same cluster for the KiCad generator: ref -> (x, y, rot) in the mechanism frame (footprint rot + cluster turn)."""
    X, Y = D["drv_xy"]; a = math.radians(D["drv_rot"]); c, s = math.cos(a), math.sin(a)
    return {ref: (round(X + c * dx - s * dy, 3), round(Y + s * dx + c * dy, 3), (rot + D["drv_rot"]) % 360)
            for ref, _fp, dx, dy, rot, _w, _l, _h in D["drv_cluster"]}

def kicad_step_path():
    return STEP
