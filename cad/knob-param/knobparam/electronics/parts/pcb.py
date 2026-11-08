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
    if D["feel_on"]:   # Q27 [Ed 6 Nov 19:33]: no 716, so no lead holes, shaft hole or compound-idler pin hole
        for px, py in D["fm_pad_xy"]:
            mc.append(cyl(F["pad_hole"] / 2, -t - 1, t + 2, px, py))                     # M2 lead holes
        # v0.17: 716 shaft and the compound-idler pin pass the board. Holes are in the proxy; KiCad NPTHs are still to add.
        mc.append(cyl(D["fm_shaft_hole"] / 2, -t - 1, t + 2, *D["fm_xy"]))
        mc.append(cyl(D["fg_hole"] / 2, -t - 1, t + 2, *D["fg_xy"]))
    mc += _em_cutters(D, t, 1.0)
    if D.get("sp_access_d"):   # v0.22b [Ed 15:50]: key hole for the detent-pedestal grub (mechanism frame)
        mc.append(cyl(D["sp_access_d"] / 2, -t - 1, t + 2, *D["sp_grub_xy"]))
    for x, y, d in D.get("enc_tht_xy", []):   # v0.24 [Ed 13:35]: the encoder riser's through-hole pins (mechanism frame)
        mc.append(cyl(d / 2, -t - 1, t + 2, x, y))
    M = D["motor"]
    for s in (-1, 1):                                                                 # M1 tab slots
        c = D["pcb_slot_clear"]
        mc.append(Pos(D["offset"] + s * M["term_pitch"] / 2, 0, -t - 1) * Box(M["term_t"] + c, M["term_w"] + c, t + 2, align=A))
    b -= _mr(D) * Compound(children=mc)
    K = D["pcb_kicad"]
    gone = set(D.get("pcb_hole_displaced", []))   # [Ed 3 Nov] v4: stale KiCad joystick holes / slot under the H7B0 or the vertical boards
    for i, h in enumerate(K.get("holes", [])):                                         # M1 relief (turns), joystick springs / pins (fixed)
        if f"hole {i}" in gone: continue
        hx, hy = (_mpt(D, h["x"], h["y"]) if _is_mech(D, h["x"], h["y"]) else (h["x"], h["y"]))
        b -= cyl(h["d"] / 2, -t - 1, t + 2, hx, hy)
    for i, sl in enumerate(K.get("slots", [])):                                                         # joystick FPC slot (oval)
        if f"slot {i}" in gone: continue
        dx, dy = sl["dx"], sl["dy"]; r = min(dx, dy) / 2
        b -= Pos(sl["x"], sl["y"], -t - 1) * extrude(SlotOverall(max(dx, dy), 2 * r, rotation=0 if dx >= dy else 90), t + 2)
    for h in D.get("js_pcb_holes", []):   # v0.19b: joystick standoff screws + hold-down springs (cad/joystick-param geom.json)
        b -= cyl(h["d"] / 2, -t - 1, t + 2, h["x"], h["y"])
    if D.get("vb"):   # [Ed 3 Nov] v4: PTH for the vertical boards' right-angle header legs (v0.24: the THT ones of the hybrid header)
        for sx in (-1, 1):
            for x, y, kind in D["vb_legs"][sx]:
                if kind == "tht":
                    b -= cyl(D["vb_hdr"]["drill"] / 2, -t - 1, t + 2, x, y)
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
    for px, py in (D["fm_pad_xy"] if D["feel_on"] else []):   # B.Cu pads [A] under the lead holes; wires drop from the 716's rear
        pad = Pos(px, py, -t - F["pad_t"]) * Rot(0, 0, D["fm_ang"] + 90) * Box(pl, pw, F["pad_t"], align=A)
        mcomps.append(pad - cyl(F["pad_hole"] / 2, -t - F["pad_t"] - 0.1, F["pad_t"] + 0.2, px, py))
    comps += [_mr(D) * c for c in mcomps]
    pad = cyl(D["rod_pad_r"], -t - D["rod_pad_t"], D["rod_pad_t"]) - cyl(D["h1_hole"] / 2, -t - 1, 2)
    out = {"PCB": b, "PCB back parts (Hall decouplers, J10, passives)": Compound(children=comps),
           f"PCB rod pad VBUS Ø{2 * D['rod_pad_r']:.1f} (B.Cu)": pad}
    out.update({k: _mr(D) * v for k, v in emitters(D).items()})
    w, h, th = D["clear_oled"]; cx, cy = D["clear_oled_xy"]
    dk = " + ".join(k for k in D["pcb_windows"] if k.startswith("D"))
    out[f'clear OLED 1.51" SSD1309 (PCB front, over window {dk})'] = Pos(cx, cy, 0) * Box(w, h, th, align=(Align.CENTER, Align.CENTER, Align.MIN))
    if D.get("pwr_vcsel_xy"):   # v0.52 [Ed 8 Nov 13:51]: the red VCSEL is the power light, straight up through the clear case
        vx, vy, vh = D["em_vcsel"]; px, py = D["pwr_vcsel_xy"]
        out["power light VCSEL 665 nm (JNJ 2835, PCB front)"] = Pos(px, py, 0) * Box(vx, vy, vh, align=(Align.CENTER, Align.CENTER, Align.MIN))
    if D.get("mcu"):   # MCU envelope over the leads, decoupling caps not modelled (panel frame)
        M = D["mcu"]; bw, bl, bh = M["body"]
        if M.get("side", "back") == "front":   # [Ed 3 Nov 09:47] v4: main-board front under the joystick
            out[f"MCU {M['part']} {M['pkg']} (PCB front, under the joystick)"] = Pos(M["xy"][0], M["xy"][1], 0.0) * Box(bw, bl, bh, align=A)
        else:   # [Ed 18:34] board back, low middle of D
            out[f"MCU {M['part']} {M['pkg']} (PCB back)"] = Pos(M["xy"][0], M["xy"][1], -t - bh) * Box(bw, bl, bh, align=A)
    return out

def _in_poly(x, y, poly):
    inside = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside

def window_hits(D, K):
    """KiCad back parts (panel-frame ones) whose footprint box touches a window, or the MCU courtyard when the MCU is on the back
    [Ed 18:34]. v4 (MCU on the front): only the windows count, so R30-R32 (under the old back courtyard) come back."""
    out = []
    M = D.get("mcu") if D.get("mcu", {}).get("side", "back") == "back" else None
    for p in K.get("back_parts", []):
        if _is_mech(D, p["x"], p["y"]):
            continue
        hw, hl = p["w"] / 2, p["l"] / 2
        pts = [(p["x"] + sx * hw, p["y"] + sy * hl) for sx in (-1, 0, 1) for sy in (-1, 0, 1)]
        if any(_in_poly(x, y, poly) for poly in D["pcb_windows"].values() for x, y in pts):
            out.append(p["ref"])
        elif M and abs(p["x"] - M["xy"][0]) < hw + M["court"] / 2 and abs(p["y"] - M["xy"][1]) < hl + M["court"] / 2:
            out.append(p["ref"])
    return out

def vb_footprint(D):
    """[Ed 3 Nov] v4: what the vertical boards put on the main-board front, as plan boxes (x0, x1, y0, y1): each board's edge, its
    header body and the header pads."""
    if not D.get("vb"):
        return []
    V, H = D["vb"], D["vb_hdr"]; y0, y1 = V["y"]; fo, fi = D["vb_face_out"], D["vb_face_in"]; r = H["pad"] / 2
    out = []
    for sx in (-1, 1):
        xs = sorted((sx * fi, sx * (fo + H["body_x"])))
        out.append((xs[0], xs[1], y0, D["vb_hdr_y1"]))
        out.append((min(sx * fi, sx * fo), max(sx * fi, sx * fo), y0, y1))
        for x, y, _ in D["vb_legs"][sx]:   # THT and SMT pads alike
            out.append((x - r, x + r, y - r, y + r))
    return out


def hole_hits(D, K):
    """[Ed 3 Nov] v4: KiCad holes / slots (panel-frame ones; the v0.16 joystick MH1 set is stale) that touch the MCU courtyard or
    the vertical boards' footprint on the main board. Left out of the proxy until the board is regenerated."""
    out = []
    M = D.get("mcu")
    boxes = list(vb_footprint(D))
    if M:
        (mx, my), c = M["xy"], M["court"] / 2
        boxes.append((mx - c, mx + c, my - c, my + c))
    def hit(x0, x1, y0, y1):
        return any(x0 < b[1] and b[0] < x1 and y0 < b[3] and b[2] < y1 for b in boxes)
    for i, h in enumerate(K.get("holes", [])):
        if _is_mech(D, h["x"], h["y"]): continue
        r = h["d"] / 2
        if hit(h["x"] - r, h["x"] + r, h["y"] - r, h["y"] + r): out.append(f"hole {i}")
    for i, sl in enumerate(K.get("slots", [])):
        if hit(sl["x"] - sl["dx"] / 2, sl["x"] + sl["dx"] / 2, sl["y"] - sl["dy"] / 2, sl["y"] + sl["dy"] / 2): out.append(f"slot {i}")
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
    mc = ([cyl(D["fm_shaft_hole"] / 2, -t - 2, t + 4, *D["fm_xy"]),
           cyl(D["fg_hole"] / 2, -t - 2, t + 4, *D["fg_xy"])] if D["feel_on"] else []) + \
         [cyl(D["brg"]["D"] / 2, -t - 2, t + 4, *D["enc_xy"])] + _em_cutters(D, t, 2.0)
    s -= _mr(D) * Compound(children=mc)
    return s

def _em_cutters(D, t, extra):
    """v0.52: a cut-out per upside-down RGB under the thrust race (mechanism frame); the LED's body sits in it."""
    cw_r, cw_t = D["em_cut"]
    return [Rot(0, 0, h["ang"]) * Pos(D["ot_r"], 0, -t - extra) * Box(cw_r, cw_t, t + 2 * extra, align=(Align.CENTER, Align.CENTER, Align.MIN))
            for h in D["em_holes"]]

def emitters(D):
    """v0.52: 24 SK6812MINI-E, soldered on the back pads with the body recessed in its cut-out, lens facing the race."""
    out = {}
    bx, by, bh = D["em_rgb"]
    for h in D["em_holes"]:
        out[f"emitter RGB {h['i'] + 1}"] = (Rot(0, 0, h["ang"]) * Pos(D["ot_r"], 0, D["em_body_z"][0])
                                           * Box(bx, by, bh, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return out

def drv_boxes(D):
    """716 driver cluster (U20 + C20–C22) on B.Cu: (x, y, w, l, h, angle) in the mechanism frame."""
    if not D["feel_on"]:   # Q27: no 716, no driver
        return []
    X, Y = D["drv_xy"]; a = math.radians(D["drv_rot"]); c, s = math.cos(a), math.sin(a)
    return [(X + c * dx - s * dy, Y + s * dx + c * dy, w, l, h, D["drv_rot"]) for _r, _fp, dx, dy, _rot, w, l, h in D["drv_cluster"]]

def drv_place(D):
    """Same cluster for the KiCad generator: ref -> (x, y, rot) in the mechanism frame (footprint rot + cluster turn)."""
    if not D["feel_on"]:
        return {}
    X, Y = D["drv_xy"]; a = math.radians(D["drv_rot"]); c, s = math.cos(a), math.sin(a)
    return {ref: (round(X + c * dx - s * dy, 3), round(Y + s * dx + c * dy, 3), (rot + D["drv_rot"]) % 360)
            for ref, _fp, dx, dy, rot, _w, _l, _h in D["drv_cluster"]}

def kicad_step_path():
    return STEP
