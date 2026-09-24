# LC-DCO control-drive and settling requirement

## Result

The segmented DAC should present no more than 1 kOhm baseband output resistance
with a nominal 10 pF local RF bypass at the varactor-control node. This gives a
10 ns time constant and a 15.9 MHz baseband pole while holding the control node
near RF ground at 2.4 GHz. The tested 1 kOhm points pass with 10--20 pF; larger
loads are not implied to pass.

The nominal transistor bench exposes two separate effects:

| Output resistance | Bypass | Carrier pull | Mean-removed tracking error | Result |
|---:|---:|---:|---:|:---:|
| 100 Ohm | 5 pF | 43.371 kHz | 14.385 kHz | Fail pull |
| 100 Ohm | 10 pF | 24.621 kHz | 15.635 kHz | Pass |
| 1 kOhm | 5 pF | 44.621 kHz | 15.635 kHz | Fail pull |
| 1 kOhm | 10 pF | 24.204 kHz | 15.214 kHz | Pass |
| 2.5 kOhm | 10 pF | 24.412 kHz | 25.422 kHz | Pass |
| 5 kOhm | 10 pF | 28.996 kHz | 42.456 kHz | Fail tracking |

At the recommended 1 kOhm/10 pF point, one negative fast-DAC trim code removes
most static pull. The calibrated run measures 2.954 kHz mean error and
21.010 kHz worst absolute error over 48 consecutive 16 MHz samples.

## Interpretation and boundary

The first 100 Ohm/1 pF experiment missed by about 150 kHz despite a 100 ps RC
time constant. The cause was RF impedance, not baseband settling: a small bypass
does not hold the shared varactor-control terminal at AC ground. Carrier pull is
separated from mean-removed tracking because the pre-burst frequency calibration
can correct a constant offset, while it cannot correct modulation distortion.

The resistor and capacitor are ideal. Capacitor density, Q, self-resonance,
routing inductance, DAC output impedance versus frequency, code glitches,
reference noise, and device noise remain unmodeled. A 10 pF on-chip bypass also
has area and leakage costs that must be included in the physical implementation.
Complete-report power and production evidence continue to follow the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce the sweep with `make lc-dco-drive-settling`. Machine-readable results
are in `lc_dco_drive_settling.json`; the calibrated waveform is in
`lc_dco_dynamic.json`.
