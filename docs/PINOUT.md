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
| 5 | D4 | P0.04 | display MOSI |
| 6 | D5 | P0.05 | COL5 |
| 7 | D6 | P1.11 | ROW0 |
| 8 | D7 | P1.12 | ROW1 |
| 9 | D8 | P1.13 | ROW2 |
| 10 | D9 | P1.14 | ROW3 |
| 11 | D10 | P1.15 | COL4 |
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
        , <&xiao_d 10 GPIO_ACTIVE_HIGH>  /* COL4  D10 P1.15 */
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

The `xiao_d` nexus only defines D0..D10. Display lines:

```dts
&pinctrl {
    spi_disp_default: spi_disp_default {
        group1 {
            psels = <NRF_PSEL(SPIM_SCK,  0, 15)>,   /* SCK  D11 P0.15 */
                    <NRF_PSEL(SPIM_MOSI, 0, 4)>;    /* MOSI D4  P0.04 */
        };
    };
};
nice_view_spi: &spi3 {                               /* not spi2: xiao_ble uses it for P1.13/P1.15 */
    compatible = "nordic,nrf-spim";
    pinctrl-0 = <&spi_disp_default>;
    cs-gpios = <&gpio0 19 GPIO_ACTIVE_LOW>;          /* CS   D12 P0.19 */
};
```

SCK, MOSI and CS all sit on pins the nRF52840 spec rates for a fast clock
(table below). No MISO: the LS0xx is write-only.

## Matrix

21 keys: 6 columns x 3 rows, plus 3 thumbs on ROW3.

| | COL0 outer | COL1 pinky | COL2 ring | COL3 middle | COL4 index | COL5 inner |
|---|---|---|---|---|---|---|
| ROW0 | SW13 | SW16 | SW3 | SW14 | SW9 | SW6 |
| ROW1 | SW5 | SW20 | SW7 | SW10 | SW12 | SW11 |
| ROW2 | SW19 | SW1 | SW8 | SW18 | SW2 | SW15 |
| ROW3 | - | - | - | SW4 | SW21 | SW17 |

## Display SPI pins: which GPIOs can carry a 1 MHz clock

Source: nRF52840 Product Specification v1.11, section 7 "aQFN73 ball
assignments" (pages 926–933 of the DigiKey PDF). Each GPIO is tagged either
plain "General purpose I/O" or "Standard drive, low frequency I/O only".
Nordic defines low frequency as up to 10 kHz (note on the same table;
DevZone case 232044 confirms: the tag marks pins near the radio that can
desense it when driven fast). The nice!view runs at `spi-max-frequency =
<1000000>` (ZMK `shields/nice_view/nice_view.overlay`), 100x over that.

| Pad | Name | Port | Spec tag | 1 MHz SPI |
|---|---|---|---|---|
| 1 | D0 | P0.02 | low frequency only | no |
| 2 | D1 | P0.03 | low frequency only | no |
| 3 | D2 | P0.28 | low frequency only | no |
| 4 | D3 | P0.29 | low frequency only | no |
| 5 | D4 | P0.04 | general purpose | **yes** |
| 6 | D5 | P0.05 | general purpose | **yes** |
| 7 | D6 | P1.11 | low frequency only | no |
| 8 | D7 | P1.12 | low frequency only | no |
| 9 | D8 | P1.13 | low frequency only | no |
| 10 | D9 | P1.14 | low frequency only | no |
| 11 | D10 | P1.15 | low frequency only | no |
| 15 | D11 | P0.15 | general purpose | **yes** |
| 16 | D12 | P0.19 | general purpose (QSPI/SCK on the module) | **yes** |
| 17 | D13 | P1.01 | low frequency only | no |
| 18 | D14 | P0.09 | low frequency only, NFC | no |
| 19 | D15 | P0.10 | low frequency only, NFC | no |
| 20 | D16 | P0.31 | low frequency only, battery sense | no |
| 21 | D17 | P1.03 | low frequency only | no |
| 22 | D18 | P1.05 | low frequency only | no |
| 23 | D19 | P1.07 | low frequency only | no |

Consequences:

- The current SCK/CS on D11/D12 (pads 15/16) are the right *electrical*
  choice: they are two of only four pins on the whole module rated for a
  fast clock. They are also the two hardest pads to route.
- Of the Plus-only pins, none is rated for SPI. Moving SCK or CS to
  D13–D19 to ease routing would put the display clock on a radio-adjacent
  pin the spec limits to 10 kHz. Seeed's own board uses P1.13/P1.15
  (low-frequency pins) for its stock `spi2`, so it works in practice, but
  it is out of spec with the radio on.
- The only in-spec fast pins on the **non-Plus** XIAO edge are D4 and D5
  (P0.04/P0.05). A design that must run on the original XIAO nRF52840 has
  exactly two SPI-capable pins, which is SCK + MOSI with CS on any GPIO
  (CS is static, no frequency limit). That leaves 9 pins for the matrix:
  a 6x4 needs 10. So the non-Plus board cannot carry this matrix plus an
  in-spec display; the Plus is required, and D11/D12 stay.
- MOSI was on D10 (P1.15), a low-frequency pin, carrying data at the same
  1 MHz as SCK. Decided 2026-09-19: MOSI moved to D4 (P0.04, fast pin);
  COL4 took D10. Matrix scanning is far below 10 kHz, so a column on a
  low-frequency pin is in spec. All three display lines (MOSI D4, SCK D11,
  CS D12) are now on the four fast pins.
