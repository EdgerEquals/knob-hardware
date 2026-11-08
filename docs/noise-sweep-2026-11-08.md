# Noise sweep (8 Nov 2026)

Asked by Ed [8 Nov 15:45]: "Before we move on, I am a little worried about noise. Can we do a bit of a sweep and we'll see where
we're at because I'm a bit of a Scrooge for low noise". Tags: [S] read in a source, [A] my estimate or choice, [C] still to check,
[Ed] Ed's decision. Picture: `docs/img/noise-sweep.png` (`tools/studies/noise_sweep_sketch.py`).

What was swept: every rail and converter (jack power board, its lower board, board L), every switching load (the 1220, the RGB ring,
the screens, the clear OLED, the dial), every analog input and output (CV in x3, CV out x3, audio in and out, the Halls, MOT_SENSE),
every crossing between boards (link flex, 2x6 stacks, posts, rod), and the outside world (USB-C, patch cables).

**Outcome: Q39 = A [Ed 8 Nov 15:59, "Yeah, that's perfect", after the 1-2 MHz answer]:** TPS62933F on all three bucks, their
frequencies set about 1-2 MHz and apart from each other and the boost's harmonics (values in step 3); the 1220's PWM at 100 kHz,
the DRV8213's top [S]. The jack board's U6 is now TPS62933FDRLR (LCSC C5219272) in design.py and its generated files.
**Q38 = A [Ed 16:04]:** two TPS62933F bucks on board L, both from 15 V. Next: Q40, then Q41.
**Q40 = A [Ed 16:07]:** TI REF3430 (3.0 V) on VREF+. Jack lower board re-set in design.py: CV-in feedback 11.3k (was
13.3k), audio-out gain 33.2k (was 30.1k), audio in x -0.28 (28.0k, 270 pF) round VMID, so the 10k/10k/1 µF bias divider is gone.
Its generated schematic, board and BOM are regenerated after Q41 (which changes a flex pin). Next: Q41.
**Q41 = A [Ed 16:11]:** flex pin 24 is AGND_SENSE: a 0R at the lower board's TLV9064 ties it to GND (in the old bias resistor's
place, same ref, so the saved placement holds); on the main board PC0 (ADC2_INP10), 100 Ω + 1 nF + 1 MΩ; ADC1 / ADC2 dual
simultaneous, subtracted in firmware. Pin map re-solved keeping every other net (`--keep`): JOY_RST to PE9, PWR_LIGHT on PB9
(the VCSEL decoder's 5 pins gone, Q36): 61 nets, 21 spare. The lower board rebuilt and re-routed from design.py.

## Where we are, in one line
Nothing is broken, but five things would show on a scope at the jacks: the switching regulators' light-load bursts, the ADC's
reference being the 3.3 V supply, the ground offset between the jack board and the main board, the RGB ring's 1.2 kHz dimming, and
the ground loop through USB with a computer. All five have cheap fixes; three need a decision from you, two are layout.

## The numbers behind the ranking
- **How small a cent is at the ADC.** CV in is scaled x 0.133 (100k in, 13.3k back) onto VMID [S step-2 circuit]. One cent at
  1 V/oct is 1/1200 V = 0.83 mV at the jack, so **0.11 mV at the ADC** [A arithmetic]. On a 16-bit ADC with a 3.3 V reference that
  is about 2 codes.
- **Reference ripple.** VREF+ is the 3.3 V supply through 47 Ω and 1 µF (corner about 3.4 kHz) [S main-board circuit]. Every 1 mV
  on VREF+ moves a mid-scale reading (about 1.6 V) by 1.6 x 1/3300 = 0.48 mV, **about 4-5 cents** [A arithmetic]. Ripple below
  3.4 kHz passes straight through; so does drift.
- **Ground offset.** The CV-in op-amps make their output against the jack board's ground; the H743 reads it against the main
  board's VSSA. **1 mV between those grounds is about 9 cents** on a CV in [A arithmetic]. The main board's return current (up to
  about 0.9 A from 15 V with the motor and the ring busy [Q38 loads]) goes back down the posts and, in parallel, the flex's 8
  ground lines, so some millivolts between the two are likely and they move with the motor and the LEDs [A; measure on the bench].
- **The CV-out side** has the same kind of offset across the 2x6 stacks: about 1 mV per amp, about 1.2 cents per amp, open since
  step 2 [S step-2 circuit, "Ground drop for 1 V/oct"].
- **When the bucks drop into light-load mode.** The TPS62933 runs PFM at light load; the TPS62933F runs forced continuous (FCCM) at
  every load [S TI datasheet]. A buck goes discontinuous below about half its ripple current. At 15 V in, 1.2 MHz, 2.2 µH [A, the
  jack board's values]: the 5 V buck below about 0.63 A, the 3.3 V buck below about 0.49 A [A arithmetic]. Board L's 5 V idles at
  about 0.2 A (motor and ring off) and its 3.3 V runs 0.25-0.5 A, so **both sit in PFM most of the time**; the jack board's 3.3 V
  (under 40 mA) always does. PFM bursts at a rate set by the load, which falls into the audio band at light load.
- **Beats between converters.** The boost runs at 600 kHz [S step-2 circuit]; its second harmonic is 1.2 MHz, the jack board's
  3.3 V buck's frequency, on the same board. Two oscillators that close beat at their difference, which can be anywhere from 0 to
  tens of kHz. [C] Both parts' frequency tolerances (TI's page shows no figure for the TPS62933's RT).
- **The RGB ring.** The SK6812MINI-E dims by PWM at **1.2 kHz**, 12 mA a colour [S datasheet, "The frequency of PWM 1.2 KHZ"].
  24 of them full white is 0.86 A pulsing at 1.2 kHz. Each LED has its own clock, so the 24 drift against each other and their
  sum wanders across the audio band. The firmware cap lowers the amplitude but not the frequency.
- **The boost at light load.** The TPS55340 skips pulses when it needs an on-time under 77 ns, "typically ... in light load
  conditions", and "pulse skipping increases the output ripple" [S datasheet 7.3.3.1]. TI's forum answer for the same part family:
  a minimum load, or a lower frequency, or an external clock [S TI E2E]. Its ripple reaches the op-amps only through the
  TPS7A4901 / TPS7A3001, which reject audio-frequency ripple well [A].

## Ranked (as in the picture)
| Rank | Source | Fix | Cost | Status |
|---|---|---|---|---|
| HIGH | Bucks in light-load mode (PFM), and two converters meeting at 1.2 MHz | TPS62933F on all three (same footprint [S]); frequencies set apart | +US$0.37 each, about 0.1 W more each at idle [A] | **Q39**, then Q38 |
| HIGH | ADC reference = the 3.3 V supply | a quiet reference on VREF+; CV-in feedback resistors re-set to fit | one SOT-23 + 2 caps, or none | **Q40** |
| HIGH | Ground offset between the jack board and the main board | a ground-sense line on the flex, read with each CV in; the stacks' sense ground | no parts; one flex ground repurposed | **Q41** |
| HIGH | RGB ring, 1.2 kHz PWM, 24 free-running clocks | the ring on its own 5 V branch: ferrite + bulk capacitor at the ring, its ground straight back to board L, never under the Halls or the ADC lines; firmware cap | a ferrite and a capacitor | doing [A] |
| HIGH | Ground loop through USB with a computer (a charger's leakage too, smaller) | the USB ground meets the jack sleeves at one point on the jack unit, so loop current never crosses the DAC / op-amp ground; shield to ground through 1 MΩ ‖ 4.7 nF [C fit on the USB board]; with a computer, an external USB isolator | two parts | doing [A] |
| MED | 1220 brushes and its 50-100 kHz drive | 100 nF across the motor's terminals, short twisted leads, the DRV8213 on its own 5 V branch with a bulk capacitor | a capacitor | doing [A] |
| MED | Screens' converters and frame-rate steps | the joystick screen on its own filtered 3.3 V branch (ferrite + capacitor) | a ferrite, a capacitor | doing [A] |
| MED | Clear OLED, row-scanned, on the op-amps' +12.5 V | its ferrite + 10 µF are already there; its ground return kept off the op-amps' ground | layout | doing [A] |
| MED | Boost pulse skipping at light load | bench-check the ±12 V ripple; a small minimum load if needed | none planned | bench |
| MED | Rod link (still to design) | data well above 20 kHz; the dial's supply filtered at the main-board end | with that circuit | later |
| LOW | SPI, USB and CV / audio on one flex | pin order already has grounds between the groups (2, 12, 15, 19, 21, 23-25) and SCK at the edge [S Q11 order] | none | keep |
| LOW | 50 MHz QSPI, the 480 MHz core | 22 Ω series resistors and the ground-flanked board R header (done) | none | keep |
| KEPT | Audio out on the H743's 12-bit DAC | **kept by choice: Q8 = B** [Ed 5 Nov: "it's a noise effect, the low bit depth might help"]; the reference fix (Q40) still keeps supply hum off it | - | - |
| ALL | Board stack-up, firmware | 4 layers with an unbroken ground plane on the main board (with the layer count); the ADC's hardware oversampling; samples timed away from the LED and motor switching | - | later |

Also on board L [A, doing]: a small input filter (ferrite + capacitors) between the posts' 15 V and the two bucks, so their
input ripple stays on board L and does not travel down the posts into the jack boards.

## Decisions, one at a time
1. **Q39** the bucks' light-load mode (below). Then **Q38** (the power tree) again, with the answer in it.
2. **Q40** the ADC's reference: A a 3.0 V reference chip on VREF+ (the CV-in range re-set to about 0.2-2.95 V: 13.3k becomes
   11.3k, 3 places [A arithmetic]); B the H743's own reference buffer at 2.5 V (VREFBUF, no part; CV-in gain down to about 0.076,
   so fewer codes a cent; [C] ST's forum reports early H743 silicon, revision Y, shipped without its factory trim); C as now.
   **Q40 as asked (8 Nov, `docs/img/adc-reference-q40.png`):** A = **TI REF3430** (3.0 V, ±0.05 %, 6 ppm/°C max, 3.8 µVp-p per
   volt 0.1-10 Hz, dropout 0.1 V max at no load, 95 µA [S TI]; LCSC C2156866, US$1.51, 312 in stock [S]) from the 3.3 V onto VREF+
   with 1 µF + 100 nF. Ranges re-set to fit 3.0 V [A]: CV-in feedback 13.3k becomes 11.3k (3 places), ±12 V reads 0.23-2.95 V,
   2.1 codes a cent; audio-out gain 30.1k becomes 33.2k (still ±5 V); audio-in gain and bias re-set for 0-3.0 V. The Halls,
   switch ladder and NTC stay on the 3.3 V; the firmware reads the 3.3 V through the H743's VBAT channel (VBAT tied to VDD) and
   corrects them. Tight: about 0.2 V of headroom from 3.3 V; thin LCSC stock. [C] its output-capacitor range. B = VREFBUF 2.5 V
   (no part; 1.7 codes a cent; revision-Y trim reports).
3. **Q41** the ground-sense line: one of the flex's grounds (23, 24 or 25) becomes the jack board's analog ground, carried to an
   ADC pin and read alongside each CV in (the firmware subtracts it, or the ADC reads differentially where the pins allow) [A].
   Plus the stacks' sense ground from step 2.
   **Q41 as asked (8 Nov, `docs/img/ground-sense-q41.png`):** A = flex pin 24 (between grounds 23 and 25) becomes AGND_SENSE,
   taken at the CV-in op-amps' ground on the lower board, into a spare ADC2 pin on the main board (100 Ω + 1 nF, 1 MΩ to ground);
   the H743 samples each CV in (ADC1) and the sense line (ADC2) together and subtracts; grounds 8 to 7 [A]. After Q40 1 mV between
   the grounds is about 11 cents; likely 1-3 mV with the motor and ring busy [A: a few mΩ in the GND post, about 10 mΩ in the
   flex's grounds]. B = leave it and measure on the first boards (a later fix needs a new flex pin-out). The stacks' sense ground
   for the CV outs is checked next, with the stack pin list.
Not proposed: isolating USB inside the module. With power on the same USB-C it needs an isolated 12 W converter as well as a USB
isolator chip; there is no room for that in the jack unit [A]. An external USB isolator does the same job when a computer is used.

## Q42 = A [Ed 16:35]: two grounds in the jack unit (the rearrangement below)
As built into the netlists (8 Nov):
- **QGND (quiet):** the four sleeves and both copper pours of the jack board; first stacks H1 inner 2 and H2 inner 2 (2 pins: no
  current, two so one bad contact never leaves the sleeves floating); a track through the upper board; second stacks left inner 6
  and right outer 3; on the lower board the DAC (GND, LDAC, pad), its REF and supply caps, VMID's 100k and 1 µF, the audio
  output's + input; link flex pin 24 (read as AGND_SENSE on the main board).
- **GND (power):** the USB-C GND contacts routed 0.5 wide to six first-stack pins (H1 outer 2, 4, 5, 6; H2 outer 2, 4; 0.75 A a pin
  at 3 A, as VBUS), second stacks right outer 6, the rest of the lower board, the posts, the flex's other six grounds.
- **One join:** the 0R (R41) from QGND to GND on the lower board. [A] its exact place is not critical: only the DAC's own steady
  supply current (about a milliamp) flows between it and the DAC.
- Refined from the picture as first shown (4 quiet + 4 power, 1 quiet + 2 power) [A]: the quiet ground carries no current, so it
  needs few pins, and the power side gets the rest (more margin).

## Q42: the sleeves' ground and the lower board's ground (found while doing Q41)
Picture: `docs/img/sleeve-sense-q42.png`. A CV is tip minus sleeve. The sleeves (and the USB-C power contacts) are on the jack
board; the DAC and the CV op-amps are on the jack lower board, two stacks down. The first stacks carry the whole module's current on
7 ground pins [S: jack-board HDR_NETS], the second carry the lower board's own current and part of the main board's on 3 [S: STACK2].
At about 10-20 mΩ a contact [A; C the PM127VS sheet], about 1 A from a charger: **likely 2-5 mV between the sleeves and the lower
board's ground, so 2-6 cents on every CV out and CV in, moving with the motor and the LEDs** [A]. 1 mV = 1.2 cents at jack scale.
Q41's sense line does not see it (it measures the lower board against the main board).
- **A: a sleeve-sense line.** One ground pin in each pair of stacks becomes SLEEVE_SENSE (first stacks 7 → 6 grounds, second
  3 → 2). On the lower board a resistor network from the DAC's reference, the lower ground and SLEEVE_SENSE sets each op-amp group's
  + input [A, worked]: CV outs (Vout = 7 x V+ - 6 x Vdac) need V+ = VMID - Δ/7, so conductances VREF : SLEEVE : GND = 4 : 1 : 2
  (e.g. 17.5k, 70k, 35k); CV ins (x 0.113) need V+ = VMID - 0.1015 Δ, so 0.5714 : 0.1015 : 0.3271. Δ = lower ground - sleeves.
  About 6 resistors (0.1 %) and capacitors split in the same ratios so the division holds at audio frequencies [A]. The
  three jack boards re-routed.
- **B: firmware only.** Δ estimated from the known loads (MOT_SENSE, the LED and screen settings) times one resistance measured on
  the bench; CV outs and readings pre-corrected. No hardware; leaves maybe a fifth, and misses fast changes [A].

**Q42 restated [Ed 16:21: "it feels like a bit of a band-aid ... can we just remove or rearrange things so that we don't have the
problem?"]** (`docs/img/quiet-ground-q42.png`): rearrange instead of correcting. Two ground nets in the jack unit:
- **Quiet ground (QGND):** the four sleeves, the DAC, the CV-out and CV-in op-amps, VMID, the audio stages and their bypass caps.
  It runs on its own stack pins: in the first stacks the four grounds between each jack's tip and ring (H1 inner 2, H1 outer 2,
  H2 inner 2, H2 outer 2); in the second stacks right outer 3 (beside J4_RING). A quiet track through the upper board.
- **Power ground (GND):** the USB-C contacts, the PD chip, the eFuse, the LDOs, the 3.3 V buck, the switches, MIDI, the expander, the
  posts, the boost and charge pump, the clear OLED and the link flex. First stacks H1 outer 4-6 and H2 outer 4 (beside the four
  VBUS pins; 4 pins at 1 A [S JLCPCB] for up to 3 A from a computer port: 75 %, said plainly); second stacks left inner 6 and
  right outer 6.
- **One join, under the DAC** (where the SPI arrives): the 0R that Q41 put at the TLV9064 becomes the join; flex pin 24 then
  carries QGND itself. QGND is a tree hanging off that one point, so no supply current can flow in it; only the CV outputs' own
  load currents (about 0.1 mA into 100k) [A]: microvolts. A ground-loop current from a computer would cross it between the join and
  the sleeves: about a milliamp of hum in some tens of mΩ, tens of µV [A].
- Parts: none added. The sense line and resistor networks (old A) and the firmware fix (old B) are not needed. Q41 stays.
- Cost: the three jack boards re-laid out (two ground nets on the 2-layer jack board, a quiet track through the upper board, the
  lower board's ground layer split along the analog / power line).

## Q39: the bucks' light-load mode (the first decision)
- **A (recommended): TPS62933F** on all three bucks (board L's 5 V and 3.3 V, and the jack board's 3.3 V). Fixed frequency at
  every load [S], so the only switching tone is at the set frequency (MHz), far above audio, at every load. Same package, pins
  and footprint as the TPS62933 [S]. LCSC C5219272, US$0.62, 3,748 in stock [S, read 8 Nov]. Cost: +US$0.37 each and about
  0.1 W more each at idle [A], so about 0.3 W more heat with the module idle. Frequencies then set apart so no two converters
  (or their harmonics) meet [A, values with step 3].
- **B: TPS62933O** ("out-of-audio"): still skips at light load, but "the minimum switching frequency is clamped above 30 kHz"
  [S TI datasheet, OOA mode; TI takes audio as 20 Hz-20 kHz]; kinder at idle. 30 kHz is only 1.5 x the top of the audio band:
  the jack board's first-order low-passes (CV in 12 kHz, audio in 22 kHz) pass it at about -9 and -5 dB, against about -40 and
  -35 dB at 1.2 MHz [A arithmetic], and a tone that close to the band can beat with another or fold back in the ADC's sampling. But it has spread spectrum (the TPS62933F does not [S]), which wobbles the switching frequency, and the rate of
  that wobble is not on TI's summary page [C]. Availability at LCSC [C].
- Keeping the TPS62933 (PFM) is not offered: its bursts are the thing we are removing.

## Bench checks to plan
- Audio out and each CV in on a spectrum (an audio interface is enough): idle, ring on, motor holding still, motor turning, screens
  on. The noise floor and any tones.
- The two grounds: millivolts between the jack board's analog ground and the main board's VSSA, with the motor and the ring busy.
- ±12 V ripple at light and full load (the boost's pulse skipping).

## Sources
- TI TPS62932 / TPS62933 / TPS62933F / TPS62933O / TPS62933P datasheet (SLUSEA4D): PFM on the 32 / 33 / 33P, FCCM on the 33F,
  out-of-audio on the 33O, spread spectrum on all but the 33F. https://ti.com/document-viewer/TPS62933/datasheet
- TI TPS55340 datasheet, 7.3.3.1 "Minimum On-Time and Pulse Skipping":
  https://www.ti.com/document-viewer/TPS55340/datasheet/GUID-7E25DA07-CEFD-452A-9944-664DEC0FD742
- TI E2E, "TPS55340-Q1: about pulse skip mode in light load":
  https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/650265/tps55340-q1-about-pulse-skip-mode-in-light-load
- SK6812MINI-E datasheet (Akizuki's copy): PWM 1.2 kHz, 12 mA a colour. https://akizukidenshi.com/goodsaffix/sk6812mini-e.pdf
- ST community, "STM32H743V Y revision VREFBUF factory trim missing":
  https://community.st.com/s/question/0D50X0000Anu8vW/stm32h743v-y-revision-vrefbuf-factory-trim-missing-
- LCSC C5219272 (TPS62933F), read 8 Nov.
- Our own: `docs/step2-power-board-circuit-2026-11-06.md` (rails, CV in / out, audio, flex pins, the stacks' ground drop),
  `docs/main-board-circuit-2026-11-07.md` (VDDA, VREF+, flex end), `docs/layout-v4-2026-11-03.md` (Q3, Q4, Q8, Q11),
  `docs/main-board-pass-plan-2026-11-07.md` (Q38 loads).
