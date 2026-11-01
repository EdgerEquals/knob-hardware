"""Exports the CAD geometry that touches the main PCB to cad_constraints.json, for make_board.py (KiCad = source of truth for the
board; this keeps it in step with the parametric model). Run with the knob-param venv (build123d), NOT the pcbnew python:
    cad/knob-param/.venv/bin/python cad/knob-param/knobparam/electronics/kicad/export_cad_constraints.py
Frame: dial axis origin, x toward the 1220 motor, y up (frame); make_board.py converts to board coords (bx = axis_bx + x,
by = axis_by - y). Contents: the base-cradle footprint on the PCB front (section at z = 0.02, outer + openings), the Hall row
(radius, angle, part per sensor, magnet polarity), the 716 lead holes, the rod-pad radius, encoder/motor axes, idlers, detents,
spring anchors, and the faceplate (front z and thickness in the knob frame, PCB front = 0) for sub/case-v01."""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..", "..")))   # cad/knob-param
from build123d import Box, Pos, Align
from knobparam.common import model
from knobparam.assembly.build import build_all

def wire_pts(w, step=0.25):
    pts = []
    for e in w.order_edges() if hasattr(w, "order_edges") else w.edges():
        n = max(2, int(math.ceil(e.length / step)) + 1)
        for i in range(n - 1):
            p = e @ (i / (n - 1)); pts.append((round(p.X, 4), round(p.Y, 4)))
    return pts

def main():
    D = model.derive(model.default_params())
    parts, *_ = build_all(D, only=["base_drive", "electronics"])
    cr = parts["base cradle"]
    sl = cr & Pos(0, 0, 0) * Box(200, 200, 0.02, align=(Align.CENTER, Align.CENTER, Align.MIN))
    faces = []
    for f in sl.faces():
        if abs(f.normal_at().Z) < 0.99 or f.center().Z > 0.01: continue   # bottom faces only
        faces.append({"outer": wire_pts(f.outer_wire()), "holes": [wire_pts(h) for h in f.inner_wires()]})
    g = lambda k, d=None: D[k] if k in D else d
    out = dict(
        version=D["version"], axis_b=(D["axis_bx"], D["axis_by"]),
        cradle_faces=faces, cradle_r_out=D["cr_r_out"],
        hall=[dict(r=r, ang=a, part=(g("hv_parts") or [D["hv_sensor"]["part"]] * D["hv_n"])[i],
                   pol=(g("hv_pol") or [1, -1, 1, -1, 1])[i]) for i, (r, a) in enumerate(zip(D["hv_r"], D["hv_phi_s"]))],
        hall_mid_idx=(g("hv_mid") or {}).get("idx", 2), hall_slot=(D["hv_slot_r0"], D["hv_slot_r1"], D["hv_slot_half"]),
        fm_pad_xy=D["fm_pad_xy"], fm_xy=D["fm_xy"], fm_ang=D["fm_ang"], fm_cd=D["fm_cd"], feel=D["feel"],
        rod_pad_r=D["rod_pad_r"], rod_pad_clear=D["rod_pad_clear"], h1_hole=D["h1_hole"],
        enc_xy=D["enc_xy"], brg=D["brg"], offset=D["offset"], motor={k: D["motor"][k] for k in ("term_w", "term_t", "term_pitch", "rear_boss_d", "rear_boss_len", "body_d")},
        idler_xy=D["idler_xy"], det_angs=D["det_angs"], det_r=D["det_r"], sl_anchor_xy=D["sl_anchor_xy"],
        d_big_tip=D["d_big_tip"], sens_xy=D["sens_xy"], pcb=(D["pcb_w"], D["pcb_above"], D["pcb_below"]),
        knob_proud=D["knob_proud"], z_top=D["z_top"], z_knob_top=g("z_knob_top"),
        faceplate_z=D["faceplate_z"], faceplate_t=D["faceplate_t"], faceplate_z_back=D["faceplate_z_back"],
    )
    p = os.path.join(HERE, "cad_constraints.json"); json.dump(out, open(p, "w"), indent=1)
    print("wrote", p, "cradle faces", len(faces), "holes", [len(f["holes"]) for f in faces], "version", out["version"])

if __name__ == "__main__":
    main()
