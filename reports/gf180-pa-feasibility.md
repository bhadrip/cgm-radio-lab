# GF180 RF output-stage feasibility

## Result

A 7-bit bank of 0.44 um NMOS / 0.88 um PMOS output slices can calibrate five
sampled power levels from -20 to 0 dBm within 0.444 dB at typical/25 C,
fast/-40 C, and slow/125 C. The bench measures the 2.44 GHz fundamental into a
broadband 50 ohm load.

| Corner | -20 dBm | -15 dBm | -10 dBm | -5 dBm | 0 dBm |
|---|---:|---:|---:|---:|---:|
| Typical, 25 C | code 8 / -20.242 | code 14 / -15.134 | code 27 / -9.982 | code 51 / -4.972 | code 94 / -0.037 |
| Fast, -40 C | code 6 / -19.810 | code 10 / -15.186 | code 19 / -9.946 | code 36 / -4.899 | code 66 / -0.031 |
| Slow, 125 C | code 12 / -19.843 | code 21 / -14.821 | code 39 / -9.956 | code 73 / -4.955 | code 128 / -0.444 |

At the selected levels, worst PA-core supply power is 4.396 mW and worst
224 us burst energy is 0.985 uJ. Drain efficiency rises from about 3% near
-20 dBm to about 22% near 0 dBm. These figures include the enabled output
devices but not their input driver.

## Architecture

The model treats the bank as 128 equal slices controlled by a calibrated power
code. The active devices are split into legal-size parallel fingers for the
transistor simulation. Only the equivalent enabled width is present in each
run; disabled-slice capacitance and the code-gating circuit are follow-up work.

## Boundary

This is an early active-device and energy feasibility result, not an RF PA
signoff result. The input is an ideal 2.44 GHz square wave, the coupling
capacitor is an ideal 10 pF element, and the load is an ideal broadband 50 ohms.
It does not establish GFSK spectral compliance, regulatory harmonic compliance,
stability, load mismatch tolerance, antenna efficiency, matching-network loss,
package parasitics, device stress, routed control power, startup energy, or
post-layout performance.

The [complex-envelope spectrum follow-on](gfsk-spectrum.md) verifies the
digital Gaussian shaping against the adjacent-channel screen before PA and
matching-network distortion are introduced.
The [harmonic follow-on](gf180-pa-harmonics.md) measures raw second- and
third-harmonic output into the same broadband load so a later output network can
be sized from evidence.

The 0.985 uJ number is only a partial allocation against PR11's provisional
15 uJ complete-report target. Oscillator, drivers, receive activity, retries,
sensor conversion, computation, storage, and sleep energy still have to share
that budget. The evidence boundary follows the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

Reproduce with `make gf180-pa-test`. Machine-readable power curves and selected
codes are in `gf180_pa.json`.
