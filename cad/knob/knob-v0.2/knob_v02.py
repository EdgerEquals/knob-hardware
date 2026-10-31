"""Knob v0.2 (2026-10-31). Supersedes knob v0.1 (../knob-v0.1).
Ed: the dial body comes around the OUTSIDE of the offset motor, down to 2 mm above the PCB front (wider than the board is fine),
and the encoder take-off at the bottom is an INTERNAL ring gear (not external).
Kept from v0.1 by import: the top region, the 12T pinion, the 68T internal ring, the hub and the bronze bush 5x8x6 [A].
New here: the cap + skirt body, and the bottom internal ring at the skirt's bottom inner edge (the encoder-takeoff v0.1 pinion meshes inside).
Printed one piece (CF-ASA or PETG) [A]; parts drawn separately. Frame as v0.1: dial axis = Z, Z = height above the PCB front."""
import math, os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "knob/knob-v0.1", "motors/1220-coreless-planetary"):
    sys.path.insert(0, os.path.join(LIB, d))
import knob_gears as kg
import motor_gearbox as mg
from sheet import Sheet

M = mg.VARIANTS["motor-1220"]
P = dict(kg.P)
p = P; m = p["module"]
p.update(
    motor_r_out=p["offset"] + M["body_d"] / 2,   # [K]+[M] 14.0 + 6.0 = 20.0: motor body outermost point from the dial axis
    skirt_clear=2.0,       # [Ed] radial clearance skirt ID to the motor body
    skirt_wall=2.0,        # [A] plain skirt wall (Ed: about 1.5-2)
    skirt_gap=2.0,         # [Ed] skirt bottom above the PCB front
    bot_face=3.0,          # [A] bottom internal ring face width
    bot_ring_wall=1.5,     # [A] wall outside the bottom ring root (band OD steps out if needed)
    pcb_w=49.0,            # [K] main PCB width (49.00 board)
)
p["skirt_id"] = 2 * (p["motor_r_out"] + p["skirt_clear"])          # 44.0
p["skirt_od"] = p["skirt_id"] + 2 * p["skirt_wall"]                 # 48.0
# bottom internal ring: smallest tooth count whose TIP circle stays outside the skirt ID (teeth do not eat the 2 mm motor clearance)
p["z_bot_int"] = math.ceil(p["skirt_id"] / m + 2 - 1e-9)            # (z - 2) m >= ID  -> 90
p["d_bi_pitch"] = p["z_bot_int"] * m; p["d_bi_tip"] = (p["z_bot_int"] - 2) * m; p["d_bi_root"] = (p["z_bot_int"] + 2.5) * m
p["bot_ring_od"] = max(p["skirt_od"], p["d_bi_root"] + 2 * p["bot_ring_wall"])   # 49.25
p["h_skirt0"] = p["skirt_gap"]; p["h_bi1"] = p["h_skirt0"] + p["bot_face"]
p["overall_od"] = max(p["skirt_od"], p["bot_ring_od"])

def profile(p=P):
    """Cap + hub + skirt half-section (r, z), closed. The bottom ring band (h_skirt0..h_bi1) is a separate part."""
    rb, rh, ri, ro = p["bush_od"] / 2, p["hub_od"] / 2, p["skirt_id"] / 2, p["skirt_od"] / 2
    return [(rb, p["h_hub0"]), (rh, p["h_hub0"]), (rh, p["h_band1"]), (ri, p["h_band1"]), (ri, p["h_bi1"]),
            (ro, p["h_bi1"]), (ro, p["h_top"]), (rb, p["h_top"])]

def build_cap_skirt(p=P):
    f = Face(Wire.make_polygon([Vector(r, 0, z) for r, z in profile(p)], close=True))
    return revolve(f, Axis.Z, 360)

def build_bottom_internal_ring(p=P):
    h0, h = p["h_skirt0"], p["bot_face"]
    cutter = kg.gear_solid(kg.gear_pts(p["z_bot_int"], m, 1.25 * m, 1.0 * m, +p["backlash"] / 2, p["pressure"]), h0, h)
    return Pos(0, 0, h0) * Cylinder(p["bot_ring_od"] / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN)) - cutter

def parts(p=P):
    """All knob v0.2 parts in the knob frame (pinion at +X = motor offset)."""
    return {"knob cap+skirt": build_cap_skirt(p), "internal ring 68T": kg.build_internal_ring(),
            "bottom internal ring": build_bottom_internal_ring(p),
            "pinion": Pos(p["offset"], 0, p["h_pinion0"]) * kg.build_pinion(), "bronze bush": kg.build_bush()}

RED = dict(color="red", weight="bold")
SUB3 = "Third-angle projection · mm · plan view drawn front-up (motor up)"

def notes(sh, view, x, ytop, lines, step, size=6.5):
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        sh.note(view, x, ytop - i * step, l, 8 if i == 0 else size, **kw)

def flag_od(p=P):
    return (f"Skirt OD {p['skirt_od']:.2f} (ring band Ø{p['bot_ring_od']:.2f}) is over the {p['pcb_w']:.0f} PCB width and the Ø{p['bezel_d']:.0f} bezel [check]", RED)

if __name__ == "__main__":
    pr = parts()
    for n, f in (("knob-cap-skirt", pr["knob cap+skirt"]), ("bottom-internal-ring", pr["bottom internal ring"])):
        export_step(f, os.path.join(HERE, n + ".step"))
    tog = Compound(children=list(pr.values()), label="knob-v0.2")
    export_step(tog, os.path.join(HERE, "knob-v0.2-together.step"))
    import itertools
    cl = {}
    for (na, a), (nb, b) in itertools.combinations(pr.items(), 2):
        r = a.intersect(b); v = sum(c.volume for c in (r if isinstance(r, (list, ShapeList)) else [r]) if c is not None) if r is not None else 0
        if v > 1e-3: cl[f"{na} / {nb}"] = v
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in p.items() if k.startswith(("skirt", "z_bot", "d_bi", "bot_", "h_skirt", "h_bi", "overall", "motor_r"))}, "clashes", cl)
    ri, ro, rbo = p["skirt_id"] / 2, p["skirt_od"] / 2, p["bot_ring_od"] / 2
    sys.path.insert(0, os.path.join(LIB, "encoder-takeoff", "encoder-takeoff-v0.1"))
    import encoder_takeoff as enc   # lazy: encoder_takeoff imports this module
    ENC = f"Encoder pinion {enc.P['z_pinion']}T meshes inside (encoder-takeoff v0.1, ratio {enc.P['ratio']:.3f})"

    # ---- sheet 1: cap + skirt ----
    k = pr["knob cap+skirt"]
    sh = Sheet(layout="panel", shape=k, gap=26, scale=1.9, label_pad=14)
    sh.hdim("front", -ro, ro, -ro, -ro - 5, f"Ø{p['skirt_od']:.2f} skirt OD ({p['skirt_wall']:.1f} wall [A])")
    sh.hdim("front", -ri, ri, 0, ro + 3, f"Ø{p['skirt_id']:.2f} skirt ID = 2 × ({p['motor_r_out']:.1f} motor reach + {p['skirt_clear']:.1f}) [Ed]")
    sh.hdim("front", -p["bush_od"] / 2, p["bush_od"] / 2, 0, -p["hub_od"] / 2 - 3, f"Ø{p['bush_od']:.1f} bore: bronze bush 5x8x6 [A]")
    sh.vdim("plan", p["h_bi1"], p["h_top"], -ro, -ro - 4, f"{p['h_top'] - p['h_bi1']:.1f} skirt to the ring band")
    sh.vdim("plan", p["h_band1"], p["h_top"], ro, ro + 4, f"{p['cap_t']:.1f} cap [A]")
    sh.vdim("plan", p["h_hub0"], p["h_top"], p["hub_od"] / 2, ro + 10, f"{p['bush_len']:.1f} hub")
    notes(sh, "plan", ro + 22, p["h_top"], [f"Top {p['h_top']:.1f} above PCB front; skirt down to the bottom ring band at {p['h_bi1']:.1f}",
        f"Bottom ring band {p['h_skirt0']:.1f}–{p['h_bi1']:.1f}: skirt ends {p['skirt_gap']:.1f} above the PCB front [Ed]",
        "Cap, hub, 68T ring band and bottom ring print as one piece (CF-ASA or PETG) [A]", flag_od(), kg.P and (f"Hub, bush, 68T ring, 12T pinion unchanged from knob v0.1", {})], 2.6)
    title = "Knob cap + skirt — v0.2, 2026-10-31"
    sub = [f"Skirt Ø{p['skirt_id']:.1f} ID × Ø{p['skirt_od']:.1f} OD round the offset motor.", "Z = height above the PCB front. [Ed] = Ed, [A] = assumed.", SUB3]
    sh.dxf(os.path.join(HERE, "knob-cap-skirt.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "knob-cap-skirt-drawing.png"), title, sub)

    # ---- sheet 2: bottom internal ring ----
    b = pr["bottom internal ring"]
    sh = Sheet(layout="panel", shape=b, gap=26, scale=2.4, label_pad=14)
    sh.hdim("front", -rbo, rbo, -rbo, -rbo - 4, f"Ø{p['bot_ring_od']:.2f} OD ({p['bot_ring_wall']:.1f} outside root) [A]")
    sh.hdim("front", -p["d_bi_tip"] / 2, p["d_bi_tip"] / 2, 0, rbo + 3, f"Ø{p['d_bi_tip']:.2f} tip = skirt ID")
    sh.hdim("front", -p["d_bi_root"] / 2, p["d_bi_root"] / 2, 0, rbo + 8, f"Ø{p['d_bi_root']:.2f} root")
    sh.vdim("plan", p["h_skirt0"], p["h_bi1"], rbo, rbo + 4, f"{p['bot_face']:.1f} face [A]")
    notes(sh, "plan", rbo + 16, p["h_bi1"] + 6, [f"{p['z_bot_int']}T INTERNAL, m {m:.1f}, 20° involute; pitch Ø{p['d_bi_pitch']:.2f}",
        "Tooth count: smallest with the tip circle >= the skirt ID (keeps the 2 mm motor clearance)",
        f"At the skirt's bottom inner edge, {p['h_skirt0']:.1f}–{p['h_bi1']:.1f} above the PCB front", ENC,
        "Replaces the v0.1 external 79T ring", flag_od()], 2.0)
    title = "Bottom internal ring (encoder) — v0.2"
    sub = [f"2026-10-31. {p['z_bot_int']}T internal ring, m{m:.1f}, at the skirt bottom.", "[A] = assumed.", SUB3]
    sh.dxf(os.path.join(HERE, "bottom-internal-ring.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "bottom-internal-ring-drawing.png"), title, sub)

    # ---- sheet 3: together ----
    sh = Sheet(layout="panel", shape=tog, gap=26, scale=1.9, label_pad=14)
    sh.hdim("front", 0, p["offset"], 0, -rbo - 4, f"{p['offset']:.1f} motor offset [K]")
    sh.hdim("front", -rbo, rbo, -rbo, -rbo - 10, f"Ø{p['bot_ring_od']:.2f} overall OD")
    sh.vdim("plan", p["h_skirt0"], p["h_top"], -rbo, -rbo - 4, f"{p['h_top'] - p['h_skirt0']:.1f} knob height")
    sh.vdim("plan", 0, p["h_skirt0"], rbo, rbo + 4, f"{p['skirt_gap']:.1f} to PCB front [Ed]")
    sh.vdim("plan", p["h_pinion0"], p["h_shaft_tip"], p["offset"] + 3.5, rbo + 10, f"{p['pinion_face']:.1f} pinion")
    clines = [(f"CLASH: {k} {v:.2f} mm³", RED) for k, v in cl.items()] or ["No clash between the knob parts"]
    notes(sh, "plan", rbo + 22, p["h_top"], [f"m {m:.1f}: pinion {p['z_pinion']}T, ring {p['z_ring']}T, ({p['z_ring']} − {p['z_pinion']}) × {m:.1f} / 2 = {p['centre_dist']:.2f} = offset [K]",
        f"Bottom ring {p['z_bot_int']}T internal; {ENC[0].lower() + ENC[1:]}", "bronze bush 5x8x6 [A] in the hub", *clines, flag_od(),
        (f"Pinion {p['z_pinion']}T: wall {p['pin_wall']:.2f} to the 3 mm shaft; undercut below 17T [check]", RED)], 2.6)
    title = "Knob v0.2 — cap/skirt + rings + pinion + bush"
    sub = ["2026-10-31. Skirt round the motor; bottom ring now internal.", "[K] = KiCad, [Ed] = Ed, [A] = assumed.", SUB3]
    sh.dxf(os.path.join(HERE, "knob-v0.2-together.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "knob-v0.2-together-drawing.png"), title, sub)
