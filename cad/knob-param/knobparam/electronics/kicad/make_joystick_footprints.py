"""Footprint generator (joystick daughterboard v0.2, 2026-11-01).
Alps SKRHADE010 (SKRH series, catalogue drawing No.4, update 2510; the land pattern is the same for SKRHAAE/ABE/ACE/ADE):
  6 terminal pads 1.35 x 1.0 [S]: columns at x = +-3.575 (5.8 inner / 8.5 outer), rows at y = 0, +-1.425 (1.85 inner / 3.85 outer).
  2 frame tabs 2.0 x 1.8 [S] at y = +-4.05 (6.3 inner / 9.9 outer) - mechanical, no net.
  2 NPTH for the guide bosses: Ø0.75 at y -1.9 and Ø1.05 at y +1.9 (3.8 apart) [S].
  Pins (circuit diagram): 1 A, 2 Center, 3 C, 4 B, 5 Common, 6 D. Directions a/b/c/d are at 45° to the body edges
  (a upper-left, b upper-right, c lower-left, d lower-right, top view). Footprint drawn in the catalogue orientation;
  rotate it -45° (visually clockwise) on the board so a -> screen UP, b -> RIGHT, c -> LEFT, d -> DOWN [verify on the bench].
PinHeader_2x03_P2.54mm_Vertical: plain 2x3 2.54 THT (Ø1.0 drill, Ø1.7 pads), pin 1 square at (0, 0), pin 2 at (2.54, 0)."""
import os
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "footprints.pretty")

def head(name, descr, ref, attr):
    return [f'(footprint "{name}"', '  (version 20241229) (generator "make_joystick_footprints.py")', '  (layer "F.Cu")', f'  (descr "{descr}")', f'  (attr {attr})']

def prop(ref, name, y0, y1):
    return [f'  (property "Reference" "{ref}" (at 0 {y0:.2f} 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))',
            f'  (property "Value" "{name}" (at 0 {y1:.2f} 0) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))']

def rect(x0, y0, x1, y1, layer, w):
    return f'  (fp_rect (start {x0:.3f} {y0:.3f}) (end {x1:.3f} {y1:.3f}) (stroke (width {w}) (type solid)) (fill no) (layer "{layer}"))'

def line(x0, y0, x1, y1, layer, w):
    return f'  (fp_line (start {x0:.3f} {y0:.3f}) (end {x1:.3f} {y1:.3f}) (stroke (width {w}) (type solid)) (layer "{layer}"))'

def skrh():
    n = "Alps_SKRHADE010"
    L = head(n, "Alps SKRH 4-direction + centre push SMD switch (SKRHADE010, 7.45x7.5x1.85). 1 A, 2 Center, 3 C, 4 B, 5 Common, 6 D. Directions at 45 deg to the body.", "SW1", "smd")
    L += prop("SW1", n, -5.6, 5.6)
    L += [rect(-3.725, -3.75, 3.725, 3.75, "F.Fab", 0.1)]
    # courtyard: body + 0.25, the pad columns and the frame tabs (tight, so the 45° part packs next to the header)
    c = [(-3.98, -4.0), (-1.25, -4.0), (-1.25, -5.2), (1.25, -5.2), (1.25, -4.0), (3.98, -4.0), (3.98, -2.2), (4.5, -2.2), (4.5, 2.2), (3.98, 2.2),
         (3.98, 4.0), (1.25, 4.0), (1.25, 5.2), (-1.25, 5.2), (-1.25, 4.0), (-3.98, 4.0), (-3.98, 2.2), (-4.5, 2.2), (-4.5, -2.2), (-3.98, -2.2)]
    L.append('  (fp_poly (pts ' + " ".join(f"(xy {x:.3f} {y:.3f})" for x, y in c) + ') (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))')
    # silk: stem ring + pin-1 dot (kept inside the body so it never reaches the board edge when rotated)
    L.append('  (fp_circle (center 0 0) (end 1.2 0) (stroke (width 0.12) (type solid)) (fill no) (layer "F.SilkS"))')
    L.append('  (fp_circle (center -2.6 -2.75) (end -2.35 -2.75) (stroke (width 0.12) (type solid)) (fill yes) (layer "F.SilkS"))')
    for lab, sx, sy in (("a", -1, -1), ("b", 1, -1), ("c", -1, 1), ("d", 1, 1)):
        L.append(f'  (fp_text user "{lab}" (at {sx * 4.6:.2f} {sy * 4.6:.2f} 0) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))')
    L.append(f'  (fp_circle (center 0 0) (end 1.5 0) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))')
    for i, (x, y) in enumerate([(-3.575, -1.425), (-3.575, 0), (-3.575, 1.425), (3.575, -1.425), (3.575, 0), (3.575, 1.425)]):
        L.append(f'  (pad "{i + 1}" smd rect (at {x:.4f} {y:.4f}) (size 1.35 1.0) (layers "F.Cu" "F.Paste" "F.Mask"))')
    # frame tabs are electrical: both go to GND (Ed). 7 is the local -y tab, 8 the local +y tab
    L.append('  (pad "7" smd rect (at 0 -4.050) (size 2.0 1.8) (layers "F.Cu" "F.Paste" "F.Mask"))')
    L.append('  (pad "8" smd rect (at 0 4.050) (size 2.0 1.8) (layers "F.Cu" "F.Paste" "F.Mask"))')
    L.append('  (pad "" np_thru_hole circle (at 0 -1.9) (size 0.75 0.75) (drill 0.75) (layers "*.Cu" "*.Mask"))')
    L.append('  (pad "" np_thru_hole circle (at 0 1.9) (size 1.05 1.05) (drill 1.05) (layers "*.Cu" "*.Mask"))')
    L.append(")"); open(os.path.join(OUT, n + ".kicad_mod"), "w").write("\n".join(L) + "\n"); print("wrote", n)

def standoff():
    n = "Mount_M2x11_Standoff"
    L = head(n, "M2 female-female brass standoff, 11 mm (XHHD STTZ2008, LCSC C50377192). PTH to GND; M2 screw from each board. Drill 2.4, pad 4.0.", "MH", "through_hole")
    L += prop("MH", n, -3.2, 3.4)
    L += ['  (fp_circle (center 0 0) (end 1.75 0) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))',
          '  (fp_circle (center 0 0) (end 2.05 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))']
    L.append('  (pad "1" thru_hole circle (at 0 0) (size 3.2 3.2) (drill 2.4) (layers "*.Cu" "*.Mask"))')
    L.append(")"); open(os.path.join(OUT, n + ".kicad_mod"), "w").write("\n".join(L) + "\n"); print("wrote", n)

def header():
    n = "PinHeader_2x03_P2.54mm_Vertical"
    L = head(n, "2x3 2.54 mm pin header, THT. J1 plastic on TOP, 6 mm mating pin down into J2 (2x3 female, 11 mm, on the main PCB). LXWCONN 254PZ-2x3P-V.", "J1", "through_hole")
    L += prop("J1", n, -1.9, 7.0)
    L += [rect(-1.27, -1.27, 3.81, 6.35, "F.Fab", 0.1), rect(-1.52, -1.52, 4.06, 6.6, "F.CrtYd", 0.05), line(-1.6, -1.27, -1.6, 1.27, "F.SilkS", 0.15)]   # pin-1 bar (no full outline: J1 sits 0.16 from the board edge)
    for i in range(6):
        x, y = (i % 2) * 2.54, (i // 2) * 2.54
        shape = "rect" if i == 0 else "circle"
        L.append(f'  (pad "{i + 1}" thru_hole {shape} (at {x:.2f} {y:.2f}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask"))')
    L.append(")"); open(os.path.join(OUT, n + ".kicad_mod"), "w").write("\n".join(L) + "\n"); print("wrote", n)

def header_1x3():
    n = "PinHeader_1x03_P2.54mm_Vertical_Long"
    L = head(n, "1x3 2.54 mm pin header, THT. Samtec TSW-103-17-T-S: insulator 2.54, mating pin 15.74, tail 2.79. Plastic on the UNDERSIDE of the joystick daughterboard, pin 1 toward the switch.", "J", "through_hole")
    L += prop("J", n, -2.2, 2.6)
    L += [rect(-3.81, -1.27, 3.81, 1.27, "F.Fab", 0.1), rect(-4.06, -1.52, 4.06, 1.52, "F.CrtYd", 0.05),
          line(-3.81, -1.55, -3.81, 1.55, "F.SilkS", 0.12)]
    for i, x in enumerate((-2.54, 0.0, 2.54)):
        shape = "rect" if i == 0 else "circle"
        L.append(f'  (pad "{i + 1}" thru_hole {shape} (at {x:.2f} 0) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask"))')
    L.append(")"); open(os.path.join(OUT, n + ".kicad_mod"), "w").write("\n".join(L) + "\n"); print("wrote", n)

def standoff_35():
    n = "Mount_M2x35_Standoff"
    L = head(n, "M2 female-female brass standoff, round body 25 mm, OD 3.2 (XHHD STTZ1022, LCSC C50378470). PTH to GND. Drill 2.4, pad 3.2. ISO 4762 M2 screw through this board into the pillar.", "MH", "through_hole")
    L += prop("MH", n, -3.2, 3.4)
    L += ['  (fp_circle (center 0 0) (end 1.75 0) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))',
          '  (fp_circle (center 0 0) (end 2.05 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))']
    L.append('  (pad "1" thru_hole circle (at 0 0) (size 3.2 3.2) (drill 2.4) (layers "*.Cu" "*.Mask"))')
    L.append(")"); open(os.path.join(OUT, n + ".kicad_mod"), "w").write("\n".join(L) + "\n"); print("wrote", n)

if __name__ == "__main__":
    skrh(); header(); standoff(); header_1x3(); standoff_35()
