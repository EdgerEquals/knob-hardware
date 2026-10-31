"""Knob stack assembly v0.4 (2026-10-31): every current part, imported from the library (no new geometry here).
Supersedes v0.3 (../knob-stack-v0.3). Parts:
  PCB v0.3 (KiCad STEP, H1 Ø5.2 NPTH, M1 motor tabs)      pcbs/knob-main-pcb
  1220 motor at the 14.0 [A] offset (end cap on the PCB front)   motors/1220-coreless-planetary (placement as v0.3)
  brass shaft v0.2: 57.31 tube + 17.5 printed flange on the PCB back   shafts/fixed-shaft-brass-5x3-v0.2
  knob v0.1: cap + hub, internal ring, bottom ring, pinion (on the motor shaft), bronze bush   knob/knob-v0.1
  screen holder v0.1, 0.71" GC9D01 round TFT (tail folded), screen adapter board (KiCad STEP + envelopes)
      holders/screen-holder-v0.1, displays/tft-0.71-round-gc9d01, pcbs/screen-adapter
Knob/holder parts are authored with Z = height above the PCB front on the dial axis; they are moved here by
Pos(dial x, -dial y, PCB front Z). World axes as in tools/sheet.py (X panel x, Y = -panel y, Z toward the panel front)."""
import os, sys, itertools
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
for d in ("tools", "motors/1220-coreless-planetary", "pcbs/knob-main-pcb", "shafts/fixed-shaft-brass-5x3-v0.2",
          "knob/knob-v0.1", "holders/screen-holder-v0.1"):
    sys.path.insert(0, os.path.join(LIB, d))
import motor_gearbox as mg
import knob_main_pcb as pcb
import fixed_shaft_brass_v02 as shaft
import knob_gears as kg
import screen_holder as hold
from sheet import Sheet

M = mg.VARIANTS["motor-1220"]; F = pcb.kicad_facts(); SP = shaft.P; KP = kg.P; HP = hold.P
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

if __name__ == "__main__":
    board = pcb.board_solid(); zf = board.bounding_box().max.Z; zb = board.bounding_box().min.Z
    hx, hy = F["shaft_x"], F["shaft_y"]
    T = Pos(hx, -hy, zf)                       # knob/holder frame -> world
    hp = hold.placed_parts()
    parts = {
        "PCB": board,
        "motor": motor_placed(),
        "brass tube": shaft.placed(shaft.build_tube()),
        "flange": shaft.placed(shaft.build_flange()),
        "knob cap+hub": T * kg.build_knob(),
        "internal ring": T * kg.build_internal_ring(),
        "bottom ring": T * kg.build_bottom_ring(),
        "pinion": T * Pos(KP["offset"], 0, KP["h_pinion0"]) * kg.build_pinion(),
        "bronze bush": T * kg.build_bush(),
        "screen holder": T * hold.build_holder(),
        "TFT backing": T * hp["backing"], "TFT glass": T * hp["glass"], "TFT tail": T * hp["tail"],
        "adapter board": T * hp["board"],
    }
    for i, c in enumerate(hp["comps"]): parts[f"adapter part {('J1', 'U1')[i] if i < 2 else i}"] = T * c
    asm = Compound(children=list(parts.values()), label="knob-stack-v0.4")
    export_step(asm, os.path.join(HERE, "knob-stack-v0.4.step"))

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
    top = HP["z_glass_top"]; R = M["body_d"] / 2
    ko, ho = KP["knob_od"] / 2, HP["od"] / 2
    sh = Sheet(asm, gap=34, scale=1.05, label_pad=20)
    # front view
    sh.hdim("front", hx, F["motor_x"], -hy, -hy - KP["d_bot_tip"] / 2 - 5, f"{MOTOR_OFFSET:.1f} motor offset [A] TBC")
    sh.hdim("front", hx - ko, hx + ko, -hy, -hy + ko + 5, f"Ø{KP['knob_od']:.2f} knob OD (Ø{KP['d_bot_tip']:.1f} gear tip)")
    sh.hdim("front", hx - ho, hx + ho, -hy, -hy + ko + 13, f"Ø{HP['od']:.2f} holder OD")
    sh.hdim("front", x0, x1, -y1, -y1 - 8, f"{x1 - x0:.2f} PCB")
    sh.vdim("front", -y0, -y1, x1, x1 + 8, f"{y1 - y0:.2f} PCB")
    # plan view (y = Z, front up)
    sh.vdim("plan", zf, zf + top, hx - ho, x0 - 12, f"{top:.2f} overall above PCB front (glass top)")
    sh.vdim("plan", zf, zf + KP["h_top"], x1, x1 + 5, f"{KP['h_top']:.1f} knob top")
    sh.vdim("plan", zf, zf + KP["h_shaft_tip"], x1, x1 + 12, f"{KP['h_shaft_tip']:.1f} motor shaft tip")
    sh.vdim("plan", zb - SP["flange_t"], zb, hx - SP["flange_side"] / 2, x0 - 4, f"{SP['flange_t']:.1f} flange")
    lines = [f"PCB v0.3 + 1220 motor + brass shaft v0.2 ({SP['tube_len']:.2f} tube) + knob v0.1 + bush + holder + TFT + adapter",
             f"Pairwise interference: {len(parts)} parts, {checked} bbox-overlapping pairs checked (threshold {THR} mm³)"]
    if clashes:
        why = {"PCB / motor": f" (motor rear boss Ø{M['rear_boss_d']:.0f} × {M['rear_boss_len']:.1f} [A] into the PCB front)",
               "screen holder / TFT backing": " (COG ledge past the holder wall)", "screen holder / TFT glass": " (COG ledge past the holder wall)",
               "screen holder / TFT tail": " (folded tail through the holder wall)"}
        lines += [(f"CLASH: {k} {v:.2f} mm³{why.get(k, '')}", RED) for k, v in clashes.items()]
    else:
        lines.append("No solid clash")
    lines.append((f"Knob OD {KP['knob_od']:.2f} (gear tip Ø{KP['d_bot_tip']:.1f}) >= Ø{KP['bezel_d']:.0f} bezel [L] [check]", RED))
    lines.append(("Screen tail supplied 100 mm: short-tail variant needed [check]", RED))
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        sh.note("side", sh.bb["side"][1] + 4, sh.bb["side"][3] - i * 3.2, l, 8 if i == 0 else 6.5, **kw)
    title = "Knob stack v0.4 — all current parts"
    sub = ["2026-10-31. PCB v0.3, motor, shaft v0.2, knob v0.1, holder, TFT, adapter.", "Parts imported from the library. [A] = assumed.",
           "Third-angle projection · mm · plan view drawn front-up"]
    sh.dxf(os.path.join(HERE, "knob-stack-v0.4.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "knob-stack-v0.4-drawing.png"), title, sub)
