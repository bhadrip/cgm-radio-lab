# GF180 PA real-load sensitivity

## Result

This screen holds each corner's calibrated 0 dBm power code fixed and sweeps
real loads from 25 to 200 ohms. It establishes whether 50 ohms is near the
useful power and drain-efficiency region before a matching topology is chosen.

| Corner | 50-ohm power / efficiency | Peak-power load / power | Peak-efficiency load / efficiency |
|---|---:|---:|---:|
| Typical, 25 C | -0.037 dBm / 22.6% | 150 ohm / 2.040 dBm | 200 ohm / 51.3% |
| Fast, -40 C | -0.031 dBm / 22.6% | 150 ohm / 1.966 dBm | 200 ohm / 52.9% |
| Slow, 125 C | -0.444 dBm / 21.6% | 150 ohm / 1.738 dBm | 200 ohm / 48.0% |

The sampled peak-power load is consistently 150 ohms, while efficiency keeps
rising through the 200-ohm endpoint. Therefore 50 ohms is a calibration point,
not the preferred PA load; the next network experiment should transform the
antenna-side impedance upward and recalibrate the power code.

Machine-readable results are in `gf180_pa_load_sweep.json`.

## Method

The same transistor PA bench used for power calibration is repeated at 25, 35,
50, 75, 100, 150, and 200 ohms for typical/25 C, fast/-40 C, and slow/125 C.
Each corner retains its calibrated 0 dBm code. Fundamental power, supply power,
drain efficiency, and H2/H3 ratios are extracted from the final 16 cycles.

## Boundary

This is a sparse real-resistance sensitivity sweep, not complex load-pull or a
matching-network design. It excludes reactive source/load impedances, stability,
package and board parasitics, antenna impedance, mismatch stress, modulation,
and independent high-frequency model validation. PR11 requires production RF
and regulatory evidence; this sweep only narrows the next schematic experiment.

The evidence boundary follows the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce with `make gf180-pa-load-test`.
