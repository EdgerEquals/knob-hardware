"""Footprints for main PCB v0.12. Copies the JEDEC ones from the KiCad library and writes the optical parts.
Run with system python before make_board.py."""
import os, re, glob
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "footprints.pretty")
LIB = "/usr/share/kicad/footprints"

def copy_fp(src, name):
    t = open(src).read().replace("${KICAD7_3DMODEL_DIR}", "${KICAD9_3DMODEL_DIR}")
    t = re.sub(r"\(footprint\s+\S+", f'(footprint "{name}"', t, count=1)
    open(os.path.join(OUT, name + ".kicad_mod"), "w").write(t)

def write(name, body):
    open(os.path.join(OUT, name + ".kicad_mod"), "w").write(
        f'(footprint "{name}"\n  (version 20241229) (generator "make_lighting_footprints.py")\n'
        f'  (layer "F.Cu")\n{body})\n')

def copy_known():
    pairs = {
        "LQFP-100_14x14mm_P0.5mm": "Package_QFP.pretty/LQFP-100_14x14mm_P0.5mm.kicad_mod",
        "SOT-23": "Package_TO_SOT_SMD.pretty/SOT-23.kicad_mod",
        "SOT-23-5": "Package_TO_SOT_SMD.pretty/SOT-23-5.kicad_mod",
        "SOIC-8_3.9x4.9mm_P1.27mm": "Package_SO.pretty/SOIC-8_3.9x4.9mm_P1.27mm.kicad_mod",
        "Crystal_3225": "Crystal.pretty/Crystal_SMD_3225-4Pin_3.2x2.5mm.kicad_mod",
        "D_SOD-323": "Diode_SMD.pretty/D_SOD-323.kicad_mod",
    }
    for name, rel in pairs.items():
        copy_fp(os.path.join(LIB, rel), name)

def r0603():
    write("R_0603", '''  (attr smd)
  (descr "0603 resistor")
  (property "Reference" "R" (at 0 -1.4 0) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))
  (property "Value" "R_0603" (at 0 1.4 0) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))
  (fp_rect (start -0.80 -0.40) (end 0.80 0.40) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))
  (fp_rect (start -1.15 -0.55) (end 1.15 0.55) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
  (pad "1" smd roundrect (at -0.75 0) (size 0.80 0.90) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2))
  (pad "2" smd roundrect (at 0.75 0) (size 0.80 0.90) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2))
''')

def vcsel():
    # JNJ 2835 drawing: 3.5 along the pins, 2.8 across, pin 1 anode, pin 2 cathode, notch on pin 2.
    # Land: pads 1.2 x 2.0, gap 0.5 (centres ±0.85).
    write("LED_2835_VCSEL", '''  (attr smd)
  (descr "JNJ 2835 VCSEL, pin 1 anode, pin 2 cathode, notch on the cathode end")
  (property "Reference" "LD" (at 0 -1.9 0) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))
  (property "Value" "VCSEL" (at 0 1.9 0) (layer "F.Fab") (effects (font (size 0.35 0.35) (thickness 0.05))))
  (fp_rect (start -1.75 -1.40) (end 1.75 1.40) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))
  (fp_line (start 1.35 -1.40) (end 1.75 -1.00) (stroke (width 0.1) (type solid)) (layer "F.Fab"))
  (fp_rect (start -1.60 -1.20) (end 1.60 1.20) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
  (fp_circle (center -1.9 -1.5) (end -1.7 -1.5) (stroke (width 0.12) (type solid)) (fill yes) (layer "F.SilkS"))
  (pad "1" smd roundrect (at -0.85 0) (size 1.20 2.00) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.15))
  (pad "2" smd roundrect (at 0.85 0) (size 1.20 2.00) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.15))
''')

def rgb():
    # SK6805-EC20 top view: 1 GND and 2 DIN on the left, 4 DOUT and 3 VDD on the right. Body 2.0.
    write("LED_SK6805_EC20", '''  (attr smd)
  (descr "SK6805-EC20 top view: 1 GND, 2 DIN, 3 VDD, 4 DOUT")
  (property "Reference" "RGB" (at 0 -1.6 0) (layer "F.Fab") (effects (font (size 0.35 0.35) (thickness 0.05))))
  (property "Value" "SK6805" (at 0 1.6 0) (layer "F.Fab") (effects (font (size 0.3 0.3) (thickness 0.05))))
  (fp_rect (start -1.0 -1.0) (end 1.0 1.0) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))
  (fp_rect (start -1.05 -1.05) (end 1.05 1.05) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
  (fp_circle (center -1.15 1.15) (end -0.95 1.15) (stroke (width 0.1) (type solid)) (fill yes) (layer "F.SilkS"))
  (pad "1" smd roundrect (at -0.55 0.55) (size 0.70 0.65) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2))
  (pad "2" smd roundrect (at -0.55 -0.55) (size 0.70 0.65) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2))
  (pad "3" smd roundrect (at 0.55 -0.55) (size 0.70 0.65) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2))
  (pad "4" smd roundrect (at 0.55 0.55) (size 0.70 0.65) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2))
''')

def padrow(n, name=None):
    name = name or f"PadRow_1x{n:02d}"
    xs = [(i - (n - 1) / 2) * 2.54 for i in range(n)]
    pads = "\n".join(
        f'  (pad "{i+1}" thru_hole circle (at {x:.2f} 0) (size 1.70 1.70) (drill 1.00) (layers "*.Cu" "*.Mask"))'
        for i, x in enumerate(xs))
    x0, x1 = xs[0] - 1.15, xs[-1] + 1.15
    write(name, f'''  (attr through_hole)
  (descr "hand-solder pad row, {n} x 2.54 mm")
  (property "Reference" "J" (at 0 -2.2 0) (layer "F.Fab") (effects (font (size 0.6 0.6) (thickness 0.1))))
  (property "Value" "{name}" (at 0 2.2 0) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))
  (fp_rect (start {x0:.2f} -1.25) (end {x1:.2f} 1.25) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
  (fp_circle (center {xs[0]:.2f} -1.3) (end {xs[0]+0.25:.2f} -1.3) (stroke (width 0.12) (type solid)) (fill yes) (layer "F.SilkS"))
{pads}
''')

def socket_1x3():
    # hanxia HX PM2.54-1x3, 11 mm body. Pads numbered toward -X = pin 1.
    padrow(3, "PinSocket_1x03_P2.54")

def mount_m2():
    write("Mount_M2_PTH", '''  (attr through_hole)
  (descr "M2 standoff hole, drill 2.4, pad 3.2, one net")
  (property "Reference" "H" (at 0 -2.2 0) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))
  (property "Value" "M2" (at 0 2.2 0) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))
  (fp_circle (center 0 0) (end 1.70 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
  (pad "1" thru_hole circle (at 0 0) (size 3.2 3.2) (drill 2.4) (layers "*.Cu" "*.Mask"))
''')

def npth_slot(name, width, length):
    """Oval NPTH. `length` is along local X (the radius, once the footprint is rotated)."""
    hx, hy = length / 2 + 0.4, width / 2 + 0.4
    write(name, f'''  (descr "NPTH slot {width:.2f} x {length:.2f} mm, long axis local X")
  (attr exclude_from_pos_files exclude_from_bom)
  (property "Reference" "H" (at 0 {-hy - 0.6:.2f} 0) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))
  (property "Value" "{name}" (at 0 {hy + 0.6:.2f} 0) (layer "F.Fab") (effects (font (size 0.3 0.3) (thickness 0.05))))
  (fp_rect (start {-hx:.2f} {-hy:.2f}) (end {hx:.2f} {hy:.2f}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
  (pad "" np_thru_hole oval (at 0 0) (size {length:.2f} {width:.2f}) (drill oval {length:.2f} {width:.2f}) (layers "*.Cu" "*.Mask"))
''')

def npth(name, d):
    write(name, f'''  (descr "NPTH {d} mm")
  (attr exclude_from_pos_files exclude_from_bom)
  (property "Reference" "H" (at 0 -2 0) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))
  (property "Value" "{name}" (at 0 2 0) (layer "F.Fab") (effects (font (size 0.3 0.3) (thickness 0.05))))
  (fp_circle (center 0 0) (end {d/2+0.4:.2f} 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
  (pad "" np_thru_hole circle (at 0 0) (size {d:.2f} {d:.2f}) (drill {d:.2f}) (layers "*.Cu" "*.Mask"))
''')

def slot():
    # joystick v0.4 FPC slot, local 3.7 x 9.9
    write("Slot_FPC_v04", '''  (descr "joystick v0.4 FPC slot 3.7 x 9.9 NPTH")
  (attr exclude_from_pos_files exclude_from_bom)
  (property "Reference" "S" (at 0 -6 0) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))
  (property "Value" "SLOT" (at 0 6 0) (layer "F.Fab") (effects (font (size 0.3 0.3) (thickness 0.05))))
  (fp_rect (start -1.95 -5.05) (end 1.95 5.05) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
  (pad "" np_thru_hole oval (at 0 0) (size 3.70 9.90) (drill oval 3.70 9.90) (layers "*.Cu" "*.Mask"))
''')

if __name__ == "__main__":
    copy_known(); r0603(); vcsel(); rgb(); socket_1x3(); mount_m2(); slot()
    for n in (2, 3, 4, 6, 8, 11): padrow(n)
    npth("Hole_NPTH_1.6", 1.6); npth("Hole_NPTH_1.8", 1.8); npth("Hole_NPTH_3.4", 3.4)
    print("footprints", len(glob.glob(os.path.join(OUT, "*.kicad_mod"))))
