"""Check-row helper shared by the local checks (each sub-assembly) and the cross-checks (assembly)."""
import math

class Rows(list):
    def __init__(self, owner): super().__init__(); self.owner = owner
    def row(self, name, val, tgt, note="", higher_ok=True, procs=None):
        """procs=("mjf", "sla"): the two faces' processes. Adds tol_need (RSS of their tolerances) and flags rows whose slack
        is under it, so a 0.05 mm gap between two printed parts shows up as a risk even though it PASSes nominally."""
        ok = (val >= tgt - 1e-9) if higher_ok else (val <= tgt + 1e-9)
        slack = (val - tgt) if higher_ok else (tgt - val)
        d = dict(name=name, value=round(val, 3), target=(">= " if higher_ok else "<= ") + f"{tgt:g}", ok=ok, note=note, owner=self.owner,
                 slack=round(slack, 3))
        if procs:
            from .process import stack
            d["tol_need"] = round(stack(*procs), 3); d["tol_ok"] = val >= d["tol_need"] - 1e-9 if higher_ok else True
        self.append(d)

def maxr(shape):
    return max(math.hypot(v.X, v.Y) for v in shape.vertices())


def _bbox_gap(a, b):
    """Lower bound on the distance between two shapes: the gap between their bounding boxes (0 if they overlap)."""
    A, B = a.bounding_box(), b.bounding_box()
    d = [max(B.min.X - A.max.X, A.min.X - B.max.X, 0), max(B.min.Y - A.max.Y, A.min.Y - B.max.Y, 0),
         max(B.min.Z - A.max.Z, A.min.Z - B.max.Z, 0)]
    return math.sqrt(sum(x * x for x in d))


def min_dist(movers, obstacles):
    """Exact min distance between any mover and any obstacle (BRepExtrema), branch-and-bound on bounding boxes.
    Pairs are tried nearest-box first; once a box gap exceeds the best exact distance found, the rest are skipped.
    Same answer as min(m.distance_to(o) for m in movers for o in obstacles), far fewer OCC calls."""
    pairs = sorted(((_bbox_gap(m, o), i, j) for i, m in enumerate(movers) for j, o in enumerate(obstacles)))
    best = math.inf
    for lb, i, j in pairs:
        if lb >= best: break
        best = min(best, movers[i].distance_to(obstacles[j]))
    return best


def posed(build, poses):
    """Build a part once and rotate it to each dial pose (z axis). Only valid when build(D, t) == Rot(0, 0, t) * build(D, 0)."""
    from build123d import Rot
    s0 = build(0.0)
    return {t: Rot(0, 0, t) * s0 for t in poses}
