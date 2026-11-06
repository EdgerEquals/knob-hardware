"""Footprint area of the jack power board's parts against the free board (knob step 2, 6 Nov 2026).
Sums each part's courtyard (KiCad library footprints read from /usr/share/kicad/footprints; this board's own footprints by the sizes
below) by block, and the free area of each face (outline minus the connectors' courtyards and a 0.25 band along the edge).
Run:  python3 area.py [out.json]"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design

KLIB = "/usr/share/kicad/footprints/"
OWN = {   # courtyard (w, h) of this board's own footprints [S-lib / S datasheet drawings, see design.py notes]
    "jpb:Hirose_FH26W-25S-0.3SHW": (10.0, 4.95),       # KiCad's Hirose_FH26-25S footprint courtyard
    "jpb:XUNPU_FPC-05F-24PH20": (17.4, 5.7),           # [S-lib] about 16.3 x 5.2 body + mounting pads, + 0.25 courtyard
    "jpb:TI_RPW0010A_VQFN-HR-10_2x2": (2.6, 2.4),
    "jpb:HUSB238_DFN-10_3x3": (3.5, 4.26),
    "jpb:Post_Pad": (0.0, 0.0),
}
BLOCKS = {"connectors": "connectors", "supply": "supply", "power in": "supply", "dac": "jack circuits", "jack circuits": "jack circuits",
          "jack1": "jack circuits", "jack2": "jack circuits", "jack3": "jack circuits", "audio": "jack circuits", "digital": "digital",
          "oled": "OLED"}


def courtyard(fp):
    if fp in OWN:
        return OWN[fp]
    lib, name = fp.split(":")
    t = open(os.path.join(KLIB, lib + ".pretty", name + ".kicad_mod")).read()
    xs, ys = [], []
    for m in re.finditer(r'\((fp_line|fp_rect|fp_poly|fp_circle)(.*?)\(layer "?F\.CrtYd"?\)', t, re.S):
        for a, b in re.findall(r'\((?:start|end|xy|center) ([-\d.]+) ([-\d.]+)\)', m.group(2)):
            xs.append(float(a)); ys.append(float(b))
    return max(xs) - min(xs), max(ys) - min(ys)


def main(out=None):
    parts = design.build()
    need, n_by = {}, {}
    rows = []
    for p in parts:
        w, h = courtyard(p["fp"])
        blk = BLOCKS.get(p["block"], p["block"])
        if p["ref"][0] in "RC" or p["ref"].startswith("FB"):
            blk = "passives"
        rows.append((p["ref"], p["value"], p["fp"].split(":")[1], round(w * h, 2), blk))
        need[blk] = need.get(blk, 0) + w * h
        n_by[blk] = n_by.get(blk, 0) + 1
    conn = need.pop("connectors", 0.0)
    # free board: the jack row 43.0 x 10.5 (+ two ears 2.6 x 2.6 round the posts), less a 0.25 band along the edge
    row = 43.0 * 10.5; ears = 2 * 2.6 * 2.6 - 2 * 3.14159 * 0.55 ** 2; band = 0.25 * (2 * (43.0 + 10.5) + 4 * 2.6)
    face = row + ears - band
    sock = 2 * courtyard("Connector_PinSocket_1.27mm:PinSocket_2x06_P1.27mm_Vertical_SMD")[0] * \
        courtyard("Connector_PinSocket_1.27mm:PinSocket_2x06_P1.27mm_Vertical_SMD")[1]
    zifs = OWN["jpb:XUNPU_FPC-05F-24PH20"][0] * OWN["jpb:XUNPU_FPC-05F-24PH20"][1] + 10.0 * 4.95
    free = {"top face": face - sock, "bottom face": face - zifs}
    # option A: a second board (the jack row only, no ears) under it on two more 2x6 stacks; the ZIFs move to its underside
    face_b = row - 0.25 * 2 * (43.0 + 10.5)
    two = (face - sock) + (face - sock) + (face_b - sock) + (face_b - zifs)
    res = dict(need={k: round(v, 1) for k, v in sorted(need.items(), key=lambda kv: -kv[1])}, count=n_by,
               free={k: round(v, 1) for k, v in free.items()}, free_two_boards=round(two, 1), connectors=round(conn, 1),
               total_need=round(sum(need.values()), 1), total_free=round(sum(free.values()), 1), parts=len(parts), rows=rows)
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))
    if out:
        json.dump(res, open(out, "w"), indent=1)
    return res


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
