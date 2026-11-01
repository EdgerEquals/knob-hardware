"""Authoring script for the KiCad top-screen joystick daughterboard (KiCad is the single source of truth for the board).
Run with the system python that has pcbnew:  /usr/bin/python3 make_project.py
Reads geom.json written by cad/joystick-param/build.py (the parameters). Writes the schematic, the board,
ERC + DRC (schematic parity, all severities), the STEP, and the fab/ pack.

v0.4: same switch, headers and standoffs as v0.3. The -y tab that carried the round stop is gone,
so the outline is symmetric and the bottom GND bus sits inboard of the new edge.
"""
import os, json, uuid, subprocess, csv, shutil, tempfile, zipfile, datetime, re
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__)); NAME = "joystick-daughterboard"
REV = "v0.4"
G = json.load(open(os.path.join(HERE, "geom.json")))
ORIGIN = (100.0, 100.0)
X0, Y0, X1, Y1 = G["board"]
NETS = ["GND", "SW_UP", "SW_DOWN", "SW_LEFT", "SW_RIGHT", "SW_CENTER"]
SW_PINS = {"1": "SW_UP", "2": "SW_CENTER", "3": "SW_LEFT", "4": "SW_RIGHT", "5": "GND", "6": "SW_DOWN", "7": "GND", "8": "GND"}
# Board: nets in inner -> outer order (closest to the switch first), assigned by position.
# Schematic: footprint pin 1, 2, 3 AFTER the underside flip. J1's flip swaps pin 1 with pin 3.
BOARD_NETS = {"J1": ("SW_RIGHT", "SW_DOWN", "GND"), "J2": ("SW_LEFT", "SW_CENTER", "SW_UP")}
SCH_NETS = {"J1": ("GND", "SW_DOWN", "SW_RIGHT"), "J2": ("SW_LEFT", "SW_CENTER", "SW_UP")}
ROOT = "6a0f3c1e-1f0b-4b8e-9d55-7e1f0a2b3c01"
SW_UUID = "6a0f3c1e-1f0b-4b8e-9d55-7e1f0a2b3c02"
J_UUID = ["6a0f3c1e-1f0b-4b8e-9d55-7e1f0a2b3c03", "6a0f3c1e-1f0b-4b8e-9d55-7e1f0a2b3c13"]
MH_UUID = ["6a0f3c1e-1f0b-4b8e-9d55-7e1f0a2b3c04", "6a0f3c1e-1f0b-4b8e-9d55-7e1f0a2b3c05",
           "6a0f3c1e-1f0b-4b8e-9d55-7e1f0a2b3c14", "6a0f3c1e-1f0b-4b8e-9d55-7e1f0a2b3c15"]
PARTS = {
    "SW1": ("Alps Alpine", "SKRHADE010", "C202415"),
    "J1": ("Samtec", "TSW-103-17-T-S", ""),
    "J2": ("Samtec", "TSW-103-17-T-S", ""),
    "MH1": ("XHHD", "STTZ1022", "C50378470"),
    "MH2": ("XHHD", "STTZ1022", "C50378470"),
    "MH3": ("XHHD", "STTZ1022", "C50378470"),
    "MH4": ("XHHD", "STTZ1022", "C50378470"),
}

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

def sym_skrh(name):
    pins = [("1", "A", -12.7, 7.62, 0), ("2", "Center", -12.7, 2.54, 0), ("3", "C", -12.7, -2.54, 0),
            ("7", "Frame", -12.7, -7.62, 0),
            ("4", "B", 12.7, 7.62, 180), ("5", "Common", 12.7, 2.54, 180), ("6", "D", 12.7, -2.54, 180),
            ("8", "Frame", 12.7, -7.62, 180)]
    return _sym(name, "SW", "SKRHADE010", "footprints:Alps_SKRHADE010", "https://tech.alpsalpine.com/e/products/detail/SKRHADE010/",
                "Alps SKRH 4-direction + centre push. Frame tabs to GND", 10.16, 10.16, pins)

def sym_conn(name):
    pins = [("1", "Inner", -7.62, 2.54, 0), ("2", "Mid", -7.62, 0, 0), ("3", "Outer", -7.62, -2.54, 0)]
    return _sym(name, "J", "TSW-103-17-T-S", "footprints:PinHeader_1x03_P2.54mm_Vertical_Long",
                "https://www.samtec.com/products/tsw-103-20-t-s",
                "1x3 2.54 header, mating pin 15.74 mm, plastic on the underside", 5.08, 5.08, pins)

def sym_mount(name):
    return _sym(name, "MH", "STTZ1022", "footprints:Mount_M2x35_Standoff", "",
                "M2x25 brass female-female standoff to GND. Socket screw through this board", 5.08, 2.54, [("1", "GND", -7.62, 0, 0)])

def write_symlib():
    s1, _ = sym_skrh("SKRHADE010"); s2, _ = sym_conn("Conn_01x03"); s3, _ = sym_mount("Mount_M2")
    open(os.path.join(HERE, "joystick.kicad_sym"), "w").write(
        '(kicad_symbol_lib (version 20241209) (generator "make_project.py")\n' + s1 + "\n" + s2 + "\n" + s3 + "\n)\n")
    open(os.path.join(HERE, "sym-lib-table"), "w").write(
        '(sym_lib_table\n  (version 7)\n  (lib (name "joystick")(type "KiCad")(uri "${KIPRJMOD}/joystick.kicad_sym")(options "")(descr "joystick daughterboard symbols"))\n)\n')
    open(os.path.join(HERE, "fp-lib-table"), "w").write(
        '(fp_lib_table\n  (version 7)\n  (lib (name "footprints")(type "KiCad")(uri "${KIPRJMOD}/../footprints.pretty")(options "")(descr "Ed project footprints"))\n)\n')

def write_sch():
    sk, skp = sym_skrh("joystick:SKRHADE010"); cn, cnp = sym_conn("joystick:Conn_01x03"); mh, mhp = sym_mount("joystick:Mount_M2")
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
    sx, sy = 55.88, 71.12          # 1.27 mm grid, so the pin ends are on the connection grid
    L = [f'(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0") (uuid "{ROOT}") (paper "A4")',
         f'  (title_block (title "Top-screen joystick daughterboard") (date "2026-11-01") (rev "{REV}") (company "Ed / Edger_Equals - knob module")',
         '    (comment 1 "SW1 Alps SKRHADE010 at -45 deg, on the carrier axis. a/b/c/d -> UP/RIGHT/LEFT/DOWN, confirmed at first power")',
         '    (comment 2 "J1 pin 1 GND, pin 2 DOWN, pin 3 RIGHT. J2 pin 1 LEFT, pin 2 CENTER, pin 3 UP. Inner pin faces the switch")',
         '    (comment 3 "Four M2x25 female-female standoffs and the frame tabs are GND. No LEDs. Headers are consigned Samtec parts"))',
         '  (lib_symbols', sk, cn, mh, '  )']
    L += inst("joystick:SKRHADE010", "SW1", "SKRHADE010", "footprints:Alps_SKRHADE010", sx, sy, SW_UUID, list(skp), *PARTS["SW1"],
              "https://tech.alpsalpine.com/e/products/detail/SKRHADE010/")
    for i, ref in enumerate(("J1", "J2")):
        jx, jy = 139.70, 50.80 + i * 40.64
        nets = {str(k + 1): SCH_NETS[ref][k] for k in range(3)}
        L += inst("joystick:Conn_01x03", ref, "TSW-103-17-T-S", "footprints:PinHeader_1x03_P2.54mm_Vertical_Long",
                  jx, jy, J_UUID[i], list(cnp), *PARTS[ref], "https://www.samtec.com/products/tsw-103-20-t-s")
        for num, (px, py) in cnp.items():
            X, Y = jx + px, jy - py
            L.append(wire(X, Y, X - 5.08, Y)); L.append(label(nets[num], X - 5.08, Y, True))
    for num, (px, py) in skp.items():
        X, Y = sx + px, sy - py; left = px < 0; e = X - 5.08 if left else X + 5.08
        L.append(wire(X, Y, e, Y)); L.append(label(SW_PINS[num], e, Y, left))
    for i, uid in enumerate(MH_UUID):
        my = 129.54 + (i % 2) * 12.70
        mx = 40.64 + (i // 2) * 30.48
        L += inst("joystick:Mount_M2", f"MH{i + 1}", "STTZ1022", "footprints:Mount_M2x35_Standoff", mx, my, uid, list(mhp), *PARTS[f"MH{i + 1}"])
        X, Y = mx + mhp["1"][0], my - mhp["1"][1]
        L.append(wire(X, Y, X - 5.08, Y)); L.append(label("GND", X - 5.08, Y, True))
    L.append(f'  (text "v0.4. Switch on the carrier axis. Two 1x3 headers, plastic on the underside, pin down into the H11 sockets on the main PCB.\\nFour M2x25 female-female standoffs and frame tabs 7 and 8 are GND. No LEDs. No round-stop tab. No ESD or pull-ups on this board.\\nJ1 and J2 are Samtec TSW-103-17-T-S, consigned. Lead style -17 is a 15.74 mm mating pin." (exclude_from_sim no) (at 20 165 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{uuid.uuid4()}"))')
    L += ['  (sheet_instances (path "/" (page "1")))', ')']
    open(os.path.join(HERE, NAME + ".kicad_sch"), "w").write("\n".join(L) + "\n")

mm = pcbnew.FromMM
def P(x, y): return pcbnew.VECTOR2I(mm(ORIGIN[0] + x), mm(ORIGIN[1] - y))

def build_board():
    b = pcbnew.BOARD(); ds = b.GetDesignSettings(); ds.SetBoardThickness(mm(G["db_t"])); ds.SetCopperLayerCount(2)
    ds.m_CopperEdgeClearance = mm(0.25); ds.m_TrackMinWidth = mm(0.2); ds.m_MinClearance = mm(0.15)
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
    r = 0.8
    seg(P(X0 + r, Y1), P(X1 - r, Y1)); seg(P(X1, Y1 - r), P(X1, Y0 + r))
    seg(P(X1 - r, Y0), P(X0 + r, Y0)); seg(P(X0, Y0 + r), P(X0, Y1 - r))
    arc(P(X1 - r, Y1 - r), P(X1 - r, Y1)); arc(P(X1 - r, Y0 + r), P(X1, Y0 + r))
    arc(P(X0 + r, Y0 + r), P(X0 + r, Y0)); arc(P(X0 + r, Y1 - r), P(X0, Y1 - r))
    lib = os.path.normpath(os.path.join(HERE, "..", "footprints.pretty"))
    sw = pcbnew.FootprintLoad(lib, "Alps_SKRHADE010"); sw.SetReference("SW1"); sw.SetValue("SKRHADE010")
    sw.SetFPID(pcbnew.LIB_ID("footprints", "Alps_SKRHADE010")); sw.SetPosition(P(0, 0)); sw.SetOrientationDegrees(G["sw_rot"]); b.Add(sw)
    sw.SetPath(pcbnew.KIID_PATH(f"/{SW_UUID}"))
    headers = []
    for i, (x, y) in enumerate(G["headers"]):
        j = pcbnew.FootprintLoad(lib, "PinHeader_1x03_P2.54mm_Vertical_Long")
        ref = f"J{i + 1}"; j.SetReference(ref); j.SetValue("TSW-103-17-T-S")
        j.SetFPID(pcbnew.LIB_ID("footprints", "PinHeader_1x03_P2.54mm_Vertical_Long"))
        j.SetPosition(P(x, y)); b.Add(j)
        j.Flip(j.GetPosition(), False)   # plastic on the underside
        j.SetPath(pcbnew.KIID_PATH(f"/{J_UUID[i]}")); headers.append(j)
    mhs = []
    for i, (x, y) in enumerate(G["standoffs"]):
        m = pcbnew.FootprintLoad(lib, "Mount_M2x35_Standoff"); m.SetReference(f"MH{i + 1}"); m.SetValue("STTZ1022")
        m.SetFPID(pcbnew.LIB_ID("footprints", "Mount_M2x35_Standoff")); m.SetPosition(P(x, y)); b.Add(m)
        m.SetPath(pcbnew.KIID_PATH(f"/{MH_UUID[i]}")); mhs.append(m)
    def cad(pad):
        return (pcbnew.ToMM(pad.GetPosition().x) - ORIGIN[0], ORIGIN[1] - pcbnew.ToMM(pad.GetPosition().y))
    # nets: header pins ordered inner -> outer (closest to the switch first)
    for fp, mp in ((sw, SW_PINS),):
        for pad in fp.Pads():
            n = pad.GetNumber()
            if n in mp: pad.SetNet(nets[mp[n]])
    for m in mhs:
        for pad in m.Pads():
            if pad.GetNumber() == "1": pad.SetNet(nets["GND"])
    hdr_pts = {}
    for j in headers:
        pads = sorted(j.Pads(), key=lambda p: abs(cad(p)[0]))
        nets_for = BOARD_NETS[j.GetReference()]
        for pad, net in zip(pads, nets_for):
            pad.SetNet(nets[net]); hdr_pts[(j.GetReference(), net)] = cad(pad)
    sw_pts = {f"SW{p.GetNumber()}": cad(p) for p in sw.Pads() if p.GetNumber()}
    mh_pts = {m.GetReference(): cad(next(p for p in m.Pads() if p.GetNumber() == "1")) for m in mhs}
    print("SW", {k: (round(x, 3), round(y, 3)) for k, (x, y) in sw_pts.items()})
    print("HDR", {k: (round(x, 3), round(y, 3)) for k, (x, y) in hdr_pts.items()})
    TW = 0.2
    def via(x, y, net):
        v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        ps = v.Padstack(); ps.SetSize(pcbnew.VECTOR2I(mm(0.6), mm(0.6)), pcbnew.F_Cu); v.SetPadstack(ps)
        v.SetDrill(mm(0.3)); v.SetNet(nets[net]); b.Add(v)
    def track(pts, net, layer=pcbnew.F_Cu):
        for a, c in zip(pts[:-1], pts[1:]):
            if abs(a[0] - c[0]) < 1e-6 and abs(a[1] - c[1]) < 1e-6: continue
            t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(mm(TW)); t.SetLayer(layer); t.SetNet(nets[net]); b.Add(t)
    # signal routes, F.Cu, kept off the standoff pads (centres near x=±14, y=±4.1)
    S, H = sw_pts, hdr_pts
    track([S["SW3"], (-5.8, S["SW3"][1]), (-5.8, 0.0), H[("J2", "SW_LEFT")]], "SW_LEFT")
    # SW_CENTER: the orthogonal exits clip the neighbouring 45° pads, so the stub leaves along the clear diagonal and the run is on B.Cu
    via(-4.0, 4.0, "SW_CENTER")
    track([S["SW2"], (-3.2, 3.2), (-4.0, 4.0)], "SW_CENTER")
    track([(-4.0, 4.0), (-4.0, 4.9), (H[("J2", "SW_CENTER")][0], 4.9), H[("J2", "SW_CENTER")]], "SW_CENTER", pcbnew.B_Cu)
    track([S["SW1"], (S["SW1"][0], 5.7), (-11.2, 5.7), (-11.2, 1.9), (H[("J2", "SW_UP")][0], 1.9), H[("J2", "SW_UP")]], "SW_UP")
    track([S["SW4"], (5.8, S["SW4"][1]), (5.8, 0.0), H[("J1", "SW_RIGHT")]], "SW_RIGHT")
    # SW_DOWN crosses the GND spine, so the long run is on B.Cu. The header pin is through-hole.
    via(S["SW6"][0], -4.7, "SW_DOWN")
    track([S["SW6"], (S["SW6"][0], -4.7)], "SW_DOWN")
    track([(S["SW6"][0], -4.7), (H[("J1", "SW_DOWN")][0], -4.7), H[("J1", "SW_DOWN")]], "SW_DOWN", pcbnew.B_Cu)
    # GND: common, both frame tabs, J1 outer pin, four standoffs. Spine at x=11.5, off SW_DOWN.
    # The v0.3 bus at y=-7.4/-8.6 lived on the round-stop tab. This board ends at y=-6.94,
    # so the bus is at y=-6.30: 0.53 mm inside the edge, 0.57 mm clear of the Ø3.2 standoff pads.
    gnd = H[("J1", "GND")]
    yb = -6.30
    track([S["SW5"], (3.2, -3.2), (4.0, -4.2), (4.0, yb), (11.5, yb), (11.5, -2.1), (gnd[0], -2.1), gnd], "GND")
    track([S["SW8"], (S["SW8"][0], yb), (11.5, yb)], "GND")
    track([S["SW7"], (4.4, S["SW7"][1]), (4.4, 6.2), (11.5, 6.2), (11.5, 2.1), (gnd[0], 2.1), gnd], "GND")
    track([mh_pts["MH1"], (mh_pts["MH1"][0], 6.2), (4.4, 6.2)], "GND")
    track([mh_pts["MH2"], (mh_pts["MH2"][0], yb), (11.5, yb)], "GND")
    track([mh_pts["MH3"], (mh_pts["MH3"][0], 6.2), (4.4, 6.2)], "GND")
    track([mh_pts["MH4"], (mh_pts["MH4"][0], yb), (11.5, yb)], "GND")
    text("JOY v0.4", 7.2, -5.15, pcbnew.F_Fab, 0.6)
    pcbnew.SaveBoard(os.path.join(HERE, NAME + ".kicad_pcb"), b)
    return sw_pts

def write_pro():
    pro = {"meta": {"filename": NAME + ".kicad_pro", "version": 3},
           "board": {"design_settings": {"rules": {"min_copper_edge_clearance": 0.25, "min_clearance": 0.15, "min_track_width": 0.2,
                                                   "min_via_diameter": 0.5, "min_through_hole_diameter": 0.25, "min_hole_clearance": 0.25}}},
           "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []}, "sheets": [[ROOT, "Root"]], "text_variables": {}}
    json.dump(pro, open(os.path.join(HERE, NAME + ".kicad_pro"), "w"), indent=2)

def export_fab():
    pcb = os.path.join(HERE, NAME + ".kicad_pcb"); sch = os.path.join(HERE, NAME + ".kicad_sch")
    fab = os.path.join(HERE, "fab"); rep = os.path.join(fab, "reports")
    if os.path.isdir(fab): shutil.rmtree(fab)
    os.makedirs(rep)
    base = f"{NAME}-{REV}"
    def run(*a):
        return subprocess.run(["kicad-cli", *a], capture_output=True, text=True)
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
    missing = [row["Designator"] for row in rows if not row["LCSC"]]
    missing_refs = set()
    for item in missing:
        missing_refs.update(x.strip() for x in item.split(",") if x.strip())
    consigned = sorted(missing_refs & {"J1", "J2"})
    status = dict(board=NAME, rev=REV, erc_messages=cnt(r"\*\* ERC messages: (\d+)", erc), erc_errors=cnt(r"Errors (\d+)", erc),
                  erc_warnings=cnt(r"Warnings (\d+)", erc), drc_violations=cnt(r"Found (\d+) DRC violations", drc),
                  drc_unconnected=cnt(r"Found (\d+) unconnected pads", drc), drc_parity=cnt(r"Found (\d+) Footprint errors", drc),
                  bom_rows=len(rows), cpl_parts=len(pos), gerber_files=nfiles,
                  bom_rows_without_lcsc=missing, consigned_samtec=consigned)
    ready = (status["drc_violations"] == 0 and status["drc_unconnected"] == 0 and status["drc_parity"] == 0
             and status["erc_errors"] == 0 and missing_refs <= {"J1", "J2"})
    with open(os.path.join(fab, "README.txt"), "w") as f:
        f.write(f"{NAME} {REV} PCBWay pack, generated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} by make_project.py\n")
        f.write(("READY TO QUOTE" if ready else "NOT READY TO ORDER (see below)") + "\n\n")
        f.write(json.dumps(status, indent=2) + "\n\n")
        f.write("Board: 2 layers, 1.0 mm FR-4; HASL or ENIG; green mask, white silk [A]. No LEDs.\n")
        f.write("J1 and J2 are Samtec TSW-103-17-T-S (1x3, mating pin 15.74 mm). Plastic on the BOTTOM. Trim the 2.79 mm tails flush on the top before the seat plate is glued on.\n")
        f.write("The 1x3 is ordered from Samtec and consigned. Lead style -17 replaces the -20 pin, which was too long for the 25 mm riser.\n")
        f.write("The two mating sockets are on the MAIN PCB: hanxia HX PM2.54-1x3P ZC H11, LCSC C41427518, one each side of the switch.\n")
        f.write("MH1-MH4 are XHHD STTZ1022, round female-female M2x25 brass, LCSC C50378470, all GND. An ISO 4762 M2x6 socket screw goes through the seat plate and this board into the pillar. An M2x4 socket screw holds the other end under the main PCB.\n")
        f.write("Screen FPC pin-out is not on this board (still open). Pull-ups and ESD are on the main PCB.\n")
        f.write("Direction map is confirmed at first-power calibration, not by a fixed legend.\n")
    print(json.dumps(status, indent=2))
    print(drc[-1500:] if not ready else "DRC clean")
    return status

if __name__ == "__main__":
    write_symlib(); write_sch(); write_pro(); build_board()
    os.chdir(HERE)
    for cmd in (["kicad-cli", "sch", "erc", "--severity-all", "-o", "erc.rpt", NAME + ".kicad_sch"],
                ["kicad-cli", "pcb", "drc", "--schematic-parity", "--severity-all", "-o", "drc.rpt", NAME + ".kicad_pcb"],
                ["kicad-cli", "pcb", "export", "step", "--subst-models", "-f", "-o", NAME + ".step", NAME + ".kicad_pcb"]):
        r = subprocess.run(cmd, capture_output=True, text=True)
        tail = (r.stdout + r.stderr).strip().splitlines()
        print(" ".join(cmd[:4]), "->", r.returncode, tail[-6:])
    export_fab()
