"""Q38 picture (8 Nov 2026): the power tree on vertical board L, 15 V (VSYS, from the jack power board's eFuse) to 5 V and 3.3 V.
Load figures: Ed's bench (1220), the SK6812MINI-E sheet (12 mA a colour), the rest [A]. Pure matplotlib:
  python3 tools/studies/power_tree_q38_sketch.py docs/img/power-tree-q38.png"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig = plt.figure(figsize=(16, 9.2), dpi=125)
ax = fig.add_axes([0.01, 0.01, 0.98, 0.9]); ax.axis("off"); ax.set_xlim(0, 160); ax.set_ylim(0, 92)
fig.text(0.015, 0.975, "Q38: power on vertical board L, 15 V in, 5 V and 3.3 V out", fontsize=14, weight="bold", va="top")
fig.text(0.015, 0.945, "15 V (VSYS) arrives already limited by the jack power board's eFuse (3 A), so board L needs no second input "
         "limit. Board L: 22 x 29 mm, two faces.", fontsize=10, va="top")


def box(x, y, w, h, t, fc, fs=8.6, b=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.45", fc=fc, ec="#333", lw=0.8))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, weight="bold" if b else None)


def arrow(x0, y0, x1, y1, t="", col="#555"):
    ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", color=col, lw=1.4))
    if t:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 1.5, t, ha="center", fontsize=7.8, color=col)


L5 = "1220 (DRV8213): 0.76 A held still [your bench]\n24 RGB: 0.86 A full white, firmware cap\ndial through the rod: 0.12 A [A]\nCAN transceiver: 0.07 A [A]\n= 1.8 A worst, about 1.3 A with the LED cap"
L33 = "H743: 0.25 A [A]\njoystick screen: 0.2 A [A]\nHalls, encoder, power light: 0.05 A\n= 0.5 A worst"
for x0, tag, two in ((0, "A (recommended): two bucks, both straight from 15 V", True),
                     (81, "B: one buck to 5 V, then an LDO to 3.3 V (the 3 Nov plan)", False)):
    ax.text(x0 + 1, 85, tag, fontsize=11.5, weight="bold")
    box(x0 + 2, 60, 12, 12, "15 V\nVSYS", "#e3f2fd", 9, True)
    box(x0 + 24, 66, 20, 10, "TPS62933F buck\n15 → 5 V, 3 A" + ("\nEN from the H743" if two else ""), "#fff9c4", 8.2, True)
    box(x0 + 24, 50, 20, 10, ("TPS62933F buck\n15 → 3.3 V, 3 A" if two else "LDO 5 → 3.3 V\n(about 0.4-0.85 W hot)"), "#fff9c4" if two else "#ffe0b2", 8.2, True)
    box(x0 + 50, 64, 28, 14, L5, "#ffcdd2", 7.4)
    box(x0 + 50, 48, 28, 12, L33, "#c8e6c9", 7.4)
    arrow(x0 + 14.5, 68, x0 + 23.5, 71)
    arrow(x0 + 44.5, 71, x0 + 49.5, 71)
    arrow(x0 + 44.5, 55, x0 + 49.5, 55)
    if two:
        arrow(x0 + 14.5, 64, x0 + 23.5, 55)
    else:
        arrow(x0 + 34, 65.5, x0 + 34, 60.5)
    notes = (["Same chip as the jack board's 3.3 V (TPS62933F, Q39, LCSC C5219272,",
              "US$0.62 [S]): one part number. About 90 % each under load, cool.",
              "Both fixed frequency, 1-2 MHz, set apart [Q39].",
              "The motor and LED noise on 5 V never rides into the 3.3 V.",
              "3.3 V is always on; the 5 V stays off until the H743 turns it on",
              "(your rule for the jack board's rails, Q6). One more pin (5V_EN).",
              "Margins: 5 V 1.8 A of 3 A; 3.3 V 0.5 A of 3 A."]
             if two else
             ["The quietest 3.3 V in the audio band (the LDO filters the 5 V's",
              "motor and LED ripple), but it burns (5 - 3.3) x current: about",
              "0.4 W normally, 0.85 W at 0.5 A, on a small vertical board.",
              "3.3 V hangs off the 5 V, so the 5 V must always be on, and its",
              "motor and LED load sit upstream of the main chip.",
              "Fewer parts by one inductor."])
    for k, t in enumerate(notes):
        ax.text(x0 + 2, 40 - k * 4.2, t, fontsize=9)
ax.text(1, 9, "Either way: the main chip's analog supply (VDDA) gets its own ferrite and capacitors on the main board (AN4938); "
        "the 1220's driver and the LED ring each on their own filtered 5 V branch;", fontsize=9, color="#555")
ax.text(1, 5.5, "a small input filter between the posts' 15 V and the bucks (noise sweep). With a quiet reference on VREF+ (Q40, next), "
        "the 3.3 V's own noise no longer sets the CV readings.", fontsize=9, color="#555")
fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "power-tree-q38.png")
