# GF180 PA harmonic characterization

## Result

The existing GF180 output-stage sweep now extracts the second and third
harmonics at every calibrated -20 to 0 dBm setting and sampled PVT corner.
These are the raw broadband-load emissions before a matching or harmonic-filter
network.

| Quantity across 15 calibrated points | Worst value |
|---|---:|
| Second-harmonic ratio | -34.071 dBc |
| Third-harmonic ratio | -8.524 dBc |
| Absolute second-harmonic power | -34.515 dBm |
| Absolute third-harmonic power | -9.068 dBm |

The strong raw third harmonic makes harmonic rejection an explicit output
network requirement. `gf180_pa.json` records absolute dBm and dBc values for
every selected point; a later slice can translate them into network attenuation
after the applicable regulatory emission allocation is fixed.

## Method

The extractor integrates the final 16 carrier cycles of each transient at
2.44 GHz, 4.88 GHz, and 7.32 GHz. It reuses the same 128-code, three-corner
transistor sweep and calibrated power selections as the PA feasibility report.

## Boundary

This characterizes harmonic voltage delivered to an ideal broadband 50 ohm
load. It is not a regulatory pass/fail test and does not include bond/package
parasitics, antenna response, a matching network, device mismatch, routed bank
capacitance, modulated operation, or independent validation that the open device
models are accurate at 4.88 and 7.32 GHz. PR11 requires measured regulatory and
RF evidence before production; this result is an input to that later
allocation, not a substitute for it.

The evidence boundary follows the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce with `make gf180-pa-test`.
