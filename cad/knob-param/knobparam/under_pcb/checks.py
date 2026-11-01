"""under_pcb LOCAL checks (own parts + interface values only)."""
from ..common.checks import Rows

def checks(D, parts):
    T = D["tgt"]; r = Rows("under_pcb"); row = r.row
    row("big gear vs sensor (axial)", D["z_sens_open"] - D["h_big_top"], 0.3)
    if not D["brg2_on_pcb"]:
        row("back-panel depth vs module limit", D["back_panel"], T["back_panel_max"], "", higher_ok=False)
    else:
        row("deepest under-PCB part (cover depth driver)", -D["z_rear_min"], T["back_panel_max"], f"z {D['z_rear_min']:.2f}; bearing 2 on the PCB back", higher_ok=False)
    return r
