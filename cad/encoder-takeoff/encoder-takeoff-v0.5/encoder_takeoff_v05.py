"""ENCODER (Ed, locked): Omron EE-SX1131 SMD dual-channel transmissive photomicrosensor, U2 on the PCB BACK (KiCad v0.9 B.Cu),
20.20 below H2 (away from the dial axis), slot tangent. Datasheet sizes: body 5 (across the slot) x 4 (along) x 4 tall, slot
2.0 (+0.2/-0) wide x 2.8 deep, optical axis 1.0 from the open face, two 0.3 x 1.0 apertures 0.8 apart along the slot, pads
2 x 1 at +-2.5, pitch 1.4. [A]: terminal tabs drawn as 1.0 x 0.2 x 1.0 plates; apertures not modelled (axis marked).
The big gear gets a thin printed SLOTTED RIM on its PCB-side face: r 19.60–20.80 (1.2 thick [A], 0.4 each side in the 2.0 slot),
up to 0.6 [A] under the slot bottom; 119 windows [A] at pitch 1.0667 on r 20.20 (0.533 window / 0.533 bar, both > the 0.3
aperture): the 0.8 channel spacing = 3/4 pitch -> quadrature. 119 x 4 = 476 counts per gear (encoder shaft) turn; x 78/14 =
2652 counts per knob turn (119 is a multiple of 7, so the knob count is whole).
v0.5 notes: Encoder take-off v0.5 (2026-10-31). Supersedes v0.4. Knock-on of knob v0.7 (Ed: motor closer to the axis, driving a 32T
gear on the knob hub): motor offset 11.0 [K], skirt ID 38, bottom internal ring 90T -> 78T, so the three 14T pinions run at
r 16.0 = (78 - 14) x 0.5 / 2 (KiCad v0.9 H2). Brief: keep the encoder exactly 90° from the motor (H2 on the board centre line,
ENC_SET_ROT 0). With the motor at r 11, the idler at the strict +120° (30° from the motor) would sit 8.49 from the motor axis,
into the Ø12 body (needs 6.0 + 4.0 tip + 0.5 [A] = 10.5). Rather than rotate the whole set ~11°
(encoder at 79°, big gear 94T -> 81T), only that idler moves round to 41.0° [A] (minimum 40.73°); the other stays at 150°
(120° from the encoder). Spacing 131° / 109° / 120°: all gaps < 180°, so the three still locate the knob bottom [flagged].
Big gear re-derived on the centre line: 94T Ø48.0 (as v0.7). Pinions, pins, bearings and shaft unchanged.
v0.4 notes: Encoder take-off v0.4 (2026-10-31). Supersedes v0.3.
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
sys.path.insert(0, os.path.join(LIB, "encoder-takeoff/encoder-takeoff-v0.3")); sys.path.insert(0, os.path.join(LIB, "encoder-takeoff/encoder-takeoff-v0.4"))
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
_mx = K["motor_x"] - K["shaft_x"]                         # 11.0 [K] motor offset (v0.4 hard-coded 14.0)
p["idler_need"] = 6.0 + p["d_pin_tip"] / 2 + 0.5          # 10.5 motor axis to idler axis
_R = p["centre_dist"]
p["idler1_min"] = math.degrees(math.acos((_mx ** 2 + _R ** 2 - p["idler_need"] ** 2) / (2 * _mx * _R)))   # 40.73
p["idler_angs"] = [math.ceil(p["idler1_min"] * 2) / 2, p["enc_ang"] - 120.0]   # 41.0 [A], 150.0 (120° from the encoder)
p["spacing"] = [(p["idler_angs"][0] - p["enc_ang"]) % 360, (p["idler_angs"][1] - p["idler_angs"][0]) % 360, (p["enc_ang"] - p["idler_angs"][1]) % 360]
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
p["idler_motor_d"] = min(math.hypot(x - _mx, y) for x, y in map(idler_xy, p["idler_angs"]))   # 10.53
p["idler_motor_gap"] = p["idler_motor_d"] - 6.0 - p["d_pin_tip"] / 2                      # >= 0.5 [A]
A = (Align.CENTER, Align.CENTER, Align.MIN)

# ---- encoder sensor U2 (Omron EE-SX1131) + slotted rim on the big gear ----
import re as _re
def _u2_xy():
    t = open(os.path.join(LIB, "pcbs/knob-main-pcb/kicad/knob-main-pcb.kicad_pcb")).read()
    gx, gy = map(float, _re.search(r"\(grid_origin ([\d.\-]+) ([\d.\-]+)\)", t).group(1, 2))
    m = _re.search(r'\(footprint "footprints:Omron_EE-SX1131".*?\(layer "([BF])\.Cu"\).*?\(at ([\d.\-]+) ([\d.\-]+)', t, _re.S)
    return float(m.group(2)) - gx, float(m.group(3)) - gy, m.group(1)
_ux, _uy, _ul = _u2_xy()
assert _ul == "B", "U2 must be on B.Cu"
S = dict(body_x=5.0, body_y=4.0, body_h=4.0,        # datasheet: 5 across the slot, 4 along, 4 tall
         slot_w=2.0, slot_d=2.8, axis_from_open=1.0, ap_w=0.3, ap_h=1.0, ap_pitch=0.8,   # datasheet
         term_w=1.0, term_t=0.2, term_h=1.0, term_pitch=1.4)   # [A] tab envelope
p["sens_r"] = math.hypot(_ux - K["enc_x"], _uy - K["enc_y"])            # 20.20 [K]
p["n_win"] = 119; p["win_pitch"] = 0.8 / 0.75                           # [A] / quadrature
assert abs(p["sens_r"] - p["n_win"] * p["win_pitch"] / (2 * math.pi)) < 1e-4
p["rim_t"] = 1.2                                                        # [A] radial
p["rim_r0"], p["rim_r1"] = p["sens_r"] - p["rim_t"] / 2, p["sens_r"] + p["rim_t"] / 2
p["z_pcb_back"] = -p["pcb_t"]
p["z_sens_open"] = p["z_pcb_back"] - S["body_h"]                       # -5.51 open face of the slot
p["z_slot_bot"] = p["z_sens_open"] + S["slot_d"]                        # -2.71
p["z_axis"] = p["z_sens_open"] + S["axis_from_open"]                    # -4.51 optical axis
p["z_ap0"], p["z_ap1"] = p["z_axis"] - S["ap_h"] / 2, p["z_axis"] + S["ap_h"] / 2
p["rim_top"] = p["z_slot_bot"] - 0.6                                    # -3.31 [A]
p["gear_to_sensor"] = p["z_sens_open"] - p["h_big_top"]                 # 0.50
p["win_z0"], p["win_z1"] = p["z_ap0"] - 0.6, p["z_ap1"] + 0.3           # [A] window -5.61..-3.71
p["win_w"] = p["win_pitch"] / 2
p["counts_gear"] = 4 * p["n_win"]; p["counts_knob"] = p["counts_gear"] * p["z_ring"] / p["z_pinion"]
p["rim_in_slot"] = p["rim_top"] - p["z_sens_open"]
assert p["gear_to_sensor"] >= 0.5 - 1e-9 and p["win_z0"] > p["h_big_top"]
# stack behind the PCB and the shortest back panel
p["h_hub_bot"] = p["h_big_bot"] - p["big_hub_len"]
p["panel_gap_min"] = -(p["h_hub_bot"] - 0.5 - p["brg_ft"]) - p["pcb_t"]   # bearing-2 flange 0.5 [A] under the gear hub

def build_sensor():
    """EE-SX1131 in the ENCODER frame: base on the PCB back, slot opening away from the PCB, tangent (along X) at (0, -sens_r)."""
    bx, by, bh = S["body_y"], S["body_x"], S["body_h"]    # X = along the slot (tangent) 4, Y = across (radial) 5
    z0 = p["z_sens_open"]
    b = Pos(0, 0, z0) * Box(bx, by, bh, align=A)
    b -= Pos(0, 0, z0) * Box(bx, S["slot_w"], S["slot_d"], align=A)
    for sy in (-1, 1):
        for k in (-1, 0, 1):
            b += Pos(k * S["term_pitch"], sy * (by / 2 + S["term_t"] / 2), p["z_pcb_back"] - S["term_h"]) * Box(S["term_w"], S["term_t"], S["term_h"], align=A)
    return Pos(0, -p["sens_r"], 0) * b

def build_rim():
    h = p["rim_top"] - p["h_big_top"]
    r = Pos(0, 0, p["h_big_top"]) * (Cylinder(p["rim_r1"], h, align=A) - Cylinder(p["rim_r0"], h, align=A))
    cut = Box(p["win_w"], p["rim_t"] + 1.0, p["win_z1"] - p["win_z0"], align=A)
    wins = [Rot(0, 0, 360.0 * k / p["n_win"] - 90.0) * Pos(p["sens_r"], 0, p["win_z0"]) * cut for k in range(p["n_win"])]
    return r - Compound(children=wins)

def build_big_gear_rim():
    return e2.build_big_gear() + build_rim()

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
    d.pop("encoder big gear"); d["encoder big gear + slotted rim"] = build_big_gear_rim()
    d["encoder sensor EE-SX1131"] = build_sensor()
    return d

def idler_parts(p=P):
    """Idler pinions + pins in the DIAL frame (dial axis origin)."""
    out = {}
    for i, a in enumerate(p["idler_angs"], 1):
        x, y = idler_xy(a)
        out[f"idler pinion {i}"] = Pos(x, y, 0) * Rot(0, 0, phase(a)) * build_idler(p)
        out[f"idler pin {i}"] = Pos(x, y, 0) * build_pin(p)
    return out

FLAG_BIG = f"Big gear {P['z_big']}T Ø{P['d_big_tip']:.1f} (v0.4: 90T): H2 back on the board centre line ({K['enc_x'] - K['shaft_x']:.2f} off) [K]"
FLAG_SPACING = (f"Idlers NOT at 120°: {P['idler_angs'][0]:.1f}° (min {P['idler1_min']:.2f}° to clear the motor) and {P['idler_angs'][1]:.1f}°; gaps {P['spacing'][0]:.0f}/{P['spacing'][1]:.0f}/{P['spacing'][2]:.0f}° [check]", RED)
SENSOR = (f"Encoder U2 Omron EE-SX1131 [Ed] on the PCB back, {P['sens_r']:.2f} below H2; big-gear slotted rim r {P['rim_r0']:.2f}–{P['rim_r1']:.2f}, "
          f"{P['n_win']} windows, pitch {P['win_pitch']:.4f}: {P['counts_gear']} counts/gear turn, {P['counts_knob']:.0f}/knob turn (quadrature)")
FLAG_RIM = (f"Rim windows {P['win_w']:.2f} wide / bars {P['win_w']:.2f} in a {P['rim_t']:.1f} wall: resin (SLA/MSLA) print [A], FDM marginal [check]", RED)
FLAG_PIN = (f"Idler pins engage only {P['pin_engage']:.1f} in the cradle floor (option: NPTH in the PCB, not made) [check]", RED)
FLAG_BEHIND = ("Big gear BEHIND the PCB [A] (only 2 mm under the skirt); 4.5 under the PCB back, brass tube now flush [check]", RED)
SET = f"3 × 14T pinions in the {P['z_ring']}T ring at r {P['centre_dist']:.1f}: encoder {P['enc_ang']:.1f}° (90° from the motor), idlers {P['idler_angs'][0]:.1f}° and {P['idler_angs'][1]:.1f}° (motor 0°)"

if __name__ == "__main__":
    import itertools
    from sheet import Sheet
    e2.HERE = HERE
    print({k: (round(p[k], 3) if isinstance(p[k], float) else p[k]) for k in ("sens_r", "rim_r0", "rim_r1", "rim_top", "z_sens_open", "z_axis", "win_z0", "win_z1", "gear_to_sensor", "counts_gear", "counts_knob", "h_big_top", "h_big_bot", "h_hub_bot", "h_b2_top", "h_b2_bot", "h_panel", "panel_gap_min", "set_rot", "enc_ang", "idler1_min", "idler_angs", "spacing", "centre_dist", "z_ring", "idler_motor_d", "idler_motor_gap", "pocket_floor", "pin_len", "z_big", "d_big_tip")})
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
             SET, FLAG_SPACING, FLAG_PIN, "Printed PETG/POM [A] (or the encoder pinion part with a reamed bore)"]
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        sh.note("plan", sb[1] + 2, sb[3] - i * 0.42, l, 8 if i == 0 else 6.5, **kw)
    title = f"Idler pinion {p['z_pinion']}T + pin — v0.5, {T}"
    sub = [f"Two used, at {p['idler_angs'][0]:.0f}° and {p['idler_angs'][1]:.0f}° (motor 0°), in the {p['z_ring']}T bottom ring.", "[A] = assumed.", "Third-angle · mm · z-up: top view above, section A-A front"]
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
    e2.sheet(tog, "encoder-takeoff-together", "Encoder take-off v0.5 — together", f"{T}. 78T ring, H2 16.0 below the axis on the centre line; big gear re-derived.", 2.0,
          [("hdim", "front", -rb, rb, -rb, -rb - 4, f"Ø{p['d_big_tip']:.2f} big gear {p['z_big']}T"),
           ("vdim", "plan", p["h_b2_bot"], p["h_pin1"], -rb, -rb - 4, f"{p['shaft_len']:.2f} shaft"),
           ("vdim", "plan", p["h_panel"], 0, rb, rb + 30, f"{-p['h_panel']:.2f} PCB front to panel [A]")],
          ["Bearing 1 through the cradle floor into PCB H2 (dowel), as v0.3", SET, FLAG_SPACING, f"Idler nearest the motor: {p['idler_motor_d']:.2f} from the motor axis, {p['idler_motor_gap']:.2f} [A] tip to the Ø12 body",
           "Only the encoder pinion drives the big gear; idlers on fixed pins (sheet idler-pinion-pin)", FLAG_BIG, BRG + " × 2", *clines, FLAG_BEHIND], 3.0, gap=30,
          note_at=("plan", rb + 40, p["h_pin1"]), refs=refs)
    # ---- sensor part sheet (datasheet orientation: base z = 0, slot opening up, slot along Y) ----
    from sheet import Sheet as _Sheet
    sen = Rot(0, 0, 90) * Pos(0, p["sens_r"], -p["z_pcb_back"]) * build_sensor()
    sen = Rot(180, 0, 0) * sen; sen = Pos(0, 0, -sen.bounding_box().min.Z) * sen
    export_step(sen, os.path.join(HERE, "encoder-sensor-ee-sx1131.step"))
    sh = _Sheet(sen, gap=14, scale=9, label_pad=7)
    sh.set_front_section(b1.section_items({"EE-SX1131": sen}), "SECTION A-A (across the slot, through the optical axis)")
    H = S["body_h"]; X = S["body_x"] / 2; W = S["slot_w"] / 2
    sh.hdim("front", -X, X, 0, -1.4, f"{S['body_x']:.1f} body (datasheet)")
    sh.hdim("front", -W, W, H - S["slot_d"], H - S["slot_d"] + 0.6, f"{S['slot_w']:.1f} slot (+0.2/−0)")
    sh.vdim("front", 0, H, X, X + 0.9, f"{H:.1f} tall")
    sh.vdim("front", H - S["slot_d"], H, -X, -X - 0.8, f"{S['slot_d']:.1f} slot depth")
    sh.vdim("front", H - S["axis_from_open"], H, W, W + 0.5, f"{S['axis_from_open']:.1f} optical axis")
    sh.ref_line("front", -X - 0.3, H - S["axis_from_open"], X + 0.3, H - S["axis_from_open"], "")
    sh.vdim("plan", -S["body_y"] / 2, S["body_y"] / 2, X + 0.3, X + 1.0, f"{S['body_y']:.1f} along the slot")
    sb = sh.bb["plan"]; sh.cut_line("plan", sb[0] - 0.4, sb[1] + 0.4, 0, +1, "A")
    lines = ["Omron EE-SX1131 [Ed]: SMD transmissive photomicrosensor, dual channel (E1, E2), IR 940 nm; datasheet EE-SX1131_Ds.pdf",
             f"Body {S['body_x']:.0f} × {S['body_y']:.0f} × {S['body_h']:.0f}; slot {S['slot_w']:.1f} wide × {S['slot_d']:.1f} deep; optical axis {S['axis_from_open']:.1f} below the open face",
             f"Apertures {S['ap_w']:.1f} × {S['ap_h']:.1f}, two channels {S['ap_pitch']:.1f} apart along the slot (not modelled, axis marked)",
             "Pads (datasheet pattern): 6 × 2.0 × 1.0, columns 3.0 apart (inner edges), pitch 1.4; A, NC, K | C, E1, E2",
             ("Terminal tabs drawn as 1.0 × 0.2 × 1.0 plates [A]; tolerances ±0.15 (datasheet)", dict(color="#b06000")),
             f"Mounted: KiCad v0.9 U2 on B.Cu, slot opening away from the board, {p['sens_r']:.2f} from the encoder axis, slot tangent",
             SENSOR]
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        sh.note("plan", sb[1] + 1.6, sb[3] - i * 0.42, l, 8 if i == 0 else 6.5, **kw)
    title = "Encoder sensor Omron EE-SX1131 — v0.11, 2026-10-31"
    sub = ["Datasheet sizes; drawn base down, slot up (as the datasheet).", "[Ed] = Ed, [A] = assumed.", "Third-angle · mm · z-up: top view above, section A-A front"]
    sh.dxf(os.path.join(HERE, "encoder-sensor-ee-sx1131.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "encoder-sensor-ee-sx1131-drawing.png"), title, sub)
    # ---- big gear + slotted rim sheet (encoder frame, rim up = toward the PCB) ----
    g = build_big_gear_rim(); export_step(g, os.path.join(HERE, "encoder-big-gear-slotted-rim.step"))
    sh = _Sheet(g, gap=40, scale=2.4, label_pad=18)
    sh.set_front_section(b1.section_items({"big gear + rim": g}), "SECTION A-A (through the gear axis)")
    rb = p["d_big_tip"] / 2
    sh.hdim("front", -rb, rb, p["h_hub_bot"], p["h_hub_bot"] - 4, f"Ø{p['d_big_tip']:.1f} tip, {p['z_big']}T m{m:.1f}")
    sh.hdim("front", -p["rim_r1"], p["rim_r1"], p["h_hub_bot"], p["h_hub_bot"] - 9, f"Ø{2 * p['rim_r1']:.2f} rim OD")
    sh.hdim("front", -p["rim_r0"], p["rim_r0"], p["rim_top"], p["rim_top"] + 3, f"Ø{2 * p['rim_r0']:.2f} rim ID ({p['rim_t']:.1f} [A])")
    sh.vdim("front", p["h_big_top"], p["rim_top"], rb, rb + 4, f"{p['rim_top'] - p['h_big_top']:.1f} rim")
    sh.vdim("front", p["win_z0"], p["win_z1"], rb, rb + 10, f"{p['win_z1'] - p['win_z0']:.1f} windows [A]")
    sh.vdim("front", p["h_big_bot"], p["h_big_top"], -rb, -rb - 4, f"{p['big_face']:.1f} gear")
    sh.vdim("front", p["h_hub_bot"], p["h_big_bot"], -rb, -rb - 10, f"{p['big_hub_len']:.1f} hub")
    sb = sh.bb["plan"]; sh.cut_line("plan", sb[0] - 3, sb[1] + 3, 0, +1, "A")
    lines = [f"{p['z_big']}T m{m:.1f} big gear (Ø{p['d_big_tip']:.1f}, the largest on the 49 board), Ø{p['big_hub_d']:.0f} hub, Ø2 bore on the encoder shaft",
             f"Slotted rim [Ed] on the PCB-side face: r {p['rim_r0']:.2f}–{p['rim_r1']:.2f} ({p['rim_t']:.1f} [A], in the 2.0 sensor slot with {(2.0 - p['rim_t']) / 2:.1f} each side)",
             f"{p['n_win']} windows [A], pitch {p['win_pitch']:.4f} on r {p['sens_r']:.2f}: window {p['win_w']:.3f} / bar {p['win_w']:.3f} (> 0.3 aperture)",
             f"Channel spacing 0.8 = 3/4 pitch -> 90° quadrature; {p['counts_gear']} counts/gear turn, ×{p['z_ring']}/{p['z_pinion']} = {p['counts_knob']:.0f} per knob turn",
             f"Heights above the PCB front: gear {p['h_big_bot']:.2f}–{p['h_big_top']:.2f}, rim to {p['rim_top']:.2f} ({p['rim_in_slot']:.1f} into the slot, 0.6 [A] to its bottom), windows {p['win_z0']:.2f}–{p['win_z1']:.2f}",
             f"Optical axis {p['z_axis']:.2f}, apertures {p['z_ap0']:.2f}–{p['z_ap1']:.2f}: inside the windows",
             FLAG_RIM, "Printed one piece [A]"]
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        sh.note("plan", sb[1] + 12, sb[3] - i * 2.4, l, 8 if i == 0 else 6.5, **kw)
    title = f"Big gear {p['z_big']}T + slotted rim — v0.11"
    sub = [f"{p['n_win']}-window rim through the EE-SX1131 slot; rim up = toward the PCB.", "[Ed] = Ed, [A] = assumed.", "Third-angle · mm · z-up: top view above, section A-A front"]
    sh.dxf(os.path.join(HERE, "encoder-big-gear-slotted-rim.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "encoder-big-gear-slotted-rim-drawing.png"), title, sub)
