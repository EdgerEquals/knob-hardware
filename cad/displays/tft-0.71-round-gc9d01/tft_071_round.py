"""0.71" round IPS TFT, 160x160, GC9D01N driver (the centre-button screen), v0.1 2026-10-31.
Note: the 0.71" round panel uses the GC9D01; the GC9A01 is the 1.28" 240x240 panel.
Source [S]: Shenzhen Zhunyi Technology, spec Z07101-P14-G9DN-Y1 V1.0 (2024-12-13), mechanical drawing p.5,
  https://www.panelook.cn/upload/product/258253/202502242704.pdf
  cross-checked: EastRising ER-TFT0.71-2 (20.12 x 22.30 x 1.8, AA 18.0) buydisplay.com; SWICN LB071R-PF01 (1.86 thick, 10-pin ZIF 0.5 pitch).
Modelled as glass (LCD) on a backing (backlight), round with the COG ledge toward +Y, FPC tail folded behind.
Local frame: screen axis Z, backing bottom at Z = 0, glass top at Z = t_total; tail exits the ledge edge (+Y)."""
import os, sys
from build123d import *
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(LIB, "tools"))

P = dict(
    bl_d=20.12,          # [S] backlight (outer) round Ø20.12 ±0.1  = the "glass OD" used for the holder
    bl_len=22.30,        # [S] overall incl. the COG ledge, 22.30 ±0.15
    lcd_d=19.90,         # [S] LCD glass Ø19.9 ±0.1
    lcd_len=22.05,       # [S] LCD glass incl. ledge, 22.05 ±0.1
    aa_d=18.00,          # [S] active area Ø18
    t_total=1.90,        # [S] LCM 1.90 ±0.2 (EastRising 1.8, SWICN 1.86)
    glass_t=1.10,        # [A] LCD glass + polariser share of the thickness
    ledge_w=12.0,        # [A] width of the COG ledge (not dimensioned in the source)
    pins=14,             # [S] Z07101-P14: 14 pins
    pitch=0.5,           # [A] 0.5 (SWICN 10-pin version states 0.5; Zhunyi pitch not stated)
    tail_w=7.50,         # [S] tail width at the contact end
    tail_t=0.30,         # [S] FPC + PI stiffener 0.30 ±0.03
    tail_len_supplied=100.0,   # [S] 100.00 ±0.50 from the module edge (too long here: short-tail variant needed)
    stiffener_len=2.50,  # [S] PI stiffener at the contact end
    fold_drop=0.8,       # [A] default drop below the backing for the folded tail (overridden by the holder)
    tail_end_y=1.8,      # [A] default tail end (y) after folding back under the screen
)
p = P
p["bl_t"] = p["t_total"] - p["glass_t"]
p["y_edge"] = p["bl_len"] - p["bl_d"] / 2          # +12.24: ledge edge (backing) from the round centre
p["y_edge_lcd"] = p["lcd_len"] - p["lcd_d"] / 2    # +12.10
p["tail_drawn"] = None

def _outline(d, y_edge, w, z0, h):
    c = Pos(0, 0, z0) * Cylinder(d / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    r = Pos(0, y_edge / 2, z0) * Box(w, y_edge, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return c + r

def build_screen(p=P):
    backing = _outline(p["bl_d"], p["y_edge"], p["ledge_w"], 0, p["bl_t"])
    glass = _outline(p["lcd_d"], p["y_edge_lcd"], p["ledge_w"] - 0.2, p["bl_t"], p["glass_t"])
    return backing, glass

def build_tail(drop=None, y_end=None, p=P):
    """Tail folded 180° under the screen: down at the ledge edge, then back toward the centre.
    drop = distance from the backing bottom (Z=0) down to the tail's lower face."""
    drop = p["fold_drop"] if drop is None else drop; y_end = p["tail_end_y"] if y_end is None else y_end
    w, t, ye = p["tail_w"], p["tail_t"], p["y_edge"]
    A = (Align.CENTER, Align.MIN, Align.MIN)
    down = Pos(0, ye, -drop) * Box(w, t, drop + 0.2, align=A)          # vertical run (overlaps the backing by 0.2)
    back = Pos(0, y_end, -drop) * Box(w, ye + t - y_end, t, align=A)    # horizontal run back under the screen
    p["tail_drawn"] = (ye - y_end) + drop + 0.2
    return down + back

def active_area(p=P):
    return Pos(0, 0, p["t_total"]) * Cylinder(p["aa_d"] / 2, 0.005, align=(Align.CENTER, Align.CENTER, Align.MAX))

if __name__ == "__main__":
    from sheet import Sheet
    backing, glass = build_screen(); tail = build_tail()
    scr = Compound(children=[backing, glass, tail], label="tft-0.71-round")
    export_step(scr, os.path.join(HERE, "tft-0.71-round-gc9d01.step"))
    R = p["bl_d"] / 2; ye = p["y_edge"]; t = p["t_total"]
    sh = Sheet(scr, gap=26, scale=4, label_pad=14)
    sh.hdim("front", -R, R, -R, -R - 3, f"Ø{p['bl_d']:.2f} backing / glass OD [S]")
    sh.hdim("front", -p["lcd_d"] / 2, p["lcd_d"] / 2, -R, -R - 6, f"Ø{p['lcd_d']:.2f} LCD [S]")
    sh.hdim("front", -p["aa_d"] / 2, p["aa_d"] / 2, 0, 0.5, f"Ø{p['aa_d']:.1f} active area [S]")
    sh.vdim("front", -R, ye, R, R + 3, f"{p['bl_len']:.2f} overall [S]")
    sh.hdim("front", -p["tail_w"] / 2, p["tail_w"] / 2, ye, ye + 3, f"{p['tail_w']:.2f} tail [S], {p['pins']}P, {p['pitch']:.1f} pitch [A]")
    sh.hdim("front", -p["ledge_w"] / 2, p["ledge_w"] / 2, ye - 1, ye + 6, f"{p['ledge_w']:.1f} ledge [A]")
    sh.vdim("plan", 0, t, -R, -R - 3, f"{t:.2f} [S]")
    sh.vdim("plan", p["bl_t"], t, R, R + 3, f"{p['glass_t']:.1f} glass [A]")
    sh.vdim("plan", -p["fold_drop"], 0, p["tail_w"] / 2, R + 7, f"{p['fold_drop']:.1f} tail fold [A]")
    lines = [f"0.71\" round IPS TFT 160x160, GC9D01N (not GC9A01: that is the 1.28\" 240x240)",
             "Source: Zhunyi Z07101-P14-G9DN-Y1 spec p.5 (panelook.cn); EastRising ER-TFT0.71-2; SWICN LB071R-PF01",
             f"Tail {p['tail_w']:.1f} wide × {p['tail_t']:.2f} [S], stiffener {p['stiffener_len']:.1f} [S]; drawn folded behind, {p['tail_drawn']:.1f} long [A]",
             (f"Supplied tail is {p['tail_len_supplied']:.0f} mm long: needs a short-tail variant [check]", dict(color="red", weight="bold"))]
    for i, l in enumerate(["NOTES"] + lines):
        kw = dict(weight="bold") if i == 0 else {}
        if isinstance(l, tuple): l, kw = l
        sh.note("side", sh.bb["side"][1] + 3, R - i * 1.6, l, 8 if i == 0 else 6.5, **kw)
    title = "0.71\" round TFT (GC9D01) — v0.1, 2026-10-31"
    sub = ["Glass on backing, COG ledge toward +Y, tail folded behind.", "[S] = source datasheet, [A] = assumed.", "Third-angle projection · mm · plan view drawn front-up"]
    sh.dxf(os.path.join(HERE, "tft-0.71-round-gc9d01.dxf"), [title] + sub)
    sh.png(os.path.join(HERE, "tft-0.71-round-gc9d01-drawing.png"), title, sub)
    print("ok", backing.is_valid, glass.is_valid, tail.is_valid, p["y_edge"], p["bl_t"], p["tail_drawn"])
