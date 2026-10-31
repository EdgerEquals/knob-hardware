"""Fixed hollow shaft, 4 mm stainless tube, v0.1 (2026-10-31).
Ed: sits on the dial axis, fixed to the main PCB, does not rotate. 8 x 36 AWG PTFE wires from the
centre-screen adapter board run down the bore and out the back of the PCB to a connector.
Tags: [E] = locked by Ed, [A] = assumed. Part axis = Z; back end (PCB end) at Z=0, front end at Z=length.
Fixing to the PCB is TBC: no flange or fixing feature is modelled."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tools"))

P = dict(
    od=4.0,          # [E] outside diameter
    bore=2.0,        # [E] bore (ID)
    length=45.0,     # [A] length TBC
    chamfer=0.3,     # [A] 45 deg bore chamfer/deburr, both ends (wire protection)
    material="stainless tube",
)

def build(p=P):
    tube = Cylinder(p["od"] / 2, p["length"], align=(Align.CENTER, Align.CENTER, Align.MIN)) \
         - Cylinder(p["bore"] / 2, p["length"], align=(Align.CENTER, Align.CENTER, Align.MIN))
    inner = [e for e in tube.edges().filter_by(GeomType.CIRCLE) if abs(e.radius - p["bore"] / 2) < 1e-6]
    return chamfer(inner, p["chamfer"])

if __name__ == "__main__":
    from sheet import Sheet
    p = P; t = build(p); L = p["length"]; R = p["od"] / 2; r = p["bore"] / 2; c = p["chamfer"]
    export_step(t, os.path.join(HERE, "fixed-hollow-shaft-4mm.step"))
    sh = Sheet(t, gap=22, scale=3)
    # front view = end view (circles)
    sh.hdim("front", -R, R, -R, -R - 4, f"Ø{p['od']:.1f} OD [Ed]")
    sh.hdim("front", -r, r, R, R + 3, f"Ø{p['bore']:.1f} bore [Ed]")
    sh.vdim("front", -(r + c), r + c, r + c, R + 2.5, f"Ø{p['bore'] + 2 * c:.1f}")
    # side view: length horizontal (front end on the left)
    sh.hdim("side", -L, 0, -R, -R - 5, f"{L:.1f} length TBC [A]")
    sh.vdim("side", -R, R, 0, 4, f"Ø{p['od']:.1f}")
    sh.note("side", -L, R + 1.5, f"bore chamfer {c:.1f} × 45° both ends (wire protection) [A]; Ø{p['bore'] + 2 * c:.1f} at the end face", 6.5)
    nx = R + 6
    for i, line in enumerate(["NOTES",
                              "1. Bundle 8 x 36 AWG PTFE about 1.2-1.5 mm in a 2.0 mm bore",
                              "2. Fixing to PCB TBC (no flange or fixing feature drawn)",
                              f"3. Length {L:.0f} TBC [A]; OD and bore locked by Ed",
                              f"4. Bore chamfer {c:.1f} × 45° both ends [A], too small to see at this scale",
                              "5. Side view: front end on the left, PCB end on the right"]):
        sh.note("plan", nx, L - 2 - i * 1.6, line, 8 if i == 0 else 7, weight="bold" if i == 0 else "normal")
    title = "Fixed hollow shaft 4 mm — v0.1, 2026-10-31"
    sub = [f"Stainless tube Ø{p['od']:.1f} OD × Ø{p['bore']:.1f} bore [Ed]; length {L:.0f} TBC [A].",
           "Fixed on the dial axis to the main PCB; does not rotate. [A] = assumed.",
           "Third-angle projection · mm · plan view drawn front-up"]
    sh.dxf(os.path.join(HERE, "fixed-hollow-shaft-4mm.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "fixed-hollow-shaft-4mm-drawing.png"), title, sub,
           labels={"front": "FRONT VIEW (end)", "plan": "PLAN (TOP) VIEW — front up", "side": "RIGHT SIDE VIEW"})
    print("ok", t.is_valid, round(t.volume, 2))
