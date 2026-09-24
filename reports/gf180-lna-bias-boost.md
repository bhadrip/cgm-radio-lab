# GF180 LNA strong-input bias boost

## Result

An eight-point bias sweep selects 6 mA as the lowest sampled temporary
strong-input state. With the drain load rescaled to 170 ohms, all three sampled
corners keep two-tone gain compression below 1 dB at -10 dBm per tone.

| Metric | Worst sampled result | Provisional screen |
|---|---:|---:|
| Gain compression | 0.848 dB | <= 1 dB |
| Strong-input intrinsic gain | 11.204 dB | >= 10 dB |
| Noise figure | 3.467 dB | <= 4 dB |
| Input return loss | 10.079 dB | >= 10 dB |
| Drain-source voltage | 0.765 V | >= 0.5 V |

The state consumes 10.8 mW, or 2.419 uJ if held for the provisional 224 us
active interval. This is an on-demand linearity state, not the normal weak-signal
operating point.

## Method and boundary

The selected 200 um device is swept at its nominal 1.4 mA and from 2 to 8 mA.
Each load is rescaled to target the same typical-corner drain voltage. AC/noise
and coherent two-tone transient analyses run at typical/25 C, fast/-40 C, and
slow/85 C.

The -10 dBm/tone stress is intentionally not presented as the PR11 single-tone
maximum-input test. Bias switching and settling, reference generation, control
logic, transition energy, blocker behavior, matching, mismatch, extracted
layout, and measured RF remain open under the
[PR11 evidence boundary](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce with `make gf180-lna-bias-boost-test`. Machine-readable results are
in `gf180_lna_bias_boost.json`.
