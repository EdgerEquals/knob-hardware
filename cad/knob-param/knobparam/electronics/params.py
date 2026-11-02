"""electronics own params + derive (main PCB outline/proxy/KiCad STEP, adapter board + parts, Hall sensor row, Hall ADC/sampling).
Reads: interface + own + IMPORTS (under_pcb big-gear tip for the J2 pad position; build time only)."""
import math, os, json

P = dict(
    kicad_frame="mech",   # [K] v0.19: the committed KiCad boards (v0.11/v0.12) are in the mechanism frame (motor at +X); "panel" once regenerated
    # ---- main PCB [K] ----
    pcb_w=49.0,   # [K] board width (x)
    pcb_above=42.4,   # [K] dial axis to the top board edge (panel +y side, frame +y)
    pcb_below=65.1,   # [K] dial axis to the bottom board edge (frame -y)
    h1_hole=1.8,   # [K] H1 NPTH (rod)
    # ---- screen holder + adapter ----
    adapter_d=15.5,   # [K]/[A] (cord room over the nut [Ed])
    adapter_fps={"J1": ("FPC_14P_0.5mm_Top", 0.0, 3.7, 0), "U1": ("QFN-20_3x3", 0.0, -3.8, 0), "C2": ("C_0402", -2.55, -5.2, 90)},   # [K] KiCad screen-adapter v0.4 (U3/R1/R2 removed)
    adapter_env={"FPC_14P_0.5mm_Top": (10.6, 3.6, 1.0), "QFN-20_3x3": (3.0, 3.0, 0.75), "SOT-23-6_TMAG5273": (1.6, 2.9, 1.45), "C_0402": (1.0, 0.5, 0.5), "R_0402": (1.0, 0.5, 0.35)},   # [A] envelopes
    rod_pad_clear=0.3,   # [A] v0.16 B.Cu rod (VBUS) pad to the nearest other back-side copper / part / hole
    pcb_slot_clear=0.3,   # [A] motor-tab slot over the tab, each side
    hall_z=0.65,   # [A] TMAG5273 element above the adapter top
    # ---- v0.15: Hall vernier (arm down through the cradle slot, 5 magnets x 5 sensors, arcs crossing) ----
    hv_adc_bits=12,   # [A] MCU ADC
    hv_fs=4000.0,   # [A] per-sensor sample rate (Hz), 5 channels -> 20 ksps
    hv_lpf=2000.0,   # [A] RC filter per sensor output (Hz)
    hv_flick=3000.0,   # [A] fast flick peak angular velocity (deg/s)
)

IMPORTS = {"under_pcb": ["d_big_tip"]}
EXPORTS = ["pcb_w", "pcb_above", "pcb_below",          # -> under_pcb (big-gear size from the board outline)
           "adapter_d", "adapter_fps", "adapter_env"]   # -> control_dial (cup pocket, J1/U3 positions, strap height)


def derive(D):
    # v0.16 [Ed]: the bottom rod pad grows as far as the nearest back-side neighbour allows (Hall decouplers, 716 lead pads,
    # H2 bore, 1220 tab slots), minus rod_pad_clear. KiCad knob-main-pcb v0.10 follows it (TubeRodClamp_Main_M1.6_v016).
    obs = []
    if D["hall_layout"] == "vernier":
        obs += [math.hypot(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) - math.hypot(0.25, 0.5) for r, a in zip(D["hv_r"], D["hv_phi_s"])]
    F = D["feel"]
    obs += [math.hypot(x, y) - math.hypot(*F["pad"]) / 2 for x, y in D["fm_pad_xy"]]
    obs += [math.hypot(*D["enc_xy"]) - D["brg"]["D"] / 2]
    M = D["motor"]; obs += [D["offset"] - M["term_pitch"] / 2 - (M["term_w"] + 0.3) / 2]
    D["rod_pad_r"] = min(obs) - D["rod_pad_clear"]
    # v0.16 [Ed]: U3 TMAG5273 removed from the fixed adapter board; v0.16b: the dial sensor is dropped (rel_sensor=False). KiCad screen-adapter v0.4 done.
    # KiCad is the source of truth for the board: holes / slots / back-side parts it adds beyond the params (export_pcb_proxy.py).
    # Read here (not in parts/pcb.py) so the part cache key follows the JSON.
    pj = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kicad", "knob-main-pcb", "pcb_proxy.json")
    D["pcb_kicad"] = json.load(open(pj)) if os.path.exists(pj) else {}
    return D
