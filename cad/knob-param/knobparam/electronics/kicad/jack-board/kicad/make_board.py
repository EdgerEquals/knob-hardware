"""Jack board (knob step 2, CAD v0.43). Generates the schematic, the board, its footprint library and the project; --route routes it.
Run with the system python that has pcbnew (KiCad 7.0.11):  /usr/bin/python3 make_board.py [--route]
  The four Thonk PJ366ST stereo jacks sit on its top (F) face, their bushings through the faceplate, their pins soldered in plated
  slots that cover every published pin position [Ed 5 Nov Q14 = B]; the 8 Harwin P70-5100045 spring contacts on its tab press on the
  USB-C board's landing pads [Q5, Q12, Q16, Q17]; two XFCN 2x6 1.27 mm stacks on its back (B) face carry everything down to the jack
  power board 4.9 below. No other parts: the jack circuits are on the power board [Q2, Q7].
  Outline (panel frame, y up): the jack row 43.0 x 10.5 (y -48.90..-38.40), a 2.7 x 0.55 bump over each tip slot [Q18], a tongue
  ±1.26 down to y -52.14 under each sleeve slot [Q15] (the outer two 0.5 wider inward [v0.44 A]: room for the sleeve's ground past the
  ring slot), the tab ±5.85 down to y -53.90 into the USB-C channel [Q16]. 1.6 mm, 2 layers.
  KiCad frame: x = panel x, y = -(panel y - JY), JY = the jack axes (panel y -44.40); KiCad origin (100, 100).
  J1-J4  Thonk PJ366ST at x -16.5, -5.8, +5.8, +16.5 [Q15, Q17]; J1-J3 switchable [Q1, Q2], J4 the audio jack: tip = audio out,
         ring = audio in [Q9, Q10]. Slots [S-lib: KiCad's PJ398SM footprint, which Thonk says the stereo shares; 4ms, GuavTek,
         westlicht, clacktronics, requencer]: T +4.92..+5.21 from the axis (1.43 wide), R -3.35..-3.38 (1.42), S -5.715..-6.48 (1.22);
         0.35 ring. Sleeve = GND.
  P1-P8  Harwin P70-5100045 (LCSC C21675240; element14 2664891), SMD pad Ø1.2 [S-dist], at the USB-C board's landing pads.
  H1, H2 XFCN PZ127VS-12-12-H16-4.5-R (LCSC C2840009), 2x6 1.27 mm SMD male, rotated (pins along x) at x ∓11.15 [v0.42 A]; land
         pattern KiCad's PinHeader_2x06_P1.27mm_Vertical_SMD (KiCad library, CC-BY-SA 4.0 with the design exception) [C: check it
         against XFCN's drawing at the pre-quote]. 1 A a pin [S: JLCPCB listing; LCSC says 2 A]: VBUS on 4 pins, GND on 8.
Header pinout [A] (panel view from the front; 'upper' = the row nearer the jack tops); the power board's sockets mirror it:
  H1 (x -11.15) upper: J1_TIP GND GND GND GND J2_TIP      lower: J1_RING GND VBUS VBUS CC1 J2_RING
  H2 (x +11.15) upper: J3_TIP GND DP DN GND J4_TIP        lower: J3_RING VBUS VBUS CC2 GND J4_RING"""
import os, sys, subprocess, json
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
KI = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, KI)
import sch_gen
from kicad7_tools import FP, V, mm, save_fp, write_project, drc, route
import grid_router as gr

NAME = "jack-board"
PCB_VERSION = "v0.1"
CAD_VERSION = "v0.44"
LIB = "jackb"; LIB_DIR = os.path.join(HERE, LIB + ".pretty")
ORIGIN = (100.0, 100.0)
BT = 1.6
RULES = dict(clearance=0.1, track=0.2, min_track=0.1, via_d=0.45, via_drill=0.2, edge=0.25)   # PCBWay standard 4/4 mil, 0.2 drill
ROUTE_CLASSES = [("Power", 0.2, 0.5, ["VBUS"])]   # VBUS routed 0.5 wide, 0.2 clear; the rest (GND too: its sleeve pads leave the tongues past the ring pads, about 0.6 between pad and edge) at 0.2 wide, 0.15 clear
FREEROUTING = os.environ.get("FREEROUTING_JAR", "/home/claude/tools/freerouting-2.1.0.jar")
WIDTHS = {"default": 0.2, "VBUS": 0.5, "GND": 0.4}   # grid router: signals 0.2, VBUS 0.5 (1.5 A a side), GND 0.4 (plus the pours)
ROUTE_CLEARANCE = 0.15

# ---- numbers from the model (case/params.py, v0.43); check_cad.py compares them with the model ----
JY = -44.40                                  # jack axes
JACK_X = (-16.5, -5.8, 5.8, 16.5)
BODY_Y = (-4.5, 6.0)                         # PJ366ST body from its axis (sleeve side down) [S-lib]
PINS = (("T", 4.92, 5.21, 1.43), ("R", -3.38, -3.35, 1.42), ("S", -6.48, -5.715, 1.22))
RING = 0.35
BARREL_KEEP = 4.0                            # Ø, no copper on the top face round each jack axis [S-dist 3 mm; A 4]
BOARD_X = (-21.5, 21.5)
BUMP = (2.7, 0.55)                           # [Q18]
TONGUE = (1.26, -52.14)                      # half width, bottom y [Q15]
TONGUE_INNER = 0.5                           # v0.44 [A]: the outer two tongues this much wider on their inner side (room for the sleeve's ground)
TAB = (5.85, -53.90)                         # [Q16]
CONTACTS = [("15V_1", "VBUS", -0.8, -51.4), ("15V_2", "VBUS", 0.8, -51.4), ("GND_1", "GND", -0.8, -53.0), ("GND_2", "GND", 0.8, -53.0),
            ("DP", "DP", -4.0, -51.4), ("DN", "DN", 4.0, -51.4), ("CC1", "CC1", -5.0, -53.0), ("CC2", "CC2", 5.0, -53.0)]
HDR_X, HDR_Y = 11.15, (JY + BODY_Y[0] + JY + BODY_Y[1]) / 2
HDR_NETS = {"H1": (["J1_TIP", "GND", "GND", "GND", "GND", "J2_TIP"], ["J1_RING", "GND", "VBUS", "VBUS", "CC1", "J2_RING"]),
            "H2": (["J3_TIP", "GND", "DP", "DN", "GND", "J4_TIP"], ["J3_RING", "VBUS", "VBUS", "CC2", "GND", "J4_RING"])}


def kc(px, py):   # panel (mm) -> board-local KiCad (mm)
    return px, -(py - JY)


def P(x, y):
    return V(ORIGIN[0] + x, ORIGIN[1] + y)


def outline():
    """Board outline in panel coordinates (y up), clockwise from the top left: a top profile (bumps) and a bottom profile (tongues, tab)."""
    x0, x1 = BOARD_X; top, bot = JY + BODY_Y[1], JY + BODY_Y[0]
    tops = [(jx - BUMP[0] / 2, jx + BUMP[0] / 2, top + BUMP[1]) for jx in JACK_X]
    def tongue(jx):
        a, b = jx - TONGUE[0], jx + TONGUE[0]
        return (a, b + TONGUE_INNER) if jx == min(JACK_X) else (a - TONGUE_INNER, b) if jx == max(JACK_X) else (a, b)
    bots = [(*tongue(jx), TONGUE[1]) for jx in JACK_X] + [(-TAB[0], TAB[0], TAB[1])]

    def profile(spans, base, pick):
        xs = sorted({x0, x1} | {a for a, b, _ in spans} | {b for a, b, _ in spans})
        pts = []
        for a, b in zip(xs, xs[1:]):
            m = (a + b) / 2
            y = pick([base] + [v for s0, s1, v in spans if s0 <= m <= s1])
            if pts and abs(pts[-1][1] - y) < 1e-9:
                pts[-1] = (b, y)
            else:
                pts += [(a, y), (b, y)]
        return pts
    up = profile(tops, top, max)
    dn = profile(bots, bot, min)
    return up + list(reversed(dn))


def fp_jack(board):
    f = FP(board, LIB, "PJ366ST_Slots", "Thonk PJ366ST stereo 3.5 mm jack: plated slots over every published pin position [S-lib, Ed Q14 = B], "
           "0.35 ring; body -4.5..+6.0 from the axis")
    for n, y0, y1, w in PINS:
        L = (y1 - y0) + w
        f.pth(n, 0, -(y0 + y1) / 2, w + 2 * RING, L + 2 * RING, w, L)
    f.rect(-5.0, -BODY_Y[1], 5.0, -BODY_Y[0], pcbnew.F_Fab)
    tn, t0, t1, tw = PINS[0]; sn, s0, s1, sw = PINS[2]
    yt, yb, hl, yl = -(t1 + tw / 2 + RING + 0.1), -BODY_Y[0] + 0.25, sw / 2 + RING + 0.1, -(s0 - sw / 2 - RING - 0.1)
    f.poly([(-5.25, yt), (5.25, yt), (5.25, yb), (hl, yb), (hl, yl), (-hl, yl), (-hl, yb), (-5.25, yb)], pcbnew.F_CrtYd)   # body + sleeve lug
    return f.done(0.0)


def fp_contact(board):
    f = FP(board, LIB, "Harwin_P70-5100045", "Harwin P70-5100045 SMD spring contact, pad Ø1.2, body Ø1.03 [S-dist]")
    f.smd("1", 0, 0, 1.2, 1.2, shape="circle")
    f.rect(-0.65, -0.65, 0.65, 0.65, pcbnew.F_CrtYd)
    return f.done(-1.0)


def comps(hdr_nets):
    out = []
    for i, jx in enumerate(JACK_X, 1):
        role = "audio: tip out, ring in" if i == 4 else "switchable"
        out.append(dict(ref=f"J{i}", sym="PJ366ST", value="PJ366ST", fp="PJ366ST_Slots", pos=kc(jx, JY), rot=0, side="F",
                        pins=[("T", "TIP", "passive", "L"), ("R", "RING", "passive", "L"), ("S", "SLEEVE", "passive", "R")],
                        nets={"T": f"J{i}_TIP", "R": f"J{i}_RING", "S": "GND"},
                        fields={"MPN": "PJ366ST", "Manufacturer": "Thonk", "Note": role}))
    for i, (nm, net, px, py) in enumerate(CONTACTS, 1):
        out.append(dict(ref=f"P{i}", sym="SpringContact", value="P70-5100045", fp="Harwin_P70-5100045", pos=kc(px, py), rot=0, side="F",
                        pins=[("1", nm, "passive", "L")], nets={"1": net},
                        fields={"MPN": "P70-5100045", "Manufacturer": "Harwin", "LCSC": "C21675240", "Contact": nm}))
    for ref, sx in (("H1", -1), ("H2", 1)):
        out.append(dict(ref=ref, sym="Conn_2x06", value="PZ127VS-12-12-H16-4.5-R", fp="PinHeader_2x06_P1.27mm_Vertical_SMD",
                        pos=kc(sx * HDR_X, HDR_Y), rot=90, side="B",
                        pins=[(str(n), str(n), "passive", "L" if n % 2 else "R") for n in range(1, 13)], nets=hdr_nets.get(ref, {}),
                        fields={"MPN": "PZ127VS-12-12-H16-4.5-R", "Manufacturer": "XFCN", "LCSC": "C2840009"}))
    for c in out:
        c.setdefault("bom", True); c["footprint"] = LIB + ":" + c["fp"]
    return out


def build():
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings(); ds.SetBoardThickness(mm(BT)); ds.SetCopperLayerCount(2)
    ds.m_CopperEdgeClearance = mm(RULES["edge"])
    pts = [kc(x, y) for x, y in outline()]
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.05))
        s.SetStart(P(ax, ay)); s.SetEnd(P(bx, by)); board.Add(s)
    builders = {"PJ366ST_Slots": fp_jack, "Harwin_P70-5100045": fp_contact}
    if os.path.isdir(LIB_DIR):
        import shutil; shutil.rmtree(LIB_DIR)
    for n, fn in builders.items():
        save_fp(LIB_DIR, fn(board))
    hdr = pcbnew.FootprintLoad("/usr/share/kicad/footprints/Connector_PinHeader_1.27mm.pretty", "PinHeader_2x06_P1.27mm_Vertical_SMD")
    hdr.SetFPID(pcbnew.LIB_ID(LIB, "PinHeader_2x06_P1.27mm_Vertical_SMD"))
    for g in list(hdr.GraphicalItems()):
        if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            hdr.Remove(g)
    save_fp(LIB_DIR, hdr)
    builders["PinHeader_2x06_P1.27mm_Vertical_SMD"] = lambda b: pcbnew.FootprintLoad(LIB_DIR, "PinHeader_2x06_P1.27mm_Vertical_SMD")
    nets = {}

    def net(n):
        if n not in nets:
            nets[n] = pcbnew.NETINFO_ITEM(board, n); board.Add(nets[n])
        return nets[n]
    C = comps({})
    placed = {}
    for c in C:
        fp = builders[c["fp"]](board)
        fp.SetFPID(pcbnew.LIB_ID(LIB, c["fp"]))
        for g in list(fp.GraphicalItems()):
            if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                fp.Remove(g)
        fp.SetReference(c["ref"]); fp.SetValue(c["value"])
        board.Add(fp)
        fp.SetPosition(P(*c["pos"]))
        if c["rot"]:
            fp.SetOrientationDegrees(c["rot"])
        if c["side"] == "B":
            fp.Flip(fp.GetPosition(), False)
        fp.Reference().SetLayer(pcbnew.B_Fab if c["side"] == "B" else pcbnew.F_Fab)
        fp.SetPath(pcbnew.KIID_PATH(sch_gen.fp_path(NAME, c["ref"])))
        fp.SetProperty("Sheetname", "Root"); fp.SetProperty("Sheetfile", NAME + ".kicad_sch")
        for k, v in c["fields"].items():
            fp.SetProperty(k, v)
        placed[c["ref"]] = (fp, c)
    # header nets by position: upper row = nearer the jack tops (panel y higher), each row left to right in panel x
    hdr_nets = {}
    for ref in ("H1", "H2"):
        fp, c = placed[ref]
        pads = [(pcbnew.ToMM(p.GetPosition().x) - ORIGIN[0], JY - (pcbnew.ToMM(p.GetPosition().y) - ORIGIN[1]), p.GetNumber()) for p in fp.Pads()]
        ymid = sum(p[1] for p in pads) / len(pads)
        upper = sorted([p for p in pads if p[1] > ymid]); lower = sorted([p for p in pads if p[1] < ymid])
        m = {}
        for row, names in zip((upper, lower), HDR_NETS[ref]):
            for (_x, _y, num), n in zip(row, names):
                m[num] = n
        hdr_nets[ref] = m
    for ref, (fp, c) in placed.items():
        nm = hdr_nets.get(ref, c["nets"])
        c["nets"] = nm
        for pad in fp.Pads():
            n = nm.get(pad.GetNumber())
            if n:
                pad.SetNet(net(n))
    # no copper on the top face under each jack's barrel: a plug's tip comes through the back of the body there [S-dist Thonk: keep
    # copper out from under the barrel, 3 mm]; kept out to Ø4 [A]
    for jx in JACK_X:
        k = pcbnew.ZONE(board); k.SetIsRuleArea(True); k.SetLayer(pcbnew.F_Cu)
        k.SetDoNotAllowTracks(True); k.SetDoNotAllowVias(True); k.SetDoNotAllowCopperPour(True); k.SetDoNotAllowPads(False)
        k.SetDoNotAllowFootprints(False)
        ol = k.Outline(); ol.NewOutline()
        cx, cy = kc(jx, JY)
        for i in range(24):
            a = 2 * 3.141592653589793 * i / 24
            ol.Append(mm(ORIGIN[0] + cx + BARREL_KEEP / 2 * __import__("math").cos(a)), mm(ORIGIN[1] + cy + BARREL_KEEP / 2 * __import__("math").sin(a)))
        board.Add(k)
    t = pcbnew.PCB_TEXT(board); t.SetText(f"jack board {PCB_VERSION} / knob {CAD_VERSION}"); t.SetPosition(P(0.0, kc(0, HDR_Y)[1]))
    t.SetLayer(pcbnew.B_SilkS); t.SetTextSize(V(0.7, 0.7)); t.SetTextThickness(mm(0.12)); t.SetMirrored(True); board.Add(t)
    ds.SetAuxOrigin(P(0, 0)); ds.SetGridOrigin(P(0, 0))
    C = comps(hdr_nets)
    sch_gen.write(os.path.join(HERE, NAME + ".kicad_sch"), f"Jack board {PCB_VERSION}", NAME,
                  C + [dict(ref="#FLG01", sym="PWR_FLAG", pins=[("1", "~", "power_out", "L")], value="PWR_FLAG", footprint="", nets={"1": "VBUS"},
                            fields={}, bom=False),
                       dict(ref="#FLG02", sym="PWR_FLAG", pins=[("1", "~", "power_out", "L")], value="PWR_FLAG", footprint="", nets={"1": "GND"},
                            fields={}, bom=False)],
                  rev=PCB_VERSION, comment=f"knob CAD {CAD_VERSION}; generated by make_board.py")
    return board, placed


def add_gnd_zones(pcb_path):
    b = pcbnew.LoadBoard(pcb_path)
    gnd = b.FindNet("GND")
    pts = [kc(x, y) for x, y in outline()]
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(gnd)
        z.SetLocalClearance(mm(0.25)); z.SetMinThickness(mm(0.2)); z.SetThermalReliefGap(mm(0.25)); z.SetThermalReliefSpokeWidth(mm(0.4))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)   # sleeve slots get spokes (hand / selective solder); SMD pads solid
        ol = z.Outline(); ol.NewOutline()
        for x, y in pts:
            ol.Append(mm(ORIGIN[0] + x), mm(ORIGIN[1] + y))
        b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(pcb_path, b)


def grid_route(pcb_path, order=None, iters=80):
    b = pcbnew.LoadBoard(pcb_path)
    ol = [kc(x, y) for x, y in outline()]
    xs = [p[0] for p in ol]; ys = [p[1] for p in ol]
    r = gr.Router(gr.board_pads(b, ORIGIN), (min(xs), min(ys), max(xs), max(ys)), dict(RULES, hole_clearance=0.2, clearance=ROUTE_CLEARANCE),
                  WIDTHS, g=0.05, margin=0.04, via_cost=1.5, outline=ol)
    ok = r.run(iters=iters, order=order, h_inc=1.5, pf_mult=1.3)
    if not ok:
        raise SystemExit(f"grid router: nets still too close after {iters} rounds")
    r.smooth()
    gr.apply(b, r, ORIGIN, RULES["via_d"], RULES["via_drill"])
    pcbnew.SaveBoard(pcb_path, b)
    return sum(len(r.paths[n][1]) for n in r.nets)


def write_placement(pcb_path, out):
    b = pcbnew.LoadBoard(pcb_path)
    to_panel = lambda x, y: (round(pcbnew.ToMM(x) - ORIGIN[0], 4), round(JY - (pcbnew.ToMM(y) - ORIGIN[1]), 4))
    d = dict(cad_version=CAD_VERSION, pcb_version=PCB_VERSION, thickness=BT, outline=outline(), parts={}, pads=[])
    for f in b.GetFootprints():
        d["parts"][f.GetReference()] = dict(xy=to_panel(f.GetPosition().x, f.GetPosition().y), side="B" if f.IsFlipped() else "F",
                                            rot=f.GetOrientationDegrees(), value=f.GetValue())
        for p in f.Pads():
            d["pads"].append(dict(ref=f.GetReference(), num=p.GetNumber(), net=p.GetNetname(), xy=to_panel(p.GetPosition().x, p.GetPosition().y),
                                  size=(round(pcbnew.ToMM(p.GetSize().x), 4), round(pcbnew.ToMM(p.GetSize().y), 4)),
                                  drill=(round(pcbnew.ToMM(p.GetDrillSize().x), 4), round(pcbnew.ToMM(p.GetDrillSize().y), 4)),
                                  rot=p.GetOrientationDegrees()))
    json.dump(d, open(out, "w"), indent=1)


if __name__ == "__main__":
    pcb_path = os.path.join(HERE, NAME + ".kicad_pcb")
    libs = [(LIB, "${KIPRJMOD}/" + LIB + ".pretty")]
    rc = dict(RULES, clearance=0.15)   # Freerouting reads the classes: route the Default class at 0.15
    write_project(HERE, NAME, rc, libs, ROUTE_CLASSES)
    board, placed = build()
    pcbnew.SaveBoard(pcb_path, board)
    write_project(HERE, NAME, rc, libs, ROUTE_CLASSES)
    if "--route" in sys.argv:   # Freerouting (this board is roomy enough), the outline moved in 0.105 for it so tracks keep the 0.25 edge
        print("routed:", route(pcb_path, FREEROUTING, passes=100, attempts=4, edge_inset=RULES["edge"] - 0.15 + 0.005))
        add_gnd_zones(pcb_path)
    elif "--grid" in sys.argv:
        print("grid router: vias", grid_route(pcb_path))
        add_gnd_zones(pcb_path)
    write_project(HERE, NAME, rc, libs, ROUTE_CLASSES)
    nv, nu, rep = drc(pcb_path, os.path.join(HERE, "drc.rpt"))
    print("DRC violations", nv, "unconnected", nu)
    step = os.path.join(HERE, "..", NAME + ".step")
    subprocess.run(["kicad-cli", "pcb", "export", "step", "--grid-origin", "--force", "-o", step, pcb_path], check=True, capture_output=True)
    write_placement(pcb_path, os.path.join(HERE, "..", "placement.json"))
