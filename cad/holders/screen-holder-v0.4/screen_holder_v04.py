"""Screen holder v0.4 (2026-10-31). Supersedes v0.3. Dial-centre power + data link (data over power, Ed): the M1.6 rod in the
brass tube clamps the screen adapter board straight onto the tube top, so the tube now runs up THROUGH the holder floor to the
board (tube top = board seat 52.60) and the Ø3 wire passage is gone. The holder stays bonded on the tube: Ø5.2 socket, now
through, 6.00 engagement (boss bottom 46.60). Cup, floor, board seat and screen stack unchanged: glass top 56.80 (flush).
Frame: dial axis = Z, Z = height above the PCB front. Tags: [A] assumed."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "knob/knob-v0.1", "holders/screen-holder-v0.1", "holders/screen-holder-v0.2", "control-dial/control-dial-v0.1"):
    sys.path.insert(0, os.path.join(LIB, d))
import screen_holder_v02 as h2
P = dict(h2.P); p = P
p["socket_spec"] = 6.0                                  # [A]
p["tube_top"] = p["z_floor"]                            # 52.60 = adapter board underside (clamped on the tube)
p["z_socket_top"] = p["tube_top"]
p["z0"] = p["z_socket_top"] - p["socket_spec"]          # 46.60: 6.0 engagement on the tube (through the floor)
p["socket_len"] = p["z_socket_top"] - p["z0"]
p["height"] = p["z_rim"] - p["z0"]

def profile(p=P):
    rs, rb, rl, rh, ro = p["socket_d"] / 2, p["boss_d"] / 2, p["pocket_lo_d"] / 2, p["pocket_hi_d"] / 2, p["od"] / 2
    return [(rs, p["z0"]), (rb, p["z0"]), (rb, p["z_cup0"]), (ro, p["z_cup0"]), (ro, p["z_rim"]), (rh, p["z_rim"]), (rh, p["z_screen0"]),
            (rl, p["z_screen0"]), (rl, p["z_floor"]), (rs, p["z_floor"])]
def build_holder(p=P):
    return revolve(Face(Wire.make_polygon([Vector(r, 0, z) for r, z in profile(p)], close=True)), Axis.Z, 360)
def placed_parts(p=P): return h2.placed_parts(p)

if __name__ == "__main__":
    from sheet import Sheet
    import bezel as b1
    h = build_holder(); export_step(h, os.path.join(HERE, "screen-holder.step"))
    ro, rb = p["od"] / 2, p["boss_d"] / 2
    sh = Sheet(h, gap=34, scale=4, label_pad=16)
    sh.set_front_section(b1.section_items({"holder": h}), "SECTION A-A (through the dial axis)")
    sh.hdim("front", -ro, ro, p["z_rim"], p["z_rim"] + 2.5, f"Ø{p['od']:.2f} OD ({p['wall']:.1f} wall [A])")
    sh.hdim("front", -rb, rb, p["z0"], p["z0"] - 1.5, f"Ø{p['boss_d']:.1f} boss, Ø{p['socket_d']:.1f} socket through")
    sh.vdim("front", p["z0"], p["z_rim"], -ro, -ro - 2, f"{p['height']:.2f} holder")
    sh.vdim("front", p["z0"], p["z_socket_top"], ro, ro + 2, f"{p['socket_len']:.2f} on the tube")
    sh.vdim("front", p["z_cup0"], p["z_floor"], ro, ro + 5, f"{p['floor_t']:.1f} floor [A]")
    sb = sh.bb["plan"]; sh.cut_line("plan", sb[0] - 2, sb[1] + 2, 0, +1, "A")
    lines = ["Printed PETG [A], FIXED: bonded on the brass tube (Ø5.2 socket, 0.1 per side [A]), now through the floor",
             f"Tube top {p['tube_top']:.2f} = board seat: the M1.6 rod clamps the adapter board onto the tube end (GND contact)",
             f"Socket engagement {p['socket_len']:.2f} (boss bottom {p['z0']:.2f}); wire passage removed (data over power)",
             f"Glass top {p['z_glass_top']:.2f} unchanged (flush); walls and floor {p['wall']:.1f} [A]"]
    for i, l in enumerate(["NOTES"] + lines):
        sh.note("plan", sb[1] + 6, sb[3] - i * 1.3, l, 8 if i == 0 else 6.5, **(dict(weight="bold") if i == 0 else {}))
    title = "Screen holder — v0.4, 2026-10-31"
    sub = ["Tube through the floor to the adapter board; 6.0 socket.", "[A] = assumed.", "Third-angle · mm · z-up: top view above, section A-A front"]
    sh.dxf(os.path.join(HERE, "screen-holder.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "screen-holder-drawing.png"), title, sub)
    print({k: round(p[k], 3) for k in ("z0", "socket_len", "tube_top", "z_board_top", "z_screen0", "z_glass_top")})
