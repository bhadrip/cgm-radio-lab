# CGM chip market research

Research date: 2026-09-23

## Executive summary

The strongest product opportunity is not a general-purpose Bluetooth SoC with
more protocols or maximum radio range. It is a CGM-specific SoC that combines:

- a single production electrochemical channel, with a second channel as a
  product-option target;
- a deliberately small Bluetooth LE 1M subsystem;
- secure processing, storage, boot, and update;
- very low sleep and continuous-bias current; and
- enough memory to recover measurements after a phone disconnects.

Public information does not expose meaningful die-level specifications for the
custom silicon inside Abbott, Dexcom, Medtronic, or Senseonics products. The
most useful public comparisons are therefore commercial Bluetooth SoCs,
electrochemical sensor AFEs, public CGM reference designs, and measured research
silicon.

For a near-term physical product benchmark, the most relevant public design is
Texas Instruments' TIDA-010300. It combines a CC2340R5 Bluetooth MCU, a
two-channel electrochemical AFE, temperature sensing, and low-quiescent-current
power conversion in a board smaller than 20 mm in diameter. For a future custom
chip, the differentiator should be integrating those functions while removing
the unused multiprotocol and general-purpose features of commercial SoCs.

The companion [local verification and EDA setup report](pr11-local-verification-report.md)
turns these requirements into an execution approach. It identifies the
engineering roles, proposes an open-source Apple Silicon toolchain, defines the
simulation and evidence ladder for digital, analog, RF, firmware, package, and
board work, and separates what can be established locally from the foundry,
qualification-lab, and measured evidence required for production tapeout.

The separate [agentic EDA landscape and PR11 adoption plan](pr11-agentic-eda-landscape.md)
surveys commercial and open-source agentic engineering systems, then recommends
a controlled Codex-centered architecture with deterministic tools, independent
closure checks, and traceable evidence rather than autonomous signoff.

## Commercial Bluetooth SoCs

The current figures below are vendor-quoted typical values near 3 V. Test
conditions differ, so they are architecture benchmarks rather than a strict
laboratory ranking.

| Device | BLE 1M sensitivity | RX / TX at 0 dBm | Low-power state | Memory and smallest relevant package | Best CGM use |
|---|---:|---:|---:|---|---|
| Renesas DA14531 | -94 dBm | 2.2 / 3.5 mA system current | 240-270 nA hibernation; about 0.7-0.75 uA with RAM retention | 48 KB RAM, ROM BLE stack, 32 KB OTP; 1.7 x 2.0 mm WLCSP | Small, low-cost disposable proof of concept; limited memory and security headroom |
| Silicon Labs EFR32BG27 | -99.2 dBm | 3.6 / 4.1 mA system current | 1.6 uA with RTC and 64 KB RAM; 0.18 uA shutdown | Up to 768 KB flash and 64 KB RAM; 2.3 x 2.6 mm WLCSP | Strong medical product baseline with secure boot, protected keys, TrustZone, ECC, and anti-tamper features |
| Nordic nRF54L15 | -96 dBm | 3.4 / 4.8 mA vendor system headline | 0.7-2.9 uA depending on retention | 1.5 MB NVM and 256 KB RAM; approximately 2.45 x 2.25 mm WLCSP | Excellent security and software headroom, but substantially overprovisioned for a disposable CGM |
| TI CC2340R5 | -96.5 dBm | 5.3 / 5.1 mA | Less than 0.71 uA with RTC and full RAM retention; 165 nA shutdown | 512 KB flash and up to 64 KB RAM; 2.2 x 2.6 mm WCSP; integrated balun | Best near-term public CGM reference platform |
| Renesas DA14592 | -96 to -97 dBm | 1.2 / 2.3 mA radio-only current | Less than 100 nA hibernation; 3.5 uA with all RAM retained | 256 KB flash and 96 KB RAM; 3.32 x 2.48 mm WLCSP | Promising newer radio and security benchmark, but its radio-only current is not directly comparable with full-system figures |

Primary vendor sources:

- [Renesas DA14531 data sheet](https://www.renesas.com/en/document/dst/da14531-datasheet)
- [Silicon Labs EFR32BG27 product page](https://www.silabs.com/wireless/bluetooth/efr32bg27-series-2-socs)
- [Silicon Labs EFR32BG27 security features](https://www.silabs.com/documents/public/data-shorts/efr32bg27-data-short.pdf)
- [Nordic nRF54L15 product page](https://www.nordicsemi.com/Products/nRF54L15)
- [Nordic nRF54L series security overview](https://www.nordicsemi.com/Products/nRF54L15)
- [TI CC2340R5 product page](https://www.ti.com/product/CC2340R5)
- [Renesas DA14592 product page](https://www.renesas.com/en/products/da14592)

### Radio energy against the current packet

The repository's current CGM packet occupies 224 us at 1 Msym/s. Using the
vendor system-current figures above and a 3 V supply, one 0 dBm transmit burst
would consume approximately:

| Device | Energy for one 224 us burst | Energy for three such bursts |
|---|---:|---:|
| DA14531 | 2.35 uJ | 7.06 uJ |
| EFR32BG27 | 2.76 uJ | 8.27 uJ |
| nRF54L15 | 3.23 uJ | 9.68 uJ |
| CC2340R5 | 3.43 uJ | 10.28 uJ |

These derived values exclude oscillator and radio startup, MCU work, receive
windows, inter-frame spacing, retries, and regulator loss. They show why a
three-channel advertising-only design is not automatically the lowest-energy
production transport. A better product architecture is authenticated connected
operation for periodic measurements, with advertising reserved for discovery
and link recovery.

## Electrochemical sensor AFEs

| Device | Relevant specifications | CGM assessment |
|---|---|---|
| ADI MAX30131/MAX30132/MAX30134 | One, two, or four channels; up to four 16-bit current ADCs; programmable 0.8 pA to 30 pA resolution; 3.5 uA continuous bias for one sensor plus 0.25 uA for each additional sensor; electrochemical impedance spectroscopy; 2.93 x 2.93 mm WLP | Best direct public CGM AFE benchmark; explicitly intended for CGMs and two- or three-terminal electrochemical sensors |
| ADI AD5940/AD5941 | Low-power TIA spanning 50 pA to 3 mA; impedance engine; sequencer and 6 KB SRAM; 6.5 uA with the low-power potentiostat active; 3.6 x 4.2 mm WLCSP | Best sensor-development and characterization AFE; too feature-rich for the final lowest-cost disposable |
| TI LMP91000 | Analog-output potentiostat; programmable 2.75 kohm to 350 kohm TIA; about 10 uA active and 0.6 uA deep sleep; 4 x 4 mm WSON | Simple and inexpensive, but it requires an external ADC and is less integrated than the MAX3013x family |
| Undisclosed TI electrochemical AFE | Public reference material describes two channels and support for two-, three-, and four-electrode configurations | Used by TI's current CGM reference design, but its part number and detailed electrical specification are not public |

Primary vendor sources:

- [ADI MAX30134 product page](https://www.analog.com/en/products/max30134.html)
- [ADI AD5940 product page](https://www.analog.com/en/products/AD5940.html)
- [TI LMP91000 data sheet](https://www.ti.com/lit/ds/symlink/lmp91000.pdf)
- [TI TIDA-010300 CGM reference design](https://www.ti.com/tool/TIDA-010300)

The general-purpose ADCs in the Bluetooth SoCs are not substitutes for a CGM
potentiostat. The sensor needs controlled electrode bias, low input current and
noise, programmable transimpedance, continuous bias during low-power periods,
and sensor diagnostic support.

## Current product-level benchmark

The FreeStyle Libre 3 Plus is a useful external product benchmark: it is sold as
a 15-day sensor and automatically sends a glucose reading every minute. The
Dexcom G7 sends a reading every five minutes over a ten-day wear period plus a
12-hour grace period. These are complete system characteristics, not chip
specifications, but they establish the workload and user expectation that the
electronics must support.

- [Abbott FreeStyle Libre 3 Plus](https://www.freestyle.abbott/us-en/products/freestyle-libre-3.html)
- [Dexcom G7 sensor](https://www.dexcom.com/en-GB/dexcom-shop/g7/stp-gt-001?ipc=US)

A one-minute reporting interval produces 21,600 measurements over 15 days. The
repository's present eight-byte record alone would require 172,800 bytes to
retain the complete session before adding timestamps, integrity metadata, and
flash-management overhead. This supports a target of approximately 512 KB total
NVM: part for firmware and secure update, and part for measurement history.

## Fit with the current repository

The current project is a valid digital test vehicle, not yet a CGM SoC. Its
implemented scope includes:

- an eight-byte sequence, glucose, trend, status, and battery payload;
- a fixed BLE LE 1M legacy advertising packet;
- CRC, whitening, transmit/receive loopback, and BIST;
- a multiplier-free Gaussian GFSK shaper producing 16 frequency-control samples
  per symbol from the 16 MHz clock; and
- a GF180 digital implementation with completed physical verification and
  timing checks for the committed slices.

It does not yet contain:

- a potentiostat, TIA, ADC, temperature channel, or sensor diagnostics;
- a synthesizer, PA, LNA, mixer, receive baseband, RF switch, matching network,
  or antenna plan;
- a production Bluetooth controller and link layer;
- an application processor, firmware memory, measurement-history store, secure
  boot, device keys, authenticated pairing, or secure update; or
- measured radio power, sensitivity, blocker performance, startup time, RF
  area, yield, or production cost.

The laboratory company identifier `0xFFFF` and fixed manufacturer-specific
advertising packet must not become the production protocol. Bluetooth defines a
Continuous Glucose Monitoring Service with authenticated characteristics,
periodic measurement notification, stored-record recovery, trend and quality
fields, status reporting, and optional end-to-end CRC.

- [Bluetooth Continuous Glucose Monitoring Service 1.0.2](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/CGMS_v1.0.2/out/en/index-en.html)
- [Bluetooth Continuous Glucose Monitoring Profile 1.0.2](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/CGMP_v1.0.2/out/en/index-en.html)

## Recommended competitive specification

### Product requirement

> Design and validate a single-chip electrochemical CGM sensor SoC integrating
> a potentiostat/current-measurement AFE, temperature and battery monitoring,
> low-power processing and storage, and a Bluetooth LE 1M radio. The chip shall
> acquire one glucose-sensor measurement every 60 seconds, securely deliver CGM
> records to a phone or insulin-delivery controller, retain measurements during
> disconnection, operate for at least 15 days from a small primary cell, support
> a two-year product shelf life, and cost less than $0.30 per packaged-and-tested
> good unit at a committed annual volume of at least 50 million units.

The electrode, glucose-sensitive chemistry, battery, antenna, RF matching
components, 32 MHz crystal, and mechanical patch are external to the chip and
to its cost. Clinical accuracy and MARD are system properties; the chip enables
them but cannot guarantee them independently of the sensor, calibration, and
algorithm.

The table distinguishes contractual production requirements from
best-in-business goals. A value in the goal column must not silently become a
tapeout requirement without power, area, yield, and cost evidence.

| Domain | Production requirement -- shall | Best-in-business goal |
|---|---|---|
| CGM workload | Measure and either notify or queue one record every 60 seconds | Configurable 30-300 second interval without a hardware change |
| Sensor interface | One two- or three-terminal electrochemical channel with working, reference, and counter-electrode support | A second working-electrode or background channel |
| AFE | Continuously programmable potentiostat, 12-bit-or-better bias DAC, and 16-bit current ADC | Autonomous sensor-integrity or impedance measurement |
| Provisional AFE range | Programmable 50 nA, 100 nA, 250 nA, 500 nA, 1 uA, and 2 uA full-scale ranges | No greater than 1 pA resolution in the lowest range |
| Monitoring | On-chip temperature and battery-voltage measurement with programmable alarms | Autonomous temperature compensation and external-temperature input |
| Bluetooth PHY | LE 1M GFSK on all 40 channels with Core-compliant modulation, timing, blocking, and coexistence behavior | Do not add 2M, coded PHY, mesh, direction finding, channel sounding, or multiprotocol hardware unless a product requirement justifies it |
| CGM transport | Bluetooth CGM Service and Profile; connected encrypted notifications; advertising only for discovery and recovery | Interoperable phone and pump/controller operation |
| Link behavior | One active collector at a time, stored-record recovery, and at least two retained bonds | Link-loss detection within 30 seconds and alarm delivery within 60 seconds |
| TX output | Programmable from approximately -20 to 0 dBm; normal CGM setting from -8 to -4 dBm | 0 dBm without materially increasing delivered-report energy |
| Receiver | Sensitivity no worse than -92 dBm under Bluetooth LE 1M qualification conditions; tolerate a -10 dBm wanted input | Sensitivity no worse than -94 dBm |
| Conducted link budget | At least 92 dB at maximum configured TX power | At least 96 dB without an external PA |
| Report energy | No greater than 15 uJ for a successful encrypted report, including oscillator and PLL startup, processing, and three link-layer packets | No greater than 10 uJ |
| Continuous AFE current | No greater than 4 uA for one biased and measured sensor | No greater than 3.5 uA |
| Complete-IC average | No greater than 7 uA at 3 V under the defined one-minute workload | No greater than 5 uA |
| Retention sleep | No greater than 800 nA with RTC and required state retained | No greater than 500 nA |
| Shipping mode | No greater than 100 nA | No greater than 50 nA |
| Supply | Operate from 1.2 to 3.6 V and support 1.5 V silver-oxide and 3 V lithium system architectures | Cold-start at or below 1.1 V |
| Measurement storage | Retain all 21,600 one-minute records from a 15-day session without a collector | Add timestamped alarm, reset, and connectivity history |
| Memory | At least 512 KB total ROM/NVM-equivalent capacity, including at least 256 KB writable storage, plus at least 64 KB SRAM | Signed delta update without the cost of two complete firmware images |
| Security | Unique identity, TRNG, protected per-device keys, secure boot, signed update, anti-rollback, and production debug lock | Isolated root of trust, lifecycle states, and device attestation |
| BLE security | LE Security Mode 1 Level 4 after authenticated QR, NFC, or other out-of-band commissioning | No unauthenticated Just Works pairing in the production configuration |
| Clocking | At most one external 32 MHz crystal; no 32 kHz crystal required | Crystal-less option only after frequency and RF validation |
| Package | WLCSP no larger than 2.5 x 2.5 mm with minimal external RF components | Integrated balun and no more than two RF matching passives |
| Environment | Silicon operation from -40 C to +85 C; characterized CGM performance over the sensor's specified on-body range | Reliability data suitable for a regulated wearable program |
| Cost | Less than $0.30 manufacturing cost per good packaged-and-tested unit at mature yield and at least 50 million units/year | Preserve the target at lower committed volume after yield maturity |

The AFE range is a provisional market-derived envelope rather than a substitute
for sensor data. The current MAX30131 family supports 16-bit conversion,
50 nA-to-2 uA full-scale ranges, resolution down to 0.8 pA, and approximately
3.5 uA continuous bias current for one sensor. It therefore provides a useful
competitive baseline for the custom AFE.

- [ADI MAX30131/MAX30132/MAX30134 data sheet](https://www.analog.com/media/en/technical-documentation/data-sheets/max30131-max30132-max30134.pdf)

### Acceptance workload

Power and energy claims shall use a reproducible workload rather than a
datasheet sleep-current headline:

1. Operate at 3.0 V and 25 C, followed by characterization across process,
   supply, and temperature corners.
2. Continuously bias one electrochemical channel.
3. Complete one 16-bit current conversion and one temperature measurement
   every 60 seconds.
4. Send one authenticated and encrypted CGM notification every 60 seconds at
   -4 dBm.
5. Budget three link-layer packets per report, including acknowledgements or
   normal retries.
6. Retain the RTC, complete measurement history, bond information, keys, and
   alarm state.
7. Include oscillator and PLL startup, CPU work, encryption, receive windows,
   regulator loss, and flash maintenance in complete-IC average current.
8. Characterize initial pairing, reconnection, prolonged link loss, alarm
   delivery, history recovery, and firmware update separately.

The 1 Mbps value is the BLE PHY rate, not an application-throughput
requirement. A CGM generates only a few bytes per minute. The Bluetooth CGM
Service permits a minimum six-byte measurement record and provides a Record
Access Control Point for missed-data recovery. Wake-up, listening, retries,
storage, and security therefore dominate radio energy, not payload throughput.

### Security and safety basis

CRC protects against accidental transmission errors but is not a security
control. The production design shall use authenticated key establishment,
AES-CCM link encryption, protected device keys, signed firmware, and rollback
prevention. FDA cybersecurity guidance specifically discusses authenticating
telemetry, including CGM-to-insulin-pump communication. Bluetooth LE Security
Mode 1 Level 4 provides authenticated LE Secure Connections and 128-bit link
encryption. A displayless sensor should use a QR code, NFC, or factory-provisioned
out-of-band secret rather than unauthenticated Just Works pairing.

- [FDA cybersecurity guidance for medical devices](https://www.fda.gov/media/119933/download)
- [Bluetooth Generic Access Profile security modes](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-54/out/en/host/generic-access-profile.html)
- [FDA-recognized IEEE 2621.2-2022 connected-diabetes-device security standard](https://www.accessdata.fda.gov/scrIpts/cdrh/cfdocs/cfStandards/detail.cfm?standard__identification_no=43895)

### Cost definition

The $0.30 target means average manufacturing cost per good packaged-and-tested
unit at mature production yield and a committed volume of at least 50 million
units per year. It includes fabricated die, yield loss, wafer probe, bumping
and WLCSP, final test, expected scrap, and retest. It excludes sensor chemistry,
electrode, battery, antenna, PCB, external crystal/passives, mechanical patch,
and one-time development, qualification, mask, and tooling costs.

A preliminary internal allocation of $0.15 for the yielded die, $0.07 for WLCSP,
$0.04 for test, and $0.04 for yield/scrap reserve is a planning guardrail, not
a public-market fact. The requirement passes only when foundry, OSAT, test, IP,
and yield quotations close the complete cost model. A $0.30 customer selling
price is a different and substantially harder requirement because it also must
fund amortization and supplier margin.

### Sensor-characterization gate

Do not freeze or tape out the production AFE until the selected sensor has been
characterized across glucose concentration, temperature, process variation,
and the full wear period for:

- minimum, typical, and maximum sensor current;
- working-to-reference bias voltage and safe electrode limits;
- source impedance, electrode capacitance, noise spectrum, and relevant
  bandwidth;
- startup, wetting, settling, drift, and aging over at least 15 days;
- temperature coefficient and calibration model;
- oxygen, drug, and other interferent response; and
- the value of a second channel or impedance test for detecting sensor faults.

Those results freeze the ADC ranges, input-referred-noise limit, DAC range,
sampling/integration time, calibration storage, and sensor self-test. Until
then, they remain provisional architecture targets.

The -92 dBm receiver requirement is a deliberate change from the current provisional
-80 dBm goal. Commercial radios achieve approximately -94 to -99 dBm on LE 1M,
so -80 dBm would look weak in a product even if it were adequate at short range.
At the same time, a CGM should not spend energy and area chasing sensitivity it
does not need. The design should optimize energy per successfully delivered
report under body shadowing, coexistence, and retry conditions.

Measured research silicon shows that the radio goals are aggressive but useful:

- A 2025 medical-band transceiver measured -93 dBm sensitivity at 2.25 mW RX,
  5.45 mW TX consumption at 0 dBm output, and 0.48 mm2 active area.
- A 2024 BLE receiver demonstrated 167 uW using a passive-intensive RF front
  end, although it was a receiver block rather than a complete product radio.

Sources:

- [2025 compact medical-band transceiver](https://ieeexplore.ieee.org/document/10887323/)
- [2024 167 uW BLE receiver](https://ieeexplore.ieee.org/document/10454307/)

## Recommended development direction

1. Use the CC2340R5 plus MAX30132 as the external benchmark platform. Measure
   its real energy per one-minute report, reconnect behavior, sensor noise, and
   battery life under the same workload intended for the custom chip.
2. Continue the GF180 implementation as a digital and test-flow vehicle. Do not
   present its clean digital layout as evidence of RF, AFE, product, or cost
   readiness.
3. Characterize the actual electrode before freezing the AFE: current range,
   bias potential, input-referred noise, required bandwidth, drift,
   temperature response, settling, redundancy, and impedance-test needs.
4. Implement an authenticated connected CGM Service for production behavior.
   Preserve advertising for initial discovery and failed-link recovery.
5. Down-select the production process using a complete cost and IP comparison.
   GF180 is useful for the open digital shuttle; it is not automatically the
   best process for an integrated low-leakage RF product.
6. Define success as minimum energy and silicon needed to deliver a trustworthy
   glucose report to a nearby phone, rather than as a general-purpose Bluetooth
   feature contest.

Security is a product requirement, not a later enhancement. FDA guidance for
connected medical devices calls for security to be built into the design and
addresses authentication, cryptographic controls, secure updates, and lifecycle
risk management.

- [FDA cybersecurity guidance for medical devices](https://www.fda.gov/media/119933/download)

The defensible best-in-business claim is therefore a measured combination of
CGM accuracy support, delivered-report energy, secure connectivity, package
area, record recovery, yield, and cost. Maximum radio range or a long Bluetooth
feature list would not establish that claim.
