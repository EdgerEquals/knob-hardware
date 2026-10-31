"""Check-row helper shared by the local checks (each sub-assembly) and the cross-checks (assembly)."""
import math

class Rows(list):
    def __init__(self, owner): super().__init__(); self.owner = owner
    def row(self, name, val, tgt, note="", higher_ok=True):
        ok = (val >= tgt - 1e-9) if higher_ok else (val <= tgt + 1e-9)
        self.append(dict(name=name, value=round(val, 3), target=(">= " if higher_ok else "<= ") + f"{tgt:g}", ok=ok, note=note, owner=self.owner))

def maxr(shape):
    return max(math.hypot(v.X, v.Y) for v in shape.vertices())
