"""Assembly-agent own params (not geometry of any sub-assembly): output version, cross-check inputs, report densities."""
P = dict(
    # ---- 1220 motor [M] ----
    tab_solder=0.1,   # [A] solder fillet past the motor tab tip on the PCB back
    # ---- v0.15: screen turns with the dial ----
    version="v0.24",   # output -> assemblies/knob-stack-<version>/  (panel size is owned by the case sub since v0.19)
                       # v0.24 [Ed 3 Nov]: dial bezel cartridge (+4.4, job 1) + joystick v0.8 step-1 follow-ups (job 2)
                       # v0.23 [Ed 3 Nov]: layout v4 step 1 (H7B0 on the front under the joystick, vertical boards, case cradle)
    # ---- [Ed 3 Nov] layout v4 step 1: cross-check inputs for the vertical boards' spring contacts under the joystick top board ----
    # v0.24 [Ed 14:08]: the boards are the posts, so this stack (main board -> faceplate back) goes into the form-in-place bead
    vb_stack_tol=dict(vb_seat=0.15,      # [A] ± vertical board seated on the main board (header solder + seating)
                      vb_height=0.10,    # [A] ± vertical board: bottom edge to the tabs' top edges (routed outline)
                      faceplate=0.20,    # [A] ± case (SLA): faceplate back above the PCB ledge
                      cradle=0.20,       # [A] ± case cradle (SLA): flange top to the shoulder under it
                      top_board=0.10),   # [A] ± top board thickness (1.0 FR4); the bead's own dispensed height is added from the joystick
    # v0.24 [Ed 13:46] pins into sockets: engagement (vertical-axis) and lateral alignment budgets [A]
    vb_pin_tol=dict(header_z=0.10,       # [A] right-angle header placed on the vertical board (z)
                    tab_edge=0.10,       # [A] the tab edge (routed) to the header position
                    socket_h=0.10),      # [A] socket body height
    vb_pin_margin=0.30,      # [A] engagement kept inside the socket's insertion range at each end
    vb_lat_tol=dict(main_board=0.20,     # [A] ± main board in the case (y; x)
                    case=0.20,           # [A] ± case (SLA): PCB nest to the faceplate cutout
                    cradle=0.20,         # [A] ± case cradle (SLA): lip to the top-board nest
                    top_board=0.05,      # [A] ± top board glued in its nest in a jig
                    socket=0.05,         # [A] ± socket placed on the top board
                    pins=0.10),          # [A] ± male pins on the vertical board (placement and the board's lean)
    vb_capture=dict(lead_in=0.25,        # [A] socket entry funnel over the 0.4 pin (radial capture)
                    cradle_float=0.20),  # [A] the cradle slides in the lip clearance until the case closes (lip_c)
    vb_buckle_margin=3.0,    # [A] Euler load / post load, each board
    knob_hole_clear=0.4,   # [A] faceplate hole radius over the knob radius
    faceplate_z_v023=38.8,   # [Ed 3 Nov 12:41] faceplate front in v0.23: only the knob grows (+4.4), so it must stay here (check row)
    rho=dict(glass=2.5e-3, pol=1.2e-3, tape=1.0e-3, petg=1.27e-3, ndfeb=7.5e-3, steel=7.85e-3, fpc_g=0.35),   # [A] g/mm3; FPC+B2B mass g
)
