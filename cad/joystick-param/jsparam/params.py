"""Top-screen joystick stack v0.3 — params + derive.

Local frame: origin = carrier centre on the MAIN PCB FRONT (z = 0), +x right along the panel width, +y up the panel
(toward the panel top), +z out of the panel. Placement in the knob-param frame (dial axis = 0,0): (0, place_y).
Tags: [Ed] Ed's decision, [S] datasheet, [L] panel layout, [K] main-PCB KiCad, [A] assumed.
Every derived value is computed in derive(); parts and checks read only P + derived values.

The switch is on the carrier axis. Two 1x3 headers sit on the underside, one each side, and four standoffs
sit in the quadrants. The printed base enclosure is gone: a flat plate glued on the daughterboard carries
the ball seats and the round stop. The carrier floor is only the slack the 35 mm riser does not take.

Screen: DWO DO0164FMST05, 1.64" 280x456 AMOLED, mounted landscape. The FPC exit side, pin count, pitch
and pin-out were not on the pages that could be fetched — the FPC is modelled [A] and the pin-out stays open.
"""
import math
import os
import sys

P = dict(
    version="v0.3",
    # ---- placement. place_y is derived so the carrier clears the knob ----
    knob_od_design=41.70,   # [Ed] size the plan to the v0.17 knob. The live knob-param OD is checked too
    knob_extra=0.05,        # [A] a hair over the 0.55 mm target so the check is not sitting on the float
    pcb_edge=0.30,          # [A] a PTH pad stays this far inside the main-PCB copper edge
    rail_z=10.0,            # [A] Eurorack rail does not reach this far in front of the PCB
    # ---- screen (DWO DO0164FMST05, landscape: datasheet portrait 26.74 W x 41.62 H) ----
    scr=dict(part="DWO DO0164FMST05 1.64\" 456x280 AMOLED", w=41.62, h=26.74, t=1.5, active=(35.57, 21.84)),  # [S]
    scr_below_knob=5.0,     # [Ed] screen top is 5 mm below the knob top
    scr_clear=0.20,         # [A] air between the glass and the pocket wall
    print_min=1.0,          # [S] PCBWay SLS nylon minimum wall (SLA resin is 0.8). Structural walls use this
    # FPC: exit side, width, pitch and pin-out are OPEN. Model is [A].
    fpc_w=8.0,              # [A]
    fpc_t=0.12,             # [A]
    fpc_bend=2.6,           # [A] screen +x edge to the slot centre
    fpc_slot_l=2.3,         # [A]
    fpc_slot_side=1.05,     # [A] slot clearance each side of the FPC in y
    # ---- carrier ----
    car_top_below=0.3,      # [A] carrier wall top below the screen glass top. Ratio of the screen thickness would move the glass
    slide=0.40,             # [Ed] round-stop radius. Travel is a circle of Ø0.80
    skirt_gap=0.75,         # [A] rectangular skirt clearance. Larger than `slide`, so it only stops rotation
    skirt_overlap=0.75,     # [A] skirt reaches this far below the plate
    # ---- spider (unchanged flexure: same pad, arms, thickness → same ~0.74 N) ----
    sp_t=0.6,               # [A] flexure, not a wall. Kept so the press force stays the v0.1 / v0.2 number
    sp_gap=0.40,            # [Ed] 0.3-0.5 free travel
    sp_land=0.6,            # [A]
    sp_frame=1.2,           # [A]
    sp_pad=(18.0, 8.0),     # [A] same as v0.1 so the arm length (and the force) stays put
    sp_arm_w=1.2,           # [A]
    sp_E=1700.0,            # [S] PA12 MJF flexural modulus, MPa (approx)
    sp_hy=7.8,              # [A] flexure half-height, same as v0.1
    plunger_d=2.8,          # [A]
    plunger_gap=0.05,       # [A]
    # ---- cup ----
    cup_bore=3.15,          # [S/A] Ø3.1-3.2 over the Ø3 stem
    cup_od=5.0,             # [A]
    cup_engage=1.2,         # [A]
    stem_below=1.35,        # [A] carrier underside above the stem top (same stack as v0.1 / v0.2)
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
    # hex F-F. Across-flats is the "H3" in the XHHD title. Length is the riser.
    standoff=dict(part="XHHD STTZ2032", lcsc="C50377216", length=35.0, af=3.0),  # [S] H3 x M2 x 35 brass F-F
    pad_m2=3.2,             # [A] Ø pad on the Ø2.4 M2 clearance (annular ring 0.4)
    drill_m2=2.4,           # [A]
    # ---- plate, balls, stop, springs ----
    ball_d=2.0,             # [Ed]
    seat_clear=0.05,        # [A]
    spr_d=2.0,              # [A]
    spr_bore=3.4,           # [A]
    spr_boss=(2.6, 0.6),    # [A] hook boss under the carrier: Ø, height
    spr_f=0.5,              # [Ed] N each
    back_panel=22.65,       # [A] v0.2's derived back-panel depth. Still unknown; the length follows the hook
    hole_extra=0.25,        # [A] PCB slot round the carrier slot, beyond the round-stop travel
    # ---- check targets ----
    tgt=dict(stem_cup_min=0.05, gap_min=0.3, cable_min=0.5, spring_min=0.1, overtravel_max=0.15,
             knob_min=0.55, board_min=0.3, mate_min=3.5, mate_max=6.5),
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


def derive(P_):
    D = dict(P_)
    K = _knob_data()
    D.update(K)
    D["knob_od_live"] = K["knob_od"]
    sw, S = D["sw"], D["scr"]
    pm = D["print_min"]
    # the screen-well wall is the print minimum; scr_clear is the air inside that wall
    D["wall"] = pm + D["scr_clear"]
    D["car_skirt"] = pm
    D["part_gap"] = pm * 0.65          # air between neighbouring parts; also keeps the two courtyards from overlapping
    D["car"] = (S["w"] + 2 * D["wall"], S["h"] + 2 * D["wall"])
    D["pocket"] = (S["w"] + 2 * D["scr_clear"], S["h"] + 2 * D["scr_clear"])
    cw, ch = D["car"]
    # screen top, then the spider, from the knob top. The riser does not move the screen
    D["scr_top"] = D["z_knob_top"] - D["scr_below_knob"]
    D["z_scr0"] = D["scr_top"] - S["t"]
    D["z_sp1"] = D["z_scr0"] - D["sp_land"]
    D["z_sp0"] = D["z_sp1"] - D["sp_t"]
    D["z_floor1"] = D["z_sp0"] - D["sp_gap"]
    # the standoff length is the riser. The header and the socket have to mate across it
    so, hd, sk = D["standoff"], D["hdr"], D["sock"]
    D["z_db0"] = so["length"]
    D["z_db1"] = D["z_db0"] + D["db_t"]
    D["z_sw1"] = D["z_db1"] + sw["h"]
    D["z_stem_top"] = D["z_db1"] + sw["stem_top"]
    D["z_pivot"] = D["z_db1"] + sw["pivot"]
    D["z_ref"] = D["z_db1"] + sw["ref_h"]
    D["z_c0"] = D["z_stem_top"] + D["stem_below"]
    D["car_floor"] = D["z_floor1"] - D["z_c0"]
    D["riser_h"] = D["z_db0"]
    D["mate_air"] = D["riser_h"] - hd["ins"] - sk["h"]
    D["mate_in"] = hd["mate"] - D["mate_air"]
    D["standoff_d"] = so["af"] / math.cos(math.radians(30))   # hex across corners, from the across-flats
    D["plate_t"] = pm
    D["z_plate0"] = D["z_db1"]
    D["z_plate1"] = D["z_plate0"] + D["plate_t"]
    D["z_ball"] = D["z_c0"] - D["ball_d"] / 2
    D["boss_h"] = D["z_ball"] - D["z_plate1"]
    D["seat_r"] = D["ball_d"] / 2 + D["seat_clear"]
    D["boss_r"] = D["seat_r"] + pm * 0.50
    # stop bore leaves a print-minimum roof in the floor. Boss diameter follows the standoff across-flats
    D["stop_d"] = so["af"]
    D["stop_bore"] = D["stop_d"] + 2 * D["slide"]
    D["stop_engage"] = D["car_floor"] - pm
    D["z_car1"] = D["scr_top"] - D["car_top_below"]
    D["z_cup0"] = D["z_stem_top"] - D["cup_engage"]
    D["z_plunger0"] = D["z_stem_top"] + D["plunger_gap"]
    D["z_skirt0"] = D["z_plate0"] - D["skirt_overlap"]
    D["stack_h"] = D["scr_top"]
    # where the carrier sits: clear the DESIGN knob by >= 0.55 at full slide
    design_od = max(D["knob_od_design"], D["knob_od_live"])
    design_r = design_od / 2
    D["knob_od_used"] = design_od
    D["place_y"] = design_r + D["tgt"]["knob_min"] + D["knob_extra"] + D["slide"] + ch / 2
    D["y_pcb"] = D["pcb_above"] - D["place_y"]
    # switch on the carrier axis. Land extent drives the plate opening and the board
    D["sw_xy"] = (0.0, 0.0)
    D["sw_ext"] = _land_extent(sw, D["sw_rot"])
    D["body_r"] = math.hypot(sw["w"], sw["d"]) / 2
    D["cut_r"] = D["sw_ext"] + D["part_gap"]
    # 1x3 headers on the X axis, one each side, pins along X. Plastic is one pitch wide and n pitches long
    n, pitch = hd["n"], D["pitch"]
    D["hdr_len"] = n * pitch
    D["hdr_wid"] = pitch
    D["hx"] = D["sw_ext"] + D["part_gap"] + D["hdr_len"] / 2
    # board half-width: header body, then the standoff radius and the same part gap
    inset = D["pad_m2"] / 2 + D["cu_edge"]
    D["db_half_w"] = D["hx"] + D["hdr_len"] / 2 + D["standoff_d"] / 2 + D["part_gap"]
    # +y half-height: a print-minimum frame outside the switch opening. The opening is widest on the axes
    D["db_half_h"] = D["cut_r"] + pm
    # the round stop is one boss on the -y centreline, so the board grows that way (toward the knob, on the PCB)
    D["stop_xy"] = (0.0, -(D["cut_r"] + D["part_gap"] + D["stop_d"] / 2))
    D["board_x0"], D["board_x1"] = -D["db_half_w"], D["db_half_w"]
    D["board_y1"] = D["db_half_h"]
    D["board_y0"] = D["stop_xy"][1] - D["stop_d"] / 2 - pm
    D["db"] = (D["board_x1"] - D["board_x0"], D["board_y1"] - D["board_y0"], D["db_t"])
    D["db_xy"] = (0.0, (D["board_y0"] + D["board_y1"]) / 2)
    # four standoffs, symmetric about the switch. Y is whatever the main PCB can still screw into
    D["sx"] = D["db_half_w"] - inset
    sy_corner = D["db_half_h"] - inset
    sy_pcb = D["y_pcb"] - D["pcb_edge"] - D["pad_m2"] / 2
    D["sy"] = min(sy_corner, sy_pcb)
    D["sy_corner"] = sy_corner
    D["standoff_xy"] = [(sx, sy) for sx in (D["sx"], -D["sx"]) for sy in (D["sy"], -D["sy"])]
    D["hdr_xy"] = [(D["hx"], 0.0), (-D["hx"], 0.0)]
    # balls in the four quadrants, outside the switch opening, inboard of the standoffs
    D["by"] = D["db_half_h"] - D["boss_r"] - D["part_gap"]
    need = D["cut_r"] + D["boss_r"] + D["part_gap"]
    bx_min = math.sqrt(max(need ** 2 - D["by"] ** 2, 0.0))
    bx_max = D["sx"] - D["standoff_d"] / 2 - D["part_gap"] - D["boss_r"]
    D["bx"] = min(max(bx_min, (bx_min + bx_max) / 2), bx_max)
    D["balls"] = [(bx, by) for bx in (D["bx"], -D["bx"]) for by in (D["by"], -D["by"])]
    # springs out near the carrier sides, clear of the FPC drop on +x, and on the main PCB
    D["spr_x"] = cw / 2 - D["spr_boss"][0] / 2 - D["scr_clear"]
    D["spr_y"] = min(D["sy"], D["y_pcb"] - D["pcb_edge"] - D["spr_bore"] / 2)
    D["springs"] = [(sx, sy) for sx in (D["spr_x"], -D["spr_x"]) for sy in (D["spr_y"], -D["spr_y"])]
    # spider flexure, same arm run as v0.1 (the force depends on it), centred, clear of the FPC slot
    D["sp_x"] = (-15.5, 15.5)
    D["sp_in_x"] = (D["sp_x"][0] + D["sp_frame"], D["sp_x"][1] - D["sp_frame"])
    D["sp_in_hy"] = D["sp_hy"] - D["sp_frame"]
    pw, ph = D["sp_pad"]
    D["pad_x"] = (D["sw_xy"][0] - pw / 2, D["sw_xy"][0] + pw / 2)
    edge = S["w"] / 2
    skirt_outer = D["db_half_w"] + D["skirt_gap"] + D["car_skirt"]
    # the drop has to clear the skirt by the cable minimum, and still leave bend room under the glass
    D["fpc_x"] = max(edge - D["fpc_bend"], skirt_outer + D["tgt"]["cable_min"] + D["fpc_t"] / 2 + D["scr_clear"])
    D["slot_x"] = (D["fpc_x"] - D["fpc_slot_l"] / 2, D["fpc_x"] + D["fpc_slot_l"] / 2)
    D["slot_hy"] = D["fpc_w"] / 2 + D["fpc_slot_side"]
    D["hole_x0"] = D["slot_x"][0] - D["slide"] - D["hole_extra"]
    D["hole_x1"] = D["slot_x"][1] + D["slide"] + D["hole_extra"]
    D["hole_hy"] = D["slot_hy"] + D["slide"] + D["hole_extra"]
    I = D["sp_arm_w"] * D["sp_t"] ** 3 / 12
    L = D["arm_L"] = (pw / 2 - 0.6) - 0.6
    D["sp_k"] = 4 * 12 * D["sp_E"] * I / L ** 3
    D["sp_defl_click"] = D["plunger_gap"] + sw["push_travel"]
    D["sp_f_click"] = D["sp_k"] * D["sp_defl_click"]
    D["press_f"] = sw["push_f"] + D["sp_f_click"]
    D["cup_rad_clear"] = (D["cup_bore"] - sw["stem_d"]) / 2
    D["slide_need"] = D["cup_rad_clear"] + sw["tilt_travel"]
    D["spr_z1"] = D["z_c0"] - D["spr_boss"][1]
    D["spr_len"] = D["spr_z1"] + D["pcb_t"] + D["back_panel"]
    D["board_xy"] = (D["axis_bx"], D["axis_by"] - D["place_y"])
    D["well_wall"] = D["wall"] - D["scr_clear"]
    return D


def board_xy(D, x, y):
    """Carrier-frame point → main-PCB coordinates (origin = panel top-left, y down)."""
    return (D["axis_bx"] + x, D["axis_by"] - D["place_y"] - y)
