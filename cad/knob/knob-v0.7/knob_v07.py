"""Big knob v0.7 (2026-10-31). Supersedes v0.6. Ed: "move the motor closer to our axis and remove the ring gear at the top and
have it drive the knob from the wall where the bearing is ... that way we can make our knob smaller."
- The 68T internal ring under the cap is removed. The knob's bearing hub (the wall round the MR128ZZ) now carries an EXTERNAL
  32T m0.5 spur gear (pitch Ø16.0, tip Ø17.0, root Ø14.75) from 39.60 to 44.00; the 12T motor pinion (unchanged) meshes on
  its outside at 40.5–43.5. Centre distance (32 + 12) x 0.5 / 2 = 11.0 = new motor offset [K] (KiCad v0.9, was 14.0).
  Why 32T: 31T (offset 10.75) leaves only 1.125 under the tooth root over the Ø12 bearing bore (< 1.2 [A]); 30T (10.5) puts the
  motor body 0.44 from the control-dial tube (< 0.5 [A]). 32T: 1.375 root wall, motor body 0.94 from the dial tube.
- Ratio knob:motor 32:12 = 2.667 (was 68:12 = 5.667): the knob turns 2.1x faster with 2.1x less torque for the same motor.
- Smaller knob: skirt ID 2 x (11.0 + 6.0 + 2.0) = 38.0 (2.0 to the motor body kept), OD 42.0 (2.0 wall), was 48.0.
  Bottom internal ring 90T -> 78T (tip Ø38.0 = skirt ID, root Ø40.25: 0.875 wall at the no-step OD, as before, flagged).
- Heights, bearing, hub bore and lip, 0.3 gaps, top face 52.50 unchanged from v0.6.
v0.6 notes: Big knob v0.6 (2026-10-31). Supersedes v0.5. Ed: drop the knob by the 4 mm control-dial thickness so the dial lip comes out
to the full Ø48 on top of it: the raised rim is gone; the knob top face is 52.50, 0.3 [A] under the dial lip (4.30 below the glass).
Ed: a skinnier bearing: MR128ZZ 8 x 12 x 3.5 [A] on the same Ø8 bore (control-dial tube Ø8.12 unchanged), hub Ø19.0 -> Ø15.0.
The dial hub's Ø11.3 face would overlap the MR128 outer race, so the dial bears on the inner race through a Ø9.2 collar and the
outer race is held in the knob by a bottom lip (ID Ø10.6 [A]) + press fit; top shoulder 0.05 only (dial hub clearance) [A].
v0.5 notes: Big knob v0.5 (2026-10-31). Supersedes knob v0.4.
Ed: back to the earlier arrangement: no tube the whole way down; the knob comes down only to a hub that holds a bearing near
the top; the control dial is only a ~4 mm lip now, so the knob itself is much thicker and comes up at the outside round the dial.
Bearing: 688ZZ 8 x 16 x 5 [A] (Ed: fully housed in the knob hub). Its inner race runs on the unchanged control-dial tube
Ø8.12 (0.12 press on the printed PETG tube [A]), outer race pressed into the knob hub Ø16.0 bore [A]. Axial [A]: inner race top
against the control-dial hub face (43.60), outer race under the knob's shoulder; the bottom is retained by the press fit/glue [A].
Chosen over MR128ZZ 8 x 12 x 3.5 (stiffer, wider support right under the dial hub) and over 5 mm-bore bearings (Ed: keep the
dial tube, so the bearing has to sit on its Ø8.12, not on the brass).
Kept: OD Ø48.0 with no step top to bottom, skirt (ID 44), 68T ring under the cap (40–44), 90T bottom ring (2–5), 12T pinion,
motor and encoder clearances. Frame: dial axis = Z, Z = height above the PCB front. Tags: [A] assumed, [Ed] Ed."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "knob/knob-v0.1", "knob/knob-v0.2", "knob/knob-v0.4", "control-dial/control-dial-v0.1", "control-dial/control-dial-v0.3",
          "control-dial/control-dial-v0.4", "control-dial/control-dial-v0.5", "control-dial/control-dial-v0.6", "holders/screen-holder-v0.1", "holders/screen-holder-v0.2", "holders/screen-holder-v0.3", "holders/screen-holder-v0.4"):
    sys.path.insert(0, os.path.join(LIB, d))
import knob_gears as kg
import knob_v02 as kv
import knob_v04 as k4
import control_dial_v06 as cd
import bezel as b1
RED, notes = kv.RED, kv.notes
DP = cd.P
P = dict(k4.P); p = P; m = p["module"]
p.update(
    brg="MR128ZZ", brg_d=8.0, brg_D=12.0, brg_B=DP["brg_B"],   # [A] 8 x 12 x 3.5
    lip_id=10.6, lip_t=0.5,  # [A] bottom lip under the outer race (MR128 outer race land ~Ø10.4–Ø12)
    hub_wall=1.5,            # [A] round the bearing
    run=DP["run"],           # 0.3 [A] to the control dial / magnet
    z_hub_gear=32,           # [A] external hub gear (see notes for 31T / 30T)
)
p["d_hg_pitch"] = p["z_hub_gear"] * m; p["d_hg_tip"] = (p["z_hub_gear"] + 2) * m; p["d_hg_root"] = (p["z_hub_gear"] - 2.5) * m
p["hg_root_wall"] = (p["d_hg_root"] - p["brg_D"]) / 2                        # 1.375 over the bearing bore
p["hg_cd"] = (p["z_hub_gear"] + p["z_pinion"]) * m / 2
assert abs(p["hg_cd"] - p["offset"]) < 1e-9, f"KiCad motor offset {p['offset']} != hub-gear centre distance {p['hg_cd']}"
p["ratio"] = p["z_hub_gear"] / p["z_pinion"]; p["ratio_old"] = 68 / 12
p["motor_to_dial_tube"] = (p["offset"] - kg.M["body_d"] / 2) - DP["tube_od"] / 2   # 0.94
p["brg_top"] = DP["z_hub0"]                       # 43.60 (inner race against the dial hub)
p["brg_bot"] = p["brg_top"] - p["brg_B"]          # 40.10
p["hub_od"] = p["d_hg_root"]                      # 14.75: gear root circle (teeth added outside)
p["z_hub0"] = p["brg_bot"] - p["lip_t"]           # 39.60 hub bottom
p["z_top"] = DP["z_lip0"] - p["run"]              # 52.50 knob top face (no rim), 0.3 under the dial lip
p["below_glass"] = DP["z_top"] - p["z_top"]       # 4.30
p["z_under_web"] = DP["z_web0"] - p["run"]        # 47.20
p["z_under_lip"] = DP["z_lip0"] - p["run"]        # 52.50
p["r_bore_hi"] = DP["hub_od"] / 2 + p["run"]      # 5.95 round the dial hub
o = p["run"] * 2 ** 0.5                           # 45° clearance offset
p["mag_gap"] = DP["z_mag0"] - p["z_top"]          # 0.30 magnet (in the dial lip underside) to the knob top
p["height"] = p["z_top"] - p["h_skirt0"]          # bottom ring underside to the rim top
p["face_hg"] = p["h_band1"] - p["z_hub0"]           # 4.40 hub gear face (pinion 3.0)
p["motor_gap_brg"] = p["z_hub0"] - DP["motor_front"]

def profile(p=P):
    rh, rD, rb, ri, ro, rL = p["hub_od"] / 2, p["brg_D"] / 2, p["r_bore_hi"], p["skirt_id"] / 2, p["skirt_od"] / 2, p["lip_id"] / 2
    rh_d, g, rw, f = DP["hub_od"] / 2, DP["gusset"], DP["r_web"], DP["lip_fillet"]
    zg = DP["z_web0"] - g                          # dial gusset start (46.0)
    z_b = zg + (rb - rh_d) - o                      # knob bore meets the offset gusset line (45.88)
    r_w = rh_d + g + o + (p["z_under_web"] - DP["z_web0"])   # offset gusset line at z_under_web
    r_s = rw + p["run"]                             # 14.30 beside the dial web
    zl = DP["z_lip0"] - f                           # dial lip fillet start (51.80)
    z_l = zl - o + (r_s - rw - 0)                   # offset lip-fillet line at r_s
    r_l = rw + f + o - (DP["z_lip0"] - p["z_under_lip"])
    return [(rL, p["z_hub0"]), (rh, p["z_hub0"]), (rh, p["h_band1"]), (ri, p["h_band1"]), (ri, p["h_bi1"]), (ro, p["h_bi1"]),
            (ro, p["z_under_lip"]), (r_l, p["z_under_lip"]), (r_s, z_l), (r_s, p["z_under_web"]),
            (r_w, p["z_under_web"]), (rb, z_b), (rb, p["brg_top"]), (rD, p["brg_top"]), (rD, p["brg_bot"]), (rL, p["brg_bot"])]

def build_hub_teeth(p=P):
    g = kg.gear_solid(kg.gear_pts(p["z_hub_gear"], m, m, 1.25 * m, -p["backlash"] / 2, p["pressure"]), p["z_hub0"], p["face_hg"])
    g = Rot(0, 0, 180.0 / p["z_hub_gear"]) * g    # half a tooth: a space faces the pinion tooth on the +X line (pinion D-flat as the motor shaft)
    return g - Pos(0, 0, p["z_hub0"]) * Cylinder(p["d_hg_root"] / 2 - 0.02, p["face_hg"], align=(Align.CENTER, Align.CENTER, Align.MIN))

def build_knob(p=P):
    body = revolve(Face(Wire.make_polygon([Vector(r, 0, z) for r, z in profile(p)], close=True)), Axis.Z, 360)
    return body + build_hub_teeth(p)

def build_bearing(p=P):
    A = (Align.CENTER, Align.CENTER, Align.MIN)
    return Pos(0, 0, p["brg_bot"]) * (Cylinder(p["brg_D"] / 2, p["brg_B"], align=A) - Cylinder(DP["tube_od"] / 2, p["brg_B"], align=A))   # bore drawn at the pressed size (tube OD)

def parts(p=P):
    return {"knob body (cap+skirt+hub gear)": build_knob(p), "knob bearing MR128ZZ": build_bearing(p),
            "bottom internal ring": kv.build_bottom_internal_ring(p),
            "pinion": Pos(p["offset"], 0, p["h_pinion0"]) * kg.build_pinion()}

BRG = f"Bearing {P['brg']} {P['brg_d']:.0f} × {P['brg_D']:.0f} × {P['brg_B']:.1f} [A], fully housed in the knob hub; inner race on the control-dial tube Ø{DP['tube_od']:.2f} (0.12 press [A])"
FLAG_WALL = (f"{P['z_bot_int']}T bottom ring (tip Ø{P['d_bi_tip']:.1f} = skirt ID, 2 mm motor clearance): wall outside the root only {P['bot_wall']:.3f} [A] at the no-step Ø{P['skirt_od']:.0f} [check]", RED)
DRIVE = (f"Drive: 12T pinion on the motor → {P['z_hub_gear']}T m{P['module']:.1f} external gear on the bearing hub, centre distance {P['hg_cd']:.2f} = motor offset [K]; "
         f"ratio {P['ratio']:.3f} (was 68:12 = {P['ratio_old']:.3f})")
FLAG_DRIVE = (f"Hub gear root wall {P['hg_root_wall']:.3f} over the Ø{P['brg_D']:.0f} bearing press bore; 2.1× less knob torque than v0.6 [check]", RED)

if __name__ == "__main__":
    import itertools
    from sheet import Sheet
    pr = parts(); body = pr["knob body (cap+skirt+hub gear)"]
    export_step(body, os.path.join(HERE, "knob-body.step"))
    tog = Compound(children=list(pr.values()), label="knob-v0.7"); export_step(tog, os.path.join(HERE, "knob-v0.7-together.step"))
    cl = {}
    for (na, a), (nb, b) in itertools.combinations(pr.items(), 2):
        r = a.intersect(b); v = sum(c.volume for c in (r if isinstance(r, (list, ShapeList)) else [r]) if c is not None) if r is not None else 0
        if v > 1e-3: cl[f"{na} / {nb}"] = v
    print({k: round(p[k], 3) for k in ("brg_top", "brg_bot", "hub_od", "d_hg_tip", "hg_root_wall", "hg_cd", "ratio", "motor_to_dial_tube", "skirt_od", "z_bot_int", "z_under_web", "z_under_lip", "r_bore_hi", "mag_gap", "height", "motor_gap_brg")}, "clashes", cl)
    ro, rh, rD = p["skirt_od"] / 2, p["hub_od"] / 2, p["brg_D"] / 2
    for name, shape, title, items, extra in (
            ("knob-body", body, "Big knob body — v0.7, 2026-10-31", {"knob": body}, []),
            ("knob-v0.7-together", tog, "Big knob v0.7 — body + hub gear + MR128ZZ + 78T ring + pinion", pr,
             [f"m {m:.1f}: pinion {p['z_pinion']}T on the {p['z_hub_gear']}T hub gear (external), motor offset {p['offset']:.2f} [K]",
              *([(f"CLASH: {k} {v:.2f} mm³", RED) for k, v in cl.items()] or ["No clash between the knob parts"])])):
        sh = Sheet(shape, gap=34, scale=1.9, label_pad=26)
        sh.set_front_section(b1.section_items(items), "SECTION A-A (through dial and motor axes)")
        sh.hdim("front", -ro, ro, p["z_top"], p["z_top"] + 4, f"Ø{p['skirt_od']:.1f} OD, one diameter top to bottom [Ed]")
        sh.hdim("front", -p["d_hg_tip"] / 2, p["d_hg_tip"] / 2, p["z_hub0"], p["z_hub0"] - 3, f"Ø{p['d_hg_tip']:.1f} hub gear tip ({p['z_hub_gear']}T, root Ø{p['d_hg_root']:.2f})")
        sh.hdim("front", -rD, rD, p["z_hub0"], p["z_hub0"] - 7, f"Ø{p['brg_D']:.1f} bearing bore (press [A])")
        sh.vdim("front", p["h_skirt0"], p["z_top"], ro, ro + 5, f"{p['height']:.1f} knob height")
        sh.vdim("front", p["brg_bot"], p["brg_top"], -rh, -ro - 5, f"{p['brg_B']:.1f} bearing")
        sh.vdim("front", p["z_top"], DP["z_top"], ro, ro + 12, f"{p['below_glass']:.1f} below the glass (dial lip 4.0 + 0.3)")
        sb = sh.bb["plan"]; sh.cut_line("plan", sb[0] - 3, sb[1] + 3, 0, +1, "A")
        notes(sh, "plan", sb[1] + 14, sb[3], [BRG,
              f"Bearing {p['brg_bot']:.2f}–{p['brg_top']:.2f}: inner race top against the dial's Ø9.2 collar; outer race pressed in, on a Ø{p['lip_id']:.1f} bottom lip [A]",
              DRIVE, f"Hub gear {p['z_hub0']:.2f}–{p['h_band1']:.2f} ({p['face_hg']:.1f} face; pinion {p['h_pinion0']:.1f}–{p['h_pinion0'] + 3:.1f}); 68T internal ring removed [Ed]",
              f"Knob OD Ø{p['skirt_od']:.1f} (skirt ID {p['skirt_id']:.1f}: 2.0 to the motor body at offset {p['offset']:.1f}); motor body {p['motor_to_dial_tube']:.2f} from the dial tube", FLAG_DRIVE,
              f"Thick body: top {p['z_under_web']:.2f} under the dial web, {p['z_under_lip']:.2f} under the lip ({p['run']:.1f} [A] gaps)",
              f"No raised rim: top face {p['z_top']:.2f}, {p['below_glass']:.2f} below the glass; the Ø{DP['lip_od']:.0f} dial lip sits on top ({p['run']:.1f} [A]); magnet in the lip underside {p['mag_gap']:.2f} above",
              *extra, FLAG_WALL, "Printed one piece (CF-ASA or PETG) [A]"], 2.6)
        sub = ["2026-10-31. 32T gear on the bearing hub, 12T motor pinion at 11.0; OD Ø42, 78T bottom ring.", "[K] = KiCad, [Ed] = Ed, [A] = assumed.", "Third-angle · mm · z-up: top view above, section A-A front"]
        sh.dxf(os.path.join(HERE, name + ".dxf"), [title] + sub)
        sh.png(os.path.join(HERE, name + "-drawing.png"), title, sub)
