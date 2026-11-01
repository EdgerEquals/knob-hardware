"""One process table. Numbers are PCBWay's stated tolerances. tol is the +/- band; wall and feature are minima."""
PROCESS = {
    "sla":  dict(tol=0.20, wall=0.8, feature=0.5, note="PCBWay SLA, wide end of +/-0.1-0.2; clear resin is brittle"),
    "mjf":  dict(tol=0.25, wall=1.0, feature=0.5, note="PCBWay MJF/SLS PA12"),
    "fdm":  dict(tol=0.20, wall=1.2, feature=0.8, note="3 x 0.4 lines; only if a part is ever FDM"),
    "cnc":  dict(tol=0.05, wall=0.5, feature=0.3, note="brass / aluminium turned parts"),
    "buy":  dict(tol=0.02, wall=0.0, feature=0.0, note="catalogue part (bearings, balls)"),
}


def stack(*procs):
    """Clearance so two toleranced faces do not meet: root-sum-square of the two tolerances."""
    return sum(PROCESS[p]["tol"] ** 2 for p in procs) ** 0.5
