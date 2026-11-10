knob-main-pcb v2.1 PCBWay pack, generated 2026-11-10 14:51 AWST by fab_export.py
READY TO QUOTE

{
  "board": "knob-main-pcb",
  "rev": "v2.1",
  "erc_messages": 0,
  "erc_errors": 0,
  "erc_warnings": 0,
  "drc_violations": 0,
  "drc_unconnected": 0,
  "drc_parity": 0,
  "bom_rows": 43,
  "cpl_parts": 143,
  "gerber_files": 18,
  "bom_rows_without_lcsc": []
}

Board v2 (9 Nov 2026): 6 layers [Ed Q45], FR-4, 1.6 mm: F.Cu signal, In1 ground plane, In2 signal, In3 signal
(the link flex's analog lines), In4 ground plane, B.Cu signal; no controlled impedance. ENIG [A] (0.5 mm pitch LQFP,
0.3 mm flex pads, 0.4 mm X2SON Halls); green mask, white silk [A]. Outline with five windows A-E, the ring LEDs'
cut-outs and holes: see Edge.Cuts (inside corners: router radius per PCBWay [C]). Min track 0.127, gap 0.1 (0.15 for
the flex's analog lines), vias 0.45 / 0.2 drill, all tented; three of them sit under U1's body (pins 54, 56, 58).
Two-sided SMT: U1 (LQFP-100), the Halls, the crystal and the screen / SPI resistors on top; the 12 SK6812MINI-E
(reverse-mount, their bodies down through cut-outs; MSL 5a), the motor driver, the encoder sensor and most passives
on the bottom.
Not in the BOM / CPL: J1 link-flex pads (the flex is hot-bar or hand soldered), J4 Tag-Connect pads, J5 cover-board pads,
JP1 solder jumper, H1 rod clamp (hand-fit tube and nut), M1 1220 motor tabs (soldered at assembly), MP1 / MP2 posts
(Ø1.0 pins of the jack unit's brass posts in plated Ø1.15 holes, soldered at assembly).
J2 / J3: holes and pads for the vertical boards' 2x11 1.27 mm right-angle headers, which come fitted on those boards;
their legs are soldered into this board at assembly [Ed 9 Nov]. Not in this BOM / CPL.
Passives: Samsung capacitors and UNI-ROYAL / Yageo 1% resistors, LCSC numbers read on lcsc.com on 9 Nov 2026.
Not fitted (out of BOM / CPL): R10, R11 (I2C pull-ups, on the jack board), R31 (GAINSEL-high spot).
Made with KiCad 7.0.11: ERC not run (no command-line ERC in 7); DRC without schematic parity.
