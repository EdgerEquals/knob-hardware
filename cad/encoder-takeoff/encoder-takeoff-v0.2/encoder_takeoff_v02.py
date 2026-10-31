"""Encoder take-off v0.2 (2026-10-31). Supersedes v0.1: Ed asked for the PCB bearing to come in from the other way,
so bearing 1 now presses in from the PCB BACK with its flange on the back face (KiCad H2 flipped to B). Only the bearing 1
position and the pinion hub length change; the pinion teeth, shaft ends, big gear and bearing 2 stay where they were.
v0.1 notes: Ed: a pressed-in bearing in the PCB, a small gear on top of it running on the dial's
bottom internal ring, the biggest gear that stays within the board below it, and the shaft down to the back panel on a second bearing.
Ed: a Ø2 shaft is enough. Parts: 2 x F682ZZ flanged bearings [A], Ø2 shaft, 14T encoder pinion, big gear. The encoder it drives is not drawn.
Position: H2 in KiCad (Bearing_F682ZZ_Press_NPTH_5.0mm), ENC_CD below the dial axis, i.e. 90° from the motor [A].
The big gear sits BEHIND the PCB [A]: the space above the PCB under the skirt is only 2 mm. The back panel position is unknown [A];
it is drawn only as a dashed reference line.
Local frame: encoder axis = Z, Z = height above the PCB front (negative = behind). Tags: [K] KiCad, [A] assumed."""
import math, os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "pcbs/knob-main-pcb", "knob/knob-v0.1", "knob/knob-v0.2", "shafts/fixed-shaft-brass-5x3-v0.2"):
    sys.path.insert(0, os.path.join(LIB, d))
import knob_main_pcb as pcb
import knob_gears as kg
import knob_v02 as kv

K = pcb.kicad_facts(); KV = kv.P; m = KV["module"]
_bb = pcb.board_solid().bounding_box()
P = dict(
    module=m,               # = dial bottom ring module 0.5
    z_ring=KV["z_bot_int"], # dial bottom internal ring 90T (knob v0.2)
    z_pinion=14,            # [A] 14T: 1.9 wall on the Ø2 shaft; (90 − 14) × 0.5 / 2 = 19.0 centre distance
    pinion_face=2.6,        # [A] inside the 2.0–5.0 ring band with 0.2 each end
    pinion_hub_d=3.5,       # [A] hub that rests on the bearing inner race
    shaft_d=2.0,            # [Ed] Ø2 steel shaft
    brg_d=2.0, brg_D=5.0, brg_B=2.3, brg_fd=6.1, brg_ft=0.6,   # [A] F682ZZ flanged: 2 x 5 x 2.3, flange 6.1 x 0.6
    board_margin=0.5,       # [A] big gear tip to the board outline
    gear_gap=0.5,           # [A] big gear below the shaft flange back face
    big_face=2.0,           # [A]
    big_hub_d=5.0, big_hub_len=2.0,   # [A]
    panel_gap=25.0,         # [A] PCB back face to the back panel inner face (unknown)
    pcb_t=_bb.max.Z - _bb.min.Z,      # [K] STEP board 1.51
    flange_t=4.0,           # brass shaft v0.2 flange thickness (behind the PCB)
)
p = P
p["centre_dist"] = (p["z_ring"] - p["z_pinion"]) * m / 2
p["kicad_cd"] = K["enc_y"] - K["shaft_y"]
assert abs(p["centre_dist"] - p["kicad_cd"]) < 1e-6, f"KiCad H2 offset {p['kicad_cd']} != gear centre distance {p['centre_dist']}"
p["ratio"] = p["z_ring"] / p["z_pinion"]
# heights
p["h_pin0"] = KV["h_skirt0"] + 0.2; p["h_pin1"] = p["h_pin0"] + p["pinion_face"]
p["h_brg_bot"] = -(p["pcb_t"] + p["brg_ft"])       # v0.2: bearing 1 flange on the PCB BACK face (inserted from the back)
p["h_brg_top"] = p["h_brg_bot"] + p["brg_B"]       # inner race top, just above the PCB front (pinion hub rests here)
p["h_big_top"] = -(p["pcb_t"] + p["flange_t"] + p["gear_gap"])
p["h_big_bot"] = p["h_big_top"] - p["big_face"]
p["h_panel"] = -(p["pcb_t"] + p["panel_gap"])      # back panel inner face (reference only)
p["h_b2_top"] = p["h_panel"] + p["brg_ft"]; p["h_b2_bot"] = p["h_b2_top"] - p["brg_B"]
p["shaft_len"] = p["h_pin1"] - p["h_b2_bot"]
# biggest gear inside the board outline, centred on H2
ex, ey = K["enc_x"], K["enc_y"]; bx0, bx1, by0, by1 = 0.75, 49.75, 10.5, 118.0   # [K] board outline (make_board.py)
p["r_avail"] = min(ex - bx0, bx1 - ex, ey - by0, by1 - ey) - p["board_margin"]
p["z_big"] = int(math.floor(2 * p["r_avail"] / m + 1e-9)) - 2
p["d_big_tip"] = (p["z_big"] + 2) * m; p["d_big_pitch"] = p["z_big"] * m; p["d_big_root"] = (p["z_big"] - 2.5) * m
p["d_pin_tip"] = (p["z_pinion"] + 2) * m; p["d_pin_root"] = (p["z_pinion"] - 2.5) * m
A = (Align.CENTER, Align.CENTER, Align.MIN)

def tube(od, idd, z0, h): return Pos(0, 0, z0) * (Cylinder(od / 2, h, align=A) - Cylinder(idd / 2, h, align=A))

def build_bearing(z_top, p=P, flange_down=False):
    """F682ZZ envelope [A]: flange on top (z_top - ft .. z_top), body below; flange_down flips it (flange at the bottom)."""
    z0 = z_top - p["brg_B"]
    body = tube(p["brg_D"], p["brg_d"], z0, p["brg_B"])
    fl = tube(p["brg_fd"], p["brg_d"], z0 if flange_down else z_top - p["brg_ft"], p["brg_ft"])
    return body + fl

def build_pinion(p=P):
    g = kg.gear_solid(kg.gear_pts(p["z_pinion"], m, m, 1.25 * m, -KV["backlash"] / 2, KV["pressure"]), p["h_pin0"], p["pinion_face"])
    hub = Pos(0, 0, p["h_brg_top"]) * Cylinder(p["pinion_hub_d"] / 2, p["h_pin0"] - p["h_brg_top"], align=A)
    return (g + hub) - Pos(0, 0, p["h_brg_top"]) * Cylinder(p["shaft_d"] / 2, p["h_pin1"] - p["h_brg_top"], align=A)

def build_big_gear(p=P):
    g = kg.gear_solid(kg.gear_pts(p["z_big"], m, m, 1.25 * m, -KV["backlash"] / 2, KV["pressure"]), p["h_big_bot"], p["big_face"])
    hub = Pos(0, 0, p["h_big_bot"] - p["big_hub_len"]) * Cylinder(p["big_hub_d"] / 2, p["big_hub_len"], align=A)
    L = p["big_face"] + p["big_hub_len"]
    return (g + hub) - Pos(0, 0, p["h_big_bot"] - p["big_hub_len"]) * Cylinder(p["shaft_d"] / 2, L, align=A)

def build_shaft(p=P):
    return Pos(0, 0, p["h_b2_bot"]) * Cylinder(p["shaft_d"] / 2, p["shaft_len"], align=A)

def parts(p=P):
    return {"encoder bearing 1 (PCB)": build_bearing(p["h_brg_top"], flange_down=True), "encoder pinion": build_pinion(),
            "encoder shaft": build_shaft(), "encoder big gear": build_big_gear(), "encoder bearing 2 (back panel)": build_bearing(p["h_b2_top"])}

RED = dict(color="red", weight="bold")
SUB3 = "Third-angle projection · mm · plan view drawn front-up (motor up)"
FLAG_BEHIND = ("Big gear BEHIND the PCB [A] (only 2 mm under the skirt); it passes under the shaft flange and the tube's wire exit [check]", RED)
BRG = "F682ZZ flanged bearing 2 × 5 × 2.3, flange Ø6.1 × 0.6 [A]"

def notes(sh, view, x, ytop, lines, step, size=6.5):
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        sh.note(view, x, ytop - i * step, l, 8 if i == 0 else size, **kw)

def sheet(shape, name, title, sub1, scale, dims, lines, step, gap=22, note_at=None, refs=()):
    from sheet import Sheet
    export_step(shape, os.path.join(HERE, name + ".step"))
    sh = Sheet(layout="panel", shape=shape, gap=gap, scale=scale, label_pad=12)
    for d in dims: getattr(sh, d[0])(*d[1:])
    for r in refs: sh.ref_line(*r)
    v, x, y = note_at or ("side", sh.bb["side"][1] + 3, sh.bb["side"][3])
    notes(sh, v, x, y, lines, step)
    sub = [sub1, "[K] = KiCad, [Ed] = Ed, [A] = assumed.", SUB3]
    sh.dxf(os.path.join(HERE, name + ".dxf"), [title] + sub)
    sh.png(os.path.join(HERE, name + "-drawing.png"), title, sub)

if __name__ == "__main__":
    pr = parts(); import itertools
    cl = {}
    for (na, a), (nb, b) in itertools.combinations(pr.items(), 2):
        r = a.intersect(b); v = sum(c.volume for c in (r if isinstance(r, (list, ShapeList)) else [r]) if c is not None) if r is not None else 0
        if v > 1e-3: cl[f"{na} / {nb}"] = v
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in p.items()}, "clashes", cl)
    T = "2026-10-31"
    # bearing
    b = build_bearing(p["brg_B"], flange_down=True); R, rf = p["brg_D"] / 2, p["brg_fd"] / 2
    sheet(b, "encoder-bearing-f682zz", f"Encoder bearing F682ZZ — v0.2, {T}", "Stock flanged miniature ball bearing (envelope).", 8,
          [("hdim", "front", -rf, rf, -rf, -rf - 0.8, f"Ø{p['brg_fd']:.1f} flange [A]"), ("hdim", "front", -p["brg_d"] / 2, p["brg_d"] / 2, 0, rf + 0.6, f"Ø{p['brg_d']:.0f} bore [Ed]"),
           ("vdim", "plan", 0, p["brg_B"], -R, -rf - 0.8, f"{p['brg_B']:.1f} [A]"), ("vdim", "plan", 0, p["brg_ft"], rf, rf + 0.8, f"{p['brg_ft']:.1f} flange [A]"),
           ("hdim", "plan", -R, R, p["brg_B"], p["brg_B"] + 0.8, f"Ø{p['brg_D']:.0f} OD [A]")],
          [BRG, f"Two used: H2 in the PCB (Ø{K['enc_hole']:.1f} NPTH press fit [K]) and the back panel [A]", "Shown as bearing 1: flange DOWN on the PCB back face, pressed in from the back (v0.2)", f"Body runs {p['h_brg_top']:.2f} proud of the PCB front ({p['brg_B']:.1f} − {p['pcb_t']:.2f} board − {p['brg_ft']:.1f} flange)", "Bearing 2: flange on the back panel inner face (unchanged)", "Envelope only (no balls drawn)"], 0.45)
    # pinion
    pn = build_pinion(); rt = p["d_pin_tip"] / 2
    sheet(Pos(0, 0, -p["h_brg_top"]) * pn, "encoder-pinion", f"Encoder pinion {p['z_pinion']}T — v0.2, {T}", f"{p['z_pinion']}T m{m:.1f} pinion on the Ø2 shaft, on bearing 1.", 8,
          [("hdim", "front", -rt, rt, -rt, -rt - 0.8, f"Ø{p['d_pin_tip']:.1f} tip"), ("hdim", "front", -p["shaft_d"] / 2, p["shaft_d"] / 2, 0, rt + 0.6, f"Ø{p['shaft_d']:.0f} bore [Ed]"),
           ("vdim", "plan", p["h_pin0"] - p["h_brg_top"], p["h_pin1"] - p["h_brg_top"], rt, rt + 0.8, f"{p['pinion_face']:.1f} face [A]"),
           ("vdim", "plan", 0, p["h_pin0"] - p["h_brg_top"], -p["pinion_hub_d"] / 2, -rt - 0.8, f"{p['h_pin0'] - p['h_brg_top']:.1f} hub Ø{p['pinion_hub_d']:.1f} [A]")],
          [f"{p['z_pinion']}T, m {m:.1f}, 20° involute; root Ø{p['d_pin_root']:.2f}, wall {(p['d_pin_root'] - p['shaft_d']) / 2:.2f} to the Ø2 shaft",
           f"Meshes inside the dial's {p['z_ring']}T bottom ring: ({p['z_ring']} − {p['z_pinion']}) × {m:.1f} / 2 = {p['centre_dist']:.2f} = H2 offset [K]",
           f"Ratio {p['z_ring']}:{p['z_pinion']} = {p['ratio']:.3f} (encoder shaft turns per dial turn)", f"Teeth {p['h_pin0']:.1f}–{p['h_pin1']:.1f} above the PCB front, hub on the bearing inner race"], 0.45)
    # shaft
    s = build_shaft()
    sheet(s, "encoder-shaft", f"Encoder shaft Ø2 — v0.2, {T}", f"Ø{p['shaft_d']:.0f} × {p['shaft_len']:.2f} steel shaft [A].", 3,
          [("vdim", "plan", p["h_b2_bot"], p["h_pin1"], -1, -6, f"{p['shaft_len']:.2f} shaft"), ("hdim", "front", -1, 1, -1, -3, f"Ø{p['shaft_d']:.0f} [Ed]")],
          [f"Ø{p['shaft_d']:.0f} ground steel [A], from the pinion top ({p['h_pin1']:.1f} above PCB front) to the bottom of bearing 2",
           f"Back panel {p['panel_gap']:.0f} behind the PCB back [A] (position unknown)"], 3.0, note_at=("plan", 8, p["h_pin1"]))
    # big gear
    bg = build_big_gear(); rb = p["d_big_tip"] / 2
    sheet(bg, "encoder-big-gear", f"Encoder big gear {p['z_big']}T — v0.2, {T}", f"{p['z_big']}T m{m:.1f}, the largest within the board outline.", 2.5,
          [("hdim", "front", -rb, rb, -rb, -rb - 4, f"Ø{p['d_big_tip']:.2f} tip = 2 × ({p['r_avail'] + p['board_margin']:.2f} to board edge − {p['board_margin']:.1f} [A])"),
           ("hdim", "front", -p["big_hub_d"] / 2, p["big_hub_d"] / 2, 0, rb + 3, f"Ø{p['big_hub_d']:.0f} hub [A], Ø2 bore"),
           ("vdim", "plan", p["h_big_bot"] - p["big_hub_len"], p["h_big_top"], rb, rb + 4, f"{p['big_face'] + p['big_hub_len']:.1f} gear + hub [A]")],
          [f"{p['z_big']}T, m {m:.1f} [A], 20° involute; pitch Ø{p['d_big_pitch']:.2f}", f"Limited by the 49.0 board width (H2 at x {K['enc_x']:.2f}) [K]",
           f"Top {-p['h_big_top']:.2f} behind the PCB front = board + {p['flange_t']:.0f} flange + {p['gear_gap']:.1f} [A]", "Drives the encoder (TBC, not drawn)", FLAG_BEHIND], 2.0)
    # together
    tog = Compound(children=list(pr.values()))
    rb2 = rb + 3
    refs = [("plan", -rb2, 0, rb2, 0, "PCB front"), ("plan", -rb2, -p["pcb_t"], rb2, -p["pcb_t"], "PCB back"),
            ("plan", -rb2, p["h_panel"], rb2, p["h_panel"], f"back panel [A], {p['panel_gap']:.0f} behind PCB"),
            ("side", 0, -rb2, 0, rb2, ""), ("side", p["pcb_t"], -rb2, p["pcb_t"], rb2, ""), ("side", -p["h_panel"], -rb2, -p["h_panel"], rb2, "back panel [A]")]
    clines = [(f"CLASH: {k} {v:.2f} mm³", RED) for k, v in cl.items()] or ["No clash between the encoder take-off parts"]
    sheet(tog, "encoder-takeoff-together", f"Encoder take-off v0.2 — together", f"{T}. Bearing, pinion, shaft, big gear, bearing 2; panel dashed.", 2.0,
          [("hdim", "front", -rb, rb, -rb, -rb - 4, f"Ø{p['d_big_tip']:.2f} big gear"),
           ("vdim", "plan", p["h_b2_bot"], p["h_pin1"], -rb, -rb - 4, f"{p['shaft_len']:.2f} shaft"),
           ("vdim", "plan", p["h_panel"], 0, rb, rb + 30, f"{-p['h_panel']:.2f} PCB front to panel [A]")],
          [f"Pinion {p['z_pinion']}T in the dial's {p['z_ring']}T internal ring, centre distance {p['centre_dist']:.2f} = KiCad H2 [K]; ratio {p['ratio']:.3f}",
           f"Big gear {p['z_big']}T Ø{p['d_big_tip']:.1f}; encoder TBC, not drawn", BRG + " × 2", *clines, FLAG_BEHIND], 3.0, gap=30,
          note_at=("plan", rb + 40, p["h_pin1"]), refs=refs)
