# Step 2, decision 5 (4 Nov evening): the USB-C board's two power wires (15 V, GND) to the jack unit. The board goes into the shell first
# (its top 2.4 is inside the box, where the main board sits); the jack unit now comes in with the board stack (v0.34, Ed 22:21).
# Option A sketched over v0.34: a tab on the jack board's bottom edge (x ±5.5, down to y -53.6) carries 4 short spring contacts on its
# front face; they land on gold pads on the USB-C board's back face as the stack goes home (the key's ledge tab goes).
#   usb-contacts-sketch.png  1: front view of the bottom centre; 2: cut at x 3.0.
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/usb_contacts_sketch.py <out dir>
import os, sys
sys.path.insert(0, ".")
OUT = sys.argv[1] if len(sys.argv) > 1 else "."

TAB = (5.5, -53.6)                             # [A] half width, bottom edge (0.35 above the key, in the channel)
CONTACTS = [(-3.0, -52.6), (3.0, -52.6), (-3.0, -51.4), (3.0, -51.4)]   # [A] 15 V x2, GND x2, Ø1.0 barrels


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Rectangle, Circle
    from PIL import Image, ImageDraw
    from knobparam.common import model
    from knobparam.assembly.build import build_all
    from knobparam.assembly.plan_sheet import _cut_faces
    D = model.derive(model.default_params())
    parts, *_ = build_all(D)
    case, pcb = parts["case"], parts["PCB"]
    key = parts["USB-C key (printed, held by the back cover)"]
    brd, rc = parts["USB-C PD board"], parts["USB-C receptacle [S]"]
    jb = parts["jack board (FR-4, the four jacks soldered on) [A]"]
    pb = parts["jack power board (FR-4: ZIFs, ±12 V, the OLED's 12.5 V) [A]"]
    oled = parts['clear OLED 1.51" SSD1309 (PCB front, over window D)']
    k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    y0 = D["jack_bot_y"]; zj0, zj1 = D["jb_z0"], D["jb_z1"]; zu0 = D["usb_z0"]
    outs = []

    def poly(ax, s, axis, at, fc, al=1.0):
        t = _cut_faces(s, axis, at)
        if t:
            ax.add_collection(PolyCollection(t, facecolors=fc, edgecolors=fc, alpha=al, linewidths=0.2))

    def R(ax, a, b, c, d, fc="none", ec="none", al=1.0, ls="-", lw=1.0):
        ax.add_patch(Rectangle((a, c), b - a, d - c, fc=fc, ec=ec, alpha=al, ls=ls, lw=lw))

    # ---- 1: front view ----
    fig = plt.figure(figsize=(7.6, 6.0), dpi=125); ax = fig.add_axes([0.11, 0.11, 0.86, 0.8])
    poly(ax, case, "z", 28.0, "#b0bec5"); poly(ax, key, "z", 28.0, "#ffb74d")
    poly(ax, jb, "z", (zj0 + zj1) / 2, "#2e7d32", 0.6)
    R(ax, -TAB[0], TAB[0], TAB[1], y0, "#2e7d32", "#1b5e20", al=0.9)
    R(ax, -D["usb_board"][0] / 2, D["usb_board"][0] / 2, D["usb_board_y0"], D["usb_board_y1"], "none", "#6a1b9a", lw=1.6)
    for x, y in CONTACTS:
        ax.add_patch(Circle((x, y), 0.5, fc="#ffb300", ec="#e65100", lw=0.6))
    ax.annotate("jack board tab (dark green), x ±5.5 down to y -53.6:\nin the USB-C channel, 0.35 above the key", (TAB[0], TAB[1] + 0.5), (-14.5, -60.5), **k)
    ax.annotate("USB-C board (purple outline) in its channel, in the\nshell first; gold pads on its back face", (D["usb_board"][0] / 2, -55.5),
                (-1.0, -63.0), **k)
    ax.annotate("4 spring contacts [A]: 15 V x2, GND x2", CONTACTS[1], (4.0, -45.5), **k)
    ax.set_xlim(-15, 15); ax.set_ylim(-64, -44); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm, up the panel)")
    ax.set_title("1. Front view at z 28 (between the jack board and the USB-C board)", fontsize=10, loc="left")
    f = os.path.join(OUT, "_uc_1.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    # ---- 2: cut at x 3 ----
    xc = 3.0
    fig = plt.figure(figsize=(7.0, 7.6), dpi=125); ax = fig.add_axes([0.12, 0.09, 0.85, 0.84])
    poly(ax, case, "x", xc, "#b0bec5"); poly(ax, key, "x", xc, "#ffb74d"); poly(ax, pcb, "x", xc, "#2e7d32"); poly(ax, oled, "x", xc, "#90caf9")
    poly(ax, brd, "x", xc, "#6a1b9a"); poly(ax, rc, "x", xc, "#9575cd"); poly(ax, jb, "x", xc, "#2e7d32"); poly(ax, pb, "x", xc, "#66bb6a")
    R(ax, TAB[1], y0, zj0, zj1, "#2e7d32", "#1b5e20")
    for _x, y in CONTACTS[1::2]:
        R(ax, y - 0.5, y + 0.5, zj1, zu0 - 0.02, "#ffb300", "#e65100", lw=0.6)
    R(ax, D["pcb_y0"], -51.8, 0.05, D["z_ledge1"], "white")
    ax.annotate(f"spring contacts {zu0 - zj1:.2f} long [A] from the jack board's\ntab up to pads on the USB-C board's back:\n"
                "they meet in the last ~1 of the stack's travel", (-51.4, 28.0), (-59.5, 13.0), **k)
    ax.annotate("the key's ledge tab goes (the tab passes there\nas the stack goes in)", (-52.5, 1.3), (-59.5, -6.5), **k)
    ax.annotate("USB-C board pushed onto its ledge\n(the contacts' force goes into the wall)", (-55.0, 31.0), (-59.5, 43.0), **k)
    ax.set_xlim(-60, -40); ax.set_ylim(-9, 46); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("y (mm, up the panel)"); ax.set_ylabel("z (mm)")
    ax.set_title(f"2. Cut at x {xc:g}", fontsize=10, loc="left")
    f = os.path.join(OUT, "_uc_2.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    ims = [Image.open(f) for f in outs]
    H = max(i.height for i in ims); ims = [i.resize((int(i.width * H / i.height), H)) for i in ims]
    cv = Image.new("RGB", (sum(i.width for i in ims), H + 50), "white"); x = 0
    for i in ims:
        cv.paste(i, (x, 50)); x += i.width
    ImageDraw.Draw(cv).text((20, 15), "Step 2, decision 5, option A (sketch over v0.34): the USB-C board's 15 V and GND reach the jack unit through 4 spring "
                            "contacts that mate as the board stack goes home; no wires to solder inside.", fill="black")
    out = os.path.join(OUT, "usb-contacts-sketch.png"); cv.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out)


if __name__ == "__main__":
    main()
