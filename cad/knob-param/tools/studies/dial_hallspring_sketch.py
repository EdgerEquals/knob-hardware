# Sketch for Danny (4 Nov 16:19, dial item 6): the centring springs lifted above the detent block, pulling a pin on a column that
# rises from the Hall arm's rib (Danny 16:06 "extend the hall arm vertical"; 16:02 "lift everything up"). The lever goes.
# Fixed anchors: posts rising from the cradle plate, at spots found free of the dial's lower part swept ±travel and every other
# part from the plate top to the spring height (a grid search on the model, knob v0.30, mechanism frame).
#   dial-hallspring-sketch.png  1: plan at the spring height with the free post spots, the chosen springs and the parts below
#                               (projected); 2: side view (developed along the arc) of the column, posts and heights; 3: numbers
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/dial_hallspring_sketch.py <out dir>
import os, sys, math, json
sys.path.insert(0, ".")
OUT = sys.argv[1] if len(sys.argv) > 1 else "."

RP = 8.0            # [A] pin radius on the rib
ZS = 15.0           # [A] spring axis: over the detent block top (13.55) + 0.6 + the spring's radius
COL_D = 2.4         # [A] column on the rib
POST_D = 2.4        # [A] anchor post (SLA, printed in the cradle)
CLR = 0.3           # [A] post to anything, at every dial angle
K_DIAL = 0.4        # N·mm/deg, the model's centring rate [A] (dial_spring)


def main():
    import numpy as np
    from build123d import Rot, Pos, Box, Align, Compound
    from knobparam.common import model
    from knobparam.common.util import cyl, sector
    from knobparam.assembly.build import build_all
    D = model.derive(model.default_params())
    parts, *_ = build_all(D)
    T = D["travel_deg"]; A0 = D["ha_ang0"]
    pol = lambda r, a: (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
    dl = [s for n, s in parts.items() if n.startswith("control dial lower part")][0]
    # the lever goes in this design: take it off the dial (radial bar at sl_ang out to sl_r, its pin up to sl_pin_top)
    lev_half = math.degrees((D["sl_w"] / 2 + 0.6) / D["sl_r"]) + 2.0
    dl = dl - sector(D["dial_tube_od"] / 2 + 0.05, D["sl_r"] + 0.6, lev_half, D["plate_t"], D["sl_pin_top"] + 0.5 - D["plate_t"], D["sl_ang"])
    zt = ZS + 1.0
    clip = sector(4.6, 16.5, 180, D["plate_t"] + 0.05, zt - D["plate_t"], 0.0)
    obst = []
    for n, s in parts.items():
        if n.startswith(("control dial lower part", "base cradle", "detent block (", "spring anchor pin", "centring spring")):
            continue
        try:
            b = s.bounding_box()
            if b.max.Z < D["plate_t"] or b.min.Z > zt:
                continue
            q = s & clip
            if q is not None and q.volume > 1e-3:
                obst.append((n, q))
        except Exception:
            pass
    cr_up = parts["base cradle"] & clip                               # the cradle above the plate top (motor collar etc.)
    for (px, py) in D["sl_anchor_xy"]:                                # its anchor post 1 goes too (post 2 is on the block's arm)
        cr_up = cr_up - cyl(D["sl_post_d"] / 2 + 0.05, D["plate_t"], 10.0, px, py)
    blk = [s for n, s in parts.items() if n.startswith("detent block (")][0]
    # v0.30's hanger + post 2 go with the lever: take the block without them (the head ends at its inner radius)
    blk_noh = blk & sector(D["ad_r"] - D["det_boss_d"] / 2 - 0.01, 20, 180, -1, 30, 0.0)
    obst += [("base cradle (above the plate)", cr_up), ("detent block", blk_noh & clip)]
    poses = [Rot(0, 0, t) * (dl & clip) for t in np.linspace(-T, T, 7)]
    # the column on the rib (moves with the dial)
    col = cyl(COL_D / 2, D["ha_rib_z_top"] - 0.01, ZS - 0.7 - D["ha_rib_z_top"] + 0.01, *pol(RP, A0))
    cols = [Rot(0, 0, t) * col for t in np.linspace(-T, T, 7)]
    dial_all = Compound(children=poses + cols); fixed = Compound(children=[q for _n, q in obst])
    free = []
    for side, angs in (("-", range(130, 212, 4)), ("+", range(238, 330, 4))):
        for a in angs:
            for r in (6.5, 8.0, 9.5, 11.0, 12.5, 14.0):
                post = cyl(POST_D / 2, D["plate_t"], ZS - 0.7 - D["plate_t"], *pol(r, a))
                d1 = post.distance_to(dial_all); d2 = post.distance_to(fixed)
                if min(d1, d2) >= CLR:
                    free.append(dict(side=side, a=a, r=r, d_dial=d1, d_fixed=d2))
    # springs: for each free pair, the torque arm d (axis to the spring line) and the length; prefer long, symmetric, big d
    P = np.array(pol(RP, A0))
    best = None
    for f1 in [f for f in free if f["side"] == "-"]:
        for f2 in [f for f in free if f["side"] == "+"]:
            Q1, Q2 = np.array(pol(f1["r"], f1["a"])), np.array(pol(f2["r"], f2["a"]))
            L1, L2 = np.linalg.norm(Q1 - P), np.linalg.norm(Q2 - P)
            d1 = abs(np.cross(P, Q1 - P)) / L1; d2 = abs(np.cross(P, Q2 - P)) / L2
            if min(L1, L2) < 4.5 or min(d1, d2) < 5.0:
                continue
            score = min(L1, L2) + 2 * min(d1, d2) - abs(L1 - L2) - abs(d1 - d2)
            if best is None or score > best[0]:
                best = (score, f1, f2, L1, L2, d1, d2)
    res = dict(free=free, best=None)
    if best:
        _s, f1, f2, L1, L2, d1, d2 = best
        th = math.radians(T)
        springs = []
        for f, L, d in ((f1, L1, d1), (f2, L2, d2)):
            k = K_DIAL * 180 / math.pi / (2 * d * d)                     # both in tension: 2 k d² per rad
            springs.append(dict(side=f["side"], a=f["a"], r=f["r"], L_rest=L, arm=d, k=k, dL=d * th))
        res["best"] = springs
    json.dump(res, open(os.path.join(OUT, "_hallspring.json"), "w"), indent=1)
    print(json.dumps(res["best"], indent=1)); print(len(free), "free post spots")

    # ---- figure ----
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Circle
    from knobparam.assembly.plan_sheet import _cut_faces
    fig = plt.figure(figsize=(18, 8.4), dpi=120)
    ax = fig.add_axes([0.03, 0.07, 0.46, 0.84]); ax2 = fig.add_axes([0.53, 0.40, 0.45, 0.50]); axt = fig.add_axes([0.53, 0.03, 0.45, 0.33])
    for z, al in ((5.0, 0.35), (8.0, 0.35), (12.0, 0.35)):
        for n, q in obst:
            b = q.bounding_box()
            if b.min.Z <= z <= b.max.Z:
                t = _cut_faces(q, "z", z)
                if t: ax.add_collection(PolyCollection(t, facecolors="#f2a03d" if "detent" not in n else "#f2c14e", edgecolors="none", alpha=al))
        for t_ in (-T, 0.0, T):
            t = _cut_faces(Rot(0, 0, t_) * dl, "z", z)
            if t: ax.add_collection(PolyCollection(t, facecolors="#1565c0", edgecolors="none", alpha=0.12 if t_ else 0.3))
    for t_ in (-T, 0, T):
        ax.add_patch(Circle(pol(RP, A0 + t_), COL_D / 2, fc="#1565c0" if t_ == 0 else "none", ec="#1565c0", lw=0.8, alpha=1 if t_ == 0 else 0.6))
    for f in free:
        ax.add_patch(Circle(pol(f["r"], f["a"]), 0.25, fc="#9e9e9e", ec="none"))
    k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    if res["best"]:
        for sp in res["best"]:
            q = pol(sp["r"], sp["a"])
            ax.add_patch(Circle(q, POST_D / 2, fc="#455a64", ec="none"))
            ax.plot([P[0], q[0]], [P[1], q[1]], color="#c62828", lw=2.5)
            ax.annotate(f"post {sp['side']}: r {sp['r']:g}, {sp['a']}°\nspring {sp['L_rest']:.1f} long, arm {sp['arm']:.1f}", q,
                        (q[0] - 7 if sp["side"] == "-" else q[0] + 1.0, q[1] - 3.5), **k)
    ax.annotate(f"column on the Hall arm's rib, r {RP:g}\n(rest; outlines at ±{T:.1f}°), pin at z {ZS:g}", P, (-3.0, 1.8), **k)
    ax.annotate("1220 motor", pol(13, 0), (10.5, 5.5), **k)
    ax.annotate("detent block", pol(14.5, 265), (2.0, -18.5), **k)
    ax.set_xlim(-19, 17); ax.set_ylim(-19, 9); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("x (mm, mechanism frame)"); ax.set_ylabel("y (mm)")
    ax.set_title(f"1. Plan: parts between the plate and z {zt:g} (cuts at z 5, 8, 12; dial blue, pale at ±travel); grey dots = free "
                 f"post spots (Ø{POST_D:g} + {CLR:g})", fontsize=9.5, loc="left")
    # ---- 2: side view, heights ----
    ax2.add_patch(plt.Rectangle((-8, 0), 16, D["plate_t"], fc="#c9cfd4"))
    ax2.text(-7.8, 1.2, "cradle plate", fontsize=8.5)
    ax2.add_patch(plt.Rectangle((-1.5, D["hv_z_mag0"]), 3.0, D["ha_rib_z_top"] - D["hv_z_mag0"], fc="#1565c0", alpha=0.6))
    ax2.text(-1.4, 5.0, "Hall arm\n(rib)", fontsize=8, color="white")
    ax2.add_patch(plt.Rectangle((-COL_D / 2, D["ha_rib_z_top"]), COL_D, ZS - 0.7 - D["ha_rib_z_top"], fc="#1565c0", alpha=0.9))
    ax2.text(COL_D / 2 + 0.2, (D["ha_rib_z_top"] + ZS) / 2, "new column on the rib", fontsize=8.5)
    for x in (-6.0, 6.0):
        ax2.add_patch(plt.Rectangle((x - POST_D / 2, D["plate_t"]), POST_D, ZS - 0.7 - D["plate_t"], fc="#455a64"))
    ax2.text(-7.6, ZS + 0.9, "anchor post (from the plate)", fontsize=8.5)
    ax2.plot([-6, 0, 6], [ZS, ZS, ZS], color="#c62828", lw=3)
    ax2.text(0.3, ZS + 0.3, f"springs, axis z {ZS:g}", fontsize=8.5, color="#c62828")
    ax2.axhline(D["det_z1"], color="#b07d00", ls="--", lw=0.8); ax2.text(3.0, D["det_z1"] - 0.6, f"detent block top {D['det_z1']:.2f}", fontsize=8, color="#b07d00")
    ax2.axhline(D["ha_rib_z_top"], color="#1565c0", ls=":", lw=0.8)
    ax2.set_xlim(-9, 9); ax2.set_ylim(0, ZS + 2.5); ax2.set_aspect("equal"); ax2.grid(alpha=0.2)
    ax2.set_xlabel("along the arc (schematic)"); ax2.set_ylabel("z (mm)")
    ax2.set_title("2. Side view (schematic, heights from the model)", fontsize=10, loc="left")
    axt.axis("off")
    lines = [f"Lever goes; the springs pull a pin on a column rising from the Hall arm's rib (r {RP:g}, {A0:g}°) to z {ZS:g}.",
             f"Travel at the pin: ±{RP * math.radians(T):.2f} along the arc. The end stop stays in the Hall slot (v0.30)."]
    if res["best"]:
        for sp in res["best"]:
            lines.append(f"Spring {sp['side']}: to a post at r {sp['r']:g}, {sp['a']}°: {sp['L_rest']:.1f} long at rest, torque arm {sp['arm']:.1f}, "
                         f"changes ±{sp['dL']:.2f}; rate {sp['k']:.3f} N/mm for {K_DIAL:g} N·mm/deg (both in tension)")
        lines.append("Both springs stay stretched through the whole travel if each is installed >= its change + a margin past free length.")
    else:
        lines.append("NO pair of free post spots gives springs >= 4.5 long with torque arms >= 5: see the grey dots.")
    lines += ["To check in the model: the posts' height vs SLA (slender), the spring's free length and initial tension (stock part),",
              "the rib's twist under the pull (a small Hall angle offset, proportional, calibrated out), the springs vs the dial at ±travel."]
    axt.text(0, 1.0, "\n".join(lines), fontsize=8.4, va="top", family="monospace")
    fig.text(0.03, 0.965, "Dial item 6, Danny's idea (16:02-16:06): the centring springs lifted above the detent block, pulling a column on "
             "the Hall arm (no lever). From the model (v0.30); the column, posts and springs are PROPOSED (sketch).", fontsize=10)
    out = os.path.join(OUT, "dial-hallspring-sketch.png"); fig.savefig(out); print("wrote", out)


if __name__ == "__main__":
    main()
