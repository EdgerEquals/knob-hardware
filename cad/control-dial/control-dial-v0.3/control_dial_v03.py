"""Control dial v0.3 (2026-10-31; Ed: the bezel / bezel knob is now the CONTROL DIAL). Supersedes control dial v0.2 (bezel knob).
Spring-centred, Hall-sensed: turns ±10° max from centre [A]; return spring, magnet and Hall sensor TBC (not drawn).
Concentric, no bearings for now: brass tube (innermost, fixed) -> control-dial tube sleeved directly on it, the whole way down to the
PCB front -> big-knob tube sleeved over that (knob v0.4). The thinner screen holder v0.2 frees the space round the axis, so the
dial body is solid from its Ø7.3 boss clearance bore out to Ø48, 5.70 thick under the holder cup (v0.2 floor: 1.5).
OD Ø48.0 = big knob OD; top face flush with the screen glass top (holder v0.2: 56.80).
Frame: dial axis = Z, Z = height above the main PCB front. Tags: [Ed] Ed, [A] assumed."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "knob/knob-v0.1", "knob/knob-v0.2", "knob/knob-v0.4", "holders/screen-holder-v0.1", "holders/screen-holder-v0.2",
          "control-dial/control-dial-v0.1"):
    sys.path.insert(0, os.path.join(LIB, d))
import knob_v04 as k4
import screen_holder_v02 as h2
import bezel as b1

HP, KP = h2.P, k4.P
P = dict(
    tube_id=KP["dial_tube_id"], tube_od=KP["dial_tube_od"], tube_wall=KP["dial_tube_wall"],   # 5.12 / 8.12 / 1.5 [A]
    z_base=KP["knob_tube_z0"],      # tube bottom above the reserved bearing zone over the base-cradle tube boss (knob v0.4)
    z_body0=HP["z_dial0"],          # 45.80 = big knob top + 0.3 [A]
    face_d=KP["skirt_od"],          # [Ed] = big knob OD 48.0
    boss_clear=0.15,                # [A] per side round the holder socket boss
    cup_clear=0.2,                  # [A] per side round the holder cup
    cup_gap=0.3,                    # [A] pocket floor under the holder cup
    travel_deg=10.0,                # [A]
)
p = P
p["bore_d"] = HP["boss_d"] + 2 * p["boss_clear"]             # 7.30
p["pocket_d"] = HP["od"] + 2 * p["cup_clear"]                # 22.32
p["z_pf"] = HP["z_cup0"] - p["cup_gap"]                      # 51.50 pocket floor
p["z_top"] = HP["z_glass_top"]                               # 56.80 flush with the glass [Ed]
p["inner_t"] = p["z_pf"] - p["z_body0"]                      # 5.70 thick near the axis (under the cup)
p["inner_w"] = (p["pocket_d"] - p["bore_d"]) / 2             # 7.51 radial, bore to pocket wall
p["ring_t"] = p["z_top"] - p["z_body0"]                      # 11.0
p["ring_w"] = (p["face_d"] - p["pocket_d"]) / 2
p["height"] = p["z_top"] - p["z_base"]

def profile(p=P):
    ri, rt, rb, rp, ro = p["tube_id"] / 2, p["tube_od"] / 2, p["bore_d"] / 2, p["pocket_d"] / 2, p["face_d"] / 2
    return [(ri, p["z_base"]), (rt, p["z_base"]), (rt, p["z_body0"]), (ro, p["z_body0"]), (ro, p["z_top"]), (rp, p["z_top"]),
            (rp, p["z_pf"]), (rb, p["z_pf"]), (rb, p["z_body0"]), (ri, p["z_body0"])]

def build_control_dial(p=P):
    f = Face(Wire.make_polygon([Vector(r, 0, z) for r, z in profile(p)], close=True))
    return revolve(f, Axis.Z, 360)

TRAVEL = f"Control dial: spring-centred, Hall-sensed, turns ±{P['travel_deg']:.0f}° max from centre [A] (Ed: about 5–10°)"
TBC = "Return spring, magnet and Hall sensor TBC (not drawn)"

if __name__ == "__main__":
    from sheet import Sheet
    d = build_control_dial(); export_step(d, os.path.join(HERE, "control-dial.step"))
    ri, rt, rb, rp, ro = p["tube_id"] / 2, p["tube_od"] / 2, p["bore_d"] / 2, p["pocket_d"] / 2, p["face_d"] / 2
    sh = Sheet(d, gap=40, scale=2.0, label_pad=28)
    sh.set_front_section(b1.section_items({"control dial": d}), "SECTION A-A (through the dial axis)")
    sh.hdim("front", -ro, ro, p["z_top"], p["z_top"] + 9, f"Ø{p['face_d']:.1f} OD = big knob OD [Ed]")
    sh.hdim("front", -rp, rp, p["z_top"], p["z_top"] + 4, f"Ø{p['pocket_d']:.2f} cup pocket [A]")
    sh.hdim("front", -rt, rt, p["z_base"], p["z_base"] - 3, f"Ø{p['tube_od']:.2f} tube OD ({p['tube_wall']:.1f} wall [A])")
    sh.hdim("front", -ri, ri, p["z_base"], p["z_base"] - 7, f"Ø{p['tube_id']:.2f} tube ID on the Ø5.0 brass ({KP['fit']:.2f} [A])")
    sh.vdim("front", p["z_base"], p["z_top"], -ro, -ro - 4, f"{p['height']:.2f} tube bottom to the top face")
    sh.vdim("front", p["z_body0"], p["z_pf"], rb, ro + 4, f"{p['inner_t']:.2f} near the axis (v0.2: 1.5)")
    sh.vdim("front", p["z_body0"], p["z_top"], ro, ro + 12, f"{p['ring_t']:.1f} ring")
    sb = sh.bb["plan"]; sh.cut_line("plan", sb[0] - 3, sb[1] + 3, 0, +1, "A")
    lines = [TRAVEL, TBC, "Printed PETG [Ed]. Tube sleeved directly on the brass tube; no bearings [Ed]",
             f"Tube stops at {p['z_base']:.2f}: {KP['cradle_boss_top']:.1f}–{p['z_base']:.1f} reserved for future bearing [A] above the base-cradle boss",
             f"Big-knob tube Ø{KP['knob_tube_id']:.2f} ID slides over this tube's Ø{p['tube_od']:.2f} OD; PTFE liner and thrust shoulder dropped",
             f"Body {p['z_body0']:.2f}–{p['z_top']:.2f}: top flush with the glass top [Ed]; bore Ø{p['bore_d']:.2f} clears the holder boss Ø{HP['boss_d']:.1f}",
             f"Near the axis: {p['inner_t']:.2f} thick × {p['inner_w']:.2f} radial under the holder cup (v0.2: 1.5 floor)",
             "Axial location of the dial and the big knob TBC (no shoulder for now)"]
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        sh.note("plan", sb[1] + 14, sb[3] - i * 2.6, l, 8 if i == 0 else 6.5, **kw)
    title = "Control dial — v0.3, 2026-10-31"
    sub = [f"Was the bezel knob. Ø{p['face_d']:.0f}, flush with the glass, ±{p['travel_deg']:.0f}° [A]; tube on the brass tube.",
           "[Ed] = Ed, [A] = assumed.", "Third-angle · mm · z-up: top view above, section A-A front"]
    sh.dxf(os.path.join(HERE, "control-dial.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "control-dial-drawing.png"), title, sub)
    print({k: round(v, 3) for k, v in p.items() if isinstance(v, float)})
