"""Rewrite the H743 pin table in docs/main-board-circuit-2026-11-07.md from the pin map json (after each re-solve).
  python3 tools/pin_table_doc.py"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = json.load(open(os.path.join(ROOT, "cad/knob-param/knobparam/electronics/kicad/knob-main-pcb/pinmap/h743-lqfp100-simple.json")))
N = {n: v["pin"].split("-")[0].split(" ")[0] for n, v in J["nets"].items()}
S = {n: v["signal"] for n, v in J["nets"].items()}


def f(*ns, sig=False):
    return ", ".join(f"{n} {N[n]}" + (f" ({S[n]})" if sig else "") for n in ns)


rows = [
    ("Joystick screen, QUADSPI", f("JOY_QSPI_CLK", "JOY_QSPI_NCS", "JOY_QSPI_IO0", "JOY_QSPI_IO1", "JOY_QSPI_IO2", "JOY_QSPI_IO3").replace("JOY_QSPI_", "")
     + "; " + f("JOY_RST", "JOY_TE", "JOY_PWR_EN").replace("JOY_", "")),
    (f"Link flex {S['LINK_SCK'].split('_')[0]}", f("LINK_SCK", "LINK_MOSI").replace("LINK_", "") + "; " + f("CS_DAC", "CS_OLED", "OLED_DC", "OLED_RES")),
    (f"{S['I2C_SCL'].split('_')[0]}", f("I2C_SCL", "I2C_SDA").replace("I2C_", "") + "; " + f("IO_INT", "HALL3D_INT")),
    ("MIDI, dial link", f"MIDI_TX {N['MIDI_TX']} ({S['MIDI_TX'].split('_')[0]}); rod link [Q43 = A] DIAL_TX {N['DIAL_TX']} ({S['DIAL_TX']}), "
     f"DIAL_RX {N['DIAL_RX']} ({S['DIAL_RX']}), Manchester by timer + DMA"),
    ("USB FS", f("USB_DM", "USB_DP").replace("USB_", "") + " (OTG_FS: the ROM bootloader's USB DFU pins [C AN2606])"),
    (f"CAN ({S['CAN_TX'].split('_')[0]})", f("CAN_TX", "CAN_RX", "CAN_STBY").replace("CAN_", "")),
    ("ADC1", f("CV_IN1", "CV_IN2", "CV_IN3", "AUDIO_IN", "HALL1", "HALL2", "HALL4", "HALL5", "MOT_SENSE", "MOT_VOICE", "NTC", "JOY_LADDER")),
    ("ADC2, ground sense [Q41]", f"AGND_SENSE {N['AGND_SENSE']} ({S['AGND_SENSE']}): sampled by ADC2 at the same instant as ADC1's CV in / audio in "
     "(dual simultaneous mode), subtracted in firmware [A]"),
    ("DAC1", f("AUDIO_OUT")),
    (f"Encoder ({S['ENC_A'].split('_')[0]})", f("ENC_A", "ENC_B")),
    (f"1220 ({S['MOT_IN1'].split('_')[0]}), Halls", f("MOT_IN1", "MOT_IN2") + " (100 kHz PWM [Q39]); " + f("HALL_EN")),
    ("Power light [Q36]", f"PWR_LIGHT {N['PWR_LIGHT']} ({S['PWR_LIGHT']}, PWM into one transistor)"),
    ("RGB ring", f"RGB_DIN {N['RGB_DIN']} ({S['RGB_DIN'].split('_')[0]} + DMA), RGB_EN {N['RGB_EN']} (the ring's 5 V switch)"),
    ("Board L", f"5V_EN {N['5V_EN']} (the 5 V buck's enable; 3.3 V is always on) [Q38]"),
    ("Risley (reserved)", f"{N['RISLEY1']}, {N['RISLEY2']} ({S['RISLEY1'].split('_')[0]}), no tracks yet"),
    ("Cover board (later)", f"COVER_TX {N['COVER_TX']}, COVER_RX {N['COVER_RX']} ({S['COVER_TX'].split('_')[0]}), COVER_EN {N['COVER_EN']}"),
    ("System", f"BUS_PRESENT {N['BUS_PRESENT']}; HSE PH0 / PH1; SWDIO PA13, SWCLK PA14, SWO PB3"),
]
table = "| Group | Nets (pin) |\n|---|---|\n" + "".join(f"| {a} | {b} |\n" for a, b in rows)
p = os.path.join(ROOT, "docs/main-board-circuit-2026-11-07.md"); s = open(p).read()
i = s.index("| Group | Nets (pin) |"); j = s.index("\n## H743 core")
open(p, "w").write(s[:i] + table + s[j:])
print(table)
