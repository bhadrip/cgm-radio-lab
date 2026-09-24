# BLE LE 1M receiver noise budget

## Result

The first receiver allocation predicts -89.553 dBm sensitivity in a 1 MHz
noise bandwidth at the +85 C operating endpoint, leaving 9.553 dB against the
provisional -80 dBm project target and 19.553 dB against the -70 dBm Bluetooth
limit recorded by PR11.

| Stage | Gain | Noise figure |
|---|---:|---:|
| RF switch and matching | -1.5 dB | 1.5 dB |
| LNA | 12.0 dB | 4.0 dB |
| Mixer | 6.0 dB | 12.0 dB |
| Baseband channel | 30.0 dB | 20.0 dB |

Friis cascading gives 8.505 dB receiver noise figure and 46.5 dB small-signal
gain. With a provisional 15 dB detector-SNR allocation, as much as 18.059 dB
cascade noise figure would still meet -80 dBm. The design should not spend that
entire allowance: blocker tolerance, passive loss, model error, and measured
margin remain unallocated.

The required input range from -80 dBm sensitivity to the recorded -10 dBm
maximum-input test is 70 dB. The fixed 46.5 dB chain therefore needs gain
control or bypass modes before a circuit can satisfy both ends.

## Boundary

This is an algebraic architecture budget, not receiver performance evidence.
Thermal noise uses exact kT at +85 C rather than a room-temperature shortcut.
The 15 dB demodulator-SNR value and the stage allocations are provisional
engineering assumptions. BER versus SNR, blockers, image rejection, IIP2/IIP3,
compression, phase noise and reciprocal mixing, DC offsets, filtering, ADC or
limiter behavior, current, startup, and duty-cycled energy remain open.

PR11 requires PVT/noise simulation and conducted BER testing for sensitivity,
plus measured RF and Bluetooth qualification before production. The evidence
boundary follows the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce with `make rx-noise-budget`. Machine-readable results are in
`rx_noise_budget.json`.
