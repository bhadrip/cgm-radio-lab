# LC-DCO dynamic GFSK validation

## Result

The settled, locally calibrated LC-DCO follows 48 consecutive 16 MHz Gaussian
control samples at the nominal corner on advertising channel 37 when driven by
a quantized 12-bit, 0--1.8 V control. Mean frequency error is -1.421 kHz and
worst absolute error is 23.484 kHz, below the 10 kHz mean and 50 kHz peak test
limits. Differential output is 1.096 V peak-to-peak and oscillator-core power
is 1.800 mW.

The measured sequence is the final three symbols of `0000101`; the first four
symbols provide startup time. It exercises both steady -250 kHz deviation and a
Gaussian transition toward +250 kHz while holding coarse code 6 fixed.

## Failure found and corrected

The first dynamic run used the sparse seven-point tuning curve and missed by as
much as 1.790 MHz. Local calibration initially made the miss 3.178 MHz because
the static bench measured cycles 20--70 during startup while the dynamic bench
measured after 4 us. At 1.03007 V, moving the static measurement window to
400--500 ns changed 2.40175 GHz to 2.39858 GHz, exactly matching the dynamic
bench. The full PVT sweep and local calibration were regenerated with the
settled window before the passing run.

With ideal voltage resolution, the corrected bench reached -171 Hz mean and
6.454 kHz worst error. Applying the selected 12-bit quantization raises the
worst error to 23.484 kHz; the
[DAC-resolution analysis](lc-dco-dac-resolution.md) covers all packet samples,
advertising channels, and sampled corners.

This failure is retained because it shows that a dense lookup table cannot
repair inconsistent measurement conditions.

## Product and evidence boundary

At 1.800 mW, one 224 us burst would consume 0.403 uJ and three bursts 1.21 uJ,
before startup, PA, digital, receive, sensor, regulator, retry, and leakage
energy. The 15 uJ/report comparison and required verification boundaries come
from the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

This is not RF sign-off. It covers one corner, channel, short bit sequence, and
an ideal quantized voltage source under the assumed 3 nH, Q=10 tank. It does not
establish phase noise, modulation spectrum, DAC DNL/INL/noise/power/settling,
PVT dynamic tracking, pulling, Monte Carlo yield, extracted behavior, or an
EM-qualified inductor.

Reproduce the dynamic run with `make lc-dco-dynamic-test`. Machine-readable
samples and summary metrics are in `lc_dco_dynamic.json`.
