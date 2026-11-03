# Fresh block floorplan [Ed 3 Nov 11:04 "re-look at it before we build more"]: every circuit block placed on the main board
# (front + back), the two vertical boards, the top (joystick) board, a proposed jack board and the USB board. Block sizes [A].
# Run from cad/knob-param:  PYTHONPATH=. python floorplan_fig.py <scratch dir> <out.png>
import sys, json, math, pickle
sys.path.insert(0, ".")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Patch
from shapely.geometry import Polygon, box, Point
from knobparam.common import model

SP, out = sys.argv[1], sys.argv[2]
D = model.derive(model.default_params())
W = {k: Polygon(v) for k, v in json.load(open(f"{SP}/w_abcap.json")).items()}
freeb = pickle.load(open(f"{SP}/freeb.pkl", "rb"))["freeb"]
NOISE = {"digital": "#9ecae1", "noisy": "#fc9272", "quiet": "#a1d99b", "power": "#fdd0a2", "conn": "#d9d9d9", "fixed": "#bdbdbd"}
LEG = {"digital": "digital (MCU, flash, displays' logic)", "noisy": "noisy (motor drivers, LED switching)",
       "quiet": "quiet analog (CV, audio, sensors)", "power": "power conversion", "conn": "connectors / board links",
       "fixed": "placed by the mechanics (fixed)"}

def blk(ax, x, y, w, h, label, kind, fs=6.2, check=None):
    r = box(x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    ok = True if check is None else r.within(check)
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=NOISE[kind], ec="k" if ok else "red", lw=0.6 if ok else 1.6))
    ax.text(x, y, label, ha="center", va="center", fontsize=fs)
    return ok

def board(ax, title, back=False):
    ax.add_patch(Rectangle((-D["pcb_x1"], D["pcb_y0"]), 2 * D["pcb_x1"], D["pcb_y1"] - D["pcb_y0"], fc="#eef5ee", ec="#2a6b2a", lw=0.8))
    for k, p in W.items():
        ax.fill(*p.exterior.xy, fc="white", ec="#d01010", lw=0.8)
    for x, y in D["corners"]:
        ax.add_patch(Circle((x, y), D["notch_r"], fc="white", ec="#2a6b2a", lw=0.6))
    ax.set_xlim(-24, 24); ax.set_ylim(D["pcb_y0"] - 2, D["pcb_y1"] + 2); ax.set_aspect("equal"); ax.grid(True, lw=0.15)
    ax.tick_params(labelsize=6); ax.set_title(title, fontsize=8.5, loc="left")

fig = plt.figure(figsize=(22, 15.5))
# ---------------- main board front ----------------
a1 = fig.add_axes([0.01, 0.05, 0.19, 0.86]); board(a1, "MAIN BOARD, FRONT\n(looking at the panel face)")
a1.add_patch(Circle((0, 0), 20.9, fc=NOISE["fixed"], ec="k", lw=0.5, alpha=0.6)); a1.text(0, -16.5, "base cradle sits here\n(no parts)", ha="center", fontsize=6.3)
for r, t in zip(D["hv_r"], D["hv_phi_s"]):
    a = math.radians(D["mech_rot"]); x, y = r * math.cos(math.radians(t)), r * math.sin(math.radians(t))
    a1.add_patch(Rectangle((math.cos(a) * x - math.sin(a) * y - 0.8, math.sin(a) * x + math.cos(a) * y - 0.8), 1.6, 1.6, fc=NOISE["quiet"], ec="k", lw=0.4))
a1.text(-7.5, 15.0, "Hall row (fixed)", fontsize=6.0, ha="center")
blk(a1, 0, 37.0, 17.2, 17.2, "H7B0 LQFP100\n+ decoupling\n+ crystal, SWD pads", "digital", 6.5)
for s in (-1, 1):
    blk(a1, s * 16.0, 37.45, 3.0, 21.9, "", "conn"); a1.text(s * 16.0, 24.8, "vertical\nboard foot", fontsize=5.6, ha="center")
for x, y in ((12.5, 42.1), (12.5, 39.1), (-12.5, 42.1), (-12.5, 39.1)): a1.add_patch(Circle((x, y), 1.0, fc="#9aa3a8", ec="k", lw=0.4))
ow, oh, _ = D["clear_oled"]; ox, oy = D["clear_oled_xy"]
a1.add_patch(Rectangle((ox - ow / 2, oy - oh / 2), ow, oh, fc="#b9d4de", ec="#1f77b4", lw=0.8, alpha=0.5)); a1.text(0, -30, "clear OLED (over D)", ha="center", fontsize=6.5)
blk(a1, 0, -50.3, 12.5, 2.4, "OLED flex rises\nto the jack board", "conn", 5.2)
for s in (-1, 1): blk(a1, s * 12.6, -50.3, 7.6, 2.6, "link pins 2×6", "conn", 5.2)
a1.text(0, 30.0, "", fontsize=5)
# ---------------- main board back ----------------
a2 = fig.add_axes([0.205, 0.05, 0.19, 0.86]); board(a2, "MAIN BOARD, BACK\n(seen through the board from the front)", back=True)
g = freeb
for p in getattr(g, "geoms", [g]):
    if p.geom_type == "Polygon": a2.fill(*p.exterior.xy, fc="#ffffff", ec="#999", lw=0.3, ls=":")
a2.add_patch(Rectangle((-15, 35), 30, 11, fc=NOISE["fixed"], ec="k", lw=0.5, alpha=0.7)); a2.text(0, 40.5, "joystick rear spring anchor (fixed)", ha="center", fontsize=5.8)
ok = [blk(a2, -3.0, 30.0, 16.0, 4.5, "upper AMOLED connector [C]", "conn", 5.8, freeb),
      blk(a2, -15.6, 30.9, 8.0, 6.0, "NOR flash\n(Octo-SPI 2)", "digital", 5.6, freeb),
      blk(a2, -7.0, -8.0, 12.0, 10.0, "1220 driver,\ncurrent sense,\nmotor voice,\nNTC", "noisy", 5.8, freeb),
      blk(a2, -12.0, 2.75, 10.0, 8.0, "VCSEL decoder\n+ 12 switches,\nRGB, violet", "noisy", 5.6, freeb),
      blk(a2, 3.25, 6.75, 6.0, 5.0, "dial link\n(rod)", "digital", 5.6, freeb),
      blk(a2, 0, -50.0, 17.65, 4.5, "lower AMOLED connector [C]", "conn", 5.8, freeb)]
for s in (-1, 1): blk(a2, s * 12.6, -50.3, 7.6, 2.6, "link pins", "conn", 5.2)
a2.add_patch(Rectangle((12.0 - 1.5, 8.5 - 1.3), 3.0, 2.6, fc=NOISE["noisy"], ec="k", lw=0.5)); a2.text(12.0, 11.3, "716 driver\n(placed)", fontsize=5.6, ha="center")
a2.add_patch(Rectangle((-2.6, 11.9), 5.2, 4.0, fc=NOISE["fixed"], ec="k", lw=0.5)); a2.text(0, 17.0, "encoder bearing", fontsize=5.6, ha="center")
a2.add_patch(Rectangle((11.1, 21.7), 8.8, 10.4, fc=NOISE["fixed"], ec="k", lw=0.5, alpha=0.8)); a2.text(15.5, 26.9, "encoder\nboard\n(fixed)", fontsize=5.4, ha="center", va="center")
a2.add_patch(Circle((0, 0), D["rod_pad_r"], fc="#c9a227", ec="k", lw=0.4)); a2.text(0, 0, "rod\npad", fontsize=5.2, ha="center", va="center")
for x in (-6.0, 6.0): pass
a2.add_patch(Circle((0, 0), 21.3, fc="none", ec="#e6550d", lw=1.2, ls="--")); a2.text(-14.5, 15.8, "emitter ring", fontsize=5.8, color="#e6550d")
a2.text(0, -20.0, "NOISY ZONE: motors + LEDs", ha="center", fontsize=6.5, color="#a50f15", weight="bold")
a2.text(0, 46.6, "", fontsize=5)
# ---------------- vertical boards ----------------
def panel(rect, title, w, h, blocks, xl="(mm)"):
    ax = fig.add_axes(rect); ax.add_patch(Rectangle((0, 0), w, h, fc="#eef5ee", ec="#2a6b2a", lw=0.8))
    ax.add_patch(Rectangle((0, 0), w, 2.6, fc=NOISE["conn"], ec="k", lw=0.4)); ax.add_patch(Rectangle((0, h - 2.6), w, 2.6, fc=NOISE["conn"], ec="k", lw=0.4))
    ax.text(w / 2, 1.3, "right-angle header to the main board", ha="center", va="center", fontsize=5.4)
    ax.text(w / 2, h - 1.3, "right-angle header to the top board", ha="center", va="center", fontsize=5.4)
    for b in blocks: blk(ax, *b)
    ax.set_xlim(-1, w + 1); ax.set_ylim(-1, h + 1); ax.set_aspect("equal"); ax.tick_params(labelsize=5.5); ax.set_title(title, fontsize=8, loc="left")
    return ax
VW, VH = 21.9, 30.0
panel([0.40, 0.70, 0.13, 0.24], "VERTICAL BOARD L (x −16), outer face", VW, VH,
      [(6.0, 21.0, 10.5, 9.0, "15→5 V buck\n+ inductor", "power"), (16.0, 21.0, 9.0, 9.0, "5→3.3 V buck\n+ inductor", "power"),
       (6.5, 9.5, 11.0, 8.0, "15 V input\ncurrent limit\n(eFuse) + bulk", "power"), (16.5, 9.5, 8.0, 8.0, "spare", "conn")])
panel([0.545, 0.70, 0.13, 0.24], "VERTICAL BOARD L, inner face (toward the chip)", VW, VH,
      [(7.0, 15.0, 11.0, 12.0, "output filters,\nMCU analog\nsupply (LDO)", "power"), (17.0, 15.0, 7.0, 12.0, "spare", "conn")])
panel([0.40, 0.40, 0.13, 0.24], "VERTICAL BOARD R (x +16), inner face", VW, VH,
      [(7.0, 20.0, 11.0, 8.0, "CAN transceiver\n(+ ESD)", "digital"), (16.5, 20.0, 8.0, 8.0, "AMOLED\nsupply if the\nflex lacks one [C]", "power"),
       (11.0, 9.0, 20.0, 7.0, "joystick lines up to the top\nboard (QSPI, ladder, 3.3 V)", "digital")])
panel([0.545, 0.40, 0.13, 0.24], "VERTICAL BOARD R, outer face", VW, VH,
      [(11.0, 15.0, 20.0, 18.0, "spare\n(room for later: Risley drivers,\nI/O expander, test pads)", "conn")])
# ---------------- top board ----------------
a5 = fig.add_axes([0.69, 0.66, 0.15, 0.28]); a5.add_patch(Rectangle((-17.5, 26.5), 35, 21.9, fc="#eef5ee", ec="#2a6b2a", lw=0.8))
blk(a5, 0, 40.6, 10.6, 10.6, "SW1 + press peg", "fixed", 5.8); blk(a5, 12.0, 40.6, 3.0, 8.4, "", "conn"); a5.text(12, 34.9, "screen jumper\nsocket", fontsize=5.4, ha="center")
blk(a5, -11.5, 31.0, 9.0, 5.0, "switch ladder\nresistors", "digital", 5.6); blk(a5, -11.5, 45.0, 9.0, 4.0, "ESD / 3.3 V filter", "digital", 5.4)
for s in (-1, 1): a5.add_patch(Rectangle((s * 16.0 - 1.3, 26.5), 2.6, 21.9, fc=NOISE["conn"], ec="k", lw=0.4))
a5.set_xlim(-19, 19); a5.set_ylim(25, 50); a5.set_aspect("equal"); a5.tick_params(labelsize=5.5)
a5.set_title("TOP BOARD (joystick), nests in the case cradle\nheaders from both vertical boards along its sides", fontsize=8, loc="left")
# ---------------- jack board ----------------
a6 = fig.add_axes([0.69, 0.33, 0.30, 0.28]); a6.add_patch(Rectangle((-22.0, -51.5), 44.0, 12.1, fc="#eef5ee", ec="#2a6b2a", lw=0.8))
for x in D["jack_xs"]: a6.add_patch(Rectangle((x - 5.0, -45.15 - 5.25), 10.0, 10.5, fc="none", ec="k", lw=0.8, ls="--"))
a6.text(0, -38.6, "jack bodies above (dashed); parts go on the underside, facing the main board", ha="center", fontsize=6.3)
blk(a6, -12.4, -41.75, 18.0, 4.3, "CV out ×2, gate, audio out:\nop-amps + protection", "quiet", 5.6)
blk(a6, 12.4, -41.75, 18.0, 4.3, "CV in, audio in: scaling,\nclamps; mono/stereo sense", "quiet", 5.6)
blk(a6, 0, -46.35, 17.65, 4.5, "clear OLED ZIF (24-pin)\nflex comes up from below", "conn", 5.4)
blk(a6, -15.6, -46.35, 11.0, 4.5, "±12 V for CV\n(LDO + inverter)", "power", 5.4)
blk(a6, 15.6, -46.35, 11.0, 4.5, "OLED 12.5 V LDO", "power", 5.4)
for s_ in (-1, 1): blk(a6, s_ * 12.6, -50.1, 7.6, 2.4, "link pins 2×6", "conn", 5.0)
blk(a6, 19.0, -50.1, 3.6, 2.4, "15 V\nin", "conn", 4.8)
a6.set_xlim(-24, 24); a6.set_ylim(-53, -37); a6.set_aspect("equal"); a6.tick_params(labelsize=5.5)
a6.set_title("JACK BOARD (new, proposed): under the four jacks, z ~25, soldered to the jack pins;\nlong pins down to the main board's bottom strip", fontsize=8, loc="left")
# ---------------- USB board ----------------
a7 = fig.add_axes([0.86, 0.06, 0.13, 0.17]); a7.add_patch(Rectangle((-6, -2.75), 12, 5.5, fc="#eef5ee", ec="#2a6b2a", lw=0.8))
blk(a7, -1.0, 0.4, 8.94, 3.26, "USB-C (front face)", "conn", 5.6); blk(a7, 4.6, -1.6, 2.4, 2.0, "TVS", "power", 5.0)
a7.text(0, -4.2, "back face: PD sink chip (asks for ≤ 15 V) + CC parts", ha="center", fontsize=5.6)
a7.set_xlim(-8, 8); a7.set_ylim(-5.5, 4); a7.set_aspect("equal"); a7.tick_params(labelsize=5.5)
a7.set_title("USB BOARD (12 × 5.5), in the wall slot", fontsize=8, loc="left")
fig.legend(handles=[Patch(fc=NOISE[k], ec="k", label=LEG[k]) for k in NOISE], loc="lower left", bbox_to_anchor=(0.40, 0.03), ncol=2, fontsize=8, frameon=False)
fig.text(0.40, 0.22, "Signals that have to travel down the board [A]\n"
         "  top → knob zone (between A and B, 6 mm web + 2 edge strips): Halls 8, encoder 2, 1220 4, 716 3, VCSEL 5, RGB 2,\n"
         "     violet 1, dial link 1, NTC + motor voice 3  ≈ 29, plus 5 V and 3.3 V\n"
         "  top → bottom (also past D: only the two ~2.3 mm strips beside D): lower AMOLED 6-10 (QSPI/SPI, not the 16-line bus),\n"
         "     jack board link ≈ 16 (OLED SPI 5, CV/audio 6, jack sense 4, spare), plus 15 V up and 3.3 V down  ≈ 26\n"
         "  strips beside D: about 36 tracks on two signal layers. Tight but workable on a 4-layer board [C].", fontsize=7.5, va="top", family="monospace")
fig.suptitle("Fresh floorplan (blocks, not parts): where every circuit lives with the H7B0 under the joystick. Sizes are estimates [A]; "
             "red outline = block does not fit where drawn.", fontsize=11.5, x=0.01, ha="left")
fig.savefig(out, dpi=100); print("wrote", out, "back blocks fit:", ok)
