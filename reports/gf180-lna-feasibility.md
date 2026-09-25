# First GF180 BLE LNA feasibility

## Result

A 25-candidate common-gate sweep selects a 200 um NMOS at 1.4 mA with a
728.6-ohm drain load and provisional 25 fF mixer-gate load. Five candidates
meet every sampled schematic gate.

| Corner | Intrinsic voltage gain | Noise figure | Input return loss | VDS |
|---|---:|---:|---:|---:|
| Typical, 25 C | 13.948 dB | 2.743 dB | 11.548 dB | 0.675 V |
| Fast, -40 C | 15.742 dB | 2.326 dB | 11.987 dB | 0.622 V |
| Slow, 85 C | 12.401 dB | 3.141 dB | 10.500 dB | 0.734 V |

Worst sampled active power is 2.520 mW. The candidate clears the provisional
12 dB intrinsic-voltage-gain, 4 dB noise-figure, 10 dB input-return-loss, and
0.5 V drain-source-headroom screens.

## Method

The bench uses a noisy 50-ohm source, 10 pF input coupling capacitor, GF180
3.3 V NMOS devices, an ideal source-bias current sink, resistive drain load,
and 25 fF output load. Ngspice operating-point, AC, and noise analyses run at
typical/25 C, fast/-40 C, and slow/85 C. Device width and bias current are
swept; the lowest-power passing candidate is selected.

Noise figure is calculated from ngspice input-referred noise relative to the
temperature-correct 50-ohm source thermal noise.

## Boundary

This is a first transistor feasibility point, not a complete LNA or receiver.
The reported gain is drain-to-source voltage gain into a high-impedance 25 fF
load, not matched transducer power gain or S21. The noiseless ideal bias sink
must be replaced, and the assumed mixer load must be verified.

Input matching geometry, S-parameters, unconditional stability, IIP2/IIP3,
compression, blockers, mismatch, passive PVT, extracted layout, ESD/switch
loss, startup, and duty-cycled energy remain open. PR11 requires those circuit
and measured-RF gates before production. The evidence boundary follows the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce with `make gf180-lna-test`. Machine-readable results are in
`gf180_lna.json`.
