# Study scripts (3 Nov 2026, layout v4). Inputs are slices pickled by db_room.py / vb_room.py and windows from tools/pcb_windows.py
# (--ab-top 26.06 --no-mcu); pass the folder holding them as the first argument. Run from cad/knob-param with PYTHONPATH=.
# Proposed layout [Ed 3 Nov 09:47-10:07]: H7B0 off window D onto the main board under the joystick, two vertical boards
# carrying a top (joystick) board, A/B stopped at the grip-block line, jacks and USB-C lower (bottom wall slotted).
# Plan of the whole module (left) + section x = 5.75 through a middle jack, the USB-C and the chip (right). Sketch, not the model.
# Run from cad/knob-param:  PYTHONPATH=. python layout_fig.py <scratch dir> <out.png>
import sys, json
sys.path.insert(0, ".")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Patch
from matplotlib.lines import Line2D
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from knobparam.assembly.section_atlas import _parts
from knobparam.assembly.plan_sheet import cut, draw

SP, out = sys.argv[1], sys.argv[2]
D, JD, parts = _parts()
GONE = ("joystick: joystick cradle", "joystick: cradle locating", "joystick: socket 2x5", "joystick: header 2x5", "joystick: header pin", "MCU ")
keep = {n: s for n, s in parts.items() if not n.startswith(GONE)}
W = {k: Polygon(v) for k, v in json.load(open(f"{SP}/w_abcap.json")).items()}
W_old = {k: Polygon(v) for k, v in D["pcb_windows"].items()}

# ---- proposal numbers ----
CHIP = (0.0, 37.0); COURT = 17.2; BODY = 16.0
WALL_X, WALL_Y = 16.0, (26.5, 48.4); ENV = 1.5          # vertical boards: plane x = ±16 (pins 1.1 clear of the top corner notches), envelope ±1.5 [A]
Z_TOP = 30.0                                             # top board underside (today's joystick daughterboard)
JY_OLD, JY_NEW = D["jack_y"], -45.15                     # jack body top on the OLED lit-area bottom (-39.9)
JW, JH = D["jack_w"], D["jack_h"]
UY_OLD, UB_OLD = D["usb_xy"][1], D["usb_board"]
UB_NEW = (12.0, 5.5); UY_NEW = D["body_y0"] + UB_NEW[1] / 2       # board down to the rail strip (-56.4), wall slotted
ow, oh, _ = D["clear_oled"]; ox, oy = D["clear_oled_xy"]
act = box(ox - 35.05 / 2, oy + oh / 2 - 3.0 - 15.32, ox + 35.05 / 2, oy + oh / 2 - 3.0)
jacks_new = unary_union([box(x - JW / 2, JY_NEW - JH / 2, x + JW / 2, JY_NEW + JH / 2) for x in D["jack_xs"]])
seen = act.intersection(W["D"]).difference(jacks_new).area / act.area
springs = [(12.5, 42.1), (12.5, 39.1), (-12.5, 42.1), (-12.5, 39.1)]
holes = [(-2.0, -51.0), (2.0, -51.0)]

fig = plt.figure(figsize=(19, 13.5))
ax = fig.add_axes([0.02, 0.06, 0.43, 0.86]); ax2 = fig.add_axes([0.49, 0.30, 0.50, 0.60])
# ---------------- plan ----------------
px0, px1, py0, py1 = D["panel_x0"], -D["panel_x0"], D["panel_y0"], D["panel_y1"]
ax.add_patch(Rectangle((px0, py0), px1 - px0, py1 - py0, fc="#f4f8fa", ec="k", lw=0.8))
for y0_, y1_ in ((py0, D["body_y0"]), (D["body_y1"], py1)):
    ax.add_patch(Rectangle((px0, y0_), px1 - px0, y1_ - y0_, fc="#e3e3e3", ec="none", hatch="///", alpha=0.6))
ax.text(0, (py0 + D["body_y0"]) / 2 - 2.5, "rail strip: nothing behind the panel", ha="center", fontsize=7.5, color="#555")
ax.add_patch(Rectangle((-22.5, D["body_y0"]), 45, -53.5 - D["body_y0"], fc="#cfe3ea", ec="#7aa", lw=0.5))
ax.text(-21.5, D["body_y0"] + 0.6, "bottom wall (2.9)", fontsize=6.5, color="#477")
ax.add_patch(Rectangle((-D["pcb_x1"], D["pcb_y0"]), 2 * D["pcb_x1"], D["pcb_y1"] - D["pcb_y0"], fc="#cfe8cf", ec="#2a6b2a", lw=0.8))
for k, p in W_old.items():
    if k in ("A", "B"): ax.plot(*p.exterior.xy, color="#d01010", lw=0.7, ls=":")
for k, p in W.items():
    ax.fill(*p.exterior.xy, fc="white", ec="#d01010", lw=1.1)
    c = p.centroid; ax.text(c.x, c.y if k != "D" else -27.0, f"{k} {p.area:.0f}", ha="center", va="center", fontsize=7.5, color="#d01010")
ax.add_patch(Circle((0, 0), D["knob_od"] / 2, fc="none", ec="#1f77b4", lw=1.0, ls="--"))
ax.text(0, 0, "knob", ha="center", va="center", fontsize=8, color="#1f77b4")
ax.add_patch(Rectangle((-22.0, 26.1), 44.0, 55.2 - 26.1, fc="none", ec="k", lw=0.9, ls=(0, (2, 2))))
ax.text(0, 53.4, "joystick grip block above (hides what's under it, seen straight on)", ha="center", fontsize=6.8)
ax.add_patch(Rectangle((-17.5, WALL_Y[0]), 35.0, WALL_Y[1] - WALL_Y[0], fc="none", ec="#7b4fa0", lw=1.2, ls="--"))
ax.text(-17.0, WALL_Y[1] - 1.4, "top board (joystick), nests in a case cradle", fontsize=6.3, color="#4a2a66")
for s in (-1, 1):
    ax.add_patch(Rectangle((s * WALL_X - ENV, WALL_Y[0]), 2 * ENV, WALL_Y[1] - WALL_Y[0], fc="#c9b3e0", ec="none", alpha=0.8))
    ax.add_patch(Rectangle((s * WALL_X - 0.5, WALL_Y[0]), 1.0, WALL_Y[1] - WALL_Y[0], fc="#1e6b35", ec="none"))
ax.text(-WALL_X, WALL_Y[0] - 1.6, "vertical\nboard", ha="center", fontsize=7, color="#4a2a66")
ax.text(WALL_X, WALL_Y[0] - 1.6, "vertical\nboard", ha="center", fontsize=7, color="#4a2a66")
ax.plot([-WALL_X + 1.5, WALL_X - 1.5], [27.6, 27.6], color="#4a2a66", lw=1.6, ls="-."); ax.text(0, 28.0, "one standoff between the boards (z ~15)", ha="center", fontsize=6.3, color="#4a2a66")
ax.add_patch(Rectangle((CHIP[0] - COURT / 2, CHIP[1] - COURT / 2), COURT, COURT, fc="#ffe3bf", ec="#a05000", lw=0.8, ls="--"))
ax.add_patch(Rectangle((CHIP[0] - BODY / 2, CHIP[1] - BODY / 2), BODY, BODY, fc="#ffcf8a", ec="#a05000", lw=1.0))
ax.text(*CHIP, "H7B0\nLQFP100\n(main board front)", ha="center", va="center", fontsize=7.5)
for x, y in springs: ax.add_patch(Circle((x, y), 1.0, fc="#9aa3a8", ec="k", lw=0.4))
ax.text(12.5, 44.6, "hold-down\nsprings", ha="center", fontsize=6.3)
for x, y in D["corners"]: ax.add_patch(Circle((x, y), D["notch_r"], fc="#bbbbbb", ec="k", lw=0.4))
ax.add_patch(Rectangle((ox - ow / 2, oy - oh / 2), ow, oh, fc="none", ec="#1f77b4", lw=0.9, ls="--"))
ax.fill(*act.exterior.xy, fc="none", ec="#1f77b4", lw=1.6)
for x in D["jack_xs"]:
    ax.add_patch(Rectangle((x - JW / 2, JY_OLD - JH / 2), JW, JH, fc="none", ec="#777", lw=0.8, ls=":"))
    ax.add_patch(Rectangle((x - JW / 2, JY_NEW - JH / 2), JW, JH, fc="#262626", ec="k", lw=0.6, alpha=0.75))
    ax.add_patch(Circle((x, JY_NEW), D["jack_nut_d"] / 2, fc="none", ec="#bbb", lw=0.6))
ax.add_patch(Rectangle((-UB_OLD[0] / 2, UY_OLD - UB_OLD[1] / 2), UB_OLD[0], UB_OLD[1], fc="none", ec="#777", lw=0.8, ls=":"))
ax.add_patch(Rectangle((-UB_NEW[0] / 2, UY_NEW - UB_NEW[1] / 2), UB_NEW[0], UB_NEW[1], fc="#1e6b35", ec="k", lw=0.6))
ax.add_patch(Rectangle((-8.94 / 2, UY_NEW - 3.26 / 2), 8.94, 3.26, fc="#a9b0b6", ec="k", lw=0.5))
ax.text(0, UY_NEW, "USB-C", ha="center", va="center", fontsize=6.5)
ax.annotate(f"USB-C board down {UY_OLD - UY_NEW:.1f}\n(slot in the bottom wall)", xy=(-6.0, UY_NEW), xytext=(-24.0, -62.5), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.6))
ax.annotate(f"jacks down {JY_OLD - JY_NEW:.2f}:\nbody tops on the\nOLED lit-area edge", xy=(-17.25, JY_NEW + JH / 2), xytext=(-24.5, -30.5), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.6))
for x, y in holes: ax.add_patch(Circle((x, y), 0.9, fc="#c9a227", ec="k", lw=0.4))
ax.annotate("power wires straight down\nfrom the USB board (15 V, GND)", xy=(2.0, -51.0), xytext=(8.0, -59.0), fontsize=6.5, arrowprops=dict(arrowstyle="->", lw=0.5))
ax.set_xlim(px0 - 1, px1 + 1); ax.set_ylim(py0 - 1, py1 + 1); ax.set_aspect("equal"); ax.grid(True, lw=0.2)
ax.tick_params(labelsize=7); ax.set_xlabel("x (mm), looking at the panel face", fontsize=8); ax.set_ylabel("y (mm)", fontsize=8)
ax.set_title(f"Plan. Windows: A {W['A'].area:.0f} (was {W_old['A'].area:.0f}), B {W['B'].area:.0f} (was {W_old['B'].area:.0f}), "
             f"D {W['D'].area:.0f} (was {W_old['D'].area:.0f}).\nOLED lit area seen past the jacks {100 * seen:.0f}% (now 68%). "
             "Dotted = where things are today.", fontsize=9, loc="left")
# ---------------- section x = 5.75 ----------------
XS = 5.75
lay = cut(keep, "x", XS)
used = draw(ax2, lay, "", (D["panel_y0"] - 2, D["panel_y1"] + 2), (D["z_cover_out"] - 2, D["z_top"] + 2), xlabel="y (mm, up the panel)", ylabel="z (mm, PCB front = 0)")
ax2.add_patch(Rectangle((CHIP[1] - BODY / 2, 0), BODY, 1.6, fc="#ffcf8a", ec="#a05000", lw=1.0))
ax2.text(CHIP[1], 3.2, "H7B0", ha="center", fontsize=7)
ax2.add_patch(Rectangle((WALL_Y[0], 0), WALL_Y[1] - WALL_Y[0], Z_TOP, fc="none", ec="#7b4fa0", lw=1.3, ls="--"))
ax2.text((WALL_Y[0] + WALL_Y[1]) / 2, 22.5, f"vertical boards at x ±{WALL_X:g}\n(behind this plane), {WALL_Y[1] - WALL_Y[0]:.0f} × {Z_TOP:.0f}", ha="center", fontsize=7, color="#4a2a66")
zj0 = D["faceplate_z_back"] - D["jack_depth"]
ax2.add_patch(Rectangle((JY_NEW - JH / 2, zj0), JH, D["jack_depth"], fc="none", ec="k", lw=1.4))
ax2.text(JY_NEW, zj0 - 3.0, "jack, new", ha="center", fontsize=7)
ax2.add_patch(Rectangle((UY_NEW - UB_NEW[1] / 2, D["faceplate_z_back"] - 7.35 - 1.0), UB_NEW[1], 1.0, fc="#1e6b35", ec="k", lw=0.8))
ax2.add_patch(Rectangle((UY_NEW - 3.26 / 2, D["faceplate_z_back"] - 7.35), 3.26, 7.35, fc="none", ec="k", lw=1.2))
ax2.text(UY_NEW - 4.0, D["faceplate_z_back"] - 12.5, "USB-C, new", ha="center", fontsize=7)
ax2.plot([act.bounds[1], act.bounds[3]], [1.6, 1.6], color="#1f77b4", lw=3); ax2.text(-32, 3.0, "OLED lit area", fontsize=7, color="#1f77b4")
ax2.axvline(D["body_y0"], color="#888", lw=0.6, ls=":"); ax2.text(D["body_y0"] - 0.5, D["z_cover_out"] + 1, "rail strip", rotation=90, fontsize=6.5, ha="right", color="#666")
ax2.set_title(f"Section x = {XS:g} (through a middle jack, the USB-C and the chip), viewed from +x. Model as it stands with the printed cradle,\n"
              "its sockets and the window-D chip taken out; outlines = the proposal. The jack and USB-C in the model are at today's place.", fontsize=9, loc="left")
fig.legend(handles=[Patch(fc=c, label=l) for l, c in used.items()], loc="lower right", bbox_to_anchor=(0.99, 0.02), ncol=3, fontsize=7.5, frameon=False)
fig.suptitle("Proposed layout (sketch, nothing in the model changed): H7B0 under the joystick on two vertical boards + top board; "
             "jacks and USB-C lower", fontsize=12, x=0.01, ha="left")
fig.savefig(out, dpi=100); print("wrote", out, "lit seen", round(100 * seen, 1), "USB y", round(UY_NEW, 2))
