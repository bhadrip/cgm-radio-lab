# LC-DCO DAC non-ideality budget

## Result

The implementation candidate requires a 7-bit fast modulation DAC. The earlier
6-bit result covered ideal quantization only and fails once bounded static
linearity and control noise are included.

The calculation covers all 32,256 packet samples across the three advertising
channels and sampled typical, fast, and slow corners. It assumes +/-0.5 LSB
INL, +/-0.5 LSB DNL with monotonic transfer and no missing codes, and 25 uV RMS
control noise evaluated at 3 sigma.

| Fast bits | Quantization | INL contribution | 3-sigma noise | Total with 20 kHz calibration | Result |
|---:|---:|---:|---:|---:|:---:|
| 6 | 15.986 kHz | 16.179 kHz | 9.555 kHz | 61.720 kHz | Fail |
| 7 | 7.724 kHz | 8.026 kHz | 9.556 kHz | 45.307 kHz | Pass |
| 8 | 3.928 kHz | 3.997 kHz | 9.556 kHz | 37.482 kHz | Pass |

Seven bits is the minimum candidate under the 50 kHz control-error allocation.
The slow bias path remains 7 bits because its static error is removed by the
pre-burst frequency calibration.

The loaded nominal transistor bench was rerun with the 7-bit fast path. With a
two-code trim, 1 kOhm output resistance, and 10 pF bypass, it measures
-2.671 kHz mean error and 16.454 kHz worst absolute error.

## Boundary

This is a deterministic worst-case budget, not transistor mismatch or noise
simulation. INL bounds static transfer error; DNL is specified separately to
ensure monotonicity and is not double-counted as another independent voltage
error. The 25 uV RMS target includes the DAC, reference, bias, and coupled supply
noise within the relevant modulation bandwidth.

Device-level noise, PVT, mismatch Monte Carlo, reference generation, glitch
energy, layout coupling, and extracted parasitics remain open. Their power and
area must be included in the complete-report and production evidence required
by the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

The follow-on [transition budget](lc-dco-dac-transition.md) selects a
five-thermometer-MSB/two-binary-LSB encoding and derives its switch-skew target;
transistor-level glitch validation remains open.

Reproduce the budget with `make dco-dac-nonidealities`. Machine-readable values
are in `lc_dco_dac_nonidealities.json`.
