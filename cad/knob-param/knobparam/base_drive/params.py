"""base_drive own params + derive (cradle, brass tube, rod/sleeve/nuts, 1220 motor + pinion, idlers).
Reads: interface + own + IMPORTS (control_dial thrust-ball ring for the cradle groove)."""
import math
from ..common.util import cc_face, cc_on_circle

P = dict(
    # ---- 1220 motor [M] ----
    motor_pinion_face=4.4,   # [Ed 19:10] printed PA-12 12T m0.75 pinion, z 39.1-43.5 on the 5.5 shaft (0.5 under the cap); v0.24 3.0
    motor_bore_clear=0.05,   # [A]
    # ---- brass tube, rod ----
    brass_od=5.0,   # [S]/[A]
    brass_id=3.0,   # [S]/[A]
    brass_deburr=0.3,   # [S]/[A]
    glue_gap=0.1,   # [S]/[A]
    nut_s=3.2,   # [S]/[A]
    washer=(1.7, 4.0, 0.3),   # [S]/[A]
    use_washer=False,   # [Ed] v0.16: no washer - the bottom nut clamps straight onto the enlarged B.Cu rod pad
    sleeve=(1.7, 2.6),   # [S]/[A]
    rod_proud=0.5,   # [S]/[A]
    # ---- base cradle [A] ----
    cr_clear=0.5,
    peg_d_ratio=0.46,   # [A] locating peg diameter / plate thickness (~Ø1.6 on the 3.5 plate)
    peg_r_ratio=0.55,   # [A] peg radius / cradle radius
    peg_len_k=0.6,   # [A] peg engagement / PCB thickness
    peg_slot_k=0.5,   # [A] extra slot length / peg diameter (one hole is slotted)
    cradle_glue_k=0.03,   # [A] glue-line thickness / plate thickness
    cradle_land_k=0.35,   # [A] glue-land width / plate thickness
    cradle_foot_k=1.0,   # [A] future stiffener = this × cradle radius. The solid stays at r_out.
    cr_web_min=1.2,   # [Ed] v0.17: webs left round every support after the skinny-bridge cuts
    cr_bridge_fillet=0.5,   # [Ed] v0.17: fillet on those cuts (cut at the narrowest point)
    pad_cb=(7.0, 0.6),
    motor_glue=0.1,
    motor_collar_wall=1.4,
    motor_collar_top=12.0,
    collar_trim=3.0,
    dowel_pad_d=9.0,
    pocket_clear=0.5,
    dial_tube_clear=0.5,
    pin_d=1.5,
    # ---- encoder take-off [A] ----
    idler_bore=1.6,
    idler_hub_len=0.5,
    pin_head=(3.5, 0.5),
    pin_run=0.1,
    # ---- v0.15: Hall vernier (arm down through the cradle slot, 5 magnets x 5 sensors, arcs crossing) ----
    hv_slot_clear=0.5,   # [A] bar to the cradle slot walls over travel
    # ---- v0.16 detents (top-loaded: ball, spring, grub) [Ed] ----
    det_bore_clear=0.1,   # [A] bore over the ball
    det_thread_d=2.0,   # [A] M2 grub screw thread (tapped into the boss)
    det_grub_len=2.0,   # [A] M2x2 cup-point grub
    det_grub_adj=0.6,   # [A] grub top below the boss top at nominal (adjust both ways)
    det_spring=(1.4, 3.0, 0.2),   # [A] compression spring OD, free length, wire (non-magnetic: phosphor bronze / 316)
    det_preload=0.8,   # [A] spring compression on the flat (sets the feel; grub adjusts it)
    det_boss_wall=0.8,   # [A] wall round the thread (2 lines)
    det_leg_w=3.0,   # [A] leg / bridge width
    det_leg_len=2.4,   # [A] leg radial length inboard of the fan
    # ---- v0.16 centring springs + cushions ----
    stop_len=0.8,   # [A] stop face thickness. The block sits above the ear, so the thickness grows away from the lever.
    stop_bias=0.1,   # [A] deg. Parks the stop face a hair out so the at-rest gap stays ≥ 0.3 mm and contact is still at ±travel..
    stop_over=0.2,   # [A] stop block past the lever end
    sl_post_d=1.8,   # [A] spring anchor post
    # ---- v0.16 feel-motor open saddle clamp [Ed] ----
    fm_band_t=0.6,   # [A] band radial thickness (light load)
    fm_band_h=1.2,   # [A] band height (two narrow contact bands)
    fm_band_in=0.5,   # [A] band in from the grip ends
    fm_split=100.0,   # [A] split plane angle from the outboard direction (ears at the can sides, clear of the skirt)
    fm_ear=(1.6, 0.8),   # [A] ear radial length, tangential thickness (each half)
    fm_screw_d=0.0,   # overwritten: can_d * saddle_k_small (M1.2 on the Ø7 feel motor)
    saddle_k_small=1.2 / 7.0,   # [A] screw / can, small motors (feel, and later the Risley / mirror hooks)
    saddle_k_main=1.4 / 12.0,   # [A] screw / can, the 1220
    saddle_ear_k=2.0,   # [Ed] ear thickness / screw diameter
    saddle_edge_k=1.0,   # [Ed] material past the hole / screw diameter
    saddle_later=("risley prism 1", "risley prism 2", "scanner mirror"),   # hooks only; not placed until the optics round
    fm_spine_w=2.0,   # [A] seat spine width (rib to bands)
    fm_pip_r=1.15,   # [A] cap boss on the feel pinion
    fm_pip_z0=-0.55,   # [A] boss start, below the tooth bottom
    fm_pip_h=0.55,   # [A] boss height
    fm_cap_inset=0.20,   # [A] cap OD inside the tooth root
    fg_web=0.8,   # [A] compound-gear web thickness
    fg_hub_wall=0.9,   # [A] compound hub radius past the pin
    fg_tip_relief=0.9,   # [A] idler tooth-tip underside opened this far in
    fg_web_pocket=0.3,   # [A] web pocket stops this far inside the tooth root
    fg_web_land=0.2,   # [A] web disk stops this far inside the tooth root
    # ---- v0.21 [Ed 2 Nov] detent out on the arc: the boss hangs from a bridge on two columns, one each side of the arm sweep ----
    ad_col_r=1.2,   # [A] bridge column radius (Ø2.4: Ø1.6 lifted the boss ~0.09 under the spring)
    ad_col_need=0.4,   # [A] column to the swept arm, pinion tips, pockets and the feel saddle (plan)
    ad_link_w=2.0,   # [A] bridge link width; height = boss top - link bottom
    ad_E=2500.0,   # [A] UTR-8100 Young's modulus, N/mm² (clear SLA resin ~2.5 GPa; the cradle is printed in it)
    det_spring_k=0.8,   # [A] detent spring rate N/mm (Ø1.4 × 0.2 phosphor bronze, ~6 active coils, G 41 GPa): replace with the bought spring
    ad_defl_max=0.05,   # [A] boss lift under the spring (grub fully in, ball at a dimple rim): 20% of the dimple depth
    tk_slot_land=0.4,   # [A] cradle plate left between a track groove and the Hall slot
    # ---- v0.22 [Ed 2 Nov 15:27] split arm: the detent boss on a short bracket into a wall just outboard of the flange sweep;
    # the ball train on a pedestal under the detent ball (study: docs/img/dial-split-study.png) ----
    sp_wall_gap=0.35,   # [A] wall inner face to the flange's swept outer edge (0.3 + rounding)
    sp_wall_r1=16.89,   # [A] wall outer face: 0.35 inside the knob ring's upper half (r 17.24, turns with the knob)
    sp_wall_a=(246.5, 281.0),   # [A] wall from the Hall spoke's sweep (+ gap) to short of the lever's (mechanism frame)
    sp_brk_w=3.0,   # [A] bracket width, boss to wall
    sp_ped_pocket=1.5,   # [A] the pedestal block is guided this deep in a pocket in the plate
    sp_ped_clear=0.1,   # [A] pocket over the block, all round (slide fit, SLA both)
    sp_ped_lift=0.25,   # [A] block bottom above the pocket floor at nominal: ±0.25 of adjustment (the printed-stack tolerance)
    sp_grub=(2.0, 2.0),   # [Ed 15:50] M2 x 2 grub under the pedestal, tapped into the plate like the detent boss; sets the train
                          # height against the 45° knob race stack at assembly (key through the PCB from behind)
    sp_thread_min=1.5,   # [A] grub thread kept in the plate at the top of its range
    sp_lift_max=0.010,   # [Ed 2x rule] boss lift under the detent spring: 0.01 (was 0.05 for the v0.21 bridge)
    # ---- v0.25 [Ed 3 Nov 18:15] detent block: the boss, its bracket and the wall are one separate printed block (UTR-8100, like
    # the cradle), dropped in from the top after the pedestal, the train and the dial's lower part, with the ball, spring and grub
    # already in it. Danny's hold-down is a screw from behind through the main board; it does not fit (the block's foot is the
    # wall zone between the flange's sweep and the cradle OD, r 15.00-16.855 = 1.855 wide: an M2 needs 1.6 + 2 x 0.8 SLA wall =
    # 3.2, an M1.6 2.85), so the block takes his fallback: glued on its flat seat, located on two pins [A, Ed 18:15 fallback]. ----
    dt_block=True,   # [Ed 18:15] False = v0.22-v0.24: wall, bracket and boss printed in the cradle
    dt_head_half=10.0,   # [A] the head (v0.24: a 3.0-wide bracket, boss to wall) is a sector +-10° about the boss, from the boss's
                         # inner edge out to the wall, boss underside to top: the 3.0 bracket left the head 3x softer than the wall
    dt_r1_inset=0.0,   # [A] block outer face this far inside the cradle OD r_out (v0.25 gears: r_out 16.855; the v0.24 wall's 16.89
                       # stuck out 0.035). Replaces sp_wall_r1 while dt_block is on.
    dt_pin=(1.0, 1.5, 1.5),   # [A] Ø1 steel dowels: Ø, pressed depth in the plate, engagement up into the block's foot
    dt_pin_angs=(250.5, 277.0),   # [A] pin angles (mechanism frame) at the foot's mid radius: 1.0 of foot past each hole end
    dt_pin_clear=0.05,   # [A] foot hole over the pin (slip, glued)
    dt_glue=0.05,   # [A] epoxy bond line on the seat (modelled as contact; counted in the lift)
    dt_glue_E=2500.0,   # [A] cured epoxy modulus, N/mm²
    dt_glue_lap=10.0,   # [A] epoxy on sanded SLA resin, lap shear / tension allowable, MPa (conservative; datasheets 15-25)
    dt_pcb_E=10000.0,   # [A] FR4 through-thickness modulus, N/mm² (the PCB under the cradle plate, in the lift's seat term)
    # ---- v0.30 [Ed 4 Nov 15:15] (interface cc_on): two compression centring springs on an arc in the cradle plate, one each side
    # of the Hall arm's first link, and the hard stop in the Hall slot: two stop faces the arm's links meet flush at ±travel.
    # Danny's idea (13:03 "compression springs", 13:48 "an arc would be more ideal"). Sketch docs/img/dial-cspring-sketch.png. ----
    cc_wire=0.16,   # [A] (OD cc_od and axis cc_r, cc_z are interface params: the dial's seats use them too)
    cc_n=None,   # [A] active coils; None = derived from the dial's centring rate (dial_spring), to 1/4 coil
    cc_ends=2.0,   # [A] closed ends: solid length = (n + ends) x wire
    cc_G=69000.0,   # [A] 316 spring wire shear modulus, N/mm²
    cc_uts=1689.0,   # [S] Gibbs Type 316 spring wire, min tensile at its smallest listed size (0.009 in = 0.23 mm); finer wire is not weaker
    cc_tau_frac=0.45,   # [A] static allowable shear / tensile, set removed (spring-maker rule of thumb)
    cc_solid_margin=0.3,   # [A] the spring stays this much over solid with the arm at the hard stop
    cc_gap=0.0,   # [A, Ed 15:15 no preload] free end to its seat in the arm at centre: each spring pushes
                  # only when the arm moves toward it (the springs go in before the dial; preloaded they would block the bar going in)
    cc_pocket_clear=0.1,   # [A] pocket over the spring OD, radially and under it; open at the plate top
    # ---- v0.30 [Ed 4 Nov 15:46] (interface hs_slot): the dial's hard stop in the Hall slot. Two stop faces on the slot's end walls are
    # the Hall bar's link faces at exactly ±travel; the bar meets them flush (no r 7 stop blocks on the lever any more). ----
    hs_stops=((-1, 3, 13.6, 15.5), (1, 2, 10.9, 12.6)),   # [A, sketch] (side, link from pad index, r0, r1): the - stop on the bar's
                  # outer link (pads 4-5, 2.3-3.7 of plate behind it), the + stop on pads 3-4 (at r 14-16 only ~1.0: the block's pin hole)
    hs_stop_depth=0.8,   # [A] stop face block depth into the slot wall (the 0.5 slot clearance + 0.3 into the wall)
    hs_stop_z0=1.6,   # [A] stop face from z 1.6 (the bar bottom, hv_z_mag0 1.75, - 0.15) to the plate top; the sensor openings stay open
    hs_back_min=2.0,   # [A] plate behind each stop face (to the next void, along the push)
    # ---- v0.30 [Ed 4 Nov 15:46]: centring-spring anchor post 2 (with its pin) hangs from the detent block on a short arm over the
    # springs (it stood over the dial's detent spoke, attached to nothing, since the block became a separate part) ----
    dt_hang_post=2,   # [Ed 15:46] the anchor post the block carries (1-based, sl_anchor_xy order); post 1 stays on the cradle
    dt_hang_w=2.4,   # [A] arm width
    dt_hang_t=2.0,   # [A] arm depth (z)
    dt_hang_gap=0.3,   # [A] arm underside over the spring-pin tops (sl_pin_top)
    dt_hang_at=(0.0, 1.0),   # [A] the arm's root in the head: this far out from the head's inner radius, this many degrees in from
                             # its edge on the post's side (clear of the grub bore: row)
    dt_hang_F=1.0,   # [A] spring pull on post 2, conservative (initial tension + full travel; the springs' rate is ~0.23 N/mm)
)

IMPORTS = {"control_dial": ["tb_on", "tb_pcd", "tb_groove_r", "tb_z_ball",
                            "arm_det", "ad_r", "ad_ang", "ad_z_land", "tk", "tk_webs",   # v0.21 arc detent + tracks
                            "sp_ped", "sp_hw", "ad_land_half",   # v0.22 split arm: pedestal, flange half-width / half-angle
                            "dial_spring"],   # v0.30 compression centring springs: the dial's centring rate
           "main_knob": ["h_bi1", "hb_mid"]}   # feel-motor can sits above the bottom ring; herringbone apex
EXPORTS = []


def _place_pegs(D):
    """Two locating pegs on the cradle. One PCB hole is round, one is slotted along the radius."""
    peg_r = D["r_out"] * D["peg_r_ratio"]
    need = D["peg_d"] / 2 + D["cr_clear"]
    blocks = [(0.0, 0.0, D["brass_od"] / 2 + D["peg_d"]),
              (D["offset"], 0.0, D["motor_bore_d"] / 2 + D["peg_d"]),
              (*D["enc_xy"], D["brg"]["D"] / 2 + D["peg_d"]),
              (*D["fm_xy"], D["feel"]["can_d"] / 2)]
    for x, y in D["idler_xy"]:
        blocks.append((x, y, D["enc_pocket_d"] / 2 + D["peg_d"] / 2))
    for r, a in zip(D["hv_r"], D["hv_phi_s"]):
        blocks.append((r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), 2.0))
    def clear(a):
        x, y = peg_r * math.cos(math.radians(a)), peg_r * math.sin(math.radians(a))
        return min(math.hypot(x - bx, y - by) - br for bx, by, br in blocks)
    best = None
    for a in range(0, 360, 5):
        for b in range(a + 90, a + 270, 5):
            c = min(clear(a), clear(b % 360))
            if best is None or c > best[0]:
                best = (c, a, b % 360)
    _c, a, b = best
    def xy(ang):
        return (peg_r * math.cos(math.radians(ang)), peg_r * math.sin(math.radians(ang)))
    D["peg_xy"] = [xy(a), xy(b)]
    D["peg_ang"] = [a, b]
    D["peg_r"] = peg_r


def _pol(r, a): return r * math.cos(math.radians(a)), r * math.sin(math.radians(a))


def _ad(a, b): return min((a - b) % 360.0, (b - a) % 360.0)


def _arm_swept_hit(D, x, y, rr):
    """True if a disk (x, y, rr) comes within ad_col_need of the dial arm swept ±travel (fan, land, rib, lever, track webs)
    or stands over the Hall slot. Plan only; the bridge links run above the arm, the columns go down to the plate."""
    R2D = math.degrees; T = D["travel_deg"]; c = D["ad_col_need"]
    r = math.hypot(x, y); a = math.degrees(math.atan2(y, x)) % 360.0
    if r < 1e-6: return True
    def in_sector(r0, r1, a0, a1):   # disk within c of a sector swept ±T
        if r + rr + c < r0 or r - rr - c > r1: return False
        mid, half = (a0 + a1) / 2, (a1 - a0) / 2 + T + R2D((rr + c) / max(r, 0.5))
        return _ad(a, mid) < half
    if in_sector(D["fan_r0"], D["fan_r1"], D["ha_ang0"] - D["fan_half"], D["ha_ang0"] + D["fan_half"]): return True
    for r0, r1, a0, a1 in D["tk_webs"]:
        if in_sector(r0, r1, a0, a1): return True
    # rib: trapezoid along ha_ang0, width w0 at the hub to w1 at the hammerhead and on to ha_rib_r1
    if r - rr - c < D["ha_rib_r1"]:
        r0, rh = D["ha_rib_r_hub"], D["ha_rib_r_head"]
        rr_ = min(max(r, r0), D["ha_rib_r1"])
        w = D["ha_rib_w0"] + (D["ha_rib_w1"] - D["ha_rib_w0"]) * (rr_ - r0) / max(rh - r0, 1e-6) if rr_ <= rh else D["ha_rib_w1"]
        if _ad(a, D["ha_ang0"]) < T + R2D(math.asin(min(1.0, (w / 2 + rr + c) / max(r, 0.5)))): return True
    # lever, stop blocks, spring anchors: everything near the lever inside sl_r + 2
    if r - rr - c < D["sl_r"] + 2.0 and _ad(a, D["sl_ang"]) < T + 30.0: return True
    # Hall slot (the plate must be under the column): bar samples, pad + slot clearance, swept ±T
    pr = D["hv_pad_r"] + D["hv_slot_clear"]
    rs, ps = D["hv_r"], D["hv_phi_m"]
    for i in range(len(rs)):
        for k in range(9 if i else 1):
            t = k / 8
            r_s = rs[i - 1] + (rs[i] - rs[i - 1]) * t if i else rs[0]
            a_s = ps[i - 1] + (ps[i] - ps[i - 1]) * t if i else ps[0]
            for th in range(-int(T) - 1, int(T) + 2):
                th = max(-T, min(T, th))
                bx, by = _pol(r_s, a_s + th)
                if math.hypot(x - bx, y - by) < pr + rr + c: return True
    return False


def _place_arc_bridge(D):
    """v0.21: two columns, one each side of the arm sweep (encoder side, lever side), each the nearest site to the detent
    boss that stands on the plate clear of the arm sweep, the pinions and pockets, the feel saddle, the dial tube and the ring.
    Links at det_z0 (over the land, the rib top and the webs) run from each column to the boss."""
    rr, c = D["ad_col_r"], D["ad_col_need"]
    bx, by = D["det_xy"][0]
    can = D["feel"]["can_d"] / 2 + D["feel"]["saddle_rad"]
    holes = [(*D["enc_xy"], D["enc_pocket_d"] / 2), *[(x, y, D["enc_pocket_d"] / 2) for x, y in D["idler_xy"]],
             (*D["fm_xy"], can), (*D["fm_xy"], D["fm_shaft_hole"] / 2), *[(x, y, D["fm_lead_r"]) for x, y in D["fm_pad_xy"]]]
    def seg_clear(x0, y0, x1, y1, px, py):
        vx, vy = x1 - x0, y1 - y0; L2 = vx * vx + vy * vy
        t = 0.0 if L2 < 1e-9 else max(0.0, min(1.0, ((px - x0) * vx + (py - y0) * vy) / L2))
        return math.hypot(x0 + t * vx - px, y0 + t * vy - py)
    best = {}
    for ir in range(int((D["dial_tube_od"] / 2 + 1) * 10), int(D["r_out"] * 10)):
        r = ir / 10.0
        if r + rr > D["r_out"] - 0.3 or r - rr < D["dial_clear_d"] / 2 + c: continue
        for ia in range(0, 720):
            a = ia / 2.0
            side = -1 if ((a - D["ha_ang0"]) % 360.0) > 180.0 else 1
            if _ad(a, D["ha_ang0"]) > 90.0: continue
            x, y = _pol(r, a)
            if any(math.hypot(x - hx, y - hy) < hr + rr + c for hx, hy, hr in holes): continue
            if _arm_swept_hit(D, x, y, rr): continue
            if seg_clear(x, y, bx, by, *D["fm_xy"]) < can + D["ad_link_w"] / 2 + c: continue
            L = math.hypot(x - bx, y - by)
            if side not in best or L < best[side][0]:
                best[side] = (L, x, y)
    if set(best) != {-1, 1}:
        raise ValueError("no site for the arc detent bridge columns on both sides of the arm")
    D["ad_col_xy"] = [best[-1][1:], best[1][1:]]
    D["ad_link_len"] = [best[-1][0], best[1][0]]
    D["ad_z_link"] = D["det_z0"]                                             # links over the land / rib top (+ det_gap)
    # bridge lift under the spring: two L frames (column + link) in parallel, plate taken as rigid
    E = D["ad_E"]; h = D["ad_z_link"] - D["plate_t"]; hl = D["det_z1"] - D["ad_z_link"]
    Ic = math.pi * (2 * rr) ** 4 / 64; Il = D["ad_link_w"] * hl ** 3 / 12
    k = sum(1.0 / (L * L * h / (E * Ic) + L ** 3 / (3 * E * Il)) for L in D["ad_link_len"])
    D["det_force_max"] = D["det_spring_k"] * (D["det_preload"] + D["det_grub_adj"] + D["det_dimple"])
    D["ad_defl"] = D["det_force_max"] / k


def _place_split_mount(D):
    """v0.22: wall sector outboard of the flange sweep (plate to boss top), a radial bracket from the boss to the wall, and the
    boss lift under the full spring force: the wall bends as a cantilever from the plate under the moment F·e (e = boss to the
    wall's mid radius), lift at the boss = F e² h / (E I), I of the wall's plan section about its tangential axis."""
    r0 = D["ad_r"] + D["sp_hw"] + D["sp_wall_gap"]; a0, a1 = D["sp_wall_a"]
    r1 = D["r_out"] - D["dt_r1_inset"] if D["dt_block"] else D["sp_wall_r1"]   # v0.25: flush with the cradle OD, not past it
    D["sp_wall_r0"], D["sp_wall_r1_used"] = r0, r1
    rm = (r0 + r1) / 2; t = r1 - r0; L = rm * math.radians(a1 - a0)
    D["det_force_max"] = D["det_spring_k"] * (D["det_preload"] + D["det_grub_adj"] + D["det_dimple"])
    e = rm - D["ad_r"]; h = D["det_z1"] - D["plate_t"]; I = L * t ** 3 / 12
    D["sp_wall_e"], D["sp_wall_I"], D["sp_wall_h"] = e, I, h
    D["sp_lift"] = D["det_force_max"] * e * e * h / (D["ad_E"] * I)
    if D["dt_block"]:
        _detent_block_joint(D, r0, r1, rm, t, L, e)
        if D["hs_slot"] and not D["cc_on"]:
            _dt_hanger(D)
    # v0.22b [Ed 15:50]: pedestal is a separate block on an M2 grub, guided in a pocket
    zb = D["tk"][0]["z"]; D["sp_z_blk1"] = zb - D["bt_up"]                     # block top (train seat level)
    D["sp_z_pf"] = D["plate_t"] - D["sp_ped_pocket"]                       # pocket floor
    D["sp_z_blk0"] = D["sp_z_pf"] + D["sp_ped_lift"]                       # block bottom = grub tip at nominal
    gd, gl = D["sp_grub"]
    D["sp_z_grub0"] = D["sp_z_blk0"] - gl                                   # grub bottom (hex socket, key from below)
    D["sp_adj_down"] = min(D["sp_ped_lift"], D["sp_z_grub0"])               # until the block meets the floor / the grub the PCB
    D["sp_adj_up"] = D["sp_z_pf"] - D["sp_thread_min"] - D["sp_z_grub0"]   # while sp_thread_min of thread stays in the plate
    D["sp_guide"] = D["plate_t"] - D["sp_z_blk0"]


def _detent_block_joint(D, r0, r1, rm, t, L, e):
    """v0.25 [Ed 18:15] detent block glued on its seat (the wall's footprint on the plate top). Boss lift under the full spring
    force F at the boss (r ad_r), moment M = F e about the seat's centroid, as rotations summed over the load path:
      wall from the seat up to the bracket (I = L t³/12), the head (wall + bracket, the boss and its bore left out), the epoxy
      bond line and, conservatively, the cradle plate and the PCB under the seat taken as columns of the seat's own footprint;
      lift = sum(θ) x e. The v0.22-v0.24 one-piece check took the whole height at the wall's I with the plate rigid."""
    F, E = D["det_force_max"], D["ad_E"]; Mo = F * e; pt = D["plate_t"]
    I_seat = L * t ** 3 / 12
    h1 = D["det_z0"] - pt                                                   # wall alone, under the bracket
    h2 = D["det_z1"] - D["det_z0"]                                          # head: wall + bracket
    ri = D["ad_r"] - D["det_boss_d"] / 2                                    # head: sector from the boss's inner edge to the wall
    wb = 2 * D["ad_r"] * math.sin(math.radians(D["dt_head_half"])) - D["det_thread_d"]   # its width less the bore / thread
    rb0 = ri
    A1, c1 = L * t, rm; A2, c2 = wb * (r0 - rb0), (r0 + rb0) / 2
    cc = (A1 * c1 + A2 * c2) / (A1 + A2)
    I_head = I_seat + A1 * (c1 - cc) ** 2 + wb * (r0 - rb0) ** 3 / 12 + A2 * (c2 - cc) ** 2
    th = dict(wall=Mo * h1 / (E * I_seat), head=Mo * h2 / (E * I_head),
              bond=Mo * D["dt_glue"] / (D["dt_glue_E"] * I_seat),
              plate=Mo * (pt / E + D["pcb_t"] / D["dt_pcb_E"]) / I_seat)
    D["dt_lift_parts"] = {k: v * e for k, v in th.items()}
    D["dt_lift"] = sum(D["dt_lift_parts"].values())
    D["dt_I_seat"], D["dt_I_head"] = I_seat, I_head
    D["dt_seat_area"] = L * t
    D["dt_bond_sigma"] = F / (L * t) + 6 * Mo / (L * t * t)                 # peak tension at the seat's inner edge
    D["dt_seat"] = (r0, r1, D["sp_wall_a"][0], D["sp_wall_a"][1])
    pd = D["dt_pin"][0] + D["dt_pin_clear"]
    D["dt_pin_wall"] = min(rm - r0, r1 - rm) - pd / 2                       # foot material each side of a pin hole (radial)
    D["dt_pin_xy"] = [_pol(rm, a) for a in D["dt_pin_angs"]]
    D["dt_pin_end"] = min(min(a - D["sp_wall_a"][0], D["sp_wall_a"][1] - a) for a in D["dt_pin_angs"]) * math.pi / 180 * rm - pd / 2
    D["dt_screw_need"] = {"M2": 1.6 + 2 * 0.8, "M1.6": 1.25 + 2 * 0.8}      # foot width a tapped screw needs (tap drill + SLA walls)


def _hs_stops(D):
    """v0.30 [Ed 4 Nov 15:46]: the dial's hard stop in the Hall slot. Each stop face is the Hall bar's link face (pads j, j+1) on
    side s, rotated to s x travel, between radii r0 and r1, hs_stop_depth into the slot's end wall."""
    T = D["travel_deg"]; D["hs_stop_polys"] = []
    for s, j, r0, r1 in D["hs_stops"]:
        p, u, o, L = cc_face(D, j, s)
        ca, sa = math.cos(math.radians(s * T)), math.sin(math.radians(s * T))
        rot = lambda q: (q[0] * ca - q[1] * sa, q[0] * sa + q[1] * ca)
        a_, b_ = cc_on_circle(p, u, r0), cc_on_circle(p, u, r1)
        e = D["hs_stop_depth"]
        poly = [rot(a_), rot(b_), rot((b_[0] + e * o[0], b_[1] + e * o[1])), rot((a_[0] + e * o[0], a_[1] + e * o[1]))]
        D["hs_stop_polys"].append((s, j, r0, r1, poly))
    D["hs_stop_h"] = D["plate_t"] - D["hv_z_mag0"]                         # contact height: the bar in the plate (its bottom = the magnets' bottom)


def _dt_hanger(D):
    """v0.30 [Ed 4 Nov 15:46]: anchor post dt_hang_post hangs from the detent block's head on a straight arm over the springs, its
    anchor pin pressed down through the arm into it. Deflection at the spring's height under dt_hang_F (arm bent sideways and
    twisted, the post bent), and the extra peak tension it puts on the block's glued seat."""
    k = D["dt_hang_post"] - 1; px, py = D["sl_anchor_xy"][k]
    a_post = math.degrees(math.atan2(py, px)) % 360.0
    sg = 1.0 if ((a_post - D["ad_ang"] + 180) % 360 - 180) > 0 else -1.0  # the post's side of the head
    ri = D["ad_r"] - D["det_boss_d"] / 2
    rA = ri + D["dt_hang_at"][0]; aA = D["ad_ang"] + sg * (D["dt_head_half"] - D["dt_hang_at"][1])
    ax, ay = _pol(rA, aA)
    z_post = D["sl_top"] + D["tgt"]["arm_vs_cradle"] + 0.15
    z0 = D["sl_pin_top"] + D["dt_hang_gap"]; z1 = z0 + D["dt_hang_t"]
    w, t = D["dt_hang_w"], D["dt_hang_t"]; L = math.hypot(px - ax, py - ay)
    E = D["ad_E"]; G = E / 2.6; F = D["dt_hang_F"]
    z_load = D["sl_top"] + D["sl_spring_gap"] + D["sl_spring"][0] / 2      # the spring's axis
    hp = z0 - z_load                                                       # post length below the arm, to the load
    Ib = t * w ** 3 / 12                                                   # arm, bending sideways
    a_, b_ = max(w, t), min(w, t); J = a_ * b_ ** 3 * (1 / 3 - 0.21 * b_ / a_ * (1 - b_ ** 4 / (12 * a_ ** 4)))
    Ip = math.pi * D["sl_post_d"] ** 4 / 64
    dl = dict(arm=F * L ** 3 / (3 * E * Ib), twist=F * hp * L / (G * J) * hp, post=F * hp ** 3 / (3 * E * Ip))
    bx, by = _pol(D["ad_r"], D["ad_ang"])
    D["dt_hang"] = dict(post_xy=(px, py), post_ang=a_post, root=(ax, ay), root_r=rA, root_ang=aA, z_post=z_post, z0=z0, z1=z1, L=L,
                        defl=sum(dl.values()), defl_parts=dl, z_load=z_load,
                        bore_clear=math.hypot(ax - bx, ay - by) - w / 2 - D["det_thread_d"] / 2,
                        top_room=D["det_z1"] - z1)
    r0, r1 = D["dt_seat"][0], D["dt_seat"][1]; ts = r1 - r0; Ls = D["dt_seat_area"] / ts
    D["dt_hang_sigma"] = 6 * F * (z_load - D["plate_t"]) / (Ls * ts * ts)  # pull at the spring's height, about the seat's weak axis


def _ccspring(D):
    """v0.30 [Ed 4 Nov 15:15]: the compression centring springs (one per side, on an arc at cc_r, each pushing its flat seat in the
    Hall bar's first link only when the arm turns toward it; seats from the interface) and the hard stop in the Hall slot (stop
    faces: _hs_stops)."""
    R2D = math.degrees; T = D["travel_deg"]; R = D["cc_r"]
    d, od = D["cc_wire"], D["cc_od"]; Dm = od - d
    D["cc_travel_arc"] = R * math.radians(T)
    # coils for the dial's centring rate with one spring working per side: k R² (rad) = dial_spring (per deg), to 1/4 coil
    k_need = D["dial_spring"] * 180.0 / math.pi / (R * R)
    n = D["cc_n"] if D["cc_n"] else round(D["cc_G"] * d ** 4 / (8 * Dm ** 3 * k_need) * 4) / 4
    D["cc_n_used"] = n
    D["cc_k"] = D["cc_G"] * d ** 4 / (8 * Dm ** 3 * n)                      # N/mm
    D["cc_solid"] = (n + D["cc_ends"]) * d
    D["cc_L_stop"] = D["cc_solid"] + D["cc_solid_margin"]                 # spring length with the arm at the hard stop
    pre = D["cc_gap"]                                                      # arm travel before it meets the spring
    D["cc_L0"] = D["cc_travel_arc"] + D["cc_L_stop"] - pre                 # free length
    D["cc_dead_deg"] = R2D(pre / R)                                        # each side of centre, nominal
    D["cc_pocket_ang"] = {s: D["cc_seat_ang"][s] + s * R2D((D["cc_travel_arc"] + D["cc_L_stop"]) / R) for s in (-1, 1)}
    D["cc_free_ang"] = {s: D["cc_seat_ang"][s] + s * R2D(pre / R) for s in (-1, 1)}
    D["cc_F_max"] = D["cc_k"] * (D["cc_travel_arc"] - pre)
    D["cc_T_end"] = D["cc_F_max"] * R                                      # N·mm at ±travel (one spring)
    D["cc_rate"] = D["cc_k"] * R * R * math.pi / 180.0                     # N·mm/deg, one spring per side
    C = Dm / d; Kw = (4 * C - 1) / (4 * C - 4) + 0.615 / C
    D["cc_C"] = C
    D["cc_tau"] = 8 * D["cc_F_max"] * Dm * Kw / (math.pi * d ** 3)
    D["cc_tau_allow"] = D["cc_tau_frac"] * D["cc_uts"]


def derive(D):
    R2D = math.degrees; M = D["motor"]
    D["fm_screw_d"] = D["feel"]["can_d"] * D["saddle_k_small"]
    D["main_screw_d"] = M["body_d"] * D["saddle_k_main"]
    D["h_motor_front"] = M["motor_len"] + M["gearbox_len"] + M["boss_len"]
    D["h_shaft_tip"] = D["h_motor_front"] + M["shaft_len"]
    D["h_pinion0"] = D["h_shaft_tip"] - D["motor_pinion_face"]
    # ---- cradle ----
    D["r_out"] = D["skirt_id"] / 2 - D["cr_clear"]
    D["cradle_foot_r"] = D["r_out"] * D["cradle_foot_k"]   # exported; not drawn past r_out
    D["cradle_glue"] = D["plate_t"] * D["cradle_glue_k"]
    D["cradle_land"] = D["plate_t"] * D["cradle_land_k"]
    D["peg_d"] = D["plate_t"] * D["peg_d_ratio"]
    D["peg_len"] = D["pcb_t"] * D["peg_len_k"]
    D["peg_slot"] = D["peg_d"] * (1.0 + D["peg_slot_k"])
    D["cr_bore_d"] = D["brass_od"] + 2 * D["glue_gap"]
    D["motor_bore_d"] = M["body_d"] + 2 * D["motor_glue"]
    D["motor_collar_od"] = D["motor_bore_d"] + 2 * D["motor_collar_wall"]
    D["enc_pocket_d"] = D["d_pin_tip"] + 2 * D["pocket_clear"]
    D["dial_clear_d"] = D["dial_tube_od"] + 2 * D["dial_tube_clear"]
    _place_pegs(D)
    # ---- idlers ----
    D["idler_floor"] = D["h_pin0"] - D["idler_hub_len"]
    D["idler_pocket_top"] = D["h_pin1"] + D["cr_clear"]
    D["pin_z1"] = D["h_pin1"] + D["pin_run"] + D["pin_head"][1]
    # ---- rod ----
    D["nut_seat_t"] = D["washer"][2] if D["use_washer"] else D["rod_pad_t"]
    D["z_rod_bot"] = D["z_pcb_back"] - D["nut_seat_t"] - D["nut_m"] - D["rod_proud"]
    # ---- Hall slot through the cradle plate (vernier) ----
    if D["hall_layout"] == "vernier":
        D["hv_slot_r0"] = D["hv_r"][0] - D["hv_pad_r"] - D["hv_slot_clear"]
        D["hv_slot_r1"] = D["skirt_id"] / 2 + 0.5
        dev = max(abs(a - D["ha_ang0"]) for a in D["hv_phi_m"] + D["hv_phi_s"])
        D["hv_slot_half"] = dev + D["travel_deg"] + R2D((D["hv_pad_r"] + D["hv_slot_clear"]) / D["hv_slot_r0"])
        if D["cc_on"]:
            _ccspring(D)
        if D["hs_slot"]:
            _hs_stops(D)
    # ---- v0.16 detents (v0.21: one detent on the arc, riding a land flush with the rib top) ----
    db = D["det_ball"]
    arc = D["arm_det"] in ("arc", "split") and D["ad_r"] is not None   # v0.22: split shares the arc keys
    z_ride = D["ad_z_land"] if arc else D["fan_top"]                         # the surface the ball rides on
    D["det_z0"] = z_ride + D["det_gap"]                                     # boss underside
    D["det_z_ball"] = z_ride + db / 2                                       # ball centre riding on the flat land / wing top
    D["det_bore_d"] = db + D["det_bore_clear"]
    D["det_spring_inst"] = D["det_spring"][1] - D["det_preload"]
    D["det_z_grub0"] = D["det_z_ball"] + db / 2 + D["det_spring_inst"]
    D["det_z_thread0"] = D["det_z_grub0"] - D["det_grub_adj"]
    D["det_z1"] = D["det_z_grub0"] + D["det_grub_len"] + D["det_grub_adj"]
    D["det_boss_d"] = D["det_thread_d"] + 2 * D["det_boss_wall"]
    # v0.17: foot stops below the moving ear; the bridge and boss stay above the ear (det_z0)
    ear_r0 = min(D["bt_rs"]) - D["bt_groove_r"] - D["fan_clear"]
    D["det_leg_r1"] = max(D["dial_tube_od"] / 2 + D["det_leg_len"], ear_r0 - D["fan_clear"])
    D["det_leg_r0"] = D["det_leg_r1"] - D["det_leg_len"]
    D["det_foot_z1"] = D["fan_z0"] - D["fan_clear"]
    D["det_xy"] = [_pol(D["ad_r"], D["ad_ang"])] if arc else [_pol(D["det_r"], a) for a in D["det_angs"]]
    # ---- v0.16 centring springs: anchors tangential from the lever pin, one hook-to-hook length each way ----
    a = math.radians(D["sl_ang"]); L = D["sl_spring"][1]
    px, py = D["sl_pin_r"] * math.cos(a), D["sl_pin_r"] * math.sin(a); tx, ty = -math.sin(a), math.cos(a)
    D["sl_anchor_xy"] = [(px + L * tx, py + L * ty), (px - L * tx, py - L * ty)]
    # ---- feel motor mount (axial, pinion in the bottom-ring band, can above the ring) ----
    F = D["feel"]
    D["fm_z_can0"] = max(D["h_pin1"] + F["can_gap"], D["h_bi1"] + F["clear"])
    D["fm_z_can1"] = D["fm_z_can0"] + F["can_len"]
    D["fm_grip"] = F["clip_frac"] * F["can_len"]   # [A] collar length = this fraction of the can, from the shaft end
    # wall uses whatever skirt margin the placement left, capped at the 1220 collar wall
    D["fm_wall"] = min(D["motor_collar_wall"], D["skirt_id"] / 2 - (D["fm_cd"] + F["can_d"] / 2 + D["motor_glue"]) - F["clear"])
    D["fm_pocket_r"] = D["feel"]["shaft_d"] / 2 + D["motor_bore_clear"]   # v0.17: shaft only; the pinion is under the PCB
    D["fg_shaft_len"] = D["fm_z_can0"] - D["fg_z_bot"]                    # 716 shaft stick-out down through the catalogue pinion
    D["fm_rib_r0"] = D["dial_tube_od"] / 2 + F["clear"]                 # outside the dial tube
    D["fm_rib_r1"] = D["fm_cd"] - D["fm_pocket_r"] - D["motor_glue"]    # inside the pinion pocket
    D["fm_rib_w"] = F["can_d"] / 2                                      # [A] tangential width, half the can
    D["fm_z_rib1"] = D["fm_z_can0"] - D["motor_glue"]                    # glue gap under the clip foot
    D["fm_lead_r"] = F["pad_hole"] / 2 + D["motor_glue"]
    if arc and D["arm_det"] == "split":
        _place_split_mount(D)
    elif arc:
        _place_arc_bridge(D)   # v0.21: needs the feel lead holes above
    return D
