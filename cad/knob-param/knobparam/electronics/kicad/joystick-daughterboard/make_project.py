"""Authoring script for the KiCad top-screen joystick daughterboard (KiCad is the single source of truth for the board).
Run with the system python that has pcbnew:  /usr/bin/python3 make_project.py
Writes joystick-daughterboard.kicad_sch / .kicad_pcb / .kicad_pro, joystick.kicad_sym, sym-lib-table, fp-lib-table,
then runs ERC + DRC (with schematic parity) and exports the STEP with kicad-cli.

v0.1 (2026-11-01, Ed): Alps SKRHADE010 (SW1) turned -45° (visually clockwise) so its diagonal directions a/b/c/d line up
with the screen UP/RIGHT/LEFT/DOWN; all 5 contacts + common go individually to J1 (firmware reads two closed contacts as a
diagonal). J1 = 2x3 2.54 male header, plastic on the TOP side, long pins down into J2 (2x3 2.54 female, 8.5 tall) on the
main PCB = the riser. No parts on the board besides SW1 + J1: pull-ups (MCU internal or 10k) and ESD sit on the main PCB.
A printed riser post (part of the joystick base) supports the board under SW1. Board 16.6 x 12.0 x 1.0, 2 layers.
Mechanical reference (Dwgs.User): base window, spring holes, FPC slot, carrier and the 4 balls, in board coordinates.
Geometry numbers mirror cad/joystick-param/jsparam/params.py (CAD y up = KiCad -y). Tags: [S] datasheet, [A] assumed."""
import os, json, uuid, subprocess, math
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__)); NAME = "joystick-daughterboard"
ORIGIN = (100.0, 100.0)            # KiCad position of the daughterboard centre (= carrier centre in plan)
DB_W, DB_H, DB_T = 16.6, 12.0, 1.0  # [A] board
CORNER_R = 0.5
SW_X, SW_ROT = -2.9, -45.0          # [A]/[Ed] switch centre (CAD x) and footprint rotation (KiCad, deg)
HDR_X = 5.6                         # [A] header centre (CAD x); pins at x HDR_X -+ 1.27
# mechanical reference (from jsparam params, CAD coords: x right, y up)
WIN = (17.4, 12.8); SPR = (10.8, 6.6, 3.4); BALL = (14.0, 7.0, 2.0); CAR = (33.6, 20.6); FPC_HOLE = (13.0, 16.2, 5.35)
NETS = ["GND", "SW_UP", "SW_DOWN", "SW_LEFT", "SW_RIGHT", "SW_CENTER"]
SW_PINS = {"1": "SW_UP", "2": "SW_CENTER", "3": "SW_LEFT", "4": "SW_RIGHT", "5": "GND", "6": "SW_DOWN"}   # A, Center, C, B, Common, D
J_PINS = {"1": "SW_UP", "2": "SW_CENTER", "3": "SW_RIGHT", "4": "SW_LEFT", "5": "GND", "6": "SW_DOWN"}
U = lambda: str(uuid.uuid5(uuid.NAMESPACE_URL, "joystick-db/" + str(U.n) + "/" + str(U.__dict__.setdefault("k", 0)))) if False else str(uuid.uuid4())
ROOT = "6a0f3c1e-1f0b-4b8e-9d55-7e1f0a2b3c01"; SW_UUID = "6a0f3c1e-1f0b-4b8e-9d55-7e1f0a2b3c02"; J_UUID = "6a0f3c1e-1f0b-4b8e-9d55-7e1f0a2b3c03"

# ------------------------------------------------------------------ symbols
def sym_skrh(name):
    pins = [("1", "A", -10.16, 5.08, 0), ("2", "Center", -10.16, 0, 0), ("3", "C", -10.16, -5.08, 0),
            ("4", "B", 10.16, 5.08, 180), ("5", "Common", 10.16, 0, 180), ("6", "D", 10.16, -5.08, 180)]
    return _sym(name, "SW", "SKRHADE010", "footprints:Alps_SKRHADE010", "https://tech.alpsalpine.com/e/products/detail/SKRHADE010/",
                "Alps SKRH 4-direction + centre push SMD switch, 1M cycles", 7.62, 7.62, pins)

def sym_conn(name):
    pins = [(str(i + 1), f"Pin_{i + 1}", -7.62 if i % 2 == 0 else 7.62, 2.54 - (i // 2) * 2.54, 0 if i % 2 == 0 else 180) for i in range(6)]
    return _sym(name, "J", "Conn_02x03", "footprints:PinHeader_2x03_P2.54mm_Vertical", "", "2x3 2.54 mm header", 5.08, 5.08, pins)

def _sym(name, ref, val, fp, ds, desc, hw, hh, pins):
    base = name.split(":")[-1]
    P = [f'  (symbol "{name}" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)',
         f'    (property "Reference" "{ref}" (at 0 {hh + 1.27:.2f} 0) (effects (font (size 1.27 1.27))))',
         f'    (property "Value" "{val}" (at 0 {-hh - 1.27:.2f} 0) (effects (font (size 1.27 1.27))))',
         f'    (property "Footprint" "{fp}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'    (property "Datasheet" "{ds}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'    (property "Description" "{desc}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'    (symbol "{base}_0_1" (rectangle (start {-hw} {hh}) (end {hw} {-hh}) (stroke (width 0.254) (type default)) (fill (type background))))',
         f'    (symbol "{base}_1_1"']
    for num, nm, x, y, a in pins:
        P.append(f'      (pin passive line (at {x} {y} {a}) (length 2.54) (name "{nm}" (effects (font (size 1.27 1.27)))) (number "{num}" (effects (font (size 1.27 1.27)))))')
    P += ['    )', '  )']
    return "\n".join(P), {num: (x, y) for num, nm, x, y, a in pins}

def write_symlib():
    s1, _ = sym_skrh("SKRHADE010"); s2, _ = sym_conn("Conn_02x03")
    open(os.path.join(HERE, "joystick.kicad_sym"), "w").write('(kicad_symbol_lib (version 20241209) (generator "make_project.py")\n' + s1 + "\n" + s2 + "\n)\n")
    open(os.path.join(HERE, "sym-lib-table"), "w").write('(sym_lib_table\n  (version 7)\n  (lib (name "joystick")(type "KiCad")(uri "${KIPRJMOD}/joystick.kicad_sym")(options "")(descr "joystick daughterboard symbols"))\n)\n')
    open(os.path.join(HERE, "fp-lib-table"), "w").write('(fp_lib_table\n  (version 7)\n  (lib (name "footprints")(type "KiCad")(uri "${KIPRJMOD}/../footprints.pretty")(options "")(descr "Ed project footprints"))\n)\n')

def write_sch():
    sk, skp = sym_skrh("joystick:SKRHADE010"); cn, cnp = sym_conn("joystick:Conn_02x03")
    def inst(lib, ref, val, fp, x, y, uid, pins, ds=""):
        L = [f'  (symbol (lib_id "{lib}") (at {x} {y} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{uid}")',
             f'    (property "Reference" "{ref}" (at {x} {y - 10.16} 0) (effects (font (size 1.27 1.27))))',
             f'    (property "Value" "{val}" (at {x} {y + 10.16} 0) (effects (font (size 1.27 1.27))))',
             f'    (property "Footprint" "{fp}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))',
             f'    (property "Datasheet" "{ds}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))',
             f'    (property "Description" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))']
        L += [f'    (pin "{p}" (uuid "{uuid.uuid4()}"))' for p in pins]
        L += [f'    (instances (project "{NAME}" (path "/{ROOT}" (reference "{ref}") (unit 1))))', '  )']
        return L
    def label(net, x, y, left):
        a, j = (180, "right") if left else (0, "left")
        return f'  (label "{net}" (at {x:.2f} {y:.2f} {a}) (effects (font (size 1.27 1.27)) (justify {j} bottom)) (uuid "{uuid.uuid4()}"))'
    def wire(x0, y0, x1, y1):
        return f'  (wire (pts (xy {x0:.2f} {y0:.2f}) (xy {x1:.2f} {y1:.2f})) (stroke (width 0) (type default)) (uuid "{uuid.uuid4()}"))'
    sx, sy, jx, jy = 60.96, 63.5, 129.54, 63.5
    L = [f'(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0") (uuid "{ROOT}") (paper "A5")',
         '  (title_block (title "Top-screen joystick daughterboard") (date "2026-11-01") (rev "v0.1") (company "Ed / Edger_Equals - knob module")',
         '    (comment 1 "SW1 Alps SKRHADE010 turned -45 deg: a/b/c/d -> UP/RIGHT/LEFT/DOWN [verify on the bench]")',
         '    (comment 2 "All 5 contacts + common to J1; pull-ups + ESD on the main PCB (MCU reads 2 contacts = diagonal)")',
         '    (comment 3 "J1 2x3 2.54 male (plastic on top, pins down) into J2 2x3 female 8.5 on the main PCB = riser"))',
         '  (lib_symbols', sk, cn, '  )']
    L += inst("joystick:SKRHADE010", "SW1", "SKRHADE010", "footprints:Alps_SKRHADE010", sx, sy, SW_UUID, list(skp), "https://tech.alpsalpine.com/e/products/detail/SKRHADE010/")
    L += inst("joystick:Conn_02x03", "J1", "Conn_02x03 (to main PCB J2)", "footprints:PinHeader_2x03_P2.54mm_Vertical", jx, jy, J_UUID, list(cnp))
    for pins, x0, y0, net in ((skp, sx, sy, SW_PINS), (cnp, jx, jy, J_PINS)):
        for num, (px, py) in pins.items():
            X, Y = x0 + px, y0 - py; left = px < 0; e = X - 5.08 if left else X + 5.08
            L.append(wire(X, Y, e, Y)); L.append(label(net[num], e, Y, left))
    L.append(f'  (text "Directions with the footprint at -45 deg: A(1)=UP, B(4)=RIGHT, C(3)=LEFT, D(6)=DOWN, 2=CENTRE push, 5=COMMON (GND).\\nDiagonals = two contacts closed (firmware window). No ESD/pull-ups here: J2 on the main PCB carries them." (exclude_from_sim no) (at 30.48 86.36 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{uuid.uuid4()}"))')
    L += ['  (sheet_instances (path "/" (page "1")))', ')']
    open(os.path.join(HERE, NAME + ".kicad_sch"), "w").write("\n".join(L) + "\n")

# ------------------------------------------------------------------ board
mm = pcbnew.FromMM
def P(x, y): return pcbnew.VECTOR2I(mm(ORIGIN[0] + x), mm(ORIGIN[1] - y))   # CAD (x, y up) -> KiCad
def K(x, y): return pcbnew.VECTOR2I(mm(ORIGIN[0] + x), mm(ORIGIN[1] + y))   # KiCad-relative (y down)

def build_board():
    b = pcbnew.BOARD(); ds = b.GetDesignSettings(); ds.SetBoardThickness(mm(DB_T)); ds.SetCopperLayerCount(2)
    ds.m_CopperEdgeClearance = mm(0.3); ds.m_TrackMinWidth = mm(0.15); ds.m_MinClearance = mm(0.15); ds.m_ViasMinSize = mm(0.45); ds.m_MinThroughDrill = mm(0.25)
    nets = {}
    for n in NETS:   # local labels on the root sheet -> "/NAME"
        ni = pcbnew.NETINFO_ITEM(b, "/" + n); b.Add(ni); nets[n] = ni
    def seg(a, c, layer=pcbnew.Edge_Cuts, w=0.05):
        s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT); s.SetLayer(layer); s.SetWidth(mm(w)); s.SetStart(a); s.SetEnd(c); b.Add(s)
    def arc(c, st, en, layer=pcbnew.Edge_Cuts, w=0.05):
        s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_ARC); s.SetLayer(layer); s.SetWidth(mm(w)); s.SetCenter(c); s.SetStart(st); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T), False); b.Add(s)
    def rect(x0, y0, x1, y1, layer, w=0.1):
        for a, c in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))): seg(P(*a), P(*c), layer, w)
    def circ(x, y, r, layer, w=0.1):
        s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_CIRCLE); s.SetLayer(layer); s.SetWidth(mm(w)); s.SetCenter(P(x, y)); s.SetEnd(P(x + r, y)); b.Add(s)
    def text(t, x, y, layer, size=0.8):
        tx = pcbnew.PCB_TEXT(b); tx.SetText(t); tx.SetPosition(P(x, y)); tx.SetLayer(layer); tx.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); tx.SetTextThickness(mm(size * 0.15)); b.Add(tx)
    # outline with rounded corners
    w2, h2, r = DB_W / 2, DB_H / 2, CORNER_R
    seg(P(-w2 + r, h2), P(w2 - r, h2)); seg(P(w2, h2 - r), P(w2, -h2 + r)); seg(P(w2 - r, -h2), P(-w2 + r, -h2)); seg(P(-w2, -h2 + r), P(-w2, h2 - r))
    for cx, cy, sx, sy in ((w2 - r, h2 - r, 0, 1), (w2 - r, -h2 + r, 1, 0), (-w2 + r, -h2 + r, 0, -1), (-w2 + r, h2 - r, -1, 0)):
        pass
    # corner arcs: start points chosen so a +90 sweep (KiCad CW in y-down = CCW visually reversed) closes each corner
    for (cx, cy), (stx, sty) in (((w2 - r, h2 - r), (w2 - r, h2)), ((w2 - r, -h2 + r), (w2, -h2 + r)), ((-w2 + r, -h2 + r), (-w2 + r, -h2)), ((-w2 + r, h2 - r), (-w2, h2 - r))):
        arc(P(cx, cy), P(stx, sty), None)
    # footprints
    lib = os.path.normpath(os.path.join(HERE, "..", "footprints.pretty"))
    sw = pcbnew.FootprintLoad(lib, "Alps_SKRHADE010"); sw.SetReference("SW1"); sw.SetValue("SKRHADE010")
    sw.SetFPID(pcbnew.LIB_ID("footprints", "Alps_SKRHADE010")); sw.SetPosition(P(SW_X, 0)); sw.SetOrientationDegrees(SW_ROT); b.Add(sw)
    sw.SetPath(pcbnew.KIID_PATH(f"/{SW_UUID}"))
    j = pcbnew.FootprintLoad(lib, "PinHeader_2x03_P2.54mm_Vertical"); j.SetReference("J1"); j.SetValue("Conn_02x03 (to main PCB J2)")
    j.SetFPID(pcbnew.LIB_ID("footprints", "PinHeader_2x03_P2.54mm_Vertical")); j.SetPosition(K(HDR_X - 1.27, -2.54)); b.Add(j); j.SetPath(pcbnew.KIID_PATH(f"/{J_UUID}"))
    for fp, m in ((sw, SW_PINS), (j, J_PINS)):
        for pad in fp.Pads():
            n = pad.GetNumber()
            if n in m: pad.SetNet(nets[m[n]])
    pads = {f"SW{p.GetNumber()}": p.GetPosition() for p in sw.Pads() if p.GetNumber()}
    pads.update({f"J{p.GetNumber()}": p.GetPosition() for p in j.Pads()})
    rel = {k: (pcbnew.ToMM(v.x) - ORIGIN[0], pcbnew.ToMM(v.y) - ORIGIN[1]) for k, v in pads.items()}   # KiCad-relative, y down
    print("pads (KiCad rel, y down):", {k: (round(x, 2), round(y, 2)) for k, (x, y) in rel.items()})
    # tracks (KiCad-relative coords, y down)
    TW = 0.25
    def track(pts, net, layer=pcbnew.F_Cu):
        for a, c in zip(pts[:-1], pts[1:]):
            t = pcbnew.PCB_TRACK(b); t.SetStart(K(*a)); t.SetEnd(K(*c)); t.SetWidth(mm(TW)); t.SetLayer(layer); t.SetNet(nets[net]); b.Add(t)
    def via(x, y, net):
        v = pcbnew.PCB_VIA(b); v.SetPosition(K(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        ps = v.Padstack(); ps.SetSize(pcbnew.VECTOR2I(mm(0.6), mm(0.6)), pcbnew.F_Cu); v.SetPadstack(ps); v.SetDrill(mm(0.3)); v.SetNet(nets[net]); b.Add(v)
    R = rel
    # UP: SW1.1 -> over the top (F.Cu) -> J1.1
    p1 = R["SW1"]; j1 = R["J1"]
    track([p1, (p1[0], -4.9), (j1[0] - 0.85, -4.9), (j1[0], -4.05), j1], "SW_UP")
    # CENTER: SW1.2 -> via -> B.Cu along the top -> J1.2
    p2 = R["SW2"]; j2 = R["J2"]; v2 = (-6.0, -3.95)
    track([p2, v2], "SW_CENTER"); via(*v2, "SW_CENTER")
    track([v2, (-6.0, -5.25), (j2[0] - 0.7, -5.25), (j2[0], -4.55), j2], "SW_CENTER", pcbnew.B_Cu)
    # LEFT: SW1.3 -> via at the left edge -> B.Cu between the boss holes and the header rows -> J1.4
    p3 = R["SW3"]; j4 = R["J4"]; v3 = (-7.45, -0.2)
    track([p3, v3], "SW_LEFT"); via(*v3, "SW_LEFT")
    track([v3, (-6.3, -0.2), (-0.6, -0.2), (0.0, -0.2), (j1[0] - 1.27 + 0.2, -1.27), (j4[0] - 1.27, -1.27), j4], "SW_LEFT", pcbnew.B_Cu)
    # RIGHT: SW1.4 -> J1.3 (F.Cu)
    p4 = R["SW4"]; j3 = R["J3"]
    track([p4, (p4[0] + 1.52, 0.0), j3], "SW_RIGHT")
    # GND: SW1.5 -> J1.5 (F.Cu, under the RIGHT pad)
    p5 = R["SW5"]; j5 = R["J5"]
    track([p5, (p5[0] + 1.27, 3.8), (j5[0] - 0.73, 3.8), j5], "GND")
    # DOWN: SW1.6 -> J1.6 (F.Cu, along the bottom)
    p6 = R["SW6"]; j6 = R["J6"]
    track([p6, (p6[0], 4.95), (j6[0] - 0.75, 4.95), (j6[0], 4.2), j6], "SW_DOWN")
    # silk + fab
    text("UP", SW_X - 4.3, 4.9, pcbnew.F_SilkS, 0.8)
    seg(P(SW_X - 4.3, 4.2), P(SW_X - 4.3, 3.2), pcbnew.F_SilkS, 0.15); seg(P(SW_X - 4.3, 4.2), P(SW_X - 4.6, 3.8), pcbnew.F_SilkS, 0.15); seg(P(SW_X - 4.3, 4.2), P(SW_X - 4.0, 3.8), pcbnew.F_SilkS, 0.15)
    text("JOY v0.1", HDR_X, -5.2, pcbnew.F_SilkS, 0.8)
    # mechanical reference (Dwgs.User): base window, springs, balls, FPC hole, carrier outline (board coords)
    D = pcbnew.Dwgs_User
    rect(-WIN[0] / 2, -WIN[1] / 2, WIN[0] / 2, WIN[1] / 2, D)
    rect(-CAR[0] / 2, -CAR[1] / 2, CAR[0] / 2, CAR[1] / 2, D)
    rect(FPC_HOLE[0], -FPC_HOLE[2], FPC_HOLE[1], FPC_HOLE[2], D)
    for sx in (1, -1):
        for sy in (1, -1):
            circ(sx * SPR[0], sy * SPR[1], SPR[2] / 2, D); circ(sx * BALL[0], sy * BALL[1], BALL[2] / 2, D)
    text("Dwgs.User: base window 17.4x12.8, spring holes 4x D3.4, balls 4x D2, FPC hole, carrier 33.6x20.6 (main-PCB keep-outs)", 0, -11.6, D, 0.6)
    pcbnew.SaveBoard(os.path.join(HERE, NAME + ".kicad_pcb"), b)
    return b

def write_pro():
    pro = {"meta": {"filename": NAME + ".kicad_pro", "version": 3},
           "board": {"design_settings": {"rules": {"min_copper_edge_clearance": 0.3, "min_clearance": 0.15, "min_track_width": 0.15, "min_via_diameter": 0.45, "min_through_hole_diameter": 0.25}}},
           "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []}, "sheets": [[ROOT, "Root"]], "text_variables": {}}
    json.dump(pro, open(os.path.join(HERE, NAME + ".kicad_pro"), "w"), indent=2)

if __name__ == "__main__":
    write_symlib(); write_sch(); write_pro(); build_board()
    os.chdir(HERE)
    for cmd in (["kicad-cli", "sch", "erc", "--severity-all", "-o", "erc.rpt", NAME + ".kicad_sch"],
                ["kicad-cli", "pcb", "drc", "--schematic-parity", "--severity-all", "-o", "drc.rpt", NAME + ".kicad_pcb"],
                ["kicad-cli", "pcb", "export", "step", "--subst-models", "-f", "-o", NAME + ".step", NAME + ".kicad_pcb"]):
        r = subprocess.run(cmd, capture_output=True, text=True); print(" ".join(cmd[:3]), "->", r.returncode, (r.stdout + r.stderr).strip().splitlines()[-3:])
