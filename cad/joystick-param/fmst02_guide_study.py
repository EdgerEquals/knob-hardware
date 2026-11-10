"""Study for the guide / press-spring decision at the +x end (after [Ed 16:22]): the DO0164FMST02 goes in with its flex leaving -x, so
its B2B header sits at x +11.75; the custom jumper's top end (socket + stiffener) hangs under it. Which guide and press-spring
positions clear it, and do the existing joystick checks still pass?
Run from cad/joystick-param with the knob-param venv:  python fmst02_guide_study.py <fmst02.brep>
The jumper's top end is an envelope [A] until the panel's B2B family is known.
Historical (v0.6): it reads the press springs and the press peg, which v0.8 removed; run it on the v0.6 model (git 4fbcae0)."""
import sys, os, copy, itertools
sys.path.insert(0, os.getcwd())
from build123d import import_brep, Pos, Rot, Box, Align, Cylinder
from jsparam import params, parts, checks

scr = import_brep(sys.argv[1])
bb = scr.bounding_box(); cy = (bb.min.Y + bb.max.Y) / 2

# jumper top end envelope [A]: socket 9.0 (y) x 3.4 (x) round the 8.0 x 2.5 plug, from 1.3 behind the glass (header base) to 0.25 past
# the plug tip; stiffener + flex 0.3 under it, 10.0 x 4.4; the flex (8.0 wide, 0.12) leaves +x under the stiffener to x 16.
HX = 11.75
def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)

def jumper_top(D):
    zg = D["z_scr0"]
    z_tip = zg - 2.15
    s0, s1 = z_tip - 0.25, zg - 1.3
    st0 = s0 - 0.3
    return (box(HX - 1.7, HX + 1.7, -4.5, 4.5, s0, s1) + box(HX - 2.2, HX + 2.2, -5.0, 5.0, st0, s0)
            + box(HX + 2.2, D["db_sock_x"] + 0.5, -4.0, 4.0, st0, st0 + 0.12))

def study(label, sets):
    P0 = copy.deepcopy(params.P)
    for k, v in sets.items():
        P0[k] = v
    D = params.derive(P0)
    P = parts.build(D)
    jt = jumper_top(D)
    panel = Pos(0, 0, D["z_scr0"]) * Rot(0, 0, -90) * Pos(0, -cy, 0) * scr
    # what the jumper top and the panel's header end hit (the roof plate itself gets pockets, so the screen carrier is judged by its bosses)
    bosses = []
    for (x, y) in D["g_xy"]:
        bosses.append((f"guide roof boss ({x:+.1f},{y:+.1f})", Pos(x, y, (D["g_ins_bot"] + D["z_roof"]) / 2)
                       * Cylinder(D["g_rboss_r"], D["z_roof"] - D["g_ins_bot"])))
    for (x, y) in D["cs_xy"]:
        bosses.append((f"press spring + pilot ({x:+.1f},{y:+.1f})", Pos(x, y, D["z_roof"] - 1.5) * Cylinder(D["cs_bore_r"], 3.0)))
    bosses.append(("peg roof boss", Pos(0, 0, (D["p_ins_bot"] + D["z_roof"]) / 2) * Cylinder(D["p_rboss_r"], D["z_roof"] - D["p_ins_bot"])))
    near = []
    for n, s in bosses + [(n, s) for n, s in P.items() if n.startswith(("guide", "press peg", "compression spring", "brass insert"))]:
        d = jt.distance_to(s)
        near.append((d, n))
    near.sort()
    rows = checks.run(D, P)
    cl = checks.clashes(P)
    bad = [r for r in rows if not r["ok"]]
    # panel back depth over each guide insert (the insert top is 0.6 under the glass now)
    over = []
    for (x, y) in D["g_xy"] + [(0.0, 0.0)]:
        col = Pos(x, y, D["z_scr0"] - 1.5) * Cylinder(D["guide"]["ins"]["od"] / 2 + 0.3, 3.0)
        b = (panel & col).bounding_box() if (panel & col).volume > 1e-4 else None
        over.append((x, y, round(D["z_scr0"] - b.min.Z, 2) if b else 0.0))
    print(f"\n== {label}: guides {D['g_xy']}, press springs {D['cs_xy'][:2]} ==")
    print("   nearest to the jumper top end: " + "; ".join(f"{n} {d:.2f}" for d, n in near[:4]))
    print(f"   panel back depth over the guide / peg inserts (mm behind the glass): {over}  (insert top sits 0.6 under the glass now)")
    print(f"   joystick checks: {len(rows) - len(bad)}/{len(rows)} PASS; clashes {len(cl)}")
    for r in bad:
        print(f"     FAIL {r['name']}: {r['value']:.3f} {r['target']}  {r['note'][:110]}")
    for k, v in cl.items():
        print(f"     CLASH {k}: {v:.3f}")

study("now (v0.5)", {})
study("guides (±6.5, 0)", {"guide_xy": (6.5, 0.0)})
study("guides (6.5, 2.0) / (-6.5, -2.0)", {"guide_xy": (6.5, 2.0)})
study("guides (±6.5, 0), springs y ±6.2", {"guide_xy": (6.5, 0.0), "cs_xy_v05": (11.5, 6.2)})
study("guides (±6.0, 0), springs y ±6.2", {"guide_xy": (6.0, 0.0), "cs_xy_v05": (11.5, 6.2)})
