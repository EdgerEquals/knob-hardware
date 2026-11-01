"""v0.15 Hall vernier: field model + resolution / dynamics estimate (pure numpy, all inputs from D).
Field: each axially magnetised cylinder = two uniformly charged discs (exact for an ideal magnet, better than a dipole at
gap ~ size); Bz at each Hall element (per-sensor element height hv_z_elems). Polarity per magnet from hv_pol (v0.16b [Ed]:
N/S/N/S/N). Dipole kept for comparison. v0.16b: the middle sensor is a 3D TMAG5273 -> full B vector there (field_vec)."""
import math
import numpy as np

MU = 1e-7  # mu0/4pi

def _disc_grid(r, nr=10, nt=36):
    rr = (np.arange(nr) + 0.5) / nr * r; tt = (np.arange(nt) + 0.5) / nt * 2 * math.pi
    R, T = np.meshgrid(rr, tt); dA = (r / nr) * R * (2 * math.pi / nt)
    return (R * np.cos(T)).ravel(), (R * np.sin(T)).ravel(), dA.ravel()

def bz_cyl(px, py, pz, cx, cy, z0, d, h, br, grid=None):
    """Bz (T) at points from a cylinder (axis z, faces z0 / z0+h, M along +z). Br in T; lengths mm."""
    gx, gy, dA = grid if grid is not None else _disc_grid(d / 2)
    out = 0.0
    for zf, sgn in ((z0 + h, 1.0), (z0, -1.0)):   # top face +sigma, bottom face -sigma ; B = Br/(4pi) * sum sigma*(p-q)/|p-q|^3 dA
        dx = px[..., None] - (np.asarray(cx)[..., None] + gx); dy = py[..., None] - (np.asarray(cy)[..., None] + gy); dz = pz[..., None] - zf
        r3 = (dx * dx + dy * dy + dz * dz) ** 1.5
        out = out + sgn * (dz / r3 * dA).sum(-1)
    return br / (4 * math.pi) * out

def bz_dipole(px, py, pz, cx, cy, zc, d, h, br):
    m = br / (4e-7 * math.pi) * math.pi * (d / 2) ** 2 * h * 1e-9       # A m^2
    dx, dy, dz = (px - cx) * 1e-3, (py - cy) * 1e-3, (pz - zc) * 1e-3
    r2 = dx * dx + dy * dy + dz * dz
    return MU * m * (3 * dz * dz - r2) / r2 ** 2.5

def layout(D):
    n = D["hv_n"]; r = np.array(D["hv_r"]); pm = np.radians(D["hv_phi_m"]); ps = np.radians(D["hv_phi_s"])
    pol = D["hv_pol"]
    return r, pm, ps, np.array(pol, float)

def b_cyl(px, py, pz, cx, cy, z0, d, h, br, grid=None):
    """Full B (T) vector (bx, by, bz) at points from an axial cylinder magnet (charged-disc model, M along +z)."""
    gx, gy, dA = grid if grid is not None else _disc_grid(d / 2)
    out = np.zeros(3)
    for zf, sgn in ((z0 + h, 1.0), (z0, -1.0)):
        dx = px - (cx + gx); dy = py - (cy + gy); dz = pz - zf
        r3 = (dx * dx + dy * dy + dz * dz) ** 1.5
        out = out + sgn * np.array([(dx / r3 * dA).sum(), (dy / r3 * dA).sum(), (dz / r3 * dA).sum()])
    return br / (4 * math.pi) * out

def field_vec(D, j, thetas):
    """B vector (mT, [k, 3]) at sensor j's element for dial angles thetas (deg), all magnets with polarity."""
    r, pm, ps, pol = layout(D); md, mh = D["hv_mag"]; br = D["hv_br"]; grid = _disc_grid(md / 2)
    sx, sy, sz = r[j] * math.cos(ps[j]), r[j] * math.sin(ps[j]), D["hv_z_elems"][j]
    out = []
    for t in np.radians(np.asarray(thetas, float)):
        b = sum(pol[i] * b_cyl(sx, sy, sz, r[i] * math.cos(pm[i] + t), r[i] * math.sin(pm[i] + t), D["hv_z_mag0"], md, mh, br, grid) for i in range(len(r)))
        out.append(b)
    return np.array(out) * 1e3

def field(D, thetas, model="disc"):
    """B[k, j] (mT) at sensor j for dial angle thetas[k] (deg)."""
    r, pm, ps, pol = layout(D); md, mh = D["hv_mag"]; br = D["hv_br"]
    sx, sy = r * np.cos(ps), r * np.sin(ps); sz = np.array(D["hv_z_elems"], float)
    th = np.radians(np.asarray(thetas, float))
    B = np.zeros((len(th), len(r))); grid = _disc_grid(md / 2)
    for i in range(len(r)):
        cx, cy = r[i] * np.cos(pm[i] + th), r[i] * np.sin(pm[i] + th)
        P = lambda a: np.broadcast_to(a, (len(th), len(r)))
        X, Y, Z = P(sx[None, :]), P(sy[None, :]), P(sz[None, :])
        if model == "disc":
            b = bz_cyl(X, Y, Z, cx[:, None], cy[:, None], D["hv_z_mag0"], md, mh, br, grid)
        else:
            b = bz_dipole(X, Y, Z, cx[:, None], cy[:, None], D["hv_z_mag0"] + mh / 2, md, mh, br)
        B += pol[i] * b
    return B * 1e3   # mT (sensor sees -Bz of a north-down magnet as negative; sign is irrelevant)

def noise(D):
    s = D["hv_sensor"]; fc = D["hv_lpf"]
    enbw = min(fc * math.pi / 2, s["bw_khz"] * 1e3)                    # single-pole RC noise bandwidth
    b_rms = s["nd_nt"] * 1e-6 * math.sqrt(enbw)                        # mT rms (sensor)
    lsb_mv = s["vcc"] * 1e3 / 2 ** D["hv_adc_bits"]
    q_rms = lsb_mv / s["s_mv_mt"] / math.sqrt(12)                      # mT rms (ADC quantisation)
    return math.hypot(b_rms, q_rms), b_rms, q_rms, lsb_mv

def analyse(D, step=0.02, model="disc"):
    T = D["travel_deg"]; th = np.arange(-T - 1, T + 1 + 1e-9, step)
    B = field(D, th, model); dB = np.gradient(B, step, axis=0)        # mT/deg
    sig, b_rms, q_rms, lsb = noise(D)
    inr = np.abs(th) <= T + 1e-9
    S = np.sqrt((dB ** 2).sum(1))                                      # Fisher: sigma_theta = sigma_B / |dB/dtheta|
    s_th = sig / S
    # vernier crossing index: pair with the largest |B| product
    best = np.argmax(np.abs(B) * 1.0, axis=1)
    fs = D["hv_fs"]; vel = D["hv_flick"]
    N = max(int(round(fs * 0.002)), 3)                                 # 2 ms regression window [A]
    s_th_w = float(s_th[inr].max())
    s_v = s_th_w * math.sqrt(12 / N ** 3) * fs                         # deg/s rms, LSQ slope over N samples
    k = D["dial_spring"]
    out = dict(theta=th, B=B, dB=dB, S=S, s_theta=s_th, best=best,
               B_peak=float(np.abs(B[inr]).max()), B_peak_j=np.abs(B[inr]).max(0), B_min_peak=float(np.abs(B[inr]).max(0).min()),
               slope_min=float(S[inr].min()), slope_max=float(S[inr].max()),
               s_theta_worst=s_th_w, s_theta_best=float(s_th[inr].min()),
               noise_mT=sig, noise_sensor_mT=b_rms, noise_adc_mT=q_rms, lsb_mV=lsb,
               range_ok=float(np.abs(B[inr]).max()) < D["hv_sensor"]["range_mt"] * 0.9,
               fs=fs, fs_total=fs * D["hv_n"], N_win=N, s_vel=s_v,
               deg_per_sample_at_flick=vel / fs, nyq_motion_hz=fs / 2,
               torque_res=k * s_th_w, force_res_lip_mN=k * s_th_w / D["R"] * 1e3,
               torque_full=k * T, steps_full=2 * T / s_th_w)
    return out

def natural_freq(J_gmm2, k_nmm_deg):
    k = k_nmm_deg * 180 / math.pi * 1e-3          # N*m/rad
    J = J_gmm2 * 1e-9                              # kg m^2
    return math.sqrt(k / J) / (2 * math.pi)

