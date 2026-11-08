# Saved from the 8 Nov logo study: builds the model (cache) and dumps the parts' boxes and the case shell (.brep) for panel_face_extract.py.
# Run from cad/knob-param: KNOBPARAM_CACHE=$PWD/.cache-knob PYTHONPATH=$PWD .venv/bin/python ../../tools/studies/panel_face_dump.py <model.json> <case.brep>
import sys, json, pickle
from knobparam.common import model
from knobparam.assembly.build import build_all
D = model.derive(model.default_params())
parts, _, _, owner = build_all(D)
keys = ["z_fp0", "z_fp1", "panel_x0", "panel_x1", "panel_y0", "panel_y1", "panel_w", "panel_h", "version", "knob_hole_d", "jack_xy", "jack_hole", "usb_xy", "usb_rcpt", "clear_oled", "clear_oled_xy", "rail_keep_d", "rail_hole_d"]
print({k: D.get(k) for k in keys})
rows = []
for n, s in parts.items():
    try:
        b = s.bounding_box()
    except Exception:
        continue
    rows.append((n, round(b.min.X,2), round(b.max.X,2), round(b.min.Y,2), round(b.max.Y,2), round(b.min.Z,2), round(b.max.Z,2)))
json.dump(dict(D={k: (v if isinstance(v,(int,float,str,list,tuple,dict,type(None))) else str(v)) for k, v in D.items() if not callable(v)}, rows=rows), open(sys.argv[1], "w"), default=str)
from build123d import export_brep
export_brep(parts["case"], sys.argv[2])
print(len(rows), "parts")
