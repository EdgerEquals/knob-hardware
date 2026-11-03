"""Real colours, by material (v0.19b, 2 Nov). One table for the renders, the section sheet and the exported models.

The material comes from export_parts.classify (the BOM rules), refined by name where the BOM material is generic
(a board vs the black parts on it, brass vs steel hardware, glass vs steel balls). Joystick parts carry a "joystick: " prefix.
"""
from .export_parts import classify

# key: (legend, colour, see-through)
MATERIALS = {
    "clear":   ("UTR-8100 clear resin (SLA)", "#d4ecf2", True),
    "glass":   ("borosilicate glass, glass spacer balls", "#eaf6fa", True),
    "oled":    ("clear OLED (transparent)", "#b9d4de", True),
    "pa12":    ("PA-12, MJF (natural grey)", "#6e7377", False),
    "petg":    ("PETG, opaque (seal ring)", "#2b3035", False),
    "asacf":   ("ASA-CF, black (back cover, screen pad)", "#1f2124", False),
    "nylon":   ("nylon pinion (natural)", "#e8e1cf", False),
    "steel":   ("stainless steel: screws, shafts, balls, springs, bearings, USB-C shell", "#a9b0b6", False),
    "brass":   ("brass: tube, inserts, standoffs; ENIG pad", "#c9a227", False),
    "magnet":  ("N52 magnets, nickel-plated", "#c3c8cd", False),
    "ruby":    ("synthetic ruby accent balls", "#9b1b30", False),
    "motor":   ("motor cans (steel)", "#8f969c", False),
    "pcb":     ("PCBs, green solder mask", "#1e6b35", False),
    "ic":      ("ICs, sensors, headers, switch, passives (black)", "#1c1c1c", False),
    "led":     ("VCSEL / RGB LED packages (white)", "#f1f0ea", False),
    "display": ("AMOLEDs and joystick screen (black glass)", "#0e1013", False),
    "flex":    ("flex circuits (polyimide amber)", "#c98a1b", False),
    "jack":    ("PJ366ST jacks (black body)", "#262626", False),
    "glow":    ("Shimicoat glow coat", "#d7efae", False),
    "silicone": ("silicone O-ring (black)", "#141414", False),
    "foam":    ("foam tape pads (black)", "#3a3a3a", False),
    "gasket":  ("silicone sponge gasket (grey)", "#8a8f94", False),
    "other":   ("unassigned (check the material rules)", "#ff00ff", False),
}


def key(name):
    n = name[len("joystick: "):] if name.startswith("joystick: ") else name
    low = n.lower()
    # name overrides first: places where the BOM material string is generic or the part is a sub-feature
    if "o-ring" in low: return "silicone"
    if "foam pad" in low: return "foam"                       # v0.6 joystick screen pads
    if "gasket" in low: return "gasket"                       # v0.23 joystick cradle gasket
    if low.startswith("vertical board") and ("header" in low or "spring contacts" in low): return "ic"   # v0.23 (contacts: black body)
    if low.startswith("vertical board") and "fr4" in low or "top board" in low: return "pcb"           # v0.23 boards
    if low.startswith("mcu "): return "ic"                     # [Ed 18:34] H7B0 LQFP100 on the main PCB back
    if "jumper" in low and ("b2b socket" in low or "plug end" in low): return "ic"   # v0.6 jumper connectors
    if "seal ring" in low: return "petg"
    if "clear oled" in low: return "oled"
    if "ruby" in low: return "ruby"
    if "glass" in low and "ball" in low: return "glass"
    if "nylon" in low: return "nylon"
    if "rod pad" in low: return "brass"
    if "spring" in low: return "steel"                       # 'non-magnetic' springs must not read as magnets
    if "socket" in low and "fpc" in low: return "ic"           # FPC socket on the joystick board
    if low.startswith("jack ") and ("bushing" in low or "nut" in low): return "steel"
    if low.startswith("pcb back parts"): return "ic"
    if "daughterboard" in low or low == "pcb" or low.startswith("adapter board") or "pd board" in low: return "pcb"
    if low.startswith(("hall sensor", "encoder sensor", "dial tmag", "adapter part")) or "header" in low or low.startswith("sw1") or (low.startswith("socket ") and "h11" in low):
        return "ic"
    if low.startswith("emitter "): return "led"
    if low.startswith(("jack ", "pj366st")) or "bushing" in low: return "jack"
    if "usb-c" in low: return "steel"
    if any(k in low for k in ("fpc", "jumper", "b2b")) or "strap" in low and "saddle" not in low: return "flex"
    if "amoled" in low or "dwo" in low or (low.startswith("screen ") and low.endswith(" panel")): return "display"
    if "glow coat" in low: return "glow"
    _, mat, _ = classify(n)
    m = mat.lower()
    if "utr-8100" in m: return "clear"
    if "pa-12" in m: return "pa12"
    if "asa-cf" in m: return "asacf"
    if "petg" in m: return "petg"
    if "borosilicate" in m: return "glass"
    if m == "display": return "display"
    if "fr-4" in m: return "pcb"
    if "pcba parts" in m or "encoder daughterboard" in m: return "ic"
    if "vcsel" in m: return "led"
    if "brass" in m and "steel" not in m: return "brass"
    if "steel / brass hardware" in m: return "brass" if ("brass" in low or "insert" in low or "standoff" in low) else "steel"
    if "n52" in m: return "magnet"
    if "flex" in m: return "flex"
    if m == "motor": return "motor"
    if "bearing" in m or "spring" in m or "dowel" in m or "balls" in m: return "steel"
    if "pj366st" in m: return "jack"
    if "shimicoat" in m: return "glow"
    return "other"


def colour(name):
    return MATERIALS[key(name)][1]


def legend(name):
    return MATERIALS[key(name)][0]


def see_through(name):
    return MATERIALS[key(name)][2]


def groups():
    """render.GROUPS-style list: (legend, colour, match), one per material, 'other' last (the fallback)."""
    out = []
    for k, (leg, col, _) in MATERIALS.items():
        if k == "other":
            continue
        out.append((leg, col, (lambda kk: (lambda n: key(n) == kk))(k)))
    leg, col, _ = MATERIALS["other"]
    out.append((leg, col, lambda n: True))
    return out
