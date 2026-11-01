"""Assembly-agent own params (not geometry of any sub-assembly): output version, cross-check inputs, report densities."""
P = dict(
    # ---- 1220 motor [M] ----
    tab_solder=0.1,   # [A] solder fillet past the motor tab tip on the PCB back
    # ---- v0.15: screen turns with the dial ----
    version="v0.18",   # output -> assemblies/knob-stack-<version>/
    hp=10,             # [L] module width
    hp_pitch=5.08,     # [L] mm per HP
    hp_gap=0.30,       # [L] Doepfer panel is n × pitch − this
    panel_h=128.5,     # [L] 3U
    knob_hole_clear=0.4,   # [A] faceplate hole radius over the knob radius
    rho=dict(glass=2.5e-3, pol=1.2e-3, tape=1.0e-3, petg=1.27e-3, ndfeb=7.5e-3, steel=7.85e-3, fpc_g=0.35),   # [A] g/mm3; FPC+B2B mass g
)
