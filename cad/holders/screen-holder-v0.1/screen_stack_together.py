"""Together sheet (2026-10-31): screen holder + 0.71" round TFT + adapter board + the top of the brass fixed tube (v0.2).
Only these parts; the main assembly is not updated. Frame: Z = height above the main PCB front (as knob v0.1)."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(LIB, "shafts", "fixed-shaft-brass-5x3-v0.2"))
import screen_holder as sh_mod
import fixed_shaft_brass_v02 as shaft
from sheet import Sheet

p = sh_mod.P; SP = shaft.P
SHOW_TUBE = 10.0   # [A] length of tube top shown below its top end

def vol(s):
    if s is None: return 0.0
    items = s if isinstance(s, (list, ShapeList)) else [s]
    return sum(c.volume for c in items if c is not None)

if __name__ == "__main__":
    h = sh_mod.build_holder(); parts = sh_mod.placed_parts()
    zt = p["z_socket_top"]; A = (Align.CENTER, Align.CENTER, Align.MIN)
    tube = Pos(0, 0, zt - SHOW_TUBE) * (Cylinder(SP["tube_od"] / 2, SHOW_TUBE, align=A) - Cylinder(SP["tube_id"] / 2, SHOW_TUBE, align=A))
    screen = [parts["backing"], parts["glass"], parts["tail"]]
    allp = [h, tube, parts["board"]] + parts["comps"] + screen
    asm = Compound(children=allp, label="screen-stack-v0.1")
    export_step(asm, os.path.join(HERE, "screen-stack-together.step"))
    pairs = {"holder/screen ledge": (h, parts["backing"]), "holder/glass": (h, parts["glass"]), "holder/tail": (h, parts["tail"]),
             "holder/board": (h, parts["board"]), "holder/tube": (h, tube), "board/tube": (parts["board"], tube),
             "tail/board parts": (parts["tail"], Compound(children=parts["comps"])), "screen/board parts": (parts["backing"], Compound(children=parts["comps"]))}
    for i, c in enumerate(parts["comps"]): pairs[f"holder/component {i+1}"] = (h, c)
    clashes = {k: vol(a.intersect(b)) for k, (a, b) in pairs.items()}
    clashes = {k: v for k, v in clashes.items() if v > 1e-4}
    print("clashes", {k: round(v, 3) for k, v in clashes.items()})

    ro = p["od"] / 2; ye = sh_mod.S["y_edge"]
    s = Sheet(layout="panel", shape=asm, gap=26, scale=3.5, label_pad=14)
    s.hdim("front", -ro, ro, -ro, -ro - 3, f"Ø{p['od']:.2f} holder OD")
    s.vdim("front", 0, ye, ro, ro + 3, f"{ye:.2f} axis to ledge edge [S]")
    s.vdim("plan", p["z0"], p["z_rim"], -ro, -ro - 3, f"{p['height']:.2f} holder")
    s.vdim("plan", zt - SHOW_TUBE, zt, SP["tube_od"] / 2, ro + 3, f"tube top at {zt:.1f} above PCB front")
    s.vdim("plan", p["z_screen0"], p["z_glass_top"], ro, ro + 3, f"{p['screen_t']:.2f} screen [S]")
    s.vdim("plan", p["z_floor"], p["z_board_top"], ro, ro + 7, f"{p['board_t']:.1f} board [K]")
    s.note("plan", ro + 14, p["z_rim"] + 1, f"Z: holder {p['z0']:.1f}–{p['z_rim']:.1f}, board {p['z_floor']:.1f}, screen {p['z_screen0']:.1f}, glass top {p['z_glass_top']:.1f}", 6.5)
    lines = ["Holder FIXED on the tube; the knob (v0.1, top 45.5) turns below it with 0.3 clearance [A]",
             f"Tube {SP['tube_len']:.2f} long (v0.2), top at the socket end; knurl = {SP['knurl_len']:.0f} mm socket engagement",
             f"Board Ø{p['board_d']:.1f} [K] in the Ø{p['pocket_lo_d']:.1f} pocket; wires up the Ø3.0 bore to W1"]
    if clashes:
        lines.append(("CLASH: " + ", ".join(f"{k} {v:.2f} mm³" for k, v in clashes.items()), dict(color="red", weight="bold")))
        lines.append(("Screen COG ledge and tail reach past the holder OD: slot or bigger OD needed [check]", dict(color="red", weight="bold")))
    else:
        lines.append("No clash")
    lines.append((f"Supplied tail is {sh_mod.S['tail_len_supplied']:.0f} mm: short-tail variant needed [check]", dict(color="red", weight="bold")))
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        s.note("side", s.bb["side"][1] + 3, ro - i * 1.8, l, 8 if i == 0 else 6.5, **kw)
    title = "Screen stack v0.1 — holder + TFT + board + tube top"
    sub = ["2026-10-31. Not in the main assembly yet.", "[K] = KiCad, [S] = screen source, [A] = assumed.", "Third-angle projection · mm · plan view drawn front-up"]
    s.dxf(os.path.join(HERE, "screen-stack-together.dxf"), [title] + sub)
    s.png(os.path.join(HERE, "screen-stack-together-drawing.png"), title, sub)
