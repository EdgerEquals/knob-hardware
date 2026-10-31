"""Knob stack assembly v0.8 (2026-10-31): v0.7 with (Ed) the bezel knob renamed CONTROL DIAL (v0.3), the thinner screen holder v0.2,
concentric plain tubes the whole way down (brass -> control-dial tube -> big-knob tube, sliding fits, no bearings; PTFE liner and
thrust shoulder dropped) and the big knob v0.4 with no OD step. The printed back flange is replaced by the BASE CRADLE v0.3 on the
PCB front (holds the brass tube, cradles the motor, fills the skirt); both dial tubes stop 0.3 [A] above its tube boss. Gears, motor, encoder, skirt unchanged. z-up sheet layout.
v0.7 notes: Knob stack assembly v0.7 (2026-10-31): v0.6 with bezel v0.1 -> bezel knob v0.2 (Ø48 ring on the big knob, top flush with
the glass; holder/screen/adapter up 1.80 vs holder v0.1, clear of the bezel knob, which turns ±10° [A]). No other change.
v0.6 notes: Knob stack assembly v0.6 (2026-10-31): every current part, imported from the library (no new geometry here).
Supersedes v0.5: + bezel v0.1 (PETG sleeve on the tube, Ø35 face), knob v0.2 -> v0.3 (PTFE 10x8 liner instead of the bronze bush),
encoder take-off v0.1 -> v0.2 (PCB bearing from the back; PCB v0.5 has H2 on B). The screen holder (geometry unchanged) now sits
on the bezel face, so the holder, screen and adapter move up by the bezel face height; the tube v0.2 is NOT lengthened (flagged).
v0.5 notes:
Supersedes v0.4 (../knob-stack-v0.4): knob v0.1 -> knob v0.2 (skirt round the motor, bottom ring internal 90T). Parts:
  PCB v0.4 (KiCad STEP, H1 Ø5.2 NPTH, M1 motor tabs, H2 Ø5.0 encoder bearing)      pcbs/knob-main-pcb
  1220 motor at the 14.0 [A] offset (end cap on the PCB front)   motors/1220-coreless-planetary (placement as v0.3)
  brass shaft v0.2: 57.31 tube + 17.5 printed flange on the PCB back   shafts/fixed-shaft-brass-5x3-v0.2
  knob v0.2: cap + skirt + hub, 68T internal ring, 90T bottom internal ring, 12T pinion, bronze bush   knob/knob-v0.2
  encoder take-off v0.1: 2 x F682ZZ, Ø2 shaft, 14T pinion, 94T big gear behind the PCB; back panel = dashed line only [A]   encoder-takeoff/encoder-takeoff-v0.1
  screen holder v0.1, 0.71" GC9D01 round TFT (tail folded), screen adapter board (KiCad STEP + envelopes)
      holders/screen-holder-v0.1, displays/tft-0.71-round-gc9d01, pcbs/screen-adapter
Knob/holder parts are authored with Z = height above the PCB front on the dial axis; they are moved here by
Pos(dial x, -dial y, PCB front Z). World axes as in tools/sheet.py (X panel x, Y = -panel y, Z toward the panel front)."""
import os, sys, itertools
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "motors/1220-coreless-planetary", "pcbs/knob-main-pcb", "shafts/fixed-shaft-brass-5x3-v0.2",
          "knob/knob-v0.1", "knob/knob-v0.2", "knob/knob-v0.4", "control-dial/control-dial-v0.1", "control-dial/control-dial-v0.3", "holders/screen-holder-v0.1", "holders/screen-holder-v0.2", "encoder-takeoff/encoder-takeoff-v0.2", "encoder-takeoff/encoder-takeoff-v0.3", "base-cradle/base-cradle-v0.3"):
    sys.path.insert(0, os.path.join(LIB, d))
import motor_gearbox as mg
import knob_main_pcb as pcb
import fixed_shaft_brass_v02 as shaft
import knob_gears as kg
import knob_v04 as kv
import control_dial_v03 as bz
import encoder_takeoff_v03 as enc
import screen_holder_v02 as hold
import base_cradle_v03 as cr
from sheet import Sheet

M = mg.VARIANTS["motor-1220"]; F = pcb.kicad_facts(); SP = shaft.P; KP = kv.P; HP = hold.P
MOTOR_OFFSET = F["motor_x"] - F["shaft_x"]   # [A] 14.0 in make_board.py
RED = dict(color="red", weight="bold")

def motor_placed():   # same placement as v0.3
    return Pos(F["motor_x"], -F["motor_y"], -pcb.Z_PCB_FRONT) * Rot(0, 0, -90) * Rot(0, -90, 0) * mg.build(M)

def vol(s):
    if s is None: return 0.0
    items = s if isinstance(s, (list, ShapeList)) else [s]
    return sum(c.volume for c in items if c is not None)

def bbox_overlap(a, b, tol=1e-6):
    A, B = a.bounding_box(), b.bounding_box()
    return all(tuple(A.min)[i] < tuple(B.max)[i] - tol and tuple(B.min)[i] < tuple(A.max)[i] - tol for i in range(3))

def build_parts():
    """All v0.6 parts in world coordinates (also used by iso_section.py)."""
    board = pcb.board_solid(); zf = board.bounding_box().max.Z; zb = board.bounding_box().min.Z
    hx, hy = F["shaft_x"], F["shaft_y"]
    T = Pos(hx, -hy, zf)                       # knob/bezel frame -> world
    BZ = bz.P; dz = 0.0                        # holder v0.2 is authored in the assembly frame (no shift)
    TH = T
    hp = hold.placed_parts()
    parts = {
        "PCB": board,
        "motor": motor_placed(),
        "brass tube": shaft.placed(shaft.build_tube()),
        "base cradle": T * cr.build_cradle(),
        **{n: T * part for n, part in kv.parts().items()},
        **{n: Pos(F["enc_x"], -F["enc_y"], zf) * part for n, part in enc.parts().items()},
        "control dial": T * bz.build_control_dial(),
        "screen holder": TH * hold.build_holder(),
        "TFT backing": TH * hp["backing"], "TFT glass": TH * hp["glass"], "TFT tail": TH * hp["tail"],
        "adapter board": TH * hp["board"],
    }
    for i, c in enumerate(hp["comps"]): parts[f"adapter part {('J1', 'U1')[i] if i < 2 else i}"] = TH * c
    return parts, board, zf, zb, hx, hy, BZ, dz

if __name__ == "__main__":
    parts, board, zf, zb, hx, hy, BZ, dz = build_parts()
    asm = Compound(children=list(parts.values()), label="knob-stack-v0.8")
    export_step(asm, os.path.join(HERE, "knob-stack-v0.8.step"))

    # pairwise interference (bbox prefilter; touching faces / bonded fits give ~0 volume)
    THR = 1e-3
    clashes, checked = {}, 0
    for (na, a), (nb, b) in itertools.combinations(parts.items(), 2):
        if not bbox_overlap(a, b): continue
        checked += 1
        v = vol(a.intersect(b))
        if v > THR: clashes[f"{na} / {nb}"] = v
    print("pairs bbox-overlapping", checked, "of", len(parts) * (len(parts) - 1) // 2, "clashes", {k: round(v, 3) for k, v in clashes.items()})

    bb = board.bounding_box(); x0, x1, y0, y1 = bb.min.X, bb.max.X, -bb.max.Y, -bb.min.Y
    top = HP["z_glass_top"] + dz; R = M["body_d"] / 2
    ko, ho = KP["bot_ring_od"] / 2, HP["od"] / 2
    sh = Sheet(asm, gap=44, scale=0.92, label_pad=20, layout="z-up")
    # front view
    # FRONT view replaced by full section A-A: plane through the dial axis and the motor axis (world Y = -dial y)
    cut = Plane(origin=(0, -hy, 0), x_dir=(1, 0, 0), z_dir=(0, 1, 0))
    HATCH = ["////", "\\\\", "xx", "---", "|||", "//", "\\\\\\", "++", "...", "/", "\\", "-", "|", "x", "oo", "////\\\\"]
    items, hi = [], 0
    for n, part in parts.items():
        try:
            fs = section(part, section_by=cut).faces()
        except Exception:
            fs = []
        if fs:
            items.append((n, list(fs), HATCH[hi % len(HATCH)])); hi += 1
    sh.set_front_section(items, "SECTION A-A (through dial and motor axes)")
    cut_names = [n for n, _, _ in items]
    print("cut parts", cut_names)
    zt = zf + top
    sh.hdim("front", hx - BZ["face_d"] / 2, hx + BZ["face_d"] / 2, zf + BZ["z_top"], zt + 10, f"Ø{BZ['face_d']:.1f} control dial = big knob OD")
    sh.hdim("front", hx - ho, hx + ho, zf + HP["z_rim"] + dz, zt + 4, f"Ø{HP['od']:.2f} holder OD")
    sh.hdim("front", hx - KP["skirt_od"] / 2, hx + KP["skirt_od"] / 2, zb, zb - 25, f"Ø{KP['skirt_od']:.2f} big knob OD, no step [Ed]")
    sh.hdim("front", hx, F["motor_x"], zb, zb - 9, f"{MOTOR_OFFSET:.1f} motor offset [A] TBC")
    sh.hdim("front", x0, x1, zb, zb - 17, f"{x1 - x0:.2f} PCB")
    sh.vdim("front", zf, zt, x1, x1 + 14, f"{top:.2f} overall above PCB front")
    # TOP view (layout z-up: x = X, y = world Y = -panel y), looking down the dial axis; A-A cutting line here
    sh.hdim("plan", hx, F["motor_x"], -hy, -hy + ko + 5, f"{MOTOR_OFFSET:.1f} motor offset [A] TBC")
    sh.hdim("plan", x0, x1, -y0, -y0 + 6, f"{x1 - x0:.2f} PCB")
    sh.vdim("plan", -y1, -y0, x1, x1 + 8, f"{y1 - y0:.2f} PCB")
    sh.vdim("plan", -F["enc_y"], -hy, x0, x0 - 8, f"{F['enc_y'] - hy:.1f} H2 below the dial axis [K]")
    sh.cut_line("plan", x0 - 5, x1 + 5, -hy, +1, "A")
    # RIGHT SIDE view (x = world Y, y = Z): heights line up with the section
    sh.vdim("side", zf, zf + KP["h_top"], -y0, -y0 + 5, f"{KP['h_top']:.1f} knob top")
    sh.vdim("side", zf, zf + KP["h_shaft_tip"], -y0, -y0 + 12, f"{KP['h_shaft_tip']:.1f} motor shaft tip")
    sh.vdim("side", zf, zf + KP["h_skirt0"], -hy + ko, -y0 + 19, f"{KP['skirt_gap']:.1f} skirt to PCB [Ed]")
    sh.vdim("side", zf, zf + cr.P["top"], -hy - cr.P["r_out"], -y1 - 6, f"{cr.P['top']:.1f} base cradle")
    sh.vdim("side", zb - SP["flange_t"], zb, -hy, -y1 - 14, f"{SP['flange_t']:.1f} tube below the PCB")
    EP = enc.P; zp = zf + EP["h_panel"]
    sh.hdim("side", -y1, -y0, zb, zp - 6, f"{y1 - y0:.2f} PCB")
    sh.ref_line("front", x0 - 2, zp, x1 + 2, zp, "")
    sh.ref_line("side", -y1 - 2, zp, -y0 + 2, zp, "back panel [A]")
    lines = [f"PCB v0.6, 1220 motor, brass tube v0.2 ({SP['tube_len']:.2f}), base cradle v0.3, control dial v0.3, big knob v0.4, encoder v0.3, holder v0.2, TFT, adapter",
             f"Pairwise interference: {len(parts)} parts, {checked} bbox-overlapping pairs checked (threshold {THR} mm³)"]
    if clashes:
        why = {"PCB / motor": f" (motor rear boss Ø{M['rear_boss_d']:.0f} × {M['rear_boss_len']:.1f} [A] into the PCB front)",
               "screen holder / TFT backing": " (COG ledge past the holder wall)", "screen holder / TFT glass": " (COG ledge past the holder wall)",
               "screen holder / TFT tail": " (folded tail through the holder wall)",
               "control dial / TFT backing": " (COG ledge into the pocket wall)", "control dial / TFT glass": " (COG ledge into the pocket wall)",
               "control dial / TFT tail": " (folded tail into the pocket wall)"}
        lines += [(f"CLASH: {k} {v:.2f} mm³{why.get(k, '')}", RED) for k, v in clashes.items()]
    else:
        lines.append("No solid clash")
    lines.append("Section A-A cuts (each hatched differently): " + ", ".join(cut_names[:5]) + ",")
    lines.append("    " + ", ".join(cut_names[5:10]) + ",")
    lines.append("    " + ", ".join(cut_names[10:]) + "; encoder pinion, shaft and bearings lie off the plane")
    k4flag = kv.FLAG_WALL
    lines.append(f"Concentric, no bearings [Ed]: brass Ø5.0 → control-dial tube Ø{KP['dial_tube_id']:.2f}/Ø{KP['dial_tube_od']:.2f} → big-knob tube Ø{KP['knob_tube_id']:.2f}/Ø{KP['knob_tube_od']:.2f} ({KP['fit']:.2f} fits, 1.5 walls [A])")
    lines.append(f"Control dial Ø{BZ['face_d']:.0f}, top {BZ['z_top']:.2f} flush with the glass; {BZ['inner_t']:.2f} thick near the axis; holder v0.2 walls/floor {HP['wall']:.1f} [A]")
    lines.append(bz.TRAVEL + "; " + bz.TBC[0].lower() + bz.TBC[1:])
    CP = cr.P
    lines.append(f"Base cradle v0.3 on the PCB front (CF-ASA/PETG [A]): Ø{2 * CP['r_out']:.1f} × {CP['top']:.1f}, tube bonded {CP['boss_top']:.1f}, motor bore Ø{CP['motor_bore_d']:.1f}; back flange removed")
    lines.append(kv.FLAG_TUBES)
    lines.append((f"Brass tube unchanged: now sticks out {SP['flange_t']:.1f} behind the PCB (could be cut to {SP['tube_len'] - SP['flange_t']:.2f}) [check]", RED))
    lines.append("Axial location of the control dial and the big knob TBC (no shoulder for now)")
    lines.append((f"Holder socket engagement {HP['socket_len']:.2f} on the unchanged tube v0.2 (spec 6.0 [A]) [check]", RED))
    lines.append(k4flag)
    lines.append(f"Encoder bearing 1 pressed in from the front through the {enc.P['cradle_floor']:.1f} [A] cradle floor, {enc.P['into_pcb']:.2f} into PCB H2: dowel for gluing (KiCad v0.6, H2 on F)")
    lines.append((f"Big knob OD {KP['skirt_od']:.0f} (no step) is over the 49 PCB width [check]", RED))
    lines.append(("Big gear BEHIND the PCB [A] (only 2 mm under the skirt); passes 0.5 under the brass tube end", RED))
    lines.append(("    and its wire exit [check]", RED))
    lines.append(f"Encoder: {enc.P['z_pinion']}T pinion in the 90T ring (ratio {enc.P['ratio']:.3f}), H2 {enc.P['centre_dist']:.1f} below the dial axis [K]; encoder TBC")
    lines.append(("Screen tail supplied 100 mm: short-tail variant needed [check]", RED))
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        sh.note("plan", x1 + 40, -y0 - i * 3.4, l, 8 if i == 0 else 6.5, **kw)
    title = "Knob stack v0.8 rev A — all current parts"
    sub = ["2026-10-31. PCB v0.6, base cradle v0.3, control dial v0.3, big knob v0.4, encoder v0.3, holder v0.2.", "Concentric plain tubes, no bearings; no OD step; base cradle on the PCB front. z-up layout.",
           "Third-angle projection · mm · front = section A-A · [S] stock, [A] assumed"]
    sh.dxf(os.path.join(HERE, "knob-stack-v0.8.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "knob-stack-v0.8-drawing.png"), title, sub)
