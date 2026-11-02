"""Fit the Waveshare-STEP MS-DO0164FMST02 into the v0.5 joystick grip block: clashes and plan cuts, both flex-exit ends.
Run from cad/joystick-param with the knob-param venv:  python fmst02_fit.py <board.stp> <out.png>
<board.stp> is esp32-s3-touch-amoled-1_64.stp from Waveshare's ESP32-S3-Touch-AMOLED-1.64 structure zip (Waveshare's file, not
committed here). The panel solid is cached as fmst02.brep next to <out.png>. Study for [Ed 16:14]; output docs/img/fmst02-in-grip-block-v0.5.png."""
import sys, os, math, pickle
sys.path.insert(0, os.getcwd())
stp, out = sys.argv[1], sys.argv[2]
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch
from build123d import import_step, Pos, Rot, Box, Align
from jsparam import params, parts

D = params.derive(params.P)
P = parts.build(D)
S = D["scr"]
z0 = D["z_scr0"]
print(f"z_scr0 {z0:.3f}  z_roof {D['z_roof']:.3f}  roof_t {D['roof_t']}  z_bz0 {D['z_bz0']:.3f}  scr_top {D['scr_top']:.3f}")
print(f"guides {D['g_xy']}  g_rboss_r {D['g_rboss_r']:.2f} g_ins_bot {D['g_ins_bot']:.2f}  peg boss r {D.get('p_rboss_r', 0):.2f} p_ins_bot {D.get('p_ins_bot', 0):.2f}")
print(f"press springs {D['cs_xy']}  bore r {D['cs_bore_r']:.2f}; db_sock_x {D.get('db_sock_x')}; fpc_x {D['fpc_x']:.2f}; half_w {D['half_w']:.2f} half_h {D['half_h']:.2f} bz_lip {D['bz_lip']}")

cache = os.path.join(os.path.dirname(out), "fmst02.brep")
if os.path.exists(cache):
    from build123d import import_brep
    scr = import_brep(cache)
else:
    c = import_step(stp)
    def find(s, name):
        if (getattr(s, "label", "") or "") == name: return s
        for ch in getattr(s, "children", []) or []:
            r = find(ch, name)
            if r is not None: return r
    scr = find(c, "MS-DO0164FMST02").solids()[0]
    from build123d import export_brep
    export_brep(scr, cache)
bb = scr.bounding_box()
cy = (bb.min.Y + bb.max.Y) / 2
back = scr & (Pos(0, 0, -5) * Box(80, 80, 5, align=(Align.CENTER, Align.CENTER, Align.MIN)))   # everything behind the panel

skip = ("top screen", "screen FPC", "screen jumper FPC")
res = {}
for tag, ang in (("exit +x (v0.5 side)", 90.0), ("exit -x", -90.0)):
    b = Pos(0, 0, z0) * Rot(0, 0, ang) * Pos(0, -cy, 0) * back
    hits = []
    for n, s in P.items():
        if n.startswith(skip): continue
        try:
            v = (b & s).volume
        except Exception:
            v = 0.0
        if v > 1e-3: hits.append((n, v))
    res[tag] = (b, sorted(hits, key=lambda t: -t[1]))
    print(tag); [print(f"   {n}: {v:.2f} mm3") for n, v in res[tag][1]]

def faces_at(solid, z):
    sl = solid & (Pos(0, 0, z - 0.001) * Box(200, 200, 0.002, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    tris = []
    for f in sl.faces():
        if abs(f.normal_at().Z) < 0.99: continue
        vs, ts = f.tessellate(0.02)
        tris += [[(vs[i].X, vs[i].Y) for i in t] for t in ts]
    return tris

levels = [(z0 - 0.6, "0.6 behind the glass (in the roof plate)"), (z0 - 1.9, "1.9 behind the glass (under the roof: bosses, springs)")]
fig, axs = plt.subplots(2, 2, figsize=(16, 10.5))
for col, (tag, (b, hits)) in enumerate(res.items()):
    for row, (z, what) in enumerate(levels):
        ax = axs[row][col]
        for n, s in P.items():
            if n.startswith(skip): continue
            bbn = s.bounding_box()
            if not (bbn.min.Z < z < bbn.max.Z): continue
            tr = faces_at(s, z)
            if tr: ax.add_collection(PolyCollection(tr, facecolors="#c9dbe3" if "carrier" in n else "#9aa3a8", edgecolors="none", alpha=0.9))
        tr = faces_at(b, z)
        if tr: ax.add_collection(PolyCollection(tr, facecolors="#e08a1e", edgecolors="none", alpha=0.55))
        ax.add_patch(plt.Rectangle((-S["w"] / 2, -S["h"] / 2), S["w"], S["h"], fill=False, ls="--", lw=0.7, color="k"))
        ax.set_xlim(-26, 26); ax.set_ylim(-17, 17); ax.set_aspect("equal"); ax.grid(True, lw=0.3)
        ax.set_title(f"{tag}: z {z:.2f}, {what}", fontsize=9)
        if row == 1:
            ax.text(-25.5, -16.3, "clashes: " + ("; ".join(f"{n.split(' (')[0]} {v:.1f}" for n, v in hits[:6]) or "none"), fontsize=7, va="bottom")
fig.legend(handles=[Patch(fc="#e08a1e", alpha=0.55, label="FMST02 folded flex + B2B header (from the Waveshare STEP)"),
                    Patch(fc="#c9dbe3", label="grip block (screen carrier) and joystick carrier"),
                    Patch(fc="#9aa3a8", label="inserts, springs, guides, peg"),
                    Patch(fc="none", ec="k", ls="--", label="glass outline 41.62 x 26.74")], loc="lower center", ncol=4, fontsize=8, frameon=False)
fig.suptitle("Joystick v0.5 grip block with the DO0164FMST02 dropped in (looking down on the panel, glass removed)", fontsize=11, x=0.01, ha="left")
fig.subplots_adjust(top=0.93, bottom=0.07, hspace=0.18, wspace=0.08)
fig.savefig(out, dpi=100); print("wrote", out)
