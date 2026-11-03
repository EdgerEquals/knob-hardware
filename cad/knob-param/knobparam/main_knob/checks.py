"""main_knob LOCAL checks (own parts + interface values only)."""
from ..common.checks import Rows
from ..common.process import stack

def checks(D, parts):
    T = D["tgt"]; r = Rows("main_knob")
    if D["kb_race"] == "chamfer":
        r.row("knob hub wall (hub-gear root over the bore)", D["race_wall"], T["race_wall"],
              f"bore Ø{2 * D['r_knob_bore']:.2f} on the Ø{2 * D['kb_rt']:.2f} dial tube; root Ø{D['d_hg_root']:.2f} "
              f"(m{D['hub_mod']:g} {D['z_hub_gear']}T, x {D['hub_x_gear']:+.3f}); v0.25 all PA-12 ({'the inner cap hub' if D.get('cs_on') else 'the hub-gear ring'})")
    else:
        r.row("knob race wall (hub-gear root over the cone)", D["race_wall"], T["race_wall"])
    r.row(f"knob ring wall ({D['z_ring']}T root to the cap)", D["ring_wall"], D["hb_wall_min"],
          f"cap skin r {D['cap_r']:.2f}; glass is the outer wall; {'spur' if not D['hb_beta'] else 'herringbone'} m{D['hb_mn']:.2f}, "
          f"{'one piece' if not D['hb_split'] else 'two halves'}")
    r.row("printed hub-gear tooth tip vs the MJF tooth floor", D["hub_tip_th"], D["hb_tooth_min"],
          f"m{D['hub_mod']:g} {D['z_hub_gear']}T x {D['hub_x_gear']:+.3f}, stub {D['spur_addendum']:.2f}, backlash {D['brass_backlash']:.2f}; "
          f"v0.25 floor = the ring stage's {D['hb_tooth_min']:.2f} [Ed 19:06] (was the {D['spur_tooth_min']:.2f} short-feature floor)")
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
        if D.get("cs_on") and "cs_r" in D and "cs_z_step" in D:   # v0.25 [Ed 19:46]: PA-12 inner hub keyed into the clear cap
            sla, mjf = PROCESS[D["cap_proc"]]["wall"], PROCESS["mjf"]["wall"]
            r.row("upper cap split: key bearing stress at the joint design torque vs UTR-8100 (MPa)", D["cs_key_bearing"], D["utr_uts"],
                  f"{D['hg_keys']} keys {D['hg_key_w']:g} x {D['hg_key_h']:g} x {D['cs_key_len']:.2f} on the PA-12 hub's Ø{2 * D['cs_r']:.1f} rim; "
                  f"{D['cs_T']:.0f} mNm = the {D['hub_i_limit']:g} mNm limit x {D['ratio_knob_motor']:.3f} x SF {D['sf_static']:g} (the knob's break torque): "
                  f"{D['cs_key_F']:.1f} N a key, key shear {D['cs_key_shear']:.1f} MPa (PA-12 {D['pa12_uts']:g}); margin "
                  f"{D['utr_uts'] / D['cs_key_bearing']:.0f}x; glue {D['hg_glue']:g} radial / {D['hg_glue_ax']:g} on the step over "
                  f"{D['cs_bond_area']:.0f} mm² (retention, not counted)", higher_ok=False)
            r.row("upper cap split: clear ledge under the PA-12 hub's flange vs the SLA wall (mm)", D["cs_ledge"], sla,
                  f"step z {D['cs_z_step']:.2f} at r {D['cs_r']:g}-{D['cs_r_flange']:g}; the race load only pushes the hub down: it goes "
                  f"through in bearing on this ledge")
            r.row("upper cap split: PA-12 flange over the step vs the MJF wall (mm)", D["cs_flange"], mjf,
                  f"30° cone top over the step at r {D['cs_r']:g}")
            r.row("upper cap split: PA-12 from the race groove to the joint vs the MJF wall (mm)", D["cs_groove_wall"], mjf,
                  f"Ø{2 * D['kb_seat_r']:g} groove at r {D['kb_seat_c_knob'][0]:.2f}; the 53 Ø1 steel balls roll on PA-12, not resin [Ed 19:46]")
            r.row("upper cap split: clear web outside the key slots (the torque path to the glass, mm)", D["cs_neck"], 1.5,
                  f"slots to r {D['cs_slot_r']:.2f}; same 1.5 floor as the v0.24-v0.25 neck rows (v0.25 collar neck {D['hg_neck']:.2f})")
        elif "hg_collar_r" in D:   # v0.25 [Ed 19:00-19:10]: PA-12 hub-gear ring glued into a clear cap
            sla = PROCESS[D["cap_proc"]]["wall"]
            r.row("upper cap (clear): neck outside the hub-gear pocket (underside to the cap top)", D["hg_neck"], 1.5,
                  f"the torque path out of the keys; pocket r {D['hg_pocket_r']:.2f} (slots r {D['hg_slot_r']:.2f}), flat underside z "
                  f"{D['h_band1']:.2f}, flat top z {D['knob_hub_top']:.2f}; v0.24 neck (PA-12, at the hub-gear root) {D['cap_neck']:.2f}")
            r.row("upper cap (clear): resin over the hub-gear collar vs the SLA wall", D["hg_resin_over"], sla,
                  f"pocket top z {D['hg_pocket_z1']:.2f} (collar {D['hg_collar_h']:g} + bond {D['hg_glue_ax']:g}), cap top z {D['knob_hub_top']:.2f}; "
                  f"{D['cap_proc'].upper()} wall {sla:g}")
            r.row("upper cap (clear): resin from the pocket corner to the cap top / race groove", min(D["hg_resin_top"], D["hg_resin_groove"]), sla,
                  f"to the top {D['hg_resin_top']:.2f}, to the Ø{2 * D['kb_seat_r']:g} ball groove {D['hg_resin_groove']:.2f}")
            r.row("hub-gear ring: key bearing stress at the joint design torque vs UTR-8100 (MPa)", D["hg_key_bearing"], D["utr_uts"],
                  f"{D['hg_keys']} keys {D['hg_key_w']:g} × {D['hg_key_h']:g} × {D['hg_collar_h']:g} on the Ø{2 * D['hg_collar_r']:.2f} collar; "
                  f"{D['hg_T_joint']:.0f} mNm = the {D['hub_i_limit']:g} mNm limit × {D['ratio_knob_motor']:.3f} × SF {D['sf_static']:g}: "
                  f"{D['hg_key_F']:.1f} N a key, key shear {D['hg_key_shear']:.1f} MPa (PA-12 {D['pa12_uts']:g}); resin tensile {D['utr_uts']:g} [S] "
                  f"taken for bearing; glue {D['hg_glue']:g} radial / {D['hg_glue_ax']:g} axial over {D['hg_bond_area']:.0f} mm² (retention, not counted)",
                  higher_ok=False)
        if "cap_neck" in D and "hg_collar_r" not in D:   # v0.21 cone cap [Ed 2 Nov]
            r.row("upper cap: neck at the hub (hub-gear root corner to the cap top)", D["cap_neck"], 1.5,
                  f"was 0.70 in v0.20; race {D['kb_rc']:.2f} from the axis; flat top z {D['knob_hub_top']:.2f}, flat underside z {D['h_band1']:.2f}")
        if "cap_neck" in D:
            r.row("upper cap: cone wall (normal), parallel faces", D["cap_cone_t"], 2 * PROCESS[D.get("cap_proc", "mjf")]["wall"],
                  f"{D['cone_deg']:g}° cone from r {D['cap_cone_r0']:.2f} to {D['cap_cone_r1']:.2f}; underside flat to r {D['cap_flat_r1']:.2f}")
            r.row("upper cap: running gap to the dial cone (normal)", D["cap_cone_run"], D["knob_run"] - 0.01,
                  "dial underside and cap top are parallel cones")
            r.row("upper cap: plug length in the glass bore", D["cap_plug_len"], 1.0,
                  f"plug Ø{2 * D['sleeve_spigot_r']:.2f} from z {D['cap_plug_z0']:.2f} to the chamfer seat z {D['cap_seat_z_foot']:.2f}")
            r.row("upper cap: cone top lands inside the glass-top seat", D["cap_seat_r_top"] - D["cap_cone_r1"], 0.5,
                  f"flat ring r {D['cap_cone_r1']:.2f}–{D['cap_seat_r_top']:.2f} flush with the glass top")
        else:
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
