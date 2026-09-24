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

The first circuit experiment is documented in the
[GF180 ring-oscillator feasibility result](../reports/ring-dco-feasibility.md).
It rules out that topology for the BLE LO across the tested PVT corners; it does
not change this controller interface.

The subsequent [LC-oscillator feasibility result](../reports/lc-vco-feasibility.md)
brackets the BLE band with the PDK transistor and MIM-capacitor models, but only
under an explicit lumped-inductor/Q assumption. It is not yet a realizable DCO.

[Physical tuning-bank sizing](../reports/lc-dco-bank-sizing.md) shows that the
12-bit linear code cannot map directly to legal MIM units. Preserve the
frequency-request/error-feedback logic, but split the physical interface into a
calibrated 4-bit coarse MIM code and analog MOS-varactor fine control.

The [transistor-level tuning validation](../reports/lc-dco-tuning-validation.md)
confirms that adjacent coarse codes overlap and the sampled envelope covers the
BLE band at typical, fast, and slow corners under the assumed tank model.

The [GFSK drive mapping](../reports/lc-dco-gfsk-drive.md) selects one calibrated
coarse code before each burst and maps the modulator frequency stream onto the
fine-control voltage without switching the coarse bank during the packet.
The [dynamic validation](../reports/lc-dco-dynamic-validation.md) checks that
mapping over 48 nominal-corner samples after oscillator startup.
