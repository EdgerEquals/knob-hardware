"""Knob v0.4 (big knob, 2026-10-31). Supersedes knob v0.3.
Ed: (1) concentric tubes the whole way down, one sleeved over the other, no bearings for now: the big knob gets a plain printed
tube that slides directly over the control-dial tube (the PTFE liner and the bezel thrust shoulder are dropped);
(2) no step on the OD at the bottom: one continuous Ø48.0 from top to bottom, with the 90T internal ring kept inside.
90T kept (tip Ø44.0 = skirt ID keeps the 2 mm motor clearance); its root Ø46.25 leaves a local wall of 0.875 [A, flagged].
Cap, skirt, 68T ring, 12T pinion as v0.2/v0.3. Frame: dial axis = Z, Z = height above the PCB front."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "knob/knob-v0.1", "knob/knob-v0.2", "control-dial/control-dial-v0.1"):
    sys.path.insert(0, os.path.join(LIB, d))
import knob_gears as kg
import knob_v02 as kv
import bezel as b1
flag_od, RED, notes, SUB3 = kv.flag_od, kv.RED, kv.notes, kv.SUB3

P = dict(kv.P)
p = P; m = p["module"]
p.update(
    brass_od=5.0,          # brass tube (shaft v0.2), innermost, fixed
    fit=0.12,              # [A] diametral sliding clearance at each tube interface (0.1-0.15)
    dial_tube_wall=1.5,    # [A] control-dial tube (printed PETG, >= 1.2)
    knob_tube_wall=1.5,    # [A] big-knob tube (printed, >= 1.2)
    cradle_boss_top=8.0,   # [A] base cradle v0.3 tube boss top (bonded length on the brass tube 8.0 >= 6)
    bearing_zone=5.0,      # [A] axial zone above the cradle boss reserved for a future bearing (e.g. MR105 5x10x4 / 685 5x11x5)
)
# Ed (accepted): both dial tubes stop above the base cradle's tube boss; the zone between is reserved for a future bearing.
p["knob_tube_z0"] = p["cradle_boss_top"] + p["bearing_zone"]         # 13.00
p["dial_tube_id"] = p["brass_od"] + p["fit"]                         # 5.12
p["dial_tube_od"] = p["dial_tube_id"] + 2 * p["dial_tube_wall"]      # 8.12
p["knob_tube_id"] = p["dial_tube_od"] + p["fit"]                     # 8.24
p["knob_tube_od"] = p["knob_tube_id"] + 2 * p["knob_tube_wall"]      # 11.24
p["bot_ring_od"] = p["skirt_od"]                                     # no step: Ø48.0 top to bottom
p["overall_od"] = p["skirt_od"]
p["bot_wall"] = (p["bot_ring_od"] - p["d_bi_root"]) / 2              # 0.875 local wall outside the 90T root
p["motor_gap_tube"] = (p["offset"] - kg.M["body_d"] / 2) - p["knob_tube_od"] / 2   # motor body to the knob tube, radial

def profile(p=P):
    rti, rto, ri, ro = p["knob_tube_id"] / 2, p["knob_tube_od"] / 2, p["skirt_id"] / 2, p["skirt_od"] / 2
    return [(rti, p["knob_tube_z0"]), (rto, p["knob_tube_z0"]), (rto, p["h_band1"]), (ri, p["h_band1"]), (ri, p["h_bi1"]),
            (ro, p["h_bi1"]), (ro, p["h_top"]), (rti, p["h_top"])]

def build_knob(p=P):
    f = Face(Wire.make_polygon([Vector(r, 0, z) for r, z in profile(p)], close=True))
    return revolve(f, Axis.Z, 360)

def parts(p=P):
    return {"knob cap+skirt+tube": build_knob(p), "internal ring 68T": kg.build_internal_ring(),
            "bottom internal ring": kv.build_bottom_internal_ring(p), "pinion": Pos(p["offset"], 0, p["h_pinion0"]) * kg.build_pinion()}

FLAG_TUBES = (f"Dial tubes stop at {P['knob_tube_z0']:.2f}; {P['cradle_boss_top']:.1f}–{P['knob_tube_z0']:.1f} above the cradle boss reserved for future bearing [A] (not drawn)")
FLAG_WALL = (f"90T ring kept (tip Ø{P['d_bi_tip']:.1f} = skirt ID, 2 mm motor clearance): wall outside the root only {P['bot_wall']:.3f} [A] at the no-step Ø{P['skirt_od']:.0f} [check]", RED)

if __name__ == "__main__":
    import itertools
    from sheet import Sheet
    pr = parts()
    export_step(pr["knob cap+skirt+tube"], os.path.join(HERE, "knob-cap-skirt-tube.step"))
    export_step(pr["bottom internal ring"], os.path.join(HERE, "bottom-internal-ring.step"))
    tog = Compound(children=list(pr.values()), label="knob-v0.4"); export_step(tog, os.path.join(HERE, "knob-v0.4-together.step"))
    cl = {}
    for (na, a), (nb, b) in itertools.combinations(pr.items(), 2):
        r = a.intersect(b); v = sum(c.volume for c in (r if isinstance(r, (list, ShapeList)) else [r]) if c is not None) if r is not None else 0
        if v > 1e-3: cl[f"{na} / {nb}"] = v
    print({k: round(p[k], 3) for k in ("dial_tube_id", "dial_tube_od", "knob_tube_id", "knob_tube_od", "bot_wall", "motor_gap_tube")}, "clashes", cl)
    ro, rti, rto = p["skirt_od"] / 2, p["knob_tube_id"] / 2, p["knob_tube_od"] / 2
    tube = f"Big-knob tube Ø{p['knob_tube_id']:.2f} ID × Ø{p['knob_tube_od']:.2f} OD ({p['knob_tube_wall']:.1f} wall [A]), {p['knob_tube_z0']:.1f}–{p['h_top']:.1f} above the PCB front"
    fit = f"Slides directly on the control-dial tube Ø{p['dial_tube_od']:.2f} ({p['fit']:.2f} diametral [A]); no liner, no bearing; axial location TBC"
    for name, shape, sc, title, items, extra in (
            ("knob-cap-skirt-tube", pr["knob cap+skirt+tube"], 1.9, "Big knob cap + skirt + tube — v0.4, 2026-10-31", {"knob": pr["knob cap+skirt+tube"]}, []),
            ("bottom-internal-ring", pr["bottom internal ring"], 2.4, "Bottom internal ring 90T (no OD step) — v0.4", {"ring": pr["bottom internal ring"]},
             [f"{p['z_bot_int']}T internal, m {m:.1f}; tip Ø{p['d_bi_tip']:.2f}, root Ø{p['d_bi_root']:.2f}; OD Ø{p['bot_ring_od']:.1f} = skirt OD (no step)"]),
            ("knob-v0.4-together", tog, 1.9, "Big knob v0.4 — cap/skirt/tube + rings + pinion", pr,
             [f"m {m:.1f}: pinion {p['z_pinion']}T, ring {p['z_ring']}T, centre distance {p['centre_dist']:.2f} = offset [K]",
              *([(f"CLASH: {k} {v:.2f} mm³", RED) for k, v in cl.items()] or ["No clash between the knob parts"])])):
        sh = Sheet(shape, gap=34, scale=sc, label_pad=16)
        sh.set_front_section(b1.section_items(items), "SECTION A-A (through dial and motor axes)")
        bb = sh.bb["front"]
        sh.hdim("front", -ro, ro, bb[3], bb[3] + 4, f"Ø{p['skirt_od']:.1f} OD, one diameter top to bottom [Ed]")
        if name != "bottom-internal-ring":
            sh.hdim("front", -rto, rto, p["knob_tube_z0"], p["knob_tube_z0"] - 3, f"Ø{p['knob_tube_od']:.2f} tube OD")
            sh.hdim("front", -rti, rti, p["knob_tube_z0"], p["knob_tube_z0"] - 7, f"Ø{p['knob_tube_id']:.2f} tube ID")
            sh.vdim("front", p["knob_tube_z0"], p["h_top"], ro, ro + 5, f"{p['h_top'] - p['knob_tube_z0']:.1f} tube to the top")
        sb = sh.bb["plan"]; sh.cut_line("plan", sb[0] - 3, sb[1] + 3, 0, +1, "A")
        notes(sh, "plan", sb[1] + 14, sb[3], [tube, fit, *extra, FLAG_WALL,
              FLAG_TUBES, f"Motor body to the tube: {p['motor_gap_tube']:.2f} radial", "Printed one piece (CF-ASA or PETG) [A]"], 2.6 * sc / 1.9)
        sub = ["2026-10-31. Tube sleeved on the control-dial tube; no OD step.", "[K] = KiCad, [Ed] = Ed, [A] = assumed.", "Third-angle · mm · z-up: top view above, section A-A front"]
        sh.dxf(os.path.join(HERE, name + ".dxf"), [title] + sub)
        sh.png(os.path.join(HERE, name + "-drawing.png"), title, sub)
