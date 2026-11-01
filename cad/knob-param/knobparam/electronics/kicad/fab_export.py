"""PCBWay handover pack per board (run after make_board.py):  python3 fab_export.py [board ...]
For each board writes <board>/fab/:
  <name>-<rev>-gerbers.zip   Gerber X2 (Cu, mask, paste, silk, Edge.Cuts) + Excellon drill (PTH / NPTH separate) + drill map
  <name>-<rev>-bom.csv       grouped BOM from the schematic: Item, Designator, Qty, Value, Footprint, Manufacturer, MPN, LCSC
  <name>-<rev>-cpl.csv       PCBWay pick & place: Designator, Mid X, Mid Y, Layer, Rotation (mm, KiCad absolute origin, Y up)
  reports/erc.rpt, reports/drc.rpt   kicad-cli ERC + DRC (schematic parity, all severities)
  README.txt                 status summary (ERC/DRC counts, unrouted, BOM rows without an LCSC part)
Coordinates of Gerbers, drill and CPL all use the KiCad absolute origin."""
import os, sys, csv, glob, re, json, shutil, subprocess, tempfile, zipfile, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
BOARDS = {"knob-main-pcb": "knob-main-pcb/kicad", "screen-adapter": "screen-adapter/kicad"}
LAYERS = "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"

def run(*a): return subprocess.run(["kicad-cli", *a], capture_output=True, text=True)

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
        r = run("pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both", "--exclude-dnp", "-o", p, pcb); assert r.returncode == 0, r.stderr
        pos = list(csv.DictReader(open(p)))
        with open(os.path.join(fab, base + "-cpl.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
            for row in pos:
                w.writerow([row["Ref"], f'{float(row["PosX"]):.4f}mm', f'{float(row["PosY"]):.4f}mm', "Top" if row["Side"] == "top" else "Bottom",
                            f'{float(row["Rot"]):.1f}'])
    run("sch", "erc", "--severity-all", "--format", "report", "-o", os.path.join(rep, "erc.rpt"), sch)
    run("pcb", "drc", "--schematic-parity", "--severity-all", "--format", "report", "-o", os.path.join(rep, "drc.rpt"), pcb)
    erc = open(os.path.join(rep, "erc.rpt")).read(); drc = open(os.path.join(rep, "drc.rpt")).read()
    def cnt(pat, txt): m = re.search(pat, txt); return int(m.group(1)) if m else -1
    erc_n = cnt(r"\*\* ERC messages: (\d+)", erc); erc_e = cnt(r"Errors (\d+)", erc); erc_w = cnt(r"Warnings (\d+)", erc)
    drc_v = cnt(r"Found (\d+) DRC violations", drc); drc_u = cnt(r"Found (\d+) unconnected pads", drc); drc_p = cnt(r"Found (\d+) Footprint errors", drc)
    no_lcsc = [r["Designator"] for r in rows if not r["LCSC"]]
    status = dict(board=name, rev=rev, erc_messages=erc_n, erc_errors=erc_e, erc_warnings=erc_w, drc_violations=drc_v, drc_unconnected=drc_u,
                  drc_parity=drc_p, bom_rows=len(rows), cpl_parts=len(pos), gerber_files=nfiles, bom_rows_without_lcsc=no_lcsc)
    ready = drc_v == 0 and drc_u == 0 and drc_p == 0 and erc_e == 0 and not no_lcsc
    with open(os.path.join(fab, "README.txt"), "w") as f:
        f.write(f"{name} {rev} PCBWay pack, generated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} AWST by fab_export.py\n")
        f.write(("READY TO QUOTE" if ready else "NOT READY TO ORDER (see below)") + "\n\n")
        f.write(json.dumps(status, indent=2) + "\n\n")
        f.write("Board: 2 layers, FR-4; thickness per the .kicad_pcb (main 1.6 mm, adapter 1.0 mm); HASL or ENIG; green mask, white silk [A].\n")
        f.write("Hand-fit parts (excluded from BOM/CPL): main H1 rod pad, M1 1220 motor, M2 716 motor leads, J10 MCU-link pads; adapter C1 rod clamp.\n")
    return status

if __name__ == "__main__":
    for n in (sys.argv[1:] or BOARDS): print(json.dumps(export(n)))
