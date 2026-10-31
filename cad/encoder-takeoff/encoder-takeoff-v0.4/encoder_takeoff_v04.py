"""Encoder take-off v0.4 (2026-10-31). Supersedes v0.3.
Ed: the big knob is now located only at the top (688ZZ), so two more pinions 120° apart hold it at the bottom: three 14T pinions
in the 90T bottom ring; only the encoder pinion goes through to the big gear.
Idler pinions: identical 14T m0.5 teeth (2.2–4.8) and Ø3.5 hub, plain Ø2.1 bore [A] running on a fixed Ø2 steel pin [A]
(Ø1.5 [A] tried per Ed: strong enough), pins bonded in the base cradle plate.
Set angle: with the encoder 90° from the motor, the idler at +120° would sit 30° from the motor, 9.81 from its axis, i.e. into the
Ø12 motor body (needs 6.0 + 4.0 tip + 0.5 [A] = 10.5). The whole set is rotated by 3.0° [A] (minimum 2.88°) toward the motor side,
so that idler is at 33.0° from the motor, 10.52 from its axis. KiCad v0.7 moves H2 accordingly (19.0 from the axis, 0.99 off the
board centre line), so the biggest on-board big gear drops from 94T to 90T [flagged].
Frame: dial axis = Z, Z = height above the PCB front; motor at +X (0°)."""
import math, os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(LIB, "encoder-takeoff/encoder-takeoff-v0.3"))
import encoder_takeoff_v03 as e3
from encoder_takeoff_v03 import e2, K, m, RED, BRG, kg
import encoder_takeoff_v02 as _e2
P = e3.P; p = P
p.update(idler_bore=1.6,       # [A] plain running bore on the Ø1.5 pin
         pin_d=1.5,            # [A] Ed: try Ø1.5: steel, 3.6 lever, ~11 MPa per N of mesh load (yield > 300): OK for an m0.5 idler
         idler_hub_len=0.5,    # [A] hub under the teeth, thrust face on the pocket floor
         pin_head_d=3.5, pin_head_t=0.5,   # [A] head over the pinion (axial retention)
         run=0.1)              # [A] axial running gap under the head
p["set_rot"] = math.degrees(math.atan2(K["enc_x"] - K["shaft_x"], K["enc_y"] - K["shaft_y"]))   # 3.0 from KiCad v0.7
p["enc_ang"] = 270.0 + p["set_rot"]                       # dial frame, motor at 0°
p["idler_angs"] = [p["enc_ang"] + 120.0 - 360.0, p["enc_ang"] + 240.0 - 360.0]   # 33.0, 153.0
p["pocket_floor"] = p["h_pin0"] - p["idler_hub_len"]      # 1.70
p["pin_z0"] = 0.0                                         # pin bottom on the PCB front (through the 1.7 floor)
p["pin_z1"] = p["h_pin1"] + p["run"] + p["pin_head_t"]    # 5.40 head top
p["pin_len"] = p["pin_z1"] - p["pin_z0"]
p["pin_engage"] = p["pocket_floor"]                       # 1.70 in the cradle floor [check]
def idler_xy(a, p=P): return (p["centre_dist"] * math.cos(math.radians(a)), p["centre_dist"] * math.sin(math.radians(a)))
def enc_xy(p=P): return idler_xy(p["enc_ang"])
def phase(a, p=P):
    """Pinion spin (deg) that meshes it in the fixed 90T ring at dial angle a; v0.8 reference: a = 270, spin 0 (no clash)."""
    t = 360.0 / p["z_pinion"]
    return ((a - 270.0) * (1.0 - p["z_ring"] / p["z_pinion"])) % t
_mx = 14.0
p["idler_motor_d"] = min(math.hypot(x - _mx, y) for x, y in map(idler_xy, p["idler_angs"]))   # 10.52
p["idler_motor_gap"] = p["idler_motor_d"] - 6.0 - p["d_pin_tip"] / 2                      # >= 0.5 [A]
A = (Align.CENTER, Align.CENTER, Align.MIN)

def build_idler(p=P):
    """Idler pinion in its own frame (axis Z, heights above the PCB front)."""
    g = kg.gear_solid(kg.gear_pts(p["z_pinion"], m, m, 1.25 * m, -e2.KV["backlash"] / 2, e2.KV["pressure"]), p["h_pin0"], p["pinion_face"])
    hub = Pos(0, 0, p["pocket_floor"]) * Cylinder(p["pinion_hub_d"] / 2, p["idler_hub_len"], align=A)
    return (g + hub) - Pos(0, 0, p["pocket_floor"]) * Cylinder(p["idler_bore"] / 2, p["h_pin1"] - p["pocket_floor"], align=A)

def build_pin(p=P):
    shank = Pos(0, 0, p["pin_z0"]) * Cylinder(p["pin_d"] / 2, p["pin_z1"] - p["pin_head_t"] - p["pin_z0"], align=A)
    head = Pos(0, 0, p["pin_z1"] - p["pin_head_t"]) * Cylinder(p["pin_head_d"] / 2, p["pin_head_t"], align=A)
    return shank + head

def parts(p=P):
    """Encoder parts in the ENCODER frame (as v0.3); the pinion spun to mesh at the rotated set angle."""
    d = e3.parts(p); d["encoder pinion"] = Rot(0, 0, phase(p["enc_ang"])) * d["encoder pinion"]
    return d

def idler_parts(p=P):
    """Idler pinions + pins in the DIAL frame (dial axis origin)."""
    out = {}
    for i, a in enumerate(p["idler_angs"], 1):
        x, y = idler_xy(a)
        out[f"idler pinion {i}"] = Pos(x, y, 0) * Rot(0, 0, phase(a)) * build_idler(p)
        out[f"idler pin {i}"] = Pos(x, y, 0) * build_pin(p)
    return out

FLAG_BIG = (f"Big gear {P['z_big']}T Ø{P['d_big_tip']:.1f} (was 94T Ø48): H2 rotated {P['set_rot']:.1f}° [A] is {K['enc_x'] - K['shaft_x']:.2f} off the board centre line [check]", RED)
FLAG_PIN = (f"Idler pins engage only {P['pin_engage']:.1f} in the cradle floor (option: NPTH in the PCB, not made) [check]", RED)
FLAG_BEHIND = ("Big gear BEHIND the PCB [A] (only 2 mm under the skirt); 4.5 under the PCB back, brass tube now flush [check]", RED)
SET = f"3 × 14T pinions 120° apart in the 90T ring at r {P['centre_dist']:.1f}: encoder {P['enc_ang']:.1f}°, idlers {P['idler_angs'][0]:.1f}° and {P['idler_angs'][1]:.1f}° (motor 0°)"

if __name__ == "__main__":
    import itertools
    from sheet import Sheet
    e2.HERE = HERE
    print({k: (round(p[k], 3) if isinstance(p[k], float) else p[k]) for k in ("set_rot", "enc_ang", "idler_angs", "idler_motor_d", "idler_motor_gap", "pocket_floor", "pin_len", "z_big", "d_big_tip")})
    T = "2026-10-31"
    # idler pinion + pin sheet
    ip = build_idler(); pin = build_pin(); both = Compound(children=[ip, pin])
    rt = p["d_pin_tip"] / 2
    sh = Sheet(both, gap=20, scale=8, label_pad=10)
    sys.path.insert(0, os.path.join(LIB, "control-dial/control-dial-v0.1")); import bezel as b1
    sh.set_front_section(b1.section_items({"idler pinion": ip, "pin": pin}), "SECTION A-A (through the pin axis)")
    sh.hdim("front", -rt, rt, p["pin_z1"], p["pin_z1"] + 0.8, f"Ø{p['d_pin_tip']:.1f} tip")
    sh.hdim("front", -p["pin_head_d"] / 2, p["pin_head_d"] / 2, p["pin_z1"], p["pin_z1"] + 1.6, f"Ø{p['pin_head_d']:.1f} pin head [A]")
    sh.hdim("front", -p["pin_d"] / 2, p["pin_d"] / 2, 0, -0.8, f"Ø{p['pin_d']:.1f} pin [A]")
    sh.vdim("front", 0, p["pin_z1"], -rt, -rt - 0.8, f"{p['pin_len']:.1f} pin")
    sh.vdim("front", p["h_pin0"], p["h_pin1"], rt, rt + 0.8, f"{p['pinion_face']:.1f} face")
    sh.vdim("front", p["pocket_floor"], p["h_pin0"], rt, rt + 2.0, f"{p['idler_hub_len']:.1f} hub Ø{p['pinion_hub_d']:.1f}")
    sh.vdim("front", 0, p["pocket_floor"], rt, rt + 3.2, f"{p['pocket_floor']:.1f} in the cradle floor")
    sb = sh.bb["plan"]; sh.cut_line("plan", sb[0] - 0.5, sb[1] + 0.5, 0, +1, "A")
    lines = [f"Idler pinion ×2: {p['z_pinion']}T m {m:.1f} 20° involute, identical teeth/hub to the encoder pinion; plain Ø{p['idler_bore']:.1f} bore [A]",
             f"Teeth {p['h_pin0']:.1f}–{p['h_pin1']:.1f} above the PCB front; hub thrust face on the {p['pocket_floor']:.1f} pocket floor",
             f"Pin ×2: Ø{p['pin_d']:.1f} ground steel [A] (Ed: Ø1.5 tried; ~11 MPa/N bending, OK), {p['pin_len']:.1f} long, bonded through the floor onto the PCB front",
             f"Head Ø{p['pin_head_d']:.1f} × {p['pin_head_t']:.1f} [A] keeps the pinion on ({p['run']:.1f} axial run); or a pressed-on cap [A]",
             SET, FLAG_PIN, "Printed PETG/POM [A] (or the encoder pinion part with a reamed bore)"]
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        sh.note("plan", sb[1] + 2, sb[3] - i * 0.42, l, 8 if i == 0 else 6.5, **kw)
    title = f"Idler pinion {p['z_pinion']}T + pin — v0.4, {T}"
    sub = ["Two used, 120° and 240° from the encoder pinion, in the 90T bottom ring.", "[A] = assumed.", "Third-angle · mm · z-up: top view above, section A-A front"]
    sh.dxf(os.path.join(HERE, "idler-pinion-pin.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "idler-pinion-pin-drawing.png"), title, sub)
    # encoder together (big gear re-derived)
    pr = parts(); cl = {}
    for (na, a), (nb, b) in itertools.combinations(pr.items(), 2):
        r = a.intersect(b); v = sum(c.volume for c in (r if isinstance(r, (list, ShapeList)) else [r]) if c is not None) if r is not None else 0
        if v > 1e-3: cl[f"{na} / {nb}"] = v
    tog = Compound(children=list(pr.values())); rb = p["d_big_tip"] / 2; rb2 = rb + 3; cf = p["cradle_floor"]
    refs = [("plan", -rb2, 0, rb2, 0, "PCB front"), ("plan", -rb2, -p["pcb_t"], rb2, -p["pcb_t"], "PCB back"),
            ("plan", -rb2, cf, rb2, cf, "base cradle floor top"), ("plan", -rb2, p["h_panel"], rb2, p["h_panel"], f"back panel [A], {p['panel_gap']:.0f} behind PCB")]
    clines = [(f"CLASH: {k} {v:.2f} mm³", RED) for k, v in cl.items()] or ["No clash between the encoder take-off parts"]
    e2.sheet(tog, "encoder-takeoff-together", "Encoder take-off v0.4 — together", f"{T}. H2 rotated {p['set_rot']:.1f}° [A]; big gear re-derived.", 2.0,
          [("hdim", "front", -rb, rb, -rb, -rb - 4, f"Ø{p['d_big_tip']:.2f} big gear {p['z_big']}T"),
           ("vdim", "plan", p["h_b2_bot"], p["h_pin1"], -rb, -rb - 4, f"{p['shaft_len']:.2f} shaft"),
           ("vdim", "plan", p["h_panel"], 0, rb, rb + 30, f"{-p['h_panel']:.2f} PCB front to panel [A]")],
          ["Bearing 1 through the cradle floor into PCB H2 (dowel), as v0.3", SET, f"Idler nearest the motor: {p['idler_motor_d']:.2f} from the motor axis, {p['idler_motor_gap']:.2f} [A] tip to the Ø12 body",
           "Only the encoder pinion drives the big gear; idlers on fixed pins (sheet idler-pinion-pin)", FLAG_BIG, BRG + " × 2", *clines, FLAG_BEHIND], 3.0, gap=30,
          note_at=("plan", rb + 40, p["h_pin1"]), refs=refs)
