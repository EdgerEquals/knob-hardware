"""The routed main board's copper as meshes for the 3D viewer (tools/web_model.py --extra): tracks, pads and vias per layer,
in the model's panel frame (KiCad (100 + x, 100 - y)), each layer a thin slab at its height in the 1.6 mm board. The two ground
planes (In1, In4) are left out: they would hide everything inside.
  /usr/bin/python3 export_copper_mesh.py <out dir> <board top z> [board thickness 1.6]
Writes <out dir>/copper_<layer>.npz (P float32 n x 3, T int32 m x 3) and copper.json (the parts list for web_model.py)."""
import json, math, os, sys
import numpy as np
import pcbnew
from shapely.geometry import Polygon
from shapely.ops import triangulate

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "kicad", "knob-main-pcb.kicad_pcb")
OUT = sys.argv[1]; ZTOP = float(sys.argv[2]); T_PCB = float(sys.argv[3]) if len(sys.argv) > 3 else 1.6
CU = 0.035
LAYERS = [(pcbnew.F_Cu, "front", ZTOP + CU), (pcbnew.In2_Cu, "In2", ZTOP - 0.45), (pcbnew.In3_Cu, "In3", ZTOP - T_PCB + 0.45 + CU),
          (pcbnew.B_Cu, "back", ZTOP - T_PCB)]   # z of each slab's top face: front and back stand proud of the board by 0.035, so they don't fight its faces


def xy(v):
    return pcbnew.ToMM(v.x) - 100.0, 100.0 - pcbnew.ToMM(v.y)


class Mesh:
    def __init__(self):
        self.P, self.T = [], []

    def prism(self, ring, z0, z1):
        """A closed prism over a convex-or-not outline ring (triangulated top and bottom, quads round the side)."""
        n0 = len(self.P); k = len(ring)
        for x, y in ring:
            self.P.append((x, y, z0))
        for x, y in ring:
            self.P.append((x, y, z1))
        poly = Polygon(ring)
        if not poly.is_valid or poly.area <= 0:
            return
        tris = [t for t in triangulate(poly) if poly.buffer(1e-6).contains(t.centroid)] if k > 4 else None
        idx = {p: i for i, p in enumerate(ring)}
        if tris is None:   # quad or triangle: a fan
            caps = [(0, i, i + 1) for i in range(1, k - 1)]
        else:
            caps = []
            for t in tris:
                c = list(t.exterior.coords)[:3]
                ids = [idx.get(min(idx, key=lambda q: (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2)) for p in c]
                caps.append(tuple(ids))
        for a, b, c in caps:
            self.T.append((n0 + a, n0 + c, n0 + b)); self.T.append((n0 + k + a, n0 + k + b, n0 + k + c))
        for i in range(k):
            j = (i + 1) % k
            self.T.append((n0 + i, n0 + j, n0 + k + j)); self.T.append((n0 + i, n0 + k + j, n0 + k + i))

    def save(self, path):
        np.savez_compressed(path, P=np.asarray(self.P, np.float32), T=np.asarray(self.T, np.int32))
        return len(self.T)


def seg_ring(a, b, w):
    (ax, ay), (bx, by) = a, b; L = math.hypot(bx - ax, by - ay)
    if L < 1e-6:
        return circle((ax, ay), w / 2, 8)
    ux, uy = (bx - ax) / L, (by - ay) / L; nx, ny = -uy * w / 2, ux * w / 2
    ax, ay, bx, by = ax - ux * w / 2, ay - uy * w / 2, bx + ux * w / 2, by + uy * w / 2   # square ends half a width out
    return [(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)]


def circle(c, r, n):
    return [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


b = pcbnew.LoadBoard(PCB)
meshes = {lid: Mesh() for lid, _n, _z in LAYERS}
zof = {lid: z for lid, _n, z in LAYERS}
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        continue
    if t.GetLayer() in meshes:
        z = zof[t.GetLayer()]
        meshes[t.GetLayer()].prism(seg_ring(xy(t.GetStart()), xy(t.GetEnd()), pcbnew.ToMM(t.GetWidth())), z - CU, z)
for f in b.GetFootprints():
    for p in f.Pads():
        for lid in (pcbnew.F_Cu, pcbnew.B_Cu):
            if not p.IsOnLayer(lid):
                continue
            ps = p.GetEffectivePolygon()
            for k in range(ps.OutlineCount()):
                o = ps.Outline(k)
                ring = [xy(o.CPoint(i)) for i in range(o.PointCount())]
                ring = [q for i, q in enumerate(ring) if i == 0 or q != ring[i - 1]]
                if len(ring) >= 3:
                    meshes[lid].prism(ring, zof[lid] - CU, zof[lid])
vias = Mesh()
for v in b.GetTracks():
    if v.GetClass() == "PCB_VIA":
        vias.prism(circle(xy(v.GetPosition()), pcbnew.ToMM(v.GetWidth()) / 2, 8), ZTOP - T_PCB - CU, ZTOP + CU)
os.makedirs(OUT, exist_ok=True)
parts = []
for lid, name, _z in LAYERS:
    path = os.path.join(OUT, f"copper_{name}.npz"); nt = meshes[lid].save(path)
    P = np.asarray(meshes[lid].P)
    parts.append(dict(n=f"main board copper: {name} (tracks{' and pads' if name in ('front', 'back') else ''})", sub="board_copper", mesh=path,
                      bb=[float(v) for v in (*P.min(axis=0), *P.max(axis=0))], tris=nt))
path = os.path.join(OUT, "copper_vias.npz"); nt = vias.save(path); P = np.asarray(vias.P)
parts.append(dict(n="main board copper: vias", sub="board_copper", mesh=path, bb=[float(v) for v in (*P.min(axis=0), *P.max(axis=0))], tris=nt))
json.dump(parts, open(os.path.join(OUT, "copper.json"), "w"), indent=1)
print({p["n"]: p["tris"] for p in parts})
