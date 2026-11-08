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
import argparse, math, json, re, sys, xml.etree.ElementTree as ET

from ortools.sat.python import cp_model

SPIS = ["SPI1", "SPI2", "SPI3", "SPI4", "SPI5", "SPI6"]
UARTS = ["USART1", "USART2", "USART3", "USART6", "USART10", "UART4", "UART5", "UART7", "UART8", "UART9", "LPUART1"]
# PC13-PC15 sit in the backup domain: 3 mA, 2 MHz, one output switching at a time (datasheet note). Only slow inputs go there.
SLOW_PINS = {"PC13", "PC14", "PC15"}   # matched as name prefixes ("PC14-OSC32_IN (OSC32_IN)" on the H743)
SLOW_OK = {"BUS_PRESENT"}   # plus every interrupt / TE input (nets marked *)
TIMS = ["TIM1", "TIM2", "TIM3", "TIM4", "TIM5", "TIM8", "TIM12", "TIM13", "TIM14", "TIM15", "TIM16", "TIM17", "TIM23", "TIM24"]


def signal_list(profile):
    """[(group, kind, instances, [(net, [signal patterns with {i}])], exclusive_kind)].  kind 'gpio' nets take any free pin."""
    G = []
    q1 = [("JOY_QSPI_CLK", ["OCTOSPIM_P1_CLK", "QUADSPI_CLK"]), ("JOY_QSPI_NCS", ["OCTOSPIM_P1_NCS", "QUADSPI_BK1_NCS"])] + \
         [(f"JOY_QSPI_IO{k}", [f"OCTOSPIM_P1_IO{k}", f"QUADSPI_BK1_IO{k}"]) for k in range(4)]   # Octo-SPI (H7A/B, H72x) or QUADSPI (H74x)
    if profile == "lqfp100-flashquad":   # the other way round: flash on the quad port (memory-mapped), screen on 4-wire SPI
        G.append(("NOR flash (quad, Octo-SPI port 1)", "fixed", [""], [(n.replace("JOY", "FLASH"), sgs) for n, sgs in q1], None))
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
    # [Ed 8 Nov Q43 = A] the rod link is a bias tee with a Manchester code (about 2 Mbit/s): one timer sends (PWM / DMA) and
    # times the received edges (input capture / DMA)
    G.append(("dial link through the rod (Manchester on the rod's 5 V, one timer + DMA)", "inst", TIMS,
              [("DIAL_TX", ["{i}_CH1", "{i}_CH3"]), ("DIAL_RX", ["{i}_CH2", "{i}_CH4"])], "TIM"))
    # [A] OTG_FS on PA11 / PA12 only (8 Nov, step 3): the H74x ROM bootloader's USB DFU uses those pins [C AN2606], and the
    # field update path counts on it; the step-3 re-solve had moved USB to OTG_HS's PB14 / PB15
    G.append(("USB (link flex, FS on the internal PHY)", "fixed", [""], [("USB_DM", ["USB_OTG_FS_DM"]), ("USB_DP", ["USB_OTG_FS_DP"])], None))
    G.append(("CAN (vertical board R's transceiver)", "inst", ["FDCAN1", "FDCAN2"], [("CAN_TX", ["{i}_TX"]), ("CAN_RX", ["{i}_RX"])], "FDCAN"))
    G.append(("CAN standby", "gpio", [""], [("CAN_STBY", [])], None))
    analog = ["CV_IN1", "CV_IN2", "CV_IN3", "AUDIO_IN", "HALL1", "HALL2", "HALL4", "HALL5", "MOT_SENSE", "MOT_VOICE", "NTC", "JOY_LADDER"]
    G.append(("analog inputs (ADC1/2)", "adc", [""], [(n, []) for n in analog], None))
    # [Ed 8 Nov Q41 = A] the jack lower board's analog ground, up flex pin 24: on an ADC2 input, so ADC2 samples it at the same instant
    # as ADC1 samples a CV in or the audio in (dual simultaneous mode) and the firmware subtracts it
    G.append(("ground sense for the CV ins and audio in (ADC2, sampled with ADC1)", "adc2", [""], [("AGND_SENSE", [])], None))
    G.append(("audio out (link)", "fixed", [""], [("AUDIO_OUT", ["DAC1_OUT1", "DAC1_OUT2"])], None))
    G.append(("encoder (timer in encoder mode)", "inst", ["TIM1", "TIM2", "TIM3", "TIM4", "TIM5", "TIM8", "TIM23", "TIM24"],
              [("ENC_A", ["{i}_CH1"]), ("ENC_B", ["{i}_CH2"])], "TIM"))
    G.append(("1220 driver PWM (IN1, IN2)", "inst", TIMS, [("MOT_IN1", ["{i}_CH1", "{i}_CH3"]), ("MOT_IN2", ["{i}_CH2", "{i}_CH4"])], "TIM"))
    # [S TI DRV8213 DSG] the DSG package has no nSLEEP pin (it sleeps itself when IN1 = IN2 = 0) and VREF is fixed inside
    G.append(("Hall enable", "gpio", [""], [("HALL_EN", [])], None))
    # [Ed 8 Nov Q35 / Q36 = B] the ring's VCSELs and their decoder are gone; one red VCSEL is the power light, one transistor, PWM
    G.append(("power light VCSEL (PWM, one transistor)", "inst", TIMS, [("PWR_LIGHT", ["{i}_CH1", "{i}_CH2", "{i}_CH3", "{i}_CH4"])], "TIM"))
    G.append(("RGB ring data (timer + DMA)", "inst", TIMS, [("RGB_DIN", ["{i}_CH1", "{i}_CH2", "{i}_CH3", "{i}_CH4"])], "TIM"))
    # the violet source is on the dial board, run by the dial's own chip over the rod link: no main-chip pin
    G.append(("RGB ring power switch", "gpio", [""], [("RGB_EN", [])], None))
    G.append(("Risley motors (PWM, later) [A reserved]", "inst", TIMS,
              [("RISLEY1", ["{i}_CH1", "{i}_CH3"]), ("RISLEY2", ["{i}_CH2", "{i}_CH4"])], "TIM"))
    G.append(("joystick screen reset, TE, power", "gpio", [""], [("JOY_RST", []), ("JOY_TE*", []), ("JOY_PWR_EN", [])], None))
    G.append(("15 V present", "gpio", [""], [("BUS_PRESENT", [])], None))
    G.append(("5 V on (board L's 5 V buck enable) [Ed Q38 = A]", "gpio", [""], [("5V_EN", [])], None))
    G.append(("crystal", "fixed", [""], [("HSE_IN", ["RCC_OSC_IN"]), ("HSE_OUT", ["RCC_OSC_OUT"])], None))
    G.append(("debug (SWD + SWO)", "fixed", [""], [("SWDIO", ["DEBUG_JTMS-SWDIO"]), ("SWCLK", ["DEBUG_JTCK-SWCLK"]), ("SWO", ["DEBUG_JTDO-SWO"])], None))
    if profile.endswith("-simple"):   # subtraction: no back screens on the first build, no external flash (program and the joystick
        # screen's pictures in the chip's own flash); a UART + enable kept for a later back-screen cover board with its own chip
        drop = ("NOR flash", "flash", "back AMOLED")
        G = [g for g in G if not g[0].startswith(drop)]
        G.append(("later cover board for the back screens (UART, commands)", "inst", UARTS,
                  [("COVER_TX", ["{i}_TX"]), ("COVER_RX", ["{i}_RX"])], "UART"))
        G.append(("later cover board power enable", "gpio", [""], [("COVER_EN", [])], None))
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


def solve(pins, groups, spare_min=0, keep=None, near=None):
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
                if p.startswith(tuple(SLOW_PINS)) and not (net.endswith("*") or net in SLOW_OK):   # names differ by family
                    continue
                if "_C" in p and kind not in ("adc", "adc2"):   # the ADC-switch pads (PA0_C, PC2_C ...): analog only [A]
                    continue
                if kind == "gpio":
                    ok = [("GPIO", None)]
                elif kind == "adc":
                    ok = [(s, None) for s in sigs if re.match(r"ADC[12]_INP?\d+$", s)][:1]
                elif kind == "adc2":
                    ok = [(s, None) for s in sigs if re.match(r"ADC2_INP\d+$", s)][:1]
                elif kind == "fixed":
                    ok = [(s, None) for s in sigs if s in pats]
                else:
                    ok = [(pat.format(i=i), i) for i in insts for pat in pats if pat.format(i=i) in sigs]
                for s, i in ok:
                    v = m.NewBoolVar(f"{net}@{p}:{s}")
                    x[(net, p, s)] = v; cands.append(v); pin_load[p].append(v)
                    if kind == "inst":
                        m.AddImplication(v, inst_vars[gi][i])
                    if s not in ("GPIO",) and kind not in ("adc", "adc2"):
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
    if near:   # [A] step 3: each net to the pin nearest where it goes on the placed board (tenths of a mm, straight line)
        xy, tg = near
        def dist(net, p):
            t = tg.get(net.rstrip("*")); q = xy.get(str(pins[p][0]))
            return 0 if t is None or q is None else int(round(10 * math.hypot(t[0] - q[0], t[1] - q[1])))
        m.Minimize(sum(dist(net, p) * v for (net, p, sg), v in x.items()))
    elif keep:   # [A] a re-solve keeps every net it can on its previous pin (so a small change stays a small change)
        m.Maximize(sum(v for (net, p, sg), v in x.items() if keep.get(net.rstrip("*")) == p))
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
    ap.add_argument("--out"); ap.add_argument("--keep", help="a previous --out json: keep nets on their pins where possible")
    ap.add_argument("--near", help="pin targets from the placed board (make_board.py --targets): each net to its nearest pin, "
                                   "trying the chip's four quarter turns")
    a = ap.parse_args()
    pins = load(a.data, a.part)
    groups = signal_list(a.profile)
    nets = sum(len(g[3]) for g in groups)
    keep = {n: v["pin"] for n, v in json.load(open(a.keep))["nets"].items()} if a.keep else None
    rot = None
    if a.near:
        T = json.load(open(a.near)); best = None
        for r_, xy in sorted(T["pin_xy"].items()):
            res_, st_ = solve(pins, groups, near=(xy, T["targets"]))
            if res_ is None:
                continue
            tot = sum(math.hypot(T["targets"][n][0] - xy[str(pins[p][0])][0], T["targets"][n][1] - xy[str(pins[p][0])][1])
                      for n, (p, _s) in res_.items() if n in T["targets"])
            print(f"  chip turned {r_}: straight-line total {tot:.0f} mm ({st_})")
            if best is None or tot < best[0]:
                best = (tot, r_, res_, st_)
        _t, rot, res, status = best
    else:
        res, status = solve(pins, groups, keep=keep)
    print(f"{a.part} ({a.profile}): {len(pins)} I/O pins, {nets} nets: {status}" + (f"; chip turned {rot}" if rot is not None else ""))
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
                       spare=spare, **({"mcu_rot": float(rot)} if rot is not None else {})), open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
