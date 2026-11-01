"""Components the v0.12 lighting / laser / motor round adds. Consumed by knob-main-pcb/kicad/design.py."""
import lighting_params as LP

def _pins(names, et="passive"):
    return [(str(i + 1), n, et if isinstance(et, str) else et[i], "L" if i < (len(names) + 1) // 2 else "R") for i, n in enumerate(names)]

def register(PINS):
    PINS["MCU"] = []
    for n, port, net, et, grp, rnd in LP.pin_rows():
        kind = "power_in" if grp == "power" else et
        PINS["MCU"].append((str(n), port, kind, "L" if n <= 50 else "R"))
    PINS["NMOS"] = [("1", "G", "input", "L"), ("2", "S", "passive", "L"), ("3", "D", "passive", "R")]
    PINS["PMOS"] = [("1", "G", "input", "L"), ("2", "S", "passive", "L"), ("3", "D", "passive", "R")]
    PINS["NPN"] = [("1", "B", "input", "L"), ("2", "E", "passive", "L"), ("3", "C", "passive", "R")]
    PINS["VCSEL"] = [("1", "A", "passive", "L"), ("2", "K", "passive", "R")]
    PINS["RGB"] = [("1", "GND", "passive", "L"), ("2", "DIN", "passive", "L"), ("3", "VDD", "passive", "R"), ("4", "DOUT", "passive", "R")]
    PINS["LDO"] = [("1", "VIN", "power_in", "L"), ("2", "GND", "power_in", "L"), ("3", "EN", "input", "L"),
                   ("4", "BP", "passive", "R"), ("5", "VOUT", "power_out", "R")]
    PINS["CAN"] = [("1", "D", "input", "L"), ("2", "GND", "power_in", "L"), ("3", "VCC", "power_in", "L"), ("4", "R", "output", "L"),
                   ("5", "Vref", "passive", "R"), ("6", "CANL", "passive", "R"), ("7", "CANH", "passive", "R"), ("8", "Rs", "passive", "R")]
    PINS["XTAL"] = [("1", "X1", "passive", "L"), ("2", "GND", "passive", "L"), ("3", "X2", "passive", "R"), ("4", "GND", "passive", "R")]
    PINS["DIODE"] = [("1", "K", "passive", "L"), ("2", "A", "passive", "R")]
    PINS["M2"] = [("1", "P", "passive", "R")]
    for n in (2, 3, 4, 6, 8, 11):
        PINS[f"P{n}"] = [(str(i + 1), str(i + 1), "passive", "L" if i < n / 2 else "R") for i in range(n)]

def _fld(key, note=""):
    mpn, mfr, lc, stock = LP.PARTS[key]
    f = {"MPN": mpn, "Manufacturer": mfr, "LCSC": lc}
    if note: f["Note"] = note + f" LCSC stock {stock} on 2026-11-01."
    else: f["Note"] = f"LCSC stock {stock} on 2026-11-01."
    return f

def _hit(x, y, boxes):
    import math
    if any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in boxes): return True
    return math.hypot(x - 25.25, y - 52.9) < 9

def _sot_slots():
    import math
    avoid = [(8, 34, 30, 48), (18, 82, 33, 96)]
    holes = [(25.25, 68.2, 6.5), (22.5, 39.9, 8.0), (36.0, 52.9, 7.0), (12.0, 45.3, 4.0)]
    pts = []
    for y in (66.0, 71.2, 76.4, 81.6, 87.0):
        for col in range(7):
            x = 9.0 + col * 5.3
            if _hit(x, y, avoid): continue
            if any(math.hypot(x - hx, y - hy) < r for hx, hy, r in holes): continue
            pts.append((x, y))
    pts += [(36.5, 91.0), (42.0, 91.0), (46.2, 91.0)]
    return pts

def _passive_slots():
    import math
    avoid = [(8, 34, 30, 48), (8, 54, 24, 64), (18, 82, 33, 96), (12, 96, 40, 118), (2, 63, 48, 92)]
    raw = []
    for y in (23.2, 25.4):
        x = 8.0
        while x <= 40:
            raw.append((round(x, 2), y)); x += 2.2
    y = 31.0
    while y <= 60.0:
        x = 10.0
        while x <= 42.0:
            if not _hit(x, y, avoid) and math.hypot(x - 36.0, y - 52.9) >= 7:
                raw.append((round(x, 2), round(y, 2)))
            x += 2.2
        y += 2.0
    y = 102.0
    while y <= 114.0:
        for x in (6.6, 9.2, 11.8):
            raw.append((x, round(y, 2)))
        y += 2.0
    kept = []
    for p in raw:
        if all(math.hypot(p[0] - q[0], p[1] - q[1]) >= 2.1 for q in kept):
            kept.append(p)
    return kept

class B:
    def __init__(self):
        self.out, self.mech = [], []
        self._sot, self._pas = _sot_slots(), _passive_slots()
        self._big = [(44.0, 37.0 + i * 3.8) for i in range(8)]
    def add(self, ref, sym, value, fp, nets, place, fields=None, bom=True, side="B", auto=False):
        if fp in ("SOT-23", "SOT-23-5", "WSON-8_2x2_DRV8837"): auto = True
        if auto:
            if not self._sot: raise RuntimeError("sot grid full at " + ref)
            x, y = self._sot.pop(0); place = (x, y, 0)
        self.out.append(dict(ref=ref, sym=sym, pins=None, value=value, footprint="footprints:" + fp, nets=nets,
                             fields=fields or {}, bom=bom, place=place, side=side))
    def R(self, ref, val, key, n1, n2, xy=None, side="B"):
        big = key in ("100R",)
        pool = self._big if big else self._pas
        if not pool: raise RuntimeError(("0603" if big else "passive") + " grid full at " + ref)
        xy = pool.pop(0)
        self.add(ref, "R", val, "R_0603" if big else "R_0402", {"1": n1, "2": n2}, (*xy, 0), _fld(key), side=side)
    def C(self, ref, val, key, n1, n2, xy=None, fp="C_0402", side="B"):
        if fp == "C_0603":
            xy = self._big.pop(0)
            self.add(ref, "C", val, fp, {"1": n1, "2": n2}, (*xy, 0), _fld(key), side=side)
            return
        if not self._pas: raise RuntimeError("passive grid full at " + ref)
        xy = self._pas.pop(0)
        self.add(ref, "C", val, fp, {"1": n1, "2": n2}, (*xy, 0), _fld(key), side=side)

def build():
    b = B()
    F = _fld
    # ---- MCU, clock, 3V3, CAN ----
    nets = {}
    for n, port, net, et, grp, rnd in LP.pin_rows():
        if grp == "power":
            nets[str(n)] = {"VBAT": "+3V3", "VDD": "+3V3", "VDDA": "+3V3", "VREF+": "+3V3", "VSS": "GND", "VSSA": "GND"}[port]
        else:
            nets[str(n)] = net  # None => no-connect for the five spare I/O
    b.add("U1", "MCU", "STM32G474VET6", "LQFP-100_14x14mm_P0.5mm", nets, (26.0, 107.5, 0), F("mcu",
          "0 stock at LCSC on 1 Nov 2026; consign. Only MCU on the module."), side="B")
    b.add("U22", "LDO", "AP2112K-3.3", "SOT-23-5",
          {"1": "+5V", "2": "GND", "3": "+5V", "4": "BP", "5": "+3V3"}, (40.5, 100.0, 0), F("ldo"), side="B")
    b.C("C40", "100n", "100n", "BP", "GND", (42.6, 100.0))
    b.C("C41", "10u", "10u", "+3V3", "GND", (40.5, 102.6), "C_0603")
    b.C("C42", "10u", "10u", "+5V", "GND", (43.2, 102.6), "C_0603")
    for i, xy in enumerate(((20.5, 96.5), (20.5, 109.5), (35.5, 96.5), (35.5, 109.5), (28.0, 94.2))):
        b.C(f"C4{3+i}", "100n", "100n", "+3V3", "GND", xy)
    b.add("Y1", "XTAL", "16MHz", "Crystal_3225", {"1": "OSC_IN", "2": "GND", "3": "OSC_OUT", "4": "GND"},
          (7.4, 96.2, 0), F("xtal", "Load capacitance not printed on the page; 15 pF caps are a starting point."), side="B")
    b.C("C48", "15p", "15p", "OSC_IN", "GND", (16.2, 107.2))
    b.C("C49", "15p", "15p", "OSC_OUT", "GND", (18.4, 107.2))
    b.R("R40", "10k", "10k", "+3V3", "NRST", (16.2, 100.5))
    b.C("C50", "100n", "100n", "NRST", "GND", (18.4, 100.5))
    b.R("R41", "100k", "100k", "BOOT0", "GND", (14.0, 100.5))
    b.add("U23", "CAN", "SN65HVD230DR", "SOIC-8_3.9x4.9mm_P1.27mm",
          {"1": "CAN_TX", "2": "GND", "3": "+3V3", "4": "CAN_RX", "5": None, "6": "CANL", "7": "CANH", "8": "CAN_RS"},
          (41.5, 98.5, 0), F("can", "Rs high = standby (off). Pulled up; drive low for high speed."), side="B")
    b.R("R42", "100k", "100k", "+3V3", "CAN_RS", (44.8, 92.0))
    b.C("C51", "100n", "100n", "+3V3", "GND", (44.8, 94.0))
    # ---- 716 stays off until FEEL_nSLEEP is driven. VM is +5 V now. ----
    b.R("R43", "100k", "100k", "FEEL_nSLEEP", "GND", (8.0, 40.0))
    # ---- 1220 driver + hardware stall clamp ----
    b.add("U21", "DRV8837", "DRV8837DSGR", "WSON-8_2x2_DRV8837",
          {"8": "+3V3", "1": "+5V", "6": "M1220_IN1", "5": "M1220_IN2", "7": "M1220_NS",
           "2": "MAIN_MOT_A", "3": "MAIN_MOT_B", "4": "M1220_SENSE", "9": "M1220_SENSE"},
          (40.5, 78.5, 0), F("drv", "1220 bridge. Chip GND is the sense node, about 0.7 V up at 120 mA."), side="B")
    b.C("C52", "100n", "100n", "+3V3", "GND", (43.2, 78.5))
    b.C("C53", "100n", "100n", "+5V", "GND", (43.2, 80.4))
    for i, x in enumerate((33.6, 35.6, 37.6, 39.6)):
        b.R(f"R4{4+i}", "22R", "22R", "M1220_SENSE", "GND", (x, 75.6))
    b.add("Q24", "NPN", "MMBT3904", "SOT-23", {"1": "NS_BASE", "2": "GND", "3": "M1220_NS"},
          (33.6, 78.5, 0), F("npn", "Pulls 1220 nSLEEP down when the sense divider reaches Vbe. Pin 1 base, 2 emitter, 3 collector."), side="B")
    b.R("R48", "10k", "10k", "M1220_SENSE", "NS_BASE", (31.2, 77.2))
    b.R("R49", "10k", "10k", "NS_BASE", "GND", (31.2, 79.2))
    b.R("R50", "1k", "1k", "M1220_nSLEEP", "M1220_NS", (31.2, 81.2))
    b.R("R51", "100k", "100k", "M1220_NS", "GND", (33.6, 81.2))
    # ---- shared VCSEL current sink, rail off by default ----
    b.add("Q15", "PMOS", "AO3401A", "SOT-23", {"1": "LSR_GATE", "2": "+5V", "3": "V_LASER"},
          (22.0, 86.0, 0), F("pmos", "Laser anode rail. Gate pulled to source, so the rail is off until LASER_EN."), side="B")
    b.add("Q14", "NMOS", "AO3400A", "SOT-23", {"1": "LASER_EN", "2": "GND", "3": "LSR_GATE"},
          (22.0, 88.6, 0), F("nmos"), side="B")
    b.R("R52", "100k", "100k", "LSR_GATE", "+5V", (24.4, 86.0))
    b.R("R53", "100k", "100k", "LASER_EN", "GND", (24.4, 88.6))
    b.C("C54", "10u", "10u", "V_LASER", "GND", (19.4, 86.0), "C_0603")
    b.add("Q16", "NPN", "MMBT3904", "SOT-23", {"1": "LBASE", "2": "LSENSE", "3": "KCOM"},
          (14.0, 88.6, 0), F("npn", "Shared sink for all 13 VCSELs. One laser on at a time is a firmware rule; the sink caps the sum."), side="B")
    b.R("R54", "100R", "100R", "LSENSE", "GND", (11.4, 88.6))
    b.R("R55", "10k", "10k", "+3V3", "LBASE", (11.4, 86.6))
    b.R("R56", "10k", "10k", "LBASE", "GND", (9.2, 86.6))
    b.R("R57", "10k", "10k", "LBASE", "GND", (9.2, 88.6))
    # 13 low-side switches. Sources meet at KCOM. 100k keeps every gate off.
    ring = LP.ring_positions()
    for i in range(13):
        col, row = i % 5, i // 5
        xy = (4.0 + col * 2.5, 60.5 + row * 3.3)
        net = "VCS_SCAN" if i == 12 else f"VCS{i+1}"
        b.add(f"Q{i+1}", "NMOS", "AO3400A", "SOT-23", {"1": net, "2": "KCOM", "3": f"LD{i+1}_K"},
              (xy[0], xy[1], 0), F("nmos"), side="B")
        b.R(f"R{60+i}", "100k", "100k", net, "GND", (xy[0], xy[1] + 1.45))
    for i, (x, y, ang) in enumerate(ring):
        bx, by = LP.board_of(x, y)
        if i % 2 == 0:
            k = i // 2 + 1  # LD1..LD12
            b.add(f"LD{k}", "VCSEL", "665nm", "LED_2835_VCSEL", {"1": "V_LASER", "2": f"LD{k}_K"},
                  (bx, by, ang), F("vcsel", "Pin 1 anode toward the footprint origin side. Notch is the cathode. Measure before trusting polarity."), side="F")
        else:
            k = i // 2 + 1  # RGB1..RGB12
            b.add(f"RGB{k}", "RGB", "SK6805-EC20", "LED_SK6805_EC20",
                  {"1": "GND", "2": "RGB1_DI" if k == 1 else f"L{k-1}", "3": "VLED", "4": None if k == 12 else f"L{k}"},
                  (bx, by, ang), F("rgb", "GRB order, 800 kHz. Power-on reset inside the LED keeps it dark."), side="F")
            b.C(f"C{60+k}", "100n", "100n", "VLED", "GND", (bx, by))
    # chain data, first DIN through the level shifter
    b.add("Q25", "NMOS", "AO3400A", "SOT-23", {"1": "+3V3", "2": "RGB_DIN", "3": "RGB_PAD"},
          (36.5, 86.0, 0), F("nmos", "Level shift: gate at 3.3 V, source is the GPIO, drain is the 5 V DIN."), side="B")
    b.R("R73", "4k7", "4k7", "RGB_PAD", "VLED", (36.5, 88.4))
    b.R("R74", "220R", "220R", "RGB_PAD", "RGB1_DI", (38.6, 88.4))
    # DOUT of one LED is the DIN of the next (same net). No series link on this short ring.
    b.add("Q17", "PMOS", "AO3401A", "SOT-23", {"1": "RGB_GATE", "2": "+5V", "3": "RGB_A"},
          (36.5, 82.5, 0), F("pmos", "RGB rail, off until RGB_EN. Two 22R in series are the brightness cap."), side="B")
    b.add("Q18", "NMOS", "AO3400A", "SOT-23", {"1": "RGB_EN", "2": "GND", "3": "RGB_GATE"},
          (38.8, 82.5, 0), F("nmos"), side="B")
    b.R("R75", "100k", "100k", "RGB_GATE", "+5V", (36.5, 84.4))
    b.R("R76", "100k", "100k", "RGB_EN", "GND", (38.8, 84.4))
    b.R("R77", "22R", "22R", "RGB_A", "RGB_B", (41.2, 82.5))
    b.R("R78", "22R", "22R", "RGB_B", "VLED", (43.4, 82.5))
    b.C("C73", "10u", "10u", "VLED", "GND", (43.4, 84.8), "C_0603")
    # scanner VCSEL, same sink, its own gate
    b.add("LD13", "VCSEL", "665nm", "LED_2835_VCSEL", {"1": "V_LASER", "2": "LD13_K"},
          (*LP.SCAN_BOARD, 90), F("vcsel", "Case scanner. Same shared sink as the ring. Position is [A] until case-v01 exists."), side="F")
    # violet module, its own supply MOSFET, not on the 5 mA sink
    b.add("Q19", "PMOS", "AO3401A", "SOT-23", {"1": "VIO_GATE", "2": "+5V", "3": "VIOLET"},
          (43.4, 70.5, 0), F("pmos", "Civillaser 405 nm, <55 mA, no TTL. Off until VIOLET_EN."), side="B")
    b.add("Q20", "NMOS", "AO3400A", "SOT-23", {"1": "VIOLET_EN", "2": "GND", "3": "VIO_GATE"},
          (43.4, 73.0, 0), F("nmos"), side="B")
    b.R("R79", "100k", "100k", "VIO_GATE", "+5V", (45.6, 70.5))
    b.R("R80", "100k", "100k", "VIOLET_EN", "GND", (45.6, 73.0))
    # Risley + mirror, unidirectional
    for ref, gate, sw, y in (("Q21", "RISLEY1", "RIS1", 64.0), ("Q22", "RISLEY2", "RIS2", 67.2), ("Q23", "MIRROR", "MIR", 61.0)):
        b.add(ref, "NMOS", "AO3400A", "SOT-23", {"1": gate, "2": "GND", "3": sw}, (43.4, y, 0),
              F("nmos", "Unidirectional PWM. No motor spec in the repo; assumed small coreless on +5 V."), side="B")
        b.R(f"R{90 + int(y)}", "100k", "100k", gate, "GND", (45.6, y))
    b.add("D40", "DIODE", "1N4148WS", "D_SOD-323", {"1": "+5V", "2": "RIS1"}, (46.7, 75.8, 0), F("diode"), side="B")
    b.add("D41", "DIODE", "1N4148WS", "D_SOD-323", {"1": "+5V", "2": "RIS2"}, (46.7, 78.4, 0), F("diode"), side="B")
    b.add("D42", "DIODE", "1N4148WS", "D_SOD-323", {"1": "+5V", "2": "MIR"}, (46.7, 81.0, 0), F("diode"), side="B")
    # ---- joystick v0.4 sockets and standoffs ----
    j2 = LP.js_board(9.75, 0); j3 = LP.js_board(-9.75, 0)
    b.add("J2", "P3", "HX-1x3", "PinSocket_1x03_P2.54", {"1": "SW_RIGHT", "2": "SW_DOWN", "3": "GND"},
          (*j2, 0), F("sock", "Mates with daughterboard J1. Pin 1 is the inner pin (toward the switch)."), side="F")
    b.add("J3", "P3", "HX-1x3", "PinSocket_1x03_P2.54", {"1": "SW_LEFT", "2": "SW_CENTER", "3": "SW_UP"},
          (*j3, 180), F("sock", "Mates with daughterboard J2. Placed at 180° so pin 1 is the inner pin."), side="F")
    for i, (lx, ly) in enumerate(((14.04, 3.73), (14.04, -3.73), (-14.04, 3.73), (-14.04, -3.73))):
        b.add(f"H1{i}", "M2", "M2", "Mount_M2_PTH", {"1": "GND"}, (*LP.js_board(lx, ly), 0),
              {"Note": "XHHD DTTZ3033 stud, nut under the board. Not a turnkey part."}, bom=False, side="F")
    for i, net in enumerate(("SW_UP", "SW_DOWN", "SW_LEFT", "SW_RIGHT", "SW_CENTER")):
        b.R(f"R{220+i}", "10k", "10k", "+3V3", net, (8.0 + i * 1.6, 26.2))
    # ---- hand-soldered pad rows (no LCSC connector; the mating part is not frozen) ----
    def pads(ref, n, nets, xy, rot=0, side="F"):
        b.add(ref, f"P{n}", ref, f"PadRow_1x{n:02d}", {str(i + 1): net for i, net in enumerate(nets)},
              (*xy, rot), {"Note": "Hand-soldered pads, not in the turnkey BOM."}, bom=False, side=side)
    pads("J4", 3, ["+5V", "GND", "+5V"], (3.4, 50.0), 90, "B")
    pads("J5", 3, ["CANH", "CANL", "GND"], (3.4, 58.5), 90, "B")
    pads("J6", 3, ["USB_DM_P", "USB_DP_P", "GND"], (3.4, 67.0), 90, "B")
    pads("J7", 3, ["UCPD_CC1", "UCPD_CC2", "+5V"], (3.4, 75.5), 90, "B")
    pads("J8", 3, ["SWDIO", "SWCLK", "GND"], (3.4, 84.0), 90, "B")
    pads("J17", 2, ["+5V", "MIR"], (3.4, 91.0), 90, "B")
    pads("J9", 3, ["NRST", "+3V3", "GND"], (48.0, 108.0), 90, "B")
    pads("J15", 2, ["VIOLET", "GND"], (48.0, 98.5), 90, "B")
    pads("J16", 4, ["+5V", "RIS1", "+5V", "RIS2"], (48.0, 89.5), 90, "B")
    pads("J12", 6, ["AUD_IN", "AUD_OUT", "MOT_VOICE_EN", "MIC_EN", "NTC", "BUS_PRESENT"], (48.0, 66.5), 90, "B")
    pads("J14", 8, ["TFT_SCK", "TFT_MOSI", "TFT_CS", "TFT_DC", "TFT_RST", "TFT_BL", "+3V3", "GND"], (48.0, 46.0), 90)
    pads("J11", 6, ["CV_OUT1", "CV_OUT2", "CV_IN", "GATE_OUT", "GND", "+3V3"], (3.4, 30.0), 90, "B")
    pads("J13", 11, ["QSPI_CLK", "QSPI_NCS", "QSPI_IO0", "QSPI_IO1", "QSPI_IO2", "QSPI_IO3", "LCD_RST", "LCD_TE", "LCD_PWR", "GND", "+3V3"],
         (24.0, 28.2))
    b.R("R95", "22R", "22R", "USB_DM", "USB_DM_P", (24.5, 112.4))
    b.R("R96", "22R", "22R", "USB_DP", "USB_DP_P", (26.5, 112.4))
    # series 1k on the two CV outputs (short-proof into a TS plug)
    # The MCU net is CV_OUTn; the pad sees it through 1k. Rework: the pads above used CV_OUT1 directly.
    # Leave them direct and add the 1k by splitting. Done below by renaming — pads already use CV_OUT1.
    # Insert the resistors by changing the pad nets. Handled here:
    b.out[[c["ref"] for c in b.out].index("J11")]["nets"]["1"] = "CV1_PAD"
    b.out[[c["ref"] for c in b.out].index("J11")]["nets"]["2"] = "CV2_PAD"
    b.R("R97", "1k", "1k", "CV_OUT1", "CV1_PAD", (6.2, 30.5))
    b.R("R98", "1k", "1k", "CV_OUT2", "CV2_PAD", (6.2, 32.2))
    # mechanical holes
    fx, fy = LP.board_of(*LP.CSTR["fm_xy"])
    ix, iy = LP.board_of(*LP.CSTR["idler_xy"][1])
    b.mech += [("H3", "Hole_NPTH_1.6", (fx, fy, 0), "F"),
               ("H4", "Hole_NPTH_1.8", (ix, iy, 0), "F"),
               ("S1", "Slot_FPC_v04", (LP.js_board(18.25, 0)[0], LP.js_board(18.25, 0)[1], 0), "F")]
    for i, (lx, ly) in enumerate(((22.50, 4.03), (22.50, -4.03), (-22.50, 4.03), (-22.50, -4.03))):
        b.mech.append((f"HS{i+1}", "Hole_NPTH_3.4", (*LP.js_board(lx, ly), 0), "F"))
    # Glued cradle: one round locating hole and one radial slot. Empty until the export lands.
    for h in LP.cradle_locating_holes():
        bx, by = LP.board_of(h["x"], h["y"])
        if h["slot"]:
            tag = f"{h['d']:.2f}x{h['slot']:.2f}".replace(".", "p")
            # local +X of the oval is the radius. Board y is down, so the frame angle flips.
            rot = 0.0 if h["ang"] is None else -h["ang"]
            b.mech.append((f"HP{h['i']+1}", f"Slot_NPTH_{tag}", (bx, by, rot), "F"))
        else:
            tag = f"{h['d']:.2f}".replace(".", "p")
            b.mech.append((f"HP{h['i']+1}", f"Hole_NPTH_{tag}", (bx, by, 0), "F"))
    return b

def attach_pins(comps, PINS):
    for c in comps:
        c["pins"] = PINS[c["sym"]]
