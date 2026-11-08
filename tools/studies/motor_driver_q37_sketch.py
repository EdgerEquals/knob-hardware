"""Q37 picture (8 Nov 2026): Ed's 1220 stall bench points and the driver for it. Pure matplotlib:
  python3 tools/studies/motor_driver_q37_sketch.py docs/img/motor-driver-q37.png"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

V = [1.0, 2.0]; I = [0.144, 0.299]                 # [Ed 8 Nov 15:31] stall, his bench
s = (I[1] - I[0]) / (V[1] - V[0]); R = 1 / s; Vb = V[0] - I[0] * R
fig = plt.figure(figsize=(15, 7.6), dpi=125)
fig.text(0.02, 0.965, "Q37: the 1220's driver, from your stall readings", fontsize=14, weight="bold", va="top")
ax = fig.add_axes([0.06, 0.12, 0.36, 0.72])
xs = [0, 6.2]
ax.plot(xs, [max(0, (x - Vb) / R) for x in xs], color="#1565c0", lw=1.6, label=f"line through your points: {R:.2f} Ω, brushes {Vb:.2f} V")
ax.plot(V, I, "o", color="#c62828", ms=9, label="your stall readings (1 V 0.144 A, 2 V 0.299 A)")
i5 = (5 - Vb) / R; i6 = (6 - Vb) / R
ax.plot([5], [i5], "s", color="#2e7d32", ms=9, label=f"5 V rail: about {i5:.2f} A held still ({5 * i5:.1f} W)")
ax.plot([6], [i6], "^", color="#888", ms=8, label=f"6 V rated: {i6:.2f} A")
ax.set_xlabel("volts on the motor"); ax.set_ylabel("stall current (A)"); ax.grid(alpha=0.2)
ax.set_xlim(0, 6.3); ax.set_ylim(0, 1.0); ax.legend(fontsize=8.6, loc="upper left")
ax.set_title("Held still (stall). Includes your meter and leads.", fontsize=10, loc="left")

bx = fig.add_axes([0.47, 0.06, 0.52, 0.82]); bx.axis("off"); bx.set_xlim(0, 100); bx.set_ylim(0, 100)


def box(x, y, w, h, t, fc, fs=9, b=False):
    bx.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5", fc=fc, ec="#333", lw=0.8))
    bx.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, weight="bold" if b else None)


def ln(x0, y0, x1, y1, t="", col="#555"):
    bx.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", color=col, lw=1.3))
    if t:
        bx.text((x0 + x1) / 2, (y0 + y1) / 2 + 2, t, ha="center", fontsize=8, color=col)


bx.text(0, 97, "A (recommended): TI DRV8213, 2 x 2 mm", fontsize=11.5, weight="bold", va="top")
box(2, 62, 18, 12, "5 V rail", "#e3f2fd")
box(34, 58, 22, 20, "DRV8213\n1.65-11 V, 4 A peak\n0.24 Ω, PWM to 100 kHz", "#fff9c4", 8.6, True)
box(72, 62, 18, 12, "1220\n6 V, 6.45 Ω", "#ffcdd2", 9, True)
box(34, 82, 22, 8, "H743: IN1, IN2 (PWM), nSLEEP", "#ffcdd2", 7.8)
box(34, 38, 22, 9, "IPROPI: current out\n→ MOT_SENSE (ADC)", "#c8e6c9", 8)
box(62, 38, 22, 9, "VREF: the current limit\n(one resistor pair)", "#c8e6c9", 8)
ln(20.5, 68, 33.5, 68); ln(56.5, 68, 71.5, 68); ln(45, 81.5, 45, 78.5)
ln(45, 57.5, 45, 47.5); ln(62, 47, 56.5, 58.5)
notes = ["Current sensing is inside the chip: no shunt resistor or amplifier. Its output",
         "goes straight to MOT_SENSE for the feel loop, and VREF caps the current (so the",
         "most torque) with no help from the firmware. US$0.68, 3,698 in stock at LCSC [S].",
         "",
         "B: TI DRV8837 (the 716's old driver): 1.8 A, no current sensing, so MOT_SENSE",
         "needs a sense resistor and an amplifier added, and the limit lives in firmware."]
for k, t in enumerate(notes):
    bx.text(0, 28 - k * 4.6, t, fontsize=9, va="top", weight="bold" if t.startswith("B:") else None)
fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "motor-driver-q37.png")
print(f"R {R:.3f}  Vb {Vb:.3f}  I5 {i5:.3f}")
