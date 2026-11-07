"""Link flex geometry from the model (Q29 [Ed 7 Nov] = A, the J path) -> link_flex_geom.json, read by make_flex.py.
Run from cad/knob-param:  .venv/bin/python knobparam/electronics/kicad/jack-link-flex/export_geom.py"""
import json, os, sys
sys.path.insert(0, os.getcwd())
from knobparam.common import model

D = model.derive(model.default_params())
L = D["link_flex"]
out = dict(
    version=D.get("version"), flat_len=round(D["lf_flat"], 4), t=L["t"], t_end=L["t_end"], w=L["w"], n=L["n"], pitch=L["pitch"],
    x1=L["x1"], x_range=[round(v, 4) for v in D["lf_x"]], pad_y=list(L["pad_y"]), stiff=L["stiff"], mate=L["mate"],
    r_bottom=round(D["lf_rb"], 4), r_top=D["lf_rt"], riser_y=[round(D["lf_y_out"], 4), round(D["lf_y_in"], 4)],
    contact_face_z=round(D["lf_zcf"], 4), mouth_y=round(D["lf_mouth"], 4), end_y=round(D["lf_y_end"], 4),
    oled_edge_y=round(D["clear_oled_xy"][1] - D["clear_oled"][1] / 2, 4),
)
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "link_flex_geom.json")
json.dump(out, open(p, "w"), indent=1); print("wrote", p); print(out)
