"""Shared drawing-sheet helpers: third-angle views from a build123d shape -> DXF + A3 PNG.
World axes: X = panel x (right), Y = up (= -y from panel top), Z = toward the panel front.
Third-angle layout: FRONT view looks along -Z; PLAN (top) view sits above it, looking down (-Y);
RIGHT SIDE view sits to the right, looking along -X, front (+Z) on its left.
CONVENTION (Ed, 2026-10-31): the PLAN view is drawn with the front (+Z, toward the panel) pointing UP the sheet,
e.g. board at the bottom and motor shaft tip at the top. It is the true top view (top-visible edges, X still to the right)
mirrored top-to-bottom; strict third-angle would put the front at the bottom. Set PLAN_FRONT_UP = False for strict.

LAYOUT "z-up" (DEFAULT from 2026-10-31, Ed on assembly v0.7): the dial axis (+Z, toward the panel front) is UP the sheet in every
elevation, as if the module lies on the bench with the knob up. Strict third-angle:
  "front" = FRONT elevation, looking along +Y (from the panel-bottom side): sheet x = X, y = Z (board at the bottom, shaft up)
  "plan"  = TOP view placed ABOVE the front, looking down the dial axis (-Z): sheet x = X, y = Y (panel top edge up)
  "side"  = RIGHT SIDE view placed RIGHT of the front, looking along -X: sheet x = Y, y = Z (front-view side on its left)
The front and side share Z heights; the front and plan share X. Dims/notes use those view coordinates.
LAYOUT "panel" is the earlier layout (front = panel face X-Y, plan = X-Z front-up above it, side x = -Z, y = Y); existing
part scripts pass layout="panel" explicitly so they render as before."""
import math
from build123d import GeomType

FAR = 1000
PLAN_FRONT_UP = True
VIEWS = {"front": ((0, 0, FAR), (0, 1, 0)), "plan": ((0, FAR, 0), (0, 0, -1)), "side": ((FAR, 0, 0), (0, 1, 0))}
VIEWS_ZUP = {"front": ((0, -FAR, 0), (0, 0, 1)), "plan": ((0, 0, FAR), (0, 1, 0)), "side": ((FAR, 0, 0), (0, 0, 1))}
DEFAULT_LAYOUT = "z-up"


def project(shape, layout="panel"):
    out = {}
    for k, (o, up) in (VIEWS_ZUP if layout == "z-up" else VIEWS).items():
        vis, hid = shape.project_to_viewport(o, up, (0, 0, 0))
        def pts(es):
            res = []
            for e in es:
                n = 2 if e.geom_type == GeomType.LINE else 64
                res.append([((e @ (i / (n - 1))).X, (e @ (i / (n - 1))).Y) for i in range(n)])
            return res
        v, h = pts(vis), pts(hid)
        if k == "plan" and PLAN_FRONT_UP and layout != "z-up":
            v = [[(x, -y) for x, y in pl] for pl in v]; h = [[(x, -y) for x, y in pl] for pl in h]
        out[k] = (v, h)
    return out


def bbox2d(polys):
    xs = [x for pl in polys for x, _ in pl]; ys = [y for pl in polys for _, y in pl]
    return min(xs), max(xs), min(ys), max(ys)


class Sheet:
    def __init__(self, shape=None, gap=18, scale=1.0, label_pad=13, layout=None):
        """scale = PNG drawing scale (e.g. 3 -> 3:1); the DXF is always 1:1. gap is in sheet mm. layout: "z-up" (default) or "panel"."""
        self.layout = layout or DEFAULT_LAYOUT
        self.v = project(shape, self.layout)
        f = bbox2d(self.v["front"][0]); p = bbox2d(self.v["plan"][0]); s = bbox2d(self.v["side"][0])
        self.bb = {"front": f, "plan": p, "side": s}
        self.gap = gap; self._set_scale(scale); self.scale = scale; self.label_pad = label_pad
        self.sections = []   # (label, face, scale, notes)
        self.zones = []      # (view, x0, y0, x1, y1, hatch)
        self.refs = []       # (view, x0, y0, x1, y1, label): dashed reference lines (not parts)
        self.fsec = None     # front view replaced by a section: list of (name, [polygons], hatch)
        self.cut_lines = []  # (view, x0, x1, y, arrow_dir, letter): section cutting lines
        self.dims = []   # (kind, view, p1, p2, offset, text)
        self.texts = []  # (view, x, y, text, size)

    def _set_scale(self, k):
        # align plan above front (same x), side right of front (same y)
        f, p, s = self.bb["front"], self.bb["plan"], self.bb["side"]; g = self.gap
        self.k = k
        dy = getattr(self, "side_dy", 0.0)
        self.off = {"front": (0, 0), "plan": (0, (f[3] - p[2]) * k + g), "side": ((f[1] - s[0]) * k + g, dy * k)}

    def P(self, view, x, y):
        ox, oy = self.off[view]; return x * self.k + ox, y * self.k + oy

    def hdim(self, view, x1, x2, yref, yline, text): self.dims.append(("h", view, x1, x2, yref, yline, text))
    def vdim(self, view, y1, y2, xref, xline, text): self.dims.append(("v", view, y1, y2, xref, xline, text))
    def note(self, view, x, y, text, size=6.5, **kw): self.texts.append((view, x, y, text, size, kw))

    def hatch_zone(self, view, x0, y0, x1, y1, hatch="||||"):
        """Hatched rectangle in view coords (e.g. a knurl zone that is not modelled as geometry). PNG only."""
        self.zones.append((view, x0, y0, x1, y1, hatch))

    def ref_line(self, view, x0, y0, x1, y1, label=""):
        """Thin dashed reference line in view coords (e.g. an assumed back-panel position). Not a part."""
        self.refs.append((view, x0, y0, x1, y1, label))

    def set_front_section(self, items, title="SECTION A-A"):
        """Replace the FRONT view with a full section. items = [(name, faces, hatch)], faces are planar build123d Faces
        lying in a plane of constant world Y; they are drawn in (X, Z) with Z up the sheet (front-up, like the plan)."""
        def pts(w):
            out = []
            for e in w.order_edges():
                n = 2 if e.geom_type == GeomType.LINE else 24
                out += [((e @ (i / (n - 1))).X, (e @ (i / (n - 1))).Z) for i in range(n - 1)]
            return out
        self.fsec = []
        outl = []
        for name, faces, hatch in items:
            polys = []
            for f in faces:
                ws = [f.outer_wire()] + list(f.inner_wires())
                polys.append([pts(w) for w in ws])
                outl += [q + [q[0]] for q in polys[-1]]
            self.fsec.append((name, polys, hatch))
        self.v["front"] = (outl, [])
        self.bb["front"] = bbox2d(outl)
        self.front_title = title
        f, sd = self.bb["front"], self.bb["side"]
        if self.layout != "z-up":   # panel layout: the side view no longer shares the front's y (section is X-Z)
            self.side_dy = (f[2] + f[3]) / 2 - (sd[2] + sd[3]) / 2
        self._set_scale(self.k)

    def cut_line(self, view, x0, x1, y, arrow_dir=-1, letter="A"):
        """Section cutting line (chain, thick ends) at view-y = y from x0 to x1; arrows point along view-y arrow_dir."""
        self.cut_lines.append((view, x0, x1, y, arrow_dir, letter))

    def add_section(self, label, face, scale, notes=()):
        """Enlarged cross-section (a planar build123d Face in its own XY), drawn hatched in the
        title-block column of the PNG at `scale`, and at 1:1 to the right of the views in the DXF."""
        self.sections.append((label, face, scale, list(notes)))

    @staticmethod
    def _wire_pts(w, n=24):
        pts = []
        for e in w.order_edges():
            m = 2 if e.geom_type == GeomType.LINE else n
            pts += [((e @ (i / (m - 1))).X, (e @ (i / (m - 1))).Y) for i in range(m - 1)]
        return pts

    def dxf(self, path, title_lines, extra_layers=None):
        import ezdxf
        k_png = self.k; self._set_scale(1.0)
        doc = ezdxf.new("R2010", setup=True); doc.header["$INSUNITS"] = 4
        for n, c, lt in (("VISIBLE", 7, "CONTINUOUS"), ("HIDDEN", 8, "DASHED"), ("DIMS", 3, "CONTINUOUS"), ("TEXT", 7, "CONTINUOUS")):
            doc.layers.add(n, color=c, linetype=lt)
        msp = doc.modelspace()
        for k, (vis, hid) in self.v.items():
            for layer, es in (("VISIBLE", vis), ("HIDDEN", hid)):
                for pl in es:
                    msp.add_lwpolyline([self.P(k, x, y) for x, y in pl], dxfattribs={"layer": layer})
        ds = dict(dimstyle="EZDXF", override={"dimtxt": 1.6, "dimasz": 1.0, "dimexe": 0.6, "dimexo": 0.5, "dimdec": 2}, dxfattribs={"layer": "DIMS"})
        for d in self.dims:
            if d[0] == "h":
                _, k, x1, x2, yref, yl, t = d
                msp.add_linear_dim(base=self.P(k, x1, yl), p1=self.P(k, x1, yref), p2=self.P(k, x2, yref), **ds).render()
            else:
                _, k, y1, y2, xref, xl, t = d
                msp.add_linear_dim(base=self.P(k, xl, y1), p1=self.P(k, xref, y1), p2=self.P(k, xref, y2), angle=90, **ds).render()
        for k, a0, b0, a1, b1, lab in self.refs:
            msp.add_line(self.P(k, a0, b0), self.P(k, a1, b1), dxfattribs={"layer": "HIDDEN"})
        for k, x, y, t, s, kw in self.texts:
            msp.add_text(t, height=1.4, dxfattribs={"layer": "TEXT"}).set_placement(self.P(k, x, y))
        x0 = min(self.P("front", self.bb["front"][0], 0)[0], 0); y0 = self.P("front", 0, self.bb["front"][2])[1] - 14
        for i, t in enumerate(title_lines):
            msp.add_text(t, height=1.6, dxfattribs={"layer": "TEXT"}).set_placement((x0, y0 - i * 2.6))
        if self.sections:
            doc.layers.add("SECTION", color=5)
            sx0 = self.P("side", self.bb["side"][1], 0)[0] + 15
            for i, (lab, face, k, notes) in enumerate(self.sections):
                cx, cy = sx0 + 10 + i * 20, 0
                for w in [face.outer_wire()] + list(face.inner_wires()):
                    q = [(x + cx, y + cy) for x, y in self._wire_pts(w)]
                    msp.add_lwpolyline(q, close=True, dxfattribs={"layer": "SECTION"})
                msp.add_text(lab + " (1:1)", height=1.0, dxfattribs={"layer": "TEXT"}).set_placement((cx - 4, cy + 4))
        doc.saveas(path); self._set_scale(k_png)

    def png(self, path, title, sub_lines, labels=None):
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
        fig = plt.figure(figsize=(16.54, 11.69), dpi=150)
        ax = fig.add_axes([0.03, 0.03, 0.94, 0.94]); ax.set_aspect("equal"); ax.axis("off")
        for k, (vis, hid) in self.v.items():
            for pl in hid:
                q = [self.P(k, x, y) for x, y in pl]; ax.plot([a for a, _ in q], [b for _, b in q], color="0.5", lw=0.5, ls=(0, (3, 2)))
            for pl in vis:
                q = [self.P(k, x, y) for x, y in pl]; ax.plot([a for a, _ in q], [b for _, b in q], color="black", lw=1.0)
        for k, a0, b0, a1, b1, hp in self.zones:
            (X0z, Y0z), (X1z, Y1z) = self.P(k, a0, b0), self.P(k, a1, b1)
            ax.add_patch(Rectangle((min(X0z, X1z), min(Y0z, Y1z)), abs(X1z - X0z), abs(Y1z - Y0z),
                                   facecolor="none", edgecolor="black", lw=0.6, hatch=hp))
        if self.fsec:
            from matplotlib.path import Path as MPath0
            from matplotlib.patches import PathPatch as PP0
            import matplotlib as _mpl
            _mpl.rcParams["hatch.linewidth"] = 0.45
            for name, polys, hp in self.fsec:
                for rings in polys:
                    verts, codes = [], []
                    for q in rings:
                        qq = [self.P("front", x, y) for x, y in q]
                        verts += qq + [qq[0]]; codes += [MPath0.MOVETO] + [MPath0.LINETO] * (len(qq) - 1) + [MPath0.CLOSEPOLY]
                    ax.add_patch(PP0(MPath0(verts, codes), facecolor="white", edgecolor="black", lw=0.7, hatch=hp))
        for k, x0c, x1c, yc, dr, let in self.cut_lines:
            (A0, B0), (A1, _) = self.P(k, x0c, yc), self.P(k, x1c, yc)
            ax.plot([A0, A1], [B0, B0], color="black", lw=0.5, ls=(0, (10, 2, 2, 2)))
            for A in (A0, A1):
                ax.plot([A, A + (4 if A == A0 else -4)], [B0, B0], color="black", lw=1.6)
                ax.annotate("", (A, B0 + dr * 6), (A, B0), arrowprops=dict(arrowstyle="-|>", lw=1.0, color="black", shrinkA=0, shrinkB=0))
                ax.text(A, B0 + dr * 9, let, ha="center", va="center", fontsize=10, weight="bold")
        for k, a0, b0, a1, b1, lab in self.refs:
            (X0r, Y0r), (X1r, Y1r) = self.P(k, a0, b0), self.P(k, a1, b1)
            ax.plot([X0r, X1r], [Y0r, Y1r], color="0.35", lw=0.6, ls=(0, (6, 3)))
            if lab: ax.text(X1r + 1, Y1r, lab, fontsize=6.5, va="center", color="0.25")
        fs = 7.5
        for d in self.dims:
            if d[0] == "h":
                _, k, x1, x2, yref, yl, t = d
                (a1, r), (a2, _) = self.P(k, x1, yref), self.P(k, x2, yref); _, l = self.P(k, 0, yl)
                s = 1 if l > r else -1
                for a in (a1, a2): ax.plot([a, a], [r + 0.4 * s, l + 0.8 * s], color="black", lw=0.4)
                ax.annotate("", (a1, l), (a2, l), arrowprops=dict(arrowstyle="<->", lw=0.6, shrinkA=0, shrinkB=0))
                ax.text((a1 + a2) / 2, l + (0.5 if s > 0 else -0.7), t, ha="center", va="bottom" if s > 0 else "top", fontsize=fs)
            else:
                _, k, y1, y2, xref, xl, t = d
                (r, b1), (_, b2) = self.P(k, xref, y1), self.P(k, xref, y2); l, _ = self.P(k, xl, 0)
                s = 1 if l > r else -1
                for b in (b1, b2): ax.plot([r + 0.4 * s, l + 0.8 * s], [b, b], color="black", lw=0.4)
                ax.annotate("", (l, b1), (l, b2), arrowprops=dict(arrowstyle="<->", lw=0.6, shrinkA=0, shrinkB=0))
                ax.text(l + (-0.6 if s < 0 else 0.6), (b1 + b2) / 2, t, ha="right" if s < 0 else "left", va="center", fontsize=fs, rotation=90)
        for k, x, y, t, s, kw in self.texts:
            X, Y = self.P(k, x, y); ax.text(X, Y, t, fontsize=s, **kw)
        if self.layout == "z-up":
            names = labels or {"front": getattr(self, "front_title", None) or "FRONT VIEW", "plan": "TOP VIEW (looking down the dial axis)", "side": "RIGHT SIDE VIEW"}
        else:
            names = labels or {"front": getattr(self, "front_title", None) or "FRONT VIEW", "plan": "PLAN (TOP) VIEW" + (" — front up" if PLAN_FRONT_UP else ""), "side": "RIGHT SIDE VIEW"}
        for k, lab in names.items():
            b = self.bb[k]; X, Y = self.P(k, b[0], b[3]); ax.text(X, Y + self.label_pad, lab, fontsize=9, weight="bold")
        # extents
        allx, ally = [], []
        for k in self.v:
            b = self.bb[k]; x1, y1 = self.P(k, b[0], b[2]); x2, y2 = self.P(k, b[1], b[3]); allx += [x1, x2]; ally += [y1, y2]
        X0, X1, Y0, Y1 = min(allx) - 18, max(allx) + 18, min(ally) - 12, max(ally) + self.label_pad + 4
        # title block bottom-right, scale bar above it
        tbw, tbh = 92, 15
        tbx, tby = X1 + 10, Y0
        ax.add_patch(Rectangle((tbx, tby), tbw, tbh, fill=False, lw=0.9))
        ax.plot([tbx, tbx + tbw], [tby + 10, tby + 10], color="black", lw=0.5)
        ax.text(tbx + 1, tby + 12.5, title, fontsize=9, weight="bold", va="center")
        for i, t in enumerate(sub_lines):
            ax.text(tbx + 1, tby + 8.2 - i * 2.4, t, fontsize=6.8, va="center")
        sx, sy = tbx + tbw - 9, tby + 3.5
        ax.plot([sx - 3.2, sx - 3.2, sx - 1.0, sx - 1.0, sx - 3.2], [sy - 0.6, sy + 0.6, sy + 1.3, sy - 1.3, sy - 0.6], color="black", lw=0.5)
        th = [i * 2 * math.pi / 60 for i in range(61)]
        for rr in (1.3, 0.6): ax.plot([sx + 1.5 + rr * math.cos(t) for t in th], [sy + rr * math.sin(t) for t in th], color="black", lw=0.5)
        bx, by = tbx, tby + tbh + 5
        k = self.k; seg = 2.0 if k < 2 else 1.0   # real mm per segment
        for i in range(10):
            ax.add_patch(Rectangle((bx + i * seg * k, by), seg * k, 0.8, facecolor="black" if i % 2 == 0 else "white", edgecolor="black", lw=0.4))
        for v in (0, 5 * seg, 10 * seg): ax.text(bx + v * k, by - 0.6, f"{v:g}" + (" mm" if v == 10 * seg else ""), ha="center", va="top", fontsize=6.5)
        if k != 1: ax.text(bx + 10 * seg * k + 4, by + 0.4, f"Scale {k:g}:1 (DXF 1:1)", fontsize=6.5, va="center")
        from matplotlib.path import Path as MPath
        from matplotlib.patches import PathPatch
        sy_cursor = by + 12
        for lab, face, k2, notes in self.sections:
            fb = face.bounding_box(); hgt = fb.size.Y * k2
            cx = tbx + tbw / 2 - (fb.min.X + fb.max.X) / 2 * k2
            cy = sy_cursor + len(notes) * 2.6 + 4 - fb.min.Y * k2
            verts, codes = [], []
            for w in [face.outer_wire()] + list(face.inner_wires()):
                q = [(cx + x * k2, cy + y * k2) for x, y in self._wire_pts(w)]
                verts += q + [q[0]]; codes += [MPath.MOVETO] + [MPath.LINETO] * (len(q) - 1) + [MPath.CLOSEPOLY]
            ax.add_patch(PathPatch(MPath(verts, codes), facecolor="white", edgecolor="black", lw=0.9, hatch="////"))
            ax.plot([cx - fb.size.X * k2 * 0.7, cx + fb.size.X * k2 * 0.7], [cy, cy], color="0.3", lw=0.4, ls=(0, (8, 2, 1, 2)))
            ax.plot([cx, cx], [cy - hgt * 0.7, cy + hgt * 0.7], color="0.3", lw=0.4, ls=(0, (8, 2, 1, 2)))
            ax.text(tbx + tbw / 2, cy + hgt * 0.75 + 3, f"{lab} (scale {k2:g}:1)", ha="center", fontsize=9, weight="bold")
            for i, t in enumerate(notes):
                ax.text(tbx + 2, sy_cursor + (len(notes) - 1 - i) * 2.6, t, fontsize=6.8)
            sy_cursor = cy + hgt * 0.75 + 10
            Y1 = max(Y1, sy_cursor)
        ax.set_xlim(X0, tbx + tbw + 4); ax.set_ylim(Y0 - 4, Y1)
        fig.savefig(path, facecolor="white"); plt.close(fig)
