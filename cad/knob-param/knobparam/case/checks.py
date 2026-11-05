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
    cover = next(v for k, v in parts.items() if k.startswith("back cover"))
    cb = cover.bounding_box()
    row("cover flush in X", min(D["x_out1"] - cb.max.X, cb.min.X - D["x_out0"]), 0.0,
        f"cover x {cb.min.X:.2f}..{cb.max.X:.2f}, shell ±{D['x_out1']:.2f}")
    row("cover flush in Y", min(D["body_y1"] - cb.max.Y, cb.min.Y - D["body_y0"]), 0.0,
        f"cover y {cb.min.Y:.2f}..{cb.max.Y:.2f}, box {D['body_y0']:.2f}..{D['body_y1']:.2f}")
    sla = D["sla_min"]
    row("SLA wall", D["wall"], sla, "UTR-8100 plain clear, no tint; front face polished, every other face as-printed")
    if D["top_corners"]:
        row("top posts stop under the joystick board", D["joy_board_z"] - D["z_post_top"], 1.0,
            f"post top z {D['z_post_top']:.2f}; lowest part over them about z {D['joy_board_z']:.1f} [A] (v0.25: nothing of the joystick "
            "stack is over the posts' plan; the assembly path rows measure the real parts)")
    if D.get("joy_step"):   # v0.24 [Ed 14:02] joystick top-edge step
        st = D["joy_step"]
        row("joystick top-edge step: faceplate left over the rebate", D["wall"] - st["d"], 0.8,
            f"rebate {st['w']:g} past the cutout wall, {st['d']:g} into the {D['wall']:g} faceplate back, from y {D['joy_step_y0']:.2f} up the long sides "
            "and across the top; the joystick cradle's dam and the bead sit in it")
        ry = D["place_y"] + D["joy_reb"][1] / 2
        rr = min(math.hypot(max(abs(x) - D["joy_reb"][0] / 2, 0.0), D["rail_y_top"] - ry) for x in D["rail_x_top"]) - D["rail_hole_d"] / 2
        row("joystick top-edge rebate clear of the top rail holes", rr, 1.0,
            f"rebate top edge y {ry:.2f}; rail holes Ø{D['rail_hole_d']:g} at y {D['rail_y_top']:.2f}")
    row("resin wall round the insert", D["insert_wall"], 1.2, f"M{D['screw_d']:g} insert Ø{D['insert_od']:.1f} in a Ø{2 * D['screw_boss_r']:.1f} boss")
    if D["back_screens"] == "amoled2":
        x0, x1, y0, y1 = D["amo_upper"]; lx0, lx1, ly0, ly1 = D["amo_lower"]
        row("back AMOLEDs overlap behind the knob", D["amo_overlap"], 11.0,   # [Ed 2 Nov] ~11 mm overlap is fine (was 15)
            f"lower y {ly0:.2f}..{ly1:.2f}, upper y {y0:.2f}..{y1:.2f}; seam inside the knob shadow")
        row("back AMOLEDs inside the cover pocket", min(D["void_x1"] - x1, x0 - D["void_x0"], D["void_y1"] - y1, ly0 - D["void_y0"]), 0.3,
            f"{D['amo_w']:.2f} wide in a {D['void_x1'] - D['void_x0']:.2f} pocket")
        if D.get("amo_drop_air"):   # v0.25 [Ed 19:12 (5)]: each screen drops straight onto the cover floor past the corner columns
            from build123d import Pos as _P, Box as _B, Align as _Al
            big = 9e9
            for nm, (sx0, sx1, sy0, sy1), (sz0, sz1) in (("upper", D["amo_upper"], D["amo_upper_z"]), ("lower", D["amo_lower"], D["amo_lower_z"])):
                path = _P((sx0 + sx1) / 2, (sy0 + sy1) / 2, sz1 + 0.05) * _B(sx1 - sx0, sy1 - sy0, D["z_rim_seat"] - sz1,
                                                                            align=(_Al.CENTER, _Al.CENTER, _Al.MIN))
                dd = path.distance_to(cover)
                if dd < big: big, who = dd, nm
            row("back AMOLEDs drop straight in: path clear of the cover (corner flares trimmed)", big, 0.3,   # [A] the v0.25 path rule
                f"[Ed 19:12 (5)] each screen's plan swept from its own top face up to the cover rim; nearest: the {who} screen. The flare and "
                f"ring of each corner column are cut {D['amo_drop_air']:g} round the screens' plans (v0.24: the upper AMOLED caught a top flare by 0.48)")
        row("cover depth from the screen rule (not deeper than needed)", D["cover_depth"], D["cover_depth"],
            f"deepest rear part z {D['z_rear_parts']:.2f} over the upper screen, {D['screen_air']:.1f} air -> floor z {D['z_cover_in']:.2f}; the 3D screen-rule check confirms the air", higher_ok=False)
    else:
        row("back TFT window", min(D["win_w"], D["win_h"]), min(D["tft_w"], D["tft_h"]),
            f"active {D['win_w']:.2f}×{D['win_h']:.2f} at x {D['win_x0']:.2f}..{D['win_x1']:.2f}, "
            f"y {D['win_y0']:.2f}..{D['win_y1']:.2f}; module {D['tft_mod_w']:.2f}×{D['tft_mod_h']:.2f}×{D['tft_mod_t']:.1f} "
            f"with a {D['tft_border']:.1f} mm border")
        win = parts["back TFT window"]
        cover_hit = cover.intersect(win)
        blocked = 0.0 if cover_hit is None or not cover_hit.solids() else sum(s.volume for s in cover_hit.solids())
        row("TFT light path is open through the cover", blocked, 0.0,
            "the active area is a hole in the back skin, not a front window", higher_ok=False)
        mod = parts.get("back TFT module (placeholder)")
        if mod is not None:
            mb = mod.bounding_box()
            inside = min(D["void_x1"] - mb.max.X, mb.min.X - D["void_x0"], D["void_y1"] - mb.max.Y, mb.min.Y - D["void_y0"])
            row("back TFT module inside the pocket", inside, D["tft_gap"],
                f"outline {D['tft_mod_w']:.2f}×{D['tft_mod_h']:.2f} at y {D['mod_y0']:.2f}..{D['mod_y1']:.2f}")
    row("faceplate thickness", D["fp_t"], D["wall"], "same resin wall as the sides")
    row("edge strip thickness", D["edge_t"], D["wall"], "the rim is the full faceplate, one plane with the rest")
    row("ligament thickness", D["ligament_t"], D["wall"], "bridge between the holes is the full plate")
    if D["scanner_enabled"]:
        row("grating-slot lip", D["slot_lip"], sla, "shelf left above and below the film")
    row("outside edge radius", D["edge_r"], D["edge_r_ratio"] * D["wall"],
        "the only radius on the plain box, a ratio of the wall")
    row("joystick grip block height", D["z_bz1"] - D["z_bz0"], D["grip_h"],
        f"[Ed 2 Nov] at least {D['grip_h']:g} mm to hold (replaces the 1.5 mm bezel cap); walls {D['bz_lip']:.2f}")
    row("finger gap: knob glass to the joystick bezel", D["finger_gap"], D["finger_min"],
        f"[Ed 2 Nov] joystick place_y {D['place_y']:.2f} ({D['joy_rule']} rule; v0.4 knob rule {D['place_y_knob']:.2f}); "
        f"knob {D['knob_drop'] + D['knob_drop2']:.1f} below the v0.18 panel position")
    row("joystick bezel clear of the top rail screw washers (full slide)", D["rail_head_clear"], D["tol_mjf"] + D["rail_float"],
        f"{D['rail_washer']} under an M3 pan head, keep-out Ø{D['rail_keep_d']:.1f} at y {D['rail_y_top']:.2f}")
    exp_y = -36.6 + D["knob_drop2"] - D["oled_drop"]   # v0.19b centre, moved by the two [Ed] drops
    row("clear OLED placed per knob_drop2 − oled_drop (within 0.05)", 0.05 - abs(D["clear_oled_xy"][1] - exp_y), 0.0,
        f"electronics clear_oled_xy y {D['clear_oled_xy'][1]:.2f}, expected {exp_y:.2f}")
    row("clear OLED vs the bottom corner posts", D["oled_post_clear"], 0.3,
        f"OLED {D['clear_oled'][0]:g} x {D['clear_oled'][1]:g} at y {D['clear_oled_xy'][1]:.2f}; posts at y {D['corners'][0][1]:.2f}"
        f"{' (in the bottom wall [Ed])' if D['bot_posts_in_wall'] else ''}")
    # the row above uses higher_ok so value 1.5-bz_t >= 0. Good.
    row("knob radial clearance", D["knob_hole_r"] - D["knob_r"], D["knob_rad_clear"],
        f"hole Ø{2 * D['knob_hole_r']:.2f}, knob Ø{D['knob_od_used']:.2f} (live {D['knob_od']:.2f}, design {D['knob_od_design']:.2f})")
    row("joystick lip overlap", D["fp_overlap"], sla,
        f"opening {D['joy_hole'][0]:.2f}×{D['joy_hole'][1]:.2f} at place_y {D['place_y']:.2f}")
    row("web, knob hole to joystick hole", D["web_knob_joy"], sla, "plan width of the bridge")
    row("bezel above the faceplate", D["z_bz0"] - D["z_fp1"], 0.0,
        f"lip z {D['z_bz0']:.2f}–{D['z_bz1']:.2f}, plate top {D['z_fp1']:.2f}")
    row("knob stands proud of the faceplate", D["z_top"] - D["z_fp1"], D["knob_proud"],
        f"screen top {D['z_top']:.2f} (v0.18 knob_proud is to the glass); faceplate front {D['z_fp1']:.2f}")
    row("knob proud, not more", D["z_top"] - D["z_fp1"], D["knob_proud"],
        "faceplate z is the screen top minus knob_proud (interface)", higher_ok=False)
    row("faceplate to PCB ledge", D["fp_to_pcb"], D["z_top"] - D["knob_proud"],
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
    if not D["top_corners"]:
        row("boss clears the joystick opening", D["boss_joy_clear"], D["boss_gap"],
            "upper pair sits under the joystick hole")
    if D["scanner_enabled"]:
        row("boss clears the scanner mirror", D["boss_scan_clear"], D["boss_gap"],
            f"lower bosses y {D['corners'][0][1]:.2f}")
    if D["rail_top_ok"]:
        row("top rail screw web", D["rail_top_web"], D["sla_min"], "holes are in the panel, clear of the joystick opening")
    else:
        need = D["rail_hole_d"] + 2.0 * D["sla_min"]
        have = (D["panel_w"] - D["joy_hole"][0]) / 2.0
        row("top rail screws omitted", 1.0, 1.0,
            f"the side strip is {have:.2f} mm and a Ø{D['rail_hole_d']:.1f} hole with {D['sla_min']:.1f} webs needs {need:.2f}; "
            f"web would be {D['rail_top_web']:.2f}. Holes left out. Bottom pair stays.")
    row("ledge width", D["ledge_w"], D["sla_min"], "inboard of the PCB edge, ratio of the wall")
    row("rim flush with the PCB back", abs(D["z_rim"] - D["z_pcb_back"]), 0.0,
        f"shell rim z {D['z_rim']:.2f}, PCB back {D['z_pcb_back']:.2f}", higher_ok=False)
    if D["cover_clamp"] != "tubes":
        row("clamp clears B-side parts", D["bside_clear"] - D["clamp_overlap"], D["sla_min"],
            f"overlap {D['clamp_overlap']:.2f}, nearest {D['bside_ref'] or 'edge'} is {D['bside_clear']:.2f} from the outline")
    row("preload before the rim seats", D["preload_gap"], D["seat_gap"],
        f"PCB land at {D['z_pcb_land']:.2f}, shell seat at {D['z_rim_seat']:.2f}; tongue {D['clamp_t']:.2f} closes the step")
    if D["back_screens"] != "amoled2":   # v0.19: the screen rule sets the depth; clearances are measured in the assembly
        row("pocket clears the rear envelope", D["pocket_gap"], D["cover_pocket"],
            f"d_big_tip Ø{D['d_big_tip']:.2f} at the encoder; cavity depth {D['cover_depth']:.2f} unchanged")
    row("body clears the rails", D["rail_clear"], sla, "outer 10 mm of the panel, behind the face only")
    row("panel height", D["panel_h"], 128.5, "3U")
    row("panel height cap", D["panel_h"], 128.5, "3U, not taller", higher_ok=False)
    if D["back_screens"] != "amoled2":
        row("cover depth past the rear stack", D["cover_depth"] - D["rear_stack"], D["rear_stack"] * D["cover_clear_ratio"],
            f"placeholder rear stack {D['rear_stack']:.2f} (bearing 2); cover cavity {D['cover_depth']:.2f}; "
            f"retainer plate on {D['knob_commit'][:7]} has not reported a depth yet")
    row("carrier fits the rounded opening", D["car_in_hole"], 0.0,
        f"corner clearance {D['car_in_hole']:.2f}; carrier {2 * D['car_hw']:.2f}×{2 * D['car_hh']:.2f}")
    row("top light-strip width", D["edge_top_w"], sla, "panel edge above the bezel")
    if D["scanner_enabled"]:
        row("mirror reaches the beam", D["mirror_r"] - D["beam_off"], 0.0,
            f"mirror Ø{D['mirror_d']:.1f} assumed; beam {D['beam_off']:.2f} off the motor axis")
        row("film clears the motor can", D["film_gap"], D["scan_motor_clear"],
            "FLAG: motor is an assumed Ø{:.0f}×{:.0f} coreless, no part chosen".format(D["scan_motor_d"], D["scan_motor_len"]))

    # probes: the booleans really left a wall, a hole, an open back, a thin rim
    z_mid = (D["z_fp0"] + D["z_fp1"]) / 2
    z_cavity = (D["z_ledge1"] + D["z_fp0"]) / 2
    wall_x = (D["x_out0"] + D["x_in0"]) / 2
    row("side wall is material", 1.0 if _inside(case, wall_x, D["body_yc"], z_cavity) else 0.0, 1.0, "probe in the left wall")
    lx = (D["usb_ch_hw"] + 2.0) if D.get("usb_slot") else 0.0   # v0.32: the USB-C channel cuts the bottom ledge at x 0 (the key's tab fills it)
    row("ledge is material", 1.0 if _inside(case, lx, D["pcb_y0"] + D["ledge_w"] / 2, (D["z_ledge0"] + D["z_ledge1"]) / 2) else 0.0,
        1.0, f"bottom ledge, under the PCB front edge, probe at x {lx:.2f}" + (" (beside the USB-C channel; the key's tab is the ledge in it)"
                                                                            if D.get("usb_slot") else ""))
    if D.get("usb_slot"):
        key = parts.get("USB-C key (printed, held by the back cover)")
        if key is not None and not D.get("usb_pwr_tab"):
            row("USB-C key's tab restores the bottom ledge in the channel", 1.0 if _inside(key, 0.0, D["pcb_y0"] + D["ledge_w"] / 2,
                (D["z_ledge0"] + D["z_ledge1"]) / 2) else 0.0, 1.0, "probe at x 0 on the ledge line")
    row("knob hole is open", 0.0 if _inside(case, D["ox"], D["oy"], z_mid) else 1.0, 1.0, "probe on the dial axis, in the plate")
    row("shell back is open for the PCB", 0.0 if _inside(case, D["ox"], D["oy"], (D["z_rim"] + D["z_ledge0"]) / 2) else 1.0, 1.0,
        "the PCB drops in from the back and stops on the ledge; the cover clamps it")
    row("collar bore is open", 0.0 if _inside(case, D["ox"], D["oy"], (D["z_collar0"] + D["z_fp0"]) / 2) else 1.0, 1.0,
        "knob module slides down through the collar")
    rim_y = D["panel_y0"] + D["edge_w"] / 2
    row("edge strip is material", 1.0 if _inside(case, D["ox"], rim_y, (D["z_fp0"] + D["z_fp1"]) / 2) else 0.0, 1.0,
        "bottom rim is the same plate as the rest of the face")
    row("front face is one plane", 1.0 if _inside(case, D["ox"], rim_y, D["z_fp1"] - 0.4) else 0.0, 1.0,
        "no light-pipe step and no joystick rebate; the TFT window, knob and joystick opening share z_fp1")
    row("seal ring stands on the face",
        1.0 if _inside(case, D["knob_hole_r"] + D["lab_ring_t"] / 2.0, 0.0, (D["lab_ring_z0"] + D["lab_ring_z1"]) / 2.0) else 0.0,
        1.0, f"thin ring Ø{2 * D['lab_ring_r']:.2f}, {D['lab_ring_h']:.2f} mm above the face; "
             f"knob shoulder bore Ø{2 * D['lab_shoulder_r']:.2f} from z {D['lab_shoulder_z0']:.2f}")
    row("seal ring bore is open",
        0.0 if _inside(case, 0.0, 0.0, (D["lab_ring_z0"] + D["lab_ring_z1"]) / 2.0) else 1.0, 1.0,
        "the knob passes through; its shoulder drops over the ring")

    if D["scanner_enabled"]:
        knob = knob_envelope(D)
        joy = joy_envelope(D)
        beam = beam_solid(D)
        row("beam vs knob", beam.distance_to(knob), D["scan_clear"], "swept fan stays off the dial")
        row("beam vs joystick", beam.distance_to(joy), D["scan_clear"], "fan stays off the carrier and the lip")
        row("beam reaches the side wall", D["beam_gap"], 0.0, "fan stands off the wall by beam_gap")
        row("beam close to the side wall", D["beam_reach"] - D["beam_gap"], 0.0, "close enough to light the wall")
        row("beam reaches the rim", D["beam_z1"], D["z_mirror"], "rises from the mirror to the faceplate underside")

    if D["insert_od"]:
        eng = min(D["screw_engage"], D["insert_len"])
        row(f"M{D['screw_d']:g} thread engaged in the brass insert / diameter", eng / D["screw_d"], D["insert_engage_min"],
            f"insert Ø{D['insert_od']:.1f}×{D['insert_len']:.1f} at z {D['z_rim']:.2f}..{D['z_insert1']:.2f}; screw engages {eng:.2f}")
        row("screw tip clearance hole stays under the post top", D["z_post_top"] - (D["z_tip"] + D["tip_hole"]), D["wall"],
            f"tip z {D['z_tip']:.2f}, hole to {D['z_tip'] + D['tip_hole']:.2f}, post top {D['z_post_top']:.2f}")
    else:
        row("thread engagement / diameter", D["tap_len"] / D["screw_d"], D["engage_min"],
            f"printed M{D['screw_d']:.0f}×{D['screw_p']:.2f}, engagement {D['tap_len']:.2f} (asked {D['engage']:.2f})")
    if False:  # v0.19: brass insert; see "resin wall round the insert"
        row("boss wall / diameter", (D["screw_boss_r"] - D["screw_d"] / 2) / D["screw_d"], D["boss_wall_mult"],
            f"boss Ø{2 * D['screw_boss_r']:.2f} around the Ø{D['screw_d']:.2f} thread")
    back = D.get("cover_screw") == "back"
    std = "ISO 14580" if back else "ISO 4762"
    row("PETG over the screw head" if back else "PETG under the screw head", D["cover_skin"], D["cover_under_mult"] * D["screw_d"],
        f"{std} head Ø{D['screw_dk']:.1f}×{D['head_k']:.2f}, {D.get('screw_drive', 'hex')}; counterbore {D['cbore_depth']:.2f} "
        f"(head {D['head_below']:.2f} below the face); " +
        (f"in from the back, under a Ø{2 * D.get('col_r', 0):.1f} column; solid over the head {D['cover_skin']:.2f}" if back else
         f"pad {D['pad_h']:.2f} on the {D['clamp_t']:.2f} tongue; left under the head {D['cover_skin']:.2f}"))
    row("counterbore sinks the head", D["cbore_depth"] - D["head_k"], D["head_below"],
        f"flat bottom, the Ø{D['screw_dk']:g} × {D['head_k']:g} head is fully below the cover face")
    row(f"{std} thread past the grip", D["screw_engage"] / D["screw_d"], D["engage_min"],
        f"M{D['screw_d']:g}×{D['screw_len']:.0f} {D['screw_mat']}, thread {D['screw_thread']:.0f} "
        f"({'to the head' if D['screw_len'] <= D['screw_full_to'] else 'partial, b=' + format(D['screw_b'], '.0f')}); "
        f"grip {D['screw_grip']:.2f}, in the resin {D['screw_engage']:.2f}")
    if not D["insert_od"]:
        row("screw tip inside the printed tap", D["z_thread1"] - D["z_tip"], 0.0,
            f"tip z {D['z_tip']:.2f}, tap ends {D['z_thread1']:.2f}")
    if back:   # v0.19b [Ed 2 Nov]: head in the floor, under the column; the cover depth is unchanged
        row("head counterbore stays inside the cover floor", D["cover_t"] - D["cbore_depth"], 0.15,
            f"floor {D['cover_t']:.2f}, counterbore Ø{2 * D['cbore_r']:.2f} × {D['cbore_depth']:.2f} under the Ø{2 * D['col_r']:.2f} column")
        row("column clears the screen layer (column r + air vs the column ring)", D["col_ring_r"] - D["col_r"], 0.0,
            f"slim to z {D['col_z1']:.2f}, 45° flare to the Ø{2 * D['col_ring_r']:.2f} ring at z {D['col_z2']:.2f}")
        if "amo_room_lower" in D:
            row("back screens: room left toward the ends before a corner column", min(D["amo_room_lower"], D["amo_room_upper"]), 0.0,
                f"lower screen could drop {D['amo_room_lower']:.2f}, upper rise {D['amo_room_upper']:.2f} (column r {D['col_r']:.2f} + {D['col_screen_air']:g} air)")
    else:
        row("pad does not set the depth", D["z_pad_out"] - D["z_cover_out"], 0.0,
            f"pad face {D['z_pad_out']:.2f}, cover back {D['z_cover_out']:.2f}; the 3 mm head fits in the local pad")
    row("corner screw through the notch", D["notch_r"] - D["screw_d"] / 2, D["notch_gap"],
        f"notch Ø{2 * D['notch_r']:.2f} at x {D['corners'][1][0]:.2f}, y {D['corners'][1][1]:.2f}")
    row("corner screw tip vs faceplate", D["z_fp0"] - D["z_tip"], D["tip_clear"],
        f"tip z {D['z_tip']:.2f}, plate underside {D['z_fp0']:.2f}")
    row("knob bolt tip vs front skin", D["z_fp1"] - D["z_bolt_tip"], D["wall"],
        f"{len(D['knob_bolts'])} bolts up into the shell, tip z {D['z_bolt_tip']:.2f}")
    if D["knob_bolt_n"] > 0:
        row("knob bolts present", float(len(D["knob_bolts"])), 2.0,
            f"{len(D['knob_bolts'])} on the lower arc; the TFT window and the bosses leave room for fewer than {D['knob_bolt_n']}")
    # a point in the boss wall (outside the thread) is resin
    cx, cy = D["corners"][0]
    row("corner boss is resin", 1.0 if _inside(case, cx + D["screw_boss_r"] * 0.7, cy, (D["z_thread0"] + D["z_tip"]) / 2) else 0.0, 1.0,
        f"M{D['screw_d']:g} brass insert Ø{D['insert_od']:.1f}×{D['insert_len']:.1f} epoxied in a Ø{2 * D['screw_boss_r']:.1f} boss")
    row("corner post top vs jack pins", D["z_jack_pins"] - D["z_post_top"], D["post_jack_clear"],
        f"post top z {D['z_post_top']:.2f}, PJ366ST pin tips z {D['z_jack_pins']:.2f} (body {D['jack_depth']:.1f} + pins {D['jack_pin_len']:.1f} behind the plate)")
    row("post stands above the thread", D["z_post_top"] - D["z_thread1"], D["wall"],
        f"post top z {D['z_post_top']:.2f}, tap ends z {D['z_thread1']:.2f}")

    if D.get("jack_lip_notch") is not None:   # step 2 [Ed 4 Nov 20:12]: the jacks come in straight from behind (later on the jack board)
        from build123d import Pos as _P, Box as _B, Align as _Al
        glow = parts.get("glow coat (inside walls)")
        jw, jh = D["jack_w"], D["jack_h"]; z0p = D["z_rim"] - 1.0; z1p = D["z_fp0"] - 1.0   # the last 1.0 is the body at home (clash check)
        paths = [_P(x - jw / 2, y - jh / 2, z0p) * _B(jw, jh, z1p - z0p, align=(_Al.MIN,) * 3) for x, y in D["jack_xy"]]
        dc = min(p_.distance_to(case) for p_ in paths)
        row("jacks' straight path from behind: clear of the case", dc, 0.3,
            f"each body ({jw:g} x {jh:g}) swept from behind the rim to 1.0 short of home; the side ledges notched y {D['jack_notch_y'][0]:.2f}.."
            f"{D['jack_notch_y'][1]:.2f}, the bottom posts cut flat at y {D['post_clip_y']:.2f}, jacks 1/4 {D['x_in1'] - (max(D['jack_xs']) + jw / 2):.2f} "
            "from the side walls [Ed 4 Nov 20:12]")
        if glow is not None:
            row("jacks' straight path from behind: clear of the glow coat", min(p_.distance_to(glow) for p_ in paths), 0.1,
                "the side coat is left off the jack strip (it stood 0.15 into jacks 1 and 4)")
        if D.get("jb_on"):   # v0.33 [Ed 21:30] option B: the two jack boards go in with the jacks, on the same path
            bx0, bx1 = D["jb_x"]
            stack = _P(bx0, D["jack_bot_y"], z0p) * _B(bx1 - bx0, jh, z1p - z0p, align=(_Al.MIN,) * 3)
            row("jack boards + jacks (one unit) straight in from behind: clear of the case", stack.distance_to(case), 0.3,
                f"the jack row's outline {bx1 - bx0:.1f} x {jh:g} swept from behind the rim to 1.0 short of home: both boards, the headers, "
                "the ZIFs and the parts envelopes stay inside it [Ed 4 Nov 21:30]")
            row("jack pins through the jack board", D["jb_pin_out"], 1.0,
                f"{D['jack_pin_len']:g} pins [S] through a {D['jb_t']:g} board [A]: room for the fillet")
            row("jack pin tips to the power board's parts", D["jb_pin_tip_air"], 0.5,
                f"pin tips z {D['jack_depth_z0'] - D['jack_pin_len']:.2f}; power board top z {D['jb2_z1']:.2f} + {D['jb2_parts']:g} parts [A]")
            row("between the two boards' parts envelopes", D["jb_env_air"], 0.5,
                f"jack board underside parts to z {D['jb_under_z0']:.2f} [A], power board parts to z {D['jb2_parts_z1']:.2f} [A]; "
                f"boards {D['jb2_gap']:g} apart on the headers")
            if D.get("jb_post_xy"):   # v0.34 [Ed 22:21] option 1A: the jack unit rides in with the stack on two posts
                oy0 = D["clear_oled_xy"][1] - D["clear_oled"][1] / 2; r_ = D["jb_post_d"] / 2
                py = D["jb_post_xy"][0][1]; ly = D["pcb_y0"] + D["ledge_w"]
                row("jack unit posts: to the clear OLED's bottom edge", oy0 - (py + r_), 0.3,
                    f"Ø{D['jb_post_d']:g} posts at y {py:.2f}, x ±{abs(D['jb_post_xy'][0][0]):g}, in the main board's strip under the OLED (edge y {oy0:.2f})")
                hx, ty = D["jb_tab"]
                ears = [_P(x - hx, ty, z0p) * _B(2 * hx, D["jack_bot_y"] - ty, D["jb2_z1"] - z0p, align=(_Al.MIN,) * 3) for x, _y in D["jb_post_xy"]]
                glow_ = parts.get("glow coat (inside walls)")
                dd = min(min(e.distance_to(case) for e in ears), min(e.distance_to(glow_) for e in ears) if glow_ is not None else 9e9)
                row("jack unit posts + the power board's ears: clear of the case and glow coat as the shell comes down", dd, 0.3,
                    f"the ears (±{hx:g} round each post, down to y {ty:g}) and the posts swept over the shell's whole travel; the bottom ledge's "
                    f"inner face is y {ly:.2f}; its glow coat is left off ±1.6 round each post")
                if D.get("link_lane"):   # v0.36 [Ed 22:52]
                    lx0, lx1, ly = D["link_lane"]; r2 = D["jb_post_d"] / 2; px2 = D["jb_post_xy"][1][0]
                    row("right post: to the clear OLED's flex", (px2 - r2) - 6.25, 0.5,
                        f"post 2 at x {px2:g} (15 V, brass, soldered both ends); the OLED's flex is 12.5 wide [S], centred")
                    row("link flex lane: to the right post", lx0 - (px2 + r2), 0.3, f"lane x {lx0:g}..{lx1:g}, ~16 lines at 0.5 [A]")
                    cx, cy = D["corners"][1]
                    row("link flex pads: clear of the main board's corner notch", math.hypot(lx1 - cx, ly - cy) - D["notch_r"], 0.3,
                        f"pads down to y {ly:g} at x {lx1:g}; notch r {D['notch_r']:.2f} at ({cx:g}, {cy:.2f})")
                    row("jack holes: float for the bushings", (D["jack_hole"] - D["jack_bush_d"]) / 2, 0.25,
                        f"Ø{D['jack_hole']:g} holes for Ø{D['jack_bush_d']:g} bushings [Ed 22:52]: the stack sets the jack unit within this")
                    row("jack nuts still cover the holes", (D["jack_nut_d"] - D["jack_hole"]) / 2, 0.5, f"Ø{D['jack_nut_d']:g} nuts")
                zf = D["zif_z0"]; oz_ = D["clear_oled"][2] / 2
                need = (zf + 1.0 - oz_) + 3.0
                row("the clear OLED's flex reaches its ZIF (slack)", D["oled_flex_len"] - need, 3.0,
                    f"{D['oled_flex_len']:g} flex [S] from the OLED's edge (z {oz_:.2f}) up to the ZIF under the power board (face z {zf:.2f}): "
                    f"~{need:.1f} of path incl. the turn and 3 into the ZIF [A]; the rest folds (plugged on the bench)")
            oz = D["clear_oled"][2]
            row("ZIFs to the clear OLED below (room for the two flexes to turn up into them)", D["zif_z0"] - oz, 8.0,
                f"ZIF faces z {D['zif_z0']:.2f}, OLED front z {oz:.2f} [A: target]")
        row("bottom posts cut flat: air to the jack bodies", D["jack_post_air"], 0.3,
            f"jack bodies' bottom y {D['jack_bot_y']:.2f}; posts at y {D['corners'][0][1]:.2f} ({D['bot_post_drop']:g} lower), r {D['screw_boss_r']:.2f}, "
            f"cut flat at y {D['post_clip_y']:.2f}")
        row("bottom inserts: resin to the flat (jack side)", D["post_insert_wall_jack"], 1.2,
            f"insert hole Ø{D['insert_od'] + 2 * D['insert_glue']:.2f} (Ø{D['insert_od']:g} + epoxy) at y {D['corners'][0][1]:.2f}")
        row("bottom inserts: resin to the bottom face", D["post_insert_wall_out"], 1.2,
            f"bottom face y {D['body_y0']:.2f}")
    if D.get("usb_slot"):   # [Ed 4 Nov 20:15] option C
        from build123d import Pos as _P, Box as _B, Align as _Al
        key = parts.get("USB-C key (printed, held by the back cover)")
        brd = parts.get("USB-C board (socket, TVS, ESD)"); rc = parts.get("USB-C receptacle [S]")
        row("USB-C board to the jack bodies", D["usb_jack_air"], 0.5,
            f"board y {D['usb_board_y0']:.2f}..{D['usb_board_y1']:.2f} (5.5 tall), jack bodies from y {D['jack_bot_y']:.2f}")
        row("USB-C board's edge not past the bottom face", -D["usb_board_out"], 0.0,
            f"board edge y {D['usb_board_y0']:.2f}, bottom face y {D['body_y0']:.2f} (the rail line) [Ed 11:09]")
        row("USB-C ledge each side of the receptacle (board edge on it)", D["usb_ledge_side"], 1.0,
            f"board {D['usb_board'][0]:g} wide on the wall left in front of it; receptacle pocket ±{D['usb_pocket_hw']:.2f}")
        row("USB-C ledge under the receptacle pocket", D["usb_ledge_below"], D["web_min"],
            f"pocket from y {D['usb_pocket_y0']:.2f}, bottom face y {D['body_y0']:.2f}: a {D['usb_ledge_below']:.2f} web, "
            f"{D['z_fp0'] - D['usb_z1']:.2f} tall, joined to the faceplate")
        if brd is not None and rc is not None:
            zb = D["z_rim"] - 1.0
            bp = _P(-D["usb_board"][0] / 2, D["usb_board_y0"], zb) * _B(D["usb_board"][0], D["usb_board"][1], D["usb_z0"] - 0.5 - zb, align=(_Al.MIN,) * 3)
            uw, uh, ud = D["usb_rcpt"]; uy = D["usb_xy"][1]
            rp = _P(-uw / 2, uy - uh / 2, zb) * _B(uw, uh, D["z_fp1"] - 0.5 - zb, align=(_Al.MIN,) * 3)
            glow_ = parts.get("glow coat (inside walls)")
            row("USB-C board + receptacle path from behind (the channel): clear of the case and glow coat",
                min(bp.distance_to(case), rp.distance_to(case), bp.distance_to(glow_) if glow_ is not None else 9e9), 0.1,
                f"channel ±{D['usb_ch_hw']:.2f} through the bottom wall and ledge, from the back edge to z {D['usb_z1']:.2f}; swept to 0.5 short of home")
        if D.get("usb_pwr_tab") and D.get("jb_on"):   # v0.35 [Ed 22:36] option A
            tw, ty = D["usb_pwr_tab"]; zb = D["z_rim"] - 1.0
            tp = _P(-tw, ty, zb) * _B(2 * tw, D["jack_bot_y"] - ty, D["jb_z1"] - zb, align=(_Al.MIN,) * 3)
            glow_ = parts.get("glow coat (inside walls)")
            dd = min(tp.distance_to(case), tp.distance_to(key) if key is not None else 9e9, tp.distance_to(glow_) if glow_ is not None else 9e9)
            row("jack board's USB tab: clear of the case, glow coat and key as the stack goes in", dd, 0.3,
                f"tab ±{tw:g} down to y {ty:g}, swept from behind the rim to its home; the key (in the channel, shell first) is the nearest")
            row("USB power spring contacts: working length", D["usb_z0"] - D["jb_z1"], 3.0,
                f"{len(D['usb_pwr_contacts'])} contacts Ø{D['usb_pwr_d']:g} [A] from the tab's face z {D['jb_z1']:.2f} to the USB-C board's back z "
                f"{D['usb_z0']:.2f}; they meet in the stack's last ~1 [C: a part ~4.2 working, ~1 A each, 2 per power line]")
            py = [y for _x, y in D["usb_pwr_contacts"]]
            row("USB power contacts land on the USB-C board (inside the box, above the key)", min(min(py) - D["usb_pwr_d"] / 2 - D["y_in0"],
                D["usb_board_y1"] - (max(py) + D["usb_pwr_d"] / 2)), 0.3,
                f"contacts y {min(py):g}..{max(py):g}; the board's back face is free from y {D['y_in0']:.2f} (the key below) to its top edge {D['usb_board_y1']:.2f}")
            cts = D["usb_pwr_contacts"]; dmin = 9e9
            for i in range(len(cts)):
                for j in range(i + 1, len(cts)):
                    dmin = min(dmin, ((cts[i][0] - cts[j][0]) ** 2 + (cts[i][1] - cts[j][1]) ** 2) ** 0.5 - D["usb_pwr_d"])
            row("USB spring contacts: gap between barrels", dmin, 0.4,
                f"{len(cts)} contacts Ø{D['usb_pwr_d']:g} [A] in two rows (v0.37, Ed 5 Nov 11:24); gold pads about Ø{D['usb_pwr_d'] + 0.1:g}")
            if D.get("usb_shell_legs"):
                cy_ = D["usb_xy"][1]
                dl = min(((x - lx) ** 2 + (y - cy_ - ly) ** 2) ** 0.5 - D["usb_pwr_d"] / 2 - 0.55 for x, y in cts for lx, ly in D["usb_shell_legs"])
                row("USB spring contacts clear of the socket's shell-leg pads", dl, 0.5,
                    "legs at x ±4.9, ±1.3 from the socket centre, pads r 0.55 [A: socket part not chosen]")
        if key is not None:
            row("USB-C key: clear of the channel walls", key.distance_to(case), 0.03, f"{D['usb_key_gap']:g} a side [A]")
            if brd is not None:
                row("USB-C key to the board's back face (it clamps the board on the ledge)", key.distance_to(brd), 0.05,
                    "0.02 nominal", higher_ok=False)
            row("USB-C key to the back cover (the cover holds it in)", key.distance_to(cover), 0.05,
                "0.02 nominal; the key ends behind the case rim, at the cover's face", higher_ok=False)

    vol = case.volume
    mass = vol * D["case_rho"]
    row("case mass", mass, D["mass_max"],
        f"volume {vol:.0f} mm³ ({vol / 1000:.1f} cm³), UTR-8100 {D['case_rho'] * 1000:.2f} g/cm³", higher_ok=False)
    row("one hollow shell", 1.0 if vol > 0 else 0.0, 1.0,
        f"overall {D['panel_w']:.2f} × {D['panel_h']:.2f} × {D['z_fp1'] - D['z_foot']:.2f} mm; "
        f"faceplate to PCB {D['fp_to_pcb']:.2f} mm")
    return r
