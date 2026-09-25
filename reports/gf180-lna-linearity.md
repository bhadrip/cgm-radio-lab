# GF180 LNA two-tone linearity screen

## Result

Two equal tones at 2.430 and 2.450 GHz bracket 1 dB gain compression between
-20 and -15 dBm per tone at every sampled corner.

| Corner | Low-level gain | Two-tone 1 dB compression bracket | Minimum uncompressed finite-level IIP3 estimate |
|---|---:|---:|---:|
| Typical, 25 C | 13.866 dB | -20 to -15 dBm/tone | 0.009 dBm |
| Fast, -40 C | 15.652 dB | -20 to -15 dBm/tone | -0.070 dBm |
| Slow, 85 C | 12.325 dB | -20 to -15 dBm/tone | 0.958 dBm |

At -10 dBm per tone, gain is compressed by 4.17 to 6.27 dB. The result
supports adding gain control or bypass before evaluating the PR11 maximum-input
condition; it does not establish that single-tone requirement.

## Method and boundary

Ngspice transient simulations drive the selected LNA with coherent equal-power
tones. Trapezoidal Fourier projections extract the fundamentals and 2f1-f2 /
2f2-f1 products. IIP3 is reported conservatively from points within 0.5 dB of
the -30 dBm/tone gain; it is a finite-level estimate, not an extrapolated or
measured IIP3.

The ideal bias, provisional mixer load, package, matching, blockers, mismatch,
layout extraction, and measured RF remain open under the
[PR11 evidence boundary](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce with `make gf180-lna-linearity-test`. Machine-readable results are in
`gf180_lna_linearity.json`.
