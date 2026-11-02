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
