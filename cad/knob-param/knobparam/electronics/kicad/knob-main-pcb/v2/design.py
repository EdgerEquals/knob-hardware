"""Main board v2 (knob model v0.52, 8 Nov 2026): the netlist, in one place. Pure Python (no KiCad), the same shape as the jack
power board's design.py, so the board generator (step 3, next) builds the schematic and the board from it.

Where it comes from:
- Architecture Q33 = A (docs/architecture-fresh-look-2026-11-07.md): STM32H743VIT6, the joystick screen on its quad port, no flash.
- Circuit: docs/main-board-circuit-2026-11-07.md (part 1, the ring lights Q35/Q36, the rod link Q43) and the noise decisions
  Q38-Q43 (docs/noise-sweep-2026-11-08.md). Plan: docs/img/main-board-plan.png [Ed 8 Nov 19:10 "Y"].
- MCU pins: ../pinmap/h743-lqfp100-simple.json (tools/main_board_pinmap.py on ST's pin data; 61 nets, 21 spare). Pin names for the
  symbol: h743vit6_lqfp100_pins.json, derived from STM32_open_pin_data (BSD-3-Clause, (c) 2020 STMicroelectronics).
Tags: [S] read in a datasheet or our docs, [A] my choice or a standard value, [C] to check, [Ed] Danny's decision.

Each part: ref, value, footprint (KiCad lib:name, "footprints:<name>" for the repo's ../../footprints.pretty, or "mb:<name>" for this
board's own, drawn by the generator), pins {pin number: net}, block (for the floorplan zones of the plan picture), face ("F" toward the
panel / "B" toward the back cover), LCSC / MPN where chosen, dnp, and a note. Nets in CAPS; the MCU's nets keep the pin map's names.
A net that ends at a resistor in front of an MCU pin gets "_L" (line side), e.g. HALL1_L -> 100R -> HALL1 (the pin)."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
PINMAP = json.load(open(os.path.join(HERE, "..", "pinmap", "h743-lqfp100-simple.json")))
MCU_PINS = {int(k): v for k, v in json.load(open(os.path.join(HERE, "h743vit6_lqfp100_pins.json")))["pins"].items()}

PARTS = []
_count = {}


def _ref(prefix):
    _count[prefix] = _count.get(prefix, 0) + 1
    return f"{prefix}{_count[prefix]}"


def part(prefix, value, fp, pins, block, face="B", lcsc="", mpn="", note="", names=None, ref=None, dnp=False):
    r = ref or _ref(prefix)
    if ref and ref[len(prefix):].isdigit():   # a fixed ref takes its number out of the count
        _count[prefix] = max(_count.get(prefix, 0), int(ref[len(prefix):]))
    PARTS.append(dict(ref=r, value=value, fp=fp, pins={str(k): v for k, v in pins.items()}, block=block, face=face, lcsc=lcsc,
                      mpn=mpn, note=note, names={str(k): v for k, v in (names or {}).items()}, dnp=dnp))
    return r


_SIZE = {"0201": "R_0201_0603Metric", "0402": "R_0402_1005Metric", "0603": "R_0603_1608Metric", "0805": "R_0805_2012Metric"}


def R(val, a, b, block, size="0402", note="", face="B", dnp=False):
    return part("R", val, "Resistor_SMD:" + _SIZE[size], {1: a, 2: b}, block, face=face, note=note, dnp=dnp)


def C(val, a, b, block, size="0402", note="", face="B", dnp=False):
    return part("C", val, "Capacitor_SMD:" + _SIZE[size].replace("R_", "C_"), {1: a, 2: b}, block, face=face, note=note, dnp=dnp)


def adc_rc(line, pin, block, face="B", note=""):
    """100R + 1 nF C0G at an ADC pin [A, main-board circuit doc]: keeps the ADC's sampling kicks off the line; corner 1.6 MHz."""
    R("100R", line, pin, block, face=face, note=note)
    C("1nF C0G", pin, "GND", block, face=face)


def mcu_nets():
    """LQFP100 position -> net: the pin map's 61 signals plus the power, reset, boot and reference pins [S ST pin data, AN4938]."""
    m = {v["position"]: n for n, v in PINMAP["nets"].items()}
    for pos, (name, typ) in MCU_PINS.items():
        if typ == "I/O":
            continue
        m[pos] = {"VDD": "3V3", "VSS": "GND", "VSSA": "GND", "VDDA": "VDDA", "VREF+": "VREFP", "VCAP": "VCAP", "VBAT": "3V3",
                  "NRST": "NRST", "BOOT0": "BOOT0"}[name]
    m = {p: n for p, n in m.items() if n not in ("RISLEY1", "RISLEY2")}   # reserved for later, no track [A]
    return {p: m.get(p) for p in sorted(MCU_PINS)}


# --------------------------------------------------------------------------------------------------------------------------------
# board L (power) and board R (screen + CAN) bottom headers: 2 x 11 at 1.27 [S layout v4: R 8 SMT + 14 THT, L 22 THT]. Pin order [A]:
# set again with the vertical boards' own layouts. Currents [A, power-tree Q38]: 15 V up to 0.9 A, 5 V down up to 1.8 A, 3.3 V
# 0.5 A; about 1 A a pin [C: the header's rating], so 3 / 4 / 3 pins and ten grounds spread between them.
HDR_L = ["VSYS", "GND", "VSYS", "GND", "VSYS", "GND", "5V", "GND", "5V", "5V", "5V", "GND", "3V3", "GND", "3V3", "3V3", "GND",
         "5V_EN", "GND", "JOY_LADDER_L", "GND", "GND"]
# R: the screen's quad port with a ground beside the clock and every data line (the same rule as R's 13 top pins), then CAN
HDR_R = ["GND", "QSPI_CLK_R", "GND", "QSPI_NCS_R", "QSPI_IO0_R", "GND", "QSPI_IO1_R", "QSPI_IO2_R", "GND", "QSPI_IO3_R", "JOY_RST",
         "JOY_TE", "JOY_PWR_EN", "GND", "CAN_TX", "CAN_RX", "CAN_STBY", "GND", "5V", "3V3", "GND", "GND"]
# link flex, main-board end: pad k = the jack lower board's J6 pin k (the flex keeps each contact at the same panel x, make_flex.py)
FLEX = ["SCK_L", "GND", "MOSI_L", "CS_DAC", "CS_OLED", "OLED_DC", "OLED_RES", "I2C_SCL", "I2C_SDA", "IO_INT", "MIDI_TX", "GND",
        "USB_DP", "USB_DM", "GND", "CV_IN1_L", "CV_IN2_L", "CV_IN3_L", "GND", "AUDIO_OUT", "GND", "AUDIO_IN_L", "GND", "AGND_SENSE_L", "GND"]
RING_N = 12   # SK6812MINI-E on the thrust pitch, every 30 deg, turned along the ring [Ed 8 Nov 19:37 Q44 = A; was 24 at 13:54]


def build():
    PARTS.clear(); _count.clear()
    # ------------------------------------------------------------------------------------------------------- connectors
    part("J", "link flex pads", "footprints:LinkFlex_MainBoard_Pads_25x0.3", {i + 1: n for i, n in enumerate(FLEX)}, "link", face="F",
         note="the flex's solder end, hot-bar or hand [Q29/Q30]; pin 24 = the jack unit's quiet ground, read as AGND_SENSE [Q41]",
         ref="J1")
    part("J", "board L header 2x11 1.27 THT", "mb:VBoard_L_Header_2x11_P1.27_THT", {i + 1: n for i, n in enumerate(HDR_L)}, "headers",
         face="F", note="vertical board L (power): 15 V up, 5 V and 3.3 V down, 5V_EN, the switch ladder [A order]", ref="J2")
    part("J", "board R header 2x11 1.27 hybrid", "mb:VBoard_R_Header_2x11_P1.27_Hybrid", {i + 1: n for i, n in enumerate(HDR_R)},
         "headers", face="F", note="vertical board R: the screen's quad port, CAN to its transceiver [A order]; 8 SMT legs over the "
         "encoder sensor, 14 THT [S model v0.52 vb_hdr]", ref="J3")
    part("J", "TC2030-IDC-NL", "Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical",
         {1: "3V3", 2: "SWDIO", 3: "NRST", 4: "SWCLK", 5: "GND", 6: "SWO"}, "debug", face="F",
         note="pads only, nothing fitted; cable TC2030-CTX-NL [S Tag-Connect]", ref="J4",
         names={1: "VCC", 2: "SWDIO", 3: "nRESET", 4: "SWCLK", 5: "GND", 6: "SWO"})
    part("J", "cover board pads", "mb:Pads_1x6_P1.27_SMD", {1: "COVER_TX", 2: "COVER_RX", 3: "COVER_EN", 4: "3V3", 5: "5V", 6: "GND"},
         "cover", note="the later back-screen board (Q33 = A): pads only [A]", ref="J5")
    # the two brass posts from the jack unit, soldered at both ends [Ed 4 Nov 22:52]: GND (left ear) and VSYS = 15 V after the eFuse
    part("MP", "post GND", "mb:Post_Pin_1.0", {1: "GND"}, "power", note="Ø1.0 pin of the Ø2 post, plated Ø1.15, Ø1.6 pad [Q24, as the "
         "jack power board's end; C the main-board end]", ref="MP1")
    part("MP", "post VSYS", "mb:Post_Pin_1.0", {1: "VSYS"}, "power", note="15 V [Q38: straight up to board L]", ref="MP2")
    # rod clamp (the dial's 5 V + data on the rod, the tube the return) and the 1220's tabs: hand-fitted, as v0.11
    part("H", "TubeRodClamp_M1.6", "footprints:TubeRodClamp_Main_M1.6", {1: "GND", 2: "ROD"}, "rod", face="F",
         note="tube = ground, rod = 5 V + data [Q43]", ref="H1")
    part("M", "1220 coreless planetary, 6 V (hand-solder)", "footprints:Motor_1220_Tabs_Relief", {1: "MOT_A", 2: "MOT_B"}, "motor",
         face="F", note="6 V version [Ed 8 Nov 12:38]; run from 5 V [Q34]", ref="M1")

    # ------------------------------------------------------------------------------------------------------- H743 core
    part("U", "STM32H743VIT6", "Package_QFP:LQFP-100_14x14mm_P0.5mm", mcu_nets(), "mcu", face="F", lcsc="C114409",
         mpn="STM32H743VIT6", note="under the joystick (layout v4); pins from the pin map", ref="U1",
         names={p: n for p, (n, t) in MCU_PINS.items()})
    for _ in range(5):
        C("100nF", "3V3", "GND", "mcu", face="F", note="one at each VDD pin [S AN4938 2.2]")
    C("10uF", "3V3", "GND", "mcu", size="0603", face="F", note="package bulk (4.7 uF min) [S AN4938 7.4]")
    C("2.2uF", "VCAP", "GND", "mcu", size="0603", face="F", note="ESR < 100 mohm, VCAP1 and VCAP2 tied [S AN4938 fig 18]")
    C("2.2uF", "VCAP", "GND", "mcu", size="0603", face="F")
    part("FB", "FCM1608KF-601T03", "Inductor_SMD:L_0603_1608Metric", {1: "3V3", 2: "VDDA"}, "mcu", face="F", lcsc="C141723",
         mpn="FCM1608KF-601T03", note="600R at 100 MHz, the bead AN4938 table 9 names [S]")
    C("1uF", "VDDA", "GND", "mcu", face="F"); C("100nF", "VDDA", "GND", "mcu", face="F")
    C("100nF", "3V3", "GND", "mcu", face="F", note="VBAT tied to VDD (no battery) [S AN4938 table 9]")
    C("100nF", "NRST", "GND", "mcu", face="F", note="[S AN4938 fig 18]")
    R("10k", "BOOT0", "GND", "mcu", face="F", note="[S AN4938 table 9]")
    part("JP", "BOOT0 to 3V3 (bridge to start the ROM bootloader)", "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
         {1: "BOOT0", 2: "3V3"}, "mcu", face="F", note="[A]")
    part("Y", "25MHz 12pF", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", {1: "HSE_IN", 2: "GND", 3: "HSE_OUT", 4: "GND"}, "mcu", face="F",
         lcsc="C9006", mpn="X322525MOB4SI", note="25 / 5 x 192 / 2 = 480 MHz [A]; [C] trim the 15 pF on the first boards",
         names={1: "XIN", 2: "GND", 3: "XOUT", 4: "GND"})
    C("15pF C0G", "HSE_IN", "GND", "mcu", face="F"); C("15pF C0G", "HSE_OUT", "GND", "mcu", face="F")
    # VREF+ = TI REF3430 3.0 V [Ed 8 Nov Q40 = A]; the ADC and DAC span 0-3.0 V
    part("U", "REF3430IDBVR", "Package_TO_SOT_SMD:SOT-23-6", {1: "GND", 2: "GND", 3: "3V3", 4: "3V3", 5: "VREFP", 6: "VREFP"}, "adc",
         lcsc="C2156866", mpn="REF3430IDBVR", note="EN tied to IN (on >= 1.6 V, never above IN); output stable 0.1-10 uF [S TI REF34]",
         names={1: "GND_F", 2: "GND_S", 3: "EN", 4: "IN", 5: "OUT_S", 6: "OUT_F"})
    C("1uF", "3V3", "GND", "adc", note="REF3430 input: 1-10 uF + 100 nF [S]"); C("100nF", "3V3", "GND", "adc")
    C("1uF", "VREFP", "GND", "adc", note="1.1 uF in all, inside 0.1-10 uF [S]"); C("100nF", "VREFP", "GND", "adc")

    # ------------------------------------------------------------------------------------------------------- the link flex's lines
    R("33R", "LINK_SCK", "SCK_L", "link", face="F", note="[A] edges for the 25-way flex"); R("33R", "LINK_MOSI", "MOSI_L", "link", face="F")
    for k in (1, 2, 3):
        adc_rc(f"CV_IN{k}_L", f"CV_IN{k}", "adc", note="scaled on the jack board [S]")
    adc_rc("AUDIO_IN_L", "AUDIO_IN", "adc")
    adc_rc("AGND_SENSE_L", "AGND_SENSE", "adc", note="[Q41]: sampled by ADC2 with ADC1's CV / audio, subtracted")
    R("1M", "AGND_SENSE_L", "GND", "adc", note="reads 0 with the flex out [A]")
    R("4.7k", "3V3", "I2C_SCL", "adc", dnp=True, note="not fitted: the pull-ups are on the jack board [S]")
    R("4.7k", "3V3", "I2C_SDA", "adc", dnp=True, note="not fitted")
    # USB D+ / D- go straight to PA12 / PA11 (ESD at the USB-C, internal pull-up) [S]; MIDI_TX, IO_INT, AUDIO_OUT straight

    # ------------------------------------------------------------------------------------------------------- the screen (board R)
    for n in ("CLK", "NCS", "IO0", "IO1", "IO2", "IO3"):
        R("22R", f"JOY_QSPI_{n}", f"QSPI_{n}_R", "screen", face="F", note="[A] at the H743")
    adc_rc("JOY_LADDER_L", "JOY_LADDER", "adc", note="the top board's switch ladder, down board L")

    # ------------------------------------------------------------------------------------------------------- Halls (as v0.11)
    # four TMAG5253 linear Halls into ADC1, the middle one a TMAG5273 3D Hall on I2C [S v0.11 design.py]; 100 nF at each
    for k in (1, 2, 4, 5):
        part("U", "TMAG5253BA3IQDMRR", "footprints:X2SON-4_TMAG5253", {1: "3V3", 2: "GND", 3: "HALL_EN", 4: f"HALL{k}_L", 5: "GND"},
             "halls", face="F", lcsc="C22401868", mpn="TMAG5253BA3IQDMRR", note=f"Hall row {k}/5 (linear)",
             names={1: "VCC", 2: "GND", 3: "EN", 4: "OUT", 5: "EP"})
        C("100nF", "3V3", "GND", "halls")
        adc_rc(f"HALL{k}_L", f"HALL{k}", "adc")
    part("U", "TMAG5273A2QDBVR", "footprints:SOT-23-6_TMAG5273_Tight",
         {4: "3V3", 2: "GND", 3: "GND", 1: "I2C_SCL", 6: "I2C_SDA", 5: "HALL3D_INT"}, "halls", face="F", lcsc="C3715882",
         mpn="TMAG5273A2QDBVR", note="Hall row 3/5 (3D, I2C; A2 +-133 mT)", names={1: "SCL", 2: "GND", 3: "TEST", 4: "VCC", 5: "INT", 6: "SDA"})
    C("100nF", "3V3", "GND", "halls")
    R("10k", "3V3", "HALL3D_INT", "halls")

    # ------------------------------------------------------------------------------------------------------- encoder (as v0.11)
    # Q27 [Ed 6 Nov 19:42]: no feel stage, so the EE-SX1321 sits straight on the back (no riser board) [S model v0.52 enc_riser False]
    # pins (datasheet p3): 1 anode, 2 + 3 cathode, 4 E2, 5 E1, 6 collector [S v0.11]
    part("U", "EE-SX1321", "footprints:Omron_EE-SX1321", {1: "ENC_LED", 2: "GND", 3: "GND", 6: "3V3", 5: "ENC_A_L", 4: "ENC_B_L"},
         "encoder", lcsc="C469128", mpn="EE-SX1321", note="slot tangent to the disc rim (model sens_xy); E1 = A, E2 = B",
         names={1: "A", 2: "K", 3: "K", 4: "E2", 5: "E1", 6: "C"})
    R("220R", "3V3", "ENC_LED", "encoder", note="LED 9-10 mA [S v0.11]")
    R("10k", "ENC_A_L", "GND", "encoder"); R("10k", "ENC_B_L", "GND", "encoder")
    R("100R", "ENC_A_L", "ENC_A", "encoder", note="[A] edge damping at the timer pin"); R("100R", "ENC_B_L", "ENC_B", "encoder")

    # ------------------------------------------------------------------------------------------------------- the 1220 driver
    # TI DRV8213DSG [Ed 8 Nov Q37 = A], WSON-8 2 x 2: 1 VM, 2 OUT1, 3 OUT2, 4 GND, 5 IN2, 6 IN1, 7 GAINSEL, 8 IPROPI, pad GND [S].
    # Current sense [S TI DRV8213]: I_IPROPI = A x I_motor, A = 205 uA/A (GAINSEL low, 0.35-2 A), 1050 (open, 60-350 mA), 4900
    # (high, 10-60 mA), +-6 %; the driver limits the current when IPROPI reaches VREF = 0.47 / 0.51 / 0.55 V (min / typ / max);
    # I_IPROPI <= 1 mA and VM - V_IPROPI >= 1.25 V. IN1 = IN2 = 0: coast, then asleep after about 1 ms (20 nA); 250 us to wake.
    # PWM at 100 kHz [Q39]. Its own 5 V branch [noise sweep]: a 0R at the 5 V pins makes the star, then VM's bulk here.
    R("0R", "5V", "VM", "motor", size="0805", note="the motor's own branch from the 5 V pins [A, noise sweep]")
    part("U", "DRV8213DSGR", "Package_SON:WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm",
         {1: "VM", 2: "MOT_A", 3: "MOT_B", 4: "GND", 5: "MOT_IN2", 6: "MOT_IN1", 7: "GAINSEL", 8: "IPROPI", 9: "GND"}, "motor",
         lcsc="C22407186", mpn="DRV8213DSGR", note="sleeps itself (no nSLEEP) [S]; US$0.68, 3,698 in stock (8 Nov)",
         names={1: "VM", 2: "OUT1", 3: "OUT2", 4: "GND", 5: "IN2", 6: "IN1", 7: "GAINSEL", 8: "IPROPI", 9: "PAD"})
    C("100nF 16V", "VM", "GND", "motor", note="low-ESR bypass at VM [S]")
    C("22uF 10V", "VM", "GND", "motor", size="0805", note="bulk: TI gives no value ('system-level testing') [A]")
    C("100nF 16V", "MOT_A", "MOT_B", "motor", face="F", note="across the 1220's tabs, at the motor [noise sweep]")
    # GAINSEL three-level: fitted to ground = low gain (205 uA/A), which covers the 1220's whole range (held still at 5 V it draws
    # about 0.76 A [Ed bench 15:31]); with the 3.3 k below the limit sits at 0.51 / (3.3 k x 205 uA/A) = 0.75 A typ (0.65-0.87) [A].
    # Danny's lever-force reading (torque per amp) may move the limit or the gain: the open spot gives 1050 uA/A for finer reading
    # below 350 mA [C bench]. V_IPROPI 0.55 V max, I_IPROPI 0.16 mA: inside both limits [S].
    R("0R", "GAINSEL", "GND", "motor", note="GAINSEL low [A; C bench]")
    R("0R", "GAINSEL", "3V3", "motor", dnp=True, note="spot for GAINSEL high")
    R("3.3k 1%", "IPROPI", "GND", "motor", note="current limit about 0.75 A [A; C bench]")
    adc_rc("IPROPI", "MOT_SENSE", "adc", note="the motor current")
    R("10k", "MOT_A", "MOT_VOICE", "motor", note="motor voice: 5 V -> 3.0 V [A]"); R("15k", "MOT_VOICE", "GND", "motor")
    C("1nF C0G", "MOT_VOICE", "GND", "adc")
    # NTC by the driver and the motor: 10k + 10k NTC from the 3.3 V (ratiometric with the Halls, corrected by VBAT) [A]
    R("10k 1%", "3V3", "NTC", "motor")
    part("RT", "10k NTC B3380", "Resistor_SMD:R_0402_1005Metric", {1: "NTC", 2: "GND"}, "motor", lcsc="C77131",
         mpn="NCP15XH103F03RC", note="Murata, B25/50 3380 K +-1 % [S]")
    C("1nF C0G", "NTC", "GND", "adc")

    # ------------------------------------------------------------------------------------------------------- the LED ring
    # 12 x SK6812MINI-E reverse-mounted in cut-outs on the back, shining through the board into the clear race [Ed 13:35; Q44 = A
    # 19:37: 12, turned along the ring so their end pads stay off the windows]. Full white 12 x 36 mA = 0.43 A [S 12 mA a colour].
    # Its own 5 V branch: a 2 A bead, the H743's switch (RGB_EN), 2 x 22 uF; data level-shifted to 5 V (VIH 0.7 x VDD) [S].
    part("FB", "BLM18KG121TZ1D", "Inductor_SMD:L_0603_1608Metric", {1: "5V", 2: "RING_IN"}, "ring", lcsc="C396652",
         mpn="BLM18KG121TZ1D", note="Murata, 120R at 100 MHz, 30 mohm, 3 A [S]")
    C("1uF 10V", "RING_IN", "GND", "ring")
    part("U", "TPS22918DBVR", "Package_TO_SOT_SMD:SOT-23-6", {1: "RING_IN", 2: "GND", 3: "RGB_EN", 4: "RING_CT", 5: "RING_5V", 6: "RING_5V"},
         "ring", lcsc="C131941", mpn="TPS22918DBVR", note="2 A, 52 mohm at 5 V; QOD to VOUT = 24 ohm discharge (load <= 200 uF) [S]",
         names={1: "VIN", 2: "GND", 3: "ON", 4: "CT", 5: "QOD", 6: "VOUT"})
    R("100k", "RGB_EN", "GND", "ring", note="off until the H743 says so (ON must not float) [S]")
    C("1nF", "RING_CT", "GND", "ring", note="2.5 ms rise at 5 V [S: SR = 0.55 x CT + 30 us/V]: about 90 mA into the 44 uF")
    C("22uF 10V", "RING_5V", "GND", "ring", size="0805"); C("22uF 10V", "RING_5V", "GND", "ring", size="0805")   # [A] kept at 2 for 12
    part("U", "SN74AHCT1G125DBVR", "Package_TO_SOT_SMD:SOT-23-5", {1: "GND", 2: "RGB_DIN", 3: "GND", 4: "RING_DY", 5: "RING_5V"}, "ring",
         lcsc="C7484", mpn="SN74AHCT1G125DBVR", note="VIH 2.0 V at 5 V [S]; powered with the ring so it never drives a dead chain; "
         "its input takes 5.5 V with VCC off (no clamp to VCC) [S], so RGB_DIN can sit at either level [A]",
         names={1: "OE#", 2: "A", 3: "GND", 4: "Y", 5: "VCC"})
    C("100nF", "RING_5V", "GND", "ring")
    R("33R", "RING_DY", "RING_D0", "ring", note="[A]")
    for k in range(RING_N):
        part("D", "SK6812MINI-E", "mb:LED_SK6812MINI-E_Reverse",
             {1: "RING_5V", 2: f"RING_D{k + 1}" if k < RING_N - 1 else "RING_DOUT", 3: "GND", 4: f"RING_D{k}"}, "ring", lcsc="C5149201",
             mpn="SK6812MINI-E", note=f"ring site {k + 1}/{RING_N}; pads after Keebio-Parts (MIT) and marbastlib (CERN-OHL-P) [S]; "
             "MSL 5a; [C] pin order against the datasheet drawing of the revision LCSC ships", names={1: "VDD", 2: "DOUT", 3: "GND", 4: "DIN"})
        C("100nF", "RING_5V", "GND", "ring")

    # ------------------------------------------------------------------------------------------------------- rod link, main end
    # Q43 = A [Ed 18:58]: a bias tee. DC: 5 V through the choke onto the rod. Data: a Manchester code at about 2 Mbit/s through the
    # coupling capacitor; DIAL_TX drives it (high-Z between frames), the comparator receives (sees our own frames too) [A].
    part("L", "NR3015T470M", "Inductor_SMD:L_Taiyo-Yuden_NR-30xx", {1: "5V", 2: "ROD"}, "rod", lcsc="C87171", mpn="NR3015T470M",
         note="Taiyo Yuden 47 uH, 3 x 3 x 1.5, DCR 1.34 ohm, Isat 0.32 A, SRF >= 17 MHz [S]; the dial's 0.12 A drops 0.16 V here [A]; "
         "[C] LCSC stock (alt SXN SMNR3015-470MT C135243, DCR 1.63, no SRF listed)")
    C("1uF 10V", "5V", "GND", "rod", note="the choke's 5 V end")
    C("100nF 16V", "ROD", "DIAL_BUS", "rod", note="coupling")
    R("100R", "DIAL_TX", "DIAL_BUS", "rod", note="send")
    R("10k", "3V3", "DIAL_MID", "rod"); R("10k", "DIAL_MID", "GND", "rod"); C("100nF", "DIAL_MID", "GND", "rod")
    R("10k", "DIAL_BUS", "DIAL_MID", "rod", note="biases the bus at mid-supply")
    R("1k", "DIAL_BUS", "DIAL_CMN", "rod", note="limits the clamp current at power-up (5 V step through the coupling cap)")
    R("4.7k", "DIAL_MID", "DIAL_CMP", "rod"); R("47k", "DIAL_RX", "DIAL_CMP", "rod", note="hysteresis about 0.3 V [A]")
    part("U", "TLV3601DBVR", "Package_TO_SOT_SMD:SOT-23-5", {1: "DIAL_RX", 2: "GND", 3: "DIAL_CMP", 4: "DIAL_CMN", 5: "3V3"}, "rod",
         lcsc="C5213958", mpn="TLV3601DBVR", note="2.5 ns, push-pull, inputs to the rails +-0.2 V [S]; wired inverting (firmware flips "
         "the code) [A]. US$2.80 and 626 in stock (8 Nov): [C] a 40 ns part is enough at 2 Mbit/s if stock stays low",
         names={1: "OUT", 2: "V-", 3: "IN+", 4: "IN-", 5: "V+"})
    C("100nF", "3V3", "GND", "rod")

    # ------------------------------------------------------------------------------------------------------- power light (Q36 = B)
    # one red VCSEL on the front at about (1.3, 26.5), shining up through the clear case onto a frosted dot [Ed 13:51]
    part("D", "JNJ-V-2835CW-665003-S-D1", "LED_SMD:LED_PLCC_2835", {1: "LIGHT_K", 2: "LIGHT_A"}, "light", face="F", lcsc="C42375664",
         mpn="JNJ-V-2835CW-665003-S-D1", note="665 nm VCSEL, threshold about 4 mA; [C] pads and polarity against JNJ's drawing; [C] "
         "optical power at the chosen current", names={1: "K", 2: "A"})
    R("220R", "3V3", "LIGHT_A", "light", face="F", note="about 6 mA at full PWM [A; C the forward voltage]")
    part("Q", "2N7002", "Package_TO_SOT_SMD:SOT-23", {1: "LIGHT_G", 2: "GND", 3: "LIGHT_K"}, "light", lcsc="C8545", mpn="2N7002",
         note="JSCJ, JLC basic part", names={1: "G", 2: "S", 3: "D"})
    R("100R", "PWR_LIGHT", "LIGHT_G", "light"); R("100k", "LIGHT_G", "GND", "light")

    # ------------------------------------------------------------------------------------------------------- power
    # 15 V comes up the right post and goes straight up board L; 5 V and 3.3 V come back down [Q38 = A]. Local bulk here [A].
    C("10uF 25V", "VSYS", "GND", "power", size="0805", note="at the post"); C("100nF 25V", "VSYS", "GND", "power")
    C("22uF 10V", "5V", "GND", "power", size="0805", note="at board L's 5 V pins"); C("10uF", "3V3", "GND", "power", size="0603")
    # BUS_PRESENT (PE4, 5 V tolerant): 15 V -> 3.19 V; reads low below about 10.9 V, an early warning before the 3.3 V goes [A]
    R("100k", "VSYS", "BUS_PRESENT", "power"); R("27k", "BUS_PRESENT", "GND", "power"); C("1nF", "BUS_PRESENT", "GND", "power")
    return PARTS


def nets(parts=None):
    out = {}
    for p in parts or PARTS:
        for num, n in p["pins"].items():
            if n:
                out.setdefault(n, []).append((p["ref"], num))
    return out


def check(parts):
    """Every net has two ends (or is meant not to), every pin-map net is used, no MCU pin left that should have a net."""
    N = nets(parts)
    single_ok = {"RING_DOUT"}
    bad = [(n, v) for n, v in N.items() if len(v) < 2 and n not in single_ok]
    used = set(N)
    missing = [n for n in PINMAP["nets"] if n not in used and n not in ("RISLEY1", "RISLEY2")]
    mcu = next(p for p in parts if p["ref"] == "U1")
    unwired_power = [pos for pos, (nm, t) in MCU_PINS.items() if t != "I/O" and not mcu["pins"].get(str(pos))]
    refs = [p["ref"] for p in parts]
    dup = {r for r in refs if refs.count(r) > 1}
    return dict(single=bad, missing=missing, unwired_power=unwired_power, dup=sorted(dup))


if __name__ == "__main__":
    P = build()
    ck = check(P)
    blocks = {}
    for p in P:
        blocks.setdefault((p["face"], p["block"]), []).append(p)
    print(f"{len(P)} parts ({sum(not p['dnp'] for p in P)} fitted, {sum(p['dnp'] for p in P)} not fitted), {len(nets(P))} nets")
    for (f, b), ps in sorted(blocks.items()):
        print(f"  {f} {b:8s} {len(ps):3d}: " + ", ".join(sorted({p['value'] for p in ps}))[:150])
    for k, v in ck.items():
        print(k, v if v else "none")
