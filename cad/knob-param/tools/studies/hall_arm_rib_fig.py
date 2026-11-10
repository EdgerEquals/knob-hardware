"""Ed 10 Nov 11:23: does the Hall arm need to be so long, and stand past where the centring springs join it? One picture: the
real part (model cache) from the side, and a to-scale elevation along the arm (224°) with the rib as built and the taper the
stiffness check allows past the spring column.
  .venv/bin/python tools/studies/hall_arm_rib_fig.py <out.png>"""
import os, sys, json, math
import numpy as np
import pyvista as pv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from knobparam.common import model

OUT = sys.argv[1]
D = model.derive(model.default_params())
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".cache-knob", "anim", "index.json")
idx = json.load(open(CACHE))["parts"]
TMP = os.path.dirname(os.path.abspath(OUT))


def mesh(name):
    z = np.load(idx[name]["mesh"]); P, T = z["P"], z["T"]
    return pv.PolyData(P, np.hstack([np.full((len(T), 1), 3), T]).astype(np.int64))


# ---- 1. the real parts, from the side of the arm (cache frame = mechanism frame turned -90°) ----
pl = pv.Plotter(off_screen=True, window_size=(1150, 900)); pl.set_background("white")
arm = mesh("control dial lower part (tube, Hall and detent spokes, spring column)").clip("z", origin=(0, 0, 11.5), invert=True)
pl.add_mesh(arm, color="#5b8fd6", smooth_shading=False, show_edges=False)
cr = mesh("base cradle")
pl.add_mesh(cr, color="#c9ced3", opacity=1.0)
for n in idx:
    if n.startswith("centring spring"):
        pl.add_mesh(mesh(n), color="#9c5a3c")
    elif n.startswith(("spring pin on", "spring anchor pin")):
        pl.add_mesh(mesh(n), color="#30363b")
a = math.radians(D["ha_ang0"] - 90.0); u = np.array([math.cos(a), math.sin(a), 0.0]); n_ = np.array([-u[1], u[0], 0.0])
c = u * 9.0 + np.array([0, 0, 6.0])
pl.camera.position = tuple(c - n_ * 52 + np.array([0, 0, 22.0]) + u * 4); pl.camera.focal_point = tuple(c); pl.camera.up = (0, 0, 1)
pl.camera.view_angle = 30
f1 = os.path.join(TMP, "_ha_1.png"); pl.screenshot(f1); pl.close()

# ---- 2. elevation along the arm, to scale (mechanism numbers) ----
zt, zl, zc = D["ha_rib_z_top"], D["ha_rib_z_low"], D["ha_rib_z_cage"]
rhub, rstep, r1 = D["ha_rib_r_hub"], D["ha_rib_r_step"], D["ha_rib_r1"]
pr, zb0, zb1 = D["hv_pad_r"], D["hv_bar_z0"], D["fan_top"]
md, mh = D["hv_mag"]
rc, cd, ctop = D["es_rp"], D["es_col_d"], D["es_top"]
X0 = rc + cd / 2 + 0.2   # the taper starts just past the column
fig = plt.figure(figsize=(11.5, 9.0), dpi=100)
ax = fig.add_axes([0.07, 0.10, 0.9, 0.78])
ax.add_patch(Rectangle((0, 0), 18.2, D["plate_t"], fc="#e3e6e9", ec="none"))
ax.text(0.2, 0.3, "cradle plate (the bar\nruns in its Hall slot)", ha="left", fontsize=9.5, color="#555")
ax.add_patch(Rectangle((0, zc), D["dial_tube_od"] / 2, 13 - zc, fc="#cfdcf0", ec="#5b8fd6", lw=1))
ax.text(0.3, 12.2, "dial tube", fontsize=10, color="#2d5aa0")
# magnet bar: pads + links
ax.add_patch(Rectangle((D["hv_r"][0] - pr, zb0), D["hv_r"][-1] - D["hv_r"][0] + 2 * pr, zb1 - zb0, fc="#cfdcf0", ec="#5b8fd6", lw=1))
for k, r in enumerate(D["hv_r"], 1):
    ax.add_patch(Rectangle((r - md / 2, zb0), md, mh, fc="#d64545", ec="#8a1f1f", lw=0.8))
    ax.text(r, zb0 - 0.55, f"{k}", ha="center", fontsize=10, color="#8a1f1f", weight="bold")
ax.text(D["hv_r"][2], -1.0, "Hall magnets (r " + ", ".join(f"{r:.1f}" for r in D["hv_r"]) + ")", ha="center", fontsize=10, color="#8a1f1f")
# rib as built
rib = [(rhub, zc), (rstep, zc), (rstep, zl), (r1, zl), (r1, zt), (rhub, zt)]
ax.add_patch(Polygon(rib, closed=True, fc="#5b8fd6", ec="#1f4f99", lw=1.2, alpha=0.85))
# what the stiffness rule does not need: above the taper line past the column
cut = [(X0, zt), (r1, zt), (r1, zb1)]
ax.add_patch(Polygon(cut, closed=True, fc="none", ec="#e65100", lw=0, hatch="////"))
ax.plot([X0, r1], [zt, zb1], color="#e65100", lw=2.2, ls="--")
# column, pin, springs
ax.add_patch(Rectangle((rc - cd / 2, zt), cd, ctop - zt, fc="#5b8fd6", ec="#1f4f99", lw=1))
ax.add_patch(Rectangle((rc - D["es_pin_d"] / 2, ctop - 1.5), D["es_pin_d"], D["es_z"] + D["es_od"] / 2 + 0.4 - ctop + 1.5, fc="#30363b", ec="none"))
ax.add_patch(Circle((rc + 1.3, D["es_z"]), D["es_od"] / 2, fc="none", ec="#9c5a3c", lw=2))
ax.add_patch(Circle((rc - 1.3, D["es_z"]), D["es_od"] / 2, fc="none", ec="#9c5a3c", lw=2))
ax.annotate("spring column + steel pin (r 8):\nthe two springs hook on here,\nthen run off sideways (out of the page)", (rc, D["es_z"] + 1.0), (1.0, 15.2),
            fontsize=10.5, arrowprops=dict(arrowstyle="-", color="#333", lw=0.8))
ax.annotate("rib top z 9.0 (raised from 6.8 for the 2 N\nstiffness check: 2x rule)", ((rc + r1) / 2 + 2, zt), (11.0, 14.0), fontsize=10.5,
            arrowprops=dict(arrowstyle="-", color="#333", lw=0.8))
ax.annotate("could taper to the bar top (z 5.9) at the tip:\nstiffness margin 2.19x -> 2.17x; 118 mm³ less", (14.5, 7.4), (12.6, 11.4), fontsize=10.5,
            color="#b23c00", arrowprops=dict(arrowstyle="-", color="#b23c00", lw=0.8))
ax.annotate("", (r1, -2.0), (0, -2.0), arrowprops=dict(arrowstyle="<->", color="#333", lw=0.9))
ax.text(0.3, -3.0, f"arm length from the axis: r {r1:g} (the outer magnet sits as far out as the knob ring allows)", ha="left", fontsize=10.5)
ax.set_xlim(-0.3, 18.4); ax.set_ylim(-3.8, 17.2); ax.set_aspect("equal")
ax.set_xlabel("radius along the Hall arm, 224° (mm)"); ax.set_ylabel("z (mm)")
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("2. Side view along the arm, to scale", loc="left", fontsize=12.5, weight="bold")
f2 = os.path.join(TMP, "_ha_2.png"); fig.savefig(f2); plt.close(fig)

# ---- compose ----
A, B = Image.open(f1), Image.open(f2)
H = max(A.height, B.height); W = A.width + B.width
cv = Image.new("RGB", (W, H + 120), "white"); cv.paste(A, (0, 110 + (H - A.height) // 2)); cv.paste(B, (A.width, 110))
d = ImageDraw.Draw(cv)
try:
    fb = ImageFont.truetype("DejaVuSans-Bold.ttf", 30); fr = ImageFont.truetype("DejaVuSans.ttf", 21)
except OSError:
    fb = fr = ImageFont.load_default()
d.text((24, 16), f"Knob {D['version']}: the Hall arm and the centring springs' pin", font=fb, fill="black")
d.text((24, 62), "1. The real part (blue) from the side of the arm; springs brown, pins black, cradle grey. The arm is long for the "
       "Hall magnets, not for the springs.", font=fr, fill="#222")
cv.save(OUT)
for f in (f1, f2):
    os.remove(f)
print("wrote", OUT)
