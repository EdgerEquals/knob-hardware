"""Top-screen joystick stack v0.4 — params + derive.

Local frame: origin = carrier centre on the MAIN PCB FRONT (z = 0), +x right along the panel width, +y up the panel
(toward the panel top), +z out of the panel. Placement in the knob-param frame (dial axis = 0,0): (0, place_y).
Tags: [Ed] Ed's decision, [S] datasheet, [L] panel layout, [K] main-PCB KiCad, [A] assumed.
Every derived value is computed in derive(); parts and checks read only P + derived values.

The switch is on the carrier axis. Two 1x3 headers sit on the underside, one each side, and four standoffs
sit in the quadrants. There is no printed base, no nylon spider, no plunger and no round stop. The switch's
own end of travel is the only stop for tilt and for the centre press.

The screen is glued to a separate screen carrier (the bezel). Four catalog compression springs sit at the
top, between that bezel and the main carrier, outside the glass. Each spring stands on an M2 grub screw in a
brass insert in the carrier floor. Ed dials the preload on the carrier + bezel sub-assembly, from underneath,
before the rest of the stack goes together. Nothing is added so the screws can be reached later.
Four hold-down extension springs still hold the carrier down on the balls. They do not touch the new springs.

The bezel is taller at the four spring corners than along the middle of the long sides. The middle is what
faces the knob, so the corners can clear the glass without pushing the module off the main-PCB standoffs.

Screen: DWO DO0164FMST05, 1.64" 280x456 AMOLED, mounted landscape. The FPC exit side, pin count, pitch
and pin-out were not on the pages that could be fetched — the FPC is modelled [A] and the pin-out stays open.
"""
import math
import os
import sys

P = dict(
    version="v0.4",
    # ---- placement. place_y is derived so the notched edge clears the knob ----
    knob_od_design=41.70,   # [Ed] size the plan to the v0.17 knob. The live knob-param OD is checked too
    knob_extra=0.0,         # nominal gap is the process stack itself
    pcb_edge=0.30,          # [A] a PTH pad stays this far inside the main-PCB copper edge
    rail_z=10.0,            # [A] Eurorack rail does not reach this far in front of the PCB
    # PCBWay process tolerances. A clearance is one of these, not a looser drawing gap.
    tol_sla=0.20,           # [S] SLA resin, the wide end of PCBWay's ±0.1–0.2 mm
    tol_mjf=0.25,           # [S] MJF/SLS nylon
    tol_fdm=0.20,           # [S] FDM, if a jig or a trial part is printed that way
    # ---- screen (DWO DO0164FMST05, landscape: datasheet portrait 26.74 W x 41.62 H) ----
    scr=dict(part="DWO DO0164FMST05 1.64\" 456x280 AMOLED", w=41.62, h=26.74, t=1.5, active=(35.57, 21.84),
             mass_g=8.0),  # [S] outline/thickness; mass [A] until the module is weighed
    scr_below_knob=5.0,     # [Ed] screen top is 5 mm below the knob top
    print_min=1.0,          # [S] PCBWay SLS nylon minimum wall (SLA resin is 0.8). Structural walls use this
    # FPC: exit side, width, pitch and pin-out are OPEN. Model is [A].
    fpc_w=8.0,              # [A]
    fpc_t=0.12,             # [A]
    fpc_bend=2.6,           # [A] screen +x edge to the slot centre, when the skirt allows it
    fpc_slot_l=2.3,         # [A]
    # ---- carrier / bezel ----
    car_top_below=0.3,      # [A] glass stands this far proud of the bezel top
    bz_lip=1.2,             # [Ed] bezel lip, same as the other bezel. 1.5 mm is the maximum
    bz_t=1.2,               # [Ed] bezel thickness. Same limit
    fp_t=2.5,               # [A] faceplate of the one-piece case. UTR-8100 clear resin, wall ~2.5 mm
    fp_overlap=0.90,        # [A] how far the lip covers the faceplate at rest, before the slide
    skirt_overlap=0.75,     # [A] skirt reaches this far below the plate
    # ---- return springs (Lee Spring instrument series, catalog) ----
    # 5.5 lbf/in = 0.963 N/mm. Short on purpose: the spring lives in the bezel, not in a thick floor.
    cs=dict(part="Lee Spring CI 008B 01 M", wire=0.20, od=2.24, free=3.18, rate_lb_in=5.5,
            solid=1.07, hole=2.38, rod=1.68),  # [S] music wire, tinned; hole/rod are Lee's machined sizes
    cs_turns=0.5,           # [A] nominal preload, in turns of the M2 grub, set on the sub-assembly
    # grub screw and the insert it runs in. The hex hangs under the carrier. No later access hole.
    grub=dict(part="ISO 4026 M2x3 A2 flat point", pitch=0.40, length=3.0, d=2.0, flat=1.0),  # [S] DIN 913, hex 0.9
    ins=dict(part="M2x2x3.2 brass heat-set", od=3.2, length=2.0, hole=3.0),  # [S] knurled insert, L x OD
    # ---- cup. The bore is derived: stem diameter plus one SLA tolerance per side ----
    cup_od=5.0,             # [A]
    cup_engage=1.2,         # [A]
    stem_below=1.35,        # [A] carrier underside above the stem top. The 35 mm riser fixes this slack
    # ---- switch ----
    sw=dict(part="Alps SKRHADE010", w=7.45, d=7.5, h=1.85, stem_d=3.0, stem_top=5.0, pivot=0.49, ref_h=4.3,
            tilt_travel=0.25, push_travel=0.15, tilt_f=1.2, push_f=2.35, f_tol=0.69,   # [S]
            pad_x=3.575, pad_y=1.425, pad=(1.35, 1.0), tab_y=4.05, tab=(2.0, 1.8)),    # [S] land pattern
    sw_rot=-45.0,           # [Ed] directions line up with the screen axes
    # ---- daughterboard. Outline is derived. Thickness is the fab stack, not the print minimum ----
    db_t=1.0,               # [A] 2-layer FR4
    cu_edge=0.30,           # [A] copper-to-outline, same rule as the KiCad board
    pitch=2.54,             # [S]
    # male header, plastic on the UNDERSIDE, long pin down into the socket. Samtec ships the 1x3;
    # LCSC lists the same -20 lead as TSW-103-20-T-D (C3345998, dual row) and TSW-125-20-T-S (C3334257).
    hdr=dict(part="Samtec TSW-103-20-T-S", lcsc="C3345998 lead style", mate=25.91, ins=2.54, tail=2.79, n=3),  # [S]
    # female socket on the main PCB. Same hanxia H11 family as the v0.2 2x3, split into two 1x3s.
    sock=dict(part="hanxia HX PM2.54-1x3P ZC H11", lcsc="C41427518", h=11.0, tail=3.2, n=3),  # [S]
    # hex male-female. H3 x M2 x 35 is the body between the boards; +4 is the stud through the main PCB.
    # STTZ2032 (C50377216, female-female) was out of stock. The nut under the PCB replaces the lower screw.
    standoff=dict(part="XHHD DTTZ3033", lcsc="C50377642", length=35.0, af=3.0, stud=4.0),  # [S] H3*M2*35+4 brass
    nut=dict(part="ISO 4032 M2", af=4.0, thick=1.6),  # [S] hex nut, across flats 4, height 1.6
    pad_m2=3.2,             # [A] Ø pad on the Ø2.4 M2 clearance (annular ring 0.4)
    drill_m2=2.4,           # [A]
    # ---- plate, balls, hold-down springs (kept from v0.3) ----
    ball_d=2.0,             # [Ed]
    cup_depth_frac=0.30,    # [A] cup depth / ball diameter. Shallow: a hemisphere would be ~0.5
    cup_margin=0.20,        # [A] mm the contact stays short of the rim at full slide
    seat_clear=0.05,        # [A] unused once the cups are spherical; kept so old overrides still parse
    spr_d=2.0,              # [A]
    spr_bore=3.4,           # [A]
    spr_boss=(2.6, 0.6),    # [A] hook boss under the carrier: Ø, height
    spr_f=0.5,              # [Ed] N each
    back_panel=22.65,       # [A] v0.2's derived back-panel depth. Still unknown; the length follows the hook
    # ---- check targets. derive() overwrites the ones that are process tolerances ----
    tgt=dict(stem_cup_min=0.20, gap_min=0.20, cable_min=0.25, spring_min=0.10,
             knob_min=0.50, board_min=0.25, mate_min=3.5, mate_max=6.5),
)


def _knob_data():
    """Read knob-param as data only (do not modify it). Live OD and the knob top set the plan and the stack."""
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    kp = os.path.join(here, "knob-param")
    if kp not in sys.path:
        sys.path.insert(0, kp)
    from knobparam.common import model
    D = model.derive(model.default_params())
    return dict(knob_od=float(D["knob_od"]), z_knob_top=float(D["z_knob_top"]),
                pcb_above=float(D["pcb_above"]), pcb_w=float(D["pcb_w"]), pcb_t=float(D["pcb_t"]),
                axis_bx=float(D["axis_bx"]), axis_by=float(D["axis_by"]))


def _rot(x, y, deg):
    """Same Z rotation as build123d Rot(0, 0, deg): positive is CCW, y up."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (x * c - y * s, x * s + y * c)


def _land_extent(sw, deg):
    """Radius of the rotated body and its land. The circular plate opening has to clear this."""
    pts = [_rot(sx * sw["w"] / 2, sy * sw["d"] / 2, deg) for sx in (-1, 1) for sy in (-1, 1)]
    px, py = sw["pad_x"], sw["pad_y"]
    pw, ph = sw["pad"]
    tw, th = sw["tab"]
    for x, y in ((px, py), (-px, py), (px, -py), (-px, -py), (px, 0.0), (-px, 0.0)):
        for sx in (-1, 1):
            for sy in (-1, 1):
                pts.append(_rot(x + sx * pw / 2, y + sy * ph / 2, deg))
    for y in (sw["tab_y"], -sw["tab_y"]):
        for sx in (-1, 1):
            for sy in (-1, 1):
                pts.append(_rot(sx * tw / 2, y + sy * th / 2, deg))
    return max(math.hypot(x, y) for x, y in pts)


def _place_for(x, y_edge, rc):
    """place_y that puts carrier-frame point (x, y_edge) exactly on a circle of radius rc about the knob."""
    if abs(x) >= rc - 1e-9:
        return -y_edge
    return -y_edge + math.sqrt(rc * rc - x * x)


def derive(P_):
    D = dict(P_)
    K = _knob_data()
    D.update(K)
    D["knob_od_live"] = K["knob_od"]
    sw, S, cs, grub, ins = D["sw"], D["scr"], D["cs"], D["grub"], D["ins"]
    pm = D["print_min"]
    sla, mjf = D["tol_sla"], D["tol_mjf"]
    # clearances are the process tolerances. A looser v0.3 number is tightened; a tighter one is raised.
    D["scr_clear"] = sla
    D["glue"] = sla
    D["tgt"] = dict(D["tgt"])
    D["tgt"]["stem_cup_min"] = sla
    D["tgt"]["knob_min"] = 2 * mjf          # carrier and knob are both MJF
    D["tgt"]["cable_min"] = mjf
    D["tgt"]["board_min"] = mjf
    D["tgt"]["gap_min"] = sla
    D["fpc_slot_side"] = mjf
    D["hole_extra"] = mjf
    D["wall"] = pm
    D["well_wall"] = pm
    D["car_skirt"] = pm
    D["part_gap"] = pm * 0.65               # air between neighbouring parts; keeps the two courtyards apart
    # the cup clears the stem by one SLA tolerance. Slide is that plus the tilt travel, so the switch is the stop.
    D["cup_bore"] = sw["stem_d"] + 2 * sla
    D["cup_rad_clear"] = sla
    D["slide"] = D["cup_rad_clear"] + sw["tilt_travel"]
    D["slide_need"] = D["slide"]
    D["skirt_gap"] = D["slide"] + mjf       # the skirt is still clear when the switch has already stopped
    # The bezel is a 1.2 mm lip around the glass, not a tower. Springs, the carrier and the
    # switch live under it, inside the faceplate hole.
    D["cs_bore_r"] = cs["od"] / 2 + sla
    D["pilot_r"] = D["cs_bore_r"]
    D["sh_r"] = D["cs_bore_r"]
    D["lip_r"] = D["cs_bore_r"]
    D["sock_r"] = D["cs_bore_r"]
    D["cs_outer_r"] = D["cs_bore_r"]
    D["lip_t"] = D["bz_t"]
    D["sh_t"] = 0.0
    D["up_gap"] = 0.02
    D["snap"] = D["fp_overlap"]
    D["peg_d"] = 1.80
    D["half_w"] = S["w"] / 2 + D["bz_lip"]
    D["half_h"] = S["h"] / 2 + D["bz_lip"]
    D["h_mid"] = D["half_h"]
    D["x_notch"] = D["half_w"]
    D["hole_hw"] = D["half_w"] - D["fp_overlap"]
    D["hole_hh"] = D["half_h"] - D["fp_overlap"]
    D["car_hw"] = D["hole_hw"] - D["slide"] - sla
    D["car_hh"] = D["hole_hh"] - D["slide"] - sla
    D["cs_x"] = D["car_hw"] - cs["od"] / 2 - sla
    D["cs_y"] = D["car_hh"] - cs["od"] / 2 - sla
    D["car"] = (2 * D["half_w"], 2 * D["half_h"])
    D["pocket"] = (S["w"] + 2 * D["glue"], S["h"] + 2 * D["glue"])
    D["cs_xy"] = [(sx, sy) for sx in (D["cs_x"], -D["cs_x"]) for sy in (D["cs_y"], -D["cs_y"])]
    # screen top from the knob top. The riser does not move the screen
    D["scr_top"] = D["z_knob_top"] - D["scr_below_knob"]
    # bezel is bz_t thick. Its bottom is where the old glass bottom was. The glass sits on the
    # 0.30 mm spring pads, so the glass top is 0.30 above the old 47.50 target.
    D["z_bz0"] = D["scr_top"] - S["t"]
    D["z_bz1"] = D["z_bz0"] + D["bz_t"]
    D["z_roof"] = D["z_bz0"] + 0.30
    D["z_scr0"] = D["z_roof"]
    D["scr_top"] = D["z_scr0"] + S["t"]
    so, hd, sk = D["standoff"], D["hdr"], D["sock"]
    D["z_db0"] = so["length"]
    D["z_db1"] = D["z_db0"] + D["db_t"]
    D["z_sw1"] = D["z_db1"] + sw["h"]
    D["z_stem_top"] = D["z_db1"] + sw["stem_top"]
    D["z_pivot"] = D["z_db1"] + sw["pivot"]
    D["z_ref"] = D["z_db1"] + sw["ref_h"]
    # faceplate under the lip. The bezel sits 0.02 mm above it so the faces do not fuse.
    D["z_fp1"] = D["z_bz0"] - D["up_gap"]
    D["z_fp0"] = D["z_fp1"] - D["fp_t"]
    D["fp_rebate"] = D["tol_sla"] + 0.15 + 0.20   # filled in after press_travel exists; placeholder
    # carrier floor is one SLA tolerance under the faceplate, so the module hangs below it
    D["car_floor"] = pm
    D["z_floor1"] = D["z_fp0"] - sla
    D["z_c0"] = D["z_floor1"] - D["car_floor"]
    D["stem_below"] = D["z_c0"] - D["z_stem_top"]
    D["riser_h"] = D["z_db0"]
    D["mate_air"] = D["riser_h"] - hd["ins"] - sk["h"]
    D["mate_in"] = hd["mate"] - D["mate_air"]
    D["standoff_d"] = so["af"] / math.cos(math.radians(30))
    # the 4 mm stud through the 1.6 mm board leaves 2.4 mm below it. The nut lives in that 2.4 mm.
    nt = D["nut"]
    D["stud_d"] = 2.0
    D["stud_below"] = so["stud"] - D["pcb_t"]
    D["z_stud0"] = -so["stud"]
    D["z_nut1"] = -D["pcb_t"] - 0.01
    D["z_nut0"] = D["z_nut1"] - nt["thick"]
    D["nut_past"] = D["z_nut0"] - D["z_stud0"]
    D["nut_d"] = nt["af"] / math.cos(math.radians(30))
    D["plate_t"] = pm
    D["z_plate0"] = D["z_db1"]
    D["z_plate1"] = D["z_plate0"] + D["plate_t"]
    D["z_ball"] = D["z_c0"] - D["ball_d"] / 2
    D["boss_h"] = D["z_ball"] - D["z_plate1"]
    D["seat_r"] = D["ball_d"] / 2 + D["seat_clear"]
    D["boss_r"] = D["seat_r"] + pm * 0.50
    D["z_cup0"] = D["z_stem_top"] - D["cup_engage"]
    D["z_skirt0"] = D["z_plate0"] - D["skirt_overlap"]
    D["stack_h"] = D["scr_top"]
    # press: the peg meets the stem after one SLA tolerance, then the switch travels its own 0.15 mm
    D["press_gap"] = sla
    D["press_travel"] = D["press_gap"] + sw["push_travel"]
    D["fp_rebate"] = D["press_travel"] + sla          # the lip can drop this far into the faceplate before it stops
    D["z_peg"] = D["z_stem_top"] + D["press_gap"]
    D["z_lip0"] = D["z_bz0"]
    D["z_lip1"] = D["z_bz1"]
    D["z_sh0"] = D["z_bz0"]
    D["z_sh1"] = D["z_bz0"]
    D["z_sock_top"] = D["z_bz0"]
    D["z_car1"] = D["z_floor1"]
    # nominal grub protrusion is the whole preload. The free spring just reaches the bezel.
    D["z_seat"] = D["z_roof"] - cs["free"]
    D["grub_protrude"] = D["cs_turns"] * grub["pitch"]
    D["z_tip"] = D["z_seat"] + D["grub_protrude"]
    D["z_ins0"] = D["z_seat"] - ins["length"]
    D["ins_hole"] = ins["hole"]
    D["ins_od_model"] = ins["od"] - 0.30     # slip in the model. The real insert is a heat-set interference
    D["ins_id_model"] = 1.70                 # under the M2 minor diameter, so the modelled screw does not clash
    D["grub_d_model"] = 1.50
    D["boss_d"] = ins["hole"] + 2 * pm
    D["hex_proud"] = grub["length"] - ins["length"] - D["grub_protrude"]
    # forces. 1 lbf/in = 0.175127 N/mm
    D["cs_rate"] = cs["rate_lb_in"] * 0.175127
    D["cs_n"] = 4
    nrate = D["cs_n"] * D["cs_rate"]
    D["cs_defl_preload"] = D["grub_protrude"]
    D["cs_defl_press"] = D["cs_defl_preload"] + D["press_travel"]
    D["cs_f_preload"] = nrate * D["cs_defl_preload"]
    D["cs_f_press"] = nrate * D["cs_defl_press"]
    D["cs_f_turn"] = nrate * grub["pitch"]
    D["cs_f_turn_1"] = D["cs_rate"] * grub["pitch"]
    D["scr_weight"] = S["mass_g"] * 9.81e-3
    D["cs_solid_room"] = (cs["free"] - cs["solid"]) - D["cs_defl_press"]
    lo = sw["push_f"] - sw["f_tol"]
    hi = sw["push_f"] + sw["f_tol"]
    D["push_lo"] = lo
    D["push_hi"] = hi

    def _turns_at(force):
        return (force / nrate - D["press_travel"]) / grub["pitch"]

    # useful window: press force inside the centre-push band, preload above 5x the screen weight,
    # and preload still under the bottom of that band so rest is not already a click
    D["turns_lo"] = max(_turns_at(lo), 5 * D["scr_weight"] / D["cs_f_turn"])
    D["turns_hi"] = min(_turns_at(hi), lo / D["cs_f_turn"])
    D["turns_hex"] = (grub["length"] - ins["length"] - 0.40) / grub["pitch"]
    D["press_f"] = D["cs_f_press"]
    # where the carrier sits. The knob sees the notched middle, not the tall corners
    design_od = max(D["knob_od_design"], D["knob_od_live"])
    D["knob_od_used"] = design_od
    rc = design_od / 2 + D["tgt"]["knob_min"] + D["knob_extra"] + D["slide"]
    D["knob_rc"] = rc
    silhouette = [(0.0, -D["half_h"]), (D["half_w"], -D["half_h"])]
    D["place_y"] = max(_place_for(x, y, rc) for x, y in silhouette)
    D["y_pcb"] = D["pcb_above"] - D["place_y"]
    # switch on the carrier axis. Land extent drives the plate opening and the board
    D["sw_xy"] = (0.0, 0.0)
    D["sw_ext"] = _land_extent(sw, D["sw_rot"])
    D["body_r"] = math.hypot(sw["w"], sw["d"]) / 2
    D["cut_r"] = D["sw_ext"] + D["part_gap"]
    n, pitch = hd["n"], D["pitch"]
    D["hdr_len"] = n * pitch
    D["hdr_wid"] = pitch
    D["hx"] = D["sw_ext"] + D["part_gap"] + D["hdr_len"] / 2
    inset = D["pad_m2"] / 2 + D["cu_edge"]
    D["db_half_w"] = D["hx"] + D["hdr_len"] / 2 + D["standoff_d"] / 2 + D["part_gap"]
    D["db_half_h"] = D["cut_r"] + pm
    # no round stop: the board is symmetric. The v0.3 -y tab existed only for that stop
    D["board_x0"], D["board_x1"] = -D["db_half_w"], D["db_half_w"]
    D["board_y0"], D["board_y1"] = -D["db_half_h"], D["db_half_h"]
    D["db"] = (D["board_x1"] - D["board_x0"], D["board_y1"] - D["board_y0"], D["db_t"])
    D["db_xy"] = (0.0, 0.0)
    D["sx"] = D["db_half_w"] - inset
    sy_corner = D["db_half_h"] - inset
    sy_pad = D["y_pcb"] - D["pcb_edge"] - D["pad_m2"] / 2
    # the nut is wider than the pad, so it sets how close the screw can sit to the PCB edge
    sy_nut = D["y_pcb"] - D["pcb_edge"] - D["nut"]["af"] / 2
    D["sy"] = min(sy_corner, sy_pad, sy_nut)
    D["sy_corner"] = sy_corner
    D["sy_pad"] = sy_pad
    D["sy_nut"] = sy_nut
    D["standoff_xy"] = [(sx, sy) for sx in (D["sx"], -D["sx"]) for sy in (D["sy"], -D["sy"])]
    D["hdr_xy"] = [(D["hx"], 0.0), (-D["hx"], 0.0)]
    # shallow spherical cups, same above and below. The ratio is the smallest cup radius
    # that still keeps cup_margin at the full slide. A ratio near 1.05 only allows ~0.15 mm.
    Rb = D["ball_d"] / 2.0
    cd = D["cup_depth_frac"] * D["ball_d"]
    s_need = D["slide"] + D["cup_margin"]

    def _smax(Rc):
        a2 = 2.0 * Rc * cd - cd * cd
        if Rc <= Rb or a2 <= 0.0:
            return 0.0
        return 2.0 * (Rc - Rb) * math.sqrt(a2) / Rc

    lo, hi = Rb * 1.02, Rb * 4.0
    for _ in range(48):
        mid = 0.5 * (lo + hi)
        if _smax(mid) < s_need:
            lo = mid
        else:
            hi = mid
    D["cup_r"] = hi
    D["cup_ratio"] = hi / Rb
    D["cup_depth"] = cd
    D["cup_rim_r"] = math.sqrt(max(2.0 * hi * cd - cd * cd, 0.0))
    D["cup_s_max"] = _smax(hi)
    D["cup_travel_margin"] = D["cup_s_max"] - D["slide"]
    D["z_ball"] = D["z_c0"] - Rb
    D["z_rim_lo"] = D["z_ball"] - (Rb - cd)
    D["z_rim_hi"] = D["z_ball"] + (Rb - cd)
    D["z_sc_lo"] = D["z_rim_lo"] + (hi - cd)
    D["z_sc_hi"] = D["z_rim_hi"] - (hi - cd)
    D["boss_r"] = D["cup_rim_r"] + pm
    D["boss_h"] = D["z_rim_lo"] - D["z_plate1"]
    D["by"] = D["db_half_h"] - D["boss_r"] - D["part_gap"]
    need = D["cut_r"] + D["boss_r"] + D["part_gap"]
    bx_min = math.sqrt(max(need ** 2 - D["by"] ** 2, 0.0))
    bx_max = D["sx"] - D["standoff_d"] / 2 - D["part_gap"] - D["boss_r"]
    D["bx"] = bx_max          # as far toward the plate corners as the standoffs allow
    D["balls"] = [(bx, by) for bx in (D["bx"], -D["bx"]) for by in (D["by"], -D["by"])]
    # hold-downs stay inboard of the FPC drop and under the bezel. The old pair at x=±22.5
    # stood outside the lip; that is the yellow tube Ed circled.
    D["spr_x_raw"] = D["car_hw"] - D["spr_boss"][0] / 2 - sla
    D["spr_x"] = 6.5
    D["spr_y"] = min(3.5, D["y_pcb"] - D["pcb_edge"] - D["spr_bore"] / 2)
    D["springs"] = [(sx, sy) for sx in (D["spr_x"], -D["spr_x"]) for sy in (D["spr_y"], -D["spr_y"])]
    edge = S["w"] / 2
    skirt_outer = D["db_half_w"] + D["skirt_gap"] + D["car_skirt"]
    D["fpc_x"] = max(edge - D["fpc_bend"], skirt_outer + D["tgt"]["cable_min"] + D["fpc_t"] / 2 + sla)
    D["slot_x"] = (D["fpc_x"] - D["fpc_slot_l"] / 2, D["fpc_x"] + D["fpc_slot_l"] / 2)
    D["slot_hy"] = D["fpc_w"] / 2 + D["fpc_slot_side"]
    D["hole_x0"] = D["slot_x"][0] - D["slide"] - D["hole_extra"]
    D["hole_x1"] = D["slot_x"][1] + D["slide"] + D["hole_extra"]
    D["hole_hy"] = D["slot_hy"] + D["slide"] + D["hole_extra"]
    D["spr_z1"] = D["z_c0"] - D["spr_boss"][1]
    D["spr_len"] = D["spr_z1"] + D["pcb_t"] + D["back_panel"]
    D["board_xy"] = (D["axis_bx"], D["axis_by"] - D["place_y"])
    return D


def board_xy(D, x, y):
    """Carrier-frame point → main-PCB coordinates (origin = panel top-left, y down)."""
    return (D["axis_bx"] + x, D["axis_by"] - D["place_y"] - y)
