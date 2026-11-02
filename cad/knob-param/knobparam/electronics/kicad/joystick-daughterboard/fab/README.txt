joystick-daughterboard v0.4 PCBWay pack, generated 2026-11-01 14:53 by make_project.py
READY TO QUOTE

{
  "board": "joystick-daughterboard",
  "rev": "v0.4",
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
J1 and J2 are Samtec TSW-103-17-T-S (1x3, mating pin 15.74 mm). Plastic on the BOTTOM. Trim the 2.79 mm tails flush on the top before the seat plate is glued on.
The 1x3 is ordered from Samtec and consigned. Lead style -17 replaces the -20 pin, which was too long for the 25 mm riser.
The two mating sockets are on the MAIN PCB: hanxia HX PM2.54-1x3P ZC H11, LCSC C41427518, one each side of the switch.
MH1-MH4 are XHHD STTZ1022, round female-female M2x25 brass, LCSC C50378470, all GND. An ISO 4762 M2x6 socket screw goes through the seat plate and this board into the pillar. An M2x4 socket screw holds the other end under the main PCB.
Screen FPC pin-out is not on this board (still open). Pull-ups and ESD are on the main PCB.
Direction map is confirmed at first-power calibration, not by a fixed legend.
