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
    row("PCB side air", D["side_air"], D["pcb_clear"],
        f"{D['hp']}HP panel {D['panel_w']:.2f} (scope {D['hp_scope']}HP is {D['panel_w_scope']:.2f}, short by {D['scope_short']:.2f})")
    row("rear envelope air", D["rear_air"], D["rear_clear"], f"d_big_tip Ø{D['d_big_tip']:.2f}")
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
    z_cavity = (D["z_seat"] + D["z_fp0"]) / 2
    wall_x = (D["panel_x0"] + D["x_in0"]) / 2
    row("side wall is material", 1.0 if _inside(case, wall_x, D["body_yc"], z_cavity) else 0.0, 1.0, "probe in the left wall")
    row("knob hole is open", 0.0 if _inside(case, D["ox"], D["oy"], z_mid) else 1.0, 1.0, "probe on the dial axis, in the plate")
    row("shell back is open for the cover", 0.0 if _inside(case, D["ox"], D["oy"], (D["z_cover_in"] + D["z_pcb_back"]) / 2) else 1.0, 1.0,
        "the shell drops down over the PCB; the PETG plate closes the back")
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
    row("countersink vs cover thickness", D["cover_t"] - D["csink_depth"], D["csink_depth"] * D["cover_web_ratio"],
        f"ISO 10642 countersink {D['csink_depth']:.2f} in PETG {D['cover_t']:.2f} (smoky grey, see-through)")
    row("corner screw tip vs PCB", D["z_pcb_back"] - D["z_tip"], D["tip_clear"],
        f"tip z {D['z_tip']:.2f}, PCB back {D['z_pcb_back']:.2f}")
    row("knob bolt tip vs front skin", D["z_fp1"] - D["z_bolt_tip"], D["wall"],
        f"{len(D['knob_bolts'])} bolts up into the shell, tip z {D['z_bolt_tip']:.2f}")
    row("knob bolts present", float(len(D["knob_bolts"])), float(D["knob_bolt_n"]), "lower arc, clear of the bezel")
    # a point in the boss wall (outside the thread) is resin; the pin hole opens the side wall
    cx, cy = D["corners"][0]
    row("corner boss is resin", 1.0 if _inside(case, cx + D["screw_boss_r"] * 0.7, cy, (D["z_thread0"] + D["z_tip"]) / 2) else 0.0, 1.0,
        "printed thread, no insert")
    row("cross pin opens the side", 0.0 if _inside(case, D["panel_x0"] + D["wall"] / 2, D["place_y"], D["pin_z"]) else 1.0, 1.0,
        f"Ø{D['cross_pin_d']:.2f} pin, hole Ø{2 * D['pin_hole_r']:.2f}, z {D['pin_z']:.2f} (axis not yet exported by joystick v0.4)")

    vol = case.volume
    mass = vol * D["case_rho"]
    row("case mass", mass, D["mass_max"],
        f"volume {vol:.0f} mm³ ({vol / 1000:.1f} cm³), UTR-8100 {D['case_rho'] * 1000:.2f} g/cm³", higher_ok=False)
    row("one hollow shell", 1.0 if vol > 0 else 0.0, 1.0,
        f"overall {D['panel_w']:.2f} × {D['panel_h']:.2f} × {D['z_fp1'] - D['z_foot']:.2f} mm")
    return r
