"""Assembly-agent own params (not geometry of any sub-assembly): output version, cross-check inputs, report densities."""
P = dict(
    # ---- 1220 motor [M] ----
    tab_solder=0.1,   # [A] solder fillet past the motor tab tip on the PCB back
    # ---- v0.15: screen turns with the dial ----
    version="v0.23",   # output -> assemblies/knob-stack-<version>/  (panel size is owned by the case sub since v0.19)
                       # v0.23 [Ed 3 Nov]: layout v4 step 1 (H7B0 on the front under the joystick, vertical boards, case cradle)
    # ---- [Ed 3 Nov] layout v4 step 1: cross-check inputs for the vertical boards' spring contacts under the joystick top board ----
    vb_stack_tol=dict(vb_seat=0.15,      # [A] ± vertical board seated on the main board (outline routing ±0.1 + seating)
                      contact_body=0.10, # [A] ± contact strip soldered on the vertical board's top edge
                      faceplate=0.20,    # [A] ± case (SLA): faceplate back above the PCB ledge
                      cradle=0.20,       # [A] ± case cradle (SLA): flange top to the shoulder under it
                      top_board=0.10),   # [A] ± top board thickness (1.0 FR4); the gasket's band is added from the joystick
    vb_travel_margin=0.10,   # [A] the contacts keep this much travel at each end of the RSS band
    vb_hold_margin=1.3,      # [A] net contact preload over the worst-case click (the joystick's tipping-safety margin)
    knob_hole_clear=0.4,   # [A] faceplate hole radius over the knob radius
    faceplate_z_v023=38.8,   # [Ed 3 Nov 12:41] faceplate front in v0.23: only the knob grows (+4.4), so it must stay here (check row)
    rho=dict(glass=2.5e-3, pol=1.2e-3, tape=1.0e-3, petg=1.27e-3, ndfeb=7.5e-3, steel=7.85e-3, fpc_g=0.35),   # [A] g/mm3; FPC+B2B mass g
)
