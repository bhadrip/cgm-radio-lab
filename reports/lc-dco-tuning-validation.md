# GF180 LC-DCO tuning validation

## Result

The proposed coarse/fine network covers 2402--2480 MHz at the sampled typical,
fast, and slow corners. All 84 transistor-level points sustain oscillation, and
adjacent coarse-code tuning ranges overlap by at least 15.4 MHz.

The bench uses a 26 um square base MIM capacitor per branch, selected legal-size
5 um square MIM cells, and sixteen legal-size 1 um square NMOS capacitors. The
tail current is 1 mA. The inductor remains the explicit 3 nH, Q=10 assumption
from the parent experiment.

| Corner | Coarse codes | Sustained envelope | Minimum adjacent overlap |
|---|---:|---:|---:|
| Typical, 25 C | 4--7 | 2.352--2.528 GHz | 16.2 MHz |
| Fast, -40 C | 10--13 | 2.357--2.507 GHz | 16.6 MHz |
| Slow, 125 C | 0--3 | 2.326--2.523 GHz | 15.4 MHz |

## Product-budget context

The [PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md)
sets a provisional 15 uJ complete-report target and requires workload-level
accounting. This oscillator core draws 1.8 mW, or 0.403 uJ for one 224 us burst.
Three such bursts consume 1.21 uJ, about 8.1% of that target, before startup,
settling, PA, digital, receive, sensor, regulator, retry, and leakage energy.

## Remaining gates

Coarse cells are instantiated directly; RF switches and their parasitics are
not modeled. The fine-control source is ideal, so DAC/bias noise, resolution,
settling, and power are absent. The C-V sweep is static and does not demonstrate
1 Msym/s GFSK, spectral mask, phase noise, pulling, Monte Carlo yield, or
post-layout behavior. The inductor still requires an EM-qualified geometry.

Reproduce the sweep with `make lc-dco-test`. Machine-readable results are in
`lc_dco_sweep.json` and `lc_dco_sweep.csv` in this directory.
