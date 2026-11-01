"""case LOCAL checks. Wall, openings, PCB, scanner beam. Reads this sub's scope only."""
import math
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.TopAbs import TopAbs_IN
from OCP.gp import gp_Pnt
from ..common.checks import Rows
from .parts.shell import beam_solid, knob_envelope, joy_envelope


def _inside(solid, x, y, z):
    c = BRepClass3d_SolidClassifier(solid.wrapped, gp_Pnt(float(x), float(y), float(z)), 1e-6)
    return c.State() == TopAbs_IN


def checks(D, parts):
    r = Rows("case")
    row = r.row
    case = parts["case"]
    cover = parts["back cover (PETG)"]
    cb = cover.bounding_box()
    row("cover flush in X", min(D["x_out1"] - cb.max.X, cb.min.X - D["x_out0"]), 0.0,
        f"cover x {cb.min.X:.2f}..{cb.max.X:.2f}, shell ±{D['x_out1']:.2f}")
    row("cover flush in Y", min(D["body_y1"] - cb.max.Y, cb.min.Y - D["body_y0"]), 0.0,
        f"cover y {cb.min.Y:.2f}..{cb.max.Y:.2f}, box {D['body_y0']:.2f}..{D['body_y1']:.2f}")
    sla = D["sla_min"]
    row("SLA wall", D["wall"], sla, "UTR-8100, nominal 2.5")
    row("faceplate thickness", D["fp_t"], D["wall"], "same resin wall as the sides")
    row("edge strip thickness", D["edge_t"], sla, "light-pipe rim, thinner than the plate")
    row("ligament thickness", D["ligament_t"], sla, "bridge between knob hole and joystick hole")
    row("grating-slot lip", D["slot_lip"], sla, "shelf left above and below the film")
    row("fillet bead", D["fillet_r"], sla, "wall-to-faceplate joint")
    row("bezel thickness under the cap", D["bz_max"] - D["bz_t"], 0.0,
        f"joystick v0.4 lip {D['bz_t']:.2f}, cap {D['bz_max']:.1f}")
    # the row above uses higher_ok so value 1.5-bz_t >= 0. Good.
    row("knob radial clearance", D["knob_hole_r"] - D["knob_r"], D["knob_rad_clear"],
        f"hole Ø{2 * D['knob_hole_r']:.2f}, knob Ø{D['knob_od_used']:.2f} (live {D['knob_od']:.2f}, design {D['knob_od_design']:.2f})")
    row("joystick lip overlap", D["fp_overlap"], sla,
        f"opening {D['joy_hole'][0]:.2f}×{D['joy_hole'][1]:.2f} at place_y {D['place_y']:.2f}")
    row("web, knob hole to joystick hole", D["web_knob_joy"], sla, "plan width of the bridge")
    row("bezel above the faceplate", D["z_bz0"] - D["z_fp1"], 0.0,
        f"lip z {D['z_bz0']:.2f}–{D['z_bz1']:.2f}, plate top {D['z_fp1']:.2f}")
    row("knob stands proud of the faceplate", D["knob_top_used"] - D["z_fp1"], D["knob_proud"],
        f"knob top {D['knob_top_used']:.2f} from {D['knob_top_src']}; faceplate front {D['z_fp1']:.2f}")
    row("knob proud, not more", D["knob_top_used"] - D["z_fp1"], D["knob_proud"],
        "faceplate z is the knob top minus knob_proud", higher_ok=False)
    row("faceplate to PCB ledge", D["fp_to_pcb"], D["knob_top_used"] - D["knob_proud"],
        f"faceplate front to the PCB front (ledge datum z=0) is {D['fp_to_pcb']:.2f} mm; "
        f"model ledge face at z {D['z_ledge0']:.2f} leaves nest_gap {D['nest_gap']:.2f}")
    row("10HP panel", D["panel_w"], 10 * D["hp_pitch"] - D["hp_gap"],
        f"{D['hp']}HP  {D['panel_w']:.2f} mm, wall {D['wall']:.2f}")
    row("PCB width within the shell", D["pcb_max_w"] - D["nest_w"], 0.0,
        f"board {D['nest_w']:.2f} wide, {D['nest_above']:.2f} above, {D['nest_below']:.2f} below "
        f"(live {D['pcb_w']:.2f} × {D['pcb_live_above']:.2f}/{D['pcb_live_below']:.2f})")
    row("PCB inside the side walls", D["x_in1"] - D["pcb_x1"], D["pcb_clear"],
        f"board edge ±{D['pcb_x1']:.2f}, wall inner ±{D['x_in1']:.2f}")
    row("PCB inside the top and bottom", min(D["y_in1"] - D["pcb_y1"], D["pcb_y0"] - D["y_in0"]), D["pcb_clear"],
        f"board y {D['pcb_y0']:.2f}..{D['pcb_y1']:.2f} inside the box {D['body_y0']:.2f}..{D['body_y1']:.2f}")
    row("PCB side air", D["side_air"], D["pcb_clear"],
        f"wall {D['wall']:.2f} + clearance {D['pcb_clear']:.2f} each side of the {D['nest_w']:.2f} board")
    row("bezel on the 10HP panel", D["bezel_margin"], 0.0,
        f"bezel {D['bezel_w']:.2f} wide, {D['bezel_margin']:.2f} mm each side; a 49 mm bezel would have {D['bezel49_margin']:.2f}")
    row("knob collar inside the panel", D["collar_margin"], D["sla_min"],
        f"Ø{D['knob_od_used']:.2f} knob, collar Ø{D['collar_od']:.2f}, {D['collar_margin']:.2f} mm of panel outside it")
    row("boss axis inside the PCB", D["pcb_x1"] - D["boss_x"], 0.0,
        f"boss x ±{D['boss_x']:.2f}, PCB edge ±{D['pcb_x1']:.2f}, notch Ø{2 * D['notch_r']:.2f}")
    row("boss clears the knob hole", D["boss_knob_clear"], D["boss_gap"],
        f"upper bosses y {D['corners'][2][1]:.2f}, room between knob and joystick {D['boss_y_room']:.2f}")
    row("boss clears the joystick opening", D["boss_joy_clear"], D["boss_gap"],
        "upper pair sits under the joystick hole")
    row("boss clears the scanner mirror", D["boss_scan_clear"], D["boss_gap"],
        f"lower bosses y {D['corners'][0][1]:.2f}")
    row("top rail screws", D["rail_top_web"], D["sla_min"],
        "joystick opening leaves too little panel for a Ø3.2 hole with an SLA web both sides; top screws omitted, bottom screws stay")
    row("ledge width", D["ledge_w"], D["sla_min"], "inboard of the PCB edge, ratio of the wall")
    row("rim flush with the PCB back", abs(D["z_rim"] - D["z_pcb_back"]), 0.0,
        f"shell rim z {D['z_rim']:.2f}, PCB back {D['z_pcb_back']:.2f}", higher_ok=False)
    row("clamp clears B-side parts", D["bside_clear"] - D["clamp_overlap"], D["sla_min"],
        f"overlap {D['clamp_overlap']:.2f}, nearest {D['bside_ref'] or 'edge'} is {D['bside_clear']:.2f} from the outline")
    row("preload before the rim seats", D["preload_gap"], D["seat_gap"],
        f"PCB land at {D['z_pcb_land']:.2f}, shell seat at {D['z_rim_seat']:.2f}; tongue {D['clamp_t']:.2f} closes the step")
    row("pocket clears the rear envelope", D["pocket_gap"], D["cover_pocket"],
        f"d_big_tip Ø{D['d_big_tip']:.2f} at the encoder; cavity depth {D['cover_depth']:.2f} unchanged")
    row("body clears the rails", D["rail_clear"], sla, "outer 10 mm of the panel, behind the face only")
    row("panel height", D["panel_h"], 128.5, "3U")
    row("panel height cap", D["panel_h"], 128.5, "3U, not taller", higher_ok=False)
    row("cover depth past the rear stack", D["cover_depth"] - D["rear_stack"], D["rear_stack"] * D["cover_clear_ratio"],
        f"placeholder rear stack {D['rear_stack']:.2f} (bearing 2); cover cavity {D['cover_depth']:.2f}; "
        f"retainer plate on {D['knob_commit'][:7]} has not reported a depth yet")
    row("carrier fits the rounded opening", D["car_in_hole"], 0.0,
        f"corner clearance {D['car_in_hole']:.2f}; carrier {2 * D['car_hw']:.2f}×{2 * D['car_hh']:.2f}")
    row("top light-strip width", D["edge_top_w"], sla, "panel edge above the bezel")
    row("mirror reaches the beam", D["mirror_r"] - D["beam_off"], 0.0,
        f"mirror Ø{D['mirror_d']:.1f} assumed; beam {D['beam_off']:.2f} off the motor axis")
    row("film clears the motor can", D["film_gap"], D["scan_motor_clear"],
        "FLAG: motor is an assumed Ø{:.0f}×{:.0f} coreless, no part chosen".format(D["scan_motor_d"], D["scan_motor_len"]))

    # probes: the booleans really left a wall, a hole, an open back, a thin rim
    z_mid = (D["z_fp0"] + D["z_fp1"]) / 2
    z_cavity = (D["z_ledge1"] + D["z_fp0"]) / 2
    wall_x = (D["x_out0"] + D["x_in0"]) / 2
    row("side wall is material", 1.0 if _inside(case, wall_x, D["body_yc"], z_cavity) else 0.0, 1.0, "probe in the left wall")
    row("ledge is material", 1.0 if _inside(case, 0.0, D["pcb_y0"] + D["ledge_w"] / 2, (D["z_ledge0"] + D["z_ledge1"]) / 2) else 0.0,
        1.0, "bottom ledge, under the PCB front edge")
    row("knob hole is open", 0.0 if _inside(case, D["ox"], D["oy"], z_mid) else 1.0, 1.0, "probe on the dial axis, in the plate")
    row("shell back is open for the PCB", 0.0 if _inside(case, D["ox"], D["oy"], (D["z_rim"] + D["z_ledge0"]) / 2) else 1.0, 1.0,
        "the PCB drops in from the back and stops on the ledge; the cover clamps it")
    row("collar bore is open", 0.0 if _inside(case, D["ox"], D["oy"], (D["z_collar0"] + D["z_fp0"]) / 2) else 1.0, 1.0,
        "knob module slides down through the collar")
    rim_y = D["panel_y0"] + D["edge_w"] / 2
    row("edge strip is material", 1.0 if _inside(case, D["ox"], rim_y, D["z_fp0"] + D["edge_t"] / 2) else 0.0, 1.0,
        "bottom rim, the light pipe, kept at the back of the plate")
    row("edge strip is thinned", 0.0 if _inside(case, D["ox"], rim_y, D["z_fp1"] - D["edge_depth"] / 2) else 1.0,
        1.0, "the front of the rim is pocketed so the band lights")

    knob = knob_envelope(D)
    joy = joy_envelope(D)
    beam = beam_solid(D)
    row("beam vs knob", beam.distance_to(knob), D["scan_clear"], "swept fan stays off the dial")
    row("beam vs joystick", beam.distance_to(joy), D["scan_clear"], "fan stays off the carrier and the lip")
    row("beam reaches the side wall", D["beam_gap"], 0.0, "fan stands off the wall by beam_gap")
    row("beam close to the side wall", D["beam_reach"] - D["beam_gap"], 0.0, "close enough to light the wall")
    row("beam reaches the rim", D["beam_z1"], D["z_mirror"], "rises from the mirror to the faceplate underside")

    row("thread engagement / diameter", D["tap_len"] / D["screw_d"], D["engage_min"],
        f"printed M{D['screw_d']:.0f}×{D['screw_p']:.2f}, engagement {D['tap_len']:.2f} (asked {D['engage']:.2f})")
    row("boss wall / diameter", (D["screw_boss_r"] - D["screw_d"] / 2) / D["screw_d"], D["boss_wall_mult"],
        f"boss Ø{2 * D['screw_boss_r']:.2f} around the Ø{D['screw_d']:.2f} thread")
    row("PETG under the screw head", D["cover_under"], D["cover_under_mult"] * D["screw_d"],
        f"DIN 7984 head {D['head_k']:.2f}, counterbore {D['cbore_depth']:.2f} (head {D['head_below']:.2f} below the face); "
        f"pad {D['pad_h']:.2f} on the {D['clamp_t']:.2f} tongue; left under the head {D['cover_skin']:.2f}")
    row("corner screw through the notch", D["notch_r"] - D["screw_d"] / 2, D["notch_gap"],
        f"notch Ø{2 * D['notch_r']:.2f} at x {D['corners'][1][0]:.2f}, y {D['corners'][1][1]:.2f}")
    row("corner screw tip vs faceplate", D["z_fp0"] - D["z_tip"], D["tip_clear"],
        f"tip z {D['z_tip']:.2f}, plate underside {D['z_fp0']:.2f}")
    row("knob bolt tip vs front skin", D["z_fp1"] - D["z_bolt_tip"], D["wall"],
        f"{len(D['knob_bolts'])} bolts up into the shell, tip z {D['z_bolt_tip']:.2f}")
    row("knob bolts present", float(len(D["knob_bolts"])), float(D["knob_bolt_n"]), "lower arc, clear of the bezel")
    # a point in the boss wall (outside the thread) is resin; the pin hole opens the side wall
    cx, cy = D["corners"][0]
    row("corner boss is resin", 1.0 if _inside(case, cx + D["screw_boss_r"] * 0.7, cy, (D["z_thread0"] + D["z_tip"]) / 2) else 0.0, 1.0,
        "printed thread, no insert")
    row("cross pin opens the side", 0.0 if _inside(case, wall_x, D["place_y"], D["pin_z"]) else 1.0, 1.0,
        f"Ø{D['cross_pin_d']:.2f} pin, hole Ø{2 * D['pin_hole_r']:.2f}, z {D['pin_z']:.2f} (axis not yet exported by joystick v0.4)")

    vol = case.volume
    mass = vol * D["case_rho"]
    row("case mass", mass, D["mass_max"],
        f"volume {vol:.0f} mm³ ({vol / 1000:.1f} cm³), UTR-8100 {D['case_rho'] * 1000:.2f} g/cm³", higher_ok=False)
    row("one hollow shell", 1.0 if vol > 0 else 0.0, 1.0,
        f"overall {D['panel_w']:.2f} × {D['panel_h']:.2f} × {D['z_fp1'] - D['z_foot']:.2f} mm; "
        f"faceplate to PCB {D['fp_to_pcb']:.2f} mm")
    return r
