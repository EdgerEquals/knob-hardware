joystick-daughterboard v0.3 PCBWay pack, generated 2026-11-01 11:58 by make_project.py
READY TO QUOTE

{
  "board": "joystick-daughterboard",
  "rev": "v0.3",
  "erc_messages": 0,
  "erc_errors": 0,
  "erc_warnings": 0,
  "drc_violations": 0,
  "drc_unconnected": 0,
  "drc_parity": 0,
  "bom_rows": 3,
  "cpl_parts": 7,
  "gerber_files": 14,
  "bom_rows_without_lcsc": [
    "J1,J2"
  ],
  "consigned_samtec": [
    "J1",
    "J2"
  ]
}

Board: 2 layers, 1.0 mm FR-4; HASL or ENIG; green mask, white silk [A]. No LEDs.
J1 and J2 are Samtec TSW-103-20-T-S (1x3, mating pin 25.91 mm). Plastic on the BOTTOM. Trim the 2.79 mm tails flush on the top before the seat plate is glued on.
LCSC lists the same -20 lead as TSW-103-20-T-D (C3345998, two rows) and TSW-125-20-T-S (C3334257, 25 pins). The 1x3 is ordered from Samtec and consigned. Do not fit the 2-row part.
The two mating sockets are on the MAIN PCB: hanxia HX PM2.54-1x3P ZC H11, LCSC C41427518, one each side of the switch.
MH1-MH4 are XHHD STTZ2032, M2x35 hex female-female, LCSC C50377216, all GND. Screws are hand-fit: four M2x6 through the seat plate and this board, four M2x6 through the main PCB.
Screen FPC pin-out is not on this board (still open). Pull-ups and ESD are on the main PCB.
Direction map is confirmed at first-power calibration, not by a fixed legend.
