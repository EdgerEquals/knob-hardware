"""[Ed 3 Nov 09:47-11:32] layout v4: two vertical boards standing on the main-board front under the joystick (PANEL frame).

v0.24 [Ed 13:31-14:08]: each board (y-z plane at x = ±vb.x) stands on a hybrid right-angle header along its bottom edge (two rows at
1.27, insulator on the main board against the outer face; through-hole legs where the main-board back is clear, surface-mount legs where
it is not: R over the encoder riser). No standoff between the boards. At the top, a right-angle 1.27 male header on the outer face puts
13 pins up into the socket under the joystick top board; the board's edge is lowered under the socket and its two end tabs reach up and
bear on the top board (the boards are the posts that hold the joystick cradle up). L (-x): power. R (+x): CAN and the joystick lines.
Envelopes [A] until parts are picked."""
from build123d import *
from ...common.util import A


def _box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=A)


def build(D):
    V, H, Q = D["vb"], D["vb_hdr"], D["vb_pin"]
    t = D["pcb_t"]
    y0, y1 = V["y"]
    fo, fi, z0 = D["vb_face_out"], D["vb_face_in"], V["z0"]
    ze, ztab = D["vb_ze"], D["vb_z1"] - 0.01            # edge under the sockets; tab tops 0.01 under the top board (bearing)
    out = {}
    for sx, tag, role in ((-1, "L", V["roles"][0]), (1, "R", V["roles"][1])):
        xa, xb = sorted((sx * fi, sx * fo))
        board = _box(xa, xb, y0, y1, z0, ze)
        for ta, tb in D["vb_tabs"]:
            board += _box(xa, xb, ta, tb, ze - 0.01, ztab)
        out[f"vertical board {tag} ({role}), 1.0 FR4"] = board
        # bottom: hybrid right-angle header; THT legs through the main board (tails behind it), SMT legs end on the front pads
        hb = _box(min(sx * fo, sx * (fo + H["body_x"])), max(sx * fo, sx * (fo + H["body_x"])), y0, D["vb_hdr_y1"], z0, H["body_z"])
        legs = [Pos(x, y, -t - H["tail"]) * Box(H["pin"], H["pin"], t + H["tail"] + 0.01, align=A)
                for x, y, kind in D["vb_legs"][sx] if kind == "tht"]
        nt = len(legs); ns = len(D["vb_legs"][sx]) - nt
        out[f"vertical board {tag} header (right-angle 2×1.27, {nt} THT + {ns} SMT legs) [A]"] = Compound(children=[hb] + legs)
        # top: right-angle male header on the outer face under the lowered edge; pins up to the tip inside the socket
        ys0, ys1 = D["vb_sock_y"]
        mb = _box(min(sx * fo, sx * (fo + Q["body_x"])), max(sx * fo, sx * (fo + Q["body_x"])), ys0 + 0.2, ys1 - 0.2, ze - Q["body_z"], ze)
        pins = [Pos(sx * D["vb_top_x"], y, ze - 0.01) * Box(Q["pin"], Q["pin"], D["vb_tip_z"] - ze + 0.01, align=A) for y in D["vb_top_y"]]
        out[f"vertical board {tag} male pins (right-angle 1.27, {Q['n']} into the top-board socket) [A]"] = Compound(children=[mb] + pins)
    return out
