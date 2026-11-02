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
    # ---- v0.19b [Ed 2 Nov] 716 driver moved off the emitter radius (U20 DRV8837 + C20–C22, B.Cu), mechanism frame ----
    drv_xy=(-8.5, 12.0),   # [A] U20 centre: 3.6 mm from the 716 lead pads, 0.8 clear of the pads, pegs, Hall decouplers and compound gear plan
    drv_rot=45.0,   # [A] cluster turn (deg). v0.19 was U20 at (-10.25, 12.96), 0°, which reached the emitter band (keep-out 124–137°)
    drv_cluster=(("U20", "WSON-8_2x2_DRV8837", 0.0, 0.0, 0, 2.95, 2.55, 0.8),   # [K] design.py offsets: ref, fp, dx, dy, rot, w, l, h
                 ("C20", "C_0402", 0.0, 2.2, 0, 1.91, 0.99, 0.5),
                 ("C21", "C_0402", -2.9, 1.0, 90, 0.99, 1.91, 0.5),
                 ("C22", "C_0603", -4.7, 1.0, 90, 1.55, 3.05, 0.8)),
    pcb_windows={   # [Ed 2 Nov] see-through windows, PANEL frame (scratchpad calc/windows.py: screen behind, 1.5 rail, 1.0 round every
                    # obstacle, 1.5 round the encoder daughterboard/header;
                    # obstacle: knob r 24.1, joystick carrier, corner posts, J10, bearing 2 seat). A, B: rear AMOLED; C, E: front AMOLED; D: clear OLED
        "A": [(-17.63, 16.38), (-18.04, 16.11), (-18.53, 16.07), (-18.98, 16.28), (-19.28, 16.67), (-19.36, 17.06), (-19.36, 19.95), (-19.19, 20.51), (-18.83, 20.83), (-18.46, 20.95), (-15.17, 20.95), (-14.61, 20.78), (-14.33, 20.49), (-14.18, 20.12), (-14.19, 19.73), (-14.36, 19.37), (-16.16, 17.83)],
        "B": [(14.57, 19.15), (14.22, 19.63), (14.18, 20.12), (14.39, 20.57), (14.78, 20.87), (15.17, 20.95), (18.36, 20.95), (18.83, 20.83), (19.19, 20.51), (19.36, 20.05), (19.36, 17.06), (19.24, 16.58), (18.99, 16.28), (18.63, 16.1), (18.24, 16.07), (17.87, 16.19), (16.16, 17.83)],
        "C": [(13.98, -21.8), (13.43, -21.63), (13.06, -21.19), (13.0, -20.61), (13.27, -20.1), (15.71, -18.22), (17.78, -16.25), (18.14, -16.08), (18.44, -16.06), (18.73, -16.13), (19.06, -16.34), (19.28, -16.67), (19.36, -17.06), (19.36, -20.9), (19.24, -21.27), (19.07, -21.51), (18.74, -21.72), (18.46, -21.8)],
        "D": [(18.2, -24.6), (18.58, -24.68), (18.91, -24.89), (19.12, -25.22), (19.2, -25.6), (19.2, -47.6), (19.08, -48.07), (18.76, -48.43), (18.2, -48.6), (-18.2, -48.6), (-18.67, -48.48), (-19.03, -48.16), (-19.2, -47.6), (-19.2, -25.6), (-19.08, -25.13), (-18.76, -24.77), (-18.2, -24.6)],
        "E": [(-19.36, -17.06), (-19.19, -16.5), (-18.82, -16.17), (-18.24, -16.07), (-17.78, -16.25), (-15.71, -18.22), (-13.27, -20.1), (-13.1, -20.33), (-12.99, -20.71), (-13.0, -21.0), (-13.15, -21.36), (-13.51, -21.68), (-13.98, -21.8), (-18.36, -21.8), (-18.92, -21.63), (-19.24, -21.27), (-19.36, -20.9)],
    },
    clear_oled=(42.04, 27.22, 1.25),   # [S] EastRising ER-OLED1.51-1B / Waveshare 1.51" SSD1309 transparent, on the PCB front over window D
    clear_oled_xy=(0.0, -36.6),   # [Ed] centre of the 38.4 x 24 cut-away (zone sketch, +4 mm into this frame); 1.8 / 1.6 mm ledge all round
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
           "clear_oled", "clear_oled_xy",                 # -> case (ledge relief round the clear OLED)
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
    gj = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kicad", "joystick-daughterboard", "geom.json")
    D["js_pcb_holes"] = json.load(open(gj)).get("main_pcb_holes", []) if os.path.exists(gj) else []   # joystick build output
    from .parts import pcb as _pcb   # v0.19b: KiCad back parts that now sit in a window (move them when the board is regenerated)
    D["pcb_win_displaced"] = _pcb.window_hits(D, D["pcb_kicad"])
    return D
