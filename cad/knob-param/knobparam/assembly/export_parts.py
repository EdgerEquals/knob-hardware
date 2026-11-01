"""v0.19: one STEP per printed part (panel frame), with material and process, plus a bought-parts BOM.

Material recipe [Ed, 2 Nov]: MJF PA-12 for gears and structure, SLA UTR-8100 clear resin for clear parts,
PETG for the back cover. Anything the rules below do not place is listed as UNASSIGNED so it is not missed.
Run: python -m knobparam.assembly.export_parts  (from cad/knob-param)."""
import csv, os, re, sys
from collections import OrderedDict

# (regex on the part name, kind, material, process). First match wins. kind: print | buy | board | ref
RULES = [
    (r"^PCB$|^PCB back parts|^PCB rod pad", "board", "FR-4 main PCB (KiCad)", "PCBWay PCBA"),
    (r"^emitter ", "buy", "VCSEL / RGB LED (LCSC)", "on the PCBA"),
    (r"^hall sensor|^adapter part|^adapter board", "board", "PCBA parts", "PCBWay PCBA"),
    (r"^encoder daughterboard|^encoder header|^encoder sensor", "board", "encoder daughterboard (EE-SX1321)", "PCBWay PCBA"),
    (r"^case$", "print", "UTR-8100 clear resin, front face polished", "SLA"),
    (r"glow coat", "ref", "Shimicoat strontium aluminate, brushed", "Ed"),
    (r"back cover|lower screen pad", "print", "PETG, smoky/black", "FDM"),
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
    (r"ball", "buy", "steel / glass / ruby balls", "buy"),
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
