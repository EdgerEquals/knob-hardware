"""Free space around the outer thrust race, all the way round (8 Nov 2026, Ed: "make it wider where it can be").
For every part near the race, cut it with half-planes through the knob axis every STEP degrees and paint what it occupies in the
(radius, height) plane. Union over all angles = the part's shadow. A part that turns with the knob must be cleared everywhere; a fixed
part that only covers a few degrees could be cleared with a local notch instead. Writes an .npz with the shadows and a picture.
Run from cad/knob-param:
  KNOBPARAM_CACHE=$PWD/.cache-knob PYTHONPATH=$PWD .venv/bin/python ../../tools/studies/race_envelope.py <out.npz> [step_deg]"""
import math, sys, json
import numpy as np
from matplotlib.path import Path
from build123d import Plane
from knobparam.common import model
from knobparam.assembly.build import build_all

out = sys.argv[1]; STEP = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
D = model.derive(model.default_params())
parts, _, _, owner = build_all(D)
R0, R1, Z0, Z1, H = 14.0, 25.0, -0.6, 6.5, 0.02
rr = np.arange(R0, R1, H) + H / 2; zz = np.arange(Z0, Z1, H) + H / 2
RG, ZG = np.meshgrid(rr, zz); pts = np.c_[RG.ravel(), ZG.ravel()]
near = {}
for n, s in parts.items():
    if n == "PCB" or n.startswith("emitter"):
        continue
    b = s.bounding_box()
    if b.min.Z > Z1 or b.max.Z < Z0:
        continue
    near[n] = s
shadow = {n: np.zeros(RG.shape, bool) for n in near}
cover = {n: 0 for n in near}           # how many angles the part shows up in the race band (r 17-23, z < 3)
angles = np.arange(0.0, 360.0, STEP)
for a in angles:
    u = (math.cos(math.radians(a)), math.sin(math.radians(a)))
    pl = Plane(origin=(0, 0, 0), x_dir=(u[0], u[1], 0), z_dir=(-u[1], u[0], 0))
    for n, s in near.items():
        try:
            sec = s.intersect(pl)
        except Exception:
            continue
        if sec is None:
            continue
        hit = np.zeros(RG.shape, bool)
        for f in sec.faces():
            poly = []
            for e in f.outer_wire().edges():
                for t in np.linspace(0, 1, 20):
                    p = e.position_at(t); poly.append((p.X * u[0] + p.Y * u[1], p.Z))
            poly = np.array(poly)
            if len(poly) < 3 or poly[:, 0].max() < R0 or poly[:, 0].min() > R1:   # the other half of the plane, or out of the window
                continue
            m = Path(poly).contains_points(pts).reshape(RG.shape)
            for hole in f.inner_wires():
                hp = []
                for e in hole.edges():
                    for t in np.linspace(0, 1, 20):
                        p = e.position_at(t); hp.append((p.X * u[0] + p.Y * u[1], p.Z))
                if len(hp) >= 3:
                    m &= ~Path(np.array(hp)).contains_points(pts).reshape(RG.shape)
            hit |= m
        shadow[n] |= hit
        if (hit & (RG > 17) & (RG < 23) & (ZG < 3)).any():
            cover[n] += 1
    print(f"angle {a:5.1f}", flush=True) if a % 45 == 0 else None
np.savez_compressed(out, rr=rr, zz=zz, names=np.array(list(near)), shadows=np.array([shadow[n] for n in near]),
                    cover=np.array([cover[n] for n in near]), n_ang=len(angles))
json.dump(dict(owner={n: str(owner.get(n, "")) for n in near}, D={k: D[k] for k in ("ot_r", "ot_rg", "ot_z", "ot_land_th", "hb_root_r",
          "cap_r", "ot_track_extra", "ot_axial_gap", "h_skirt0", "pcb_t") if k in D}), open(out.replace(".npz", ".json"), "w"), indent=1)
print("done", len(near), "parts")
