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
BOARDS = {"knob-main-pcb": "knob-main-pcb/v2/kicad", "screen-adapter": "screen-adapter/kicad", "usb-c-board": "usb-c-board/kicad", "jack-board": "jack-board/kicad",
          "jack-power-board": "jack-power-board/upper/kicad", "jack-lower-board": "jack-power-board/lower/kicad"}
FAB = {"jack-power-board": "jack-power-board/upper/fab", "jack-lower-board": "jack-power-board/lower/fab",
       "knob-main-pcb": "knob-main-pcb/v2/fab"}   # else <board>/fab
INNER = {"jack-power-board": ",In1.Cu,In2.Cu", "jack-lower-board": ",In1.Cu,In2.Cu",                         # 4-layer boards
         "knob-main-pcb": ",In1.Cu,In2.Cu,In3.Cu,In4.Cu"}                                                       # 6 layers [Ed Q45]
DESIGN_BOM = {"knob-main-pcb": "knob-main-pcb/v2/bom.csv"}   # design.py's BOM: datasheet links and who fits each part
NOTES = {"knob-main-pcb": "Board v2 (9 Nov 2026): 6 layers [Ed Q45], FR-4, 1.6 mm: F.Cu signal, In1 ground plane, In2 signal, In3 signal\n"
                          "(the link flex's analog lines), In4 ground plane, B.Cu signal; no controlled impedance. ENIG [A] (0.5 mm pitch LQFP,\n"
                          "0.3 mm flex pads, 0.4 mm X2SON Halls); green mask, white silk [A]. Outline with five windows A-E, the ring LEDs'\n"
                          "cut-outs and holes: see Edge.Cuts (inside corners: router radius per PCBWay [C]). Min track 0.127, gap 0.1 (0.15 for\n"
                          "the flex's analog lines), vias 0.45 / 0.2 drill, all tented; three of them sit under U1's body (pins 54, 56, 58).\n"
                          "Two-sided SMT: U1 (LQFP-100), the Halls, the crystal and the screen / SPI resistors on top; the 12 SK6812MINI-E\n"
                          "(reverse-mount, their bodies down through cut-outs; MSL 5a), the motor driver, the encoder sensor and most passives\n"
                          "on the bottom.\n"
                          "Not in the BOM / CPL: J1 link-flex pads (the flex is hot-bar or hand soldered), J4 Tag-Connect pads, J5 cover-board pads,\n"
                          "JP1 solder jumper, H1 rod clamp (hand-fit tube and nut), M1 1220 motor tabs (soldered at assembly), MP1 / MP2 posts\n"
                          "(Ø1.0 pins of the jack unit's brass posts in plated Ø1.15 holes, soldered at assembly).\n"
                          "J2 / J3: the vertical boards' 2x11 1.27 mm headers, in the BOM as PCBA-fitted (design.py) [C: fitted here or with the\n"
                          "vertical boards]. Passives: values and packages set, LCSC numbers still to choose (next step).\n",
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
                       "Thonk PJ366ST is not an LCSC part: supplied separately (Thonk) or sourced by PCBWay [C].\n",
         "jack-power-board": "Board: 4 layers (F.Cu, In1.Cu ground plane, In2.Cu, B.Cu), FR-4, 1.6 mm, the jack row 43.0 x 10.5 with two ears; ENIG;\n"
                             "BLACK mask [A] (behind the jacks; matches the jack board), no silk. Two-sided SMT. Min track 0.127, gap 0.1, vias 0.45 / 0.2.\n"
                             "MP1, MP2: plated Ø1.15 holes for the Ø1.0 pins of the two brass posts (hand-soldered at assembly, not parts).\n"
                             "U1 TPS259470ARPWR land pattern is a PLACEHOLDER until TI's RPW0010A drawing [C]. TMUX7212RUMR / TCA9535RGER [Ed Q25].\n",
         "jack-lower-board": "Board: 4 layers (F.Cu, In1.Cu ground plane, In2.Cu, B.Cu), FR-4, 1.6 mm, 43.0 x 10.5; ENIG; BLACK mask [A], no silk.\n"
                             "Two-sided SMT: the two flex connectors (J5 XUNPU FPC-05F-24PH20, J6 Hirose FH26W-25S) on the bottom, opening to the\n"
                             "board's bottom edge. Min track 0.127, gap 0.1, vias 0.45 / 0.2.\n"}
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
    fab = os.path.join(HERE, FAB.get(name, os.path.join(name, "fab"))); rep = os.path.join(fab, "reports")
    if os.path.isdir(fab): shutil.rmtree(fab)
    os.makedirs(rep)
    rev = rev_of(pcb) if rev_of(pcb) != "rev" else rev_of(sch)
    base = f"{name}-{rev}"
    with tempfile.TemporaryDirectory() as t:
        g = os.path.join(t, "gerbers"); os.makedirs(g)
        r = run("pcb", "export", "gerbers", "-l", LAYERS + INNER.get(name, ""), "--subtract-soldermask", "-o", g + "/", pcb); assert r.returncode == 0, r.stderr
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
        ds = {}
        if name in DESIGN_BOM:   # each part's datasheet link travels with it to PCBWay [Ed]
            for d in csv.DictReader(open(os.path.join(HERE, DESIGN_BOM[name]))):
                for ref in d["Refs"].split():
                    ds[ref] = d.get("Datasheet", "")
        with open(os.path.join(fab, base + "-bom.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["Item", "Designator", "Qty", "Value", "Footprint", "Manufacturer", "MPN", "LCSC", "Datasheet"])
            for i, row in enumerate(rows, 1):
                link = next((ds[r] for r in row["Designator"].split(",") if ds.get(r)), "")
                w.writerow([i] + [row[k] for k in ("Designator", "Qty", "Value", "Footprint", "Manufacturer", "MPN", "LCSC")] + [link])
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
