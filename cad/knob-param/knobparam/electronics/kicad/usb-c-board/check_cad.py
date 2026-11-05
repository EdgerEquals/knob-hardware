"""USB-C board vs the knob model (step 2, 5 Nov 2026): the KiCad board (placement.json, written by kicad/make_board.py) must put
the socket, its legs and posts, the 8 spring-contact landing pads and the two protection parts where the CAD model has them
(case/params.py, the CAD version named in placement.json).
Run from cad/knob-param:  PYTHONPATH=. .venv/bin/python knobparam/electronics/kicad/usb-c-board/check_cad.py
Writes check_cad.txt next to this file and exits 1 on any FAIL."""
import json, math, os, sys
sys.path.insert(0, ".")
from knobparam.common import model

HERE = os.path.dirname(os.path.abspath(__file__))
TOL = 0.005
NET = {"15 V": "VBUS", "GND": "GND", "D+": "DP", "D-": "DN", "CC1": "CC1", "CC2": "CC2"}


def main():
    D = model.derive(model.default_params())
    pl = json.load(open(os.path.join(HERE, "placement.json")))
    rows = []

    def row(name, ok, detail):
        rows.append(("PASS" if ok else "FAIL", name, detail))
    cx, cy = D["usb_xy"]
    bx, by = pl["board"]["centre"]
    row("socket centre (board centre)", abs(bx - cx) <= TOL and abs(by - cy) <= TOL, f"board ({bx:.3f}, {by:.3f}), model ({cx:.3f}, {cy:.3f})")
    bw, bh, bt = D["usb_board"]
    row("board size", (pl["board"]["w"], pl["board"]["h"], pl["board"]["t"]) == (bw, bh, bt),
        f"board {pl['board']['w']} x {pl['board']['h']} x {pl['board']['t']}, model {bw} x {bh} x {bt}")
    row("board top / bottom edge", abs(by + pl["board"]["h"] / 2 - D["usb_board_y1"]) <= TOL and abs(by - pl["board"]["h"] / 2 - D["usb_board_y0"]) <= TOL,
        f"board y {by - pl['board']['h'] / 2:.3f} .. {by + pl['board']['h'] / 2:.3f}, model {D['usb_board_y0']:.3f} .. {D['usb_board_y1']:.3f}")
    pads = pl["pads"]
    for (x, y), nm in zip(D["usb_pwr_contacts"], D["usb_pwr_names"]):
        near = [p for p in pads if p["ref"].startswith("P") and math.dist(p["xy"], (x, y)) <= TOL]
        ok = len(near) == 1 and near[0]["net"] == NET[nm] and abs(near[0]["size"][0] - D["usb_pwr_pad"]) <= TOL
        det = f"model ({x:.2f}, {y:.2f}) {nm}: " + (f"{near[0]['ref']} net {near[0]['net']}, pad {near[0]['size'][0]}" if near else "no landing pad there")
        row(f"spring contact {nm} at ({x:.1f}, {y:.1f})", ok, det)
    legs = [p for p in pads if p["ref"] == "J1" and p["num"] == "S"]
    for lx, ly in D["usb_shell_legs"]:
        near = [p for p in legs if math.dist(p["xy"], (cx + lx, cy + ly)) <= TOL]
        ok = len(near) == 1 and abs(near[0]["size"][0] - D["usb_leg_pad"][0]) <= TOL and abs(near[0]["size"][1] - D["usb_leg_pad"][1]) <= TOL
        row(f"shell leg ({lx:+.2f}, {ly:+.2f})", ok, (f"pad {near[0]['size'][0]} x {near[0]['size'][1]}, model {D['usb_leg_pad'][0]} x {D['usb_leg_pad'][1]}"
                                                      if near else "no leg pad there"))
    holes = [p for p in pads if p["ref"] == "J1" and p["num"] == ""]
    for px, py in D["usb_posts"]:
        near = [p for p in holes if math.dist(p["xy"], (cx + px, cy + py)) <= TOL]
        ok = len(near) == 1 and near[0]["drill"] <= D["usb_post_hole"] + TOL
        row(f"locating post hole ({px:+.2f})", ok, (f"hole {near[0]['drill']}, model {D['usb_post_hole']} (the model's hole is the larger, so its "
                                                    f"gaps are the worse case)" if near else "no hole there"))
    clear = D["usb_pocket_clear"]
    refs = {"TVS": "D1", "ESD": "U1"}
    for name, x0, x1, y0, y1, h in D["usb_prot"]:
        ref = refs["TVS" if "TVS" in name else "ESD"]
        part = pl["parts"].get(ref)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        ok = part is not None and part["side"] == "B" and math.dist(part["xy"], (mx, my)) <= TOL
        det = (f"{ref} {part['value']} on side {part['side']} at ({part['xy'][0]:.3f}, {part['xy'][1]:.3f}); model body "
               f"{x1 - x0:.2f} x {y1 - y0:.2f} centred ({mx:.3f}, {my:.3f}), key pocket {clear} round it") if part else f"{ref} missing"
        row(f"{name.split(' [')[0]} in its key pocket", ok, det)
        if part and ref == "U1":
            ext = [p for p in pads if p["ref"] == "U1"]
            px0 = min(p["xy"][0] - p["size"][0] / 2 for p in ext); px1 = max(p["xy"][0] + p["size"][0] / 2 for p in ext)
            row("U1 pads inside the pocket outline (copper only, 0.035 high)", px0 >= x0 - clear - TOL and px1 <= x1 + clear + TOL,
                f"pads x {px0:.3f} .. {px1:.3f}; pocket x {x0 - clear:.3f} .. {x1 + clear:.3f}")
    out = [f"USB-C board {pl['pcb_version']} vs knob model {pl['cad_version']} (tolerance {TOL} mm)"]
    out += [f"  {s}  {n}: {d}" for s, n, d in rows]
    nf = sum(1 for s, *_ in rows if s == "FAIL")
    out.append(f"{len(rows) - nf}/{len(rows)} PASS")
    txt = "\n".join(out) + "\n"
    open(os.path.join(HERE, "check_cad.txt"), "w").write(txt)
    print(txt)
    return 1 if nf else 0


if __name__ == "__main__":
    sys.exit(main())
