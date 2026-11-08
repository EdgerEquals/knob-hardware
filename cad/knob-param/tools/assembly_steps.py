"""Assembly sequence rules for tools/assembly_anim.py (data only; panel frame: z = 0 is the main-PCB front, +z toward the
faceplate, +y toward the panel top, the knob axis at (0, 0), the joystick axis at (0, 40.63)).

v0.25 (3 Nov evening, dial job): the dial in two parts (lower part before the cap, dish bonded on after the balls), the
detent block from the top with its pins, the cap in two parts (PA-12 hub glued in the clear cap), the cartridge's sideways
magnets and key ribs. v0.24 (3 Nov): layout v4 step 1 + its follow-ups (case cradle with the top board, vertical boards with pins into sockets,
cup in the bezel, no press springs) and the dial bezel cartridge (+4.4). The joystick order is Danny's step-1 proposal (L4
"Open after step 1"): cradle with the top board glued in from the back; carrier and grip block from the front through the
lip ring; then the main board over the hanging hold-down springs, hooks pulled onto the cross pins from behind. The dial
cartridge drops in from the top and plugs in on the way down [Ed 12:31/12:41].

Each step:
  id      short key (unique)
  name    plain words, shown in the captions and the sheet
  parts   regexes (re.search, case-insensitive) on the part name; "exclude" regexes take parts back out
  dir     direction the parts MOVE as they go in ("+z", "-z", "+x", ... or a 3-tuple; normalised)
  travel  mm from the exploded start to home, or "auto" (just clear of everything already placed, by bounding box, + 4 mm)
  note    one line: how it is held (solder / glue / press / screw / clamp / magnet / loose) and the source; [A] = my assumption
  sub     sub-assembly the step builds into (default "main"). A sub is built off to the side (shown at its exploded offset)
          and goes in as one rigid group at its "join" step.
  join    this step moves the whole finished sub-assembly <join> into <sub>
  base    True: the first part of a (sub-)assembly: it does not move relative to that (sub-)assembly
Every part must match exactly one step: `assembly_anim.py seq` lists unassigned and doubly assigned parts.
A step whose regexes match nothing is reported as EMPTY and skipped (placeholders for parts not modelled yet).
Sources: docs/design-notes.md (DN), docs/case-decisions-2026-11-02.md (CD), docs/top-screen-joystick.md (TJ),
docs/layout-v4-2026-11-03.md (L4), knobparam/assembly/export_parts.py (BOM kinds)."""

import math

STEPS = [
    # ------------------------------------------------------------------ main PCB, bench, front face up
    dict(id="pcb", name="Main PCB with its soldered parts (H7B0 on the front)", base=True, dir="+z", travel=10,
         parts=[r"^PCB$", r"^PCB back parts", r"^PCB rod pad", r"^emitter ", r"^power light VCSEL", r"^MCU ", r"^hall sensor ", r"^encoder sensor"],
         note="PCBWay PCBA: 24 upside-down RGB in their cut-outs (v0.52), the red VCSEL power light, Hall row, H743 under the joystick, rod pad, and (v0.49, Q27) the EE-SX1321 on the back; "
              "(Q30) the link flex hot-bar bonded onto the strip, shown with the jack unit (BOM 'board'; L4 step 1)"),
    dict(id="vboards", name="Vertical boards L and R onto the main board (hybrid headers, male pins on top)", dir="-z",
         travel="auto", parts=[r"^vertical board [LR]"],
         note="PCBA: THT legs through the main board, SMT legs over the encoder riser; no standoff (L4 Ed 13:31-13:39)"),
    dict(id="oled", name="Clear OLED onto the PCB front over window D", dir="-z", travel="auto",
         parts=[r"^clear OLED(?! flex)"], note="sits on the 1.6 ledge round window D [A: bonded with a tape ring]; its flex is plugged into the jack unit later (v0.34)"),
    dict(id="back", name="Back-side parts: bearing-2 seat + bearing, joystick spring anchor (+ the encoder riser board with the feel stage)",
         dir="+z", travel="auto",
         parts=[r"^encoder (daughterboard|header)", r"^encoder bearing 2", r"^joystick: rear spring anchor"],
         note="riser on its hybrid 6-pin header, no standoffs (L4 Ed 13:35); bearing-2 seat glued, bearing pressed; anchor glued (TJ)"),
    # ------------------------------------------------------------------ base drive
    dict(id="cradle", name="Base cradle + brass centre tube onto the PCB", dir="-z", travel="auto",
         parts=[r"^base cradle$", r"^brass tube$"],
         note="cradle glued to the PCB [A]; brass tube in the cradle's square flange, bonded (DN)"),
    dict(id="motor", name="1220 main motor (pinion on) down through the cradle", dir="-z", travel="auto",
         parts=[r"^motor$", r"^pinion$"],
         note="tabs soldered from the PCB back (DN); pinion pressed on the shaft first [A]"),
    dict(id="enc-b1", name="Encoder bearing 1 into the cradle + PCB bore", dir="-z", travel="auto",
         parts=[r"^encoder bearing 1"], note="pressed [A]"),
    dict(id="pedestal", name="Detent train: pedestal grub, pedestal block, train balls", dir="-z", travel="auto",
         parts=[r"^detent pedestal grub", r"^detent train pedestal", r"^track \d+ (separator )?ball"],
         note="grub from the top down the pocket, then the block, then the Ø1/Ø0.8/Ø1 train (CD 15:50); loose till the dial. "
              "v0.25: the detent boss is no longer printed over the pocket, so it is open from the top [Ed 18:15]"),
    dict(id="thrust", name="Outer thrust ring: load balls, glass spacers, rubies", dir="-z", travel="auto",
         parts=[r"^outer thrust"], note="loose in the cradle race, cageless closed ring (CD)"),
    # ------------------------------------------------------------------ knob base and the herringbone stage
    dict(id="pinions", name="Idler pins + pinions and encoder shaft + pinion (caps on)", dir="-z", travel="auto",
         parts=[r"^idler pin \d", r"^idler pinion \d", r"^encoder (shaft|pinion)"],
         note="v0.25: in before the ring (spur teeth; the ring comes down over them); shaft through both bearings; Fresnel caps glued on (DN)"),
    dict(id="back2", name="Back: feel compound gear on idler pin 1", dir="+z", travel="auto",
         parts=[r"^feel compound gear"], note="pressed / glued on the pin end [A]"),
    dict(id="feel", name="716 feel motor in its open saddle (seat first), shaft down through the PCB", dir="-z", travel="auto",
         parts=[r"^feel motor (coreless|shaft|saddle seat)"],
         note="saddle seat glued on the cradle rib [A]; motor inverted, shaft down (DN)"),
    dict(id="feel-strap", name="Saddle strap + M1 screw round the 716", dir=(-0.868, -0.496, 0.0), travel=12,
         parts=[r"^feel motor saddle (strap|screw)"], note="C-band strap from the outboard side, M1 screw (DN); direction radial [A]",
         expect=[(r"saddle screw", r"saddle seat", "thread", "the M1 screw cuts its thread in the printed seat")]),
    dict(id="feel-pin", name="Back: printed 11T pinion + cap onto the 716 shaft", dir="+z", travel="auto",
         parts=[r"^feel motor pinion"], note="pressed on the shaft [A]; meshes the compound gear (v0.25: 39T)"),
    dict(id="ring-lo", name="Knob base: lower-cap land + one-piece ring down over the pinions", dir="-z", travel="auto",
         parts=[r"^knob lower-cap land", r"^bottom internal ring( \(lower half\))?$"],
         note="land and ring glued as one [A]; rides on the thrust balls. v0.25 [Ed 19:00]: one-piece spur ring (v0.24: the lower half of the split herringbone). v0.25 order: after the pinions and the 716 strap: the ring's top lip overhangs the pinions (they cannot drop in past it) and the strap comes in sideways across the ring's height"),
    dict(id="glass", name="Borosilicate glass sleeve into the land", dir="-z", travel="auto",
         parts=[r"^knob glass sleeve"], note="glued; caps printed to the measured tube (CD)"),
    # ------------------------------------------------------------------ v0.25 [Ed 18:12-19:46]: the dial's lower part goes in first
    # (built off to the side), then the anchor pins, the detent block and the cap; the balls; the dish is bonded on last.
    dict(id="es-pins", name="Two steel hook pins pressed into the tops of the cradle's spring posts", dir="-z", travel=4,
         parts=[r"^spring anchor pin"], note="v0.31 [Ed 4 Nov 16:35]: the posts are printed up from the cradle plate (150° and 310°)",
         expect=[(r"^spring anchor pin", r"^base cradle$", "press", "pressed into the posts")]),
    dict(id="dial", sub="dial", base=True, name="Control dial lower part (tube, Hall and detent spokes; v0.31: column on the Hall arm, no lever)",
         parts=[r"^control dial lower part"], note="MJF PA-12; the dial is two parts since v0.25 [Ed 18:12]"),
    dict(id="dial-hall", sub="dial", name="Five Hall magnets into the Hall bar (from below)", dir="+z", travel=8,
         parts=[r"^hall magnet \d"], note="pressed, poles N/S/N/S/N face down (DN)"),
    dict(id="dial-pin", sub="dial", name="Steel spring pin pressed into the top of the Hall arm's column", dir="-z", travel=4,
         parts=[r"^spring pin on the Hall arm's column"], note="v0.31 [Ed 4 Nov 16:35]: the springs hook onto it later, from above",
         expect=[(r"^spring pin on", r"^control dial lower part", "press", "pressed into the column")]),
    dict(id="dial-in", join="dial", name="Dial lower part down through the glass and the ring, flange onto the train", dir="-z",
         travel="auto", note="tube over the brass tube, Hall bar down the cradle slot; nothing of the cap or the detent boss is there yet"),
    dict(id="dt-pins", name="Two Ø1 locating pins for the detent block pressed into the plate", dir="-z", travel="auto",
         parts=[r"^detent block locating pin"], note="pressed [A]; the block's seat is glued over them [Ed 18:15 fallback: no room for a screw]"),
    dict(id="dblock", sub="detent block", base=True, name="Detent block (UTR-8100: wall, head, boss)",
         parts=[r"^detent block \("], note="SLA, one print [Ed 18:15]"),
    dict(id="dblock-det", sub="detent block", name="Ball, spring, grub down the block's bore (grease holds the ball)", dir="-z",
         travel=6, parts=[r"^detent \d+ (ball|spring|grub)"],
         note="grub sets the preload (DN, CD v0.22); a lip cannot hold the ball: it must hang 0.15 below the boss to latch [A: grease]"),
    dict(id="dblock-in", join="detent block", name="Detent block down onto its seat over the two pins, glued (ball onto the flange)",
         dir="-z", travel="auto", note="after the pedestal, the train and the dial's lower part, before the cap [Ed 18:15]; epoxy on the flat seat [A]. "
         ""),
    dict(id="springs", name="Two extension centring springs hooked from the column's pin to the posts' pins, from above", dir="-z",
         travel=6, parts=[r"^centring spring"], note="v0.31 [Ed 4 Nov 16:35]: at z 15, over the detent block's top; the knob is open at the "
         "top until the cap goes on", expect=[(r"^centring spring", r"^spring (anchor )?pin", "hook", "hooked on the pins")]),
    dict(id="cap", sub="cap", base=True, name="Knob upper-cap, clear UTR-8100 part (web, plug, glass seat)",
         parts=[r"^knob upper-cap \(clear"], note="SLA, clear [Ed 19:00]"),
    dict(id="cap-hub", sub="cap", name="PA-12 hub (hub-gear teeth + 45° race) down into the clear part, keyed and glued", dir="-z", travel=8,
         parts=[r"^knob upper-cap hub"], note="teeth first down the clear bore; six keys in the slots, its rim on the clear ledge [Ed 19:46]; "
                                               "bond 0.10 / 0.05 [A]"),
    dict(id="cap-in", join="cap", name="Upper cap down over the dial tube into the glass top (hub gear onto the 1220 pinion)",
         dir="-z", travel="auto", note="bore Ø8.62 over the Ø8.12 tube [Ed 18:12]; plug + 45° seat glued on the ground inner chamfer (CD)"),
    dict(id="kballs", name="53 x Ø1 race balls onto the cap's 45° cone (PA-12 hub)", dir="-z", travel="auto",
         parts=[r"^knob balls"], note="loose; held by the dial race above (CD v0.21); they roll on PA-12, not resin [Ed 19:46]",
         expect=[(r"^knob balls", r"upper-cap", "seat", "0.04 mm³ only in the last 0.25 mm: seated on the 45° cone")]),
    dict(id="dish", sub="dish", base=True, name="Control dial dish (top, race, pocket, land, key slots)",
         parts=[r"^control dial dish"], note="MJF PA-12 [Ed 18:12]"),
    # six pairs at 0/30/120/150/240/270° since v0.27 [Ed 4 Nov 11:46]; each magnet goes in radially, so dir is the radial at its angle
    *[dict(id=f"dish-mag-{a}", sub="dish", name=f"Dial-wall magnet at {a}° pressed sideways into the dish's outer wall (facing out)",
           dir=(-round(math.cos(math.radians(a)), 3), -round(math.sin(math.radians(a)), 3), 0.0), travel=5,
           parts=[rf"^cartridge magnet .*\(dial wall.* {a}°$"],
           note="Ø1x0.5 N52 [A], glued; poles attract its bezel partner (L4 v0.27, Ed 4 Nov 11:46)")
      for a in (0, 30, 120, 150, 240, 270)],
    dict(id="dish-in", join="dish", name="Dial dish bonded onto the tube end (socket over the tube, flat keyed), seated on the balls",
         dir="-z", travel="auto", note="epoxy in the socket [A]; the race centres the dish, the bond takes up the train-vs-race height [Ed 18:12]",
         expect=[(r"^control dial dish", r"^knob balls", "seat", "0.04 mm³ only in the last 0.25 mm: the dish's race groove seats on the balls")]),
    dict(id="sleeve", name="Insulating sleeve down the brass tube", dir="-z", travel="auto",
         parts=[r"^rod sleeve"], note="before the rod-link board: the board's hole passes the rod, not the sleeve"),
    dict(id="rodlink", name="Rod-link board onto the brass tube top (in the dial well)", dir="-z", travel="auto",
         parts=[r"^rod-link board"], note="Ø12 × 1.0, replaces the Ø15.5 adapter; it is the dial up-stop (L4 dial cartridge)"),
    dict(id="rod", name="Centre bolt: rod down the sleeve, top nut on the rod-link board", dir="-z", travel="auto",
         parts=[r"^rod (M1\.6|nut top)"], note="down the brass tube and through the PCB (DN)"),
    dict(id="rod-nut", name="Back: bottom rod nut onto the VBUS pad", dir="+z", travel="auto",
         parts=[r"^rod nut bottom"], note="clamps rod-link board -> tube -> PCB, straight onto the B.Cu pad, no washer (DN)"),
    dict(id="disc", name="Back: encoder disc on its shaft (after the rod nut: it covers it)", dir="+z",
         travel="auto", parts=[r"^encoder disc"], note="pressed / glued on the shaft end [A]; rim into the EE-SX1321 slot"),
    dict(id="dialboard", name="Dial board PCBA (ESP32 underneath) into the dial top, strap loop to the rod-link board",
         dir="-z", travel="auto", parts=[r"^dial board", r"^dial strap loop"],
         note="board on the 55.1 ledge, lobe in the land cut; strap soldered on the board, its free end to the rod-link board [A]"),
    # ------------------------------------------------------------------ front shell (built off to the side)
    # v0.34 [Ed 4 Nov 22:21] step 2, decision 4, option 1A: the jack unit rides in with the board stack (both flexes plugged on the bench)
    dict(id="jack-unit", name="Jack unit (jacks, jack board, power board and lower board on their headers) onto its two posts on the main "
         "board's bottom strip; the clear OLED's flex and the link flex plugged into its ZIFs", dir="-z", travel="auto",
         parts=[r"^jack \d PJ366ST", r"^jack \d bushing", r"^jack board", r"^jack power board", r"^jack lower board", r"^jack unit post",
                r"^USB spring contact", r"^clear OLED flex", r"^link flex"],
         note="on the bench, everything in reach; the link flex (bonded to the main board, Q30) plugged into the unit's FH26W with the "
              "unit tilted at the board's edge, then the unit swung down; the posts (15 V, GND) soldered at both ends; the Ø6.6 jack holes "
              "give the bushings ±0.3 (L4 step 2, Ed 4 Nov 22:21, 22:52; 7 Nov Q30)"),
    dict(id="shell", sub="shell", base=True, name="Front shell (clear UTR-8100) with its glow coat",
         parts=[r"^case$", r"^glow coat"], note="SLA, front face polished; Shimicoat brushed inside (CD)"),
    dict(id="shell-ins", sub="shell", name="Corner brass inserts into the shell's corner posts", dir="+z", travel=8,
         parts=[r"^corner insert"], note="epoxied in the resin (CD)"),
    dict(id="shell-usb", sub="shell", name="USB-C board + receptacle slid in from behind along the bottom-wall channel onto its ledge",
         dir="+z", travel="auto", parts=[r"^USB-C board", r"^USB-C receptacle"],
         note="before the board stack: its top 2.4 is inside the box, where the main board sits; its two power wires to the jack unit "
              "(which now comes in with the stack) are decision 5 (L4 step 2, Ed 4 Nov 20:15)"),
    dict(id="shell-usb-key", sub="shell", name="Printed key into the channel behind the USB-C board (the back cover holds it in)",
         dir="+z", travel="auto", parts=[r"^USB-C key"], note="no glue: comes out with the cover off (L4 step 2, option C, Ed 4 Nov 20:15)"),
    dict(id="jcr-tb", sub="shell", name="Top board PCBA (SW1, two 13-way sockets, FPC socket) up from the back, glued under the printed shoulders",
         dir="+z", travel="auto",
         parts=[r"^joystick: joystick top board", r"^joystick: top-board socket", r"^joystick: SW1 ", r"^joystick: screen FPC socket"],
         note="corner notches pass the top corner posts; glue still wet when the board stack goes in, so the pins centre it [A] (L4 v0.25)"),
    dict(id="js-balls", sub="shell", name="Four Ø2 balls into the cradle's ball seats, from the front", dir="-z", travel="auto",
         parts=[r"^joystick: ball \d"], note="loose, held by the carrier and the hold-downs (TJ); dropped through the lip ring [A]"),
    # ---- joystick top (grip block + carrier), on the bench
    dict(id="jt-block", sub="joystick top", base=True, name="Grip block (bezel, cup over the stem) with its roof inserts",
         parts=[r"^joystick: screen carrier \(printed\)", r"^joystick: guide insert"],
         note="heat-set inserts; the cup over the switch stem is printed into the bezel (L4 Ed 13:09)"),
    dict(id="jt-screen", sub="joystick top", name="Jumper on the panel header, foam pads, panel glued on the block",
         dir="-z", travel=10, parts=[r"^joystick: top screen", r"^joystick: screen foam pads", r"^joystick: screen jumper"],
         note="TJ v0.6 order (1)-(2): jumper socket on the panel header, tail down through the roof window, pads, panel glued",
         expect=[(r"screen jumper", r"screen carrier \(printed\)", "flex", "the tail is fed through the roof window, not pushed in bent")]),
    dict(id="jc", sub="joystick carrier", base=True, name="Joystick carrier (no press springs, grubs or inserts)",
         parts=[r"^joystick: joystick carrier"], note="v0.8: the switch's own click is the press (L4 Ed 13:16)"),
    dict(id="jt-carrier", sub="joystick top", join="joystick carrier", name="Carrier up under the block (jumper tail through its slot)",
         dir="+z", travel=10, note="TJ v0.6 order (3)",
         expect=[(r"joystick carrier", r"screen jumper", "flex", "the tail is fed through the slot (joystick model: plug passes with 0.25)")]),
    dict(id="jt-guides", sub="joystick top", name="Up-stop cushions, guide sleeves + M2 low-head screws from below", dir="+z",
         travel=8, parts=[r"^joystick: guide (sleeve|screw)", r"^joystick: guide up-stop cushion"],
         note="screws into the roof inserts; the heads on the HT-870 cushions are the up-stop [A, L4 follow-up 1]"),
    dict(id="jt-hold", sub="joystick top", name="Four hold-down springs hooked to the carrier, hanging", dir="+z", travel=8,
         parts=[r"^joystick: hold-down spring"], note="0.9 N extension springs (CD 13:08); they hang through the cradle as the top goes in"),
    dict(id="js-top", sub="shell", join="joystick top", name="Joystick top (block + carrier) in from the front through the lip ring",
         dir="-z", travel="auto", note="Danny's step-1 order: onto the balls; the jumper plug meets the top-board socket [A: blind]"),
    # ------------------------------------------------------------------ the board stack goes into the shell
    dict(id="shell-on", join="shell", name="Shell + joystick over the board stack (the stack goes in from the back, springs through)", dir="-z",
         travel="auto",
         note="PCB nests in the shell's recess (CD); knob through the faceplate hole; male pins into the top-board sockets (L4 Ed 13:46)"),
    dict(id="jack-nuts", name="Jack nuts from the front (pull the jack unit to the faceplate)", dir="-z", travel=8,
         parts=[r"^jack \d nut"], note="threaded on the bushings (v0.34: after the shell, the jack unit came in with the stack)"),
    dict(id="js-pins", name="Back: two cross pins through the spring anchor, hooks pulled on", dir="-x", travel="auto",
         parts=[r"^joystick: cross pin"], note="hook the springs' lower ends behind the PCB (CD); slide-in direction [A]"),
    dict(id="oring", name="Drip O-ring stretched over the dial onto the glass", dir="-z", travel="auto",
         parts=[r"^knob drip O-ring"], note="40 x 1 silicone, ~5% stretch, a dab of RTV, no contact with the case (CD)"),
    # ------------------------------------------------------------------ dial screen bezel cartridge (built off to the side)
    dict(id="cart", sub="cartridge", base=True, name="Dial bezel (printed ring, the whole outside of the dial top)",
         parts=[r"^dial bezel"], note="MJF PA-12, dyed black [A] (L4 dial cartridge, Ed 12:41)"),
    *[dict(id=f"cart-mag-{a}", sub="cartridge", name=f"Bezel magnet at {a}° pressed sideways into the skirt from the bore (facing in)",
           dir=(round(math.cos(math.radians(a)), 3), round(math.sin(math.radians(a)), 3), 0.0), travel=6,
           parts=[rf"^cartridge magnet .*\(bezel skirt.* {a}°$"],
           expect=[(r"^cartridge magnet .*bezel skirt", r"^dial bezel", "inside", "put in the bore, then pressed out into its pocket: a straight line from outside the bezel crosses its far wall")],
           note="Ø1x0.5 N52 [A], glued; 0.3 above its dial-wall partner, attracting: pulls the cartridge down (L4 v0.27, Ed 4 Nov 11:46)")
      for a in (0, 30, 120, 150, 240, 270)],
    dict(id="cart-panel", sub="cartridge", name="Glass + panel (Waveshare Z132A2441) glued up into the bezel from underneath",
         dir="+z", travel=10, parts=[r"^dial screen Z132A2441"],
         note="lens laps the bezel's 0.55 step; tail folded under, plug faces down (L4 Ed 12:41); v0.25: nothing inside r 18.5 below the glass"),
    dict(id="cart-pad", sub="cartridge", name="Printed plug pad + arm under the plug", dir="+z", travel=6,
         parts=[r"^dial cartridge plug pad"], note="glued to the bezel with the cartridge seated, so the plug lands on the socket (L4)",
         expect=[(r"plug pad", r"plug end", "flex", "the tail is lifted to slide the pad under the plug")]),
    dict(id="cart-in", join="cartridge", name="Dial cartridge drops in from the top, plugs in on the way down", dir="-z",
         travel="auto", note="key rib sets the angle, the key and two seat ribs bottom in their slots (the seat), three sideways magnet pairs "
                             "pull it down; suction cup on the glass lifts it out (L4 Ed 12:31, v0.25 Ed 18:26, 19:12)"),
    # ------------------------------------------------------------------ back cover (built off to the side)
    dict(id="cover", sub="cover", base=True, name="Back cover (ASA-CF)", parts=[r"^back cover"], note="FDM, black (CD 12:04)"),
    dict(id="cover-upper", sub="cover", name="Upper AMOLED and the lower screen pad on the cover floor", dir="-z", travel=10,
         parts=[r"^back AMOLED upper", r"^lower screen pad"], note="Kapton tape under the screens (CD 14:30); pad glued [A]"),
    dict(id="cover-lower", sub="cover", name="Lower AMOLED on its 1 mm pad", dir="-z", travel=10,
         parts=[r"^back AMOLED lower"], note="lower screen in front (CD); optional in the first build (L4 Ed 11:37)"),
    dict(id="cover-on", join="cover", name="Back cover with the screens onto the back", dir="+z", travel="auto",
         note="seam 0.3-0.5 with neutral-cure RTV (CD); screen flexes plugged first [A]"),
    dict(id="screws", name="Four M2.5 corner screws from the back", dir="+z", travel="auto",
         parts=[r"^corner screw"], note="ISO 14580 Torx T8 into the brass inserts (handover v0.19b)"),
]
