"""main_knob LOCAL checks (own parts + interface values only)."""
from ..common.checks import Rows
from ..common.process import stack

def checks(D, parts):
    T = D["tgt"]; r = Rows("main_knob")
    if D["kb_race"] == "chamfer":
        r.row("knob hub wall (hub-gear root over the bore)", D["race_wall"], T["race_wall"], f"bore Ø{2 * D['r_knob_bore']:.2f} on the Ø{2 * D['kb_rt']:.2f} dial tube")
    else:
        r.row("knob race wall (hub-gear root over the cone)", D["race_wall"], T["race_wall"])
    r.row(f"knob ring wall ({D['z_ring']}T root to the cap)", D["ring_wall"], D["hb_wall_min"],
          f"cap skin r {D['cap_r']:.2f}; glass is the outer wall; herringbone mn {D['hb_mn']:.2f}")
    r.row("printed hub-gear tooth tip vs MJF short-feature floor", D["hub_tip_th"], D["spur_tooth_min"],
          f"m{D['hub_mod']:.1f} {D['z_hub_gear']}T stub {D['spur_addendum']:.2f}, backlash {D['brass_backlash']:.2f}; preferred tooth {D['hb_tooth_min']:.2f}")
    r.row("cone balls chord play", D["kb_gap"], D["kb_play"], f"{D['kb_n']} × Ø{D['kb_ball_d']:g} on PCD {D['kb_pcd']:.2f}")
    r.row("borosilicate wall, at least the bought minimum", D["sleeve_wall"], D["sleeve_wall_lo"],
          f"nominal {D['sleeve_wall']:.2f} inside {D['sleeve_wall_lo']:.1f}–{D['sleeve_wall_hi']:.1f}; ID Ø{D['sleeve_id']:.2f}")
    r.row("borosilicate wall, not over the bought maximum", D["sleeve_wall"], D["sleeve_wall_hi"],
          f"thick-wall ID Ø{D['sleeve_id_spec']:.2f} (37.4 at OD 42 and wall 2.3)", higher_ok=False)
    r.row("measured glass OD covers the screen", D["knob_od"] - D["knob_od_min"], 0.0,
          f"screen minimum Ø{D['knob_od_min']:.3f}; sleeve Ø{D['knob_od']:.2f}")
    r.row("cap OD flush or inside the glass OD", D["knob_od"] / 2 - D["cap_r"], 0.0,
          f"cap Ø{2 * D['cap_r']:.2f}")
    r.row("glue gap on the measured bore", D["sleeve_glue"], D["sleeve_glue_lo"],
          f"round-tube design point inside {D['sleeve_glue_lo']:.2f}–{D['sleeve_glue_hi']:.2f}; "
          f"the built spigot is the minor-bore fit Ø{2 * D['sleeve_spigot_r']:.2f}")
    r.row("glue gap, not over the band", D["sleeve_glue"], D["sleeve_glue_hi"], higher_ok=False)
    r.row("glue gap at the tight side of ovality and wall", D["sleeve_gap_lo"], D["sleeve_glue_lo"],
          f"spigot fitted to the minor bore (ID {D['sleeve_id']:.2f} − ovality {D['sleeve_ovality']:.2f}); wall is the measured wall")
    r.row("glue gap at the loose side of ovality and wall", D["sleeve_gap_hi"], D["sleeve_gap_hi"],
          f"round spigot, oval bore; opens by ovality/2 from the {D['sleeve_glue_lo']:.2f} minimum", higher_ok=False)
    g0, g1 = D["sleeve_id"] / 2, D["knob_od"] / 2
    l0, l1 = D["sleeve_land_ri"], D["cap_r"]
    overlap = min(g1, l1) - max(g0, l0)
    race = min(D["ot_r"] - max(g0, l0), min(g1, l1) - D["ot_r"])
    r.row("light path from the bottom race up through the glass", min(overlap, race), D["ot_seat_gap"],
          f"glass end r {g0:.2f}–{g1:.2f} on the clear land r {l0:.2f}–{l1:.2f}; race r {D['ot_r']:.2f}; sleeve {D['sleeve_len']:.2f} mm")
    need = stack("buy", "mjf")
    r.row("glass ID clears the ring tips", D["sleeve_id_worst"] / 2 - D["hb_tip_r"], need,
          f"worst bore Ø{D['sleeve_id_worst']:.2f} (OD −{D['sleeve_od_tol']:g}, wall {D['sleeve_wall_worst']:.2f}, ovality {D['sleeve_ovality']:g}); "
          f"tips Ø{2 * D['hb_tip_r']:.2f}. The v0.17 skirt was Ø36.50; spec ID at wall {D['sleeve_wall_hi']:.1f} is Ø{D['sleeve_id_spec']:.2f}",
          procs=("buy", "mjf"))
    r.row("glass ID clears everything inside the sleeve", D["sleeve_id_worst"] / 2 - D["sleeve_inside_r"], need,
          f"outermost can r {D['sleeve_inside_r']:.2f}; nominal bore Ø{D['sleeve_id']:.2f}",
          procs=("buy", "mjf"))
    r.row("sleeve length is the visible band", D["sleeve_len"], 1.0,
          f"z {D['sleeve_z0']:.2f} to {D['sleeve_z1']:.2f}; insert {D['sleeve_insert']:.2f} each end; chamfer {D['sleeve_chamfer']:.2f}")
    r.row("cap engagement leaves an open bore between the plugs", D["sleeve_len"] - 2 * D["sleeve_insert"], D["sleeve_insert"])
    if D["glass_to_dial"]:
        from ..common.process import PROCESS
        r.row("upper cap: dished web / flare wall (normal) vs MJF wall", D["cap_flare_wall"], PROCESS["mjf"]["wall"],
              f"web {D['z_under_web'] - D['h_band1']:.2f} at the hub gear to {D['cap_web_rim']:.2f} at r {D['cap_r_s']:.2f}; "
              f"flare {D['cap_flare_slope']:.0f}° up to the plug foot z {D['cap_z_plug0']:.2f}")
        if D["cap_top"] == "chamfer":
            r.row("glass top: flat face left between the two ground chamfers", D["glass_top_flat"], 0.4,
                  f"wall {D['sleeve_wall']:.2f} − inner {D['sleeve_top_cin']:g} − outer {D['sleeve_top_cout']:g} (45°); thin wall {D['sleeve_wall_lo']:g} leaves {D['sleeve_wall_lo'] - D['sleeve_top_cin'] - D['sleeve_top_cout']:.2f}")
            r.row("glass top under the dial lip (running gap)", D["z_lip0"] - D["sleeve_z1"], D["knob_run"] - 0.01,
                  f"glass top z {D['sleeve_z1']:.2f}; cap cone seats on the {D['sleeve_top_cin']:g} inner chamfer (bond {D['sleeve_seat_glue']:g} along z); "
                  "the cap position now follows the glass length and its bore: print the cap to the measured tube")
        else:
            r.row("upper cap: shoulder on the glass top (thickness)", D["cap_sh_z1"] - D["cap_sh_z0"], PROCESS["mjf"]["wall"],
                  f"OD Ø{D['knob_od']:.2f} = glass OD; z {D['cap_sh_z0']:.2f}–{D['cap_sh_z1']:.2f}, bond {D['cap_shoulder_glue']:.2f} on the glass top z {D['sleeve_z1']:.2f}")
    return r
