"""Base cradle v0.4 (2026-10-31). Supersedes v0.3. Ed: "I didn't intend it to be so thick, only 3 or 4 mm thick."
Now a 3.5 [A] plate on the PCB front (was the solid 36.0 fill), with short bonded collars only where support is needed:
  tube collar on the brass tube up to 8.0 (8.0 bonded length >= 6 [A]; 4.5 above the plate),
  motor collar round the Ø12 motor up to 12.0 [A] (12.0 bonded, 8.5 above the plate, ~60 % of the 20 can [M]),
  encoder bearing seat: Ø5.0 press bore through the 1.0 [A] floor under a Ø9.0 pinion pocket, bearing on into PCB H2 (dowel).
Same outline Ø43.0 (0.5 [A] inside the skirt ID / 90T tips), printed CF-ASA or PETG [A], bonded to the PCB FRONT.
Frame: dial axis = Z, Z = height above the PCB front; motor at +X, encoder H2 at -Y."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(LIB, "base-cradle/base-cradle-v0.3"))
sys.path.insert(0, os.path.join(LIB, "encoder-takeoff/encoder-takeoff-v0.4"))
import base_cradle_v03 as c3
import encoder_takeoff_v04 as e4
from base_cradle_v03 import KP, b1
EP = e4.P
P = dict(c3.P); p = P
p.update(plate_t=3.5,          # [A] Ed: 3-4
         tube_collar_wall=2.0,  # [A]
         motor_collar_wall=1.4, # [A] outer edge 0.5 inside the skirt ID
         motor_collar_top=12.0, # [A]
         pad_cb_d=7.0, pad_cb_h=0.6)   # [A] counterbore over the tube solder ring Ø6.4 (fillet room)
p["enc_x"], p["enc_y"] = e4.enc_xy()                                  # (0.99, -18.97): set rotated 3.0° [A] (KiCad v0.7)
p["idlers"] = [e4.idler_xy(a) for a in EP["idler_angs"]]             # 33° and 153° from the motor
p["idler_floor"] = EP["pocket_floor"]                                  # 1.70 under the idler hubs
p["idler_pocket_top"] = EP["h_pin1"] + p["clear"]                      # 5.30 (cut through the motor collar locally)
p["pin_hole_d"] = EP["pin_d"]                                          # 2.0 bonded [A]
p["tube_collar_od"] = p["bore_d"] + 2 * p["tube_collar_wall"]          # 9.20
p["motor_collar_od"] = p["motor_bore_d"] + 2 * p["motor_collar_wall"]  # 15.00
p["motor_collar_r_out"] = p["motor_x"] + p["motor_collar_od"] / 2      # 21.50
p["motor_collar_to_tube"] = (p["motor_x"] - p["motor_collar_od"] / 2) - p["tube_collar_od"] / 2
assert p["motor_collar_r_out"] <= p["r_out"] + 1e-9
A = (Align.CENTER, Align.CENTER, Align.MIN)

def build_cradle(p=P):
    c = Cylinder(p["r_out"], p["plate_t"], align=A)
    c += Cylinder(p["tube_collar_od"] / 2, p["boss_top"], align=A)
    c += Pos(p["motor_x"], 0, 0) * Cylinder(p["motor_collar_od"] / 2, p["motor_collar_top"], align=A)
    ex, ey = p["enc_x"], p["enc_y"]
    c += Pos(ex, ey, 0) * Cylinder(p["dowel_pad_d"] / 2, p["floor"], align=A)
    c -= Cylinder(p["bore_d"] / 2, p["boss_top"], align=A)
    c -= Cylinder(p["pad_cb_d"] / 2, p["pad_cb_h"], align=A)   # tube is soldered on the PCB ring under here
    c -= Pos(p["motor_x"], 0, 0) * Cylinder(p["motor_bore_d"] / 2, p["motor_collar_top"], align=A)
    c -= Pos(ex, ey, p["floor"]) * Cylinder(p["enc_pocket_d"] / 2, p["plate_t"], align=A)
    c -= Pos(ex, ey, 0) * Cylinder(p["brg_bore_d"] / 2, p["floor"], align=A)
    for x, y in p["idlers"]:
        c -= Pos(x, y, p["idler_floor"]) * Cylinder(p["enc_pocket_d"] / 2, p["idler_pocket_top"] - p["idler_floor"], align=A)
        c -= Pos(x, y, 0) * Cylinder(p["pin_hole_d"] / 2, p["idler_floor"], align=A)
    return c

if __name__ == "__main__":
    from sheet import Sheet
    c = build_cradle(); export_step(c, os.path.join(HERE, "base-cradle.step"))
    ro, mx = p["r_out"], p["motor_x"]
    sh = Sheet(c, gap=36, scale=2.0, label_pad=26)
    sh.set_front_section(b1.section_items({"cradle": c}), "SECTION A-A (through dial and motor axes)")
    sh.hdim("front", -ro, ro, p["motor_collar_top"], p["motor_collar_top"] + 9, f"Ø{2 * ro:.1f} plate = skirt ID {KP['skirt_id']:.0f} − 2×{p['clear']:.1f} [A]")
    sh.hdim("front", mx - p["motor_collar_od"] / 2, mx + p["motor_collar_od"] / 2, p["motor_collar_top"], p["motor_collar_top"] + 4, f"Ø{p['motor_collar_od']:.1f} motor collar")
    sh.hdim("front", -p["tube_collar_od"] / 2, p["tube_collar_od"] / 2, p["boss_top"], p["boss_top"] + 3, f"Ø{p['tube_collar_od']:.1f} tube collar")
    sh.hdim("front", mx - p["motor_bore_d"] / 2, mx + p["motor_bore_d"] / 2, 0, -4, f"Ø{p['motor_bore_d']:.1f} motor bore (bond)")
    sh.hdim("front", -p["bore_d"] / 2, p["bore_d"] / 2, 0, -8, f"Ø{p['bore_d']:.1f} tube bore (bond)")
    sh.vdim("front", 0, p["plate_t"], -ro, -ro - 4, f"{p['plate_t']:.1f} plate [A]")
    sh.vdim("front", 0, p["boss_top"], -ro, -ro - 9, f"{p['boss_top']:.1f} tube collar")
    sh.vdim("front", 0, p["motor_collar_top"], ro, ro + 8, f"{p['motor_collar_top']:.1f} motor collar [A]")
    sh.vdim("side", 0, p["floor"], p["enc_y"] - p["enc_pocket_d"] / 2, -ro - 6, f"{p['floor']:.1f} floor [A]")
    sh.hdim("plan", p["enc_x"] - p["enc_pocket_d"] / 2, p["enc_x"] + p["enc_pocket_d"] / 2, p["enc_y"], p["enc_y"] + 8, f"Ø{p['enc_pocket_d']:.1f} pocket, Ø{p['brg_bore_d']:.1f} bearing bore")
    sh.hdim("plan", 0, mx, 0, 12, f"{mx:.1f} motor offset [K]")
    sh.vdim("plan", p["enc_y"], 0, -ro, -ro - 4, f"{-p['enc_y']:.2f} H2 [K]")
    sb = sh.bb["plan"]; sh.cut_line("plan", sb[0] - 3, sb[1] + 3, 0, +1, "A")
    lines = ["Printed CF-ASA or PETG [A], bonded to the PCB FRONT; nothing on the PCB back",
             f"Plate {p['plate_t']:.1f} [A] (Ed: 3–4; v0.3 was a solid {c3.P['top']:.0f} fill), Ø{2 * ro:.1f}: {p['clear']:.1f} [A] inside the skirt ID / 90T tips",
             f"Tube collar Ø{p['tube_collar_od']:.1f} to {p['boss_top']:.1f}: Ø{p['bore_d']:.1f} bonded bore, {p['boss_top'] - p['pad_cb_h']:.1f} bonded (>= 6 [A]), {p['boss_top'] - p['plate_t']:.1f} above the plate",
             f"Tube SOLDERED on the PCB ring (GND, Ø3.4–Ø6.4): Ø{p['pad_cb_d']:.1f} × {p['pad_cb_h']:.1f} [A] counterbore over the pad and fillet",
             f"Motor collar Ø{p['motor_collar_od']:.1f} ({p['motor_collar_wall']:.1f} wall [A]) to {p['motor_collar_top']:.1f}: Ø{p['motor_bore_d']:.1f} bonded bore, {p['motor_collar_top'] - p['plate_t']:.1f} above the plate",
             f"Motor collar outer edge r {p['motor_collar_r_out']:.1f} = plate edge; {p['motor_collar_to_tube']:.2f} from the tube collar",
             f"Motor tab pads inside the motor bore, {p['pad_margin']:.2f} from its wall [K]",
             f"Encoder F682ZZ pressed through the {p['floor']:.1f} [A] floor (Ø{p['brg_bore_d']:.1f}) into PCB H2: locating dowel with the tube in H1",
             f"Ø{p['enc_pocket_d']:.1f} pinion pocket through the plate; Ø{p['dowel_pad_d']:.1f} floor pad round the bearing, {p['floor_to_skirt']:.1f} under the skirt",
             e4.SET, f"Idler pockets Ø{p['enc_pocket_d']:.1f} above a {p['idler_floor']:.1f} floor, Ø{p['pin_hole_d']:.1f} bonded pin holes; pockets notch the motor collar to {p['idler_pocket_top']:.1f}",
             e4.FLAG_PIN,
             "Dial tubes and the reserved bearing zone (8.0–13.0 [A]) sit above the tube collar",
             "KiCad v0.8: H2 rotated 3.0° [A]; H1 = tube solder ring + M1.6 rod NPTH Ø1.8 (tube no longer through the PCB)"]
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        sh.note("plan", sb[1] + 14, sb[3] - i * 2.6, l, 8 if i == 0 else 6.5, **kw)
    title = "Base cradle — v0.4, 2026-10-31"
    sub = ["3.5 plate on the PCB front with short tube and motor collars.", "[K] = KiCad, [M] = motor, [A] = assumed.",
           "Third-angle · mm · z-up: top view above, section A-A front"]
    sh.dxf(os.path.join(HERE, "base-cradle.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "base-cradle-drawing.png"), title, sub)
    print({k: round(p[k], 3) for k in ("plate_t", "tube_collar_od", "boss_top", "motor_collar_od", "motor_collar_top", "motor_collar_to_tube")}, round(c.volume))
