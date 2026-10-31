"""Knob stack assembly v0.6 (2026-10-31): every current part, imported from the library (no new geometry here).
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
          "knob/knob-v0.1", "knob/knob-v0.2", "knob/knob-v0.3", "control-dial/control-dial-v0.1", "holders/screen-holder-v0.1", "encoder-takeoff/encoder-takeoff-v0.2"):
    sys.path.insert(0, os.path.join(LIB, d))
import motor_gearbox as mg
import knob_main_pcb as pcb
import fixed_shaft_brass_v02 as shaft
import knob_gears as kg
import knob_v03 as kv
import bezel as bz
import encoder_takeoff_v02 as enc
import screen_holder as hold
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
    BZ = bz.P; dz = BZ["z_f1"] - HP["z0"]       # holder now sits on the bezel face (was on the 0.3 gap over the knob)
    TH = Pos(hx, -hy, zf + dz)                 # holder / screen / adapter frame -> world
    hp = hold.placed_parts()
    parts = {
        "PCB": board,
        "motor": motor_placed(),
        "brass tube": shaft.placed(shaft.build_tube()),
        "flange": shaft.placed(shaft.build_flange()),
        **{n: T * part for n, part in kv.parts().items()},
        **{n: Pos(F["enc_x"], -F["enc_y"], zf) * part for n, part in enc.parts().items()},
        "bezel": T * bz.build_bezel(),
        "screen holder": TH * hold.build_holder(),
        "TFT backing": TH * hp["backing"], "TFT glass": TH * hp["glass"], "TFT tail": TH * hp["tail"],
        "adapter board": TH * hp["board"],
    }
    for i, c in enumerate(hp["comps"]): parts[f"adapter part {('J1', 'U1')[i] if i < 2 else i}"] = TH * c
    return parts, board, zf, zb, hx, hy, BZ, dz

if __name__ == "__main__":
    parts, board, zf, zb, hx, hy, BZ, dz = build_parts()
    asm = Compound(children=list(parts.values()), label="knob-stack-v0.6")
    export_step(asm, os.path.join(HERE, "knob-stack-v0.6.step"))

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
    sh = Sheet(layout="panel", shape=asm, gap=34, scale=1.05, label_pad=20)
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
    sh.hdim("front", hx - BZ["face_d"] / 2, hx + BZ["face_d"] / 2, zf + BZ["z_f1"], zt + 10, f"Ø{BZ['face_d']:.1f} bezel face [L]")
    sh.hdim("front", hx - ho, hx + ho, zf + HP["z_rim"] + dz, zt + 4, f"Ø{HP['od']:.2f} holder OD")
    sh.hdim("front", hx - KP["skirt_od"] / 2, hx + KP["skirt_od"] / 2, zb, zb - 25, f"Ø{KP['skirt_od']:.2f} skirt OD (ring band Ø{KP['bot_ring_od']:.2f})")
    sh.hdim("front", hx, F["motor_x"], zb, zb - 9, f"{MOTOR_OFFSET:.1f} motor offset [A] TBC")
    sh.hdim("front", x0, x1, zb, zb - 17, f"{x1 - x0:.2f} PCB")
    sh.vdim("front", zf, zt, x1, x1 + 14, f"{top:.2f} overall above PCB front")
    sh.vdim("side", -y0, -y1, -zb, -zb + 8, f"{y1 - y0:.2f} PCB")
    sb = sh.bb["side"]
    sh.cut_line("side", sb[0] - 4, sb[1] + 4, -hy, -1, "A")
    sh.note("plan", x0, zf - 34, "Section plane A-A contains both axes and is parallel to this view: cutting line shown on the side view", 6.5)
    # plan view (y = Z, front up)
    sh.vdim("plan", zf, zf + top, hx - ho, x0 - 12, f"{top:.2f} overall above PCB front (glass top)")
    sh.vdim("plan", zf, zf + KP["h_top"], x1, x1 + 5, f"{KP['h_top']:.1f} knob top")
    sh.vdim("plan", zf, zf + KP["h_skirt0"], hx + ko, x1 + 19, f"{KP['skirt_gap']:.1f} skirt to PCB [Ed]")
    sh.vdim("plan", zf, zf + KP["h_shaft_tip"], x1, x1 + 12, f"{KP['h_shaft_tip']:.1f} motor shaft tip")
    sh.vdim("plan", zb - SP["flange_t"], zb, hx - SP["flange_side"] / 2, x0 - 4, f"{SP['flange_t']:.1f} flange")
    EP = enc.P; zp = zf + EP["h_panel"]
    sh.ref_line("plan", x0 - 2, zp, x1 + 2, zp, f"back panel [A], {EP['panel_gap']:.0f} behind PCB back")
    sh.ref_line("side", -zp, -y1, -zp, -y0, "back panel [A]")
    sock = HP["socket_len"] - dz
    lines = [f"PCB v0.5, 1220 motor, shaft v0.2 ({SP['tube_len']:.2f} tube), bezel v0.1, knob v0.3, encoder v0.2, holder, TFT, adapter",
             f"Pairwise interference: {len(parts)} parts, {checked} bbox-overlapping pairs checked (threshold {THR} mm³)"]
    if clashes:
        why = {"PCB / motor": f" (motor rear boss Ø{M['rear_boss_d']:.0f} × {M['rear_boss_len']:.1f} [A] into the PCB front)",
               "screen holder / TFT backing": " (COG ledge past the holder wall)", "screen holder / TFT glass": " (COG ledge past the holder wall)",
               "screen holder / TFT tail": " (folded tail through the holder wall)"}
        lines += [(f"CLASH: {k} {v:.2f} mm³{why.get(k, '')}", RED) for k, v in clashes.items()]
    else:
        lines.append("No solid clash")
    lines.append("Section A-A cuts (each hatched differently): " + ", ".join(cut_names[:5]) + ",")
    lines.append("    " + ", ".join(cut_names[5:10]) + ",")
    lines.append("    " + ", ".join(cut_names[10:]) + "; encoder pinion, shaft and bearings lie off the plane")
    lines.append(bz.flag_fit(HP["od"], KP["skirt_od"]))
    lines.append(f"Knob runs on a PTFE {BZ['liner_od']:.0f}×{BZ['liner_id']:.0f} liner [S] on the bezel journal Ø{BZ['journal_d']:.2f}; bezel stem on the PCB front")
    lines.append((f"Holder now sits on the bezel face ({BZ['z_f1']:.2f}, +{dz:.2f}): tube v0.2 engages the socket only {sock:.2f} of {HP['socket_len']:.1f}", RED))
    lines.append((f"    [check: tube +{dz:.2f} = {SP['tube_len'] + dz:.2f} if wanted; not changed]", RED))
    lines.append("Encoder bearing 1 now pressed in from the PCB back, flange on the back face (H2 on B in KiCad)")
    lines.append(kv.flag_od())
    lines.append(("Big gear BEHIND the PCB [A] (only 2 mm under the skirt); passes under the shaft flange", RED))
    lines.append(("    and the tube's wire exit [check]", RED))
    lines.append(f"Encoder: {enc.P['z_pinion']}T pinion in the 90T ring (ratio {enc.P['ratio']:.3f}), H2 {enc.P['centre_dist']:.1f} below the dial axis [K]; encoder TBC")
    lines.append(("Screen tail supplied 100 mm: short-tail variant needed [check]", RED))
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        sh.note("side", max(sh.bb["side"][1], -zp) + 6, sh.bb["side"][3] - 6 - i * 3.2, l, 8 if i == 0 else 6.5, **kw)
    title = "Knob stack v0.6 rev A — all current parts"
    sub = ["2026-10-31. PCB v0.5, motor, shaft v0.2, bezel, knob v0.3, encoder v0.2, holder, TFT, adapter.", "Front view = full section A-A. [S] = stock, [A] = assumed.",
           "Third-angle projection · mm · plan view drawn front-up"]
    sh.dxf(os.path.join(HERE, "knob-stack-v0.6.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "knob-stack-v0.6-drawing.png"), title, sub)
