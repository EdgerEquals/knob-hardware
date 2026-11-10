"""KiCad knob-main-pcb -> knob-main-pcb/pcb_proxy.json for the CAD board proxy (electronics/parts/pcb.py). Run with /usr/bin/python3
after make_board.py. Frame coords (dial axis origin, y up): x = bx - 25.25, y = 52.9 - by (board mm, KiCad origin offset removed).
Writes: NPTH / plated holes not already in the proxy (M1 relief, joystick springs / pins / FPC slot) and the B.Cu part envelopes
(courtyard bbox, height by package [A])."""
import os, json, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "knob-main-pcb", "kicad", "knob-main-pcb.kicad_pcb")
OUT = os.path.join(HERE, "knob-main-pcb", "pcb_proxy.json")
AX, AY, ORG = 25.25, 52.9, 100.0
H = {"C_0402": 0.5, "R_0402": 0.35, "C_0603": 0.8, "WSON-8_2x2_DRV8837": 0.8, "Pads_2x14_P2.00_SMD": 0.05}   # [A] body heights
SKIP_BACK = {"M2", "H1", "U2"}   # modelled elsewhere (716 lead pads, rod pad, encoder sensor part)
def fr(v): return (round(pcbnew.ToMM(v.x) - ORG - AX, 4), round(AY - (pcbnew.ToMM(v.y) - ORG), 4))
b = pcbnew.LoadBoard(PCB)
holes, slots, back = [], [], []
for fp in b.GetFootprints():
    ref, name = fp.GetReference(), fp.GetFPID().GetLibItemName().wx_str()
    if ref in ("M1", "MH1"):
        for p in fp.Pads():
            if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH: continue
            x, y = fr(p.GetPosition()); ds = p.GetDrillSize()
            if ds.x == ds.y: holes.append(dict(ref=ref, x=x, y=y, d=round(pcbnew.ToMM(ds.x), 3)))
            else:
                bb = p.GetBoundingBox(); slots.append(dict(ref=ref, x=x, y=y, dx=round(pcbnew.ToMM(bb.GetWidth()), 3), dy=round(pcbnew.ToMM(bb.GetHeight()), 3)))
    if fp.IsFlipped() and ref not in SKIP_BACK:
        bb = fp.GetCourtyard(pcbnew.B_CrtYd).BBox() if fp.GetCourtyard(pcbnew.B_CrtYd).OutlineCount() else fp.GetBoundingBox(False)
        c = fr(bb.Centre())
        back.append(dict(ref=ref, fp=name, x=c[0], y=c[1], w=round(pcbnew.ToMM(bb.GetWidth()), 3), l=round(pcbnew.ToMM(bb.GetHeight()), 3), h=H.get(name, 0.8)))
json.dump(dict(src=os.path.relpath(PCB, HERE), holes=holes, slots=slots, back_parts=sorted(back, key=lambda d: d["ref"])), open(OUT, "w"), indent=1)
print(len(holes), "holes", len(slots), "slots", len(back), "back parts ->", OUT)
