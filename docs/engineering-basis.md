# Engineering basis

This is the requirements ledger for the CGM radio. It distinguishes a standard
requirement from a project target and from an unanswered product question. A
number does not become a design constraint until its source and verification
method are recorded here.

## Product boundary

The product objective is a single-chip, ultra-low-power CGM sensor interface and
Bluetooth LE 1M radio for communication with a nearby phone. The present RTL is
only a test vehicle: it emits a fixed, non-connectable advertising packet and
does not implement GFSK, an RF front end, a Bluetooth controller, security, or a
production CGM profile.

The first Wafer.Space submission should therefore prove the digital control,
packet, clocking, test, and pad-integration path. It cannot validate an RF link
unless RF-qualified devices, models, passives, extraction, and an antenna/package
plan are available in the submission PDK.

## Requirements ledger

| ID | Kind | Requirement | Source | Verification | State |
|---|---|---|---|---|---|
| PHY-001 | Bluetooth | Support LE 1M: uncoded 1 Mb/s at 1 Msym/s. | Core 6.2, Vol 6, Part A, sec. 1 | Bit-accurate model, RTL simulation, RF test | Fixed |
| PHY-002 | Bluetooth | Cover 40 channels, 2402--2480 MHz, spaced 2 MHz. | Core 6.2, Vol 6, Part A, sec. 2 | Synthesizer analysis and RF test | Fixed |
| PHY-003 | Bluetooth | Use binary GFSK with BT=0.5 and modulation index 0.45--0.55. | Core 6.2, Vol 6, Part A, sec. 3.1 | Modulation simulation and RF test | Fixed |
| PHY-004 | Bluetooth | At 1 Msym/s, minimum frequency deviation is at least 185 kHz and symbol timing error is within +/-50 ppm. | Core 6.2, Vol 6, Part A, sec. 3.1 | PVT simulation and RF test | Fixed |
| PHY-005 | Bluetooth | Keep packet center-frequency error within +/-150 kHz, drift below 50 kHz, and drift rate below 400 Hz/us. | Core 6.2, Vol 6, Part A, sec. 3.3 | PVT simulation and RF test | Fixed |
| TX-001 | Bluetooth | At 1 Msym/s, adjacent-channel power is at most -20 dBm at 2 MHz offset and -30 dBm at offsets of 3 MHz or more. | Core 6.2, Vol 6, Part A, sec. 3.2.2 | Modulation/spectral simulation and RF test | Fixed |
| TX-002 | Project | Provide programmable output from approximately -20 to 0 dBm. | Architecture target | Load-pull/PVT simulation and conducted RF test | Provisional |
| RX-001 | Bluetooth | LE uncoded actual sensitivity is no greater than -70 dBm at the payload-dependent BER limit. | Core 6.2, Vol 6, Part A, sec. 4.1 | Conducted BER test | Fixed |
| RX-002 | Project | Target -80 dBm actual sensitivity without spending power for long-range operation. | Architecture target | PVT/noise simulation and conducted BER test | Provisional |
| RX-003 | Bluetooth | Operate at -10 dBm input with BER no greater than 0.1%. | Core 6.2, Vol 6, Part A, sec. 4.5 | Conducted BER test | Fixed |
| RX-004 | Bluetooth | At -67 dBm wanted power, meet LE 1M C/I limits: 21 dB co-channel, 15 dB at 1 MHz, -17 dB at 2 MHz, -27 dB at 3 MHz or more, and -9 dB at the image. | Core 6.2, Vol 6, Part A, sec. 4.2 | Two-signal BER test | Fixed |
| RX-005 | Bluetooth | Meet out-of-band blocking from 30 MHz to 12.75 GHz at the specified -30/-35 dBm blocker levels and allowed exceptions. | Core 6.2, Vol 6, Part A, sec. 4.3 | Blocker BER sweep | Fixed |
| SYS-001 | Project | Optimize energy per delivered glucose report, including startup, retries, and sleep leakage. | Product objective | Workload simulation and measured charge | Provisional |
| SYS-002 | Product | Choose connected GATT, advertising, or a hybrid transport before freezing the link layer. | Product decision | Phone prototype | Open |
| AFE-001 | Product | Define sensor current range, bias potential, noise bandwidth, electrode count, settling time, and calibration interface. | Sensor characterization | Sensor-vendor data and bench characterization | Open |
| COST-001 | Product | Whole packaged and tested chip costs less than $0.30 at a declared volume. | Product objective | Quoted wafer, yield, package, and test model | Open |
| QUAL-001 | Product | Define lifetime, battery, temperature, biocompatibility boundary, regulatory market, and reliability targets. | Product decision | Product and regulatory review | Open |

The -80 dBm and -20-to-0 dBm entries are architecture targets, not Bluetooth
requirements. The sub-$0.30 goal is not yet testable because volume, die yield,
package, probe, final test, and commercial wafer pricing are unspecified. Free
MPW access reduces prototype fabrication cost; it does not establish production
unit cost.

## Power accounting

Block power numbers are insufficient for a CGM. Track charge and energy over one
reporting interval:

```text
E_report = E_wake + E_measure + E_compute + N_tx*E_tx + N_rx*E_rx
           + P_sleep*T_sleep
P_average = E_report / T_report
```

`T_report`, retry statistics, connection behavior, battery voltage, and service
life remain inputs. Every future radio comparison must use the same workload and
report both active power and energy per successfully delivered report.

## Review gates

1. **Digital test vehicle:** reproducible simulation, synthesis, physical
   verification, timing closure, and hardware-observable BIST.
2. **Architecture:** phone transport chosen; link, noise, blocker, phase-noise,
   startup, power, area, and cost budgets close algebraically.
3. **Circuit:** schematic PVT and Monte Carlo results meet allocated margins;
   device operating points and model validity are reviewed.
4. **Layout:** extracted PVT, EM/IR, antenna, latch-up, ESD, matching, DRC, and LVS
   pass using foundry-qualified decks.
5. **Product:** package/antenna co-design, production test, qualification,
   Bluetooth qualification, regulatory approval, yield, and quoted cost close.

Passing one gate is not evidence that a later gate passes. In particular, clean
digital GDS is not evidence of RF performance or production readiness.

## Working references

Primary sources govern requirements:

- [Bluetooth Core 6.2, LE Radio Physical Layer](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-62/out/en/low-energy-controller/radio-physical-layer-specification.html)
- [GF180MCU design-rule manual](https://gf180mcu-pdk.readthedocs.io/en/latest/physical_verification/design_man.html)
- [GF180MCU analog layout guidance](https://gf180mcu-pdk.readthedocs.io/en/latest/physical_verification/design_manual/drm_10_6.html)
- [GF180MCU I/O-cell data sheet](https://gf180mcu-pdk.readthedocs.io/en/latest/IPs/IO/gf180mcu_fd_io/datasheet.html)

The reading order for design judgment is deliberately narrower than a generic RF
bibliography:

1. Behzad Razavi, [*RF Microelectronics*, 2nd ed.](https://www.pearson.com/en-us/subject-catalog/p/rf-microelectronics/P200000000562/9780137134731): noise, sensitivity, dynamic
   range, transceiver architectures, LNA, mixer, oscillator, and PA budgets.
2. Thomas H. Lee, [*The Design of CMOS Radio-Frequency Integrated Circuits*, 2nd
   ed.](https://www.cambridge.org/highereducation/books/the-design-of-cmos-radio-frequency-integrated-circuits/A81450CAE27BBDD03914214FB8AFF19A):
   passive loss, matching, phase noise, oscillators, and complete-chip
   tradeoffs.
3. Behzad Razavi, *Design of Analog CMOS Integrated Circuits*: bias, noise,
   feedback, comparators, data converters, and PVT reasoning for the AFE.
4. David Pozar, *Microwave Engineering*: transmission lines, S-parameters,
   matching networks, and passive structures.
5. Steve Cripps, *RF Power Amplifiers for Wireless Communications*: PA classes,
   load lines, efficiency, and nonlinear verification.
6. Allen Bard and Larry Faulkner, *Electrochemical Methods*: the sensor/electrode
   physics that must precede potentiostat and readout design.

The community lists in
[r/rfelectronics](https://www.reddit.com/r/rfelectronics/comments/i4tbu2/an_rf_book_list/)
and [r/chipdesign](https://www.reddit.com/r/chipdesign/) are useful for discovering
references and practical failure modes. They are not specification sources;
claims taken from them must be checked against standards, foundry documents,
textbooks, measurements, or peer-reviewed work.
