"""Top-screen joystick stack v0.5 — params + derive.

v0.5 (2 Nov 2026, Ed): the bezel is a 5 mm grip block with the glass on top; the switch stack is lifted 2 mm on
M2x30 standoffs so the carrier rises into the faceplate hole; two guide screws in brass sleeves tie the bezel to the
carrier (no rocking on the press springs, and their heads are the up-stop v0.4 lacked); the joystick sits as high as
the top rail screws (ISO 7092 Ø6 washers) allow, and the knob moves down on the panel instead (finger room);
two 2x3 board-to-board headers (12 pins); the screen flex socket sits on a tab of the daughterboard beyond the plate.

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
    version="v0.5",
    # ---- placement. place_y is derived so the notched edge clears the knob ----
    knob_od_design=41.70,   # [Ed] size the plan to the v0.17 knob. The live knob-param OD is checked too
    knob_extra=0.0,         # nominal gap is the process stack itself (v0.4 rule only)
    place_rule="rail",      # [Ed] 2 Nov v0.5: "rail" = as high as the top rail screw keep-out allows (the case owns the rule
                            # and publishes place_y); "knob" = v0.4, as close to the knob as the process stack allows
    finger_min=5.0,         # [Ed] 2 Nov: plan gap from the knob glass to the bezel at rest, at least this (finger room)
    pcb_edge=0.30,          # [A] a PTH pad stays this far inside the main-PCB copper edge
    rail_z=10.0,            # [A] Eurorack rail does not reach this far in front of the PCB
    # PCBWay process tolerances. A clearance is one of these, not a looser drawing gap.
    tol_sla=0.20,           # [S] SLA resin, the wide end of PCBWay's ±0.1–0.2 mm
    tol_mjf=0.25,           # [S] MJF/SLS nylon
    tol_fdm=0.20,           # [S] FDM, if a jig or a trial part is printed that way
    # ---- screen (DWO DO0164FMST05, landscape: datasheet portrait 26.74 W x 41.62 H) ----
    scr=dict(part="DWO DO0164FMST05 1.64\" 456x280 AMOLED", w=41.62, h=26.74, t=1.5, active=(35.57, 21.84),
             mass_g=8.0),  # [S] outline/thickness; mass [A] until the module is weighed
    scr_below_knob=5.0,     # [Ed] old screen target. knob_proud now places the faceplate; the screen follows the bezel
    knob_proud=16.45,       # [Ed] adopted value. derive() recomputes it from the 25 mm riser; 16–20 is the accepted window
    print_min=1.0,          # [S] PCBWay SLS nylon minimum wall (SLA resin is 0.8). Structural walls use this
    # FPC: exit side, width, pitch and pin-out are OPEN. Model is [A].
    fpc_w=8.0,              # [A]
    fpc_t=0.12,             # [A]
    fpc_bend=2.6,           # [A] screen +x edge to the slot centre, when the skirt allows it
    fpc_slot_l=2.3,         # [A]
    # ---- carrier / bezel ----
    car_top_below=0.3,      # [A] glass stands this far proud of the bezel top
    bz_lip=1.2,             # [Ed] bezel lip (side wall of the grip block), same as the other bezel. 1.5 mm is the maximum
    bz_t=1.2,               # [Ed] v0.4 bezel thickness; v0.5 uses grip_h for the height (kept so old overrides parse)
    grip_h=5.0,             # [Ed] 2 Nov v0.5: the bezel is a grip block at least 5 mm tall, glass on top; the faceplate tucks in behind its edge
    glass_proud=0.6,        # [A] glass top above the block rim (as v0.4: 1.5 glass on 0.3 pads in a 1.2 bezel)
    roof_t=1.6,             # [A] roof plate under the glass: the springs push on its underside, the glass is glued on top
    # guides (v0.5, Ed 2 Nov): two screws through brass sleeves tie the bezel to the carrier. The sleeve slides in a reamed
    # bore in the carrier; the screw head under the carrier boss is the up-stop (v0.4 had none).
    guide=dict(part="ISO 7984 M2x8 A2 low-head socket screw + brass tube sleeve OD 3.0 / ID 2.1, cut to length",
               d=2.0, sleeve_od=3.0, head_d=3.8, head_k=1.6, bore_fit=0.03, boss_wall=1.0,
               ins=dict(part="M2x3x3.2 brass heat-set (bezel roof)", od=3.2, length=3.0, hole=3.0)),   # [S] DIN 7984 M2 head Ø3.8 × 1.6 max [A]
    guide_gy=5.0,           # [A] guides on the y axis at (0, ±guide_gy): clear of the cup, the switch and the hold-down hooks
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
    stem_below=1.10,        # [Ed] 2 Nov: carrier underside above the stem top
    fpc_to_db=True,         # [Ed] 2 Nov: the screen flex plugs into a socket on the joystick daughterboard (no slot in the main PCB;
                            # the old drop landed on the top-right corner bolt post). Signals go down through the board-to-board headers.
    db_fpc_sock=(8.4, 3.0, 0.9),   # [S/A] AXE530127 30-pin 0.4 mm socket: long side (along y, the flex width), short side (x), mated height
    db_fpc_x_in=3.0,        # [A] v0.4 only (socket under the plate)
    # ---- switch ----
    sw=dict(part="Alps SKRHADE010", w=7.45, d=7.5, h=1.85, stem_d=3.0, stem_top=5.0, pivot=0.49, ref_h=4.3,
            tilt_travel=0.25, push_travel=0.15, tilt_f=1.2, push_f=2.35, f_tol=0.69,   # [S]
            pad_x=3.575, pad_y=1.425, pad=(1.35, 1.0), tab_y=4.05, tab=(2.0, 1.8)),    # [S] land pattern
    sw_rot=-45.0,           # [Ed] directions line up with the screen axes
    # ---- daughterboard. Outline is derived. Thickness is the fab stack, not the print minimum ----
    db_t=1.0,               # [A] 2-layer FR4
    cu_edge=0.30,           # [A] copper-to-outline, same rule as the KiCad board
    pitch=2.54,             # [S]
    # male header, plastic on the UNDERSIDE, pin down into the socket. Lead style -17 is the
    # straight-pin post that mates a 25 mm riser (Samtec TSW chart: tail 2.79, post 15.74).
    # The -20 post (25.91) went through the main PCB. The 1x3 is consigned; LCSC's -20 line is 2-row.
    # v0.5: two 2x3 (12 pins): 10 signals (QSPI CLK, CS, IO0-3, RST, TE, PWR_EN, switch ladder) + 3.3 V + GND; the four brass
    # standoffs are GND too. Two 2x5 would need the board ~4 mm wider, into the top corner posts.
    hdr=dict(part="Samtec TSW-103-xx-T-D long-post 2x3 header, post about 21.5 mm for the 30 mm riser (exact -xx code to pick)", lcsc="consigned", mate=21.5, ins=2.54, tail=2.79, n=3, rows=2),  # [A] 2 Nov v0.5
    # female socket on the main PCB. Same hanxia H11 family as the v0.2 2x3, split into two 1x3s.
    sock=dict(part="2.54 mm 2x3 female socket, 11 mm (hanxia PM2.54 H11 family, 2x3 part to pick)", lcsc="TBC", h=11.0, tail=3.2, n=3, rows=2),  # [A] v0.5 (v0.4: 1x3 C41427518)
    # round female-female brass. Body is the riser. An ISO 4762 screw goes in each end.
    # Hex H3×M2×25 (STTZ2022) and the male-female 25 mm parts were out of stock on LCSC, 1 Nov 2026.
    # OD 3.2 is the usual knurled round M2 pillar; LCSC does not publish it. [A]
    standoff=dict(part="M2x30 female-female brass standoff (stock size; printed spacer if none in stock)", lcsc="TBC", length=30.0, od=3.2, kind="female-female"),  # [Ed] 2 Nov v0.5: 30 mm lifts the switch 2 mm (was 28)
    shcs=dict(part="ISO 4762 M2 A2", head_d=3.8, head_h=2.0, socket=1.5, top=6.0, bot=4.0),  # [S] DIN 912. Top through plate+board, bottom through the PCB
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
    spr_xy=(6.0, 4.6),      # [A] v0.5 hold-down springs at (±x, ±y): clear of the 2x3 header bodies (y ±2.54) and the balls
    spr_f=1.40,             # [A] 2 Nov v0.5, pending Ed: N each (v0.4 0.5 [Ed]). Sized so a sideways push on the glass top tips the
                            # carrier only above 1.3x the switch's worst-case tilt force (balls only 8 mm apart up/down)
    tip_margin=1.3,         # [A] tipping force / worst-case switch tilt force
    spr_ext=8.0,            # [A] extension at rest, mm. Free length is installed length minus this
    pin_d=1.2,              # [A] push-in cross pin, stainless or music wire
    pin_clear=0.30,         # [A] bore diameter over the pin, so it slides while pliers hold the hook
    eye_wire=0.70,          # [A] hook wire diameter
    eye_clear=0.20,         # [A] radial gap from the pin to the hook wire
    ra_wall=1.0,            # [S] rear-anchor wall, the print minimum
    back_panel=22.65,       # [A] old back-panel depth. The springs no longer reach it
    # ---- check targets. derive() overwrites the ones that are process tolerances ----
    tgt=dict(stem_cup_min=0.20, gap_min=0.20, cable_min=0.25, spring_min=0.10,
             knob_min=0.50, board_min=0.25, mate_min=3.5, mate_max=6.5),
)


def _knob_data():
    """Read knob-param as data only (do not modify it). Live OD and the knob top set the plan and the stack.
    knob_proud is included only once the assembly interface publishes it."""
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    kp = os.path.join(here, "knob-param")
    if kp not in sys.path:
        sys.path.insert(0, kp)
    from knobparam.common import model
    D = model.derive(model.default_params())
    out = dict(knob_od=float(D["knob_od"]), z_knob_top=float(D["z_knob_top"]),
               pcb_above=float(D["pcb_above"]), pcb_w=float(D["pcb_w"]), pcb_t=float(D["pcb_t"]),
               axis_bx=float(D["axis_bx"]), axis_by=float(D["axis_by"]))
    if "knob_proud" in D:
        out["knob_proud"] = float(D["knob_proud"])
    # v0.5: the case owns the panel layout. It publishes the faceplate z, the joystick place_y (rail rule), the
    # rail strip and the main-PCB nest. Read as data; the joystick keeps its own copy only as a fallback.
    for k in ("faceplate_z", "place_y", "panel_y1", "rail_clear", "pcb_y1", "pcb_x1", "y_in1", "rail_y_top",
              "rail_keep_d", "rail_x_top"):
        if k in D:
            out["case_" + k] = D[k]
    return out


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
    # The stock body is the riser. Everything above it — stem slack, carrier, faceplate, bezel —
    # stacks on that length. knob_proud is then the gap from the faceplate front up to the knob top,
    # which is what the knob and the case adopt. A longer riser lifts the faceplate, so proud falls.
    so, hd, sk = D["standoff"], D["hdr"], D["sock"]
    D["knob_proud_live"] = "knob_proud" in K
    D["knob_proud_in"] = D["knob_proud"]
    D["z_db0"] = so["length"]
    D["z_db1"] = D["z_db0"] + D["db_t"]
    D["z_sw1"] = D["z_db1"] + sw["h"]
    D["z_stem_top"] = D["z_db1"] + sw["stem_top"]
    D["z_pivot"] = D["z_db1"] + sw["pivot"]
    D["z_ref"] = D["z_db1"] + sw["ref_h"]
    D["car_floor"] = pm
    D["z_c0"] = D["z_stem_top"] + D["stem_below"]
    D["z_floor1"] = D["z_c0"] + D["car_floor"]
    # v0.5: the faceplate z is the knob's (interface faceplate_z, via the case). The 30 mm riser lifts the carrier
    # into the faceplate hole; v0.4 derived the faceplate from the stack (carrier floor + one SLA tolerance).
    if "case_faceplate_z" in K:
        D["z_fp1"] = float(K["case_faceplate_z"])
        D["z_fp0"] = D["z_fp1"] - D["fp_t"]
    else:
        D["z_fp0"] = D["z_floor1"] + sla
        D["z_fp1"] = D["z_fp0"] + D["fp_t"]
    D["z_bz0"] = D["z_fp1"] + D["up_gap"]
    # grip block: walls from just above the faceplate to the rim; glass on a roof plate, standing glass_proud above the rim
    D["z_bz1"] = D["z_bz0"] + D["grip_h"]
    D["scr_top"] = D["z_bz1"] + D["glass_proud"]
    D["z_scr0"] = D["scr_top"] - S["t"]
    D["z_roof"] = D["z_scr0"] - D["roof_t"]          # roof plate underside: the press springs and the guide bosses hang from it
    D["scr_drop"] = D["z_knob_top"] - D["scr_top"]
    D["fp_rebate"] = D["tol_sla"] + 0.15 + 0.20   # filled in after press_travel exists; placeholder
    D["knob_proud"] = D["z_knob_top"] - D["z_fp1"]
    D["z_glass"] = D["z_knob_top"] + 4.3   # [A] v0.18: glass 56.8 = knob shell top 52.5 + 4.3
    D["riser_h"] = D["z_db0"]
    D["riser_catalog"] = so["length"]
    D["z_hdr_tip"] = D["z_db0"] - hd["ins"] - hd["mate"]
    D["mate_air"] = D["riser_h"] - hd["ins"] - sk["h"]
    D["mate_in"] = hd["mate"] - D["mate_air"]
    D["standoff_d"] = so["od"]
    sc = D["shcs"]
    D["screw_d_model"] = 1.70            # slip in the Ø2.4 hole. The real thread engages the pillar
    D["z_head_bot1"] = -D["pcb_t"] - 0.01
    D["z_head_bot0"] = D["z_head_bot1"] - sc["head_h"]
    D["engage_bot"] = sc["bot"] - D["pcb_t"]
    D["plate_t"] = pm
    D["z_plate0"] = D["z_db1"]
    D["z_plate1"] = D["z_plate0"] + D["plate_t"]
    D["z_head_top0"] = D["z_plate1"] + 0.01
    D["z_head_top1"] = D["z_head_top0"] + D["shcs"]["head_h"]
    D["engage_top"] = D["shcs"]["top"] - D["plate_t"] - D["db_t"]
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
    D["place_y_knob"] = max(_place_for(x, y, rc) for x, y in silhouette)   # v0.4 rule: as close to the knob as allowed
    if D["place_rule"] == "rail" and "case_place_y" in K:
        D["place_y"] = float(K["case_place_y"])     # v0.5: the case's rail rule (joystick as high as the rail screws allow)
    else:
        D["place_y"] = D["place_y_knob"]
    D["finger_gap"] = D["place_y"] - D["half_h"] - design_od / 2   # knob glass to the bezel, plan, at rest
    # main-PCB top edge and the rail strip, local to the joystick axis
    D["y_pcb"] = (K["case_pcb_y1"] if "case_pcb_y1" in K else D["pcb_above"]) - D["place_y"]
    D["y_rail"] = ((K["case_panel_y1"] - K["case_rail_clear"]) - D["place_y"]) if "case_panel_y1" in K else 99.0
    D["rail_margin"] = 0.5   # [A] air kept between a part behind the panel and the rail strip line
    # switch on the carrier axis. Land extent drives the plate opening and the board
    D["sw_xy"] = (0.0, 0.0)
    D["sw_ext"] = _land_extent(sw, D["sw_rot"])
    D["body_r"] = math.hypot(sw["w"], sw["d"]) / 2
    D["cut_r"] = D["sw_ext"] + D["part_gap"]
    n, pitch = hd["n"], D["pitch"]
    D["hdr_len"] = n * pitch
    D["hdr_wid"] = hd.get("rows", 1) * pitch
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
    sy_head = D["y_pcb"] - D["pcb_edge"] - D["shcs"]["head_d"] / 2
    # v0.5: the 2x3 header bodies are 5.08 wide, so the standoffs sit just outside them in y
    D["sy_need"] = D["hdr_wid"] / 2 + D["part_gap"] + D["standoff_d"] / 2
    D["sy"] = max(D["sy_need"], 0.0) if hd.get("rows", 1) > 1 else min(sy_corner, sy_pad, sy_head)
    D["sy_corner"] = sy_corner
    D["sy_pad"] = sy_pad
    D["sy_head"] = sy_head
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
    D["spr_x"], D["spr_y"] = D["spr_xy"]   # v0.5: clear of the 2x3 header bodies (y ±2.54) and the ball cups
    D["springs"] = [(sx, sy) for sx in (D["spr_x"], -D["spr_x"]) for sy in (D["spr_y"], -D["spr_y"])]
    edge = S["w"] / 2
    skirt_outer = D["db_half_w"] + D["skirt_gap"] + D["car_skirt"]
    D["fpc_x"] = max(edge - D["fpc_bend"], skirt_outer + D["tgt"]["cable_min"] + D["fpc_t"] / 2 + sla)
    if D["fpc_to_db"]:
        # v0.5: the socket sits on a tab of the daughterboard past the +x standoffs, outside the seat plate. Its long side
        # runs along y (the flex width), so the flex drops straight onto it. The carrier skirt is notched over the tab.
        sl_, ss_, sz_ = D["db_fpc_sock"]
        D["db_sock_x"] = D["sx"] + D["standoff_d"] / 2 + D["part_gap"] + ss_ / 2
        D["tab_x1"] = D["db_sock_x"] + ss_ / 2 + D["cu_edge"]
        D["tab_hy"] = sl_ / 2 + D["cu_edge"]
        D["fpc_x"] = D["db_sock_x"]
        D["fpc_bend"] = edge - D["fpc_x"]
    D["slot_x"] = (D["fpc_x"] - D["fpc_slot_l"] / 2, D["fpc_x"] + D["fpc_slot_l"] / 2)
    D["slot_hy"] = D["fpc_w"] / 2 + D["fpc_slot_side"]
    D["hole_x0"] = D["slot_x"][0] - D["slide"] - D["hole_extra"]
    D["hole_x1"] = D["slot_x"][1] + D["slide"] + D["hole_extra"]
    D["hole_hy"] = D["slot_hy"] + D["slide"] + D["hole_extra"]
    D["spr_z1"] = D["z_c0"] - D["spr_boss"][1]
    # lower hooks end just behind the PCB. Two pins run along X, one per Y pair.
    pr = D["pin_d"] / 2.0
    wr = D["eye_wire"] / 2.0
    major = pr + D["eye_clear"] + wr
    D["eye_major"] = major
    D["eye_minor"] = wr
    D["eye_ro"] = major + wr
    D["pin_bore"] = D["pin_d"] + D["pin_clear"]
    D["z_pin"] = -D["pcb_t"] - 0.02 - D["ra_wall"] - major
    D["spr_len"] = D["spr_z1"] - D["z_pin"]
    D["spr_len_was"] = D["spr_z1"] + D["pcb_t"] + D["back_panel"]
    D["spr_free"] = D["spr_len"] - D["spr_ext"]
    D["spr_rate"] = D["spr_f"] / D["spr_ext"]
    wall = D["ra_wall"]
    D["ra_x0"] = -D["spr_x"] - major - wall
    D["ra_x1"] = D["spr_x"] + major + 2.0
    D["ra_y0"] = -D["spr_y"] - D["eye_ro"] - wall
    D["ra_y1"] = D["spr_y"] + D["eye_ro"] + wall
    D["ra_z1"] = -D["pcb_t"] - 0.02
    D["ra_z0"] = D["z_pin"] - D["eye_ro"] - wall
    D["pin_x0"] = D["ra_x0"] + wall + 0.3
    D["pin_x1"] = D["ra_x1"] - 0.25
    D["pin_head_d"] = D["pin_d"] * 1.8
    D["pin_head_t"] = 0.8
    D["pin_y"] = (D["spr_y"], -D["spr_y"])
    D["ra_slot"] = D["spr_d"] + 1.2
    D["ra_bond"] = (D["ra_x1"] - D["ra_x0"]) * (D["ra_y1"] - D["ra_y0"])
    # ---- v0.5 press-spring stations: inside the carrier outline (their insert bosses rise into the faceplate hole),
    # and below the rail strip if the boss still reaches behind the panel. With the guides they no longer stop the
    # bezel rocking, so they can come in from the corners.
    br_cs = D["boss_d"] / 2
    D["cs_bossr"] = br_cs
    D["cs_x"] = D["car_hw"] - br_cs - sla
    cs_y = D["car_hh"] - br_cs - sla
    if D["z_ins0"] < D["z_fp0"]:
        cs_y = min(cs_y, D["y_rail"] - D["rail_margin"] - br_cs)
    D["cs_y"] = cs_y
    D["cs_xy"] = [(sx, sy) for sx in (D["cs_x"], -D["cs_x"]) for sy in (D["cs_y"], -D["cs_y"])]
    # skirt walls (±y only in v0.5) end this far out, short of the grubs hanging under the stations
    D["skirt_x"] = min(D["board_x1"] + D["skirt_gap"] + D["car_skirt"], D["cs_x"] - D["grub_d_model"] / 2 - 0.5)
    # ---- v0.5 guides: screw + brass sleeve, bezel to carrier. Head under a carrier boss = up-stop; sleeve in a reamed bore.
    G = D["guide"]; gi = G["ins"]
    D["g_xy"] = [(0.0, D["guide_gy"]), (0.0, -D["guide_gy"])]
    D["g_boss_r"] = G["sleeve_od"] / 2 + G["boss_wall"]
    D["g_bore"] = G["sleeve_od"] + 2 * G["bore_fit"]
    D["g_ins_top"] = D["z_scr0"] - 0.6                    # [A] 0.6 of roof left under the glass over the insert
    D["g_ins_bot"] = D["g_ins_top"] - gi["length"]
    D["g_rboss_r"] = gi["od"] / 2 + 1.0
    zmin = D["z_sw1"] + D["press_travel"] + mjf + G["head_k"]   # head clears the switch body at full press
    best = None
    for L in (4.0, 5.0, 6.0, 8.0, 10.0):                   # ISO 7984 stock lengths
        z0 = max(zmin, D["g_ins_bot"] + 2.0 - L)            # at least 2 mm of thread in the insert
        if z0 + L <= D["g_ins_top"] - 0.2 + 1e-9 and z0 <= D["z_c0"] - 1.0:
            best = (L, z0)
    D["g_len"], D["g_z0"] = best if best else (6.0, zmin)
    D["g_zmin"] = zmin
    D["g_tip"] = D["g_z0"] + D["g_len"]
    D["g_engage"] = D["g_tip"] - D["g_ins_bot"]
    D["g_sleeve_len"] = D["g_ins_bot"] - D["g_z0"]
    D["g_guide_len"] = D["z_floor1"] - D["g_z0"]
    D["g_head0"] = D["g_z0"] - G["head_k"]
    D["g_gap_press"] = D["g_ins_bot"] - D["z_floor1"]       # roof boss bottom to the carrier floor top (must exceed the press)
    # ---- v0.5 tipping: a sideways push on the glass top, reacted by the stem at its tilt reference height, against
    # the hold-down springs about the far ball line. The ball rows are only 2·by apart up/down.
    tilt_max = sw["tilt_f"] + sw["f_tol"]
    D["tip_need"] = D["tip_margin"] * tilt_max
    D["tip_arm_top"] = D["scr_top"] - D["z_ref"]
    D["tip_arm_mid"] = (D["z_bz0"] + D["z_bz1"]) / 2 - D["z_ref"]
    fhd = len(D["springs"]) * D["spr_f"]
    D["tip_f_top_y"] = fhd * D["by"] / D["tip_arm_top"]
    D["tip_f_mid_y"] = fhd * D["by"] / D["tip_arm_mid"]
    D["tip_f_top_x"] = fhd * D["bx"] / D["tip_arm_top"]
    D["spr_f_need"] = D["tip_need"] * D["tip_arm_top"] / (len(D["springs"]) * D["by"])
    D["board_xy"] = (D["axis_bx"], D["axis_by"] - D["place_y"])
    return D


def board_xy(D, x, y):
    """Carrier-frame point → main-PCB coordinates (origin = panel top-left, y down)."""
    return (D["axis_bx"] + x, D["axis_by"] - D["place_y"] - y)
