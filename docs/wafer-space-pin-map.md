# Wafer.Space GF180 wrapper

The wrapper in `wafer_space/chip_core.sv` matches the `chip_core` interface in
the official Wafer.Space GF180MCU template at commit
`0de7e394337a1f7f5303ac7a3681bf2481b58176`. It targets the `0p5x0p5` slot,
which provides 4 input pads, 38 bidirectional pads, and 4 analog pads.

| Pad | Direction | Function |
|---|---|---|
| `input[0]` | input | register write enable |
| `input[1]` | input | register read enable |
| `input[2]` | input | output mode: 0 legacy/register, 1 GFSK observation |
| `input[3]` | input | reserved |
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

With `input[2]` high, the same output pads expose the waveform path:

| Pad | Function in GFSK observation mode |
|---|---|
| `bidir[30:12]` | signed 19-bit instantaneous frequency offset, Hz |
| `bidir[31]` | frequency sample valid |
| `bidir[32]` | transmitter busy |
| `bidir[33]` | completion interrupt |
| `bidir[34]` | loopback BIST pass |
| `bidir[35]` | accepted packet bit |
| `bidir[36]` | accepted packet bit valid |
| `bidir[37]` | reserved, driven low |

The wrapper integrates the packet engine and digital GFSK modem. It does not
yet contain a PLL/DCO, PA, RF front end, electrochemical analog front end,
antenna match, or production BLE link layer.

The official template is pinned as a submodule. Run synthesis and floorplanning
for the smallest slot with:

```bash
git submodule update --init
make container-gf180-floorplan
```

Run the SRAM-free pad-connected PDN, placement, clock tree, and detailed route:

```bash
make container-gf180-route
```

Run stream-out, extracted timing, DRC, density, antenna, and LVS:

```bash
make container-gf180-signoff
```
