"""Top-screen joystick stack (v0.9): build, checks, clash, render.
  python build.py                 parts + checks + clashes -> ../assemblies/joystick-<version>/check.json, and the top board's geom.json
  python build.py --render        + joystick-<version>.png (A-A section + iso cut-away + plan) and -plan.png
  python build.py --preview       low-resolution isometric, before the colour render
  python build.py --set spr_f=1.0   override any param (dotted for dicts: sw.tilt_travel=0.3)
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
    KNOWN = {}   # none expected: contacts (balls/seats, board under the shoulders) are zero-volume
    w = max(len(r["name"]) for r in rows)
    print(f"\n{'CHECK':{w}s}  {'value':>8s}  {'target':>10s}  result  note"); print("-" * (w + 40))
    for r in rows: print(f"{r['name']:{w}s}  {r['value']:8.3f}  {r['target']:>10s}  {'PASS' if r['ok'] else 'FAIL'}    {r['note']}")
    print(f"\nPAIRWISE CLASHES ({len(P)} parts): " + ("none" if not cl else ""))
    for k, v in cl.items(): print(f"  {'KNOWN' if k in KNOWN else 'CLASH'} {k}: {v:.3f} mm³")
    nf = sum(not r["ok"] for r in rows)
    print(f"\nSUMMARY: {len(rows) - nf}/{len(rows)} checks PASS, {nf} FAIL; {len(cl)} clashes")
    vols = {n: P[n].volume / 1000.0 for n in P if n.startswith("joystick carrier") or n.startswith("screen carrier")}
    keyd = {k: D[k] for k in (
        "version", "riser_h", "stack_h", "scr_top", "z_knob_top", "z_db0", "z_db1", "z_stem_top", "z_c0",
        "z_ball", "z_scr0", "z_bz0", "z_bz1", "z_roof", "slide", "slide_need",
        "press_gap", "press_travel", "car", "car_floor",
        "well_wall", "half_w", "half_h", "h_mid", "x_notch", "db", "db_xy", "place_y", "board_xy", "spr_len",
        "knob_od_live", "knob_od_design", "fpc_x", "slot_x",
        "balls", "springs", "sw_xy", "bx", "by",
        "board_x0", "board_x1", "board_y0", "board_y1", "cup_bore", "scr_clear", "glue")}
    for k in ("cup_col_od", "car_cup_hole", "g_boss0", "g_len", "g_sleeve_len", "us_rss", "us_wc", "us_gap", "us_float", "us_room",
              "preload_max", "preload_lim", "us_table", "sock_y", "sock_pin_y", "z_sock0", "eng_nom", "gk_nom", "gk_range", "bead_band",
              "bead_band_net", "z_fl1", "z_reb1", "z_dam1", "st_y0", "step_land", "tb_flex", "tb_span",   # v0.8
              "fl_drop", "tb_notch", "tb_notch_size", "tb_notch_y0", "tb_plate", "tb_k", "op_gap", "op_f", "glue_len", "glue_q_click",
              "glue_q_op", "sf_up_wc", "vb_pin_x", "board_x1"):   # v0.9
        if k in D:
            keyd[k] = D[k]
    keyd["volume_cm3"] = vols
    json.dump(dict(rows=rows, clashes=cl, set=a.set, key=keyd), open(os.path.join(OUT, "check.json"), "w"), indent=1, default=str)
    geom = dict(rev=V, pitch=D["pitch"], db_t=D["db_t"], corner_r=D["cu_edge"] + D["part_gap"],
                board=[D["board_x0"], D["board_y0"], D["board_x1"], D["board_y1"]],
                sw_xy=list(D["sw_xy"]), sw_rot=D["sw_rot"],
                # v0.5: holes the joystick needs in the MAIN PCB, knob panel frame (joystick axis at (0, place_y)); read by the knob
                # model's electronics (js_pcb_holes). Since v0.8 the hold-down spring bores are the only ones
                place_y=D["place_y"],
                main_pcb_holes=[dict(x=round(x, 3), y=round(y + D["place_y"], 3), d=D["spr_bore"], what="hold-down spring")
                                for x, y in D["springs"]],
                fpc_socket=dict(part="Panasonic AXE530127", x=D.get("db_sock_x"), long_y=D["db_fpc_sock"][0], short_x=D["db_fpc_sock"][1]))
    # v0.8 [Ed 13:46/14:08]: what the KiCad top-board generator needs next (not yet read by it)
    S = D["tb_sock"]
    geom["top_joint"] = dict(kind="sockets", part=S["part"], pitch=S["pitch"], n=S["n"], side="bottom (SMT)",
                             rows_x=[-D["vb_pin_x"], D["vb_pin_x"]], pin_y=[round(y, 3) for y in D["sock_pin_y"]],
                             body=[S["w"], round(D["sock_len"], 3), S["h"]], pad_hw=S["pad_hw"],
                             post_land="bare board under the vertical boards' end tabs (x ±15.5..16.5, beyond the sockets in y)")
    geom["guide_keepout"] = [dict(x=x, y=y, d=D["guide"]["head_d"] + 2 * D["tol_mjf"], what="no parts under the guide heads")
                             for x, y in D["g_xy"]]
    geom["notes"] = ("v0.8: no spring-contact pads, no grub-access holes; two 13-way 1.27 sockets on the underside; the board is "
                     f"±{D['board_x1']:.2f} wide (v0.7 ±18.90)")
    if D.get("cradle_in_case"):   # v0.9 [Ed 18:35 / 19:12]
        geom["top_joint"]["post_land"] = "none: the vertical boards' end tabs clear the top board (the pins take the stack)"
        geom["top_joint"]["pads"] = "alternate sides (single-row SMT socket); the end pin by each corner notch has its pad inboard [A]"
        geom["corner_notches"] = [dict(post_x=round(x, 3), post_y=round(y, 3), r=round(r, 3),
                                       square_from_x=round((abs(x) - r) * (1 if x > 0 else -1), 3), up_to_y=round(D["board_y1"], 3),
                                       what="notch round the top corner post, squared off to the board's +y edge (no copper within 0.3)")
                                  for x, y, r in D.get("tb_notch", ())]
        geom["notes"] = (f"v0.9: board ±{D['board_x1']:.2f} (v0.8 ±19.25); the socket rows 0.3 inboard (x ±{D['vb_pin_x']:g}) and "
                         f"{D['sock_y_shift']:+g} in y; 4.5 tall sockets; corner notches {D['tb_notch_size'][0]:.2f} × "
                         f"{D['tb_notch_size'][1]:.2f}; glued up under the printed shoulders of the case (no bare lands for posts)")
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
