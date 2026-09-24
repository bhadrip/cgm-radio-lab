# BLE LE 1M GFSK modulator

`rtl/ble_gfsk_modulator.sv` is the digital-to-radio boundary for a future
direct-modulation transmitter. It consumes one hard bit per symbol and emits a
signed instantaneous frequency offset in integer hertz.

| Property | Value |
|---|---:|
| Symbol rate | 1 Msym/s |
| Reference clock and sample rate | 16 MHz |
| Samples per symbol | 16 |
| Gaussian BT | 0.5 |
| Nominal modulation index | 0.5 |
| Steady frequency deviation | +/-250 kHz |
| Filter span | 4 symbols |
| Causal group delay | 2 symbols |

The `bit_valid`/`bit_ready` handshake occurs once per symbol. `sample_valid`
qualifies each frequency word. Continuous input produces sixteen samples per
symbol without gaps; stalled input pauses after the current symbol while
retaining filter history.

The implementation is equivalent to a 65-tap sampled Gaussian FIR but uses five
symbol-history contributions for each of sixteen sample phases. This removes
multipliers and makes the interface suitable for a PLL/DCO or phase-accumulator
experiment. It does not model synthesizer bandwidth, DCO nonlinearity, carrier
frequency error, PA behavior, or regulatory emissions.

`model/gfsk.py` is the executable reference. Tests require unity DC gain,
constant envelope, nominal modulation index, at least 185 kHz deviation for a
settled `1010` pattern, and exact agreement between every RTL frequency word and
the quantized model.
