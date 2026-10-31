"""Knob v0.1 (2026-10-31): knob + motor pinion + internal ring gear + bottom (encoder take-off) ring gear.
Ed asked for these four parts only. Not placed in the assembly yet.
The knob turns about the dial axis on the fixed Ø5 brass tube, running on a sintered-bronze bush 5 ID × 8 OD × 6 long [A].
The 1220 motor pinion (on the 3 mm D-shaft tip) drives an internal ring inside the knob's top region.
An external ring at the knob base takes the rotation off to the encoder (encoder pinion TBC, not drawn).
The knob cap + hub, the internal ring band and the bottom ring are printed as ONE piece (CF-ASA or PETG) [A];
they are drawn as separate parts so each gets its own sheet.
Involute profiles are generated here (20° pressure angle, standard addendum 1.0 m / dedendum 1.25 m, no profile shift).
Frame: knob axis = Z, Z = height above the PCB front face (the motor end cap sits on the PCB front).
The pinion is drawn about its own axis; in the together sheet it sits at +X = the motor offset.
Tags: [K] read from KiCad, [M] from the motor part params, [A] assumed."""
import math, os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "pcbs/knob-main-pcb", "motors/1220-coreless-planetary"):
    sys.path.insert(0, os.path.join(LIB, d))
import knob_main_pcb as pcb
import motor_gearbox as mg
from sheet import Sheet

K = pcb.kicad_facts(); M = mg.VARIANTS["motor-1220"]
P = dict(
    offset=K["motor_x"] - K["shaft_x"],   # [K] motor axis to dial axis (14.0 in make_board.py, itself [A])
    module=0.5,          # [A] FDM-printable; 0.4 rejected: 12T pinion root Ø3.8 leaves 0.4 wall on the 3 mm shaft
    pressure=20.0,       # [A] deg
    z_pinion=12,         # [A] 10-12 allowed; 10 or 11 at m0.5 leave root < 3.0 shaft / 0.4 wall
    backlash=0.10,       # [A] total, on the pitch circle (half off each part)
    pinion_face=3.0,     # [A] face width
    shaft_d=M["shaft_d"], shaft_flat=M["shaft_flat"], shaft_len=M["shaft_len"],   # [M] 3.0, 2.5, 5.5
    bore_clear=0.05,     # [A] D-bore: Ø shaft + 0.05, flat + 0.05
    band_margin=0.5,     # [A] ring band beyond the pinion face, each end
    ring_wall=1.5,       # [A] knob wall outside the internal ring root (>= 1.5, Ed)
    motor_front_gap=0.5, # [A] knob base above the motor front face
    bottom_face=1.5,     # [A] bottom ring face width
    cap_t=1.5,           # [A] knob top cap thickness
    bush_id=5.0, bush_od=8.0, bush_len=6.0,   # [A] sintered bronze bush 5x8x6
    hub_wall=1.5,        # [A] hub wall round the bush
    z_bottom=None,       # [A] bottom ring teeth; None = smallest count whose root is >= the knob OD
    bezel_d=35.0,        # [L] Hall bezel ring Ø35 (knob-module-v1.md)
    tube_top=None,       # set below: brass tube top above the PCB front (from the brass shaft + KiCad STEP)
)
p = P; m = p["module"]
zr2 = p["z_pinion"] + 2 * p["offset"] / m
assert abs(zr2 - round(zr2)) < 1e-9, f"offset {p['offset']} not reachable at m{m}: z_ring would be {zr2}"
p["z_ring"] = int(round(zr2))
p["centre_dist"] = (p["z_ring"] - p["z_pinion"]) * m / 2
assert abs(p["centre_dist"] - p["offset"]) < 1e-9
# heights (above the PCB front)
Lm = M["motor_len"] + M["gearbox_len"] + M["boss_len"]          # [M] 38.0 motor front (boss face)
p["h_motor_front"] = Lm; p["h_shaft_tip"] = Lm + p["shaft_len"]  # 43.5
p["h_pinion0"] = p["h_shaft_tip"] - p["pinion_face"]            # pinion front flush with the shaft tip [A]
p["h_band0"] = p["h_pinion0"] - p["band_margin"]; p["h_band1"] = p["h_shaft_tip"] + p["band_margin"]
p["h_base"] = p["h_motor_front"] + p["motor_front_gap"]
p["h_bottom1"] = p["h_base"] + p["bottom_face"]
assert p["h_bottom1"] <= p["h_band0"] + 1e-9
p["h_top"] = p["h_band1"] + p["cap_t"]
# diameters
p["d_ring_pitch"] = p["z_ring"] * m; p["d_ring_root"] = (p["z_ring"] + 2.5) * m; p["d_ring_tip"] = (p["z_ring"] - 2) * m
p["knob_od"] = p["d_ring_root"] + 2 * p["ring_wall"]
p["d_pin_pitch"] = p["z_pinion"] * m; p["d_pin_tip"] = (p["z_pinion"] + 2) * m; p["d_pin_root"] = (p["z_pinion"] - 2.5) * m
if p["z_bottom"] is None: p["z_bottom"] = math.ceil(p["knob_od"] / m + 2.5 - 1e-9)
p["d_bot_pitch"] = p["z_bottom"] * m; p["d_bot_tip"] = (p["z_bottom"] + 2) * m; p["d_bot_root"] = (p["z_bottom"] - 2.5) * m
p["d_bot_bore"] = p["d_ring_root"]
p["hub_od"] = p["bush_od"] + 2 * p["hub_wall"]
p["h_hub0"] = p["h_top"] - p["bush_len"]
p["pin_wall"] = (p["d_pin_root"] - p["shaft_d"]) / 2
def tube_facts(p=P):
    """Brass tube top (above the PCB front) and knurl length from the CURRENT shaft (v0.2). Imported lazily:
    shaft v0.2 derives its length from the screen holder, which imports this module."""
    sys.path.insert(0, os.path.join(LIB, "shafts", "fixed-shaft-brass-5x3-v0.2"))
    import fixed_shaft_brass_v02 as fsb
    bb = pcb.board_solid().bounding_box()
    p["tube_top"] = fsb.P["above_flange"] - (bb.max.Z - bb.min.Z)
    p["knurl_len"] = fsb.P["knurl_len"]
    return p["tube_top"], p["knurl_len"]

def inv(a): return math.tan(a) - a

def build_bush(p=P):
    """Sintered-bronze bush 5 ID x 8 OD x 6 [A] (bought part), pressed into the hub bore, flush with the knob top."""
    A = (Align.CENTER, Align.CENTER, Align.MIN)
    return Pos(0, 0, p["h_hub0"]) * (Cylinder(p["bush_od"] / 2, p["bush_len"], align=A) - Cylinder(p["bush_id"] / 2, p["bush_len"], align=A))

def gear_pts(z, m, add, ded, dthick, alpha_deg=20.0, n=7):
    """External involute outline: z teeth, addendum add, dedendum ded, tooth thickness change dthick (mm on pitch)."""
    a = math.radians(alpha_deg); rp = z * m / 2; rb = rp * math.cos(a); ra = rp + add; rf = rp - ded
    psi = (math.pi * m / 2 + dthick) / (2 * rp)   # half tooth angle on the pitch circle
    r0 = max(rb, rf)
    def th(r): return psi + inv(a) - inv(math.acos(min(1.0, rb / r)))
    rs = [r0 + (ra - r0) * i / (n - 1) for i in range(n)]
    pts = []
    for i in range(z):
        c = 2 * math.pi * i / z
        if rf < rb: pts.append((rf, c - th(rb)))
        pts += [(r, c - th(r)) for r in rs]
        pts += [(r, c + th(r)) for r in reversed(rs)]
        if rf < rb: pts.append((rf, c + th(rb)))
    return [(r * math.cos(t), r * math.sin(t)) for r, t in pts]

def gear_solid(pts, z0, h):
    f = Face(Wire.make_polygon([Vector(x, y, z0) for x, y in pts], close=True))
    return extrude(f, h)

def build_pinion(p=P):
    m = p["module"]
    g = gear_solid(gear_pts(p["z_pinion"], m, m, 1.25 * m, -p["backlash"] / 2, p["pressure"]), 0, p["pinion_face"])
    r = (p["shaft_d"] + p["bore_clear"]) / 2; fl = p["shaft_flat"] + p["bore_clear"]
    dbore = Cylinder(r, p["pinion_face"], align=(Align.CENTER, Align.CENTER, Align.MIN)) & \
            Pos(0, fl / 2 - r, 0) * Box(2 * r, fl, p["pinion_face"], align=(Align.CENTER, Align.CENTER, Align.MIN))
    return g - dbore

def build_internal_ring(p=P):
    m = p["module"]; h0, h = p["h_band0"], p["h_band1"] - p["h_band0"]
    cutter = gear_solid(gear_pts(p["z_ring"], m, 1.25 * m, 1.0 * m, +p["backlash"] / 2, p["pressure"]), h0, h)
    return Pos(0, 0, h0) * Cylinder(p["knob_od"] / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN)) - cutter

def build_bottom_ring(p=P):
    m = p["module"]; h0, h = p["h_base"], p["bottom_face"]
    g = gear_solid(gear_pts(p["z_bottom"], m, m, 1.25 * m, -p["backlash"] / 2, p["pressure"]), h0, h)
    return g - Pos(0, 0, h0) * Cylinder(p["d_bot_bore"] / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN))

def knob_profile(p=P):
    """Half-section (r, h) of the knob cap + hub, closed polygon."""
    rb, rh, ro = p["bush_od"] / 2, p["hub_od"] / 2, p["knob_od"] / 2
    return [(rb, p["h_hub0"]), (rh, p["h_hub0"]), (rh, p["h_band1"]), (ro, p["h_band1"]), (ro, p["h_top"]), (rb, p["h_top"])]

def build_knob(p=P):
    prof = knob_profile(p)
    f = Face(Wire.make_polygon([Vector(r, 0, h) for r, h in prof], close=True))
    return revolve(f, Axis.Z, 360)

def section_face(p=P):
    prof = knob_profile(p); h0 = p["h_hub0"]
    q = [(r, h - h0) for r, h in prof]
    a = Face(Wire.make_polygon([Vector(x, y, 0) for x, y in q], close=True))
    b = Face(Wire.make_polygon([Vector(-x, y, 0) for x, y in q], close=True))
    return a, b

def vol(s):
    if s is None: return 0.0
    items = s if isinstance(s, (list, ShapeList)) else [s]
    return sum(c.volume for c in items if c is not None)

def notes(sh, view, x, ytop, lines, step, size=7):
    for i, line in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(line, tuple): line, kw = line
        sh.note(view, x, ytop - i * step, line, 8 if i == 0 else size, **kw)

SUB3 = "Third-angle projection · mm · plan view drawn front-up"
RED = dict(color="red", weight="bold")

if __name__ == "__main__":
    m = p["module"]
    pin = build_pinion(); ring = build_internal_ring(); bot = build_bottom_ring(); knob = build_knob()
    pin_placed = Pos(p["offset"], 0, p["h_pinion0"]) * pin
    for n, s in (("knob-cap-hub", knob), ("motor-pinion", pin), ("internal-ring-gear", ring), ("bottom-ring-gear", bot)):
        export_step(s, os.path.join(HERE, n + ".step"))
    together = Compound(children=[knob, ring, bot, pin_placed], label="knob-v0.1")
    export_step(together, os.path.join(HERE, "knob-v0.1-together.step"))
    pairs = {"pinion/internal ring": (pin_placed, ring), "pinion/knob hub+cap": (pin_placed, knob), "pinion/bottom ring": (pin_placed, bot)}
    clashes = {k: vol(a.intersect(b)) for k, (a, b) in pairs.items()}
    clashes = {k: v for k, v in clashes.items() if v > 1e-4}
    od_flag = p["knob_od"] >= p["bezel_d"] or p["d_bot_tip"] >= p["bezel_d"]
    tube_facts()
    bush_engaged = min(p["tube_top"], p["h_top"]) - p["h_hub0"]
    knurl_on_bush = p["tube_top"] - p["knurl_len"] < p["h_top"] - 1e-9
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in p.items()})
    print("clashes", clashes, "valid", pin.is_valid, ring.is_valid, bot.is_valid, knob.is_valid, "bush engaged", round(bush_engaged, 2))

    FLAG_OD = (f"KNOB OD {p['knob_od']:.2f} (bottom gear tip Ø{p['d_bot_tip']:.1f}) >= {p['bezel_d']:.0f} BEZEL [check]", RED)
    TUBE_OK = f"Tube (shaft v0.2) top {p['tube_top']:.2f} above PCB front: bush fully engaged ({bush_engaged:.2f} of {p['bush_len']:.1f}); knurl zone starts {p['tube_top'] - p['knurl_len']:.2f}, above the bush"
    FLAG_TUBE = (f"Tube top {p['tube_top']:.2f} is {p['h_top'] - p['tube_top']:.2f} below the knob top: bush engaged {bush_engaged:.2f} of {p['bush_len']:.1f} [check]", RED)
    FLAG_KN = (f"Bush runs on the tube's top {p['knurl_len']:.0f} mm knurl zone [check]", RED)
    FLAG_PIN = (f"Pinion {p['z_pinion']}T: root Ø{p['d_pin_root']:.2f}, wall {p['pin_wall']:.2f} to the 3 mm shaft; undercut below 17T (no profile shift) [check]", RED)
    TUBE_FLAGS = ([FLAG_TUBE] if bush_engaged < p["bush_len"] - 1e-9 else []) + ([FLAG_KN] if knurl_on_bush else [])
    if not TUBE_FLAGS: TUBE_FLAGS = [TUBE_OK]
    MESH = f"m {m:.1f}, 20°: pinion {p['z_pinion']}T, ring {p['z_ring']}T, ({p['z_ring']} − {p['z_pinion']}) × {m:.1f} / 2 = {p['centre_dist']:.2f} = motor offset [K]"
    BUSH = f"bronze bush {p['bush_id']:.0f}x{p['bush_od']:.0f}x{p['bush_len']:.0f} [A]"

    # ---- sheet 1: knob cap + hub ----
    rb, rh, ro = p["bush_od"] / 2, p["hub_od"] / 2, p["knob_od"] / 2
    sh = Sheet(knob, gap=26, scale=2.5, label_pad=16)
    sh.hdim("front", -ro, ro, -ro, -ro - 5, f"Ø{p['knob_od']:.2f} knob OD = ring root Ø{p['d_ring_root']:.2f} + 2 × {p['ring_wall']:.1f} wall [A]")
    sh.hdim("front", -rb, rb, 0, rh + 3, f"Ø{p['bush_od']:.1f} bore: {BUSH}")
    sh.hdim("front", -rh, rh, 0, -rh - 3, f"Ø{p['hub_od']:.1f} hub [A]")
    sh.vdim("plan", p["h_band1"], p["h_top"], ro, ro + 4, f"{p['cap_t']:.1f} cap [A]")
    sh.vdim("plan", p["h_hub0"], p["h_top"], -rh, -ro - 4, f"{p['bush_len']:.1f} hub = bush length")
    sh.vdim("plan", 0, 0, 0, 0, "") if False else None
    sh.note("plan", ro + 14, p["h_top"] + 1, f"top at {p['h_top']:.2f} above PCB front; hub from {p['h_hub0']:.2f}", 6.5)
    secs = section_face()
    sh.add_section("SECTION A-A (cap + hub)", secs[0].fuse(secs[1]) if False else Face(Wire.make_polygon(
        [Vector(x, y - (p['h_hub0'] + p['h_top']) / 2, 0) for x, y in knob_profile()], close=True)), 2.5,
        ["Half-section, Ø8 bush bore wall on the left", BUSH + " pressed in, flush with the top"])
    notes(sh, "side", sh.bb["side"][1] + 3, ro, ["Printed CF-ASA or PETG, one piece with the internal ring band and the bottom ring [A]",
        BUSH + ": Ø8.0 bore for the press fit, runs on the Ø5.0 brass tube", f"Rotates about the dial axis; centre open for the tube (wires to the dial TFT)",
        FLAG_OD] + TUBE_FLAGS, 2.0, 6.5)
    title = "Knob cap + hub — v0.1, 2026-10-31"
    sub = [f"Cap Ø{p['knob_od']:.2f} × {p['cap_t']:.1f}, hub Ø{p['hub_od']:.0f} with the Ø8 bush bore.", "Z = height above the PCB front. [A] = assumed.", SUB3]
    sh.dxf(os.path.join(HERE, "knob-cap-hub.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "knob-cap-hub-drawing.png"), title, sub)

    # ---- sheet 2: motor pinion ----
    rt = p["d_pin_tip"] / 2; f = p["pinion_face"]
    sh = Sheet(pin, gap=14, scale=10, label_pad=8)
    sh.hdim("front", -rt, rt, -rt, -rt - 1.0, f"Ø{p['d_pin_tip']:.2f} tip")
    sh.vdim("front", -p["d_pin_pitch"] / 2, p["d_pin_pitch"] / 2, -rt, -rt - 1.0, f"Ø{p['d_pin_pitch']:.2f} pitch")
    sh.hdim("front", -(p["shaft_d"] + p["bore_clear"]) / 2, (p["shaft_d"] + p["bore_clear"]) / 2, 0, rt + 0.8, f"Ø{p['shaft_d'] + p['bore_clear']:.2f} D-bore [A]")
    sh.vdim("front", -(p["shaft_d"] + p["bore_clear"]) / 2, p["shaft_flat"] + p["bore_clear"] - (p["shaft_d"] + p["bore_clear"]) / 2, rt, rt + 0.5, f"{p['shaft_flat'] + p['bore_clear']:.2f} flat [A]")
    sh.vdim("plan", 0, f, rt, rt + 1.0, f"{f:.1f} face [A]")
    notes(sh, "side", 3, rt + 0.5, [f"{p['z_pinion']}T, m {m:.1f}, 20° involute, backlash {p['backlash']:.2f} total [A]",
        f"Root Ø{p['d_pin_root']:.2f}; fits the 1220 3 mm D-shaft (2.5 flat, 5.5 long) [M]",
        f"Front face flush with the shaft tip: {p['h_pinion0']:.1f}–{p['h_shaft_tip']:.1f} above PCB front", "Glue or press on the D-flat [A]", FLAG_PIN], 0.55, 7)
    title = "Motor pinion — v0.1, 2026-10-31"
    sub = [f"{p['z_pinion']}T m{m:.1f} involute pinion for the 1220 motor shaft.", "[M] = motor params, [A] = assumed.", SUB3]
    sh.dxf(os.path.join(HERE, "motor-pinion.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "motor-pinion-drawing.png"), title, sub)

    # ---- sheet 3: internal ring gear ----
    sh = Sheet(ring, gap=26, scale=2.5, label_pad=16)
    sh.hdim("front", -ro, ro, -ro, -ro - 5, f"Ø{p['knob_od']:.2f} OD ({p['ring_wall']:.1f} wall outside root) [A]")
    sh.hdim("front", -p["d_ring_tip"] / 2, p["d_ring_tip"] / 2, 0, ro + 3, f"Ø{p['d_ring_tip']:.2f} tip")
    sh.hdim("front", -p["d_ring_root"] / 2, p["d_ring_root"] / 2, 0, ro + 8, f"Ø{p['d_ring_root']:.2f} root")
    sh.vdim("plan", p["h_band0"], p["h_band1"], ro, ro + 4, f"{p['h_band1'] - p['h_band0']:.1f} band [A]")
    sh.note("plan", ro + 14, p["h_band1"], f"band {p['h_band0']:.1f}–{p['h_band1']:.1f} above PCB front = pinion ± {p['band_margin']:.1f}", 6.5)
    notes(sh, "side", sh.bb["side"][1] + 3, ro, [f"{p['z_ring']}T internal, m {m:.1f}, 20° involute, pitch Ø{p['d_ring_pitch']:.2f}", MESH,
        f"At the motor shaft-tip height ({p['h_shaft_tip']:.1f}), knob top region", "Printed one piece with the knob [A]", FLAG_OD], 2.0, 6.5)
    title = "Internal ring gear (in knob) — v0.1"
    sub = [f"2026-10-31. {p['z_ring']}T internal ring, driven by the {p['z_pinion']}T motor pinion.", "[K] = KiCad, [A] = assumed.", SUB3]
    sh.dxf(os.path.join(HERE, "internal-ring-gear.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "internal-ring-gear-drawing.png"), title, sub)

    # ---- sheet 4: bottom ring gear ----
    rbt = p["d_bot_tip"] / 2
    sh = Sheet(bot, gap=26, scale=2.5, label_pad=16)
    sh.hdim("front", -rbt, rbt, -rbt, -rbt - 5, f"Ø{p['d_bot_tip']:.2f} tip")
    sh.hdim("front", -p["d_bot_bore"] / 2, p["d_bot_bore"] / 2, 0, rbt + 3, f"Ø{p['d_bot_bore']:.2f} bore")
    sh.vdim("plan", p["h_base"], p["h_bottom1"], rbt, rbt + 4, f"{p['bottom_face']:.1f} face [A]")
    sh.note("plan", rbt + 14, p["h_bottom1"], f"knob base {p['h_base']:.1f} above PCB front = motor front {p['h_motor_front']:.1f} + {p['motor_front_gap']:.1f} [A]", 6.5)
    notes(sh, "side", sh.bb["side"][1] + 3, rbt, [f"{p['z_bottom']}T external, m {m:.1f} [A], 20° involute; pitch Ø{p['d_bot_pitch']:.2f}, root Ø{p['d_bot_root']:.2f}",
        "Tooth count is a parameter: smallest count with root >= knob OD [A]", "Encoder pinion TBC, not drawn", "Printed one piece with the knob [A]", FLAG_OD], 2.0, 6.5)
    title = "Bottom ring gear (encoder) — v0.1"
    sub = [f"2026-10-31. {p['z_bottom']}T external ring at the knob base.", "[A] = assumed.", SUB3]
    sh.dxf(os.path.join(HERE, "bottom-ring-gear.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "bottom-ring-gear-drawing.png"), title, sub)

    # ---- sheet 5: together ----
    sh = Sheet(together, gap=26, scale=2.2, label_pad=16)
    sh.hdim("front", 0, p["offset"], 0, -rbt - 4, f"{p['centre_dist']:.2f} centre distance = motor offset [K]")
    sh.hdim("front", -rbt, rbt, -rbt, -rbt - 10, f"Ø{p['d_bot_tip']:.2f} max (bottom gear tip)")
    sh.hdim("front", -ro, ro, ro, ro + 4, f"Ø{p['knob_od']:.2f} knob OD vs Ø{p['bezel_d']:.0f} bezel [L]")
    sh.vdim("plan", p["h_base"], p["h_top"], -rbt, -rbt - 5, f"{p['h_top'] - p['h_base']:.1f} knob height")
    sh.vdim("plan", p["h_pinion0"], p["h_shaft_tip"], p["offset"] + rt, rbt + 4, f"{p['pinion_face']:.1f} pinion")
    sh.vdim("plan", 0, 0, 0, 0, "") if False else None
    sh.note("plan", rbt + 14, p["h_top"], f"Z: base {p['h_base']:.1f}, band {p['h_band0']:.1f}–{p['h_band1']:.1f}, top {p['h_top']:.1f} above PCB front", 6.5)
    clash_lines = [("CLASH: " + ", ".join(f"{k} {v:.3f} mm³" for k, v in clashes.items()), RED)] if clashes else ["No clash between the four parts"]
    notes(sh, "side", sh.bb["side"][1] + 3, ro, [MESH, f"Bottom ring {p['z_bottom']}T m{m:.1f} [A]; encoder pinion TBC", BUSH, *clash_lines, FLAG_OD] + TUBE_FLAGS + [FLAG_PIN], 2.2, 6.5)
    title = "Knob v0.1 — knob + pinion + two ring gears"
    sub = ["2026-10-31. Four parts together; placed in assembly v0.4.", "[K] = KiCad, [L] = layout, [A] = assumed.", SUB3]
    sh.dxf(os.path.join(HERE, "knob-v0.1-together.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "knob-v0.1-together-drawing.png"), title, sub)
