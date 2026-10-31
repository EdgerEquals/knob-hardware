# 1.39" round AMOLED, 454×454, RM69330 — Kingtech PV13904PY24G-V01

Status: modelled for knob stack v0.13 (`amoled_139.py`). **S** = from the Kingtech spec, **[A]** = assumed / scaled.

## Source
- Kingtech Group, *Product Specification PV13904PY24G-V01*, doc v02 (2019-03-26), 19 pp.
  Ed's link https://www.kingtechlcd.com/static/file/all-view-angle-1.39-inch-454-454-round-amoled.pdf
  does not download from the box (TLS EOF / 504). The same document came from
  https://www.kingtechdisplay.com/uploads/file/20241128/all-view-angle-1-39-inch-454-454-round-amoled.pdf.
  A local copy and crops of the outline drawing (p.17) are in `ref/`.
- RM69330 driver datasheet v0.0 (Raydium, 2017): interfaces (osptek mirror).

## Mechanical
| Item | Value | Src |
|---|---|---|
| Panel outline (encap glass) | **Ø38.21 ±0.15** | S |
| LTPS glass | 38.83 (V) × 38.21 (W): the round plus a **0.62 ledge** at the FPC side | S |
| → ledge edge from the centre | 38.83 − 19.105 = **19.725** | S (derived) |
| Encap glass across the FPC-side flat | 37.79 ±0.15 | S |
| Polarizer | Ø37.71 ±0.15 (37.21 V) | S |
| Active area | Ø35.41 ±0.10 (454 × 78 µm) | S |
| Rear tape | Ø37.61 ±0.15, 0.13 | S |
| Stack | POL 0.134 + encap 0.20 + LTPS 0.20 + rear tape 0.13 = **0.66 ±0.15** (spec table: 0.68) | S |
| COF / FPC exit | at the ledge, ~12 wide [A], bent round the LTPS edge onto the back; bend adds ~0.3 radially [A] | [A] |
| Folded FPC on the back | 25.11 ±0.30 long [S]; 14 wide [A]; parts zone Hmax 0.95 (incl. insulation tape) and 0.55 [S]; COF+IC Hmax 0.60 [S]; SUS304 0.10 stiffener [S] | S/[A] |
| Connector | YXT-BB1F-24P-02 board-to-board on the folded FPC [S]; 5 × 2.6 × 0.9 [A] | S/[A] |
| Back envelope with the folded FPC | 0.66 + ~1.1 = **~1.8** [A] | [A] |

## Electrical / interface
- 24-pin FPC [S]. 1 XRES, 2 VCI_EN, 3 VPP (OTP), 4/10/16 GND, 5 TE, 6/8 DSI_D0N/P, 12/14 DSI_CLKN/P,
  7 AM_SPI_CSX, 9 AM_SPI_SCL, 11 AM_SPI_DCX, 13 AM_SPI_SDI, 15 AM_SPI_SDO, 17 ID, 18/20 VDDIO, 19/21–24 VBAT.
- **Interface: the panel is NOT MIPI-only.** The spec says "MIPI/SPI" and the FPC brings out a 4-wire SPI port
  (CSX, SCL, DCX, SDI, SDO) next to a 1-lane MIPI DSI. The RM69330 supports SPI, dual-SPI and QSPI [S, RM69330 DS].
  The FPC has only SDI and SDO, so QSPI (4 data lines) is not available. Plain 4-wire SPI is, and dual-SPI might be [A].
  Interface select (IM) is not on the FPC, so it must be strapped on the COF [A]. Confirm with Kingtech that SPI is the shipped mode.
- VDDIO 1.65–1.95 V (1.8 typ) [S]. The CH32V003 runs at 3.3 V, so the SPI lines need level shifting. VBAT 2.9–4.8 V (3.7 typ) [S].
- Power: 252 mW typ at 100 % white and 450 nits; 12 mW idle (10 %, 30 nits) [S].
- Bandwidth: 454 × 454 × 24 bit ≈ 4.9 Mbit/frame, so about 8 fps at 40 MHz SPI [A].

## Fit in the Ø39.5 knob (v0.13)
- Fixed panel on holder v0.6, glass flush at 56.80. The rotating dial lip has an ID of Ø38.51 (0.15 [A] running gap), leaving a **0.495 wall** at Ø39.5.
- **Problem:** the ledge reaches r 19.725 [S] and the COF bend about r 20.03 [A], past the knob radius of 19.75. The lip has a slot at the tail
  (12 + ±10° travel + 1 = 19.9 wide). The bend sticks out about 0.28 beyond Ø39.5 there [A]. Fixes: offset the panel 0.3 away from the tail,
  or use a variant whose FPC exits from the back.
