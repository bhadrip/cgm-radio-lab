# GF180 LNA BLE-band sweep

## Result

The selected 200 um, 1.4 mA common-gate LNA passes its provisional schematic
gates at all 40 BLE channel centers from 2.402 to 2.480 GHz across the sampled
typical, fast, and slow corners.

| Corner | Minimum gain | Maximum noise figure | Minimum input return loss |
|---|---:|---:|---:|
| Typical, 25 C | 13.851 dB | 2.745 dB | 11.536 dB |
| Fast, -40 C | 15.654 dB | 2.327 dB | 11.971 dB |
| Slow, 85 C | 12.297 dB | 3.144 dB | 10.497 dB |

The screens are at least 12 dB intrinsic voltage gain, at most 4 dB noise
figure, and at least 10 dB input return loss.

## Method and boundary

Ngspice AC and noise analyses reuse the first-LNA schematic and sample each BLE
channel center at three PVT points. The ideal noiseless bias, high-impedance
25 fF load, and other limitations of the center-frequency experiment remain.

This is not an S-parameter, stability, linearity, blocker, mismatch, passive
PVT, extracted-layout, or measured-RF result. Those gates remain open under the
[PR11 evidence boundary](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce with `make gf180-lna-band-test`. Machine-readable results are in
`gf180_lna_band.json`.
