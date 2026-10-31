"""Base cradle v0.3 (2026-10-31). Supersedes the printed shaft flange (shaft v0.1/v0.2 flange, bonded to the PCB BACK).
Ed: move the piece supporting the brass rod to the TOP of the PCB so it encompasses the motor, supports it, and uses all the
volume inside the knob diameter; it can be slightly thinner. Nothing is glued to the PCB back any more.
Printed CF-ASA or PETG [A], bonded to the PCB FRONT. It grips the brass tube in a bonded bore (8.0 long [A], >= 6) and cradles the
Ø12 motor in a bondable close-fit bore, and fills the space inside the big-knob skirt with these clearances (>= 0.5 [A]):
skirt ID and 90T ring tips, the dial tubes on the axis (they stop above a 5.0 [A] zone over the tube boss reserved for future bearing), motor pinion / 68T ring (above
the cradle top), and the encoder pinion (pocket). Encoder bearing 1 (F682ZZ) presses through the cradle's 1.0 [A] floor under
the pinion into the PCB H2 hole, so it locates the cradle while gluing (with the brass tube in H1). The motor tab pads lie inside the motor bore.
Frame: dial axis = Z, Z = height above the PCB front; the motor at +X (offset), the encoder H2 at -Y (19 below the dial axis).
Tags: [K] KiCad, [M] motor params, [A] assumed."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "pcbs/knob-main-pcb", "motors/1220-coreless-planetary", "knob/knob-v0.1", "knob/knob-v0.2", "knob/knob-v0.4",
          "encoder-takeoff/encoder-takeoff-v0.2", "encoder-takeoff/encoder-takeoff-v0.3", "control-dial/control-dial-v0.1"):
    sys.path.insert(0, os.path.join(LIB, d))
import knob_main_pcb as pcb
import motor_gearbox as mg
import knob_v04 as k4
import encoder_takeoff_v03 as enc
import bezel as b1

K = pcb.kicad_facts(); M = mg.VARIANTS["motor-1220"]; KP = k4.P; EP = enc.P
P = dict(
    clear=0.5,                 # [A] to every moving part
    plate_t=3.0,               # [A] base plate (was the 4.0 back flange) [Ed: slightly thinner]
    tube_d=5.0, glue_gap=0.1,  # brass tube; [A] per side
    boss_top=KP["cradle_boss_top"],   # 8.0 [A] bonded length on the tube
    motor_d=M["body_d"], motor_glue=0.1,   # [M] Ø12; [A] per side
    top=36.0,                  # [A] cradle top: 2.0 below the motor front (38.0) [M]; pinion and 68T ring above
    pad_clear_min=0.5,         # [A]
)
p = P
p["r_out"] = KP["skirt_id"] / 2 - p["clear"]                      # 21.50 (skirt ID r 22.0 = 90T tip r 22.0)
p["bore_d"] = p["tube_d"] + 2 * p["glue_gap"]                     # 5.20 bonded
p["axis_clear_d"] = KP["knob_tube_od"] + 2 * p["clear"]           # 12.24 round the big-knob tube above the boss
p["motor_bore_d"] = p["motor_d"] + 2 * p["motor_glue"]            # 12.20
p["motor_x"] = K["motor_x"] - K["shaft_x"]; p["enc_y"] = -(K["enc_y"] - K["shaft_y"])   # +14.0, -19.0 [K]
p["enc_pocket_d"] = EP["d_pin_tip"] + 2 * p["clear"]              # 9.0 round the 14T pinion (and the Ø6.1 bearing flange)
p["floor"] = EP["cradle_floor"]                                   # 1.0 [A] floor under the pinion; bearing flange on its top
p["brg_bore_d"] = EP["brg_D"]                                     # 5.0 [A] press, same as the PCB H2 [K]
p["dowel_pad_d"] = p["enc_pocket_d"]                              # [A] floor pad round the bearing where it pokes past the OD
p["pad_wall"] = (p["dowel_pad_d"] - p["brg_bore_d"]) / 2           # 2.0
p["floor_to_skirt"] = KP["h_skirt0"] - p["floor"]                 # 1.0 under the skirt / 90T ring
p["enc_pocket_h"] = EP["h_pin1"] + p["clear"]                     # 5.30
p["wall_motor_out"] = p["r_out"] - (p["motor_x"] + p["motor_bore_d"] / 2)   # outer wall beside the motor
p["wall_axis_motor"] = (p["motor_x"] - p["motor_bore_d"] / 2) - p["axis_clear_d"] / 2
# motor solder pads [K]: inside the motor bore?
pads = [(x - K["shaft_x"], y - K["shaft_y"], w, h) for x, y, w, h in K["motor_pads"]]
def pad_margin():
    import math
    rb = p["motor_bore_d"] / 2; worst = 1e9
    for x, y, w, h in pads:
        for cx in (x - w / 2, x + w / 2):
            for cy in (y - h / 2, y + h / 2):
                worst = min(worst, rb - math.hypot(cx - p["motor_x"], cy))
    return worst
p["pad_margin"] = pad_margin()
assert p["pad_margin"] >= p["pad_clear_min"], p["pad_margin"]
A = (Align.CENTER, Align.CENTER, Align.MIN)

def build_cradle(p=P):
    c = Cylinder(p["r_out"], p["top"], align=A)
    c -= Cylinder(p["bore_d"] / 2, p["top"], align=A)                                         # bonded bore on the tube
    c -= Pos(0, 0, p["boss_top"]) * Cylinder(p["axis_clear_d"] / 2, p["top"] - p["boss_top"], align=A)   # dial tubes
    c -= Pos(p["motor_x"], 0, 0) * Cylinder(p["motor_bore_d"] / 2, p["top"], align=A)        # motor (pads inside)
    c += Pos(0, p["enc_y"], 0) * Cylinder(p["dowel_pad_d"] / 2, p["floor"], align=A)           # floor pad (below the skirt)
    c -= Pos(0, p["enc_y"], p["floor"]) * Cylinder(p["enc_pocket_d"] / 2, p["enc_pocket_h"] - p["floor"], align=A)  # pinion pocket
    c -= Pos(0, p["enc_y"], 0) * Cylinder(p["brg_bore_d"] / 2, p["floor"], align=A)            # bearing 1 press bore (dowel)
    return c

FLAG_TUBES = k4.FLAG_TUBES
if __name__ == "__main__":
    from sheet import Sheet
    c = build_cradle(); export_step(c, os.path.join(HERE, "base-cradle.step"))
    ro = p["r_out"]
    sh = Sheet(c, gap=36, scale=2.0, label_pad=30)
    sh.set_front_section(b1.section_items({"cradle": c}), "SECTION A-A (through dial and motor axes)")
    sh.hdim("front", -ro, ro, p["top"], p["top"] + 9, f"Ø{2 * ro:.1f} OD = skirt ID {KP['skirt_id']:.0f} − 2×{p['clear']:.1f} [A]")
    sh.hdim("front", -p["axis_clear_d"] / 2, p["axis_clear_d"] / 2, p["top"], p["top"] + 4, f"Ø{p['axis_clear_d']:.2f} clear of the dial tubes")
    sh.hdim("front", p["motor_x"] - p["motor_bore_d"] / 2, p["motor_x"] + p["motor_bore_d"] / 2, 0, -4, f"Ø{p['motor_bore_d']:.1f} motor bore (bond)")
    sh.hdim("front", -p["bore_d"] / 2, p["bore_d"] / 2, 0, -8, f"Ø{p['bore_d']:.1f} tube bore (bond)")
    sh.hdim("plan", 0, p["motor_x"], 0, 10, f"{p['motor_x']:.1f} motor offset [K]")
    sh.vdim("front", 0, p["top"], -ro, -ro - 4, f"{p['top']:.1f} cradle height [A]")
    sh.vdim("front", 0, p["boss_top"], -ro, -ro - 10, f"{p['boss_top']:.1f} bonded on tube [A]")
    sh.vdim("side", 0, p["enc_pocket_h"], p["enc_y"] - p["enc_pocket_d"] / 2, -ro - 4, f"{p['enc_pocket_h']:.1f} encoder pocket")
    sh.vdim("side", 0, p["floor"], p["enc_y"] - p["enc_pocket_d"] / 2, -ro - 12, f"{p['floor']:.1f} floor [A]")
    sh.hdim("plan", p["enc_y"] * 0 - p["enc_pocket_d"] / 2, p["enc_pocket_d"] / 2, p["enc_y"], p["enc_y"] + 8, f"Ø{p['enc_pocket_d']:.1f} pocket, Ø{p['brg_bore_d']:.1f} bearing bore")
    sh.vdim("plan", p["enc_y"], 0, -ro, -ro - 4, f"{-p['enc_y']:.1f} H2 [K]")
    sb = sh.bb["plan"]; sh.cut_line("plan", sb[0] - 3, sb[1] + 3, 0, +1, "A")
    RED = dict(color="red", weight="bold")
    lines = ["Printed CF-ASA or PETG [A], bonded to the PCB FRONT; replaces the back flange (nothing on the PCB back now)",
             f"Grips the brass tube: Ø{p['bore_d']:.1f} bonded bore, {p['boss_top']:.1f} long [A] (>= 6)",
             f"Cradles the Ø{p['motor_d']:.0f} motor: Ø{p['motor_bore_d']:.1f} bonded bore up to {p['top']:.1f} ({p['top'] - 38.0:+.1f} to the motor front)",
             f"Encoder F682ZZ pressed through the {p['floor']:.1f} [A] floor (Ø{p['brg_bore_d']:.1f}) into PCB H2: locating dowel with the tube in H1",
             f"Floor pad Ø{p['dowel_pad_d']:.1f} round the bearing ({p['pad_wall']:.1f} wall), {p['floor_to_skirt']:.1f} under the skirt / 90T ring",
             f"Motor tab pads inside the motor bore, {p['pad_margin']:.2f} from its wall [K]",
             f"Clearances {p['clear']:.1f} [A]: skirt ID / 90T tips (OD Ø{2 * ro:.1f}), dial tubes / future bearing (Ø{p['axis_clear_d']:.2f} above {p['boss_top']:.1f}), encoder pinion/bearing pocket",
             f"Pinion and 68T ring stay above the {p['top']:.1f} top; walls: {p['wall_axis_motor']:.2f} axis-to-motor, {p['wall_motor_out']:.2f} motor-to-OD",
             f"Base plate {p['plate_t']:.1f} [A] merges into the solid fill (Ed: use the volume in the skirt); sparse infill [A]",
             "KiCad v0.6: H2 back on the front side, holes unchanged (H1 Ø5.2, M1 slots, H2 Ø5.0); cradle fits inside the 49 board",
             FLAG_TUBES]
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        sh.note("plan", sb[1] + 14, sb[3] - i * 2.6, l, 8 if i == 0 else 6.5, **kw)
    title = "Base cradle — v0.3 (was the shaft flange), 2026-10-31"
    sub = ["On the PCB front: holds the brass tube, cradles the motor, fills the skirt.", "[K] = KiCad, [M] = motor, [A] = assumed.",
           "Third-angle · mm · z-up: top view above, section A-A front"]
    sh.dxf(os.path.join(HERE, "base-cradle.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "base-cradle-drawing.png"), title, sub)
    print({k: round(v, 3) for k, v in p.items() if isinstance(v, float)})
