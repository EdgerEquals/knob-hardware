"""v0.19: one STEP per printed part (panel frame), with material and process, plus a bought-parts BOM.

Material recipe [Ed, 2 Nov]: MJF PA-12 for gears and structure, SLA UTR-8100 clear resin for clear parts,
ASA-CF for the back cover (v0.20, Ed 2 Nov; was PETG). Anything the rules below do not place is listed as UNASSIGNED so it is not missed.
Run: python -m knobparam.assembly.export_parts  (from cad/knob-param)."""
import csv, os, re, sys
from collections import OrderedDict

# (regex on the part name, kind, material, process). First match wins. kind: print | buy | board | ref
RULES = [
    # [Ed 3 Nov 12:41-12:58] v0.24 dial screen as a bezel cartridge (Waveshare Z132A2441), dial board, rod-link board, strap loop
    (r"^dial bezel", "print", "PA-12, dyed black [A] (bezel material open: MJF to match the dial, or SLA [C])", "MJF"),
    (r"^dial screen Z132A2441", "buy", "Waveshare Z132A2441-V0 1.32in AMOLED (lens, panel, flex, 24-pin plug) [C: bare panel source]", "buy"),
    (r"^dial cartridge plug pad", "print", "PA-12", "MJF"),
    (r"^dial board \(", "board", "dial board (FR-4 0.8, PCBA)", "PCBWay PCBA"),
    (r"^dial board ", "board", "PCBA parts (ESP32-S3-PICO-1-N8R8, LDO, PHY, 24-pin 0.4 receptacle, 405 nm diode, LEDs)", "PCBWay PCBA"),
    (r"^dial strap loop", "buy", "flex, 2-layer PI, 4 lines (2 + 2 spares)", "buy"),
    (r"^rod-link board", "board", "rod-link board (FR-4)", "PCBWay PCBA"),
    (r"^MCU ", "board", "PCBA parts (STM32H7B0VBT6, LQFP100)", "PCBWay PCBA"),   # [Ed 3 Nov] v0.23: main PCB front, under the joystick
    # [Ed 3 Nov] v0.23 layout v4: vertical boards under the joystick, and the joystick's case cradle / gasket / top board
    (r"^vertical board [LR] \(", "board", "vertical board (FR-4, parts on both faces)", "PCBWay PCBA"),
    (r"^vertical board [LR] header", "buy", "right-angle 1.27 mm two-row hybrid THT / SMT header (on the PCBA)", "on the PCBA"),
    # v0.24 [Ed 13:31-14:08]: pins into sockets, the bead, the up-stop cushions
    (r"^vertical board [LR] male pins", "buy", "right-angle 1.27 mm single-row male header, SMT (on the PCBA)", "on the PCBA"),
    (r"top-board socket", "buy", "1.27 mm single-row female socket 3.4, SMT (on the top-board PCBA)", "on the PCBA"),
    (r"form-in-place", "buy", "form-in-place silicone bead (dispensed)", "dispense"),
    (r"up-stop cushion", "buy", "BISCO HT-870 silicone sponge ring 1.59, die-cut", "buy"),
    (r"^vertical board [LR] spring contacts", "buy", "right-angle spring-contact (pogo) strip (on the PCBA)", "on the PCBA"),
    (r"^vertical boards' standoff", "buy", "M2 female-female brass standoff", "buy"),
    (r"case cradle", "print", "UTR-8100 clear resin", "SLA"),
    (r"gasket", "buy", "closed-cell silicone sponge gasket, die-cut", "buy"),
    (r"top board", "board", "joystick top board (FR-4, ENIG contact pads)", "PCBWay PCBA"),
    (r"magnet", "buy", "N52 magnet", "buy"),
    (r"locating pin|dowel", "buy", "steel dowel", "buy"),
    (r"saddle strap|saddle seat|screen carrier|holder", "print", "PA-12", "MJF"),
    (r"foam pad", "buy", "foam tape (PET carrier), cut to shape", "buy"),   # v0.6 joystick screen pads
    (r"FPC|jumper|B2B", "buy", "flex / connector", "buy"),
    (r"O-ring", "buy", "silicone O-ring (metric)", "buy"),
    (r"seal ring", "print", "PETG, opaque", "FDM"),   # v0.19b: before the glass rule (the name says 'bonded on the glass')
    (r"knob upper-cap", "print", "PA-12", "MJF"),     # v0.19b: carries the 1220 hub gear; was caught by the clear 'cap' rule
    (r"base cradle", "print", "UTR-8100 clear resin (clear race fused in)", "SLA"),   # the race land is the light path
    (r"train pedestal", "print", "UTR-8100 clear resin", "SLA"),   # v0.22b: before the hardware rule (its name says 'grub-set')
    (r"nylon", "buy", "nylon pinion (Tempero 0.5M-12T)", "buy"),
    (r"anchor", "print", "PA-12", "MJF"),             # joystick rear spring anchor (printed), not a spring
    (r"ball|ruby", "buy", "steel / glass / ruby balls", "buy"),
    (r"^PCB$|^PCB back parts|^PCB rod pad", "board", "FR-4 main PCB (KiCad)", "PCBWay PCBA"),
    (r"^emitter ", "buy", "VCSEL / RGB LED (LCSC)", "on the PCBA"),
    (r"^hall sensor|^adapter part|^adapter board", "board", "PCBA parts", "PCBWay PCBA"),
    (r"^encoder daughterboard|^encoder header|^encoder sensor", "board", "encoder daughterboard (EE-SX1321)", "PCBWay PCBA"),
    (r"^case$", "print", "UTR-8100 clear resin, front face polished", "SLA"),
    (r"glow coat", "ref", "Shimicoat strontium aluminate, brushed", "Ed"),
    (r"back cover|lower screen pad", "print", "ASA-CF, black (print floor-down; PET/Kapton film under the screens)", "FDM"),
    (r"cap\b|caps\b|Fresnel", "print", "UTR-8100 clear resin", "SLA"),
    (r"thrust carrier|thrust race|bottom thrust", "print", "UTR-8100 clear resin", "SLA"),
    (r"Risley wedge", "print", "UTR-8100 clear resin (acrylic fallback)", "SLA"),
    (r"glass|sleeve \(borosilicate|borosilicate", "buy", "borosilicate tube", "buy"),
    (r"^back AMOLED|screen panel|^screen\b|AMOLED|clear OLED", "buy", "display", "buy"),
    (r"^jack |PJ366ST|bushing|^USB-C receptacle", "buy", "PJ366ST jack / USB-C", "buy"),
    (r"USB-C PD board", "board", "USB-C PD board", "PCBWay PCBA"),
    (r"motor coreless|feel motor coreless|^motor$|1220", "buy", "motor", "buy"),
    (r"bearing(?! 2 seat)", "buy", "F682ZZ bearing", "buy"),
    (r"bearing 2 seat", "print", "PA-12", "MJF"),
    (r"brass tube|brass", "buy", "brass 5x3 tube", "buy"),
    (r"rod|nut|screw|grub|insert|pin\b|pins\b|dowel|shaft", "buy", "steel / brass hardware", "buy"),
    (r"ball|ruby", "buy", "steel / glass / ruby balls", "buy"),
    (r"thrust blank", "print", "UTR-8100 clear resin", "SLA"),
    (r"clear OLED", "buy", "EastRising ER-OLED1.51-1B (SSD1309, transparent)", "-"),
    (r"spring", "buy", "stainless 316 / phosphor bronze spring", "buy"),
    (r"magnet|cushion", "buy", "N52 magnet", "buy"),
    (r"FPC|jumper|strap|B2B", "buy", "flex / connector", "buy"),
    (r"gear|pinion|idler|ring\b|knob|dial|cradle|saddle|carrier|holder|disc|standoff|lever|arm|detent|hub|clip|seat", "print", "PA-12", "MJF"),
]


def classify(name):
    for rx, kind, mat, proc in RULES:
        if re.search(rx, name, re.I):
            return kind, mat, proc
    return "UNASSIGNED", "UNASSIGNED", "UNASSIGNED"


def slug(n):
    return re.sub(r"[^A-Za-z0-9]+", "-", n).strip("-").lower()[:80]


def main():
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, here)
    from build123d import export_step
    from knobparam.common import model
    from knobparam.assembly.build import build_all, view
    D = model.derive(model.default_params())
    parts, stats, keys, owner = build_all(D)
    parts, keys = view(parts, keys, D, "panel")
    out = os.path.join(os.path.dirname(here), "assemblies", f"knob-stack-{D['version']}")
    pdir = os.path.join(out, "parts")
    os.makedirs(pdir, exist_ok=True)
    rows = []
    for n, s in parts.items():
        kind, mat, proc = classify(n)
        bb = s.bounding_box()
        try:
            vol = sum(x.volume for x in s.solids())
        except Exception:
            vol = 0.0
        f = ""
        if kind == "print":
            f = os.path.join("parts", slug(n) + ".step")
            export_step(s, os.path.join(out, f))
        rows.append(OrderedDict(part=n, sub=owner.get(n, ""), kind=kind, material=mat, process=proc,
                                volume_mm3=round(vol, 2), size_mm=f"{bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}", step=f))
    with open(os.path.join(out, "parts.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    un = [r["part"] for r in rows if r["kind"] == "UNASSIGNED"]
    print(f"{len(rows)} parts, {sum(r['kind'] == 'print' for r in rows)} printed STEP files -> {out}")
    print("UNASSIGNED:", un or "none")


if __name__ == "__main__":
    main()
