"""[Ed 3 Nov 09:47-11:32] layout v4: two vertical boards standing on the main-board front under the joystick (PANEL frame).

Each board (y-z plane at x = ±vb.x) has a right-angle header along its bottom edge (body on the main board against the outer face,
legs into the main board) and a right-angle spring-contact strip along its top edge (body on the outer face, plungers up onto
gold pads under the joystick top board, drawn at their nominal compression). One standoff joins the two boards at mid height,
with a low-head screw through each board. L (-x): power. R (+x): CAN and the joystick lines. Envelopes [A] until parts are picked."""
from build123d import *
from ...common.util import A, cyl


def _box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=A)


def _cyl_x(d, x0, x1, y, z):
    """Cylinder along x from x0 to x1 (either order), diameter d, axis at (y, z)."""
    a, b = min(x0, x1), max(x0, x1)
    return Pos((a + b) / 2, y, z) * Rot(0, 90, 0) * Cylinder(d / 2, b - a)


def build(D):
    V, H, G, S = D["vb"], D["vb_hdr"], D["vb_pogo"], D["vb_standoff"]
    t = D["pcb_t"]
    y0, y1 = V["y"]
    fo, fi, z0, z1 = D["vb_face_out"], D["vb_face_in"], V["z0"], D["vb_z1"]
    sc = S["screw"]
    out = {}
    for sx, tag, role in ((-1, "L", V["roles"][0]), (1, "R", V["roles"][1])):
        board = _box(min(sx * fi, sx * fo), max(sx * fi, sx * fo), y0, y1, z0, z1)
        board -= _cyl_x(sc["hole"], sx * (fi - 0.5), sx * (fo + 0.5), S["y"], S["z"])
        out[f"vertical board {tag} ({role}), 1.0 FR4"] = board
        # right-angle header: insulator on the main board against the outer face; legs down through the main board
        hb = _box(min(sx * fo, sx * (fo + H["body_x"])), max(sx * fo, sx * (fo + H["body_x"])), y0, D["vb_hdr_y1"], z0, H["body_z"])
        legs = [Pos(sx * D["vb_pin_x"], y, -t - H["tail"]) * Box(H["pin"], H["pin"], t + H["tail"] + 0.01, align=A)
                for y in D["vb_pins"][sx]]
        out[f"vertical board {tag} header (right-angle, {len(legs)} pins into the main board) [A]"] = Compound(children=[hb] + legs)
        # spring-contact strip: insulator on the outer face along the top edge; plungers at their nominal compression
        yc = D["vb_contact_y"]
        cb = _box(min(sx * fo, sx * (fo + G["body_x"])), max(sx * fo, sx * (fo + G["body_x"])),
                  yc[0] - G["pitch"] / 2, yc[-1] + G["pitch"] / 2, z1 - G["body_z"], z1)
        pl = [cyl(G["plunger"] / 2, z1 - 0.01, V["top_board_z"] - 0.005 - (z1 - 0.01), sx * D["vb_contact_x"], y) for y in yc]
        out[f"vertical board {tag} spring contacts (right-angle strip, {len(yc)}) [A]"] = Compound(children=[cb] + pl)
        # standoff screw: low head on the outer face, shank through the board into the standoff
        head = _cyl_x(sc["head_d"], sx * (fo + 0.01), sx * (fo + 0.01 + sc["head_k"]), S["y"], S["z"])
        shank = _cyl_x(sc["d_model"], sx * (fi - 0.02), sx * (fo + 0.02), S["y"], S["z"])
        out[f"vertical board {tag} M2 screw ({sc['part']})"] = head + shank
    so = _cyl_x(S["od"], -(fi - 0.01), fi - 0.01, S["y"], S["z"]) - _cyl_x(sc["hole"] - 0.4, -fi, fi, S["y"], S["z"])
    out["vertical boards' standoff (M2 F-F brass, joins L and R) [A]"] = so
    return out
