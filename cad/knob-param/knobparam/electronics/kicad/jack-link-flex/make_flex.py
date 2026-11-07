"""Link flex (knob step 2, 7 Nov 2026): the single-sided polyimide flex from the main board's strip to the FH26W on the jack lower
board's underside, on the J path [Ed 7 Nov 18:15, Q29 = A]. Run with the system python that has pcbnew (KiCad 7):
    /usr/bin/python3 make_flex.py            -> kicad/jack-link-flex.kicad_pcb (+ .kicad_pro, fp library), DRC, fab/ (gerbers, README)
Also writes the main board's matching pad footprint into ../footprints.pretty (placed in the main-board pass).

Drawn flat, seen from the copper side (KiCad's top = the copper side, F.Cu): X = panel x (+100), Y = 100 at the FH26W end, growing
towards the main-board end. Along the J the flex only bends about the panel x axis, so contact k sits at the same panel x at both ends
(x1 + 0.3 (k - 1), as J6 on the lower board), and the copper faces up into the bottom-contact FH26W and down onto the strip's pads.
Geometry from the model: link_flex_geom.json (export_geom.py). Pin order: the jack lower board's LINK list (design.py, Q11)."""
import json, os, re, subprocess, sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from kicad7_tools import FP, V, save_fp, write_project, drc, save_board   # noqa: E402

G = json.load(open(os.path.join(HERE, "link_flex_geom.json")))
src = open(os.path.join(os.path.dirname(HERE), "jack-power-board", "design.py")).read()
LINK = eval(re.search(r"LINK = (\[.*?\])", src, re.S).group(1))
assert len(LINK) == G["n"] == 25

NAME = "jack-link-flex"
KDIR = os.path.join(HERE, "kicad"); FAB = os.path.join(HERE, "fab"); LIB = os.path.join(KDIR, "jlf.pretty")
MAIN_LIB = os.path.join(os.path.dirname(HERE), "footprints.pretty")
O = 100.0
W, L, P, N, X1 = G["w"], G["flat_len"], G["pitch"], G["n"], G["x1"]
XC = X1 + (N - 1) * P / 2
TRACK = 0.15            # [A] conductor 0.15 / gap 0.15 at the 0.3 pitch (Hirose's drawing gives (0.15) as a reference) [C]
ZIF_EXP = (0.10, 2.50)  # [C] exposed contacts from the FH26W end: 0.1 back from the edge to 2.5 (the catalogue's 2.5 ± 0.3)
SOLDER_EXP = (0.10, 0.90)   # [A] exposed solder fingers from the main-board end; coverlay from 0.9, the bend starts at 1.1
MAIN_PAD = (0.15, 1.20)     # [A] main board pads: 0.15 wide, 1.2 long (0.3 past the flex's end for the hot-bar fillet / inspection)
RULES = dict(clearance=0.12, track=TRACK, min_track=0.1, via_d=0.45, via_drill=0.2, edge=0.1)   # edge: the contacts stop 0.1
                                                                                                # short of the ends; the sides keep 0.225


def xk(k):   # panel x of contact k (1-based)
    return X1 + P * (k - 1)


def footprints(board):
    """Three footprints: the FH26W end's contacts and the main-board end's fingers (on the flex), and the main board's pads."""
    zif = FP(board, "jlf", "LinkFlex_FH26W_End_25", "Link flex: 25 exposed contacts at 0.3 for the Hirose FH26W (bottom contact), copper side")
    for k in range(1, N + 1):
        p = zif.smd(str(k), xk(k) - XC, (ZIF_EXP[0] + ZIF_EXP[1]) / 2, TRACK, ZIF_EXP[1] - ZIF_EXP[0], paste=False)
    zif.rect(-W / 2, 0, W / 2, 4.0, pcbnew.F_Fab)
    sol = FP(board, "jlf", "LinkFlex_SolderEnd_25", "Link flex: 25 solder fingers at 0.3 (hot-bar onto the main board's strip), copper side")
    for k in range(1, N + 1):
        sol.smd(str(k), xk(k) - XC, -(SOLDER_EXP[0] + SOLDER_EXP[1]) / 2, TRACK, SOLDER_EXP[1] - SOLDER_EXP[0], paste=False)
    mb = FP(board, "footprints", "LinkFlex_MainBoard_Pads_25x0.3",
            "Main board pads for the link flex's solder end (Q29): 25 x 0.15 x 1.2 at 0.3, pad 1 at panel x 10.5; the flex's end lies "
            "0.3 short of the pads' top end. Hot-bar bonded (PCBWay, pre-quote) or hand-soldered [A]")
    for k in range(1, N + 1):
        mb.smd(str(k), xk(k) - XC, 0.0, MAIN_PAD[0], MAIN_PAD[1], paste=True)
    hl = MAIN_PAD[1] / 2
    mb.rect(-W / 2, -hl, W / 2, hl - 0.3, pcbnew.F_Fab)                          # the flex's end over the pads
    mb.rect(-W / 2 - 0.25, -hl - 0.25, W / 2 + 0.25, hl + 0.25, pcbnew.F_CrtYd)
    return zif.done(-0.6), sol.done(0.6), mb.done(hl + 0.6)


def main():
    os.makedirs(KDIR, exist_ok=True); os.makedirs(FAB, exist_ok=True)
    board = pcbnew.BOARD()
    zif, sol, mb = footprints(board)
    for f in (zif, sol):
        save_fp(LIB, f)
    # footprints.pretty holds files from newer KiCads that KiCad 7 can't load, so the main board's footprint is saved on its own and copied
    import shutil, tempfile
    tmp = tempfile.mkdtemp(); save_fp(os.path.join(tmp, "x.pretty"), mb); del mb
    pcbnew.FootprintLibCreate  # (keeps the import used)
    shutil.copy(os.path.join(tmp, "x.pretty", "LinkFlex_MainBoard_Pads_25x0.3.kicad_mod"), MAIN_LIB)
    write_project(KDIR, NAME, RULES, [("jlf", "${KIPRJMOD}/jlf.pretty")])
    open(os.path.join(KDIR, NAME + ".kicad_dru"), "w").write("(version 1)\n")

    board = pcbnew.BOARD()
    ds = board.GetDesignSettings(); ds.SetCopperLayerCount(2)
    board.SetLayerName(pcbnew.User_1, "User.Stiffener"); board.SetLayerName(pcbnew.User_2, "User.Notes")
    # the 7 ground lines are separate on a single layer (they meet on the two boards), so each gets its own net here: GND_p<pin>
    names = [f"GND_p{k}" if n == "GND" else n for k, n in enumerate(LINK, 1)]
    nets = {}
    for n in names:
        ni = pcbnew.NETINFO_ITEM(board, n); board.Add(ni); nets[n] = ni
    x0, x1 = O + XC - W / 2, O + XC + W / 2
    y0, y1 = O, O + L
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(*a)); s.SetEnd(V(*b))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(pcbnew.FromMM(0.05)); board.Add(s)
    for f, (x, y), ref in ((zif, (O + XC, y0), "J1"), (sol, (O + XC, y1), "J2")):
        f = f.Duplicate().Cast(); f.SetReference(ref); f.SetPosition(V(x, y)); board.Add(f)
        for p in f.Pads():
            p.SetNet(nets[names[int(p.GetNumber()) - 1]])
    # conductors: straight, contact k to finger k
    for k in range(1, N + 1):
        t = pcbnew.PCB_TRACK(board); t.SetStart(V(O + xk(k), y0 + sum(ZIF_EXP) / 2)); t.SetEnd(V(O + xk(k), y1 - sum(SOLDER_EXP) / 2))
        t.SetWidth(pcbnew.FromMM(TRACK)); t.SetLayer(pcbnew.F_Cu); t.SetNet(nets[names[k - 1]]); board.Add(t)
    # stiffener on the back of the FH26W end, the bends' positions and notes
    st = pcbnew.PCB_SHAPE(board); st.SetShape(pcbnew.SHAPE_T_RECT); st.SetStart(V(x0, y0)); st.SetEnd(V(x1, y0 + G["stiff"]))
    st.SetLayer(pcbnew.User_1); st.SetWidth(pcbnew.FromMM(0.1)); st.SetFilled(True); board.Add(st)
    s_top0 = (G["end_y"] - (G["riser_y"][1] + G["r_top"]))                       # flat from the end to the top bend
    s_top1 = s_top0 + 3.14159265 / 2 * (G["r_top"] + G["t"] / 2)
    s_bot1 = L - (G["pad_y"][1] - G["pad_y"][0])                                # from the end to where the bottom bend meets the fingers
    s_bot0 = s_bot1 - 3.14159265 / 2 * (G["r_bottom"] + G["t"] / 2)
    for s0, s1, lab in ((s_top0, s_top1, f"top bend r {G['r_top']:g}"), (s_bot0, s_bot1, f"bottom bend r {G['r_bottom']:.2f}")):
        for s in (s0, s1):
            ln = pcbnew.PCB_SHAPE(board); ln.SetShape(pcbnew.SHAPE_T_SEGMENT); ln.SetStart(V(x0 - 1.0, y0 + s)); ln.SetEnd(V(x1 + 1.0, y0 + s))
            ln.SetLayer(pcbnew.User_2); ln.SetWidth(pcbnew.FromMM(0.05)); board.Add(ln)
        tx = pcbnew.PCB_TEXT(board); tx.SetText(lab); tx.SetPosition(V(x1 + 1.3, y0 + (s0 + s1) / 2)); tx.SetLayer(pcbnew.User_2)
        tx.SetTextSize(V(0.5, 0.5)); tx.SetTextThickness(pcbnew.FromMM(0.07)); tx.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT); board.Add(tx)
    notes = (f"Link flex v0.1 (knob {G['version']}): single-sided PI, 25 x 0.15 at 0.3, {W:g} x {L:.2f} flat. Copper side shown.\n"
             f"Top end -> Hirose FH26W-25S-0.3SHW(60), contacts up; 0.20 +/-0.03 total over {G['stiff']:g} with a PI stiffener on the back.\n"
             f"Bottom end -> main board strip, fingers down, hot-bar (or hand) soldered. Bends: r {G['r_top']:g} and r {G['r_bottom']:.2f}, once.")
    tx = pcbnew.PCB_TEXT(board); tx.SetText(notes); tx.SetPosition(V(x0, y1 + 1.5)); tx.SetLayer(pcbnew.User_2)
    tx.SetTextSize(V(0.4, 0.4)); tx.SetTextThickness(pcbnew.FromMM(0.06)); tx.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    tx.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_TOP); board.Add(tx)
    pcb = os.path.join(KDIR, NAME + ".kicad_pcb")
    save_board(pcb, board)
    check_against_lower_board()
    nv, nu, _ = drc(pcb, os.path.join(KDIR, "drc.rpt"))
    print(f"{NAME}: {W:g} x {L:.2f}, DRC {nv} violations, {nu} unconnected")
    fab(pcb, nv, nu)


def check_against_lower_board():
    """Contact k on the flex sits at the same panel x as pin k of J6 on the jack lower board, with the same net."""
    lb = pcbnew.LoadBoard(os.path.join(os.path.dirname(HERE), "jack-power-board", "lower", "kicad", "jack-lower-board.kicad_pcb"))
    j6 = lb.FindFootprintByReference("J6")
    worst = 0.0
    for p in j6.Pads():
        if not p.GetNumber().isdigit():
            continue
        k = int(p.GetNumber()); x = pcbnew.ToMM(p.GetPosition().x) - O
        worst = max(worst, abs(x - xk(k)))
        assert p.GetNetname() == LINK[k - 1], (k, p.GetNetname(), LINK[k - 1])
    assert worst < 0.001, worst
    print(f"J6 on the lower board: 25 pins match the flex's contacts by x (worst {worst:.4f}) and by net")


def fab(pcb, nv, nu):
    for f in os.listdir(FAB):
        os.remove(os.path.join(FAB, f))
    r = subprocess.run(["kicad-cli", "pcb", "export", "gerbers", "-o", FAB + "/", "--layers",
                        "F.Cu,F.Mask,Edge.Cuts,User.1,User.2", "--no-protel-ext", pcb], capture_output=True, text=True)
    if r.returncode:
        print(r.stderr)
    import zipfile
    zp = os.path.join(FAB, NAME + "-gerbers.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(FAB)):
            if f != os.path.basename(zp):
                z.write(os.path.join(FAB, f), f)
    ready = nv == 0 and nu == 0
    open(os.path.join(FAB, "README.txt"), "w").write(
        f"{NAME} v0.1 for PCBWay's flex line ({'DRC clean' if ready else 'NOT READY: DRC ' + str(nv) + ' / unconnected ' + str(nu)}).\n"
        "STATUS: NOT READY to order until the [C] items below are checked against Hirose's FH26 catalogue drawing.\n\n"
        f"Outline {W:g} x {L:.2f} mm (Edge.Cuts). Single-sided flex: polyimide 25 um base, 1/2 oz (18 um) rolled-annealed copper, polyimide\n"
        "coverlay 25 um + adhesive on the copper side with openings at both ends (F.Mask); ENIG on the openings [A]. No holes, no vias.\n"
        f"Stiffener (User.1 'Stiffener'): polyimide on the BACK (non-copper side) of the FH26W end, {G['stiff']:g} mm from the end, thick enough\n"
        "for 0.20 +/- 0.03 mm total over the contacts [S Hirose: FPC 0.2 +/- 0.03, stiffener 3.5 min].\n"
        "Conductors 0.15 / gaps 0.15 at 0.3 pitch, 25 positions; contact span 7.2 (C), even contacts 6.6 (B), width 7.8 (F) [S Hirose table].\n"
        "Bottom end: 25 solder fingers, exposed 0.10-0.90 from the end, bonded face down onto the main board's pads (footprint\n"
        "LinkFlex_MainBoard_Pads_25x0.3): hot-bar at PCBWay if they offer it (pre-quote question), else by hand.\n"
        f"Installed bent twice (once): r {G['r_top']:g} and r {G['r_bottom']:.2f} inner radius (bend lines on User.2).\n\n"
        "[C] to check before ordering: Hirose's recommended-FPC drawing (FH26 catalogue p. 8) - conductor width at the contacts,\n"
        "exposed length (2.5 here), contact start from the end (0.1 here), corner radius (R0.2 max, square here), and whether the FPC\n"
        "needs side ears or notches for the flip lock (none drawn). The catalogue's numbers came through without their labels.\n")
    print("fab ->", FAB)


if __name__ == "__main__":
    main()
