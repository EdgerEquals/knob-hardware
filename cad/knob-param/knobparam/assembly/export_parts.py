"""v0.19: one STEP per printed part (panel frame), with material and process, plus a bought-parts BOM.

Material recipe [Ed, 2 Nov]: MJF PA-12 for gears and structure, SLA UTR-8100 clear resin for clear parts,
ASA-CF for the back cover (v0.20, Ed 2 Nov; was PETG). Anything the rules below do not place is listed as UNASSIGNED so it is not missed.
Run: python -m knobparam.assembly.export_parts  (from cad/knob-param)."""
import csv, os, re, sys
from collections import OrderedDict

# (regex on the part name, kind, material, process). First match wins. kind: print | buy | board | ref
RULES = [
    # v0.33 [Ed 4 Nov 21:30] step 2, decision 3 option B: the jack board (jacks soldered on), the jack power board under it, and
    # (v0.47, Q23) the jack lower board under that
    (r"^clear OLED flex", "ref", "the clear OLED's own flex (part of the display)", "-"),
    (r"^link flex", "buy", "custom FPC, single-sided PI, 25 lines at 0.3, PI stiffener at the contacts (Q29) [A]", "PCBWay"),
    (r"^USB spring contact", "buy", "Harwin P70-5100045 spring contact, Ø1.03, 2 A, works 3.85-4.20 [S-dist]", "on the jack board PCBA"),
    (r"^USB-C board (VBUS TVS|data ESD)", "buy", "TVS / ESD (LCSC) [A]", "on the USB-C board PCBA"),
    (r"^jack unit post", "buy", "brass Ø2 pin [A] (soldered in the jack power board's tab)", "buy"),
    (r"^jack (power |lower )?board .*envelope", "ref", "parts envelope [A] (the parts come with the KiCad boards)", "-"),
    (r"^jack (power |lower )?board.*(ZIF|headers|stacks|FPC connector)", "buy",
     "FPC connector (XUNPU C2856805 / Hirose FH26W C2904698) / XFCN 1.27 stack (C2840009 + C2840010)", "on the PCBA"),
    (r"^jack board|^jack power board|^jack lower board", "board", "jack boards, FR-4 [A] (KiCad)", "PCBWay PCBA"),
    # [Ed 3 Nov 12:41-12:58] v0.24 dial screen as a bezel cartridge (Waveshare Z132A2441), dial board, rod-link board, strap loop
    (r"^dial bezel", "print", "PA-12, dyed black [A] (bezel material open: MJF to match the dial, or SLA [C])", "MJF"),
    (r"^dial screen Z132A2441", "buy", "Waveshare Z132A2441-V0 1.32in AMOLED (lens, panel, flex, 24-pin plug) [C: bare panel source]", "buy"),
    (r"^dial cartridge plug pad", "print", "PA-12", "MJF"),
    (r"^dial board \(", "board", "dial board (FR-4 0.8, PCBA)", "PCBWay PCBA"),
    (r"^dial board ", "board", "PCBA parts (ESP32-S3-PICO-1-N8R8, LDO, PHY, 24-pin 0.4 receptacle, 405 nm diode, LEDs)", "PCBWay PCBA"),
    (r"^dial strap loop", "buy", "flex, 2-layer PI, 4 lines (2 + 2 spares)", "buy"),
    (r"^rod-link board", "board", "rod-link board (FR-4)", "PCBWay PCBA"),
    (r"^control dial lower part|^control dial dish", "print", "PA-12", "MJF"),   # 10 Nov sweep: its name says "spring column"
    (r"^MCU ", "board", "PCBA parts (STM32H743VIT6, LQFP100; Q33 = A, 7 Nov)", "PCBWay PCBA"),
    (r"^power light VCSEL", "buy", "JNJOPTO JNJ-V-2835CW-665003-S-D1 red VCSEL (LCSC C42375664), the power light", "on the PCBA"),   # [Ed 3 Nov] v0.23: main PCB front, under the joystick
    # [Ed 3 Nov] v0.23 layout v4: vertical boards under the joystick (the joystick's own parts are listed by cad/joystick-param)
    (r"^vertical board [LR] \(", "board", "vertical board (FR-4, parts on both faces)", "PCBWay PCBA"),
    (r"^vertical board [LR] header", "buy", "right-angle 1.27 mm two-row hybrid THT / SMT header (on the PCBA)", "on the PCBA"),
    (r"^vertical board [LR] male pins", "buy", "right-angle 1.27 mm single-row male header, SMT (on the PCBA)", "on the PCBA"),
    # the joystick's parts (viewer colours; its BOM is cad/joystick-param's)
    (r"top-board socket", "buy", "1.27 mm single-row female socket 3.4, SMT (on the top-board PCBA)", "on the PCBA"),
    (r"up-stop cushion", "buy", "BISCO HT-870 silicone sponge ring 1.59, die-cut", "buy"),
    (r"top board", "board", "joystick top board (FR-4)", "PCBWay PCBA"),
    (r"foam pad", "buy", "foam tape (PET carrier), cut to shape", "buy"),   # v0.6 joystick screen pads
    (r"SKRHADE010", "buy", "Alps SKRHADE010 switch (on the top-board PCBA)", "on the PCBA"),
    # v0.25 (dial job): "non-magnetic" springs read as magnets and the spring anchor pins as printed anchors; the detent block's
    # name mentions its pins (hardware rule); the cap's inner hub is PA-12 [Ed 19:46]. Explicit rules ahead of the generic ones.
    (r"^centring spring", "buy", "stainless 316 extension spring, OD 1.6, wire 0.2, extended hooks (non-magnetic; v0.31 rate / free lengths in check.json)", "buy"),
    (r"^spring pin on", "buy", "steel dowel Ø0.8 (spring hook pin, pressed into the Hall arm's column)", "buy"),
    (r"^spring anchor pin", "buy", "steel dowel Ø0.8 (spring anchor, pressed into a cradle post)", "buy"),
    (r"^detent block \(", "print", "UTR-8100 clear resin (glued on two Ø1 pins) [Ed 18:15]", "SLA"),
    (r"^knob upper-cap hub", "print", "PA-12: hub-gear teeth + 45° ball race, keyed and glued into the clear cap [Ed 19:46]", "MJF"),
    (r"magnet", "buy", "N52 magnet", "buy"),
    (r"locating pin|dowel", "buy", "steel dowel", "buy"),
    (r"FPC|jumper|B2B", "buy", "flex / connector", "buy"),
    (r"O-ring", "buy", "silicone O-ring (metric)", "buy"),
    (r"knob upper-cap", "print", "UTR-8100 clear resin (PCBWay lists no WaterShed XC, 3 Nov) [Ed 19:00]", "SLA"),   # v0.19b-v0.24: PA-12 MJF (it carried the hub gear)
    (r"base cradle", "print", "UTR-8100 clear resin (clear race fused in)", "SLA"),   # the race land is the light path
    (r"train pedestal", "print", "UTR-8100 clear resin", "SLA"),   # v0.22b: before the hardware rule (its name says 'grub-set')
    (r"anchor", "print", "PA-12", "MJF"),             # joystick rear spring anchor (printed), not a spring
    (r"ball|ruby", "buy", "steel / glass / ruby balls", "buy"),
    (r"^PCB$|^PCB back parts|^PCB front parts|^PCB rod pad", "board", "FR-4 main PCB (KiCad)", "PCBWay PCBA"),
    (r"^emitter ", "buy", "SK6812MINI-E reverse-mount RGB (LCSC C5149201)", "on the PCBA"),
    (r"^hall sensor", "board", "PCBA parts", "PCBWay PCBA"),
    (r"^encoder sensor", "board", "EE-SX1321 on the main board's back (Q27; LCSC C469128)", "PCBWay PCBA"),
    (r"^case$", "print", "UTR-8100 clear resin, front face polished; the joystick cradle printed in (v0.25, Ed 18:35)", "SLA"),
    (r"^USB-C key", "print", "UTR-8100 clear resin [A], printed with the case; fills the bottom-wall channel behind the USB-C board, "
                             "held in by the back cover (v0.32, Ed 4 Nov 20:15)", "SLA"),
    (r"glow coat", "ref", "Shimicoat strontium aluminate, brushed", "Ed"),
    (r"back cover|lower screen pad", "print", "ASA-CF, black (print floor-down; PET/Kapton film under the screens)", "FDM"),
    (r"cap\b|caps\b|Fresnel", "print", "UTR-8100 clear resin", "SLA"),
    (r"glass|sleeve \(borosilicate|borosilicate", "buy", "borosilicate tube", "buy"),
    (r"^back AMOLED|screen panel|^screen\b|AMOLED|clear OLED", "buy", "display", "buy"),
    (r"^jack |PJ366ST|bushing|^USB-C receptacle", "buy", "PJ366ST jack / USB-C", "buy"),
    (r"^USB-C board \(socket", "board", "USB-C board (socket, TVS, ESD; v0.37: PD chip on the jack power board)", "PCBWay PCBA"),
    (r"^motor$|1220", "buy", "motor", "buy"),
    (r"bearing(?! 2 seat)", "buy", "F682ZZ bearing", "buy"),
    (r"bearing 2 seat", "print", "PA-12", "MJF"),
    (r"\binsert\b", "buy", "brass heat-set insert (M2.5 case corners, M2 joystick guides)", "buy"),   # 10 Nov sweep: was the brass tube rule
    (r"brass tube|brass", "buy", "brass 5x3 tube", "buy"),
    (r"rod|nut|screw|grub|pin\b|pins\b|dowel|shaft", "buy", "steel / brass hardware", "buy"),
    (r"spring", "buy", "stainless 316 / phosphor bronze spring", "buy"),
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
