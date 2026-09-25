# LC-DCO fast-DAC transition budget

## Result

Use five thermometer-coded MSBs and two binary LSBs for the 7-bit fast
modulation DAC. This requires 31 equal thermometer elements plus two weighted
binary elements. At the 750 ps switch-skew target, its worst transition adds a
3.572 kHz frequency-error bound and keeps the combined control error at
48.879 kHz, below the 50 kHz allocation.

The calculation covers 32,247 transitions in all 32,256 packet samples across
the three advertising channels and sampled typical, fast, and slow corners.
The packet changes by at most five codes per 62.5 ns sample. Carry transitions,
not the intended sample step, set the glitch bound.

| Thermometer MSBs | Binary LSBs | Switched elements | Worst excursion | Error at 750 ps | Maximum skew | Result |
|---:|---:|---:|---:|---:|---:|:---:|
| 0 | 7 | 7 | 63 codes | 75.003 kHz | 45 ps | Fail |
| 2 | 5 | 8 | 31 codes | 36.906 kHz | 92 ps | Fail |
| 3 | 4 | 11 | 15 codes | 17.858 kHz | 192 ps | Fail |
| 4 | 3 | 18 | 7 codes | 8.334 kHz | 415 ps | Fail |
| 5 | 2 | 33 | 3 codes | 3.572 kHz | 998 ps | Pass |
| 6 | 1 | 64 | 1 code | 1.191 kHz | 3.352 ns | Pass |
| 7 | 0 | 127 | 0 codes | 0 kHz | Unbounded | Pass |

Five thermometer MSBs are the smallest passing candidate by switched-element
count. The 750 ps implementation target retains about 25% timing margin to its
998 ps calculated limit.

## Method and boundary

For each observed code transition, every changed weighted element may switch in
any order during the skew window. The model takes the largest excursion outside
the two endpoint codes, converts it through the 125.984 uV fast-DAC LSB and the
maximum measured 130.781 MHz/V tuning gain, then applies the measured 1 kOhm and
10 pF control-node time constant. The remaining glitch allocation is 4.693 kHz
after the prior quantization, INL, noise, and calibration bound.

This is a topology and timing requirement, not transistor-level glitch proof.
It does not model decoder hazards, charge injection, clock feedthrough, element
mismatch, reference movement, extracted parasitics, power, or area. The next
circuit slice must build the DAC switches, measure their transient waveform,
and include their energy in the complete-report budget required by the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

The follow-on [registered decoder](lc-dco-dac-decoder.md) removes combinational
decode hazards from the analog boundary. Physical output skew and the transistor
DAC transient remain open.

Reproduce with `make dco-dac-transition`. Machine-readable results are in
`lc_dco_dac_transition.json`.
