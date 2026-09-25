# GF180 current-steered fast-DAC mismatch sensitivity

## Result

Treat 2.0% as the maximum one-sigma single-unit current mismatch for this 6+1
fast-DAC candidate. At that assumption, 49,984 of 50,000 seeded device
populations pass the +/-0.5 LSB INL/DNL limits at all three measured PVT
transfers. The observed yield is 99.968%; its one-sided 95% Wilson lower bound
is 99.952%, above the 99.9% screening target. The next sampled assumption,
2.25%, fails that target.

| Single-unit sigma | Passing trials | Observed yield | 95% lower bound | P99.9 max INL | P99.9 max DNL | Gate |
|---:|---:|---:|---:|---:|---:|:---:|
| 1.00% | 50,000 | 100.000% | 99.995% | 0.266 LSB | 0.123 LSB | pass |
| 1.50% | 50,000 | 100.000% | 99.995% | 0.372 LSB | 0.156 LSB | pass |
| 2.00% | 49,984 | 99.968% | 99.952% | 0.461 LSB | 0.191 LSB | pass |
| 2.25% | 49,912 | 99.824% | 99.790% | 0.512 LSB | 0.210 LSB | fail |
| 2.50% | 49,645 | 99.290% | 99.226% | 0.583 LSB | 0.224 LSB | fail |

## Method

Each trial starts with the 128-code transistor transfer measured at
typical/25 C, fast/-40 C, and slow/125 C. It adds independent Gaussian current
errors to the 63 weight-two thermometer sources and the one binary source. The
weight-two sources use `sigma/sqrt(2)` relative mismatch to reflect twice the
active device area. The same device population is evaluated at every corner,
and a trial passes only if every corner passes. Endpoint gain is removed, as it
is in the calibrated INL definition.

## Boundary

This is a reproducible behavioral sensitivity analysis, not foundry device
Monte Carlo. The open GF180 models used here do not supply a qualified mismatch
distribution for this circuit. Spatial correlation, systematic gradients,
reference-current mismatch and noise, extracted layout parasitics, and package
effects are not modeled. The result therefore creates a layout/device-sizing
requirement; it does not prove the process meets it.

Production evidence still requires qualified foundry mismatch models and
extracted-layout statistical verification. Complete-chip power, energy, and
product claims remain governed by the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce with `make gf180-fast-dac-mismatch-test`. Machine-readable results
are in `gf180_fast_dac_mismatch.json`.
