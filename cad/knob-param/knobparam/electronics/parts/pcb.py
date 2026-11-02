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
    for p in K.get("back_parts", []):
        if p["ref"].startswith("C1") and len(p["ref"]) == 3: continue   # C11..C15 = the Hall decouplers above
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

def kicad_step_path():
    return STEP
