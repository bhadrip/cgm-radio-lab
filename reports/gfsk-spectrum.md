# BLE LE 1M GFSK adjacent-channel screen

## Result

The quantized 16 MHz GFSK waveform clears the repository's adjacent-channel
screen when normalized to the PA's worst-case 0 dBm setting.

| Offset | Negative side | Positive side | Limit | Worst margin |
|---:|---:|---:|---:|---:|
| 2 MHz | -65.627 dBm | -65.624 dBm | -20 dBm | 45.624 dB |
| 3 MHz | -99.568 dBm | -99.666 dBm | -30 dBm | 69.568 dB |
| 4 MHz | -143.549 dBm | -143.584 dBm | -30 dBm | 113.549 dB |

Integer-Hz RTL coefficient quantization changes the measured 2 MHz bands by
less than 0.001 dB relative to the floating-point reference.

## Method

A 4,096-symbol PRBS9 sequence drives the existing BT=0.5, modulation-index=0.5
reference model. Its integer-Hz frequency words are integrated into complex IQ
at 16 samples/symbol. A 65,536-point radix-2 FFT with a periodic Hann window
then integrates power in 1 MHz bands centered at +/-2, +/-3, and +/-4 MHz.
Relative band power is converted to absolute dBm using the maximum 0 dBm PA
setting, which is the worst programmed output level for this check.

## Boundary

This is a deterministic complex-envelope screening calculation, not the
Bluetooth transmitter measurement procedure or RF signoff. It excludes DCO
phase noise and spurs, PA AM-to-PM conversion and memory, PA switching edges,
harmonics, supply coupling, matching-network response, package/antenna effects,
PVT modulation distortion, and instrument filtering. The large computed margin
therefore validates the digital Gaussian shaping but cannot establish TX-001
for silicon.

Production evidence and the complete workload boundary continue to follow the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce with `make gfsk-spectrum`. Machine-readable results are in
`gfsk_spectrum.json`.
