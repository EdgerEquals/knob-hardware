"""Big knob: cap + skirt + hub with the external hub gear and the knob half of the 45 deg race (v0.15c: track in the top chamfer); bottom internal ring; balls."""
import math
from build123d import *
from ...common.util import A, rev, cyl, ext_gear, int_cutter, ext_phase

def profile(D):
    o = D["knob_run"] * math.sqrt(2)
    rh, rD, rb, ri, ro = D["d_hg_root"] / 2, D["kb_rt"] - 0.06, D["r_bore_hi"], D["skirt_id"] / 2, D["knob_od"] / 2
    rh_d, g, rw, f, run = D["dial_hub_od"] / 2, D["gusset"], D["r_web"], D["lip_fillet"], D["knob_run"]
    zg = D["z_web0"] - g
    z_b = zg + (rb - rh_d) - o
    r_w = rh_d + g + o + (D["z_under_web"] - D["z_web0"])
    r_s = rw + run
    zl = D["z_lip0"] - f
    z_l = zl - o + (r_s - rw)
    r_l = rw + f + o - (D["z_lip0"] - D["z_knob_top"])
    z0, zt = D["knob_hub_z0"], D["knob_hub_top"]
    if D["kb_race"] == "chamfer":   # v0.15c: plain bore up to the 45° top chamfer (the ball track face)
        rk = D["r_knob_bore"]   # v0.15d: hub filled in to the dial tube; flat top 0.3 under the dial hub, then the 45° chamfer
        return [(rk, z0), (rh, z0), (rh, D["h_band1"]), (ri, D["h_band1"]), (ri, D["h_bi1"]), (ro, D["h_bi1"]),
                (ro, D["z_knob_top"]), (r_l, D["z_knob_top"]), (r_s, z_l), (r_s, D["z_under_web"]),
                (r_w, D["z_under_web"]), (D["r_chamfer0"], zt), (rk, zt)]
    return [(rD, z0), (rh, z0), (rh, D["h_band1"]), (ri, D["h_band1"]), (ri, D["h_bi1"]), (ro, D["h_bi1"]),
            (ro, D["z_knob_top"]), (r_l, D["z_knob_top"]), (r_s, z_l), (r_s, D["z_under_web"]),
            (r_w, D["z_under_web"]), (rb, z_b), (rb, zt), (rD, zt)]

def race_cut(D):
    z0, zt = D["knob_hub_z0"], D["knob_hub_top"]
    return rev([(0, z0 - 0.5), (D["kb_r_lo"], z0 - 0.5), (D["kb_r_lo"], D["kb_zk0"]), (D["kb_r_up"], D["kb_zk1"]),
                (D["kb_r_up"], zt + 0.5), (0, zt + 0.5)])

def build(D):
    zh, fh = D["knob_hub_z0"], D["hub_gear_face"]
    teeth = Rot(0, 0, ext_phase(D["z_hub_gear"], D["z_pinion"])) * ext_gear(D, D["z_hub_gear"], zh, fh)
    teeth -= cyl(D["d_hg_root"] / 2 - 0.02, zh, fh)
    body = rev(profile(D)) + teeth
    if D["kb_race"] == "chamfer":   # ball track groove in the chamfer (torus, R kb_seat_r, centre on the 45° line)
        cr, cz = D["kb_seat_c_knob"]; body -= Pos(0, 0, cz) * Torus(cr, D["kb_seat_r"])
    else:
        body -= race_cut(D)
    # v0.16 [Ed]: diametric ring magnet in the knob under-web face (top flush), read by the TMAG5273 in the dial above
    ri_, ro_, th_ = D["tm_ring"]; zt_ = D["z_under_web"]
    body -= cyl(ro_ / 2 + D["tm_press"], zt_ - th_, th_ + 0.01) - cyl(ri_ / 2 - D["tm_press"], zt_ - th_ - 0.01, th_ + 0.03)
    ring_mag = cyl(ro_ / 2, zt_ - th_, th_) - cyl(ri_ / 2, zt_ - th_ - 0.01, th_ + 0.02)
    h0, h = D["h_skirt0"], D["bot_face"]
    ring = cyl(D["knob_od"] / 2, h0, h) - int_cutter(D, D["z_ring"], h0, h)
    R = D["kb_ball_d"] / 2; n = D["kb_n"]
    balls = Compound(children=[Pos(D["kb_rc"] * math.cos(2 * math.pi * i / n), D["kb_rc"] * math.sin(2 * math.pi * i / n), D["kb_zc"]) * Sphere(R) for i in range(n)])
    return {"knob body (cap+skirt+hub gear)": body, "bottom internal ring": ring, f"knob ring magnet Ø{ro_:g}/Ø{ri_:g}×{th_:g} diametric": ring_mag, f"knob balls {n} x Ø{D['kb_ball_d']:g} (45° cones)": balls}
