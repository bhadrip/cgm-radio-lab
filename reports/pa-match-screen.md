# First PA output-network screen

## Result

The 150-ohm peak-power load from the transistor sweep maps to a first-pass
low-pass L-match of 4.612 nH series inductance and 0.615 pF shunt capacitance at
2.44 GHz when the antenna-side load is 50 ohms.

| Inductor Q | Fundamental loss | H2 rejection | H3 rejection |
|---:|---:|---:|---:|
| 5 | 1.149 dB | 6.152 dB | 13.097 dB |
| 8 | 0.736 dB | 6.078 dB | 13.195 dB |
| 10 | 0.593 dB | 6.058 dB | 13.240 dB |
| 15 | 0.400 dB | 6.038 dB | 13.310 dB |
| 20 | 0.302 dB | 6.031 dB | 13.350 dB |
| 30 | 0.202 dB | 6.025 dB | 13.393 dB |

At the screening assumption of Q=10, the inductor has 7.071 ohms series loss
at 2.44 GHz. The network would add about 13.24 dB of third-harmonic rejection,
which improves the raw PA result but does not by itself establish a regulatory
margin.

## Method

The ideal L-match equations transform a 50-ohm termination to 150 ohms at the
PA port. A linear Thevenin-source model then computes transducer gain at the
fundamental, second harmonic, and third harmonic. Constant inductor Q sets a
frequency-dependent series resistance; capacitor and interconnect loss remain
ideal.

## Boundary

This is a component-sizing screen, not a nonlinear harmonic-balance or complex
load-pull result. The 150-ohm value comes from a sparse real-load sweep, and a
switching PA is not a linear 150-ohm source. The model excludes device stress,
stability, PVT component spread, self-resonance, layout coupling, package and
antenna impedance, modulation, and realizable foundry passive geometry.

PR11 requires package/antenna co-design and measured RF/regulatory evidence;
the candidate values therefore guide the next simulation and are not a tapeout
claim. The evidence boundary follows the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce with `make pa-match-screen`.
