"""Q27 after picture (6 Nov 2026): under the main board, v0.48 (716 stage + encoder on its riser) vs v0.49 (no feel motor,
EE-SX1321 back on the board's back). Red = the feel stage, amber = encoder disc + sensor (+ riser), grey see-through = the rest.
Run from cad/knob-param:  KNOBPARAM_CACHE=$PWD/.cache-knob .venv/bin/python ../../tools/studies/feel_motor_removal_after.py"""
import os, sys
sys.path.insert(0, os.getcwd())
import numpy as np, pyvista as pv
from knobparam.common import model
from knobparam.assembly.build import build_all

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs", "img", "feel-motor-removal-v049.png")
SKIP = ("vertical board", "rod-link", "upper-cap", "glass sleeve", "drip O-ring", "knob balls", "hall sensor", "lower-cap", "track ",
        "detent", "spring", "thrust", "ruby", "tube", "rod", "Hall", "dial", "centring")


def mesh(solid, tol=0.03):
    v, t = solid.tessellate(tol, 0.3)
    P = np.array([[p.X, p.Y, p.Z] for p in v]); T = np.array(t)
    return pv.PolyData(P, np.hstack([np.full((len(T), 1), 3), T]).ravel())


pl = pv.Plotter(shape=(1, 2), off_screen=True, window_size=(2400, 1150))
for i, (title, sets) in enumerate([("v0.48: 716 stage, encoder dropped 4.6 onto its riser board", ["feel_on=True"]),
                                   ("v0.49: no feel motor, EE-SX1321 back on the main board's back", [])]):
    D = model.derive(model.apply_overrides(model.default_params(), sets))
    parts, _, _, _ = build_all(D, only=["base_drive", "under_pcb", "electronics", "main_knob"])
    pl.subplot(0, i)
    for n, s in parts.items():
        if any(k in n for k in SKIP):
            continue
        m = mesh(s)
        if n == "PCB":
            pl.add_mesh(m, color="#2e7d32", opacity=0.18)
        elif n.startswith("feel "):
            pl.add_mesh(m, color="#d32f2f", smooth_shading=True)
        elif n.startswith(("encoder disc", "encoder sensor", "encoder daughterboard", "encoder header")):
            pl.add_mesh(m, color="#f9a825", smooth_shading=True)
        else:
            pl.add_mesh(m, color="#9e9e9e", opacity=0.22)
    pl.add_text(title, font_size=12)
    ex, ey = D["enc_xy"]
    c = np.array([ex, ey, -6.0]); cam = np.array([-1.0, 1.2, -0.8])
    pl.camera.focal_point = c; pl.camera.position = c + 110 * cam / np.linalg.norm(cam); pl.camera.up = (0, 0, 1)
pl.set_background("white")
pl.screenshot(OUT); print("wrote", OUT)
