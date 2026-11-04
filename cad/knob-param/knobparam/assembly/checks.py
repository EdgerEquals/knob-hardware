"""Checks runner. LOCAL checks live in each sub-assembly (checks.py, own parts + scope only); the CROSS checks below need parts
or values from more than one sub-assembly and are owned by the assembly agent. Plus pairwise solid clashes (bbox prefilter,
OCC intersection volume, parallel spawn pool, cached per part-hash pair)."""
import hashlib, itertools, json, math, os, time
from build123d import *
from ..common.cache import CACHE
from ..common.checks import Rows, min_dist
from ..common.util import cyl
from ..common import model

KNOWN = {"PCB / motor": "1220 rear boss Ø3×0.6 into the PCB front: the KiCad M1 footprint has no Ø3.2 relief hole yet (v0.13 same)",
         # v0.32: J10 (the 2x14 placeholder test-pad field on B.Cu, 0.05 thick) sits at y -57.27..-52.92 in the committed v0.11 board, 4 mm
         # off the board's bottom edge (-53.3); the key's back end (behind the case rim, at the cover's face) meets those pads. Stale
         # placement: the KiCad regeneration (handover, after step 2) puts J10 back on the board.
         "PCB back parts (Hall decouplers, J10, DRV8837, passives) / USB-C key (printed, held by the back cover)":
             "J10 placeholder pads 4 mm off the board edge in the v0.11 KiCad board (stale); fixed by the KiCad regeneration"}

def local(D, parts, owner, subs=None):
    rows = []
    for s in model.ALL:
        if subs and s not in subs: continue
        rows += model.sub(s).checks(model.view(D, s), {n: p for n, p in parts.items() if owner[n] == s})
    return rows

def _dial(parts, which="all"):
    """v0.25 [Ed 18:12]: the control dial is two parts (lower part, dish); before that one. which: "lower", "dish" or "all"
    (fused for distance checks)."""
    if "control dial" in parts:
        return parts["control dial"]
    pre = {"lower": ("control dial lower part",), "dish": ("control dial dish",), "all": ("control dial lower part", "control dial dish")}[which]
    q = [s for n, s in parts.items() if n.startswith(pre)]
    return q[0] if len(q) == 1 else Compound(children=q)

def cross(D, parts):
    from .. import control_dial as cd
    from . import hall_dyn
    T = D["tgt"]; r = Rows("assembly"); row = r.row
    Tdeg = D["travel_deg"]
    TR = (-Tdeg, -D["det_deg"], 0.0, D["det_deg"], Tdeg); on = D["screen_on_dial"]
    Dc = model.view(D, "control_dial")
    _arm0 = cd.arm(Dc, 0.0)                       # build once; arm(D, t) is that solid rotated about Z
    ARM = {t: Rot(0, 0, t) * _arm0 for t in TR}
    if on and D.get("cart"):   # v0.24 [Ed 3 Nov 12:41-12:58] dial screen as a bezel cartridge
        _cart_cross(D, parts, row, TR, Dc)
    elif on:
        stat = {n: parts[n] for n in parts if n.startswith("adapter part") and not n.endswith(D["b2b_at"])}
        stat["rod + nut"] = cyl(D["nut_s"] / math.sqrt(3), D["z_board_top"], D["nut_m"])
        if "adapter cup (fixed)" in parts: stat["adapter cup (fixed)"] = parts["adapter cup (fixed)"]
        smin, swho = 1e9, ""
        for t in TR:
            sb = cd.strap_bent(Dc, t)
            for n, q in stat.items():
                d = sb.distance_to(q)
                if d < smin: smin, swho = d, n
        row("FPC service strap vs U3 / nut / cup (±travel)", smin, T["strap_vs_parts"], f"nearest: {swho}; strap z {D['strap_z0']:.2f}-{D['strap_z1']:.2f}")
    else:
        row("jumper FPC vs TMAG5273 U3", parts["screen jumper FPC [A]"].distance_to(parts["adapter part U3"]), 0.3, f"B2B over {D['b2b_at']}")
    M = D["motor"]; ex, ey = D["enc_xy"]; worst = 9.9
    for s in (-1, 1):
        x = D["offset"] + s * M["term_pitch"] / 2; rr = math.hypot(x - ex, 0 - ey)
        tip = -M["term_len"] - D["tab_solder"]
        if D["rim_r0"] - 1.2 <= rr <= D["rim_r1"] + 1.2: worst = min(worst, tip - D["rim_top"])
    row("1220 tab + solder vs encoder rim (axial)", worst, T["tab_vs_rim"], "tab at r %.2f from H2, rim r %.2f-%.2f" % (math.hypot(D["offset"] + M["term_pitch"] / 2 - ex, ey), D["rim_r0"], D["rim_r1"]))
    tips = {}
    for a, nm in [(D["enc_ang"], "encoder pinion")] + [(a, f"idler {i + 1}") for i, a in enumerate(D["idler_angs"])]:
        x, y = D["enc_cd"] * math.cos(math.radians(a)), D["enc_cd"] * math.sin(math.radians(a))
        tips[nm] = cyl(D["d_pin_tip"] / 2, D["h_pin0"], D["pin_face"], x, y)
    tips["motor collar"] = cyl(D["motor_collar_od"] / 2, 0, 40, D["offset"])
    hmin, hwho = 1e9, ""
    for t in TR:
        arm = ARM[t]
        for n, s in tips.items():
            d = arm.distance_to(s)
            if d < hmin: hmin, hwho = d, n
    row("Hall arm vs pinions / motor collar (±travel)", hmin, T["hall_vs_pinions"], f"nearest: {hwho}")
    if D["hall_layout"] == "vernier":
        cr = parts["base cradle"]; sens = [parts[n] for n in parts if n.startswith("hall sensor")]
        from ..common.util import sector
        if D.get("hs_slot"):   # v0.30 [Ed 4 Nov 15:46]: the hard stop is two faces in the Hall slot; the lever has no stops
            from ..base_drive.parts import hall_slot as _hs
            stops = _hs.stop_faces(model.view(D, "base_drive"))
            near = None
            for _s, _j, r0, r1, poly in D["hs_stop_polys"]:
                angs = [math.degrees(math.atan2(y, x)) % 360 for x, y in poly]
                lo, hi = min(angs), max(angs)
                q = sector(max(r0 - 0.8, 0.2), r1 + 0.8, (hi - lo) / 2 + 2.0, -1, 20, (lo + hi) / 2)
                near = q if near is None else near + q
            cr_far = cr - near                                                      # stop faces checked separately
        else:
            cr_far = cr - sector(0, D["sl_r"] + 3, 60, -1, 20, D["sl_ang"]) if D["fan_on"] else cr   # stop blocks checked separately
        row("Hall arm / fan vs cradle, detent blocks, track (±travel)", min_dist(list(ARM.values()), [cr_far]), T["arm_vs_cradle"], f"slot r {D['hv_slot_r0']:.2f}-{D['hv_slot_r1']:.2f}")
        if D.get("hs_slot"):
            note = (f"stop contact at ±{D['travel_deg']:.2f}° (past the ±{D['det_deg']:g}° end detent by {D['travel_deg'] - D['det_deg']:.2f}°, "
                    "the ball's bore play)")
            row("Hall bar vs the slot's stop faces at rest", ARM[0.0].distance_to(stops), T["arm_vs_cradle"])
            row("Hall bar vs the slot's stop faces when latched at ±det_deg", min(ARM[t].distance_to(stops) for t in (-D["det_deg"], D["det_deg"])), 0.02, note)
            row("Hall bar meets the slot's stop faces at ±travel (gap)", max(ARM[t].distance_to(stops) for t in (-Tdeg, Tdeg)), 0.02,
                "[Ed 4 Nov 15:46] flush contact = the hard end stop; " + "; ".join(
                    f"{'-' if _s < 0 else '+'}: the bar's link pads {_j + 1}-{_j + 2}, r {r0:g}-{r1:g}" for _s, _j, r0, r1, _p in D["hs_stop_polys"]), higher_ok=False)
            ov = max(((ARM[t] & stops).volume if ARM[t].distance_to(stops) < 1e-6 else 0.0) for t in (-Tdeg, Tdeg))
            row("Hall bar into the slot's stop faces at ±travel (overlap, mm³)", ov, 0.01, "the faces are the bar's link faces at ±travel", higher_ok=False)
            Td = D["dsp"]["T_design"]; allow = min(D.get("utr_uts", 41.6), D.get("pa12_uts", 43.0)) / 2
            bear = []
            for _s, _j, r0, r1, poly in D["hs_stop_polys"]:
                Lc = math.hypot(poly[1][0] - poly[0][0], poly[1][1] - poly[0][1])
                bear.append(Td / ((r0 + r1) / 2) / (Lc * D["hs_stop_h"]))
            row("hard stop: bearing on the stop faces at the dial design torque (MPa)", max(bear), allow,
                f"{Td:g} mNm [A] on one face: " + ", ".join(f"{b_:.1f}" for b_ in bear) + f" MPa over the face x the bar's {D['hs_stop_h']:.2f} in the "
                f"plate; UTR-8100 / PA-12 strength / 2 (the v0.29 r 7 stop blocks took ~72 MPa at this torque)", higher_ok=False)
        elif D["fan_on"]:
            stops = cr - cr_far
            lv = lambda t: ARM[t]
            row("dial lever vs hard stops at rest", lv(0).distance_to(stops), T["arm_vs_cradle"])
            row("dial lever vs hard stops when latched at ±det_deg", min(lv(t).distance_to(stops) for t in (-D["det_deg"], D["det_deg"])), 0.02,
                f"stop contact at ±{D['travel_deg']:.2f}° (past the ±{D['det_deg']:g}° end detent by {D['travel_deg'] - D['det_deg']:.2f}°, the ball's bore play)")
            row("dial lever meets the stop faces at ±travel (gap)", max(lv(t).distance_to(stops) for t in (-D["travel_deg"], D["travel_deg"])), 0.02, "flush contact = hard end stop", higher_ok=False)
        if D["fan_on"]:
            if D["cu_on"]:
                md, mh = D["cu_mag"]; m_dip = D["hv_br"] / (4e-7 * math.pi) * math.pi * (md / 2e3) ** 2 * (mh / 1e3)
                cus = [parts[n] for n in parts if n.startswith("cushion magnet")]
                dmin = min(c.distance_to(s_) for c in cus for s_ in sens) + md / 2
                bst = 1e3 * 2e-7 * m_dip / (dmin / 1e3) ** 3 * len(cus)
                row("cushion magnets: stray field at the nearest Hall-row sensor / range", bst / D["hv_sensor"]["range_mt"], D["cu_stray_max"],
                    f"{len(cus)} × Ø{md:g}×{mh:g}, nearest {dmin:.1f} mm, ≤ {bst:.2f} mT", higher_ok=False)
            fan_d = min(ARM[t].distance_to(parts[n]) for t in TR for n in parts if n.startswith("detent") and "ball" not in n)
            row("fan vs detent springs / grubs (±travel)", fan_d, T["arm_vs_cradle"])
        mi = D["hv_mid"]["idx"] if D["hv_mid"] else -1
        s53 = [parts[n] for n in parts if n.startswith("hall sensor") and "TMAG5273" not in n]
        s73 = [parts[n] for n in parts if n.startswith("hall sensor") and "TMAG5273" in n]
        row("Hall bar / magnets vs TMAG5253 tops (air gap, ±travel)", min_dist(list(ARM.values()), s53), D["hv_gap"] - 0.01, f"element gap {D['hv_elem_gap']:.2f}")
        if s73:
            row("Hall bar / magnets vs TMAG5273 (H3) top (air gap, ±travel)", min_dist(list(ARM.values()), s73), D["hv_gap_mid"] - 0.01,
                f"SOT-23-6 h {D['hv_mid']['h']:g}; element gap {D['hv_mid_elem_gap']:.2f}; magnet faces z {D['hv_z_mag0']:.2f}")
        row("Hall sensors vs cradle", min_dist(sens, [cr]), T["sensor_vs_cradle"])
        H = hall_dyn.analyse(D)
        pk53 = max(float(H["B_peak_j"][j]) for j in range(D["hv_n"]) if j != mi)
        row("Hall peak |Bz| at the TMAG5253s vs range (mT)", pk53, 0.9 * D["hv_sensor"]["range_mt"], f"{D['hv_sensor']['part']} ±{D['hv_sensor']['range_mt']:g} mT; poles " + "/".join("N" if p > 0 else "S" for p in D["hv_pol"]), higher_ok=False)
        if mi >= 0:
            import numpy as _np
            bv = hall_dyn.field_vec(D, mi, _np.linspace(-D["travel_deg"], D["travel_deg"], 23))
            pax = float(_np.abs(bv).max()); pxy = float(_np.abs(bv[:, :2]).max()); pz = float(_np.abs(bv[:, 2]).max())
            row("Hall peak field at the TMAG5273 (H3), worst axis vs range (mT)", pax, 0.9 * D["hv_mid"]["range_mt"],
                f"{D['hv_mid']['part']} ±{D['hv_mid']['range_mt']:g} mT/axis: |Bz| ≤ {pz:.1f}, |Bx|,|By| ≤ {pxy:.1f}; elem gap {D['hv_mid_elem_gap']:.2f}", higher_ok=False)
        row("Hall angle noise, worst over ±travel (deg rms)", H["s_theta_worst"], 0.01, f"min |dB/dθ| {H['slope_min']:.1f} mT/deg, noise {H['noise_mT'] * 1e3:.0f} µT rms", higher_ok=False)
    if D["kb_groove_h"] > 0:
        kb = [parts[n] for n in parts if n.startswith("knob") and "ball" not in n]
        row("seat: dial vs knob (race region)", min(_dial(parts, "dish").distance_to(q) for q in kb), T["seat_vs_knob"])
    row("idler 1 vs 1220 can", math.hypot(D["idler_xy"][0][0] - D["offset"], D["idler_xy"][0][1]) - D["can_r"] - D["d_pin_tip"] / 2, T["idler_motor"])
    feel_names = [n for n in parts if n.startswith("feel motor")]
    feels = [parts[n] for n in feel_names]
    clip = parts["feel motor saddle seat [A]"].fuse(parts["feel motor saddle strap [A]"])
    can = [parts[n] for n in feel_names if "shaft" not in n and "saddle" not in n and "pinion" not in n][0]
    pin = [parts[n] for n in feel_names if "pinion" in n][0]
    knob = parts["knob glass sleeve"]
    rings = [parts[n] for n in parts if n.startswith("bottom internal ring")]
    ring = rings[0] if len(rings) == 1 else rings[0].fuse(*rings[1:])
    row("feel saddle vs knob skirt", clip.distance_to(knob), D["feel"]["clear"],
        f"can {can.distance_to(knob):.2f} inside the skirt; {D['fg_pinion']['part']} at {D['fm_ang']:.1f}°, overall {D['fm_ratio']:.2f}:1, knob Ø{D['knob_od']:.2f}")
    row("feel can/saddle vs bottom ring", min(can.distance_to(ring), clip.distance_to(ring)), D["feel"]["clear"])
    row("feel pinion vs encoder pinion", pin.distance_to(parts["encoder pinion"]), D["feel"]["clear"])
    row("feel motor vs dial tube", min(p.distance_to(_dial(parts, "lower")) for p in feels), D["feel"]["clear"])
    row("feel motor vs Hall arm (±travel)", min_dist(list(ARM.values()), feels), T["hall_vs_pinions"])
    # v0.17 swept motion: springs follow the lever pin, track balls roll at half the dial angle
    from ..base_drive.parts.mech import springs_at, track_balls_at
    if D.get("es_on"):   # v0.31 [Ed 4 Nov 16:35]: the lifted springs, from the Hall arm column's pin to the posts' pins
        from ..base_drive.parts.mech import es_springs_at
        Db = model.view(D, "base_drive")
        low = _dial(parts, "lower"); zs = D["es_z"]
        fixed = {n: q for n, q in parts.items() if not n.startswith(("base cradle", "centring spring", "spring anchor pin", "spring pin on",
                                                                       "control dial", "case"))}
        fixed = {n: q for n, q in fixed.items() if q.bounding_box().min.Z < zs + 2 and q.bounding_box().max.Z > zs - 2}
        smin, swho = 1e9, ""
        for th in TR:
            for sp in es_springs_at(Db, th):
                for n, q in list(fixed.items()) + [("control dial lower part (turned)", Rot(0, 0, th) * low)]:
                    d = sp.distance_to(q)
                    if d < smin: smin, swho = d, n
        row("lifted centring springs vs the dial's lower part and the fixed parts (±travel)", smin, T["arm_vs_cradle"],
            f"[Ed 4 Nov 16:35] springs at z {zs:g} from the Hall arm's column pin to the posts; nearest: {swho}; "
            f"sampled {', '.join(f'{t:+.1f}' for t in TR)}")
        # the springs' pull twists the Hall arm's rib a little: a Hall angle offset in step with the angle (calibrated out) [A]
        Ft = D["dial_spring"] * Tdeg / D["es_rp"]                               # net tangential pull at ±travel, N
        zc = (D["ha_rib_z_top"] + D["ha_rib_z_low"]) / 2; Lr = D["es_rp"] - D["ha_rib_r_hub"]
        b_, h_ = max(D["ha_rib_w0"], D["ha_rib_z_top"] - D["ha_rib_z_low"]), min(D["ha_rib_w0"], D["ha_rib_z_top"] - D["ha_rib_z_low"])
        J = b_ * h_ ** 3 * (1 / 3 - 0.21 * h_ / b_ * (1 - h_ ** 4 / (12 * b_ ** 4)))
        G = D.get("pa12_E", 1700.0) / 2.6
        tw = Ft * (zs - zc) * Lr / (G * J)
        off = math.degrees(tw * (zc - D["hv_z_mag0"]) / D["hv_r_mid"])
        row("lifted centring springs: Hall angle offset from the rib's twist at ±travel (deg, estimate)", off, 0.05,
            f"{Ft:.2f} N tangential at z {zs:g} on the column, rib {D['ha_rib_w0']:g} wide x {D['ha_rib_z_top'] - D['ha_rib_z_low']:.2f} deep over "
            f"{Lr:.2f} from the tube, PA-12 G {G:.0f} [A]: twist {tw * 1e3:.2f} mrad, magnets {tw * (zc - D['hv_z_mag0']) * 1e3:.1f} µm; "
            "in step with the angle, so a calibration removes it", higher_ok=False)
    else:
        # coils seat on the anchor posts, so the cradle distance is ~0 there; check they stay clear of the drive
        obstacles = [parts["motor"], parts["encoder pinion"], *rings]
        spr_d = min(sp.distance_to(o) for th in TR for sp in springs_at(D, th) for o in obstacles)
        row("centring springs vs motor / encoder / ring across ±travel", spr_d, D["feel"]["clear"],
            f"lever pin at {D['sl_ang']:.0f}° + θ; sampled {', '.join(f'{t:+.1f}' for t in TR)}")
    if D.get("arm_det") in ("arc", "split") and D.get("tk"):
        _arc_cross(D, parts, row, TR, ARM)
    else:
        roll_left = min(D["bt_half"] - abs(th) / 2 for th in TR)
        row("track balls stay in the groove across ±travel (deg of groove left)", roll_left,
            math.degrees((D["bt_ball"] / 2) / min(D["bt_rs"])),
            "ball rolls at θ/2 between the plate groove and the ear; end detents at ±%.2f°, hard stop ±%.2f°" % (D["det_deg"], D["travel_deg"]))
    gear = parts[f"feel compound gear {D['fg_z_gear']}T"]
    tb_d = min(b.distance_to(gear) for th in TR for b in track_balls_at(D, th))
    row("track balls vs compound gear across ±travel", tb_d, D["feel"]["clear"],
        "balls posed at θ/2 for each sample")
    row("printed spur stays on the feel side of the centre tube", D["enc_cd"] - D["fg_tip"] - 2.5, D["feel"]["clear"],
        f"{D['fg_z_gear']}T tip r {D['fg_tip']:.2f} at the idler r {D['enc_cd']:.2f}; tube Ø5")
    row("printed spur tooth tip vs MJF short-feature floor", D["spur_tip_th"], D["spur_tooth_min"],
        f"thinnest nylon spur (hub, motor pinion, {D['fg_z_gear']}T, feel pinion); preferred {D['hb_tooth_min']:.2f}")
    row("compound gear vs encoder rim (axial)", D["fg_z_bot"] - D["rim_top"], D["fg_clear"],
        f"gear z {D['fg_z_bot']:.2f} to {D['fg_z_top']:.2f}; rim top {D['rim_top']:.2f}; sensor dropped {D['enc_drop']:.2f} onto the daughterboard")
    ot_bits = [parts[n] for n in parts if n.startswith("outer thrust") and "blank" not in n]
    caps = [n for n in parts if n.endswith(" cap")]

    def _cap_mount(cap, other):
        if cap == "pinion cap":
            return other == "pinion"
        if cap == "encoder pinion cap":
            return other in ("encoder pinion", "encoder shaft")
        if cap.startswith("idler pinion ") and cap.endswith(" cap"):
            idx = cap.split()[2]
            return other in (f"idler pinion {idx}", f"idler pin {idx}")
        if cap == "feel motor pinion cap":
            return other.startswith("feel motor pinion")
        if cap == "hub gear cap":
            return other.startswith("knob upper-cap")
        return False

    if caps:
        cap_d, cap_who = 1e9, ""
        for n in caps:
            for m, s in parts.items():
                if m == n or _cap_mount(n, m):
                    continue
                d = parts[n].distance_to(s)
                if d < cap_d:
                    cap_d, cap_who = d, f"{n} / {m}"
        row("resin caps vs everything they do not mount on", cap_d, 0.3,
            f"nearest {cap_who}; UTR-8100 stepped Fresnel, press modelled at {D['cap_fit_gap']:.2f}")
    row("bottom thrust land, clear resin under the groove", D["ot_land_th"], D["ot_land_min"],
        f"groove bottom z {D['ot_z'] - D['ot_rg']:.2f}; ball centre {D['ot_z']:.2f}; underside was skirt_gap {D['skirt_gap']:.2f}, now {D['h_skirt0']:.2f}. UTR-8100, not an insert",
        procs=("sla", "sla"))
    hosts = rings + ([parts["knob lower-cap land"]] if "knob lower-cap land" in parts else [])
    row("outer thrust balls vs bottom ring", min(b.distance_to(h) for b in ot_bits for h in hosts), 0.0,
        f"Ø{D['ot_ball_d']:g} load × {D['ot_n']}, glass {D['ot_spacer_min']:g}–{D['ot_spacer_max']:g} × {D['ot_n_spacer']}, ruby {len(D['ot_ruby_idx'])} on r {D['ot_r']:.2f}",
        procs=("buy", "mjf"))
    row("spacer clears both tracks at the large end", D["ot_track_clear_max"], D["ot_seat_gap"],
        f"{D['ot_track_clear_min']:.3f} at {D['ot_spacer_min']:g} mm, {D['ot_track_clear_alt']:.3f} at {D['ot_spacer_alt']:g} mm")
    row("spacer gap at the large end (no jam)", D["ot_gap_max"], D["ot_play_max"],
        f"chord {D['ot_chord']:.3f}; ring play {D['ot_play_total']:.2f}", higher_ok=False)
    row("spacer still touches at the small end (gap)", D["ot_gap_min"], D["ot_play_max"],
        f"1.588 mm gap {D['ot_gap_alt']:.3f}", higher_ok=False)
    row("spacer gap stays positive at the small end", D["ot_gap_min"], D["ot_play"])
    row("light path between a load ball and a spacer", D["ot_light_gap"], D["ot_play"],
        f"axial window beside a {D['ot_spacer_max']:g} spacer {D['ot_track_clear_max']:.3f}")
    # The glass top end face stays bare so the wall can shine up into the dial. A wafer of that annulus must miss every printed part.
    zi, ch = D["sleeve_z1"], D["sleeve_chamfer"]
    ri, ro = D["sleeve_id"] / 2 + ch, D["knob_od"] / 2 - ch
    sh = D.get("glass_to_dial", False)
    cham = sh and D.get("cap_top") == "chamfer"
    if cham:   # the flat face sits between the two ground chamfers
        ri, ro = D["sleeve_id"] / 2 + D["sleeve_top_cin"], D["knob_od"] / 2 - D["sleeve_top_cout"]
    rim = cyl(ro, zi, 0.01) - cyl(ri, zi - 0.05, 0.11)   # v0.19b: thin wafer, so the 0.3 running gap to the dial lip reads as 0.3
    rb = rim.bounding_box()
    def _hits(bb, m=1.0):   # v0.24: 1 mm margin, so a part that starts just above the rim (the dial bezel, 0.3 up) is measured too
        return not (bb.max.X < rb.min.X - m or bb.min.X > rb.max.X + m or bb.max.Y < rb.min.Y - m or bb.min.Y > rb.max.Y + m
                    or bb.max.Z < rb.min.Z - m or bb.min.Z > rb.max.Z + m)
    # v0.19b [Ed 2 Nov]: the upper cap is bonded on the glass (shoulder on the face, or cone on the inner chamfer), so it is left out.
    near = [(n, s) for n, s in parts.items() if not n.startswith("knob glass") and not (sh and n.startswith("knob upper-cap"))
            and _hits(s.bounding_box())]
    rim_d, rim_who = min(((s.distance_to(rim), n) for n, s in near), default=(1e9, ""))
    row("printed parts clear the glass top rim" + ((" (cap seated on the inner chamfer)" if cham else " (cap shoulder bonded on it)") if sh else ""),
        rim_d, ch, f"nearest {rim_who}; end face r {ri:.2f}–{ro:.2f} at z {zi:.2f} " +
        ("stays open into the dial lip" if (cham or not sh) else f"under the {D['cap_shoulder_t']:g} mm cap shoulder (bond {D['cap_shoulder_glue']:g})"))
    entry = min(D["ot_r"] - D["sleeve_id"] / 2, D["knob_od"] / 2 - D["ot_r"])
    row("light path through the emitter holes, the race and into the glass", min(D["em_ap"] / 2, entry), D["ot_seat_gap"],
        f"{2 * D['em_n']} reverse-mount holes on r {D['ot_r']:.2f}; aperture Ø{D['em_ap']:.2f}; "
        f"hollow pins in VCSEL {D['em_pin_i'][0] // 2 + 1} (round) and {D['em_pin_i'][1] // 2 + 1} (radial slot); "
        f"land {D['ot_land_th']:.2f} mm")
    # ---- v0.16 relative knob-vs-dial angle: diametric ring magnet in the knob under the dial TMAG5273 ----
    if D["rel_sensor"]:   # v0.16b [Ed]: removed by default
        B = ring_field(D)
        row("dial TMAG5273: peak |B| from the knob ring / range (nominal gap)", B["peak"] / D["tm_range_mt"], 0.3,
            f"ring Ø{D['tm_ring'][1]:g}/Ø{D['tm_ring'][0]:g}×{D['tm_ring'][2]:g} N52 diametric, element gap {D['tm_gap']:.2f}: |B| {B['peak']:.0f} mT, in-plane {B['bxy_min']:.0f}-{B['bxy_max']:.0f} mT")
        row("dial TMAG5273: peak |B| / range with the dial lifted to the stop", B["peak_lift"] / D["tm_range_mt"], 0.9,
            f"gap {D['tm_gap_min']:.2f}: {B['peak_lift']:.0f} mT", higher_ok=False)
    from ..common import gearcheck
    gearcheck.rows(D, row)          # contact ratio and backlash band; tooth counts are this stack's, not the old spur set
    gearcheck.strength_rows(D, row)   # v0.25 [Ed 19:10]: Lewis allowables of the hub mesh and the ring stage (MJF PA-12)
    pz0, pz1 = D["h_pinion0"], D["h_pinion0"] + D["motor_pinion_face"]
    row("hub mesh: engaged face, 1220 pinion inside the hub-gear teeth (mm)", min(pz1, D["h_band1"]) - max(pz0, D["knob_hub_z0"]),
        D["hub_face"] - 0.01, f"pinion z {pz0:.2f}-{pz1:.2f}, hub-gear teeth z {D['knob_hub_z0']:.2f}-{D['h_band1']:.2f} [Ed 19:10 face {D['hub_face']:g}]")
    row("1220 pinion top under the clear cap and the hub-gear collar (axial gap)", D["h_band1"] - pz1, 0.3,
        f"shaft tip z {D['h_shaft_tip']:.2f}; cap underside / collar bottom z {D['h_band1']:.2f}")
    hg = [s for n, s in parts.items() if n.startswith(("knob hub gear ring", "knob upper-cap hub"))]   # v0.25 [Ed 19:46]: the inner hub
    if hg:
        # v0.25 [Ed 19:46]: the PA-12 hub's flat underside now spans the 1220 shaft tip (0.5 over it, the pinion-top row's gap), so
        # this row keeps to what it says: the can and the boss (below the gearbox front)
        lo = [s & cyl(30.0, -60.0, D["h_motor_front"] + 60.0 + 0.01, D["offset"]) for n, s in parts.items() if n == "motor"]
        row("hub-gear ring vs the 1220 can and boss", min(hg[0].distance_to(q) for q in lo), 0.5,
            f"teeth down to z {D['knob_hub_z0']:.2f} (v0.24 39.6); can top z {D['motor']['motor_len'] + D['motor']['gearbox_len']:.1f}, "
            f"boss to z {D['h_motor_front']:.1f}")
    from .. import optics
    optics.beam_rows(D, parts, row)  # no-op while optics_on is False
    # v0.19 [Ed]: screen rule. Every part behind the PCB keeps screen_air (1.0) from both back AMOLEDs.
    scr = {n: parts[n] for n in parts if n.startswith("back AMOLED")}
    if scr:
        case_like = ("case", "back cover", "glow coat", "corner screw", "corner insert", "jack ", "USB-C", "back AMOLED", "lower screen pad", "knob bolt")
        rear = {n: p for n, p in parts.items() if n != "PCB" and not n.startswith(case_like) and p.bounding_box().min.Z < D["z_pcb_back"] - 0.01}
        smin, swho = 1e9, ""
        for sn, sp in scr.items():
            sb = sp.bounding_box()
            for n, p in rear.items():
                pb = p.bounding_box()
                if pb.max.X < sb.min.X - 3 or pb.min.X > sb.max.X + 3 or pb.max.Y < sb.min.Y - 3 or pb.min.Y > sb.max.Y + 3:
                    continue
                d = sp.distance_to(p)
                if d < smin: smin, swho = d, f"{n} over the {sn.split('(')[0].replace('back AMOLED ', '').strip()} screen"
        row("parts behind the PCB vs the back AMOLEDs (screen rule)", smin, D.get("screen_air", 1.0) - 0.01, f"nearest: {swho}")
    # v0.20 [Ed 2 Nov]: the clear OLED moved 1.4 toward the knob (knob down 5.2, OLED down 3.8 on the panel)
    oled = [parts[n] for n in parts if n.startswith("clear OLED")]
    if oled:
        o = oled[0]; ob = o.bounding_box(); omin, owho = 1e9, ""
        skip = ("PCB", "PCB back parts", "glow coat", "case")
        for n, p in parts.items():
            if n.startswith("clear OLED") or n in skip or n.startswith(skip):
                continue
            pb = p.bounding_box()
            if pb.max.X < ob.min.X - 2 or pb.min.X > ob.max.X + 2 or pb.max.Y < ob.min.Y - 2 or pb.min.Y > ob.max.Y + 2 \
                    or pb.min.Z > ob.max.Z + 2 or pb.max.Z < ob.min.Z - 2:
                continue
            d = o.distance_to(p)
            if d < omin: omin, owho = d, n
        if omin < 1e9:
            row("clear OLED vs the knob base and nearby parts", omin, 0.3, f"nearest: {owho}")
    return r

def _cart_cross(D, parts, row, TR, Dc):
    """v0.24 [Ed 3 Nov 12:41-12:58]: the strap loop swept over ±travel, the bezel over the main knob, the faceplate left where it was."""
    from .. import control_dial as cd
    T = D["tgt"]
    stat = {"rod + nut": cyl(D["nut_s"] / math.sqrt(3), D["z_board_top"], D["nut_m"])}   # fixed (the strap's foot sits on the board)
    rot = {n: parts[n] for n in parts if n.startswith("dial board") and not n.startswith("dial board (")}   # turn with the dial
    rot["control dial"] = _dial(parts, "all")
    smin, swho = 1e9, ""
    for t in TR:
        sb = cd.strap_loop(Dc, t)
        for n, q in stat.items():
            d = sb.distance_to(q)
            if d < smin: smin, swho = d, f"{n} at {t:+.1f}°"
        for n, q in rot.items():
            d = sb.distance_to(Rot(0, 0, t) * q)
            if d < smin: smin, swho = d, f"{n} at {t:+.1f}°"
    row("strap loop vs nut / rod / dial-board parts / dial (±travel)", smin, T["strap_vs_parts"],
        f"nearest: {swho}; ribbon z {D['strap_z0']:.2f}-{D['strap_z1']:.2f} from (0, -4.6) on the rod-link board to (0, 4.0) under the dial board (panel frame)")
    bz = parts.get("dial bezel (printed cartridge ring)")
    kn = {n: q for n, q in parts.items() if n.startswith(("knob glass", "knob upper-cap", "knob drip", "knob lower-cap"))}
    if bz is not None and kn:
        d, who = min((bz.distance_to(q), n) for n, q in kn.items())
        row("bezel bottom vs the main knob (running gap)", d, D["knob_run"] - 0.01,
            f"nearest: {who}; bezel underside z {D['z_lip0']:.2f} = the v0.23 lip underside, knob top {D['z_knob_top']:.2f}: the main knob does not move")
    lo = [q for n, q in parts.items() if n.startswith("control dial lower part")]
    if lo:   # v0.25 [Ed 18:12]: the lower part goes in before the cap, the cap over its tube, the dish on last
        from ..common.util import tube
        lo = lo[0]; tip = D["hb_tip_r"]; spg = D["sleeve_lip_r"]; gl = D["sleeve_id_worst"] / 2
        rr = min(tip, spg)   # the ring's innermost: its teeth (tips) and the plug ring up into the glass (ID sleeve_lip_r)
        d_ring = lo.distance_to(tube(rr, rr + 3.0, -5.0, 80.0))           # exact: the lower part's outermost point vs that circle, all z
        row("dial split: lower part passes down through the glass and the ring (ring bore - its outermost point, radial)", d_ring,
            T["arm_vs_cradle"], f"ring tips r {tip:.3f} (v0.25 spur), its plug ring ID r {spg:.2f}, worst glass bore r {gl:.2f}; outermost: the "
            "Hall rib's outer corner (r 16.90, the rib top); nothing of the cap or the detent boss is in yet")
        hi = lo & cyl(30.0, D["knob_hub_z0"] - 0.5, 30.0)                  # what the cap passes over on its way down
        rk = D["r_knob_bore"]
        d_cap = hi.distance_to(tube(rk, rk + 3.0, D["knob_hub_z0"] - 1.0, 30.0))
        row("dial split: upper cap passes down over the lower part (cap bore - the lower part above the cap's bottom, radial)",
            d_cap, 0.2, f"cap bore Ø{2 * rk:.2f} [Ed 18:12 Ø8.62] in the inner PA-12 hub [Ed 19:46]; above z {D['knob_hub_z0'] - 0.5:.1f} "
            f"only the Ø{D['dial_tube_od']:.2f} tube is there")
    v0 = D["faceplate_z_v023"]; fz, fz1 = D["faceplate_z"], D.get("z_fp1", D["faceplate_z"])
    row("faceplate front unchanged by the taller knob (|z - v0.23|)", max(abs(fz - v0), abs(fz1 - v0)), 0.001,
        f"interface {fz:.3f}, case {fz1:.3f}, v0.23 {v0:g}: lens top {D['z_top']:.2f} (+{D['z_top'] - (v0 + 18.0):.2f}), knob_proud "
        f"{D['knob_proud']:g}; rod-link board {D['z_floor']:.2f}-{D['z_board_top']:.2f}, main PCB front 0", higher_ok=False)


def _arc_cross(D, parts, row, TR, ARM):
    """v0.21 [Ed 2 Nov] swept checks for the detent on the arc and the three ball tracks. Balls roll θ/2 (both races move θ
    apart), the arm turns θ, everything else is fixed. Samples: ±travel (hard stops), ±det_deg (end detents), 0."""
    from ..base_drive.parts.mech import track_ball_list, arc_bridge
    T = D["tgt"]
    cr = parts["base cradle"]
    seat = D["bt_groove_r"] - D["bt_ball"] / 2
    balls = {th: track_ball_list(D, th) for th in TR}
    for t in D["tk"]:
        dmin, who = 1e9, ""
        for th in TR:
            bs = Compound(children=[Pos(x, y, z) * Sphere(d / 2) for n, d, x, y, z in balls[th] if n.startswith(f"track {t['k']} ")])
            low = parts.get("detent train pedestal (SLA, grub-set)", cr) if D["arm_det"] == "split" else cr
            for nm, s in (("pedestal" if D["arm_det"] == "split" else "plate", low), ("arm web", ARM[th])):
                d = bs.distance_to(s)
                if d < dmin: dmin, who = d, f"{nm} at {th:+.2f}°"
        row(f"ball track {t['k']}: balls stay inside both grooves across ±travel (ball to race, mm)", dmin, seat - 0.01,
            f"nearest: {who}; balls posed at θ/2, arm at θ; seat gap {seat:.2f} all round in the groove")
    # every fixed neighbour (moving Hall magnets posed with the arm)
    fixed = {n: s for n, s in parts.items() if not n.startswith(("base cradle", "control dial", "track ", "detent ", "hall magnet"))}
    allb = Compound(children=[Pos(x, y, z) * Sphere(d / 2) for th in TR for n, d, x, y, z in balls[th]])
    bb = allb.bounding_box()
    near = {n: s for n, s in fixed.items() if not (lambda q: q.max.X < bb.min.X - 3 or q.min.X > bb.max.X + 3 or q.max.Y < bb.min.Y - 3
                                                       or q.min.Y > bb.max.Y + 3 or q.max.Z < bb.min.Z - 3 or q.min.Z > bb.max.Z + 3)(s.bounding_box())}
    dmin, who = 1e9, ""
    for th in TR:
        bs = Compound(children=[Pos(x, y, z) * Sphere(d / 2) for n, d, x, y, z in balls[th]])
        for n, s in near.items():
            d = bs.distance_to(s)
            if d < dmin: dmin, who = d, n
        for n in [n for n in parts if n.startswith("hall magnet")]:
            d = bs.distance_to(Rot(0, 0, th) * parts[n])
            if d < dmin: dmin, who = d, n
    row("ball tracks vs every other part across ±travel (mm)", dmin, T["arm_vs_cradle"], f"nearest: {who} (Hall magnets posed with the arm)")
    if D["arm_det"] == "split":
        from ..base_drive.parts.mech import split_mount
        mt = split_mount(model.view(D, "base_drive"))
        bd = min(ARM[th].distance_to(mt) for th in TR)
        row("split detent mount (pedestal, wall, bracket, boss) vs the arm across ±travel (mm)", bd, T["arm_vs_cradle"],
            f"wall r {D['sp_wall_r0']:.2f}-{D.get('sp_wall_r1_used', D['sp_wall_r1']):.3f}; land top {D['ad_z_land']:.2f}, boss from {D['det_z0']:.2f}"
            + ("; v0.25 the separate detent block [Ed 18:15]" if D.get("dt_block") else ""))
        caps = [s for n, s in parts.items() if "cap" in n and "pinion" in n]
        if caps:
            dc = min(ARM[th].distance_to(c) for th in TR for c in caps)
            row("split detent: arm (flange, spokes) vs the pinion caps across ±travel (mm)", dc, T["arm_vs_cradle"],
                f"flange underside z {D['sp_z_fu']:.2f}")
        # v0.22b [Ed 15:50]: the pedestal grub is set from behind (back cover and screens off) through a hole in the PCB
        gx, gy = D["sp_grub_xy"]; zg = D["sp_z_grub0"]
        key = cyl(0.5, -13.4, zg + 13.4 - 0.01, gx, gy)   # Ø1.0 key line from just over the front AMOLED to the grub socket
        skip = ("base cradle", "detent pedestal grub", "detent train pedestal")
        ispcb = lambda n: n == "PCB" or n.startswith("main PCB")
        hits = [(n, key.distance_to(q)) for n, q in parts.items() if not n.startswith(skip) and not ispcb(n)
                and q.bounding_box().min.Z < zg and q.bounding_box().max.Z > -13.4]
        nn, dk = min(hits, key=lambda t: t[1]) if hits else ("none", 9.0)
        pcb = [q for n, q in parts.items() if ispcb(n)]
        row("split detent: pedestal grub reachable from behind the PCB (key line clear, mm)", dk, 0.1,
            f"Ø1.0 key line from z -13.4 (back cover and screens off) at r {D['sp_r']:g}, {D['sp_ang']:g}°; nearest: {nn}")
        if pcb:
            row("split detent: PCB key hole round the key line (mm)", min(key.distance_to(q) for q in pcb), 0.2,
                f"Ø{D['sp_access_d']:g} NPTH in the main PCB [Ed 15:50]")
        ring = [s for n, s in parts.items() if n.startswith("bottom internal ring")]
        if ring:
            row("split detent wall vs the knob's internal ring (mm)", min(mt.distance_to(q) for q in ring), T["arm_vs_cradle"],
                "the ring turns with the knob")
    else:
        br = arc_bridge(model.view(D, "base_drive"))
        bd = min(ARM[th].distance_to(br) for th in TR)
        row("arc detent bridge (columns, links, boss) vs the arm across ±travel (mm)", bd, T["arm_vs_cradle"],
            f"links from z {D['ad_z_link']:.2f} over the land / rib top {D['ad_z_land']:.2f}; columns r " +
            ", ".join(f"{math.hypot(x, y):.2f}" for x, y in D["ad_col_xy"]))


def ring_field(D):
    """Field of the diametric ring (dipole sum, Br from hv_br) at the dial TMAG5273 element, over a full knob turn."""
    import numpy as np
    ri, ro, th = D["tm_ring"]; Br = D["hv_br"]; M = Br / (4e-7 * np.pi)
    rr = np.linspace(ri / 2, ro / 2, 9)[:-1] + (ro - ri) / 32; ph = np.linspace(0, 2 * np.pi, 240, endpoint=False); zz = np.linspace(-th, 0, 5)[:-1] + th / 8
    R_, P_, Z_ = np.meshgrid(rr, ph, zz, indexing="ij"); dV = (ro - ri) / 2 / 8 * (2 * np.pi / 240) * R_ * th / 4 * 1e-9
    X, Y = R_ * np.cos(P_), R_ * np.sin(P_)
    sx, sy = D["tm_xy"]
    def field(gap):
        out = []
        for a in np.linspace(0, 2 * np.pi, 72, endpoint=False):
            mx, my = np.cos(a) * M * dV, np.sin(a) * M * dV
            rx, ry, rz = (sx - X) * 1e-3, (sy - Y) * 1e-3, (gap - Z_) * 1e-3
            r2 = rx * rx + ry * ry + rz * rz; r5 = r2 ** 2.5; md = mx * rx + my * ry
            b = 1e-7 * np.array([np.sum((3 * md * rx - mx * r2) / r5), np.sum((3 * md * ry - my * r2) / r5), np.sum(3 * md * rz / r5)]) * 1e3
            out.append(b)
        return np.array(out)
    b = field(D["tm_gap"]); bl = field(D["tm_gap_min"])
    nb = np.linalg.norm(b, axis=1); bxy = np.linalg.norm(b[:, :2], axis=1)
    return dict(peak=float(nb.max()), peak_lift=float(np.linalg.norm(bl, axis=1).max()), bxy_min=float(bxy.min()), bxy_max=float(bxy.max()))

def _bb(s):
    b = s.bounding_box(); return (b.min.X, b.min.Y, b.min.Z, b.max.X, b.max.Y, b.max.Z)
def _ov(A, B, t=1e-6): return all(A[i] < B[i + 3] - t and B[i] < A[i + 3] - t for i in range(3))

def _work(job):
    from ..common.cache import load
    pair, pa, pb = job
    try:
        s = load(pa).intersect(load(pb)); v = 0.0 if s is None else sum(c.volume for c in (s if isinstance(s, (list, ShapeList)) else [s]))
    except Exception:
        v = -1.0
    return pair, v

def clashes(parts, keys, thr=1e-3, procs=8):
    from .build import PATHS
    from ..common.cache import pool
    os.makedirs(CACHE, exist_ok=True); cp = os.path.join(CACHE, "clash.json")
    memo = json.load(open(cp)) if os.path.exists(cp) else {}
    bbs = {n: _bb(s) for n, s in parts.items()}
    todo, res, cand = [], {}, 0
    for a, b in itertools.combinations(parts, 2):
        if not _ov(bbs[a], bbs[b]): continue
        cand += 1
        k = hashlib.sha1((keys[a] + "|" + keys[b]).encode()).hexdigest()[:20]
        if k in memo: res[(a, b)] = memo[k]
        else: todo.append(((a, b), k))
    t = time.time()
    if todo:
        for (pair, v) in pool(procs).imap_unordered(_work, [(p, PATHS[p[0]], PATHS[p[1]]) for p, _ in todo]):
            res[pair] = v
        for pair, k in todo: memo[k] = res[pair]
        json.dump(memo, open(cp, "w"))
    out = {f"{a} / {b}": v for (a, b), v in res.items() if v > thr or v < 0}
    return out, cand, len(todo), time.time() - t
