"""Knob v0.3 (2026-10-31). Supersedes knob v0.2 (../knob-v0.2).
Ed: the knob slides on the bezel with a PTFE tube. So the bronze bush 5x8x6 is replaced by a stock PTFE tube liner
10 OD x 8 ID x 6 [S] pressed in the hub, running on the bezel v0.1 journal (Ø7.9). Only the hub bore changes (Ø8.0 -> Ø10.0);
the hub keeps its 1.5 wall [A], so the hub OD follows (11.0 -> 13.0). Cap, skirt, 68T ring, 90T bottom ring and 12T pinion are
v0.2 unchanged (imported). Frame as v0.2: dial axis = Z, Z = height above the PCB front."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "knob/knob-v0.1", "knob/knob-v0.2", "control-dial/control-dial-v0.1"):
    sys.path.insert(0, os.path.join(LIB, d))
import knob_gears as kg
import knob_v02 as kv
import bezel as bz
from sheet import Sheet
flag_od, RED, notes, SUB3 = kv.flag_od, kv.RED, kv.notes, kv.SUB3

P = dict(kv.P)
p = P; m = p["module"]
p["hub_bore"] = bz.P["liner_od"]                 # [S] PTFE 10 OD (ATP AFE10); press / CA in the hub [A]
p["bush_od"] = p["hub_bore"]                     # kv.profile() reads the bore from bush_od
p["hub_od"] = p["hub_bore"] + 2 * p["hub_wall"]  # 13.0 (1.5 wall [A], as v0.1)

def parts(p=P):
    """Knob v0.3 parts in the knob frame (pinion at +X = motor offset)."""
    return {"knob cap+skirt": kv.build_cap_skirt(p), "internal ring 68T": kg.build_internal_ring(),
            "bottom internal ring": kv.build_bottom_internal_ring(), "pinion": Pos(p["offset"], 0, p["h_pinion0"]) * kg.build_pinion(),
            "PTFE liner": bz.build_liner()}

if __name__ == "__main__":
    import itertools
    pr = parts()
    export_step(pr["knob cap+skirt"], os.path.join(HERE, "knob-cap-skirt.step"))
    tog = Compound(children=list(pr.values()), label="knob-v0.3"); export_step(tog, os.path.join(HERE, "knob-v0.3-together.step"))
    cl = {}
    for (na, a), (nb, b) in itertools.combinations(pr.items(), 2):
        r = a.intersect(b); v = sum(c.volume for c in (r if isinstance(r, (list, ShapeList)) else [r]) if c is not None) if r is not None else 0
        if v > 1e-3: cl[f"{na} / {nb}"] = v
    print("hub", p["hub_bore"], p["hub_od"], "clashes", cl)
    ro, rbo, rhb, rho = p["skirt_od"] / 2, p["bot_ring_od"] / 2, p["hub_bore"] / 2, p["hub_od"] / 2
    BZ = bz.P
    liner = f"PTFE tube {BZ['liner_od']:.0f} × {BZ['liner_id']:.0f} × {BZ['liner_len']:.0f} [S] (ATP AFE10) in the hub, on the bezel Ø{BZ['journal_d']:.2f} journal"
    for name, shape, sc, title, extra in (
            ("knob-cap-skirt", pr["knob cap+skirt"], 1.9, "Knob cap + skirt — v0.3, 2026-10-31", []),
            ("knob-v0.3-together", tog, 1.9, "Knob v0.3 — cap/skirt + rings + pinion + PTFE liner",
             [f"m {m:.1f}: pinion {p['z_pinion']}T, ring {p['z_ring']}T, centre distance {p['centre_dist']:.2f} = offset [K]",
              f"Bottom ring {p['z_bot_int']}T internal (encoder pinion 14T meshes inside, encoder take-off v0.2)",
              *([(f"CLASH: {k} {v:.2f} mm³", kv.RED) for k, v in cl.items()] or ["No clash between the knob parts"])])):
        sh = Sheet(layout="panel", shape=shape, gap=30, scale=sc, label_pad=14)
        sh.set_front_section(bz.section_items({"part": shape} if name == "knob-cap-skirt" else pr), "SECTION A-A (through dial and motor axes)")
        sh.hdim("front", -rhb, rhb, p["h_hub0"], p["h_hub0"] - 4, f"Ø{p['hub_bore']:.1f} hub bore = PTFE OD [S] (was Ø8.0)")
        sh.hdim("front", -rho, rho, p["h_top"], p["h_top"] + 4, f"Ø{p['hub_od']:.1f} hub ({p['hub_wall']:.1f} wall [A])")
        sh.hdim("front", -ro, ro, p["h_top"], p["h_top"] + 10, f"Ø{p['skirt_od']:.2f} skirt OD (v0.2)")
        sh.vdim("front", p["h_hub0"], p["h_top"], rho, ro + 6, f"{p['bush_len']:.1f} hub")
        sb = sh.bb["side"]; sh.cut_line("side", sb[0] - 4, sb[1] + 4, 0, -1, "A")
        kv.notes(sh, "plan", rbo + 22, p["h_top"], [liner, "Only the hub bore changed from v0.2 (bronze bush 5x8x6 removed); hub OD follows the 1.5 wall",
                 *extra, kv.flag_od(), "Printed one piece (CF-ASA or PETG) [A]"], 2.6)
        sub = ["2026-10-31. Bronze bush -> PTFE 10x8 liner on the bezel journal.", "[K] = KiCad, [S] = stock, [A] = assumed.", kv.SUB3]
        sh.dxf(os.path.join(HERE, name + ".dxf"), [title] + sub)
        sh.png(os.path.join(HERE, name + "-drawing.png"), title, sub)
