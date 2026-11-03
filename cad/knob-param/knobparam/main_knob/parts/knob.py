"""Big knob: borosilicate sleeve, printed caps glued on the bore, hub gear, 45 deg race, bottom ring.
v0.25 [Ed 3 Nov 19:00-19:10]: the upper cap is clear resin; the hub gear is a separate PA-12 ring glued into it; the bottom
internal ring is straight (spur) and one piece."""
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
    if D["cap_shape"] == "cone" and D["glass_to_dial"] and D["kb_race"] == "chamfer" and D["cap_top"] == "chamfer":
        # v0.21 [Ed 2 Nov]: no steps. Hub, flat underside over the pinion, one straight cone up to the plug in the bore, the 45° seat
        # on the glass's inner chamfer, a flat ring flush with the glass top, one straight cone (parallel) down to the race, hub top.
        rk = D["r_knob_bore"]; z1 = D["sleeve_z1"]
        if "hg_collar_r" in D:   # v0.25: the hub (gear, hub wall) is the separate PA-12 ring; the clear cap starts at its top
            return [(rk, D["h_band1"]), (D["cap_flat_r1"], D["h_band1"]), (sp, D["cap_plug_z0"]),
                    (sp, D["cap_seat_z_foot"]), (D["cap_seat_r_top"], z1), (D["cap_cone_r1"], z1),
                    (D["cap_cone_r0"], D["z_under_web"]), (D["r_chamfer0"], zt), (rk, zt)]
        return [(rk, z0), (rh, z0), (rh, D["h_band1"]), (D["cap_flat_r1"], D["h_band1"]), (sp, D["cap_plug_z0"]),
                (sp, D["cap_seat_z_foot"]), (D["cap_seat_r_top"], z1), (D["cap_cone_r1"], z1),
                (D["cap_cone_r0"], D["z_under_web"]), (D["r_chamfer0"], zt), (rk, zt)]
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
    if D.get("seal_type") == "oring":   # v0.19b: drip ring, a torus sitting on the glass OD just above the faceplate ring
        cs = D["seal_oring"][1]
        zc = D["lab_ring_z1"] + D["seal_oring_z_air"] + cs / 2
        return Pos(0, 0, zc) * Torus(D["knob_od"] / 2 + cs / 2, cs / 2)
    rb = D["knob_od"] / 2 + D["seal_glue"]
    z0 = D["lab_ring_z1"] + D["lab_gap"]; z1 = z0 + D["seal_top_t"]
    rs0 = D["lab_shoulder_r"]; rs1 = rs0 + D["seal_wall"]; zs = D["lab_shoulder_z0"]
    c = min(0.4, D["seal_top_t"] / 2)
    return rev([(rb, z0), (rs0, z0), (rs0, zs), (rs1, zs), (rs1, z1 - c), (rs1 - c, z1), (rb, z1)])

def race_cut(D):
    z0, zt = D["knob_hub_z0"], D["knob_hub_top"]
    return rev([(0, z0 - 0.5), (D["kb_r_lo"], z0 - 0.5), (D["kb_r_lo"], D["kb_zk0"]), (D["kb_r_up"], D["kb_zk1"]),
                (D["kb_r_up"], zt + 0.5), (0, zt + 0.5)])

def hub_teeth(D):
    """1220 hub gear teeth (profile-shifted, interface hub_x_gear), turned so a space faces the pinion on +X."""
    zh, fh, m, x = D["knob_hub_z0"], D["hub_gear_face"], D["hub_mod"], D["hub_x_gear"]
    dth = 2 * x * m * math.tan(math.radians(D["pressure"])) - D["brass_backlash"] / 2
    return Rot(0, 0, ext_phase(D["z_hub_gear"], D["z_pinion"])) * ext_gear(
        D, D["z_hub_gear"], zh, fh, module=m, dthick=dth,
        addendum=D["spur_addendum"] + x, dedendum=D["spur_dedendum"] - x)

def _keys(D, r0, r1, w, z0, h):
    n = D["hg_keys"]
    return [Rot(0, 0, 360.0 * k / n + 180.0 / n) * Pos((r0 + r1) / 2, 0, z0) * Box(r1 - r0, w, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
            for k in range(n)]

def hub_gear_ring(D):
    """v0.25 [Ed 19:00-19:10]: PA-12 (MJF) ring. Teeth z knob_hub_z0..h_band1; bore = the knob's running bore on the dial tube;
    a collar (r hg_collar_r) with hg_keys keys up into the cap's pocket. Keys between teeth angles (off the +X space)."""
    zh, z1, rk = D["knob_hub_z0"], D["hg_z1"], D["r_knob_bore"]
    ring = hub_teeth(D) + cyl(D["hg_collar_r"], D["h_band1"], z1 - D["h_band1"])
    for k in _keys(D, D["hg_collar_r"] - 0.05, D["hg_collar_r"] + D["hg_key_h"], D["hg_key_w"], D["h_band1"], z1 - D["h_band1"]):
        ring += k
    return ring - cyl(rk, zh - 0.1, z1 - zh + 0.2)

def cap_pocket(D):
    """Pocket in the clear cap's underside for the ring's collar and keys (bond lines hg_glue / hg_glue_ax)."""
    z0, z1, g = D["h_band1"] - 0.05, D["hg_pocket_z1"], D["hg_glue"]
    p = cyl(D["hg_pocket_r"], z0, z1 - z0)
    for k in _keys(D, D["hg_collar_r"] - 0.05, D["hg_slot_r"], D["hg_key_w"] + 2 * g, z0, z1 - z0):
        p += k
    return p

def build(D):
    split_hub = "hg_collar_r" in D   # v0.25: separate PA-12 hub-gear ring in a clear cap
    if split_hub:
        body = rev(profile(D)) - cap_pocket(D)
    else:
        zh, fh = D["knob_hub_z0"], D["hub_gear_face"]
        teeth = hub_teeth(D) - cyl(D["d_hg_root"] / 2 - 0.02, zh, fh)
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
        return cyl(D["sleeve_nylon_r"], z0, z1 - z0) - int_herringbone_half(D, D["z_ring"], z0 - 0.01, z1 + 0.01, mid)
    seat = D["cap_seat_gap"]
    z_top = h0 + h - seat                         # the glass sits this far above the printed cap
    groove = Pos(0, 0, D["ot_z"]) * Torus(D["ot_r"], D["ot_rg"])
    if D["hb_split"]:   # v0.18-v0.24 herringbone: two halves, gap at the apex
        lower = _half(h0, mid - gap / 2)
        upper = _half(mid + gap / 2, z_top)
        lower -= groove
    else:               # v0.25 [Ed 19:00]: straight teeth, one piece
        lower = None
        upper = _half(h0, z_top)
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
           **({"bottom internal ring (lower half)": lower, "bottom internal ring (upper half)": upper} if D["hb_split"]
              else {"bottom internal ring": upper}),
           "knob lower-cap land": land,
           f"knob balls {n} x Ø{D['kb_ball_d']:g} (45° cones)": balls}
    if split_hub:
        out["knob hub gear ring (PA-12, glued in the upper cap)"] = hub_gear_ring(D)
    if seal is not None:
        out[f"knob drip O-ring {D['seal_oring'][0]:g}x{D['seal_oring'][1]:g} silicone (on the glass)" if D.get("seal_type") == "oring"
            else "knob seal ring (PETG, bonded on the glass)"] = seal
    if D["rel_sensor"]: out[f"knob ring magnet Ø{ro_:g}/Ø{ri_:g}×{th_:g} diametric"] = ring_mag
    return out
