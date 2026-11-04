# Step 2, decision 4 (4 Nov evening): plugging the two flexes into the jack power board's ZIFs. Schematic from the v0.33 params.
#   jack-flex-sketch.png  1: the plan as written [Ed 11:25] ("plugged as the main board goes in"): the main board ~15 mm back, as far as the
#                         clear OLED's 36 mm flex reaches; the board fills the back opening (0.6 a side), so the ZIFs cannot be reached;
#                         2: option A: the jack unit rides in with the board stack on two printed legs from the main board's bottom strip
#                         (flexes plugged on the bench).
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/jack_flex_sketch.py <out dir>
import os, sys
sys.path.insert(0, ".")
OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    from PIL import Image
    from knobparam.common import model
    D = model.derive(model.default_params())
    y0, y1 = D["jack_bot_y"], D["jack_top_y"]
    k = dict(fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    cy, ch, ct = D["clear_oled_xy"][1], D["clear_oled"][1], D["clear_oled"][2]
    oy0 = cy - ch / 2
    outs = []

    def R(ax, a, b, c, d, fc="none", ec="none", al=1.0, ls="-", lw=1.0):
        ax.add_patch(Rectangle((a, c), b - a, d - c, fc=fc, ec=ec, alpha=al, ls=ls, lw=lw))

    def shell(ax):
        R(ax, -56.4, -53.9, -1.6, D["z_fp0"], "#b0bec5")
        R(ax, -66.4, -25.0, D["z_fp0"], D["z_fp1"], "#b0bec5")
        R(ax, D["pcb_y0"], D["pcb_y0"] + D["ledge_w"], 0.05, D["z_ledge1"], "#b0bec5")   # bottom ledge
        R(ax, y0, y1, D["jack_depth_z0"], D["z_fp0"] - 0.02, "#1565c0", al=0.5)
        R(ax, y0, y1, D["jb_z0"], D["jb_z1"], "#2e7d32", "#1b5e20")
        R(ax, y0, y1, D["jb2_z0"], D["jb2_z1"], "#66bb6a", "#1b5e20")
        R(ax, y0 + 0.2, y0 + 5.7, D["zif_z0"], D["jb2_z0"], "#d32f2f")

    # ---- 1: as written ----
    fig = plt.figure(figsize=(7.0, 7.6), dpi=125); ax = fig.add_axes([0.12, 0.09, 0.85, 0.84])
    shell(ax)
    back = 15.0
    R(ax, D["pcb_y0"], -25.0, -1.6 - back, -back, "#2e7d32")
    R(ax, oy0, -25.0, -back, ct - back, "#90caf9")
    ax.plot([oy0, oy0 - 0.6, oy0 - 0.6, y0 + 1.5, y0 + 1.5], [ct / 2 - back, ct / 2 - back, D["zif_z0"] - 1.2, D["zif_z0"] - 1.2, D["zif_z0"]],
            color="#e65100", lw=1.6)
    ax.annotate(f"main board {back:g} back: about as far as the clear\nOLED's 36 mm flex reaches up to its ZIF", (-40.0, -1.6 - back),
                (-50.0, -26.0), **k)
    ax.annotate("the board fills the back opening (0.6 a side):\nno way in for a hand or a tool", (D["pcb_y0"], -back - 0.8), (-65.0, -21.0), **k)
    ax.annotate("ZIFs on the jack power board", (y0 + 3.0, D["zif_z0"]), (-46.0, 8.0), **k)
    ax.set_xlim(-66, -25); ax.set_ylim(-30, 42); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("y (mm, up the panel)"); ax.set_ylabel("z (mm)")
    ax.set_title("1. As written (11:25): plugged as the main board goes in", fontsize=10, loc="left")
    f = os.path.join(OUT, "_jf_1.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    # ---- 2: option A ----
    fig = plt.figure(figsize=(7.0, 7.6), dpi=125); ax = fig.add_axes([0.12, 0.09, 0.85, 0.84])
    shell(ax)
    R(ax, D["pcb_y0"], -25.0, -1.6, 0.0, "#2e7d32")
    R(ax, oy0, -25.0, 0.0, ct, "#90caf9")
    R(ax, y0, y1, 0.02, D["jb2_z0"] - 0.02, "#ffb74d", "#e65100", al=0.35, ls="--", lw=1.4)     # legs (at the ends, behind this cut)
    ax.annotate("two printed legs [A] at the ends (x ±21.2..22.1, between the\nOLED's sides and the board edge, in the ledge notches):\n"
                "main board up to the jack power board; the jack\nunit rides in with the board stack", (y0 + 2.0, 9.0), (-65.0, -12.0), **k)
    ax.annotate("both flexes plugged on the bench\n(unplug for service once the stack is out)", (y0 + 3.0, D["zif_z0"]), (-46.0, 3.0), **k)
    ax.set_xlim(-66, -25); ax.set_ylim(-30, 42); ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlabel("y (mm, up the panel)"); ax.set_ylabel("z (mm)")
    ax.set_title("2. Option A: the jack unit rides in with the stack", fontsize=10, loc="left")
    f = os.path.join(OUT, "_jf_2.png"); fig.savefig(f); plt.close(fig); outs.append(f)

    ims = [Image.open(f) for f in outs]
    H = max(i.height for i in ims); ims = [i.resize((int(i.width * H / i.height), H)) for i in ims]
    cv = Image.new("RGB", (sum(i.width for i in ims), H), "white"); x = 0
    for i in ims:
        cv.paste(i, (x, 0)); x += i.width
    out = os.path.join(OUT, "jack-flex-sketch.png"); cv.save(out)
    for f in outs:
        os.remove(f)
    print("wrote", out)


if __name__ == "__main__":
    main()
