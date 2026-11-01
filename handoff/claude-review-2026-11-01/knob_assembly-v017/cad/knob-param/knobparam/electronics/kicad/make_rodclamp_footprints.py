"""Writes the tube / rod clamp footprints (2026-10-31) for the dial-centre power + data link (data over power):
an M1.6 threaded rod [A] (POSITIVE, VBUS_DATA) runs down the brass tube bore (NEGATIVE, GND) and clamps the screen adapter
board to the main PCB. Both rod holes are NPTH Ø1.8 [A] (M1.6 clearance); copper rings are custom SMD pads (annuli)."""
import os
HERE = os.path.dirname(os.path.abspath(__file__)); LIB = os.path.join(HERE, "footprints.pretty")
def ring(num, r_in, r_out, side, paste=False):
    mid, w = (r_in + r_out) / 2, r_out - r_in
    L = f'"{side}.Cu" "{side}.Mask"' + (f' "{side}.Paste"' if paste else "")
    return (f'  (pad "{num}" smd custom (at {mid:.3f} 0) (size {w:.3f} {w:.3f}) (layers {L})\n'
            f'    (options (clearance outline) (anchor circle))\n'
            f'    (primitives (gr_circle (center {-mid:.3f} 0) (end 0 0) (width {w:.3f}) (fill no))))\n')
def fp(name, descr, hole, rings, crt_f, crt_b):
    crt = max(crt_f, crt_b)
    s = f'(footprint "{name}" (version 20240108) (generator "make_rodclamp_footprints") (layer "F.Cu")\n  (descr "{descr}")\n  (attr smd)\n'
    s += f'  (fp_text reference "REF**" (at 0 {-crt - 0.8:.2f}) (layer "F.SilkS") hide (effects (font (size 0.5 0.5) (thickness 0.08))))\n'
    s += f'  (fp_text value "{name}" (at 0 {crt + 0.8:.2f}) (layer "F.Fab") hide (effects (font (size 0.5 0.5) (thickness 0.08))))\n'
    s += f'  (fp_circle (center 0 0) (end {crt_f:.3f} 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))\n'
    s += f'  (fp_circle (center 0 0) (end {crt_b:.3f} 0) (stroke (width 0.05) (type solid)) (fill no) (layer "B.CrtYd"))\n'
    s += f'  (pad "" np_thru_hole circle (at 0 0) (size {hole:.3f} {hole:.3f}) (drill {hole:.3f}) (layers "*.Cu" "*.Mask"))\n'
    for r in rings: s += ring(*r)
    s += ")\n"
    open(os.path.join(LIB, name + ".kicad_mod"), "w").write(s)
HOLE = 1.8   # [A] M1.6 clearance, NPTH
# main PCB: pad 1 = GND tube solder ring (F), pad 2 = VBUS_DATA rod clamp ring under the M1.6 washer (B)
MAIN = dict(tube=(1.7, 3.2), clamp=(1.2, 2.2))
fp("TubeRodClamp_Main_M1.6", "Brass tube 5x3 solder ring (F, GND) + M1.6 rod clamp ring (B, VBUS_DATA), NPTH 1.8",
   HOLE, [("1", *MAIN["tube"], "F", True), ("2", *MAIN["clamp"], "B")], 3.45, 2.45)
# adapter: pad 1 = GND tube contact ring (B, tube top end presses on it), pad 2 = VBUS_DATA ring under the M1.6 thin nut (F)
ADAPT = dict(tube=(1.6, 2.8), clamp=(1.2, 1.8))
fp("TubeRodClamp_Adapter_M1.6", "Brass tube top contact ring (B, GND) + M1.6 thin-nut clamp ring (F, VBUS_DATA), NPTH 1.8",
   HOLE, [("1", *ADAPT["tube"], "B"), ("2", *ADAPT["clamp"], "F")], 1.9, 3.05)
print("written", MAIN, ADAPT)
