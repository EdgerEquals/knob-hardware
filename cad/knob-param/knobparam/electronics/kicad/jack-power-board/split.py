# Two-board splits of the jack power board netlist (6 Nov 2026): every split of the blocks between the upper and lower board, scored by
# the fuller board (footprint area / free area) with at most 22 lines (not counting ground) on the second stacks. Run here: python3 split.py
import sys, itertools
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design, area
parts = design.build()
cy = {p["ref"]: area.courtyard(p["fp"]) for p in parts}
A_free = 318 + (465 - 27 - 116)      # top (sockets) + bottom (stack-2 males)
B_free = (424.7 - 116) + (424.7 - 149)  # top (stack-2 sockets) + bottom (ZIFs)
# group parts: each passive goes with the chip/block it serves -> use the 'block' label; refine supply sub-blocks by nets
def group(p):
    b = p["block"]
    n = set(v for v in p["pins"].values() if v)
    if b == "supply":
        if n & {"SW_3","BST_3","SS_3","FB_3"} or p["value"].startswith("TPS62933"): return "buck"
        if n & {"P_FB","P_NR"} or p["value"].startswith("TPS7A49") : return "ldo+"
        if n & {"N_FB","N_NR","VNEG_RAW"} or p["value"].startswith("TPS7A30"): return "ldo-"
        if n & {"P12_EN","N12_EN"}: return "en"
        if n & {"EFUSE_FLT"}: return "power in"
        return "boost"
    if b.startswith("jack") and b != "jack circuits":
        if p["value"].startswith("TMUX") or "25V" in p["value"] and p["ref"].startswith("C") or n & {"MR1","MR2","MR3","MT1","MT2","MT3","MY1","MY2","MY3"} or n & {"RS1","RS2","RS3"}:
            return "switching"
        if n & {"CI1_N","CI2_N","CI3_N"}: return "cv in"
        return "cv out"
    if b == "jack circuits":
        if p["value"].startswith("OPA") or "25V" in p["value"]: return "cv out"
        return "cv in"
    if b == "digital":
        if p["value"].startswith("SN74") : return "switching"
        if n & {"MIDI_TX"}: return "switching"
        return "expander"
    return b
G = {}
for p in parts:
    if p["ref"] in ("H1","H2","J5","J6","MP1","MP2"): continue
    G.setdefault(group(p), []).append(p)
print({g: (len(v), round(sum(cy[q["ref"]][0]*cy[q["ref"]][1] for q in v))) for g, v in G.items()})
fixedA = {"H1","H2","MP1","MP2"}   # sockets to the jack board, posts
def evaluate(Bgroups, link_on="B"):
    onB = set()
    for g in Bgroups: onB |= {p["ref"] for p in G[g]}
    onB |= {"J5"} | ({"J6"} if link_on == "B" else set())
    netsA, netsB = set(), set()
    import json
    hdr = {"H1": ["GND","VBUS","CC1","J1_RING","J2_RING","J1_TIP","J2_TIP"], "H2": ["VBUS","DN","DP","CC2","J3_RING","J4_RING","J3_TIP","J4_TIP","GND"]}
    for h, ns in hdr.items(): netsA |= set(ns)
    netsA |= {"GND","VSYS"}
    aA = aB = 0
    for p in parts:
        if p["ref"] in ("H1","H2"): continue
        ns = set(v for v in p["pins"].values() if v)
        if p["ref"] in onB: netsB |= ns; 
        else: netsA |= ns
        if p["ref"] in ("J5","J6","MP1","MP2"): continue
        a = cy[p["ref"]][0]*cy[p["ref"]][1]
        if p["ref"] in onB: aB += a
        else: aA += a
    if link_on == "A": aA += 49.5; 
    cross = sorted((netsA & netsB) - {"GND"})
    return aA, aB, cross
groups = sorted(G)
best = []
for r in range(1, len(groups)):
    for Bg in itertools.combinations(groups, r):
        for link in ("A","B"):
            aA, aB, cross = evaluate(Bg, link)
            fa = aA / (A_free + (49.5 if link=="B" else 0)); fb = aB / (B_free + (0 if link=="B" else 49.5))
            best.append((max(fa, fb), len(cross), Bg, link, round(fa*100), round(fb*100), cross))
ok = [b for b in best if b[1] <= 22]
ok.sort(key=lambda b: (b[0], b[1]))
for b in ok[:12]:
    print(f"max {b[0]*100:.0f}%  cross {b[1]}  A {b[4]}% B {b[5]}%  link on {b[3]}  B gets {b[2]}\n    {b[6]}")
