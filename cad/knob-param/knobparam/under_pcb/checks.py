"""under_pcb LOCAL checks (own parts + interface values only)."""
from ..common.checks import Rows

def checks(D, parts):
    T = D["tgt"]; r = Rows("under_pcb"); row = r.row
    row("big gear vs sensor (axial)", D["z_sens_open"] - D["h_big_top"], 0.3)
    if not D["brg2_on_pcb"]:
        row("back-panel depth vs module limit", D["back_panel"], T["back_panel_max"], "", higher_ok=False)
    else:
        row("deepest under-PCB part behind the PCB back (cover depth driver)", D["z_pcb_back"] - D["z_rear_min"], T["back_panel_max"], f"z {D['z_rear_min']:.2f}; bearing 2 on the PCB back", higher_ok=False)
    if D["brg2_on_pcb"] and D["brg2_h2_engage"] > 0:   # v0.19b: both bearings in the one H2 bore
        B = D["brg"]
        row("bearing 2 located in the H2 bore (engagement)", D["brg2_in_h2"], 0.5,
            f"bearing 2 top z {D['h_b2_top']:.2f}, {D['h_brg_bot'] - D['h_b2_top']:.2f} under bearing 1; centres "
            f"{(D['h_brg_top'] + D['h_brg_bot'] - D['h_b2_top'] - D['h_b2_bot']) / 2:.2f} apart; wheel {D['h_b2_bot'] - D['h_big_bot']:.1f} below bearing 2")
    if D.get("enc_riser") and not D.get("enc_standoffs", True):   # v0.24 [Ed 13:35-13:39]: the riser hangs on its hybrid header (riser: feel_on only, Q27)
        n = D["enc_header_n"]; tht = list(D["enc_header_tht"])
        row("encoder riser: hybrid header, through-hole pins at the inner end (no standoffs)", len(tht), 2,
            f"{n} pins at {D['enc_header_pitch']:g}: THT {tht} (inner end, the main-board front is clear), SMT "
            f"{[k for k in range(n) if k not in tht]} (outer end, under vertical board R's foot); riser {D['enc_db_t']:g} board, "
            f"{D['enc_standoff_h']:.1f} off the main-board back; ~1 g, no load [Ed]")
    return r
