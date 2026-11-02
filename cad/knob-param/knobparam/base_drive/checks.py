"""base_drive LOCAL checks (own parts + interface values only)."""
from ..common.checks import Rows

def _one(parts, prefix):
    return parts[[n for n in parts if n.startswith(prefix)][0]]

def _arc_rows(D, parts, r):
    """v0.21 [Ed 2 Nov]: detent on the arc (boss on a two-column bridge) and the three ball tracks' plate grooves."""
    import math
    from .parts import mech, hall_slot
    from ..common.util import cyl
    r.row("arc detent: bridge lift under the spring, grub fully in, ball on a dimple rim (mm)", D["ad_defl"], D["ad_defl_max"],
          f"{D['det_force_max']:.2f} N at {D['det_spring_k']:g} N/mm [A]; two Ø{2 * D['ad_col_r']:g} columns, links "
          + ", ".join(f"{L:.1f}" for L in D["ad_link_len"]) + f" × {D['ad_link_w']:g} × {D['det_z1'] - D['ad_z_link']:.1f}; E {D['ad_E'] / 1000:g} GPa [A]",
          higher_ok=False)
    cols = [cyl(D["ad_col_r"], D["plate_t"] - 0.01, 1.0, x, y) for x, y in D["ad_col_xy"]]
    sl = hall_slot.window(D)
    r.row("arc detent: bridge columns stand on the plate (column to the Hall slot, mm)", min(c.distance_to(sl) for c in cols), D["ad_col_need"],
          "columns at " + ", ".join(f"r {math.hypot(x, y):.2f} {math.degrees(math.atan2(y, x)) % 360:.1f}°" for x, y in D["ad_col_xy"]))
    g = list(mech.track_grooves(D).solids())
    def mine(t):   # the groove solid nearest this track's mid point
        x, y = t["r"] * math.cos(math.radians(t["ang"])), t["r"] * math.sin(math.radians(t["ang"]))
        return min(g, key=lambda q: math.hypot(q.center().X - x, q.center().Y - y))
    lands = [mine(t).distance_to(sl) for t in D["tk"]]
    r.row("ball tracks: plate left between a track groove and the Hall slot (mm)", min(lands), D["tk_slot_land"],
          "; ".join(f"track {t['k']} r {t['r']:.2f} at {t['ang']:.1f}° ±{t['half']:.1f}°" for t in D["tk"])
          + "; lands " + ", ".join(f"{v:.2f}" for v in lands))
    return r

def _split_rows(D, parts, r):
    """v0.22 [Ed 2 Nov 15:27]: detent boss on a bracket into a wall outboard of the flange; the train's pedestal on solid plate."""
    import math
    from .parts import mech, hall_slot
    r.row("split detent: boss lift under the spring, grub fully in, ball on a dimple rim (mm)", D["sp_lift"], D["sp_lift_max"],
          f"{D['det_force_max']:.2f} N; wall r {D['sp_wall_r0']:.2f}-{D['sp_wall_r1']:.2f}, {D['sp_wall_a'][0]:g}-{D['sp_wall_a'][1]:g}°, "
          f"I {D['sp_wall_I']:.1f} mm⁴, lever {D['sp_wall_e']:.2f}, height {D['sp_wall_h']:.1f}; E {D['ad_E'] / 1000:g} GPa [A]; "
          f"physical limit {D['ad_defl_max']:g} (20% of the dimple depth): margin {D['ad_defl_max'] / max(D['sp_lift'], 1e-9):.1f}x", higher_ok=False)
    sl = hall_slot.window(D)
    g = mech.track_grooves(D)
    r.row("split detent: pedestal groove clear of the Hall slot (plate land, mm)", g.distance_to(sl), D["tk_slot_land"],
          f"pedestal r {D['sp_ped'][0]:.2f}-{D['sp_ped'][1]:.2f}, ±{D['sp_ped'][2]:.1f}° about {D['ad_ang']:.0f}°")
    return r

def checks(D, parts):
    T = D["tgt"]; F = D["feel"]; r = Rows("base_drive")
    r.row("1220 can vs dial tube", D["offset"] - D["can_r"] - D["dial_tube_od"] / 2, T["motor_dial_tube"])
    r.row("motor pinion tip vs skirt ID (radial)", D["skirt_id"] / 2 - D["offset"] - D["hub_pin_tip_r"], 1.0,
          f"nylon {D['z_pinion']}T m{D['hub_mod']:.1f} (RW tooth form) / {D['z_hub_gear']}T hub, ratio {D['ratio_knob_motor']:.3f}, mesh {D['hub_cd']:.2f} vs motor {D['offset']:.2f}")
    r.row("hub mesh vs the KiCad motor axis (mm)", abs(D["hub_cd_err"]), 0.15,
          "negative err is a tight mesh; 0.05 mm is inside the 0.10 printed backlash", higher_ok=False)
    r.row("herringbone pinion teeth inside the ring", D["z_enc_pinion"], D["hb_z_min"],
          f"25° helix, virtual teeth {D['hb_virtual']:.1f} (classical 20° undercut wants ~17); mn {D['hb_mn']:.2f}, ring {D['z_ring']}T")
    r.row("herringbone pinion tip thickness vs MJF tooth floor", D["hb_tip_th"], D["hb_tooth_min"],
          f"stub addendum {D['hb_addendum']:.2f}, backlash {D['hb_backlash']:.2f} shared")
    note = (f"{D['fg_pinion']['part']} {D['fg_z_pin']}T × {D['fg_z_gear']}T on the {D['fg_ang']:.0f}° idler, "
            f"then {D['z_enc_pinion']}T into the {D['z_ring']}T herringbone, overall {D['fm_ratio']:.2f}:1, "
            f"can at {D['fm_ang']:.1f}°; knob Ø{D['knob_od']:.2f}; "
            + ", ".join(f"{k} {v:.2f}" for k, v in sorted(D["fm_clear"].items(), key=lambda kv: kv[1])))
    r.row("feel placement (worst plan clearance)", min(D["fm_clear"].values()), F["clear"], note)
    ro = F["can_d"] / 2 + D["motor_glue"] + D["fm_band_t"]
    r.row("feel saddle strap vs skirt ID (radial)", D["skirt_id"] / 2 - D["fm_cd"] - ro, F["clear"],
          f"open saddle: 2 bands × {D['fm_band_h']:g} over {D['fm_grip']:.1f} of the Ø{F['can_d']:g}×{F['can_len']:g} can, ears at ±{D['fm_split']:g}°")
    r.row("detent ball guided in its bore when latched (centre above the boss underside)", D["det_z_ball"] - D["det_dimple"] - D["det_z0"], 0.1,
          f"Ø{D['det_ball']:g} ball, spring {D['det_spring'][0]:g}×{D['det_spring'][1]:g} preload {D['det_preload']:g}, M{D['det_thread_d']:g}×{D['det_grub_len']:g} grub ±{D['det_grub_adj']:g}")
    if D["arm_det"] == "split" and D["ad_r"] is not None:   # v0.22: own spoke, train under the ball
        _split_rows(D, parts, r)
    elif D["arm_det"] == "arc" and D["ad_r"] is not None:   # v0.21: the inboard window no longer applies; the detent is on the arc
        _arc_rows(D, parts, r)
    else:
        r.row("detent angle margin inside its window (min of both sides, deg)" if D["det_n"] != 1 else "detent angle margin inside its window (one detent, deg)", min(D["det_off"] - D["det_lo"], D["det_hi"] - D["det_off"]), 0.0,
              f"detents at ±{D['det_off']:.1f}° from the Hall arm, r {D['det_r']:.2f}; latch ±{D['det_deg']:g}°")
    r.row("feel mount rib (radial depth)", D["fm_rib_r1"] - D["fm_rib_r0"], F["clear"],
          f"r {D['fm_rib_r0']:.2f}-{D['fm_rib_r1']:.2f}, under the saddle seat")
    can = _one(parts, "feel motor " + F["part"])
    pin = _one(parts, "feel motor pinion")
    r.row("feel can vs 1220 motor", can.distance_to(parts["motor"]), F["clear"])
    for i in (1, 2):
        if i - 1 == D["fg_idler"]:
            r.row("feel pinion vs compound gear (centre-distance error, mm)", abs(D["fg_cd_err"]), 0.12,
                  f"CD {D['fg_cd']:.3f}, nominal {(D['fg_z_gear'] + D['fg_z_pin']) * D['fg_mod'] / 2:.3f} "
                  f"({D['fg_pinion']['part']}, {D['fg_pinion']['material']}, bore Ø{D['fg_pinion']['bore']:g}); "
                  f"shaft stick-out {D['fg_shaft_len']:.1f} mm", higher_ok=False)
        else:
            r.row(f"feel pinion vs idler {i}", pin.distance_to(parts[f"idler pinion {i}"]), F["clear"])
    r.row("cradle web left round a support after the bridge cut", D["cr_web_min"], D["cr_web_min"],
          f"fillet R{D['cr_bridge_fillet']:g} at the narrowest point of each top-idler breakout")
    # The clear race is fused into the cradle and sits flat on the PCB. Pins are hollow tubes in two VCSEL holes.
    from ..common.process import PROCESS
    r.row("hollow race pin wall vs the SLA feature floor", D["em_wall"], PROCESS["sla"]["feature"],
          f"bore Ø{D['em_ap']:.2f} is the aperture; pin OD Ø{D['em_pin_od']:.2f}")
    r.row("emitter package covers its hole", D["em_pkg_min"] - D["em_hole_d"], 2 * D["em_cover_k"] * D["em_pkg_min"],
          f"smaller body Ø{D['em_pkg_min']:.2f}; pin hole Ø{D['em_hole_d']:.2f}; open hole Ø{D['em_ap']:.2f}; reverse mount")
    r.row("race web beside a pin hole", D["em_web"], D["ot_seat_gap"],
          f"annulus each side of Ø{D['em_hole_d']:.2f} at r {D['ot_r']:.2f}; SLA feature floor is {PROCESS['sla']['feature']:.2f} and does not fit")
    if D["ot_keep_ang"]:   # v0.19b: with the closed ring the emitters are evenly spaced; the cageless balls roll past them anyway
        r.row("emitter hole centre clears the nearest ball", D["em_ball_clear"], 0.0,
              f"holes sit in the ball gaps; pins in VCSEL holes {D['em_pin_i'][0]} and {D['em_pin_i'][1]}")
    return r
