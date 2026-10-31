"""Bezel v0.1 (2026-10-31). Ed: the bezel goes against the brass rod and the big knob goes outside it; printed, probably PETG,
it slides on the brass rod, and the knob slides on it with a PTFE tube (or a small sleeve if no stock size fits).
So: a FIXED [A] printed PETG sleeve on the Ø5 brass tube (sliding fit, bore Ø5.1 [A]). Its outer journal carries a stock
PTFE tube liner 10 OD x 8 ID [S], which is pressed into the knob hub and turns with the knob. A visible face ring Ø35 [L]
(knob-module-v1.md bezel) sits above the knob cap with a running gap, round the screen holder, and the holder sits on it.
The stem runs down to the PCB front, so the bezel is clamped between the PCB front and the holder (plus a drop of CA [A]).
A shoulder under the knob hub takes the knob's axial load.
Frame: dial axis = Z, Z = height above the main PCB front (as knob v0.1/v0.2). Tags: [K] KiCad, [L] layout, [S] stock, [A] assumed.
PTFE source: ATP Australia metric PTFE tube AFE10 10 x 8 (also 4x2.5, 6x4, 8x6, 12x10), https://www.atpaust.com.au/products/straight-tube/ptfe-tube/"""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "knob/knob-v0.1"):
    sys.path.insert(0, os.path.join(LIB, d))
import knob_gears as kg

K = kg.P
P = dict(
    tube_od=5.0,          # brass tube (shaft v0.2)
    bore=5.1,             # [A] sliding fit on the Ø5.0 tube
    liner_od=10.0, liner_id=8.0,   # [S] stock PTFE tube 10 x 8 (ATP AFE10, OD ±0.1); 8x6 rejected: journal Ø6 leaves 0.45 PETG wall
    liner_len=K["bush_len"],       # = the knob hub length 6.0 (was the bronze bush length)
    journal_clear=0.1,    # [A] diametral: journal Ø = liner ID - 0.1 (running fit; the liner is fixed in the hub)
    run_clear=0.3,        # [A] axial gaps: shoulder to the hub bottom, knob top to the bezel face
    shoulder_d=12.0,      # [A] thrust shoulder under the hub (motor body is at r 8.0 from the dial axis)
    shoulder_t=1.0,       # [A]
    face_d=K["bezel_d"],  # [L] Ø35 bezel (knob-module-v1.md)
    face_t=1.5,           # [A] visible face ring thickness
    z_base=0.0,           # stem stands on the PCB front [A]
)
p = P
p["journal_d"] = p["liner_id"] - p["journal_clear"]           # 7.9
p["wall"] = (p["journal_d"] - p["bore"]) / 2                    # 1.40 PETG
p["z_sh1"] = K["h_hub0"] - p["run_clear"]                       # 39.2: shoulder top, 0.3 under the knob hub
p["z_sh0"] = p["z_sh1"] - p["shoulder_t"]
p["z_f0"] = K["h_top"] + p["run_clear"]                         # 45.8: face underside, 0.3 over the knob top
p["z_f1"] = p["z_f0"] + p["face_t"]                             # 47.3: top face = screen holder seat
p["height"] = p["z_f1"] - p["z_base"]

def profile(p=P):
    rb, rj, rs, ro = p["bore"] / 2, p["journal_d"] / 2, p["shoulder_d"] / 2, p["face_d"] / 2
    return [(rb, p["z_base"]), (rj, p["z_base"]), (rj, p["z_sh0"]), (rs, p["z_sh0"]), (rs, p["z_sh1"]), (rj, p["z_sh1"]),
            (rj, p["z_f0"]), (ro, p["z_f0"]), (ro, p["z_f1"]), (rb, p["z_f1"])]

def build_bezel(p=P):
    f = Face(Wire.make_polygon([Vector(r, 0, z) for r, z in profile(p)], close=True))
    return revolve(f, Axis.Z, 360)

def build_liner(p=P):
    """Stock PTFE tube 10 x 8 cut to the hub length, pressed into the knob hub (turns with the knob)."""
    A = (Align.CENTER, Align.CENTER, Align.MIN)
    return Pos(0, 0, K["h_hub0"]) * (Cylinder(p["liner_od"] / 2, p["liner_len"], align=A) - Cylinder(p["liner_id"] / 2, p["liner_len"], align=A))

HATCH = ["////", "\\\\\\\\", "xx", "---", "|||", "//", "\\\\\\\\\\\\", "++", "...", "/", "\\\\", "-", "|", "x", "oo", "////\\\\\\\\"]

def section_items(parts, y=0.0):
    """[(name, faces, hatch)] for Sheet.set_front_section: cut on the world plane Y = y (through the dial axis)."""
    cut = Plane(origin=(0, y, 0), x_dir=(1, 0, 0), z_dir=(0, 1, 0))
    items = []
    for n, part in parts.items():
        try: fs = section(part, section_by=cut).faces()
        except Exception: fs = []
        if fs: items.append((n, list(fs), HATCH[len(items) % len(HATCH)]))
    return items

def flag_fit(holder_od, knob_od, p=P):
    """Visible face ring round the screen holder, inside the knob cap."""
    ring = (p["face_d"] - holder_od) / 2
    ok = holder_od < p["face_d"] < knob_od
    txt = f"Bezel face Ø{p['face_d']:.1f} [L]: {ring:.2f} visible ring round the Ø{holder_od:.2f} holder, inside the Ø{knob_od:.1f} knob cap"
    return (txt + " — fits", {}) if ok else (txt + " — DOES NOT FIT [check]", dict(color="red", weight="bold"))

if __name__ == "__main__":
    from sheet import Sheet
    sys.path.insert(0, os.path.join(LIB, "holders", "screen-holder-v0.1")); sys.path.insert(0, os.path.join(LIB, "knob", "knob-v0.2"))
    import screen_holder as hold, knob_v02 as kv
    b = build_bezel(); export_step(b, os.path.join(HERE, "bezel.step"))
    rb, rj, rs, ro = p["bore"] / 2, p["journal_d"] / 2, p["shoulder_d"] / 2, p["face_d"] / 2
    sh = Sheet(b, gap=34, scale=2.4, label_pad=14)
    sh.set_front_section(section_items({"bezel": b}), "SECTION A-A (through the dial axis)")
    sh.hdim("front", -ro, ro, p["z_f1"], p["z_f1"] + 4, f"Ø{p['face_d']:.1f} face [L]")
    sh.hdim("front", -rj, rj, p["z_base"], p["z_base"] - 7, f"Ø{p['journal_d']:.2f} journal + stem = PTFE ID {p['liner_id']:.0f} − {p['journal_clear']:.1f} [A]")
    sh.hdim("front", -rb, rb, p["z_base"], p["z_base"] - 3, f"Ø{p['bore']:.1f} bore [A] on the Ø5.0 tube")
    sh.vdim("front", p["z_base"], p["z_f1"], -ro, -ro - 4, f"{p['height']:.2f} overall (PCB front to the face top)")
    sh.vdim("plan", p["z_f0"], p["z_f1"], ro, ro + 4, f"{p['face_t']:.1f} face [A]")
    sh.vdim("plan", p["z_sh1"], p["z_f0"], rj, ro + 10, f"{p['z_f0'] - p['z_sh1']:.1f} journal")
    sh.vdim("plan", p["z_sh0"], p["z_sh1"], rs, ro + 16, f"{p['shoulder_t']:.1f} shoulder [A]")
    sb = sh.bb["side"]; sh.cut_line("side", sb[0] - 3, sb[1] + 3, 0, -1, "A")
    lines = ["Printed PETG [Ed], FIXED [A]: slides on the brass tube, clamped between the PCB front and the screen holder (+ CA drop [A])",
             f"Journal carries a stock PTFE tube {p['liner_od']:.0f} × {p['liner_id']:.0f} [S] (ATP AFE10), {p['liner_len']:.0f} long, pressed in the knob hub",
             f"PETG wall {p['wall']:.2f} at the journal (Ø{p['journal_d']:.2f} over the Ø{p['bore']:.1f} bore)",
             f"Shoulder top {p['z_sh1']:.2f} = {p['run_clear']:.1f} [A] under the knob hub; face underside {p['z_f0']:.2f} = {p['run_clear']:.1f} [A] over the knob top",
             f"Thrust shoulder Ø{p['shoulder_d']:.1f} × {p['shoulder_t']:.1f} [A] under the hub (motor body at r 8.0 from the axis)",
             f"Top face {p['z_f1']:.2f} above the PCB front = the screen holder seat",
             flag_fit(hold.P["od"], kv.P["skirt_od"]),
             ("8x6 PTFE rejected (journal Ø6 → 0.45 wall); 10x8 chosen, so the knob hub bore grows 8 → 10 (knob v0.3)", {})]
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        sh.note("plan", ro + 30, p["z_f1"] - i * 2.4, l, 8 if i == 0 else 6.5, **kw)
    title = "Bezel — v0.1, 2026-10-31"
    sub = [f"Printed PETG sleeve on the Ø5 tube; Ø{p['face_d']:.0f} face; PTFE 10x8 journal.", "[L] = layout, [S] = stock, [Ed] = Ed, [A] = assumed.",
           "Third-angle projection · mm · plan view drawn front-up"]
    sh.dxf(os.path.join(HERE, "bezel.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "bezel-drawing.png"), title, sub)
    print({k: round(v, 3) if isinstance(v, float) else v for k, v in p.items()})
