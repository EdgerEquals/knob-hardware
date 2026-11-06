"""Jack power board(s): the netlist, in one place (knob step 2, 6 Nov 2026). Pure Python (no KiCad): make_board.py builds the
schematic and the board from it; area.py sums the footprints. Parts as approved [Ed 6 Nov 10:02 Q22 = A, with the Q21 eFuse];
circuit as decided: Q1-Q11 (jack roles, power from USB-C 5-15 V, PD sink here, one boost + charge pump + two LDOs, everything
switchable and off by default, the switchable-jack circuit as drawn in docs/img/switchable-jack.png), Q19 (4 layers).
Values: [S] from a datasheet (docs/step2-power-board-circuit.md lists the sources), [A] my choice or a standard value.

Each part: ref, value, footprint (KiCad lib:name, or "jpb:<name>" for this board's own footprints), pins {pin number: net}, a block
(for the floorplan), LCSC/MPN where chosen, and a note. Pin numbers are the package's (datasheet pin tables, or the KiCad symbol for
the standard ones). Nets in CAPS; the jack lines keep the jack board's names (J1_TIP ... J4_RING, VBUS, CC1, CC2, DP, DN, GND)."""

PARTS = []
_count = {}
_B = ["upper"]   # the board the next parts go on [Ed 6 Nov Q23 = A]: "upper" = the power board (on the posts), "lower" = the board under it


def _ref(prefix):
    _count[prefix] = _count.get(prefix, 0) + 1
    return f"{prefix}{_count[prefix]}"


def part(prefix, value, fp, pins, block, lcsc="", mpn="", note="", names=None, ref=None, side=None):
    r = ref or _ref(prefix)
    PARTS.append(dict(ref=r, value=value, fp=fp, pins={str(k): v for k, v in pins.items()}, block=block, lcsc=lcsc, mpn=mpn,
                      note=note, names={str(k): v for k, v in (names or {}).items()}, board=_B[0], side=side))
    return r


_SIZE = {"0201": "R_0201_0603Metric", "0402": "R_0402_1005Metric", "0603": "R_0603_1608Metric", "0805": "R_0805_2012Metric",
         "1206": "R_1206_3216Metric"}


def R(val, a, b, block, size="0402", note=""):
    return part("R", val, "Resistor_SMD:" + _SIZE[size], {1: a, 2: b}, block, note=note)


def C(val, a, b, block, size="0402", note=""):
    return part("C", val, "Capacitor_SMD:" + _SIZE[size].replace("R_", "C_"), {1: a, 2: b}, block, note=note)


def build():
    PARTS.clear(); _count.clear()
    _B[0] = "upper"
    # ------------------------------------------------------------------ connectors
    # H1/H2: XFCN PM127VS-12-12-H34 2x6 1.27 SMD female (LCSC C2840010) on the top face, under the jack board's males; nets by position
    # from the jack board's placement.json (make_board.py maps them), so only listed here.
    part("H", "PM127VS-12-12-H34", "Connector_PinSocket_1.27mm:PinSocket_2x06_P1.27mm_Vertical_SMD", {}, "connectors", lcsc="C2840010",
         mpn="PM127VS-12-12-H34-4.5-R", note="nets by position from the jack board's H1", ref="H1")
    part("H", "PM127VS-12-12-H34", "Connector_PinSocket_1.27mm:PinSocket_2x06_P1.27mm_Vertical_SMD", {}, "connectors", lcsc="C2840010",
         mpn="PM127VS-12-12-H34-4.5-R", note="nets by position from the jack board's H2", ref="H2")
    _B[0] = "lower"
    # link flex: Hirose FH26W-25S-0.3SHW(60), 25 positions at 0.3 [Q11: 17 signals + 7 grounds; the 25th a ground] [A order: SCK at the
    # far edge, grounds either side of the USB pair, the CV inputs and the audio]
    LINK = ["SCK", "GND", "MOSI", "CS_DAC", "CS_OLED", "OLED_DC", "OLED_RES", "SCL", "SDA", "IO_INT", "MIDI_TX", "GND", "DP", "DN", "GND",
            "CV_IN1", "CV_IN2", "CV_IN3", "GND", "AOUT", "GND", "AIN", "GND", "GND", "GND"]
    part("J", "FH26W-25S-0.3SHW(60)", "jpb:Hirose_FH26W-25S-0.3SHW", {i + 1: n for i, n in enumerate(LINK)}, "connectors",
         lcsc="C2904698", mpn="FH26W-25S-0.3SHW(60)", note="link flex to the main board [Q11]", ref="J6")
    _B[0] = "upper"
    # the two Ø2 brass posts to the main board [Ed 4 Nov 22:21, 22:52]: GND (left ear, x -16.5) and VSYS = 15 V after the eFuse (right ear,
    # x +8.0); each steps down to a Ø1.0 pin through a plated Ø1.15 hole, Ø1.6 pad [Ed 6 Nov Q24 = A]
    part("MP", "post GND", "jpb:Post_Pad", {1: "GND"}, "connectors", note="Ø2 brass post, left ear", ref="MP1")
    part("MP", "post VSYS", "jpb:Post_Pad", {1: "VSYS"}, "connectors", note="Ø2 brass post, right ear", ref="MP2")
    _B[0] = "lower"
    # clear OLED, ER-OLED1.51-1 (SSD1309), 24-pin 0.5 flex into the XUNPU FPC-05F-24PH20 ZIF [pins: EastRising datasheet, in the repo]:
    # 4-wire SPI (BS1 = BS2 = 0), R/W# and E/RD# and D3-D7 to VSS, D2 open in serial mode, NC 1/24 (supports) to ground, NC 4 open [S]
    OLED = {1: "GND", 2: "GND", 3: "GND", 4: None, 5: "3V3", 6: "GND", 7: "GND", 8: "CS_OLED", 9: "OLED_RES", 10: "OLED_DC",
            11: "GND", 12: "GND", 13: "SCK", 14: "MOSI", 15: None, 16: "GND", 17: "GND", 18: "GND", 19: "GND", 20: "GND",
            21: "IREF", 22: "VCOMH", 23: "OLED_VCC", 24: "GND", 25: "GND", 26: "GND"}
    part("J", "FPC-05F-24PH20", "jpb:XUNPU_FPC-05F-24PH20", OLED, "connectors", lcsc="C2856805", mpn="FPC-05F-24PH20",
         note="clear OLED flex [C: the flex's contact side against this bottom-contact ZIF on the board's underside]", ref="J5",
         names={1: "NC(GND)", 2: "VLSS", 3: "VSS", 4: "NC", 5: "VDD", 6: "BS1", 7: "BS2", 8: "CS#", 9: "RES#", 10: "D/C#",
                11: "R/W#", 12: "E/RD#", 13: "D0/SCLK", 14: "D1/SDIN", 15: "D2", 16: "D3", 17: "D4", 18: "D5", 19: "D6", 20: "D7",
                21: "IREF", 22: "VCOMH", 23: "VCC", 24: "NC(GND)", 25: "MP", 26: "MP"})
    # OLED support [S: Crystalfontz CFAL12856A0-0151-B, the same glass: VCC 0.1 + 10 uF, VCOMH 4.7 uF/25 V, IREF ~910k (< 10 uA),
    # VDD 0.1 + 4.7 uF]; VCC 12.0-13.5 V, 27.4 mA typ all lit [S EastRising]: from +12.5 V through a ferrite [Ed Q6]
    part("FB", "600R@100MHz 0603", "Inductor_SMD:L_0603_1608Metric", {1: "P12V5", 2: "OLED_VCC"}, "oled", note="[A]")
    C("10uF 25V", "OLED_VCC", "GND", "oled", size="0805"); C("100nF 25V", "OLED_VCC", "GND", "oled")
    C("4.7uF 25V", "VCOMH", "GND", "oled", size="0805"); R("910k", "IREF", "GND", "oled")
    C("4.7uF", "3V3", "GND", "oled", size="0603"); C("100nF", "3V3", "GND", "oled")
    _B[0] = "upper"
    # ------------------------------------------------------------------ USB-C power in: PD sink, CC ESD, eFuse
    # HUSB238_002DD (DFN-10 3x3 + pad): 1 VIN, 2 D+, 3 D-, 4 CC1, 5 CC2, 6 SDA, 7 SCL, 8 VSET, 9 ISET, 10 GATE, pad GND [S Rev 2.1];
    # VSET 14.0k = 15 V (open would ask 20 V and trip the OVLO), ISET 22.6k = 3 A; D+/D- and GATE open (no load switch) [S]
    part("U", "HUSB238_002DD", "Package_DFN_QFN:DFN-10-1EP_3x3mm_P0.5mm_EP1.65x2.38mm",
         {1: "VBUS", 2: None, 3: None, 4: "CC1", 5: "CC2", 6: "SDA", 7: "SCL", 8: "VSET", 9: "ISET", 10: None, 11: "GND"}, "power in",
         lcsc="C7471904", mpn="HUSB238_002DD", note="I2C 0x08; pad size [C: KiCad's DFN-10 3x3 EP 1.65 x 2.38 until the drawing]",
         names={1: "VIN", 2: "D+", 3: "D-", 4: "CC1", 5: "CC2", 6: "SDA", 7: "SCL", 8: "VSET", 9: "ISET", 10: "GATE", 11: "GND"})
    C("1uF 50V", "VBUS", "GND", "power in", size="0603"); R("14.0k", "VSET", "GND", "power in"); R("22.6k", "ISET", "GND", "power in")
    for cc in ("CC1", "CC2"):
        part("D", "PESD24VL1BA", "Diode_SMD:D_SOD-323", {1: cc, 2: "GND"}, "power in", lcsc="C69324", mpn="PESD24VL1BA,115",
             note="bidirectional, 24 V standoff [S]")
    # eFuse TPS259470ARPWR: 1 EN/UVLO, 2 OVLO, 3 AUXOFF, 4 FLT, 5 IN, 6 OUT, 7 dVdt, 8 GND, 9 ILM, 10 ITIMER [S SLVSFC9B]
    #   ILIM = 3334 / RILM: 1.00k = 3.33 A (±10 %) [S, Q21 about 3.3 A]
    #   one string IN-102k-EN-30.1k-OVLO-10.0k-GND: UVLO 1.20 x 142.1/40.1 = 4.25 V up (3.86 down); OVLO 1.20 x 142.1/10.0 = 17.05 V up
    #   (15.49 down) [S thresholds 1.20 / 1.09 V]; EN at 17 V = 4.8 V (5 V recommended max, 6.5 V abs) [S]
    #   dVdt 1 nF: 2 V/ms (0.2 A into 100 uF), 7.5 ms to 15 V [S CdVdt(pF) = 2000 / SR]; ITIMER 2.2 nF: 1.8 ms overcurrent blanking [S]
    part("U", "TPS259470ARPWR", "jpb:TI_RPW0010A_VQFN-HR-10_2x2",
         {1: "EF_EN", 2: "EF_OV", 3: None, 4: "EFUSE_FLT", 5: "VBUS", 6: "VSYS", 7: "EF_DVDT", 8: "GND", 9: "EF_ILM", 10: "EF_TMR"},
         "power in", lcsc="C3662799", mpn="TPS259470ARPWR", note="auto-retry [Q21]; land pattern [C: TI RPW0010A drawing]",
         names={1: "EN/UVLO", 2: "OVLO", 3: "AUXOFF", 4: "FLT", 5: "IN", 6: "OUT", 7: "dVdt", 8: "GND", 9: "ILM", 10: "ITIMER"})
    R("102k", "VBUS", "EF_EN", "power in"); R("30.1k", "EF_EN", "EF_OV", "power in"); R("10.0k", "EF_OV", "GND", "power in")
    R("1.00k", "EF_ILM", "GND", "power in", note="3.33 A"); C("1nF 25V", "EF_DVDT", "GND", "power in"); C("2.2nF", "EF_TMR", "GND", "power in")
    C("1uF 50V", "VBUS", "GND", "power in", size="0603"); C("10uF 25V", "VSYS", "GND", "power in", size="0805")
    _B[0] = "lower"
    # ------------------------------------------------------------------ rails [Ed Q6]: boost to 18 V, charge pump, +12.5 V and -12 V LDOs
    # TPS55340RTE: 1/15/16 SW, 2 VIN, 3 EN, 4 SS, 5 SYNC, 6 AGND, 7 COMP, 8 FB, 9 FREQ, 10/14 NC (to ground), 11-13 PGND, pad AGND [S]
    #   VOUT = 1.229 x (1 + 137k/10.0k) = 18.07 V [S VREF, R2 about 10k]; 78.7k = 600 kHz [S]: on-time 240 ns at 15.75 V in (77 ns min),
    #   duty 73 % at 5 V in (89 % min max) [A]; SS 47 nF [S example]; EN: internal 950k pull-down = off until the expander drives it [S]
    #   compensation for 18 V / 20-100 mA, about 7.5 uF effective out [A, recalculated from the datasheet's method; bench-check the step]:
    #   2.00k + 470 nF (zero 170 Hz near the output pole) + 220 pF; crossover about 15 kHz at 12 V in, 35 kHz at 5 V in
    part("U", "TPS55340RTER", "Package_DFN_QFN:QFN-16-1EP_3x3mm_P0.5mm_EP1.7x1.7mm",
         {1: "SW_B", 2: "VSYS", 3: "BOOST_EN", 4: "B_SS", 5: "GND", 6: "GND", 7: "B_COMP", 8: "B_FB", 9: "B_FREQ", 10: "GND",
          11: "GND", 12: "GND", 13: "GND", 14: "GND", 15: "SW_B", 16: "SW_B", 17: "GND"}, "supply", lcsc="C169167", mpn="TPS55340RTER",
         names={1: "SW", 2: "VIN", 3: "EN", 4: "SS", 5: "SYNC", 6: "AGND", 7: "COMP", 8: "FB", 9: "FREQ", 10: "NC", 11: "PGND",
                12: "PGND", 13: "PGND", 14: "NC", 15: "SW", 16: "SW", 17: "PAD"})
    part("L", "10uH 1.5A", "Inductor_SMD:L_Cenker_CKCS4020", {1: "VSYS", 2: "SW_B"}, "supply", note="4 x 4 x 2, Isat >= 1.5 A [A]")
    part("D", "PMEG4010CEJ", "Diode_SMD:D_SOD-323F", {1: "BOOST", 2: "SW_B"}, "supply", lcsc="C50704", mpn="PMEG4010CEJ,115",
         note="40 V 1 A Schottky; pin 1 cathode")
    R("137k", "BOOST", "B_FB", "supply"); R("10.0k", "B_FB", "GND", "supply"); R("78.7k", "B_FREQ", "GND", "supply")
    C("47nF", "B_SS", "GND", "supply"); R("2.00k", "B_COMP", "B_CZ", "supply"); C("470nF", "B_CZ", "GND", "supply")
    C("220pF", "B_COMP", "GND", "supply")
    C("10uF 25V", "VSYS", "GND", "supply", size="0805"); C("100nF 50V", "VSYS", "GND", "supply")
    C("4.7uF 50V", "BOOST", "GND", "supply", size="0805"); C("4.7uF 50V", "BOOST", "GND", "supply", size="0805")
    # charge pump off the switch node: -(18.4 - 2 x 0.4) = about -17.6 V [A]; 2.2 R limits the diode peaks (BAT54S 1.25 A surge) [parts doc]
    R("2.2R", "SW_B", "CP_R", "supply", size="0603"); C("1uF 50V", "CP_R", "CP_A", "supply", size="0603")
    part("D", "BAT54SFILM", "Package_TO_SOT_SMD:SOT-23", {1: "VNEG_RAW", 2: "GND", 3: "CP_A"}, "supply", lcsc="C377935",
         mpn="BAT54SFILM", note="1 A1, 2 K2, 3 K1/A2: VNEG_RAW -> CP_A -> GND")
    C("4.7uF 50V", "VNEG_RAW", "GND", "supply", size="0805")
    _B[0] = "upper"   # [Ed 6 Nov 11:56 Q25 = A] the +12.5 V LDO and the 3.3 V buck on the power board (both boards about 63 % full)
    # TPS7A4901DGN: 1 OUT, 2 FB, 3 NC, 4 GND, 5 EN, 6 NR/SS, 7 DNC (no net at all), 8 IN, pad GND or open [S]
    #   VOUT = 1.188 x (1 + 95.3k/10.0k) = 12.51 V (12.57 V with the 1.194 V of the Japanese sheet) [S]; CFF 10 nF, NR 10 nF [S]
    part("U", "TPS7A4901DGNR", "Package_SO:HVSSOP-8-1EP_3x3mm_P0.65mm_EP1.57x1.89mm",
         {1: "P12V5", 2: "P_FB", 3: None, 4: "GND", 5: "P12_EN", 6: "P_NR", 7: None, 8: "BOOST", 9: "GND"}, "supply", lcsc="C16430",
         mpn="TPS7A4901DGNR", names={1: "OUT", 2: "FB", 3: "NC", 4: "GND", 5: "EN", 6: "NR/SS", 7: "DNC", 8: "IN", 9: "PAD"})
    R("95.3k 0.5%", "P12V5", "P_FB", "supply"); R("10.0k 0.5%", "P_FB", "GND", "supply"); C("10nF 25V", "P12V5", "P_FB", "supply")
    C("10nF", "P_NR", "GND", "supply"); C("4.7uF 50V", "BOOST", "GND", "supply", size="0805")
    C("10uF 25V", "P12V5", "GND", "supply", size="0805")
    _B[0] = "upper"
    # TPS7A3001DGN: same pins; VOUT = -1.176 x (1 + 93.1k/10.0k) = -12.13 V [S Table 2: -12 V = 93.1k / 10k]; EN high (3.3 V) enables [S]
    part("U", "TPS7A3001DGNR", "Package_SO:HVSSOP-8-1EP_3x3mm_P0.65mm_EP1.57x1.89mm",
         {1: "N12V", 2: "N_FB", 3: None, 4: "GND", 5: "N12_EN", 6: "N_NR", 7: None, 8: "VNEG_RAW", 9: "GND"}, "supply", lcsc="C33835",
         mpn="TPS7A3001DGNR", names={1: "OUT", 2: "FB", 3: "NC", 4: "GND", 5: "EN", 6: "NR/SS", 7: "DNC", 8: "IN", 9: "PAD"})
    C("4.7uF 50V", "VNEG_RAW", "GND", "supply", size="0805", note="the LDO's input: VNEG_RAW comes up the second stacks")
    R("93.1k 0.5%", "N12V", "N_FB", "supply"); R("10.0k 0.5%", "N_FB", "GND", "supply"); C("10nF 25V", "N12V", "N_FB", "supply")
    C("10nF", "N_NR", "GND", "supply"); C("10uF 25V", "N12V", "GND", "supply", size="0805")
    _B[0] = "upper"
    # 3.3 V: TPS62933DRLR: 1 RT, 2 EN, 3 VIN, 4 GND, 5 SW, 6 BST, 7 SS, 8 FB [S]; RT to GND = 1.2 MHz, 2.2 uH, >= 10 uF effective [S table];
    #   EN floating = on (0.7 uA pull-up; 6 V abs max, so never to VSYS) [S]: the board's 3.3 V is up whenever VSYS is, so the expander
    #   holds every switch open and every rail off from the start; VOUT = 0.8 x (1 + 30.9k/10.0k) = 3.27 V (the OLED's VDD max is 3.3) [S/A]
    part("U", "TPS62933DRLR", "Package_TO_SOT_SMD:SOT-583-8",
         {1: "GND", 2: None, 3: "VSYS", 4: "GND", 5: "SW_3", 6: "BST_3", 7: "SS_3", 8: "FB_3"}, "supply", lcsc="C3200405",
         mpn="TPS62933DRLR", names={1: "RT", 2: "EN", 3: "VIN", 4: "GND", 5: "SW", 6: "BST", 7: "SS", 8: "FB"})
    part("L", "2.2uH 1A", "Inductor_SMD:L_Cenker_CKCS252012", {1: "SW_3", 2: "3V3"}, "supply", note="2.5 x 2.0 [A]")
    C("100nF 25V", "BST_3", "SW_3", "supply"); C("10nF", "SS_3", "GND", "supply", note="1.5 ms (6.8 nF minimum) [S]")
    R("30.9k", "3V3", "FB_3", "supply"); R("10.0k", "FB_3", "GND", "supply")
    C("10uF 25V", "VSYS", "GND", "supply", size="0805"); C("100nF 50V", "VSYS", "GND", "supply")
    C("22uF 10V", "3V3", "GND", "supply", size="0805"); C("22uF 10V", "3V3", "GND", "supply", size="0805")
    _B[0] = "lower"
    # ------------------------------------------------------------------ jack circuits
    # DAC80504 (RTE): 3 CV channels + 1 spare; 0-2.5 V: internal 2.5 V reference divided by 2 (REFDIV high, required below VDD 3.3 V)
    # and gain 2 (GAIN high) [S]; resets to midscale (RSTSEL high: the outputs read +2.5 V, the switches are open anyway); LDAC low
    # (each write updates at once); SDO not used.
    part("U", "DAC80504RTET", "Package_DFN_QFN:QFN-16-1EP_3x3mm_P0.5mm_EP1.7x1.7mm",
         {1: "VREF", 2: "DAC1", 3: "DAC2", 4: "DAC3", 5: None, 6: "GND", 7: "3V3", 8: "3V3", 9: "3V3", 10: "3V3", 11: "GND",
          12: "CS_DAC", 13: "SCK", 14: "MOSI", 15: None, 16: "3V3", 17: "GND"}, "dac", lcsc="C2862796", mpn="DAC80504RTET",
         note="1 REF, 2-5 OUT0-3, 6 GND, 7 VDD, 8 GAIN, 9 RSTSEL, 10 REFDIV, 11 LDAC, 12 CS, 13 SCLK, 14 SDI, 15 SDO, 16 VIO, pad GND [S]",
         names={1: "REF", 2: "OUT0", 3: "OUT1", 4: "OUT2", 5: "OUT3", 6: "GND", 7: "VDD", 8: "GAIN", 9: "RSTSEL", 10: "REFDIV",
                11: "LDAC", 12: "CS", 13: "SCLK", 14: "SDI", 15: "SDO", 16: "VIO", 17: "EP"})
    C("220nF", "VREF", "GND", "dac", note="REF: 150 nF minimum [S]"); C("1uF", "3V3", "GND", "dac"); C("100nF", "3V3", "GND", "dac")
    C("100nF", "3V3", "GND", "dac", note="VIO")
    # VMID = VREF x 100/175 = 1.4286 V: the bias for the three CV output stages and the three CV input stages [A]; 14 uA from REF
    R("75.0k 0.1%", "VREF", "VMID", "dac"); R("100k 0.1%", "VMID", "GND", "dac"); C("1uF", "VMID", "GND", "dac")
    # CV outputs (OPA4197 A/B/C): inverting, Vout = 7 x VMID - 6 x Vdac: DAC 0..2.5 V -> +10..-5 V [A]; 1k inside the loop
    # (feedback taken after it) with Cf from the op-amp output to -in [parts doc: split feedback]; switch after it, outside the loop
    for k in (1, 2, 3):
        R("20.0k 0.1%", f"DAC{k}", f"CV{k}_N", f"jack{k}")
        R("120k 0.1%", f"CV{k}_S", f"CV{k}_N", f"jack{k}")
        C("47pF C0G", f"CV{k}_O", f"CV{k}_N", f"jack{k}")
        R("1.00k", f"CV{k}_O", f"CV{k}_S", f"jack{k}")
    # audio out (OPA4197 D): the H7B0's DAC (0-3.3 V) AC-coupled, x -3.01 -> about ±5 V, 1k out [Q8, Q9]
    C("1uF", "AOUT", "AO_C", "audio"); R("10.0k", "AO_C", "AO_N", "audio"); R("30.1k", "AO_O", "AO_N", "audio")
    C("220pF C0G", "AO_O", "AO_N", "audio", note="24 kHz"); R("1.00k", "AO_O", "J4_TIP", "audio")
    part("U", "OPA4197IDR", "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
         {1: "CV1_O", 2: "CV1_N", 3: "VMID", 4: "P12V5", 5: "VMID", 6: "CV2_N", 7: "CV2_O", 8: "CV3_O", 9: "CV3_N", 10: "VMID",
          11: "N12V", 12: "GND", 13: "AO_N", 14: "AO_O"}, "jack circuits", lcsc="C2058532", mpn="OPA4197IDR", note="CV outs A-C, audio out D")
    C("100nF 25V", "P12V5", "GND", "jack circuits"); C("100nF 25V", "N12V", "GND", "jack circuits")
    # CV inputs (TLV9064 A/B/C on 3.3 V): 100k in, x -0.133 + 1.619 V: ±12 V -> 3.21..0.02 V [parts doc: 100k, Rf about 13.7k]; 12 kHz
    for k in (1, 2, 3):
        R("100k", f"J{k}_TIP", f"CI{k}_N", f"jack{k}")
        R("13.3k", f"CV_IN{k}", f"CI{k}_N", f"jack{k}")
        C("1nF C0G", f"CV_IN{k}", f"CI{k}_N", f"jack{k}")
    # audio in (TLV9064 D): ring, AC-coupled, x -0.33 about 1.65 V: ±5 V -> 3.3..0 V [Q8, Q9]; 22 kHz
    C("1uF 50V", "J4_RING", "AI_C", "audio", size="0603"); R("100k", "AI_C", "AI_N", "audio")
    R("33.0k", "AIN", "AI_N", "audio"); C("220pF C0G", "AIN", "AI_N", "audio")
    R("10.0k", "3V3", "ABIAS", "audio"); R("10.0k", "ABIAS", "GND", "audio"); C("1uF", "ABIAS", "GND", "audio")
    part("U", "TLV9064IPWR", "Package_SO:TSSOP-14_4.4x5mm_P0.65mm",
         {1: "CV_IN1", 2: "CI1_N", 3: "VMID", 4: "3V3", 5: "VMID", 6: "CI2_N", 7: "CV_IN2", 8: "CV_IN3", 9: "CI3_N", 10: "VMID",
          11: "GND", 12: "ABIAS", 13: "AI_N", 14: "AIN"}, "jack circuits", lcsc="C779410", mpn="TLV9064IPWR", note="CV ins A-C, audio in D")
    C("100nF", "3V3", "GND", "jack circuits")
    _B[0] = "upper"
    # MIDI out [Q2, Q7]: one UART TX into the three open-drain buffers; tip = pin 5 (sink, 10 R), ring = pin 4 (33 R to 3.3 V) [S CA-033]
    part("U", "SN74LVC3G07DCUR", "Package_SO:VSSOP-8_2.3x2mm_P0.5mm",
         {1: "MIDI_TX", 2: "MY3", 3: "MIDI_TX", 4: "GND", 5: "MY2", 6: "MIDI_TX", 7: "MY1", 8: "3V3"}, "digital", lcsc="C131955",
         mpn="SN74LVC3G07DCUR", note="1A>1Y 7, 2A 3>2Y 5, 3A 6>3Y 2 [S-lib KiCad 74LVC3G07]")
    C("100nF", "3V3", "GND", "digital")
    for k in (1, 2, 3):
        R("10R", f"MY{k}", f"MT{k}", f"jack{k}", note="MIDI RC (pin 5)")
        R("33R 0.5W", "3V3", f"MR{k}", f"jack{k}", size="0805", note="MIDI RA (pin 4); 0.33 W if a mono plug shorts the ring: an 0805 "
              "anti-surge part rated 0.5 W (e.g. Panasonic ERJ-P06) [A]")
    # switches: one TMUX7212 per switchable jack: SW1 CV out -> tip, SW2 MIDI sink -> tip, SW3 MIDI source -> ring, SW4 spare
    # ring sense: 100k in series, 470k pull-up, BAV99 clamp to GND / 3.3 V (the expander's pins are not 12 V tolerant)
    for k in (1, 2, 3):
        R("100k", f"J{k}_RING", f"RS{k}", f"jack{k}"); R("470k", f"RS{k}", "3V3", f"jack{k}")
        part("D", "BAV99", "Package_TO_SOT_SMD:SOT-23", {1: "GND", 2: "3V3", 3: f"RS{k}"}, f"jack{k}", lcsc="C2500", mpn="BAV99",
             note="pin 1 A1, 2 K2, 3 K1/A2 [C: confirm on C2500's datasheet]")
    # TMUX7212RUMR [Ed 6 Nov Q25 = A: the same chip in WQFN-16 4x4, 0.65 pitch]: 1 S1, 2 VSS, 3 GND, 4 S4, 5 D4, 6 SEL4, 7 SEL3, 8 D3,
    #   9 S3, 10 NC, 11 VDD, 12 S2, 13 D2, 14 SEL2, 15 SEL1, 16 D1, pad not connected inside (to ground here) [S TI pin table];
    #   SEL high = closed, 4 M pull-downs (open at power-up), VIH 1.3 V; ±4.5..±22 V supplies (here +12.5 / -12) [S]
    for k in (1, 2, 3):
        part("U", "TMUX7212RUMR", "Package_DFN_QFN:QFN-16-1EP_4x4mm_P0.65mm_EP2.5x2.5mm",
             {15: f"SW{k}_CV", 16: f"J{k}_TIP", 1: f"CV{k}_S", 2: "N12V", 3: "GND", 4: "GND", 5: "GND", 6: "GND", 7: f"SW{k}_MR",
              8: f"J{k}_RING", 9: f"MR{k}", 10: "GND", 11: "P12V5", 12: f"MT{k}", 13: f"J{k}_TIP", 14: f"SW{k}_MT", 17: "GND"}, f"jack{k}",
             lcsc="C3657300", mpn="TMUX7212RUMR", note=f"jack {k}: SW1 CV out, SW2 MIDI tip, SW3 MIDI ring, SW4 spare; land pattern KiCad's "
             "generic 4x4 QFN-16 [C: TI RUM0016A]",
             names={15: "SEL1", 16: "D1", 1: "S1", 2: "VSS", 3: "GND", 4: "S4", 5: "D4", 6: "SEL4", 7: "SEL3", 8: "D3", 9: "S3",
                    10: "NC", 11: "VDD", 12: "S2", 13: "D2", 14: "SEL2", 17: "PAD"})
        C("100nF 25V", "P12V5", "GND", f"jack{k}"); C("100nF 25V", "N12V", "GND", f"jack{k}")
    # I/O expander (TCA9535, 0x20): switch controls, ring sense, rail enables, eFuse fault  [A allocation; may be swapped for routing]
    IO = {"P00": "SW1_CV", "P01": "SW1_MT", "P02": "SW1_MR", "P03": "SW2_CV", "P04": "SW2_MT", "P05": "SW2_MR", "P06": "SW3_CV",
          "P07": "SW3_MT", "P10": "SW3_MR", "P11": "RS1", "P12": "RS2", "P13": "RS3", "P14": "BOOST_EN", "P15": "P12_EN",
          "P16": "N12_EN", "P17": "EFUSE_FLT"}
    # [Ed 6 Nov Q25 = A] TCA9535RGER, VQFN-24 4x4: pins as TI's table for RTW/RGE [S]; the centre pad to ground (or open) [S]
    TCA = {"P00": 1, "P01": 2, "P02": 3, "P03": 4, "P04": 5, "P05": 6, "P06": 7, "P07": 8, "GND": 9, "P10": 10, "P11": 11, "P12": 12,
           "P13": 13, "P14": 14, "P15": 15, "P16": 16, "P17": 17, "A0": 18, "SCL": 19, "SDA": 20, "VCC": 21, "INT": 22, "A1": 23, "A2": 24}
    pins = {TCA[k]: v for k, v in IO.items()}
    pins.update({TCA["INT"]: "IO_INT", TCA["A0"]: "GND", TCA["A1"]: "GND", TCA["A2"]: "GND", TCA["GND"]: "GND", TCA["SCL"]: "SCL",
                 TCA["SDA"]: "SDA", TCA["VCC"]: "3V3", 25: "GND"})
    part("U", "TCA9535RGER", "Package_DFN_QFN:Texas_RGE0024C_VQFN-24-1EP_4x4mm_P0.5mm_EP2.1x2.1mm", pins, "digital", lcsc="C527428",
         mpn="TCA9535RGER", note="I2C 0x20; inputs at power-up, no pull-ups [S]; LCSC had 51 in stock on 6 Nov",
         names={**{v: k for k, v in TCA.items()}, 25: "PAD"})
    C("100nF", "3V3", "GND", "digital")
    R("4.7k", "SCL", "3V3", "digital"); R("4.7k", "SDA", "3V3", "digital"); R("10k", "IO_INT", "3V3", "digital")
    for en in ("P12_EN", "N12_EN"):   # the boost's EN has its own 950k pull-down [S]
        R("100k", en, "GND", "supply", note="off by default [Ed Q6]")
    R("10k", "EFUSE_FLT", "3V3", "supply")
    # ------------------------------------------------------------------ the second stacks [Ed 6 Nov Q23 = A]: power board underside (males)
    # to the lower board's top face (sockets), at x ∓11.15 under the first ones; 21 lines + 3 grounds [A]. Each list: inner column then
    # outer column, each from the top (nearer the jack tops) down, as the jack board's HDR_NETS.
    for ref_m, ref_f, cols in (("H3", "H5", STACK2["left"]), ("H4", "H6", STACK2["right"])):
        _B[0] = "upper"
        part("H", "PZ127VS-12-12-H16", "Connector_PinHeader_1.27mm:PinHeader_2x06_P1.27mm_Vertical_SMD", {}, "connectors",
             lcsc="C2840009", mpn="PZ127VS-12-12-H16-4.5-R", note="second stack, male, on the power board's underside", ref=ref_m, side="B")
        _B[0] = "lower"
        part("H", "PM127VS-12-12-H34", "Connector_PinSocket_1.27mm:PinSocket_2x06_P1.27mm_Vertical_SMD", {}, "connectors",
             lcsc="C2840010", mpn="PM127VS-12-12-H34-4.5-R", note="second stack, female, on the lower board's top face", ref=ref_f, side="F")
    return PARTS


# the second stacks' pinout [A]: (inner column, outer column), each top to bottom. Power and the left jacks on the left; the I2C, MIDI,
# USB data and the right jacks on the right (the link flex connector is at x +14.1 on the lower board).
STACK2 = {"left": (["CV2_S", "J2_TIP", "3V3", "P12V5", "N12V", "GND"], ["CV1_S", "J1_TIP", "BOOST_EN", "BOOST", "VNEG_RAW", "VSYS"]),
          "right": (["CV3_S", "J3_TIP", "MIDI_TX", "IO_INT", "SCL", "SDA"], ["J4_TIP", "J4_RING", "GND", "DP", "DN", "GND"])}


if __name__ == "__main__":
    build()
    print(len(PARTS), "parts so far")
