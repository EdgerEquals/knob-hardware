"""Centre rod + hardware v0.1 (2026-10-31): dial-centre power + data link (data over power, Ed).
An M1.6 threaded rod [A] (Ed: 1.5 if possible; M1.6 is the nearest stock size) runs down the brass tube bore as the POSITIVE
conductor (VBUS_DATA) and bolts the screen adapter board to the main PCB through the tube:
  top: M1.6 THIN nut (DIN 439, s 3.2 × 1.0 [S/A]) on the adapter F.Cu VBUS_DATA ring, rod cut flush; it stays under the screen (0.3);
  bottom: M1.6 washer (DIN 125, Ø1.7 × Ø4.0 × 0.3) + nut (DIN 934, s 3.2 × 1.3) on the main PCB B.Cu VBUS_DATA ring, 0.5 rod proud.
Both board holes NPTH Ø1.8, so the rod touches only the positive rings via nut/washer. Insulating sleeve in the Ø3.0 bore:
radial room (3.0 − 1.6)/2 = 0.70 (M2 would leave 0.50). Sleeve Ø1.7 ID × Ø2.6 OD [A] (PTFE tube, or 3/32" 2:1 heatshrink shrunk on the
rod), 0.20 radial to the bore; full tube length. Frame: dial axis = Z, Z = height above the main PCB front."""
import math, os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "pcbs/knob-main-pcb", "knob/knob-v0.1", "holders/screen-holder-v0.1", "holders/screen-holder-v0.2", "holders/screen-holder-v0.4",
          "shafts/fixed-shaft-brass-5x3-v0.2", "shafts/fixed-shaft-brass-5x3-v0.4"):
    sys.path.insert(0, os.path.join(LIB, d))
import knob_main_pcb as pcb
import screen_holder_v04 as h4
import fixed_shaft_brass_v04 as tb
_bb = pcb.board_solid().bounding_box()
P = dict(rod_d=1.6, nut_s=3.2, nut_m=1.3, thin_m=1.0, wash_id=1.7, wash_od=4.0, wash_t=0.3, proud=0.5,   # [S] M1.6 DIN 934/439/125
         sleeve_id=1.7, sleeve_od=2.6,          # [A]
         pcb_t=_bb.max.Z - _bb.min.Z, bore=tb.P["tube_id"])
p = P
p["z_adapter_top"] = h4.P["z_board_top"]                 # 53.60
p["z_top"] = p["z_adapter_top"] + p["thin_m"]            # 54.60 rod flush with the thin nut
p["screen_gap"] = h4.P["z_screen0"] - p["z_top"]         # 0.30 under the screen back
p["z_wash1"] = -p["pcb_t"]; p["z_wash0"] = p["z_wash1"] - p["wash_t"]
p["z_nut0"] = p["z_wash0"] - p["nut_m"]
p["z_bot"] = p["z_nut0"] - p["proud"]
p["rod_len"] = p["z_top"] - p["z_bot"]
p["sleeve_len"] = tb.P["tube_len"]
p["room"] = (p["bore"] - p["rod_d"]) / 2
p["sleeve_gap"] = (p["bore"] - p["sleeve_od"]) / 2
A = (Align.CENTER, Align.CENTER, Align.MIN)
def _tube(a, b, z0, h): return Pos(0, 0, z0) * (Cylinder(b / 2, h, align=A) - Cylinder(a / 2, h, align=A))
def _nut(z0, m):
    hexa = Pos(0, 0, z0) * extrude(RegularPolygon(p["nut_s"] / math.sqrt(3), 6), m)
    return hexa - Pos(0, 0, z0) * Cylinder(p["rod_d"] / 2, m, align=A)
def parts(p=P):
    return {"rod M1.6 (VBUS_DATA)": Pos(0, 0, p["z_bot"]) * Cylinder(p["rod_d"] / 2, p["rod_len"], align=A),
            "rod sleeve": _tube(p["sleeve_id"], p["sleeve_od"], 0, p["sleeve_len"]),
            "rod nut top (thin)": _nut(p["z_adapter_top"], p["thin_m"]),
            "rod washer bottom": _tube(p["wash_id"], p["wash_od"], p["z_wash0"], p["wash_t"]),
            "rod nut bottom": _nut(p["z_nut0"], p["nut_m"])}
NOTE = (f"M1.6 rod {P['rod_len']:.2f} [A] (POSITIVE) in a Ø{P['sleeve_id']:.1f}/Ø{P['sleeve_od']:.1f} sleeve [A] ({P['room']:.2f} radial room, "
        f"{P['sleeve_gap']:.2f} to the bore); thin nut on the adapter, washer + nut under the PCB")

if __name__ == "__main__":
    from sheet import Sheet
    sys.path.insert(0, os.path.join(LIB, "control-dial/control-dial-v0.1")); import bezel as b1
    pr = parts(); both = Compound(children=list(pr.values())); export_step(both, os.path.join(HERE, "rod-m1.6-hardware.step"))
    sh = Sheet(both, gap=70, scale=1.6, label_pad=20)
    sh.set_front_section(b1.section_items(pr), "SECTION A-A (through the rod axis)")
    sh.vdim("front", p["z_bot"], p["z_top"], -2, -8, f"{p['rod_len']:.2f} rod M1.6 [A]")
    sh.vdim("front", 0, p["sleeve_len"], 2, 8, f"{p['sleeve_len']:.2f} sleeve [A]")
    sh.hdim("front", -p["wash_od"] / 2, p["wash_od"] / 2, p["z_bot"], p["z_bot"] - 3, f"Ø{p['wash_od']:.1f} washer, nut s{p['nut_s']:.1f}")
    sh.hdim("front", -p["nut_s"] / 2, p["nut_s"] / 2, p["z_top"], p["z_top"] + 3, f"thin nut s{p['nut_s']:.1f} × {p['thin_m']:.1f}")
    sb = sh.bb["plan"]
    lines = ["Data over power [Ed]: rod = POSITIVE (VBUS_DATA), brass tube = NEGATIVE (GND)",
             f"Rod M1.6 [A] (Ed: 1.5 if possible), {p['rod_len']:.2f} long, {p['z_bot']:.2f} to {p['z_top']:.2f} from the PCB front",
             f"Sleeve Ø{p['sleeve_id']:.1f} × Ø{p['sleeve_od']:.1f} × {p['sleeve_len']:.1f} [A]: PTFE tube or 3/32\" 2:1 heatshrink; room {p['room']:.2f} radial (M2: 0.50)",
             f"Top: DIN 439 thin nut s{p['nut_s']:.1f} × {p['thin_m']:.1f} on the adapter F.Cu ring, rod flush; {p['screen_gap']:.2f} under the screen",
             f"Bottom: DIN 125 washer Ø{p['wash_id']:.1f}/Ø{p['wash_od']:.1f} × {p['wash_t']:.1f} + DIN 934 nut × {p['nut_m']:.1f} on the PCB B.Cu ring, {p['proud']:.1f} proud",
             "Rod holes NPTH Ø1.8 in both boards: contact only through the nuts/washer"]
    for i, l in enumerate(["NOTES"] + lines):
        sh.note("plan", sb[1] + 20, sb[3] + 4 - i * 3.0, l, 8 if i == 0 else 6.5, **(dict(weight="bold") if i == 0 else {}))
    title = "Centre rod M1.6 + nuts + sleeve — v0.1, 2026-10-31"
    sub = ["Positive conductor and clamp through the brass tube.", "[S] = stock, [A] = assumed.", "Third-angle · mm · z-up"]
    sh.dxf(os.path.join(HERE, "rod-m1.6-hardware.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "rod-m1.6-hardware-drawing.png"), title, sub)
    print({k: round(v, 3) for k, v in p.items()})
