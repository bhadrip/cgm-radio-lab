# GF180 fast-DAC complementary gate driver

## Result

A minimum-size, three-inverter output path paired with a two-inverter dummy
path passes the 63-to-64 carry gate at the three sampled PVT corners. The
drivers replace the ideal complementary edges for the two elements that switch
at this carry.

| Corner | Peak glitch | Combined frequency error | Excess carry energy |
|---|---:|---:|---:|
| Typical, 25 C | 20.000 uV | 47.923 kHz | 14.242 fJ |
| Fast, -40 C | 20.000 uV | 47.923 kHz | 14.112 fJ |
| Slow, 125 C | 20.000 uV | 47.923 kHz | 14.616 fJ |

The selected inverter uses 0.22 um NMOS and 0.44 um PMOS devices. The alternate
one-output/two-dummy-stage topology at the same size fails nominally at
50.538 kHz. Increasing it to the base drive size passes nominally but costs
more transition energy than the selected three/two-stage topology.

## Method

The bench applies a 100 ps ideal logic edge to transistor inverters built from
the GF180 3.3 V MOS models. The binary element changes first and the incoming
thermometer element changes 750 ps later, matching the existing carry-skew
budget. Only those two changing elements use transistor drivers; the 62 static
elements retain DC gate sources. Both undershoot and overshoot are measured,
and the larger excursion is added to the existing packet-level frequency-error
budget.

## Boundary

This closes the ideal-complementary-edge assumption only for the tested carry
and schematic device models. The 100 ps input edge and 750 ps inter-element
skew remain imposed bench conditions. Register output loading, all-code dynamic
activity, decoder power, routed skew, extracted parasitics, simultaneous noise,
and foundry mismatch remain open. The reported energy covers the two switching
driver chains, not the decoder or complete DAC.

Complete-chip power and production claims remain governed by the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce with `make gf180-fast-dac-gate-driver-test`. Machine-readable results
are in `gf180_fast_dac_gate_driver.json`.
