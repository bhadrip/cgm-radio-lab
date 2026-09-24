# LC-DCO tuning-bank sizing

## Decision

Replace the placeholder 12-bit linear capacitor code with two controls:

- a calibrated 4-bit coarse MIM bank with 16 codes; and
- analog fine control over at least sixteen minimum-size NMOS capacitors.

The existing digital error-feedback block can continue to express a frequency
request, but an analog mapping/calibration loop must produce these controls.

## Evidence

The 1 mA LC sweep gives 0.82--0.92 MHz/fF near 2.441 GHz. A 50 kHz frequency
step therefore corresponds to only 0.051--0.061 fF. The GF180 KLayout PCells set
the minimum square MIM to 5 um per side and the minimum square MOS capacitor to
1 um per side.

| Corner | Local gain | Capacitance for 50 kHz | Minimum MIM | 16-MOSCAP span | V-control step for 50 kHz |
|---|---:|---:|---:|---:|---:|
| Typical | 0.921 MHz/fF | 0.054 fF | 44.3 fF | 63.3 fF | 0.274 mV |
| Fast | 0.823 MHz/fF | 0.061 fF | 37.5 fF | 57.0 fF | 0.341 mV |
| Slow | 0.904 MHz/fF | 0.055 fF | 51.2 fF | 69.7 fF | 0.254 mV |

The PVT/channel geometry span is equivalent to about 542 fF at nominal MIM
density, or 13 minimum-MIM intervals. Sixteen coarse codes cover that range.
Sixteen minimum MOS capacitors provide more tuning span than one coarse step in
all three corners, so adjacent coarse codes can overlap.

## Consequences

The fine-control generator, its noise, and the varactor bias point are now
first-order RF requirements. At the modeled maximum-slope bias, nominal
GFSK deviation of +/-250 kHz uses only about +/-1.4 mV. Switch parasitics,
varactor Q, AM-to-PM conversion, DAC noise, fractional spurs, monotonicity, and
Monte Carlo mismatch are not included. The next circuit must close those items
before the digital controller can be connected to the oscillator.

Reproduce the sizing with `make dco-bank-sizing`; machine-readable values are
in `lc_dco_bank.json` in this directory.
