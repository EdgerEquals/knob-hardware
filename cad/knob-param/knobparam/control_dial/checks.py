"""control_dial LOCAL checks (own parts + interface values only)."""
import math
from build123d import Rot
from ..common.checks import Rows, maxr
from .parts import hall_arm as hall

def checks(D, parts):
    T = D["tgt"]; r = Rows("control_dial"); row = r.row
    scr = [s for n, s in parts.items() if n.startswith("screen ") and "jumper" not in n]
    r_max = max([D["scr_far"]] + [maxr(s) for s in scr])
    row("knob OD vs screen (R - outermost screen point)", D["R"] - r_max, T["knob_od_vs_screen"], f"knob Ø{D['knob_od']:.2f}, screen offset {D['scr_off']:.2f} from the FPC exit")
    on = D["screen_on_dial"]; TR = (-D["travel_deg"], 0, D["travel_deg"])
    if on:
        row("dial lip wall (far side, lip bonded round the panel)", D["lip_wall"], T["lip_wall"],
            f"lip ID Ø{D['lip_id']:.2f} = panel Ø{D['S']['od']:.2f} + 2×bond {D['lip_bond_gap']:.2f}, centred on the panel (offset {D['scr_off']:.3f}); near side {D['lip_wall_near']:.2f}; {D['lip_wall_lines']} lines × {D['nozzle']:g}")
        if D["lip_closed"]:
            row("dial lip wall outside the COF-bend pocket (closed ring)", D["lip_wall_bend"], T["lip_wall"],
                f"bend reaches r {D['bend_reach_ax']:.3f} + clear {D['bend_clear']:g}; knob Ø{D['knob_od']:.2f} (min {D['knob_od_min']:.3f})")
            row("dial up-stop: free lift to the adapter board (no cup)", D["dial_lift"], 0.1, "board clamped by the rod nut; 45° race carries the knob up-load into the dial")
            row("dial up-stop: free lift (max)", D["dial_lift"], 0.5, "", higher_ok=False)
    else:
        row("dial lip wall (far side of the offset panel)", D["lip_wall"], T["lip_wall"], f"lip ID Ø{D['lip_id']:.2f} = panel Ø{D['S']['od']:.2f} + 2×(offset {D['scr_off']:.2f} + run {D['run_gap']:.2f})")
    dial = parts["control dial"]
    fp = [n for n in parts if n.endswith("FPC + B2B")][0]
    dmin = min(parts[fp].distance_to(Rot(0, 0, t) * dial) for t in ((0,) if on else TR))
    row("FPC fold / COF bend vs dial" + ("" if on else " (±travel)"), dmin, 0.1, "fold corners inside the lip ID, bend in the lip slot" + (" (turn together)" if on else ""))
    pn = [n for n in parts if n.endswith(" panel")][0]
    if on:
        row("panel vs dial lip (bond gap, turns with the dial)", parts[pn].distance_to(dial), max(D["lip_bond_gap"] - 0.01, 0.0), "no running gap [Ed]")
        row("FPC strap bend strain at ±travel (%)", D["strap_strain_pct"], D["strap_strain_max"],
            f"L {D['strap_L']:.1f}, R {D['strap_R']:.0f} mm, t {D['strap_t']:g}, end moves {D['strap_end_move']:.2f}", higher_ok=False)
        b2b = parts[fp]
        if "adapter cup (fixed)" in parts:
          bmin = min((Rot(0, 0, t) * b2b).distance_to(parts["adapter cup (fixed)"]) for t in TR)
          row("rotating B2B / fold vs fixed adapter cup (±travel)", bmin, T["carrier_vs_cup"])
          row("screen carrier vs fixed adapter cup", parts["screen carrier (on dial)"].distance_to(parts["adapter cup (fixed)"]), T["carrier_vs_cup"], f"carrier_run {D['carrier_run']:g}")
    else:
        row("panel vs dial lip (running gap)", parts[pn].distance_to(dial), D["run_gap"] - 0.01)
    row(f"screen carrier magnet: stray field at the {D['carr_stray_to']} / range", D["carr_stray_mt"] / D["carr_stray_rng"], D["carr_stray_max"],
        f"{D['carr_stray_mt']:.3f} mT on-axis dipole worst case" + ("; co-rotates with the sensor -> fixed offset, calibrated out" if D["rel_sensor"] else "; turns ±travel over a fixed sensor -> tiny, calibrated"), higher_ok=False)
    if D["hall_layout"] == "vernier":
        row("Hall bar vs ring tips (radial)", D["skirt_id"] / 2 - D["hv_r_out"] - D["hv_pad_r"], T["arm_vs_ring"], f"outer magnet r {D['hv_r_out']:.2f}")
        tc = [parts[n] for n in parts if n.startswith("thrust")]
        if tc:
            row("Hall spoke vs thrust balls / cage (±travel)", min(hall.arm(D, t).distance_to(q) for t in TR for q in tc), 0.3)
    else:
        row("Hall paddle vs ring tips (radial)", D["ha_r_tip"] - D["ha_pad_r1"], 0.3)
    if D["kb_groove_h"] > 0:
        cr_, cz_ = D["kb_seat_c"]; px, pz = D["kb_seat_contact"]
        ang = math.degrees(math.atan2(cz_ - pz, px - cr_)) % 180          # contact -> groove centre direction
        row("seat: 45° contact line kept (|angle - 45|, deg)", abs(ang - 135.0) if ang > 90 else abs(ang - 45.0), 0.01,
            f"groove R{D['kb_seat_r']:g} centred {D['kb_seat_r'] - D['kb_ball_d'] / 2:.2f} past the ball centre on the 45° line", higher_ok=False)
        row("seat: groove rim half-width - ball chord at the cone face", D["kb_seat_w"] - D["kb_ball_cap_w"], 0.0,
            f"depth {D['kb_groove_h']:.3g}: groove ±{D['kb_seat_w']:.3f}, ball ±{D['kb_ball_cap_w']:.3f}")
        if D["kb_race"] == "chamfer":
            row("dial: material under the cup-boss bore (above the hub bottom)", D["z_bore0"] - D["z_hub0"], D["dial_bore_floor"] - 1e-6,
                f"socket on the tube {D['hold_socket_len']:.2f}" if D["adapter_cup"] else "no cup: plain tube ID")
            row("seat: groove land to the 45° face ends (min)", D["kb_land"], T["race_land"],
                f"track at {D['kb_race_at']:g} of the {D['kb_face_len']:.2f} gusset face, both faces grooved")
        else:
            row("seat: ball vs dial plain tube (radial)", D["kb_ball_tube"], T["race_ball_tube"])
    return r
