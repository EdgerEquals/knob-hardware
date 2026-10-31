"""Control dial v0.5 (2026-10-31). Supersedes v0.4. Ed: the big knob drops by the 4 mm dial thickness so the control dial's 4.0 lip
comes out to the full Ø48 (same OD as the big knob), sitting on top of the knob, flush with the screen; 0.3 [A] running gap.
Magnet placeholder [A] (size TBC) now sits in an annular pocket in the LIP UNDERSIDE (Ø39.4–Ø43.4 × 2.0, 2.0 skin above),
facing the big knob's top face 0.3 below. Bearing now MR128ZZ 8 x 12 x 3.5 [A] (knob v0.6): the hub's bottom face is raised
0.3 and a Ø9.2 [A] collar bears on the inner race only (the outer race land starts at about r 5.2).
Tube Ø5.12/Ø8.12 from 13.00 unchanged [Ed]. Spring and Hall sensor TBC (not drawn).
v0.4 notes: Control dial v0.4 (2026-10-31). Supersedes v0.3.
Ed: the control dial is only a lip about 4 mm thick at the top; the big knob comes up round the outside into where the dial was,
and the magnet fits round the lip. Ed: keep the control-dial tube exactly as it is (Ø5.12 / Ø8.12, sleeved on the brass tube,
from 13.00), no shoulder on it. Spring-centred, Hall-sensed, ±10° [A]; spring and Hall sensor TBC (not drawn).
Shape (one printed PETG piece): unchanged tube -> hub round the holder boss -> 4.0 web under the screen cup -> 4.0 lip at the top.
Snap-off fix (tube unchanged): the brass tube runs inside the dial up to 45.50, so bending at the tube/hub junction goes into the
brass; the hub is Ø11.30 (2.0 wall [A]) round the Ø7.30 holder-boss bore, with a 1.5 × 45° gusset fillet [A] into the web and a
1.0 × 45° fillet [A] web-to-lip, so there is no thin neck; and the big knob's 688ZZ bearing (steel inner race) sits on the tube
right under the hub, its inner race top against the hub's bottom face, which stiffens that section.
Magnet placeholder: plain ring on the lip OD, size TBC [A].
Frame: dial axis = Z, Z = height above the main PCB front. Tags: [Ed] Ed, [A] assumed."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "knob/knob-v0.1", "knob/knob-v0.2", "knob/knob-v0.4", "holders/screen-holder-v0.1", "holders/screen-holder-v0.2",
          "holders/screen-holder-v0.3", "holders/screen-holder-v0.4", "control-dial/control-dial-v0.1", "control-dial/control-dial-v0.4", "control-dial/control-dial-v0.3"):
    sys.path.insert(0, os.path.join(LIB, d))
import knob_v04 as k4
import screen_holder_v04 as h3   # v0.4 holder (tube through to the adapter board)
import control_dial_v03 as d3
import bezel as b1

HP, KP = h3.P, k4.P
P = dict(
    tube_id=d3.P["tube_id"], tube_od=d3.P["tube_od"], tube_wall=d3.P["tube_wall"], z_base=d3.P["z_base"],   # [Ed] unchanged 5.12/8.12 from 13.00
    run=0.3,                 # [A] running gap to fixed / other rotating parts
    hub_wall=2.0,            # [A] round the holder-boss bore
    web_t=4.0,               # [A] web under the screen cup
    lip_t=4.0,               # [Ed] about 4 mm
    gusset=1.5,              # [A] 45° hub-to-web fillet
    lip_fillet=1.0,          # [A] 45° web-to-lip fillet
    lip_od=48.0,             # [Ed] full knob OD
    mag_id=39.4,             # [A] magnet placeholder ID (as v0.4)
    brg_B=3.5,               # MR128ZZ width [A] (knob v0.6)
    collar_d=9.2,            # [A] inner-race collar (MR128 inner race land ~Ø9.4)
    collar_h=0.3,            # [A] hub face raised clear of the outer race
    motor_front=38.0, motor_clear=0.6,   # [M] 1220 front face; [A] bearing above it
    mag_t=2.0, mag_h=2.0,    # [A] magnet placeholder radial thickness and height (size TBC), in the lip underside
    travel_deg=10.0,         # [A]
)
p = P
p["z_top"] = HP["z_glass_top"]                        # 56.80 flush with the glass [Ed]
p["z_lip0"] = p["z_top"] - p["lip_t"]                 # 52.80
p["r_cup"] = HP["od"] / 2 + 0.2                       # 11.16 round the holder cup (0.2 [A], as v0.3)
p["z_web1"] = HP["z_cup0"] - p["run"]                 # 51.50 under the cup
p["z_web0"] = p["z_web1"] - p["web_t"]                # 47.50
p["bore_d"] = HP["boss_d"] + 2 * 0.15                 # 7.30 round the holder boss (0.15 [A])
p["z_bore0"] = HP["z0"] - p["run"]                    # 45.50: brass inside the dial up to here
p["hub_od"] = p["bore_d"] + 2 * p["hub_wall"]         # 11.30
p["z_hub0"] = 43.6                                    # [A] bearing top (as v0.4); collar on the inner race
p["z_hubf"] = p["z_hub0"] + p["collar_h"]             # 43.90 hub face
p["r_web"] = 14.0                                     # [A] web OD radius (lip/web junction)
p["mag_od"] = p["mag_id"] + 2 * p["mag_t"]            # 43.4
p["z_mag0"] = p["z_lip0"]                             # 52.80: flush with the lip underside
p["mag_skin"] = p["lip_t"] - p["mag_h"]               # 2.0 above the magnet
p["hub_len"] = p["z_web0"] - p["z_hubf"]              # 3.60
p["brass_in_dial"] = p["z_bore0"] - p["z_base"]       # 32.50 sliding on the brass

def profile(p=P):
    ri, rt, rb, rh, rc, rw, rl = p["tube_id"] / 2, p["tube_od"] / 2, p["bore_d"] / 2, p["hub_od"] / 2, p["r_cup"], p["r_web"], p["lip_od"] / 2
    g, f = p["gusset"], p["lip_fillet"]
    return [(ri, p["z_base"]), (rt, p["z_base"]), (rt, p["z_hub0"]), (p["collar_d"] / 2, p["z_hub0"]), (p["collar_d"] / 2, p["z_hubf"]), (rh, p["z_hubf"]), (rh, p["z_web0"] - g), (rh + g, p["z_web0"]),
            (rw, p["z_web0"]), (rw, p["z_lip0"] - f), (rw + f, p["z_lip0"]), (rl, p["z_lip0"]), (rl, p["z_top"]), (rc, p["z_top"]),
            (rc, p["z_web1"]), (rb, p["z_web1"]), (rb, p["z_bore0"]), (ri, p["z_bore0"])]

def _rev(pts):
    return revolve(Face(Wire.make_polygon([Vector(r, 0, z) for r, z in pts], close=True)), Axis.Z, 360)
def build_control_dial(p=P):
    a, b = p["mag_id"] / 2, p["mag_od"] / 2
    pocket = _rev([(a, p["z_mag0"]), (b, p["z_mag0"]), (b, p["z_mag0"] + p["mag_h"]), (a, p["z_mag0"] + p["mag_h"])])
    return _rev(profile(p)) - pocket
def build_magnet(p=P):
    a, b = p["mag_id"] / 2, p["mag_od"] / 2
    return _rev([(a, p["z_mag0"]), (b, p["z_mag0"]), (b, p["z_mag0"] + p["mag_h"]), (a, p["z_mag0"] + p["mag_h"])])

TRAVEL = f"Control dial: spring-centred, Hall-sensed, ±{P['travel_deg']:.0f}° max [A]; spring and Hall sensor TBC (not drawn)"
MAGNET = f"Magnet [A] — size TBC: ring Ø{P['mag_id']:.1f} × Ø{P['mag_od']:.1f} × {P['mag_h']:.1f} in a pocket in the lip underside ({P['mag_skin']:.1f} skin), facing the knob top"
STRUCT = [f"Snap-off: brass runs inside the dial up to {P['z_bore0']:.2f} ({P['brass_in_dial']:.1f} sliding length), past the tube/hub junction",
          f"Hub Ø{P['hub_od']:.2f} ({P['hub_wall']:.1f} wall [A]) round the Ø{P['bore_d']:.2f} boss bore, {P['gusset']:.1f}×45° gusset to the web, {P['lip_fillet']:.1f}×45° web-to-lip",
          f"Big-knob MR128ZZ inner race on the tube right under the hub (top {P['z_hub0']:.2f} against the Ø{P['collar_d']:.1f} collar)"]

if __name__ == "__main__":
    from sheet import Sheet
    d = build_control_dial(); mg = build_magnet()
    export_step(d, os.path.join(HERE, "control-dial.step")); export_step(mg, os.path.join(HERE, "magnet-placeholder.step"))
    ri, rt, rb, rh, rc, rw, rl = p["tube_id"] / 2, p["tube_od"] / 2, p["bore_d"] / 2, p["hub_od"] / 2, p["r_cup"], p["r_web"], p["lip_od"] / 2
    both = Compound(children=[d, mg])
    sh = Sheet(both, gap=40, scale=1.6, label_pad=30)
    sh.set_front_section(b1.section_items({"control dial": d, "magnet": mg}), "SECTION A-A (through the dial axis)")
    mo = p["mag_od"] / 2
    sh.hdim("front", -mo, mo, p["z_top"], p["z_top"] + 10, f"Ø{p['mag_od']:.1f} magnet OD [A]")
    sh.hdim("front", -rl, rl, p["z_top"], p["z_top"] + 6, f"Ø{p['lip_od']:.1f} lip OD = big knob OD [Ed]")
    sh.hdim("front", -rc, rc, p["z_top"], p["z_top"] + 2, f"Ø{2 * rc:.2f} round the holder cup")
    sh.hdim("front", -rt, rt, p["z_base"], p["z_base"] - 3, f"Ø{p['tube_od']:.2f} tube OD (unchanged [Ed])")
    sh.hdim("front", -ri, ri, p["z_base"], p["z_base"] - 7, f"Ø{p['tube_id']:.2f} tube ID on the Ø5.0 brass")
    sh.vdim("front", p["z_base"], p["z_top"], -rl, -rl - 4, f"{p['z_top'] - p['z_base']:.2f} tube bottom to top")
    sh.vdim("front", p["z_lip0"], p["z_top"], rl, rl + 4, f"{p['lip_t']:.1f} lip [Ed]")
    sh.vdim("front", p["z_web0"], p["z_web1"], rl, rl + 12, f"{p['web_t']:.1f} web [A]")
    sh.vdim("front", p["z_hub0"], p["z_web0"], -rh, -rh - 6, f"{p['hub_len']:.1f} hub")
    sh.vdim("front", p["z_mag0"], p["z_mag0"] + p["mag_h"], rl, rl + 20, f"{p['mag_h']:.1f} magnet [A]")
    sb = sh.bb["plan"]; sh.cut_line("plan", sb[0] - 3, sb[1] + 3, 0, +1, "A")
    lines = [TRAVEL, "Printed PETG [Ed]; tube Ø5.12/Ø8.12 from 13.00 unchanged, no shoulder [Ed]",
             f"Lip {p['lip_t']:.1f} thick ({p['z_lip0']:.2f}–{p['z_top']:.2f}), top flush with the glass; out to the big knob OD, on top of it",
             f"Web {p['web_t']:.1f} under the screen cup ({p['run']:.1f} [A] gap); bore Ø{p['bore_d']:.2f} from {p['z_bore0']:.2f} round the holder boss",
             *STRUCT, (MAGNET, dict(color="#b000b0")), f"Lip sits {p['run']:.1f} [A] above the big knob top face (knob v0.6 has no raised rim now)",
             "Axial location of the dial TBC (no shoulder on the tube [Ed])"]
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        sh.note("plan", sb[1] + 14, sb[3] - i * 3.0, l, 8 if i == 0 else 6.5, **kw)
    title = "Control dial — v0.5, 2026-10-31"
    sub = [f"4 mm lip out to Ø48 on top of the big knob; magnet in the lip underside.", "[Ed] = Ed, [A] = assumed.",
           "Third-angle · mm · z-up: top view above, section A-A front"]
    sh.dxf(os.path.join(HERE, "control-dial.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "control-dial-drawing.png"), title, sub)
    print({k: round(v, 3) for k, v in p.items() if isinstance(v, float)}, "vol", round(d.volume))
