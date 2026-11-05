"""USB-C board (knob step 2, CAD v0.39; Ed 5 Nov Q4 = A, Q5 = B, Q12 = A, Q13 = A). Generates the schematic, the board and the STEP.
Run with the system python that has pcbnew (KiCad 7.0.11):  /usr/bin/python3 make_board.py [--route]
  12.0 x 6.0 x 1.6 mm, 2 layers, ENIG (the 8 spring-contact landing pads are bare gold). Board centre = the socket centre
  (panel x, y -53.40); KiCad y = -panel y. F side faces the faceplate: the socket. B side faces the jack board's tab: the 8 landing
  pads, and the two protection parts in the band the printed key presses (pockets in the key).
  J1  SHOU HAN TYPE-C 16P LTH6.8 vertical USB-C, LCSC C5187468. Land pattern from the published numbers [S-lib: LCSC/EasyEDA
      "USB-C-SMD_TYPE-C-16P-LTH6.8"; the same pad map in three other open footprints]: 16 SMD 0.30 x 0.87 in rows at y -0.865
      (A1 A4 A5 A6 A7 A8 A9 A12 at x -2.75 -1.25 -0.75 -0.25 0.25 0.75 1.25 2.75) and y +0.865 (B1 B4 ... B12 at +2.75 ... -2.75),
      shell legs in plated slots 0.85 x 0.60 at (±2.40, ±2.15), pads 1.35 x 1.10; locating posts NPTH Ø0.80 (+3.75) / Ø0.60 (-3.75).
  D1  ST ESDA25P35-1U1M VBUS TVS (LCSC C1974707), DFN1610-2: terminals 0.80 x 0.35 at 1.05 pitch [S]; pads 0.55 x 0.95 [A];
      pin 1 (bar) taken as the cathode [A, C: confirm on ST's figure 1].
  U1  TI TPD2E2U06DRLR data ESD (LCSC C1972959), SOT-5X3: 1 NC, 2 NC, 3 IO1, 4 GND, 5 IO2 [S: TI pin table]; KiCad SOT-553 footprint
      (KiCad library, CC-BY-SA 4.0 with the design exception).
  P1-P8 landing pads Ø1.20 for the Harwin P70-5100045 spring contacts on the jack board's tab [S-dist], no paste.
CC1/CC2 go to the HUSB238 on the jack power board (its CC ESD, PESD24VL1BA, sits there too). SBU1/SBU2 not connected.
Routing (--route): ../../grid_router.py (negotiated-congestion grid router, 0.025 mm grid), then pulled tight, then GND poured on both
sides (solid pad connections). Freerouting (--freerouting) leaves this board part-routed even with the right rules, so it is not the default.
Tracks: 0.127 signals, 0.3 VBUS, 0.25 GND; vias 0.45 / 0.2 drill; rule clearance 0.1 (PCBWay standard 4/4 mil, 0.2 drill), routed to 0.127."""
import os, sys, json, subprocess
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
KI = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, KI)
import sch_gen
from kicad7_tools import FP, V, mm, save_fp, write_project, drc, route
import grid_router as gr

NAME = "usb-c-board"
PCB_VERSION = "v0.1"
CAD_VERSION = "v0.40"
LIB = "usbc"; LIB_DIR = os.path.join(HERE, LIB + ".pretty")
ORIGIN = (100.0, 100.0)
BW, BH, BT = 12.0, 6.0, 1.6
RULES = dict(clearance=0.1, track=0.127, min_track=0.1, via_d=0.45, via_drill=0.2, edge=0.25)   # PCBWay standard: 4/4 mil, 0.2 drill
FREEROUTING = os.environ.get("FREEROUTING_JAR", "/home/claude/tools/freerouting-2.1.0.jar")
WIDTHS = {"default": 0.127, "VBUS": 0.3, "GND": 0.25}
ROUTE_CLEARANCE = 0.127   # the router keeps 5 mil (+ its 0.02 grid margin) although the rule is 4 mil
ROUTE_ORDER = ["VBUS", "GND", "DP", "DN", "CC1", "CC2"]   # first-round order: the best of 4 orders tried (14 vias; the others 16-18)

# spring-contact landing pads: (name, net, panel x, panel y) from the CAD (case/params.py usb_pwr_contacts, v0.38)
SOCKET_PANEL_Y = -53.40
CONTACTS = [("15V_1", "VBUS", -0.8, -51.4), ("15V_2", "VBUS", 0.8, -51.4), ("GND_1", "GND", -0.8, -53.0), ("GND_2", "GND", 0.8, -53.0),
            ("DP", "DP", -4.6, -51.4), ("DN", "DN", 4.6, -51.4), ("CC1", "CC1", -5.0, -53.0), ("CC2", "CC2", 5.0, -53.0)]


def kc(px, py):   # panel (mm) -> board-local KiCad (mm)
    return px, -(py - SOCKET_PANEL_Y)


def P(x, y):
    return V(ORIGIN[0] + x, ORIGIN[1] + y)


def fp_usbc(board):
    f = FP(board, LIB, "USB_C_16P_Vertical_ShouHan_LTH6.8", "SHOU HAN TYPE-C 16P LTH6.8 vertical, LCSC C5187468 (land pattern from the "
           "published numbers: LCSC/EasyEDA footprint and three open footprints agree)")
    for i, n in enumerate(("A1", "A4", "A5", "A6", "A7", "A8", "A9", "A12")):
        f.smd(n, (-2.75, -1.25, -0.75, -0.25, 0.25, 0.75, 1.25, 2.75)[i], -0.865, 0.30, 0.87)
    for i, n in enumerate(("B1", "B4", "B5", "B6", "B7", "B8", "B9", "B12")):
        f.smd(n, (2.75, 1.25, 0.75, 0.25, -0.25, -0.75, -1.25, -2.75)[i], 0.865, 0.30, 0.87)
    for sx in (-1, 1):
        for sy in (-1, 1):
            f.pth("S", sx * 2.40, sy * 2.15, 1.35, 1.10, 0.85, 0.60)
    f.npth(3.75, 0.0, 0.80); f.npth(-3.75, 0.0, 0.60)
    f.rect(-4.47, -1.58, 4.47, 1.58, pcbnew.F_Fab)
    f.rect(-4.75, -2.95, 4.75, 2.95, pcbnew.F_CrtYd)
    return f.done(-3.4)


def fp_dfn1610(board):
    f = FP(board, LIB, "D_DFN1610-2_ESDA25P35", "ST ESDA25P35-1U1M QFN 1.6 x 1.0, 2 terminals 0.80 x 0.35 at 1.05 [S]; pads [A]; pin 1 = bar")
    f.smd("1", -0.525, 0, 0.55, 0.95); f.smd("2", 0.525, 0, 0.55, 0.95)
    f.rect(-0.8, -0.5, 0.8, 0.5, pcbnew.F_Fab); f.rect(-1.05, -0.7, 1.05, 0.7, pcbnew.F_CrtYd)
    return f.done(-1.0)


def fp_contact(board):
    f = FP(board, LIB, "SpringContact_Landing_D1.2", "landing pad for a Harwin P70-5100045 spring contact (pad Ø1.2 [S-dist]), no paste")
    f.smd("1", 0, 0, 1.2, 1.2, shape="circle", paste=False)
    f.rect(-0.75, -0.75, 0.75, 0.75, pcbnew.F_CrtYd)
    return f.done(-1.0)


def comps():
    usb_pins = [("A1", "GND", "power_in", "L"), ("A4", "VBUS", "power_out", "L"), ("A5", "CC1", "bidirectional", "L"),
                ("A6", "D+", "bidirectional", "L"), ("A7", "D-", "bidirectional", "L"), ("A8", "SBU1", "passive", "L"),
                ("A9", "VBUS", "power_out", "L"), ("A12", "GND", "power_in", "L"),
                ("B1", "GND", "power_in", "R"), ("B4", "VBUS", "power_out", "R"), ("B5", "CC2", "bidirectional", "R"),
                ("B6", "D+", "bidirectional", "R"), ("B7", "D-", "bidirectional", "R"), ("B8", "SBU2", "passive", "R"),
                ("B9", "VBUS", "power_out", "R"), ("B12", "GND", "power_in", "R"), ("S", "SHIELD", "passive", "R")]
    usb_nets = {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "S": "GND", "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
                "A5": "CC1", "B5": "CC2", "A6": "DP", "B6": "DP", "A7": "DN", "B7": "DN", "A8": None, "B8": None}
    out = [dict(ref="J1", sym="USB_C_16P", value="TYPE-C 16P LTH6.8", fp="USB_C_16P_Vertical_ShouHan_LTH6.8", pos=(0.0, 0.0), rot=0, side="F",
                pins=usb_pins, nets=usb_nets, fields={"MPN": "TYPE-C 16P LTH6.8", "Manufacturer": "SHOU HAN", "LCSC": "C5187468"}),
           dict(ref="D1", sym="TVS_Uni", value="ESDA25P35-1U1M", fp="D_DFN1610-2_ESDA25P35", pos=kc(-0.6, -55.55), rot=0, side="B",
                pins=[("1", "K", "passive", "L"), ("2", "A", "passive", "R")], nets={"1": "VBUS", "2": "GND"},
                fields={"MPN": "ESDA25P35-1U1M", "Manufacturer": "STMicroelectronics", "LCSC": "C1974707"}),
           dict(ref="U1", sym="TPD2E2U06", value="TPD2E2U06DRLR", fp="SOT-553", pos=kc(4.2, -55.25), rot=0,
                side="B", pins=[("1", "NC", "no_connect", "L"), ("2", "NC", "no_connect", "L"), ("3", "IO1", "passive", "L"),
                                ("4", "GND", "passive", "R"), ("5", "IO2", "passive", "R")],
                nets={"1": None, "2": None, "3": "DP", "4": "GND", "5": "DN"},
                fields={"MPN": "TPD2E2U06DRLR", "Manufacturer": "Texas Instruments", "LCSC": "C1972959"})]
    for i, (nm, net, px, py) in enumerate(CONTACTS, 1):
        out.append(dict(ref=f"P{i}", sym="LandingPad", value=f"contact {nm}", fp="SpringContact_Landing_D1.2", pos=kc(px, py), rot=0, side="B",
                        pins=[("1", nm, "passive", "L")], nets={"1": net}, fields={"Note": "landing pad, bare ENIG gold"}, bom=False))
    for c in out:
        c.setdefault("bom", True); c.setdefault("lib", LIB)
        c["footprint"] = c["lib"] + ":" + c["fp"]; c["place"] = c["pos"]
    return out


def build():
    C = comps()
    flags = [dict(ref=f"#FLG0{i + 1}", sym="PWR_FLAG", pins=[("1", "~", "power_out", "L")], value="PWR_FLAG", footprint="", nets={"1": n},
                  fields={}, bom=False, place=None, side=None) for i, n in enumerate(("VBUS", "GND"))]
    sch_gen.write(os.path.join(HERE, NAME + ".kicad_sch"), f"USB-C board {PCB_VERSION}", NAME, C + flags, rev=PCB_VERSION,
                  comment=f"knob CAD {CAD_VERSION}; generated by make_board.py")
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings(); ds.SetBoardThickness(mm(BT)); ds.SetCopperLayerCount(2)
    ds.m_CopperEdgeClearance = mm(RULES["edge"])
    r = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_RECT); r.SetLayer(pcbnew.Edge_Cuts); r.SetWidth(mm(0.05))
    r.SetStart(P(-BW / 2, -BH / 2)); r.SetEnd(P(BW / 2, BH / 2)); board.Add(r)
    builders = {"USB_C_16P_Vertical_ShouHan_LTH6.8": fp_usbc, "D_DFN1610-2_ESDA25P35": fp_dfn1610, "SpringContact_Landing_D1.2": fp_contact}
    if os.path.isdir(LIB_DIR):
        import shutil; shutil.rmtree(LIB_DIR)
    for n, fn in builders.items():
        save_fp(LIB_DIR, fn(board))
    # KiCad's own SOT-553 (KiCad footprint library, CC-BY-SA 4.0 with the design exception), copied in so the project stands alone
    sot = pcbnew.FootprintLoad("/usr/share/kicad/footprints/Package_TO_SOT_SMD.pretty", "SOT-553")
    sot.SetFPID(pcbnew.LIB_ID(LIB, "SOT-553"))
    for g in list(sot.GraphicalItems()):   # the board copy has no silk (below), so neither has the library copy
        if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            sot.Remove(g)
    save_fp(LIB_DIR, sot)
    builders["SOT-553"] = lambda b: pcbnew.FootprintLoad(LIB_DIR, "SOT-553")
    nets = {}

    def net(n):
        if n not in nets:
            nets[n] = pcbnew.NETINFO_ITEM(board, n); board.Add(nets[n])
        return nets[n]
    placed = {}
    for c in C:
        fp = builders[c["fp"]](board)
        fp.SetFPID(pcbnew.LIB_ID(LIB, c["fp"]))
        for g in list(fp.GraphicalItems()):   # no silkscreen on this 12 x 6 board (the socket covers the front, pads fill the back)
            if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                fp.Remove(g)
        fp.SetReference(c["ref"]); fp.SetValue(c["value"])
        board.Add(fp)
        fp.SetPosition(P(*c["pos"]))
        if c["rot"]:
            fp.SetOrientationDegrees(c["rot"])
        if c["side"] == "B":
            fp.Flip(fp.GetPosition(), False)
        fp.SetPath(pcbnew.KIID_PATH(sch_gen.fp_path(NAME, c["ref"])))
        if hasattr(fp, "SetSheetname"):
            fp.SetSheetname("Root"); fp.SetSheetfile(NAME + ".kicad_sch")
        else:   # KiCad 7
            fp.SetProperty("Sheetname", "Root"); fp.SetProperty("Sheetfile", NAME + ".kicad_sch")
        for k, v in c["fields"].items():
            if v:
                (fp.SetField if hasattr(fp, "SetField") else fp.SetProperty)(k, v)
        if hasattr(fp, "GetFields"):
            for t in fp.GetFields():
                if not (t.IsReference() or t.IsValue()):
                    t.SetVisible(False)
        if not c["bom"]:
            if hasattr(fp, "SetExcludedFromBOM"):
                fp.SetExcludedFromBOM(True); fp.SetExcludedFromPosFiles(True)
            else:   # KiCad 7: attributes
                fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        pname = {pn: nm for pn, nm, *_ in c["pins"]}
        for pad in fp.Pads():
            num = pad.GetNumber()
            if num == "" or num not in pname:
                continue
            n = c["nets"].get(num)
            pad.SetNet(net(n if n else f"unconnected-({c['ref']}-{pname[num]}-Pad{num})"))
        placed[c["ref"]] = fp

    def txt(t, x, y, layer, size, mirror):
        g = pcbnew.PCB_TEXT(board); g.SetText(t); g.SetPosition(P(x, y)); g.SetLayer(layer)
        g.SetTextSize(V(size, size)); g.SetTextThickness(mm(size * 0.15)); g.SetMirrored(mirror); board.Add(g)
    ds.SetAuxOrigin(P(0, 0)); ds.SetGridOrigin(P(0, 0))
    return board, placed


def add_gnd_zones(pcb_path):
    b = pcbnew.LoadBoard(pcb_path)
    gnd = b.FindNet("GND")
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(gnd)
        z.SetLocalClearance(mm(0.2)); z.SetMinThickness(mm(0.15)); z.SetThermalReliefGap(mm(0.2)); z.SetThermalReliefSpokeWidth(mm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)   # spokes starve on the 0.3 mm socket pads
        ol = z.Outline(); ol.NewOutline()
        for x, y in ((-BW / 2, -BH / 2), (BW / 2, -BH / 2), (BW / 2, BH / 2), (-BW / 2, BH / 2)):
            ol.Append(mm(ORIGIN[0] + x), mm(ORIGIN[1] + y))
        b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(pcb_path, b)


def grid_route(pcb_path):
    b = pcbnew.LoadBoard(pcb_path)
    r = gr.Router(gr.board_pads(b, ORIGIN), (-BW / 2, -BH / 2, BW / 2, BH / 2), dict(RULES, hole_clearance=0.2, clearance=ROUTE_CLEARANCE), WIDTHS)
    ok = r.run(iters=80, order=ROUTE_ORDER, h_inc=1.5, pf_mult=1.3)
    if not ok:
        raise SystemExit("grid router: nets still too close after 80 rounds")
    r.smooth()
    gr.apply(b, r, ORIGIN, RULES["via_d"], RULES["via_drill"])
    pcbnew.SaveBoard(pcb_path, b)
    return sum(len(r.paths[n][1]) for n in r.nets)


def write_placement(pcb_path, out):
    """Pad and part positions in the knob's panel frame (x as KiCad, y up the panel; z not used) for check_cad.py."""
    b = pcbnew.LoadBoard(pcb_path)
    to_panel = lambda x, y: (round(pcbnew.ToMM(x) - ORIGIN[0], 4), round(SOCKET_PANEL_Y - (pcbnew.ToMM(y) - ORIGIN[1]), 4))
    d = dict(board=dict(w=BW, h=BH, t=BT, centre=(0.0, SOCKET_PANEL_Y)), cad_version=CAD_VERSION, pcb_version=PCB_VERSION, parts={}, pads=[])
    for f in b.GetFootprints():
        bb = f.GetFpPadsLocalBbox() if hasattr(f, "GetFpPadsLocalBbox") else None
        fab = [g for g in f.GraphicalItems() if g.GetLayer() in (pcbnew.F_Fab, pcbnew.B_Fab) and hasattr(g, "GetShape") and g.GetShape() == pcbnew.SHAPE_T_RECT]
        box = None
        if fab:
            (x0, y0), (x1, y1) = to_panel(fab[0].GetStart().x, fab[0].GetStart().y), to_panel(fab[0].GetEnd().x, fab[0].GetEnd().y)
            box = (min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1))
        d["parts"][f.GetReference()] = dict(xy=to_panel(f.GetPosition().x, f.GetPosition().y), side="B" if f.IsFlipped() else "F",
                                            rot=f.GetOrientationDegrees(), fab_box=box, value=f.GetValue())
        for p in f.Pads():
            d["pads"].append(dict(ref=f.GetReference(), num=p.GetNumber(), net=p.GetNetname(), xy=to_panel(p.GetPosition().x, p.GetPosition().y),
                                  size=(round(pcbnew.ToMM(p.GetSize().x), 4), round(pcbnew.ToMM(p.GetSize().y), 4)),
                                  drill=round(pcbnew.ToMM(p.GetDrillSize().x), 4)))
    json.dump(d, open(out, "w"), indent=1)


if __name__ == "__main__":
    pcb_path = os.path.join(HERE, NAME + ".kicad_pcb")
    libs = [(LIB, "${KIPRJMOD}/" + LIB + ".pretty")]
    write_project(HERE, NAME, RULES, libs)   # before any save, so nothing writes KiCad's default net class over it
    board, placed = build()
    pcbnew.SaveBoard(pcb_path, board)
    write_project(HERE, NAME, RULES, libs)
    if "--route" in sys.argv:
        print("grid router: vias", grid_route(pcb_path))
        add_gnd_zones(pcb_path)
    elif "--freerouting" in sys.argv:
        print("routed:", route(pcb_path, FREEROUTING, passes=100, attempts=6))
        add_gnd_zones(pcb_path)
    write_project(HERE, NAME, RULES, libs)
    nv, nu, rep = drc(pcb_path, os.path.join(HERE, "drc.rpt"))
    print("DRC violations", nv, "unconnected", nu)
    step = os.path.join(HERE, "..", NAME + ".step")
    subprocess.run(["kicad-cli", "pcb", "export", "step", "--grid-origin", "--force", "-o", step, pcb_path], check=True, capture_output=True)
    write_placement(pcb_path, os.path.join(HERE, "..", "placement.json"))
