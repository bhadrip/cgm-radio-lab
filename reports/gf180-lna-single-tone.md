# GF180 LNA maximum-input screen

## Result

At PR11's provisional -10 dBm maximum input, the normal 1.4 mA LNA state
exceeds the provisional 1 dB compression screen. The 6 mA bias-boost state
passes across all three sampled corners.

| Corner | Normal compression | Bias-boost compression |
|---|---:|---:|
| Typical, 25 C | 1.694 dB | 0.144 dB |
| Fast, -40 C | 2.289 dB | 0.155 dB |
| Slow, 85 C | 1.311 dB | 0.112 dB |

This closes the schematic-level single-tone compression screen for the boost
state. It does not close the product maximum-input requirement.

## Method and boundary

Ngspice transient simulations sweep a 2.44 GHz tone from -30 to -5 dBm. A
coherent Fourier projection measures intrinsic voltage gain relative to the
-30 dBm point for normal and boosted states at sampled PVT.

Bluetooth qualification, blockers and desensitization, bias transitions,
package and input-network effects, mismatch, extracted layout, and measured RF
remain open under the
[PR11 evidence boundary](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce with `make gf180-lna-single-tone-test`. Machine-readable results are
in `gf180_lna_single_tone.json`.
