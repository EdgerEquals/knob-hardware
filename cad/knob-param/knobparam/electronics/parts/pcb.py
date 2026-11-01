"""Main PCB PROXY: outline, holes (H1, H2, M2, 1220 tab slots + KiCad extras: M1 Ø3.2 relief, joystick spring / pin holes and FPC slot)
and the key back-side component boxes. KiCad is the source of truth: the extras and the back-side parts come from
kicad/knob-main-pcb/pcb_proxy.json (export_pcb_proxy.py, run after make_board.py; read by params.derive -> D['pcb_kicad']). Full KiCad STEP: pcb_full()."""
import math, os
from build123d import *
from ...common.util import A, cyl

def board_xy(D, bx, by): return (bx - D["axis_bx"], -(by - D["axis_by"]))

def build(D):
    t, w = D["pcb_t"], D["pcb_w"]
    yc = (D["pcb_above"] - D["pcb_below"]) / 2
    b = Pos(0, yc, -t) * Box(w, D["pcb_above"] + D["pcb_below"], t, align=A)
    b -= cyl(D["h1_hole"] / 2, -t - 1, t + 2)
    ex, ey = D["enc_xy"]; b -= cyl(D["brg"]["D"] / 2, -t - 1, t + 2, ex, ey)          # H2 press bore
    F = D["feel"]; pw, pl = F["pad"]   # (radial, tangential) copper around each lead hole
    for px, py in D["fm_pad_xy"]:
        b -= cyl(F["pad_hole"] / 2, -t - 1, t + 2, px, py)                          # M2 lead holes
    # v0.17: 716 shaft and the compound-idler pin pass the board. Holes are in the proxy; KiCad NPTHs are still to add.
    b -= cyl(D["fm_shaft_hole"] / 2, -t - 1, t + 2, *D["fm_xy"])
    b -= cyl(D["fg_hole"] / 2, -t - 1, t + 2, *D["fg_xy"])
    M = D["motor"]
    for s in (-1, 1):                                                                 # M1 tab slots
        b -= Pos(D["offset"] + s * M["term_pitch"] / 2, 0, -t - 1) * Box(M["term_t"] + 0.3, M["term_w"] + 0.3, t + 2, align=A)
    K = D["pcb_kicad"]
    for h in K.get("holes", []): b -= cyl(h["d"] / 2, -t - 1, t + 2, h["x"], h["y"])               # M1 relief, joystick springs / pins
    for sl in K.get("slots", []):                                                                       # joystick FPC slot (oval)
        dx, dy = sl["dx"], sl["dy"]; r = min(dx, dy) / 2
        b -= Pos(sl["x"], sl["y"], -t - 1) * extrude(SlotOverall(max(dx, dy), 2 * r, rotation=0 if dx >= dy else 90), t + 2)
    # back-side parts: Hall decouplers behind each sensor [K positions follow the params]; the rest from KiCad (pcb_proxy.json)
    comps = []
    if D["hall_layout"] == "vernier":   # one 0402 decoupler behind each Hall sensor [A]
        pts = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), a) for r, a in zip(D["hv_r"], D["hv_phi_s"])]
    else:
        pts = [(D["ha_r_m"] * math.cos(math.radians(a)), D["ha_r_m"] * math.sin(math.radians(a)), a) for a in D["ha_sens_angs"]]
    for x, y, a in pts:
        comps.append(Pos(x, y, -t - 0.5) * Rot(0, 0, a) * Box(0.5, 1.0, 0.5, align=A))
    for p in K.get("back_parts", []):
        if p["ref"].startswith("C1") and len(p["ref"]) == 3: continue   # C11..C15 = the Hall decouplers above
        comps.append(Pos(p["x"], p["y"], -t - p["h"]) * Box(p["w"], p["l"], p["h"], align=A))
    for px, py in D["fm_pad_xy"]:   # B.Cu pads [A] under the lead holes; wires drop from the 716's rear via the cradle pocket
        pad = Pos(px, py, -t - F["pad_t"]) * Rot(0, 0, D["fm_ang"] + 90) * Box(pl, pw, F["pad_t"], align=A)
        comps.append(pad - cyl(F["pad_hole"] / 2, -t - F["pad_t"] - 0.1, F["pad_t"] + 0.2, px, py))
    pad = cyl(D["rod_pad_r"], -t - D["rod_pad_t"], D["rod_pad_t"]) - cyl(D["h1_hole"] / 2, -t - 1, 2)
    return {"PCB": b, "PCB back parts (Hall decouplers, J10, DRV8837, passives)": Compound(children=comps), f"PCB rod pad VBUS Ø{2 * D['rod_pad_r']:.1f} (B.Cu)": pad}

STEP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kicad", "knob-main-pcb", "knob-main-pcb.step")

def pcb_full(D):
    """The real board (KiCad STEP export, committed in electronics/kicad/knob-main-pcb/), moved into the dial frame.
    Needs NO KiCad: only build123d's STEP import. Regenerate the STEP with kicad-cli after editing the board (see AGENTS.md)."""
    s = import_step(STEP); zf = s.bounding_box().max.Z
    s = Pos(-D["axis_bx"], D["axis_by"], -zf) * s
    # same NPTHs the proxy drills; the KiCad board does not have them yet (see design notes).
    # v0.18 moved H2 with the herringbone centre distance, so the committed STEP hole is drilled out at the new axis too.
    t = D["pcb_t"]
    s -= cyl(D["fm_shaft_hole"] / 2, -t - 2, t + 4, *D["fm_xy"])
    s -= cyl(D["fg_hole"] / 2, -t - 2, t + 4, *D["fg_xy"])
    s -= cyl(D["brg"]["D"] / 2, -t - 2, t + 4, *D["enc_xy"])
    return s

def kicad_step_path():
    return STEP
