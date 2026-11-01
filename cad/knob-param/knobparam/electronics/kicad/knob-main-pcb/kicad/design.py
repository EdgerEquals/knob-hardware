"""knob main PCB v0.11 (knob CAD v0.16): the ONE netlist + placement for the board. Pure Python (no KiCad):
make_board.py turns it into knob-main-pcb.kicad_sch (via ../../sch_gen.py) and knob-main-pcb.kicad_pcb (pcbnew).
Positions come from ../../cad_constraints.json (exported from the parametric model by export_cad_constraints.py) or are [A].
Coordinates here: board mm (panel top-left origin, x right, y down). Frame -> board: bx = axis_bx + x, by = axis_by - y.

MCU: the main PCB has no MCU section yet. Every signal is brought to J10, a PLACEHOLDER 2x14 test-pad field on B.Cu, with an
assumed pin-out (below) so the MCU section (STM32 [A]) can be drawn against it. Hall outputs are analog (ADC), the middle
TMAG5273 is I2C (+INT), the encoder is two emitter outputs, the 716 feel motor runs from an on-board DRV8837 (IN1/IN2/nSLEEP
from the MCU), the 1220 main motor and VBUS_DATA (rod) go straight to J2 for the MCU-side driver / link."""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import lighting_build, lighting_params
C = json.load(open(os.path.join(HERE, "..", "..", "cad_constraints.json")))
AX, AY = C["axis_b"]
def B(x, y): return (AX + x, AY - y)          # frame -> board
JS = json.load(open(os.path.join(HERE, "..", "..", "joystick_stack_v016.json")))   # joystick v0.1 stack (make_v016_footprints.py)
JX, JY = 25.25, 21.1   # [L] carrier / top-screen centre (panel layout v5; joystick v0.1)
def pol(r, a): return (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))

# v0.11: 10k -> YAGEO RC0402FR-0710KL (UNI-ROYAL C25744 showed 0 stock at LCSC on 2026-11-01); encoder LED 150R -> 220R (see U2)
LCSC = {"100n": ("CL05B104KO5NNNC", "Samsung", "C1525"), "10k": ("RC0402FR-0710KL", "YAGEO", "C60490"),
        "4k7": ("0402WGF4701TCE", "UNI-ROYAL", "C25900"), "220R": ("0402WGF2200TCE", "UNI-ROYAL", "C25091"),
        "10u": ("CL10A106KP8NNNC", "Samsung", "C19702")}
DS = {"TMAG5253": "https://www.ti.com/lit/ds/symlink/tmag5253.pdf", "TMAG5273": "https://www.ti.com/lit/ds/symlink/tmag5273.pdf",
      "DRV8837": "https://www.ti.com/lit/ds/symlink/drv8837.pdf", "EE-SX1321": "https://components.omron.com/us-en/products/sensors/EE-SX1321"}

P2 = lambda: [("1", "1", "passive", "L"), ("2", "2", "passive", "R")]
PINS = {
    "TMAG5253": [("1", "VCC", "power_in", "L"), ("2", "GND", "power_in", "L"), ("3", "EN", "input", "L"), ("4", "OUT", "output", "R"), ("5", "EP", "passive", "R")],
    "TMAG5273": [("4", "VCC", "power_in", "L"), ("2", "GND", "power_in", "L"), ("3", "TEST", "input", "L"), ("1", "SCL", "input", "R"),
                 ("6", "SDA", "bidirectional", "R"), ("5", "INT", "open_collector", "R")],
    "DRV8837": [("8", "VCC", "power_in", "L"), ("1", "VM", "power_in", "L"), ("6", "IN1", "input", "L"), ("5", "IN2", "input", "L"),
                ("7", "nSLEEP", "input", "L"), ("2", "OUT1", "output", "R"), ("3", "OUT2", "output", "R"), ("4", "GND", "passive", "R"), ("9", "EP", "passive", "R")],
    # EE-SX1321 (datasheet p3): 1 Anode, 2 + 3 Cathode, 4 + 5 Emitter (4 = E2, 5 = E1 per the tape drawing), 6 Collector (common)
    "EE-SX1321": [("1", "A", "passive", "L"), ("2", "K", "passive", "L"), ("3", "K", "passive", "L"), ("6", "C", "passive", "R"), ("5", "E1", "passive", "R"), ("4", "E2", "passive", "R")],
    "R": P2(), "C": P2(), "Motor": [("1", "+", "passive", "L"), ("2", "-", "passive", "R")],
    "TubeRodClamp": [("1", "TUBE_GND", "passive", "L"), ("2", "ROD_VBUS", "passive", "R")],
    "PWR_FLAG": [("1", "pwr", "power_out", "R")],
}
# J10 MCU-link placeholder pin-out [A]
J10_PINS = ["+3V3", "GND", "HALL1", "HALL2", "HALL4", "HALL5", "HALL_EN", "I2C_SCL", "I2C_SDA", "HALL3D_INT", "ENC_A", "ENC_B", "GND",
           "FEEL_IN1", "FEEL_IN2", "FEEL_nSLEEP", "VM_FEEL", "GND", "MAIN_MOT_A", "MAIN_MOT_B", "VBUS_DATA",
           "SW_UP", "SW_DOWN", "SW_LEFT", "SW_RIGHT", "SW_CENTER", "GND", "+3V3"]
PINS["J10"] = [(str(i + 1), n, "passive", "L" if i < 14 else "R") for i, n in enumerate(J10_PINS)]
# joystick daughterboard socket: same pin-out as the daughterboard J1 (joystick-daughterboard/make_project.py J_PINS)
J2_PINS = ["SW_UP", "SW_CENTER", "SW_RIGHT", "SW_LEFT", "GND", "SW_DOWN"]
PINS["J2"] = [(str(i + 1), n, "passive", "L" if i % 2 == 0 else "R") for i, n in enumerate(J2_PINS)]
lighting_build.register(PINS)

def comps():
    out = []
    def add(ref, sym, value, fp, nets, place, fields=None, bom=True, side="F"):
        f = dict(fields or {})
        out.append(dict(ref=ref, sym=sym, pins=PINS[sym], value=value, footprint="footprints:" + fp, nets=nets, fields=f, bom=bom,
                        place=place, side=side))
    def passive(ref, kind, val, fp, n1, n2, place, side="B"):
        mpn, mfr, lc = LCSC[val]
        add(ref, kind, val, fp, {"1": n1, "2": n2}, place, {"MPN": mpn, "Manufacturer": mfr, "LCSC": lc}, side=side)
    # ---- mechanical / hand-fit (not in the PCBWay BOM / CPL) ----
    add("H1", "TubeRodClamp", "TubeRodClamp_M1.6_v016", "TubeRodClamp_Main_M1.6_v016", {"1": "GND", "2": "VBUS_DATA"}, (*B(0, 0), 0), bom=False)
    add("M1", "Motor", "1220 coreless planetary (hand-solder)", "Motor_1220_Tabs_Relief", {"1": "MAIN_MOT_A", "2": "MAIN_MOT_B"}, (*B(C["offset"], 0), 0), bom=False)
    # 716 lead pads: pads tangential at fm_pad_xy (orientation solved in make_board.py)
    add("M2", "Motor", "716 coreless feel motor (hand-solder)", "FeelMotor_716_LeadPads", {"1": "FEEL_A", "2": "FEEL_B"}, (*B(*C["fm_xy"]), C["fm_ang"] + 90), bom=False, side="B")
    # ---- Hall row (F.Cu) + decouplers right behind (B.Cu), as in the CAD proxy ----
    mid = C["hall_mid_idx"]
    for i, s in enumerate(C["hall"]):
        x, y = pol(s["r"], s["ang"]); bx, by = B(x, y); ref = f"U{11 + i}"; cref = f"C{11 + i}"
        if i == mid:
            add(ref, "TMAG5273", "TMAG5273A2QDBVR", "SOT-23-6_TMAG5273_Tight",
                {"4": "+3V3", "2": "GND", "3": "GND", "1": "I2C_SCL", "6": "I2C_SDA", "5": "HALL3D_INT"}, (bx, by, s["ang"]),
                {"MPN": "TMAG5273A2QDBVR", "Manufacturer": "TI", "LCSC": "C3715882", "Datasheet": DS["TMAG5273"],
                 "Note": f"Hall row {i + 1}/5 (middle, 3D, I2C, A2 +-133 mT: A1 would saturate), r {s['r']:.2f} @ {s['ang']:.3f} deg; magnet above: {'N' if s['pol'] > 0 else 'S'} face down"})
        else:
            add(ref, "TMAG5253", "TMAG5253BA3IQDMRR", "X2SON-4_TMAG5253",
                {"1": "+3V3", "2": "GND", "3": "HALL_EN", "4": f"HALL{i + 1}", "5": "GND"}, (bx, by, s["ang"]),
                {"MPN": "TMAG5253BA3IQDMRR", "Manufacturer": "TI", "LCSC": "C22401868", "Datasheet": DS["TMAG5253"],
                 "Note": f"Hall row {i + 1}/5 (linear, ADC), r {s['r']:.2f} @ {s['ang']:.3f} deg; magnet above: {'N' if s['pol'] > 0 else 'S'} face down"})
        passive(cref, "C", "100n", "C_0402", "+3V3", "GND", (bx, by, s["ang"] + 90))
    # ---- TMAG5273 I2C pull-ups + INT pull-up (B.Cu, near J2) [A: could live at the MCU] ----
    passive("R20", "R", "4k7", "R_0402", "+3V3", "I2C_SCL", (44.2, 30.4, 0))
    passive("R21", "R", "4k7", "R_0402", "+3V3", "I2C_SDA", (46.4, 30.4, 0))
    passive("R22", "R", "10k", "R_0402", "+3V3", "HALL3D_INT", (44.2, 32.2, 0))
    # ---- encoder EE-SX1321 (B.Cu, slot tangent to the disc rim) + LED / emitter-load resistors ----
    # LED: IF = (3.3 - VF 1.1..1.3) / 220R = 9-10 mA: inside the datasheet IF derating (25 mA to 25 degC, ~13 mA at 60 degC); IL >= 150 uA
    # at IF 5 mA, so >= ~300 uA at 10 mA -> >= 3 V across the 10k emitter loads (logic high), dark current 100 nA max -> 1 mV (low).
    sx, sy = B(*C["sens_xy"])
    add("U2", "EE-SX1321", "EE-SX1321", "Omron_EE-SX1321", {"1": "ENC_LED", "2": "GND", "3": "GND", "6": "+3V3", "5": "ENC_A", "4": "ENC_B"},
        (sx, sy, 90), {"MPN": "EE-SX1321", "Manufacturer": "Omron", "LCSC": "C469128", "Datasheet": DS["EE-SX1321"],
                       "Note": "replaces the discontinued EE-SX1131 [Ed 2026-11-01]; E1 = ENC_A, E2 = ENC_B (direction sign is calibrated in firmware)"}, side="B")
    passive("R30", "R", "220R", "R_0402", "+3V3", "ENC_LED", (46.4, 32.2, 0))
    passive("R31", "R", "10k", "R_0402", "ENC_A", "GND", (44.2, 34.0, 0))
    passive("R32", "R", "10k", "R_0402", "ENC_B", "GND", (46.4, 34.0, 0))
    # ---- 716 feel motor driver DRV8837 (B.Cu, next to the M2 lead pads) ----
    fx, fy = B(*C["fm_xy"])
    add("U20", "DRV8837", "DRV8837DSGR", "WSON-8_2x2_DRV8837",
        {"8": "+3V3", "1": "+5V", "6": "FEEL_IN1", "5": "FEEL_IN2", "7": "FEEL_nSLEEP", "2": "FEEL_A", "3": "FEEL_B", "4": "GND", "9": "GND"},
        (fx - 7.5, fy, 0), {"MPN": "DRV8837DSGR", "Manufacturer": "TI", "LCSC": "C39159", "Datasheet": DS["DRV8837"]}, side="B")
    passive("C20", "C", "100n", "C_0402", "+3V3", "GND", (fx - 7.5, fy - 2.2, 0))
    passive("C21", "C", "100n", "C_0402", "+5V", "GND", (fx - 10.4, fy - 1.0, 90))
    passive("C22", "C", "10u", "C_0603", "+5V", "GND", (fx - 12.2, fy - 1.0, 90))
    lit = lighting_build.build()
    lighting_build.attach_pins(lit.out, PINS)
    out.extend(lit.out)
    # +3V3 is driven by U22. +5V is the board input. GND needs one power_out.
    for i, n in enumerate(("+5V", "GND")):
        out.append(dict(ref=f"#FLG0{i + 1}", sym="PWR_FLAG", pins=PINS["PWR_FLAG"], value="PWR_FLAG", footprint="", nets={"1": n}, fields={}, bom=False, place=None, side=None))
    return out

# board-only mechanical footprints (no schematic symbol)
MECH = [("H2", "Bearing_F682ZZ_Press_NPTH_5.0mm", (*B(*C["enc_xy"]), 0), "F")]
MECH += lighting_build.build().mech
