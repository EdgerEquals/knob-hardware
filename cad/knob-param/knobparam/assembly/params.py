"""Assembly-agent own params (not geometry of any sub-assembly): output version, cross-check inputs, report densities."""
P = dict(
    # ---- 1220 motor [M] ----
    tab_solder=0.1,   # [A] solder fillet past the motor tab tip on the PCB back
    # ---- v0.15: screen turns with the dial ----
    version="v0.25",   # output -> assemblies/knob-stack-<version>/  (panel size is owned by the case sub since v0.19)
                       # v0.25 [Ed 3 Nov evening]: review decisions: spur gears + hub m0.75 12/17 nylon in a split clear cap,
                       # cradle printed into the case, dial split, detent block, cartridge sideways magnets + key
                       # v0.24 [Ed 3 Nov]: dial bezel cartridge (+4.4, job 1) + joystick v0.8 step-1 follow-ups (job 2)
                       # v0.23 [Ed 3 Nov]: layout v4 step 1 (H7B0 on the front under the joystick, vertical boards, case cradle)
    # ---- [Ed 3 Nov] layout v4 step 1: cross-check inputs for the vertical boards' spring contacts under the joystick top board ----
    # v0.24 [Ed 14:08]: the boards are the posts, so this stack (main board -> faceplate back) goes into the form-in-place bead
    # v0.25 [Ed 18:35]: the cradle is printed into the case, so the PCB ledge to the top-board shoulders is ONE SLA dimension (the
    # faceplate and cradle terms of v0.24 merge: "loses the cradle-to-faceplate term"); the pins take this stack (decision (c))
    vb_stack_tol=dict(vb_seat=0.15,      # [A] ± vertical board seated on the main board (header solder + seating)
                      vb_height=0.10,    # [A] ± vertical board: bottom edge to the tabs' top edges (routed outline)
                      case=0.20,         # [A] ± case (SLA, one print): main-board ledge to the printed top-board shoulders
                      top_board=0.10),   # [A] ± top board thickness (1.0 FR4), glued up under the shoulders
    # v0.24 [Ed 13:46] pins into sockets: engagement (vertical-axis) and lateral alignment budgets [A]
    vb_pin_tol=dict(header_z=0.10,       # [A] right-angle header placed on the vertical board (z, from its bottom edge)
                    socket_h=0.10),      # [A] socket body height (v0.25: the tab_edge term went: the tabs no longer hold the top board)
    vb_pin_margin=0.30,      # [A] engagement kept inside the socket's insertion range at each end
    vb_tab_margin=0.30,      # [A] v0.25: end tabs (and the male header body under the socket) clear of the top board / socket at the worst case
    path_min=0.30,           # [A] v0.25: parts going in from the back (top board, vertical boards' headers) clear the case by this
    # v0.25 [Ed 18:35]: no separate cradle (its 0.2 lip float and its lip-to-nest term are gone); the top board floats in its printed
    # nest (0.2 a side) while its glue is wet [A], so the pins centre it as the board stack goes in, then the glue sets
    vb_lat_tol=dict(main_board=0.20,     # [A] ± main board in the case (y; x)
                    case=0.20,           # [A] ± case (SLA, one print): PCB nest / corner posts to the printed top-board nest
                    socket=0.05,         # [A] ± socket placed on the top board
                    pins=0.10),          # [A] ± male pins on the vertical board (placement and the board's lean)
    vb_capture=dict(lead_in=0.25,        # [A] socket entry funnel over the 0.4 pin (radial capture)
                    board_float=0.20),   # [A] v0.25: the top board in its nest (0.2 a side) while the glue is still wet (v0.24: the cradle's lip float)
    vb_buckle_margin=3.0,    # [A] Euler load / post load, each board
    knob_hole_clear=0.4,   # [A] faceplate hole radius over the knob radius
    faceplate_z_v023=38.8,   # [Ed 3 Nov 12:41] faceplate front in v0.23: only the knob grows (+4.4), so it must stay here (check row)
    rho=dict(glass=2.5e-3, pol=1.2e-3, tape=1.0e-3, petg=1.27e-3, ndfeb=7.5e-3, steel=7.85e-3, fpc_g=0.35),   # [A] g/mm3; FPC+B2B mass g
)
