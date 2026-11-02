"""Top-screen joystick stack (v0.5): build, checks, clash, render.
  python build.py                 parts + checks + clashes -> ../assemblies/joystick-<version>/check.json
  python build.py --render        + joystick-<version>.png (A-A section + iso cut-away + plan) and -plan.png
  python build.py --preview       low-resolution isometric, before the colour render
  python build.py --set cs_turns=0.75   override any param (dotted for dicts: sw.tilt_travel=0.3)
  python build.py --step          + STEP of the whole stack"""
import argparse, ast, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)

def overrides(P, sets):
    import copy; P = copy.deepcopy(P)
    for s in sets:
        k, v = s.split("=", 1)
        try: v = ast.literal_eval(v)
        except Exception: pass
        if "." in k:
            a, b = k.split(".", 1); assert a in P and b in P[a], f"unknown param {k}"; P[a][b] = v
        else:
            assert k in P, f"unknown param {k}"; P[k] = v
    return P

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", action="append", default=[]); ap.add_argument("--render", action="store_true")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--section", action="store_true", help="low-res section on y=0 only")
    ap.add_argument("--step", action="store_true"); ap.add_argument("--out", default=None)
    a = ap.parse_args()
    from jsparam import params, parts, checks
    D = params.derive(overrides(params.P, a.set)); V = D["version"]
    OUT = a.out or os.path.join(os.path.dirname(HERE), "assemblies", f"joystick-{V}"); os.makedirs(OUT, exist_ok=True)
    t = time.time(); P = parts.build(D); print(f"parts: {len(P)} in {time.time() - t:.2f} s")
    rows = checks.run(D, P); cl = checks.clashes(P)
    KNOWN = {}   # none expected: contacts (balls/seats, board on the plate) are zero-volume
    w = max(len(r["name"]) for r in rows)
    print(f"\n{'CHECK':{w}s}  {'value':>8s}  {'target':>10s}  result  note"); print("-" * (w + 40))
    for r in rows: print(f"{r['name']:{w}s}  {r['value']:8.3f}  {r['target']:>10s}  {'PASS' if r['ok'] else 'FAIL'}    {r['note']}")
    print(f"\nPAIRWISE CLASHES ({len(P)} parts): " + ("none" if not cl else ""))
    for k, v in cl.items(): print(f"  {'KNOWN' if k in KNOWN else 'CLASH'} {k}: {v:.3f} mm³")
    nf = sum(not r["ok"] for r in rows)
    print(f"\nSUMMARY: {len(rows) - nf}/{len(rows)} checks PASS, {nf} FAIL; {len(cl)} clashes")
    vols = {n: P[n].volume / 1000.0 for n in P if n.startswith("joystick carrier") or n.startswith("screen carrier") or n.startswith("seat plate")}
    keyd = {k: D[k] for k in (
        "version", "riser_h", "stack_h", "scr_top", "z_knob_top", "z_db0", "z_db1", "z_stem_top", "z_c0",
        "z_ball", "z_scr0", "z_bz0", "z_bz1", "z_roof", "z_seat", "z_tip", "z_skirt0", "slide", "slide_need",
        "press_gap", "press_travel", "press_f", "cs_f_preload", "cs_f_press", "cs_f_turn", "cs_f_turn_1",
        "cs_turns", "turns_lo", "turns_hi", "turns_hex", "grub_protrude", "hex_proud", "car", "car_floor",
        "well_wall", "half_w", "half_h", "h_mid", "x_notch", "db", "db_xy", "place_y", "board_xy", "spr_len",
        "back_panel", "knob_od_live", "knob_od_design", "fpc_x", "slot_x", "hole_x0", "hole_x1", "hole_hy",
        "balls", "springs", "cs_xy", "standoff_xy", "sw_xy", "hdr_xy", "mate_in", "sx", "sy", "hx", "bx", "by",
        "board_x0", "board_x1", "board_y0", "board_y1", "cup_bore", "skirt_gap", "scr_clear", "glue")}
    keyd["volume_cm3"] = vols
    json.dump(dict(rows=rows, clashes=cl, set=a.set, key=keyd), open(os.path.join(OUT, "check.json"), "w"), indent=1, default=str)
    geom = dict(rev=V, pitch=D["pitch"], db_t=D["db_t"], corner_r=D["cu_edge"] + D["part_gap"],
                board=[D["board_x0"], D["board_y0"], D["board_x1"], D["board_y1"]],
                sw_xy=list(D["sw_xy"]), sw_rot=D["sw_rot"],
                headers=[list(p) for p in D["hdr_xy"]], standoffs=[list(p) for p in D["standoff_xy"]],
                drill_m2=D["drill_m2"], pad_m2=D["pad_m2"],
                hdr=D["hdr"], sock=D["sock"], standoff=D["standoff"],
                # v0.5: holes the joystick needs in the MAIN PCB, knob panel frame (joystick axis at (0, place_y))
                place_y=D["place_y"],
                main_pcb_holes=[dict(x=round(x, 3), y=round(y + D["place_y"], 3), d=D["drill_m2"], what="standoff screw M2")
                                for x, y in D["standoff_xy"]] +
                               [dict(x=round(x, 3), y=round(y + D["place_y"], 3), d=D["spr_bore"], what="hold-down spring")
                                for x, y in D["springs"]] +
                               [dict(x=round(x, 3), y=round(y + D["place_y"], 3), d=D["cradle"]["pin"]["d"] + 0.05,
                                     what="cradle locating dowel (NPTH)") for x, y in D.get("cr_pins", [])] +
                               [dict(x=round(x, 3), y=round(y + D["place_y"], 3), d=D["grub_access_d"],
                                     what="press-spring grub access (NPTH)") for x, y in D.get("access_xy", [])],
                # v0.5: header body footprint (x, y), pin offsets, the cradle ring and the socket tab
                hdr_body=[D["hdr_len"], D["hdr_wid"]], hdr_pins=[list(p) for p in D["hdr_pins"]],
                cradle_ring=dict(inner=[D.get("cr_in_x"), D.get("cr_in_y")], outer=[D.get("cr_out_x"), D.get("cr_out_y0"), D.get("cr_out_y1")]),
                fpc_socket=dict(part="Panasonic AXE530127", x=D.get("db_sock_x"), long_y=D["db_fpc_sock"][0], short_x=D["db_fpc_sock"][1]),
                tab=dict(x1=D.get("tab_x1"), hy=D.get("tab_hy")))
    gpath = os.path.join(os.path.dirname(HERE), "knob-param", "knobparam", "electronics", "kicad", "joystick-daughterboard", "geom.json")
    json.dump(geom, open(gpath, "w"), indent=1)
    print("geom:", gpath)
    if a.section and not a.render:
        from jsparam import render
        prev = os.path.join(OUT, f"joystick-{V}-section-preview.png")
        render.section_preview(D, P, prev); print("section:", prev)
    if a.preview and not a.render:
        from jsparam import render
        prev = os.path.join(OUT, f"joystick-{V}-preview.png")
        render.preview(D, P, prev); print("preview:", prev)
    if a.render:
        from jsparam import render
        png = os.path.join(OUT, f"joystick-{V}.png"); render.render(D, P, rows, png); print("PNG:", png)
    if a.step:
        from build123d import Compound, export_step
        export_step(Compound(children=list(P.values())), os.path.join(OUT, f"joystick-{V}.step"))

if __name__ == "__main__":
    main()
