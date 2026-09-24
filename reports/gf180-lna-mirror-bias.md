# GF180 LNA low-headroom mirror-bias screen

## Result

A diode-referenced 16:1 NMOS current mirror cannot replace the ideal LNA source
current sink. None of six sampled geometries passes the existing current, gain,
noise, input-match, and headroom screens across PVT.

The least RF-loaded candidate uses a 20 um reference device and 320 um output
device. Even it produces only 0.842--1.009 mA instead of the screened
1.2--1.6 mA range, with these worst-case RF results:

| Metric | Result | Provisional screen |
|---|---:|---:|
| Intrinsic gain | 10.488 dB | >= 12 dB |
| Noise figure | 6.131 dB | <= 4 dB |
| Input return loss | 9.926 dB | >= 10 dB |

Increasing mirror width raises NF as high as 10.986 dB and reduces input return
loss to 1.530 dB. This implementation is rejected; the LNA bias/topology must
change rather than hiding the problem behind an ideal sink.

## Method and boundary

The reference leg draws 87.5 uA and the output leg uses a 16:1 geometry ratio.
Reference widths from 20 to 240 um are swept with GF180 3.3 V NMOS devices.
Operating-point, AC, and noise analyses run at typical/25 C, fast/-40 C, and
slow/85 C.

The reference current itself remains ideal. Alternative source resistors,
feedback LNAs, inverter-based LNAs, physical reference generation, mismatch,
layout, and measured RF remain open under the
[PR11 evidence boundary](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce with `make gf180-lna-mirror-bias-test`. Machine-readable results are
in `gf180_lna_mirror_bias.json`.
