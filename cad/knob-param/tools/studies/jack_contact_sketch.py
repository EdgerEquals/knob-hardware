# Step 2 boards, jack board Q17 (5 Nov): on the jack board, the sleeve-pin slots of the two middle jacks (x ±5.5, pads with their
# 0.35 ring, Q14/Q15) land on the two outer upper spring-contact pads (x ±4.6, y -51.4, Ø1.2 [S-dist]).
#   jack-contact-sketch.png  1: as modelled (v0.41): they overlap; 2: proposal A: middle jacks out to ±5.8, the D+/D- contacts in to
#   ±4.0 (the USB-C board is re-routed; 0.325 to the socket's leg pads there); 3: proposal B: the whole jack row 1.25 up.
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/jack_contact_sketch.py <out dir>
import os, sys
sys.path.insert(0, ".")
OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
    from knobparam.common import model
    D = model.derive(model.default_params())
    ring, pr = D["jack_slot_ring"], D["usb_pwr_pad"] / 2
    tw, ty = D["usb_pwr_tab"]; ax_y0 = D["jack_y"]
    k = dict(fontsize=7.5, arrowprops=dict(arrowstyle="-", lw=0.6))
    fig, axs = plt.subplots(1, 3, figsize=(15, 5.2), dpi=125)
    cases = (("1. As modelled (v0.41): sleeve slots of jacks 2 and 3 on the D+/D- contacts", 5.5, 4.6, 0.0),
             ("2. A: middle jacks out to ±5.8, D+/D- contacts in to ±4.0", 5.8, 4.0, 0.0),
             ("3. B: jack row 1.25 up, contacts as they are", 5.5, 4.6, 1.25))

    def gap(J, C, up):
        n, s0, s1, w = [p for p in D["jack_pins"] if p[0] == "S"][0]
        sy0, sy1 = ax_y0 + up + s0 - w / 2 - ring, ax_y0 + up + s1 + w / 2 + ring
        sx0 = J - w / 2 - ring
        cx, cy = C, -51.4
        dx = max(sx0 - cx, 0); dy = max(sy0 - cy, cy - sy1, 0)
        return (dx * dx + dy * dy) ** 0.5 - pr if (dx or dy) else -(min(cx + pr - sx0, 1e9))
    for ax, (title, J, C, up) in zip(axs, cases):
        ay = ax_y0 + up
        ax.add_patch(Rectangle((-tw, ty), 2 * tw, D["jack_bot_y"] + up - ty, fc="#a5d6a7", ec="#1b5e20", alpha=0.5, lw=1.0))
        for sx in (-1, 1):
            x = sx * J
            ax.add_patch(Rectangle((x - D["jb_tongue_hw"], D["jb_tongue_y"] + up), 2 * D["jb_tongue_hw"], D["jack_bot_y"] - D["jb_tongue_y"],
                                   fc="#a5d6a7", ec="#1b5e20", alpha=0.5, lw=1.0))
            ax.add_patch(Rectangle((x - 5, D["jack_bot_y"] + up), 10, 3.0, fc="#424242", alpha=0.25))
            for n, y0, y1, w in D["jack_pins"]:
                L = (y1 - y0) + w
                ax.add_patch(FancyBboxPatch((x - w / 2 - ring, ay + min(y0, y1) - w / 2 - ring), w + 2 * ring, L + 2 * ring,
                                            boxstyle=f"round,pad=0,rounding_size={w / 2 + ring}", fc="#ffb300", ec="#e65100", lw=0.6, zorder=4))
        for (x, y) in D["usb_pwr_contacts"]:
            xx = (C if x > 0 else -C) if abs(abs(x) - 4.6) < 1e-6 else x
            ax.add_patch(Circle((xx, y), pr, fc="#ffd54f", ec="#bf360c", lw=0.8, zorder=5, alpha=0.9))
        g = gap(J, C, up)
        ax.annotate(("overlap " + f"{-g:.2f}" if g < 0 else f"gap {g:.2f}") + " between the D- contact pad\nand jack 3's sleeve-slot pad", (C + 0.45, -51.2), (1.6, -55.9), **k)
        ax.set_xlim(-9.5, 9.5); ax.set_ylim(-56.6, -43.4); ax.set_aspect("equal"); ax.grid(alpha=0.2)
        ax.set_title(title, fontsize=8.5, loc="left"); ax.set_xlabel("x (mm)")
    axs[0].set_ylabel("y (mm, up the panel)")
    axs[0].annotate("jack board tab and tongues (green),\n8 contact pads (yellow), slot pads (orange)", (-3.0, -53.6), (-9.2, -44.6), **k)
    axs[1].annotate("jacks 10.7 / 11.6 / 10.7 apart\n(was 11.0 each)", (5.8, -46.2), (-9.2, -44.4), **k)
    axs[2].annotate("about 1.25 more of the clear OLED's\nlit area covered (about 82% seen, was 90%)", (5.5, -45.2), (-9.2, -44.2), **k)
    fig.tight_layout()
    out = os.path.join(OUT, "jack-contact-sketch.png"); fig.savefig(out); print("wrote", out)
    for title, J, C, up in cases:
        print(title, "gap", round(gap(J, C, up), 3))


if __name__ == "__main__":
    main()
