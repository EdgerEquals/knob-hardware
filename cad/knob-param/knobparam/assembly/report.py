"""v0.15 engineering report: seat groove, screen-on-dial mass/inertia, FPC strap, Hall vernier layout + dynamics, variants.
Writes assemblies/knob-stack-<version>/report-<version>.txt (+ .json). Uses the cached parts (run build.py first). CLI: python report.py [--set=name=value ...]"""
import copy, json, math, os, sys
from ..common.util import LIB
from ..common import model
from .build import build_all
from . import hall_dyn as H
P = None
def derive(p): return model.derive(p)
def apply_overrides(p, sets): return model.apply_overrides(model.default_params() if p is None else p, sets)
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.gp import gp_Ax1, gp_Pnt, gp_Dir
from build123d import Pos, Box, Align
from ..common.util import cyl

def vol_I(shape):
    g = GProp_GProps(); BRepGProp.VolumeProperties_s(shape.wrapped, g)
    return g.Mass(), g.MomentOfInertia(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)))   # mm3, mm5 (x rho -> g mm2)

def main(sets):
    D = derive(apply_overrides(P, sets)); V = D["version"]; out = os.path.join(LIB, "assemblies", f"knob-stack-{V}"); os.makedirs(out, exist_ok=True)
    parts, _, _, _ = build_all(D, full_pcb=False); rho = D["rho"]; L = []; J = {}
    p = lambda s="": L.append(s)
    p(f"KNOB STACK {V} REPORT (knob-param; all values derived from params.py; [Ed] Ed's, [A] assumed, [S] datasheet)"); p()
    # ---- groove ----
    kR = D["kb_ball_d"] / 2; k = kR / math.sqrt(2)
    p("1. BALL SEATING GROOVE (dial cone = the race the greased balls sit in with the dial lip-down)")
    p(f"   form: single-radius (circular) seat R{D['kb_seat_r']:g} [Ed] for Ø{D['kb_ball_d']:g} balls, depth {D['kb_seat_depth']:g} [A] into the cone face")
    p(f"   dial cone face moved {D['kb_seat_depth']:g} toward the ball (c {D['kb_c_dial']:.4f} -> {D['kb_c_dial_face']:.4f}; flare z {D['kb_zd0']:.3f}-{D['kb_zd1']:.3f})")
    p(f"   groove centre (r, z) = ({D['kb_seat_c'][0]:.4f}, {D['kb_seat_c'][1]:.4f}) = ball centre + {D['kb_seat_r'] - kR:.2f} along the 45° line (away from the dial)")
    p(f"   ball touches the groove bottom at ({D['kb_seat_contact'][0]:.4f}, {D['kb_seat_contact'][1]:.4f}) = the v0.14 45° contact point: contact line kept")
    p(f"   conformity R_groove / R_ball = {D['kb_seat_r'] / kR:.2f} (gothic-arch alternative: two R0.52 arcs offset ±0.02 -> 2-point contact; not chosen, keeps one 45° line)")
    p(f"   groove width at the cone face 2×{D['kb_seat_w']:.3f} = {2 * D['kb_seat_w']:.3f}; ball chord there 2×{D['kb_ball_cap_w']:.3f} (ball drops in, {D['kb_seat_w'] - D['kb_ball_cap_w']:.3f} side clearance)")
    p(f"   ball centre / PCD Ø{D['kb_pcd']:.2f} / {D['kb_n']} balls / knob cone unchanged; ball-to-tube {D['kb_ball_tube']:g}")
    p("   ASSEMBLY: hold the dial lip-down, fill the groove with grease, drop the balls in one by one (each self-centres in the seat),")
    p("   lower the knob on axially (its cone closes over the ring), flip the pair together, fit onto the stack."); p()
    # ---- screen on dial ----
    S = D["S"]; th_l = S.get("stack", (0, 0, 0, 0))
    vols = {}
    for n, s in parts.items(): vols[n] = vol_I(s)
    pn = [n for n in parts if n.endswith(" panel")][0]; fp = [n for n in parts if n.endswith("FPC + B2B")][0]
    # panel mass by layers (glass = encap + LTPS incl. ledge; POL; tape) [A densities]
    tp, te, tl, tt = th_l
    v_pol = math.pi * (S["d_pol"] / 2) ** 2 * tp; v_tape = math.pi * (S["d_tape"] / 2) ** 2 * tt
    v_tot, I_tot = vols[pn]; v_glass = v_tot - v_pol - v_tape
    m_panel = v_glass * rho["glass"] + v_pol * rho["pol"] + v_tape * rho["tape"]
    I_panel = I_tot * (m_panel / v_tot)
    m_fpc = rho["fpc_g"]; r_fpc = math.hypot(*D["b2b_xy"]) + 4.0; I_fpc = m_fpc * r_fpc ** 2 * 0.5
    vc, Ic = vols["screen carrier (on dial)"]; m_car, I_car = vc * rho["petg"], Ic * rho["petg"]
    vd, Id = vols["control dial"]; m_dial, I_dial = vd * rho["petg"], Id * rho["petg"]
    mags = [n for n in parts if n.startswith("hall magnet") or n.startswith("dial magnet")]
    m_mag = sum(vols[n][0] for n in mags) * rho["ndfeb"]; I_mag = sum(vols[n][1] for n in mags) * rho["ndfeb"]
    J_old = I_dial + I_mag; J_new = J_old + I_panel + I_fpc + I_car
    m_old = m_dial + m_mag; m_new = m_old + m_panel + m_fpc + m_car
    p("2. SCREEN TURNS WITH THE DIAL")
    p(f"   panel {D['screen']} bonded into the lip (bond gap {D['lip_bond_gap']:g}, no running gap); lip ID Ø{D['lip_id']:.2f} centred on the panel,")
    p(f"   panel offset {D['scr_off']:.3f} from the axis away from the FPC exit (exact solve over the COF bend arc |y|<={D['cof_half']:.1f}, step {D['offset_step']:g})")
    p(f"   lip wall: far side {D['lip_wall']:.3f} (target {D['tgt']['lip_wall']:g}) / near side {D['lip_wall_near']:.3f}  (v0.14: 0.195)")
    sol = math.sqrt((math.sqrt(D['R'] ** 2 - D['cof_half'] ** 2) + D['tgt']['lip_wall'] - (D['R'] - D['scr_r'] - D['lip_bond_gap']) + 0) ** 2) if False else None
    # bend that makes the lip pass: offset <= R - scr_r - bond - lip_tgt
    o_max = D["R"] - D["scr_r"] - D["lip_bond_gap"] - D["tgt"]["lip_wall"]
    b_max = math.sqrt((o_max + math.sqrt(D["R"] ** 2 - D["cof_half"] ** 2)) ** 2 + D["cof_half"] ** 2) - S["r_edge"]
    p(f"   -> lip passes 0.4 only if the offset <= {o_max:.3f}, i.e. COF bend <= {b_max:.3f} radial past the ledge (table [A] {S['bend']:.2f});")
    p(f"      try: --set cof_bend={math.floor(b_max * 100) / 100:.2f}  (needs the vendor's minimum COF bend radius)")
    p(f"   screen carrier (PETG [A]) bonded on the dial shoulder z {D['z_holder0']:.2f}, Ø{D['lip_id']:.2f} plate {D['z_back'] - D['z_holder0']:.3f} thick, FPC window;")
    p(f"   fixed adapter cup (socket on the tube, adapter well) now stops at z {D['z_cup_top']:.2f}, {D['carrier_run']:g} under the carrier; adapter still clamped by the rod nut.")
    p(f"   MASS / INERTIA about the dial axis ([A] densities g/mm3: glass {rho['glass']}, POL {rho['pol']}, tape {rho['tape']}, PETG {rho['petg']}, NdFeB {rho['ndfeb']})")
    rows = [("control dial (PETG)", m_dial, I_dial), ("magnets (hub Ø3×1 + Hall row)", m_mag, I_mag), ("panel (glass+POL+tape)", m_panel, I_panel),
            ("FPC fold + B2B (lumped [A])", m_fpc, I_fpc), ("screen carrier (PETG)", m_car, I_car)]
    for n, m, I in rows: p(f"     {n:34s} {m:7.3f} g   {I:9.1f} g·mm²")
    p(f"     dial unit v0.15 (moving)           {m_new:7.3f} g   {J_new:9.1f} g·mm²   (dial + magnets only: {m_old:.3f} g, {J_old:.1f} g·mm²; x{J_new / J_old:.2f})")
    fn_old = H.natural_freq(J_old, D["dial_spring"]); fn = H.natural_freq(J_new, D["dial_spring"])
    p(f"   spring-centred dial k = {D['dial_spring']:g} N·mm/deg [A] -> natural frequency {fn:.0f} Hz with the screen (was {fn_old:.0f} Hz without)")
    J["J_new"], J["J_old"], J["m_new"], J["m_old"], J["fn"] = J_new, J_old, m_new, m_old, fn
    p("   FPC SERVICE LOOP: diametral strap through the axis")
    p(f"     B2B moved to {tuple(round(v, 2) for v in D['b2b_xy'])} (rotating, under the fold) opposite J1 {D['j1_xy']} (stationary, adapter board)")
    p(f"     strap L {D['strap_L']:.1f} flat in the vertical plane, z {D['strap_z0']:.2f}-{D['strap_z1']:.2f} ({D['strap_z1'] - D['strap_z0']:.2f} wide), t {D['strap_t']:g} [A] 2-layer PI,")
    p(f"     clear over the rod/nut (top {D['z_rod_top']:.2f}) and U3 TMAG5273; {D['strap_lines']} lines [A] (J1 14P)")
    p(f"     at ±{D['travel_deg']:g}°: B2B end moves {D['strap_end_move']:.2f} sideways and turns {D['travel_deg']:g}° -> clamped-clamped beam with both ends on a diameter")
    p(f"     bends to a uniform arc R {D['strap_R']:.0f} mm: strain {D['strap_strain_pct']:.3f}% (limit {D['strap_strain_max']:g}% dynamic flex) - no twist, no tension")
    EI = 3.0e3 * (D["strap_z1"] - D["strap_z0"]) * D["strap_t"] ** 3 / 12
    p(f"     restoring torque ≈ EI·κ = {EI * D['strap_kappa']:.3f} N·mm at ±{D['travel_deg']:g}° (PI E 3 GPa [A], EI {EI:.2f} N·mm²) = {EI * D['strap_kappa'] / (D['dial_spring'] * D['travel_deg']) * 100:.1f}% of the centring spring")
    p()
    # ---- Hall ----
    a = H.analyse(D); s = D["hv_sensor"]
    p("3. HALL VERNIER")
    p(f"   arm: spoke from the dial tube at z {D['hv_spoke_z0']:.2f}-{D['hv_bar_top']:g} (w {D['hv_spoke_w']:g}), then a curved bar DOWN through the cradle slot to z {D['hv_bar_z0']:.2f}")
    p(f"   magnets: {D['hv_n']} × Ø{D['hv_mag'][0]:g}×{D['hv_mag'][1]:g} N52 axial, alternating poles, pockets from below, faces at z {D['hv_z_mag0']:.2f}")
    p(f"   sensors: {D['hv_n']} × {s['part']} {s['l']}×{s['w']}×{s['h']} [S], ±{s['range_mt']:g} mT, {s['s_mv_mt']:g} mV/mT @3.3 V, BW {s['bw_khz']:g} kHz, EN pin")
    p(f"   rows: radial pitch {D['hv_pitch']:g}, r = " + ", ".join(f"{r:.2f}" for r in D["hv_r"]) + f" (outer = ring tips - {D['hv_ring_clear']:g} - pad)")
    p(f"   curvature: magnets φ = {D['ha_ang0']:g}° + {D['hv_g']:.4f}°/mm·(r - {D['hv_r_mid']:.2f}); sensors φ = {D['ha_ang0']:g}° - {D['hv_g']:.4f}°/mm·(r - {D['hv_r_mid']:.2f})")
    p("     magnets φ: " + ", ".join(f"{v:.2f}" for v in D["hv_phi_m"]) + "   sensors φ: " + ", ".join(f"{v:.2f}" for v in D["hv_phi_s"]))
    xy = lambda r, ph: (r * math.cos(math.radians(ph)), r * math.sin(math.radians(ph)))
    p("     sensor centres (frame x, y) / board (bx, by): " + "; ".join(f"H{i + 1} ({x:.2f}, {y:.2f}) / ({x + D['axis_bx']:.2f}, {D['axis_by'] - y:.2f})" for i, (x, y) in enumerate(xy(r, ph) for r, ph in zip(D["hv_r"], D["hv_phi_s"]))))
    p(f"   crossing: r_x(θ) = {D['hv_r_mid']:.2f} - θ/(2g) = {D['hv_r_mid']:.2f} - {1 / (2 * D['hv_g']):.3f}·θ mm -> end pairs at ±{D['hv_cross_travel']:g}°; one pair per {2 * D['hv_g'] * D['hv_pitch']:.2f}°")
    p(f"   cradle slot: per-pad swept sectors, r {D['hv_slot_r0']:.2f}-{D['hv_slot_r1']:.2f}, ±travel + {D['hv_slot_clear']:g}")
    bb = [parts[n].bounding_box() for n in parts if n.startswith("hall sensor")]
    p(f"   PCB area: {D['hv_n']} X2SON (front) + {D['hv_n']} × 0402 (back) in a {max(b.max.X for b in bb) - min(b.min.X for b in bb):.1f} × {max(b.max.Y for b in bb) - min(b.min.Y for b in bb):.1f} mm patch; bodies ≥ {D['hv_pitch'] - s['l']:.2f} apart radially")
    p(f"     (DRV5055 SOT-23: ~3×3 footprint incl. pads -> pitch ≥ 3.3, 4 pitches = 13.2 vs {D['hv_r'][-1] - D['hv_r'][0]:.1f} available between the thrust web and the ring: X2SON TMAG5253 chosen)")
    p()
    p("4. DYNAMICS (charged-disc magnet model; dipole cross-check)")
    i0 = int(abs(a["theta"]).argmin())
    p(f"   element gap {D['hv_elem_gap']:.2f} (air {D['hv_gap']:g} + {s['elem']:g} in the package); Bz at θ=0: " + ", ".join(f"H{j + 1} {a['B'][i0, j]:+.1f}" for j in range(D["hv_n"])) + " mT")
    Bd = H.field(D, [0.0], "dipole")[0]
    p("     dipole model at θ=0: " + ", ".join(f"{v:+.1f}" for v in Bd) + " mT (overestimates the aligned pair by ~25% at this gap)")
    p(f"   field range over ±{D['travel_deg']:g}°: peak |B| {a['B_peak']:.1f} mT (BA3 range ±{s['range_mt']:g}; each sensor reaches ≥ {a['B_min_peak']:.1f} mT at its crossing)")
    p(f"   noise: sensor {s['nd_nt']:g} nT/√Hz [S] -> {a['noise_sensor_mT'] * 1e3:.1f} µT rms with a {D['hv_lpf']:g} Hz RC; ADC {D['hv_adc_bits']}-bit LSB {a['lsb_mV']:.2f} mV = {a['noise_adc_mT'] * 1e3:.1f} µT rms; total {a['noise_mT'] * 1e3:.1f} µT")
    p(f"   sensitivity |dB/dθ| (all 5 combined): {a['slope_min']:.1f}-{a['slope_max']:.1f} mT/deg over ±travel (never zero: some pair is always on a flank)")
    p(f"   angle noise (Cramér-Rao, per sample): {a['s_theta_best'] * 1e3:.2f}-{a['s_theta_worst'] * 1e3:.2f} m° rms  -> {a['steps_full']:.0f} noise steps over ±{D['travel_deg']:g}°")
    p("     realistic accuracy is set by calibration, not noise: magnet Br/position tolerances, 15% sensitivity error [S], axial play.")
    p("     Per-unit calibration (sweep against the TMAG5273 hub angle) -> expect ~0.02-0.05° repeatability [A].")
    p(f"   bandwidth: sensor {s['bw_khz']:g} kHz (-3 dB), power-on 20-45 µs [S]; RC {D['hv_lpf']:g} Hz; sample {D['hv_fs']:g} Hz/sensor = {a['fs_total'] / 1e3:.0f} ksps total")
    p(f"   flick: {D['hv_flick']:g}°/s [A] -> full ±{D['travel_deg']:g}° sweep in {2 * D['travel_deg'] / D['hv_flick'] * 1e3:.1f} ms; {a['deg_per_sample_at_flick']:.2f}°/sample = {2 * D['travel_deg'] / a['deg_per_sample_at_flick']:.0f} samples per sweep")
    p(f"     RC {D['hv_lpf']:g} Hz lag {1e3 / (2 * math.pi * D['hv_lpf']):.3f} ms -> {D['hv_flick'] / (2 * math.pi * D['hv_lpf']):.2f}° lag at the flick (compensate or raise the RC)")
    p(f"   velocity: least-squares slope over {a['N_win']} samples (2 ms) -> σv ≈ {a['s_vel']:.1f}°/s rms (noise-limited) i.e. {a['s_vel'] / D['hv_flick'] * 100:.3f}% of a flick")
    p(f"   acceleration available from the same window (2nd-order fit); dial natural frequency {fn:.0f} Hz << Nyquist {D['hv_fs'] / 2:.0f} Hz")
    p(f"   FORCE (spring-centred): torque = k·θ, k {D['dial_spring']:g} N·mm/deg [A]: full scale ±{a['torque_full']:.1f} N·mm (= ±{a['torque_full'] / D['R'] * 1e3:.0f} mN tangential at the lip)")
    p(f"     torque noise {a['torque_res']:.4f} N·mm -> {a['force_res_lip_mN']:.3f} mN at the lip per sample; with damping/inertia: τ = kθ + cθ' + Jθ'' (J {J_new:.0f} g·mm²)")
    w = math.radians(D["hv_flick"]); KE = 0.5 * J_new * 1e-9 * w * w * 1e3; PE = 0.5 * D["dial_spring"] * 180 / math.pi * math.radians(D["travel_deg"]) ** 2
    p(f"     inertial torque at a {D['hv_flick']:g}°/s flick stopping in 5 ms: J·α = {J_new * 1e-9 * w / 0.005 * 1e3:.1f} N·mm = {J_new * 1e-9 * w / 0.005 * 1e3 / a['torque_full']:.1f}× the spring full scale")
    p(f"     -> KE {KE:.2f} mJ vs spring energy at ±{D['travel_deg']:g}° {PE:.2f} mJ: a flick that fast hits the end stop; finger torque = kθ + Jθ'' (+cθ')")
    p(f"        must use θ'' from the same fit. Fastest flick the spring alone absorbs: {math.degrees(math.sqrt(2 * PE * 1e-3 / (J_new * 1e-9))):.0f}°/s")
    p("   AXIAL PRESS (option): all 5 fields scale together with the air gap (common mode); jointly fitting (θ, z) from 5 readings")
    import numpy as np
    dz = 0.01; D2 = dict(D); D2["hv_z_mag0"] = D["hv_z_mag0"] + dz
    Bz2 = H.field(D2, a["theta"]); dBz = (Bz2 - a["B"]) / dz
    inr = np.abs(a["theta"]) <= D["travel_deg"]
    sz = []
    for kk in np.where(inr)[0][::25]:
        Jm = np.c_[a["dB"][kk], dBz[kk]]; C = np.linalg.inv(Jm.T @ Jm) * a["noise_mT"] ** 2; sz.append(math.sqrt(C[1, 1]))
    p(f"     σz ≈ {min(sz) * 1e3:.2f}-{max(sz) * 1e3:.2f} µm per sample -> a press is measurable only if the dial has axial compliance (e.g. a 0.1 mm/N spring)")
    p()
    p("5. COUNT / LAYOUT ALTERNATIVES (same model, same noise; worst-case σθ over ±travel, peak |B|)")
    variants = [("5x5 vernier (v0.15 default)", []), ("3x3 vernier, pitch 3.3", ["hv_n=3", "hv_pitch=3.3"]), ("7x7 vernier, pitch 1.6 (X2SON too tight)", ["hv_n=7", "hv_pitch=1.6"]),
                ("5x5 no curvature (parallel rows)", ["hv_cross_travel=0.0001"]), ("5x5 crossing at ±20°", ["hv_cross_travel=20.0"]),
                ("5x5 crossing at ±5°", ["hv_cross_travel=5.0"]), ("5x5 Ø2×1 magnets, gap 1.6", ["hv_mag=(2.0,1.0)", "hv_gap=1.6"]),
                ("5x5 gap 1.0", ["hv_gap=1.0"]), ("4x4 vernier pitch 2.75", ["hv_n=4", "hv_pitch=2.75"])]
    vt = []
    for lab, ov in variants:
        Dv = derive(apply_overrides(P, sets + ov)); av = H.analyse(Dv)
        vt.append((lab, av["s_theta_worst"], av["B_peak"], av["slope_min"]))
        st = f"{av['s_theta_worst'] * 1e3:8.2f} m°" if av["slope_min"] > 0.05 else "     inf (all pairs peak together at θ=0)"
        p(f"   {lab:42s} σθ {st}   peak {av['B_peak']:6.1f} mT   min slope {av['slope_min']:6.2f} mT/deg")
    p("   -> 5x5 is the knee: 3x3 loses ~5x worst-case (dead-ish spots between pairs), 7x7 gains nothing and won't fit at pitch 1.6;")
    p("      the cross-over must stay inside the travel (±20° leaves the ends uncovered). Keep 5x5, crossing at ±10°.")
    p()
    json.dump(dict(J=J, hall=dict(B0=a["B"][i0].tolist(), s_theta_worst=a["s_theta_worst"], B_peak=a["B_peak"], s_vel=a["s_vel"]), variants=vt),
              open(os.path.join(out, f"report-{V}.json"), "w"), indent=1)
    txt = "\n".join(L); open(os.path.join(out, f"report-{V}.txt"), "w").write(txt); print(txt)


