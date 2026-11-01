# PCBWay resin 3D-printing menu: clear-resin knob-module case
Researched 2026-11-01 (AWST). Sources are PCBWay pages unless noted.

## Full resin list (PCBWay resin materials page)
https://www.pcbway.com/rapid-prototyping/3d-printing/plastic/resin/
- Price is shown only as a "$$$$$" scale; real prices come from the instant quote. Lead time is 5-10 business days.
- The page says photopolymers "are not stable over time" (https://www.pcbway.com/rapid-prototyping/3d-printing/3d-printing-SLA.html, Drawbacks).

| Material | Process | Colour / clarity | Notes |
|---|---|---|---|
| UTR 8360 Standard white | SLA | Matte white, opaque | Supports spray painting, dyeing, silk screen. Most used. |
| UTR Imagine Black | SLA | Black | |
| UTR-8100 (transparent) | SLA | "Transparent (Spray varnish)", "Matte diffuse" | The only clear resin |
| UTR-8100 (translucent) | SLA | Translucent | Same resin, no varnish |
| PWR Dark Black | SLA | Black (waxed) | Turns whitish when polished, so it gets waxed |
| Somos Ledo | SLA | (colour not captured; page timed out) | Tagged "High toughness, Heat resistant" |
| UTR 8220 | SLA | "Tender green" (clarity not stated) | Elongation 16%, notched impact 27 J/m, HDT 58 C. https://www.pcbway.com/rapid-prototyping/3d-printing/plastic/resin/UTR-8220/ |
| UTR 3000 | SLA | (not captured) | Paint/dye-able |
| UTR Therm | SLA | | 150 C, high hardness |
| Somos EvoLVe 128 | SLA | | ABS/PBT-like |
| UTR Flex | DLP | | Flexible |
| Somos PerFORM | SLA | | Very hard composite |
| TDS EvoDent | DLP | | Dental |
| Formlabs ESD Resin | SLA | | ESD-safe |
| UFSH100 / UFSH220 | SLA | | High-temp |
| FR42 | SLA | | UL94 V0 flame retardant |

- DLP offers only UTR Flex and TDS EvoDent, with no clear resin (https://www.pcbway.com/rapid-prototyping/3D-Printing/3D-Printing-DLP.html).
- PCBWay lists no LCD resin process.

## UTR-8100 detail
- Transparent: https://www.pcbway.com/rapid-prototyping/3d-printing/plastic/resin/UTR-8100/
- Translucent: https://www.pcbway.com/rapid-prototyping/3d-printing/plastic/resin/UTR-8100-translucent/
- PCBWay says it is "nearly colorless after polished and sprayed processing". It is "difficult to be completely transparent in complex structures", and air bubbles may form during printing (they ask you to talk to their technicians).
- Toughness: tensile 41.56 MPa, elongation 9%, notched impact 24 J/m2, Shore 83-85D, HDT 52 C/50 C, density 1.3 g/cm3. Fairly brittle, so ~2.5 mm walls are sensible. SLA minimum wall is 0.8 mm.
- Listed use: "Transparent shell parts of electronic appliances."
- Price example (third party, burariweb): a small case cost US$18.28 base in UTR-8100 transparent, with dyeing as an extra fee. The fee is the same for a standard or a custom Pantone colour. Production took about 8-9 days. https://burariweb.info/gadget/3d-printer/pcbway-utr8100-dyeing.html

## Tinting: YES, via the Dyeing finish on clear resin
- PCBWay dyeing page: "Applicable to all pantone colors". Materials: Nylon and Resin. "Usually the result of dyeing will have a certain color difference." Swatches: Red 032 U, Yellow U, Blue 072 U, Green U, Black U, Orange 021 U, Purple U, Process Blue, Red 0331 U. https://www.pcbway.com/rapid-prototyping/Surface-Finishing/dyeing/dyeing/
- On the quote page, UTR-8100 transparent > Surface finish > Dyeing > swatch or custom Pantone code (Adafruit guide: https://learn.adafruit.com/clear-resin-3d-prints-with-pcbway/uploading-files.md).
- Real results:
  - Emerald tint with Pantone 360C on 2 mm walls; thinner walls dye lighter and both faces came sanded smooth (burariweb, above).
  - A light red tint and a black tint also shown (https://burariweb.info/electronic-work/pcbway-3dprinting-service.html).
  - Blue tint with Pantone 2191C (https://www.reddit.com/r/flipperzero/comments/177isgl/).
- Caveat: one PCBWay customer review says the dye came out "lighter than expected and inconsistent" and more translucent than expected. https://www.pcbway.com/project/member/feedback/?bmbno=532BF659-9FBF-42
- PCBWay's blog says dyeing suits absorbent materials like nylon best and "may be uneven". https://www.pcbway.com/blog/3D_Printing/What_surface_finish_can_be_chosen_for_3D_printing_fc4ba015.html

## Glow-in-the-dark / photoluminescent resin: NOT OFFERED
None appear on the resin list. PCBWay's glow-in-the-dark product is PCB silkscreen, not 3D-print resin (https://hackaday.com/2025/03/24/glow-in-the-dark-pcbs-are-pretty-cool/).

## UV-reactive / fluorescent resin: NOT OFFERED
None appear on the list. There is no listed fluorescent paint or finish either. A custom finish would have to be asked about at 3dcnc@pcbway.com.

## Standard finishes (SLA page)
- Spray painting: matte, high-gloss, imitation electroplating, varnish, leather; any Pantone.
- Polished: "transparent parts can be polished ... to improve transparency".
- Electroplating, inlay nut, glazing, "reinforced coating", testing.
- No finish called "UV coating" or "UV-blocking clear coat" is listed. The transparent grade's spray varnish is the clear coat.
- Custom finishes go through 3dcnc@pcbway.com.

## Yellowing under UV / 405 nm
- PCBWay publishes nothing on yellowing for UTR-8100.
- Its general note says photopolymers are "not stable over time".
- UnionTech's UTR8100 datasheet claims "Durability of resin-built parts for more than 6.5 months". https://ufc-oversea.oss-accelerate.aliyuncs.com/wp-content/uploads/2022/05/Transparent-Clear-Resin-1.pdf
- General industry guidance: clear resins yellow with ongoing UV exposure, and a UV-protective coat helps (https://3dspro.com/resources/3dspro-lab/why-is-my-3d-printed-resin-product-turning-yellow-and-how-to-prevent-this).
- Inference (not sourced): 665 nm red is not a yellowing risk. 405 nm violet is near-UV, so long exposure could slowly yellow it. A yellow drift would hide best under a warm tint (amber/red/orange) and show most on a pale blue/clear case.

## Recommendation
- UTR-8100 transparent (spray varnish) + Dyeing, light red/amber Pantone tint, ~2.5 mm walls.
- Red suits the 665 nm scanner: red light passes, so the dots stay bright, and it hides any violet-induced yellowing.
- Glow is not available in-house. The route is the Shimicoat strontium aluminate Ed already has, brushed on inside surfaces, or a custom-finish email to PCBWay (not sent).
