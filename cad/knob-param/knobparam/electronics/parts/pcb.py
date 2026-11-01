"""Main PCB PROXY: outline, holes (H1, H2, M2, 1220 tab slots) and the key back-side component boxes. Full KiCad STEP: pcb_full()."""
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
        b -= cyl(F["pad_hole"] / 2, -t - 1, t + 2, px, py)                          # M2 lead holes (shaft no longer passes the board)
    M = D["motor"]
    for s in (-1, 1):                                                                 # M1 tab slots
        b -= Pos(D["offset"] + s * M["term_pitch"] / 2, 0, -t - 1) * Box(M["term_t"] + 0.3, M["term_w"] + 0.3, t + 2, align=A)
    # back-side parts [K positions follow the params]: C3/C4 0402 behind U4/U5, J2 pads below the wheel
    comps = []
    if D["hall_layout"] == "vernier":   # one 0402 decoupler behind each Hall sensor [A]
        pts = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), a) for r, a in zip(D["hv_r"], D["hv_phi_s"])]
    else:
        pts = [(D["ha_r_m"] * math.cos(math.radians(a)), D["ha_r_m"] * math.sin(math.radians(a)), a) for a in D["ha_sens_angs"]]
    for x, y, a in pts:
        comps.append(Pos(x, y, -t - 0.5) * Rot(0, 0, a) * Box(0.5, 1.0, 0.5, align=A))
    comps.append(Pos(0, D["enc_xy"][1] - D["d_big_tip"] / 2 - 1.95, -t - 0.2) * Box(5.75, 2.45, 0.2, align=A))
    for px, py in D["fm_pad_xy"]:   # B.Cu pads [A] under the lead holes; wires drop from the 716's rear via the cradle pocket
        pad = Pos(px, py, -t - F["pad_t"]) * Rot(0, 0, D["fm_ang"] + 90) * Box(pl, pw, F["pad_t"], align=A)
        comps.append(pad - cyl(F["pad_hole"] / 2, -t - F["pad_t"] - 0.1, F["pad_t"] + 0.2, px, py))
    pad = cyl(D["rod_pad_r"], -t - D["rod_pad_t"], D["rod_pad_t"]) - cyl(D["h1_hole"] / 2, -t - 1, 2)
    return {"PCB": b, "PCB back parts (Hall decouplers, J2)": Compound(children=comps), f"PCB rod pad VBUS Ø{2 * D['rod_pad_r']:.1f} (B.Cu)": pad}

STEP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kicad", "knob-main-pcb", "knob-main-pcb.step")

def pcb_full(D):
    """The real board (KiCad STEP export, committed in electronics/kicad/knob-main-pcb/), moved into the dial frame.
    Needs NO KiCad: only build123d's STEP import. Regenerate the STEP with kicad-cli after editing the board (see AGENTS.md)."""
    s = import_step(STEP); zf = s.bounding_box().max.Z
    return Pos(-D["axis_bx"], D["axis_by"], -zf) * s

def kicad_step_path():
    return STEP
