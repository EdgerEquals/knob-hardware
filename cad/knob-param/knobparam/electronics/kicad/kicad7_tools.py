"""Shared helpers for the step-2 boards (5 Nov 2026), written for KiCad 7.0.11 (the Ubuntu archive's KiCad: KiCad's own repository is
blocked from the cloud workspace). KiCad 8 and 9 open and upgrade what these write.
  - footprint builders (pads, fab and courtyard rectangles) so each board's footprints are generated from numbers in one place
  - write_project(): project file with the board's rules
  - drc(): DRC through pcbnew.WriteDRCReport (kicad-cli 7 has no DRC); returns (violations, unconnected, report text)
  - route(): Freerouting (GPL-3.0, https://github.com/freerouting/freerouting), DSN out / SES in, best of a few attempts
Run with the system python that has pcbnew (/usr/bin/python3)."""
import json, os, re, subprocess
import pcbnew

mm = pcbnew.FromMM


def V(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


class FP:
    """Build a footprint at the origin, in KiCad coordinates (y down)."""

    def __init__(self, board, lib, name, descr=""):
        self.fp = pcbnew.FOOTPRINT(board)
        self.fp.SetFPID(pcbnew.LIB_ID(lib, name))
        self.fp.SetDescription(descr)
        self.fp.SetPosition(V(0, 0))

    @staticmethod
    def _at(p, x, y):   # KiCad 7 keeps a pad's footprint-local position in pos0
        p.SetPosition(V(x, y))
        if hasattr(p, "SetPos0"):
            p.SetPos0(V(x, y))

    def smd(self, num, x, y, w, h, shape="rect", paste=True, rr=0.25):
        p = pcbnew.PAD(self.fp)
        p.SetNumber(num); p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        p.SetShape({"rect": pcbnew.PAD_SHAPE_RECT, "circle": pcbnew.PAD_SHAPE_CIRCLE, "oval": pcbnew.PAD_SHAPE_OVAL,
                    "roundrect": pcbnew.PAD_SHAPE_ROUNDRECT}[shape])
        if shape == "roundrect":
            p.SetRoundRectRadiusRatio(rr)
        p.SetSize(V(w, h)); self._at(p, x, y)
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.F_Mask)
        if paste:
            ls.AddLayer(pcbnew.F_Paste)
        p.SetLayerSet(ls)
        self.fp.Add(p)
        return p

    def pth(self, num, x, y, w, h, dw, dh=None, shape="oval"):
        p = pcbnew.PAD(self.fp)
        p.SetNumber(num); p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        p.SetShape(pcbnew.PAD_SHAPE_OVAL if shape == "oval" else pcbnew.PAD_SHAPE_CIRCLE)
        p.SetSize(V(w, h)); self._at(p, x, y)
        if dh is not None and dh != dw:
            p.SetDrillShape(pcbnew.PAD_DRILL_SHAPE_OBLONG); p.SetDrillSize(V(dw, dh))
        else:
            p.SetDrillShape(pcbnew.PAD_DRILL_SHAPE_CIRCLE); p.SetDrillSize(V(dw, dw))
        p.SetLayerSet(pcbnew.PAD.PTHMask())
        self.fp.Add(p)
        return p

    def npth(self, x, y, d):
        p = pcbnew.PAD(self.fp)
        p.SetNumber(""); p.SetAttribute(pcbnew.PAD_ATTRIB_NPTH); p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        p.SetSize(V(d, d)); p.SetDrillSize(V(d, d)); self._at(p, x, y)
        p.SetLayerSet(pcbnew.PAD.UnplatedHoleMask())
        self.fp.Add(p)
        return p

    def rect(self, x0, y0, x1, y1, layer, w=0.05):
        s = pcbnew.FP_SHAPE(self.fp, pcbnew.SHAPE_T_RECT)
        s.SetStart(V(x0, y0)); s.SetEnd(V(x1, y1)); s.SetLayer(layer); s.SetWidth(mm(w)); s.SetLocalCoord()
        self.fp.Add(s)

    def poly(self, pts, layer, w=0.05):
        s = pcbnew.FP_SHAPE(self.fp, pcbnew.SHAPE_T_POLY)
        s.SetPolyPoints([V(x, y) for x, y in pts]); s.SetLayer(layer); s.SetWidth(mm(w)); s.SetLocalCoord()
        self.fp.Add(s)

    def done(self, ref_y=0.0):
        self.fp.Reference().SetPosition(V(0, ref_y)); self.fp.Reference().SetLayer(pcbnew.F_Fab)
        self.fp.Reference().SetTextSize(V(0.5, 0.5)); self.fp.Reference().SetTextThickness(mm(0.08))
        self.fp.Value().SetVisible(False)
        return self.fp


def save_fp(lib_dir, fp):
    if not os.path.isdir(lib_dir):
        pcbnew.FootprintLibCreate(lib_dir)
    pcbnew.FootprintSave(lib_dir, fp)


def _netclass(name, clearance, track, via_d, via_drill):
    # KiCad 7 drops a net class that lacks any of its keys (and falls back to clearance 0.2, via 0.6), so all are written
    return {"name": name, "clearance": clearance, "track_width": track, "via_diameter": via_d, "via_drill": via_drill,
            "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
            "bus_width": 12, "wire_width": 6, "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"}


def write_project(here, name, rules, libs, classes=()):
    """classes: extra net classes [(name, clearance, track, [net names])] on top of Default (from rules)."""
    ncs = [_netclass("Default", rules["clearance"], rules["track"], rules["via_d"], rules["via_drill"])]
    pats = []
    for cn, cl, tr, nets in classes:
        ncs.append(_netclass(cn, cl, tr, rules["via_d"], rules["via_drill"]))
        pats += [{"netclass": cn, "pattern": n} for n in nets]
    pro = {"meta": {"filename": name + ".kicad_pro", "version": 1},
           "board": {"design_settings": {"rules": {"min_clearance": rules["clearance"], "min_track_width": rules["min_track"],
                                                   "min_via_diameter": rules["via_d"], "min_through_hole_diameter": rules["via_drill"],
                                                   "min_copper_edge_clearance": rules["edge"], "min_hole_clearance": 0.2,
                                                   "min_hole_to_hole": 0.25, "min_via_annular_width": 0.1, "min_silk_clearance": 0.0,
                                                   "min_text_height": 0.5},
                                         "track_widths": [0.0, rules["track"], 0.3, 0.4],
                                         "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": rules["via_d"], "drill": rules["via_drill"]}]}},
           "net_settings": {"classes": ncs, "meta": {"version": 3}, "net_colors": None, "netclass_assignments": None,
                            "netclass_patterns": pats},
           "sheets": [], "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []}}
    json.dump(pro, open(os.path.join(here, name + ".kicad_pro"), "w"), indent=2)
    rows = "".join(f'  (lib (name "{n}")(type "KiCad")(uri "{u}")(options "")(descr ""))\n' for n, u in libs)
    open(os.path.join(here, "fp-lib-table"), "w").write(f"(fp_lib_table\n{rows})\n")


def _fresh(*args):
    """Run one of this file's commands in a new process. A board saved earlier in this process leaves its project (with KiCad's
    default net class: clearance 0.2, via 0.6) open in pcbnew's settings manager, and later loads reuse it instead of the
    .kicad_pro on disk; a new process reads the file."""
    import sys
    subprocess.run([sys.executable, os.path.abspath(__file__)] + [str(a) for a in args], check=True, capture_output=True)


def drc(pcb_path, report=None):
    """Run DRC (KiCad 7 python, in a new process). Returns (violations, unconnected, text)."""
    rep = report or pcb_path.replace(".kicad_pcb", "_drc.rpt")
    _fresh("drc", pcb_path, rep)
    txt = open(rep).read()
    v = re.search(r"\*\* Found (\d+) DRC violations", txt); u = re.search(r"\*\* Found (\d+) unconnected pads", txt)
    return (int(v.group(1)) if v else -1), (int(u.group(1)) if u else -1), txt


def _sexpr(txt):
    toks = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', txt)
    stack = [[]]
    for t in toks:
        if t == "(":
            stack.append([])
        elif t == ")":
            x = stack.pop(); stack[-1].append(x)
        else:
            stack[-1].append(t[1:-1] if t.startswith('"') else t)
    return stack[0]


def _find(node, key):
    for c in node:
        if isinstance(c, list) and c and c[0] == key:
            yield c


def import_ses(board, ses_path):
    """KiCad 7's ImportSpecctraSES only works inside the editor (it needs the editor's board): read the session's routes here."""
    root = _sexpr(open(ses_path).read())[0]
    routes = next(_find(root, "routes"))
    res = float(next(_find(routes, "resolution"))[2])           # units per um
    k = 1.0 / res / 1000.0                                        # session units -> mm
    layers = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}
    n_seg = n_via = 0
    for net in _find(next(_find(routes, "network_out")), "net"):
        ni = board.FindNet(net[1])
        for w in _find(net, "wire"):
            for path in _find(w, "path"):
                lay, wid = path[1], float(path[2]) * k
                pts = [(float(path[i]) * k, -float(path[i + 1]) * k) for i in range(3, len(path) - 1, 2)]
                for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                    if abs(x0 - x1) < 1e-6 and abs(y0 - y1) < 1e-6:
                        continue
                    t = pcbnew.PCB_TRACK(board); t.SetStart(V(x0, y0)); t.SetEnd(V(x1, y1)); t.SetWidth(mm(wid))
                    t.SetLayer(layers[lay]); t.SetNet(ni); board.Add(t); n_seg += 1
        for v in _find(net, "via"):
            m = re.search(r"_(\d+):(\d+)_um", v[1])
            d, dr = (float(m.group(1)) / 1000.0, float(m.group(2)) / 1000.0) if m else (0.5, 0.25)
            via = pcbnew.PCB_VIA(board); via.SetPosition(V(float(v[2]) * k, -float(v[3]) * k)); via.SetWidth(mm(d)); via.SetDrill(mm(dr))
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); via.SetNet(ni); board.Add(via); n_via += 1
    return n_seg, n_via


def route(pcb_path, jar, passes=60, attempts=4):
    dsn = pcb_path.replace(".kicad_pcb", ".dsn"); ses = pcb_path.replace(".kicad_pcb", ".ses")
    _fresh("dsn", pcb_path, dsn)
    unrouted = open(pcb_path).read(); best = None
    for attempt in range(attempts):
        subprocess.run(["java", "-Djava.awt.headless=true", "-jar", jar, "-de", dsn, "-do", ses, "-mp", str(passes),
                        "--router.max_passes=" + str(passes), "-dct", "0", "--gui.enabled=false"], check=True, timeout=900,
                       capture_output=True)
        open(pcb_path, "w").write(unrouted); b = pcbnew.LoadBoard(pcb_path)
        print("imported", import_ses(b, ses))
        pcbnew.SaveBoard(pcb_path, b)
        nv, nu, _ = drc(pcb_path)
        print("route attempt", attempt + 1, "violations", nv, "unconnected", nu)
        if best is None or (nu, nv) < best[0]:
            best = ((nu, nv), open(pcb_path).read())
        if nu == 0 and nv == 0:
            break
    open(pcb_path, "w").write(best[1])
    for p in (dsn, ses):
        if os.path.exists(p):
            os.remove(p)
    return best[0]


if __name__ == "__main__":   # commands run by _fresh()
    import sys
    cmd, a = sys.argv[1], sys.argv[2:]
    b = pcbnew.LoadBoard(a[0])
    if cmd == "drc":
        pcbnew.WriteDRCReport(b, a[1], pcbnew.EDA_UNITS_MILLIMETRES, True)
    elif cmd == "dsn":
        assert pcbnew.ExportSpecctraDSN(b, a[1]), "DSN export failed"
