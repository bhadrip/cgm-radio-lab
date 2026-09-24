# GF180 PA and output-match co-simulation

## Result

A 25-point transistor-level network sweep selects 5.5 nH series inductance and
0.7 pF shunt capacitance with an inductor Q of 10 at 2.44 GHz. The fixed network
is recalibrated to 0 dBm independently at all three sampled PVT corners.

| Corner | Code | Output | Drain efficiency | 224 us energy | H3 |
|---|---:|---:|---:|---:|---:|
| Typical, 25 C | 80 | 0.008 dBm | 30.6% | 0.734 uJ | -26.550 dBc |
| Fast, -40 C | 55 | -0.024 dBm | 31.1% | 0.717 uJ | -26.600 dBc |
| Slow, 125 C | 118 | -0.013 dBm | 29.6% | 0.754 uJ | -26.422 dBc |

The network improves the worst raw third-harmonic ratio by 17.898 dB while
retaining at least eight power codes of headroom. Worst calibration error is
0.024 dB and worst PA-core burst energy is 0.754 uJ.

## Selection method

The sweep covers 4.5 to 6.5 nH and 0.5 to 0.9 pF. Each network is retuned with
an integer power code at typical/25 C, fast/-40 C, and slow/125 C. Candidates
must hold error within 0.1 dB, leave at least eight codes below the 128-code
ceiling, and remain below the existing 1 uJ PA-core burst screen. Among those,
the selection minimizes worst-corner H3 and then burst energy.

These are engineering selection screens, not Bluetooth or regulatory limits.

## Boundary

The co-simulation contains GF180 PA transistors, a 10 pF blocking capacitor, a
shunt capacitor, a series inductor, fixed Q-derived series loss, and a 50-ohm
load. It still excludes the input driver, disabled-slice capacitance, passive
PVT and self-resonance, layout coupling, package and antenna impedance,
stability, mismatch, device stress, and modulated operation.

PR11 requires qualified models, extracted verification, package/antenna
co-design, and measured Bluetooth/regulatory evidence. This result accepts a
schematic candidate for deeper verification; it is not tapeout signoff. The
evidence boundary follows the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce with `make gf180-pa-match-test`. Machine-readable results are in
`gf180_pa_match.json`.
