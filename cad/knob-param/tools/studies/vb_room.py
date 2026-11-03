# Room on the main PCB FRONT for two vertical boards under the joystick [Ed 09:47-09:58], printed cradle and its sockets removed.
import sys, pickle, time
sys.path.insert(0, ".")
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from knobparam.assembly.section_atlas import _parts
from knobparam.assembly.plan_sheet import _cut_faces
t0 = time.time()
D, JD, parts = _parts()
GONE = ("joystick: joystick cradle", "joystick: cradle locating", "joystick: socket 2x5", "joystick: header 2x5", "joystick: header pin")
ZS = [0.2, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 29.5]
occ, names = {}, {}
for z in ZS:
    gs, nm = [], []
    for n, s in parts.items():
        if n == "PCB" or n.startswith(GONE): continue
        bb = s.bounding_box()
        if not (bb.min.Z <= z <= bb.max.Z) or bb.max.Y < 8: continue
        tris = _cut_faces(s, "z", z)
        g = unary_union([Polygon(t).buffer(1e-4) for t in tris if len(t) >= 3 and Polygon(t).area > 1e-9]) if tris else None
        if g is not None and not g.is_empty:
            gs.append(g); nm.append(n)
    occ[z] = unary_union(gs) if gs else Polygon(); names[z] = nm
    print(f"z {z:5.1f}: {len(gs)} parts", flush=True)
pickle.dump({"ZS": ZS, "occ": occ, "names": names}, open(f"{sys.argv[1]}/vb_occ.pkl", "wb"))
print("done", round(time.time() - t0), "s")
