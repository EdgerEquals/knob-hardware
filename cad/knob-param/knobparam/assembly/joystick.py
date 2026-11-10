"""Joystick stack (cad/joystick-param, read as data) placed in the knob panel frame, and its clashes with the knob stack.

The joystick model has its own frame: joystick axis at (0, 0), +y toward the panel top, z 0 = main PCB front (same z as here).
It sits at (0, place_y) in the knob panel frame. Its two proxies (main PCB patch, faceplate) are dropped: the knob model has the
real ones. Run from cad/knob-param:  python -m knobparam.assembly.joystick  (prints the clash list)."""
import os, sys, time

PREFIX = "joystick: "
PROXIES = ("main PCB (proxy", "faceplate (case proxy")


def _jsdir():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(here))), "joystick-param")


_JD = {}


def _jd():
    """The joystick D (derived once per process)."""
    js = _jsdir()
    if js not in sys.path:
        sys.path.insert(0, js)
    if "D" not in _JD:
        from jsparam import params
        _JD["D"] = params.derive(params.P)
    return _JD["D"]


def placed():
    """{'joystick: <name>': solid} in the knob panel frame, plus the joystick D. v0.25 [Ed 18:35]: the cradle is printed into the case,
    so it is not a joystick part here: build_all fuses it into "case" (cradle_for_case)."""
    from build123d import Pos
    JD = _jd()
    from jsparam import parts
    P = parts.build(JD)
    skip = PROXIES + ((parts.cc_name(JD),) if JD.get("cradle_in_case") else ())
    out = {PREFIX + n: Pos(0, JD["place_y"], 0) * s for n, s in P.items() if not n.startswith(skip)}
    return out, JD


def cradle_for_case(ov=0.02):
    """v0.25 [Ed 18:35]: the joystick cradle as printed in the case (knob panel frame), with its lip and flange riser running ov into the
    faceplate so it fuses, and a cache key (joystick source + its derived values). (None, "") when the cradle is a separate part."""
    import hashlib, json
    from build123d import Pos
    JD = _jd()
    if JD.get("base") != "case" or not JD.get("cradle_in_case"):
        return None, ""
    from jsparam import parts
    src = "".join(open(m.__file__, encoding="utf-8").read() for m in src_modules()[:2])
    ck = hashlib.sha1((src + json.dumps(JD, sort_keys=True, default=repr) + f"{ov}").encode()).hexdigest()[:16]
    return Pos(0, JD["place_y"], 0) * parts.case_cradle(JD, ov=ov), ck


def _zsweep(shape, dz_lo, dz_hi):
    """Prisms swept by each solid of `shape` moving along z by dz_lo..dz_hi (each solid taken as a prism in z: its plan at mid height)."""
    from build123d import Box, Pos, extrude
    out = []
    for s in shape.solids():
        bb = s.bounding_box(); c = bb.center(); zm = (bb.min.Z + bb.max.Z) / 2
        sec = s & (Pos(c.X, c.Y, zm) * Box(bb.size.X + 2, bb.size.Y + 2, 1e-3))
        for f in sec.faces():
            if f.normal_at().Z < -0.99:
                f0 = Pos(0, 0, bb.min.Z + dz_lo - f.center().Z) * f
                out.append(extrude(f0, amount=(bb.max.Z - bb.min.Z) + (dz_hi - dz_lo), dir=(0, 0, 1)))
    return out


def _path(movers, fixed, dz_lo, dz_hi):
    """Least distance from the swept movers to the fixed parts, and which pair."""
    best, who = 9e9, ""
    for mn, m in movers.items():
        for pr in _zsweep(m, dz_lo, dz_hi):
            pb = pr.bounding_box()
            for fn, f in fixed.items():
                fb = f.bounding_box()
                if (pb.min.X > fb.max.X + 2 or fb.min.X > pb.max.X + 2 or pb.min.Y > fb.max.Y + 2 or fb.min.Y > pb.max.Y + 2
                        or pb.min.Z > fb.max.Z + 2 or fb.min.Z > pb.max.Z + 2):
                    continue
                d = pr.distance_to(f)
                if d < best:
                    best, who = d, f"{mn[len(PREFIX):] if mn.startswith(PREFIX) else mn} / {fn}"
    return best, who


def src_modules():
    """Modules whose source decides the joystick rows (for the rows cache key in build.py)."""
    import importlib
    js = _jsdir()
    if js not in sys.path:
        sys.path.insert(0, js)
    return [importlib.import_module(m) for m in ("jsparam.params", "jsparam.parts", "jsparam.checks")]


def cross(D, pp, jp, JD):
    """[Ed 3 Nov] layout v4: cross-checks between the knob model (electronics vertical boards, MCU, encoder riser, case) and the joystick
    (top board, sockets, hold-down springs). v0.24 [Ed 13:31-14:08]: pins into sockets. v0.25 [Ed 18:35 / 19:12]: the cradle is printed
    into the case (fused into "case" by build_all), the pins take the stack (the end tabs clear the top board), 4.5 sockets, the top board
    goes in from the back on its own (corner notches), the pin rows 0.3 inboard (and 2.5 toward the knob [A]).
    pp: knob parts in the panel frame; jp: placed joystick parts (no cradle: it is in the case)."""
    import math
    from ..common.checks import Rows
    r = Rows("assembly"); row = r.row
    if JD.get("base") != "case" or not D.get("vb"):
        return r
    from jsparam.parts import db_name
    V, Q, H = D["vb"], D["vb_pin"], D["vb_hdr"]
    S = JD["tb_sock"]
    py = JD["place_y"]
    rss = lambda T: math.sqrt(sum(v * v for v in T.values()))

    def info(name, val, tgt, note):   # a row that reports, it does not gate
        r.append(dict(name=name, value=round(float(val), 3), target=tgt, ok=True, note=note, owner=r.owner, slack=None))
    # ---- values that must match across the two models
    dz = abs(JD["z_db0"] - V["top_board_z"])
    row("top board height: joystick tb_z0 = electronics vb.top_board_z", dz, 0.01,
        f"joystick top board underside z {JD['z_db0']:.2f}; electronics vb.top_board_z {V['top_board_z']:.2f}", higher_ok=False)
    dm = max(abs(JD["vb_pin_x"] - D["vb_top_x"]), abs(JD["vb_plane_x"] - V["x"]), *(abs(a - b) for a, b in zip(JD["vb_y_panel"], V["y"])),
             *(abs(a + py - b) for a, b in zip(JD["sock_pin_y"], D["vb_top_y"])), abs(S["n"] - Q["n"]), abs(S["pitch"] - Q["pitch"]),
             abs(S["h"] - Q["sock_h"]), *(abs(a - b) for a, b in zip(S["ins"], Q["sock_ins"])),
             abs(JD["sock_y"][0] + py - D["vb_sock_y"][0]), abs(JD["sock_y"][1] + py - D["vb_sock_y"][1]))
    row("pins and sockets: rows, positions, height and insertion range, electronics = joystick", dm, 0.01,
        f"{Q['n']} × 2 at {Q['pitch']:g}, rows x ±{D['vb_top_x']:.2f} [Ed 19:12 (4): 0.3 inboard], y {D['vb_top_y'][0]:.2f}..{D['vb_top_y'][-1]:.2f} "
        f"({Q.get('y_shift', 0):+g} toward the knob [A]); socket {S['h']:g} tall [Ed 19:12 (7)], insertion {S['ins'][0]:g}-{S['ins'][1]:g}",
        higher_ok=False)
    dh = max(abs(D["joy_hole"][0] - 2 * JD["hole_hw"]), abs(D["joy_hole"][1] - 2 * JD["hole_hh"]), abs(D["place_y"] - py))
    row("faceplate cutout and place_y: case = joystick", dh, 0.01,
        f"cutout {D['joy_hole'][0]:.2f} × {D['joy_hole'][1]:.2f} at y {D['place_y']:.2f}", higher_ok=False)
    # ---- the pins take the stack (decision (c), kept under [Ed 18:35]): main-board ledge -> printed shoulders is ONE SLA dimension now
    ST, PT = D["vb_stack_tol"], D["vb_pin_tol"]
    TE = dict(vb_seat=ST["vb_seat"], header_z=PT["header_z"], case=ST["case"], top_board=ST["top_board"], socket_h=PT["socket_h"])
    er, ew = rss(TE), sum(TE.values())
    eng = D["vb_tip_z"] - JD["z_sock0"]
    lo, hi = S["ins"]
    m_rss = min(eng - er - lo, hi - (eng + er)); m_wc = min(eng - ew - lo, hi - (eng + ew))
    row("pins in the sockets: engagement margin at both stack ends (RSS); the pins take the stack", m_rss, D["vb_pin_margin"],
        f"nominal {eng:.2f} into the {S['h']:g} socket (insertion {lo:g} [S Samtec FLE class]–{hi:g} [A]): band {eng - er:.2f}–{eng + er:.2f} "
        f"RSS (±{er:.2f} of " + ", ".join(f"{k} {v:g}" for k, v in TE.items()) + f"), {eng - ew:.2f}–{eng + ew:.2f} worst (margin {m_wc:.2f}). "
        "v0.24's faceplate + cradle terms are one 'case' term (the shoulders are printed in the case); no bead, no posts")
    TT = dict(vb_seat=ST["vb_seat"], vb_height=ST["vb_height"], case=ST["case"], top_board=ST["top_board"])
    g_tab = V["top_board_z"] - D["vb_z1"]
    row("vertical boards' end tabs clear of the top board at the worst-case stack (no longer posts)", g_tab - sum(TT.values()),
        D["vb_tab_margin"],
        f"tab tops z {D['vb_z1']:.2f}, {g_tab:.2f} under the top board; worst stack ±{sum(TT.values()):.2f} (RSS ±{rss(TT):.2f}: " +
        ", ".join(f"{k} {v:g}" for k, v in TT.items()) + "). Tabs: " + ", ".join(f"y {a:.2f}..{b:.2f}" for a, b in D["vb_tabs"]))
    g_h = JD["z_sock0"] - D["vb_ze"]
    row("male header body and board edge clear of the socket's face at the worst-case stack", g_h - ew, D["vb_tab_margin"],
        f"header body top / board edge z {D['vb_ze']:.2f}, {g_h:.2f} under the socket entry z {JD['z_sock0']:.2f}; worst stack ±{ew:.2f} "
        f"(the pins bottom at {hi - (eng + ew):.2f} past it)")
    L = D["vb_lat_tol"]; lr = rss(L)
    C = D["vb_capture"]; cap = C["lead_in"] + C["board_float"]
    row("pins line up with the sockets as the board stack goes in (RSS vs capture, y)", cap - lr, 0.05,
        f"misalignment ±{lr:.2f} RSS of " + ", ".join(f"{k} {v:g}" for k, v in L.items()) + f"; capture {cap:.2f} = socket lead-in "
        f"{C['lead_in']:g} [A] + the top board floating in its printed nest ({JD['cc']['nest_c']:g} a side) while its glue is wet [A, needs "
        f"Danny's OK]. With the glue already set the capture is the lead-in alone: {C['lead_in'] - rss(dict(L, board=0.05)):.2f}. In x the 1.0 "
        f"boards also flex (about {_vb_flex(D):.1f} N per 0.3 mm)")
    # ---- header legs vs the top corner PCB notches (case corners), and vs the encoder riser behind R
    rp = H["pad"] / 2; best, who = 9e9, ""
    for cx, cy in D["corners"]:
        for sx in (-1, 1):
            for x, y, _ in D["vb_legs"][sx]:
                d = math.hypot(x - cx, y - cy) - D["notch_r"] - rp
                if d < best: best, who = d, f"leg ({x:.2f}, {y:.2f}) to the notch at ({cx:g}, {cy:.2f})"
    row("vertical-board header pads to the top corner PCB notches", best, 1.0,
        f"notch r {D['notch_r']:.2f}; {who}. Rows stop at y {H['y_max'][0]:g} / {H['y_max'][1]:g} (vb_hdr.y_max) [Ed 19:12 (6)]")
    vbp = {n: q for n, q in pp.items() if n.startswith("vertical board")}
    enc = [q for n, q in pp.items() if n.startswith(("encoder standoff", "encoder header", "encoder daughterboard"))]
    hdr = [q for n, q in vbp.items() if " header " in n]
    if enc and hdr:
        d = min(a.distance_to(b) for a in hdr for b in enc)
        nt = {sx: sum(k == "tht" for _, _, k in D["vb_legs"][sx]) for sx in (-1, 1)}
        row("vertical-board header legs vs the encoder riser and its header", d, 0.5,
            f"[Ed 13:31] R: SMT legs over y {H['smt'][0][1]:g}-{H['smt'][0][2]:g} (no tails over the riser), {nt[1]} THT legs above; "
            f"L {nt[-1]} THT. The riser's own header is hybrid (THT at its inner end), no standoffs [Ed 13:39]")
    from knobparam.electronics.parts import pcb as _pcb
    a = math.radians(D.get("mech_rot", 0.0)); c_, s_ = math.cos(a), math.sin(a)
    tp = [(c_ * x - s_ * y, s_ * x + c_ * y, d) for x, y, d in D.get("enc_tht_xy", [])]
    if tp:
        best, who = 9e9, ""
        for X, Y, d in tp:
            rr = D["vb_hdr"]["pad"] / 2 + 0.15
            for bx0, bx1, by0, by1 in _pcb.vb_footprint(D):
                dd = math.hypot(max(bx0 - X, 0, X - bx1), max(by0 - Y, 0, Y - by1)) - rr
                if dd < best: best, who = dd, f"pin ({X:.2f}, {Y:.2f}) to the vertical boards' foot"
            (mx, my), cm = D["mcu"]["xy"], D["mcu"]["court"] / 2
            dd = math.hypot(max(abs(X - mx) - cm, 0), max(abs(Y - my) - cm, 0)) - rr
            if dd < best: best, who = dd, f"pin ({X:.2f}, {Y:.2f}) to the H7B0 courtyard"
            for k, poly in D["pcb_windows"].items():
                from knobparam.electronics.checks import _seg_d
                dd = min(_seg_d(X, Y, p, q) for p, q in zip(poly, poly[1:] + poly[:1])) - rr
                if dd < best: best, who = dd, f"pin ({X:.2f}, {Y:.2f}) to window {k}"
        row("encoder riser THT pins on the main-board front: clear of R's foot, the windows and the H7B0", best, 0.5,
            f"[Ed 13:35] pins {list(D['enc_header_tht'])} through (pad + 0.15 ring); the rest SMT on the back under R's foot; nearest: {who}")
    # ---- vertical boards vs the case (the printed cradle is part of it now), the joystick springs and the rear anchor
    case = {n: q for n, q in pp.items() if n == "case" or n.startswith("glow coat")}
    d, who = min(((a.distance_to(b), f"{na} / {nb}") for na, a in vbp.items() for nb, b in case.items()), default=(9.9, ""))
    row("vertical boards and their parts vs the case (corner posts, ledges, glow coat, the printed cradle)", d, 1.0,
        f"nearest: {who}. The male header body (z {D['vb_ze'] - Q['body_z']:.2f}-{D['vb_ze']:.2f}) is inboard of the top corner posts' plan")
    boards = [q for n, q in vbp.items() if "FR4" in n]
    hd = [q for n, q in jp.items() if "hold-down spring" in n]
    d = min(a.distance_to(b) for a in boards for b in hd)
    row("vertical boards (inner faces) vs the joystick hold-down springs", d, 1.0,
        f"inner faces x ±{D['vb_face_in']:.2f}; springs (wire Ø{JD['spr_d']:g}) at x ±{JD['spr_x']:.2f}: inner-face parts there stay under "
        f"{max(d - 1.0, 0):.2f} mm to keep 1.0 air [C]")
    ra = {n: q for n, q in jp.items() if "rear spring anchor" in n or "cross pin" in n}
    d, who = min(((a.distance_to(b), f"{na} / {nb[len(PREFIX):]}") for na, a in vbp.items() for nb, b in ra.items()), default=(9.9, ""))
    row("vertical boards (and header legs behind the main board) vs the joystick rear anchor and cross pins", d, 1.0,
        f"nearest: {who}; anchor x {JD['ra_x0']:.2f}..{JD['ra_x1']:.2f} on the board back, pin heads out to x {JD['ra_x1'] + 0.25 + JD['pin_head_t']:.2f}")
    tb = jp[PREFIX + db_name(JD)]
    sk = [q for n, q in jp.items() if "top-board socket" in n]
    pins = [q for n, q in vbp.items() if "male pins" in n]
    if sk and pins:
        dp = min(a.distance_to(b) for a in pins for b in sk)
        row("male pins inside the socket holes (no touch in the model)", dp, 0.02,
            f"pins {Q['pin']:g} square in Ø0.7 model holes; tips z {D['vb_tip_z']:.2f}")
    # ---- the H7B0 under the joystick
    M = D["mcu"]; (mx, my), c = M["xy"], M["court"] / 2
    best = 9e9
    for x, y in JD["springs"]:
        X, Y = x, y + py
        dx_ = max(abs(X - mx) - c, 0.0); dy_ = max(abs(Y - my) - c, 0.0)
        best = min(best, math.hypot(dx_, dy_) - JD["spr_d"] / 2)
    row("H7B0 courtyard to the joystick hold-down springs (plan)", best, 1.0,
        f"courtyard {M['court']:g} □ at ({mx:g}, {my:g}); springs at (±{JD['spr_x']:.2f}, " + " / ".join(f"{py + y:.2f}" for y in sorted({y for _x, y in JD["springs"]})) + ")")
    # ---- [Ed 18:35] the cradle printed into the case
    cs = pp.get("case")
    if cs is not None:
        cr, _ = cradle_for_case()
        ns = len(cs.solids())
        probe = (JD["nest_hw"] + JD["cc"]["wall"] / 2, py + (JD["nest_y0"] + JD["nest_y1"]) / 2, (JD["z_nest0"] + JD["z_fl0"]) / 2)
        inside = cs.is_inside(probe)
        row("joystick cradle printed into the case: one solid with the hangers in it", ns + (0 if inside else 9), 1,
            f"[Ed 18:35] case = shell + the joystick cradle (lip ring, flange + riser, hangers, end walls, ball seats on their brackets, "
            f"top-board shoulders), {cr.volume / 1000:.2f} cm³ fused in with a 0.02 overlap; {ns} solid(s); hanger probe "
            f"{'inside' if inside else 'NOT inside'} the case. BOM and per-part STEP: one printed part, 'case'", higher_ok=False)
        gl = [q for n, q in pp.items() if n.startswith("glow coat")]
        if gl:
            d = min(cr.distance_to(g) for g in gl)
            row("printed cradle flange clear of the side-wall glow coat", d, JD["cc"]["glow_air"] - 0.01,
                f"flange edge x ±{JD['fl_x1']:.2f}; the coat is modelled {D['glow_gap']:g} off the wall at x ±{D['x_in1']:.2f} (brush access)")
        # the top board goes in from the back on its own (with its sockets, SW1 and the screen socket) up to its printed nest
        fixed = {n: q for n, q in pp.items() if n == "case" or n.startswith(("glow coat", "corner insert", "jack ", "USB-C"))}
        mov = {n: q for n, q in jp.items() if n.startswith(tuple(PREFIX + k for k in ("joystick top board", "top-board socket", "SW1 ", "screen FPC socket")))}
        top = max(q.bounding_box().max.Z for q in mov.values())
        lo_ = (D["z_rim"] - 2.0) - top
        hi_ = (JD["z_nest0"] - D["path_min"]) - JD["z_db1"]
        dpath, who = _path(mov, fixed, lo_, hi_)
        nx, ny = JD.get("tb_notch_size", (0.0, 0.0))
        row("top board (with its sockets and parts) path from the back clear of the case and inserts", dpath, D["path_min"],
            f"[Ed 18:35] swept from behind the rim up to {JD['z_db1'] - JD['z_nest0'] + D['path_min']:.1f} short of home (the last bit is the "
            f"printed nest, {JD['cc']['nest_c']:g} a side); nearest: {who}. Corner notches {nx:.2f} × {ny:.2f} round the top corner posts "
            f"(v0.24: the board caught the posts' bases by ~1). TIGHT: the sockets' outer corners pass the posts' bases at about this")
        # the vertical boards' male pin headers (and the boards) go in with the board stack from the back
        movh = {n: q for n, q in vbp.items() if "male pins" in n}
        movb = {n: q for n, q in vbp.items() if "male pins" not in n}
        top = max(q.bounding_box().max.Z for q in vbp.values())
        lo_ = (D["z_rim"] - 2.0) - top
        dh_, whoh = _path(movh, fixed, lo_, 0.0)
        db_, whob = _path(movb, fixed, lo_, 0.0)
        row("vertical boards' male pin headers: path from the back clear of the case", dh_, D["path_min"],
            f"[Ed 19:12 (4)] headers 0.3 inboard (pins x ±{D['vb_top_x']:.2f}, body to ±{D['vb_face_out'] + Q['body_x']:.2f}) and the rows "
            f"{Q.get('y_shift', 0):+g} in y [A]; nearest: {whoh} (v0.24: 0.15 into the top corner posts' bases). The boards and their bottom "
            f"headers: {db_:.2f} ({whob})")
        # ---- [Ed 4 Nov 10:03] joystick item 5: the cutout starts just behind the faceplate, so the top wall, top ledge and top posts are back
        if D.get("joy_cut_to") is not None:
            from build123d import Box, Pos, Align
            A_ = (Align.MIN,) * 3
            z0c = D["z_joy_cut0"]
            col = Pos(-D["hole_hw"], D["y_in1"], z0c - 3.0) * Box(2 * D["hole_hw"], D["body_y1"] - D["y_in1"], D["z_fp1"] - z0c + 3.0, align=A_)
            zlow, who = 9e9, "-"
            for n, q in jp.items():
                try:
                    x = q & col
                    if x is not None and x.volume > 1e-6 and x.bounding_box().min.Z < zlow:
                        zlow, who = x.bounding_box().min.Z, n
                except Exception:
                    pass
            row("case top wall back under the joystick: lowest joystick part over it", zlow - z0c, D["topwall_air"],
                f"[Ed 4 Nov 10:03] the joystick cutout runs from z {z0c:.2f} ({D['joy_cut_to']:g} behind the faceplate back), not the case's "
                f"whole depth: the top wall (y {D['y_in1']:.2f}-{D['body_y1']:.2f}, x ±{D['hole_hw']:.2f}) and the top corner posts are whole "
                f"again (v0.25 first cut: open from z -0.42); the main board's top ledge comes back only at its ends (cut over "
                f"x ±{D['joy_tb_pass']:.2f} for the top board's path, its own row). Lowest part over the wall: {who} at z {zlow:.2f}. "
                f"A {D['z_fp0'] - z0c:.2f} slit stays between the wall top and the faceplate back (inside the rack, behind the faceplate overhang)")
    return r


def _vb_flex(D):
    """N to push one vertical board's top edge 0.3 sideways (cantilever from the header, FR4 E 18 GPa [A])."""
    V = D["vb"]; I = (V["y"][1] - V["y"][0]) * V["t"] ** 3 / 12.0
    return 3 * 18000.0 * I / D["vb_z1"] ** 3 * 0.3


def _bb(s):
    b = s.bounding_box()
    return (b.min.X, b.min.Y, b.min.Z, b.max.X, b.max.Y, b.max.Z)


def _ov(a, b, pad=0.0):
    return all(a[i] - pad <= b[i + 3] and b[i] - pad <= a[i + 3] for i in range(3))


def clashes(jparts, kparts, thr=1e-3):
    """Joystick part vs knob part interference volume (mm³), panel frame. Serial: only a few dozen bbox pairs."""
    jb = {n: _bb(s) for n, s in jparts.items()}
    kb = {n: _bb(s) for n, s in kparts.items()}
    out, cand = {}, 0
    for jn, js in jparts.items():
        for kn, ks in kparts.items():
            if not _ov(jb[jn], kb[kn]):
                continue
            cand += 1
            try:
                x = js & ks
                v = x.volume if x is not None else 0.0
            except Exception:
                v = -1.0
            if v > thr or v < 0:
                out[f"{jn} / {kn}"] = v
    return out, cand


def main():
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, here)
    from knobparam.common import model
    from knobparam.assembly.build import build_all, view
    t0 = time.time()
    D = model.derive(model.default_params())
    parts, stats, keys, owner = build_all(D)
    parts, keys = view(parts, keys, D, "panel")
    jp, JD = placed()
    cl, cand = clashes(jp, parts, D["tgt"]["clash_mm3"])
    print(f"joystick at (0, {JD['place_y']:.2f}); {len(jp)} parts, {cand} bbox pairs vs the knob stack ({time.time() - t0:.0f} s)")
    for k, v in sorted(cl.items(), key=lambda kv: -kv[1]):
        print(f"  CLASH {k}: {v:.3f} mm³")
    if not cl:
        print("  none")


if __name__ == "__main__":
    main()
