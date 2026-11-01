"""Authoring script for the KiCad top-screen joystick daughterboard (KiCad is the single source of truth for the board).
Run with the system python that has pcbnew:  /usr/bin/python3 make_project.py
Writes the schematic, the board, the symbols and the lib tables, then ERC + DRC (schematic parity, all severities),
the STEP, and the fab/ pack (Gerbers, drill, BOM, CPL, reports, README).

v0.2 (2026-11-01, Ed): same SKRHADE010 at -45° (a/b/c/d → UP/RIGHT/LEFT/DOWN, confirmed at first-power calibration).
Frame tabs (pads 7 and 8) are tied to GND. Two M2×11 brass standoffs (MH1, MH2) are PTH to GND; J1 pin 5 stays GND.
J2 on the main PCB is the 11 mm socket (hanxia HX PM2.54-2x3P ZC H11), not the 8.5 mm part.
Board 19.2 × 13.8 × 1.0, centred at CAD (0.2, -3.2). Numbers mirror cad/joystick-param (CAD y up = KiCad y down).
"""
import os, json, uuid, subprocess, math, csv, shutil, tempfile, zipfile, datetime, re
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__)); NAME = "joystick-daughterboard"
REV = "v0.2"
ORIGIN = (100.0, 100.0)          # KiCad position of the carrier centre
# geometry from jsparam v0.2 (carrier frame, y up)
DB_W, DB_H, DB_T = 19.2, 13.8, 1.0
DB_XY = (0.2, -3.2)
CORNER_R = 0.5
SW_XY, SW_ROT = (-3.0, -1.2), -45.0
HDR_XY = (5.9, -1.0)
STANDOFFS = ((-7.5, -8.0), (7.2, -7.6))
NETS = ["GND", "SW_UP", "SW_DOWN", "SW_LEFT", "SW_RIGHT", "SW_CENTER"]
SW_PINS = {"1": "SW_UP", "2": "SW_CENTER", "3": "SW_LEFT", "4": "SW_RIGHT", "5": "GND", "6": "SW_DOWN", "7": "GND", "8": "GND"}
J_PINS = {"1": "SW_UP", "2": "SW_CENTER", "3": "SW_RIGHT", "4": "SW_LEFT", "5": "GND", "6": "SW_DOWN"}
ROOT = "6a0f3c1e-1f0b-4b8e-9d55-7e1f0a2b3c01"
SW_UUID = "6a0f3c1e-1f0b-4b8e-9d55-7e1f0a2b3c02"
J_UUID = "6a0f3c1e-1f0b-4b8e-9d55-7e1f0a2b3c03"
MH_UUID = ["6a0f3c1e-1f0b-4b8e-9d55-7e1f0a2b3c04", "6a0f3c1e-1f0b-4b8e-9d55-7e1f0a2b3c05"]
# BOM identity. The socket is on the main PCB, not on this board.
PARTS = {
    "SW1": ("Alps Alpine", "SKRHADE010", "C202415"),
    "J1": ("LXWCONN", "254PZ-2x3P-V", "C53055678"),
    "MH1": ("XHHD", "STTZ2008", "C50377192"),
    "MH2": ("XHHD", "STTZ2008", "C50377192"),
}

def sym_skrh(name):
    pins = [("1", "A", -12.7, 7.62, 0), ("2", "Center", -12.7, 2.54, 0), ("3", "C", -12.7, -2.54, 0),
            ("7", "Frame", -12.7, -7.62, 0),
            ("4", "B", 12.7, 7.62, 180), ("5", "Common", 12.7, 2.54, 180), ("6", "D", 12.7, -2.54, 180),
            ("8", "Frame", 12.7, -7.62, 180)]
    return _sym(name, "SW", "SKRHADE010", "footprints:Alps_SKRHADE010", "https://tech.alpsalpine.com/e/products/detail/SKRHADE010/",
                "Alps SKRH 4-direction + centre push. Frame tabs to GND", 10.16, 10.16, pins)

def sym_conn(name):
    pins = [(str(i + 1), f"Pin_{i + 1}", -7.62 if i % 2 == 0 else 7.62, 2.54 - (i // 2) * 2.54, 0 if i % 2 == 0 else 180) for i in range(6)]
    return _sym(name, "J", "254PZ-2x3P-V", "footprints:PinHeader_2x03_P2.54mm_Vertical", "",
                "2x3 2.54 mm header, 6 mm mating pin, plastic on top", 5.08, 5.08, pins)

def sym_mount(name):
    return _sym(name, "MH", "STTZ2008", "footprints:Mount_M2x11_Standoff", "",
                "M2x11 brass female-female standoff to GND", 5.08, 2.54, [("1", "GND", -7.62, 0, 0)])

def _sym(name, ref, val, fp, ds, desc, hw, hh, pins):
    base = name.split(":")[-1]
    P = [f'  (symbol "{name}" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)',
         f'    (property "Reference" "{ref}" (at 0 {hh + 1.27:.2f} 0) (effects (font (size 1.27 1.27))))',
         f'    (property "Value" "{val}" (at 0 {-hh - 1.27:.2f} 0) (effects (font (size 1.27 1.27))))',
         f'    (property "Footprint" "{fp}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'    (property "Datasheet" "{ds}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'    (property "Description" "{desc}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'    (property "Manufacturer" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'    (property "MPN" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'    (property "LCSC" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'    (symbol "{base}_0_1" (rectangle (start {-hw} {hh}) (end {hw} {-hh}) (stroke (width 0.254) (type default)) (fill (type background))))',
         f'    (symbol "{base}_1_1"']
    for num, nm, x, y, a in pins:
        P.append(f'      (pin passive line (at {x} {y} {a}) (length 2.54) (name "{nm}" (effects (font (size 1.27 1.27)))) (number "{num}" (effects (font (size 1.27 1.27)))))')
    P += ['    )', '  )']
    return "\n".join(P), {num: (x, y) for num, nm, x, y, a in pins}

def write_symlib():
    s1, _ = sym_skrh("SKRHADE010"); s2, _ = sym_conn("Conn_02x03"); s3, _ = sym_mount("Mount_M2")
    open(os.path.join(HERE, "joystick.kicad_sym"), "w").write(
        '(kicad_symbol_lib (version 20241209) (generator "make_project.py")\n' + s1 + "\n" + s2 + "\n" + s3 + "\n)\n")
    open(os.path.join(HERE, "sym-lib-table"), "w").write(
        '(sym_lib_table\n  (version 7)\n  (lib (name "joystick")(type "KiCad")(uri "${KIPRJMOD}/joystick.kicad_sym")(options "")(descr "joystick daughterboard symbols"))\n)\n')
    open(os.path.join(HERE, "fp-lib-table"), "w").write(
        '(fp_lib_table\n  (version 7)\n  (lib (name "footprints")(type "KiCad")(uri "${KIPRJMOD}/../footprints.pretty")(options "")(descr "Ed project footprints"))\n)\n')

def write_sch():
    sk, skp = sym_skrh("joystick:SKRHADE010"); cn, cnp = sym_conn("joystick:Conn_02x03"); mh, mhp = sym_mount("joystick:Mount_M2")
    def inst(lib, ref, val, fp, x, y, uid, pins, mfr, mpn, lcsc, ds=""):
        L = [f'  (symbol (lib_id "{lib}") (at {x} {y} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{uid}")',
             f'    (property "Reference" "{ref}" (at {x} {y - 12.7} 0) (effects (font (size 1.27 1.27))))',
             f'    (property "Value" "{val}" (at {x} {y + 12.7} 0) (effects (font (size 1.27 1.27))))',
             f'    (property "Footprint" "{fp}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))',
             f'    (property "Datasheet" "{ds}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))',
             f'    (property "Description" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))',
             f'    (property "Manufacturer" "{mfr}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))',
             f'    (property "MPN" "{mpn}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))',
             f'    (property "LCSC" "{lcsc}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))']
        L += [f'    (pin "{p}" (uuid "{uuid.uuid4()}"))' for p in pins]
        L += [f'    (instances (project "{NAME}" (path "/{ROOT}" (reference "{ref}") (unit 1))))', '  )']
        return L
    def label(net, x, y, left):
        a, j = (180, "right") if left else (0, "left")
        return f'  (label "{net}" (at {x:.2f} {y:.2f} {a}) (effects (font (size 1.27 1.27)) (justify {j} bottom)) (uuid "{uuid.uuid4()}"))'
    def wire(x0, y0, x1, y1):
        return f'  (wire (pts (xy {x0:.2f} {y0:.2f}) (xy {x1:.2f} {y1:.2f})) (stroke (width 0) (type default)) (uuid "{uuid.uuid4()}"))'
    sx, sy, jx, jy = 55.88, 60.96, 132.08, 60.96
    L = [f'(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0") (uuid "{ROOT}") (paper "A4")',
         f'  (title_block (title "Top-screen joystick daughterboard") (date "2026-11-01") (rev "{REV}") (company "Ed / Edger_Equals - knob module")',
         '    (comment 1 "SW1 Alps SKRHADE010 at -45 deg: a/b/c/d -> UP/RIGHT/LEFT/DOWN, confirmed at first-power calibration")',
         '    (comment 2 "Frame tabs 7 and 8, and MH1/MH2 M2x11 standoffs, are GND. J1 pin 5 is GND too")',
         '    (comment 3 "J1 2x3 male (plastic on top) into J2 hanxia 11 mm socket on the main PCB. Pull-ups and ESD on the MCU"))',
         '  (lib_symbols', sk, cn, mh, '  )']
    L += inst("joystick:SKRHADE010", "SW1", "SKRHADE010", "footprints:Alps_SKRHADE010", sx, sy, SW_UUID, list(skp), *PARTS["SW1"],
              "https://tech.alpsalpine.com/e/products/detail/SKRHADE010/")
    L += inst("joystick:Conn_02x03", "J1", "254PZ-2x3P-V", "footprints:PinHeader_2x03_P2.54mm_Vertical", jx, jy, J_UUID, list(cnp), *PARTS["J1"])
    for i, uid in enumerate(MH_UUID):
        L += inst("joystick:Mount_M2", f"MH{i + 1}", "STTZ2008", "footprints:Mount_M2x11_Standoff", 40.64, 104.14 + i * 15.24, uid, list(mhp), *PARTS[f"MH{i + 1}"])
    for pins, x0, y0, net in ((skp, sx, sy, SW_PINS), (cnp, jx, jy, J_PINS)):
        for num, (px, py) in pins.items():
            X, Y = x0 + px, y0 - py; left = px < 0; e = X - 5.08 if left else X + 5.08
            L.append(wire(X, Y, e, Y)); L.append(label(net[num], e, Y, left))
    for i in range(2):
        X, Y = 40.64 + mhp["1"][0], (104.14 + i * 15.24) - mhp["1"][1]
        L.append(wire(X, Y, X - 5.08, Y)); L.append(label("GND", X - 5.08, Y, True))
    L.append(f'  (text "v0.2. Directions at -45 deg: A(1)=UP, B(4)=RIGHT, C(3)=LEFT, D(6)=DOWN, 2=CENTRE, 5=COMMON.\\nFrame tabs 7 and 8 and the two M2x11 standoffs are GND. Diagonals = two contacts, read at first-power calibration.\\nNo ESD or pull-ups on this board." (exclude_from_sim no) (at 25.4 140 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{uuid.uuid4()}"))')
    L += ['  (sheet_instances (path "/" (page "1")))', ')']
    open(os.path.join(HERE, NAME + ".kicad_sch"), "w").write("\n".join(L) + "\n")

mm = pcbnew.FromMM
def P(x, y): return pcbnew.VECTOR2I(mm(ORIGIN[0] + x), mm(ORIGIN[1] - y))
def K(x, y): return pcbnew.VECTOR2I(mm(ORIGIN[0] + x), mm(ORIGIN[1] + y))

def build_board():
    b = pcbnew.BOARD(); ds = b.GetDesignSettings(); ds.SetBoardThickness(mm(DB_T)); ds.SetCopperLayerCount(2)
    ds.m_CopperEdgeClearance = mm(0.3); ds.m_TrackMinWidth = mm(0.2); ds.m_MinClearance = mm(0.15)
    ds.m_ViasMinSize = mm(0.5); ds.m_MinThroughDrill = mm(0.25); ds.m_HoleClearance = mm(0.25)
    nets = {}
    for n in NETS:
        ni = pcbnew.NETINFO_ITEM(b, "/" + n); b.Add(ni); nets[n] = ni
    def seg(a, c, layer=pcbnew.Edge_Cuts, w=0.05):
        s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT); s.SetLayer(layer); s.SetWidth(mm(w)); s.SetStart(a); s.SetEnd(c); b.Add(s)
    def arc(c, st):
        s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_ARC); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.05))
        s.SetCenter(c); s.SetStart(st); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T), False); b.Add(s)
    def text(t, x, y, layer, size=0.7):
        tx = pcbnew.PCB_TEXT(b); tx.SetText(t); tx.SetPosition(P(x, y)); tx.SetLayer(layer)
        tx.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); tx.SetTextThickness(mm(size * 0.15)); b.Add(tx)
    dx, dy = DB_XY; w2, h2, r = DB_W / 2, DB_H / 2, CORNER_R
    x0, x1, y0, y1 = dx - w2, dx + w2, dy - h2, dy + h2
    seg(P(x0 + r, y1), P(x1 - r, y1)); seg(P(x1, y1 - r), P(x1, y0 + r))
    seg(P(x1 - r, y0), P(x0 + r, y0)); seg(P(x0, y0 + r), P(x0, y1 - r))
    arc(P(x1 - r, y1 - r), P(x1 - r, y1)); arc(P(x1 - r, y0 + r), P(x1, y0 + r))
    arc(P(x0 + r, y0 + r), P(x0 + r, y0)); arc(P(x0 + r, y1 - r), P(x0, y1 - r))
    lib = os.path.normpath(os.path.join(HERE, "..", "footprints.pretty"))
    sw = pcbnew.FootprintLoad(lib, "Alps_SKRHADE010"); sw.SetReference("SW1"); sw.SetValue("SKRHADE010")
    sw.SetFPID(pcbnew.LIB_ID("footprints", "Alps_SKRHADE010")); sw.SetPosition(P(*SW_XY)); sw.SetOrientationDegrees(SW_ROT); b.Add(sw)
    sw.SetPath(pcbnew.KIID_PATH(f"/{SW_UUID}"))
    j = pcbnew.FootprintLoad(lib, "PinHeader_2x03_P2.54mm_Vertical"); j.SetReference("J1"); j.SetValue("254PZ-2x3P-V")
    hx, hy = HDR_XY
    j.SetFPID(pcbnew.LIB_ID("footprints", "PinHeader_2x03_P2.54mm_Vertical"))
    j.SetPosition(K(hx - 1.27, -hy - 2.54)); b.Add(j); j.SetPath(pcbnew.KIID_PATH(f"/{J_UUID}"))
    mhs = []
    for i, (x, y) in enumerate(STANDOFFS):
        m = pcbnew.FootprintLoad(lib, "Mount_M2x11_Standoff"); m.SetReference(f"MH{i + 1}"); m.SetValue("STTZ2008")
        m.SetFPID(pcbnew.LIB_ID("footprints", "Mount_M2x11_Standoff")); m.SetPosition(P(x, y)); b.Add(m)
        m.SetPath(pcbnew.KIID_PATH(f"/{MH_UUID[i]}")); mhs.append(m)
    for fp, mp in ((sw, SW_PINS), (j, J_PINS)):
        for pad in fp.Pads():
            n = pad.GetNumber()
            if n in mp: pad.SetNet(nets[mp[n]])
    for m in mhs:
        for pad in m.Pads():
            if pad.GetNumber() == "1": pad.SetNet(nets["GND"])
    def cad(pad):
        return (pcbnew.ToMM(pad.GetPosition().x) - ORIGIN[0], ORIGIN[1] - pcbnew.ToMM(pad.GetPosition().y))
    pads = {f"SW{p.GetNumber()}": cad(p) for p in sw.Pads() if p.GetNumber()}
    pads.update({f"J{p.GetNumber()}": cad(p) for p in j.Pads()})
    pads.update({m.GetReference(): cad(next(p for p in m.Pads() if p.GetNumber() == "1")) for m in mhs})
    print("pads CAD y-up:", {k: (round(x, 2), round(y, 2)) for k, (x, y) in sorted(pads.items())})
    TW = 0.25
    def track(pts, net, layer=pcbnew.F_Cu):
        for a, c in zip(pts[:-1], pts[1:]):
            t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(mm(TW)); t.SetLayer(layer); t.SetNet(nets[net]); b.Add(t)
    def via(x, y, net):
        v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        ps = v.Padstack(); ps.SetSize(pcbnew.VECTOR2I(mm(0.6), mm(0.6)), pcbnew.F_Cu); v.SetPadstack(ps); v.SetDrill(mm(0.3)); v.SetNet(nets[net]); b.Add(v)
    # Routes in CAD y-up, from the placed pads. F.Cu and B.Cu are split so a track crosses the other layer's lane.
    R = pads
    # UP on B.Cu. The via sits 0.65 below the top edge (via radius 0.3 + 0.3 clearance).
    via(-3.9, 3.05, "SW_UP")
    track([R["SW1"], (-4.52, 3.05), (-3.9, 3.05)], "SW_UP")
    track([(-3.9, 3.05), (4.63, 3.05), R["J1"]], "SW_UP", pcbnew.B_Cu)
    # CENTER on B.Cu, ducked under UP's drop so the two B.Cu nets do not cross
    via(-6.9, 2.05, "SW_CENTER")
    track([R["SW2"], (-5.53, 2.05), (-6.9, 2.05)], "SW_CENTER")
    track([(-6.9, 2.05), (-6.9, 2.40), (2.2, 2.40), (2.2, 0.30), (8.4, 0.30), (8.4, 1.54), R["J2"]], "SW_CENTER", pcbnew.B_Cu)
    # RIGHT on F.Cu into J3
    track([R["SW4"], (0.54, -1.0), R["J3"]], "SW_RIGHT")
    # DOWN on F.Cu
    track([R["SW6"], (-1.48, -5.35), (6.35, -5.35), (6.35, -3.54), R["J6"]], "SW_DOWN")
    # LEFT on B.Cu, above the standoff pads, up between J3 and J4
    via(-8.15, 0.32, "SW_LEFT")
    track([R["SW3"], (-8.15, 0.32)], "SW_LEFT")
    track([(-8.15, 0.32), (-8.15, -4.9), (5.90, -4.9), (5.90, -1.0), R["J4"]], "SW_LEFT", pcbnew.B_Cu)
    # GND. Common pin dipped under the RIGHT pad; both frame tabs and both standoffs on F.Cu
    track([R["SW5"], (-0.47, -4.5), (3.3, -4.5), (3.3, -3.73), R["J5"]], "GND")
    track([R["MH1"], (-7.5, -6.15), (-3.3, -6.15), (-3.3, -3.2), (-0.47, -3.2), R["SW5"]], "GND")
    track([R["SW8"], (-8.55, -4.06), (-8.55, -8.0), R["MH1"]], "GND")
    track([R["SW7"], (-0.14, 2.85), (8.85, 2.85)], "GND")
    track([R["MH2"], (8.85, -7.6), (8.85, 2.85)], "GND")
    track([(8.85, -2.27), (5.2, -2.27), (5.2, -3.54), R["J5"]], "GND")
    text("JOY v0.2", 0.3, -8.7, pcbnew.F_Fab, 0.8)
    pcbnew.SaveBoard(os.path.join(HERE, NAME + ".kicad_pcb"), b)
    return pads

def write_pro():
    pro = {"meta": {"filename": NAME + ".kicad_pro", "version": 3},
           "board": {"design_settings": {"rules": {"min_copper_edge_clearance": 0.3, "min_clearance": 0.15, "min_track_width": 0.2,
                                                   "min_via_diameter": 0.5, "min_through_hole_diameter": 0.25, "min_hole_clearance": 0.25}}},
           "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []}, "sheets": [[ROOT, "Root"]], "text_variables": {}}
    json.dump(pro, open(os.path.join(HERE, NAME + ".kicad_pro"), "w"), indent=2)

def export_fab():
    """PCBWay-style pack in fab/: Gerbers+drill zip, BOM (MPN+LCSC), CPL, ERC/DRC reports, README."""
    pcb = os.path.join(HERE, NAME + ".kicad_pcb"); sch = os.path.join(HERE, NAME + ".kicad_sch")
    fab = os.path.join(HERE, "fab"); rep = os.path.join(fab, "reports")
    if os.path.isdir(fab): shutil.rmtree(fab)
    os.makedirs(rep)
    base = f"{NAME}-{REV}"
    def run(*a):
        r = subprocess.run(["kicad-cli", *a], capture_output=True, text=True)
        return r
    with tempfile.TemporaryDirectory() as t:
        g = os.path.join(t, "gerbers"); os.makedirs(g)
        layers = "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
        r = run("pcb", "export", "gerbers", "-l", layers, "--subtract-soldermask", "-o", g + "/", pcb); assert r.returncode == 0, r.stderr
        r = run("pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th", "--generate-map", "--map-format", "gerberx2", "-o", g + "/", pcb)
        assert r.returncode == 0, r.stderr
        with zipfile.ZipFile(os.path.join(fab, base + "-gerbers.zip"), "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(os.listdir(g)): z.write(os.path.join(g, f), f)
        nfiles = len(os.listdir(g))
        b = os.path.join(t, "bom.csv")
        r = run("sch", "export", "bom", "--fields", "Reference,${QUANTITY},Value,Footprint,Manufacturer,MPN,LCSC",
                "--labels", "Designator,Qty,Value,Footprint,Manufacturer,MPN,LCSC", "--group-by", "Value,Footprint,MPN,LCSC",
                "--ref-range-delimiter", "", "--exclude-dnp", "-o", b, sch); assert r.returncode == 0, r.stderr
        rows = [row for row in csv.DictReader(open(b)) if not row["Designator"].startswith("#")]
        for row in rows: row["Footprint"] = row["Footprint"].split(":")[-1]
        with open(os.path.join(fab, base + "-bom.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["Item", "Designator", "Qty", "Value", "Footprint", "Manufacturer", "MPN", "LCSC"])
            for i, row in enumerate(rows, 1):
                w.writerow([i] + [row[k] for k in ("Designator", "Qty", "Value", "Footprint", "Manufacturer", "MPN", "LCSC")])
        p = os.path.join(t, "pos.csv")
        r = run("pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both", "--exclude-dnp", "-o", p, pcb); assert r.returncode == 0, r.stderr
        pos = list(csv.DictReader(open(p)))
        with open(os.path.join(fab, base + "-cpl.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
            for row in pos:
                w.writerow([row["Ref"], f'{float(row["PosX"]):.4f}mm', f'{float(row["PosY"]):.4f}mm',
                            "Top" if row["Side"] == "top" else "Bottom", f'{float(row["Rot"]):.1f}'])
    run("sch", "erc", "--severity-all", "--format", "report", "-o", os.path.join(rep, "erc.rpt"), sch)
    run("pcb", "drc", "--schematic-parity", "--severity-all", "--format", "report", "-o", os.path.join(rep, "drc.rpt"), pcb)
    erc = open(os.path.join(rep, "erc.rpt")).read(); drc = open(os.path.join(rep, "drc.rpt")).read()
    def cnt(pat, txt):
        m = re.search(pat, txt); return int(m.group(1)) if m else -1
    status = dict(board=NAME, rev=REV, erc_messages=cnt(r"\*\* ERC messages: (\d+)", erc), erc_errors=cnt(r"Errors (\d+)", erc),
                  erc_warnings=cnt(r"Warnings (\d+)", erc), drc_violations=cnt(r"Found (\d+) DRC violations", drc),
                  drc_unconnected=cnt(r"Found (\d+) unconnected pads", drc), drc_parity=cnt(r"Found (\d+) Footprint errors", drc),
                  bom_rows=len(rows), cpl_parts=len(pos), gerber_files=nfiles,
                  bom_rows_without_lcsc=[row["Designator"] for row in rows if not row["LCSC"]])
    ready = status["drc_violations"] == 0 and status["drc_unconnected"] == 0 and status["drc_parity"] == 0 and status["erc_errors"] == 0 and not status["bom_rows_without_lcsc"]
    with open(os.path.join(fab, "README.txt"), "w") as f:
        f.write(f"{NAME} {REV} PCBWay pack, generated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} by make_project.py\n")
        f.write(("READY TO QUOTE" if ready else "NOT READY TO ORDER (see below)") + "\n\n")
        f.write(json.dumps(status, indent=2) + "\n\n")
        f.write("Board: 2 layers, 1.0 mm FR-4; HASL or ENIG; green mask, white silk [A].\n")
        f.write("J2 (the 11 mm socket) is on the MAIN PCB, not this board. Screws are hand-fit: four M2x4 pan-head, one in each end of MH1/MH2.\n")
        f.write("Screen FPC pin-out is not on this board (open until the DO0164FMST05 drawing is confirmed). Pull-ups and ESD are on the main PCB.\n")
        f.write("Direction map is confirmed at first-power calibration, not by a fixed legend.\n")
    print(json.dumps(status))
    return status

if __name__ == "__main__":
    write_symlib(); write_sch(); write_pro(); build_board()
    os.chdir(HERE)
    for cmd in (["kicad-cli", "sch", "erc", "--severity-all", "-o", "erc.rpt", NAME + ".kicad_sch"],
                ["kicad-cli", "pcb", "drc", "--schematic-parity", "--severity-all", "-o", "drc.rpt", NAME + ".kicad_pcb"],
                ["kicad-cli", "pcb", "export", "step", "--subst-models", "-f", "-o", NAME + ".step", NAME + ".kicad_pcb"]):
        r = subprocess.run(cmd, capture_output=True, text=True)
        tail = (r.stdout + r.stderr).strip().splitlines()
        print(" ".join(cmd[:4]), "->", r.returncode, tail[-4:])
    export_fab()
