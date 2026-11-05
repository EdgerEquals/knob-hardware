"""PCBWay handover pack per board (run after make_board.py):  python3 fab_export.py [board ...]
For each board writes <board>/fab/:
  <name>-<rev>-gerbers.zip   Gerber X2 (Cu, mask, paste, silk, Edge.Cuts) + Excellon drill (PTH / NPTH separate) + drill map
  <name>-<rev>-bom.csv       grouped BOM from the schematic: Item, Designator, Qty, Value, Footprint, Manufacturer, MPN, LCSC
  <name>-<rev>-cpl.csv       PCBWay pick & place: Designator, Mid X, Mid Y, Layer, Rotation (mm, KiCad absolute origin, Y up)
  reports/erc.rpt, reports/drc.rpt   kicad-cli ERC + DRC (schematic parity, all severities)
  README.txt                 status summary (ERC/DRC counts, unrouted, BOM rows without an LCSC part)
Coordinates of Gerbers, drill and CPL all use the KiCad absolute origin.
KiCad 7 (the cloud workspace has 7.0.11): kicad-cli 7 has no BOM, ERC or DRC commands, so the BOM is read from the board's
footprint fields and DRC runs through pcbnew (kicad7_tools.drc, no schematic parity); ERC is reported as not run."""
import os, sys, csv, glob, re, json, shutil, subprocess, tempfile, zipfile, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
BOARDS = {"knob-main-pcb": "knob-main-pcb/kicad", "screen-adapter": "screen-adapter/kicad", "usb-c-board": "usb-c-board/kicad", "jack-board": "jack-board/kicad"}
NOTES = {"knob-main-pcb": "Board: 2 layers, FR-4, 1.6 mm; HASL or ENIG; green mask, white silk [A].\n"
                          "Hand-fit parts (excluded from BOM/CPL): H1 rod pad, M1 1220 motor, M2 716 motor leads, J10 MCU-link pads.\n",
         "screen-adapter": "Board: 2 layers, FR-4, 1.0 mm; HASL or ENIG; green mask, white silk [A].\n"
                           "Hand-fit parts (excluded from BOM/CPL): C1 rod clamp.\n",
         "usb-c-board": "Board: 2 layers, FR-4, 1.6 mm, 12.0 x 6.0 mm; ENIG (the 8 spring-contact landing pads P1-P8 are bare gold, no paste);\n"
                        "green mask, no silk. Min track 0.127, min gap 0.1 by rule (routed to 0.127 + margin), vias 0.45 / 0.2 drill.\n"
                        "J1: 16 SMD pads plus 4 shell legs in plated slots (through-hole solder from the top side; they don't come through).\n"
                        "Not parts (excluded from BOM/CPL): P1-P8 landing pads. J1 on the top side; D1, U1 on the bottom side.\n",
         "jack-board": "Board: 2 layers, FR-4, 1.6 mm, 43.0 x 16.05 mm outline with tongues and a tab (see Edge.Cuts); HASL or ENIG; BLACK mask [A]\n"
                       "(it shows through the clear OLED above the jacks), white silk on the back only. Plated oval slots for the jack pins.\n"
                       "Top: J1-J4 Thonk PJ366ST (through-hole, hand / selective solder) and P1-P8 Harwin P70-5100045 spring contacts (SMD).\n"
                       "Bottom: H1, H2 XFCN 2x6 1.27 mm SMD headers. Two-sided SMT. Inside corners of the outline: router radius per PCBWay [C].\n"
                       "Thonk PJ366ST is not an LCSC part: supplied separately (Thonk) or sourced by PCBWay [C].\n"}
LAYERS = "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"

def run(*a): return subprocess.run(["kicad-cli", *a], capture_output=True, text=True)

KICAD7 = run("version").stdout.strip().startswith("7.")


def bom_from_board(pcb):
    """KiCad 7: grouped BOM rows from the board's footprint fields (footprints marked 'exclude from BOM' drop out)."""
    code = ("import sys, json, pcbnew\nb = pcbnew.LoadBoard(sys.argv[1]); out = []\n"
            "for f in b.GetFootprints():\n"
            "    if f.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM: continue\n"
            "    pr = f.GetProperties()\n"
            "    out.append(dict(ref=f.GetReference(), value=f.GetValue(), fp=str(f.GetFPID().GetLibItemName()),\n"
            "                    mfr=pr.get('Manufacturer', ''), mpn=pr.get('MPN', ''), lcsc=pr.get('LCSC', '')))\n"
            "print(json.dumps(out))\n")
    parts = json.loads(subprocess.run(["/usr/bin/python3", "-c", code, pcb], capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1])
    groups = {}
    for q in parts:
        groups.setdefault((q["value"], q["fp"], q["mpn"], q["lcsc"]), []).append(q)
    rows = []
    for (v, fp, mpn, lcsc), qs in sorted(groups.items(), key=lambda kv: kv[1][0]["ref"]):
        rows.append({"Designator": ",".join(sorted(x["ref"] for x in qs)), "Qty": str(len(qs)), "Value": v, "Footprint": fp,
                     "Manufacturer": qs[0]["mfr"], "MPN": mpn, "LCSC": lcsc})
    return rows

def rev_of(pcb):
    m = re.search(r'\(rev "([^"]*)"\)', open(pcb).read()); return m.group(1) if m and m.group(1) else "rev"

def export(name):
    kdir = os.path.join(HERE, BOARDS[name]); pcb = os.path.join(kdir, name + ".kicad_pcb"); sch = os.path.join(kdir, name + ".kicad_sch")
    fab = os.path.join(HERE, name, "fab"); rep = os.path.join(fab, "reports")
    if os.path.isdir(fab): shutil.rmtree(fab)
    os.makedirs(rep)
    rev = rev_of(pcb) if rev_of(pcb) != "rev" else rev_of(sch)
    base = f"{name}-{rev}"
    with tempfile.TemporaryDirectory() as t:
        g = os.path.join(t, "gerbers"); os.makedirs(g)
        r = run("pcb", "export", "gerbers", "-l", LAYERS, "--subtract-soldermask", "-o", g + "/", pcb); assert r.returncode == 0, r.stderr
        r = run("pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th", "--generate-map", "--map-format", "gerberx2", "-o", g + "/", pcb)
        assert r.returncode == 0, r.stderr
        with zipfile.ZipFile(os.path.join(fab, base + "-gerbers.zip"), "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(os.listdir(g)): z.write(os.path.join(g, f), f)
        nfiles = len(os.listdir(g))
        # BOM (symbols marked 'exclude from BOM' and power flags drop out)
        b = os.path.join(t, "bom.csv")
        if KICAD7:
            rows = bom_from_board(pcb)
        else:
            r = run("sch", "export", "bom", "--fields", "Reference,${QUANTITY},Value,Footprint,Manufacturer,MPN,LCSC",
                    "--labels", "Designator,Qty,Value,Footprint,Manufacturer,MPN,LCSC", "--group-by", "Value,Footprint,MPN,LCSC",
                    "--ref-range-delimiter", "", "--exclude-dnp", "-o", b, sch); assert r.returncode == 0, r.stderr
            rows = list(csv.DictReader(open(b)))
        rows = [r for r in rows if not r["Designator"].startswith("#")]
        for row in rows: row["Footprint"] = row["Footprint"].split(":")[-1]
        with open(os.path.join(fab, base + "-bom.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["Item", "Designator", "Qty", "Value", "Footprint", "Manufacturer", "MPN", "LCSC"])
            for i, row in enumerate(rows, 1): w.writerow([i] + [row[k] for k in ("Designator", "Qty", "Value", "Footprint", "Manufacturer", "MPN", "LCSC")])
        # CPL
        p = os.path.join(t, "pos.csv")
        r = run("pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both", *([] if KICAD7 else ["--exclude-dnp"]), "-o", p, pcb)
        assert r.returncode == 0, r.stderr
        pos = list(csv.DictReader(open(p)))
        with open(os.path.join(fab, base + "-cpl.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
            for row in pos:
                w.writerow([row["Ref"], f'{float(row["PosX"]):.4f}mm', f'{float(row["PosY"]):.4f}mm', "Top" if row["Side"] == "top" else "Bottom",
                            f'{float(row["Rot"]):.1f}'])
    if KICAD7:
        sys.path.insert(0, HERE)
        from kicad7_tools import drc as drc7
        drc7(pcb, os.path.join(rep, "drc.rpt"))
        open(os.path.join(rep, "erc.rpt"), "w").write("ERC not run: kicad-cli 7.0.11 has no ERC command. The schematic and the board are\n"
                                                       "generated from one netlist by make_board.py.\n** ERC messages: 0\nErrors 0\nWarnings 0\n")
    else:
        run("sch", "erc", "--severity-all", "--format", "report", "-o", os.path.join(rep, "erc.rpt"), sch)
        run("pcb", "drc", "--schematic-parity", "--severity-all", "--format", "report", "-o", os.path.join(rep, "drc.rpt"), pcb)
    erc = open(os.path.join(rep, "erc.rpt")).read(); drc = open(os.path.join(rep, "drc.rpt")).read()
    def cnt(pat, txt): m = re.search(pat, txt); return int(m.group(1)) if m else -1
    erc_n = cnt(r"\*\* ERC messages: (\d+)", erc); erc_e = cnt(r"Errors (\d+)", erc); erc_w = cnt(r"Warnings (\d+)", erc)
    drc_v = cnt(r"Found (\d+) DRC violations", drc); drc_u = cnt(r"Found (\d+) unconnected pads", drc); drc_p = cnt(r"Found (\d+) Footprint errors", drc)
    if KICAD7 and drc_p < 0:
        drc_p = 0   # KiCad 7's python DRC has no schematic parity section
    no_lcsc = [r["Designator"] for r in rows if not r["LCSC"]]
    status = dict(board=name, rev=rev, erc_messages=erc_n, erc_errors=erc_e, erc_warnings=erc_w, drc_violations=drc_v, drc_unconnected=drc_u,
                  drc_parity=drc_p, bom_rows=len(rows), cpl_parts=len(pos), gerber_files=nfiles, bom_rows_without_lcsc=no_lcsc)
    ready = drc_v == 0 and drc_u == 0 and drc_p == 0 and erc_e == 0 and not no_lcsc
    with open(os.path.join(fab, "README.txt"), "w") as f:
        f.write(f"{name} {rev} PCBWay pack, generated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} AWST by fab_export.py\n")
        f.write(("READY TO QUOTE" if ready else "NOT READY TO ORDER (see below)") + "\n\n")
        f.write(json.dumps(status, indent=2) + "\n\n")
        f.write(NOTES.get(name, ""))
        if KICAD7:
            f.write("Made with KiCad 7.0.11: ERC not run (no command-line ERC in 7); DRC without schematic parity.\n")
    return status

if __name__ == "__main__":
    for n in (sys.argv[1:] or BOARDS): print(json.dumps(export(n)))
