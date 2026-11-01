"""Top-screen joystick stack v0.1 — params + derive.

Local frame: origin = carrier centre on the MAIN PCB FRONT (z = 0), +x right along the panel width, +y up the panel
(toward the panel top), +z out of the panel. Placement in the knob-param frame (dial axis = 0,0): (0, place_y).
Tags: [Ed] Ed's decision, [S] datasheet, [L] panel layout v5 (scope/knob-module-v1.md), [K] main-PCB KiCad, [A] assumed.
Every derived value is computed in derive(); parts and checks read only P + derived values.

The screen top is the faceplate front from the knob interface (z_glass - knob_proud). The J2 socket stays the
8.5 mm part soldered on the main PCB. A printed extender fills from the socket top up to the daughterboard,
and the riser grows so the stem keeps its air under the carrier.
"""
import math
import os
import sys

P = dict(
    version="v0.1",
    # ---- placement (panel layout v5 / knob-main-pcb make_board.py) ----
    place_y=31.8,            # [L] carriage centre board y 21.1 -> knob frame y = 52.9 - 21.1 (dial axis board y 52.9)
    pcb_t=1.6,               # [K]
    # ---- screen (1.14" 240x135 IPS ST7789V, landscape) ----
    scr=dict(part='1.14" 240x135 IPS (ST7789V)', w=31.0, h=17.6, t=1.55, active=(24.9, 14.9)),  # [L] module w×h; t [A]
    # screen top is derived: it is the knob faceplate front (interface z_glass - knob_proud)
    scr_clear=0.3,           # [A] screen to the carrier pocket wall
    fpc_w=8.0,               # [A] screen FPC width (placeholder until the module is chosen)
    fpc_t=0.12,              # [A]
    fpc_x=15.0,              # [A] FPC drop line (folds down at the +x / COG end of the module)
    # ---- carrier (printed) ----
    car=(33.6, 20.6),        # [L] carriage outline (panel cut-out 35.2 x 22.2 = 0.8 / side)
    car_wall=1.0,            # [A] side wall round the screen pocket
    car_floor=1.2,           # [A] floor under the spider pad
    car_skirt=0.8,           # [A] skirt round the base top = slide stop
    car_top_below=0.3,       # [A] carrier wall top below the screen glass top
    slide=0.40,              # [A] carrier slide to the hard stop, each axis (skirt inner to base outer)
    skirt_overlap=0.75,      # [A] skirt reaches this far below the base top
    car_slot=(2.0, 0.75),    # [A] FPC slot in the carrier floor: length along x, clearance each side of the FPC in y
    # ---- spider (printed nylon PA12 MJF / resin), screen bonded on its pad land ----
    sp_t=0.6,                # [A] plate thickness (sets stiffness ~ t^3)
    sp_gap=0.40,             # [Ed] 0.3-0.5 free travel under the pad (pad never bottoms: the switch takes the full press)
    sp_land=0.6,             # [A] raised land on the pad the screen sits on (screen clears the frame + arms)
    sp_frame=1.2,            # [A] frame width
    sp_pad=(18.0, 8.0),      # [A] pad (centred on the switch axis)
    sp_arm_w=1.2,            # [A] arm width
    sp_E=1700.0,             # [S] PA12 MJF flexural modulus, MPa (approx)
    plunger_d=2.8,           # [A] plunger under the pad, presses the stem top
    plunger_gap=0.05,        # [A] plunger tip to stem top at rest
    # ---- cup over the stem (on the carrier) ----
    cup_bore=3.15,           # [S/A] Ø3.1-3.2 over the Ø3 stem (Alps keytop note)
    cup_od=5.0,              # [A]
    cup_engage=1.2,          # [A] cup bottom below the stem top
    # ---- switch: Alps SKRHADE010 (catalogue drawing No.4, Update 2510) ----
    sw=dict(part="Alps SKRHADE010", w=7.45, d=7.5, h=1.85, stem_d=3.0, stem_top=5.0, pivot=0.49, ref_h=4.3,
            tilt_travel=0.25, push_travel=0.15, tilt_f=1.2, push_f=2.35, f_tol=0.69),   # [S]
    sw_rot=-45.0,            # [Ed] footprint turned 45° so the switch's diagonal directions line up with screen up/down/left/right
    sw_x=-2.9,               # [A] switch (and press) axis: under the active-area centre, clear of the riser header
    # ---- daughterboard + risers ----
    db=(16.6, 12.0, 1.0),    # [A] daughterboard w, h, t (PCBWay 1.0 FR4)
    hdr_x=5.6,               # [A] 2x3 2.54 header centre (J1 male on the daughterboard, plastic on TOP, pins down)
    hdr_body=(5.08, 7.62, 2.5),   # [S] 2x3 2.54 male header plastic
    sock=(5.08, 7.62, 8.5),  # [S] 2x3 2.54 female socket soldered on the main PCB (FG FG-PM2.54-2-03P-H8.5). Not the riser height.
    stem_gap=1.35,           # [A] carrier underside above the stem top. The 8.5 mm socket left this when the screen was at z 20.2
    post_d=4.0,              # [A] printed riser post under the switch (part of the base)
    # ---- base (printed, glued to the main PCB, 4 locating pins) ----
    base_wall=1.2, base_floor=1.0, base_top_t=1.75,   # [A]
    win_clear=0.4,           # [A] top-plate window round the daughterboard (board drops in from the top)
    pin=(1.2, 1.0),          # [A] locating pins Ø, length into the PCB
    pin_xy=6.0,              # [A] pins at (±pin_xy, ±(base half-h - wall/2))
    # ---- balls ----
    ball_d=2.0,              # [A] steel (or ceramic) balls, one per corner
    ball_xy=(14.0, 7.0),     # [A]
    seat_clear=0.05,         # [A] hemisphere seat radius over the ball
    # ---- hold-down springs (4 extension springs through the PCB to the back panel) ----
    spr_d=2.0,               # [A] spring OD
    spr_xy=(10.8, 6.6),      # [Ed/A] inside the balls
    spr_bore=3.4,            # [A] bore in the base + PCB hole
    spr_boss=(2.6, 0.6),     # [A] hook boss under the carrier: Ø, height
    spr_f=0.5,               # [A] hold-down force per spring, N
    back_panel=25.0,         # [A] PCB back -> back panel (spring length)
    # ---- FPC hole through the base + PCB ----
    hole_extra=0.2,          # [A] base / PCB slot round the carrier slot at full slide
    # ---- check targets ----
    tgt=dict(stem_cup_min=0.05, gap_min=0.3, cable_min=0.5, spring_min=0.1, overtravel_max=0.15, knob_min=0.5, board_min=0.3),
)


def _faceplate():
    """Knob-frame faceplate front and thickness. Same subtraction as interface.derive."""
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    kp = os.path.join(here, "knob-param")
    if kp not in sys.path:
        sys.path.insert(0, kp)
    from knobparam.assembly.interface import P as IP
    z = float(IP["z_glass"]) - float(IP["knob_proud"])
    return z, float(IP["faceplate_t"])


def derive(P_):
    D = dict(P_)
    sw, S = D["sw"], D["scr"]
    D["faceplate_z"], D["faceplate_t"] = _faceplate()
    D["scr_top"] = D["faceplate_z"]          # v0.1 glass is flush with the faceplate front
    D["z_scr0"] = D["scr_top"] - S["t"]
    D["z_sp1"] = D["z_scr0"] - D["sp_land"]          # spider plate top
    D["z_sp0"] = D["z_sp1"] - D["sp_t"]               # spider plate bottom = carrier ledge
    D["z_floor1"] = D["z_sp0"] - D["sp_gap"]          # carrier floor top under the pad
    D["z_c0"] = D["z_floor1"] - D["car_floor"]        # carrier underside = ball tops
    D["z_ball"] = D["z_c0"] - D["ball_d"] / 2         # ball centres = base top
    D["z_base1"] = D["z_ball"]
    D["z_base_top0"] = D["z_base1"] - D["base_top_t"]
    D["z_skirt0"] = D["z_base1"] - D["skirt_overlap"]
    D["z_car1"] = D["scr_top"] - D["car_top_below"]
    # Riser follows the faceplate. The socket stays 8.5 mm on the PCB; riser_ext is the printed spacer above it.
    D["z_db0"] = D["z_c0"] - D["db"][2] - sw["stem_top"] - D["stem_gap"]
    D["sock_h"] = D["sock"][2]
    D["riser_ext"] = D["z_db0"] - D["sock_h"]
    D["z_db1"] = D["z_db0"] + D["db"][2]
    D["z_sw1"] = D["z_db1"] + sw["h"]
    D["z_stem_top"] = D["z_db1"] + sw["stem_top"]
    D["z_pivot"] = D["z_db1"] + sw["pivot"]
    D["z_ref"] = D["z_db1"] + sw["ref_h"]             # height where the 0.25 tilt travel is specified
    D["z_cup0"] = D["z_stem_top"] - D["cup_engage"]
    D["z_plunger0"] = D["z_stem_top"] + D["plunger_gap"]
    # outlines
    cw, ch = D["car"]
    D["base_w"] = cw - 2 * (D["car_skirt"] + D["slide"]); D["base_h"] = ch - 2 * (D["car_skirt"] + D["slide"])
    D["pocket"] = (S["w"] + 2 * D["scr_clear"], S["h"] + 2 * D["scr_clear"])
    D["cav"] = (D["base_w"] - 2 * D["base_wall"], D["base_h"] - 2 * D["base_wall"])
    dw, dh, _ = D["db"]
    D["win"] = (dw + 2 * D["win_clear"], dh + 2 * D["win_clear"])
    # spider: frame from the pocket's -x wall to just short of the FPC slot; pad centred on the switch axis
    sl, sc = D["car_slot"]
    D["slot_x"] = (D["fpc_x"] - 1.4, D["fpc_x"] + 0.6)
    D["slot_hy"] = D["fpc_w"] / 2 + sc
    D["sp_x"] = (-D["pocket"][0] / 2 + 0.3, D["slot_x"][0] - 0.3); D["sp_hy"] = D["pocket"][1] / 2 - 1.3
    D["sp_in_x"] = (D["sp_x"][0] + D["sp_frame"], D["sp_x"][1] - D["sp_frame"]); D["sp_in_hy"] = D["sp_hy"] - D["sp_frame"]
    pw, ph = D["sp_pad"]
    D["pad_x"] = (D["sw_x"] - pw / 2, D["sw_x"] + pw / 2)
    # base / PCB FPC hole: carrier slot grown by the slide + extra, open to the base +x end (notch)
    D["hole_x0"] = D["slot_x"][0] - D["slide"] - D["hole_extra"]
    D["hole_hy"] = D["slot_hy"] + D["slide"] + D["hole_extra"]
    D["hole_x1"] = D["slot_x"][1] + D["slide"] + D["hole_extra"]
    # spider stiffness (4 guided L/U arms, beam length ~ horizontal run) and press force budget
    I = D["sp_arm_w"] * D["sp_t"] ** 3 / 12
    L = D["arm_L"] = (pw / 2 - 0.6) - 0.6
    D["sp_k"] = 4 * 12 * D["sp_E"] * I / L ** 3                     # N/mm, 4 arms, guided-end beams
    D["sp_defl_click"] = D["plunger_gap"] + sw["push_travel"]
    D["sp_f_click"] = D["sp_k"] * D["sp_defl_click"]
    D["press_f"] = sw["push_f"] + D["sp_f_click"]
    # slide needed to actuate a direction, at the cup (stem tilts about its pivot; travel specified at ref_h)
    D["cup_rad_clear"] = (D["cup_bore"] - sw["stem_d"]) / 2
    D["slide_need"] = D["cup_rad_clear"] + sw["tilt_travel"]
    # stack
    D["stack_h"] = D["scr_top"]
    D["riser_h"] = D["z_db0"]
    D["spr_z1"] = D["z_c0"] - D["spr_boss"][1]
    D["spr_len"] = D["spr_z1"] + D["pcb_t"] + D["back_panel"]
    return D
