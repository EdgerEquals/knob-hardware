"""Footprint generator: Omron EE-SX1321 SMD dual-channel transmissive photomicrosensor (encoder, main PCB v0.11, 2026-11-01).
Replaces the discontinued EE-SX1131 [Ed 2026-11-01]. Source: Omron datasheet EE-SX1321 (omron.com, rev 10/2021), page 3
'Dimensions and Internal Circuit' + recommended soldering pattern + tape drawing. Verified from the drawing, NOT copied from the 1131:
  body 5.1 (across the slot: 1.55 arm + 2.0 slot + 1.55 arm) x 4.0 (along the slot) x 4.0 tall; slot 2.0 +-0.2 wide, 2.8 deep;
  optical axis 1.0 below the open face; detector apertures 1.0 x 0.3, 2 channels along the slot; terminals castellated on the
  board end face, pitch 1.4.
  Land pattern: 6 pads 2.0 (across) x 1.0 (along), inner edges 3.1 apart (centres +-2.55), pitch 1.4 (0.4 gaps).
  Pin numbers (top view, counter-clockwise like an IC): emitter arm 1 (top), 2, 3; detector arm 4 (bottom), 5, 6 (top),
  so 6 faces 1. Terminal table: 1 Anode, 2 + 3 Cathode, 4 + 5 Emitter, 6 Collector (common). Tape drawing labels
  A-C, K-E1, K-E2 across the slot, so 5 = E1 (opposite 2) and 4 = E2 (opposite 3).
  DIFFERENCES vs the EE-SX1131 footprint: pad centres +-2.55 (was +-2.5); pin 2 is a 2nd cathode (was NC); the detector column
  is numbered the other way (1131: 4 C / 5 E1 / 6 E2 top-down; 1321: 6 C / 5 E1 / 4 E2 top-down). The function positions
  (A opposite C, K opposite E1, K opposite E2) are the same.
Slot runs along footprint Y. Authored on F.Cu; the board places it flipped to B.Cu."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "Omron_EE-SX1321"
BODY_X, BODY_Y, SLOT_W = 5.1, 4.0, 2.0          # [S] datasheet
PAD_W, PAD_H, PAD_GAP, PITCH = 2.0, 1.0, 3.1, 1.4   # [S] recommended soldering pattern
PX = PAD_GAP / 2 + PAD_W / 2                    # 2.55
pads = [("1", -PX, -PITCH), ("2", -PX, 0.0), ("3", -PX, PITCH), ("4", PX, PITCH), ("5", PX, 0.0), ("6", PX, -PITCH)]
names = {"1": "A", "2": "K", "3": "K", "4": "E2", "5": "E1", "6": "C"}
cx, cy = PX + PAD_W / 2 + 0.25, BODY_Y / 2 + 0.25
L = [f'(footprint "{NAME}"', '  (version 20241229) (generator "make_eesx1321_footprint.py")', '  (layer "F.Cu")',
     '  (descr "Omron EE-SX1321 SMD transmissive photomicrosensor, 2 mm slot, 0.3 mm apertures, dual channel; body 5.1x4x4; pads per datasheet recommended pattern (2.0x1.0, gap 3.1, pitch 1.4); 1 A, 2-3 K, 4 E2, 5 E1, 6 C; slot along Y")',
     '  (attr smd)',
     '  (property "Reference" "U2" (at 0 -3.2 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))',
     f'  (property "Value" "{NAME}" (at 0 3.2 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))',
     f'  (fp_rect (start {-BODY_X / 2:.3f} {-BODY_Y / 2:.3f}) (end {BODY_X / 2:.3f} {BODY_Y / 2:.3f}) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))',
     f'  (fp_rect (start {-SLOT_W / 2:.3f} {-BODY_Y / 2:.3f}) (end {SLOT_W / 2:.3f} {BODY_Y / 2:.3f}) (stroke (width 0.1) (type dash)) (fill no) (layer "F.Fab"))',
     f'  (fp_circle (center {-BODY_X / 2 + 0.5:.3f} {-BODY_Y / 2 + 0.5:.3f}) (end {-BODY_X / 2 + 0.7:.3f} {-BODY_Y / 2 + 0.5:.3f}) (stroke (width 0.1) (type solid)) (fill yes) (layer "F.Fab"))',
     f'  (fp_rect (start {-cx:.3f} {-cy:.3f}) (end {cx:.3f} {cy:.3f}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))',
     '  (fp_line (start -1.2 -2.2) (end 1.2 -2.2) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))',
     '  (fp_line (start -1.2 2.2) (end 1.2 2.2) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))',
     f'  (fp_circle (center {-PX - PAD_W / 2 - 0.35:.3f} {-PITCH - 0.6:.3f}) (end {-PX - PAD_W / 2 - 0.25:.3f} {-PITCH - 0.6:.3f}) (stroke (width 0.12) (type solid)) (fill yes) (layer "F.SilkS"))']
for n, x, y in pads:
    L.append(f'  (pad "{n}" smd rect (at {x:.3f} {y:.3f}) (size {PAD_W:.3f} {PAD_H:.3f}) (layers "F.Cu" "F.Paste" "F.Mask"))')
    L.append(f'  (fp_text user "{n} {names[n]}" (at {x + (1.7 if x > 0 else -1.7):.3f} {y:.3f} 0) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))')
L.append(")")
open(os.path.join(HERE, "footprints.pretty", NAME + ".kicad_mod"), "w").write("\n".join(L) + "\n")
print("wrote", NAME)
