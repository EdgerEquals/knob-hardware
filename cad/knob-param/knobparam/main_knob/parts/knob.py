"""Big knob: borosilicate sleeve, printed caps glued on the bore, hub gear, 45 deg race, bottom ring."""
import math
from build123d import *
from ...common import util
from ...common.util import A, rev, cyl, ext_gear, int_herringbone_half, ext_phase
SRC_DEPS = [util]

def profile(D):
    """Upper cap only. The see-through wall is the glass sleeve; this cap plugs the top of the bore."""
    o = D["knob_run"] * math.sqrt(2)
    rh, rD, rb = D["d_hg_root"] / 2, D["kb_rt"] - 0.06, D["r_bore_hi"]
    sp, spi = D["sleeve_spigot_r"], D["sleeve_lip_r"]
    z_ins = D["h_band1"] - D["sleeve_insert"]
    rh_d, g, rw, f, run = D["dial_hub_od"] / 2, D["gusset"], D["r_web"], D["lip_fillet"], D["knob_run"]
    zg = D["z_web0"] - g
    z_b = zg + (rb - rh_d) - o
    r_w = rh_d + g + o + (D["z_under_web"] - D["z_web0"])
    r_s = rw + run
    zl = D["z_lip0"] - f
    z_l = zl - o + (r_s - rw)
    r_l = rw + f + o - (D["z_lip0"] - D["z_knob_top"])
    z0, zt = D["knob_hub_z0"], D["knob_hub_top"]
    if D["glass_to_dial"] and D["kb_race"] == "chamfer" and D["cap_top"] == "chamfer":
        # v0.19b [Ed 2 Nov, later]: the glass runs right up under the dial. Its top inner edge is ground to a 45° chamfer and the cap's
        # cone seats on it, so the cap cannot go down past it; the cap top is flush with the glass top face.
        rk = D["r_knob_bore"]; z1 = D["sleeve_z1"]
        return [(rk, z0), (rh, z0), (rh, D["h_band1"]),
                (D["cap_r_s"], D["cap_z_rim_bot"]), (sp, D["cap_z_plug0"]),           # web underside, flare underside
                (sp, D["cap_seat_z_foot"]), (D["cap_seat_r_top"], z1),               # plug OD in the bore, cone on the inner chamfer
                (spi, z1), (spi, D["cap_z_flare_top"]),                              # cap top, plug ID
                (D["cap_r_s"], D["z_under_web"]), (r_w, D["z_under_web"]),           # flare top, web top under the dial
                (D["r_chamfer0"], zt), (rk, zt)]
    if D["glass_to_dial"] and D["kb_race"] == "chamfer":
        # v0.19b [Ed 2 Nov]: the glass runs up under the dial. The cap is a thin dished web: flat top under the dial web,
        # bottom tapering from the hub-gear top to cap_web_rim at the dial cup wall, a flare of the same wall out to the
        # plug foot, the plug glued in the bore, and a shoulder of the glass OD bonded on the glass top face.
        rk, ro = D["r_knob_bore"], D["knob_od"] / 2
        return [(rk, z0), (rh, z0), (rh, D["h_band1"]),
                (D["cap_r_s"], D["cap_z_rim_bot"]), (sp, D["cap_z_plug0"]),        # web underside, then the flare underside
                (sp, D["cap_sh_z0"]), (ro, D["cap_sh_z0"]), (ro, D["cap_sh_z1"]),  # plug OD in the bore, shoulder on the glass
                (spi, D["cap_sh_z1"]), (spi, D["cap_z_flare_top"]),                 # shoulder top, plug ID
                (D["cap_r_s"], D["z_under_web"]), (r_w, D["z_under_web"]),          # flare top, web top under the dial
                (D["r_chamfer0"], zt), (rk, zt)]
    # The plug stops on the bore. Nothing printed lies on the glass top face, so the rim stays open into the dial.
    plug = [(rh, D["h_band1"]), (spi, D["h_band1"]), (spi, z_ins), (sp, z_ins), (sp, D["h_band1"])]
    lip = [(min(r, sp), z) for r, z in ((r_l, D["z_knob_top"]), (r_s, z_l), (r_s, D["z_under_web"]), (r_w, D["z_under_web"]))]
    if D["kb_race"] == "chamfer":   # v0.15c: plain bore up to the 45° top chamfer (the ball track face)
        rk = D["r_knob_bore"]   # v0.15d: hub filled in to the dial tube; flat top 0.3 under the dial hub, then the 45° chamfer
        return [(rk, z0), (rh, z0)] + plug + lip + [(D["r_chamfer0"], zt), (rk, zt)]
    return [(rD, z0), (rh, z0)] + plug + lip + [(rb, z_b), (rb, zt), (rD, zt)]

def glass_sleeve(D):
    """Bought borosilicate 3.3 tube. Ends chamfered for the fire polish. Caps locate on the bore, not on this OD."""
    ro, ri, ch = D["knob_od"] / 2, D["sleeve_id"] / 2, D["sleeve_chamfer"]
    z0, z1 = D["sleeve_z0"], D["sleeve_z1"]
    if D["glass_to_dial"] and D["cap_top"] == "chamfer":   # v0.19b: ground top chamfers, inner (cap seat) and outer
        ci, co = D["sleeve_top_cin"], D["sleeve_top_cout"]
        return rev([(ri + ch, z0), (ro - ch, z0), (ro, z0 + ch), (ro, z1 - co),
                    (ro - co, z1), (ri + ci, z1), (ri, z1 - ci), (ri, z0 + ch)])
    return rev([(ri + ch, z0), (ro - ch, z0), (ro, z0 + ch), (ro, z1 - ch),
                (ro - ch, z1), (ri + ch, z1), (ri, z1 - ch), (ri, z0 + ch)])

def seal_ring(D):
    """v0.19b [Ed 2 Nov]: labyrinth seal. Bonded on the glass OD, flange over the faceplate ring (case lab_ring_*), skirt down
    outside it to the case's shoulder line (lab_shoulder_*). Turns with the knob; running gaps are the case's lab_gap."""
    if not D.get("seal_ring") or "lab_ring_r" not in D:
        return None
    rb = D["knob_od"] / 2 + D["seal_glue"]
    z0 = D["lab_ring_z1"] + D["lab_gap"]; z1 = z0 + D["seal_top_t"]
    rs0 = D["lab_shoulder_r"]; rs1 = rs0 + D["seal_wall"]; zs = D["lab_shoulder_z0"]
    c = min(0.4, D["seal_top_t"] / 2)
    return rev([(rb, z0), (rs0, z0), (rs0, zs), (rs1, zs), (rs1, z1 - c), (rs1 - c, z1), (rb, z1)])

def race_cut(D):
    z0, zt = D["knob_hub_z0"], D["knob_hub_top"]
    return rev([(0, z0 - 0.5), (D["kb_r_lo"], z0 - 0.5), (D["kb_r_lo"], D["kb_zk0"]), (D["kb_r_up"], D["kb_zk1"]),
                (D["kb_r_up"], zt + 0.5), (0, zt + 0.5)])

def build(D):
    zh, fh = D["knob_hub_z0"], D["hub_gear_face"]
    teeth = Rot(0, 0, ext_phase(D["z_hub_gear"], D["z_pinion"])) * ext_gear(
        D, D["z_hub_gear"], zh, fh, module=D["hub_mod"], dthick=-D["brass_backlash"] / 2,
        addendum=D["spur_addendum"], dedendum=D["spur_dedendum"])
    teeth -= cyl(D["d_hg_root"] / 2 - 0.02, zh, fh)
    body = rev(profile(D)) + teeth
    if D["kb_race"] == "chamfer":   # ball track groove in the chamfer (torus, R kb_seat_r, centre on the 45° line)
        cr, cz = D["kb_seat_c_knob"]; body -= Pos(0, 0, cz) * Torus(cr, D["kb_seat_r"])
    else:
        body -= race_cut(D)
    # v0.16 [Ed]: diametric ring magnet in the knob under-web face (top flush), read by the TMAG5273 in the dial above
    # v0.16b [Ed]: removed (rel_sensor False) - duplicate of the encoder + Hall row
    ri_, ro_, th_ = D["tm_ring"]; zt_ = D["z_under_web"]
    if D["rel_sensor"]:
        body -= cyl(ro_ / 2 + D["tm_press"], zt_ - th_, th_ + 0.01) - cyl(ri_ / 2 - D["tm_press"], zt_ - th_ - 0.01, th_ + 0.03)
        ring_mag = cyl(ro_ / 2, zt_ - th_, th_) - cyl(ri_ / 2, zt_ - th_ - 0.01, th_ + 0.02)
    h0, h = D["h_skirt0"], D["bot_face"]
    mid, gap = D["hb_mid"], D["hb_gap"]
    def _half(z0, z1):
        return cyl(D["sleeve_nylon_r"], z0, z1 - z0) - int_herringbone_half(D, D["z_ring"], z0, z1, mid)
    seat = D["cap_seat_gap"]
    z_top = h0 + h - seat                         # the glass sits this far above the printed cap
    lower = _half(h0, mid - gap / 2)
    upper = _half(mid + gap / 2, z_top)
    groove = Pos(0, 0, D["ot_z"]) * Torus(D["ot_r"], D["ot_rg"])
    lower -= groove
    upper -= groove
    # Locating plug on the nylon, same radius as the upper cap. The clear land is the race and the light path.
    upper += cyl(D["sleeve_spigot_r"], z_top, D["sleeve_insert"] + seat) - cyl(D["sleeve_lip_r"], z_top - 0.02, D["sleeve_insert"] + seat + 0.04)
    land = cyl(D["cap_r"], h0, z_top - h0) - cyl(D["sleeve_land_ri"], h0 - 0.02, z_top - h0 + 0.04)
    land -= groove
    R = D["kb_ball_d"] / 2; n = D["kb_n"]
    balls = Compound(children=[Pos(D["kb_rc"] * math.cos(2 * math.pi * i / n), D["kb_rc"] * math.sin(2 * math.pi * i / n), D["kb_zc"]) * Sphere(R) for i in range(n)])
    seal = seal_ring(D)
    out = {"knob upper-cap": body,
           "knob glass sleeve": glass_sleeve(D),
           "bottom internal ring (lower half)": lower, "bottom internal ring (upper half)": upper,
           "knob lower-cap land": land,
           f"knob balls {n} x Ø{D['kb_ball_d']:g} (45° cones)": balls}
    if seal is not None: out["knob seal ring (PETG, bonded on the glass)"] = seal
    if D["rel_sensor"]: out[f"knob ring magnet Ø{ro_:g}/Ø{ri_:g}×{th_:g} diametric"] = ring_mag
    return out
