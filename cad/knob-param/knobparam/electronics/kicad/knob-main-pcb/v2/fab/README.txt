knob-main-pcb v2.0 PCBWay pack, generated 2026-11-09 17:54 AWST by fab_export.py
NOT READY TO ORDER (see below)

{
  "board": "knob-main-pcb",
  "rev": "v2.0",
  "erc_messages": 0,
  "erc_errors": 0,
  "erc_warnings": 0,
  "drc_violations": 0,
  "drc_unconnected": 0,
  "drc_parity": 0,
  "bom_rows": 47,
  "cpl_parts": 145,
  "gerber_files": 18,
  "bom_rows_without_lcsc": [
    "C13,C14",
    "C1,C10,C11,C12,C16,C18,C2,C25,C27,C29,C3,C31,C33,C4,C44,C45,C46,C47,C48,C49,C5,C50,C51,C52,C53,C54,C55,C56,C59,C60",
    "C19,C20,C21,C22,C23,C24,C26,C28,C30,C32,C37,C38,C39",
    "C34,C36,C58",
    "C40,C57",
    "C41,C65",
    "C35,C42,C43,C63",
    "C6,C64",
    "C61",
    "C62",
    "C7,C8",
    "C15,C17,C9",
    "J2",
    "J3",
    "R1,R23,R25,R26,R34,R40,R41,R42",
    "R12,R13,R14,R15,R16,R17",
    "R18,R19,R20,R21,R22,R27,R28,R33,R39,R4,R47,R5,R6,R7,R8",
    "R2,R3,R38",
    "R29",
    "R30",
    "R32",
    "R35",
    "R36",
    "R43",
    "R44",
    "R45",
    "R24,R46",
    "R37,R48,R49",
    "R50",
    "R9"
  ]
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
J2 / J3: the vertical boards' 2x11 1.27 mm headers, in the BOM as PCBA-fitted (design.py) [C: fitted here or with the
vertical boards]. Passives: values and packages set, LCSC numbers still to choose (next step).
Made with KiCad 7.0.11: ERC not run (no command-line ERC in 7); DRC without schematic parity.
