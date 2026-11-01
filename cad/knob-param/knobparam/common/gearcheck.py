"""Spur and transverse-plane mesh quality. ha and hf are addendum and dedendum in modules of the pitch module used
(the transverse module for a herringbone). HA and HF are the full-depth constants; the built gears pass their own
stub addendum from the params, so a change of tooth form reaches this check and the solid from the same number.

References: standard textbook relations (contact ratio, undercut)."""
import math

HA, HF = 1.0, 1.25          # full-depth addendum / dedendum, in modules. Use these instead of a literal 1 or 1.25


def tip_d(z, m, internal=False, ha=HA):
    return (z - 2 * ha) * m if internal else (z + 2 * ha) * m


def root_d(z, m, internal=False, hf=HF):
    return (z + 2 * hf) * m if internal else (z - 2 * hf) * m


def mesh(z1, z2, m, alpha_deg=20.0, cd=None, internal=False, backlash_tooth=0.0, ha=HA, hf=HF):
    """z1 is the external pinion. cd is the actual centre distance (default nominal). backlash_tooth is the total
    circular thinning of the pair. Returns contact ratio, operating pressure angle, interference and backlash."""
    a0 = math.radians(alpha_deg)
    r1, r2 = z1 * m / 2, z2 * m / 2
    rb1, rb2 = r1 * math.cos(a0), r2 * math.cos(a0)
    a_nom = (r2 - r1) if internal else (r1 + r2)
    a = a_nom if cd is None else cd
    aw = math.acos(max(-1.0, min(1.0, ((rb2 - rb1) if internal else (rb1 + rb2)) / a)))
    ra1 = tip_d(z1, m, ha=ha) / 2
    ra2 = tip_d(z2, m, internal, ha) / 2
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
    jt = backlash_tooth + 2 * (a - a_nom) * math.tan(a0) * (-1 if internal else 1)
    return dict(eps=eps, eps_eff=eps_eff, alpha_w=math.degrees(aw), intf_pinion=intf1, intf_wheel=intf2,
                undercut=z1 < z_min, z_min=z_min, x_min=x_min, backlash=jt, cd=a, cd_nom=a_nom, ha=ha, hf=hf)


def rows(D, row):
    """Contact ratio, non-conjugate path and backlash band for the meshes this stack actually cuts.
    The herringbone is scored in the transverse plane (module mt, transverse pressure angle). Stub addendum
    comes from the params, not from HA."""
    b = math.radians(D["hb_beta"])
    mt, mn = D["hb_mt"], D["hb_mn"]
    at = math.degrees(math.atan(math.tan(math.radians(D["hb_pressure"])) / math.cos(b)))
    ha_h, hf_h = D["hb_addendum"] * mn / mt, D["hb_dedendum"] * mn / mt
    pairs = [
        ("1220 pinion / hub gear", D["z_pinion"], D["z_hub_gear"], D["hub_mod"], D["hub_cd"], False,
         D["brass_backlash"], D["spur_addendum"], D["spur_dedendum"], D["pressure"]),
        ("idler pinion / internal ring", D["z_enc_pinion"], D["z_ring"], mt, D["enc_cd"], True,
         D["hb_backlash"], ha_h, hf_h, at),
        ("encoder pinion / internal ring", D["z_enc_pinion"], D["z_ring"], mt, D["enc_cd"], True,
         D["hb_backlash"], ha_h, hf_h, at),
        ("feel pinion / compound gear", D["fg_z_pin"], D["fg_z_gear"], D["fg_mod"], D["fg_cd"], False,
         D["brass_backlash"], D["spur_addendum"], D["spur_dedendum"], D["pressure"]),
    ]
    for name, z1, z2, mm, cd, internal, bl, ha, hf, alpha in pairs:
        g = mesh(z1, z2, mm, alpha, cd, internal, bl, ha, hf)
        im = g["intf_pinion"] if g["intf_wheel"] is None else min(g["intf_pinion"], g["intf_wheel"])
        row(f"{name}: effective contact ratio", g["eps_eff"], 1.2,
            f"{z1}/{z2}T m{mm:.3f}, ha {ha:.3f}, alpha_w {g['alpha_w']:.2f}°, geometric {g['eps']:.2f}; "
            f"non-conjugate {max(0, -im):.2f} mm"
            + (f"; pinion under the {g['z_min']:.1f}T undercut limit" if g["undercut"] else ""))
        row(f"{name}: circular backlash (mm)", g["backlash"], 0.05,
            f"cd {g['cd']:.3f} vs nominal {g['cd_nom']:.3f}")
        row(f"{name}: circular backlash, upper (mm)", g["backlash"], 0.25, higher_ok=False)
