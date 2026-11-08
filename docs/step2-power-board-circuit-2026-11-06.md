# Step 2: the jack power board circuit, with values (6 Nov 2026)

The netlist lives in one place: `cad/knob-param/knobparam/electronics/kicad/jack-power-board/design.py` (149 parts: 25 chips, diodes,
inductors and connectors, 120 passives). This note is the plan in words. Parts as approved [Ed 6 Nov 10:02 Q22 = A]; circuit as decided
in Q1-Q11, Q19, Q21. Tags: [S] read in a datasheet (sources at the end), [A] my value, [C] to confirm.

## The problem first: it doesn't fit on one board

The parts' footprints (KiCad courtyards, every passive counted) need **839 mm²**; the power board has **603 mm²** free over both faces
(the jack row 43.0 x 10.5 plus the ears, less the two sockets on the top face and the two flex connectors on the bottom). That is 139 %
full before a single track. Boards like this route at about 65 % full on 4 layers. The 5 Nov floorplan said "fits": it left out the
passives (about 70 guessed; 120 counted now) and used smaller packages than the approved list.

Picture: `docs/img/power-board-area-sketch.png`. `jack-power-board/area.py` makes the numbers (`area.json`).

- Smallest packages (the TMUX7212 in its 4x4 QFN, LCSC C3657300, 915 in stock; OPA4197 in TSSOP; TCA9535 in QFN) and 0201 passives
  save about 183 mm²: still 109 % full.
- Dropping MIDI out and the ring sense as well: about 86 % full. Still not routable.
- More board above the jack row would sit in front of the clear OLED's lit area. **Under the power board there is 17 mm of air** down
  to the clear OLED, inside the jack row's outline, hidden behind the jacks; the model has nothing else in it (checked on v0.46).

**Q23 [Ed 6 Nov 11:27] = A (v0.47).** Asked as: **A** a second board under the power board (same outline, about 4.9 below it on two more 2x6 stacks; the flex
connectors move to its underside; the posts pass its bottom edge to the power board's ears): 1,221 mm² free, 69 % full. **B** cut
the circuit to fit one board (no MIDI out, no ring sense, smallest packages, 0201 passives): about 86 % full, very likely not routable.

If A, the split I'd use [A, the best of every split of the netlist's blocks that keeps the second stacks to 24 pins]:
- upper board (the power board, on the posts): power in (HUSB238, eFuse, CC ESD), the +12.5 V and -12 V LDOs, the switching (three
  TMUX7212, the MIDI buffer and resistors, ring sense) and the I/O expander: about 65 % full;
- lower board: the DAC, both quad op-amps with the CV out, CV in and audio parts, the boost and charge pump, the 3.3 V buck, the
  OLED's parts and both flex connectors: about 66 % full;
- the second stacks carry 21 lines (VSYS, 18 V, ±12 V, 3.3 V, the boost EN, 3 CV drives, the 3 tips back to the CV inputs, the audio
  tip and ring, MIDI TX, I2C SCL/SDA/INT, D+/D-) and 3 grounds.

## Power in

- **PD sink HUSB238_002DD** (DFN-10 3x3): VIN = VBUS with 1 µF 50 V; CC1/CC2 from the stacks; **VSET 14.0 kΩ = 15 V** (open asks
  20 V and would trip the OVLO); **ISET 22.6 kΩ = 3 A**; D+/D- and GATE open (no load switch); I2C 0x08 [S]. CC ESD: two
  PESD24VL1BA (bidirectional, 24 V) [S].
- **eFuse TPS259470ARPWR** (VQFN-HR 2x2, auto-retry [Q21]): IN = VBUS, OUT = **VSYS** (to the right post and the converters).
  - Current limit **RILM 1.00 kΩ = 3.33 A** (3334/RILM, ±10 %) [S].
  - One string IN-102k-EN-30.1k-OVLO-10.0k-GND: **UVLO 4.25 V** rising (3.86 falling), **OVLO 17.05 V** rising (15.49 falling)
    [S thresholds 1.20 / 1.09 V]. EN sits at 4.8 V at 17 V in (5 V recommended max, 6.5 V absolute; 5.6 V at a 20 V fault).
  - dVdt 1 nF: 2 V/ms, 7.5 ms to 15 V (0.2 A into 100 µF) [S CdVdt(pF) = 2000/SR]. ITIMER 2.2 nF: 1.8 ms blanking [S].
  - FLT open drain, 10 kΩ to 3.3 V, read on the expander. No power-good pin on the 470A (pin 3 is AUXOFF, left open) [S].

## Rails [Ed Q6]: everything but 3.3 V off until the H7B0 turns it on

- **Boost TPS55340RTER** to **18.07 V** (137k/10.0k, VREF 1.229 V) [S], **600 kHz** (FREQ 78.7k) [S]: on-time 240 ns at 15.75 V in
  (77 ns minimum), duty 73 % at 5 V in (89 % maximum) [A]. 10 µH (4x4, Isat ≥ 1.5 A [A]), PMEG4010CEJ diode, 2 x 4.7 µF 50 V out,
  10 µF 25 V + 100 nF in, SS 47 nF [S example]. EN from the expander; its own 950 kΩ pull-down keeps it off [S].
  Compensation [A, from the datasheet's method, for 20-100 mA]: 2.00 kΩ + 470 nF, 220 pF; crossover about 15 kHz (12 V in) to
  35 kHz (5 V in). [C] bench-check a load step. A non-synchronous boost passes VIN to its output when off: the LDOs' ENs do the off.
- **Charge pump** off the switch node: 2.2 Ω, 1 µF 50 V, BAT54SFILM, 4.7 µF 50 V: about **-17.6 V** [A].
- **+12.5 V: TPS7A4901** (95.3k/10.0k: 12.51 V with the 1.188 V reference, 12.57 V with the 1.194 V of the Japanese sheet; the OLED
  wants 12.0-13.5) [S]; CFF 10 nF, NR 10 nF, 4.7 µF 50 V in, 10 µF 25 V out [S: 2.2 µF min]; EN from the expander + 100 kΩ pull-down.
  Pin 7 is DNC (no net at all) [S].
- **-12 V: TPS7A3001** (93.1k/10.0k = -12.13 V, TI's own table) [S]; same caps; EN high (3.3 V) enables [S]; + 100 kΩ pull-down.
- **3.3 V: TPS62933FDRLR** [Ed 8 Nov Q39 = A: the forced-continuous version, no light-load bursts; same pins; `docs/noise-sweep-2026-11-08.md`;
  [C] its frequency moves off 1.2 MHz, the boost's 600 kHz x 2, in step 3], RT to GND = 1.2 MHz, 2.2 µH, 2 x 22 µF [S table: ≥ 10 µF effective]; BST 100 nF; SS 10 nF (1.5 ms);
  **30.9k/10.0k = 3.27 V** (the OLED's VDD maximum is 3.3 V). **EN left floating = on** (0.7 µA pull-up; 6 V absolute, so never to
  VSYS) [S]: the 3.3 V is up whenever VSYS is, so the expander holds every switch open and every rail off from the start.
- Loads [A]: +12.5 V about 45 mA (OLED 27 mA typ all lit [S], op-amps, switches, outputs); -12 V about 15 mA; 3.3 V under 40 mA
  (MIDI 3 x 7 mA when sending). About 1.2 W from the boost.

## Jack circuits (Q2, Q7: `docs/img/switchable-jack.png`)

- **DAC80504RTET** on 3.3 V: internal 2.5 V reference **divided by 2 and gain 2 = 0-2.5 V** (REFDIV and GAIN tied high; dividing is
  required below VDD 3.3 V [S]); resets to midscale; LDAC low; REF 220 nF (150 nF minimum) [S]; SPI 24-bit frames, data on the
  falling edge [S]. OUT3 spare.
- **VMID = 1.4286 V** = REF x 100/175 (75.0k/100k 0.1 %, 1 µF): the bias for all six CV stages, ratiometric with the DAC [A].
- **CV out** (OPA4197 A-C on +12.5/-12 V): inverting, **Vout = 7 x VMID - 6 x Vdac: 0..2.5 V -> +10..-5 V** (20.0k in, 120k back,
  0.1 %) [A]; 1 kΩ inside the loop (feedback after it), 47 pF from the op-amp output to -in (split feedback for the switch + cable) [A].
  1 LSB = 0.23 mV ≈ 0.3 cent.
- **CV in** (TLV9064 A-C on 3.3 V): 100k in, **11.3k** + 1 nF back (14 kHz), +in at VMID: **±12 V -> 2.95..0.23 V** [A; Ed 8 Nov
  Q40 = A: inside the H743's 3.0 V reference; was 13.3k, 3.21..0.02 V]; survives about
  ±25 V (0.25 mA into the clamps). Always on the tip, so it reads back the output.
- **Switches**: one **TMUX7212PWR** per switchable jack: SW1 CV drive -> tip, SW2 MIDI sink -> tip, SW3 MIDI source -> ring, SW4 spare
  (to ground). SEL high = closed, 4 MΩ pull-downs: all open at power-up [S].
- **MIDI out** [S CA-033 at 3.3 V]: one UART TX into the SN74LVC3G07's three open-drain buffers; tip (pin 5) through 10 Ω, ring
  (pin 4) 33 Ω 0.5 W (1206) to 3.3 V.
- **Ring sense**: 100k from the ring, 470k pull-up, BAV99 clamp to ground and 3.3 V (pin 1 A1, 2 K2, 3 common [S Nexperia]): open ring
  reads high, a mono plug reads 0.58 V (low). The expander's pins are not 12 V tolerant.
- **Audio jack** [Q8, Q9]: out = the H743's DAC (0-3.0 V since Q40), 1 µF in, x -3.32 (10.0k/33.2k, 220 pF: 22 kHz), 1 kΩ out
  (OPA4197 D, +in to ground); in = ring, 1 µF 50 V, 100k, x -0.28 (28.0k, 270 pF: 21 kHz) about VMID (TLV9064 D): ±5 V ->
  2.83..0.03 V [Ed 8 Nov Q40 = A; was x -3.01 out, x -0.33 in round a 3.3 V divider, now gone].
- **Expander TCA9535PWR** at 0x20 [A]: P00-P10 the 9 switches, P11-P13 ring sense, P14 boost EN, P15 +12.5 EN, P16 -12 EN, P17 eFuse
  FLT. INT to the flex. I2C pull-ups 4.7k, INT 10k [A] (the HUSB238 needs them: none on its side [S]).

## OLED and the flexes

- **Clear OLED** (ER-OLED1.51-1, pins from EastRising's datasheet in `docs/datasheets/`): 4-wire SPI (BS1 = BS2 = 0), R/W#, E/RD#
  and D3-D7 to ground, D2 open, pins 1 and 24 to ground, pin 4 open [S]. VCC from +12.5 V through a ferrite, 10 µF + 100 nF; VCOMH
  4.7 µF 25 V; IREF 910 kΩ; VDD 3.3 V with 4.7 µF + 100 nF [S: Crystalfontz CFAL12856A0-0151-B, the same glass].
- **XUNPU FPC-05F-24PH20** land pattern [S-lib LCSC/EasyEDA C2856805]: 24 pads 0.30 x 1.25 at 0.5 pitch, mounting pads 2.0 x 2.5 at
  ±7.44.
- **Link flex, FH26W-25S** (KiCad's Hirose FH26-25S footprint; FH26W is the same mechanics [S]), pins [A order, Q11 content]:
  1 SCK, 2 GND, 3 MOSI, 4 CS_DAC, 5 CS_OLED, 6 OLED_DC, 7 OLED_RES, 8 SCL, 9 SDA, 10 IO_INT, 11 MIDI_TX, 12 GND, 13 D+, 14 D-, 15 GND,
  16-18 CV_IN1-3, 19 GND, 20 AOUT, 21 GND, 22 AIN, 23 GND, **24 QGND**, 25 GND [Ed 8 Nov Q41 = A, Q42 = A: pin 24 carries the
  quiet ground to an ADC2 pin on the H743 (AGND_SENSE there), which subtracts it from the CV ins and the audio in].
- **Two grounds [Ed 8 Nov Q42 = A]:** QGND (the sleeves, the DAC and its caps, VMID, the audio output's + input) on its own stack
  pins (first stacks H1 / H2 inner 2; second stacks left inner 6, right outer 3), joined to GND by one 0R (R41) on this board; GND
  (power) on the rest. No supply current flows in QGND. `docs/noise-sweep-2026-11-08.md`.

## Tight or open

- **[C] eFuse land pattern**: TI's RPW0010A drawing gives the pad sizes but not their positions in text; the TI footprint zip on E2E
  and the KiCad draft (MR 3703) could not be read from here. Needs TI's drawing PDF (mpqf568) or the Ultra Librarian files.
- **[C] OLED flex contact side**: the XUNPU is bottom-contact; on the board's underside its contacts face up. The flex's contacts are
  on the side away from its stiffener [S drawing]; which way that faces after the bend into the connector is still to draw. Fallback
  in the parts list: dual-contact HC-FPC-0.5-24P-FHH20 (C19273940).
- **[C] FH26W entry side**: taken as the even-row (+x) side of KiCad's footprint [A]; check with its 3D model.
- **Ground drop for 1 V/oct**: the whole module's return current (up to 3 A) crosses the 2x6 stacks' 8 ground pins between the jack
  board (the sleeves) and the power board (the DAC and op-amps). At about 1 mΩ for the 8 pins in parallel [A] that is 1 mV per amp,
  about 1.2 cents per amp, moving with the motor. A sense ground (one stack pin as a quiet ground from the sleeves to the analog
  ground) would fix it; it needs a pin, so it belongs with Q23.
- Values for the boost compensation, the inductors and the ferrite are [A] (no LCSC numbers yet); generic passives by PCBWay.
- HUSB238 exposed pad size [C]; KiCad's DFN-10 3x3 (1.65 x 2.38) used until the drawing.

## Sources

- TPS25947: [pins](https://ti.com/document-viewer/lit/html/SLVSFC9B/GUID-930B2835-A158-4CEE-8149-F42EA5642FE1),
  [specs](https://ti.com/document-viewer/lit/html/SLVSFC9B/GUID-B28BEBBA-B2D9-4AB6-8766-FDB5D7000705), [RPW0010A drawing](https://ti.com/lit/pdf/mpqf568)
- TPS55340: [pins](https://www.ti.com/document-viewer/lit/html/SLVSBD4E/GUID-19767479-97CB-47E5-BE06-AF043D5157EF),
  [frequency](https://www.ti.com/document-viewer/lit/html/SLVSBD4E/GUID-CE12F047-4D68-4CC7-9734-90EC02F049D9),
  [compensation](https://www.ti.com/document-viewer/lit/html/SLVSBD4E/GUID-1937F9F8-BE35-4F9C-A2DF-04867491ADD9)
- TPS7A49: [pins](https://www.ti.com/document-viewer/TPS7A49/datasheet/pin_configuration_and_functions), [specs](https://www.ti.com/document-viewer/TPS7A49/datasheet/specifications)
- TPS7A30: [pins](https://ti.com/document-viewer/TPS7A30/datasheet/pin_configuration_and_functions), [application](https://www.ti.com/document-viewer/TPS7A30/datasheet/application_and_implementation#SBVS125468)
- TPS62933: [pins](https://ti.com/document-viewer/TPS62932/datasheet/GUID-7817D9E5-1D9C-44EE-93BF-1B62AFF07529),
  [EN](https://www.ti.com/document-viewer/TPS62932/datasheet/GUID-B6200EFD-5F04-400F-B781-64072002582C),
  [LC table](https://ti.com/document-viewer/TPS62933/datasheet/GUID-D42A5AAE-BBE6-4AB1-9419-33BC72E44D37)
- HUSB238: [datasheet Rev 2.1](https://pdf.elecfans.com/p/6825233.html), [VSET/ISET](https://done.land/components/power/powersupplies/usb/usbtriggers/husb238/)
- DAC80504: [pins](https://www.ti.com/document-viewer/DAC70504/datasheet/pin-configuration-and-functions-slase734711),
  [reference divider](https://www.ti.com/document-viewer/DAC70504/datasheet/reference-divider-t3921239-52),
  [power supply](https://www.ti.com/document-viewer/lit/html/SBAS871C/power-supply-recommendations-slase735713)
- TMUX7212: [pins](https://www.ti.com/document-viewer/lit/html/SCDS416D/GUID-4D16BFB9-9F28-4C49-BD2F-65394F88B6B0),
  [RUM at LCSC](https://lcsc.com/product-detail/Analog-Switches-Multiplexers_Texas-Instruments-TMUX7212RUMR_C3657300.html)
- SN74LVC3G07: [datasheet](https://pdf.elecfans.com/BURR-BROWN/SN74LVC3G07DCUT.html); BAV99: [Nexperia](https://web.pa.msu.edu/people/edmunds/Disco_Kraken/Components/Sundry_Components/NOT_Currently_In_Design/bav99_dual_diode.pdf)
- OLED: EastRising ER-OLED1.51-1 datasheet (`docs/datasheets/`), [Crystalfontz CFAL12856A0-0151-B](https://pdf.bomkeyelectronics.com/pdf/19/OLED%20DISPLAY%20MODULE.pdf)
- FH26: [Hirose catalogue](https://www.mouser.com/datasheet/3/731/1/FH26_Catalog_D49355_en.pdf), KiCad library (CC-BY-SA 4.0 with the design exception)
