"""under_pcb LOCAL checks (own parts + interface values only)."""
from ..common.checks import Rows
from .parts import feel

def checks(D, parts):
    T = D["tgt"]; r = Rows("under_pcb"); row = r.row
    wheel = parts["encoder big gear + slotted rim"]
    fmn = [n for n in parts if n.startswith("feel motor") and "shaft" not in n and "clip" not in n][0]
    row("feel motor can vs encoder wheel", parts[fmn].distance_to(wheel), T["feel_vs_wheel"])
    row("feel motor clip vs encoder wheel", parts["feel motor clip [A]"].distance_to(wheel), T["feel_vs_wheel"])
    row("feel gearhead envelope vs wheel", feel.gearhead(D).distance_to(wheel), T["feel_vs_wheel"], f"+{D['feel']['gearhead_len']:g} gear stage [A]")
    row("big gear vs sensor (axial)", D["z_sens_open"] - D["h_big_top"], 0.3)
    row("back panel: direct feel motor fits (set - needed)", D["back_panel"] - D["depth_direct"], 0.0, f"needs {D['depth_direct']:.1f}, set {D['back_panel']:.1f}")
    row("back panel: geared feel motor fits (set - needed)", D["back_panel"] - D["depth_geared"], 0.0, f"needs {D['depth_geared']:.1f} with +{D['feel']['gearhead_len']:g} gearhead")
    row("back-panel depth vs module limit", D["back_panel"], T["back_panel_max"], "", higher_ok=False)
    return r
