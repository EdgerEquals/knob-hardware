# Sketch for Danny (4 Nov, dial item 5): the screen's B2B plug held 0.10 short of full mate (now) vs fully mated (the option).
# Side view, drawn from numbers (not cut from the model; the model's plug and receptacle are plain blocks). Heights from the board top.
# Run from cad/knob-param:  .venv/bin/python tools/studies/cart_plug_sketch.py OUT.png
import sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

MATED = 0.80      # [S] mated height, board top to the plug's back
SHORT = 0.10      # [A] stand-off (now)
fig, axs = plt.subplots(1, 2, figsize=(14, 4.9), dpi=120)
for ax, gap, title in ((axs[0], SHORT, f"Now (v0.28): ribs on their slot floors, plug {SHORT:.2f} short of full mate"),
                       (axs[1], 0.0, "Option: plug fully mated, pad glued with the ribs seated (no shim)")):
    ax.add_patch(Rectangle((0, -0.8), 8.0, 0.8, fc="#1f6e3a"))                       # dial board
    ax.text(0.2, -0.45, "dial board", color="white", fontsize=9, va="center")
    ax.add_patch(Rectangle((1.0, 0), 3.6, 0.55, fc="#202326"))                       # receptacle
    ax.text(2.8, 0.27, "receptacle", color="white", fontsize=8.5, ha="center", va="center")
    zb = MATED + gap                                                                  # plug back
    ax.add_patch(Rectangle((1.2, zb - 0.55), 3.2, 0.55, fc="#55595d", alpha=0.9))   # plug body, nesting into the receptacle
    ax.text(2.8, zb - 0.2, "screen's plug", color="white", fontsize=8.5, ha="center", va="center")
    ax.add_patch(Rectangle((1.0, zb), 3.6, 0.6, fc="#c88a1a"))                       # pad (printed), glued to the arm
    ax.text(2.8, zb + 0.85, "printed pad (glued to the bezel's arm)", fontsize=8.5, ha="center", va="center")
    if gap:
        ax.plot([0.6, 4.9], [MATED, MATED], ls="--", lw=0.9, color="#c62828")
        ax.text(0.55, MATED, "full mate", fontsize=8, color="#c62828", ha="right", va="center")
    ax.annotate("", (5.0, 0), (5.0, zb), arrowprops=dict(arrowstyle="<->", lw=0.9))
    ax.text(5.15, zb / 2, f"{zb:.2f}" + (f"\n(0.80 mated + {gap:.2f})" if gap else "\n(0.80 mated)"), fontsize=9, va="center")
    # rib on its slot floor, at the right (a different place round the dial, same heights)
    ax.add_patch(Rectangle((8.0, -0.8), 2.0, 0.8, fc="#7a8085"))              # dial wall under the slot floor
    ax.add_patch(Rectangle((8.4, 0.0), 1.2, 1.9, fc="#3a3f44"))                       # rib
    ax.text(9.0, 0.95, "rib", color="white", fontsize=9, ha="center", va="center", rotation=90)
    ax.text(9.0, -0.4, "slot floor", fontsize=8.5, ha="center", va="center")
    ax.text(7.6, 2.25, "ribs carry the cartridge" if gap else "ribs and plug both seated:\nthe plug shares any press on the glass",
            fontsize=9, ha="left")
    if gap:
        ax.text(1.0, -1.55, "Contacts still overlap, but less than at full mate; how much contact is left\n"
                            "at 0.10 short is the connector's wipe: not in the datasheets [C]. The lock may not click.",
                fontsize=9)
    else:
        ax.text(1.0, -1.55, "The connector is used as designed (lock clicks, full contact). Phones hold B2B plugs\n"
                            "down this way; but the plug becomes a second seat beside the ribs.", fontsize=9)
    ax.set_xlim(-0.6, 11.4); ax.set_ylim(-2.1, 2.7); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title, fontsize=10, loc="left")
fig.text(0.01, 0.97, "Dial item 5: the screen's 24-pin 0.4 mm board-to-board plug in the dial board's receptacle (sketch, not to the model; "
             "heights from the board top)", fontsize=10, va="top")
fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "cart-plug-sketch.png", bbox_inches="tight")
