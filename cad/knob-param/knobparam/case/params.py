"""Enclosure (case) v0.1 — own params + derive.

One-piece SLA shell in PCBWay UTR-8100 clear resin. The faceplate is the Eurorack panel
(integrated; no separate plate, no acrylic). Knob frame: dial axis = Z, Z above the main-PCB
front, +X = motor, +Y = panel top.

Geometry that belongs to the other two open branches is snapshotted here, not imported
(those trees are not on param-dev, and this sub cannot edit them):

* Joystick v0.4 bezel / faceplate contract — commit bce854b54acdef8a2a4c86b35ff4460e1a8e460a
  (origin/sub/joystick-v04). Screen DWO DO0164FMST05, 1.2 mm lip, 0.90 mm overlap,
  place_y from the same clearance rule as jsparam.derive.
* Knob v0.17 OD — commit 00502746fa2fb2aaef44580e1b9edbcc907f73e7 (origin/sub/assembly-v017).
  Design notes: minimum Ø41.641, drawn Ø41.65. The joystick sizes the plan to Ø41.70.
  z_knob_top is 52.5 on both that branch and param-dev (z_glass 56.8 − lip 4.0 − knob_run 0.3).
  The faceplate front is that height minus knob_proud (16.45 mm). When cad_constraints grows a
  z_knob_top / knob_top key, the plate follows it.

The live interface knob_od (v0.16b Ø40.85 on param-dev) is read as well; the opening uses
whichever is larger, so a later merge cannot make the hole smaller than the knob.

Tags: [Ed] Ed's decision, [L] module scope (knob-module-v1 panel layout), [S] datasheet / PCBWay,
[K] KiCad, [A] assumed, [J] joystick v0.4 snapshot, [N] knob v0.17 snapshot.
"""
import json
import math
import os

P = dict(
    case_rev="v0.1",
    joystick_commit="bce854b54acdef8a2a4c86b35ff4460e1a8e460a",   # [J] sub/joystick-v04
    knob_commit="00502746fa2fb2aaef44580e1b9edbcc907f73e7",       # [N] sub/assembly-v017
    # ---- Eurorack panel, from the module scope unless a wall will not fit ----
    # 10HP actual width in the scope is 50.50 = 10 × 5.08 − 0.30 (Doepfer table, layout v2+).
    # 3U height 128.5. Rail zones are the outer 10 mm behind the panel (sdiy.info).
    hp_scope=10,            # [L] locked module width, kept as the preference
    hp_pitch=5.08,          # [L] mm per HP
    hp_gap=0.30,            # [L] Doepfer panel is n × pitch − this (10 HP → 50.50)
    panel_h=128.5,         # [L] 3U
    rail_clear=10.0,       # [L] keep the body out of the rail strips
    rail_inset=7.5,        # [L] screw station, 7.5 from the panel edge (layout v5)
    rail_edge=3.0,         # [L] screw centre from the panel top / bottom
    rail_hole_d=3.2,       # [L] Ø3.2
    # ---- resin ----
    # UTR-8100: tensile 41.6 MPa, elongation 9%, density 1.3 g/cm³. SLA min wall 0.8.
    # Plain clear resin, no tint [Ed]. Only the front face is polished; every other face is as-printed.
    wall=2.5,              # [Ed] nominal wall, about 2.5
    sla_min=0.8,           # [S] PCBWay SLA minimum wall
    case_rho=1.3e-3,       # [S] g/mm³ (1.3 g/cm³)
    resin_rgb=(236, 240, 242),  # [Ed] untinted clear; a faint cool grey so it reads on white
    resin_opacity=0.20,   # [A] Quick Look / render opacity, no dye
    resin_rough=0.55,     # [Ed] as-printed faces. The front face alone is polished (resin_face_rough).
    resin_face_rough=0.08,# [Ed] polished front face only
    finish_front="polished",     # [Ed]
    finish_other="as-printed",   # [Ed]
    glow_rgb=(188, 240, 170),  # [A] Shimicoat strontium aluminate, green, drawn heavier than the real film
    glow_t=0.35,           # [A] drawn coat thickness so the brushed faces show; the real coat is a film
    glow_gap=0.30,         # [A] air between the drawn coat and the wall (keeps the solids apart)
    # ---- knob opening (v0.17 / joystick plan) ----
    knob_od_design=42.0,   # [Ed] glass + caps, about Ø42. Opening uses the larger of this and the live knob.
    z_knob_snap=52.5,      # [N] z_knob_top on v0.16b and v0.17, until cad_constraints carries it
    knob_proud=16.45,      # [Ed] knob top above the faceplate; 25 mm brass joystick pillar
    knob_rad_clear=0.20,   # [A] = one SLA tolerance, radial, dial and knob share this hole
    # ---- joystick bezel (v0.4 snapshot; formulas match jsparam.derive) ----
    scr_w=41.62,           # [J] DO0164FMST05 landscape width
    scr_h=26.74,           # [J]
    scr_t=1.5,             # [J]
    scr_below_knob=5.0,    # [J][Ed] screen top 5 mm under the knob top, before the 0.30 pad
    bz_lip=1.2,            # [J][Ed] lip, max 1.5
    bz_t=1.2,              # [J][Ed] bezel thickness
    bz_max=1.5,            # [Ed] lip and bezel thickness must not exceed this
    fp_overlap=0.90,       # [J] lip covers the faceplate at rest
    up_gap=0.02,           # [J] bezel sits this far above the plate so the faces do not fuse
    roof_pad=0.30,         # [J] glass sits on the spring pads; raises the glass 0.30
    sw_tilt=0.25,          # [J][S] SKRHADE010 tilt travel
    sw_push=0.15,          # [J][S] centre press
    tol_sla=0.20,          # [J][S] SLA, wide end of PCBWay ±0.1–0.2
    tol_mjf=0.25,          # [J][S] carrier and knob are MJF; joystick's knob clearance is 2 × this
    hole_corner_r=1.2,     # [A] rounded joystick opening (material left in the corners)
    fp_corner_r=2.0,       # [A] faceplate outer corner
    fillet_r=1.2,          # [A] bead on the wall-to-faceplate joint and the body corners
    # ---- scanner (665 nm). No mirror motor has been chosen. ----
    scan_motor_d=8.0,      # [A] FLAG: assumed small coreless / coin-style can, no catalogue part
    scan_motor_len=12.0,   # [A] FLAG
    scan_motor_clear=0.80, # [A] air from the can to the nearest wall or shelf
    mirror_d=16.0,         # [A] FLAG: disc on the motor shaft, large enough to catch the beam
    mirror_t=0.40,         # [A]
    mirror_tilt=45.0,      # [A] degrees, sends the +Z beam out across the walls
    vcsel_l=3.5,           # [S] 2835 body, JNJ-V-2835CW-665003-S-D1 (the 665 nm part named on v0.17)
    vcsel_w=2.8,           # [S]
    vcsel_h=0.80,          # [S]
    film_w=4.5,            # [A] grating film square
    film_t=0.12,           # [A]
    slot_clear=0.20,       # [A] film to the slot, each side
    shelf_t=2.2,           # [A] grating ledge; lips above and below the slot stay ≥ sla_min
    shelf_z=4.5,           # [A] ledge centre height above the PCB front
    film_gap=1.0,          # [A] film edge to the motor can
    beam_t=0.80,           # [A] thickness of the check volume for the swept fan
    beam_gap=0.40,         # [A] fan stops this far short of the wall and the faceplate
    beam_reach=1.2,        # [A] the fan must come at least this close (it is the light)
    # ---- printed metric thread + DIN 7984 low-head socket cap (M3) ----
    # Ed: ISO 4762 Allen head, low-head DIN 7984 acceptable if it saves depth. DIN 7984 M3
    # head is 2.0 mm instead of ISO 4762's 3.0 mm, so the counterbore is 1 mm shallower.
    # Flat-bottom counterbore in the PETG, head flush or just below. No 90° countersink.
    # Bosses are tapped in the resin. No inserts.
    screw_d=3.0,           # [Ed] M3
    screw_p=0.5,           # [S] ISO coarse pitch for M3
    screw_dk=5.50,         # [S] DIN 7984 / ISO 4762 head diameter, M3
    head_k=2.0,            # [S] DIN 7984 M3 head height (ISO 4762 is 3.0)
    screw_hex=2.0,         # [S] DIN 7984 hex socket across flats (ISO 4762 M3 is 2.5)
    screw_socket=1.3,      # [S] hex socket depth
    head_below=0.10,       # [A] head sits this far below the cover face
    cbore_clear=0.20,      # [A] counterbore radius over the head radius
    thread_int_k=1.082532, # [S] internal minor D1 = d − this × pitch
    thread_ext_k=1.226869, # [S] external minor d3 = d − this × pitch
    thread_crest=0.125,    # [S] crest flat, fraction of pitch (P/8)
    thread_root=0.25,      # [S] root flat, fraction of pitch (P/4)
    thread_fit=0.22,       # [A] radial air so the screw and the printed thread do not occupy the same solid
    engage_min=2.0,        # [Ed] engagement / diameter, minimum
    engage_mult=3.0,       # [Ed] used when there is room past the minimum
    boss_wall_mult=1.0,    # [Ed] resin around the thread, in diameters
    screw_hole_ratio=0.08, # [A] clearance hole over the screw, as a fraction of the diameter
    tip_clear_ratio=0.5,   # [A] screw tip stays this many diameters off the PCB and off rear parts
    # ---- back cover: transparent smoky-grey PETG, as shallow as the countersink allows ----
    # Depth behind the PCB is a placeholder until sub/assembly-v017 reports the bearing-retainer
    # plate. Today the tallest back-side part is encoder bearing 2, seated on under_pcb's back panel.
    rear_panel_snap=25.0,  # [A] under_pcb back_panel (not exported). Bearing 2 sits here.
    cover_clear_ratio=0.08,# [A] extra depth past that stack, as a fraction of the stack
    pocket_wall=2.14,      # [A] pocket back and tub wall; not the local screw pad
    cover_under_mult=0.5,  # [Ed] PETG left under the screw head, in screw diameters
    notch_gap=0.30,        # [A] air, printed boss to the PCB corner notch
    boss_gap=0.40,         # [A] air, boss to the knob hole and to the joystick opening
    cover_rho=1.27e-3,     # [A] PETG, g/mm³
    cover_rgb=(132, 136, 142),  # [A] smoky grey, still see-through
    cover_opacity=0.34,    # [A]
    # ---- knob collar, labyrinth placeholder, bolts up into the shell ----
    collar_h_mult=3.0,     # [A] collar length / screw diameter
    collar_wall=2.5,       # [A] radial wall; the labyrinth is cut into it
    lab_n=3,               # [A] placeholder groove count
    lab_w_ratio=0.4,       # [A] groove width / pitch, the pitch itself is a fraction of the collar
    lab_pitch_ratio=0.35,  # [A] groove pitch / collar length
    lab_d_ratio=0.25,      # [A] groove depth / collar wall
    knob_bolt_n=4,         # [Ed] bolts the knob module up into the shell
    # ---- joystick spring cross pins: side access. v0.4 has no exported pin axis yet. ----
    cross_pin_d=1.6,       # [A] cross pin diameter
    pin_clear_ratio=0.2,   # [A] hole over the pin, as a fraction of the pin
    pin_below_ratio=0.15,  # [A] pin centre below the faceplate underside, as a fraction of the plate height above the PCB
    seat_gap=0.08,         # [A] air so the cover, the shell and the PCB do not fuse in the model
    nest_gap=0.05,         # [A] air, PCB front face to the ledge stop (solids stay apart)
    ledge_ratio=0.60,      # [A] ledge width / wall, inboard of the PCB edge
    preload_ratio=0.04,    # [A] shell-rim seat recessed by this fraction of the cover field; the PCB land touches first
    clamp_t_ratio=0.45,    # [A] clamp tongue / cover field, thin enough to close the preload
    clamp_keep=0.45,       # [A] clamp overlap uses this fraction of the nearest B-side edge clearance
    cover_pocket=0.40,     # [A] air, pocket wall to the rear envelope (d_big_tip)
    pcb_clear=0.60,        # [A] air, PCB edge to the inner side wall
    rear_clear=0.80,       # [A] air, d_big_tip envelope to the inner side wall
    fuse=0.02,             # [A] overlap so adjacent walls fuse into one solid
    cut_slop=0.50,         # [A] cutters run this far past the face they open
    edge_w=2.2,            # [A] light-pipe band at the faceplate rim
    edge_t=1.2,            # [A] thinned rim (≥ sla_min, thinner than the 2.5 plate so it lights)
    ligament_t=1.2,        # [A] bridge between the knob hole and the joystick hole
    web_min=0.80,          # [A] smallest plan web, = sla_min
    pad_extra=1.0,         # [A] full-thickness pad past the rail-hole radius
    # ---- bottom TFT, on the PCB, shining out through the clear shell [L] design-notes ----
    # 2.0" 320×240 (4:3). Active size from the diagonal; no datasheet part is named yet.
    tft_in=2.0,            # [L] inch
    tft_px=(320, 240),     # [L]
    tft_air=1.0,           # [A] window starts this far above the PCB (the glass is not bonded)
    tft_gap=0.80,          # [A] keep-out beyond the active area, and off walls / the scanner
    # ---- laser light-show, PLACEHOLDER only. Knob agent is moving the feel motor to the bottom. ----
    # Do not change the PCB. 2× in the top corners under the joystick; laser_n=1 is the centred alternative.
    laser_n=2,             # [A] FLAG
    laser_w=12.0,          # [A] FLAG module width
    laser_d=8.0,           # [A] FLAG module depth along Y
    laser_h=8.0,           # [A] FLAG height above the PCB
    mass_max=140.0,        # [A] g, resin shell only (the PETG cover is separate)
    stl_tol=0.08,          # [A] STL chord tolerance, mm
    stl_ang=0.3,           # [A] STL angular tolerance, rad
    usdz_tol=0.15,         # [A] Quick Look mesh chord, mm
    scan_clear=0.50,       # [A] swept beam to the knob and to the joystick envelope
)

IMPORTS = {"electronics": ["pcb_w", "pcb_above", "pcb_below"],
           "under_pcb": ["d_big_tip"]}
EXPORTS = ["panel_w", "panel_h", "hp", "place_y", "knob_hole_r",
           "joy_hole", "z_fp0", "z_fp1", "z_foot", "fp_to_pcb"]


def _clear_rect(cx, cy, r, x0, y0, x1, y1):
    """Air between a circle and an axis-aligned rectangle. Negative means they overlap."""
    dx = max(x0 - cx, 0.0, cx - x1)
    dy = max(y0 - cy, 0.0, cy - y1)
    return math.hypot(dx, dy) - r


def _place_for(x, y_edge, rc):
    """place_y that puts (x, y_edge) on a circle of radius rc about the knob. Joystick v0.4 rule."""
    if abs(x) >= rc - 1e-9:
        return -y_edge
    return -y_edge + math.sqrt(rc * rc - x * x)


def _json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except OSError:
        return {}


def _data_files():
    here = os.path.dirname(os.path.abspath(__file__))
    kicad = os.path.normpath(os.path.join(here, "..", "electronics", "kicad"))
    return (os.path.join(kicad, "cad_constraints.json"),
            os.path.join(kicad, "knob-main-pcb", "pcb_proxy.json"))


def _knob_top(cons, fallback):
    """Knob-top z from cad_constraints when the knob branch writes it; else the snapshot."""
    for key in ("z_knob_top", "knob_top"):
        if key in cons and isinstance(cons[key], (int, float)):
            return float(cons[key]), "cad_constraints"
    return float(fallback), "placeholder"


def _pcb_outline(cons, pcb_w, above, below):
    pcb = cons.get("pcb")
    if isinstance(pcb, (list, tuple)) and len(pcb) == 3:
        return float(pcb[0]), float(pcb[1]), float(pcb[2]), "cad_constraints"
    return float(pcb_w), float(above), float(below), "interface"


def _bside_clear(parts, pcb_w, above, below):
    """Smallest plan gap from a B-side box to the PCB outline. Negative means the box crosses the edge."""
    x1 = pcb_w / 2.0
    y0, y1 = -below, above
    best = min(x1, y1 - y0)
    hit = ""
    for p in parts:
        hx, hy = p["w"] / 2.0, p["l"] / 2.0
        d = min((p["x"] - hx) + x1, x1 - (p["x"] + hx), (p["y"] - hy) - y0, y1 - (p["y"] + hy))
        if d < best:
            best, hit = d, p.get("ref", "")
    return best, hit


def derive(D):
    sla = D["sla_min"]
    # opening uses the larger of the live knob and the v0.17 / joystick design size
    D["knob_od_used"] = max(D["knob_od"], D["knob_od_design"])
    D["knob_r"] = D["knob_od_used"] / 2
    D["half_w"] = D["scr_w"] / 2 + D["bz_lip"]
    D["half_h"] = D["scr_h"] / 2 + D["bz_lip"]
    D["slide"] = D["tol_sla"] + D["sw_tilt"]
    D["knob_rc"] = D["knob_r"] + 2 * D["tol_mjf"] + D["slide"]
    D["place_y"] = max(_place_for(0.0, -D["half_h"], D["knob_rc"]),
                       _place_for(D["half_w"], -D["half_h"], D["knob_rc"]))
    D["hole_hw"] = D["half_w"] - D["fp_overlap"]
    D["hole_hh"] = D["half_h"] - D["fp_overlap"]
    D["car_hw"] = D["hole_hw"] - D["slide"] - D["tol_sla"]
    D["car_hh"] = D["hole_hh"] - D["slide"] - D["tol_sla"]
    D["joy_hole"] = (2 * D["hole_hw"], 2 * D["hole_hh"])
    # press rebate, same stack as the joystick proxy
    D["press_travel"] = D["tol_sla"] + D["sw_push"]
    D["fp_rebate"] = D["press_travel"] + D["tol_sla"]
    # Faceplate from the knob top. The bezel still rests on the plate; the plate is no longer
    # parked 5 mm under the knob. Knob top comes from cad_constraints when that key lands.
    cons_path, proxy_path = _data_files()
    cons = _json(cons_path)
    D["knob_top_used"], D["knob_top_src"] = _knob_top(cons, D["z_knob_snap"])
    D["z_fp1"] = D["knob_top_used"] - D["knob_proud"]
    D["z_fp0"] = D["z_fp1"] - D["wall"]
    D["fp_t"] = D["wall"]
    D["fp_to_pcb"] = D["z_fp1"]
    D["z_bz0"] = D["z_fp1"] + D["up_gap"]
    D["z_bz1"] = D["z_bz0"] + D["bz_t"]
    # 10HP panel. The box behind the rail ears is one rectangle: shell and cover share it.
    # The PCB is inset from that rectangle by the wall plus the drop-in clearance, on all four sides.
    _, above, below, src = _pcb_outline(cons, D["pcb_w"], D["pcb_above"], D["pcb_below"])
    D["pcb_live_above"] = above
    D["pcb_live_below"] = below
    D["pcb_src"] = src
    D["hp"] = int(D["hp_scope"])
    D["panel_w"] = D["hp"] * D["hp_pitch"] - D["hp_gap"]
    D["panel_w_scope"] = D["panel_w"]
    D["panel_x0"] = -D["panel_w"] / 2.0
    D["panel_x1"] = D["panel_w"] / 2.0
    D["panel_y1"] = D["axis_by"]
    D["panel_y0"] = D["axis_by"] - D["panel_h"]
    D["panel_yc"] = (D["panel_y0"] + D["panel_y1"]) / 2.0
    D["body_y1"] = D["panel_y1"] - D["rail_clear"]
    D["body_y0"] = D["panel_y0"] + D["rail_clear"]
    D["body_yc"] = (D["body_y0"] + D["body_y1"]) / 2.0
    D["x_out1"] = D["panel_w"] / 2.0
    D["x_out0"] = -D["x_out1"]
    D["x_in1"] = D["x_out1"] - D["wall"]
    D["x_in0"] = -D["x_in1"]
    D["y_in1"] = D["body_y1"] - D["wall"]
    D["y_in0"] = D["body_y0"] + D["wall"]
    D["pcb_x1"] = D["x_in1"] - D["pcb_clear"]
    D["pcb_y1"] = D["y_in1"] - D["pcb_clear"]
    D["pcb_y0"] = D["y_in0"] + D["pcb_clear"]
    D["nest_w"] = 2.0 * D["pcb_x1"]
    D["nest_above"] = D["pcb_y1"]
    D["nest_below"] = -D["pcb_y0"]
    D["pcb_max_w"] = D["nest_w"]
    # The PCB drops in from the back. Its back face is flush with the shell rim; the ledge
    # stops the front face. nest_gap keeps the two solids from fusing.
    D["z_rim"] = D["z_pcb_back"]
    D["z_ledge0"] = D["nest_gap"]
    D["z_ledge1"] = D["z_ledge0"] + D["wall"]
    D["ledge_w"] = D["ledge_ratio"] * D["wall"]
    D["screw_boss_r"] = D["screw_d"] * (0.5 + D["boss_wall_mult"])
    D["pad_r"] = D["screw_boss_r"]
    D["hole_r"] = D["screw_d"] * (0.5 + D["screw_hole_ratio"])
    D["tip_clear"] = D["tip_clear_ratio"] * D["screw_d"]
    # Boss axis is inside the PCB; the post uses the wall for its outer half and the board is notched.
    br = D["screw_boss_r"]
    D["boss_x"] = D["x_out1"] - D["web_min"] - br
    D["hp_need_w"] = D["panel_w"]
    D["z_seat"] = D["seat_gap"]
    # Placeholder rear stack: bearing 2 bottom behind the PCB back. Same arithmetic as under_pcb
    # (back panel seat + flange − bearing width). The retainer plate on sub/assembly-v017 replaces
    # rear_panel_snap when it reports a depth; the cover cavity then moves with it. The cavity
    # depth itself is not changed here.
    B = D["brg"]
    D["rear_stack"] = D["rear_panel_snap"] - B["ft"] + B["B"]
    D["z_bearing_bot"] = D["z_pcb_back"] - D["rear_stack"]
    D["cover_depth"] = D["rear_stack"] * (1.0 + D["cover_clear_ratio"])
    D["z_cover_in"] = D["z_pcb_back"] - D["cover_depth"]
    D["cbore_depth"] = D["head_k"] + D["head_below"]
    D["cbore_r"] = D["screw_dk"] / 2.0 + D["cbore_clear"]
    D["cover_t"] = D["pocket_wall"]
    D["z_cover_out"] = D["z_cover_in"] - D["cover_t"]
    # Clamping rim. The PCB land is seat_gap off the board; the shell-rim seat is recessed a
    # further preload_gap so the screws clamp the PCB before the cover bottoms on the rim.
    # The tongue is thinner than the pocket wall so it can close that gap.
    D["preload_gap"] = D["preload_ratio"] * D["cover_t"]
    D["z_pcb_land"] = D["z_pcb_back"] - D["seat_gap"]
    D["z_rim_seat"] = D["z_pcb_land"] - D["preload_gap"]
    D["clamp_t"] = D["clamp_t_ratio"] * D["cover_t"]
    D["z_flange_out"] = D["z_rim_seat"] - D["clamp_t"]
    D["cover_under"] = D["cover_under_mult"] * D["screw_d"]
    D["pad_h"] = max(0.0, D["cover_under"] + D["cbore_depth"] - D["clamp_t"])
    D["z_pad_out"] = D["z_flange_out"] - D["pad_h"]
    D["cover_skin"] = D["clamp_t"] + D["pad_h"] - D["cbore_depth"]
    D["z_foot"] = min(D["z_pad_out"], D["z_cover_out"])
    D["z_wall0"] = D["z_rim"]
    avail = (D["z_fp0"] - D["tip_clear"]) - D["z_rim"]
    D["engage"] = min(D["engage_mult"] * D["screw_d"], avail)
    D["knob_hole_r"] = D["knob_r"] + D["knob_rad_clear"]
    # bridge between the two openings, along +Y
    D["joy_y_near"] = D["place_y"] - D["hole_hh"]
    D["joy_y_far"] = D["place_y"] + D["hole_hh"]
    D["bezel_y_near"] = D["place_y"] - D["half_h"]
    D["bezel_y_far"] = D["place_y"] + D["half_h"]
    D["web_knob_joy"] = D["joy_y_near"] - D["knob_hole_r"]
    D["edge_top_w"] = D["panel_y1"] - D["bezel_y_far"]
    # carrier corner vs the rounded opening (local to the joystick centre)
    r = D["hole_corner_r"]
    cx, cy = D["hole_hw"] - r, D["hole_hh"] - r
    D["car_corner_dist"] = math.hypot(D["car_hw"] - cx, D["car_hh"] - cy)
    D["car_in_hole"] = D["hole_corner_r"] - D["car_corner_dist"]
    # side clearances the HP choice is supposed to buy
    D["side_air"] = (D["x_in1"] - D["x_in0"] - D["nest_w"]) / 2
    D["rear_air"] = (D["x_in1"] - D["x_in0"]) / 2 - D["d_big_tip"] / 2
    # B-side keep-out: KiCad proxy boxes plus the pad courtyards written into cad_constraints.
    boxes = list(_json(proxy_path).get("back_parts") or [])
    feel = cons.get("feel") or {}
    pw, pl = (feel.get("pad") or (1.8, 1.8))[:2]
    for xy in cons.get("fm_pad_xy") or []:
        boxes.append({"ref": "feel pad", "x": xy[0], "y": xy[1], "w": pw, "l": pl})
    rod_r = cons.get("rod_pad_r")
    if isinstance(rod_r, (int, float)) and rod_r > 0:
        boxes.append({"ref": "rod pad", "x": 0.0, "y": 0.0, "w": 2.0 * rod_r, "l": 2.0 * rod_r})
    D["bside_clear"], D["bside_ref"] = _bside_clear(boxes, D["nest_w"], D["nest_above"], D["nest_below"])
    D["clamp_overlap"] = max(D["sla_min"], D["clamp_keep"] * D["bside_clear"])
    # Outer skin matches the shell. On X the rear envelope sets how thick that skin can be;
    # it stays at least the SLA minimum and never outside the shell line.
    ex, ey = D["enc_xy"]
    D["cover_side"] = min(D["wall"], max(D["sla_min"], D["x_out1"] - (abs(ex) + D["d_big_tip"] / 2.0 + D["cover_pocket"])))
    D["void_x1"] = D["x_out1"] - D["cover_side"]
    D["void_x0"] = -D["void_x1"]
    D["void_y0"] = D["y_in0"]
    D["void_y1"] = D["y_in1"]
    D["pocket_gap"] = min(ex - D["void_x0"], D["void_x1"] - ex, ey - D["void_y0"], D["void_y1"] - ey) - D["d_big_tip"] / 2.0
    # rail screws. Bottom stations stay on the Doepfer 7.5 mm grid.
    # Top stations move outboard of the joystick opening: the bezel crosses the usual columns,
    # and a Eurorack rail takes the nut anywhere along its slot.
    x_std0 = D["panel_x0"] + D["rail_inset"]
    x_std1 = D["panel_x0"] + D["rail_inset"] + (D["hp"] - 3) * D["hp_pitch"]
    D["rail_x_std"] = (x_std0, x_std1)
    push = D["hole_hw"] + D["rail_hole_d"] / 2 + D["web_min"]
    limit = D["panel_w"] / 2 - D["rail_hole_d"] / 2 - D["web_min"]

    def _station(x):
        if abs(x) >= push:
            return x
        out = math.copysign(push, x if x else 1.0)
        return out if abs(out) <= limit else x

    D["rail_x_top"] = (_station(x_std0), _station(x_std1))
    D["rail_y_top"] = D["panel_y1"] - D["rail_edge"]
    D["rail_y_bot"] = D["panel_y0"] + D["rail_edge"]
    D["rail_pad_r"] = D["rail_hole_d"] / 2 + D["pad_extra"]
    # scanner, bottom-left inner corner (−X, −Y). Motor axis inset so the fillet bead is clear.
    mr = D["scan_motor_d"] / 2
    D["motor_r"] = mr
    D["mirror_r"] = D["mirror_d"] / 2
    # far enough in that the mirror disc clears both walls; the can is smaller than the disc
    D["x_mot"] = D["x_in0"] + D["mirror_r"] + D["scan_motor_clear"]
    D["y_mot"] = D["y_in0"] + D["mirror_r"] + D["scan_motor_clear"]
    D["z_mot0"] = D["z_seat"]
    D["z_mot1"] = D["z_mot0"] + D["scan_motor_len"]
    D["z_mirror"] = D["z_mot1"]
    # film just outside the can, on the +X side, still under the mirror disc
    D["x_beam"] = D["x_mot"] + mr + D["film_gap"] + D["film_w"] / 2
    D["y_beam"] = D["y_mot"]
    D["beam_off"] = D["x_beam"] - D["x_mot"]
    # shelf tied to the bottom wall, clear of the can
    lip = D["sla_min"]
    D["shelf_x0"] = D["x_mot"] + mr + D["scan_motor_clear"]
    D["shelf_x1"] = D["x_beam"] + D["film_w"] / 2 + lip
    D["shelf_y0"] = D["y_in0"]
    D["shelf_y1"] = D["y_beam"] + D["film_w"] / 2 + lip
    D["shelf_z0"] = D["shelf_z"] - D["shelf_t"] / 2
    D["shelf_z1"] = D["shelf_z"] + D["shelf_t"] / 2
    # groove, open toward +Y (into the cavity) so the film slides in before the PCB
    sc = D["slot_clear"]
    D["slot_x0"] = D["x_beam"] - D["film_w"] / 2 - sc
    D["slot_x1"] = D["x_beam"] + D["film_w"] / 2 + sc
    D["slot_y0"] = D["y_beam"] - D["film_w"] / 2 - sc
    D["slot_y1"] = D["shelf_y1"] + D["cut_slop"]
    D["slot_z0"] = D["shelf_z"] - D["film_t"] / 2 - sc
    D["slot_z1"] = D["shelf_z"] + D["film_t"] / 2 + sc
    D["slot_lip"] = (D["shelf_t"] - (D["slot_z1"] - D["slot_z0"])) / 2
    # VCSEL on the PCB, under the film, emitting +Z
    D["x_vc"] = D["x_beam"]
    D["y_vc"] = D["y_beam"]
    D["z_vc0"] = D["nest_gap"]
    D["z_vc1"] = D["vcsel_h"]
    # swept fan: along the inner left wall and the inner bottom wall, then up to the rim
    D["beam_x"] = D["x_in0"] + D["beam_gap"] + D["beam_t"] / 2
    D["beam_y"] = D["y_in0"] + D["beam_gap"] + D["beam_t"] / 2
    D["beam_z1"] = D["z_fp0"] - D["beam_gap"]
    # Bottom TFT window. 2.0" active area, as low as the ledge allows, and to the right of the
    # scanner bay so the mirror and the grating shelf stay out of the light path.
    diag = D["tft_in"] * 25.4
    aspect = D["tft_px"][0] / D["tft_px"][1]
    D["tft_w"] = diag * aspect / math.hypot(aspect, 1.0)
    D["tft_h"] = D["tft_w"] / aspect
    gap = D["tft_gap"]
    scan_x1 = max(D["shelf_x1"], D["x_mot"] + D["mirror_r"]) + gap
    # stay inboard of the side ledge as well as the wall; the ledge is shell, not a window
    D["win_x1"] = min(D["x_in1"], D["pcb_x1"] - D["ledge_w"]) - gap
    D["win_x0"] = max(scan_x1, D["win_x1"] - D["tft_w"])
    D["win_y0"] = D["pcb_y0"] + D["ledge_w"] + gap
    D["win_y1"] = min(D["win_y0"] + D["tft_h"], -D["knob_hole_r"] - gap)
    D["win_w"] = D["win_x1"] - D["win_x0"]
    D["win_h"] = D["win_y1"] - D["win_y0"]
    D["tft_z0"] = D["tft_air"]
    D["tft_z1"] = D["z_fp0"] - gap   # the plain faceplate over this rectangle is the window itself
    D["tft_short_w"] = max(0.0, D["tft_w"] - D["win_w"])
    # Laser placeholders, on the PCB under the joystick, not printed. Two top corners.
    ly = D["pcb_y1"] - D["ledge_w"] - D["laser_d"] / 2.0 - gap
    lx = D["pcb_x1"] - D["ledge_w"] - D["laser_w"] / 2.0 - gap
    if D["laser_n"] == 1:
        D["lasers"] = ((0.0, ly),)
    else:
        D["lasers"] = ((-lx, ly), (lx, ly))
    # collar under the knob opening, and the placeholder labyrinth
    D["collar_h"] = D["collar_h_mult"] * D["screw_d"]
    D["z_collar0"] = D["z_fp0"] - D["collar_h"]
    D["collar_r"] = D["knob_hole_r"] + D["collar_wall"]
    D["lab_pitch"] = D["collar_h"] * D["lab_pitch_ratio"]
    D["lab_w"] = D["lab_pitch"] * D["lab_w_ratio"]
    D["lab_d"] = D["collar_wall"] * D["lab_d_ratio"]
    D["lab_z0"] = D["z_collar0"] + (D["collar_h"] - (D["lab_n"] - 1) * D["lab_pitch"]) / 2.0
    # knob bolts: on the bolt circle outside the collar, on the underside of the plate,
    # clear of the joystick opening and of the rail zone. The free arc is the bottom.
    D["bolt_r"] = D["collar_r"] + D["seat_gap"] + D["screw_boss_r"]
    limit_x = D["panel_w"] / 2.0 - D["screw_boss_r"] - D["web_min"]
    bolts = []
    steps = 36
    for i in range(steps):
        ang = math.pi * (1.0 + (i + 0.5) / steps)   # π .. 2π: the bottom half, away from the bezel at +Y
        x = D["bolt_r"] * math.cos(ang)
        y = D["bolt_r"] * math.sin(ang)
        if abs(x) > limit_x or y - D["screw_boss_r"] < D["body_y0"] or y + D["screw_boss_r"] > D["body_y1"]:
            continue
        # keep the whole boss (and the head below it) inboard of the side walls
        if abs(x) + D["screw_boss_r"] + D["seat_gap"] > D["x_in1"]:
            continue
        dx = max(abs(x) - D["hole_hw"], 0.0)
        dy = max(abs(y - D["place_y"]) - D["hole_hh"], 0.0)
        if math.hypot(dx, dy) < D["screw_boss_r"] + D["seat_gap"]:
            continue
        if _clear_rect(x, y, D["screw_boss_r"], D["win_x0"], D["win_y0"], D["win_x1"], D["win_y1"]) < D["tft_gap"]:
            continue
        if any(math.hypot(x - px, y - py) < 2.0 * D["screw_boss_r"] + D["seat_gap"] for px, py in bolts):
            continue
        bolts.append((x, y))
        if len(bolts) >= D["knob_bolt_n"]:
            break
    D["knob_bolts"] = tuple(bolts)
    D["z_bolt0"] = D["z_fp0"] - D["engage"]
    # Cover screws. The axis is inside the PCB outline; a notch in the board lets the
    # resin post occupy the corner and the wall. Upper pair sits in the gap between the
    # knob and the joystick opening. Lower pair sits just above the scanner mirror.
    bx = D["boss_x"]
    gap = D["boss_gap"]
    dmin = D["knob_hole_r"] + br + gap
    y_knob = math.sqrt(max(0.0, dmin * dmin - bx * bx))
    y_joy = D["joy_y_near"] - br - gap
    D["boss_y_room"] = y_joy - y_knob
    y_hi = (y_knob + y_joy) / 2.0 if y_joy >= y_knob else y_knob
    y_scan = D["y_mot"] + D["mirror_r"] + br + gap
    y_floor = max(y_scan, D["pcb_y0"] + br + gap)
    y_lo = y_floor if y_floor <= -y_knob else -y_knob
    # a boss that would sit in the TFT light path moves above the window, still clear of the knob
    y_above = D["win_y1"] + br + D["tft_gap"]

    def _y_for(x):
        y = y_lo
        if _clear_rect(x, y, br, D["win_x0"], D["win_y0"], D["win_x1"], D["win_y1"]) < D["tft_gap"]:
            y = y_above if y_above <= -y_knob else y
        return y

    D["corners"] = ((-bx, _y_for(-bx)), (bx, _y_for(bx)), (-bx, y_hi), (bx, y_hi))
    D["knob_bolts"] = tuple(
        (x, y) for x, y in D["knob_bolts"]
        if all(math.hypot(x - cx, y - cy) >= 2.0 * br + gap for cx, cy in D["corners"]))
    D["notch_r"] = br + D["notch_gap"]
    D["boss_knob_clear"] = min(math.hypot(x, y) - D["knob_hole_r"] - br for x, y in D["corners"])
    D["boss_joy_clear"] = min(
        _clear_rect(x, y, br, -D["hole_hw"], D["joy_y_near"], D["hole_hw"], D["joy_y_far"]) for x, y in D["corners"])
    D["boss_scan_clear"] = min(math.hypot(x - D["x_mot"], y - D["y_mot"]) - D["mirror_r"] - br for x, y in D["corners"])
    D["boss_win_clear"] = min(
        _clear_rect(x, y, br, D["win_x0"], D["win_y0"], D["win_x1"], D["win_y1"]) for x, y in D["corners"])
    D["z_thread0"] = D["z_rim"]
    D["tap_len"] = D["engage"] - D["screw_p"]
    D["z_thread1"] = D["z_thread0"] + D["tap_len"]
    D["z_tip"] = D["z_thread1"]
    D["z_bolt_tip"] = D["z_bolt0"] + D["tap_len"]
    # cross-pin axis: through each side wall, at the joystick, just under the plate
    D["pin_z"] = D["z_fp0"] - D["pin_below_ratio"] * (D["z_fp0"] - D["z_seat"])
    D["pin_hole_r"] = D["cross_pin_d"] * (0.5 + D["pin_clear_ratio"])
    D["edge_depth"] = D["fp_t"] - D["edge_t"]
    D["lig_depth"] = D["fp_t"] - D["ligament_t"]
    D["scope_short"] = D["pcb_w"] - D["pcb_max_w"]
    D["bezel_w"] = 2.0 * D["half_w"]
    D["bezel_margin"] = (D["panel_w"] - D["bezel_w"]) / 2.0
    D["bezel49_margin"] = (D["panel_w"] - 49.0) / 2.0
    D["collar_od"] = 2.0 * D["collar_r"]
    D["collar_margin"] = (D["panel_w"] - D["collar_od"]) / 2.0
    # top rail screws: room beside the joystick opening, inside the panel, with an SLA web both sides
    top_span = (D["panel_w"] - D["joy_hole"][0]) / 2.0
    D["rail_top_web"] = (top_span - D["rail_hole_d"]) / 2.0
    D["rail_top_ok"] = 1.0 if D["rail_top_web"] >= D["sla_min"] else 0.0
    D["ox"] = 0.0
    D["oy"] = 0.0
    return D
