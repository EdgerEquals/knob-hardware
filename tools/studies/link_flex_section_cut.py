"""Cut the full model at x = argv[1] (window y -55..-41, z -4..16) and pickle the y-z outlines for link_flex_path_sketch.py.
Run from cad/knob-param:  KNOBPARAM_CACHE=$PWD/.cache-knob .venv/bin/python ../../tools/studies/link_flex_section_cut.py 14 out.pkl"""
import os, sys, pickle
sys.path.insert(0, os.getcwd())
from knobparam.common import model
from knobparam.assembly.build import build_all
from build123d import Plane, Box, Pos, Location
D = model.derive(model.default_params())
parts, _, _, owner = build_all(D)
X = float(sys.argv[1]) if len(sys.argv) > 1 else 14.0
win = Pos(X, -48.0, 6.0) * Box(0.02, 14.0, 20.0)
out = {}
for n, s in parts.items():
    try:
        bb = s.bounding_box()
        if bb.min.X > X or bb.max.X < X or bb.min.Y > -41 or bb.max.Y < -55 or bb.min.Z > 16 or bb.max.Z < -4:
            continue
        c = s & win
        if c.volume < 1e-6:
            continue
        polys = []
        for f in c.faces():
            if abs(f.normal_at().X) > 0.9:
                for w in f.wires():
                    pts = [(v.Y, v.Z) for v in w.positions(list(i / 60 for i in range(61)))] if hasattr(w, "positions") else []
                    polys.append(pts)
        if polys:
            out[n] = polys
    except Exception as e:
        print("skip", n, e)
pickle.dump((D["jack_bot_y"], out), open(sys.argv[2], "wb")); print(len(out), "parts cut")
