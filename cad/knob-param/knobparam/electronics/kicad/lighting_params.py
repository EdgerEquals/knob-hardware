"""Lighting / laser / motor parameters for main PCB v0.12. KiCad is generated from this file.

Geometry sources (read, not edited):
  origin/sub/assembly-v017 @ 00502746  optics lock + v0.17 holes (716 shaft Ø1.6 at 102°,
      compound-idler NPTH Ø1.8 at the 150° idler). cad_constraints.json was NOT regenerated
      on that branch; fm_xy / idler_xy / hall still match param-dev v0.16b and the v0.17
      note says the 716 stays at 102°. Re-check the cradle keep-out when v0.17 exports
      a new cad_constraints.json (knob OD grew to Ø41.65).
  origin/sub/joystick-v04 @ bce854b  REPORT.md "Main PCB, not edited" (carrier centre,
      1x3 sockets, M2 standoffs, Ø3.4 springs, FPC slot). sub/case-v01 is not on origin.

Board coordinates: panel top-left origin, x right, y down. Frame: motor at +X (0°), y up.
"""
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))

# ---- ring / lasers / motors (edit these) ----
RING_R = 19.0          # [A] mm, under the clear carrier, inboard of the Ø1.5 balls at r 19.54
N_VCSEL = 12           # [Ed] red 665 nm under the carrier
N_RGB = 12             # [Ed] addressable RGB, alternating with the VCSELs
PART_R = 1.70          # [A] mm, keep-out radius of one 2835 / 2020 body
LASER_MA = 4.5         # [A] mA setpoint (Vbe sink, 100R). Datasheet abs max IF 10 mA. Start near 5 mA.
LASER_MA_CEILING = 8.0 # [A] do not fit an emitter resistor under 68R (would push toward the 10 mA abs max)
RGB_RS = 44.0          # [A] ohm, two 22R in series. Caps a 5 V SK6805 chain near (5-3.5)/44 ≈ 34 mA
RGB_FULL_WHITE_A = 0.186  # [S] 12 x SK6805-EC20, 5 mA x 3 colours. A WS2812-class chain would be ~0.7 A.
STALL_A = 0.24         # [A] 1220 clamp: 4x 22R in parallel, 10k/10k onto a Vbe. Motor current is still assumed.
VIOLET_MA = 55         # [S] Civillaser module ceiling

# joystick v0.4 (bce854b REPORT)
JS_CENTRE = (25.25, 16.53)   # board mm
JS_PLACE_Y = 36.37

# scanner sits at the bottom end of this PCB. sub/case-v01 was not on the remote.
SCAN_BOARD = (8.0, 110.0)    # [A] re-check when the case round lands

CSTR = json.load(open(os.path.join(HERE, "cad_constraints.json")))
AX, AY = CSTR["axis_b"]

def board_of(frame_x, frame_y):
    return (AX + frame_x, AY - frame_y)

def cradle_locating_holes(cstr=None):
    """Glued cradle: one round NPTH and one slot along the radius. Empty until the export lands.

    Frame millimetres, motor at +x. Accepted exports:
      peg_xy + peg_d, with peg_slot (length of the second hole) and peg_ang (degrees), or
      cradle_pegs: a list of {xy, d, slot, ang}. The first hole is round. The second is the slot.
    """
    cstr = CSTR if cstr is None else cstr
    if "cradle_pegs" in cstr:
        holes = []
        for i, item in enumerate(cstr["cradle_pegs"]):
            if "xy" in item:
                x, y = item["xy"]
            else:
                x, y = item["x"], item["y"]
            d = float(item.get("d", item.get("dia", item.get("diameter"))))
            ang = item.get("ang", item.get("angle"))
            field = item.get("slot", i == 1)
            if isinstance(field, (int, float)) and not isinstance(field, bool):
                holes.append(_locating_hole(i, float(x), float(y), d, True, ang, field))
            else:
                holes.append(_locating_hole(i, float(x), float(y), d, bool(field), ang, item.get("slot_len")))
        return holes
    if "peg_xy" not in cstr or "peg_d" not in cstr:
        return []
    d = float(cstr["peg_d"])
    angs = list(cstr.get("peg_ang") or [])
    slot = cstr.get("peg_slot")
    holes = []
    for i, (x, y) in enumerate(cstr["peg_xy"]):
        ang = angs[i] if i < len(angs) else None
        holes.append(_locating_hole(i, float(x), float(y), d, i == 1, ang, slot if i == 1 else None))
    return holes

def _locating_hole(i, x, y, d, want_slot, ang, slot_len):
    ang = None if ang is None else float(ang)
    if not want_slot:
        return {"i": i, "x": x, "y": y, "d": d, "slot": None, "ang": ang}
    if isinstance(slot_len, (list, tuple)):
        slot_len = slot_len[i]
    if not isinstance(slot_len, (int, float)) or isinstance(slot_len, bool):
        raise ValueError(f"cradle locating hole {i + 1} is the slot and needs a length (peg_slot)")
    return {"i": i, "x": x, "y": y, "d": d, "slot": float(slot_len), "ang": ang}

def js_board(local_x, local_y):
    """Carrier-local (x right, y up the panel) → board mm. Matches joystick-param board_xy."""
    return (JS_CENTRE[0] + local_x, JS_CENTRE[1] - local_y)

def _arcs(flags):
    """flags[i] True = 0.1° step i is free. Return inclusive degree ranges."""
    arcs, s = [], None
    for i, ok in enumerate(flags):
        if ok and s is None: s = i
        if not ok and s is not None:
            arcs.append((s / 10.0, (i - 1) / 10.0)); s = None
    if s is not None: arcs.append((s / 10.0, (len(flags) - 1) / 10.0))
    # merge the wrap-around arc
    if len(arcs) >= 2 and arcs[0][0] == 0.0 and arcs[-1][1] > 359.0:
        arcs = [(arcs[-1][0], arcs[0][1] + 360.0)] + arcs[1:-1]
    return arcs

def ring_positions(r=RING_R, n=N_VCSEL + N_RGB, part_r=PART_R):
    """Evenly space `n` parts on the free arc at radius r. Skips the 1220 can, the 716 can,
    the Hall spoke and (if r is in it) the 124–137° carrier keep-out. Returns frame (x, y, deg)."""
    obs = [(CSTR["offset"], 0.0, 6.0 + 0.55, "1220"),
           (*CSTR["fm_xy"], 3.5 + 0.55, "716"),
           (*CSTR["enc_xy"], 4.2, "H2"), (*CSTR["fm_xy"], 2.2, "H3"),
           (*CSTR["idler_xy"][1], 2.2, "H4")]
    for i, h in enumerate(CSTR["hall"]):
        a = math.radians(h["ang"])
        obs.append((h["r"] * math.cos(a), h["r"] * math.sin(a), 3.4, f"H{i+1}"))
    free = []
    for k in range(3600):
        a = k / 10.0
        x, y = r * math.cos(math.radians(a)), r * math.sin(math.radians(a))
        bad = any(math.hypot(x - ox, y - oy) < rad + part_r for ox, oy, rad, _ in obs)
        if 18.0 <= r <= 20.5 and 124.0 <= a <= 137.0: bad = True
        free.append(not bad)
    samples = [k / 10.0 for k, ok in enumerate(free) if ok]
    if len(samples) < n * 5: raise RuntimeError(f"ring free arc too small for {n} parts at r {r}")
    # walk the free samples and drop a part every equal arc, but never closer than 3.5 mm
    step = len(samples) / n
    out, last = [], None
    for i in range(n):
        ang = samples[min(len(samples) - 1, int(i * step + step * 0.5))]
        x, y = r * math.cos(math.radians(ang)), r * math.sin(math.radians(ang))
        if last is not None and math.hypot(x - last[0], y - last[1]) < 3.5:
            # push forward along the free list until the chord clears
            k = min(len(samples) - 1, int(i * step + step * 0.5))
            while k < len(samples) - 1:
                k += 1
                ang = samples[k]
                x, y = r * math.cos(math.radians(ang)), r * math.sin(math.radians(ang))
                if math.hypot(x - last[0], y - last[1]) >= 3.5: break
        out.append((x, y, ang)); last = (x, y)
    # the closing gap back to the first part
    gaps = [math.hypot(out[i][0] - out[(i + 1) % n][0], out[i][1] - out[(i + 1) % n][1]) for i in range(n)]
    if min(gaps) < 3.4:
        raise RuntimeError(f"ring at r {r} min spacing {min(gaps):.2f} mm")
    return out

# ---- STM32G474VET6 LQFP100. Pin numbers from ST open pin data (CubeMX 6.18), gaw.ru table 2026-10-11.
# 86 I/O. "before" is the 62-pin list including SWD and the one violet MOSFET (design notes, assembly 00502746).
# This round adds the 19 lighting / Risley / scanner / mirror gates. Five I/O stay spare.
POWER_PINS = {6: "VBAT", 23: "VSS", 24: "VDD", 35: "VSSA", 36: "VREF+", 37: "VDDA",
              48: "VSS", 49: "VDD", 63: "VSS", 64: "VDD", 74: "VSS", 75: "VDD", 99: "VSS", 100: "VDD"}
# num: (port, net, etype, group, round)   round is "before" or "v012"
IO = {
    12: ("PF0", "OSC_IN", "passive", "clock", "before"),
    13: ("PF1", "OSC_OUT", "passive", "clock", "before"),
    14: ("NRST", "NRST", "passive", "reset", "before"),
    76: ("PA13", "SWDIO", "bidirectional", "swd", "before"),
    77: ("PA14", "SWCLK", "bidirectional", "swd", "before"),
    72: ("PA11", "USB_DM", "bidirectional", "usb", "before"),
    73: ("PA12", "USB_DP", "bidirectional", "usb", "before"),
    93: ("PB6", "UCPD_CC1", "bidirectional", "usb", "before"),
    91: ("PB4", "UCPD_CC2", "bidirectional", "usb", "before"),
    82: ("PD0", "CAN_RX", "input", "can", "before"),
    83: ("PD1", "CAN_TX", "output", "can", "before"),
    97: ("PE0", "CAN_RS", "output", "can", "before"),
    41: ("PE10", "QSPI_CLK", "bidirectional", "qspi", "before"),
    42: ("PE11", "QSPI_NCS", "output", "qspi", "before"),
    43: ("PE12", "QSPI_IO0", "bidirectional", "qspi", "before"),
    44: ("PE13", "QSPI_IO1", "bidirectional", "qspi", "before"),
    45: ("PE14", "QSPI_IO2", "bidirectional", "qspi", "before"),
    46: ("PE15", "QSPI_IO3", "bidirectional", "qspi", "before"),
    38: ("PE7", "LCD_RST", "output", "qspi", "before"),
    39: ("PE8", "LCD_TE", "input", "qspi", "before"),
    40: ("PE9", "LCD_PWR", "output", "qspi", "before"),
    90: ("PB3", "TFT_SCK", "output", "spi", "before"),
    92: ("PB5", "TFT_MOSI", "output", "spi", "before"),
    78: ("PA15", "TFT_CS", "output", "spi", "before"),
    80: ("PC11", "TFT_DC", "output", "spi", "before"),
    81: ("PC12", "TFT_RST", "output", "spi", "before"),
    84: ("PD2", "TFT_BL", "output", "spi", "before"),
    67: ("PC8", "I2C_SCL", "bidirectional", "hall", "before"),
    68: ("PC9", "I2C_SDA", "bidirectional", "hall", "before"),
    47: ("PB10", "HALL3D_INT", "input", "hall", "before"),
    34: ("PB2", "HALL_EN", "output", "hall", "before"),
    15: ("PC0", "HALL1", "input", "hall", "before"),
    16: ("PC1", "HALL2", "input", "hall", "before"),
    17: ("PC2", "HALL4", "input", "hall", "before"),
    18: ("PC3", "HALL5", "input", "hall", "before"),
    20: ("PA0", "ENC_A", "input", "enc", "before"),
    21: ("PA1", "ENC_B", "input", "enc", "before"),
    55: ("PD8", "SW_UP", "input", "joy", "before"),
    56: ("PD9", "SW_DOWN", "input", "joy", "before"),
    57: ("PD10", "SW_LEFT", "input", "joy", "before"),
    58: ("PD11", "SW_RIGHT", "input", "joy", "before"),
    59: ("PD12", "SW_CENTER", "input", "joy", "before"),
    22: ("PA2", "VBUS_DATA", "bidirectional", "link", "before"),
    65: ("PC6", "FEEL_IN1", "output", "feel716", "before"),
    66: ("PC7", "FEEL_IN2", "output", "feel716", "before"),
    60: ("PD13", "FEEL_nSLEEP", "output", "feel716", "before"),
    53: ("PB14", "M1220_IN1", "output", "m1220", "before"),
    54: ("PB15", "M1220_IN2", "output", "m1220", "before"),
    61: ("PD14", "M1220_nSLEEP", "output", "m1220", "before"),
    25: ("PA3", "M1220_SENSE", "passive", "m1220", "before"),
    98: ("PE1", "VIOLET_EN", "output", "violet", "before"),
    26: ("PA4", "CV_OUT1", "output", "cv", "before"),
    28: ("PA6", "CV_OUT2", "output", "cv", "before"),
    32: ("PB0", "CV_IN", "input", "cv", "before"),
    69: ("PA8", "GATE_OUT", "output", "cv", "before"),
    33: ("PB1", "AUD_IN", "input", "audio", "before"),
    27: ("PA5", "AUD_OUT", "output", "audio", "before"),
    62: ("PD15", "MOT_VOICE_EN", "output", "audio", "before"),
    5: ("PE6", "MIC_EN", "output", "audio", "before"),
    50: ("PB11", "NTC", "input", "sense", "before"),
    4: ("PE5", "BUS_PRESENT", "input", "sense", "before"),
    95: ("PB8", "BOOT0", "passive", "boot", "before"),
    # this round
    1: ("PE2", "LASER_EN", "output", "laser", "v012"),
    2: ("PE3", "RGB_EN", "output", "rgb", "v012"),
    3: ("PE4", "VCS_SCAN", "output", "laser", "v012"),
    10: ("PF9", "VCS1", "output", "laser", "v012"),
    11: ("PF10", "VCS2", "output", "laser", "v012"),
    19: ("PF2", "VCS3", "output", "laser", "v012"),
    30: ("PC4", "VCS4", "output", "laser", "v012"),
    31: ("PC5", "VCS5", "output", "laser", "v012"),
    51: ("PB12", "VCS6", "output", "laser", "v012"),
    52: ("PB13", "VCS7", "output", "laser", "v012"),
    70: ("PA9", "VCS8", "output", "laser", "v012"),
    71: ("PA10", "VCS9", "output", "laser", "v012"),
    85: ("PD3", "VCS10", "output", "laser", "v012"),
    86: ("PD4", "VCS11", "output", "laser", "v012"),
    87: ("PD5", "VCS12", "output", "laser", "v012"),
    79: ("PC10", "RGB_DIN", "output", "rgb", "v012"),
    96: ("PB9", "RISLEY1", "output", "risley", "v012"),
    94: ("PB7", "RISLEY2", "output", "risley", "v012"),
    29: ("PA7", "MIRROR", "output", "scan", "v012"),
}
SPARE = {7: "PC13", 8: "PC14", 9: "PC15", 88: "PD6", 89: "PD7"}  # PC14/PC15 kept for a future LSE

def pin_rows():
    rows = []
    for n in range(1, 101):
        if n in POWER_PINS:
            net = {"VBAT": "+3V3", "VDD": "+3V3", "VDDA": "+3V3", "VREF+": "+3V3", "VSS": "GND", "VSSA": "GND"}[POWER_PINS[n]]
            rows.append((n, POWER_PINS[n], net, "power", "power", "before"))
        elif n in IO:
            port, net, et, grp, rnd = IO[n]
            rows.append((n, port, net, et, grp, rnd))
        else:
            rows.append((n, SPARE[n], None, "passive", "spare", "spare"))
    return rows

def counts():
    b = sum(1 for n in IO.values() if n[4] == "before")
    v = sum(1 for n in IO.values() if n[4] == "v012")
    return b, v, len(SPARE), b + v + len(SPARE)

# LCSC stock checked against the product pages on 2026-11-01. STM32G474VET6 (C431632) was 0.
PARTS = {
    "mcu": ("STM32G474VET6", "ST", "C431632", 0),
    "ldo": ("AP2112K-3.3TRG1", "Diodes", "C51118", 3770),
    "can": ("SN65HVD230DR", "TI", "C12084", 58856),
    "drv": ("DRV8837DSGR", "TI", "C39159", 124305),
    "nmos": ("AO3400A", "Alpha & Omega", "C20917", 613610),
    "pmos": ("AO3401A", "Alpha & Omega", "C15127", 1319660),
    "npn": ("MMBT3904", "Jiangsu Changjing", "C20526", 2186100),
    "diode": ("1N4148WS", "MDD", "C2128", 429400),
    "vcsel": ("JNJ-V-2835CW-665003-S-D1", "JNJOPTO", "C42375664", 472),
    "rgb": ("SK6805-EC20", "OPSCO", "C2890036", 11130),
    "xtal": ("X322516MLB4SI", "YXC", "C13738", 259940),
    "sock": ("HX PM2.54-1x3P ZC H11", "hanxia", "C41427518", 595),
    "100n": ("CL05B104KO5NNNC", "Samsung", "C1525", 5096000),
    "10u": ("CL10A106KP8NNNC", "Samsung", "C19702", 2337040),
    "15p": ("0402CG150J500NT", "FH", "C1548", 597500),
    "10k": ("RC0402FR-0710KL", "YAGEO", "C60490", 1829400),
    "100k": ("0402WGF1003TCE", "UNI-ROYAL", "C25741", 1418500),
    "4k7": ("0402WGF4701TCE", "UNI-ROYAL", "C25900", 7170800),
    "1k": ("0402WGF1001TCE", "UNI-ROYAL", "C11702", 9327100),
    "220R": ("0402WGF2200TCE", "UNI-ROYAL", "C25091", 1214500),
    "100R": ("0603WAF1000T5E", "UNI-ROYAL", "C22775", 940000),
    "22R": ("0402WGF220KTCE", "UNI-ROYAL", "C25101", 3563000),
    "0R": ("0402WGF0000TCE", "UNI-ROYAL", "C17168", 2663600),
}

def power_budget():
    """mA on the +5 V input (3V3 LDO load is included; it comes from +5 V)."""
    idle = [("MCU, HSE, loads off [A]", 6.0), ("AP2112 Iq [S]", 0.055),
            ("CAN transceiver standby [S, order]", 0.4), ("pull-ups [A]", 1.5)]
    typ = [("MCU active [A]", 12), ("Hall row [A]", 6), ("encoder LED + photo [S/A]", 11),
           ("top AMOLED, modest [A]", 25), ("bottom TFT, modest [A]", 20),
           ("dial screen + CH32 over the rod [A]", 15), ("one 665 nm VCSEL", LASER_MA),
           ("RGB dim, under the cap [A]", 8), ("LDO and the rest [A]", 9)]
    peak = [("MCU [A]", 20), ("three screens, bright [A]", 125), ("Hall + encoder", 16),
            ("one VCSEL", LASER_MA), ("RGB at the series-resistor cap", 34),
            ("violet module [S]", VIOLET_MA), ("1220 moving, not stalled [A]", 120),
            ("716 moving [A]", 60), ("two Risley motors [A]", 80), ("rails and LDO [A]", 15)]
    ceil = [("1220 held at the hardware stall clamp", STALL_A * 1000), ("RGB cap", 34),
            ("violet [S]", VIOLET_MA), ("716 + two Risley + mirror, all spinning [A]", 60 + 80 + 40),
            ("screens bright + MCU + Hall", 125 + 20 + 16), ("one VCSEL", LASER_MA)]
    def s(rows): return rows, round(sum(v for _, v in rows), 1)
    return {"idle": s(idle), "typical": s(typ), "peak": s(peak), "ceiling": s(ceil)}

def write_reports(dirpath):
    os.makedirs(dirpath, exist_ok=True)
    b, v, sp, total = counts()
    assert b == 62 and total == 86, (b, v, sp, total)
    rows = pin_rows()
    p = os.path.join(dirpath, "PINMAP.md")
    with open(p, "w") as f:
        f.write("# STM32G474VET6 pin map (main PCB v0.12)\n\n")
        f.write("LQFP100, 86 I/O. The \"before\" column is the 62-pin list from the 1 Nov 2026 MCU note "
                "(including SWD and the one violet supply MOSFET). This round adds 19 gates. "
                f"**{sp} I/O spare** after that (PC13, PC14, PC15, PD6, PD7). "
                "PC14/PC15 are left for a later 32 kHz crystal. PC13 is the RTC pin; do not load it.\n\n")
        f.write("QSPI bank 1 is the top-screen AMOLED (DO0164, connector is pads until the folded FPC is frozen). "
                "The bottom 2.0\" TFT is SPI (one QSPI peripheral). The dial-screen QSPI stays on the CH32V003; "
                "the G4 only has the single data-over-power line (`VBUS_DATA` on LPUART1_TX, PA2).\n\n")
        f.write("Firmware: only one of the 13 VCSEL gates (VCS1–VCS12 and VCS_SCAN) may be high at a time. "
                "The shared sink still limits the sum if two are on. `LASER_EN` must be high as well; it powers "
                "the anode rail and is pulled off. RGB, violet, 1220, 716, Risley and the mirror motor are each "
                "pulled off and stay off until firmware turns them on.\n\n")
        f.write("| Pin | Port | Net | Group | Round |\n|---|---|---|---|---|\n")
        for n, port, net, et, grp, rnd in rows:
            f.write(f"| {n} | {port} | {net or '— spare'} | {grp} | {rnd} |\n")
        f.write(f"\nBefore: **{b}**. This round: **{v}**. Spare: **{sp}**. I/O total: **{total}**.\n\n")
        f.write("## Open, re-check when the other rounds land\n\n")
        f.write("- `sub/case-v01` is not on the remote. The scanner VCSEL is at board (8, 110), the bottom end. Move it when the case scan position exists.\n")
        f.write("- The base cradle is glued to the PCB front. Locating features are two NPTH holes, one round and one slot along the radius, not screws. "
                "Assembly `fee6c60` still exports `cad_constraints.json` as v0.16b and does not list `peg_xy` / `peg_d` / `peg_slot` yet, so the holes are not drilled. "
                "They are read from that file when the keys appear. Cradle keep-out is still v0.16b. The Fab circle is Ø41.65 from `00502746`. "
                "The ring gear moving inward will change both.\n")
        f.write("- The cradle later grows into a glued stiffener over as much of the PCB front as it can. "
                "New electronics are on the back. Tall front-side parts that a full-front plate cannot cover:\n")
        f.write("  - J2 and J3, 11 mm joystick sockets, with the four M2 studs H10–H13, clustered at board y 12–21. They have to stay there to mate with the daughterboard.\n")
        f.write("  - M1, the 1220, body in the cradle bore at (36.0, 52.9). H1, the brass tube, at the dial axis. H2, the F682ZZ flange, at (25.25, 68.15).\n")
        f.write("  - The 24 ring emitters are only 0.8 mm tall, but they have to stay in the clear-carrier window. A solid plate over them blocks the beams.\n")
        f.write("  - LD13, the scanner VCSEL, is 0.8 mm at (8, 110). A stiffener over that corner blocks the scan.\n")
        f.write("  - Hall sensors U11–U15 are on the front and under 1.2 mm, already in the cradle Hall slot.\n")
        f.write("  - J13 and J14 are flat pad rows on the front (y 28.2 and the right edge at y 46). They are not tall. A plate glued over them covers the solder joints. A connector body fitted later would stand proud.\n")
        f.write("- Joystick holes are from `bce854b` REPORT.md, not from a regenerated main-board file (that agent did not edit this PCB).\n")
        f.write("- Ring centres at the bottom (about y 70.5–70.9) cross the 2.0\" TFT outline (y 70.5) by about 2 mm. That is the inactive top border of the TFT in the panel notes. Confirm before the glass is ordered.\n")
        f.write("- No Risley or mirror motor is specified in the repo. Drivers are unidirectional AO3400A low-side PWM from +5 V. Reverse the leads if the prism must spin the other way. A geared 1220-class part will not fit; these assume a small coreless, stall under 300 mA.\n")
        f.write("- STM32G474VET6 LCSC C431632 had 0 stock on 1 Nov 2026. No other LQFP100 VET6 bin was found. PCBWay has to consign it.\n")
        f.write("- Dial-screen QSPI is not on this MCU. Top screen QSPI and the bottom TFT SPI come out to pad rows, because the FPC drawings are still open.\n")
    q = os.path.join(dirpath, "POWER.md")
    bud = power_budget()
    with open(q, "w") as f:
        f.write("# Power budget (main PCB v0.12)\n\n")
        f.write("Currents are on the +5 V input. The 3.3 V rail is an AP2112 from that 5 V. "
                "The USB-PD / Eurorack OR-ing front end is not on this board; +5 V comes in on J4. "
                "Motor currents are still assumptions. Every load below is switchable and off until firmware asks.\n\n")
        labels = {"idle": "Idle, loads off", "typical": "Typical", "peak": "Peak (run, not stall)",
                  "ceiling": "Hardware ceiling (1220 clamped, RGB capped, show running)"}
        for key in ("idle", "typical", "peak", "ceiling"):
            rows, tot = bud[key]
            f.write(f"## {labels[key]}: {tot:.0f} mA\n\n")
            f.write("| Item | mA |\n|---|---|\n")
            for name, ma in rows: f.write(f"| {name} | {ma:.1f} |\n")
            f.write(f"| **Total** | **{tot:.1f}** |\n\n")
        f.write("The 0.7 A figure is a WS2812-class chain at full white. The fitted SK6805-EC20 is 5 mA per colour "
                f"({RGB_FULL_WHITE_A*1000:.0f} mA for 12 at full white). Two 22 Ω resistors in series on the LED rail "
                "collapse that to about 34 mA, because the LEDs need at least 3.5 V. "
                f"The 1220 clamp is about {STALL_A:.2f} A: four 22 Ω resistors in parallel under the bridge, divided by 10k/10k onto a transistor base. "
                "Trip current is about 1.3 V / Rparallel. Add parallel 22 Ω resistors to raise it. "
                "At the assumed 120 mA run current the sense stack drops about 0.7 V.\n\n")
        f.write("Laser setpoint is about "
                f"{LASER_MA:.1f} mA (100 Ω emitter resistor, base near 1.10 V). "
                "JNJOPTO lists 4 mW minimum / 6 mW typical at 10 mA and a 4 mA threshold, and no curve, "
                "so the first articles have to be measured and the 100 Ω raised if the beam is over 1 mW. "
                f"Do not fit less than ~68 Ω ({LASER_MA_CEILING:.0f} mA order); the absolute maximum is 10 mA. "
                "The datasheet on LCSC is filed under both 665003 and 665005; confirm the reel.\n")
    return p, q

def preview_png(path):
    """Placement preview in board millimetres (y down). Not a copper plot."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(5.2, 11))
    ax.set_aspect("equal"); ax.set_xlim(0, 50.5); ax.set_ylim(118, 10)
    ax.add_patch(plt.Rectangle((0.75, 10.5), 49, 107.5, fill=False, lw=0.8, color="#222"))
    ax.add_patch(plt.Circle((AX, AY), RING_R, fill=False, ls="--", color="#c04040", lw=0.6))
    for i, (x, y, ang) in enumerate(ring_positions()):
        bx, by = board_of(x, y)
        ax.add_patch(plt.Circle((bx, by), 1.15, color="#c04040" if i % 2 == 0 else "#2060c0"))
    ax.add_patch(plt.Circle(SCAN_BOARD, 1.3, color="#c04040"))
    ax.plot(*JS_CENTRE, "+", color="#888")
    for lx, ly in ((9.75, 0), (-9.75, 0)):
        ax.plot(*js_board(lx, ly), "s", color="#222", ms=4)
    for lx in (14.04, -14.04):
        for ly in (3.73, -3.73):
            ax.plot(*js_board(lx, ly), "o", color="#222", ms=3)
    fx, fy = board_of(*CSTR["fm_xy"]); ax.plot(fx, fy, "k+")
    ix, iy = board_of(*CSTR["idler_xy"][1]); ax.plot(ix, iy, "k+")
    ax.set_title("v0.12 placement preview (red VCSEL, blue RGB)")
    fig.savefig(path, dpi=130, bbox_inches="tight"); plt.close()

if __name__ == "__main__":
    b, v, sp, total = counts()
    print(f"pins before {b}  this round {v}  spare {sp}  total {total}")
    pts = ring_positions()
    print(f"ring {len(pts)} at r {RING_R}, first angle {pts[0][2]:.1f}, last {pts[-1][2]:.1f}")
    write_reports("/tmp/lighting-reports")
