"""Bezel knob v0.2 (2026-10-31). Supersedes bezel v0.1 (renamed bezel knob; ../bezel-knob-v0.1).
Ed: concentrically it is the fixed brass tube, then the bezel knob on the tube, then the big knob on the bezel knob's journal
(via the PTFE liner). The bezel knob's OD equals the big knob's OD (48.0), so it is a full-diameter ring sitting on top of the
big knob, and its top face is flush with the screen glass top.
It is the spring-centred, Hall-sensed bezel dial: it turns only ±10° max [A] from centre (Ed: about 5–10° either way).
The return spring, magnet and Hall sensor are TBC and not drawn.
Kept from v0.1 by import: bore Ø5.1, journal Ø7.9 for the PTFE 10x8 liner, thrust shoulder, stem on the PCB front.
New: the face ring grows to Ø48.0 and up to the glass top, with a pocket round the FIXED screen holder. Because the bezel knob
moves (±10°) and the holder is fixed to the tube, the holder no longer sits on it: it clears the pocket floor by 0.3 [A] and
the pocket wall by 0.2 per side [A]. The holder, screen and adapter move up 0.30 (holder base 47.60).
Frame: dial axis = Z, Z = height above the main PCB front. Tags: [L] layout, [S] stock, [A] assumed."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "knob/knob-v0.1", "knob/knob-v0.2", "bezel-knob/bezel-knob-v0.1", "holders/screen-holder-v0.1"):
    sys.path.insert(0, os.path.join(LIB, d))
import bezel as b1
import knob_v02 as kv
import screen_holder as hold

HP = hold.P
P = dict(b1.P)
p = P
p.update(
    face_d=kv.P["skirt_od"],   # [Ed] = big knob OD 48.0
    floor_t=1.5,               # [A] pocket floor (was the v0.1 face thickness)
    holder_gap=0.3,            # [A] holder base above the pocket floor (holder fixed, bezel knob moves ±10°)
    pocket_clear=0.2,          # [A] per side, pocket wall to the holder OD
    travel_deg=10.0,           # [A] ±10° max from centre (Ed: about 5–10°)
)
p["z_floor"] = p["z_f0"] + p["floor_t"]                    # 47.3 pocket floor top
p["holder_z0"] = p["z_floor"] + p["holder_gap"]            # 47.6 holder base
p["holder_dz"] = p["holder_z0"] - HP["z0"]                 # shift of holder/screen/adapter vs the holder v0.1 frame (45.8)
p["z_top"] = HP["z_glass_top"] + p["holder_dz"]            # = glass top: bezel-knob top face flush with it
p["pocket_d"] = HP["od"] + 2 * p["pocket_clear"]
p["ring_w"] = (p["face_d"] - p["pocket_d"]) / 2
p["height"] = p["z_top"] - p["z_base"]
p["socket_engage"] = HP["socket_len"] - p["holder_dz"]     # tube v0.2 in the holder socket (tube not lengthened)

def profile(p=P):
    rb, rj, rs, ro, rp = p["bore"] / 2, p["journal_d"] / 2, p["shoulder_d"] / 2, p["face_d"] / 2, p["pocket_d"] / 2
    return [(rb, p["z_base"]), (rj, p["z_base"]), (rj, p["z_sh0"]), (rs, p["z_sh0"]), (rs, p["z_sh1"]), (rj, p["z_sh1"]),
            (rj, p["z_f0"]), (ro, p["z_f0"]), (ro, p["z_top"]), (rp, p["z_top"]), (rp, p["z_floor"]), (rb, p["z_floor"])]

def build_bezel_knob(p=P):
    f = Face(Wire.make_polygon([Vector(r, 0, z) for r, z in profile(p)], close=True))
    return revolve(f, Axis.Z, 360)

build_liner = b1.build_liner
TRAVEL = f"Bezel knob = spring-centred Hall-sensed bezel dial: turns ±{P['travel_deg']:.0f}° max from centre [A] (Ed: about 5–10°)"
TBC = "Return spring, magnet and Hall sensor TBC (not drawn)"

if __name__ == "__main__":
    from sheet import Sheet
    b = build_bezel_knob(); export_step(b, os.path.join(HERE, "bezel-knob.step"))
    rb, rj, ro, rp = p["bore"] / 2, p["journal_d"] / 2, p["face_d"] / 2, p["pocket_d"] / 2
    sh = Sheet(layout="panel", shape=b, gap=40, scale=2.0, label_pad=24)
    sh.set_front_section(b1.section_items({"bezel knob": b}), "SECTION A-A (through the dial axis)")
    sh.hdim("front", -ro, ro, p["z_top"], p["z_top"] + 9, f"Ø{p['face_d']:.1f} OD = big knob OD [Ed]")
    sh.hdim("front", -rp, rp, p["z_top"], p["z_top"] + 4, f"Ø{p['pocket_d']:.2f} pocket = holder Ø{HP['od']:.2f} + 2×{p['pocket_clear']:.1f} [A]")
    sh.hdim("front", -rb, rb, p["z_base"], p["z_base"] - 3, f"Ø{p['bore']:.1f} bore [A] on the Ø5.0 tube")
    sh.hdim("front", -rj, rj, p["z_base"], p["z_base"] - 7, f"Ø{p['journal_d']:.2f} journal + stem (PTFE 10×8 [S])")
    sh.vdim("front", p["z_base"], p["z_top"], -ro, -ro - 4, f"{p['height']:.2f} overall (PCB front to the top face)")
    sh.vdim("plan", p["z_f0"], p["z_top"], ro, ro + 4, f"{p['z_top'] - p['z_f0']:.2f} ring")
    sh.vdim("plan", p["z_f0"], p["z_floor"], rp, ro + 10, f"{p['floor_t']:.1f} floor [A]")
    sh.vdim("plan", p["z_sh1"], p["z_f0"], rj, ro + 16, f"{p['z_f0'] - p['z_sh1']:.1f} journal")
    sb = sh.bb["side"]; sh.cut_line("side", sb[0] - 3, sb[1] + 3, 0, -1, "A")
    lines = [TRAVEL, (TBC, {}),
             "Printed PETG [Ed]; on the Ø5 brass tube; the big knob runs on its journal via the PTFE 10×8 liner [S]",
             f"Top face {p['z_top']:.2f} above the PCB front, flush with the screen glass top [Ed]",
             f"Ring Ø{p['face_d']:.1f} × {p['z_top'] - p['z_f0']:.2f} from {p['z_f0']:.2f} ({p['run_clear']:.1f} [A] over the big knob top); visible ring {p['ring_w']:.2f} wide",
             f"Pocket: fixed screen holder base {p['holder_z0']:.2f} = floor + {p['holder_gap']:.1f} [A]; holder/screen/adapter up {p['holder_dz']:.2f} vs holder v0.1",
             f"Bore Ø{p['bore']:.1f}, journal Ø{p['journal_d']:.2f}, shoulder Ø{p['shoulder_d']:.0f} × {p['shoulder_t']:.0f}: unchanged from v0.1",
             (f"Tube v0.2 now engages the holder socket {p['socket_engage']:.2f} of {HP['socket_len']:.1f} (tube not lengthened) [check]", dict(color="red", weight="bold"))]
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        sh.note("plan", ro + 26, p["z_top"] - i * 2.6, l, 8 if i == 0 else 6.5, **kw)
    title = "Bezel knob — v0.2, 2026-10-31"
    sub = [f"Ø{p['face_d']:.0f} ring on the big knob, top flush with the glass; ±{p['travel_deg']:.0f}° [A].", "[L] = layout, [S] = stock, [Ed] = Ed, [A] = assumed.",
           "Third-angle projection · mm · plan view drawn front-up"]
    sh.dxf(os.path.join(HERE, "bezel-knob.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "bezel-knob-drawing.png"), title, sub)
    print({k: round(v, 3) if isinstance(v, float) else v for k, v in p.items()})
