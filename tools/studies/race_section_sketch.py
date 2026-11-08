"""The outer thrust race in section (8 Nov 2026, Ed: "can we just make the clear ball race bigger? it might be too small anyway").
A cut through the knob axis at one load ball, from the built model, with the race's thin places measured. Run from cad/knob-param:
  KNOBPARAM_CACHE=$PWD/.cache-knob PYTHONPATH=$PWD .venv/bin/python ../../tools/studies/race_section_sketch.py <out.png>"""
import math, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from build123d import Plane, Vector
from knobparam.common import model
from knobparam.assembly.build import build_all

D = model.derive(model.default_params())
parts, _, _, owner = build_all(D)
balls = parts["outer thrust load balls 30 x Ø2"]
c = balls.solids()[0].center()
th = math.atan2(c.Y, c.X)
u = (math.cos(th), math.sin(th))
pl = Plane(origin=(0, 0, 0), x_dir=(u[0], u[1], 0), z_dir=(-u[1], u[0], 0))
R0, R1, Z0, Z1 = 14.5, 24.5, -3.2, 7.5
COL = {"PCB": "#2e7d32", "base cradle": "#b3e5fc", "outer thrust": "#9e9e9e", "knob lower-cap land": "#ffcc80",
       "bottom internal ring": "#ffe0b2", "knob glass sleeve": "#e1f5fe", "emitter": "#ef9a9a", "idler": "#ce93d8",
       "hall": "#a5d6a7", "detent": "#d7ccc8", "control dial": "#cfd8dc", "encoder": "#cfd8dc", "case": "#eeeeee"}
fig, ax = plt.subplots(figsize=(13, 8.5), dpi=130)
seen = {}
for n, s in parts.items():
    b = s.bounding_box()
    rmax = max(math.hypot(x, y) for x in (b.min.X, b.max.X) for y in (b.min.Y, b.max.Y))
    if b.min.Z > Z1 or b.max.Z < Z0 or rmax < R0:
        continue
    try:
        sec = s.intersect(pl)
    except Exception:
        continue
    if sec is None:
        continue
    col = next((v for k, v in COL.items() if n.startswith(k)), "#f5f5f5")
    for f in sec.faces():
        for w in [f.outer_wire()]:
            pts = []
            for e in w.edges():
                for t in [i / 24 for i in range(25)]:
                    p = e.position_at(t)
                    pts.append((p.X * u[0] + p.Y * u[1], p.Z))
            if not pts or max(p[0] for p in pts) < R0 or min(p[0] for p in pts) > R1:
                continue
            ax.add_patch(Polygon(pts, closed=True, fc=col, ec="#333", lw=0.5, zorder=2 if n.startswith("outer") else 1))
            seen[n] = col
ax.set_xlim(R0, R1); ax.set_ylim(Z0, Z1); ax.set_aspect("equal"); ax.grid(alpha=0.15)
ax.set_xlabel("radius from the knob axis (mm)"); ax.set_ylabel("height above the PCB front (mm)")
r, rg, zb = D["ot_r"], D["ot_rg"], D["ot_z"]
# the measured thin places
ax.annotate("", (r + 1.6, 0), (r + 1.6, zb - rg), arrowprops=dict(arrowstyle="<->", color="#c62828", lw=1.4))
ax.text(r + 1.75, (zb - rg) / 2, f"clear race floor\nunder the groove {D['ot_land_th']:.2f}", color="#c62828", fontsize=9, va="center")
for x0, x1, lab in ((D["hb_root_r"], r - rg, f"{D['ot_land_in']:.2f}"), (r + rg, D["cap_r"], f"{D['ot_land_out']:.2f}")):
    ax.annotate("", (x0, zb + 0.15), (x1, zb + 0.15), arrowprops=dict(arrowstyle="<->", color="#c62828", lw=1.2))
    ax.text((x0 + x1) / 2, zb + 0.45, lab, color="#c62828", fontsize=9, ha="center")
ax.text(r, zb + 1.35, "top track's side walls beside the groove\n(knob cap: hub gear root inside, cap edge outside)", color="#c62828",
        fontsize=8.6, ha="center")
handles = [plt.Rectangle((0, 0), 1, 1, fc=c, ec="#333") for c in seen.values()]
ax.legend(handles, list(seen.keys()), fontsize=7.2, loc="lower left", ncol=2, framealpha=0.9)
ax.set_title(f"The thrust race in section at a load ball, model {D.get('version')}: Ø{D['ot_ball_d']:g} balls on r {r:.2f}; "
             f"groove r {rg:.2f}", fontsize=11, loc="left")
fig.tight_layout()
fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "race-section.png")
print("angle", round(math.degrees(th), 2), "parts", list(seen))
