"""main_knob LOCAL checks (own parts + interface values only)."""
from ..common.checks import Rows

def checks(D, parts):
    T = D["tgt"]; r = Rows("main_knob")
    if D["kb_race"] == "chamfer":
        r.row("knob hub wall (hub-gear root over the bore)", D["race_wall"], T["race_wall"], f"bore Ø{2 * D['r_knob_bore']:.2f} on the Ø{2 * D['kb_rt']:.2f} dial tube")
    else:
        r.row("knob race wall (hub-gear root over the cone)", D["race_wall"], T["race_wall"])
    r.row(f"knob ring wall ({D['z_ring']}T root to OD)", D["ring_wall"], 0.8, "flagged since v0.8")
    r.row("cone balls chord play", D["kb_gap"], D["kb_play"], f"{D['kb_n']} × Ø{D['kb_ball_d']:g} on PCD {D['kb_pcd']:.2f}")
    return r
