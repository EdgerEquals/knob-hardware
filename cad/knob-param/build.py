#!/usr/bin/env python3
"""Knob stack - ONE CLI for the parametric model (v0.15 default; outputs -> cad/assemblies/knob-stack-<version>/).
Full assembly (assembly agent):
  python build.py                       build all parts (cached) + local + cross checks + clashes
  python build.py --render              full sections PNG (A-A, iso quarter cut, insets B/C/D/H/E)
  python build.py --preview             fast low-res A-A + iso PNG
  python build.py --set knob_wall=1.8 --set feel.can_d=6      override any param (dotted for dict params)
One sub-assembly (sub-assembly agent; touches nothing else):
  python build.py --sub control_dial    build that sub-assembly's parts only + its LOCAL checks + its internal clashes
  python build.py --sub control_dial --preview   ... + a preview PNG of just those parts (out: cad/knob-param/out/)
Other: --full (committed KiCad STEP board instead of the proxy), --step, --no-check, --no-clash, --dump, --clear-cache,
       --contract (print the interface / exports / imports contract), --out PATH"""
import argparse, json, os, shutil, sys, time
T_START = time.time()
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
LIB = os.path.dirname(HERE)

def contract():
    from knobparam.common import model
    I = model.interface()
    print("INTERFACE params (assembly/interface.py):", ", ".join(I.P))
    D = model.derive(model.default_params())
    print("INTERFACE derived:", ", ".join(sorted(D.ikeys - set(I.P))))
    for s in model.SUBS:
        m = model.sub_params(s)
        print(f"{s}: own params {len(m.P)}, EXPORTS {m.EXPORTS}, IMPORTS {m.IMPORTS}")
    errs = list(model.validate()) + lint_imports(model.SUBS)
    print("contract:", "OK" if not errs else "FAIL"); [print("  -", e) for e in errs]
    if errs: sys.exit(1)

def lint_imports(subs):
    """Static rule: code inside knobparam/<sub>/ may import only knobparam.common and its own folder."""
    import ast
    errs, root = [], os.path.join(HERE, "knobparam")
    banned = set(subs) | {"assembly"}
    for s in subs:
        for dp, _, fs in os.walk(os.path.join(root, s)):
            if "kicad" in dp.split(os.sep): continue   # KiCad generator scripts are standalone tools
            for f in fs:
                if not f.endswith(".py"): continue
                p = os.path.join(dp, f); rel = os.path.relpath(p, root)
                depth = len(os.path.relpath(dp, root).split(os.sep))   # 1 = knobparam/<sub>/
                for n in ast.walk(ast.parse(open(p).read())):
                    mods = []
                    if isinstance(n, ast.ImportFrom):
                        if n.level == 0: mods = [n.module or ""]
                        elif n.level > depth:   # climbs out of <sub>/ -> resolve to the top-level name
                            mods = ["knobparam." + (n.module or "")] + ["knobparam." + a.name for a in n.names if not n.module]
                    elif isinstance(n, ast.Import): mods = [a.name for a in n.names]
                    for m in mods:
                        parts = m.split(".")
                        tgt = parts[1] if parts[0] == "knobparam" and len(parts) > 1 else None
                        if tgt and tgt != s and tgt in banned:
                            errs.append(f"{rel}:{n.lineno} imports {m} (cross-sub import; use interface params / EXPORTS)")
    return errs

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", action="append", default=[], metavar="NAME=VALUE", help="override a param (dotted for dict params)")
    ap.add_argument("--sub", default=None, help="build + check ONE sub-assembly: main_knob, control_dial, base_drive, under_pcb, electronics")
    ap.add_argument("--preview", action="store_true"); ap.add_argument("--render", action="store_true")
    ap.add_argument("--opposite", action="store_true", help="with --clean: view from the other side (A-A from -Y, iso from -X-Y; the other half / quadrant cut away)")
    ap.add_argument("--clean", action="store_true", help="clean assembly view: A-A + iso quarter cut + colour legend only (no insets/tables/clash text)")
    ap.add_argument("--full", action="store_true", help="committed KiCad STEP board instead of the proxy (no KiCad needed)")
    ap.add_argument("--step", action="store_true"); ap.add_argument("--no-check", action="store_true"); ap.add_argument("--no-clash", action="store_true")
    ap.add_argument("--dump", action="store_true"); ap.add_argument("--clear-cache", action="store_true"); ap.add_argument("--contract", action="store_true")
    ap.add_argument("--out", default=None, help="output PNG path")
    a = ap.parse_args()
    if a.contract: return contract()
    from knobparam.common import model, cache
    if a.clear_cache and os.path.isdir(cache.CACHE): shutil.rmtree(cache.CACHE)
    t = time.time(); D = model.derive(model.apply_overrides(model.default_params(), a.set)); t_der = time.time() - t
    V = D["version"]
    if a.sub and a.sub not in model.ALL: sys.exit(f"--sub must be one of {model.ALL}")
    OUT = os.path.join(HERE, "out", f"{a.sub}-{V}") if a.sub else os.path.join(LIB, "assemblies", f"knob-stack-{V}")
    if a.dump:
        keys = sorted(D.scope[a.sub]) if a.sub else sorted(D)
        for k in keys:
            if a.sub or k not in model.default_params() or a.set: print(f"{k} = {D[k]!r}  [{D.owner[k]}]"[:220])
    from knobparam.assembly.build import build_all
    t = time.time(); parts, stats, keys, owner = build_all(D, full_pcb=a.full, only=[a.sub] if a.sub else None); t_build = time.time() - t
    nb = sum(1 for s in stats if s[1] == "built")
    print(f"parts: {len(parts)} from {len(stats)} modules, {nb} rebuilt, {len(stats) - nb} cached, {t_build:.2f} s  " +
          " ".join(f"{s[0].split('.')[-1]}={s[2]:.2f}" for s in stats if s[1] == "built"))
    os.makedirs(OUT, exist_ok=True)
    from knobparam.assembly import checks as check
    clash_lines, cl = [], {}
    t_clash = t_render = t_gaps = 0.0
    if not a.no_check and not a.no_clash:   # pools first (fork safety), then BRepExtrema gaps
        t = time.time(); cl, cand, ran, dtc = check.clashes(parts, keys, D["tgt"]["clash_mm3"]); t_clash = time.time() - t
        clash_lines = [f"PAIRWISE CLASHES ({len(parts)} parts, {cand} bbox pairs, {ran} recomputed):"] + \
                      ([f"  {'KNOWN' if k in check.KNOWN else 'CLASH'} {k}: {v:.2f} mm³" for k, v in sorted(cl.items(), key=lambda kv: -kv[1])] or ["  none"])
    tm = None
    case_job = None
    if a.sub == "case" and (a.preview or a.render or a.clean or a.step):
        # the case has its own sheets (section, iso, plan, clean, quarter cuts) and STEP/STL/USDZ
        case_job = dict(preview=bool(a.preview) and not (a.render or a.clean),
                        full=bool(a.render or a.clean), export=bool(a.render or a.clean or a.step))
        a.preview = a.render = a.clean = a.step = False
    title = f"Knob stack {V} — sections in colour (2026-10-31; Ed / Edger_Equals, knob module v1, 10HP)" + (f"  [--set {' '.join(a.set)}]" if a.set else "")
    if a.sub: title = f"{a.sub} ({V}) — sub-assembly preview" + (f"  [--set {' '.join(a.set)}]" if a.set else "")
    if a.clean:
        from knobparam.assembly import render
        png = a.out or os.path.join(OUT, f"knob-stack-{V}-clean.png")
        t = time.time()
        ov = [x for x in a.set if not x.startswith("version=")]
        tm = render.render(D, parts, keys, png, clean=True, title=f"Knob stack {V} — assembly sections" + (" (OPPOSITE SIDE: A-A viewed from -Y, iso from -X-Y)" if a.opposite else ""), opposite=a.opposite,
                           note=(f"Overrides: {' '.join(ov)}." if ov else None))
        t_render = time.time() - t
        print(f"\nPNG: {png}  render {t_render:.1f} s  " + " ".join(f"{k}={v:.1f}" for k, v in tm.items())); tm = None
    elif a.preview or a.render:
        from knobparam.assembly import render
        if a.sub: a.preview, a.render = True, False   # sub-assembly renders are previews (insets need the whole stack)
        png = a.out or os.path.join(OUT, f"{'knob-stack-' + V if not a.sub else a.sub + '-' + V}-{'preview' if a.preview and not a.render else 'sections'}.png")
        t = time.time()
        tm = render.render(D, parts, keys, png, preview=a.preview and not a.render, clash_lines=clash_lines, gap_lines=[], title=title)
        t_render = time.time() - t
    rows = []
    if not a.no_check:
        t = time.time()
        rows = check.local(D, parts, owner, [a.sub] if a.sub else None)
        if not a.sub: rows += check.cross(D, parts)
        t_gaps = time.time() - t
        w = max(len(r["name"]) for r in rows)
        print(f"\n{'CHECK':{w}s}  {'value':>8s}  {'target':>8s}  result  {'owner':12s}  note"); print("-" * (w + 54))
        for r in rows: print(f"{r['name']:{w}s}  {r['value']:8.3f}  {r['target']:>8s}  {'PASS' if r['ok'] else 'FAIL'}    {r['owner']:12s}  {r['note']}")
        print(); print("\n".join(clash_lines))
        nf = sum(not r["ok"] for r in rows); nc = sum(1 for k in cl if k not in check.KNOWN)
        print(f"\nSUMMARY{' (' + a.sub + ', local only)' if a.sub else ''}: {len(rows) - nf}/{len(rows)} gap checks PASS, {nf} FAIL; {nc} unexpected clashes, {len(cl) - nc} known")
        json.dump(dict(rows=rows, clashes=cl, set=a.set, sub=a.sub), open(os.path.join(OUT, "check.json"), "w"), indent=1)
    if tm is not None:   # re-compose with the gap FAIL list now that gaps are known (matplotlib only, no OCC)
        from knobparam.assembly import render
        fails = [f"FAIL {r['name']}: {r['value']:.3f} ({r['target']})" for r in rows if not r["ok"]]
        g = (["GAP CHECKS: %d/%d PASS" % (len(rows) - len(fails), len(rows))] + fails) if rows else []
        tmp = render.TMP; prev = a.preview and not a.render
        ins = [] if prev else [f"{tmp}/{n}.png" for n in ("bb", "cc", "d", "ee") + (("hh",) if D["hall_layout"] == "vernier" else ())]
        render.compose(D, parts, f"{tmp}/aa.png", f"{tmp}/iso.png", ins, png, prev, clash_lines, g, title)
        print(f"\nPNG: {png}  render {t_render:.1f} s  " + " ".join(f"{k}={v:.1f}" for k, v in tm.items()))
    if case_job:
        from knobparam.case.render import render_case
        t = time.time()
        arts = render_case(D, parts, preview=case_job["preview"], full=case_job["full"], export=case_job["export"],
                           rows=rows, clashes=cl)
        t_render = time.time() - t
        print(f"\nCASE ({'preview' if case_job['preview'] else 'full'}) {t_render:.1f} s")
        for p in arts:
            print(f"  {p}")
    if a.step:
        from build123d import Compound, export_step
        export_step(Compound(children=list(parts.values())), os.path.join(OUT, f"knob-stack-{V}.step"))
    print(f"TIMES: derive {t_der:.3f} s, parts {t_build:.2f} s, clash {t_clash:.2f} s, render {t_render:.2f} s, gaps {t_gaps:.2f} s, "
          f"total wall incl. imports {time.time() - T_START:.1f} s")

if __name__ == "__main__":
    main()
