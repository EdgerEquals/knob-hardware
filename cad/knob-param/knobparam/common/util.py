"""Shared geometry helpers (no sub-assembly internals). Involute outline vendored from cad/knob/knob-v0.1/knob_gears.py
(gear_pts / gear_solid, identical maths) so the package has no path dependency on the rest of the repo."""
import math, os
from build123d import *
from .gearcheck import HA, HF
PKG = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # cad/knob-param
LIB = os.path.dirname(PKG)                                                            # cad/  (outputs -> cad/assemblies/)
A = (Align.CENTER, Align.CENTER, Align.MIN)

def _inv(a): return math.tan(a) - a
def gear_pts(z, m, add, ded, dthick, alpha_deg=20.0, n=7):
    """External involute outline: z teeth, addendum add, dedendum ded, tooth thickness change dthick (mm on pitch)."""
    a = math.radians(alpha_deg); rp = z * m / 2; rb = rp * math.cos(a); ra = rp + add; rf = rp - ded
    psi = (math.pi * m / 2 + dthick) / (2 * rp)   # half tooth angle on the pitch circle
    r0 = max(rb, rf)
    def th(r): return psi + _inv(a) - _inv(math.acos(min(1.0, rb / r)))
    rs = [r0 + (ra - r0) * i / (n - 1) for i in range(n)]
    pts = []
    for i in range(z):
        c = 2 * math.pi * i / z
        if rf < rb: pts.append((rf, c - th(rb)))
        pts += [(r, c - th(r)) for r in rs]
        pts += [(r, c + th(r)) for r in reversed(rs)]
        if rf < rb: pts.append((rf, c + th(rb)))
    return [(r * math.cos(t), r * math.sin(t)) for r, t in pts]
def gear_solid(pts, z0, h):
    f = Face(Wire.make_polygon([Vector(x, y, z0) for x, y in pts], close=True))
    return extrude(f, h)
def tooth_tip(z, mn, alpha_deg, backlash=0.0, addendum=HA, beta_deg=0.0, x=0.0):
    """Transverse tip thickness (mm). `mn` is the normal module (the spur module when beta is 0).
    `backlash` is removed from this tooth's pitch thickness only. v0.25: `x` is the profile shift (modules): the tip
    radius grows by x*mn and the pitch thickness by 2*x*mn*tan(alpha); `addendum` is the unshifted addendum."""
    b = math.radians(beta_deg); an = math.radians(alpha_deg)
    mt = mn / math.cos(b) if beta_deg else mn
    at = math.atan(math.tan(an) / math.cos(b)) if beta_deg else an
    rp = z * mt / 2; rb = rp * math.cos(at); ra = rp + (addendum + x) * mn
    if ra <= rb or rp <= 0: return 0.0
    aa = math.acos(min(0.999999, rb / ra))
    tp = math.pi * mt / 2 + 2 * x * mn * math.tan(an) - backlash
    return ra * (tp / rp + 2 * (_inv(at) - _inv(aa)))
def _transverse(z, mn, beta, alpha, add_k, ded_k, dthick):
    """Transverse involute outline. mn is the normal module; centre distance uses mt = mn/cos(beta) (= mn for a spur)."""
    b = math.radians(beta)
    mt = mn / math.cos(b)
    at = math.degrees(math.atan(math.tan(math.radians(alpha)) / math.cos(b))) if beta else alpha
    return gear_pts(z, mt, add_k * mn, ded_k * mn, dthick, at), mt
def _face_at(pts, z, phi):
    c, s = math.cos(phi), math.sin(phi)
    return Face(Wire.make_polygon([Vector(x * c - y * s, x * s + y * c, z) for x, y in pts], close=True))
def _helix(pts, z0, z1, pitch_r, beta_deg, mid, n=4):
    """One helical run. phi = |z - mid| * tan(beta) / pitch_r, so two runs joined at `mid` are a herringbone."""
    rate = math.tan(math.radians(beta_deg)) / pitch_r
    faces = [_face_at(pts, z0 + (z1 - z0) * i / n, abs((z0 + (z1 - z0) * i / n) - mid) * rate) for i in range(n + 1)]
    return loft(faces, ruled=True)
def int_cutter(D, z, z0, h):  # spur tooth-space cutter (kept for a straight ring; v0.18 uses int_herringbone_half)
    m = D["module"]; return gear_solid(gear_pts(z, m, HF * m, HA * m, +D["backlash"] / 2, D["pressure"]), z0, h)
def ext_gear(D, z, z0, h, module=None, pressure=None, dthick=None, addendum=HA, dedendum=HF):
    """External spur. dthick is the pitch-thickness change (negative thins the tooth)."""
    m = D["module"] if module is None else module
    pa = D["pressure"] if pressure is None else pressure
    if dthick is None: dthick = -D["backlash"] / 2
    return gear_solid(gear_pts(z, m, addendum * m, dedendum * m, dthick, pa), z0, h)
def ext_herringbone(D, z, z0, h, mid):
    """Printed external ring-stage pinion. Apex on the plane z = mid, shared with the split ring.
    v0.25 [Ed 3 Nov 19:00]: hb_beta 0 is the straight (spur) ring stage: a plain extrusion (the hb_ names are kept)."""
    mn, beta, pa = D["hb_mn"], D["hb_beta"], D["hb_pressure"]
    pts, mt = _transverse(z, mn, beta, pa, D["hb_addendum"], D["hb_dedendum"], -D["hb_backlash"] / 2)
    if not beta:
        return gear_solid(pts, z0, h)
    rp = z * mt / 2
    return _helix(pts, z0, mid, rp, beta, mid) + _helix(pts, mid, z0 + h, rp, beta, mid)
def int_herringbone_half(D, z, z0, z1, mid):
    """Tooth-space cutter for one axial half of the internal ring (same hand as the pinion half it meets).
    v0.25: with hb_beta 0 it is the straight cutter for the one-piece spur ring over z0..z1."""
    mn, beta, pa = D["hb_mn"], D["hb_beta"], D["hb_pressure"]
    pts, mt = _transverse(z, mn, beta, pa, D["hb_dedendum"], D["hb_addendum"], +D["hb_backlash"] / 2)
    if not beta:
        return gear_solid(pts, z0, z1 - z0)
    return _helix(pts, z0, z1, z * mt / 2, beta, mid)
def rev(pts):
    return revolve(Face(Wire.make_polygon([Vector(r, 0, z) for r, z in pts], close=True)), Axis.Z, 360)
def cyl(r, z0, h, x=0.0, y=0.0): return Pos(x, y, z0) * Cylinder(r, h, align=A)
def tube(ri, ro, z0, h, x=0.0, y=0.0): return Pos(x, y, z0) * (Cylinder(ro, h, align=A) - Cylinder(ri, h, align=A))
def sector(r0, r1, a_half, z0, h, a_mid, n=24):
    pts = [(r1 * math.cos(math.radians(a_mid - a_half + 2 * a_half * i / n)), r1 * math.sin(math.radians(a_mid - a_half + 2 * a_half * i / n))) for i in range(n + 1)]
    pts += [(r0 * math.cos(math.radians(a_mid + a_half - 2 * a_half * i / n)), r0 * math.sin(math.radians(a_mid + a_half - 2 * a_half * i / n))) for i in range(n + 1)]
    return Pos(0, 0, z0) * extrude(Face(Wire.make_polygon([Vector(x, y, 0) for x, y in pts], close=True)), h)
def ring_phase(D, a, zp=None):
    """Spin (deg) of a zp-tooth pinion at dial angle a so it meshes the fixed z_ring internal ring (v0.13 rule, any ring parity).
    zp defaults to the encoder / idler tooth count."""
    zp = D["z_enc_pinion"] if zp is None else zp
    zr = D["z_ring"]; t = 360.0 / zp
    off = 0.5 - ((zr * 270.0 / 360.0) % 1.0)
    ph = ((a - 270.0) * (1.0 - zr / zp) + off * t) % t
    # The v0.13 half-tooth term is centred for 14T. For a pinion whose tooth count is a multiple of 4
    # (the 12T herringbone) it lands half a tooth out, tooth-on-tooth. A section test puts the clearance
    # window one half-pitch away, so shift by that.
    if zp % 4 == 0:
        ph = (ph - t / 2.0) % t
    return ph
def ext_phase(z_gear, z_pinion):
    """Gear spin so a space faces the pinion on the +X line (gear_pts puts a tooth at 0 deg)."""
    return 180.0 / z_gear if z_pinion % 2 == 0 else 0.0
def ext_mesh_spin(z_gear, z_pin, alpha_deg, pin_spin=0.0):
    """World spin (deg) of an external gear so it meshes a pinion.

    gear_pts puts a tooth at local 0. `alpha_deg` is the world angle of the pinion from the gear centre.
    `pin_spin` is the world angle the pinion's tooth 0 points at. The two profiles are standard 20° full depth,
    so a half-pitch complement along the line of centres is a mesh."""
    pitch_p = 360.0 / z_pin
    pitch_g = 360.0 / z_gear
    face = (alpha_deg + 180.0 - pin_spin) % pitch_p   # 0 = pinion tooth toward the gear
    off = face / pitch_p
    return alpha_deg - pitch_g * ((0.5 - off) % 1.0)
def fresnel_cap(od, bore, z0, t=0.40, rings=3, step_h=0.16, step_w=0.42):
    """Light clear-resin cap: a disk plus stepped Fresnel rings on the outer face. The bore is the press/snap
    (modeled oversize so the fit is not a solid clash). Rings stop inside the rim."""
    s = cyl(od / 2, z0, t) - cyl(bore / 2, z0 - 0.05, t + step_h + 0.2)
    r = bore / 2 + 0.30
    for _ in range(rings):
        if r + step_w > od / 2 - 0.12:
            break
        s += cyl(r + step_w, z0 + t, step_h) - cyl(r, z0 + t - 0.02, step_h + 0.04)
        r += step_w + 0.08
    return s
def thrust_groove(pcd, groove_r, z_ball):
    """Torus groove for a ring of thrust balls (cut into BOTH the cradle plate and the dial tube end; numbers are the
    control_dial exports tb_pcd / tb_groove_r / tb_z_ball)."""
    return Pos(0, 0, z_ball) * Torus(pcd / 2, groove_r)


class overlay(dict):
    """Tracked view of D with a few keys replaced. ext_gear(overlay(D, module=m), ...) keeps backlash and pressure in the cache key."""
    def __init__(self, base, **kw): super().__init__(kw); self.base = base
    def __getitem__(self, k): return super().__getitem__(k) if super().__contains__(k) else self.base[k]
    def get(self, k, default=None): return super().__getitem__(k) if super().__contains__(k) else self.base.get(k, default)
    def __contains__(self, k): return super().__contains__(k) or k in self.base
