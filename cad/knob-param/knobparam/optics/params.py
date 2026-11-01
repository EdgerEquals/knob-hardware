"""optics own params + derive. Every value tagged; [A] = assumed until the optics round fixes it.
Everything is a ratio of interface values where one exists (knob OD, glass z), so a knob or screen change carries through."""
import math

P = dict(
    optics_on=False,           # [Ed rule 5] every subsystem off by default; --set optics_on=True to build + check
    # ---- 405 nm laser module (Civillaser 1 mW, Φ8 x 31) [S] ----
    las_d=8.0, las_len=31.0,
    las_r_frac=0.0,            # [A] laser axis radius as a fraction of the knob radius (0 = on the knob axis)
    las_z_below_glass=24.0,    # [A] laser aperture this far below the glass
    beam_d=1.0,                # [A] beam diameter at the aperture (collimated module ~1 mm)
    beam_div_mrad=0.5,         # [A] full divergence
    # ---- Risley pair: two identical resin wedges, flat face toward the laser [A] ----
    rp_wedge_deg=8.0,          # wedge angle alpha
    rp_n=1.53,                 # [A] clear SLA resin at 405 nm (measure: datasheets quote nD ~1.51-1.53)
    rp_d=7.0, rp_t_min=0.8,    # disc diameter, thin edge (>= SLA print minimum)
    rp_gap=0.8,                # air gap between the wedges
    rp_samples=24,             # angle samples per prism for the sweep (24 x 24 = 576 rays)
    # ---- glow targets ----
    glow_below_glass=1.5,      # [A] glow coat plane under the glass (dial lid underside)
    glow_r_frac=0.80,          # [A] usable glow radius as a fraction of the knob radius
    beam_clear=0.3,            # [A] beam edge to any solid
    # ---- ring lights under the clear race carrier [Ed] ----
    rl_n=12,                   # VCSELs; the same number of RGB LEDs sits between them (alternating)
    rl_r_frac=0.86,            # [A] emitter circle as a fraction of the skirt ID radius
    rl_phase_deg=7.5,          # [A] first VCSEL angle (half the 15° pitch, so no emitter sits on 0°)
    vcsel=dict(part="JNJ-V-2835CW-665003-S-D1", lcsc="C42375664", x=2.8, y=3.5, h=0.8, half_angle_deg=12.0),   # [S] 2835; beam half-angle [A]
    rgb=dict(part="addressable 2020 [A]", x=2.0, y=2.0, h=0.9),
)

IMPORTS = {}       # v0.18: {"control_dial": ["lid_z0"], "main_knob": ["race_r", "race_z", "carrier_z0"]} once those exist
EXPORTS = []


def derive(D):
    R = D["knob_od"] / 2
    D["las_xy"] = (D["las_r_frac"] * R, 0.0)
    D["las_z_ap"] = D["z_glass"] - D["las_z_below_glass"]                 # aperture (top of the module)
    a = math.radians(D["rp_wedge_deg"]); d = D["rp_d"]
    D["rp_t_max"] = D["rp_t_min"] + d * math.tan(a)                       # thick edge follows the wedge angle
    D["rp1_z0"] = D["las_z_ap"] + 0.5
    D["rp2_z0"] = D["rp1_z0"] + D["rp_t_max"] + D["rp_gap"]
    D["rp_top"] = D["rp2_z0"] + D["rp_t_max"]
    D["rp_dev_thin_deg"] = (D["rp_n"] - 1) * D["rp_wedge_deg"]            # thin-prism estimate per wedge (check uses exact Snell)
    D["glow_z"] = D["z_glass"] - D["glow_below_glass"]
    D["glow_r"] = D["glow_r_frac"] * R
    D["rl_r"] = D["rl_r_frac"] * D["skirt_id"] / 2
    D["rl_pitch_deg"] = 360.0 / (2 * D["rl_n"])                           # alternating VCSEL / RGB
