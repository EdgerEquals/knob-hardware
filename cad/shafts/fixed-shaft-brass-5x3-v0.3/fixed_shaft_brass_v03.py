"""Fixed shaft v0.3: brass tube 5 x 3 only (2026-10-31). Supersedes the shaft v0.2 tube + flange.
Ed: shorten the tube so it does not stick out behind the PCB. The printed flange is gone (base cradle v0.3 on the PCB front
grips the tube in its 8.0 [A] bonded bore). Tube back end flush with the PCB back; top unchanged at 51.80 above the PCB front
(screen holder socket end). Length 51.80 + 1.51 board [K] = 53.31 (v0.2: 57.31). Knurl/flats and deburr as v0.2.
Local frame: Z from the PCB back (Z = 0) upward."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "pcbs/knob-main-pcb", "knob/knob-v0.1", "holders/screen-holder-v0.1", "shafts/fixed-shaft-brass-5x3-v0.2"):
    sys.path.insert(0, os.path.join(LIB, d))
import fixed_shaft_brass_v02 as s2
P = dict(s2.P); p = P
p["flange_t"] = 0.0                                   # no flange: back end flush with the PCB back
p["tube_len"] = p["above_flange"]                     # 53.31
p["pcb_t"] = s2._step_t

def build_tube(p=P): return s2.build_tube(p)
def placed(shape, p=P): return s2.placed(shape, p)

if __name__ == "__main__":
    from sheet import Sheet
    t = build_tube(); export_step(t, os.path.join(HERE, "brass-tube-5x3.step"))
    R, r, L = p["tube_od"] / 2, p["tube_id"] / 2, p["tube_len"]
    sh = Sheet(layout="panel", shape=t, gap=26, scale=3.5, label_pad=16)
    sh.vdim("plan", 0, L, -R, -R - 5, f"{L:.2f} long (v0.2: 57.31)")
    sh.vdim("plan", L - p["knurl_len"], L, R, R + 5, f"{p['knurl_len']:.1f} knurl / flats (holder socket)")
    sh.vdim("plan", 0, p["pcb_t"], R, R + 12, f"{p['pcb_t']:.2f} in the PCB [K]")
    sh.hdim("front", -R, R, -R, -R - 3, f"Ø{p['tube_od']:.0f} OD [Ed]")
    sh.hdim("front", -r, r, R, R + 3, f"Ø{p['tube_id']:.0f} ID [Ed]")
    s2.notes(sh, "plan", R + 30, L, [s2.NOTE_TUBE, f"Back end flush with the PCB back (no flange); top {L - p['pcb_t']:.2f} above the PCB front",
             "Bonded in the base cradle v0.3 (Ø5.2 bore, 8.0 long [A]) and through PCB H1 Ø5.2 [K]", s2.NOTE_KN,
             f"Deburr {p['deburr']:.1f} × 45° both bore ends [A]"], 3.0)
    title = "Brass tube 5 × 3 — fixed shaft v0.3, 2026-10-31"
    sub = [f"Shortened to {L:.2f}: flush with the PCB back.", "[K] = KiCad, [Ed] = Ed, [A] = assumed.", s2.SUB3]
    sh.dxf(os.path.join(HERE, "brass-tube-5x3.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "brass-tube-5x3-drawing.png"), title, sub)
    print(round(L, 3))
