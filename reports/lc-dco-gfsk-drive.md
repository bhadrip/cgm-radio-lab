# BLE GFSK to LC-DCO drive mapping

## Result

A single calibrated coarse code covers the complete +/-250 kHz modulation range
for every advertising channel at each sampled PVT corner. The full 224-bit CGM
packet maps to 3,584 fine-control samples without saturation or coarse switching.

| Corner | Channel 37 code | Channel 38 code | Channel 39 code |
|---|---:|---:|---:|
| Typical, 25 C | 6 | 6 | 4 |
| Fast, -40 C | 12 | 11 | 10 |
| Slow, 125 C | 2 | 1 | 0 |

Across the nine calibrations, center control voltage is 0.99--1.31 V and the
packet waveform spans 4.04--7.08 mV peak-to-peak. The largest 16 MHz sample step
is 0.660 mV, equivalent to 0.0106 V/us. The smallest margin between the nominal
modulation range and a selected coarse-code endpoint is 9.57 MHz.

## Method and boundary

The packet bits, whitening, Gaussian BT=0.5 filter, 1 Msym/s rate, and 16 MHz
sample stream come from the existing independent Python models. Fine voltage is
the piecewise-linear inverse of the settled transistor-level sweep plus local
calibration at center and +/-250 kHz. The final calibration residual is at most
20 kHz across the nine channel/corner combinations. Tests round-trip each
request through that mapping.

The nominal channel-37 mapping is exercised dynamically in
[the transistor-level validation](lc-dco-dynamic-validation.md). The ideal
fine source is quantized by the
[DAC-resolution analysis](lc-dco-dac-resolution.md), which selects 12 bits over
0--1.8 V. DAC non-idealities and power, phase noise, fractional spurs, and the
transmitted spectrum are not measured. Those checks are required by the
verification ladder in the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce the local calibration with `make lc-dco-local-calibration`, then the
mapping with `make dco-modulation`. Summary results are in
`lc_dco_modulation.json`; the nominal channel-37 waveform is in
`lc_dco_modulation_nominal_ch37.csv`.
