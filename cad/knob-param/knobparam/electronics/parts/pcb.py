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
    fx, fy = D["fm_xy"]; b -= cyl(0.8, -t - 1, t + 2, fx, fy)                       # M2 NPTH Ø1.6 (feel-motor shaft)
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
    return {"PCB": b, "PCB back parts (Hall decouplers, J2)": Compound(children=comps)}

STEP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kicad", "knob-main-pcb", "knob-main-pcb.step")

def pcb_full(D):
    """The real board (KiCad STEP export, committed in electronics/kicad/knob-main-pcb/), moved into the dial frame.
    Needs NO KiCad: only build123d's STEP import. Regenerate the STEP with kicad-cli after editing the board (see AGENTS.md)."""
    s = import_step(STEP); zf = s.bounding_box().max.Z
    return Pos(-D["axis_bx"], D["axis_by"], -zf) * s

def kicad_step_path():
    return STEP
