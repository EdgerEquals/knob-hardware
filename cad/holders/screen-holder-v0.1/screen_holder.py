"""Screen holder v0.1 (2026-10-31): printed cup (CF-ASA or PETG), FIXED (does not rotate), bonded onto the knurled
top of the fixed brass tube. It holds the round adapter board; the 0.71" round TFT sits on top, glass flush with the rim.
The knob turns around and below it: the holder sits above the knob cap/hub with a running clearance.
Frame: dial axis = Z, Z = height above the main PCB front face (same as knob/knob-v0.1).
Tags: [K] KiCad, [S] screen source, [A] assumed; heights from knob v0.1, screen and adapter-board parameters."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "knob/knob-v0.1", "displays/tft-0.71-round-gc9d01", "pcbs/screen-adapter"):
    sys.path.insert(0, os.path.join(LIB, d))
import knob_gears as kg
import tft_071_round as scr
import screen_adapter as ad

S, K, A = scr.P, kg.P, ad.F
P = dict(
    knob_top=K["h_top"],          # knob v0.1 top (cap and hub) 45.5 above the PCB front
    run_clear=0.3,                # [A] holder bottom above the knob top (knob turns, holder fixed)
    tube_od=5.0,                  # brass tube (shaft v0.2)
    glue_gap=0.1,                 # [A] per side: socket Ø = tube + 0.2
    socket_len=6.0,               # [A] engagement on the knurled tube top
    wire_d=3.0,                   # central wire passage = tube bore
    floor_t=1.0,                  # [A] floor between the socket and the board pocket
    board_d=A["diameter"], board_t=A["thickness"],   # [K] adapter board Ø15.5 × 1.0
    board_clear=0.2,              # [A] per side, board pocket
    comp_h=max(h for _, _, h in ad.ENVELOPES.values()),   # [A] tallest part on the board (J1 1.0)
    screen_gap=0.3,               # [A] components to the screen back
    screen_d=S["bl_d"], screen_t=S["t_total"],        # [S] Ø20.12 × 1.90
    screen_clear=0.1,             # [A] per side, screen pocket
    proud=0.0,                    # [A] glass above the rim (0 = flush)
    wall=1.0,                     # [A] outside the screen pocket
    tail_slot_z=0.35,             # [A] tail lower face above the board front (FPC connector slot)
)
p = P
p["z0"] = p["knob_top"] + p["run_clear"]
p["socket_d"] = p["tube_od"] + 2 * p["glue_gap"]
p["z_socket_top"] = p["z0"] + p["socket_len"]          # = tube top (shaft v0.2 derives its length from this)
p["z_floor"] = p["z_socket_top"] + p["floor_t"]
p["z_board_top"] = p["z_floor"] + p["board_t"]
p["z_screen0"] = p["z_board_top"] + p["comp_h"] + p["screen_gap"]
p["z_glass_top"] = p["z_screen0"] + p["screen_t"]
p["z_rim"] = p["z_glass_top"] - p["proud"]
p["pocket_lo_d"] = p["board_d"] + 2 * p["board_clear"]
p["pocket_hi_d"] = p["screen_d"] + 2 * p["screen_clear"]
p["od"] = p["pocket_hi_d"] + 2 * p["wall"]
p["height"] = p["z_rim"] - p["z0"]

def profile(p=P):
    rs, rw, rl, rh, ro = p["socket_d"] / 2, p["wire_d"] / 2, p["pocket_lo_d"] / 2, p["pocket_hi_d"] / 2, p["od"] / 2
    return [(rs, p["z0"]), (ro, p["z0"]), (ro, p["z_rim"]), (rh, p["z_rim"]), (rh, p["z_screen0"]), (rl, p["z_screen0"]),
            (rl, p["z_floor"]), (rw, p["z_floor"]), (rw, p["z_socket_top"]), (rs, p["z_socket_top"])]

def build_holder(p=P):
    f = Face(Wire.make_polygon([Vector(r, 0, z) for r, z in profile(p)], close=True))
    return revolve(f, Axis.Z, 360)

def placed_parts(p=P):
    """Screen, tail, adapter board and envelopes in the holder frame."""
    backing, glass = scr.build_screen()
    z_tail_low = p["z_floor"] + ad.board_solid().bounding_box().max.Z + p["tail_slot_z"]
    j1 = A["fps"]["J1"]; y_end = j1["y"] + ad.ENVELOPES[j1["name"]][1] / 2   # tail ends at the J1 entry face
    tail = scr.build_tail(drop=p["z_screen0"] - z_tail_low, y_end=y_end)
    T = Pos(0, 0, p["z_screen0"])
    board = Pos(0, 0, p["z_floor"]) * ad.board_solid()
    comps = [Pos(0, 0, p["z_floor"]) * c for c in ad.components()]
    return dict(backing=T * backing, glass=T * glass, tail=T * tail, board=board, comps=comps)

if __name__ == "__main__":
    from sheet import Sheet
    h = build_holder(); export_step(h, os.path.join(HERE, "screen-holder.step"))
    ro, rh, rl, rs, rw = p["od"] / 2, p["pocket_hi_d"] / 2, p["pocket_lo_d"] / 2, p["socket_d"] / 2, p["wire_d"] / 2
    sh = Sheet(h, gap=26, scale=4, label_pad=14)
    sh.hdim("front", -ro, ro, -ro, -ro - 3, f"Ø{p['od']:.2f} OD = screen Ø{p['screen_d']:.2f} + 2×{p['screen_clear']:.1f} + 2×{p['wall']:.1f} wall [A]")
    sh.hdim("front", -rh, rh, 0, ro + 2, f"Ø{p['pocket_hi_d']:.2f} screen pocket")
    sh.hdim("front", -rl, rl, 0, ro + 5, f"Ø{p['pocket_lo_d']:.2f} board pocket")
    sh.hdim("front", -rw, rw, 0, -rl + 1.5, f"Ø{p['wire_d']:.1f} wire passage")
    sh.vdim("plan", p["z0"], p["z_rim"], -ro, -ro - 3, f"{p['height']:.2f} holder")
    sh.vdim("plan", p["z0"], p["z_socket_top"], ro, ro + 3, f"{p['socket_len']:.1f} socket Ø{p['socket_d']:.1f} [A]")
    sh.vdim("plan", p["z_socket_top"], p["z_floor"], ro, ro + 7, f"{p['floor_t']:.1f} floor [A]")
    sh.vdim("plan", p["z_screen0"], p["z_rim"], ro, ro + 11, f"{p['z_rim'] - p['z_screen0']:.2f} screen pocket")
    sec = Face(Wire.make_polygon([Vector(r, z - (p["z0"] + p["z_rim"]) / 2, 0) for r, z in profile()], close=True))
    sh.add_section("SECTION A-A (half)", sec, 3, ["Axis 2.6 left of the socket wall", "Steps: socket, floor, board pocket, screen ledge"])
    lines = ["Printed CF-ASA or PETG; FIXED, epoxy-bonded on the knurled tube top (0.1 glue gap per side)",
             f"Bottom at {p['z0']:.1f} above PCB front = knob top {p['knob_top']:.1f} + {p['run_clear']:.1f} running clearance [A]",
             f"Socket top {p['z_socket_top']:.1f} = brass tube top (shaft v0.2)",
             f"Board pocket holds the Ø{p['board_d']:.1f} adapter board; screen sits on the {p['z_screen0']:.1f} step, glass flush [A]",
             ("COG ledge + folded tail stick out past the OD: needs a slot [check]", dict(color="red", weight="bold"))]
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        sh.note("plan", ro + 16, p["z_rim"] - i * 1.4, l, 8 if i == 0 else 6.5, **kw)
    title = "Screen holder — v0.1, 2026-10-31"
    sub = [f"Printed cup Ø{p['od']:.2f} × {p['height']:.2f}, fixed on the brass tube.", "Z = height above the PCB front. [A] = assumed.", "Third-angle projection · mm · plan view drawn front-up"]
    sh.dxf(os.path.join(HERE, "screen-holder.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "screen-holder-drawing.png"), title, sub)
    print({k: round(v, 3) if isinstance(v, float) else v for k, v in p.items()}, h.is_valid)
