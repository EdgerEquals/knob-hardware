"""Shared geometry helpers (no sub-assembly internals). Involute outline vendored from cad/knob/knob-v0.1/knob_gears.py
(gear_pts / gear_solid, identical maths) so the package has no path dependency on the rest of the repo."""
import math, os
from build123d import *
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
def ext_gear(D, z, z0, h):   # external spur gear (pinion / wheel)
    m = D["module"]; return gear_solid(gear_pts(z, m, m, 1.25 * m, -D["backlash"] / 2, D["pressure"]), z0, h)
def int_cutter(D, z, z0, h):  # tooth-space cutter for an internal ring
    m = D["module"]; return gear_solid(gear_pts(z, m, 1.25 * m, 1.0 * m, +D["backlash"] / 2, D["pressure"]), z0, h)
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
    return ((a - 270.0) * (1.0 - zr / zp) + off * t) % t
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
def thrust_groove(pcd, groove_r, z_ball):
    """Torus groove for a ring of thrust balls (cut into BOTH the cradle plate and the dial tube end; numbers are the
    control_dial exports tb_pcd / tb_groove_r / tb_z_ball)."""
    return Pos(0, 0, z_ball) * Torus(pcd / 2, groove_r)


class overlay(dict):
    """Tracked view of D with a few keys replaced: ext_gear(overlay(D, module=m), ...) instead of Dm = dict(D); Dm[...] = m."""
    def __init__(self, base, **kw): super().__init__(kw); self.base = base
    def __getitem__(self, k): return super().__getitem__(k) if super().__contains__(k) else self.base[k]
    def get(self, k, default=None): return super().__getitem__(k) if super().__contains__(k) else self.base.get(k, default)
    def __contains__(self, k): return super().__contains__(k) or k in self.base
