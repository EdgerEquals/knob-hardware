# Power budget (main PCB v0.12)

Currents are on the +5 V input. The 3.3 V rail is an AP2112 from that 5 V. The USB-PD / Eurorack OR-ing front end is not on this board; +5 V comes in on J4. Motor currents are still assumptions. Every load below is switchable and off until firmware asks.

## Idle, loads off: 8 mA

| Item | mA |
|---|---|
| MCU, HSE, loads off [A] | 6.0 |
| AP2112 Iq [S] | 0.1 |
| CAN transceiver standby [S, order] | 0.4 |
| pull-ups [A] | 1.5 |
| **Total** | **8.0** |

## Typical: 110 mA

| Item | mA |
|---|---|
| MCU active [A] | 12.0 |
| Hall row [A] | 6.0 |
| encoder LED + photo [S/A] | 11.0 |
| top AMOLED, modest [A] | 25.0 |
| bottom TFT, modest [A] | 20.0 |
| dial screen + CH32 over the rod [A] | 15.0 |
| one 665 nm VCSEL | 4.5 |
| RGB dim, under the cap [A] | 8.0 |
| LDO and the rest [A] | 9.0 |
| **Total** | **110.5** |

## Peak (run, not stall): 530 mA

| Item | mA |
|---|---|
| MCU [A] | 20.0 |
| three screens, bright [A] | 125.0 |
| Hall + encoder | 16.0 |
| one VCSEL | 4.5 |
| RGB at the series-resistor cap | 34.0 |
| violet module [S] | 55.0 |
| 1220 moving, not stalled [A] | 120.0 |
| 716 moving [A] | 60.0 |
| two Risley motors [A] | 80.0 |
| rails and LDO [A] | 15.0 |
| **Total** | **529.5** |

## Hardware ceiling (1220 clamped, RGB capped, show running): 674 mA

| Item | mA |
|---|---|
| 1220 held at the hardware stall clamp | 240.0 |
| RGB cap | 34.0 |
| violet [S] | 55.0 |
| 716 + two Risley + mirror, all spinning [A] | 180.0 |
| screens bright + MCU + Hall | 161.0 |
| one VCSEL | 4.5 |
| **Total** | **674.5** |

The 0.7 A figure is a WS2812-class chain at full white. The fitted SK6805-EC20 is 5 mA per colour (186 mA for 12 at full white). Two 22 Ω resistors in series on the LED rail collapse that to about 34 mA, because the LEDs need at least 3.5 V. The 1220 clamp is about 0.24 A: four 22 Ω resistors in parallel under the bridge, divided by 10k/10k onto a transistor base. Trip current is about 1.3 V / Rparallel. Add parallel 22 Ω resistors to raise it. At the assumed 120 mA run current the sense stack drops about 0.7 V.

Laser setpoint is about 4.5 mA (100 Ω emitter resistor, base near 1.10 V). JNJOPTO lists 4 mW minimum / 6 mW typical at 10 mA and a 4 mA threshold, and no curve, so the first articles have to be measured and the 100 Ω raised if the beam is over 1 mW. Do not fit less than ~68 Ω (8 mA order); the absolute maximum is 10 mA. The datasheet on LCSC is filed under both 665003 and 665005; confirm the reel.
