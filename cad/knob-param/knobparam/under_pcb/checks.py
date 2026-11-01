"""under_pcb LOCAL checks (own parts + interface values only)."""
from ..common.checks import Rows

def checks(D, parts):
    T = D["tgt"]; r = Rows("under_pcb"); row = r.row
    row("big gear vs sensor (axial)", D["z_sens_open"] - D["h_big_top"], 0.3)
    row("back-panel depth vs module limit", D["back_panel"], T["back_panel_max"], "", higher_ok=False)
    return r
