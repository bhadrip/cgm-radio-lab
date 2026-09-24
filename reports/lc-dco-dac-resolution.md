# LC-DCO fine-control DAC resolution

## Result

A 12-bit DAC spanning 0--1.8 V is the minimum tested resolution that keeps the
modeled fine-control error within the 50 kHz allocation across all 32,256 packet
samples: three advertising channels at typical, fast, and slow corners.

| Bits | LSB | Maximum quantization error | With 20 kHz calibration bound | Pass |
|---:|---:|---:|---:|:---:|
| 10 | 1.760 mV | 108.457 kHz | 128.457 kHz | No |
| 11 | 0.879 mV | 51.567 kHz | 71.567 kHz | No |
| 12 | 0.440 mV | 27.758 kHz | 47.758 kHz | Yes |
| 13 | 0.220 mV | 13.784 kHz | 33.784 kHz | Yes |

The 12-bit choice was then applied to the transistor-level nominal channel-37
bench. Its 48 measured samples have -1.421 kHz mean error and 23.484 kHz worst
absolute error. The ideal-resolution baseline was 6.454 kHz worst error.

## Boundary

This result specifies resolution; it is not a DAC implementation. The source is
ideal except for quantization, so DNL, INL, thermal and flicker noise, reference
noise, settling, output impedance, area, and power remain unmodeled. A narrowed
or segmented range may reduce implementation cost, but must still cover the
0.99--1.31 V calibrated PVT range with startup and trim margin.

The error allocation is an engineering margin inside the Bluetooth frequency
accuracy requirement. Product power and evidence boundaries follow the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce the sweep with `make dco-dac-resolution` and the quantized dynamic run
with `make lc-dco-dynamic-test`. Machine-readable results are in
`lc_dco_dac_resolution.json` and `lc_dco_dynamic.json`.
