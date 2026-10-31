"""Footprint generator: Omron EE-SX1131 SMD dual-channel transmissive photomicrosensor (encoder, v0.11, 2026-10-31).
From the Omron datasheet (EE-SX1131_Ds.pdf, 'Recommended Soldering Pattern'): 6 pads 2.0 x 1.0, two columns 3.0 apart
(inner edges; centres +-2.5), pitch 1.4 along the slot. Body 5 (across the slot) x 4 (along the slot) x 4 tall, slot 2.0 wide.
Pins: A, NC, K on one arm; C, E1, E2 on the other (datasheet terminal table). Pad numbering 1-6 = A, NC, K, C, E1, E2 [A].
Slot runs along footprint Y. Authored on F.Cu; the board places it flipped to B.Cu."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "Omron_EE-SX1131"
pads = [("1", -2.5, -1.4), ("2", -2.5, 0.0), ("3", -2.5, 1.4), ("4", 2.5, -1.4), ("5", 2.5, 0.0), ("6", 2.5, 1.4)]
names = {"1": "A", "2": "NC", "3": "K", "4": "C", "5": "E1", "6": "E2"}
L = [f'(footprint "{NAME}"', '  (version 20241229) (generator "make_eesx1131_footprint.py")', '  (layer "F.Cu")',
     '  (descr "Omron EE-SX1131 SMD transmissive photomicrosensor, 2 mm slot, 0.3 mm apertures, dual channel; pads per datasheet recommended pattern; slot along Y")',
     '  (attr smd)',
     '  (property "Reference" "U2" (at 0 -3.2 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))',
     f'  (property "Value" "{NAME}" (at 0 3.2 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))',
     '  (fp_rect (start -2.5 -2.0) (end 2.5 2.0) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))',
     '  (fp_rect (start -1.0 -2.0) (end 1.0 2.0) (stroke (width 0.1) (type dash)) (fill no) (layer "F.Fab"))',
     '  (fp_rect (start -3.75 -2.25) (end 3.75 2.25) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))',
     '  (fp_line (start -1.2 -2.2) (end 1.2 -2.2) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))',
     '  (fp_line (start -1.2 2.2) (end 1.2 2.2) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))']
for n, x, y in pads:
    L.append(f'  (pad "{n}" smd rect (at {x:.3f} {y:.3f}) (size 2.000 1.000) (layers "F.Cu" "F.Paste" "F.Mask"))')
    L.append(f'  (fp_text user "{names[n]}" (at {x + (1.6 if x > 0 else -1.6):.3f} {y:.3f} 0) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))')
L.append(")")
open(os.path.join(HERE, "footprints.pretty", NAME + ".kicad_mod"), "w").write("\n".join(L) + "\n")
print("wrote", NAME)
