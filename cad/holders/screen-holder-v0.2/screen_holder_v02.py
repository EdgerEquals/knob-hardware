"""Screen holder v0.2 (2026-10-31). Supersedes v0.1. Ed: make the top piece that holds the screen and the microcontroller
thinner, so the control dial can be thicker near the axis.
Printed PETG [A], FIXED, bonded on the brass tube top. Walls and floor thinned to 0.8 [A] (practical printed minimum).
The solid Ø22.3 x 6 socket block of v0.1 becomes a slim socket boss (Ø5.2 socket + 0.9 wall [A] = Ø7.0) under a thin cup,
so the control dial fills the space round the boss. The cup floor sits ON the tube top (brass shaft v0.2 unchanged), which sets
the whole screen stack: the glass top drops from 58.80 (v0.7) to 56.80.
Frame: dial axis = Z, Z = height above the main PCB front. Tags: [S] screen source, [K] KiCad, [A] assumed."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "knob/knob-v0.1", "holders/screen-holder-v0.1"):
    sys.path.insert(0, os.path.join(LIB, d))
import knob_gears as kg
import screen_holder as h1

P = dict(h1.P)
p = P
p.update(
    wall=0.8,            # [A] was 1.0
    floor_t=0.8,         # [A] was 1.0
    boss_wall=0.9,       # [A] round the Ø5.2 glue socket
    boss_gap=0.3,        # [A] boss bottom above the control-dial body (dial turns ±10°, holder fixed)
    dial_run=0.3,        # [A] control-dial body above the big knob top (as v0.1/v0.2)
)
p["tube_top"] = h1.P["z_socket_top"]                  # brass shaft v0.2 top, 51.80 above the PCB front (unchanged)
p["z_dial0"] = kg.P["h_top"] + p["dial_run"]          # 45.80 control-dial body underside
p["z0"] = p["z_dial0"] + p["boss_gap"]                # 46.10 boss bottom
p["z_socket_top"] = p["tube_top"]                     # cup floor underside = tube top
p["socket_len"] = p["z_socket_top"] - p["z0"]          # 5.70 engagement
p["boss_d"] = p["socket_d"] + 2 * p["boss_wall"]      # 7.00
p["z_cup0"] = p["z_socket_top"]
p["z_floor"] = p["z_cup0"] + p["floor_t"]             # board seat
p["z_board_top"] = p["z_floor"] + p["board_t"]
p["z_screen0"] = p["z_board_top"] + p["comp_h"] + p["screen_gap"]
p["z_glass_top"] = p["z_screen0"] + p["screen_t"]
p["z_rim"] = p["z_glass_top"] - p["proud"]
p["od"] = p["pocket_hi_d"] + 2 * p["wall"]
p["height"] = p["z_rim"] - p["z0"]

def profile(p=P):
    rs, rw, rb, rl, rh, ro = p["socket_d"] / 2, p["wire_d"] / 2, p["boss_d"] / 2, p["pocket_lo_d"] / 2, p["pocket_hi_d"] / 2, p["od"] / 2
    return [(rs, p["z0"]), (rb, p["z0"]), (rb, p["z_cup0"]), (ro, p["z_cup0"]), (ro, p["z_rim"]), (rh, p["z_rim"]), (rh, p["z_screen0"]),
            (rl, p["z_screen0"]), (rl, p["z_floor"]), (rw, p["z_floor"]), (rw, p["z_socket_top"]), (rs, p["z_socket_top"])]

def build_holder(p=P):
    f = Face(Wire.make_polygon([Vector(r, 0, z) for r, z in profile(p)], close=True))
    return revolve(f, Axis.Z, 360)

def placed_parts(p=P):
    return h1.placed_parts(p)

if __name__ == "__main__":
    from sheet import Sheet
    sys.path.insert(0, os.path.join(LIB, "control-dial", "control-dial-v0.1")); import bezel as b1
    h = build_holder(); export_step(h, os.path.join(HERE, "screen-holder.step"))
    ro, rh, rl, rs, rb = p["od"] / 2, p["pocket_hi_d"] / 2, p["pocket_lo_d"] / 2, p["socket_d"] / 2, p["boss_d"] / 2
    sh = Sheet(h, gap=34, scale=4, label_pad=16)          # z-up layout: top view, section A-A front, side
    sh.set_front_section(b1.section_items({"holder": h}), "SECTION A-A (through the dial axis)")
    sh.hdim("front", -ro, ro, p["z_rim"], p["z_rim"] + 2.5, f"Ø{p['od']:.2f} OD = screen Ø{p['screen_d']:.2f} + 2×{p['screen_clear']:.1f} + 2×{p['wall']:.1f} wall [A]")
    sh.hdim("front", -rb, rb, p["z0"], p["z0"] - 1.5, f"Ø{p['boss_d']:.1f} boss = Ø{p['socket_d']:.1f} socket + 2×{p['boss_wall']:.1f} [A]")
    sh.vdim("front", p["z0"], p["z_rim"], -ro, -ro - 2, f"{p['height']:.2f} holder")
    sh.vdim("front", p["z0"], p["z_socket_top"], ro, ro + 2, f"{p['socket_len']:.2f} socket engagement")
    sh.vdim("front", p["z_cup0"], p["z_floor"], ro, ro + 5, f"{p['floor_t']:.1f} floor [A]")
    sh.hdim("plan", -rh, rh, 0, ro + 1.5, f"Ø{p['pocket_hi_d']:.2f} screen pocket")
    sh.hdim("plan", -rl, rl, 0, -ro - 1.5, f"Ø{p['pocket_lo_d']:.2f} board pocket")
    sb = sh.bb["plan"]; sh.cut_line("plan", sb[0] - 2, sb[1] + 2, 0, +1, "A")
    lines = ["Printed PETG [A], FIXED: bonded on the brass tube top (Ø5.2 glue socket, 0.1 per side [A])",
             f"Walls and floor thinned to {p['wall']:.1f} [A] (v0.1: 1.0); the solid socket block is now a Ø{p['boss_d']:.1f} boss",
             f"Cup floor underside = tube v0.2 top {p['tube_top']:.2f}; boss bottom {p['z0']:.2f} = control dial + {p['boss_gap']:.1f} [A]",
             f"Glass top {p['z_glass_top']:.2f} above the PCB front (v0.7: 58.80); Ø{p['wire_d']:.0f} wire passage through the floor",
             (f"Socket engagement {p['socket_len']:.2f} (v0.1 spec 6.0 [A]) [check]", dict(color="red", weight="bold"))]
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        sh.note("plan", ro + 8, ro - i * 1.3, l, 8 if i == 0 else 6.5, **kw)
    title = "Screen holder — v0.2, 2026-10-31"
    sub = ["Thinner: 0.8 walls/floor [A], slim socket boss.", "[S] = screen source, [A] = assumed.", "Third-angle projection · mm · z-up: top view above, section A-A front"]
    sh.dxf(os.path.join(HERE, "screen-holder.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "screen-holder-drawing.png"), title, sub)
    print({k: round(v, 3) for k, v in p.items() if isinstance(v, float)})
