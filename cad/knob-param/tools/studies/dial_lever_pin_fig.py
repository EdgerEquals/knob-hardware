# v0.30 finding (4 Nov): with the stop blocks gone, the cross rows see the lever's spring pin at ±travel: it reaches the opposite
# anchor post (touching), and that extension spring would have to shrink from 2.6 to ~1.3 hook to hook. Plan at z 8.0, at rest and
# at -travel, mechanism frame. Run from cad/knob-param:  PYTHONPATH=. python tools/studies/dial_lever_pin_fig.py <out dir>
import os, sys, math
sys.path.insert(0, ".")
OUT = sys.argv[1] if len(sys.argv) > 1 else "."

def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Circle
    from build123d import Rot
    from knobparam.common import model
    from knobparam.assembly.build import build_all
    from knobparam.assembly.plan_sheet import _cut_faces
    from knobparam.base_drive.parts.mech import springs_at
    D = model.derive(model.default_params()); parts, *_ = build_all(D)
    T = D["travel_deg"]; z = 8.0
    cr = parts["base cradle"]; blk = [s for n, s in parts.items() if n.startswith("detent block (")][0]
    dl = [s for n, s in parts.items() if n.startswith("control dial lower part")][0]
    pins = [s for n, s in parts.items() if n.startswith("spring anchor pin")]
    Dv = model.view(D, "base_drive")
    fig, axs = plt.subplots(1, 2, figsize=(14, 7.2), dpi=120)
    for ax, th, title in ((axs[0], 0.0, "At rest"), (axs[1], -T, f"At -{T:.2f}° (the hard stop)")):
        for s, col, al in ((cr, "#c9cfd4", 1), (blk, "#f2c14e", 1), (Rot(0, 0, th) * dl, "#1565c0", 0.55)):
            t = _cut_faces(s, "z", z)
            if t: ax.add_collection(PolyCollection(t, facecolors=col, edgecolors="none", alpha=al))
        for p in pins:
            t = _cut_faces(p, "z", z)
            if t: ax.add_collection(PolyCollection(t, facecolors="#455a64", edgecolors="none"))
        a = math.radians(D["sl_ang"] + th); px, py = D["sl_pin_r"] * math.cos(a), D["sl_pin_r"] * math.sin(a)
        ax.add_patch(Circle((px, py), D["sl_pin_d"] / 2, fc="#c62828", ec="none"))
        for k, (ax_, ay_) in enumerate(D["sl_anchor_xy"], 1):
            d = math.hypot(ax_ - px, ay_ - py)
            ax.plot([px, ax_], [py, ay_], color="#8d6e63", lw=2.0)
            ax.text((px + ax_) / 2 + 0.15, (py + ay_) / 2 + 0.25, f"spring {k}: {d:.2f}\ncentre to centre", fontsize=8)
        k_ = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
        ax.annotate("lever's spring pin (red)", (px, py), (2.5, -11.5), **k_)
        ax.annotate("post 2 + pin (on the block's arm)", D["sl_anchor_xy"][1], (-9.5, -2.0), **k_)
        ax.annotate("post 1 + pin (cradle)", D["sl_anchor_xy"][0], (6.5, -2.0), **k_)
        ax.set_xlim(-10, 12); ax.set_ylim(-13, 0); ax.set_aspect("equal"); ax.grid(alpha=0.2)
        ax.set_title(f"{title}: plan at z {z:g}", fontsize=10, loc="left")
    fig.text(0.01, 0.97, "v0.30 finding: at the hard stop the lever's spring pin meets the opposite anchor post, and that extension\n"
             "spring would have to shrink from 2.60 to 1.30 centre to centre (the v0.17 layout; the old stop blocks hid it).", fontsize=11, va="top")
    fig.subplots_adjust(top=0.86)
    out = os.path.join(OUT, "dial-lever-pin-v030.png"); fig.savefig(out); print("wrote", out)

if __name__ == "__main__":
    main()
