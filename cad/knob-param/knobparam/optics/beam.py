"""Exact Risley-pair ray trace (vector Snell at all four faces) plus beam clearance against solids."""
import math


def _norm(v):
    l = math.sqrt(sum(c * c for c in v))
    return tuple(c / l for c in v)


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def refract(i, n, eta):
    """i = unit incident direction, n = unit surface normal, eta = n_from / n_to. None on total internal reflection."""
    if _dot(n, i) > 0:
        n = tuple(-c for c in n)
    ci = -_dot(n, i)
    k = 1 - eta * eta * (1 - ci * ci)
    if k < 0:
        return None
    return _norm(tuple(eta * a + (eta * ci - math.sqrt(k)) * b for a, b in zip(i, n)))


def risley_dir(D, th1, th2):
    """Beam direction after both wedges. Flat entry face normal +z, exit face tilted alpha toward angle th."""
    a, n = math.radians(D["rp_wedge_deg"]), D["rp_n"]
    d = (0.0, 0.0, 1.0)
    for th in (math.radians(th1), math.radians(th2)):
        d = refract(d, (0.0, 0.0, 1.0), 1.0 / n)
        if d is None:
            return None
        d = refract(d, (math.sin(a) * math.cos(th), math.sin(a) * math.sin(th), math.cos(a)), n)
        if d is None:
            return None
    return d


def rays(D):
    """[(th1, th2, start xyz, end xyz on the glow plane, landing radius)] over the sample grid."""
    x0, y0 = D["las_xy"]
    z0 = D["rp_top"]
    zt = D["glow_z"]
    N = D["rp_samples"]
    out = []
    for i in range(N):
        for j in range(N):
            t1, t2 = 360.0 * i / N, 360.0 * j / N
            d = risley_dir(D, t1, t2)
            if d is None or d[2] <= 0:
                out.append((t1, t2, (x0, y0, z0), None, math.inf))
                continue
            s = (zt - z0) / d[2]
            e = (x0 + s * d[0], y0 + s * d[1], zt)
            out.append((t1, t2, (x0, y0, z0), e, math.hypot(e[0], e[1])))
    return out


def beam_rows(D, parts, row, skip=("Risley", "laser", "glow")):
    """Every sampled ray lands on the glow target, and every beam segment clears every solid. No-op while optics_on is False."""
    if not D["optics_on"]:
        return
    from build123d import Edge, Vector
    from ..common.checks import min_dist
    R = rays(D)
    r_max = max(r[4] for r in R)
    row("laser: every ray lands inside the glow target (margin, mm)", D["glow_r"] - r_max, 0.0,
        f"{len(R)} rays, max landing r {r_max:.2f} vs glow r {D['glow_r']:.2f}; cone {math.degrees(math.atan2(r_max, D['glow_z'] - D['rp_top'])):.1f}° half-angle")
    L = D["glow_z"] - D["rp_top"]
    r_beam = D["beam_d"] / 2 + L * D["beam_div_mrad"] * 1e-3 / 2
    segs = [Edge.make_line(Vector(*s), Vector(*e)) for _, _, s, e, _ in R[:: max(1, len(R) // 96)] if e is not None]
    obst = [p for n, p in parts.items() if not any(k in n for k in skip)]
    if obst:
        row("laser: beam centre line vs any solid (mm)", min_dist(segs, obst) - r_beam, D["beam_clear"],
            f"{len(segs)} sampled segments vs {len(obst)} parts; beam radius {r_beam:.2f} at the target")
