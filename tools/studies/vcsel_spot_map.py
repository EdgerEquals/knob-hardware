"""Picture for the red VCSEL's new home (8 Nov 2026). Reads vcsel_spot_study.py's .npz: where a 2.8 x 3.5 package fits on the
main board front, coloured by how far its straight-up beam travels before something opaque. Pure numpy/matplotlib:
  python3 tools/studies/vcsel_spot_map.py <vcsel_spots.npz> docs/img/vcsel-spots.png"""
import sys, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import ndimage

npz, out = sys.argv[1], sys.argv[2]
d = np.load(npz, allow_pickle=True); meta = json.load(open(npz.replace(".npz", ".json")))
xs, ys, first, who, busy, board, names = d["xs"], d["ys"], d["first"], d["who"], d["front_busy"], d["board"], list(d["names"])
X, Y = np.meshgrid(xs, ys); R = np.hypot(X, Y)
ok = ndimage.binary_erosion(board & ~busy, structure=np.ones((21, 17), bool))   # 4.1 x 3.3 patch (package + 0.3)
tall = np.where(np.isinf(first), 60, first)
fig, ax = plt.subplots(figsize=(11, 11.5), dpi=120)
ext = [xs[0], xs[-1], ys[0], ys[-1]]
img = np.zeros(X.shape + (4,)); img[board] = (0.18, 0.49, 0.2, 0.25); img[busy & board] = (0.4, 0.4, 0.4, 0.45)
ax.imshow(img, origin="lower", extent=ext, interpolation="nearest")
m = np.ma.masked_where(~ok, tall)
im = ax.imshow(m, origin="lower", extent=ext, cmap="plasma", vmin=0, vmax=30, interpolation="nearest")
cb = fig.colorbar(im, ax=ax, shrink=0.6); cb.set_label("beam travel straight up before an opaque part (mm; 30+ = up through the clear case)")
kr = meta["knob_r"]
ax.add_patch(plt.Circle((0, 0), kr, fill=False, ec="#0d47a1", lw=1.5, ls="--"))
ax.text(0, -kr - 1.5, "knob (glass OD)", ha="center", color="#0d47a1", fontsize=9)
ax.add_patch(plt.Circle((0, 0), 19.84, fill=False, ec="#0d47a1", lw=0.8, ls=":"))
cands = [((-10.7, -9.9), "x", "inside the knob: only just fits,\nand the control dial is 4.3 mm\nabove it (not offered)"),
         ((1.3, 26.5), "B", "B: between the knob and the\njoystick, straight up through the\nclear case to a frosted spot on\nthe faceplate's inside")]
for (x, y), k, t in cands:
    ax.plot(x, y, "o", ms=16, mfc="none", mec="w", mew=2.2)
    ax.text(x, y, k, color="w", ha="center", va="center", fontsize=11, weight="bold")
    ax.text(x + 2.6, y + 1.5, t, fontsize=8.6, color="k", bbox=dict(fc="w", ec="#999", alpha=0.85))
ax.text(-29, 49, "A (not on this board): the dial board's underside, shining DOWN into the knob.\n"
        "Ed 3 Nov 11:50 kept room there for lights; the grey PA-12 dial under it needs a window.", fontsize=9,
        va="top", bbox=dict(fc="#fff3e0", ec="#ef6c00"))
ax.set_xlim(-30, 30); ax.set_ylim(-12, 52); ax.set_aspect("equal")
ax.set_xlabel("x (mm), panel frame"); ax.set_ylabel("y (mm)")
ax.set_title("Where a red VCSEL (2.8 x 3.5, shining straight up) fits on the main board's front, v0.51\n"
             "grey = the board front is taken; coloured = free for the package", fontsize=10.5, loc="left")
fig.tight_layout(); fig.savefig(out)
