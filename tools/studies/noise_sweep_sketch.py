"""Noise sweep (8 Nov 2026, Ed 15:45: "I'm a bit of a Scrooge for low noise"). One table: what makes noise, how it travels, what it
would spoil, the fix and its cost, ranked. Details and sources: docs/noise-sweep-2026-11-08.md. Pure matplotlib:
  python3 tools/studies/noise_sweep_sketch.py docs/img/noise-sweep.png"""
import sys, textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROWS = [
    ("HIGH", "Switching regulators in light-load mode (PFM). Board L's 5 V and 3.3 V sit below their mode change (about 0.6 A and 0.5 A [A]) most of the time; the jack board's 3.3 V (under 40 mA) always",
     "bursts at a rate that moves with the load, down into the audio band, on the supplies and their grounds",
     "audio in / out, CV in / out",
     "TPS62933F on all three: same chip and footprint, fixed frequency at every load [S]. And their frequencies set apart (today the boost's 600 kHz x 2 = the jack 3.3 V's 1.2 MHz)",
     "+US$0.37 each; about 0.1 W more each at idle [A] (Q39)"),
    ("HIGH", "The ADC's reference (VREF+) is the 3.3 V supply through 47 Ω",
     "1 cent at a CV jack is 0.11 mV at the ADC; 1 mV of supply ripple moves a mid-scale reading 0.5 mV, about 4-5 cents [A]",
     "CV in (1 V/oct), audio in, audio out (the DAC uses it too), Halls",
     "a quiet reference on VREF+: a 3.0 V reference chip, or the H743's own 2.5 V buffer; the 3 CV-in feedback resistors re-set to fit",
     "one SOT-23 + 2 caps, or none (decision)"),
    ("HIGH", "Ground offset between boards: CV in is made against the jack board's ground, read against the main board's; the main board's return current crosses between",
     "1 mV between the grounds reads as about 9 cents on a CV in [A]; on the CV-out side, about 1.2 cents per amp across the 2x6 stacks (step-2 note)",
     "CV in and CV out, moving with the motor and the LEDs",
     "a ground-sense line: one of the flex's 8 grounds carries the jack board's analog ground to an ADC pin, read with each CV in; the stacks' sense ground from step 2",
     "no parts; one flex ground becomes a sense line (decision)"),
    ("HIGH", "24 RGB LEDs dim by switching at 1.2 kHz [S], each on its own clock",
     "up to 0.86 A pulsing on the 5 V and its ground; 24 free-running clocks beat together across the audio band",
     "audio, CV in, the Halls on the same board",
     "the ring on its own 5 V branch: ferrite + bulk capacitor at the ring, its ground straight back to board L, never under the Halls or the ADC lines; firmware cap",
     "a ferrite and a capacitor"),
    ("HIGH", "Ground loop through USB with a computer: its ground meets the patch cables' grounds (a charger's leakage too, smaller)",
     "mains hum and computer noise as current along the patch cables' sleeves",
     "audio in, CV in",
     "the USB ground meets the jack sleeves at one point on the jack unit, so the loop current never crosses the DAC / op-amp ground; shield through 1 MΩ ‖ 4.7 nF; with a computer, an external USB isolator",
     "two parts; the isolator is yours"),
    ("MED", "1220 brushes and its 50-100 kHz drive (0.76 A held still)",
     "supply ripple, ground current, radiated from the motor leads",
     "Halls, MOT_SENSE, audio",
     "100 nF across the motor's terminals, short twisted leads, the driver on its own 5 V branch + bulk capacitor",
     "a capacitor"),
    ("MED", "Screens' own converters and frame-rate current steps (joystick, dial)",
     "steps at the frame rate on 3.3 V / 5 V",
     "CV in, audio in",
     "the joystick screen on its own filtered 3.3 V branch (ferrite + capacitor)",
     "a ferrite and a capacitor"),
    ("MED", "Clear OLED: row-scanned, on the +12.5 V the op-amps share",
     "row-rate pulses, audio band, on +12.5 V and its ground",
     "CV out, audio out",
     "its ferrite + 10 µF already there; its ground return kept off the op-amps' ground; bench-check",
     "layout only"),
    ("MED", "Boost to 18 V (TPS55340) skips pulses at light load [S]",
     "uneven ripple on 18 V and the -17.6 V charge pump",
     "the ±12 V LDOs' inputs",
     "the LDOs reject it at audio frequencies [A]; bench-check; a small minimum load if needed (TI forum)",
     "none planned"),
    ("MED", "Rod link (still to design): the dial's power and data on one wire",
     "data edges and the dial's current steps on the 5 V",
     "Halls, audio",
     "data well above 20 kHz; the dial's supply filtered at the main-board end",
     "with that circuit"),
    ("LOW", "SPI clock and USB on the same flex as CV / audio",
     "crosstalk between neighbours",
     "CV in, audio",
     "pin order already has grounds between the groups (2, 12, 15, 19, 21, 23-25) and SCK at the edge; keep it",
     "none"),
    ("LOW", "50 MHz QSPI to the joystick screen; the main chip's 480 MHz",
     "radiated, edges",
     "nothing analog nearby",
     "series resistors and grounds between (done); a solid ground plane",
     "-"),
    ("KEPT", "Audio out on the H743's 12-bit DAC",
     "its steps are its floor",
     "audio out",
     "kept: your Q8 = B (\"it's a noise effect, the low bit depth might help\"). The reference in row 2 still keeps supply hum off it",
     "-"),
    ("ALL", "Board stack-up and firmware",
     "every return current",
     "everything",
     "4 layers with an unbroken ground plane on the main board; firmware: the ADC's hardware oversampling, samples timed away from the LED and motor switching",
     "with the layer count"),
]
cols = [(0, 5, "rank"), (5, 20, "noise source"), (25, 17, "how it travels"), (42, 12, "what it spoils"), (54, 31, "fix"), (85, 15, "cost")]
WRAP = 2.05                                    # characters per column unit at 8.3 pt on a 17 in wide sheet
wrapped_rows = [[textwrap.wrap(t, int(w * WRAP)) for t, (x, w, _h) in zip(row, cols)] for row in ROWS]
LINE = 0.205                                   # inches per text line
row_h = [LINE * max(len(c) for c in wr) + 0.16 for wr in wrapped_rows]
H = 1.25 + 0.3 + sum(row_h) + 0.03 * len(ROWS) + 0.15
fig = plt.figure(figsize=(17, H), dpi=115)
ax = fig.add_axes([0.01, 0, 0.98, 1]); ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(-H, 0)
ax.text(0.2, -0.18, "Noise sweep: what makes noise, how it travels, what it would spoil, and the fix", fontsize=14.5, weight="bold", va="top")
ax.text(0.2, -0.5, "Ranked for an audio / CV module. Sources and figures in docs/noise-sweep-2026-11-08.md. "
        "[S] read in a source, [A] my estimate.", fontsize=10, va="top")
y = -1.0
for x, w, h in cols:
    ax.text(x + 0.3, y, h, fontsize=9.5, weight="bold", va="top")
y -= 0.3
COL = {"HIGH": "#ffcdd2", "MED": "#fff9c4", "LOW": "#e8f5e9", "KEPT": "#eeeeee", "ALL": "#e3f2fd"}
for row, wr, hgt in zip(ROWS, wrapped_rows, row_h):
    ax.add_patch(plt.Rectangle((0, y - hgt), 100, hgt, fc=COL[row[0]], ec="w", lw=1.5, zorder=0))
    for (x, w, _h), lines in zip(cols, wr):
        for k, ln in enumerate(lines):
            ax.text(x + 0.3, y - 0.08 - k * LINE, ln, fontsize=8.3, va="top", weight="bold" if x == 0 else None)
    y -= hgt + 0.03
fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "noise-sweep.png")
