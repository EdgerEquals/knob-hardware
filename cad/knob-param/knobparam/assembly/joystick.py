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
    """[Ed 3 Nov] layout v4 step 1: cross-checks between the knob model (electronics vertical boards and MCU, case) and the joystick
    (top board, case cradle, gasket, hold-down springs). pp: knob parts in the panel frame; jp: placed joystick parts."""
    import math
    from build123d import Pos, Cylinder, Align
    from ..common.checks import Rows
    r = Rows("assembly"); row = r.row
    if JD.get("base") != "case" or not D.get("vb"):
        return r
    from jsparam.parts import CC_NAME, GK_NAME
    V, G, H = D["vb"], D["vb_pogo"], D["vb_hdr"]
    py = JD["place_y"]
    # ---- values that must match across the two models
    dz = abs(JD["z_db0"] - V["top_board_z"])
    row("top board height: joystick tb_z0 = electronics vb.top_board_z", dz, 0.01,
        f"joystick top board underside z {JD['z_db0']:.2f}; electronics contacts reach z {V['top_board_z']:.2f}", higher_ok=False)
    dm = max(abs(JD["vb_contact_x"] - D["vb_contact_x"]), *(abs(a - b) for a, b in zip(JD["vb_y_panel"], V["y"])))
    row("vertical boards: contact line and span, joystick mirror = electronics", dm, 0.01,
        f"contacts x ±{D['vb_contact_x']:.2f}, boards y {V['y'][0]:g}..{V['y'][1]:g} (joystick ±{JD['vb_contact_x']:.2f}, "
        f"{JD['vb_y_panel'][0]:g}..{JD['vb_y_panel'][1]:g})", higher_ok=False)
    dh = max(abs(D["joy_hole"][0] - 2 * JD["hole_hw"]), abs(D["joy_hole"][1] - 2 * JD["hole_hh"]), abs(D["place_y"] - py))
    row("faceplate cutout and place_y: case = joystick", dh, 0.01,
        f"cutout {D['joy_hole'][0]:.2f} × {D['joy_hole'][1]:.2f} at y {D['place_y']:.2f}: unchanged by the lip (the carrier narrowed instead)",
        higher_ok=False)
    # ---- spring contacts: compression band over the stack, force balance, overpress
    T = dict(D["vb_stack_tol"]); T["gasket"] = (JD["gk_range"][1] - JD["gk_range"][0]) / 2
    rss = math.sqrt(sum(v * v for v in T.values())); wc = sum(T.values())
    work = G["free"] - (V["top_board_z"] - D["vb_z1"])
    lo, hi = work - rss, work + rss
    m = D["vb_travel_margin"]
    row("spring contacts: compression band over the stack (RSS) inside the travel", min(lo, G["travel"] - hi), m,
        f"nominal {work:.2f} of {G['travel']:g} [A]; ±{rss:.2f} RSS of " + ", ".join(f"{k} {v:.2f}" for k, v in T.items()) +
        f" → {lo:.2f}..{hi:.2f}. TIGHT. Worst case ±{wc:.2f} runs {max(wc - work, wc - (G['travel'] - work)):.2f} past the travel: "
        "contacts with 1.5 travel, or the vertical boards' height set in a jig")
    nhd = len(JD["springs"]); fhd = nhd * JD["spr_f"]
    net_lo = D["vb_n_contacts"] * G["f_lo"] - fhd
    net_nom = D["vb_n_contacts"] * G["f_nom"] - fhd
    row("cradle stays seated through a worst-case click (net contact preload / click)", net_lo / JD["push_hi"], D["vb_hold_margin"],
        f"{D['vb_n_contacts']} × {G['f_lo']:g} N [A] at the least compression − hold-downs {nhd} × {JD['spr_f']:g} N = {net_lo:.2f} N over "
        f"the worst click {JD['push_hi']:.2f} N (nominal {G['f_nom']:g} N each: {net_nom / JD['push_hi']:.2f}). Below this the cradle "
        "lifts off the gasket and the press goes into the contacts")
    row("overpress: lip still in the cutout when the contacts bottom", JD["lip_engage"] - (G["travel"] - lo), 1.0,
        f"cradle drop before the plungers bottom ≤ {G['travel'] - lo:.2f} (then the press goes edge-on into the vertical boards); "
        f"lip {JD['lip_engage']:.2f} into the faceplate")
    # ---- the contacts land on the top board's pads
    best, who = 9e9, ""
    holes = [(x, y, JD["spr_bore"]) for x, y in JD["springs"]] + [(x, y, JD["grub_access_d"]) for x, y in JD.get("access_xy", [])]
    pr = JD["tb_pad"] / 2 + JD["tb_tol"]
    for sx in (-1, 1):
        for y in D["vb_contact_y"]:
            x, yl = sx * D["vb_contact_x"], y - py
            e = min(JD["board_x1"] - abs(x), yl - JD["board_y0"], JD["board_y1"] - yl) - pr
            if e < best: best, who = e, f"board edge at ({x:.2f}, {y:.2f})"
            for hx, hy, hd in holes:
                d = math.hypot(x - hx, yl - hy) - hd / 2 - pr
                if d < best: best, who = d, f"hole at ({hx:.2f}, {hy + py:.2f})"
    row("spring contacts land on the top board's pads (copper to edge / holes)", best, JD["cu_edge"],
        f"pads Ø{JD['tb_pad']:g} ± {JD['tb_tol']:g} [A]; nearest: {who}")
    vbp = {n: q for n, q in pp.items() if n.startswith("vertical board")}
    # ---- header legs vs the top corner PCB notches (case corners)
    rp = H["pad"] / 2; best, who = 9e9, ""
    for cx, cy in D["corners"]:
        for sx in (-1, 1):
            for y in D["vb_pins"][sx]:
                d = math.hypot(sx * D["vb_pin_x"] - cx, y - cy) - D["notch_r"] - rp
                if d < best: best, who = d, f"leg ({sx * D['vb_pin_x']:.2f}, {y:.2f}) to the notch at ({cx:g}, {cy:.2f})"
    row("vertical-board header pads to the top corner PCB notches", best, 1.0,
        f"notch r {D['notch_r']:.2f}; {who}. Legs stop at y {D['vb_pin_y'][-1]:.2f} (vb_hdr.y_max {H['y_max']:g})")
    enc = [q for n, q in pp.items() if n.startswith(("encoder standoff", "encoder header", "encoder daughterboard"))]
    hdr = [q for n, q in vbp.items() if " header " in n]
    if enc and hdr:
        d = min(a.distance_to(b) for a in hdr for b in enc)
        row("vertical-board header legs (tails behind the main board) vs the encoder daughterboard, its header and standoff", d, 0.5,
            f"R has {len(D['vb_pins'][1])} legs (y {D['vb_pins'][1][0]:.2f}..{D['vb_pins'][1][-1]:.2f}): none over the encoder standoff "
            f"(vb_hdr.skip); L has {len(D['vb_pins'][-1])}. The encoder header is modelled with solder pads on the main-board back; "
            "if it is through-hole, its pins at (16.29, 25.92) and (14.66, 27.86) come up under R's foot [C]")
    # ---- vertical boards vs the case, the joystick springs and the case cradle
    case = {n: q for n, q in pp.items() if n == "case" or n.startswith("glow coat")}
    d, who = min(((a.distance_to(b), f"{na} / {nb}") for na, a in vbp.items() for nb, b in case.items()), default=(9.9, ""))
    row("vertical boards and their parts vs the case (corner posts, ledges, glow coat)", d, 1.0,
        f"nearest: {who}. Outer-face parts near the top corner posts (y ≈ 42-48.4, z < {D['z_post_top']:.1f}) stay under "
        f"{max(d - 1.0, 0):.2f} mm to keep 1.0 air [C]")
    boards = [q for n, q in vbp.items() if "FR4" in n]
    hd = [q for n, q in jp.items() if "hold-down spring" in n]
    d = min(a.distance_to(b) for a in boards for b in hd)
    row("vertical boards (inner faces) vs the joystick hold-down springs", d, 1.0,
        f"inner faces x ±{D['vb_face_in']:.2f}; springs (wire Ø{JD['spr_d']:g}) at x ±{JD['spr_x']:.2f}, panel y {py - JD['spr_y'] - 1:.1f}.."
        f"{py + JD['spr_y'] + 1:.1f}: inner-face parts there stay under {max(d - 1.0, 0):.2f} mm to keep 1.0 air [C]")
    ra = {n: q for n, q in jp.items() if "rear spring anchor" in n or "cross pin" in n}
    d, who = min(((a.distance_to(b), f"{na} / {nb[len(PREFIX):]}") for na, a in vbp.items() for nb, b in ra.items()), default=(9.9, ""))
    row("vertical boards (and header legs behind the main board) vs the joystick rear anchor and cross pins", d, 1.0,
        f"nearest: {who}; anchor x {JD['ra_x0']:.2f}..{JD['ra_x1']:.2f} on the board back, pin heads out to x {JD['ra_x1'] + 0.25 + JD['pin_head_t']:.2f}")
    cc = jp[PREFIX + CC_NAME]
    d, who = min(((cc.distance_to(q), n) for n, q in vbp.items()), default=(9.9, ""))
    row("vertical boards and their contacts vs the joystick case cradle", d, 0.5, f"nearest: {who}")
    tb = jp[PREFIX + "joystick top board (on the spring contacts)"]
    cts = [q for n, q in vbp.items() if "spring contacts" in n]
    dt = max(c.distance_to(tb) for c in cts)
    row("spring-contact tips on the top board's underside (drawn at nominal compression)", dt, 0.02,
        f"{len(D['vb_contact_y'])} per board at x ±{D['vb_contact_x']:.2f}, panel y {D['vb_contact_y'][0]:.2f}..{D['vb_contact_y'][-1]:.2f}",
        higher_ok=False)
    # ---- the H7B0 under the joystick
    M = D["mcu"]; (mx, my), c = M["xy"], M["court"] / 2
    best = 9e9
    for x, y in JD["springs"]:
        X, Y = x, y + py
        dx_ = max(abs(X - mx) - c, 0.0); dy_ = max(abs(Y - my) - c, 0.0)
        best = min(best, math.hypot(dx_, dy_) - JD["spr_d"] / 2)
    row("H7B0 courtyard to the joystick hold-down springs (plan)", best, 1.0,
        f"courtyard {M['court']:g} □ at ({mx:g}, {my:g}); springs at (±{JD['spr_x']:.2f}, {py - JD['spr_y']:.2f} / {py + JD['spr_y']:.2f})")
    keys = [Pos(x, y + py, -12.0) * Cylinder((JD["grub_access_d"] - 0.3) / 2, (JD["z_tip"] - JD["grub"]["length"]) + 12.0 - 0.05,
                                             align=(Align.CENTER, Align.CENTER, Align.MIN)) for x, y in JD.get("access_xy", [])]
    el = {n: q for n, q in pp.items() if n.startswith(("vertical board", "MCU "))}
    d, who = min(((k.distance_to(q), n) for k in keys for n, q in el.items()), default=(9.9, ""))
    row("press-spring grub key lines clear of the vertical boards, standoff and H7B0", d, 0.3,
        f"Ø{JD['grub_access_d'] - 0.3:.1f} key lines from behind the main PCB at (±{JD['cs_x']:.2f}, ±{JD['cs_y']:.2f}); nearest: {who}")
    # ---- the case cradle and its gasket against the real case
    cs = pp.get("case")
    if cs is not None:
        d = cc.distance_to(cs)
        row("joystick case cradle vs the real case (lip in the cutout, flange under the faceplate)", d, JD["cc"]["lip_c"] - 0.01,
            f"lip {JD['cc']['lip_c']:.2f} from the cutout walls, flange {JD['z_fp0'] - JD['z_fl1']:.2f} under the faceplate back")
        gk = jp[PREFIX + GK_NAME]
        row("cradle gasket on the real faceplate back", gk.distance_to(cs), 0.02,
            f"gasket top z {JD['z_fp0'] - 0.01:.2f}, faceplate back z {D['z_fp0']:.2f}", higher_ok=False)
        gl = [q for n, q in pp.items() if n.startswith("glow coat")]
        if gl:
            d = min(min(cc.distance_to(g), gk.distance_to(g)) for g in gl)
            row("case cradle flange and gasket clear of the side-wall glow coat", d, JD["cc"]["glow_air"] - 0.01,
                f"flange edge x ±{JD['fl_x1']:.2f}; the coat is modelled {D['glow_gap']:g} off the wall at x ±{D['x_in1']:.2f}")
    return r


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
