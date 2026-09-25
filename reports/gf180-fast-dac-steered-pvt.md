# GF180 current-steered fast-DAC PVT gate

## Result

The 6+1 current-steered fast DAC passes the static-linearity and 750 ps carry
transition gates at the sampled typical/25 C, fast/-40 C, and slow/125 C
conditions.

| Corner | Range | Max INL | DNL range | Carry glitch | Combined error | Max active power |
|---|---:|---:|---:|---:|---:|---:|
| Typical, 25 C | 15.660 mV | 0.067 LSB | -0.027 to +0.054 LSB | 20.777 uV | 48.024 kHz | 28.423 uW |
| Fast, -40 C | 15.620 mV | 0.063 LSB | -0.024 to +0.057 LSB | 21.477 uV | 48.116 kHz | 28.354 uW |
| Slow, 125 C | 15.720 mV | 0.074 LSB | -0.031 to +0.050 LSB | 20.565 uV | 47.997 kHz | 28.536 uW |

The fast/-40 C transition is the closest frequency-error case, retaining
1.884 kHz below the 50 kHz limit. The slow/125 C transfer sets the largest INL,
and all 128 codes remain monotonic at every sampled corner.

## Boundary

The ideal 125.984 nA reference current is held constant across this sweep, so
this is a device/switch PVT result rather than a reference-generator PVT result.
Endpoint gain error is removed when calculating INL and remains a calibration
requirement. The model still assumes ideal complementary gate timing and matched
devices.

Mismatch Monte Carlo, reference variation and noise, decoder power, post-route
skew, extracted parasitics, and layout area remain open. Complete-chip power and
production evidence continue to follow the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce with `make gf180-fast-dac-steered-pvt-test`. Machine-readable results
are in `gf180_fast_dac_steered_pvt.json`.
