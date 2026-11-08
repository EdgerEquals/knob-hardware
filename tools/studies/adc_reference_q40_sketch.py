"""Q40 picture (8 Nov 2026, noise sweep): the ADC's reference. Every ADC reading (and the DAC's output) is a fraction of VREF+,
so whatever moves VREF+ moves every CV-in reading. Figures: step-2 circuit (CV-in scaling), TI REF34 page and LCSC C2156866 [S],
the rest [A] arithmetic. Pure matplotlib:
  python3 tools/studies/adc_reference_q40_sketch.py docs/img/adc-reference-q40.png"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

CENT = 1 / 1200                       # V at the jack, 1 V/oct
fig = plt.figure(figsize=(16, 9.6), dpi=125)
ax = fig.add_axes([0.01, 0.01, 0.98, 0.9]); ax.axis("off"); ax.set_xlim(0, 160); ax.set_ylim(0, 90)
fig.text(0.015, 0.975, "Q40: what the main chip measures against (its reference, VREF+)", fontsize=14, weight="bold", va="top")
fig.text(0.015, 0.945, "Every reading is a fraction of VREF+, so anything that moves VREF+ moves every CV-in reading. "
         "The audio out (the chip's DAC) is a fraction of it too.", fontsize=10, va="top")


def box(x, y, w, h, t, fc, fs=8.6, b=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.45", fc=fc, ec="#333", lw=0.8))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, weight="bold" if b else None)


def arrow(x0, y0, x1, y1, t="", col="#555"):
    ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", color=col, lw=1.4))
    if t:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 1.6, t, ha="center", fontsize=7.8, color=col)


# the chain, today
ax.text(1, 86, "Today", fontsize=11.5, weight="bold")
box(2, 72, 16, 9, "CV jack\n±12 V", "#e3f2fd", 9, True)
box(28, 72, 30, 9, "jack board: x 0.133 round VMID\n(100k in, 13.3k back)", "#c8e6c9", 8.4)
box(70, 72, 22, 9, "main chip's ADC\n16-bit", "#fff9c4", 9, True)
box(70, 58, 22, 8, "VREF+ = the 3.3 V supply\nthrough 47 Ω + 1 µF", "#ffcdd2", 8.2)
arrow(18.5, 76.5, 27.5, 76.5); arrow(58.5, 76.5, 69.5, 76.5)
ax.text(64, 70.2, "0.02-3.21 V,\nup the flex", ha="center", fontsize=7.8, color="#555", va="top")
arrow(81, 66.5, 81, 71.5)
g = 0.133
ax.text(97, 80, f"1 cent at the jack = {CENT * g * 1e3:.2f} mV at the ADC", fontsize=9.5)
ax.text(97, 75.5, f"1 mV on the 3.3 V moves a mid-scale reading {1.6 / 3.3:.2f} mV", fontsize=9.5)
ax.text(97, 71, f"= about {1.6 / 3.3 / (CENT * g * 1e3):.0f} cents. Ripple under 3.4 kHz and slow drift pass", fontsize=9.5, weight="bold", color="#c62828")
ax.text(97, 66.5, "straight through the 47 Ω + 1 µF.", fontsize=9.5, weight="bold", color="#c62828")

# A
x0 = 1
ax.text(x0, 50, "A (recommended): a 3.0 V reference chip on VREF+", fontsize=11.5, weight="bold")
box(x0 + 1, 33, 22, 10, "TI REF3430\n3.0 V, SOT-23-6", "#fff9c4", 9, True)
box(x0 + 33, 33, 22, 10, "VREF+\n1 µF + 100 nF", "#c8e6c9", 9)
arrow(x0 + 23.5, 38, x0 + 32.5, 38, "from the 3.3 V")
gA = 0.113
la = [f"±0.05 %, 6 ppm/°C, noise 3.8 µVp-p per volt (0.1-10 Hz) [S TI]. US$1.51, LCSC C2156866, 312 in stock [S].",
      f"Range re-set to fit 3.0 V: CV-in 13.3k becomes 11.3k (3 places): ±12 V reads 0.23-2.95 V [A]. {CENT * gA / (3.0 / 65536):.1f} codes a cent.",
      "Audio out gain 30.1k becomes 33.2k (still ±5 V); audio in gain and bias re-set to fit 0-3.0 V [A].",
      "The Halls, switch ladder and temperature sensor run on the 3.3 V: the firmware reads the 3.3 V itself",
      "(the chip's VBAT channel, VBAT tied to VDD) and corrects them [A].",
      "Tight, said plainly: its dropout is up to 0.1 V at no load [S], so from 3.3 V it has about 0.2 V to spare;",
      "312 at LCSC is thin stock for a run [S]. [C] its output-capacitor range from the datasheet."]
for k, t in enumerate(la):
    ax.text(x0 + 1, 27 - k * 3.6, t, fontsize=8.8)

# B
x0 = 82
ax.text(x0, 50, "B: the main chip's own reference buffer, 2.5 V (VREFBUF)", fontsize=11.5, weight="bold")
box(x0 + 1, 33, 26, 10, "inside the H743\nVREFBUF 2.5 V", "#fff9c4", 9, True)
box(x0 + 37, 33, 22, 10, "VREF+\n1 µF + 100 nF", "#c8e6c9", 9)
arrow(x0 + 27.5, 38, x0 + 36.5, 38)
gB = 0.076
lb = ["No part. Everything re-set to fit 2.5 V: CV-in gain down to 0.076,",
      f"so {CENT * gB / (2.5 / 65536):.1f} codes a cent instead of 2.1 [A]; audio in and out re-set the same way.",
      "Its drift and noise are the chip's own figures [C, not yet read].",
      "ST's forum reports early H743 chips (revision Y) that shipped without",
      "this buffer's factory trim [S].",
      "",
      "Not offered: leave it as today (about 4 cents per mV on the 3.3 V)."]
for k, t in enumerate(lb):
    ax.text(x0 + 1, 27 - k * 3.6, t, fontsize=8.8, color="#555" if t.startswith("Not offered") else None)
fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "adc-reference-q40.png")
