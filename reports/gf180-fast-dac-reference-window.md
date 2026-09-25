# GF180 fast-DAC reference-current window

## Result

Hold the fast-DAC reference current between 0.85x and 1.05x nominal over the
sampled operating conditions. The neighboring 0.825x and 1.075x points fail,
so this is a sampled requirement of -15%/+5%, not a rounded +/-15% target.

| Reference scale | Minimum headroom | Packet quantization | Carry error | Total error | Gate |
|---:|---:|---:|---:|---:|:---:|
| 0.800 | 2.669 mV | 6.291 kHz | 3.923 kHz | 46.080 kHz | fail |
| 0.825 | 2.864 mV | 6.526 kHz | 3.923 kHz | 46.512 kHz | fail |
| 0.850 | 3.060 mV | 6.369 kHz | 3.923 kHz | 46.552 kHz | pass |
| 0.900 | 3.450 mV | 7.399 kHz | 2.616 kHz | 46.668 kHz | pass |
| 1.000 | 4.231 mV | 8.176 kHz | 2.616 kHz | 48.234 kHz | pass |
| 1.050 | 4.622 mV | 7.898 kHz | 3.923 kHz | 49.658 kHz | pass |
| 1.075 | 4.817 mV | 8.636 kHz | 3.923 kHz | 50.593 kHz | fail |
| 1.100 | 5.012 mV | 8.833 kHz | 3.923 kHz | 50.987 kHz | fail |
| 1.150 | 5.403 mV | 8.908 kHz | 3.923 kHz | 51.457 kHz | fail |

The low-current boundary is set by the existing 3 mV modulation headroom
requirement. The high-current boundary is set by the 50 kHz combined error
budget as the larger LSB increases quantization and allocated INL error.

## Method

All 32,256 packet samples are remapped at every scale using the three measured
128-code PVT transfers. Calibration error, +/-0.5 LSB INL, and 25 uV RMS noise
at three sigma are included. The selected transistor gate driver is separately
re-simulated at each scale for typical/25 C, fast/-40 C, and slow/125 C; the
worst carry excursion is added to the packet error.

## Boundary

The packet mapping assumes the measured code-transfer shape scales with the
reference current. The carry path is transistor-simulated, but a reference
generator has not been designed. Reference startup, supply rejection, noise,
temperature drift, mismatch, trimming, area, and energy remain open. The
0.85x--1.05x window is therefore an input requirement for that circuit, not
evidence that the open PDK meets it.

Complete-chip power and production claims remain governed by the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce with `make gf180-fast-dac-reference-window-test`. Machine-readable
results are in `gf180_fast_dac_reference_window.json`.
