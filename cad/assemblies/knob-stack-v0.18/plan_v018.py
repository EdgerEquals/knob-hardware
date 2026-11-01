import sys, math, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knob-param")))
import numpy as np
from build123d import *
from knobparam.common import model; from knobparam.assembly.build import build_all; from knobparam.assembly import render as R
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
from matplotlib.patches import Patch, Circle
from multiprocessing import get_context
LIM = 23.0
def sect(job):
    n, path, z = job
    from knobparam.common.cache import load
    s = load(path); b = s.bounding_box()
    if not (b.min.Z < z < b.max.Z): return n, [], []
    f = Pos(-80, -80, z) * Box(160, 160, 1e-3, align=(Align.MIN, Align.MIN, Align.CENTER))
    try: r = s.intersect(f)
    except Exception: return n, [], []
    faces = r.faces() if r is not None else []
    tris, segs = [], []
    for fc in faces:
        if abs(fc.center().Z - z) > 1e-3 + 5e-4 and fc.geom_type != GeomType.PLANE: continue
        if abs(fc.normal_at(fc.center()).Z) < 0.99: continue
        try: vs, T = fc.tessellate(0.01, 0.2)
        except Exception: continue
        P = np.array([(v.X, v.Y) for v in vs]); tris += [P[list(t)] for t in T]
        for e in fc.edges():
            pts = np.array([(p.X, p.Y) for p in (e.positions(np.linspace(0, 1, 40)) if e.geom_type != GeomType.LINE else [e.position_at(0), e.position_at(1)])])
            segs.append(pts)
    return n, tris, segs
def main():
    D = model.derive(model.default_params()); parts, _, keys, _ = build_all(D)
    from knobparam.assembly.build import PATHS
    zA, zB, zC = 0.2, D["hv_z_mag0"] + D["hv_mag"][1] / 2, 0.5 * (D["fan_z0"] + D["fan_top"])
    zT, zS = D["bt_z"], D["sl_top"] + D["sl_spring_gap"] + D["sl_spring"][0] / 2
    zs = (zA, zB, zC, zT, zS, -0.8)
    pool = get_context("spawn").Pool(8)
    S = {}
    for z in zs:
        S[z] = {n: (t, sg) for n, t, sg in pool.map(sect, [(n, PATHS[n], z) for n in parts]) if t or sg}
    pool.close()
    fig, axs = plt.subplots(1, 3, figsize=(30, 12.5), dpi=130)
    mags = [n for n in parts if n.startswith("hall magnet")]; sens = [n for n in parts if n.startswith("hall sensor")]
    over_T = [n for n in parts if n.startswith("track ball")]
    over_S = [n for n in parts if n.startswith(("centring spring", "detent", "spring anchor"))]
    panels = [(axs[0], zA, [(zB, mags, "#c62828")], f"PLAN 1 at z = {zA:.2f}: Hall row on the PCB (green): H1,H2,H4,H5 TMAG5253,\nH3 = 3D TMAG5273 (SOT-23-6); dashed red = magnets above (z {zB:.2f})"),
              (axs[1], zB, [(zA, sens, "#111111")], f"PLAN 2 at z = {zB:.2f}: Hall arm + magnets through the cradle window,\npoles N/S/N/S/N (face down); dashed black = sensors below (z {zA:.2f})"),
              (axs[2], zC, [(zT, over_T, "#0d47a1"), (zS, over_S, "#e65100")], f"PLAN 3 at z = {zC:.2f}: fan, detent ears, lever + hard stops;\ndashed blue = Ø{D['bt_ball']:g} track balls (z {zT:.2f}), dashed orange = detent bosses,\ncentring springs (z {zS:.2f}); detents latch at 0 / ±{D['det_deg']:g}°")]
    for ax, z, others, ttl in panels:
        groups = {}
        if z == zA and "PCB" in S[-0.8]:
            t, sg = S[-0.8]["PCB"]; c = R.GROUPS[R.group_of("PCB")][1]
            ax.add_collection(PolyCollection(t, facecolors=R.lighten(c, 0.55), edgecolors=R.lighten(c, 0.55), linewidths=0.3, zorder=1)); groups[R.group_of("PCB")] = 1
        for n, (t, sg) in S[z].items():
            col = R.GROUPS[R.group_of(n)][1]
            if t: ax.add_collection(PolyCollection(t, facecolors=R.lighten(col, 0.25), edgecolors=R.lighten(col, 0.25), linewidths=0.3, zorder=2))
            if sg: ax.add_collection(LineCollection(sg, colors="#202020", linewidths=0.6, zorder=3))
            groups[R.group_of(n)] = 1
        for oz, names, oc in others:
            for n in names:
                if n in S[oz]: ax.add_collection(LineCollection(S[oz][n][1], colors=oc, linewidths=1.5, linestyles=(0, (4, 2.5)), zorder=5)); groups[R.group_of(n)] = 1
        ax.add_patch(Circle((0, 0), D["knob_od"] / 2, fill=False, ls=":", lw=1.4, ec="#1565c0", zorder=4))
        ax.text(D["knob_od"] / 2 * math.cos(math.radians(60)), D["knob_od"] / 2 * math.sin(math.radians(60)) + 0.4, f"knob Ø{D['knob_od']:.2f}", color="#1565c0", fontsize=11)
        ax.plot([-1.5, 1.5], [0, 0], color="k", lw=1.2, zorder=6); ax.plot([0, 0], [-1.5, 1.5], color="k", lw=1.2, zorder=6)
        ax.text(0.4, 0.4, "dial axis", fontsize=10, zorder=6)
        ax.plot([D["offset"]], [0], "k+", ms=12, zorder=6); ax.text(D["offset"] + 0.4, -1.1, "1220 axis", fontsize=10, zorder=6)
        fx, fy = D["fm_xy"]; ax.plot([fx], [fy], "k+", ms=10, zorder=6); ax.text(fx + 0.5, fy + 0.5, "716 feel", fontsize=10, zorder=6)
        if z == zA:
            for i, (r, a) in enumerate(zip(D["hv_r"], D["hv_phi_s"])):
                t = math.radians(a); lab = f"H{i + 1} " + ("TMAG5273" if D["hv_mid"] and i == D["hv_mid"]["idx"] else "5253")
                ax.annotate(lab, (r * math.cos(t), r * math.sin(t)), (r * math.cos(t) - 6 + 1.3 * i, r * math.sin(t) - 5.5 - 1.4 * i), fontsize=10, arrowprops=dict(arrowstyle="-", lw=0.6), zorder=8)
        if z == zB:
            for i, (r, a) in enumerate(zip(D["hv_r"], D["hv_phi_m"])):
                t = math.radians(a); pl = "N" if D["hv_pol"][i] > 0 else "S"
                ax.text(r * math.cos(t), r * math.sin(t), pl, fontsize=11, weight="bold", color="white" if pl == "N" else "#ffeb3b", ha="center", va="center", zorder=8)
        if z == zC:
            for a in D["det_angs"]:
                x, y = D["det_r"] * math.cos(math.radians(a)), D["det_r"] * math.sin(math.radians(a))
                ax.text(x * 1.18, y * 1.18, f"detent\n{a:.0f}°", fontsize=10, ha="center", va="center", color="#e65100", zorder=7)
            a = math.radians(D["sl_ang"]); ax.text(11.5 * math.cos(a) + 1.0, 11.5 * math.sin(a), "lever, 2 springs,\nhard stops", fontsize=10, color="#5d4037", zorder=7)
        ax.plot([-LIM + 1.5, -LIM + 11.5], [-LIM + 1.5] * 2, color="k", lw=4, solid_capstyle="butt"); ax.text(-LIM + 6.5, -LIM + 2.2, "10 mm", ha="center", fontsize=12)
        ax.set_xlim(-LIM, LIM); ax.set_ylim(-LIM, LIM); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(ttl, fontsize=12.5, loc="left", weight="bold")
        ax._groups = groups
    shown = sorted(set().union(*[a._groups for a in axs]))
    hand = [Patch(facecolor=R.lighten(R.GROUPS[i][1], 0.25), edgecolor="#222", label=R.GROUPS[i][0]) for i in shown]
    fig.legend(handles=hand, loc="lower center", ncol=5, fontsize=11, frameon=True, title="PART COLOURS (cut faces)", title_fontsize=12.5)
    fig.suptitle(f"Knob stack {D['version']} — plan views looking down the knob axis (+X = 1220, right)  ·  {D['hv_n']} magnets N/S/N/S/N × 4 TMAG5253 + 1 TMAG5273 (H3) at {D['hv_pitch']:g} pitch  ·  detents at 0/±{D['det_deg']:g}°, hard stop ±{D['travel_deg']:.1f}°  ·  feel {D['fg_ratio']:.2f}:1",
                 fontsize=16, weight="bold", x=0.01, ha="left", y=0.985)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.14, wspace=0.03)
    fig.savefig(sys.argv[1], dpi=fig.dpi)
if __name__ == "__main__": main()
