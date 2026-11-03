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


def placed():
    """{'joystick: <name>': solid} in the knob panel frame, plus the joystick D."""
    from build123d import Pos
    js = _jsdir()
    if js not in sys.path:
        sys.path.insert(0, js)
    from jsparam import params, parts
    JD = params.derive(params.P)
    P = parts.build(JD)
    out = {PREFIX + n: Pos(0, JD["place_y"], 0) * s for n, s in P.items() if not n.startswith(PROXIES)}
    return out, JD


def src_modules():
    """Modules whose source decides the joystick rows (for the rows cache key in build.py)."""
    import importlib
    js = _jsdir()
    if js not in sys.path:
        sys.path.insert(0, js)
    return [importlib.import_module(m) for m in ("jsparam.params", "jsparam.parts", "jsparam.checks")]


def cross(D, pp, jp, JD):
    """[Ed 3 Nov] layout v4: cross-checks between the knob model (electronics vertical boards, MCU, encoder riser, case) and the joystick
    (top board, sockets, case cradle, bead, hold-down springs). v0.24 [Ed 13:31-14:08]: pins into sockets, the boards are the posts,
    a form-in-place bead takes the stack, the top-edge step. pp: knob parts in the panel frame; jp: placed joystick parts."""
    import math
    from ..common.checks import Rows
    r = Rows("assembly"); row = r.row
    if JD.get("base") != "case" or not D.get("vb"):
        return r
    from jsparam.parts import CC_NAME, gk_name, db_name
    V, Q, H = D["vb"], D["vb_pin"], D["vb_hdr"]
    S, B = JD["tb_sock"], JD["bead"]
    py = JD["place_y"]
    # ---- values that must match across the two models
    dz = abs(JD["z_db0"] - V["top_board_z"])
    row("top board height: joystick tb_z0 = electronics vb.top_board_z", dz, 0.01,
        f"joystick top board underside z {JD['z_db0']:.2f}; the vertical boards' end tabs reach z {V['top_board_z']:.2f}", higher_ok=False)
    dm = max(abs(JD["vb_pin_x"] - D["vb_top_x"]), abs(JD["vb_plane_x"] - V["x"]), *(abs(a - b) for a, b in zip(JD["vb_y_panel"], V["y"])),
             *(abs(a + py - b) for a, b in zip(JD["sock_pin_y"], D["vb_top_y"])), abs(S["n"] - Q["n"]), abs(S["pitch"] - Q["pitch"]),
             abs(S["h"] - Q["sock_h"]), *(abs(a - b) for a, b in zip(S["ins"], Q["sock_ins"])),
             abs(JD["sock_y"][0] + py - D["vb_sock_y"][0]), abs(JD["sock_y"][1] + py - D["vb_sock_y"][1]))
    row("pins and sockets: rows, positions, height and insertion range, electronics = joystick", dm, 0.01,
        f"{Q['n']} × 2 at {Q['pitch']:g}, rows x ±{D['vb_top_x']:.2f}, y {D['vb_top_y'][0]:.2f}..{D['vb_top_y'][-1]:.2f}; socket {S['h']:g} tall, "
        f"insertion {S['ins'][0]:g}-{S['ins'][1]:g}", higher_ok=False)
    dh = max(abs(D["joy_hole"][0] - 2 * JD["hole_hw"]), abs(D["joy_hole"][1] - 2 * JD["hole_hh"]), abs(D["place_y"] - py))
    row("faceplate cutout and place_y: case = joystick", dh, 0.01,
        f"cutout {D['joy_hole'][0]:.2f} × {D['joy_hole'][1]:.2f} at y {D['place_y']:.2f}", higher_ok=False)
    st = JD["step"]
    ds = max(abs(D["joy_step"]["w"] - st["w"]), abs(D["joy_step"]["d"] - st["d"]), abs(D["joy_step_y0"] - (JD["st_y0"] + py)))
    row("top-edge step: case rebate = joystick step (width, depth, start)", ds, 0.01,
        f"rebate {st['w']:g} past the cutout wall, {st['d']:g} into the faceplate back, from panel y {JD['st_y0'] + py:.2f} round the top",
        higher_ok=False)
    # ---- pins into sockets: engagement (the boards are the posts, so the top board always sits on the tabs: the stack does not move it)
    T = D["vb_pin_tol"]; er = math.sqrt(sum(v * v for v in T.values())); ew = sum(T.values())
    eng = D["vb_tip_z"] - JD["z_sock0"]
    lo, hi = S["ins"]
    m_rss = min(eng - er - lo, hi - (eng + er)); m_wc = min(eng - ew - lo, hi - (eng + ew))
    row("pins in the sockets: engagement margin at both stack ends (RSS)", m_rss, D["vb_pin_margin"],
        f"nominal {eng:.2f} into the {S['h']:g} socket (insertion {lo:g} [S Samtec FLE class]–{hi:g} [A]), ±{er:.2f} RSS of " +
        ", ".join(f"{k} {v:g}" for k, v in T.items()) + f" (worst ±{ew:.2f}: margin {m_wc:.2f}). The same at both ends of the ±"
        f"{math.sqrt(sum(v * v for v in D['vb_stack_tol'].values())):.2f} main-board stack: the tabs bear on the top board, so the stack goes "
        "into the bead, not into the pins. v0.23's contact travel (0.12–0.88 of 1.0) and force rows are gone")
    L = D["vb_lat_tol"]; lr = math.sqrt(sum(v * v for v in L.values()))
    C = D["vb_capture"]; cap = C["lead_in"] + C["cradle_float"]
    row("pins line up with the sockets as the main board goes in (RSS vs capture, y)", cap - lr, 0.05,
        f"misalignment ±{lr:.2f} RSS of " + ", ".join(f"{k} {v:g}" for k, v in L.items()) + f"; capture {cap:.2f} = socket lead-in "
        f"{C['lead_in']:g} [A] + the cradle sliding in its {JD['cc']['lip_c']:g} lip clearance until the case closes. In x the 1.0 boards "
        f"also flex (about {_vb_flex(D):.1f} N per 0.3 mm). TIGHT in y (the boards are stiff in their own plane): a lead-in chamfer or "
        "a locating pin between the cradle and the main board would help [C]")
    # ---- the bead takes the stack (the boards are the posts)
    VT = dict(D["vb_stack_tol"]); need = math.sqrt(sum(v * v for v in VT.values()) + B["disp"] ** 2); wc = sum(VT.values()) + B["disp"]
    band = JD["bead_band"]
    h_need = 2 * need / (B["c_hi"] - B["c_lo"])
    row("form-in-place bead takes the post stack (RSS) inside its 15–45 % band", band - need, 0.0,
        f"[Ed 14:08] stack ±{need:.2f} RSS (" + ", ".join(f"{k} {v:g}" for k, v in VT.items()) + f", the bead's own ±{B['disp']:g} height "
        f"[S Henkel]; worst ±{wc:.2f}) vs the bead's ±{band:.2f} ({B['w0']:g} × {B['h0']:g} on the {JD['gk_land_x']:.2f} long-side land). "
        f"FUNDAMENTAL: to take ±{need:.2f} in 15–45 % a bead needs about {h_need:.1f} tall (≈{h_need / 0.9:.1f} wide at aspect 0.9 [S]); "
        f"the land fits {JD['gk_land_x']:.2f}. Short end: the bead lifts off (no seal); long end: it bottoms and the posts load up. "
        "Danny's call [C]")
    nb = _bead_len(JD); f_nom = B["f_mm"] * nb; f_hi = f_nom * ((B["c_hi"] / B["c_nom"]) ** 1.5)
    fhd = len(JD["springs"]) * JD["spr_f"]; fpr = JD["push_hi"]
    post = (f_hi + fhd + fpr) / 2
    E, I, Lc = 18000.0, (V["y"][1] - V["y"][0]) * V["t"] ** 3 / 12.0, D["vb_z1"]
    p_pin = math.pi ** 2 * E * I / (0.7 * Lc) ** 2; p_free = math.pi ** 2 * E * I / (2 * Lc) ** 2
    row("posts: Euler load / post load, each board (bottom header clamped, top held by the pins)", p_pin / post, D["vb_buckle_margin"],
        f"post load {post:.1f} N a board = (bead {f_hi:.0f} N at {100 * B['c_hi']:.0f} % [A {B['f_mm']:g} N/mm at 30 %, {nb:.0f} mm of bead] "
        f"+ hold-downs {fhd:.1f} + worst press {fpr:.2f}) / 2; nominal bead {f_nom:.0f} N. Euler {p_pin:.0f} N fixed-pinned, {p_free:.0f} N "
        f"fixed-free ({p_free / post:.1f}×) [A FR4 E 18 GPa, {V['y'][1] - V['y'][0]:.1f} × {V['t']:g}, {Lc:g} tall]")
    row("bead force vs the hold-downs and a press (info: neither unloads the bead)", f_nom, 0.0,
        f"bead {f_nom:.0f} N nominal pushes the cradle onto the top board and the tabs. The hold-downs ({fhd:.1f} N) close a loop main board → "
        f"tabs → cradle → balls → carrier → springs → main board, and a press ({fpr:.2f} N) runs stem → top board → tabs → main board → back "
        "cover: neither goes through the bead (only the boards' and the main board's elastic give, microns)")
    # ---- header legs vs the top corner PCB notches (case corners), and vs the encoder riser behind R
    rp = H["pad"] / 2; best, who = 9e9, ""
    for cx, cy in D["corners"]:
        for sx in (-1, 1):
            for x, y, _ in D["vb_legs"][sx]:
                d = math.hypot(x - cx, y - cy) - D["notch_r"] - rp
                if d < best: best, who = d, f"leg ({x:.2f}, {y:.2f}) to the notch at ({cx:g}, {cy:.2f})"
    row("vertical-board header pads to the top corner PCB notches", best, 1.0,
        f"notch r {D['notch_r']:.2f}; {who}. Rows stop at y {H['y_max'][0]:g} / {H['y_max'][1]:g} (vb_hdr.y_max)")
    vbp = {n: q for n, q in pp.items() if n.startswith("vertical board")}
    enc = [q for n, q in pp.items() if n.startswith(("encoder standoff", "encoder header", "encoder daughterboard"))]
    hdr = [q for n, q in vbp.items() if " header " in n]
    if enc and hdr:
        d = min(a.distance_to(b) for a in hdr for b in enc)
        nt = {sx: sum(k == "tht" for _, _, k in D["vb_legs"][sx]) for sx in (-1, 1)}
        row("vertical-board header legs vs the encoder riser and its header", d, 0.5,
            f"[Ed 13:31] R: SMT legs over y {H['smt'][0][1]:g}-{H['smt'][0][2]:g} (no tails over the riser), {nt[1]} THT legs above; "
            f"L {nt[-1]} THT. The riser's own header is hybrid (THT at its inner end), no standoffs [Ed 13:39]")
    # the riser's THT pins come through the main-board front: clear of R's foot, the windows and the H7B0
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
    # ---- vertical boards vs the case, the joystick springs and the case cradle
    case = {n: q for n, q in pp.items() if n == "case" or n.startswith("glow coat")}
    d, who = min(((a.distance_to(b), f"{na} / {nb}") for na, a in vbp.items() for nb, b in case.items()), default=(9.9, ""))
    row("vertical boards and their parts vs the case (corner posts, ledges, glow coat)", d, 1.0,
        f"nearest: {who}. The male header body (z {D['vb_ze'] - Q['body_z']:.1f}-{D['vb_ze']:.1f}) sits {D['vb_ze'] - Q['body_z'] - D['z_post_top']:.1f} "
        "over the top corner posts")
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
    cc = jp[PREFIX + CC_NAME]
    d, who = min(((cc.distance_to(q), n) for n, q in vbp.items()), default=(9.9, ""))
    row("vertical boards and their pins vs the joystick case cradle", d, 0.5, f"nearest: {who}")
    tb = jp[PREFIX + db_name(JD)]
    bd = [q for n, q in vbp.items() if "FR4" in n]
    dt = max(b_.distance_to(tb) for b_ in bd)
    row("vertical boards' end tabs bear on the top board's underside (the posts)", dt, 0.02,
        f"tabs y {D['vb_tabs'][0][0]:.2f}..{D['vb_tabs'][0][1]:.2f} and {D['vb_tabs'][1][0]:.2f}..{D['vb_tabs'][1][1]:.2f} at x ±{V['x']:g} "
        "(bare board under them on the top board [A])", higher_ok=False)
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
        f"courtyard {M['court']:g} □ at ({mx:g}, {my:g}); springs at (±{JD['spr_x']:.2f}, {py - JD['spr_y']:.2f} / {py + JD['spr_y']:.2f})")
    # ---- the case cradle and its bead against the real case
    cs = pp.get("case")
    if cs is not None:
        d = cc.distance_to(cs)
        row("joystick case cradle vs the real case (lip in the cutout, dam in the rebate, flange under the faceplate)", d, JD["cc"]["lip_c"] - 0.01,
            f"lip {JD['cc']['lip_c']:.2f} from the cutout walls, dam {st['c']:g} from the rebate walls, flange {JD['z_fp0'] - JD['z_fl1']:.2f} "
            "under the faceplate back")
        gk = jp[PREFIX + gk_name(JD)]
        row("cradle bead on the real faceplate back and in the real rebate", gk.distance_to(cs), 0.02,
            f"bead top z {JD['z_fp0'] - 0.01:.2f} under the faceplate back z {D['z_fp0']:.2f}; in the step under the rebate ceiling z "
            f"{JD['z_reb1']:.2f}", higher_ok=False)
        gl = [q for n, q in pp.items() if n.startswith("glow coat")]
        if gl:
            d = min(min(cc.distance_to(g), gk.distance_to(g)) for g in gl)
            row("case cradle flange and bead clear of the side-wall glow coat", d, JD["cc"]["glow_air"] - 0.01,
                f"flange edge x ±{JD['fl_x1']:.2f}; the coat is modelled {D['glow_gap']:g} off the wall at x ±{D['x_in1']:.2f}")
    return r


def _vb_flex(D):
    """N to push one vertical board's top edge 0.3 sideways (cantilever from the header, FR4 E 18 GPa [A])."""
    V = D["vb"]; I = (V["y"][1] - V["y"][0]) * V["t"] ** 3 / 12.0
    return 3 * 18000.0 * I / D["vb_z1"] ** 3 * 0.3


def _bead_len(JD):
    """mm of bead: the ring next to the cutout (band centre), all four sides (flange U + the step), plus the two risers."""
    import math
    a = JD["gk_land_x"] / 2
    w, h, r = JD["hole_hw"] + a, JD["hole_hh"] + a, JD.get("corner_r", 0.0) + a
    return 2 * (2 * w + 2 * h) - (8 - 2 * math.pi) * r + 2 * (JD["z_reb1"] - JD["z_fl1"])


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
