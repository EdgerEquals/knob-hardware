"""Screen holder v0.3 (2026-10-31). Supersedes v0.2. Ed: fix the socket engagement to the full 6 mm.
Only change: the Ø7.0 socket boss is 0.30 longer downward (bottom 46.10 -> 45.80), so the Ø5.2 glue socket engages the
brass tube top by 6.00 (v0.2: 5.70). Possible because control dial v0.4 opens its bore to Ø7.30 from 45.50 (0.3 [A] below the boss).
Cup, floor, screen stack and glass top 56.80 unchanged. Frame: dial axis = Z, Z = height above the PCB front."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "knob/knob-v0.1", "holders/screen-holder-v0.1", "holders/screen-holder-v0.2", "control-dial/control-dial-v0.1"):
    sys.path.insert(0, os.path.join(LIB, d))
import screen_holder_v02 as h2

P = dict(h2.P); p = P
p["socket_spec"] = 6.0                                 # [A] spec (v0.1)
p["z0"] = p["z_socket_top"] - p["socket_spec"]         # 45.80 boss bottom
p["socket_len"] = p["z_socket_top"] - p["z0"]          # 6.00
p["height"] = p["z_rim"] - p["z0"]

def build_holder(p=P): return h2.build_holder(p)
def placed_parts(p=P): return h2.placed_parts(p)

if __name__ == "__main__":
    from sheet import Sheet
    import bezel as b1
    h = build_holder(); export_step(h, os.path.join(HERE, "screen-holder.step"))
    ro, rh, rl, rb = p["od"] / 2, p["pocket_hi_d"] / 2, p["pocket_lo_d"] / 2, p["boss_d"] / 2
    sh = Sheet(h, gap=34, scale=4, label_pad=16)
    sh.set_front_section(b1.section_items({"holder": h}), "SECTION A-A (through the dial axis)")
    sh.hdim("front", -ro, ro, p["z_rim"], p["z_rim"] + 2.5, f"Ø{p['od']:.2f} OD ({p['wall']:.1f} wall [A])")
    sh.hdim("front", -rb, rb, p["z0"], p["z0"] - 1.5, f"Ø{p['boss_d']:.1f} boss = Ø{p['socket_d']:.1f} socket + 2×{p['boss_wall']:.1f} [A]")
    sh.vdim("front", p["z0"], p["z_rim"], -ro, -ro - 2, f"{p['height']:.2f} holder")
    sh.vdim("front", p["z0"], p["z_socket_top"], ro, ro + 2, f"{p['socket_len']:.2f} socket engagement")
    sh.vdim("front", p["z_cup0"], p["z_floor"], ro, ro + 5, f"{p['floor_t']:.1f} floor [A]")
    sb = sh.bb["plan"]; sh.cut_line("plan", sb[0] - 2, sb[1] + 2, 0, +1, "A")
    lines = ["Printed PETG [A], FIXED: bonded on the brass tube top (Ø5.2 glue socket, 0.1 per side [A])",
             f"v0.3: boss bottom {p['z0']:.2f} (v0.2: 46.10): socket engagement {p['socket_len']:.2f} = spec [A]",
             f"Cup floor underside = tube top {p['tube_top']:.2f}; glass top {p['z_glass_top']:.2f} (unchanged)",
             f"Walls and floor {p['wall']:.1f} [A]; Ø{p['wire_d']:.0f} wire passage through the floor"]
    for i, l in enumerate(["NOTES"] + lines):
        sh.note("plan", sb[1] + 6, sb[3] - i * 1.3, l, 8 if i == 0 else 6.5, **(dict(weight="bold") if i == 0 else {}))
    title = "Screen holder — v0.3, 2026-10-31"
    sub = ["Full 6.0 socket engagement on the brass tube top.", "[A] = assumed.", "Third-angle · mm · z-up: top view above, section A-A front"]
    sh.dxf(os.path.join(HERE, "screen-holder.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "screen-holder-drawing.png"), title, sub)
    print({k: round(p[k], 3) for k in ("z0", "socket_len", "height", "od", "z_glass_top")})
