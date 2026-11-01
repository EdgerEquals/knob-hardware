"""Round screen from the SCREENS table (params.py), offset scr_off away from the FPC exit so nothing pokes past the knob OD.
Panel frame: tail toward local +X; placed with Rot(tail_ang) about the panel centre at -scr_off along the tail direction."""
import math
from build123d import *
from ...common.util import A, cyl

def place(D, s):
    a = math.radians(D["tail_ang"]); o = D["scr_off"]
    return Pos(-o * math.cos(a), -o * math.sin(a), 0) * Rot(0, 0, D["tail_ang"]) * s

def to_local(D, x, y):
    a = math.radians(D["tail_ang"]); o = D["scr_off"]
    x, y = x + o * math.cos(a), y + o * math.sin(a)
    return (x * math.cos(-a) - y * math.sin(-a), x * math.sin(-a) + y * math.cos(-a))

def fold_outer_local(D):
    return min(D["S"]["r_edge"] - 0.5, D["scr_off"] + D["fold_x_outer"])

def panel(D):
    S, t = D["S"], D["z_top"]; r = S["od"] / 2
    if "stack" in S:   # layered AMOLED (RM69330 1.39)
        tp, te, tl, tt = S["stack"]
        p = cyl(S["d_pol"] / 2, t - tp, tp)
        enc = cyl(r, t - tp - te, te) - Pos(S["encap_flat"] - r, -25, t - 5) * Box(5, 50, 10, align=(Align.MIN, Align.MIN, Align.MIN))
        zl = t - tp - te - tl
        ledge = Pos(S["r_edge"] - 1.5, 0, zl) * Box(3.0, S["ledge_w"], tl, align=A) & cyl(S["r_edge"], zl, tl)   # corners on the r_edge arc [A]
        ltps = cyl(r, zl, tl) + ledge
        return p + enc + ltps + cyl(S["d_tape"] / 2, D["z_back"], tt)
    b = cyl(r, D["z_back"], S["t"])   # TFT (rigid chin, corners on the r_edge arc [A]): disc + rigid chin to r_edge
    return b + (Pos((S["r_edge"] + r - 3) / 2, 0, D["z_back"]) * Box(S["r_edge"] - r + 3, S["ledge_w"], S["t"], align=A) & cyl(S["r_edge"], D["z_back"], S["t"]))

def fpc(D):
    S = D["S"]; L, W, H = S["fold"]; xo = fold_outer_local(D)
    parts = []
    if not S["rigid"]:   # COF bend outside the ledge edge (no overlap with the ledge)
        z_l = D["z_top"] - S["stack"][0] if "stack" in S else D["z_top"]
        h = z_l - D["z_fpc0"]
        band = Pos(S["r_edge"] - 0.5, 0, D["z_fpc0"]) * Box(S["bend"] + 1.0, 2 * D["cof_half"], h, align=(Align.MIN, Align.CENTER, Align.MIN))
        parts.append(band & (cyl(S["r_edge"] + S["bend"], D["z_fpc0"], h) - cyl(S["r_edge"], D["z_fpc0"], h)))   # bend follows the ledge arc [A]
    parts.append(Pos(xo, 0, D["z_fpc0"]) * Box(L, W, H, align=(Align.MAX, Align.CENTER, Align.MIN)))
    if S["b2b"]:
        bx, by = to_local(D, *D["b2b_xy"]); l, w, h = S["b2b"]
        bl = Rot(0, 0, -D["tail_ang"]) * Box(l, w, h, align=A)
        parts.append(Pos(bx, by, D["z_fpc0"] - h) * bl)
    s = parts[0]
    for q in parts[1:]: s = s + q
    return s

def jumper(D, travel=0.0):
    S = D["S"]; j1 = D["adapter_env"][D["adapter_fps"][D["b2b_at"]][0]]
    z0 = D["z_board_top"] + j1[2]; z1 = D["z_b2b0"]
    if not (D["screen_on_dial"] and D["b2b_flip"]):
        x, y = D["b2b_xy"]
        return Pos(x, y, z0) * Box(4.0, D["jumper_t"], z1 - z0, align=A)
    # v0.15 diametral service strap: J1 tail (stationary) -> strap through the axis -> B2B tail (rotating); straight at theta = 0
    (xj, yj), (xb, yb) = D["j1_xy"], D["b2b_xy"]; L = D["strap_L"]; ang = math.degrees(math.atan2(yb - yj, xb - xj))
    zs0, zs1 = D["strap_z0"], D["strap_z1"]
    strap = Pos((xj + xb) / 2, (yj + yb) / 2, zs0) * Rot(0, 0, ang) * Box(L, D["strap_t"], zs1 - zs0, align=A)
    tail = Pos(xj, yj, z0) * Rot(0, 0, ang) * Box(D["strap_t"] * 2, 4.0, zs0 - z0 + 0.3, align=A)    # J1 tail stiffener [A]
    return strap + tail

def strap_bent(D, travel):
    """Strap shape at dial angle travel: circular arc of curvature theta/L (clamped-clamped ends on a diameter), as boxes."""
    (xj, yj), (xb, yb) = D["j1_xy"], D["b2b_xy"]; L = D["strap_L"]; th = math.radians(travel); n = 16
    ang = math.atan2(yb - yj, xb - xj); pts = []
    for i in range(n + 1):
        s = L * i / n; w = th / (2 * L) * s * s                         # w'' = theta/L, w(0)=w'(0)=0
        pts.append((xj + s * math.cos(ang) - w * math.sin(ang), yj + s * math.sin(ang) + w * math.cos(ang)))
    z0, z1 = D["strap_z0"], D["strap_z1"]; out = None
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        q = Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * Rot(0, 0, math.degrees(math.atan2(y1 - y0, x1 - x0))) * Box(math.hypot(x1 - x0, y1 - y0) + 0.02, D["strap_t"], z1 - z0, align=A)
        out = q if out is None else out + q
    return out

def build(D):
    name = D["screen"]
    return {f"screen {name} panel": place(D, panel(D)), f"screen {name} FPC + B2B": place(D, fpc(D)), ("screen FPC service strap [A]" if D["screen_on_dial"] and D["b2b_flip"] else "screen jumper FPC [A]"): jumper(D)}
