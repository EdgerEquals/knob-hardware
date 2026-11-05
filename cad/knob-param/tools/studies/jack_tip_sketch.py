# Step 2 boards, jack board Q18 (5 Nov): the tip-pin slots (T +4.92..+5.21 from the jack axis, 1.43 wide [S-lib], 0.35 ring) reach
# axis +6.28, past the jack board's top edge (the jack tops, axis +6.0). With PCBWay's 0.25 copper-to-edge the board must reach
# axis +6.53 round each tip slot.
#   jack-tip-sketch.png  1: as modelled (v0.42); 2: proposal A: a small bump (2.7 x 0.55) on the top edge round each tip slot;
#   3: proposal B: the whole top edge 0.55 up.
# Run from cad/knob-param:  PYTHONPATH=. python tools/studies/jack_tip_sketch.py <out dir>
import os, sys
sys.path.insert(0, ".")
OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, FancyBboxPatch
    from knobparam.common import model
    D = model.derive(model.default_params())
    ring = D["jack_slot_ring"]; top = D["jack_top_y"]; bot = D["jack_bot_y"]
    n, t0, t1, tw = [p for p in D["jack_pins"] if p[0] == "T"][0]
    need = D["jack_y"] + t1 + tw / 2 + ring + 0.25          # board edge needed over each tip slot
    bump_h = round(need - top + 0.02, 2); bump_w = round(tw + 2 * ring + 2 * 0.25 + 0.07, 1)
    lit_y0 = -39.90
    k = dict(fontsize=7.5, arrowprops=dict(arrowstyle="-", lw=0.6))
    fig, axs = plt.subplots(3, 1, figsize=(12, 5.6), dpi=140)
    cases = (("1. As modelled (v0.42): the tip slots' pads run past the board's top edge", None),
             (f"2. A: a bump {bump_w} wide, {bump_h} tall on the top edge round each tip slot", "bump"),
             (f"3. B: the whole top edge {bump_h} up", "strip"))
    for ax, (title, mode) in zip(axs, cases):
        x0, x1 = D["jb_x"]
        ax.add_patch(Rectangle((x0, -45), x1 - x0, top + 45, fc="#a5d6a7", ec="#1b5e20", alpha=0.45, lw=1.0))
        if mode == "strip":
            ax.add_patch(Rectangle((x0, top), x1 - x0, bump_h, fc="#ef9a9a", ec="#c62828", alpha=0.6, lw=1.0))
        for jx, jy in D["jack_xy"]:
            ax.add_patch(Rectangle((jx - 5, -45), 10, top + 45, fc="#424242", alpha=0.18))
            if mode == "bump":
                ax.add_patch(Rectangle((jx - bump_w / 2, top), bump_w, bump_h, fc="#ef9a9a", ec="#c62828", alpha=0.6, lw=1.0))
            L = (t1 - t0) + tw
            ax.add_patch(FancyBboxPatch((jx - tw / 2 - ring, jy + t0 - tw / 2 - ring), tw + 2 * ring, L + 2 * ring,
                                        boxstyle=f"round,pad=0,rounding_size={tw / 2 + ring}", fc="#ffb300", ec="#e65100", lw=0.6, zorder=4))
        ax.axhline(lit_y0, color="#1565c0", lw=0.9, ls="--")
        ax.add_patch(Rectangle((-17.525, lit_y0), 35.05, 6, fc="#90caf9", alpha=0.25))
        ax.set_xlim(-23, 23); ax.set_ylim(-41.2, -36.6); ax.set_aspect("equal"); ax.grid(alpha=0.2)
        ax.set_title(title, fontsize=8.5, loc="left"); ax.set_ylabel("y (mm)")
    jx = D["jack_xy"][3][0]
    axs[0].annotate(f"tip slot pad to y {D['jack_y'] + t1 + tw / 2 + ring:.2f}; board edge y {top:.2f} (needs {need:.2f} for 0.25)",
                    (jx, top + 0.25), (-22.5, -36.95), **k)
    axs[0].annotate("clear OLED's lit area (blue) from y -39.90 [A]; jack bodies (grey) to y -38.40", (-10, -39.0), (-22.5, -40.95), **k)
    axs[1].annotate(f"4 small FR-4 bumps above the jack tops, seen through the clear OLED (black mask would hide them best)", (jx, top + bump_h),
                    (-22.5, -36.95), **k)
    cov = top + bump_h - lit_y0
    axs[2].annotate(f"a {bump_h} strip the full 43 wide: {cov:.2f} of the lit 15.32 covered (about {100 * (1 - cov / 15.32):.0f}% seen, was 90%)",
                    (0, top + bump_h), (-22.5, -36.95), **k)
    axs[2].set_xlabel("x (mm)")
    fig.tight_layout()
    out = os.path.join(OUT, "jack-tip-sketch.png"); fig.savefig(out); print("wrote", out, "bump", bump_w, bump_h, "need", round(need, 3))


if __name__ == "__main__":
    main()
