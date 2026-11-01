"""Footprint generator (v0.12, 2026-10-31): TI TMAG5273 3D Hall sensor, SOT-23-6 (DBV), and 0402 passives for the screen adapter v0.3.
SOT-23-6 DBV: body 2.90 x 1.60 [S, TI], pitch 0.95, pads 1.10 x 0.60 at x +-1.1375 [A, IPC-style land]; courtyard +-1.95 x +-1.70.
Pins (TI datasheet, top view): 1 SCL, 2 GND, 3 GND(TEST), 4 VCC, 5 INT, 6 SDA. Hall element at the package centre [A].
0402: pads 0.54 x 0.64 at +-0.48 [A]; courtyard +-0.93 x +-0.47."""
import os
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "footprints.pretty")
def write(name, descr, ref, body, crt, pads, names=None):
    L = [f'(footprint "{name}"', '  (version 20241229) (generator "make_tmag5273_footprints.py")', '  (layer "F.Cu")', f'  (descr "{descr}")', '  (attr smd)',
         f'  (property "Reference" "{ref}" (at 0 {-crt[1] - 0.6:.2f} 0) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))',
         f'  (property "Value" "{name}" (at 0 {crt[1] + 0.6:.2f} 0) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))',
         f'  (fp_rect (start {-body[0]/2:.3f} {-body[1]/2:.3f}) (end {body[0]/2:.3f} {body[1]/2:.3f}) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))',
         f'  (fp_rect (start {-crt[0]:.3f} {-crt[1]:.3f}) (end {crt[0]:.3f} {crt[1]:.3f}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))']
    for n, x, y, w, h in pads:
        L.append(f'  (pad "{n}" smd roundrect (at {x:.4f} {y:.4f}) (size {w:.3f} {h:.3f}) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25))')
    L.append(")"); open(os.path.join(OUT, name + ".kicad_mod"), "w").write("\n".join(L) + "\n"); print("wrote", name)
x = 1.1375
write("SOT-23-6_TMAG5273", "TI TMAG5273 3D Hall, SOT-23-6 DBV; 1 SCL 2 GND 3 GND(TEST) 4 VCC 5 INT 6 SDA", "U3", (1.6, 2.9), (1.95, 1.70),
      [("1", -x, -0.95, 1.1, 0.6), ("2", -x, 0, 1.1, 0.6), ("3", -x, 0.95, 1.1, 0.6), ("4", x, 0.95, 1.1, 0.6), ("5", x, 0, 1.1, 0.6), ("6", x, -0.95, 1.1, 0.6)])
write("C_0402", "0402 capacitor", "C2", (1.0, 0.5), (0.93, 0.47), [("1", -0.48, 0, 0.54, 0.64), ("2", 0.48, 0, 0.54, 0.64)])
write("R_0402", "0402 resistor", "R1", (1.0, 0.5), (0.93, 0.47), [("1", -0.48, 0, 0.54, 0.64), ("2", 0.48, 0, 0.54, 0.64)])
