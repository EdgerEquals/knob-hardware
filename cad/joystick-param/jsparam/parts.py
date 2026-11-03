"""Top-screen joystick stack parts, v0.4-v0.6: build(D) -> {name: solid}. Reads D only.
v0.6: the DO0164FMST02 with its back in roof pockets, a foam pad, the roof window and step at the connector, the custom jumper.

The carrier is a thin shell. The screen is glued to a separate bezel that floats on four catalog
compression springs. Each spring sits on an M2 grub screw in the carrier, set before the stack is
assembled. A flat plate glued on the daughterboard carries the ball seats. There is no spider,
no plunger, no round stop and no printed base.
"""
import math
from build123d import *

A = (Align.CENTER, Align.CENTER, Align.MIN)
# v0.7 part names (layout v4 step 1)
DB_NAME = "joystick top board (on the spring contacts)"
CC_NAME = "joystick case cradle (SLA, lip in the faceplate cutout)"
GK_NAME = "joystick cradle gasket (silicone sponge) [A]"
# v0.8 part names (step-1 follow-ups)
DB_NAME8 = "joystick top board (on the vertical boards, sockets under it)"
GK_NAME8 = "joystick cradle gasket: form-in-place silicone bead [A]"
SK_NAME = "top-board socket {} (1.27 single row, {}) [A]"
US_NAME = "guide up-stop cushion {} ({}) [A]"
# v0.9 [Ed 18:35] the cradle is printed into the case (one UTR-8100 print with the faceplate)
CC_NAME9 = "joystick case cradle (printed with the case, UTR-8100)"


def cc_name(D):
    return CC_NAME9 if D.get("cradle_in_case") else CC_NAME


def db_name(D):
    return DB_NAME8 if D.get("top_joint") == "sockets" else DB_NAME


def gk_name(D):
    return GK_NAME8 if D.get("top_joint") == "sockets" else GK_NAME

def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=A)

def cbox(w, h, z0, z1, x=0.0, y=0.0):
    return box(x - w / 2, x + w / 2, y - h / 2, y + h / 2, z0, z1)

def rbox(w, h, r, z0, z1, x=0.0, y=0.0):
    """Box with rounded vertical corners (review fix: matches the case opening's corner radius)."""
    if r <= 1e-6:
        return cbox(w, h, z0, z1, x, y)
    return Pos(x, y, z0) * extrude(RectangleRounded(w, h, r), z1 - z0)

def cyl(d, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, z0) * Cylinder(d / 2, z1 - z0, align=A)

def cyl_x(d, x0, x1, y=0.0, z=0.0):
    """Cylinder along X, from x0 to x1."""
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(d / 2, abs(x1 - x0))

def hex_at(af, z0, z1, x=0.0, y=0.0):
    """Hex prism, across-flats `af`. A flat faces +y so the wrench flat is parallel to the PCB edge."""
    r = (af / 2) / math.cos(math.radians(30))
    return Pos(x, y, z0) * Rot(0, 0, 30) * extrude(RegularPolygon(radius=r, side_count=6), z1 - z0)

def step_region(D, solid, y_from=None):
    """v0.8: the part of a solid on the top-edge step (local y >= the step's start, fl_y1 by default)."""
    y0 = D["st_y0"] if y_from is None else y_from
    return solid & box(-60.0, 60.0, y0, 60.0, -20.0, 80.0)

def notched(D, z0, z1):
    """Full corner rectangle, with the middle of each long side cut back to h_mid.

    The knob faces that middle edge. The four corners stay tall enough for a spring
    outside the glass, and they sit outside the knob's plan.
    """
    s = cbox(2 * D["half_w"], 2 * D["half_h"], z0, z1)
    if D["half_h"] > D["h_mid"] + 1e-6:
        s -= box(-D["x_notch"], D["x_notch"], D["h_mid"], D["half_h"] + 1.0, z0 - 0.05, z1 + 0.05)
        s -= box(-D["x_notch"], D["x_notch"], -(D["half_h"] + 1.0), -D["h_mid"], z0 - 0.05, z1 + 0.05)
    return s

def pcb(D):
    t = D["pcb_t"]
    x0, x1 = -D["pcb_w"] / 2, D["pcb_w"] / 2
    y1 = D["y_pcb"]
    y0 = -D["place_y"] - D["scr"]["h"] / 2
    p = box(x0, x1, y0, y1, -t, 0)
    for x, y in D["springs"]:
        p -= cyl(D["spr_bore"], -t - 1, 1, x, y)
    for x, y in D["standoff_xy"]:
        p -= cyl(D["drill_m2"], -t - 1, 1, x, y)
    for x, y in D.get("cr_pins", []):   # v0.5 cradle locating dowels
        p -= cyl(D["cradle"]["pin"]["d"] + 0.05, -t - 1, 1, x, y)
    for x, y in D.get("access_xy", []):   # [Ed 13:23] press-spring grub access
        p -= cyl(D["grub_access_d"], -t - 1, 1, x, y)
    if not D["fpc_to_db"]:   # v0.4 drop through the main PCB; v0.5 plugs into the daughterboard instead
        p -= box(D["hole_x0"], D["hole_x1"], -D["hole_hy"], D["hole_hy"], -t - 1, 1)
    return p

def plate(D):
    """Flat stiffener glued on the daughterboard. Ball seats stand on it.
    The standoff screws pass through the plate and the board together.
    No round stop, and no hole for the grub screws: those are outside this outline."""
    x0, x1, y0, y1 = D["board_x0"], D["board_x1"], D["board_y0"], D["board_y1"]
    p = box(x0, x1, y0, y1, D["z_plate0"], D["z_plate1"])
    p -= cyl(2 * D["cut_r"], D["z_plate0"] - 0.01, D["z_plate1"] + 0.01)
    for x, y in D["standoff_xy"]:
        p -= cyl(D["drill_m2"], D["z_plate0"] - 0.01, D["z_plate1"] + 0.01, x, y)
    for x, y in D["springs"]:
        p -= cyl(D["spr_bore"], D["z_plate0"] - 0.2, D["z_plate1"] + 0.2, x, y)
    for x, y in D["balls"]:
        p += cyl(2 * D["boss_r"], D["z_plate1"] - 0.01, D["z_rim_lo"], x, y)
        p -= Pos(x, y, D["z_sc_lo"]) * Sphere(D["cup_r"])
    for x, y in D["springs"]:
        p -= cyl(D["spr_bore"], D["z_plate0"] - 0.2, D["z_rim_lo"] + 0.2, x, y)
    return p

def cradle(D):
    """v0.5 [Ed 2 Nov]: printed cradle glued to the main PCB. A ring under the joystick board's rim (the board is glued on
    it), towers at the extreme corners carrying the lower ball cups, and two locating dowels into the PCB. The top towers
    start above the case's top corner posts and hang off the ring; the knob-side towers stand on the PCB."""
    C = D["cradle"]; zt = D["z_db0"] - 0.02
    r = box(-D["cr_out_x"], D["cr_out_x"], D["cr_out_y0"], D["cr_out_y1"], 0.01, zt)
    r -= box(-D["cr_in_x"], D["cr_in_x"], -D["cr_in_y"], D["cr_in_y"], -0.1, zt + 0.1)
    for x, y in D["balls"]:
        z0 = C["tower_z0"] if y > 0 else 0.01
        sx = 1 if x > 0 else -1
        r += cyl(2 * D["boss_r"], z0, D["z_rim_lo"], x, y)
        # bracket from the ring wall out to the tower, up to the board underside
        yr = D["cr_in_y"] if y > 0 else -D["cr_in_y"]
        r += box(min(sx * D["cr_in_x"], x), max(sx * D["cr_in_x"], x), min(yr, y), max(yr, y), z0, zt)
        r -= Pos(x, y, D["z_sc_lo"]) * Sphere(D["cup_r"])
    for x, y in D.get("cr_pins", []):
        r -= cyl(C["pin"]["d"], 0.0, C["pin"]["len"] - C["pin"]["in_pcb"] + 0.2, x, y)
    # keep the board's footprint and the hold-down bores clear above the ring
    r -= box(-D["db_half_w"] - 0.2, D["db_half_w"] + 0.2, -D["db_half_h"] - 0.2, D["db_half_h"] + 0.2, zt, zt + 5.0)
    if D["fpc_to_db"]:
        r -= box(D["db_half_w"] - 0.5, D["tab_x1"] + 0.2, -D["tab_hy"] - 0.2, D["tab_hy"] + 0.2, zt, zt + 5.0)
    return r

def case_cradle(D, ov=0.0):
    """v0.7 [Ed 3 Nov 11:03] cradle captured by the case (clear SLA). Flange behind the faceplate (−y, ±x; the +y side is over the rail
    strip), lip ring up into the cutout (closed across +y inside the cutout only), hangers and end walls round the top board with
    shoulders over its edge (the board is glued to them; the spring contacts push it up), and the four lower ball seats.
    v0.9 [Ed 18:35]: printed with the case: the lip ring fills the cutout wall below the front, the flange top is the faceplate back.
    ov: how far the lip's outer face and the flange top run into the case (0 in this model: they touch the faceplate proxy; the knob
    assembly passes a small overlap so the two solids fuse into one)."""
    cc = D["cc"]
    zf0, zf1, zl0, zl1 = D["z_fl0"], D["z_fl1"], D["z_lipb"], D["z_lip1"]
    ohw, ohh, ihw, ihh = D["lip_out_hw"] + ov, D["lip_out_hh"] + ov, D["lip_in_hw"], D["lip_in_hh"]
    fx1, fy0, fy1 = D["fl_x1"], D["fl_y0"], D["fl_y1"]
    nhw, ny0, ny1, w = D["nest_hw"], D["nest_y0"], D["nest_y1"], cc["wall"]
    lr = (D.get("corner_r", 0.0) + ov) if D.get("cradle_in_case") else D["lip_corner_r"]   # v0.9: the cutout's own corner radius
    # lip ring in the cutout, all round
    c = rbox(2 * ohw, 2 * ohh, lr, zl0, zl1) - cbox(2 * ihw, 2 * ihh, zl0 - 0.1, zl1 + 0.1)
    # lip root down to the flange, only over the flange (y <= fl_y1)
    if zl0 - zf1 > 0.005:   # v0.9: none (the flange top is the faceplate back, where the lip starts)
        root = rbox(2 * ohw, 2 * ohh, lr, zf1 - 0.01, zl0 + 0.01) - cbox(2 * ihw, 2 * ihh, zf1 - 0.2, zl0 + 0.2)
        c += root - box(-ohw - 1, ohw + 1, fy1, ohh + 1, zf1 - 0.5, zl0 + 0.5)
    # flange: the two side strips (inside edge = the nest wall) and the knob-side strip
    for sx in (-1, 1):
        c += box(min(sx * nhw, sx * fx1), max(sx * nhw, sx * fx1), fy0, fy1, zf0, zf1)
    c += box(-fx1, fx1, fy0, -ihh, zf0, zf1)
    if D.get("cradle_in_case"):   # v0.9 [Ed 18:35]: riser from the flange top to the faceplate back, outboard of the lip's inner face (one print)
        zr = D["z_fp0"] + ov
        riser = box(-fx1, fx1, fy0, fy1, zf1 - 0.01, zr) - box(-ihw, ihw, -ihh, 60.0, zf1 - 0.1, zr + 0.1)
        c += riser
    # hangers along the board's ±x edges and end walls along its ±y edges, from just under the board up to the flange
    for sx in (-1, 1):
        c += box(min(sx * nhw, sx * (nhw + w)), max(sx * nhw, sx * (nhw + w)), ny0 - w, ny1 + w, D["z_nest0"], zf0 + 0.01)
    c += box(-nhw - w, nhw + w, ny0 - w, ny0, D["z_nest0"], zf0 + 0.01)
    c += box(-nhw - w, nhw + w, ny1, ny1 + w, D["z_nest0"], zf0 + 0.01)
    # shoulders over the board edge (x sides full length; y ends), the +x one notched round the screen socket and the jumper's plug
    sh = D["sh_in"]; z0, z1 = D["z_sh0"], D["z_sh1"]
    for sx in (-1, 1):
        c += box(min(sx * (D["board_x1"] - sh), sx * nhw), max(sx * (D["board_x1"] - sh), sx * nhw) + (0.01 if sx > 0 else 0),
                 ny0, ny1, z0, z1)
    c += box(-nhw, nhw, ny0, D["board_y0"] + sh, z0, z1)
    c += box(-nhw, nhw, D["board_y1"] - sh, ny1, z0, z1)
    if D.get("fpc_to_db"):
        hy = D["db_fpc_sock"][0] / 2 + 0.6
        c -= box(D["board_x1"] - sh - 0.1, nhw - 0.01, -hy, hy, z0 - 0.1, z1 + 0.1)
    if "z_dam1" in D:   # v0.8 [Ed 14:02] the dam on the lip ring inside the faceplate's rebate (top edge + the long sides above fl_y1)
        st = D["step"]
        dam = (rbox(2 * D["dam_hw"], 2 * D["dam_hh"], max(D["reb_corner_r"] - st["c"], 0.2), D["z_dam0"], D["z_dam1"])
               - cbox(2 * ihw, 2 * ihh, D["z_dam0"] - 0.1, D["z_dam1"] + 0.1))
        c += step_region(D, dam, D["st_y0"] + st["c"])
    # lower ball seats on brackets from the hangers
    for x, y in D["balls"]:
        sx = 1 if x > 0 else -1
        c += cyl(2 * D["boss_r"], D["z_seat0"], D["z_rim_lo"], x, y)
        c += box(min(x, sx * (nhw + 0.5)), max(x, sx * (nhw + 0.5)), y - 0.8 * D["boss_r"], y + 0.8 * D["boss_r"], D["z_seat0"], zf0 + 0.01)
        c -= Pos(x, y, D["z_sc_lo"]) * Sphere(D["cup_r"])
    return c

def top_board_notches(D, db, z0=None, z1=None):
    """v0.9 [Ed 18:35]: the top board's corner notches round the top corner posts (radius = post + notch_air), squared off up to the
    board's +y edge so no thin horn of board is left at the corner. Also used for the board's path sweep (any z0..z1)."""
    z0 = D["z_db0"] - 0.1 if z0 is None else z0
    z1 = D["z_db1"] + 0.1 if z1 is None else z1
    for x, y, r in D.get("tb_notch", ()):
        db -= cyl(2 * r, z0, z1, x, y)
        xa = abs(x) - r
        db -= box(xa if x > 0 else -60.0, 60.0 if x > 0 else -xa, y, 60.0, z0, z1)
    return db

def cradle_bead(D):
    """v0.8 [Ed 14:03] form-in-place bead, drawn as its contact band at the nominal squeeze, 0.01 short of the case: (1) on the flange top
    under the faceplate back (knob side and the long sides up to fl_y1), the land next to the cutout edge (0.79 wide: the long sides'
    land); (2) a riser where the flange ends, up the rebate's end wall to the step; (3) on the dam's front face under the rebate ceiling
    (top edge and the long sides above fl_y1). The riser is a 3D dispense path [C]."""
    hw, hh, r = D["hole_hw"], D["hole_hh"], D.get("corner_r", 0.0)
    a = D["gk_land_x"]                                   # band width next to the cutout edge
    ring = lambda w, z0, z1: (rbox(2 * (hw + w), 2 * (hh + w), r + w, z0, z1) - rbox(2 * hw, 2 * hh, r, z0 - 0.1, z1 + 0.1))
    fl = ring(a, D["z_fl1"], D["z_fp0"] - 0.01) & box(-60, 60, -60, D["fl_y1"], -20, 80)
    st, y0 = D["step"], D["st_y0"]
    top = step_region(D, ring(D["step_land"], D["z_dam1"], D["z_reb1"] - 0.01), y0 + st["c"])
    risers = None
    for sx in (-1, 1):
        x0, x1 = sorted((sx * hw, sx * (hw + a)))
        rz = box(x0, x1, y0 + 0.01, y0 + st["c"], D["z_fl1"], D["z_reb1"] - 0.01)
        risers = rz if risers is None else risers + rz
    return fl + risers + top

def cradle_gasket(D):
    """v0.7 gasket on the flange top, outside the lip (−y and ±x sides), drawn at its nominal compression, 0.01 under the faceplate."""
    if D.get("top_joint") == "sockets":
        return cradle_bead(D)
    ohw, ohh = D["lip_out_hw"], D["lip_out_hh"]
    g = box(-D["fl_x1"], D["fl_x1"], D["fl_y0"], D["fl_y1"], D["z_fl1"], D["z_fp0"] - 0.01)
    g -= box(-ohw, ohw, -ohh, D["fl_y1"] + 1.0, D["z_fl1"] - 0.1, D["z_fp0"] + 0.1)
    return g

def _fpc_slot(D, z0, z1):
    """Vertical drop for the FPC, plus the in-plane run under the glass edge."""
    return box(D["slot_x"][0], D["slot_x"][1], -D["slot_hy"], D["slot_hy"], z0, z1)

def carrier(D):
    """Thin floor under the faceplate. Spring seats, cup, hold-down hooks, skirt. It fits through the faceplate hole."""
    c = rbox(2 * D["car_hw"], 2 * D["car_hh"], D.get("corner_r", 0.0), D["z_c0"], D["z_floor1"])
    for x, y in D["cs_xy"]:
        # v0.5: the insert top (the grub seat) is level with the floor top; a thin cap boss covers any step
        if D["z_seat"] > D["z_floor1"]:
            c += cyl(D["boss_d"], D["z_floor1"] - 0.01, D["z_seat"], x, y)
        else:
            c -= cyl(2 * D["cs_bore_r"], D["z_seat"], D["z_floor1"] + 0.02, x, y)
        c += cyl(D["boss_d"], D["z_ins0"], D["z_c0"] + 0.01, x, y)
    holes = [cyl(D["ins_hole"], D["z_ins0"] - 0.02, D["z_seat"] + 0.01, x, y) for x, y in D["cs_xy"]]
    for x, y in D.get("g_xy", []):   # v0.5 guide bosses: reamed bore for the brass sleeve, through the floor
        c += cyl(2 * D["g_boss_r"], D["g_boss0"], D["z_c0"] + 0.01, x, y)
        holes.append(cyl(D["g_bore"], D["g_boss0"] - 0.02, D["z_floor1"] + 0.02, x, y))
    for x, y in D["balls"]:
        c += cyl(2 * D["boss_r"], D["z_rim_hi"], D["z_c0"] + 0.01, x, y)
        c -= Pos(x, y, D["z_sc_hi"]) * Sphere(D["cup_r"])
    if D.get("cup_in_bezel"):   # v0.8: the cup is the bezel's; the floor has a clearance hole round its column
        holes.append(cyl(D["car_cup_hole"], D["z_c0"] - 0.05, D["z_floor1"] + 0.05))
    else:
        c += cyl(D["cup_od"], D["z_cup0"], D["z_c0"] + 0.01)
        c -= cyl(D["cup_bore"], D["z_cup0"] - 0.01, D["z_floor1"] + 0.02)
    hook_w = D["spr_d"] * 0.325
    hook_reach = D["spr_d"] * 1.1
    for x, y in D["springs"]:
        c += cyl(D["spr_boss"][0], D["spr_z1"], D["z_c0"] + 0.01, x, y)
        c -= box(x - hook_w, x + hook_w, y - hook_reach, y + D["spr_boss"][1], D["spr_z1"] - 0.01, D["z_c0"] + 0.02)
    m_, my_ = (D["slot_cut"], D["slot_cut"]) if "slot_cut" in D else (0.5, 0.4)   # v0.6: the slot is sized to pass the jumper plug
    c -= box(D["slot_x"][0] - m_, D["slot_x"][1] + m_, -(D["slot_hy"] + my_), D["slot_hy"] + my_,
             D["z_c0"] - 0.5, D["z_floor1"] + 0.5)
    if not D.get("skirt", True):   # v0.7: no skirt; the lip ring is the anti-rotation stop
        for h in holes:
            c -= h
        return c
    g, t = D["skirt_gap"], D["car_skirt"]
    x0, x1 = D["board_x0"] - g, D["board_x1"] + g
    y0, y1 = D["board_y0"] - g, D["board_y1"] + g
    if D["base"] == "cradle":
        # v0.5 cradle: two walls along the board's ±y edges, each in three segments that skip the press-spring grubs
        # (reached from underneath on the sub-assembly) and stop short of the corner towers. Still the anti-rotation stop.
        segs = ([(-D["skirt_x_in"], D["skirt_x_in"]), (D["skirt_x0"], D["skirt_x1"]), (-D["skirt_x1"], -D["skirt_x0"])]
                if D.get("skirt_split", True) else [(-D["skirt_x1"], D["skirt_x1"])])
        skirt = None
        for a, b_ in segs:
            for ya, yb in ((y1, y1 + t), (y0 - t, y0)):
                w = box(a, b_, ya, yb, D["z_skirt0"], D["z_c0"] + 0.01)
                skirt = w if skirt is None else skirt + w
    elif D["fpc_to_db"]:
        # v0.5: two long walls along the board's ±y edges only. They stop short of the press-spring grubs (reached from
        # underneath on the sub-assembly) and leave the +x tab with the screen socket open. Still the anti-rotation stop.
        sx_ = D["skirt_x"]
        skirt = (box(-sx_, sx_, y1, y1 + t, D["z_skirt0"], D["z_c0"] + 0.01)
                 + box(-sx_, sx_, y0 - t, y0, D["z_skirt0"], D["z_c0"] + 0.01))
    else:
        skirt = box(x0 - t, x1 + t, y0 - t, y1 + t, D["z_skirt0"], D["z_c0"] + 0.01)
        skirt -= box(x0, x1, y0, y1, D["z_skirt0"] - 0.01, D["z_c0"] + 0.02)
    c = c + skirt
    for h in holes:   # v0.5: insert and guide holes cut last, so the skirt cannot fill them
        c -= h
    return c

def screen_carrier(D):
    """v0.5 grip block (Ed 2 Nov): walls bz_lip thick from just above the faceplate to the rim, glass glued on a roof plate.
    The press springs push on the roof underside; the peg and the two guide-insert bosses hang from it."""
    S = D["scr"]
    b = cbox(2 * D["half_w"], 2 * D["half_h"], D["z_bz0"], D["z_bz1"])
    b -= cbox(D["pocket"][0], D["pocket"][1], D["z_scr0"], D["z_bz1"] + 0.05)                     # glass pocket
    b -= cbox(2 * (D["half_w"] - D["bz_lip"]), 2 * (D["half_h"] - D["bz_lip"]), D["z_bz0"] - 0.05, D["z_roof"])   # cavity
    for x, y in D["cs_xy"]:   # spring pilots, 0.3 into the roof underside
        b -= cyl(2 * D["cs_bore_r"], D["z_roof"] - 0.05, D["z_roof"] + 0.3, x, y)
    if "peg" in D:   # review fix: the peg is an M2 grub in a centre roof insert, set with a feeler
        pi = D["peg"]["ins"]
        b += cyl(2 * D["p_rboss_r"], D["p_ins_bot"], D["z_roof"] + 0.01)
        b -= cyl(pi["hole"], D["p_ins_bot"] - 0.02, D["p_ins_top"])
    elif D.get("cup_in_bezel"):   # v0.8 [Ed 13:09]: the cup column hangs from the roof; its bore's ceiling sits on the stem top
        b += cyl(D["cup_col_od"], D["z_cup0"], D["z_roof"] + 0.01)
        b -= cyl(D["cup_bore"], D["z_cup0"] - 0.01, D["z_stem_top"])
    else:
        b += cyl(D["peg_d"], D["z_peg"], D["z_roof"] + 0.01)
    gi = D["guide"]["ins"]
    if D.get("back_pk") and "win_x" in D:
        # v0.6: roof step under the connector plate (it carries the +x guide boss), then the pockets for the FMST02's back,
        # the window round the jumper socket, and the insert holes last
        b += box(D["step_x"][0], D["step_x"][1], -D["step_hy"], D["step_hy"], D["z_step"], D["z_roof"] + 0.01)
        for x, y in D["g_xy"]:
            b += cyl(2 * D["g_rboss_r"], D["g_ins_bot"], D["z_roof"] + 0.01, x, y)
        for n, x0, x1, y0, y1, d in D["back_pk"]:
            if n == "B2B header":
                continue
            b -= box(x0, x1, y0, y1, D["z_scr0"] - d, D["z_scr0"] + 0.05)
        b -= box(D["win_x"][0], D["win_x"][1], -D["win_hy"], D["win_hy"], D["z_roof"] - 0.05, D["z_scr0"] + 0.05)
        if "peg" in D:
            b -= cyl(D["peg"]["ins"]["hole"], D["p_ins_bot"] - 0.02, D["p_ins_top"] + 0.01)
        for x, y in D["g_xy"]:
            b -= cyl(gi["hole"], D["g_ins_bot"] - 0.02, D["g_ins_top"] + 0.01, x, y)
        return b
    for x, y in D["g_xy"]:
        b += cyl(2 * D["g_rboss_r"], D["g_ins_bot"], D["z_roof"] + 0.01, x, y)
        b -= cyl(gi["hole"], D["g_ins_bot"] - 0.02, D["g_ins_top"], x, y)
    hy = D["slot_hy"] + 0.3
    # flex: slot through the roof from the drop to the glass edge, and a pocket inside the +x wall for the 180° fold
    # at the glass edge (the wall keeps 0.6 outside it)
    b -= box(D["slot_x"][0] - 0.4, S["w"] / 2 + 0.2, -hy, hy, D["z_roof"] - 0.05, D["z_scr0"] + 0.05)
    b -= box(S["w"] / 2, S["w"] / 2 + D["glue"] + 0.4, -hy, hy, D["z_scr0"] - 0.9, D["scr_top"])
    return b

def faceplate(D):
    """Proxy for the one-piece case face, clear resin UTR-8100. Thickness is the ~2.5 mm wall.
    The lip overlaps the plate. A rebate lets the lip drop for the press without the switch being blocked."""
    m = 10.0
    p = cbox(2 * (D["half_w"] + m), 2 * (D["half_h"] + m), D["z_fp0"], D["z_fp1"])
    p -= rbox(2 * D["hole_hw"], 2 * D["hole_hh"], D.get("corner_r", 0.0), D["z_fp0"] - 0.05, D["z_fp1"] + 0.05)
    if "z_reb1" in D:   # v0.8 [Ed 14:02] the top-edge step: rebate in the faceplate back (top edge and the long sides above fl_y1)
        p -= step_region(D, rbox(2 * D["reb_hw"], 2 * D["reb_hh"], D["reb_corner_r"], D["z_fp0"] - 0.05, D["z_reb1"]))
    if D["up_gap"] < D["press_travel"] + D["tol_sla"] - 1e-9:   # v0.4 proxy only: the real case face is flat (no rebate)
        p -= cbox(2 * (D["half_w"] + D["tol_sla"]), 2 * (D["half_h"] + D["tol_sla"]),
                  D["z_fp1"] - D["fp_rebate"], D["z_fp1"] + 0.05)
    return p

def rear_anchor(D):
    """Printed bar glued to the PCB back. Two pin bores along X, open on +x, each through one pair of hooks.
    A slot over each spring lets the hook be pulled down onto the pin with pliers."""
    b = box(D["ra_x0"], D["ra_x1"], D["ra_y0"], D["ra_y1"], D["ra_z0"], D["ra_z1"])
    sw = D["ra_slot"]
    for y in D["pin_y"]:
        b -= cyl_x(D["pin_bore"], D["ra_x0"] + D["ra_wall"], D["ra_x1"] + 0.05, y, D["z_pin"])
        for x in (D["spr_x"], -D["spr_x"]):
            b -= box(x - sw / 2, x + sw / 2, y - sw / 2, y + sw / 2, D["z_pin"] - D["eye_ro"], D["ra_z1"] + 0.05)
    return b

def hold_down(D, x, y):
    """Spring body plus the lower hook eye. The eye clears the cross pin so the pin can be pushed through."""
    top = D["z_pin"] + D["eye_major"]
    body = cyl(D["spr_d"], top - 0.05, D["spr_z1"], x, y)
    eye = Pos(x, y, D["z_pin"]) * Rot(0, 90, 0) * Torus(D["eye_major"], D["eye_minor"])
    return body + eye

def cross_pin(D, y):
    """Shaft along X through both hooks at this y, with a head outside the +x mouth."""
    shaft = cyl_x(D["pin_d"], D["pin_x0"], D["pin_x1"], y, D["z_pin"])
    head = cyl_x(D["pin_head_d"], D["ra_x1"] + 0.25, D["ra_x1"] + 0.25 + D["pin_head_t"], y, D["z_pin"])
    return shaft + head

def insert(D, x, y):
    """Slip-fit model of the heat-set insert. The real one is an interference fit; that is not a solid overlap."""
    s = cyl(D["ins_od_model"], D["z_ins0"], D["z_seat"] - 0.02, x, y)
    s -= cyl(D["ins_id_model"], D["z_ins0"] - 0.04, D["z_seat"], x, y)
    return s

def switch(D):
    sw = D["sw"]; x, y = D["sw_xy"]; z = D["z_db1"]
    body = Pos(x, y, z) * Rot(0, 0, D["sw_rot"]) * Box(sw["w"], sw["d"], sw["h"], align=A)
    stem = cyl(sw["stem_d"], z + sw["h"], D["z_stem_top"], x, y)
    return body, stem

def build(D):
    out = {}
    out["main PCB (proxy, local patch)"] = pcb(D)
    out["faceplate (case proxy, UTR-8100)"] = faceplate(D)
    dx0, dx1, dy0, dy1 = D["board_x0"], D["board_x1"], D["board_y0"], D["board_y1"]
    db = box(dx0, dx1, dy0, dy1, D["z_db0"], D["z_db1"])
    for x, y in D["standoff_xy"]:
        db -= cyl(D["drill_m2"], D["z_db0"] - 0.1, D["z_db1"] + 0.1, x, y)
    for x, y in D["springs"]:
        db -= cyl(D["spr_bore"], D["z_db0"] - 0.1, D["z_db1"] + 0.1, x, y)
    if D["fpc_to_db"] and D["tab_x1"] > dx1:   # v0.5 tab past the +x standoffs for the screen socket (v0.7: inside the top board)
        db += box(dx1 - 0.01, D["tab_x1"], -D["tab_hy"], D["tab_hy"], D["z_db0"], D["z_db1"])
    for x, y in D.get("access_xy", []):   # [Ed 13:23] press-spring grub access
        db -= cyl(D["grub_access_d"], D["z_db0"] - 0.1, D["z_db1"] + 0.1, x, y)
    db = top_board_notches(D, db)
    out[db_name(D) if D["base"] == "case" else "joystick daughterboard"] = db
    if D.get("top_joint") == "sockets":   # v0.8 [Ed 13:46]: SMT sockets under the top board, a hole for each male pin
        S = D["tb_sock"]; ys0, ys1 = D["sock_y"]
        for sx, tag in ((-1, "L"), (1, "R")):
            x = sx * D["vb_pin_x"]
            sk = box(x - S["w"] / 2, x + S["w"] / 2, ys0, ys1, D["z_sock0"], D["z_db0"] - 0.01)
            for y in D["sock_pin_y"]:
                sk -= cyl(0.7, D["z_sock0"] - 0.05, D["z_sock0"] + S["ins"][1] + 0.05, x, y)
            out[SK_NAME.format(tag, S["n"])] = sk
    hw, hh, ht = D["hdr_len"], D["hdr_wid"], D["hdr"]["ins"]
    pin_d = D["pitch"] * 0.25
    wall = D["part_gap"]
    rows = D["hdr"].get("rows", 1)
    tag = f"{rows}x{D['hdr']['n']}"
    for i, (x, y) in enumerate(D["hdr_xy"]):
        out[f"header {tag} long pin {i + 1} (underside)"] = cbox(hw, hh, D["z_db0"] - ht, D["z_db0"], x, y)
        sock = cbox(hw, hh, 0, D["sock"]["h"], x, y)
        sock -= cbox(hw - 2 * wall, hh - 2 * wall, D["sock"]["h"] - D["mate_in"] - wall, D["sock"]["h"] + 0.02, x, y)
        out[f"socket {tag} H11 {i + 1} (main PCB)"] = sock
        z_tip = D["z_db0"] - ht - D["hdr"]["mate"]
        for j, (dx, dy) in enumerate(D["hdr_pins"]):
            out[f"header pin {i + 1}.{j + 1}"] = cyl(pin_d, z_tip, D["z_db0"] - ht, x + dx, y + dy)
    for i, (x, y) in enumerate(D["standoff_xy"]):
        # round female-female body. The screws are slip-fit solids; the real thread is in the pillar.
        body = cyl(D["standoff_d"], 0.02, D["z_db0"] - 0.02, x, y)
        out[f"brass standoff M2x{D['riser_h']:.0f} {i + 1}"] = body
        head_b = cyl(D["shcs"]["head_d"], D["z_head_bot0"], D["z_head_bot1"], x, y)
        shaft_b = cyl(D["screw_d_model"], D["z_head_bot1"], -0.02, x, y)
        out[f"M2 socket screw bottom {i + 1}"] = head_b + shaft_b
        head_t = cyl(D["shcs"]["head_d"], D["z_head_top0"], D["z_head_top1"], x, y)
        shaft_t = cyl(D["screw_d_model"], D["z_db0"] + 0.05, D["z_head_top0"], x, y)
        out[f"M2 socket screw top {i + 1}"] = head_t + shaft_t
    body, stem = switch(D)
    out["SW1 SKRHADE010 body (45°)"] = body
    out["SW1 SKRHADE010 stem"] = stem
    if D["base"] == "case":   # v0.7 [Ed 3 Nov]
        out[cc_name(D)] = case_cradle(D)
        if not D.get("cradle_in_case"):   # v0.9 [Ed 18:35]: one print, no bead
            out[gk_name(D)] = cradle_gasket(D)
    elif D["base"] == "cradle":
        out["joystick cradle (printed, glued)"] = cradle(D)
        pin = D["cradle"]["pin"]
        for i, (x, y) in enumerate(D["cr_pins"]):
            out[f"cradle locating dowel {i + 1}"] = cyl(pin["d"] - 0.05, -pin["in_pcb"] + 0.01, pin["len"] - pin["in_pcb"], x, y)
    else:
        out["seat plate (printed, glued)"] = plate(D)
    for i, (x, y) in enumerate(D["balls"]):
        out[f"ball {i + 1} Ø{D['ball_d']:g} stainless"] = Pos(x, y, D["z_ball"]) * Sphere(D["ball_d"] / 2)
    out["joystick carrier (printed)"] = carrier(D)
    out["screen carrier (printed)"] = screen_carrier(D)
    for i, (x, y) in enumerate(D["cs_xy"]):
        out[f"brass insert {i + 1}"] = insert(D, x, y)
        out[f"grub screw {i + 1}"] = cyl(D["grub_d_model"], D["z_tip"] - D["grub"]["length"], D["z_tip"], x, y)
        out[f"compression spring {i + 1}"] = cyl(D["cs"]["od"], D["z_tip"] + 0.02, D["z_roof"] - 0.02, x, y)
    S = D["scr"]
    glass = cbox(S["w"], S["h"], D["z_scr0"] + 0.02, D["scr_top"])
    if D["z_roof"] >= D["z_scr0"] - 1e-6:   # v0.4: the spring pads stood level with the glass underside
        for x, y in D["cs_xy"]:
            glass -= cyl(2 * D["cs_bore_r"] + 1.4, D["z_scr0"] - 0.05, D["z_roof"] + 0.05, x, y)
    for n, x0, x1, y0, y1, d in D.get("scr_back", ()):   # v0.6 [S] the FMST02's back (folded flex, parts, connector plate, B2B header)
        glass += box(x0, x1, y0, y1, D["z_scr0"] - d, D["z_scr0"] + 0.03)
    out["top screen " + S["part"]] = glass
    t = D["fpc_t"]
    fx = D["fpc_x"]
    z_run = D["z_scr0"] - 0.55 + D["tol_mjf"]
    if D.get("back_pk") and "win_x" in D:
        # v0.6 foam pads: under every part of the panel's back except the connector (windowed), so a press anywhere on the glass
        # goes through the panel's back into the roof, never through a part into a pocket floor. Each pad is cut round anything
        # deeper; 0.01 short of the panel so the model shows no overlap.
        win = set(D["scr_window"]); pad = None
        feats = [b_ for b_ in D["scr_back"] if b_[0] not in win]
        for n, x0, x1, y0, y1, d in feats:
            z1 = D["z_scr0"] - d - 0.01
            p_ = box(x0, x1, y0, y1, z1 - D["foam_t"] + 0.01, z1)
            for m, a0, a1, b0, b1, dd in D["back_pk"]:
                if dd - D["back_clear"] > d + 1e-6 or (m in win):
                    p_ -= box(a0, a1, b0, b1, z1 - 2.0, z1 + 0.1)
            pad = p_ if pad is None else pad + p_
        out[f"screen foam pads {D['foam_t']:g} (foam tape) [A]"] = pad
        # v0.6 [Ed 16:22] the custom jumper: socket on the panel header, flex on a stiffener, run under the roof, drop, plug
        sl_, ss_, sz_ = D["db_fpc_sock"]; stw, stt = D["jmp_stiff"]; jx = D["jmp_x"]
        hdr = next(b_ for b_ in D["scr_back"] if b_[0] == "B2B header")
        out["screen jumper B2B socket (top, on the panel header) [A]"] = (
            box(jx - ss_ / 2, jx + ss_ / 2, -sl_ / 2, sl_ / 2, D["z_js0"], D["z_js1"])
            - box(hdr[1] - 0.02, hdr[2] + 0.02, hdr[3] - 0.02, hdr[4] + 0.02, D["z_scr0"] - hdr[5] - 0.02, D["z_js1"] + 0.1))   # the plug sits in it
        sx = D["db_sock_x"]; z_db_top = D["z_db1"]; zr = D["z_run"]; hw = D["fpc_w"] / 2
        xe = jx + stw / 2; t = D["jmp_t"]
        xv, y2, y3, xa, xb = D["jmp_xv"], D["jmp_y2"], D["jmp_y3"], D["jmp_xa"], D["jmp_xb"]
        zb, zt = D["z_leg"]; zp = z_db_top + sz_ + 0.3                                      # plug flex top
        out["screen FPC socket AXE530127 (daughterboard)"] = box(sx - ss_ / 2, sx + ss_ / 2, -sl_ / 2, sl_ / 2, z_db_top + 0.02, z_db_top + sz_)
        out["screen jumper FPC [A]"] = (   # [Ed 17:16] 3 mm, 13 lines, a loose loop under the carrier (legs as envelopes)
            box(jx - stw / 2, xe, -sl_ / 2, sl_ / 2, D["z_jst0"], D["z_js0"])               # flex + stiffener under the socket
            + box(xe - t, xe, -hw, hw, min(zr, D["z_jst0"]), D["z_js0"])                     # step down out of the window
            + box(xe - t, xv + t / 2, -hw, hw, zr, zr + t)                                    # R: under the roof (takes the press)
            + box(xv - t / 2, xv + t / 2, -hw, hw, zt, zr + t)                                # V1: down the carrier slot (x)
            + box(xv - t / 2, xv + t / 2, y2 - t / 2, hw, zb, zt)                              # S1: on edge along y (x)
            + box(xa, xv + t / 2, y2 - t / 2, y2 + t / 2, zb, zt)                              # S2: on edge along -x (y)
            + box(xa - t, xa, y2 - t / 2, y3 + t / 2, zb, zt)                                  # 180° crease
            + box(xa - t / 2, xb, y3 - t / 2, y3 + t / 2, zb, zt)                              # S3: on edge back along +x (y)
            + box(xb, xb + t, y3 - t / 2, y3 + t / 2, zp, zt)                                  # down to the plug
            + box(xb, sx - stw / 2 + 0.01, y3 - hw, y3 + hw, zp, zp + t))                       # onto the plug end
        out["screen jumper plug end (bottom, in the daughterboard socket) [A]"] = box(
            sx - stw / 2, sx + stw / 2, -sl_ / 2, sl_ / 2, z_db_top + sz_ + 0.02, z_db_top + sz_ + 0.3 - 0.01)
    elif D["fpc_to_db"]:
        # [Ed] 2 Nov: short jumper flex from the screen edge down to a socket on the daughterboard (service loop not drawn)
        sx = D["db_sock_x"]; sl_, ss_, sz_ = D["db_fpc_sock"]   # v0.5: long side along y (the flex width)
        z_db_top = D["z_db1"]
        z_run = D["z_scr0"] - 0.35   # v0.5: the run under the glass sits in the roof slot
        out["screen FPC socket AXE530127 (daughterboard)"] = box(sx - ss_ / 2, sx + ss_ / 2, -sl_ / 2, sl_ / 2, z_db_top + 0.02, z_db_top + sz_)
        out["screen jumper FPC [A]"] = (
            box(fx - t / 2, fx + t / 2, -D["fpc_w"] / 2, D["fpc_w"] / 2, z_db_top + sz_ + 0.3, z_run + t)
            + box(min(fx, S["w"] / 2 - 0.4) - t / 2, max(fx, S["w"] / 2 - 0.2), -D["fpc_w"] / 2, D["fpc_w"] / 2, z_run, z_run + t)
            + box(sx, fx + t / 2, -D["fpc_w"] / 2, D["fpc_w"] / 2, z_db_top + sz_ + 0.3, z_db_top + sz_ + 0.3 + t))
    else:
        out["screen FPC [A]"] = (
            box(fx - t / 2, fx + t / 2, -D["fpc_w"] / 2, D["fpc_w"] / 2, -D["pcb_t"] - 3.0, z_run + t)
            + box(min(fx, S["w"] / 2 - 0.4) - t / 2, max(fx, S["w"] / 2 - 0.2), -D["fpc_w"] / 2, D["fpc_w"] / 2, z_run, z_run + t)
        )
    out["rear spring anchor (printed)"] = rear_anchor(D)
    if D.get("cup_in_bezel"):   # v0.8: cushion rings glued under the carrier guide bosses (the head meets them when the bezel lifts)
        U = D["upstop"]
        for i, (x, y) in enumerate(D["g_xy"]):
            out[US_NAME.format(i + 1, U["part"].split(" ring")[0])] = (cyl(U["od"], D["g_boss0"] - U["t"], D["g_boss0"] - 0.01, x, y)
                                                                     - cyl(U["id"], D["g_boss0"] - U["t"] - 0.1, D["g_boss0"], x, y))
    if "peg" in D:
        pi = D["peg"]["ins"]
        out[f"press peg grub (ISO 4026 M2x{D['p_len']:.0f})"] = cyl(1.5, D["z_peg"], D["p_top"])
        out["press peg insert (brass, bezel roof)"] = (cyl(pi["od"] - 0.30, D["p_ins_bot"] + 0.01, D["p_ins_top"] - 0.01)
                                                        - cyl(1.70, D["p_ins_bot"], D["p_ins_top"]))
    G = D["guide"]; gi = G["ins"]
    for i, (x, y) in enumerate(D["g_xy"]):   # v0.5 guides: head under the carrier boss is the up-stop
        out[f"guide screw {i + 1} (ISO 7984 M2x{D['g_len']:.0f})"] = (cyl(G["head_d"], D["g_head0"], D["g_z0"] - 0.01, x, y)
                                                                    + cyl(1.5, D["g_z0"] - 0.02, D["g_tip"], x, y))
        out[f"guide sleeve {i + 1} (brass tube)"] = (cyl(G["sleeve_od"], D["g_z0"] + 0.01, D["g_ins_bot"] - 0.01, x, y)
                                                     - cyl(2.1, D["g_z0"], D["g_ins_bot"], x, y))
        out[f"guide insert {i + 1} (brass, bezel roof)"] = (cyl(gi["od"] - 0.30, D["g_ins_bot"] + 0.01, D["g_ins_top"] - 0.01, x, y)
                                                            - cyl(1.70, D["g_ins_bot"], D["g_ins_top"], x, y))
    for i, y in enumerate(D["pin_y"]):
        out[f"cross pin {i + 1}"] = cross_pin(D, y)
    for i, (x, y) in enumerate(D["springs"]):
        out[f"hold-down spring {i + 1}"] = hold_down(D, x, y)
    return out
