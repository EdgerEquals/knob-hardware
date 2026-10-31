"""Footprint generator (v0.13 Hall array, 2026-10-31): TI DRV5055 linear Hall, SOT-23 (DBZ, 3-lead), and a 1x4 SMD pad strip [A]
for the Hall-array interface to the MCU. DRV5055 DBZ: body 2.92 x 1.30 [S, TI], max height 1.12 [S]; pins 1 VCC, 2 OUT, 3 GND [S, TI top view];
lands 1.325 x 0.60 at x -1.1375 / y +-0.95 (1, 2) and x +1.1375 / y 0 (3) [A, IPC-style]. Hall element at the package centre,
~0.65 below the top [A]. Pads_1x04_P1.27: 4 SMD pads 0.8 x 1.6 at 1.27 pitch [A], placeholder for the cable/MCU link."""
import os
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "footprints.pretty")
def write(name, descr, ref, body, crt, pads, names=None):
    L = [f'(footprint "{name}"', '  (version 20241229) (generator "make_hall_footprints.py")', '  (layer "F.Cu")', f'  (descr "{descr}")', '  (attr smd)',
         f'  (property "Reference" "{ref}" (at 0 {-crt[1] - 0.6:.2f} 0) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))',
         f'  (property "Value" "{name}" (at 0 {crt[1] + 0.6:.2f} 0) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))',
         f'  (fp_rect (start {-body[0]/2:.3f} {-body[1]/2:.3f}) (end {body[0]/2:.3f} {body[1]/2:.3f}) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))',
         f'  (fp_rect (start {-crt[0]:.3f} {-crt[1]:.3f}) (end {crt[0]:.3f} {crt[1]:.3f}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))']
    for n, x, y, w, h in pads:
        L.append(f'  (pad "{n}" smd roundrect (at {x:.4f} {y:.4f}) (size {w:.3f} {h:.3f}) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25))')
    L.append(")"); open(os.path.join(OUT, name + ".kicad_mod"), "w").write("\n".join(L) + "\n"); print("wrote", name)
x = 1.1375
write("SOT-23_DRV5055", "TI DRV5055 linear Hall, SOT-23 DBZ; 1 VCC 2 OUT 3 GND", "U4", (1.3, 2.92), (1.9, 1.75),
      [("1", -x, -0.95, 1.325, 0.6), ("2", -x, 0.95, 1.325, 0.6), ("3", x, 0, 1.325, 0.6)])
write("Pads_1x04_P1.27_SMD", "1x4 SMD pads 0.8x1.6 @1.27 [A]: Hall array to MCU (VCC, GND, HALL_A, HALL_B)", "J2", (5.4, 2.0), (2.85, 1.2),
      [(str(i + 1), (i - 1.5) * 1.27, 0, 0.8, 1.6) for i in range(4)])
