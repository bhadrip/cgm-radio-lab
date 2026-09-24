# GF180 current-steered fast-DAC experiment

## Result

Advance a 6+1 current-steered DAC to PVT and mismatch evaluation. Sixty-three
thermometer elements of weight two plus one binary LSB steer continuously
between matched output and dummy loads. Minimum-width 0.22 um switches and
complementary dummy devices limit charge injection.

| Measurement | Typical, 25 C | Gate |
|---|---:|:---:|
| Output range | 15.660 mV | Needs gain trim |
| Endpoint-fit INL | 0.067 LSB max | Pass |
| DNL | -0.027 to +0.054 LSB | Pass |
| Monotonic codes | 128/128 | Pass |
| Maximum active static power | 28.423 uW | Informational |
| 63 to 64 glitch at 750 ps skew | 20.777 uV | Pass |
| Glitch-equivalent frequency error | 2.717 kHz | Pass |
| Combined control-error bound | 48.024 kHz | Pass, 50 kHz limit |

The earlier 5+2 split minimized element count, but transistor switch charge left
too little margin at the same 750 ps skew. Moving one more bit into thermometer
coding cuts the carry excursion from three codes to one. It raises the logical
element count from 33 to 64 without increasing full-scale mirror current; area,
decoder load, and routing cost do increase.

## Boundary

This is a matched-device schematic result at one corner and temperature. Ideal
complementary gate drives switch the output and dummy branches together; their
real inverter delay and non-overlap behavior are not included. The 2.13% range
gain error still needs reference-current trim.

The result does not establish PVT, mismatch yield, noise, reference quality,
decoder power, post-route skew, extracted glitch, or layout area. The current
5+2 registered decoder must be revised to 6+1 before integration. Complete-chip
power and production evidence continue to follow the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce with `make gf180-fast-dac-steered-test`. Machine-readable results are
in `gf180_fast_dac_steered.json`.
