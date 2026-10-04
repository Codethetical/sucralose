# Sucralose firmware (ZMK module)

This repo is a [ZMK module](https://zmk.dev/docs/features/modules): `zephyr/module.yml` at the
repo root points ZMK at `firmware/`, which holds the `sucralose_left` / `sucralose_right` shield.

- Controller: Seeed XIAO nRF52840 Plus or Sense Plus, built as `seeeduino_xiao_ble`
  (see `docs/PINOUT.md` for why not `xiao_ble_sense`)
- Display: nice!view on both halves
- ZMK: v0.3

## Using it

In your zmk-config's `config/west.yml`, add this repo next to ZMK:

```yaml
    - name: sucralose
      remote: codethetical   # url-base: https://github.com/Codethetical
      revision: main
```

and in `build.yaml`:

```yaml
include:
  - board: seeeduino_xiao_ble
    shield: sucralose_left nice_view
  - board: seeeduino_xiao_ble
    shield: sucralose_right nice_view
```

`nice_view` must come after `sucralose_*`: the shield defines the display bus that `nice_view`
attaches to. There is no `nice_view_adapter`; the display is wired straight to the XIAO.

The left half is the central and advertises as "Sucralose". The default keymap is a 6-column
Corne layout; RESET and BOOT on the raise layer replace the XIAO's button.

## Pins

| Function | XIAO | nRF52840 |
|---|---|---|
| COL0..COL5 | D0 D1 D2 D3 D10 D5 | P0.02 P0.03 P0.28 P0.29 P1.15 P0.05 |
| ROW0..ROW3 | D6..D9 | P1.11..P1.14 |
| Display MOSI / SCK / CS | D4 / D11 / D12 | P0.04 / P0.15 / P0.19 (SPIM3) |

Both XIAO lands carry the same nets, so both halves use the same pins; the right half lists the
columns in reverse because its board is flipped.
