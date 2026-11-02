"""L-fold jumper study [Ed 17:05 "Yes"]: in the space under the carrier at the +x end, how long can the x-facing and y-facing legs be,
and what copper strain does that give under the ±slide (x, y) and the press (z)?
Legs (envelopes, the flex 'jmp_w' wide): R horizontal under the roof (takes the press), V1 down through the carrier slot facing x,
S1 standing on edge along y facing x, then a vertical crease, S2 standing on edge along x facing y, then the plug lead.
Clearances: every leg against every part that moves differently (carrier moved ±slide in x and y; fixed parts as they are).
Run from cad/joystick-param:  python jumper_lfold_study.py"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build123d import Pos
from jsparam import params, parts
from jsparam.parts import box

D = params.derive(params.P)
P = parts.build(D)
W, T = 4.0, 0.10                 # [A] leg width (~20 lines at 0.1/0.1, one layer), single-layer flex
C_CU = (0.006, 0.011)            # [A] copper distance from the neutral axis: 12 µm RA copper exactly centred / ±5 µm off
FAT = 0.003                      # [A] RA copper strain amplitude for ~1e6-1e7 cycles (switch: 1e6 per direction, Alps SKRH)
BEND = 0.3                       # [A] length eaten by each fold / crease
slide, press = D["slide"], D["press_travel"]
cm = D["tgt"]["cable_min"]
z_top = D["z_c0"] - cm           # standing legs stay one MJF tolerance under the carrier
z_bot = z_top - W
z_run = D["z_roof"] - cm - T
xe = D["jmp_x"] + D["jmp_stiff"][0] / 2
fixed = [n for n in P if n.startswith(("joystick daughterboard", "joystick cradle", "hold-down spring", "screen FPC socket",
                                        "SW1", "header", "socket", "cradle locating"))]
moving = [n for n in P if n.startswith(("joystick carrier", "brass insert", "grub screw", "guide screw", "guide sleeve",
                                         "compression spring", "screen carrier"))]

def clear(legs):
    worst = (9.0, "")
    for n in fixed:
        d = min(l.distance_to(P[n]) for l in legs); worst = min(worst, (d, n))
    for n in moving:
        for dx, dy in ((slide, 0), (-slide, 0), (0, slide), (0, -slide)):
            m = Pos(dx, dy, 0) * P[n]
            d = min(l.distance_to(m) for l in legs); worst = min(worst, (d, n + f" moved ({dx:+.2f},{dy:+.2f})"))
    return worst

def eps(d, L, c):
    return 6 * d / L ** 2 * c

print(f"z: run {z_run:.2f}, standing legs {z_bot:.2f}-{z_top:.2f}, carrier underside {D['z_c0']:.2f}, board top {D['z_db1']:.2f}")
for xv, ys, x2 in ((18.5, -3.0, 14.5), (18.5, -6.0, 14.7), (18.5, 3.0, 14.5), (18.8, -3.0, 14.5)):
    R = box(xe, xv, -W / 2, W / 2, z_run, z_run + T)
    V1 = box(xv - T / 2, xv + T / 2, -W / 2, W / 2, z_top, z_run)
    y0, y1 = (min(ys, -W / 2), W / 2) if ys < 0 else (-W / 2, max(ys, W / 2))
    S1 = box(xv - T / 2, xv + T / 2, y0, y1, z_bot, z_top)
    S2 = box(x2, xv, ys - T / 2, ys + T / 2, z_bot, z_top)
    w = clear([R, V1, S1, S2])
    L = dict(R=xv - xe - BEND, V1=z_run - z_top - 2 * BEND, S1=(y1 - y0) - 2 * BEND, S2=xv - x2 - 2 * BEND)
    kx = L["V1"] ** 3 + L["S1"] ** 3
    rows = []
    for c in C_CU:
        ex = max(eps(slide * L["V1"] ** 3 / kx, L["V1"], c), eps(slide * L["S1"] ** 3 / kx, L["S1"], c))
        ey = eps(slide, L["S2"], c); ez = eps(press, L["R"], c)
        rows.append(f"c {c * 1000:.0f} µm: x {100 * ex:.3f}% ({FAT / ex:.1f}×), y {100 * ey:.3f}% ({FAT / ey:.1f}×), press {100 * ez:.3f}% ({FAT / ez:.1f}×)")
    print(f"\nV1/S1 plane x {xv}, S2 at y {ys} from x {x2}: legs R {L['R']:.2f}, V1 {L['V1']:.2f}, S1 {L['S1']:.2f}, S2 {L['S2']:.2f}")
    print(f"   nearest at the full slide: {w[1]} {w[0]:.2f} (need >= {cm})")
    for r in rows:
        print("   " + r)


# ---- [Ed 17:13] fewer conductors (no touch): a narrow flex lets the legs run low under the carrier, where there is length ----
# R under the roof, V1 down the slot (faces x), S1 on edge along y (faces x), S2 on edge along -x at y2 (faces y),
# a 180° crease, S3 back along +x at y3 (faces y), lead down onto the plug. Legs sit just over the plug (z band from plug top + cm).
print("\n==== narrow flex, low legs ====")
z_lo = D["z_db1"] + D["db_fpc_sock"][2] + 0.3 + cm
for w, xv, y2, y3, xa, xb in ((2.2, 18.5, -4.0, -3.2, 9.0, 14.0), (2.5, 18.5, -4.0, -3.2, 9.0, 14.0), (3.0, 18.5, -4.0, -3.2, 9.0, 14.0)):
    zb, zt = z_lo, z_lo + w
    R = box(xe, xv, -w / 2, w / 2, z_run, z_run + T)
    V1 = box(xv - T / 2, xv + T / 2, -w / 2, w / 2, zt, z_run)
    S1 = box(xv - T / 2, xv + T / 2, y2, w / 2, zb, zt)
    S2 = box(xa, xv, y2 - T / 2, y2 + T / 2, zb, zt)
    S3 = box(xa, xb, y3 - T / 2, y3 + T / 2, zb, zt)
    wc = clear([R, V1, S1, S2, S3])
    L = dict(R=xv - xe - BEND, V1=z_run - zt - 2 * BEND, S1=(w / 2 - y2) - 2 * BEND, S2=xv - xa - 2 * BEND, S3=xb - xa - 2 * BEND)
    print(f"\nwidth {w} (lines at 0.2 pitch: {int((w - 0.5) / 0.2) + 1}), legs z {zb:.2f}-{zt:.2f}: R {L['R']:.2f}, V1 {L['V1']:.2f}, "
          f"S1 {L['S1']:.2f}, S2 {L['S2']:.2f}, S3 {L['S3']:.2f}")
    print(f"   nearest at the full slide: {wc[1]} {wc[0]:.2f} (need >= {cm})")
    for c in C_CU:
        kx = L["V1"] ** 3 + L["S1"] ** 3; ky = L["S2"] ** 3 + L["S3"] ** 3
        ex = max(eps(slide * L[k] ** 3 / kx, L[k], c) for k in ("V1", "S1"))
        ey = max(eps(slide * L[k] ** 3 / ky, L[k], c) for k in ("S2", "S3"))
        ez = eps(press, L["R"], c)
        print(f"   c {c * 1000:.0f} µm: x {100 * ex:.3f}% ({FAT / ex:.1f}×), y {100 * ey:.3f}% ({FAT / ey:.1f}×), press {100 * ez:.3f}% ({FAT / ez:.1f}×)")
