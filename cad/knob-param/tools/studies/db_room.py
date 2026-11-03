# Room behind the main PCB for an H7B0 daughterboard [Ed 3 Nov 09:47]: occupancy slices at depths behind the board back (panel frame).
import sys, pickle, time
sys.path.insert(0, ".")
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from knobparam.assembly.section_atlas import _parts
from knobparam.assembly.plan_sheet import _cut_faces
t0 = time.time()
D, JD, parts = _parts()
zb = D["z_pcb_back"]
ZS = [zb - 0.05, zb - 0.5, zb - 1.0, zb - 1.5, zb - 2.0, zb - 3.0, zb - 4.0, zb - 5.0, zb - 6.0, zb - 7.0, zb - 8.0, zb - 9.0, zb - 10.0, zb - 11.0, zb - 12.0, zb - 13.0, zb - 14.0, zb - 15.0]
skip = ("PCB", "MCU ")
occ = {}
names = {}
for z in ZS:
    gs = []
    nm = []
    for n, s in parts.items():
        if n == "PCB" or n.startswith("MCU "): continue
        bb = s.bounding_box()
        if not (bb.min.Z <= z <= bb.max.Z): continue
        tris = _cut_faces(s, "z", z)
        g = unary_union([Polygon(t).buffer(1e-4) for t in tris if len(t) >= 3 and Polygon(t).area > 1e-9]) if tris else None
        if g is not None and not g.is_empty:
            gs.append(g); nm.append((n, round(g.area, 1)))
    occ[z] = unary_union(gs) if gs else Polygon()
    names[z] = nm
    print(f"z {z:6.2f}: {len(gs)} parts, {occ[z].area:.0f} mm²", flush=True)
pickle.dump({"ZS": ZS, "occ": occ, "names": names, "zb": zb, "pcb": (D["pcb_x1"], D["pcb_y0"], D["pcb_y1"])}, open(f"{sys.argv[1]}/db_occ.pkl", "wb"))
print("done", round(time.time() - t0), "s")
