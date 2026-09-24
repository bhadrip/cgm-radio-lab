# CGM Radio Lab

The first vertical slice of a local, reproducible BLE LE 1M design loop.

This repository validates the portable digital packet and PHY primitives that a
future CGM radio can reuse across process technologies:

1. encode sequence, glucose, trend, status, and battery into an eight-byte CGM payload;
2. wrap it in a test-only BLE manufacturer-specific advertising PDU;
3. serialize the preamble, advertising access address, PDU, and BLE CRC in SystemVerilog;
4. whiten PDU+CRC and inject deterministic channel bit errors;
5. dewhiten, parse, and validate the complete packet in SystemVerilog;
6. verify recovered CGM fields, fixed packet structure, and CRC;
7. sweep raw bit-error rates and save packet-error measurements; and
8. synthesize the RTL with Yosys and save a structural report.

This slice intentionally does **not** implement GFSK, an analog RF front end,
or direct phone connectivity. It establishes the closed measurement loop that
later slices will retain while behavioral blocks are replaced with RF circuits.

## Reproducible EDA environment

The flow is pinned to the ARM64-compatible IIC-OSIC-TOOLS image required by the
IHP AMS template:

```text
docker.io/hpretl/iic-osic-tools:2026.08
```

Run the complete loop:

```bash
make container-check
```

Generated measurements are written to `reports/experiment.json`,
`reports/per_curve.csv`, and `reports/yosys-stat.txt`.

## Individual targets

```bash
make python-test
make rtl-test
make experiment
make yosys-stat
```

The individual targets expect Python, Icarus Verilog, cocotb, and Yosys on the
current `PATH`. `make container-check` supplies all of them through the pinned
container.

## Current interface

`rtl/cgm_packet_loop.sv` is the current integration point. Its transmitter emits
a fixed 224-bit legacy advertising packet. `inject_error` models a hard-decision
channel error, and the receiver recovers the CGM fields and independently checks
the fixed format and CRC. Channel numbers use the BLE range 0 through 39.

The advertising payload uses company identifier `0xFFFF` strictly for laboratory
testing. Production work requires an assigned identifier and a reviewed BLE/CGM
profile.

`rtl/cgm_chip_core.sv` adds a 16-register pad-facing control bus, direct packet
observation, an interrupt, and internal TX-to-RX self-test. It is intentionally
small and synchronous so it can be wrapped by the GF180 wafer.space padframe.
See [the prototype register map](docs/register-map.md).

The next tapeout-oriented slice will wrap this core in the wafer.space
GF180MCU project template with SPI registers, packet RAM, BIST, pads, and the
official precheck flow.
