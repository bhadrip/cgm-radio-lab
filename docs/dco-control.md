# Calibrated DCO control boundary

`rtl/ble_dco_controller.sv` converts the GFSK modulator's signed integer-Hz
request into a calibrated 12-bit tuning code. The default contract uses a
nominal DCO gain of 50 kHz/LSB, which the circuit must meet or replace after
characterization. A first-order error accumulator alternates
adjacent codes, preserving sub-LSB average frequency. Fixed thresholds and
constant additions avoid dividers and multipliers in the synthesized path.

`base_code` is not a design constant. Firmware must obtain it from a frequency
calibration loop for the selected BLE channel. The controller reports
`saturated` when the requested modulation falls outside the available code
range; a usable calibration must leave at least five codes of margin on both
sides for the nominal +/-250 kHz deviation.

The model also defines the BLE channel-center map, including advertising
channels 37 (2402 MHz), 38 (2426 MHz), and 39 (2480 MHz). It does not claim that
a transistor-level oscillator meets tuning range, phase noise, modulation
bandwidth, startup time, or power. Those are measurement gates for the DCO and
PLL circuit slice.
