# Sketch for Danny (4 Nov, dial item 6, his idea): compression centring springs + the hard stop in the Hall arm's slot through the
# cradle plate (instead of the extension springs on anchor posts and the r 7 stop blocks, which float / are too small).
# Existing geometry is cut from the model (knob v0.29, mechanism frame); the springs, pockets and stop bumps are PROPOSED, drawn
# from the numbers below (not in the model).
#   dial-cspring-sketch.png  1: plan at z 2.6 (the arm in its slot, mid height of the arm's part in the plate) with the proposal;
#                            2: one spring and its pocket, close up, at the three states (centre, arm away, arm at the stop)
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/dial_cspring_sketch.py <out dir>
import os, sys, math
sys.path.insert(0, ".")
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."

# ---- proposal [A] ----
RS = 7.4                      # spring axis radius: the largest with room both sides (r 7.8 and out run into the feel gear's pocket on the - side)
ZS = 2.6                      # spring axis height (the arm is in the plate over z 1.75-3.5)
K_DIAL = 0.4                  # N·mm/deg, the model's centring rate [A] (dial_spring), kept
OD, WIRE = 1.5, 0.15          # 316 stainless [A]
G = 69e3                      # N/mm², 316 spring wire [A]
STOP_R = {"-": 15.7, "+": 10.7}   # stop contact at a Hall pad each side: the largest radius with solid plate behind it


def spring(T_deg):
    d, Dm = WIRE, OD - WIRE
    travel = RS * math.radians(T_deg)
    k = K_DIAL * 180 / math.pi / (2 * RS * RS)            # each spring, both preloaded: K = 2 k r²
    n = G * d ** 4 / (8 * Dm ** 3 * k)
    n = round(n * 2) / 2; k = G * d ** 4 / (8 * Dm ** 3 * n)
    pre = travel + 0.05                                     # preload ≥ travel: both always push (linear, like now)
    solid = (n + 2) * d
    Lc = solid + 0.3 + travel                              # at full travel 0.3 over solid
    L0 = Lc + pre
    C = Dm / d; Kw = (4 * C - 1) / (4 * C - 4) + 0.615 / C
    Fmax = k * (pre + travel); tau = 8 * Fmax * Dm * Kw / (math.pi * d ** 3)
    return dict(k=k, n=n, travel=travel, pre=pre, solid=solid, Lc=Lc, L0=L0, F0=k * pre, Fmax=Fmax, tau=tau, C=C,
                pocket=Lc - travel, T_end=2 * k * RS * RS * math.radians(T_deg))


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Rectangle, Polygon
    from build123d import Vector
    from knobparam.common import model
    from knobparam.assembly.build import build_all
    from knobparam.assembly.plan_sheet import _cut_faces
    D = model.derive(model.default_params())
    parts, *_ = build_all(D)
    body = sorted(parts["base cradle"].solids(), key=lambda q: -q.volume)[0]
    dl = [s for n, s in parts.items() if n.startswith("control dial lower part")][0]
    T = D["travel_deg"]
    sp = spring(T)
    pol = lambda r, a: (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
    ins = lambda s, r, a, z: s.is_inside(Vector(*pol(r, a), z))
    phi_at = lambda r: float(np.interp(r, D["hv_r"], D["hv_phi_m"]))

    def edges(r):   # bar edges and slot walls along the arc r at ZS
        bar = [a for a in np.arange(phi_at(r) - 15, phi_at(r) + 15, 0.05) if ins(dl, r, a, ZS)]
        out = {}
        for sg, key in ((-1, "-"), (1, "+")):
            a = phi_at(r)
            while not ins(body, r, a, ZS) and abs(a - phi_at(r)) < 80:
                a += sg * 0.05
            w = a
            while ins(body, r, a, ZS) and abs(a - phi_at(r)) < 120:
                a += sg * 0.05
            out[key] = (w, a)
        return min(bar), max(bar), out

    # spring pockets: room check (pocket Ø OD+0.2, 0.45 wall all round; open at the plate top)
    rep = []
    b0, b1, ew = edges(RS)
    pockets = {}
    for key, bar_edge in (("-", b0), ("+", b1)):
        sg = -1 if key == "-" else 1
        a_wall_new = bar_edge + sg * math.degrees(sp["travel"] / RS)          # stop-side wall at exactly the travel (proposed)
        a_end = a_wall_new + sg * math.degrees(sp["pocket"] / RS)
        # each line of the pocket's envelope (radial ±(OD/2 + 0.1 + 0.45 wall), z ZS-0.95 floor wall .. ZS): solid run past its own
        # existing slot wall, against what the pocket needs past the existing wall at RS (pocket - the 0.55 now cleared + 0.6 end wall)
        old = ew[key][0]
        need = sp["pocket"] - (abs(old - a_wall_new) * math.pi / 180 * RS) + 0.6
        runs = []
        for dr in (-(OD / 2 + 0.55), 0.0, OD / 2 + 0.55):
            for dz in (-0.95, 0.0, 0.7):
                r = RS + dr; a = a_wall_new
                while not ins(body, r, a, ZS + dz) and abs(a - a_wall_new) < 30:
                    a += sg * 0.05
                s0 = a
                while ins(body, r, a, ZS + dz) and abs(a - s0) < 60:
                    a += sg * 0.05
                runs.append(abs(a - a_wall_new) * math.pi / 180 * RS)
        pockets[key] = (a_wall_new, a_end)
        rep.append(f"{key} side: pocket needs {need:.2f} past the existing wall; the shortest solid line of its envelope runs "
                   f"{min(runs):.2f} past the new wall")
    stops = {}
    for key, r in STOP_R.items():
        b0s, b1s, ews = edges(r)
        w, e = ews[key]
        stops[key] = (r, b0s if key == "-" else b1s, w, abs(e - w) * math.pi / 180 * r)
    print("\n".join(rep)); print(sp); print(stops)
    global ROOM
    ROOM = " / ".join(x.split("runs ")[1].split(" past")[0] for x in rep) + " of solid past the wall"

    fig = plt.figure(figsize=(19, 8.6), dpi=120)
    ax = fig.add_axes([0.04, 0.07, 0.46, 0.84]); ax2 = fig.add_axes([0.53, 0.42, 0.44, 0.46]); axt = fig.add_axes([0.53, 0.03, 0.46, 0.36])
    ax.add_collection(PolyCollection(_cut_faces(body, "z", ZS), facecolors="#c9cfd4", edgecolors="none"))
    t = _cut_faces(dl, "z", ZS)
    ax.add_collection(PolyCollection(t, facecolors="#1565c0", edgecolors="none", alpha=0.75))
    for sg in (-1, 1):   # the arm at ±travel
        c, s_ = math.cos(math.radians(sg * T)), math.sin(math.radians(sg * T))
        tt = [[(x * c - y * s_, x * s_ + y * c) for x, y in p] for p in t]
        ax.add_collection(PolyCollection(tt, facecolors="#1565c0", edgecolors="none", alpha=0.13))
    for n, s in parts.items():
        if any(w in n for w in ("feel compound gear", "detent block locating pin", "detent train pedestal", "idler pin")):
            b = s.bounding_box()
            if b.min.Z <= ZS <= b.max.Z:
                tt = _cut_faces(s, "z", ZS)
                if tt:
                    ax.add_collection(PolyCollection(tt, facecolors="#f2a03d", edgecolors="none", alpha=0.85))
    # proposal: springs (red) in pockets, stop bumps (green)
    for key, (aw, ae) in pockets.items():   # ARC pockets, concentric with the dial axis [Ed 4 Nov 13:48 "an arc would be more ideal"]
        sg = -1 if key == "-" else 1
        L = sp["Lc"]; a_bar = aw - sg * math.degrees(sp["travel"] / RS)
        ro, ri = RS + OD / 2 + 0.1, RS - OD / 2 - 0.1
        th = np.linspace(ae, aw, 30)
        band = [pol(ro, t) for t in th] + [pol(ri, t) for t in th[::-1]]
        ax.add_patch(Polygon(band, closed=True, fc="white", ec="#c62828", lw=0.8))
        n_z = 18
        zz = [pol(RS + (OD / 2) * (1 if i % 2 else -1), ae - sg * math.degrees(L * i / n_z / RS)) for i in range(n_z + 1)]
        ax.plot([q[0] for q in zz], [q[1] for q in zz], color="#c62828", lw=1.0)
    for key, (r, bar_edge, w, solid) in stops.items():
        sg = -1 if key == "-" else 1
        a_new = bar_edge + sg * T
        th = np.radians(np.linspace(a_new, w, 8))
        p = [pol(r - 1.0, a_new), pol(r + 1.0, a_new), pol(r + 1.0, w), pol(r - 1.0, w)]
        ax.add_patch(Polygon(p, closed=True, fc="#2e7d32", ec="none", alpha=0.9))
    k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    ax.annotate(f"compression springs on an arc at r {RS:g}, one each side,\nin arc pockets in the plate (proposed)", pol(RS, pockets["+"][1]), (-6.5, 1.6), **k)
    ax.annotate("", pol(RS, pockets["-"][1]), (-6.0, 1.5), **k)
    ax.annotate(f"stop bump (proposed): the arm's pad at r {STOP_R['-']:g}\nmeets it at -{T:.2f}°; {stops['-'][3]:.1f} of plate behind",
                pol(STOP_R["-"], stops["-"][2]), (-19.5, -15.8), **k)
    ax.annotate(f"stop bump (proposed): pad at r {STOP_R['+']:g} at +{T:.2f}°;\n{stops['+'][3]:.1f} of plate behind (at r 14-16 only ~1.0:\nthe detent block's pin hole)",
                pol(STOP_R["+"], stops["+"][2]), (-8.5, -19.3), **k)
    ax.annotate("Hall arm (dial), at rest; pale at ±travel", pol(12.0, phi_at(12.0)), (-19.5, 1.2), **k)
    ax.annotate("feel compound gear (its pocket thins the - side at r 10-12)", (-11.2, -3.6), (-19.5, 2.4), **k)
    for r in (RS, 10.7, 15.7):
        th = np.radians(np.linspace(185, 265, 60))
        ax.plot(r * np.cos(th), r * np.sin(th), lw=0.4, color="k", ls=":")
    ax.set_xlim(-20, 3); ax.set_ylim(-20, 3); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("x (mm, mechanism frame)"); ax.set_ylabel("y (mm)")
    ax.set_title(f"1. Plan at z {ZS:g} through the cradle plate and the Hall arm (model v0.29) + the proposal", fontsize=10, loc="left")
    # ---- 2: one spring, three states (straightened along its arc) ----
    y = 0
    for lab, L, bar_x in (("arm at centre", sp["Lc"], sp["pocket"] + sp["travel"]),
                          (f"arm {T:.1f}° away: spring {sp['Lc'] + sp['travel']:.2f} long, still pushing", sp["Lc"] + sp["travel"], sp["pocket"] + 2 * sp["travel"]),
                          (f"arm at the stop: spring {sp['pocket']:.2f}, {sp['pocket'] - sp['solid']:.2f} over solid", sp["pocket"], sp["pocket"])):
        ax2.add_patch(Rectangle((-0.8, y - 1.3), 0.8, 2.6, fc="#c9cfd4"))                      # pocket end wall
        ax2.add_patch(Rectangle((0, y - (OD / 2 + 0.1) - 0.45), sp["pocket"], 0.45, fc="#c9cfd4"))   # pocket side walls
        ax2.add_patch(Rectangle((0, y + (OD / 2 + 0.1)), sp["pocket"], 0.45, fc="#c9cfd4"))
        ax2.add_patch(Rectangle((sp["pocket"], y + 0.0 - 1.3), 0.0001, 2.6, fc="none"))
        ax2.plot([sp["pocket"], sp["pocket"]], [y - 1.3, y - (OD / 2 + 0.1) - 0.45], color="#2e7d32", lw=3)   # slot wall = the stop face
        ax2.plot([sp["pocket"], sp["pocket"]], [y + (OD / 2 + 0.1) + 0.45, y + 1.3], color="#2e7d32", lw=3)
        zz = [(L * i / 16, y + OD / 2 * (1 if i % 2 else -1)) for i in range(17)]
        ax2.plot([q[0] for q in zz], [q[1] for q in zz], color="#c62828", lw=1.2)
        ax2.add_patch(Rectangle((bar_x, y - 1.3), 0.6, 2.6, fc="#1565c0", alpha=0.8))
        ax2.text(-0.9, y + 1.45, lab, fontsize=8.5)
        y -= 3.6
    ax2.set_xlim(-1.2, 6.5); ax2.set_ylim(y + 1.6, 3.2); ax2.set_aspect("equal"); ax2.axis("off")
    ax2.set_title("2. One spring, straightened: pocket grey, slot wall (stop) green, arm blue", fontsize=10, loc="left")
    axt.axis("off")
    axt.text(0, 1.0, "\n".join([
        f"Spring [A]: 316 stainless, OD {OD:g}, wire {WIRE:g}, {sp['n']:g} active coils (C {sp['C']:.0f}), free {sp['L0']:.2f}, "
        f"solid ~{sp['solid']:.2f}",
        f"Rate {sp['k']:.3f} N/mm each at r {RS:g}: the two together give {K_DIAL:g} N·mm/deg, the model's centring rate now",
        f"Preload {sp['pre']:.2f} (≥ the {sp['travel']:.2f} travel at r {RS:g}), so both always push: {sp['F0']:.2f} N each at centre, "
        f"{sp['Fmax']:.2f} N at full travel",
        f"Torque at ±{T:.2f}°: {sp['T_end']:.1f} N·mm (as now). Shear stress at full travel ~{sp['tau']:.0f} MPa: HIGH for fine",
        "stainless wire; a spring maker's stock part to confirm, or a softer feel / bigger radius.",
        f"Arc pocket at r {RS:g}, {sp['pocket']:.2f} deep, Ø{OD + 0.2:g}, open at the plate top; -/+ side "f"{ROOM}.",
        f"Stop: the slot wall brought in to meet a pad at exactly ±{T:.2f}°; the arm, not the springs, takes the hand twist",
        f"(241 mNm [A] -> ~{241 / STOP_R['-']:.0f} N at r {STOP_R['-']:g}, ~{241 / STOP_R['+']:.0f} N at r {STOP_R['+']:g}). "
        "Goes: the lever, both stop blocks, both posts and pins.",
        "To check in the model: print tolerance on the stop angle (it must stay past the ±10° detent), a flat on the arm",
        "for each spring, a lead-in on the arm's bottom edges to push the springs back as it goes in."]), fontsize=8.0, va="top",
        family="monospace")
    fig.text(0.04, 0.965, "Dial item 6 (Danny's idea): compression centring springs and the hard stop in the Hall arm's slot through the "
             "cradle plate. Grey/blue/orange from the model (v0.29); red springs and green stop bumps are PROPOSED (sketch).", fontsize=10)
    out = os.path.join(OUT, "dial-cspring-sketch.png"); fig.savefig(out); print("wrote", out)


if __name__ == "__main__":
    main()
