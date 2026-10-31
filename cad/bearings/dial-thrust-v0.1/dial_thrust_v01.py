"""Dial thrust bearing v0.1 (2026-10-31). Ed: extend the control-dial tube (Ø5.12/Ø8.12, unchanged) down to the base cradle's
tube collar (top 8.0) and put an axial thrust bearing at the joint: a printed ball carrier (cage ring) holding Ø1.0 steel balls,
running in grooves in the dial tube's bottom face and the cradle collar's top face. The bore round the Ø5.0 brass stays clear.
Annulus available: dial tube face r 2.56–4.06 (1.5 wide), collar face r 2.60–4.60. Balls on PCD Ø6.80 [A] (ball centre r 3.40),
grooves r 2.85–3.95 in both faces (torus R 0.55 [A] = 55 % conformity, 0.25 deep). Ball centre 0.30 above the collar face,
dial tube bottom face 0.60 above it (8.60). 12 balls [A]: pitch 1.78 on the PCD, 0.68 web between Ø1.10 pockets (13 would leave 0.54).
Carrier: printed PETG/POM ring [A], ID Ø5.30 (0.15 radial to the brass), OD Ø8.60 (0.70 to the motor body at r 5.0),
0.40 thick [A], 8.10–8.50 (0.10 to each face), 12 x Ø1.10 through pockets. Option [A]: thin steel washers (e.g. 5.2 x 8 x 0.3)
in place of the printed grooves if PETG wear is an issue.
Frame: dial axis = Z, Z = height above the PCB front. Tags: [Ed] Ed, [A] assumed."""
import math, os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "knob/knob-v0.1", "knob/knob-v0.2", "knob/knob-v0.4", "control-dial/control-dial-v0.1"):
    sys.path.insert(0, os.path.join(LIB, d))
import knob_v04 as k4
KP = k4.P
P = dict(
    ball_d=1.0,          # [Ed] steel balls
    pcd=6.8,             # [A]
    n_balls=12,          # [A]
    groove_r=0.55,       # [A] groove torus minor radius (55 % conformity)
    ball_up=0.30,        # [A] ball centre above the collar face (groove depth 0.25)
    pocket_d=1.10,       # [A]
    cage_id=5.30, cage_od=8.60, cage_t=0.40,   # [A]
    brass_d=KP["brass_od"], tube_id=KP["dial_tube_id"], tube_od=KP["dial_tube_od"],
)
p = P
p["z_collar"] = KP["cradle_boss_top"]                 # 8.00 cradle tube collar top face
p["z_ball"] = p["z_collar"] + p["ball_up"]            # 8.30
p["z_tube0"] = p["z_ball"] + p["ball_up"]             # 8.60 dial tube bottom face
p["groove_depth"] = p["groove_r"] - p["ball_up"]      # 0.25
p["cage_z0"] = p["z_ball"] - p["cage_t"] / 2; p["cage_z1"] = p["z_ball"] + p["cage_t"] / 2
p["pitch"] = 2 * (p["pcd"] / 2) * math.sin(math.pi / p["n_balls"])   # chord 1.78
p["web"] = p["pitch"] - p["pocket_d"]
p["groove_in"] = p["pcd"] / 2 - p["groove_r"]; p["groove_out"] = p["pcd"] / 2 + p["groove_r"]
p["tube_face_margin_in"] = p["groove_in"] - p["tube_id"] / 2      # 0.29
p["tube_face_margin_out"] = p["tube_od"] / 2 - p["groove_out"]    # 0.11
p["cage_wall_in"] = p["pcd"] / 2 - p["pocket_d"] / 2 - p["cage_id"] / 2
p["cage_wall_out"] = p["cage_od"] / 2 - p["pcd"] / 2 - p["pocket_d"] / 2
assert p["web"] > 0.5 and p["cage_wall_in"] > 0.15 and p["tube_face_margin_out"] > 0.1
A = (Align.CENTER, Align.CENTER, Align.MIN)

def groove():
    """Torus cutting the grooves in both faces (subtract from the cradle and from the dial tube)."""
    return Pos(0, 0, p["z_ball"]) * Torus(p["pcd"] / 2, p["groove_r"])

def ball_xy(i): a = 2 * math.pi * i / p["n_balls"]; return (p["pcd"] / 2 * math.cos(a), p["pcd"] / 2 * math.sin(a))

def build_carrier():
    c = Pos(0, 0, p["cage_z0"]) * (Cylinder(p["cage_od"] / 2, p["cage_t"], align=A) - Cylinder(p["cage_id"] / 2, p["cage_t"], align=A))
    for i in range(p["n_balls"]):
        x, y = ball_xy(i); c -= Pos(x, y, p["cage_z0"]) * Cylinder(p["pocket_d"] / 2, p["cage_t"], align=A)
    return c

def build_balls():
    return Compound(children=[Pos(*ball_xy(i), p["z_ball"]) * Sphere(p["ball_d"] / 2) for i in range(p["n_balls"])])

def parts():
    return {"thrust carrier": build_carrier(), "thrust balls 12 x Ø1": build_balls()}

SUMMARY = (f"Dial thrust bearing: {p['n_balls']} × Ø{p['ball_d']:.1f} steel balls on PCD Ø{p['pcd']:.2f} [A] in grooves (R{p['groove_r']:.2f}, {p['groove_depth']:.2f} deep) "
           f"in the cradle collar top ({p['z_collar']:.2f}) and the dial tube bottom ({p['z_tube0']:.2f}); carrier Ø{p['cage_id']:.2f}×Ø{p['cage_od']:.2f}×{p['cage_t']:.2f} [A]")

if __name__ == "__main__":
    from sheet import Sheet
    sys.path.insert(0, os.path.join(LIB, "control-dial/control-dial-v0.1")); import bezel as b1
    RED = dict(color="red", weight="bold")
    c = build_carrier(); b = build_balls()
    export_step(c, os.path.join(HERE, "thrust-carrier.step"))
    tog = Compound(children=[c, b]); export_step(tog, os.path.join(HERE, "thrust-carrier-with-balls.step"))
    z0 = p["cage_z0"]
    for name, shape, items, title in (("thrust-carrier", Pos(0, 0, -z0) * c, {"carrier": Pos(0, 0, -z0) * c}, "Dial thrust ball carrier — v0.1, 2026-10-31"),
                                      ("thrust-carrier-with-balls", Pos(0, 0, -z0) * tog, {"carrier": Pos(0, 0, -z0) * c, "balls": Pos(0, 0, -z0) * b}, "Dial thrust bearing (carrier + 12 balls) — v0.1")):
        sh = Sheet(shape, gap=12, scale=8, label_pad=6)
        sh.set_front_section(b1.section_items(items), "SECTION A-A (through the dial axis)")
        t = p["cage_t"]; ro, ri = p["cage_od"] / 2, p["cage_id"] / 2
        sh.hdim("plan", -ro, ro, ro, ro + 0.8, f"Ø{p['cage_od']:.2f} OD [A]")
        sh.hdim("front", -ri, ri, 0, -0.8, f"Ø{p['cage_id']:.2f} ID [A]")
        sh.hdim("plan", -p["pcd"] / 2, p["pcd"] / 2, ro, ro + 0.4, f"PCD Ø{p['pcd']:.2f} [A]")
        sh.vdim("front", 0, t, ro, ro + 0.6, f"{t:.2f} thick [A]")
        sb = sh.bb["plan"]; sh.cut_line("plan", sb[0] - 0.4, sb[1] + 0.4, 0, +1, "A")
        lines = [f"{p['n_balls']} × Ø{p['pocket_d']:.2f} [A] pockets for Ø{p['ball_d']:.1f} steel balls [Ed], PCD Ø{p['pcd']:.2f} [A]; pitch {p['pitch']:.2f}, web {p['web']:.2f}",
                 f"Walls round the pockets: {p['cage_wall_in']:.2f} inside, {p['cage_wall_out']:.2f} outside [A]",
                 f"Sits {p['cage_z0']:.2f}–{p['cage_z1']:.2f} above the PCB front: {p['cage_z0'] - p['z_collar']:.2f} over the cradle collar top, {p['z_tube0'] - p['cage_z1']:.2f} under the dial tube",
                 f"ID clears the Ø{p['brass_d']:.1f} brass by {(p['cage_id'] - p['brass_d']) / 2:.2f}; OD {5.0 - ro:.2f} inside the motor body (r 5.0)",
                 f"Races: grooves R{p['groove_r']:.2f} × {p['groove_depth']:.2f} deep [A] at r {p['groove_in']:.2f}–{p['groove_out']:.2f} in the cradle collar top and the dial tube bottom",
                 (f"Groove {p['tube_face_margin_out']:.2f} from the dial tube OD, {p['tube_face_margin_in']:.2f} from its bore (1.5 face) [check]", RED),
                 ("Printed PETG/POM carrier 0.40 thick and steel balls on printed races: wear/brinelling TBC; option thin steel washers [A]", RED),
                 "Carries the dial + big knob axial load (knob via the MR128 bottom lip -> inner race on the dial tube)"]
        for i, l in enumerate(["NOTES"] + lines):
            kw = dict(weight="bold") if i == 0 else {}
            if isinstance(l, tuple): l, kw = l
            sh.note("plan", sb[1] + 1.2, sb[3] - i * 0.35, l, 8 if i == 0 else 6.5, **kw)
        sub = ["Printed ball cage for the control-dial tube / base-cradle collar joint.", "[Ed] = Ed, [A] = assumed.", "Third-angle · mm · z-up: top view above, section A-A front"]
        sh.dxf(os.path.join(HERE, name + ".dxf"), [title] + sub)
        sh.png(os.path.join(HERE, name + "-drawing.png"), title, sub)
    print({k: round(v, 3) if isinstance(v, float) else v for k, v in p.items()})
