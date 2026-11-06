"""Picture of both jack power boards' placement (knob step 2, 6 Nov 2026): each board, each face, seen from the front (the B faces
mirrored back so x matches the panel), every part as its pads' outline + 0.25, coloured by circuit block, chips labelled.
Reads upper/placement.json and lower/placement.json (make_boards.py) and design.py.
  python3 placement_picture.py <out.png>"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design

COL = {"power in": "#ef9a9a", "supply": "#ffcc80", "jack1": "#90caf9", "jack2": "#90caf9", "jack3": "#90caf9", "jack circuits": "#64b5f6",
       "dac": "#ce93d8", "audio": "#fff59d", "digital": "#c5e1a5", "oled": "#80deea", "connectors": "#bdbdbd"}


def main(out):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Polygon
    blk = {p["ref"]: p for p in design.build()}
    fig, axs = plt.subplots(4, 1, figsize=(13.5, 13.0), dpi=130)
    k = 0
    for which, title in (("upper", "Jack power board"), ("lower", "Jack lower board")):
        pl = json.load(open(os.path.join(HERE, which, "placement.json")))
        for face, fname in (("F", "top face (toward the jack board)"), ("B", "underside, seen through from the front")):
            ax = axs[k]; k += 1
            ax.add_patch(Polygon(pl["outline"], closed=True, fc="#1b5e20", ec="black", lw=1.0, alpha=0.25))
            by_ref = {}
            for p in pl["pads"]:
                if p["side"] == face or (p["drill"][0] > 0):
                    by_ref.setdefault(p["ref"], []).append(p)
            for ref, pads in by_ref.items():
                xs0 = [q["xy"][0] - (q["size"][1] if abs(round(q["rot"]) % 180) == 90 else q["size"][0]) / 2 for q in pads]
                xs1 = [q["xy"][0] + (q["size"][1] if abs(round(q["rot"]) % 180) == 90 else q["size"][0]) / 2 for q in pads]
                ys0 = [q["xy"][1] - (q["size"][0] if abs(round(q["rot"]) % 180) == 90 else q["size"][1]) / 2 for q in pads]
                ys1 = [q["xy"][1] + (q["size"][0] if abs(round(q["rot"]) % 180) == 90 else q["size"][1]) / 2 for q in pads]
                x0, x1, y0, y1 = min(xs0) - 0.1, max(xs1) + 0.1, min(ys0) - 0.1, max(ys1) + 0.1
                p = blk.get(ref)
                c = COL.get(p["block"], "#e0e0e0") if p else "#e0e0e0"
                ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=c, ec="black", lw=0.4))
                for q in pads:
                    w, h = q["size"]
                    if abs(round(q["rot"]) % 180) == 90:
                        w, h = h, w
                    ax.add_patch(Rectangle((q["xy"][0] - w / 2, q["xy"][1] - h / 2), w, h, fc="#b0882f", ec="none", alpha=0.8))
                if ref[0] in "UJHD" or ref.startswith(("L", "MP")):
                    nm = p["value"].split()[0][:12] if p else ref
                    ax.text((x0 + x1) / 2, (y0 + y1) / 2, f"{ref}\n{nm}", ha="center", va="center", fontsize=5.0)
            ax.set_xlim(-22.5, 22.5); ax.set_ylim(-52.0, -37.8); ax.set_aspect("equal")
            ax.set_title(f"{title}: {fname}", fontsize=9, loc="left"); ax.grid(alpha=0.12)
    axs[-1].set_xlabel("x (mm, panel)")
    h = [Rectangle((0, 0), 1, 1, fc=c) for c in ("#ef9a9a", "#ffcc80", "#90caf9", "#64b5f6", "#ce93d8", "#fff59d", "#c5e1a5", "#80deea", "#bdbdbd")]
    fig.legend(h, ["power in", "rails", "switching (per jack)", "op-amps", "DAC", "audio", "expander / MIDI", "OLED", "connectors"],
               loc="lower center", ncol=9, fontsize=7.5, frameon=False)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(out); print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "placement.png")
