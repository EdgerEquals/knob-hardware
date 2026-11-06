"""Q27 plan picture (6 Nov 2026): what goes if the 716 feel motor and its second stage are dropped [Ed 19:33 = A].
Red = goes, amber = changes (comes back up / gets simpler), grey = stays. The main PCB is drawn see-through.
Run from cad/knob-param:  KNOBPARAM_CACHE=$PWD/.cache-knob .venv/bin/python ../../tools/studies/feel_motor_removal_sketch.py"""
import os, sys
sys.path.insert(0, os.getcwd())
import numpy as np, pyvista as pv
from knobparam.common import model
from knobparam.assembly.build import build_all

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "img", "feel-motor-removal-sketch.png")
D = model.derive(model.default_params())
parts, _, _, owner = build_all(D, only=["base_drive", "under_pcb", "electronics", "main_knob"])
GOES = lambda n: n.startswith("feel ")
CHANGES = lambda n: n.startswith("encoder ") or n.startswith("idler pin 1") or n == "cradle" or n.startswith("cradle")
SKIP = lambda n: any(s in n for s in ("vertical board", "rod-link", "upper-cap", "glass sleeve", "drip O-ring", "knob balls",
                                       "hall sensor", "lower-cap", "track ", "detent", "spring", "thrust", "ruby", "tube", "rod",
                                       "Hall", "dial", "centring"))


def mesh(solid, tol=0.03):
    v, t = solid.tessellate(tol, 0.3)
    P = np.array([[p.X, p.Y, p.Z] for p in v]); T = np.array(t)
    return pv.PolyData(P, np.hstack([np.full((len(T), 1), 3), T]).ravel())


pv.OFF_SCREEN = True
views = [("from the front, above the board", (1.0, -1.3, 0.9)), ("from the back, under the board", (-1.0, 1.2, -0.8))]
pl = pv.Plotter(shape=(1, 2), off_screen=True, window_size=(2400, 1200))
for i, (title, cam) in enumerate(views):
    pl.subplot(0, i)
    for n, s in parts.items():
        if SKIP(n):
            continue
        m = mesh(s)
        if n == "PCB":
            pl.add_mesh(m, color="#2e7d32", opacity=0.18)
        elif GOES(n):
            pl.add_mesh(m, color="#d32f2f", smooth_shading=True)
        elif CHANGES(n):
            pl.add_mesh(m, color="#f9a825", smooth_shading=True, opacity=0.9)
        else:
            pl.add_mesh(m, color="#9e9e9e", opacity=0.22)
    pl.add_text(title, font_size=11)
    if i == 0:
        pl.add_text("red: goes (716 can, saddle seat, strap, screw, its pinion + cap, the 39T compound gear)\n"
                    "amber: changes (encoder riser can come back up; idler pin 1 and the cradle get simpler)\n"
                    "grey see-through: stays (1220, idler 2, ring, cradle); green: main PCB", position="lower_left", font_size=13)
    pl.camera_position = "iso"; pl.camera.azimuth = 0
    _c = parts["feel motor coreless Ø2 [A]"].center(); c = np.array([_c.X, _c.Y, _c.Z])
    pl.camera.focal_point = c; pl.camera.position = c + 120 * np.array(cam) / np.linalg.norm(cam); pl.camera.up = (0, 0, 1)
    pl.camera.zoom(1.0)
pl.set_background("white")
pl.screenshot(OUT); print("wrote", OUT)
