"""Knob stack v0.11: close-up SECTION B-B through the encoder interface behind the PCB.
Plane B-B = the board centre line (panel x = 25.25), which holds the dial axis, the encoder axis (H2) and the EE-SX1131 (U2),
so it cuts the sensor across its slot and the big gear's slotted rim. Parts are moved so the encoder axis is at x = 0 and the
PCB front at z = 0 (heights above the PCB front, negative = behind), the dial axis at x = +16.0, the sensor at x = -20.20.
Output: knob-stack-v0.11-encoder-closeup.png / .dxf (A3 sheet: top view, section B-B, side view)."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import knob_stack as ks
from sheet import Sheet
enc, F = ks.enc, ks.F
EP = enc.P
KEEP = ("PCB", "brass tube", "base cradle", "bottom internal ring", "rod", "encoder", "idler", "knob body", "thrust")

if __name__ == "__main__":
    parts, board, zf, zb, hx, hy, BZ, dz = ks.build_parts()
    Ex, Ey = F["enc_x"], -F["enc_y"]
    X = Rot(0, 0, -90) * Pos(-Ex, -Ey, -zf)
    crop = Pos(-2.5, 0, -13) * Box(49, 24, 34)
    sel = {}
    for n, s in parts.items():
        if not any(n.startswith(k) for k in KEEP): continue
        t = X * s
        t = t & crop
        if t is not None and t.volume > 1e-6: sel[n] = t
    sys.path.insert(0, os.path.join(ks.LIB, "control-dial/control-dial-v0.1")); import bezel as b1
    shape = Compound(children=list(sel.values()))
    sh = Sheet(shape, gap=24, scale=3.5, label_pad=20)
    sh.set_front_section(b1.section_items(sel), "SECTION B-B (board centre line: dial axis, encoder H2, sensor U2)")
    sr = EP["sens_r"]; xs = -sr - 2.5; xl = 16.0 + 7
    P = EP
    zp = P["h_panel"]
    for z0, z1, xline, txt in ((P["z_pcb_back"], 0.0, xs - 1, f"{P['pcb_t']:.2f} PCB"),
                               (P["z_sens_open"], P["z_pcb_back"], xs - 1, "4.0 sensor"),
                               (P["h_big_top"], P["rim_top"], xs - 4, f"{P['rim_top'] - P['h_big_top']:.1f} rim"),
                               (P["h_big_bot"], P["h_big_top"], xs - 1, "2.0 gear"),
                               (P["h_hub_bot"], P["h_big_bot"], xs - 4, "2.0 hub")):
        sh.vdim("front", z0, z1, xs, xline, txt)
    sh.vdim("front", zp, P["z_pcb_back"], 4, xl, f"{-(zp - P['z_pcb_back']):.1f} PCB back to back panel [A]")
    sh.ref_line("front", -27, zp, 21, zp, "back panel [A]")
    sh.ref_line("front", -27, P["z_axis"], -23, P["z_axis"], "")
    sh.hdim("front", 0, 16.0, P["h_hub_bot"], P["h_hub_bot"] - 3, "16.0 H2 to dial axis [K]")
    sh.hdim("front", -sr, 0, P["h_hub_bot"], P["h_hub_bot"] - 6, f"{sr:.2f} rim / sensor radius [K]")
    sb = sh.bb["plan"]; sh.cut_line("plan", sb[0] - 3, sb[1] + 3, 0, +1, "B")
    lines = [f"U2 Omron EE-SX1131 [Ed] on the PCB back, {sr:.2f} below H2, slot tangent; rim r {P['rim_r0']:.2f}–{P['rim_r1']:.2f} through the slot",
             f"{P['n_win']} windows, pitch {P['win_pitch']:.4f}: {P['counts_gear']} counts/gear turn, {P['counts_knob']:.0f}/knob turn (quadrature)", enc.FLAG_RIM,
             f"Stack (z above the PCB front): PCB back {P['z_pcb_back']:.2f}; sensor {P['z_pcb_back']:.2f} → open face {P['z_sens_open']:.2f}; optical axis {P['z_axis']:.2f}",
             f"Rim top {P['rim_top']:.2f} ({P['rim_in_slot']:.1f} in the slot, 0.6 [A] under its bottom {P['z_slot_bot']:.2f}); windows {P['win_z0']:.2f}–{P['win_z1']:.2f}",
             f"Gear faces {P['h_big_top']:.2f} / {P['h_big_bot']:.2f}; hub end {P['h_hub_bot']:.2f}; bearing 2 {P['h_b2_top']:.2f}–{P['h_b2_bot']:.2f} (flange on the panel); shaft end {P['h_b2_bot']:.2f}",
             f"Back panel {-(zp - P['z_pcb_back']):.1f} [A] behind the PCB back: {P['h_hub_bot'] - zp - P['brg_ft']:.2f} spare under the hub",
             f"Minimum: {P['panel_gap_min']:.1f} behind the PCB back (bearing-2 flange 0.5 [A] under the gear hub; shaft shortened to suit)",
             ("Board STEP is 1.51 (KiCad omits copper/mask; real 1.6): sensor 0.09 lower on the real board -> 0.41 to the gear [check]", ks.RED)]
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        sh.note("plan", sb[1] + 12, sb[3] - i * 2.6, l, 8 if i == 0 else 6.5, **kw)
    title = "Knob stack v0.11 — encoder close-up, section B-B"
    sub = ["2026-10-31. EE-SX1131 on the PCB back; 94T gear rim in its slot.", "[K] = KiCad, [Ed] = Ed, [A] = assumed.",
           "Third-angle · mm · z above the PCB front, x from H2"]
    sh.dxf(os.path.join(HERE, "knob-stack-v0.11-encoder-closeup.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "knob-stack-v0.11-encoder-closeup.png"), title, sub)
    print("closeup parts", list(sel))
