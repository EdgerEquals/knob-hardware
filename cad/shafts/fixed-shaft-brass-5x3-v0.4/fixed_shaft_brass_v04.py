"""Fixed shaft v0.4: brass tube 5 x 3 (2026-10-31). Supersedes v0.3. Dial-centre power + data link (data over power, Ed):
the tube is the NEGATIVE (GND) conductor. Its bottom end is SOLDERED to the F.Cu ring pad on the main PCB front (KiCad v0.8,
H1 TubeRodClamp_Main_M1.6) and no longer passes through the board; its top end bears on the screen adapter's B.Cu GND ring,
clamped by the M1.6 rod. Length = adapter underside 52.60 (holder v0.4 board seat) - 0 = 52.60. Bonded in the base cradle collar
above the pad. The 3.0 bore carries the insulated M1.6 rod (POSITIVE). Knurl/flats at the top for the holder bond as before.
Local frame: Z = height above the PCB front."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "pcbs/knob-main-pcb", "knob/knob-v0.1", "holders/screen-holder-v0.1", "holders/screen-holder-v0.2", "holders/screen-holder-v0.4",
          "shafts/fixed-shaft-brass-5x3-v0.2"):
    sys.path.insert(0, os.path.join(LIB, d))
import fixed_shaft_brass_v02 as s2
import screen_holder_v04 as h4
import knob_main_pcb as pcb
P = dict(s2.P); p = P
p["flange_t"] = 0.0
p["tube_len"] = h4.P["tube_top"]          # 52.60
p["knurl_len"] = h4.P["socket_len"]       # 6.0
def build_tube(p=P): return s2.build_tube(p)
def placed(shape, p=P):
    z_front = pcb.board_solid().bounding_box().max.Z
    return Pos(p["axis_x"], -p["axis_y"], z_front) * shape

if __name__ == "__main__":
    from sheet import Sheet
    t = build_tube(); export_step(t, os.path.join(HERE, "brass-tube-5x3.step"))
    R, r, L = p["tube_od"] / 2, p["tube_id"] / 2, p["tube_len"]
    sh = Sheet(layout="panel", shape=t, gap=26, scale=3.5, label_pad=16)
    sh.vdim("plan", 0, L, -R, -R - 5, f"{L:.2f} long (v0.3: 53.31)")
    sh.vdim("plan", L - p["knurl_len"], L, R, R + 5, f"{p['knurl_len']:.1f} knurl / flats (holder socket)")
    sh.hdim("front", -R, R, -R, -R - 3, f"Ø{p['tube_od']:.0f} OD [Ed]")
    sh.hdim("front", -r, r, R, R + 3, f"Ø{p['tube_id']:.0f} ID [Ed]")
    s2.notes(sh, "plan", R + 30, L, ["Brass tube 5 OD x 3 ID stock, cut to length: the NEGATIVE (GND) conductor",
             "Bottom end soldered to the main PCB F.Cu ring (Ø3.4–Ø6.4, GND); no longer through the board",
             f"Top end {L:.2f} above the PCB front bears on the adapter board's B.Cu GND ring (Ø3.2–Ø5.6)",
             "Bore carries the M1.6 rod (POSITIVE, VBUS_DATA) in a Ø1.7/Ø2.6 insulating sleeve [A]",
             "Bonded in the base cradle collar; knurl or 2 flats at the top for the holder bond", f"Deburr {p['deburr']:.1f} × 45° both bore ends [A]"], 3.0)
    title = "Brass tube 5 × 3 — fixed shaft v0.4, 2026-10-31"
    sub = [f"{L:.2f} long, soldered on the main PCB front.", "[Ed] = Ed, [A] = assumed.", s2.SUB3]
    sh.dxf(os.path.join(HERE, "brass-tube-5x3.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "brass-tube-5x3-drawing.png"), title, sub)
    print(round(L, 3))
