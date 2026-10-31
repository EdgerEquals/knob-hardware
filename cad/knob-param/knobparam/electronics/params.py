"""electronics own params + derive (main PCB outline/proxy/KiCad STEP, adapter board + parts, Hall sensor row, Hall ADC/sampling).
Reads: interface + own + IMPORTS (under_pcb big-gear tip for the J2 pad position; build time only)."""
import math

P = dict(
    # ---- main PCB [K] ----
    pcb_w=49.0,   # [K] board width (x)
    pcb_above=42.4,   # [K] dial axis to the top board edge (panel +y side, frame +y)
    pcb_below=65.1,   # [K] dial axis to the bottom board edge (frame -y)
    h1_hole=1.8,   # [K] H1 NPTH (rod)
    # ---- screen holder + adapter ----
    adapter_d=15.5,   # [K]/[A] (cord room over the nut [Ed])
    adapter_fps={"R2": ("R_0402", -3.3, -3.6, 0), "J1": ("FPC_14P_0.5mm_Top", 0.0, 3.7, 0), "U1": ("QFN-20_3x3", 0.0, -3.8, 0), "C2": ("C_0402", 3.3, -3.2, 0), "U3": ("SOT-23-6_TMAG5273", 5.7, -0.2, 90), "R1": ("R_0402", -3.3, -2.6, 0)},   # [K]
    adapter_env={"FPC_14P_0.5mm_Top": (10.6, 3.6, 1.0), "QFN-20_3x3": (3.0, 3.0, 0.75), "SOT-23-6_TMAG5273": (1.6, 2.9, 1.45), "C_0402": (1.0, 0.5, 0.5), "R_0402": (1.0, 0.5, 0.35)},   # [A] envelopes
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
    D["z_hall"] = D["z_board_top"] + D["hall_z"]          # TMAG5273 element height
    return D
