"""Top-screen joystick stack v0.2 — params + derive.

Local frame: origin = carrier centre on the MAIN PCB FRONT (z = 0), +x right along the panel width, +y up the panel
(toward the panel top), +z out of the panel. Placement in the knob-param frame (dial axis = 0,0): (0, place_y).
Tags: [Ed] Ed's decision, [S] datasheet, [L] panel layout, [K] main-PCB KiCad, [A] assumed.
Every derived value is computed in derive(); parts and checks read only P + derived values.

Screen: DWO DO0164FMST05, 1.64" 280x456 AMOLED, mounted landscape. Outline, thickness and active area are the
datasheet figures (REV 0.0, confirmed from the published mechanical table). The FPC exit side, pin count, pitch
and pin-out were not on the pages that could be fetched — the FPC is modelled [A] and the pin-out stays open.
"""
import math
import os
import sys

P = dict(
    version="v0.2",
    # ---- placement. place_y is derived so the carrier clears the knob; these are the design targets ----
    knob_od_design=41.70,   # [Ed] size the plan to the v0.17 knob (parallel agent, ~Ø41.7). The live knob-param OD is checked too
    knob_extra=0.05,        # [A] a hair over the 0.5 mm target so the check is not sitting on the float
    pcb_edge=0.40,          # [A] base / holes stay this far inside the main-PCB edge
    rail_z=10.0,            # [A] Eurorack rail does not reach this far in front of the PCB; the carrier overhang must clear it
    # ---- screen (DWO DO0164FMST05, landscape: datasheet portrait 26.74 W x 41.62 H) ----
    scr=dict(part="DWO DO0164FMST05 1.64\" 456x280 AMOLED", w=41.62, h=26.74, t=1.5, active=(35.57, 21.84)),  # [S] no cover lens
    scr_below_knob=5.0,     # [Ed] screen top is 5 mm below the knob top
    wall=1.0,               # [Ed] ~1 mm carrier wall around the screen outline
    scr_clear=0.20,         # [A] of that wall, air between the glass and the pocket
    # FPC: exit side, width, pitch and pin-out are OPEN (2D drawing not retrieved). Model is [A].
    fpc_w=8.0,              # [A] width of the drop. Open until the drawing confirms the tail
    fpc_t=0.12,             # [A]
    fpc_bend=2.6,           # [A] screen +x edge to the slot centre: room for the FPC to turn down under the glass
    fpc_slot_l=2.3,         # [A] slot length along x
    fpc_slot_side=1.05,     # [A] slot clearance each side of the FPC in y
    # ---- carrier ----
    car_skirt=0.8,          # [A] material outside the anti-rotation skirt
    car_top_below=0.3,      # [A] carrier wall top below the screen glass top
    slide=0.40,             # [Ed] round-stop radius. Travel is a circle of Ø0.80, the same in every direction
    skirt_gap=0.75,         # [A] rectangular skirt clearance. Larger than `slide`, so it only stops rotation
    skirt_overlap=0.75,     # [A] skirt reaches this far below the base top
    # ---- spider (unchanged flexure: same pad, arms, thickness → same ~0.74 N) ----
    sp_t=0.6,               # [A]
    sp_gap=0.40,            # [Ed] 0.3-0.5 free travel; the pad never bottoms
    sp_land=0.6,            # [A]
    sp_frame=1.2,           # [A]
    sp_pad=(18.0, 8.0),     # [A] flexure pad, same as v0.1 so the arm length (and the force) stays put
    sp_arm_w=1.2,           # [A]
    sp_E=1700.0,            # [S] PA12 MJF flexural modulus, MPa (approx)
    sp_hy=7.8,              # [A] flexure half-height, same as v0.1 (the screen pocket is larger; this does not grow)
    plunger_d=2.8,          # [A]
    plunger_gap=0.05,       # [A]
    # ---- cup ----
    cup_bore=3.15,          # [S/A] Ø3.1-3.2 over the Ø3 stem
    cup_od=5.0,             # [A]
    cup_engage=1.2,         # [A]
    stem_below=1.35,        # [A] carrier underside above the stem top (same stack as v0.1)
    # ---- switch ----
    sw=dict(part="Alps SKRHADE010", w=7.45, d=7.5, h=1.85, stem_d=3.0, stem_top=5.0, pivot=0.49, ref_h=4.3,
            tilt_travel=0.25, push_travel=0.15, tilt_f=1.2, push_f=2.35, f_tol=0.69),  # [S]
    sw_rot=-45.0,           # [Ed] directions line up with the screen axes; mapping confirmed at first power
    sw_xy=(-3.0, -1.2),     # [A] under the screen, 1.2 mm toward the knob so the 45° body stays inside the base cavity
    # ---- daughterboard + plug-in riser ----
    # Socket height 11 mm matches the M2x11 brass standoff. The deep carrier takes the rest of the stack.
    db=(19.2, 13.8, 1.0),   # [A] w, h, t
    db_xy=(0.2, -3.2),      # [A] board centre in the carrier frame (the board sits in the part of the base that is on the PCB)
    hdr_xy=(5.9, -1.0),     # [A] 2x3 header centre
    hdr_body=(5.08, 7.62, 2.5),  # [S] male header plastic (LXWCONN 254PZ-2x3P-V, mating pin 6 mm)
    sock=(5.08, 7.62, 11.0),     # [S] hanxia HX PM2.54-2x3P ZC H11, insulation height 11 mm = the riser
    post_d=4.0,             # [A] printed post under the switch
    standoff_d=3.5,         # [S/A] XHHD STTZ2008 hex H3 across corners (~3.5). M2 x 11 female-female brass
    standoff_xy=((-7.5, -8.0), (7.2, -7.6)),  # [A] MH1 is in the corner, clear of the switch courtyard
    # ---- base ----
    base_wall=1.2,          # [A]
    base_floor=1.0,         # [A]
    base_top_t=1.75,        # [A]
    win_clear=0.40,         # [A] top-plate window round the daughterboard
    pin=(1.2, 1.0),         # [A] locating pins Ø, length into the PCB
    pin_xy=((15.5, 1), (-16.2, 1), (15.5, -1), (-16.2, -1)),  # y is a sign: + toward base_y1, - toward base_y0; real y derived
    # ---- balls: four Ø2 stainless (Ed confirmed the Ø2 stainless ball; four seats so the carrier cannot tilt) ----
    ball_d=2.0,             # [Ed]
    ball_x=(16.4, -11.2),   # [A] +x pair, -x pair (the -x side leaves room for the round stop)
    seat_clear=0.05,        # [A]
    # ---- round stop ----
    stop_d=4.6,             # [A] boss diameter. Bore = stop_d + 2*slide, so the travel is Ø(2*slide)
    stop_xy=(-17.4, -2.2),  # [A] on the base top, clear of the cup, the springs and the window
    # ---- hold-down springs ----
    spr_d=2.0,              # [A]
    spr_x=(13.0, -14.2),    # [A] +x pair, -x pair, inward or outward of the balls
    spr_bore=3.4,           # [A]
    spr_boss=(2.6, 0.6),    # [A] hook boss under the carrier: Ø, height. A side slot lets the eye slide off
    spr_f=0.5,              # [Ed] N each
    spr_len_target=42.0,    # [Ed/A] installed length to the back panel. The back-panel depth is still unknown
    # ---- FPC hole growth ----
    hole_extra=0.25,        # [A] base / PCB slot round the carrier slot, beyond the round-stop travel
    # ---- check targets ----
    tgt=dict(stem_cup_min=0.05, gap_min=0.3, cable_min=0.5, spring_min=0.1, overtravel_max=0.15,
             knob_min=0.5, board_min=0.3),
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


def derive(P_):
    D = dict(P_)
    K = _knob_data()
    D.update(K)
    D["knob_od_live"] = K["knob_od"]
    sw, S = D["sw"], D["scr"]
    # carrier outline: 1 mm wall all round the screen. The screen stays centred on the carrier
    D["car"] = (S["w"] + 2 * D["wall"], S["h"] + 2 * D["wall"])
    D["pocket"] = (S["w"] + 2 * D["scr_clear"], S["h"] + 2 * D["scr_clear"])
    cw, ch = D["car"]
    # screen top, then the spider, from the knob top. The riser does not move the screen
    D["scr_top"] = D["z_knob_top"] - D["scr_below_knob"]
    D["z_scr0"] = D["scr_top"] - S["t"]
    D["z_sp1"] = D["z_scr0"] - D["sp_land"]
    D["z_sp0"] = D["z_sp1"] - D["sp_t"]
    D["z_floor1"] = D["z_sp0"] - D["sp_gap"]
    # riser = socket height. The carrier floor thickens so the stem still meets the cup
    D["z_db0"] = D["sock"][2]
    D["z_db1"] = D["z_db0"] + D["db"][2]
    D["z_sw1"] = D["z_db1"] + sw["h"]
    D["z_stem_top"] = D["z_db1"] + sw["stem_top"]
    D["z_pivot"] = D["z_db1"] + sw["pivot"]
    D["z_ref"] = D["z_db1"] + sw["ref_h"]
    D["z_c0"] = D["z_stem_top"] + D["stem_below"]
    D["car_floor"] = D["z_floor1"] - D["z_c0"]
    D["z_ball"] = D["z_c0"] - D["ball_d"] / 2
    D["z_base1"] = D["z_ball"]
    D["z_base_top0"] = D["z_base1"] - D["base_top_t"]
    D["z_skirt0"] = D["z_base1"] - D["skirt_overlap"]
    D["z_car1"] = D["scr_top"] - D["car_top_below"]
    D["z_cup0"] = D["z_stem_top"] - D["cup_engage"]
    D["z_plunger0"] = D["z_stem_top"] + D["plunger_gap"]
    D["riser_h"] = D["z_db0"]
    D["stack_h"] = D["scr_top"]
    # where the carrier sits: clear the DESIGN knob (the larger of the live OD and Ø41.7) by >= 0.5 at full slide
    design_od = max(D["knob_od_design"], D["knob_od_live"])
    design_r = design_od / 2
    D["knob_od_used"] = design_od
    D["place_y"] = design_r + D["tgt"]["knob_min"] + D["knob_extra"] + D["slide"] + ch / 2
    # base: inside the carrier skirt, inside the PCB, and clear of the knob. Offset toward the knob (-y)
    # so the screen can hang past the PCB top edge (the carrier underside is above the rail)
    g, sk = D["skirt_gap"], D["car_skirt"]
    lim_x = cw / 2 - sk - g
    lim_y = ch / 2 - sk - g
    y_pcb = D["pcb_above"] - D["place_y"] - D["pcb_edge"]
    y_knob = -(D["place_y"] - design_r - D["tgt"]["knob_min"] - D["knob_extra"])
    D["base_x0"], D["base_x1"] = -lim_x, lim_x
    D["base_y0"] = max(-lim_y, y_knob)
    D["base_y1"] = min(lim_y, y_pcb)
    D["base_w"] = D["base_x1"] - D["base_x0"]
    D["base_h"] = D["base_y1"] - D["base_y0"]
    D["base_dy"] = (D["base_y0"] + D["base_y1"]) / 2
    # cavity and window
    w = D["base_wall"]
    D["cav"] = (D["base_x0"] + w, D["base_x1"] - w, D["base_y0"] + w, D["base_y1"] - w)
    dx, dy = D["db_xy"]; dw, dh, _ = D["db"]
    c = D["win_clear"]
    D["win"] = (dx - dw / 2 - c, dx + dw / 2 + c, dy - dh / 2 - c, dy + dh / 2 + c)
    # balls, springs, pins — y from the base edges, x chosen to clear the window, the slot and the stop
    by1 = D["base_y1"] - 2.5
    by0 = D["base_y0"] + 2.8
    bx_p, bx_m = D["ball_x"]
    # the +y/+x ball sits inboard of the FPC slot; the -y/+x ball can stay out near the corner
    D["balls"] = [(14.8, by1), (bx_m, by1), (bx_p, by0), (bx_m, by0)]
    sx_p, sx_m = D["spr_x"]
    D["springs"] = [(12.4, by1 - 2.5), (sx_m, min(by1, D["base_y1"] - 2.5)),
                    (sx_p, by0 + 1.7), (sx_m, by0 + 1.6)]
    pin_y_hi = D["base_y1"] - 1.7
    pin_y_lo = D["base_y0"] + 1.7
    D["pins"] = []
    for x, s in D["pin_xy"]:
        D["pins"].append((x, pin_y_hi if s > 0 else pin_y_lo))
    # spider flexure, same arm run as v0.1, kept clear of the FPC slot
    D["sp_x"] = (-15.5, 15.6)
    D["sp_in_x"] = (D["sp_x"][0] + D["sp_frame"], D["sp_x"][1] - D["sp_frame"])
    D["sp_in_hy"] = D["sp_hy"] - D["sp_frame"]
    pw, ph = D["sp_pad"]
    D["pad_x"] = (D["sw_xy"][0] - pw / 2, D["sw_xy"][0] + pw / 2)
    # FPC slot under the glass, inboard of the +x edge by fpc_bend
    edge = S["w"] / 2
    cx = edge - D["fpc_bend"]
    D["fpc_x"] = cx
    D["slot_x"] = (cx - D["fpc_slot_l"] / 2, cx + D["fpc_slot_l"] / 2)
    D["slot_hy"] = D["fpc_w"] / 2 + D["fpc_slot_side"]
    D["hole_x0"] = D["slot_x"][0] - D["slide"] - D["hole_extra"]
    D["hole_x1"] = D["slot_x"][1] + D["slide"] + D["hole_extra"]
    D["hole_hy"] = D["slot_hy"] + D["slide"] + D["hole_extra"]
    # spider stiffness — same formula and the same arm as v0.1
    I = D["sp_arm_w"] * D["sp_t"] ** 3 / 12
    L = D["arm_L"] = (pw / 2 - 0.6) - 0.6
    D["sp_k"] = 4 * 12 * D["sp_E"] * I / L ** 3
    D["sp_defl_click"] = D["plunger_gap"] + sw["push_travel"]
    D["sp_f_click"] = D["sp_k"] * D["sp_defl_click"]
    D["press_f"] = sw["push_f"] + D["sp_f_click"]
    D["cup_rad_clear"] = (D["cup_bore"] - sw["stem_d"]) / 2
    D["slide_need"] = D["cup_rad_clear"] + sw["tilt_travel"]
    D["stop_bore"] = D["stop_d"] + 2 * D["slide"]
    # springs: length target 42 mm. back_panel is whatever is left, and it is still [A]
    D["spr_z1"] = D["z_c0"] - D["spr_boss"][1]
    D["back_panel"] = D["spr_len_target"] - D["spr_z1"] - D["pcb_t"]
    D["spr_len"] = D["spr_z1"] + D["pcb_t"] + D["back_panel"]
    # board coordinates of the carrier centre (KiCad y is down the panel)
    D["board_xy"] = (D["axis_bx"], D["axis_by"] - D["place_y"])
    return D


def board_xy(D, x, y):
    """Carrier-frame point → main-PCB coordinates (origin = panel top-left, y down)."""
    return (D["axis_bx"] + x, D["axis_by"] - D["place_y"] - y)
