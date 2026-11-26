"""26 Nov, sweep item A4: the Hall arm rib's root (r 4.06-4.94) still stands at z 4.61 over the thrust cage removed on 2 Nov.
Section through the rib's centre line, before (cage step, the v0.15 Hall spoke inside) and after (root at ha_rib_z_low like the
rest of the rib), with the cradle from the cached model.
  .venv/bin/python ../../tools/studies/rib_root_fig.py <out.png>   (from cad/knob-param)"""
import sys, os, json, math
import numpy as np
import pyvista as pv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from build123d import Plane, Vector
sys.path.insert(0, os.getcwd())
from knobparam.common import model
from knobparam.control_dial.parts import hall_arm as hall
from knobparam.control_dial.checks import _rib_defl

D = dict(model.derive(model.default_params()))
OLD = dict(D); OLD["ha_rib_z_cage"] = D["hv_spoke_z0"]; OLD["tb_on"] = True   # tb_on only gates the old spoke inside arm()
ang = D["ha_ang0"]
u = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0.0]); nrm = np.array([-u[1], u[0], 0.0])


def section(solid):
    out = []
    sec = solid & Plane(origin=(0, 0, 0), x_dir=tuple(u), z_dir=tuple(nrm))
    for e in sec.edges():
        pts = [e.position_at(t) for t in np.linspace(0, 1, 24)]
        out.append(np.array([[p.dot(Vector(*u)), p.Z] for p in pts]))
    return out


idx = json.load(open(os.path.join(".cache-knob", "anim", "index.json")))["parts"]
def mesh_cut(name):
    z = np.load(idx[name]["mesh"]); P, T = z["P"], z["T"]
    A = math.radians(ang - 90.0)   # cache meshes are in the panel frame (mechanism turned -90°)
    ua = np.array([math.cos(A), math.sin(A), 0.0]); na = np.array([-ua[1], ua[0], 0.0])
    s = pv.PolyData(P, np.hstack([np.full((len(T), 1), 3), T]).astype(np.int64)).slice(normal=tuple(na), origin=(0, 0, 0))
    L = s.lines.reshape(-1, 3)[:, 1:] if s.lines.size else []
    Q = s.points
    return [(np.array([Q[a] @ ua, Q[b] @ ua]), np.array([Q[a, 2], Q[b, 2]])) for a, b in L]


fig, axs = plt.subplots(1, 2, figsize=(15, 6.6), dpi=110, sharey=True)
cr = mesh_cut("base cradle")
for ax, (DD, title) in zip(axs, ((OLD, "Now: root held up at z 4.61 over the old cage"), (D, "Option A: root at z 3.85 like the rest"))):
    for x, z in cr:
        if x.max() > 0: ax.plot(x, z, color="#90a4ae", lw=0.9)
    for e in section(hall.arm(DD)):
        ax.plot(e[:, 0], e[:, 1], color="#1e88e5", lw=1.3)
    ax.axvspan(D["ha_rib_r_hub"], D["ha_rib_r_step"], color="#ff9800", alpha=0.18)
    ax.set_xlim(2.5, 12.5); ax.set_ylim(2.0, 10.0); ax.set_aspect("equal")
    ax.set_title(title, loc="left", fontsize=12.5, weight="bold"); ax.set_xlabel("r along the Hall arm (mm)")
    m = 0.07 / _rib_defl(DD)
    ax.text(2.7, 9.6, f"rib stiffness margin {m:.2f}x (needs 2x)", fontsize=11, va="top")
axs[0].set_ylabel("z (mm; main board front 0)")
axs[0].text((D["ha_rib_r_hub"] + D["ha_rib_r_step"]) / 2, 2.3, "r 4.06-4.94\n(old cage)", ha="center", fontsize=10)
axs[0].text(2.6, 3.65, "cradle (grey)", fontsize=10)
for ax in axs:
    ax.annotate("from here out the arm drops through\nthe cradle's slot to the magnet bar", (4.7, 3.3), (6.3, 4.6), fontsize=10,
                arrowprops=dict(arrowstyle="-", lw=0.7))
fig.text(0.01, 0.98, "Hall arm rib root (sweep item A4): blue = the dial's lower part through the rib's centre line", fontsize=14,
         weight="bold", va="top")
fig.text(0.01, 0.93, "The thrust cage under the dial tube went on 2 Nov, but the rib's first 0.9 mm still stands over it. Run it down "
         "like the rest of the rib (0.35 over the cradle);\nthe v0.15 Hall spoke inside the rib goes with it. The printed part gains 0.08 mm³; "
         "the stiffness check's beam loses its step. All 329 checks pass, no clashes.", fontsize=10.5, va="top")
fig.subplots_adjust(top=0.83, bottom=0.1, wspace=0.05)
fig.savefig(sys.argv[1])
print("wrote", sys.argv[1])
