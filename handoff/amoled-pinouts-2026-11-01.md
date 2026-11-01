# AMOLED screens: FPC pin-outs, power and connectors (1 Nov 2026, AWST)

Scope: the two AMOLEDs in `EdgerEquals/knob-hardware` (branch `param-dev`):
1. Control-dial round screen: Kingtech **PV13904PY24G-V01**, 1.39" 454×454, RM69330 (`cad/knob-param/knobparam/control_dial/screens/rm69330-1.39/SPEC.md`).
2. Joystick top screen: DWO **DO0164FMST05**, 1.64" 280×456, CO5300/ICNA3311 (named in `sub/joystick-v02` commit 427da4a, `jsparam/params.py`: "DWO DO0164FMST05 1.64\" 456x280 AMOLED"; FPC modelled [A] and pin-out marked open).

Tags: **[S]** = read from the maker's own spec PDF (saved in this folder). **[X]** = cross-checked against a second, independent source.
**[A]** = assumption or inference, not verified. **[?]** = open or unverified. No pin-out below is invented. Every row comes from a datasheet table.

Nothing was committed to the repo.

---

## 1. Kingtech PV13904PY24G-V01: 1.39" round 454×454 AMOLED (RM69330)

**Source:** Kingtech Group, *Product Specification PV13904PY24G-V01*, doc v02 (2019-09-18), 19 pp. → `kingtech_PV13904PY24G-V01.pdf`.
- Working link: https://www.kingtechdisplay.com/uploads/file/20241128/all-view-angle-1-39-inch-454-454-round-amoled.pdf
- The older link https://www.kingtechlcd.com/static/file/all-view-angle-1.39-inch-454-454-round-amoled.pdf still fails from the box (connection drops).
- Crops: `crops/kingtech_139_*.png`.

**Pin-out found: YES (maker's spec) [S]**. It is also cross-checked [X] against a second maker's panel with the same pin numbering: Panox BO139A454SPI (`Panox_BO139A454SPI_1.39.pdf`).

### FPC / connector
- 24 pins [S]. The panel side is a board-to-board plug on the folded FPC, not a ZIF tail and not hot-bar solder.
- Connector on the panel: **YXT-BB1F-24P-02** (亿鑫通 YXT, 0.4 mm pitch, 2 rows, 0.8 mm mated height, plug/"公") [S, drawing note 5]. Pitch and height come from panelook's connector page [X]: https://www.panelook.cn/connector_modeldetail_cn.php?id=2673
- **Mating socket for your PCB:** YXT-BB1F-24S-02 [?].
  - The part exists (HQchip listing https://item.hqchip.com/14659760.html; the page blocks bots).
  - The BB1F datasheet was not found, and no LCSC part number was found.
  - YXT-BB10-24S-02 (LCSC **C2763965**, ≈US$0.11) is the same pitch, height and pin count, but it is a different series. Fit with a BB1F plug is **unverified**: buy both and test before committing the footprint.
- **Watch out:** look-alike 1.39" RM69330 panels with the same 24-pin pin-out use a **Hirose BM28U-24DP/2-0.35V(86)** connector at 0.35 mm pitch instead (Panox BO139A454SPI; the Huawei GT2-46 replacement screens, per the eevblog thread).
  - Their mating receptacle is BM28B0.6-24DS/2-0.35V(53), LCSC **C5577343**, ≈US$1.57 (176 in stock).
  - So: **measure the connector on the panel you actually receive.**
- FPC geometry [S, outline p17]: the COF exits at the 0.62 ledge and folds onto the back. The folded FPC runs 25.11 ±0.30 from the panel edge to the connector.
  - Parts zone Hmax is 0.95 incl. insulation tape (0.55 on the other side). COF + IC Hmax is 0.60. There is an EMI film and a SUS stiffener.
  - The FPC width wasn't dimensioned in the PDF [?].
- Panel stack: 0.66 ±0.15 [S].

### Pin-out [S] (cross-checked [X] with Panox BO139A454SPI)
| Pin | Name | I/O | Function |
|---|---|---|---|
| 1 | XRES | I | Reset, active low |
| 2 | VCI_EN | I | Enables the on-FPC power IC (VCI/ELVDD/ELVSS generation) [function wording from the spec, "VCI enable signal"] |
| 3 | VPP | – | OTP programming voltage. Leave open (Panox: "NC (MTP), floating") |
| 4 | GND | P | Ground |
| 5 | TE | O | Tearing-effect sync out |
| 6 | DSI_D0N | I/O | MIPI data lane 0 − |
| 7 | AM_SPI_CSX | I | SPI chip select (active low) |
| 8 | DSI_D0P | I/O | MIPI data lane 0 + |
| 9 | AM_SPI_SCL | I | SPI clock |
| 10 | GND | P | Ground |
| 11 | AM_SPI_DCX | I | SPI data/command select |
| 12 | DSI_CLKN | I | MIPI clock − |
| 13 | AM_SPI_SDI | I/O | SPI data in |
| 14 | DSI_CLKP | I | MIPI clock + |
| 15 | AM_SPI_SDO | I/O | SPI data out |
| 16 | GND | P | Ground |
| 17 | ID(H) | – | Panel ID pin (Panox: NC) |
| 18, 20 | VDDIO | P | Logic/IO supply, **1.65–1.95 V (1.8 typ)** |
| 19, 21, 22, 23, 24 | VBAT | P | Panel power, **2.9–4.8 V (3.7 typ)** |

### Power and interface
- **Rails:** only **VBAT (2.9–4.8 V)** and **VDDIO (1.8 V)** [S].
  - No separate VCI, AVDD, ELVDD or ELVSS pins. The power IC that makes them sits on the FPC (the "器件区" component zones in the drawing) and is switched by VCI_EN [S + A for the internals].
  - **No external boost or ELVSS supply is needed.** 3.3 V on VBAT is inside the range.
- **Power draw:** 252 mW typ / 291 max at full white and 450 nits; 12 mW idle; < 10 µW deep standby [S].
- **Power sequence** (p8) [S]: VDDIO first, then VBAT/VCI_EN (≥ 10 ms), then RESX high (≥ 10 ms), then init, SLPOUT and DISPON (≥ 60 ms). Power-off is the reverse. Reset low pulse is ≥ 20 µs.
- **IO level, the catch:** VDDIO maxes out at **1.95 V**, so every logic pin is 1.8 V. With the 3.3 V CH32V003 you need:
  - a 1.8 V LDO, and
  - a level shifter on CSX, SCL, DCX, SDI, XRES and VCI_EN (SDO and TE come back the other way).
  - The eevblog builder used a TXB0108 and warned it must be wired the right way round.
- **Interface:** MIPI-DSI 1-lane, or 4-wire SPI. QSPI is **not** on the FPC (no SDI1–3 pins) and there are no IM straps, so the mode is fixed on the COF.
  - SPI is proven on this exact part number. An eevblog user drove PV13904PY24G over 4-wire SPI with CircuitPython.
  - Init used: `FE 00`, `35 00`, `C4 80` (SPI write-RAM enable, needed for SPI), `3A 05`, `11`, `29`. Source: https://www.eevblog.com/forum/microcontrollers/driving-a-round-amoled-display/ (replies #14–#20).
- **Reference circuit** (Panox p6, low-res figure) [X, values only partly legible]:
  - 100 k pull-up on XRES to 1.8 V;
  - about 1 µF decoupling on VDDIO and VBAT [? value read from a blurry image].
- **Touch:** none on this part. (The -C2 variant is listed with capacitive touch.)

### Where to buy
- Kingtech/Elsun on Made-in-China: US$35 at 100–999 pcs (MOQ 100). It says "small trial order" and "sample" are possible on request. https://kingtechlcd.en.made-in-china.com/product/LZnAuFTPqakf/China-Kingtech-1-39-Inch-Round-TFT-LCD-OLED-Display.html
- Panelook listing: https://www.panelook.com/PV13904PY24G-V01-1-39-AMOLED-454-454-450nits-MIPI-SPI-Full-view-under-sunlight-can-be-customized-detail_166695.html
- 16rd.com (CN retail, about ¥399 each per search snippet; the page is behind a slider captcha) [?]: https://www.16rd.com/shop_product-1-1149.html
- There's no clean single-unit retail source. Hobbyists buy "Huawei GT2 46 mm" replacements, but those have a different connector and a touch layer.

### Driver IC datasheet
RM69330 v0.0 public datasheet: https://ifan-display.com/wp-content/uploads/2023/08/RM69330-DataSheet_V0.0_20171101-Public-version.pdf. The site is bot-protected (HTTP 202 challenge), so it wouldn't download from the box. It opens in a browser.

---

## 2. DWO DO0164FMST05: 1.64" 280×456 AMOLED (CO5300 / ICNA3311, FT3168 touch)

**Source:** DWO Ltd, *Product Specification DO0164FMST05* REV 0.0 (2024-08-06), 23 pp. → `DWO_DO0164FMST05_spec_REV0.0.pdf`.
- The PDF is linked as "Product Datasheet" from DWO's product page https://www.dwo.net.cn/pd.jsp?id=12014. The page rate-limits repeat fetches (429), but it opens in a browser.
- Direct PDF: https://18746902.s21i.faimallusr.com/61/1/ABUIABA9GAAgyajPvgYom9KinwY.pdf. The file's PDF title says "SPEC-DO0164FMST02", but every page is DO0164FMST05.
- Also saved: `CO5300_driver_datasheet.pdf`, `FT3168_touch_datasheet.pdf`, `Panasonic_A4S_0.4mm_connector.pdf` (all linked from the same page).
- Crops: `crops/dwo_164_*.png`.

**Pin-out found: YES (maker's spec) [S]**. Cross-checked [X] against:
- the Waveshare ESP32-S3-Touch-AMOLED-1.64 schematic, which wires a 30-pin socket with the same pin names (`Waveshare_ESP32-S3-Touch-AMOLED-1.64_schematic.pdf`, crop `crops/waveshare_164_lcd_connector_wiring.png`);
- DWO's own D102 demo-board schematic.

### FPC / connector
- 30 pins at 0.4 mm pitch. Board-to-FPC **header on the panel: Panasonic AXE630124** (A4S series) [S].
- **Mating socket for your PCB:** **Panasonic AXE530127** (A4S, 30 pins, 0.4 mm, 0.8 mm mated height) [S]. The A4S datasheet pairs AXE530127 with AXE630124 at 0.8 mm [X].
  - LCSC **C425103** (AXE530127D), about US$0.15 each, 17,830 in stock: https://www.lcsc.com/product-detail/C425103.html
  - Not ZIF and not hot-bar: a press-in mezzanine connector (30 mating cycles).
- Module: 26.74 × 41.62 × 1.5 mm *including* the 0.5 cover glass; AMOLED OD 23.74 × 38.62; active 21.84 × 35.57 [S]. The repo already uses these numbers.
- FPC tail [S, drawing p6]:
  - It leaves a **short edge** of the panel (portrait top), which is the ±x end when mounted landscape. That matches the repo's assumption that the FPC drops at the +x end.
  - It is about 8.4 wide at the stiffener / connector end, with a 0.15–0.2 steel stiffener disc.
  - In the back view, the AXE630124 header centre sits **about 6.89 ±0.3 past the AMOLED edge**, and the tail is centred (11.87 / 11.87).
  - **[?]** I can't tell from the PDF whether that view shows the tail folded or flat. DWO lists the "Product 2D Drawing" as not posted, so ask DWO or the seller for the DXF before fixing the carrier slot.
  - Component zones on the FPC back are 1.2 mm max (power IC and passives); the connector is 1.1 mm max.
  - The repo placeholder `fpc_w = 8.0 [A]` is close to the 8.4 tail width read off the drawing.

### Pin-out [S] (DWO "MAIN FPC PIN DESCRIPTION" and the §5 table)
| Pin | Name | I/O | Function |
|---|---|---|---|
| 1 | GND | P | Ground |
| 2 | – | – | Not described in the spec [?]. DWO's D102 demo schematic labels it DCX_RS; Waveshare leaves it unconnected |
| 3 | TP_SCL | I | Touch I²C clock (IOVCC level); leave open if unused |
| 4 | WRX_SCL | I | SPI/QSPI clock |
| 5 | TP_SDA | I/O | Touch I²C data (FT3168, address 0x38) |
| 6 | CS | I | Chip select, active low. Tie to IOVCC in MIPI mode |
| 7 | TP_INT | O | Touch interrupt |
| 8 | SDI3 | I | QSPI data 3 (open if unused) |
| 9 | TP_RESET | I | Touch reset |
| 10 | SDI2 | I | QSPI data 2 (open if unused) |
| 11 | TP_VCC | P | Touch supply, 2.7–3.4 V |
| 12 | DCX_SDI1 | I/O | QSPI data 1 / SPI data-out / D/CX in 4-wire SPI |
| 13 | VPP (NC) | P | OTP supply: leave open |
| 14 | RDX_SDIO0 | I/O | QSPI data 0 / SPI data-in (GND if unused) |
| 15 | IM1 | I | Interface select |
| 16 | GND | P | Ground |
| 17 | IM0 | I | Interface select |
| 18 | MIPI_CLKP | I | DSI clock + (GND if unused) |
| 19 | RESET | I | Display reset, active low |
| 20 | MIPI_CLKN | I | DSI clock − (GND if unused) |
| 21 | PWR_EN | I | Enables the on-FPC power IC (drive low to cut sleep current) |
| 22 | GND | P | Ground |
| 23 | VCI (VCI_IN) | P | Driver analog supply, **2.7–3.6 V** |
| 24 | MIPI_D0P | I/O | DSI data + (GND if unused) |
| 25 | VDDIO (IOVCC) | P | Display + touch IO supply, **1.72–3.4 V** (DC table: 1.65–3.4 V) |
| 26 | MIPI_D0N | I/O | DSI data − (GND if unused) |
| 27 | TE | O | Tearing effect |
| 28 | GND | P | Ground |
| 29, 30 | VBAT | P | Panel power, **2.9–4.5 V (3.8 typ)** |

**Interface select** [S]:

| IM1 | IM0 | CS | Interface |
|---|---|---|---|
| 0 | 0 | – | 3-wire SPI |
| 0 | 1 | – | 4-wire SPI |
| 1 | 0 | – | **QSPI** |
| 0 | 0 | tied to IOVCC | MIPI-DSI 1-lane |

### Power and interface
- **Rails:** VBAT 2.9–4.5 V, VCI 2.7–3.6 V, VDDIO 1.65–3.4 V, TP_VCC 2.7–3.4 V [S]. The ELVDD/ELVSS power IC is on the FPC, enabled by PWR_EN.
  - **No external boost/ELVSS and no level shifters needed.** All four supplies can be one **3.3 V** rail.
  - Waveshare does exactly that [X]: TP_VCC, VCI, VDDIO and VBAT all on 3V3, IM1 = 3V3, IM0 = GND (QSPI), PWR_EN with a 10 k pull-up to 3V3, TE and TP_INT unused on V1.
- **Current at 350 nits, full white** [S]: IVBAT 50 mA, IVCC 2.9 mA, IIOVCC 1.8 mA. Sleep-in: VBAT about 10 µA (max 150), VCC/IOVCC about 300 µA each. 60 Hz.
- **Touch:** FT3168 on-cell, I²C at 0x38, single point + gestures [S]. Its pins share the same connector.
- **Firmware support:** Waveshare (ESP32-S3-Touch-AMOLED-1.64, CO5300 QSPI) and DWO publish ESP32-S3 / STM32 QSPI demo code and init code on the product page.

### Where to buy
- DWO direct: US$7.00, 44 in stock on the DWO list page today (1 Nov 2026). https://www.dwo.net.cn/pd.jsp?id=12014. The sister part DO0164FMST02 (SH8601) is US$6.60.
- DWO AliExpress store (store ID 1103907022, per a search result) [?, not opened].
- The same-spec panel under other part numbers: Youritech E1644AC63.A, about US$26.80 [? search snippet]. https://youritech-online.com/products/1-64-inch-280x456-amoled-color-screen-qspi-interface-oncell-touch-screen-smart-wearable-oled
- Dev board with this panel class: Waveshare ESP32-S3-Touch-AMOLED-1.64. https://docs.waveshare.com/ESP32-S3-Touch-AMOLED-1.64 (schematic and resources: https://docs.waveshare.com/ESP32-S3-Touch-AMOLED-1.64/Resources-And-Documents)

---

## 3. Better-documented substitute for the round dial screen: DWO DO0132FMST01

`DWO_DO0132FMST01_spec.pdf` (REV 0.0, 2024-05-20). Product page: https://www.dwo.net.cn/pd.jsp?id=11996 (US$6.60, 93 in stock today).

**This is a substitute, not the panel in the CAD.**

- **Panel:** 1.32" round, **466×466**, CO5300 (ICNA3311), FT3168 touch (glass + film), 600 nits.
- **Size:** AMOLED OD **36.35 × 36.35 × 0.8**, active **Ø33.55** [S].
- **FPC bends:** add ≤ 0.8 at two points of the rim (top and bottom) [S]. That makes the worst-case envelope about Ø37.95 on that axis, against the Kingtech's 38.21 + ledge + COF bend (about r 20.03, which breaks the Ø39.5 knob wall in v0.13).
- **Pin-out:** the **same 30-pin DWO pin-out and AXE630124 header** as the 1.64" [S]. So both screens would share:
  - one mating part (AXE530127, LCSC C425103);
  - one 3.3 V rail, with no 1.8 V LDO and no level shifter;
  - one QSPI driver (CO5300).
- **FPC tail:** leaves the side of the round and runs about 11.5 to the connector centre [S, back view]. It still has to fold behind the panel [?].
- **Trade-off:** the active area is about 1.9 mm smaller in diameter (33.55 vs 35.41).
- DO0132FMST02 is the same panel with a 1.1 cover lens (40.35 OD, 2.03 thick), which is too wide for the knob.
- The 1.43" DWO rounds (DO0143FMST02/10/12, 466×466) have an outline of 39.15 × 39.3, which doesn't fit Ø39.5 with a wall.

---

## Recommendations
1. **Joystick screen (DO0164FMST05): keep it.**
   - It is now fully documented: maker spec, pin-out, connector with an LCSC mate (C425103), single 3.3 V rail, QSPI, and a reference schematic (Waveshare) plus vendor code.
   - Before freezing the carrier: get DWO's 2D drawing/DXF to confirm the folded-tail path (the ~6.89 header offset), and set `fpc_w` to about 8.4.
2. **Control-dial screen (Kingtech PV13904PY24G): the pin-out is now known, but I recommend switching to DWO DO0132FMST01** (Ed's decision). Why:
   - The Kingtech is 1.8 V-only IO, which means an LDO plus a level shifter on about 7 lines.
   - Its mating connector isn't on LCSC, and look-alikes use a different 0.35 mm connector.
   - It sells mainly at MOQ 100 (US$35 each).
   - Its ledge and COF bend already break the Ø39.5 knob wall.
   - The DWO round fixes all of these and matches the 1.64" panel's connector, rails and driver. The cost is a 466×466 panel with a slightly smaller active area.
   - If Ed keeps the Kingtech: buy one panel plus both candidate sockets (YXT-BB1F-24S-02 and YXT-BB10-24S-02 C2763965), and the Hirose BM28B0.6-24DS/2-0.35V(53) C5577343 in case a 0.35 mm variant arrives. Measure, then lay out.

## Files in this folder
- `kingtech_PV13904PY24G-V01.pdf`: Kingtech 1.39" spec.
- `Panox_BO139A454SPI_1.39.pdf`: same-pin-out 1.39" RM69330 cross-check (0.35 mm BM28 connector variant).
- `DWO_DO0164FMST05_spec_REV0.0.pdf`: DWO 1.64" spec.
- `DWO_DO0132FMST01_spec.pdf`, `DWO_DO0132FMST02_spec.pdf`, `DWO_DO0143FMST02_spec.pdf`: DWO round alternatives.
- `CO5300_driver_datasheet.pdf` (226 pp), `FT3168_touch_datasheet.pdf`, `Panasonic_A4S_0.4mm_connector.pdf`.
- `Waveshare_ESP32-S3-Touch-AMOLED-1.64_schematic.pdf`.
- `crops/`: drawing and table crops used above.

## Links checked 1 Nov 2026 (box, ~20:40 AWST)
- Working: Kingtech PDF (kingtechdisplay.com), Panox PDF, DWO PDFs (faimallusr.com), DWO product page id 11996, LCSC C425103 / C2763965 / C5577343, Panasonic AXE530127 page, Waveshare 1.64 docs, eevblog thread, panelook pages, Made-in-China listing, Youritech.
- Blocked for bots (open in a browser): dwo.net.cn id 12014 (rate-limited 429 after the first fetch worked), ifan-display RM69330 PDF (202 challenge), hqchip (403), 16rd (captcha).
- Dead from the box: kingtechlcd.com PDF (connection drops).
