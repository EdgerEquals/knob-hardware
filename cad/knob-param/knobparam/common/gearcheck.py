"""Spur and transverse-plane mesh quality. ha and hf are addendum and dedendum in modules of the pitch module used
(the transverse module for a herringbone). HA and HF are the full-depth constants; the built gears pass their own
stub addendum from the params, so a change of tooth form reaches this check and the solid from the same number.

References: standard textbook relations (contact ratio, undercut).
v0.25: profile shift on external pairs (x1, x2), and a Lewis-type root-stress allowable for the printed meshes (`strength`)."""
import math

HA, HF = 1.0, 1.25          # full-depth addendum / dedendum, in modules. Use these instead of a literal 1 or 1.25


def inv(a):
    return math.tan(a) - a


def inv_solve(v):
    """Angle (rad) whose involute is v (Newton)."""
    a = max(1e-3, (3 * v) ** (1 / 3))
    for _ in range(40):
        a -= (inv(a) - v) / math.tan(a) ** 2
    return a


def shift_cd(z1, z2, m, alpha_deg, x_sum):
    """Working centre distance of an external pair cut with a total profile shift x_sum (modules)."""
    al = math.radians(alpha_deg)
    aw = inv_solve(inv(al) + 2 * math.tan(al) * x_sum / (z1 + z2))
    return (z1 + z2) * m / 2 * math.cos(al) / math.cos(aw)


def shift_sum(z1, z2, m, alpha_deg, cd):
    """Total profile shift (modules) that puts an external pair's working centre distance at cd."""
    al = math.radians(alpha_deg)
    aw = math.acos((z1 + z2) * m / 2 * math.cos(al) / cd)
    return (inv(aw) - inv(al)) * (z1 + z2) / (2 * math.tan(al))


def tip_d(z, m, internal=False, ha=HA):
    return (z - 2 * ha) * m if internal else (z + 2 * ha) * m


def root_d(z, m, internal=False, hf=HF):
    return (z + 2 * hf) * m if internal else (z - 2 * hf) * m


def mesh(z1, z2, m, alpha_deg=20.0, cd=None, internal=False, backlash_tooth=0.0, ha=HA, hf=HF, x1=0.0, x2=0.0):
    """z1 is the external pinion. cd is the actual centre distance (default: the one the pair is cut for). backlash_tooth is
    the total circular thinning of the pair. x1, x2: profile shifts (modules, external pairs; v0.25). The backlash is
    measured from the centre distance the shifts are cut for. Returns contact ratio, operating pressure angle,
    interference and backlash."""
    a0 = math.radians(alpha_deg)
    r1, r2 = z1 * m / 2, z2 * m / 2
    rb1, rb2 = r1 * math.cos(a0), r2 * math.cos(a0)
    if internal or not (x1 or x2):
        a_nom = (r2 - r1) if internal else (r1 + r2)
        aw_nom = a0
    else:
        a_nom = shift_cd(z1, z2, m, alpha_deg, x1 + x2)
        aw_nom = math.acos((rb1 + rb2) / a_nom)
    a = a_nom if cd is None else cd
    aw = math.acos(max(-1.0, min(1.0, ((rb2 - rb1) if internal else (rb1 + rb2)) / a)))
    ra1 = tip_d(z1, m, ha=ha) / 2 + x1 * m
    ra2 = tip_d(z2, m, internal, ha) / 2 + (0.0 if internal else x2 * m)
    pb = math.pi * m * math.cos(a0)
    s1 = math.sqrt(max(ra1 ** 2 - rb1 ** 2, 0))
    s2 = math.sqrt(max(ra2 ** 2 - rb2 ** 2, 0))
    L = a * math.sin(aw)
    eps = ((s1 - s2 + L) if internal else (s1 + s2 - L)) / pb
    intf1 = (s2 - L) if internal else (L - s2)
    intf2 = None if internal else (L - s1)
    z_min = 2 * ha / math.sin(a0) ** 2
    x_min = max(0.0, ha - z1 * math.sin(a0) ** 2 / 2)
    eps_eff = eps - max(0.0, -intf1) / pb - (max(0.0, -intf2) / pb if intf2 is not None else 0.0)
    jt = backlash_tooth + 2 * (a - a_nom) * math.tan(aw_nom) * (-1 if internal else 1)
    return dict(eps=eps, eps_eff=eps_eff, alpha_w=math.degrees(aw), intf_pinion=intf1, intf_wheel=intf2,
                undercut=z1 < z_min - 2 * x1 / math.sin(a0) ** 2, z_min=z_min, x_min=x_min, backlash=jt, cd=a, cd_nom=a_nom,
                ha=ha, hf=hf, x1=x1, x2=x2)


# ---- v0.25 strength: Lewis-type root stress, calibrated to the textbook Lewis Y [coordinator's method, 3 Nov 19:10] ----
# stress = CAL * 6 F h / (b s_b^2): s_b = tooth thickness at the base circle, h = tip to root (the lower of the root and
# 0.98 of the base circle). CAL makes the v0.24 1220 pinion (14T m0.6, stub 0.8, dedendum 1.25, 0.10 backlash, face 3.0)
# read sigma = F / (b m Y) with Y(14T, 20° full depth) = 0.277 [S Shigley table 14-2]. Printed gears are drawn, not
# generated: no cutter undercut.
LEWIS_REF = dict(z=14, m=0.6, b=3.0, Y=0.277, ha=0.8, hf=1.25, backlash=0.10)


def _member(z, m, x, alpha_deg, ha, hf, backlash):
    al = math.radians(alpha_deg)
    r, rb = z * m / 2, z * m * math.cos(al) / 2
    s = m * (math.pi / 2 + 2 * x * math.tan(al)) - backlash / 2      # pitch thickness less this member's half of the backlash
    ra, rf = r + (ha + x) * m, r - (hf - x) * m
    s_b = 2 * rb * (s / (2 * r) + inv(al))
    h = ra - max(rf, rb * 0.98)
    return dict(r=r, rb=rb, ra=ra, rf=rf, s_b=s_b, h=h)


def _k(mb, b):
    return 6 * mb["h"] / (b * mb["s_b"] ** 2)


def lewis_cal(alpha_deg=20.0):
    R = LEWIS_REF
    ref = _member(R["z"], R["m"], 0.0, alpha_deg, R["ha"], R["hf"], R["backlash"])
    return (1 / (R["b"] * R["m"] * R["Y"])) / _k(ref, R["b"])


def root_stress_per_N(z, m, x, b, alpha_deg=20.0, ha=0.8, hf=1.25, backlash=0.10):
    """MPa of root stress per newton of tangential load (Lewis-type, calibrated)."""
    return lewis_cal(alpha_deg) * _k(_member(z, m, x, alpha_deg, ha, hf, backlash), b)


def strength(D):
    """Allowable torques of the printed meshes [mNm]. MJF PA-12: static D['pa12_uts'] at SF D['sf_static'], fatigue
    D['pa12_fat'] x D['fat_two_way'] (two-way loading) at SF D['sf_fatigue']. Hub: the weaker member at the working
    pitch radius of the 1220 pinion (the gearbox output), times the ratio at the knob. Ring stage: one 12T pinion
    (the internal ring's teeth are stronger), at the ring's pitch radius (the knob)."""
    pa, bl = D["pressure"], D["brass_backlash"]
    s_st = D["pa12_uts"] / D["sf_static"]
    s_fa = D["pa12_fat"] * D["fat_two_way"] / D["sf_fatigue"]
    zp, zg, m, b = D["z_pinion"], D["z_hub_gear"], D["hub_mod"], D["hub_face"]
    kp = root_stress_per_N(zp, m, D["hub_x_pin"], b, pa, D["spur_addendum"], D["spur_dedendum"], bl)
    kg = root_stress_per_N(zg, m, D["hub_x_gear"], b, pa, D["spur_addendum"], D["spur_dedendum"], bl)
    k = max(kp, kg)
    rw = D["hub_cd"] * zp / (zp + zg)
    ratio = zg / zp
    out = dict(hub_weak="pinion" if kp >= kg else "hub gear", hub_k=k, hub_rw=rw,
               hub_T_static_out=s_st / k * rw, hub_T_fat_out=s_fa / k * rw, hub_T_break_out=D["pa12_uts"] / k * rw)
    for key in ("static", "fat", "break"):
        out[f"hub_T_{key}_knob"] = out[f"hub_T_{key}_out"] * ratio
    # v0.24 mesh by the same method (m0.6 14/22, face 3.0, no shift): the regression reference
    k24 = max(root_stress_per_N(14, 0.6, 0.0, 3.0, pa, 0.8, 1.25, bl), root_stress_per_N(22, 0.6, 0.0, 3.0, pa, 0.8, 1.25, bl))
    out["hub_v024_fat_knob"] = s_fa / k24 * 10.80 * 14 / 36 * 22 / 14
    out["hub_v024_static_knob"] = s_st / k24 * 10.80 * 14 / 36 * 22 / 14
    # ring stage: one ring pinion carries the knob torque at the ring pitch radius
    kr = root_stress_per_N(D["z_enc_pinion"], D["hb_mn"], 0.0, D["pin_face"], D["hb_pressure"], D["hb_addendum"],
                           D["hb_dedendum"], D["hb_backlash"])
    Rr = D["z_ring"] * D["hb_mt"] / 2
    out.update(ring_k=kr, ring_R=Rr, ring_T_static_knob=s_st / kr * Rr, ring_T_fat_knob=s_fa / kr * Rr)
    return out


def strength_rows(D, row):
    """v0.25 [Ed 19:10]: allowable torques of the hub mesh and the ring stage (Lewis, MJF PA-12)."""
    S = strength(D)
    mat = (f"MJF PA-12 {D['pa12_uts']:g} MPa static [S], fatigue {D['pa12_fat']:g} MPa x {D['fat_two_way']:.2f} two-way [S]; "
           f"SF {D['sf_static']:g} static / {D['sf_fatigue']:g} fatigue; Lewis Y calibrated [S]")
    row("hub mesh: static allowable at the 1220 output, SF 2 (mNm) vs the driver current limit", S["hub_T_static_out"],
        D["hub_i_limit"],
        f"m{D['hub_mod']:g} {D['z_pinion']}/{D['z_hub_gear']} x {D['hub_x_pin']:+.2f}/{D['hub_x_gear']:+.3f} face {D['hub_face']:g}, "
        f"weak member {S['hub_weak']}; at the knob {S['hub_T_static_knob']:.0f} (break {S['hub_T_break_knob']:.0f}); "
        f"limit {D['hub_i_limit']:g} mNm at the gearbox output [A]; " + mat)
    row("hub mesh: fatigue allowable at the knob, SF 1.5 (mNm), not below v0.24", S["hub_T_fat_knob"], S["hub_v024_fat_knob"],
        f"at the 1220 output {S['hub_T_fat_out']:.1f}; v0.24 m0.6 14/22 x 3.0 by the same method {S['hub_v024_fat_knob']:.0f} "
        f"(static {S['hub_v024_static_knob']:.0f})")
    row("ring stage: fatigue allowable at the knob through one pinion, SF 1.5 (mNm) vs the feel burst", S["ring_T_fat_knob"],
        D["feel_burst_knob"],
        f"{D['z_enc_pinion']}T m{D['hb_mn']:g} face {D['pin_face']:g} into {D['z_ring']}T; feel burst {D['feel_burst_knob']:g} mNm at the "
        f"knob [A, 2 Nov ballpark]; static SF 2 {S['ring_T_static_knob']:.0f}")
    jam = D["hub_i_limit"] * D["z_hub_gear"] / D["z_pinion"]
    row("ring stage: static allowable at the knob, SF 2 (mNm) vs the 1220 at its limit (feel train jammed)",
        S["ring_T_static_knob"], jam,
        f"a jam in the feel train puts the 1220's {D['hub_i_limit']:g} mNm x {D['z_hub_gear'] / D['z_pinion']:.3f} = {jam:.0f} mNm "
        f"through idler 1; ring pitch r {S['ring_R']:.2f}")



def rows(D, row):
    """Contact ratio, non-conjugate path and backlash band for the meshes this stack actually cuts.
    A helical ring stage is scored in the transverse plane (module mt, transverse pressure angle); v0.25 it is spur
    (hb_beta 0, mt = mn). Stub addendum comes from the params, not from HA. v0.25: the hub mesh carries profile shift and
    is scored where the 1220 really is (the KiCad axis, `offset`), not at the centre distance it is cut for (hub_cd)."""
    b = math.radians(D["hb_beta"])
    mt, mn = D["hb_mt"], D["hb_mn"]
    at = math.degrees(math.atan(math.tan(math.radians(D["hb_pressure"])) / math.cos(b)))
    ha_h, hf_h = D["hb_addendum"] * mn / mt, D["hb_dedendum"] * mn / mt
    pairs = [
        ("1220 pinion / hub gear", D["z_pinion"], D["z_hub_gear"], D["hub_mod"], D["offset"], False,
         D["brass_backlash"], D["spur_addendum"], D["spur_dedendum"], D["pressure"], D["hub_x_pin"], D["hub_x_gear"]),
        ("idler pinion / internal ring", D["z_enc_pinion"], D["z_ring"], mt, D["enc_cd"], True,
         D["hb_backlash"], ha_h, hf_h, at, 0.0, 0.0),
        ("encoder pinion / internal ring", D["z_enc_pinion"], D["z_ring"], mt, D["enc_cd"], True,
         D["hb_backlash"], ha_h, hf_h, at, 0.0, 0.0),
        ("feel pinion / compound gear", D["fg_z_pin"], D["fg_z_gear"], D["fg_mod"], D["fg_cd"], False,
         D["brass_backlash"], D["spur_addendum"], D["spur_dedendum"], D["pressure"], 0.0, 0.0),
    ]
    for name, z1, z2, mm, cd, internal, bl, ha, hf, alpha, x1, x2 in pairs:
        g = mesh(z1, z2, mm, alpha, cd, internal, bl, ha, hf, x1, x2)
        im = g["intf_pinion"] if g["intf_wheel"] is None else min(g["intf_pinion"], g["intf_wheel"])
        row(f"{name}: effective contact ratio", g["eps_eff"], 1.2,
            f"{z1}/{z2}T m{mm:.3f}, ha {ha:.3f}, alpha_w {g['alpha_w']:.2f}°, geometric {g['eps']:.2f}; "
            f"non-conjugate {max(0, -im):.2f} mm"
            + (f"; pinion under the {g['z_min']:.1f}T undercut limit" if g["undercut"] else ""))
        row(f"{name}: circular backlash (mm)", g["backlash"], 0.05,
            f"cd {g['cd']:.3f} vs nominal {g['cd_nom']:.3f}" + (f" (cut for; shift x {x1:+.2f}/{x2:+.3f})" if (x1 or x2) else ""))
        row(f"{name}: circular backlash, upper (mm)", g["backlash"], 0.25, higher_ok=False)
