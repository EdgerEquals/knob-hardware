"""control_dial LOCAL checks (own parts + interface values only)."""
import math
from build123d import Rot
from ..common.checks import Rows, min_dist, posed, maxr
from .parts import hall_arm as hall

def _rib_defl(D):
    """In-plane tip deflection (mm) of the tapered rib as a cantilever, load at ha_rib_rload, root at the dial tube."""
    F, E = D["ha_rib_load"], D["ha_rib_E"]
    r0, rh, rF = D["ha_rib_r_hub"], D["ha_rib_r_head"], D["ha_rib_rload"]
    w0, w1 = D["ha_rib_w0"], D["ha_rib_w1"]
    z1, zc, zl, rs = D["ha_rib_z_top"], D["ha_rib_z_cage"], D["ha_rib_z_low"], D["ha_rib_r_step"]
    def w(r):
        return w0 + (w1 - w0) * (r - r0) / (rh - r0) if r <= rh else w1
    def h(r):
        return z1 - (zc if r < rs else zl)
    def I(r):
        return h(r) * w(r) ** 3 / 12.0   # bending in the plane of the sweep
    n = 2000
    s = 0.0
    for i in range(n):
        r = r0 + (rF - r0) * (i + 0.5) / n
        s += F * (rF - r) ** 2 / (E * I(r))
    return s * (rF - r0) / n

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
            row("printed walls (lip far side and outside the bend pocket)", min(D["lip_wall"], D["lip_wall_bend"]), D["print_wall_min"],
                f"v0.17 floor {D['print_wall_min']:g}; designed lip {D['lip_wall_lines']}×{D['nozzle']:g} mm = {D['lip_wall_min']:.2f}")
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
        if not D["tb_on"]:   # v0.19b [Ed 2 Nov]: no thrust bearing under the dial tube, just air
            row("dial tube end: air gap over the cradle (no thrust bearing)", D["dial_z_base"] - D["plate_t"], D["dial_air_min"],
                f"tube end z {D['dial_z_base']:.2f} over the cradle top {D['plate_t']:.2f}; the 45° race on the knob carries the dial, the adapter board stops the lift ({D['dial_lift']:.2f})")
        if tc:
            row("Hall spoke vs thrust balls / cage (±travel)", min_dist(list(posed(lambda t: hall.arm(D, t), TR).values()), tc), 0.3)
        row("Hall arm rib tip deflection at the load radius (mm)", _rib_defl(D), D["ha_rib_defl"],
            f"PA12 E {D['ha_rib_E']/1000:.1f} GPa, {D['ha_rib_load']:g} N in-plane at r {D['ha_rib_rload']:g}; "
            f"rib {D['ha_rib_w0']:g}→{D['ha_rib_w1']:g} wide, z {D['ha_rib_z_cage']:.1f} over the cage / {D['ha_rib_z_low']:.1f} beyond r {D['ha_rib_r_step']:.2f}, top {D['ha_rib_z_top']:.1f}",
            higher_ok=False)
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
