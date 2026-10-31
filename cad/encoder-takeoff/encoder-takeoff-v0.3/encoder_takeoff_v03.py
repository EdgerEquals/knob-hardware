"""Encoder take-off v0.3 (2026-10-31). Supersedes v0.2. Ed: bearing 1 presses into the BASE CRADLE as well as the PCB, so it
doubles as a locating dowel when gluing the cradle on (the brass tube in H1 is the second dowel).
Bearing 1 now goes in from the FRONT: flange on the top face of the cradle's 1.0 [A] floor under the pinion, body through the
floor and 0.70 into the PCB H2 hole (Ø5.0 NPTH, unchanged; KiCad v0.6 puts H2 back on F). Pinion teeth, shaft, big gear 94T,
bearing 2 and the H2 position (90° from the motor, 19.0 below the dial axis along the board) are unchanged; the pinion hub
is shorter (it rests on the inner race, now 1.60 above the PCB front).
Local frame: encoder axis = Z, Z = height above the PCB front. Tags: [K] KiCad, [A] assumed."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(LIB, "encoder-takeoff/encoder-takeoff-v0.2"))
import encoder_takeoff_v02 as e2
from encoder_takeoff_v02 import K, m, RED, BRG, build_bearing, build_pinion, build_shaft, build_big_gear, kg
P = e2.P; p = P                                      # v0.2 params, updated in place (functions read this dict)
p["cradle_floor"] = 1.0                              # [A] base cradle floor under the pinion (skirt and 90T ring start at 2.0)
p["h_brg_top"] = p["cradle_floor"] + p["brg_ft"]     # 1.60 flange top = inner race top (pinion hub rests here)
p["h_brg_bot"] = p["h_brg_top"] - p["brg_B"]         # -0.70 into the PCB
p["into_pcb"] = -p["h_brg_bot"]                      # 0.70 of the 1.51 board (dowel across the glue joint)
p["into_cradle"] = p["cradle_floor"]                 # 1.00
assert p["h_brg_top"] < p["h_pin0"] and p["into_pcb"] < p["pcb_t"]

def parts(p=P):
    return {"encoder bearing 1 (cradle+PCB)": build_bearing(p["h_brg_top"]), "encoder pinion": build_pinion(),
            "encoder shaft": build_shaft(), "encoder big gear": build_big_gear(), "encoder bearing 2 (back panel)": build_bearing(p["h_b2_top"])}
FLAG_BEHIND = ("Big gear BEHIND the PCB [A] (only 2 mm under the skirt); passes 0.5 under the brass tube end and its wire exit [check]", RED)

if __name__ == "__main__":
    import itertools
    e2.HERE = HERE
    pr = parts(); cl = {}
    for (na, a), (nb, b) in itertools.combinations(pr.items(), 2):
        r = a.intersect(b); v = sum(c.volume for c in (r if isinstance(r, (list, ShapeList)) else [r]) if c is not None) if r is not None else 0
        if v > 1e-3: cl[f"{na} / {nb}"] = v
    print({k: round(p[k], 3) for k in ("h_brg_top", "h_brg_bot", "into_pcb", "h_pin0", "h_pin1", "shaft_len", "z_big", "d_big_tip")}, "clashes", cl)
    T = "2026-10-31"
    pn = build_pinion(); rt = p["d_pin_tip"] / 2
    e2.sheet(Pos(0, 0, -p["h_brg_top"]) * pn, "encoder-pinion", f"Encoder pinion {p['z_pinion']}T — v0.3, {T}", f"{p['z_pinion']}T m{m:.1f} pinion on the Ø2 shaft, on bearing 1.", 8,
          [("hdim", "front", -rt, rt, -rt, -rt - 0.8, f"Ø{p['d_pin_tip']:.1f} tip"), ("hdim", "front", -p["shaft_d"] / 2, p["shaft_d"] / 2, 0, rt + 0.6, f"Ø{p['shaft_d']:.0f} bore [Ed]"),
           ("vdim", "plan", p["h_pin0"] - p["h_brg_top"], p["h_pin1"] - p["h_brg_top"], rt, rt + 0.8, f"{p['pinion_face']:.1f} face [A]"),
           ("vdim", "plan", 0, p["h_pin0"] - p["h_brg_top"], -p["pinion_hub_d"] / 2, -rt - 0.8, f"{p['h_pin0'] - p['h_brg_top']:.1f} hub Ø{p['pinion_hub_d']:.1f} [A]")],
          [f"{p['z_pinion']}T, m {m:.1f}, 20° involute, teeth {p['h_pin0']:.1f}–{p['h_pin1']:.1f} above the PCB front (unchanged)",
           f"Hub now {p['h_pin0'] - p['h_brg_top']:.1f} (v0.2: 2.0): rests on the bearing inner race at {p['h_brg_top']:.2f}",
           f"Ratio {p['z_ring']}:{p['z_pinion']} = {p['ratio']:.3f}; centre distance {p['centre_dist']:.2f} = H2 [K]"], 0.45)
    tog = Compound(children=list(pr.values())); rb = p["d_big_tip"] / 2; rb2 = rb + 3
    cf = p["cradle_floor"]
    refs = [("plan", -rb2, 0, rb2, 0, "PCB front"), ("plan", -rb2, -p["pcb_t"], rb2, -p["pcb_t"], "PCB back"),
            ("plan", -rb2, cf, rb2, cf, "base cradle floor top"),
            ("plan", -rb2, p["h_panel"], rb2, p["h_panel"], f"back panel [A], {p['panel_gap']:.0f} behind PCB")]
    clines = [(f"CLASH: {k} {v:.2f} mm³", RED) for k, v in cl.items()] or ["No clash between the encoder take-off parts"]
    e2.sheet(tog, "encoder-takeoff-together", "Encoder take-off v0.3 — together", f"{T}. Bearing 1 through the cradle floor into the PCB (dowel).", 2.0,
          [("hdim", "front", -rb, rb, -rb, -rb - 4, f"Ø{p['d_big_tip']:.2f} big gear {p['z_big']}T (unchanged)"),
           ("vdim", "plan", p["h_b2_bot"], p["h_pin1"], -rb, -rb - 4, f"{p['shaft_len']:.2f} shaft"),
           ("vdim", "plan", p["h_panel"], 0, rb, rb + 30, f"{-p['h_panel']:.2f} PCB front to panel [A]")],
          [f"Bearing 1 pressed in from the FRONT: flange on the {cf:.1f} [A] cradle floor, body {cf:.1f} in the cradle + {p['into_pcb']:.2f} in the PCB H2 Ø{K['enc_hole']:.1f} [K]",
           "It locates the base cradle on the PCB while gluing (second dowel: the brass tube in H1)",
           f"KiCad v0.6: H2 back on the front side, hole unchanged; DRC 0", f"Pinion {p['z_pinion']}T in the {p['z_ring']}T ring, H2 90° from the motor, {p['centre_dist']:.1f} below the dial axis [K]",
           BRG + " × 2", *clines, FLAG_BEHIND], 3.0, gap=30, note_at=("plan", rb + 40, p["h_pin1"]), refs=refs)
