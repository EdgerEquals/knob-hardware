"""base_drive own params + derive (cradle, brass tube, rod/sleeve/nuts, 1220 motor + pinion, idlers).
Reads: interface + own + IMPORTS (control_dial thrust-ball ring for the cradle groove)."""
import math

P = dict(
    # ---- 1220 motor [M] ----
    motor_pinion_face=3.0,   # [A]
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
)

IMPORTS = {"control_dial": ["tb_on", "tb_pcd", "tb_groove_r", "tb_z_ball",
                            "arm_det", "ad_r", "ad_ang", "ad_z_land", "tk", "tk_webs"],   # v0.21 arc detent + tracks
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
    # ---- v0.16 detents (v0.21: one detent on the arc, riding a land flush with the rib top) ----
    db = D["det_ball"]
    arc = D["arm_det"] == "arc" and D["ad_r"] is not None
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
    if arc:
        _place_arc_bridge(D)   # v0.21: needs the feel lead holes above
    return D
