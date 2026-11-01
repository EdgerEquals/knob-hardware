"""Tiny schematic writer (pure Python, no KiCad needed) so each board's netlist lives in ONE place (its design.py) and both the
KiCad schematic (.kicad_sch + project symbol library knob.kicad_sym) and the board (make_board.py, pcbnew) are generated from it.
Every symbol is a plain box; each pin gets a net label at its end (or a no-connect flag), so ERC checks pin types / drivers and
the PCB is checked against it with DRC schematic parity. Symbol UUIDs are deterministic (uuid5 of the reference) so the PCB
footprints can carry the matching path."""
import uuid, os

NS = uuid.UUID("6b1f3f0e-6f0e-4c39-9a51-0d4f1b7c2a11")
def uid(*k): return str(uuid.uuid5(NS, "/".join(map(str, k))))
G = 2.54

def _q(s): return '"' + str(s).replace('"', "'") + '"'

def sym_def(name, pins, lib="knob", ref="U", power=False):
    """pins: [(num, name, etype, side)], side L/R. Returns the lib_symbols text (body + pins)."""
    nl = sum(1 for p in pins if p[3] == "L"); nr = len(pins) - nl
    h = max(nl, nr, 1) * G; w = 7.62 if len(pins) <= 2 else 12.7
    top = h / 2
    out = [f'(symbol {_q(lib + ":" + name if lib else name)} (pin_names (offset 0.762)) (exclude_from_sim no) (in_bom {"no" if power else "yes"}) (on_board {"no" if power else "yes"})',
           f'  (property "Reference" {_q(ref)} (at 0 {top + 1.5:.2f} 0) (effects (font (size 1.27 1.27))))',
           f'  (property "Value" {_q(name)} (at 0 {-top - 1.5:.2f} 0) (effects (font (size 1.27 1.27))))',
           '  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
           '  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
           f'  (symbol {_q(name + "_0_1")} (rectangle (start {-w / 2:.2f} {top:.2f}) (end {w / 2:.2f} {-top:.2f}) (stroke (width 0.254) (type default)) (fill (type background))))',
           f'  (symbol {_q(name + "_1_1")}']
    li = ri = 0; pos = {}
    for num, pname, et, side in pins:
        if side == "L": y = top - G / 2 - li * G; li += 1; x = -w / 2 - G; ang = 0
        else: y = top - G / 2 - ri * G; ri += 1; x = w / 2 + G; ang = 180
        pos[num] = (x, y, side)
        out.append(f'    (pin {et} line (at {x:.2f} {y:.2f} {ang}) (length {G}) (name {_q(pname)} (effects (font (size 1.0 1.0)))) (number {_q(num)} (effects (font (size 1.0 1.0)))))')
    out.append("  )"); out.append("  (embedded_fonts no)"); out.append(")")
    return "\n".join(out), pos, h, w

def write(path, title, project, comps, rev="", comment="", paper="A3"):
    """comps: [dict(ref, sym, pins=[(num,name,etype,side)], value, footprint, nets={num: net or None(NC)}, fields={}, bom=True)]"""
    root = uid(project, "root")
    libs, placed, labels, ncs = {}, [], [], []
    x0, y0, col_w, x, y, colmax = 30.0, 30.0, 70.0, 30.0, 30.0, 0.0
    for c in comps:
        key = c["sym"]
        if key not in libs: libs[key] = sym_def(key, c["pins"], ref=c["ref"].rstrip("0123456789") or "U")
        txt, pos, h, w = libs[key]
        if y + h + 12 > 270: x += col_w; y = y0
        cx, cy = round((x + 20) / 1.27) * 1.27, round((y + h / 2 + 5) / 1.27) * 1.27
        y += h + 14
        u = uid(project, c["ref"])
        f = dict(c.get("fields", {}))
        props = [("Reference", c["ref"], 0, -h / 2 - 2.5, False), ("Value", c["value"], 0, h / 2 + 2.5, False),
                 ("Footprint", c["footprint"], 0, h / 2 + 4.5, True), ("Datasheet", f.pop("Datasheet", ""), 0, 0, True)]
        for k, v in f.items(): props.append((k, v, 0, 0, True))
        P = [f'(symbol (lib_id {_q("knob:" + key)}) (at {cx:.2f} {cy:.2f} 0) (unit 1) (exclude_from_sim no) (in_bom {"yes" if c.get("bom", True) else "no"}) (on_board yes) (dnp no)',
             f'  (uuid {_q(u)})']
        for k, v, dx, dy, hid in props:
            P.append(f'  (property {_q(k)} {_q(v)} (at {cx + dx:.2f} {cy + dy:.2f} 0) (effects (font (size 1.27 1.27)){" (hide yes)" if hid else ""}))')
        for num, *_ in c["pins"]: P.append(f'  (pin {_q(num)} (uuid {_q(uid(project, c["ref"], "pin", num))}))')
        P.append(f'  (instances (project {_q(project)} (path {_q("/" + root)} (reference {_q(c["ref"])}) (unit 1))))')
        P.append(")"); placed.append("\n".join(P))
        for num, (px, py, side) in pos.items():
            sx, sy = cx + px, cy - py
            n = c["nets"].get(num, None)
            if n is None:
                ncs.append(f'(no_connect (at {sx:.2f} {sy:.2f}) (uuid {_q(uid(project, c["ref"], "nc", num))}))')
            else:
                ang, just = (180, "right") if side == "L" else (0, "left")
                labels.append(f'(global_label {_q(n)} (shape passive) (at {sx:.2f} {sy:.2f} {ang}) (fields_autoplaced yes) (effects (font (size 1.0 1.0)) (justify {just})) (uuid {_q(uid(project, c["ref"], "lbl", num))})'
                              f' (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {sx:.2f} {sy:.2f} 0) (effects (font (size 1.0 1.0)) (hide yes))))')
    hdr = [f'(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0")', f'  (uuid {_q(root)})', f'  (paper {_q(paper)})',
           f'  (title_block (title {_q(title)}) (rev {_q(rev)}) (comment 1 {_q(comment)}))', '  (lib_symbols']
    body = hdr + ["\n".join("    " + l for l in libs[k][0].replace('(symbol "knob:', '(symbol "knob:').split("\n")) for k in libs] + ["  )"]
    body += placed + labels + ncs + ['(sheet_instances (path "/" (page "1")))', "(embedded_fonts no)", ")"]
    open(path, "w").write("\n".join(body) + "\n")
    # project symbol library (same symbols, no lib prefix)
    lib = ['(kicad_symbol_lib (version 20241209) (generator "sch_gen.py") (generator_version "9.0")']
    for k in libs: lib.append(libs[k][0].replace(f'(symbol "knob:{k}"', f'(symbol "{k}"', 1))
    lib.append(")")
    d = os.path.dirname(path)
    open(os.path.join(d, "knob.kicad_sym"), "w").write("\n".join(lib) + "\n")
    open(os.path.join(d, "sym-lib-table"), "w").write('(sym_lib_table\n  (version 7)\n  (lib (name "knob")(type "KiCad")(uri "${KIPRJMOD}/knob.kicad_sym")(options "")(descr "generated by sch_gen.py"))\n)\n')
    return root

def fp_path(project, ref): return "/" + uid(project, ref)
