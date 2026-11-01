"""knobparam/common/gearcheck.py — spur mesh quality for standard full-depth involute gears (ha = 1.0 m, hf = 1.25 m).
Pure maths, no OCC. Pinions are external; `internal=True` means gear 2 is an internal ring.
References: standard textbook relations (e.g. KHK "Gear Technical Reference", sections on contact ratio and undercut)."""
import math

HA, HF = 1.0, 1.25          # addendum / dedendum in modules. Use these everywhere instead of literal +2 / -2.5
def tip_d(z, m, internal=False):  return (z - 2 * HA) * m if internal else (z + 2 * HA) * m
def root_d(z, m, internal=False): return (z + 2 * HF) * m if internal else (z - 2 * HF) * m

def mesh(z1, z2, m, alpha_deg=20.0, cd=None, internal=False, backlash_tooth=0.0):
    """z1 = pinion (external). cd = actual centre distance (default nominal). backlash_tooth = total circular thinning
    built into the pair (ext_gear thins the pinion by backlash/2, int_cutter widens the ring space by backlash/2 -> backlash).
    Returns dict with contact ratio, operating pressure angle, interference margins and circular backlash."""
    a0 = math.radians(alpha_deg)
    r1, r2 = z1 * m / 2, z2 * m / 2
    rb1, rb2 = r1 * math.cos(a0), r2 * math.cos(a0)
    a_nom = (r2 - r1) if internal else (r1 + r2)
    a = a_nom if cd is None else cd
    aw = math.acos((rb2 - rb1) / a) if internal else math.acos((rb1 + rb2) / a)     # operating pressure angle
    ra1 = tip_d(z1, m) / 2
    ra2 = tip_d(z2, m, internal) / 2
    pb = math.pi * m * math.cos(a0)                                                  # base pitch
    s1 = math.sqrt(max(ra1**2 - rb1**2, 0))
    s2 = math.sqrt(max(ra2**2 - rb2**2, 0))
    L = a * math.sin(aw)                                                             # T1T2 (ext) or T2T1 (int)
    eps = ((s1 - s2 + L) if internal else (s1 + s2 - L)) / pb
    # involute interference: the mate's tip must not reach past the pinion's base-tangent point T1
    intf1 = (s2 - L) if internal else (L - s2)       # >= 0 OK (mm along the line of action)
    intf2 = None if internal else (L - s1)            # wheel side, external only
    z_min = 2 * HA / math.sin(a0) ** 2                # no-undercut tooth count if generated (17.1 at 20°)
    x_min = max(0.0, HA - z1 * math.sin(a0) ** 2 / 2) # profile shift that would avoid undercut on the pinion
    # effective contact ratio: contact before the pinion's T1 is non-conjugate (the model's flank below the base circle is
    # radial, so it clears rather than collides; verified by a rotation sweep at 14/75: >= 0.041 mm gap over a full pitch)
    eps_eff = eps - max(0.0, -intf1) / pb - (max(0.0, -intf2) / pb if intf2 is not None else 0.0)
    jt = backlash_tooth + 2 * (a - a_nom) * math.tan(a0) * (-1 if internal else 1)   # circular backlash at pitch circle
    return dict(eps=eps, eps_eff=eps_eff, alpha_w=math.degrees(aw), intf_pinion=intf1, intf_wheel=intf2, undercut=z1 < z_min,
                z_min=z_min, x_min=x_min, backlash=jt, cd=a, cd_nom=a_nom)

def rows(D, row):
    """Add gear-quality rows to a Rows object. Targets: eps >= 1.2 for printed/POM teeth (tips round over and
    lose ~0.1-0.15), interference margin >= 0, circular backlash between 0.05 and 0.25 mm at m0.5."""
    m, al, bl = D["module"], D["pressure"], D["backlash"]
    pairs = [("1220 pinion / hub gear", D["z_pinion"], D["z_hub_gear"], m, D["offset"], False),
             ("idler pinion / 75T ring", D["z_enc_pinion"], D["z_ring"], m, None, True),
             ("encoder pinion / 75T ring", D["z_enc_pinion"], D["z_ring"], m, D["enc_cd"], True),
             ("716 KHK pinion / compound gear", D["fg_z_pin"], D["fg_z_gear"], D["fg_mod"], D["fg_cd"], False)]
    for name, z1, z2, mm, cd, internal in pairs:
        g = mesh(z1, z2, mm, al, cd, internal, bl)
        im = g["intf_pinion"] if g["intf_wheel"] is None else min(g["intf_pinion"], g["intf_wheel"])
        row(f"{name}: effective contact ratio", g["eps_eff"], 1.2,
            f"{z1}/{z2}T m{mm:g}, alpha_w {g['alpha_w']:.2f}°, geometric {g['eps']:.2f}; non-conjugate {max(0, -im):.2f} mm of the path"
            + (f"; pinion under the {g['z_min']:.1f}T undercut limit (x_min {g['x_min']:.2f})" if g["undercut"] else ""))
        row(f"{name}: circular backlash (mm)", g["backlash"], 0.05, f"cd {g['cd']:.3f} vs nominal {g['cd_nom']:.3f}")
        row(f"{name}: circular backlash, upper (mm)", g["backlash"], 0.25, higher_ok=False)

if __name__ == "__main__":
    for args in [(19, 24, .5, 20, 10.75, False), (14, 75, .5, 20, 15.25, True), (15, 32, .5, 20, 11.7351, False)]:
        g = mesh(*args, backlash_tooth=0.1); print(args[:2], {k: round(v, 3) if isinstance(v, float) else v for k, v in g.items()})
