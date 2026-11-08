# Noise sweep (8 Nov 2026)

Asked by Ed [8 Nov 15:45]: "Before we move on, I am a little worried about noise. Can we do a bit of a sweep and we'll see where
we're at because I'm a bit of a Scrooge for low noise". Tags: [S] read in a source, [A] my estimate or choice, [C] still to check,
[Ed] Ed's decision. Picture: `docs/img/noise-sweep.png` (`tools/studies/noise_sweep_sketch.py`).

What was swept: every rail and converter (jack power board, its lower board, board L), every switching load (the 1220, the RGB ring,
the screens, the clear OLED, the dial), every analog input and output (CV in x3, CV out x3, audio in and out, the Halls, MOT_SENSE),
every crossing between boards (link flex, 2x6 stacks, posts, rod), and the outside world (USB-C, patch cables).

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
3. **Q41** the ground-sense line: one of the flex's grounds (23, 24 or 25) becomes the jack board's analog ground, carried to an
   ADC pin and read alongside each CV in (the firmware subtracts it, or the ADC reads differentially where the pins allow) [A].
   Plus the stacks' sense ground from step 2.
Not proposed: isolating USB inside the module. With power on the same USB-C it needs an isolated 12 W converter as well as a USB
isolator chip; there is no room for that in the jack unit [A]. An external USB isolator does the same job when a computer is used.

## Q39: the bucks' light-load mode (the first decision)
- **A (recommended): TPS62933F** on all three bucks (board L's 5 V and 3.3 V, and the jack board's 3.3 V). Fixed frequency at
  every load [S], so the only switching tone is at the set frequency (MHz), far above audio, at every load. Same package, pins
  and footprint as the TPS62933 [S]. LCSC C5219272, US$0.62, 3,748 in stock [S, read 8 Nov]. Cost: +US$0.37 each and about
  0.1 W more each at idle [A], so about 0.3 W more heat with the module idle. Frequencies then set apart so no two converters
  (or their harmonics) meet [A, values with step 3].
- **B: TPS62933O** ("out-of-audio"): still skips at light load but keeps its switching above the audio band [S TI datasheet];
  kinder at idle. But it has spread spectrum (the TPS62933F does not [S]), which wobbles the switching frequency, and the rate of
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
