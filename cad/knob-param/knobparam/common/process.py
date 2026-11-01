"""One process table for every printed part (knob and joystick both read it). Numbers from the joystick v0.4 params, which
already use PCBWay's stated tolerances. tol = +/- dimensional tolerance; wall = minimum wall; feature = minimum detail."""
PROCESS = {
    "sla":  dict(tol=0.20, wall=0.8, feature=0.5, note="PCBWay SLA, wide end of +/-0.1-0.2; clear resin is brittle"),
    "mjf":  dict(tol=0.25, wall=1.0, feature=0.5, note="PCBWay MJF/SLS PA12"),
    "fdm":  dict(tol=0.20, wall=1.2, feature=0.8, note="3 x 0.4 lines; only if a part is ever FDM"),
    "cnc":  dict(tol=0.05, wall=0.5, feature=0.3, note="brass / aluminium turned parts"),
    "buy":  dict(tol=0.02, wall=0.0, feature=0.0, note="catalogue part (bearings, KHK gears, balls)"),
}

def stack(*procs):
    """Clearance needed so two toleranced faces never meet: root-sum-square of the two tolerances (worst case = plain sum)."""
    return sum(PROCESS[p]["tol"] ** 2 for p in procs) ** 0.5
