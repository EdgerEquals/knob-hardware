"""26 Nov, sweep item A5: the detent spoke on the dial's lower part runs low (z 4.1-5.9) from the tube out to r 8.7, then steps up
to the flange level (z 5.75-7.25). The step cleared v0.30's centring-spring anchor post 2 (gone since v0.31). Section along the
spoke (mechanism 263°), with the room a full-depth spoke would take (dashed) and the in-plane deflection under the detent force.
  .venv/bin/python ../../tools/studies/detent_spoke_fig.py <out.png>   (from cad/knob-param)"""
import sys, os, json, math
import numpy as np
import pyvista as pv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from build123d import Plane, Vector
sys.path.insert(0, os.getcwd())
from knobparam.common import model
from knobparam.control_dial.parts import hall_arm as hall

D = dict(model.derive(model.default_params()))
ang = D["sp_ang"]; u = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0.0]); nrm = np.array([-u[1], u[0], 0.0])
r_in = D["dial_tube_od"] / 2 - 0.3; r_hi = D["sp_r_hi0"]; zf, zl = D["sp_z_fu"], D["ad_z_land"]; z0, z1 = D["fan_z0"], D["fan_top"]
E, F, r_load = 1700.0, D["det_force_max"], D["sp_r"]
w0, w1 = D["sp_w_lo"]; wh = D["sp_w_hi"]


def defl(full):
    """In-plane tip deflection (mm) of the spoke as a cantilever from the tube to the flange, the detent force tangential at sp_r."""
    n, s = 2000, 0.0
    for i in range(n):
        r = r_in + (r_load - r_in) * (i + 0.5) / n
        if r < r_hi:
            w = w0 + (w1 - w0) * (r - r_in) / (D["sp_r_join"] + 0.2 - r_in); h = (zl - z0) if full else (z1 - z0)
        else:
            w, h = wh, zl - z0 if r < D["sp_r_join"] + 0.2 else zl - zf
        s += F * (r_load - r) ** 2 / (E * h * w ** 3 / 12.0)
    return s * (r_load - r_in) / n


arm = hall.arm(D)
sec = arm & Plane(origin=(0, 0, 0), x_dir=tuple(u), z_dir=tuple(nrm))
idx = json.load(open(os.path.join(".cache-knob", "anim", "index.json")))["parts"]
A = math.radians(ang - 90.0); ua = np.array([math.cos(A), math.sin(A), 0.0]); na = np.array([-ua[1], ua[0], 0.0])
fig, ax = plt.subplots(figsize=(13, 6.4), dpi=110)
for name, col in (("base cradle", "#90a4ae"), ("idler pinion 2", "#8e24aa"), ("spring anchor pin 2", "#795548")):
    z = np.load(idx[name]["mesh"]); P, T = z["P"], z["T"]
    s = pv.PolyData(P, np.hstack([np.full((len(T), 1), 3), T]).astype(np.int64)).slice(normal=tuple(na), origin=(0, 0, 0))
    if s.lines.size:
        Q = s.points
        for a, b in s.lines.reshape(-1, 3)[:, 1:]:
            if Q[a] @ ua > 0: ax.plot([Q[a] @ ua, Q[b] @ ua], [Q[a, 2], Q[b, 2]], color=col, lw=0.9)
for e in sec.edges():
    p = [e.position_at(t) for t in np.linspace(0, 1, 24)]
    ax.plot([q.dot(Vector(*u)) for q in p], [q.Z for q in p], color="#1e88e5", lw=1.4)
ax.add_patch(Rectangle((r_in, z1), r_hi - r_in, zl - z1, fc="#ff9800", alpha=0.25, ec="#e65100", ls="--"))
d_now, d_full = defl(False), defl(True)
ax.text(r_in + 0.2, zl + 0.35, f"fill to the flange level (orange): +{(r_hi - r_in) * (w0 + w1) / 2 * (zl - z1):.0f} mm³", fontsize=10.5)
ax.text(8.8, 8.6, f"in-plane deflection at the flange,\ndetent force {F:.2f} N:\nnow {d_now * 1000:.1f} µm, filled {d_full * 1000:.1f} µm",
        fontsize=10.5)
ax.text(5.0, 2.2, "cradle (grey)", fontsize=10)
ax.set_xlim(2.5, 16); ax.set_ylim(1.5, 10); ax.set_aspect("equal")
ax.set_xlabel("r along the detent spoke, 263° (mm)"); ax.set_ylabel("z (mm; main board front 0)")
fig.text(0.01, 0.98, "Detent spoke step-up (sweep item A5): blue = the dial's lower part along the spoke", fontsize=14, weight="bold", va="top")
fig.text(0.01, 0.93, f"The spoke stays low to r {r_hi:g} to clear an anchor post removed in v0.31. A full-depth spoke fits (1.04 to the cradle, "
         "1.5 to idler pinion 2 over ±travel)\nbut the spoke is already stiff for what it carries.", fontsize=10.5, va="top")
fig.subplots_adjust(top=0.84, bottom=0.1)
fig.savefig(sys.argv[1])
print("wrote", sys.argv[1], f"defl now {d_now * 1000:.2f} um, full {d_full * 1000:.2f} um, F {F:.3f} N")
