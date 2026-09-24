# Wafer.Space GF180 wrapper

The wrapper in `wafer_space/chip_core.sv` matches the `chip_core` interface in
the official Wafer.Space GF180MCU template at commit
`0de7e394337a1f7f5303ac7a3681bf2481b58176`. It targets the `0p5x0p5` slot,
which provides 4 input pads, 38 bidirectional pads, and 4 analog pads.

| Pad | Direction | Function |
|---|---|---|
| `input[0]` | input | register write enable |
| `input[1]` | input | register read enable |
| `input[3:2]` | input | reserved |
| `bidir[3:0]` | input | register address |
| `bidir[11:4]` | input | register write data |
| `bidir[12]` | output | serialized BLE hard bit |
| `bidir[13]` | output | packet bit valid |
| `bidir[14]` | output | packet engine busy |
| `bidir[15]` | output | completion interrupt |
| `bidir[16]` | output | loopback BIST pass |
| `bidir[24:17]` | output | register read data |
| `bidir[37:25]` | output | reserved, driven low |
| `analog[3:0]` | analog | reserved for sensor and RF experiments |

The wrapper only integrates the verified digital hard-bit path. It does not yet
contain the GFSK modem, RF front end, electrochemical analog front end, antenna
match, or a production BLE link layer.
