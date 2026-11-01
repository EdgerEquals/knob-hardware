"""Top-screen joystick stack (v0.1): build, checks, clash, render.
  python build.py                 parts + checks + clashes -> ../assemblies/joystick-<version>/check.json
  python build.py --render        + joystick-<version>.png (A-A section + iso cut-away + plan)
  python build.py --set slide=0.35 --set sp_gap=0.45   override any param (dotted for dicts: sw.tilt_travel=0.3)
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
    ap.add_argument("--step", action="store_true"); ap.add_argument("--out", default=None)
    a = ap.parse_args()
    from jsparam import params, parts, checks
    D = params.derive(overrides(params.P, a.set)); V = D["version"]
    OUT = a.out or os.path.join(os.path.dirname(HERE), "assemblies", f"joystick-{V}"); os.makedirs(OUT, exist_ok=True)
    t = time.time(); P = parts.build(D); print(f"parts: {len(P)} in {time.time() - t:.2f} s")
    rows = checks.run(D, P); cl = checks.clashes(P)
    KNOWN = {}   # none expected: contacts (balls/seats, board on socket + post, spider on its ledge, screen on its land) are zero-volume
    w = max(len(r["name"]) for r in rows)
    print(f"\n{'CHECK':{w}s}  {'value':>8s}  {'target':>10s}  result  note"); print("-" * (w + 40))
    for r in rows: print(f"{r['name']:{w}s}  {r['value']:8.3f}  {r['target']:>10s}  {'PASS' if r['ok'] else 'FAIL'}    {r['note']}")
    print(f"\nPAIRWISE CLASHES ({len(P)} parts): " + ("none" if not cl else ""))
    for k, v in cl.items(): print(f"  {'KNOWN' if k in KNOWN else 'CLASH'} {k}: {v:.3f} mm³")
    nf = sum(not r["ok"] for r in rows)
    print(f"\nSUMMARY: {len(rows) - nf}/{len(rows)} checks PASS, {nf} FAIL; {len(cl)} clashes")
    keyd = {k: D[k] for k in ("riser_h", "stack_h", "z_db0", "z_db1", "z_stem_top", "z_c0", "z_ball", "z_scr0", "slide", "slide_need", "sp_gap", "sp_k", "press_f", "base_w", "base_h", "db", "car", "spr_len")}
    json.dump(dict(rows=rows, clashes=cl, set=a.set, key=keyd), open(os.path.join(OUT, "check.json"), "w"), indent=1, default=str)
    if a.render:
        from jsparam import render
        png = os.path.join(OUT, f"joystick-{V}.png"); render.render(D, P, rows, png); print("PNG:", png)
    if a.step:
        from build123d import Compound, export_step
        export_step(Compound(children=list(P.values())), os.path.join(OUT, f"joystick-{V}.step"))

if __name__ == "__main__":
    main()
