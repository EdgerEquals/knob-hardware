"""Footprint generator, PCB v0.10 (knob CAD v0.16, 2026-11-01). Plain-text KiCad 9 .kicad_mod into footprints.pretty.
Sources: [S] datasheet land patterns, [A] assumed, [CAD] from cad_constraints.json (the parametric model).
  X2SON-4_TMAG5253      TI DMR0004A: body 1.1 x 1.4, 4 x 0.22 x 0.4 pads at 0.5 pitch (centres x +-0.25, y +-0.7), EP 0.8 x 0.6 [S].
                        Pin 1 VCC, 2 GND, 3 EN, 4 OUT, 5 EP (NC / GND) [S]. Local x = 1.1 side (placed radial, as in the CAD).
  SOT-23-6_TMAG5273_Tight   TI DBV, pins 1 SCL 2 GND 3 GND(TEST) 4 VCC 5 INT 6 SDA [S]; pads 1.0 x 0.6 at x +-1.15 (lead span radial,
                        CAD hv_mid.lead_w); courtyard trimmed to +-1.75 so it fits the 2.5 Hall-row pitch.
  WSON-8_2x2_DRV8837    TI DSG0008A: 8 x 0.25 x 0.5 at 0.5 pitch, centres x +-0.95, EP 0.9 x 1.6 (pin 9) [S].
  C_0603                generic 0603.
  Motor_1220_Tabs_Relief    Motor_1220_Tabs + Ø3.2 NPTH relief on the motor axis for the 1220 rear boss Ø3 x 0.6 (closes the PCB/motor clash).
  FeelMotor_716_LeadPads    two plated Ø1.0 lead holes in 1.8 x 1.8 pads (mask open on the back only), built as a TOP footprint and placed FLIPPED (pads on B.Cu).
                        No F courtyard: the 716 stands in the cradle pocket on the cradle floor, not on the PCB.
  TubeRodClamp_Main_M1.6_v016   F.Cu GND tube ring Ø3.4-6.4 (unchanged) + B.Cu VBUS_DATA rod-nut pad Ø1.8 -> Ø(2*rod_pad_r) [CAD], no washer.
  Pads_2x14_P2.00_SMD   J10 placeholder: MCU / backplane link test pads (no connector chosen yet) [A].
  PinSocket_2x03_P2.54_Vertical_8.5mm   J2: joystick daughterboard socket (riser), pads mirror the daughterboard J1.
  TopScreenJoystick_Stack_v016   MH1: joystick v0.1 spring holes, base pin holes, FPC slot, Fab outlines (docs/top-screen-joystick.md)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "footprints.pretty")
C = json.load(open(os.path.join(HERE, "cad_constraints.json")))
GEN = '(generator "make_v016_footprints.py")'

def head(name, descr, attr="smd", ref="REF**", ref_y=-1.5, val_y=1.5):
    return [f'(footprint "{name}"', f'  (version 20241229) {GEN}', '  (layer "F.Cu")', f'  (descr "{descr}")', f'  (attr {attr})',
            f'  (property "Reference" "{ref}" (at 0 {ref_y:.2f} 0) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))',
            f'  (property "Value" "{name}" (at 0 {val_y:.2f} 0) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))']
def rect(x0, y0, x1, y1, layer, w=0.05):
    return f'  (fp_rect (start {x0:.3f} {y0:.3f}) (end {x1:.3f} {y1:.3f}) (stroke (width {w}) (type solid)) (fill no) (layer "{layer}"))'
def circ(x, y, r, layer, w=0.05):
    return f'  (fp_circle (center {x:.3f} {y:.3f}) (end {x + r:.3f} {y:.3f}) (stroke (width {w}) (type solid)) (fill no) (layer "{layer}"))'
def line(x0, y0, x1, y1, layer, w=0.1):
    return f'  (fp_line (start {x0:.3f} {y0:.3f}) (end {x1:.3f} {y1:.3f}) (stroke (width {w}) (type solid)) (layer "{layer}"))'
def text(s, x, y, layer, size=0.5):
    return f'  (fp_text user "{s}" (at {x:.3f} {y:.3f} 0) (layer "{layer}") (effects (font (size {size} {size}) (thickness {size * 0.15:.3f}))))'
def smd(n, x, y, w, h, side="F", shape="roundrect", paste=True):
    L = f'"{side}.Cu" "{side}.Mask"' + (f' "{side}.Paste"' if paste else "")
    rr = " (roundrect_rratio 0.2)" if shape == "roundrect" else ""
    return f'  (pad "{n}" smd {shape} (at {x:.4f} {y:.4f}) (size {w:.3f} {h:.3f}) (layers {L}){rr})'
def npth(x, y, d, shape="circle", w=None, h=None):
    if shape == "oval":
        return f'  (pad "" np_thru_hole oval (at {x:.3f} {y:.3f}) (size {w:.3f} {h:.3f}) (drill oval {w:.3f} {h:.3f}) (layers "*.Cu" "*.Mask"))'
    return f'  (pad "" np_thru_hole circle (at {x:.3f} {y:.3f}) (size {d:.3f} {d:.3f}) (drill {d:.3f}) (layers "*.Cu" "*.Mask"))'
def pth(n, x, y, d, pad, shape="circle"):
    return f'  (pad "{n}" thru_hole {shape} (at {x:.3f} {y:.3f}) (size {pad:.3f} {pad:.3f}) (drill {d:.3f}) (layers "*.Cu" "*.Mask"))'
def write(name, L):
    L.append(")"); open(os.path.join(OUT, name + ".kicad_mod"), "w").write("\n".join(L) + "\n"); print("wrote", name)

# ---- TMAG5253 X2SON-4 (DMR) ----
L = head("X2SON-4_TMAG5253", "TI TMAG5253 linear Hall, X2SON-4 DMR0004A; 1 VCC 2 GND 3 EN 4 OUT 5 EP(GND); local x = 1.1 side (radial)", ref_y=-1.3, val_y=1.3)
L += [rect(-0.55, -0.7, 0.55, 0.7, "F.Fab", 0.05), circ(-0.35, -0.85, 0.05, "F.Fab", 0.05), rect(-0.6, -1.0, 0.6, 1.0, "F.CrtYd"),
      smd("1", -0.25, -0.7, 0.22, 0.4), smd("4", 0.25, -0.7, 0.22, 0.4), smd("2", -0.25, 0.7, 0.22, 0.4), smd("3", 0.25, 0.7, 0.22, 0.4),
      smd("5", 0, 0, 0.8, 0.6)]
write("X2SON-4_TMAG5253", L)
# ---- TMAG5273 SOT-23-6 tight ----
L = head("SOT-23-6_TMAG5273_Tight", "TI TMAG5273 3D Hall SOT-23-6 DBV; 1 SCL 2 GND 3 GND(TEST) 4 VCC 5 INT 6 SDA; courtyard trimmed for the 2.5 Hall pitch", ref_y=-1.9, val_y=1.9)
L += [rect(-0.8, -1.45, 0.8, 1.45, "F.Fab", 0.05), circ(-0.5, -1.15, 0.1, "F.Fab", 0.05), rect(-1.75, -1.55, 1.75, 1.55, "F.CrtYd")]
for n, (x, y) in {"1": (-1.15, -0.95), "2": (-1.15, 0), "3": (-1.15, 0.95), "4": (1.15, 0.95), "5": (1.15, 0), "6": (1.15, -0.95)}.items():
    L.append(smd(n, x, y, 1.0, 0.6))
write("SOT-23-6_TMAG5273_Tight", L)
# ---- DRV8837 WSON-8 2x2 (DSG) ----
L = head("WSON-8_2x2_DRV8837", "TI DRV8837 H-bridge WSON-8 DSG0008A; 1 VM 2 OUT1 3 OUT2 4 GND 5 IN2 6 IN1 7 nSLEEP 8 VCC 9 EP(GND)", ref_y=-1.6, val_y=1.6)
L += [rect(-1.0, -1.0, 1.0, 1.0, "F.Fab", 0.05), circ(-0.7, -0.7, 0.1, "F.Fab", 0.05), rect(-1.45, -1.25, 1.45, 1.25, "F.CrtYd")]
for i in range(4):
    L.append(smd(str(i + 1), -0.95, -0.75 + 0.5 * i, 0.5, 0.25)); L.append(smd(str(8 - i), 0.95, -0.75 + 0.5 * i, 0.5, 0.25))
L.append(smd("9", 0, 0, 0.9, 1.6))
write("WSON-8_2x2_DRV8837", L)
# ---- C_0603 ----
L = head("C_0603", "0603 capacitor", ref_y=-1.2, val_y=1.2)
L += [rect(-0.8, -0.4, 0.8, 0.4, "F.Fab", 0.05), rect(-1.5, -0.75, 1.5, 0.75, "F.CrtYd"), smd("1", -0.775, 0, 0.9, 0.95), smd("2", 0.775, 0, 0.9, 0.95)]
write("C_0603", L)
# ---- 1220 tabs + relief ----
M = C["motor"]; sw, sl = M["term_t"] + 0.4, M["term_w"] + 0.4; pw, pl = sw + 0.8, sl + 0.8; p = M["term_pitch"]; r = M["body_d"] / 2
relief = 3.2
L = head("Motor_1220_Tabs_Relief", f"1220 coreless planetary: 2 rear solder tabs (plated slots {sw:.2f}x{sl:.2f}, pitch {p:.1f}) + NPTH Ø{relief} relief for the Ø{M['rear_boss_d']} x {M['rear_boss_len']} rear boss; body Ø{M['body_d']} on F.Fab",
         attr="through_hole", ref_y=-(r + 1.0), val_y=r + 1.0)
L += [circ(0, 0, r, "F.Fab", 0.1), circ(0, 0, r + 0.15, "F.CrtYd"), npth(0, 0, relief)]
for i, x in enumerate((-p / 2, p / 2)):
    L.append(f'  (pad "{i + 1}" thru_hole oval (at {x:.3f} 0) (size {pw:.3f} {pl:.3f}) (drill oval {sw:.3f} {sl:.3f}) (layers "*.Cu" "*.Mask"))')
write("Motor_1220_Tabs_Relief", L)
# ---- 716 lead pads (placed flipped) ----
F = C["feel"]; pp = F["pad_pitch"] / 2
L = head("FeelMotor_716_LeadPads", f"716 feel motor lead pads: 2 x plated Ø{F['pad_hole']} lead holes in {F['pad'][0]}x{F['pad'][1]} pads (mask open on the solder side only), pitch {F['pad_pitch']}. Place FLIPPED (pads on B.Cu); the can stands on the cradle floor (Fab circle only).",
         ref_y=-1.8, val_y=1.8)
L += [rect(-pp - 1.1, -1.1, pp + 1.1, 1.1, "F.CrtYd"), circ(0, 0, F["can_d"] / 2, "F.Fab", 0.05)]
for i, x in enumerate((-pp, pp)):
    L.append(f'  (pad "{i + 1}" thru_hole roundrect (at {x:.3f} 0) (size {F["pad"][0]:.3f} {F["pad"][1]:.3f}) (drill {F["pad_hole"]:.3f}) (layers "*.Cu" "F.Mask") (roundrect_rratio 0.15))')
write("FeelMotor_716_LeadPads", L)
# ---- tube / rod clamp with the v0.16 rod pad ----
rp = round(C["rod_pad_r"], 3); hole = C["h1_hole"]
def ring(num, r_in, r_out, side, paste=False):
    mid, w = (r_in + r_out) / 2, r_out - r_in
    Ls = f'"{side}.Cu" "{side}.Mask"' + (f' "{side}.Paste"' if paste else "")
    return (f'  (pad "{num}" smd custom (at {mid:.3f} 0) (size {w:.3f} {w:.3f}) (layers {Ls})\n'
            f'    (options (clearance outline) (anchor circle))\n'
            f'    (primitives (gr_circle (center {-mid:.3f} 0) (end 0 0) (width {w:.3f}) (fill no))))')
L = head("TubeRodClamp_Main_M1.6_v016", f"Brass tube 5x3 solder ring (F.Cu, GND, Ø3.4-6.4) + M1.6 rod-nut pad (B.Cu, VBUS_DATA, Ø{hole + 0.6:.1f}-Ø{2 * rp:.2f}, no washer, CAD v0.16 rod_pad_r), NPTH Ø{hole}",
         ref_y=-3.8, val_y=3.8)
L += [circ(0, 0, 3.45, "F.CrtYd"), circ(0, 0, rp + 0.1, "B.CrtYd"), npth(0, 0, hole), ring("1", 1.7, 3.2, "F", True), ring("2", hole / 2 + 0.3, rp, "B")]
write("TubeRodClamp_Main_M1.6_v016", L)
# ---- J10 placeholder ----
L = head("Pads_2x14_P2.00_SMD", "J10 PLACEHOLDER: 2 x 14 SMD test pads 1.0 x 1.3 at 2.0 pitch, row pitch 2.6: MCU / backplane link until the MCU section is drawn [A]", ref_y=-2.6, val_y=2.6)
L += [rect(-14.4, -2.15, 14.4, 2.15, "F.CrtYd"), rect(-14.2, -1.95, 14.2, 1.95, "F.Fab", 0.05), text("J10 MCU LINK (placeholder)", 0, 0, "F.Fab", 0.6)]
for i in range(14):
    x = (i - 6.5) * 2.0
    L.append(smd(str(2 * i + 1), x, 1.3, 1.0, 1.3, paste=False)); L.append(smd(str(2 * i + 2), x, -1.3, 1.0, 1.3, paste=False))
write("Pads_2x14_P2.00_SMD", L)
# ---- J2: 2x3 2.54 female socket for the joystick daughterboard (docs/top-screen-joystick.md v0.1) ----
# pads mirror the daughterboard J1 (joystick-daughterboard/make_project.py: header centre CAD x 5.6, pin 1 at KiCad (-1.27, -2.54))
L = head("PinSocket_2x03_P2.54_Vertical_8.5mm", "2x3 2.54 mm female socket, 8.5 mm tall, THT (Ø1.0 drill / Ø1.7 pad); joystick daughterboard J1 plugs in from the top = the riser. Pin 1 UP 2 CENTER 3 RIGHT 4 LEFT 5 GND 6 DOWN",
         attr="through_hole", ref_y=-4.6, val_y=4.6)
L += [rect(-2.54, -3.81, 2.54, 3.81, "F.Fab", 0.1), rect(-2.79, -4.06, 2.79, 4.06, "F.CrtYd")]
for i in range(6):
    L.append(pth(str(i + 1), -1.27 + 2.54 * (i % 2), -2.54 + 2.54 * (i // 2), 1.0, 1.7, "rect" if i == 0 else "circle"))
write("PinSocket_2x03_P2.54_Vertical_8.5mm", L)
# ---- top-screen joystick stack holes (joystick v0.1, cad/joystick-param) ----
J = dict(spring=(10.8, 6.6, 3.4), pins=(6.0, 8.5, 1.3), slot=(14.6, 0.0, 3.2, 10.7), balls=(14.0, 7.0, 2.0), base=(31.2, 18.2), dboard=(16.6, 12.0),
         socket=(5.6, 0.0), carrier=(33.6, 20.6), src="docs/top-screen-joystick.md v0.1 / cad/joystick-param")
sx, sy, sd = J["spring"]; px, py, pd = J["pins"]; tx, ty, tw, tl = J["slot"]; bx, by_, bd = J["balls"]
L = head("TopScreenJoystick_Stack_v016", "MH1, top-screen joystick v0.1: 4 x Ø3.4 extension-spring holes at (+-10.8,+-6.6), 4 x Ø1.3 base locating-pin holes at (+-6,+-8.5), screen FPC slot 3.2 x 10.7 at x 13.0-16.2; origin = carrier centre; Fab: base 31.2 x 18.2, daughterboard 16.6 x 12, carrier 33.6 x 20.6, balls",
         attr="through_hole exclude_from_pos_files exclude_from_bom", ref_y=-11.0, val_y=11.0)
L += [rect(-J["base"][0] / 2, -J["base"][1] / 2, J["base"][0] / 2, J["base"][1] / 2, "F.Fab", 0.1),
      rect(-J["dboard"][0] / 2, -J["dboard"][1] / 2, J["dboard"][0] / 2, J["dboard"][1] / 2, "F.Fab", 0.05),
      rect(-J["carrier"][0] / 2, -J["carrier"][1] / 2, J["carrier"][0] / 2, J["carrier"][1] / 2, "F.Fab", 0.05),
      text("printed base 31.2x18.2 (glued, 4 pins)", 0, -9.7, "F.Fab", 0.5)]
for X in (-1, 1):
    for Y in (-1, 1):
        L += [npth(X * sx, Y * sy, sd), npth(X * px, Y * py, pd), circ(X * bx, Y * by_, bd / 2, "F.Fab", 0.05)]
L.append(npth(tx, ty, None, "oval", tw, tl)); L.append(text("FPC", tx, ty - tl / 2 - 0.6, "F.Fab", 0.5))
write("TopScreenJoystick_Stack_v016", L)
json.dump(J, open(os.path.join(HERE, "joystick_stack_v016.json"), "w"), indent=1)
