# XIAO nRF52840 Plus pin assignment

## Where these pin numbers come from

ZMK has no board definition for the **Plus** -- only `seeed/xiao_ble` for the
standard XIAO nRF52840. The Plus keeps the standard 14-pin layout and adds nine
castellated pins, so the mapping was resolved from primary sources and
cross-checked, never from the wiki pinout image (which is disputed -- see below).

| Source | What it establishes |
|---|---|
| Zephyr `boards/seeed/xiao_ble/seeed_xiao_connector.dtsi` | `xiao_d` nexus: D0..D10 -> P0.02 P0.03 P0.28 P0.29 P0.04 P0.05 P1.11 P1.12 P1.13 P1.14 P1.15. ZMK inherits this. |
| Seeed `XIAO_Series_SCH_Symbols` symbol `XIAO-nRF52840_Plus_SMD` | Footprint pad number -> pin name: pads 1..11 = D0..D10, 12=3V3, 13=GND, 14=VBUS, pads 15..23 = D11..D19. |
| Seeed Plus KiCad PCB, header footprint `U4` | Pad -> net. Pads 1..11 match the Zephyr nexus exactly; pads 15..23 give D11..D19. |
| `reference/chalk/reversible.kicad_pcb` | A working board. Its XIAO pads 1..14 are netted P0..P10 / VCC33 / GND / VCC5, agreeing with the symbol on all 14 shared pads. |

Two independent chains agree on every pin used here.

## Full Plus pin table

| Pad | Name | Port | Used for |
|---|---|---|---|
| 1 | D0 | P0.02 | COL0 |
| 2 | D1 | P0.03 | COL1 |
| 3 | D2 | P0.28 | COL2 |
| 4 | D3 | P0.29 | COL3 |
| 5 | D4 | P0.04 | COL4 |
| 6 | D5 | P0.05 | COL5 |
| 7 | D6 | P1.11 | ROW0 |
| 8 | D7 | P1.12 | ROW1 |
| 9 | D8 | P1.13 | ROW2 |
| 10 | D9 | P1.14 | ROW3 |
| 11 | D10 | P1.15 | display MOSI |
| 12 | 3V3 | - | display VCC |
| 13 | GND | - | GND |
| 14 | VBUS | - | (unused) |
| 15 | D11 | P0.15 | display SCK |
| 16 | D12 | P0.19 | display CS |
| 17 | D13 | P1.01 | free |
| 18 | D14 | P0.09 | free (NFC) |
| 19 | D15 | P0.10 | free (NFC) |
| 20 | D16 | P0.31 | free (battery sense) |
| 21 | D17 | P1.03 | free (disputed) |
| 22 | D18 | P1.05 | free (disputed) |
| 23 | D19 | P1.07 | free (disputed) |

## Pins deliberately avoided

- **D14 = P0.09, D15 = P0.10** are NFC pins by default. Usable as GPIO only with
  `CONFIG_NFCT_PINS_AS_GPIOS`.
- **D16 = P0.31** is AIN7/BAT. ZMK's `xiao_ble` board reads battery voltage on
  the ADC, so leave it alone.
- **D17/D18/D19 = P1.03/P1.05/P1.07.** Seeed's published Plus pinout image is
  reported wrong for exactly these: one user found "1.03 and 1.07 are SWAPPED"
  and confirmed it against the KiCad files; another found that blinking D19 lit
  the pad silkscreened D17. Seeed acknowledged an inconsistency. Nothing here
  depends on them.

The whole design fits in **D0..D12**, all corroborated by two independent
sources, leaving D13..D19 free.

## ZMK kscan

`diode-direction = "col2row"`: current flows column -> switch -> diode anode ->
cathode -> row, which is how the netlist is wired (switch pad 1 = column,
switch pad 2 = diode pad 2, diode pad 1 = row).

```dts
kscan0: kscan {
    compatible = "zmk,kscan-gpio-matrix";
    wakeup-source;
    diode-direction = "col2row";

    col-gpios
        = <&xiao_d 0 GPIO_ACTIVE_HIGH>   /* COL0  D0  P0.02 */
        , <&xiao_d 1 GPIO_ACTIVE_HIGH>   /* COL1  D1  P0.03 */
        , <&xiao_d 2 GPIO_ACTIVE_HIGH>   /* COL2  D2  P0.28 */
        , <&xiao_d 3 GPIO_ACTIVE_HIGH>   /* COL3  D3  P0.29 */
        , <&xiao_d 4 GPIO_ACTIVE_HIGH>   /* COL4  D4  P0.04 */
        , <&xiao_d 5 GPIO_ACTIVE_HIGH>   /* COL5  D5  P0.05 */
        ;

    row-gpios
        = <&xiao_d 6 (GPIO_ACTIVE_HIGH | GPIO_PULL_DOWN)>  /* ROW0 D6 P1.11 */
        , <&xiao_d 7 (GPIO_ACTIVE_HIGH | GPIO_PULL_DOWN)>  /* ROW1 D7 P1.12 */
        , <&xiao_d 8 (GPIO_ACTIVE_HIGH | GPIO_PULL_DOWN)>  /* ROW2 D8 P1.13 */
        , <&xiao_d 9 (GPIO_ACTIVE_HIGH | GPIO_PULL_DOWN)>  /* ROW3 D9 P1.14 */
        ;
};
```

The `xiao_d` nexus only defines D0..D10, so the display pins (D11 = P0.15,
D12 = P0.19) must be referenced as raw ports: `&gpio0 15` and `&gpio0 19`.

## Matrix

21 keys: 6 columns x 3 rows, plus 3 thumbs on ROW3.

| | COL0 outer | COL1 pinky | COL2 ring | COL3 middle | COL4 index | COL5 inner |
|---|---|---|---|---|---|---|
| ROW0 | SW13 | SW16 | SW3 | SW14 | SW9 | SW6 |
| ROW1 | SW5 | SW20 | SW7 | SW10 | SW12 | SW11 |
| ROW2 | SW19 | SW1 | SW8 | SW18 | SW2 | SW15 |
| ROW3 | - | - | - | SW4 | SW21 | SW17 |
