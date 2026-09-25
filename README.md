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

The packet loop intentionally still stops at hard bits; the standalone GFSK
modulator establishes the next digital-to-radio boundary. Neither block
implements an analog RF front end or direct phone connectivity.
The project requirements, unresolved product inputs, and review gates are kept
in [the engineering basis](docs/engineering-basis.md).
Product targets and production-evidence boundaries also follow the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

The first waveform-level modem block is a synthesizable 16-sample/symbol
[BLE LE 1M GFSK modulator](docs/gfsk-modulator.md). It exposes an integer-Hz
frequency-control stream for a later direct-modulation synthesizer. The
`cgm_gfsk_tx` integration paces the complete 224-bit CGM advertising packet at
1 Msym/s and produces a gapless 224 us modulation burst.

The next analog boundary is the calibrated
[DCO tuning-code controller](docs/dco-control.md), which noise-shapes those
frequency requests into a 12-bit oscillator code without claiming an RF circuit
that has not yet been simulated and measured.

A transistor-level GF180 feasibility sweep now rejects a minimum-length
three-stage ring as the BLE local oscillator: its unloaded slow-corner ceiling
is 1.583 GHz. See the [ring-oscillator result](reports/ring-dco-feasibility.md).
This is a useful architecture result, not an RF sign-off claim.

The follow-on [LC-oscillator experiment](reports/lc-vco-feasibility.md) starts
across the sampled PVT tuning envelope at 1 mA and brackets the BLE band, but it
depends on an assumed 3 nH, Q=10 tank. The open GF180 distribution contains no
RF inductor model or PCell, so an EM-qualified passive remains a hard gate.

The [tuning-bank sizing](reports/lc-dco-bank-sizing.md) replaces the placeholder
linear DCO assumption with a 4-bit coarse MIM bank and analog MOS-varactor fine
control. The fine-control voltage resolution is a new circuit requirement.
The [transistor-level tuning validation](reports/lc-dco-tuning-validation.md)
then verifies overlapping BLE-band coverage at all three sampled PVT corners.
The [GFSK drive mapping](reports/lc-dco-gfsk-drive.md) holds the coarse bank
fixed for each burst and maps all 3,584 packet samples onto fine-control voltage.
The [dynamic validation](reports/lc-dco-dynamic-validation.md) measures a short
nominal-corner sequence and bounds its instantaneous-frequency tracking error.
The [fine-control DAC analysis](reports/lc-dco-dac-resolution.md) selects the
minimum full-scale resolution across all packet samples and sampled corners.
The [segmented DAC architecture](reports/lc-dco-segmented-dac.md) then reduces
the high-speed switching path from 12 bits to 7 bits after
[non-ideality budgeting](reports/lc-dco-dac-nonidealities.md).
The [transition budget](reports/lc-dco-dac-transition.md) selects five
thermometer-coded MSBs plus two binary LSBs and sets a 750 ps switch-skew target.
The [registered DAC decoder](reports/lc-dco-dac-decoder.md) now implements the
6+1 encoding selected by transistor validation and checks all 128 input codes.
The first [GF180 switched-current DAC experiment](reports/gf180-fast-dac.md)
passes nominal linearity but is rejected for a 150 uV carry glitch.
The [current-steered follow-on](reports/gf180-fast-dac-steered.md) moves to a
6+1 split and passes the nominal carry gate at 20.777 uV.
The [sampled PVT gate](reports/gf180-fast-dac-steered-pvt.md) retains that pass
at typical/25 C, fast/-40 C, and slow/125 C.
The [mismatch sensitivity sweep](reports/gf180-fast-dac-mismatch.md) then bounds
the assumed single-unit current sigma at 2.0% for a 99.9% modeled-yield target;
it is explicitly not foundry-qualified Monte Carlo evidence.
The [complementary gate-driver experiment](reports/gf180-fast-dac-gate-driver.md)
replaces the ideal carry-edge controls with GF180 transistor inverters and
retains a 47.923 kHz worst-case combined error across sampled PVT.
The [reference-current sweep](reports/gf180-fast-dac-reference-window.md) then
requires the fast-DAC reference to remain within 0.85x--1.05x nominal across
the sampled operating conditions.
The [control-drive sweep](reports/lc-dco-drive-settling.md) adds explicit output
resistance and RF bypass and derives a 1 kOhm/10 pF implementation target.
The first [GF180 RF output-stage experiment](reports/gf180-pa-feasibility.md)
uses a calibrated 7-bit slice bank to cover sampled -20 to 0 dBm levels within
0.444 dB while bounding the PA-core burst energy below 0.985 uJ.
The [GFSK spectrum screen](reports/gfsk-spectrum.md) integrates the quantized
complex-envelope power in adjacent 1 MHz bands and records the remaining RF
effects required before TX spectral compliance can be claimed.
The [PA harmonic characterization](reports/gf180-pa-harmonics.md) extracts raw
second- and third-harmonic emissions for later matching-network allocation.
The [PA real-load screen](reports/gf180-pa-load-sweep.md) checks calibrated
maximum-power codes from 25 to 200 ohms before a matching topology is selected.
The [first PA match screen](reports/pa-match-screen.md) sizes a 150-to-50-ohm
low-pass candidate and sweeps loss and harmonic rejection versus inductor Q.
The [matched PA co-simulation](reports/gf180-pa-match.md) retunes that network
with GF180 PA transistors across PVT and measures delivered power and harmonics.
The [receiver noise budget](reports/rx-noise-budget.md) allocates switch, LNA,
mixer, and baseband gain/noise against the provisional -80 dBm RX target.
The [first GF180 LNA sweep](reports/gf180-lna-feasibility.md) measures gain,
noise figure, input match, headroom, and active power across sampled PVT.
The [BLE-band LNA sweep](reports/gf180-lna-band.md) checks the selected device
at all 40 channel centers from 2.402 to 2.480 GHz across the same PVT samples.
The [LNA two-tone screen](reports/gf180-lna-linearity.md) brackets compression
and estimates finite-level IM3 across sampled PVT.
The [LNA bias-boost sweep](reports/gf180-lna-bias-boost.md) selects a temporary
strong-input state and exposes its active-power cost.
The [LNA single-tone screen](reports/gf180-lna-single-tone.md) checks normal and
boosted modes at PR11's provisional -10 dBm maximum input.

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

Reproduce the longer settled LC-DCO calibration and dynamic check:

```bash
make container-rf-characterization
```

Generated measurements are written to `reports/experiment.json`,
`reports/per_curve.csv`, `reports/ring_dco_sweep.json`,
`reports/ring_dco_sweep.csv`, `reports/lc_vco_sweep.json`,
`reports/lc_vco_sweep.csv`, `reports/lc_dco_bank.json`,
`reports/lc_dco_sweep.json`, `reports/lc_dco_sweep.csv`,
`reports/lc_dco_local_calibration.json`, `reports/lc_dco_modulation.json`,
`reports/lc_dco_dac_resolution.json`, `reports/lc_dco_dynamic.json`,
`reports/lc_dco_segmented_dac.json`, `reports/lc_dco_dac_nonidealities.json`,
`reports/lc_dco_dac_transition.json`, `reports/lc_dco_drive_settling.json`,
`reports/gf180_fast_dac.json`, `reports/gf180_fast_dac_steered.json`,
`reports/gf180_fast_dac_steered_pvt.json`,
`reports/gf180_fast_dac_mismatch.json`,
`reports/gf180_fast_dac_gate_driver.json`,
`reports/gf180_fast_dac_reference_window.json`, `reports/gf180_pa.json`,
`reports/gfsk_spectrum.json`, `reports/yosys-stat.txt`,
`reports/dco-dac-yosys-stat.txt`, and the remaining GFSK/DCO synthesis reports.

## Individual targets

```bash
make python-test
make rtl-test
make analog-test
make gf180-fast-dac-test
make gf180-fast-dac-steered-test
make gf180-fast-dac-steered-pvt-test
make gf180-fast-dac-mismatch-test
make gf180-fast-dac-gate-driver-test
make gf180-fast-dac-reference-window-test
make gf180-pa-test
make gf180-pa-load-test
make gf180-pa-match-test
make gf180-lna-test
make gf180-lna-band-test
make gf180-lna-linearity-test
make gf180-lna-bias-boost-test
make gf180-lna-single-tone-test
make pa-match-screen
make rx-noise-budget
make gfsk-spectrum
make lc-dco-local-calibration
make lc-dco-dynamic-test
make dco-bank-sizing
make dco-modulation
make dco-dac-resolution
make dco-segmented-dac
make dco-dac-nonidealities
make dco-dac-transition
make lc-dco-drive-settling
make experiment
make yosys-stat
make gfsk-yosys-stat
make gfsk-tx-yosys-stat
make dco-yosys-stat
make dco-dac-yosys-stat
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
and modulation observation, an interrupt, and internal TX-to-RX self-test. It
is synchronous so it can be wrapped by the GF180 wafer.space padframe. See
[the prototype register map](docs/register-map.md).

`wafer_space/chip_core.sv` maps that interface onto the smallest `0p5x0p5`
slot in the official Wafer.Space GF180MCU project template. See
[the pad map](docs/wafer-space-pin-map.md). A later slice will stage the full
template and run LibreLane plus the official precheck.
