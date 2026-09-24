# Segmented LC-DCO control DAC

## Result

Split the fine-control source into a 7-bit slow bias DAC and a 6-bit fast
modulation DAC. The bias DAC spans 0.9--1.4 V and is programmed once before a
burst. Only the modulation DAC, spanning +/-8 mV, switches at 16 MHz.

Across all 32,256 packet samples and nine advertising-channel/PVT combinations,
the selected split has 3.505 mV of modulation-range headroom. Its maximum
modeled quantization error is 15.986 kHz; adding the 20 kHz calibration bound
gives 35.986 kHz, below the 40 kHz design limit.

| Bias + fast bits | Fast LSB | Voltage headroom | Combined error | Result |
|---:|---:|---:|---:|:---:|
| 6 + 6 | 254.0 uV | 0.767 mV | 35.431 kHz | Fail headroom |
| 7 + 5 | 516.1 uV | 3.505 mV | 51.361 kHz | Fail error |
| 7 + 6 | 254.0 uV | 3.505 mV | 35.986 kHz | Pass |
| 8 + 6 | 254.0 uV | 3.662 mV | 35.688 kHz | Pass, extra bias bit |

The nominal channel-37 transistor bench uses bias code 42 (1.06535 V) and only
changes the six-bit fast code. Across 48 measured samples, mean error is
5.246 kHz and worst absolute error is 11.612 kHz.

The follow-on [loaded-drive validation](lc-dco-drive-settling.md) adds finite
output resistance and RF bypass, then derives a 1 kOhm/10 pF implementation
target.

## Boundary

This is an interface architecture, not a transistor DAC. Both summed sources
are ideal apart from quantization. DNL, INL, code glitches, reference and device
noise, settling, output impedance, charge injection, area, leakage, and active
power remain circuit gates. The 7-bit bias code must be calibrated before each
burst or when temperature and supply movement invalidate it.

The split reduces the high-speed switching width from the monolithic 12-bit
candidate to six bits; it does not by itself prove a power saving. Power must be
measured and included in the complete-report accounting required by the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce the architecture sweep with `make dco-segmented-dac` and the dynamic
check with `make lc-dco-dynamic-test`. Machine-readable results are in
`lc_dco_segmented_dac.json` and `lc_dco_dynamic.json`.
