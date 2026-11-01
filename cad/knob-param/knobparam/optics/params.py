"""optics own params + derive. Off by default. [A] values are the check's assumptions, not an adopted design.
Wedge angle, centre and the glow plane stay here until Ed locks the optics round."""
import math

P = dict(
    optics_on=False,           # every optics solid and beam row stays off until --set optics_on=True
    las_d=8.0, las_len=31.0,   # [S] Civillaser 405 nm module envelope
    las_r_frac=0.0,            # [A] laser axis radius / knob radius
    las_z_below_glass=24.0,    # [A] aperture below the glass
    beam_d=1.0,                # [A] beam diameter at the aperture
    beam_div_mrad=0.5,         # [A] full divergence
    rp_wedge_deg=8.0,          # [A] wedge angle, not locked
    rp_n=1.53,                 # [A] clear SLA at 405 nm
    rp_d=7.0, rp_t_min=0.8,
    rp_gap=0.8,
    rp_samples=24,
    glow_below_glass=1.5,      # [A]
    glow_r_frac=0.80,          # [A]
    beam_clear=0.3,            # [A]
    rl_n=12,
    rl_r_frac=0.86,            # [A]
    rl_phase_deg=7.5,          # [A]
    vcsel=dict(part="JNJ-V-2835CW-665003-S-D1", lcsc="C42375664", x=2.8, y=3.5, h=0.8, half_angle_deg=12.0),
    rgb=dict(part="addressable 2020 [A]", x=2.0, y=2.0, h=0.9),
)

IMPORTS = {}
EXPORTS = []


def derive(D):
    R = D["knob_od"] / 2
    D["las_xy"] = (D["las_r_frac"] * R, 0.0)
    D["las_z_ap"] = D["z_glass"] - D["las_z_below_glass"]
    a = math.radians(D["rp_wedge_deg"])
    d = D["rp_d"]
    D["rp_t_max"] = D["rp_t_min"] + d * math.tan(a)
    D["rp1_z0"] = D["las_z_ap"] + 0.5
    D["rp2_z0"] = D["rp1_z0"] + D["rp_t_max"] + D["rp_gap"]
    D["rp_top"] = D["rp2_z0"] + D["rp_t_max"]
    D["rp_dev_thin_deg"] = (D["rp_n"] - 1) * D["rp_wedge_deg"]
    D["glow_z"] = D["z_glass"] - D["glow_below_glass"]
    D["glow_r"] = D["glow_r_frac"] * R
    D["rl_r"] = D["rl_r_frac"] * D["skirt_id"] / 2
    D["rl_pitch_deg"] = 360.0 / (2 * D["rl_n"])
