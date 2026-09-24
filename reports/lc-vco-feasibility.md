# GF180 LC-oscillator feasibility

## Decision

Continue with the differential LC architecture, but do not treat it as
tapeout-ready. At 1 mA tail current, the sampled tuning envelope both sustains
oscillation and brackets 2402--2480 MHz at all three PVT points. That result
depends on a 3 nH inductor with Q=10, which is not provided by the open PDK.

## Experiment

The ngspice bench uses GF180MCU `nfet_03v3` cross-coupled devices and
`cap_mim_1f5_m4m5_noshield` capacitors. Each tank branch assumes 3 nH in series
with 4.6 ohm, approximately Q=10 at 2.44 GHz. MIM square side length is swept
from 24 to 34 um; tail current is swept over 0.5, 0.7, and 1.0 mA.

| Corner | Sustained envelope at 1 mA | Example band bracket |
|---|---:|---|
| Typical, 25 C | 2.115--2.932 GHz | 28 um: 2.544 GHz; 30 um: 2.384 GHz |
| Fast, -40 C | 2.309--3.183 GHz | 32 um: 2.446 GHz |
| Slow, 125 C | 2.210--2.718 GHz | 26 um: 2.524 GHz; 28 um: 2.355 GHz |

The 1 mA source consumes 1.8 mW from 1.8 V. Lower tested currents did not
provide an all-corner band bracket: the slow corner lost startup margin before
the tank reached the lower channels. This is active power, not CGM average
power; duty cycle, startup time, packet count, PA energy, and retry rate still
belong in the report-energy budget.

## Hard gates

The installed GF180 open PDK has transistor, MOS-capacitor, and MIM-capacitor
models, but no RF inductor model or inductor PCell. Before layout or tapeout,
the assumed tank must be replaced by a geometry that has EM-extracted
inductance, Q, self-resonance, coupling, and process variation. The oscillator
also still needs a realizable bias source, switched coarse bank, fine tuning,
startup-time and Monte Carlo checks, phase noise, supply pushing, load pulling,
and post-layout extraction.

Reproduce the data with `make lc-vco-test`. Machine-readable results are in
`lc_vco_sweep.json` and `lc_vco_sweep.csv` in this directory.

The derived coarse/fine interface is documented in
[the tuning-bank sizing result](lc-dco-bank-sizing.md).
