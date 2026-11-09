"""Main board v2 (KiCad) -> knob-main-pcb/pcb_proxy.json for the model's board proxy (electronics/parts/pcb.py), so the assembly
check sees the real board: the holes its footprints drill and every part's box on both faces. Panel frame (the board's own: KiCad
(100 + x, 100 - y)); parts the model already has as parts of their own are left out (the chip, the Halls, the ring LEDs, the
encoder sensor, the power light, the vertical boards' headers, the rod clamp, the motor tabs, the posts, flat pads).
Each part is its body's plan box (the fab outline with its pads, not the courtyard, which would make neighbours touch), with
the package's datasheet maximum height [A]. Also: the rod clamp's back pad (the nut clamps on it) as a radius from the rod's axis,
and where the parts the model places itself sit on the board, for the model to check against its own.
  /usr/bin/python3 export_proxy.py            (after make_board.py)"""
import os, json
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "kicad", "knob-main-pcb.kicad_pcb")
OUT = os.path.join(os.path.dirname(HERE), "pcb_proxy.json")
ORG = 100.0
H = {"C_0402_1005Metric": 0.55, "R_0402_1005Metric": 0.40, "C_0603_1608Metric": 0.90, "L_0603_1608Metric": 0.95,
     "C_0805_2012Metric": 1.35, "R_0805_2012Metric": 0.60, "SOT-23": 1.15, "SOT-23-5": 1.45, "SOT-23-6": 1.45,
     "SOT-23-6_TMAG5273_Tight": 1.45, "WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm": 0.80, "L_Taiyo-Yuden_NR-30xx": 1.50,
     "Crystal_SMD_3225-4Pin_3.2x2.5mm": 1.00}
MODELLED = {"U1", "U3", "U4", "U5", "U6", "U7", "U8", "D13", "J1", "J2", "J3", "J4", "J5", "JP1", "H1", "M1", "MP1", "MP2"} | \
           {f"D{i}" for i in range(1, 13)}
HOLE_SKIP = {"J2", "J3"}   # the headers' legs: the model drills them from vb_legs


def fr(v):
    return round(pcbnew.ToMM(v.x) - ORG, 4), round(ORG - pcbnew.ToMM(v.y), 4)


def body_box(fp, side):
    """The fab outline's box joined with the pads' (KiCad mm, x0 y0 x1 y1)."""
    fab = pcbnew.B_Fab if side == "B" else pcbnew.F_Fab
    xs, ys = [], []
    for g in fp.GraphicalItems():
        if g.GetLayer() == fab:
            bb = g.GetBoundingBox(); xs += [bb.GetLeft(), bb.GetRight()]; ys += [bb.GetTop(), bb.GetBottom()]
    for p in fp.Pads():
        bb = p.GetBoundingBox(); xs += [bb.GetLeft(), bb.GetRight()]; ys += [bb.GetTop(), bb.GetBottom()]
    return min(xs), min(ys), max(xs), max(ys)


b = pcbnew.LoadBoard(PCB)
holes, parts = [], {"F": [], "B": []}
missing = set()
for fp in b.GetFootprints():
    ref, name = fp.GetReference(), fp.GetFPID().GetLibItemName().wx_str()
    for p in fp.Pads():
        if p.GetAttribute() in (pcbnew.PAD_ATTRIB_NPTH, pcbnew.PAD_ATTRIB_PTH) and ref not in HOLE_SKIP:
            x, y = fr(p.GetPosition()); ds = p.GetDrillSize()
            holes.append(dict(ref=ref, x=x, y=y, d=round(pcbnew.ToMM(max(ds.x, ds.y)), 3),
                              plated=p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH))
    if ref in MODELLED:
        continue
    if name not in H:
        missing.add(name); continue
    side = "B" if fp.IsFlipped() else "F"
    x0, y0, x1, y1 = body_box(fp, side)
    c = fr(pcbnew.VECTOR2I((x0 + x1) // 2, (y0 + y1) // 2))
    parts[side].append(dict(ref=ref, fp=name, x=c[0], y=c[1], w=round(pcbnew.ToMM(x1 - x0), 3), l=round(pcbnew.ToMM(y1 - y0), 3), h=H[name]))
assert not missing, f"no height for {missing}"
# the rod clamp's back pad (ROD): its farthest point from the rod's axis (H1's centre)
h1 = next(f for f in b.GetFootprints() if f.GetReference() == "H1")
cx, cy_ = h1.GetPosition().x, h1.GetPosition().y
rod = next(p for p in h1.Pads() if p.GetNetname() == "ROD")
ps = rod.GetEffectivePolygon(); o = ps.Outline(0)
rod_pad_r = round(max(pcbnew.ToMM(int(((o.CPoint(i).x - cx) ** 2 + (o.CPoint(i).y - cy_) ** 2) ** 0.5)) for i in range(o.PointCount())), 3)
fixed = {f.GetReference(): [*fr(f.GetPosition()), round(f.GetOrientationDegrees(), 2), "B" if f.IsFlipped() else "F"]
         for f in b.GetFootprints() if f.GetReference() in MODELLED}
json.dump(dict(src=os.path.relpath(PCB, os.path.dirname(OUT)), frame="panel", rod_pad_r=rod_pad_r, fixed=fixed, holes=holes, slots=[],
               back_parts=sorted(parts["B"], key=lambda d: d["ref"]), front_parts=sorted(parts["F"], key=lambda d: d["ref"])),
          open(OUT, "w"), indent=1)
print("rod pad r", rod_pad_r, ";", len(holes), "holes,", len(parts["B"]), "back parts,", len(parts["F"]), "front parts ->", OUT)
