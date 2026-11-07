# PCBWay pre-quote: questions and checks so far (7 Nov 2026)

Gathered from the layout log so they go to PCBWay in one pre-quote, before anything is commissioned (Danny's process: lock the BOM,
have PCBWay confirm sourcing and processes, then order). Each line says where it came from.

## Processes to confirm
1. **Link flex** (`electronics/kicad/jack-link-flex/fab/`): make a single-sided polyimide flex, 7.8 x 18.81, 25 x 0.15 at 0.3, ENIG
   on the openings, PI stiffener to 0.20 ± 0.03 total over the connector end (Hirose FH26 recommended FPC) - and **hot-bar bond its
   other end onto the main board during the PCBA** (25 fingers, 0.3 pitch, onto pads 0.15 x 1.2; footprint
   `LinkFlex_MainBoard_Pads_25x0.3`) [Ed 7 Nov 18:53, Q30 = A]. If they can't bond it: ship the flex loose and Danny solders it
   on the bench after the jack unit is on its posts (Q30 B, the fallback).
2. **Jack power boards**: exposed-pad vias in pad on the QFNs (tented or plugged?); VBUS / VSYS tracks at 0.3 for up to 2 A.
3. **Jack board**: tracks under the spring-contact sockets insulated by solder mask only (normal for these sockets, worth a look).

## Parts to confirm (stock, sourcing, ratings)
4. Not at LCSC or short there: DAC80504 (103 at LCSC), Harwin P70-5100045 spring contacts (none at LCSC; element14 has stock),
   Thonk PJ366ST jacks (not an LCSC part).
5. USB-C board: the LTH6.8's voltage rating.
6. Jack power boards: generic passives still need LCSC part numbers.

## Still open on our side before the pre-quote
- Jack power board (upper): 30 connections left to route by hand (KiCad DRC 0 on what is routed).
- eFuse (TPS25947, RPW0010A) land pattern is a placeholder: needs TI's package drawing (mpqf568) or their footprint files.
- Main board: the main-board pass (KiCad still from v0.18 inputs): v0.49's no-716 changes, the link flex pads, the encoder back on
  the board.
