# CGM Radio Lab

The first vertical slice of a local, reproducible BLE LE 1M design loop.

This repository currently validates the portable digital PHY primitives that a
future CGM radio can reuse across process technologies:

1. build a small BLE advertising-channel PDU in Python;
2. append the BLE 24-bit CRC;
3. whiten it in synthesizable SystemVerilog;
4. inject deterministic channel bit errors;
5. dewhiten it in synthesizable SystemVerilog;
6. verify the recovered PDU and CRC;
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

`rtl/ble_phy_loop.sv` accepts one unwhitened bit per valid clock cycle. The TX
whitener produces the channel bit, `inject_error` models a hard-decision channel
error, and the RX whitener recovers the bit. Independent TX and RX CRC engines
make corruption observable. Channel numbers use the BLE range 0 through 39.

The next tapeout-oriented slice will wrap this core in the wafer.space
GF180MCU project template with SPI registers, packet RAM, BIST, pads, and the
official precheck flow.

