"""The clear race, widened into the free space (8 Nov 2026, Ed 13:06: "make it wider where it can be ... have a little look first").
Reads the all-round free-space map from race_envelope.py (.npz) and draws the current race, what is around it (turning with the knob,
or fixed), and the proposed wider race. Pure numpy/matplotlib:
  python3 tools/studies/race_widen_sketch.py <race_env.npz> docs/img/race-widen-proposal.png"""
import json, math, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

npz, out = sys.argv[1], sys.argv[2]
d = np.load(npz, allow_pickle=True); meta = json.load(open(npz.replace(".npz", ".json")))
rr, zz, names, sh = d["rr"], d["zz"], list(d["names"]), d["shadows"]
D = meta["D"]; r0, rg, zb = D["ot_r"], D["ot_rg"], D["ot_z"]
TURN = ("bottom internal ring", "knob lower-cap land", "knob glass sleeve")
RACE = "base cradle"
fig = plt.figure(figsize=(16, 8.6), dpi=125)
ax = fig.add_axes([0.05, 0.1, 0.56, 0.78])
ext = [rr[0], rr[-1], zz[0], zz[-1]]


def paint(mask, color, alpha):
    img = np.zeros(mask.shape + (4,)); img[mask] = matplotlib.colors.to_rgba(color, alpha)
    ax.imshow(img, origin="lower", extent=ext, aspect="equal", interpolation="nearest", zorder=1)


turn = np.zeros(sh[0].shape, bool); fixed = np.zeros(sh[0].shape, bool); race = np.zeros(sh[0].shape, bool)
R, Z = np.meshgrid(rr, zz)
for i, n in enumerate(names):
    if n.startswith(TURN):
        turn |= sh[i]
    elif n == RACE:
        race |= sh[i] & (R > 18.6)          # the race ring only (the cradle's inner body is not the race)
    elif n.startswith("outer thrust"):
        pass
    else:
        fixed |= sh[i]
paint(fixed, "#9e9e9e", 0.55); paint(turn, "#ef9a9a", 0.7); paint(race, "#4fc3f7", 0.75)
ax.add_patch(plt.Circle((r0, zb), 1.0, fc="#616161", ec="k", lw=0.6, zorder=3))
# proposed race: foot from RI to RO, top 0.3 under the knob, the same groove
RI, RO, ZT = 17.5, 21.2, zb - 0.3   # 0.5 off the encoder bearing, 0.32 off the knob and the case (measured)
dz = zb - ZT; hw = math.sqrt(rg ** 2 - dz ** 2)
arc = [(r0 + rg * math.cos(t), zb + rg * math.sin(t)) for t in np.linspace(math.pi + math.asin(dz / rg), 2 * math.pi - math.asin(dz / rg), 40)]
prop = [(RI, 0.0), (RI, ZT), (r0 - hw, ZT)] + arc + [(r0 + hw, ZT), (RO, ZT), (RO, 0.0)]
ax.add_patch(Polygon(prop, closed=True, fc="none", ec="#1b5e20", lw=2.4, zorder=4))
ax.add_patch(plt.Rectangle((rr[0], -1.6), rr[-1] - rr[0], 1.6, fc="#2e7d32", ec="k", lw=0.5, zorder=0))
ax.text(15.0, -0.8, "PCB", color="w", weight="bold", fontsize=9, va="center")


def dim(x0, x1, y, txt, col="#1b5e20", dy=0.18, tcol=None):
    ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", color=col, lw=1.2), zorder=5)
    ax.text((x0 + x1) / 2, y + dy, txt, color=tcol or col, fontsize=8.6, ha="center", zorder=5)


dim(RI, RO, -0.35, f"new foot {RO - RI:.1f} wide (was 2.2)", col="w", dy=-0.45, tcol="w")
dim(RI, r0 - hw, ZT - 0.25, f"inner lip {r0 - hw - RI:.2f}", dy=-0.38)
dim(r0 + hw, RO, ZT + 0.12, f"{RO - r0 - hw:.2f}", dy=0.2)
ax.text(RO + 0.08, ZT - 0.25, "outer lip", color="#1b5e20", fontsize=8.6)
ax.annotate("", (19.0, zb), (19.0, ZT), arrowprops=dict(arrowstyle="<->", color="#6a1b9a", lw=1.0), zorder=5)
ax.annotate("0.3 under the knob", (19.0, (zb + ZT) / 2), (17.4, 2.9), color="#6a1b9a", fontsize=8.2, zorder=6,
            arrowprops=dict(arrowstyle="-", color="#6a1b9a", lw=0.8))
ax.set_xlim(14.6, 23.6); ax.set_ylim(-1.7, 6.0)
ax.set_xlabel("radius from the knob axis (mm)"); ax.set_ylabel("height above the PCB front (mm)")
ax.set_title("All the way round: what turns with the knob (red), what is fixed (grey),\nthe clear race now (blue), proposed (green outline)",
             fontsize=10.5, loc="left")
fig.text(0.05, 0.955, "The clear race, widened into the room it has", fontsize=14, weight="bold", va="top")
tx = fig.add_axes([0.63, 0.06, 0.36, 0.84]); tx.axis("off")
lines = [
    ("WIDER: yes, at its foot", "#1b5e20", True),
    ("Inward to r 17.5 (0.5 off the encoder bearing; the ring gear", None, False),
    ("is above it), outward to r 21.2 (0.32 off the case).", None, False),
    ("Foot 3.7 mm wide instead of 2.2; the knife-edge tops", None, False),
    ("drop to 0.3 under the knob, so the lips become 1.33", None, False),
    ("inside and 0.36 outside instead of about 0.05.", None, False),
    ("Nothing else moves.", None, False),
    ("", None, False),
    ("TALLER: not on its own", "#c62828", True),
    ("The 2 mm floor trial: 332 of 334 checks pass. The 2 that", None, False),
    ("fail: the knob rises 1 mm, the idler pinions with it, and", None, False),
    ("their caps meet the control dial's detent arm and Hall arm.", None, False),
    ("The detent arm has 0.03 mm to spare today, so the knob", None, False),
    ("cannot rise at all unless the control dial rises too, and", None, False),
    ("that lifts its Hall magnets 1 mm further off their sensors.", None, False),
    ("", None, False),
    ("THE KNOB'S SIDE of the race (its top track)", "#ef6c00", True),
    ("Stays about 0.1 mm a side: the ring gear's teeth are just", None, False),
    ("inside it, and outside is the rule that the cap stays inside", None, False),
    ("the glass. The way out there is Ø1.5 balls (0.35 a side).", None, False),
    ("", None, False),
    ("THE LIGHTS", "#1565c0", True),
    ("With the RGB recessed in the board (SK6812MINI-E), the", None, False),
    ("race floor no longer needs a hole over each light: the light", None, False),
    ("goes through 1 mm of clear resin. A solid floor is stronger.", None, False),
    ("The red VCSELs on the front need the taller race, so they", None, False),
    ("still need the control dial raised (Q35 B).", None, False),
]
y = 0.98
for t, c, b in lines:
    tx.text(0, y, t, fontsize=10.2 if b else 9.4, weight="bold" if b else None, color=c or "#222", va="top", transform=tx.transAxes)
    y -= 0.036
fig.savefig(out)
