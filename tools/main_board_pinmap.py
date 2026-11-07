"""Main-board pass, step 1: a pin map for the STM32H7B0 from ST's own pin data (7 Nov 2026).

Reads ST's open pin data (github.com/STMicroelectronics/STM32_open_pin_data, BSD-3-Clause, (c) 2020 STMicroelectronics; not copied
into this repo: clone it and pass the path) and solves the signal list below as a constraint problem with Google OR-Tools CP-SAT
(Apache-2.0): every net gets one pin that offers its function, one net per pin, one pin per peripheral signal, peripheral groups on
one instance each (an SPI's SCK and MOSI on the same SPI), different instances for groups that can't share, and the EXTI lines
(interrupt inputs) on different pin numbers. It answers "does it fit", lists the spare pins and writes the map.

    python3 tools/main_board_pinmap.py <STM32_open_pin_data> [--part STM32H7B0VBTx] [--profile lqfp100|lqfp144] [--out map.json]

The signal list is the step-2 architecture (link flex, vertical boards, back AMOLEDs on SPI) with [A] choices marked; see
docs/main-board-signals-2026-11-07.md. Pins are not placement-aware yet: the map is re-solved with pin preferences once the chip's
neighbours are placed."""
import argparse, json, re, sys, xml.etree.ElementTree as ET

from ortools.sat.python import cp_model

SPIS = ["SPI1", "SPI2", "SPI3", "SPI4", "SPI5", "SPI6"]
UARTS = ["USART1", "USART2", "USART3", "USART6", "USART10", "UART4", "UART5", "UART7", "UART8", "UART9", "LPUART1"]
# PC13-PC15 sit in the backup domain: 3 mA, 2 MHz, one output switching at a time (datasheet note). Only slow inputs go there.
SLOW_PINS = {"PC13", "PC14-OSC32_IN", "PC15-OSC32_OUT"}
SLOW_OK = {"BUS_PRESENT"}   # plus every interrupt / TE input (nets marked *)
TIMS = ["TIM1", "TIM2", "TIM3", "TIM4", "TIM5", "TIM8", "TIM12", "TIM13", "TIM14", "TIM15", "TIM16", "TIM17", "TIM23", "TIM24"]


def signal_list(profile):
    """[(group, kind, instances, [(net, [signal patterns with {i}])], exclusive_kind)].  kind 'gpio' nets take any free pin."""
    G = []
    q1 = [("JOY_QSPI_CLK", ["OCTOSPIM_P1_CLK"]), ("JOY_QSPI_NCS", ["OCTOSPIM_P1_NCS"])] + \
         [(f"JOY_QSPI_IO{k}", [f"OCTOSPIM_P1_IO{k}"]) for k in range(4)]
    if profile == "lqfp100-flashquad":   # the other way round: flash on the quad port (memory-mapped), screen on 4-wire SPI
        G.append(("NOR flash (quad, Octo-SPI port 1)", "fixed", [""], [(n.replace("JOY", "FLASH"), [sg]) for n, (sg,) in q1], None))
        G.append(("joystick screen (CO5300, 4-wire SPI)", "inst", SPIS, [("JOY_SCK", ["{i}_SCK"]), ("JOY_MOSI", ["{i}_MOSI"])], "SPI"))
        G.append(("joystick screen CS, D/C", "gpio", [""], [("JOY_CS", []), ("JOY_DC", [])], None))
    else:
        G.append(("joystick screen (CO5300, QSPI on Octo-SPI port 1)", "fixed", [""], q1, None))
    if profile == "lqfp100-flashquad":
        pass
    elif profile == "lqfp100-shared":   # Q32 workaround on the H7B0: the screen and the flash share port 1; a 74LVC1G19 (1-of-2)
        # steers the port's one NCS to the screen or the flash, picked by FLASH_SEL
        G.append(("flash on the shared quad port: chip-select steering (74LVC1G19)", "gpio", [""], [("FLASH_SEL", [])], None))
    elif profile == "u5-mux":            # Q32 on an STM32U5 (LQFP100 bonds out port 2's NCS): Octo-SPI multiplexed mode, the
        # second controller on the same CLK / IO lines with its own chip select
        G.append(("flash on the shared quad port (multiplexed mode, port 2 NCS)", "fixed", [""], [("FLASH_NCS", ["OCTOSPIM_P2_NCS"])], None))
    elif profile == "lqfp144":   # port 2 exists on the bigger package: the flash gets its own quad port
        q2 = [("FLASH_QSPI_CLK", ["OCTOSPIM_P2_CLK"]), ("FLASH_QSPI_NCS", ["OCTOSPIM_P2_NCS"])] + \
             [(f"FLASH_QSPI_IO{k}", [f"OCTOSPIM_P2_IO{k}"]) for k in range(4)]
        G.append(("NOR flash (quad, Octo-SPI port 2)", "fixed", [""], q2, None))
    else:                       # [A] LQFP100 has port 1 only: the flash on a plain SPI (1-bit) with its own CS
        G.append(("NOR flash (1-bit SPI; SPI1-3 have the deeper FIFO [A])", "inst", SPIS[:3], [("FLASH_SCK", ["{i}_SCK"]), ("FLASH_MOSI", ["{i}_MOSI"]),
                                                          ("FLASH_MISO", ["{i}_MISO"])], "SPI"))
        G.append(("flash CS", "gpio", [""], [("FLASH_CS", [])], None))
    for side in ("UP", "LO"):   # [A] back AMOLEDs (RM690B0) on 4-wire SPI each, until DisplayModule's tail pin list says QSPI
        G.append((f"back AMOLED {side} (RM690B0, 4-wire SPI)", "inst", SPIS,
                  [(f"AM{side}_SCK", ["{i}_SCK"]), (f"AM{side}_MOSI", ["{i}_MOSI"])], "SPI"))
        G.append((f"back AMOLED {side} CS, D/C, TE", "gpio", [""], [(f"AM{side}_CS", []), (f"AM{side}_DC", []), (f"AM{side}_TE*", [])], None))
    G.append(("back AMOLEDs shared reset and power enable", "gpio", [""], [("AM_RESX", []), ("AM_PWR_EN", [])], None))
    G.append(("link flex SPI (jack lower board: DAC80504, clear OLED)", "inst", SPIS,
              [("LINK_SCK", ["{i}_SCK"]), ("LINK_MOSI", ["{i}_MOSI"])], "SPI"))
    G.append(("link flex chip selects and OLED lines", "gpio", [""], [("CS_DAC", []), ("CS_OLED", []), ("OLED_DC", []), ("OLED_RES", [])], None))
    G.append(("I2C (TMAG5273, the jack unit's TCA9535 over the link; one bus [A])", "inst", ["I2C1", "I2C2", "I2C3", "I2C4"],
              [("I2C_SCL", ["{i}_SCL"]), ("I2C_SDA", ["{i}_SDA"])], "I2C"))
    G.append(("interrupts", "gpio", [""], [("IO_INT*", []), ("HALL3D_INT*", [])], None))
    G.append(("MIDI out (link)", "inst", UARTS, [("MIDI_TX", ["{i}_TX"])], "UART"))
    G.append(("dial link through the rod (half-duplex UART on VBUS) [A]", "inst", UARTS, [("DIAL_DATA", ["{i}_TX"])], "UART"))
    G.append(("USB (link flex, FS on the internal PHY)", "fixed", [""], [("USB_DM", ["USB_OTG_HS_DM"]), ("USB_DP", ["USB_OTG_HS_DP"])], None))
    G.append(("CAN (vertical board R's transceiver)", "inst", ["FDCAN1", "FDCAN2"], [("CAN_TX", ["{i}_TX"]), ("CAN_RX", ["{i}_RX"])], "FDCAN"))
    G.append(("CAN standby", "gpio", [""], [("CAN_STBY", [])], None))
    analog = ["CV_IN1", "CV_IN2", "CV_IN3", "AUDIO_IN", "HALL1", "HALL2", "HALL4", "HALL5", "MOT_SENSE", "MOT_VOICE", "NTC", "JOY_LADDER"]
    G.append(("analog inputs (ADC1/2)", "adc", [""], [(n, []) for n in analog], None))
    G.append(("audio out (link)", "fixed", [""], [("AUDIO_OUT", ["DAC1_OUT1", "DAC1_OUT2"])], None))
    G.append(("encoder (timer in encoder mode)", "inst", ["TIM1", "TIM2", "TIM3", "TIM4", "TIM5", "TIM8", "TIM23", "TIM24"],
              [("ENC_A", ["{i}_CH1"]), ("ENC_B", ["{i}_CH2"])], "TIM"))
    G.append(("1220 driver PWM (IN1, IN2)", "inst", TIMS, [("MOT_IN1", ["{i}_CH1", "{i}_CH3"]), ("MOT_IN2", ["{i}_CH2", "{i}_CH4"])], "TIM"))
    G.append(("1220 driver sleep, Hall enable", "gpio", [""], [("MOT_nSLEEP", []), ("HALL_EN", [])], None))
    G.append(("VCSEL one-hot decoder", "gpio", [""], [("VCSEL_A0", []), ("VCSEL_A1", []), ("VCSEL_A2", []), ("VCSEL_A3", [])], None))
    G.append(("VCSEL enable (PWM)", "inst", TIMS, [("LASER_EN", ["{i}_CH1", "{i}_CH2", "{i}_CH3", "{i}_CH4"])], "TIM"))
    G.append(("RGB ring data (timer + DMA)", "inst", TIMS, [("RGB_DIN", ["{i}_CH1", "{i}_CH2", "{i}_CH3", "{i}_CH4"])], "TIM"))
    G.append(("RGB enable, violet enable", "gpio", [""], [("RGB_EN", []), ("VIOLET_EN", [])], None))
    G.append(("Risley motors (PWM, later) [A reserved]", "inst", TIMS,
              [("RISLEY1", ["{i}_CH1", "{i}_CH3"]), ("RISLEY2", ["{i}_CH2", "{i}_CH4"])], "TIM"))
    G.append(("joystick screen reset, TE, power", "gpio", [""], [("JOY_RST", []), ("JOY_TE*", []), ("JOY_PWR_EN", [])], None))
    G.append(("15 V present", "gpio", [""], [("BUS_PRESENT", [])], None))
    G.append(("crystal", "fixed", [""], [("HSE_IN", ["RCC_OSC_IN"]), ("HSE_OUT", ["RCC_OSC_OUT"])], None))
    G.append(("debug (SWD + SWO)", "fixed", [""], [("SWDIO", ["DEBUG_JTMS-SWDIO"]), ("SWCLK", ["DEBUG_JTCK-SWCLK"]), ("SWO", ["DEBUG_JTDO-SWO"])], None))
    if profile.endswith("-local"):   # local rendering: the screens' own chips draw; the main MCU only sends them commands
        drop = ("joystick screen", "NOR flash", "flash", "back AMOLED")
        G = [g for g in G if not g[0].startswith(drop)]
        G.append(("joystick screen node (UART, commands)", "inst", UARTS, [("JOYN_TX", ["{i}_TX"]), ("JOYN_RX", ["{i}_RX"])], "UART"))
        G.append(("back screens node (UART, commands)", "inst", UARTS, [("BACKN_TX", ["{i}_TX"]), ("BACKN_RX", ["{i}_RX"])], "UART"))
        G.append(("screen nodes reset and boot (so the main MCU can load their firmware over the UART)", "gpio", [""],
                  [("JOYN_EN", []), ("JOYN_BOOT", []), ("BACKN_EN", []), ("BACKN_BOOT", [])], None))
    return G


def load(path, part):
    t = ET.parse(f"{path}/mcu/{part}.xml"); r = t.getroot(); ns = {"m": r.tag.split("}")[0][1:]}
    pins = {}
    for p in r.findall("m:Pin", ns):
        if p.get("Type") == "I/O":
            pins[p.get("Name")] = (int(p.get("Position")), [s.get("Name") for s in p.findall("m:Signal", ns)])
    return pins


def pin_number(name):
    m = re.match(r"P[A-K](\d+)", name)
    return int(m.group(1)) if m else None


def solve(pins, groups, spare_min=0):
    m = cp_model.CpModel()
    x = {}; sig_use = {}; inst_vars = {}; kind_use = {}
    pin_load = {p: [] for p in pins}
    exti = []
    for gi, (gname, kind, insts, nets, excl) in enumerate(groups):
        if kind == "inst":
            iv = {i: m.NewBoolVar(f"g{gi}_{i}") for i in insts}
            m.AddExactlyOne(iv.values()); inst_vars[gi] = iv
            for i, v in iv.items():
                kind_use.setdefault((excl, i), []).append(v)
        for net, pats in nets:
            cands = []
            for p, (_pos, sigs) in pins.items():
                if p in SLOW_PINS and not (net.endswith("*") or net in SLOW_OK):
                    continue
                if p.endswith("_C") and kind not in ("adc", "gpio"):   # the ADC-switch pads: analog or slow GPIO only [A]
                    continue
                if kind == "gpio":
                    ok = [("GPIO", None)]
                elif kind == "adc":
                    ok = [(s, None) for s in sigs if re.match(r"ADC[12]_INP?\d+$", s)][:1]
                elif kind == "fixed":
                    ok = [(s, None) for s in sigs if s in pats]
                else:
                    ok = [(pat.format(i=i), i) for i in insts for pat in pats if pat.format(i=i) in sigs]
                for s, i in ok:
                    v = m.NewBoolVar(f"{net}@{p}:{s}")
                    x[(net, p, s)] = v; cands.append(v); pin_load[p].append(v)
                    if kind == "inst":
                        m.AddImplication(v, inst_vars[gi][i])
                    if s not in ("GPIO",) and kind != "adc":
                        sig_use.setdefault(s, []).append(v)
            if not cands:
                return None, f"no pin can carry {net}"
            m.AddExactlyOne(cands)
            if net.endswith("*"):
                exti.append(net)
    for p, vs in pin_load.items():
        m.AddAtMostOne(vs)
    for s, vs in sig_use.items():
        m.AddAtMostOne(vs)
    for (excl, i), vs in kind_use.items():
        if excl in ("SPI", "UART", "FDCAN", "I2C", "TIM"):   # one peripheral instance per group (a timer runs one job:
                                                              # encoder count, motor PWM, LED data, ...)
            m.AddAtMostOne(vs)
    for n in range(16):   # interrupt inputs on different EXTI lines
        vs = [v for (net, p, s), v in x.items() if net in exti and pin_number(p) == n]
        m.AddAtMostOne(vs)
    used = sum(x.values())
    spare = len(pins) - used
    m.Add(spare >= spare_min)
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = 60; s.parameters.num_workers = 1; s.parameters.random_seed = 1   # repeatable
    r = s.Solve(m)
    if r not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, s.StatusName(r)
    out = {}
    for (net, p, sg), v in x.items():
        if s.Value(v):
            out[net.rstrip("*")] = (p, sg)
    return out, s.StatusName(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data"); ap.add_argument("--part", default="STM32H7B0VBTx"); ap.add_argument("--profile", default="lqfp100")
    ap.add_argument("--out")
    a = ap.parse_args()
    pins = load(a.data, a.part)
    groups = signal_list(a.profile)
    nets = sum(len(g[3]) for g in groups)
    res, status = solve(pins, groups)
    print(f"{a.part} ({a.profile}): {len(pins)} I/O pins, {nets} nets: {status}")
    if res is None:
        sys.exit(1)
    used = {p for p, _s in res.values()}
    spare = sorted(set(pins) - used, key=lambda p: pins[p][0])
    print(f"spare pins ({len(spare)}): {', '.join(spare)}")
    for gname, kind, insts, gnets, excl in groups:
        print(f"  {gname}: " + ", ".join(f"{n.rstrip('*')} {res[n.rstrip('*')][0]}"
                                         + (f" ({res[n.rstrip('*')][1]})" if res[n.rstrip('*')][1] != "GPIO" else "") for n, _ in gnets))
    if a.out:
        json.dump(dict(part=a.part, profile=a.profile, nets={n: dict(pin=p, signal=s, position=pins[p][0]) for n, (p, s) in res.items()},
                       spare=spare), open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
