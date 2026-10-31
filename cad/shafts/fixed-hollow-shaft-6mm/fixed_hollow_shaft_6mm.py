"""Fixed hollow shaft 6 mm, two FDM pieces bonded together, v0.1 (2026-10-31). Supersedes fixed-hollow-shaft-4mm.
Ed: fixed on the dial axis, does not rotate; 8 x 36 AWG PTFE wires run down the bore and out the back.
  BASE: square flange (side = KiCad PCB width) glued flat to the PCB BACK face; Ø6 shaft rises through the PCB,
        ends in a Ø4 spigot with an anti-rotation flat. Bore runs through the flange.
  TOP:  Ø6 tube with a matching flatted socket that bonds onto the spigot.
Tags: [E] = Ed, [K] = read from the KiCad board, [A] = assumed.
Part-local axes: shaft axis = Z (forward = +Z, toward the panel); flange FRONT face (glued to PCB back) at Z = 0;
the anti-rotation flat faces +X. placed() gives the board-relative position for a later assembly."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "pcbs/knob-main-pcb"):
    sys.path.insert(0, os.path.join(LIB, d))
import knob_main_pcb as pcb

_board = pcb.board_solid().bounding_box(); _k = pcb.kicad_facts()
P = dict(
    pcb_width=_board.size.X,          # [K] 49.0, from the KiCad board (STEP export)
    axis_x=_k["shaft_x"], axis_y=_k["shaft_y"],   # [K] dial axis = H1 shaft hole on the KiCad board
    flange_t=2.0,        # [A]
    od=6.0,              # [E]
    bore=2.0,            # [E]
    lower_len=20.0,      # [A] shaft from flange front face to the spigot shoulder
    spigot_d=4.0,        # [A]
    spigot_len=7.0,      # [A]
    key_flat=0.5,        # [A] flat depth on one side of the spigot (anti-rotation)
    glue_gap=0.1,        # [A] per side
    top_len=25.0,        # [A]
    socket_extra_depth=0.2,   # [A] socket 7.2 deep for a 7.0 spigot
    chamfer=0.3,         # [A] 45 deg at bore ends
    pcb_hole=_k["shaft_hole"] or 6.2,   # [K] H1 NPTH on the KiCad board (6.2 [A])
)
P["flange_side"] = P["pcb_width"]                       # Ed: square, side = PCB width
P["socket_d"] = P["spigot_d"] + 2 * P["glue_gap"]       # 4.2
P["socket_depth"] = P["spigot_len"] + P["socket_extra_depth"]   # 7.2
NOTE_FDM = "FDM: CF-ASA or PETG; joint bonded with toughened epoxy; flange bonded to PCB back"

def _bore_edges(shape, r, zs):
    return [e for e in shape.edges().filter_by(GeomType.CIRCLE)
            if abs(e.radius - r) < 1e-6 and any(abs(e.center().Z - z) < 1e-6 for z in zs)]

def build_base(p=P):
    s, t = p["flange_side"], p["flange_t"]
    z_sh, z_top = p["lower_len"], p["lower_len"] + p["spigot_len"]
    A = (Align.CENTER, Align.CENTER, Align.MIN)
    body = Pos(0, 0, -t) * Box(s, s, t, align=A)
    body += Cylinder(p["od"] / 2, z_sh, align=A)
    sp = Pos(0, 0, z_sh) * Cylinder(p["spigot_d"] / 2, p["spigot_len"], align=A)
    xflat = p["spigot_d"] / 2 - p["key_flat"]
    sp -= Pos(xflat, 0, z_sh) * Box(p["spigot_d"], p["spigot_d"] * 2, p["spigot_len"], align=(Align.MIN, Align.CENTER, Align.MIN))
    body += sp
    body -= Pos(0, 0, -t) * Cylinder(p["bore"] / 2, t + z_top, align=A)
    return chamfer(_bore_edges(body, p["bore"] / 2, (-t, z_top)), p["chamfer"])

def build_top(p=P):
    A = (Align.CENTER, Align.CENTER, Align.MIN)
    body = Cylinder(p["od"] / 2, p["top_len"], align=A)
    sock = Cylinder(p["socket_d"] / 2, p["socket_depth"], align=A)
    xflat = p["spigot_d"] / 2 - p["key_flat"] + p["glue_gap"]          # 1.6: matches the spigot flat + gap
    fill = Pos(xflat, 0, 0) * Box(p["socket_d"], p["socket_d"] * 2, p["socket_depth"], align=(Align.MIN, Align.CENTER, Align.MIN))
    body -= (sock - fill)
    body -= Cylinder(p["bore"] / 2, p["top_len"], align=A)
    return chamfer(_bore_edges(body, p["bore"] / 2, (p["top_len"],)), p["chamfer"])

def build_pair(p=P):
    return build_base(p), Pos(0, 0, p["lower_len"]) * build_top(p)

def placed(shape, p=P):
    """Board placement (world axes of tools/sheet.py): flange front face on the PCB back face."""
    z_back = pcb.board_solid().bounding_box().min.Z   # back face of the KiCad STEP board
    return Pos(p["axis_x"], -p["axis_y"], z_back) * shape

def _notes(sh, view, x, ytop, lines, step):
    for i, line in enumerate(lines):
        sh.note(view, x, ytop - i * step, line, 8 if i == 0 else 7, weight="bold" if i == 0 else "normal")

SUB_COMMON = "Third-angle projection · mm · plan view drawn front-up · flat faces +X"

if __name__ == "__main__":
    from sheet import Sheet
    p = P; R = p["od"] / 2; rs = p["spigot_d"] / 2; rb = p["bore"] / 2; s2 = p["flange_side"] / 2
    t = p["flange_t"]; L1 = p["lower_len"]; Ls = p["spigot_len"]; zt = L1 + Ls; xf = rs - p["key_flat"]
    base = build_base(); top = build_top(); b2, t2 = build_pair()
    export_step(base, os.path.join(HERE, "shaft-base.step"))
    export_step(top, os.path.join(HERE, "shaft-top.step"))
    export_step(Compound(children=[b2, t2]), os.path.join(HERE, "shaft-6mm-assembled.step"))

    # ---- sheet 1: base ----
    sh = Sheet(base, gap=24, scale=2)
    sh.hdim("front", -s2, s2, -s2, -s2 - 6, f"{p['flange_side']:.1f} flange = PCB width [K]")
    sh.vdim("front", -s2, s2, -s2, -s2 - 6, f"{p['flange_side']:.1f} square")
    sh.note("front", -s2 + 1, s2 - 4, f"bore Ø{p['bore']:.1f} through flange [Ed]", 6.5)
    sh.note("front", -s2 + 1, s2 - 6.5, f"Ø{p['od']:.1f} shaft, Ø{p['spigot_d']:.1f} spigot with flat", 6.5)
    sh.vdim("plan", -t, 0, -s2, -s2 - 5, f"{t:.1f} [A]")
    sh.vdim("plan", 0, L1, -R, -R - 8, f"{L1:.1f} [A]")
    sh.vdim("plan", L1, zt, -rs, -R - 8, f"{Ls:.1f} [A]")
    sh.hdim("plan", xf, rs, zt, zt + 4, f"{p['key_flat']:.1f} flat [A]")
    sh.vdim("side", -R, R, -L1 + 0.01, -(zt + 6), f"Ø{p['od']:.1f} [Ed]")
    sh.vdim("side", -rs, rs, -zt, -(zt + 2.5), f"Ø{p['spigot_d']:.1f} [A]")
    sh.vdim("side", -rb, rb, t, t + 4, f"Ø{p['bore']:.1f} bore [Ed]")
    _notes(sh, "plan", s2 + 6, zt + 4, ["NOTES",
        f"1. {NOTE_FDM}",
        f"2. PCB needs a {p['pcb_hole']:.1f} mm hole on the dial axis for the shaft (now H1 on the PCB, v0.2);",
        "    check the flange vs. motor tabs and the back-side connectors",
        f"3. Bore chamfer {p['chamfer']:.1f} × 45° at both bore ends (flange back, spigot top) [A]",
        f"4. Flange front face (Z 0) glues to the PCB back; square centred on the dial axis [A]",
        f"5. Axis at board ({p['axis_x']:.2f}, {p['axis_y']:.1f}) = H1 shaft hole in KiCad [K]",
        "6. Wires (8 × 36 AWG PTFE) exit out the back of the flange"], 2.2)
    title = "Fixed hollow shaft 6 mm — BASE — v0.1, 2026-10-31"
    sub = ["Square flange + Ø6 shaft + flatted Ø4 spigot, bore Ø2 through.",
           "[Ed] = Ed, [K] = from KiCad board, [A] = assumed.", SUB_COMMON]
    sh.dxf(os.path.join(HERE, "shaft-base.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "shaft-base-drawing.png"), title, sub)

    # ---- sheet 2: top ----
    Lt = p["top_len"]; rk = p["socket_d"] / 2; ds = p["socket_depth"]; xs = xf + p["glue_gap"]
    sh = Sheet(top, gap=40, scale=4)
    sh.hdim("front", -R, R, -R, -R - 3, f"Ø{p['od']:.1f} [Ed]")
    sh.hdim("front", -rb, rb, R, R + 2.5, f"Ø{p['bore']:.1f} bore")
    sh.vdim("front", -rk, rk, -rk, -R - 2.5, f"Ø{p['socket_d']:.1f} socket")
    sh.vdim("plan", 0, Lt, -R, -R - 4, f"{Lt:.1f} [A]")
    sh.vdim("plan", 0, ds, R, R + 3, f"{ds:.1f} socket depth [A]")
    sh.hdim("plan", xs, rk, 0, -3, f"{rk - xs:.1f} flat")
    _notes(sh, "plan", R + 14, Lt, ["NOTES",
        f"1. {NOTE_FDM}",
        f"2. Socket Ø{p['socket_d']:.1f} × {ds:.1f} deep = spigot + {p['glue_gap']:.1f}/side glue gap [A]",
        f"3. Socket flat {xs:.1f} from axis matches the spigot flat ({xf:.1f}) + gap [A]",
        f"4. Bore Ø{p['bore']:.1f} through; {p['chamfer']:.1f} × 45° chamfer at the top bore [A]",
        "5. Socket end (Z 0) bonds onto the base shoulder"], 1.2)
    title = "Fixed hollow shaft 6 mm — TOP — v0.1, 2026-10-31"
    sub = ["Ø6 tube with flatted Ø4.2 socket, bore Ø2 through.",
           "[Ed] = Ed, [A] = assumed.", SUB_COMMON]
    sh.dxf(os.path.join(HERE, "shaft-top.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "shaft-top-drawing.png"), title, sub)

    # ---- sheet 3: assembled ----
    pair = Compound(children=[b2, t2]); H = L1 + Lt
    sh = Sheet(pair, gap=24, scale=2)
    sh.hdim("front", -s2, s2, -s2, -s2 - 6, f"{p['flange_side']:.1f} flange")
    sh.vdim("front", -s2, s2, -s2, -s2 - 6, f"{p['flange_side']:.1f}")
    sh.vdim("plan", -t, 0, -s2, -s2 - 5, f"{t:.1f}")
    sh.vdim("plan", 0, L1, -R, -R - 6, f"{L1:.1f} to joint")
    sh.vdim("plan", 0, H, -R, -R - 14, f"{H:.1f} from flange front face")
    sh.vdim("plan", -t, H, R, R + 8, f"{H + t:.1f} overall")
    sh.vdim("side", -R, R, -H + 0.01, -(H + 5), f"Ø{p['od']:.1f}")
    _notes(sh, "plan", s2 + 6, H, ["NOTES",
        f"1. {NOTE_FDM}",
        f"2. Joint at {L1:.0f} from the flange front face: spigot {p['spigot_d']:.0f} × {Ls:.0f} in socket {p['socket_d']:.1f} × {ds:.1f}, keyed by the flat",
        f"3. Bore Ø{p['bore']:.1f} runs through both pieces and out the flange back (8 × 36 AWG PTFE)",
        f"4. PCB has a {p['pcb_hole']:.1f} mm NPTH (H1) on the dial axis (PCB v0.2)",
        "5. Hidden lines show the spigot inside the socket"], 2.2)
    title = "Hollow shaft 6 mm — ASSEMBLED — v0.1, 2026-10-31"
    sub = ["Base + top bonded. Parts from fixed_hollow_shaft_6mm.py.",
           "[A] values as on the part sheets.", SUB_COMMON]
    sh.dxf(os.path.join(HERE, "shaft-6mm-assembled.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "shaft-6mm-assembled-drawing.png"), title, sub)
    print("ok", base.is_valid, top.is_valid, p["flange_side"], p["axis_x"], p["axis_y"])
