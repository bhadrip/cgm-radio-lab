# GF180 fast-DAC switched-current experiment

## Decision

Reject the first PMOS mirror plus series-switch cell for the fast modulation
DAC. Its nominal static transfer is suitable, but its carry-transition glitch
exceeds the frequency-error allocation.

The 5+2 array uses 31 current elements of weight four and binary elements of
weights one and two. A 125.984 nA reference, 1 kOhm summing resistor, and 10 pF
control-node bypass target the 16 mV fast-DAC range selected by the earlier
budgets.

| Measurement | Nominal result | Gate |
|---|---:|:---:|
| Output range | 15.710 mV | Needs gain trim |
| Endpoint-fit INL | 0.072 LSB max | Pass |
| DNL | -0.030 to +0.051 LSB | Pass |
| Monotonic codes | 128/128 | Pass |
| Maximum active static power | 28.50 uW | Informational |
| 63 to 64 glitch at 750 ps skew | 150 uV | Fail |
| Glitch-equivalent frequency error | 19.617 kHz | Fail |
| Combined control-error bound | 64.924 kHz | Fail, 50 kHz limit |

The measured glitch is much larger than the 27.3 uV code-ordering-only bound.
That difference is the transistor effect the prior model intentionally left
open: switch charge injection and mirror-current recovery dominate the carry.
The 1.81% range gain error can be trimmed through reference current; it is not
the rejection reason.

## Boundary and next step

This is a typical-corner, 25 C schematic experiment with matched devices and an
ideal slow-bias source. The 28.50 uW figure excludes the registered decoder,
slow DAC, reference generation, calibration, leakage, and oscillator. No PVT,
mismatch, noise, extracted parasitics, or layout area is claimed.

The next candidate should steer current continuously between the output and a
matched dummy node, or cancel switch charge differentially, then repeat this
same 63 to 64 transient before broader PVT work. Complete-chip power and
production evidence remain governed by the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce with `make gf180-fast-dac-test`. Machine-readable code and transition
measurements are in `gf180_fast_dac.json`.
