"""Writes the project footprint library (footprints.pretty). Plain text .kicad_mod, KiCad 9 format.
Motor_1220_Tabs: the 1220 gearmotor's two rear solder tabs, through-board plated slots.
Tab sizes come from the motor part params (motor_gearbox.py VARIANTS['motor-1220'], themselves [A])."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "motors", "1220-coreless-planetary"))
import motor_gearbox as mg

def motor_tabs(name, M, slot_clear=0.2, annular=0.4):   # [A] per-side slot clearance, copper ring
    sw, sl = M["term_t"] + 2 * slot_clear, M["term_w"] + 2 * slot_clear     # slot: across tab, along tab
    pw, pl = sw + 2 * annular, sl + 2 * annular
    p = M["term_pitch"]; r = M["body_d"] / 2
    pads = "".join(
        f'  (pad "{i+1}" thru_hole oval (at {x:.3f} 0) (size {pw:.3f} {pl:.3f}) (drill oval {sw:.3f} {sl:.3f}) (layers "*.Cu" "*.Mask"))\n'
        for i, x in enumerate((-p / 2, p / 2)))
    return f'''(footprint "{name}"
  (version 20241229) (generator "make_footprints.py")
  (layer "F.Cu")
  (descr "{M['title']}: 2 rear solder tabs, plated slots {sw:.2f}x{sl:.2f}, pitch {p:.1f} [A]. Motor body Ø{M['body_d']:.1f} on F.Fab, axis at origin, motor on the front (F) side")
  (attr through_hole)
  (property "Reference" "M1" (at 0 {-(r + 1.5):.2f} 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
  (property "Value" "{name}" (at 0 {r + 1.5:.2f} 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
  (fp_circle (center 0 0) (end {r:.3f} 0) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))
  (fp_circle (center 0 0) (end {r + 0.25:.3f} 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
{pads})
'''

def shaft_hole(name, d):
    """Plain NPTH clearance hole for the fixed hollow shaft (no copper)."""
    return f'''(footprint "{name}"
  (version 20241229) (generator "make_footprints.py")
  (layer "F.Cu")
  (descr "NPTH Ø{d:.2f} clearance hole for the fixed hollow shaft on the dial axis")
  (attr exclude_from_pos_files exclude_from_bom)
  (property "Reference" "H1" (at 0 {-(d / 2 + 1.5):.2f} 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
  (property "Value" "{name}" (at 0 {d / 2 + 1.5:.2f} 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
  (fp_circle (center 0 0) (end {d / 2 + 0.25:.3f} 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
  (pad "" np_thru_hole circle (at 0 0) (size {d:.3f} {d:.3f}) (drill {d:.3f}) (layers "*.Cu" "*.Mask"))
)
'''

SHAFT_HOLE_D = 5.2   # [A] Ø5.0 brass tube (shafts/fixed-shaft-brass-5x3) + 0.1 per side. v0.2 used 6.2 (6 mm shaft, superseded)
SHAFT_HOLE_FP = f"Shaft_Hole_NPTH_{SHAFT_HOLE_D:.1f}mm"

if __name__ == "__main__":
    out = os.path.join(HERE, "footprints.pretty", "Motor_1220_Tabs.kicad_mod")
    open(out, "w").write(motor_tabs("Motor_1220_Tabs", mg.VARIANTS["motor-1220"]))
    print("wrote", out)
    out = os.path.join(HERE, "footprints.pretty", SHAFT_HOLE_FP + ".kicad_mod")
    open(out, "w").write(shaft_hole(SHAFT_HOLE_FP, SHAFT_HOLE_D))
    print("wrote", out)


# ---------------- screen adapter board footprints (2026-10-31) ----------------
def _fab_ref(ref, y):
    return (f'  (property "Reference" "{ref}" (at 0 {y:.2f} 0) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))\n')

def fpc_conn(name, n=14, pitch=0.5, pad_w=0.3, pad_l=1.0, pad_y=-1.4, mnt_w=1.0, mnt_l=1.6, mnt_x=4.6, mnt_y=0.5, body_w=10.6, body_d=3.6):
    """Generic top-contact 0.5 mm FPC/ZIF connector [A]: n contacts along x at pad_y (toward the board centre),
    2 mounting pads, cable entry on +y (KiCad y up = -y). Origin = body centre."""
    pads = "".join(f'  (pad "{i+1}" smd rect (at {(i - (n - 1) / 2) * pitch:.3f} {pad_y:.3f}) (size {pad_w:.3f} {pad_l:.3f}) (layers "F.Cu" "F.Paste" "F.Mask"))\n' for i in range(n))
    pads += "".join(f'  (pad "MP" smd rect (at {sx * mnt_x:.3f} {mnt_y:.3f}) (size {mnt_w:.3f} {mnt_l:.3f}) (layers "F.Cu" "F.Paste" "F.Mask"))\n' for sx in (-1, 1))
    cw, cd = body_w / 2, body_d / 2
    return f'''(footprint "{name}"
  (version 20241229) (generator "make_footprints.py")
  (layer "F.Cu")
  (descr "Generic {n}P {pitch} mm pitch FPC connector, top contact [A]; body {body_w}x{body_d}, height 1.0 [A]")
  (attr smd)
{_fab_ref("J1", -(cd + 0.6))}  (property "Value" "{name}" (at 0 {cd + 0.6:.2f} 0) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))
  (fp_rect (start {-cw:.3f} {-cd:.3f}) (end {cw:.3f} {cd:.3f}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
  (fp_rect (start {-cw + 0.1:.3f} {-cd + 0.1:.3f}) (end {cw - 0.1:.3f} {cd - 0.1:.3f}) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))
{pads})
'''

def qfn20(name, body=3.0, pitch=0.4, pad_w=0.2, pad_l=0.6, n_side=5):
    """QFN-20 3x3, 0.4 pitch, for CH32V003F4U6 [A] (no exposed pad assumed). Pin 1 top-left, anticlockwise."""
    h = body / 2; c = h - pad_l / 2 + 0.15   # pad centre, 0.15 outside the body edge
    pads, k = "", 1
    for side in range(4):
        for i in range(n_side):
            o = (i - (n_side - 1) / 2) * pitch
            x, y, w, l = [(-c, o, pad_l, pad_w), (o, c, pad_w, pad_l), (c, -o, pad_l, pad_w), (-o, -c, pad_w, pad_l)][side]
            pads += f'  (pad "{k}" smd rect (at {x:.3f} {y:.3f}) (size {w:.3f} {l:.3f}) (layers "F.Cu" "F.Paste" "F.Mask"))\n'; k += 1
    cy = h + 0.4
    return f'''(footprint "{name}"
  (version 20241229) (generator "make_footprints.py")
  (layer "F.Cu")
  (descr "QFN-20 {body}x{body} {pitch} pitch, CH32V003F4U6 [A], height 0.75 [A]")
  (attr smd)
{_fab_ref("U1", -(cy + 0.5))}  (property "Value" "{name}" (at 0 {cy + 0.5:.2f} 0) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))
  (fp_rect (start {-cy:.3f} {-cy:.3f}) (end {cy:.3f} {cy:.3f}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
  (fp_rect (start {-h:.3f} {-h:.3f}) (end {h:.3f} {h:.3f}) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))
{pads})
'''

def wire_pads(name, d=0.7, pitch=1.0, labels=("VCC", "GND", "D1", "D2")):
    """4 SMD solder pads on the BACK (B.Cu) at the board centre for 36 AWG wires up the 3.0 bore [A]."""
    q = pitch / 2; pos = [(-q, -q), (q, -q), (-q, q), (q, q)]
    pads = "".join(f'  (pad "{lab}" smd circle (at {x:.3f} {y:.3f}) (size {d:.3f} {d:.3f}) (layers "F.Cu" "F.Mask"))\n' for lab, (x, y) in zip(labels, pos))
    cy = q + d / 2 + 0.25
    return f'''(footprint "{name}"
  (version 20241229) (generator "make_footprints.py")
  (layer "F.Cu")
  (descr "4 wire pads VCC GND D1 D2, Ø{d} at {pitch} pitch, placed on the back (flipped), inside the Ø3.0 wire bore [A]")
  (attr smd exclude_from_bom)
  (property "Reference" "W1" (at 0 {-(cy + 0.5):.2f} 0) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))
  (property "Value" "{name}" (at 0 {cy + 0.5:.2f} 0) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))
  (fp_rect (start {-cy:.3f} {-cy:.3f}) (end {cy:.3f} {cy:.3f}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
  (fp_circle (center 0 0) (end 1.5 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.Fab"))
{pads})
'''

ADAPTER_FPS = {"FPC_14P_0.5mm_Top": fpc_conn, "QFN-20_3x3_P0.4_CH32V003": qfn20, "WirePads_4x_0.7mm_Back": wire_pads}

if __name__ == "__main__":
    for n, f in ADAPTER_FPS.items():
        out = os.path.join(HERE, "footprints.pretty", n + ".kicad_mod"); open(out, "w").write(f(n)); print("wrote", out)


# ---------------- encoder take-off bearing (2026-10-31) ----------------
ENC_BEARING_HOLE_D = 5.0   # [A] press fit for an F682ZZ flanged bearing (2 x 5 x 2.3, flange 6.1 x 0.6) [A]; Ed: 2 mm encoder shaft

def bearing_hole(name, d, flange_d=6.1):
    return f'''(footprint "{name}"
  (version 20241229) (generator "make_footprints.py")
  (layer "F.Cu")
  (descr "NPTH Ø{d:.2f} press-fit hole for a flanged miniature bearing (F682ZZ 2x5x2.3, flange Ø{flange_d} on the footprint side; H2 is placed on B = inserted from the PCB back) [A]")
  (attr exclude_from_pos_files exclude_from_bom)
  (property "Reference" "H2" (at 0 {-(flange_d / 2 + 1.0):.2f} 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))
  (property "Value" "{name}" (at 0 {flange_d / 2 + 1.0:.2f} 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))
  (fp_circle (center 0 0) (end {flange_d / 2:.3f} 0) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))
  (fp_circle (center 0 0) (end {flange_d / 2 + 0.25:.3f} 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
  (pad "" np_thru_hole circle (at 0 0) (size {d:.3f} {d:.3f}) (drill {d:.3f}) (layers "*.Cu" "*.Mask"))
)
'''
ENC_BEARING_FP = f"Bearing_F682ZZ_Press_NPTH_{ENC_BEARING_HOLE_D:.1f}mm"

if __name__ == "__main__":
    out = os.path.join(HERE, "footprints.pretty", ENC_BEARING_FP + ".kicad_mod")
    open(out, "w").write(bearing_hole(ENC_BEARING_FP, ENC_BEARING_HOLE_D)); print("wrote", out)
