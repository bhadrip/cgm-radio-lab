# PR11 local verification and EDA setup report

Research date: 2026-09-23

## Executive conclusion

PR11 is the product-requirements pull request at
[commit `627a80b`](https://github.com/bhadrip/cgm-radio-lab/commit/627a80b5983caf45cf460b5ae824246d0f7ffe56).
It describes
a complete electrochemical CGM SoC: sensor AFE, temperature and battery
monitoring, processing and storage, secure boot and update, Bluetooth LE 1M
controller and radio, a 15-day energy budget, WLCSP packaging, reliability, and
a manufacturing-cost target. It is not merely a Verilog or digital place-and-
route requirement.

An Apple Silicon Mac can provide an excellent, mostly open-source development
and verification environment for:

- executable requirements and system models;
- RTL lint, simulation, coverage, synthesis, and formal verification;
- digital RTL-to-GDS exploration and the present GF180 test chip;
- transistor-level AFE and basic RF circuit exploration;
- firmware, BLE behavior, security-negative testing, PCB design, and antenna or
  interconnect EM exploration; and
- reproducible regression evidence that Codex can run and review.

It cannot, by itself, establish that the PR11 product is ready for production.
The open GF180 PDK is explicitly an experimental preview and says it is not
intended for production use today. Production RFIC signoff also needs a
production PDK, foundry-qualified device models and verification decks,
signoff-grade extraction and reliability analysis, package/OSAT data, and
measured Bluetooth, regulatory, ESD, reliability, yield, and clinical evidence.
[GF180 open-PDK status](https://github.com/google/gf180mcu-pdk/blob/main/README.rst)

The recommended strategy is therefore three parallel tracks:

1. Keep the current GF180 design as a digital and mixed-signal learning/test
   vehicle, and strengthen it with formal, randomized, coverage, and post-layout
   checks.
2. Build a board-level product prototype with a qualified BLE SoC and a CGM AFE
   to validate the sensor, phone transport, security behavior, workload, and
   energy model before committing those decisions to silicon.
3. Start a production custom-IC path only after sensor characterization and
   foundry/package selection, using the foundry's qualified production flow for
   final analog, RF, reliability, and physical signoff.

No single simulation gives the most confidence. Confidence comes from
independent methods agreeing: a reference model, randomized simulation, formal
proof, static checks, extracted circuit simulation, EM analysis, and measured
prototypes.

## What PR11 actually requires

The PR11 product requirement has six coupled subsystems:

| Subsystem | Representative PR11 obligations | Evidence needed before production tapeout |
|---|---|---|
| Sensor and AFE | Potentiostat, 16-bit current conversion, provisional 50 nA to 2 uA ranges, temperature and battery monitoring | Sensor characterization, DC/AC/noise/transient simulation, PVT and mismatch Monte Carlo, linearity, settling, drift, electrode-fault and overload tests |
| Digital SoC | Processing, at least 512 KB ROM/NVM-equivalent capacity, at least 64 KB SRAM, 21,600 stored records | Architecture model, RTL simulation and formal proof, memory fault and retention tests, synthesis, equivalence, STA, power estimation, DFT and BIST |
| BLE and security | LE 1M on 40 channels, CGM Service/Profile, encrypted notifications, secure boot/update, anti-rollback and protected keys | Protocol simulation, negative and fault-injection tests, firmware emulation, RF simulation, interoperability tests, silicon RF/PHY and Bluetooth qualification |
| Power and clocking | No more than 7 uA complete-IC average at 3 V, no more than 15 uJ per report, retention and shipping-current limits, one 32 MHz crystal maximum | A reproducible 60-second workload, state residency and transition energy, oscillator/PLL startup, receive windows, retries, NVM maintenance, PVT and measured charge |
| Physical product | 1.2 to 3.6 V, WLCSP no larger than 2.5 mm square, minimal RF passives, -40 C to +85 C | Extracted top-level verification, EM/IR, antenna, latch-up, ESD, package/board/antenna co-simulation, thermal and reliability qualification |
| Economics and quality | At least 15 days, two-year shelf life, less than $0.30 per good packaged-and-tested unit at 50 million/year | Foundry/OSAT/test quotations, die area, mature yield model, probe/final-test coverage, scrap/retest model, qualification and production data |

The current repository implements a useful but much smaller slice: an eight-byte
CGM payload, a fixed non-connectable advertising packet, CRC, whitening,
loopback/BIST, a digital GFSK frequency-control stream, and a GF180 digital
implementation. The committed checkpoint has clean DRC/LVS and setup/hold but
still reports 519 maximum-slew and 92 maximum-capacitance violations. It also
lacks the production AFE, CPU/memory/security subsystem, link layer, synthesizer,
PA, receiver, package, and antenna. Passing its present tests is therefore
evidence for a digital test vehicle, not PR11 product compliance.

## Who designs a chip like this

“VLSI” is the broad field; “HDL,” SystemVerilog, and Verilog are languages. A
credible PR11 program is a team, not one type of engineer.

| Role | Owns |
|---|---|
| Product and systems architect | Requirements, budgets, interfaces, traceability, make/buy choices, and acceptance gates |
| Sensor/electrochemistry engineer | Electrode behavior, bias limits, current/noise envelope, aging, interferents, calibration, and sensor-fault signatures |
| Analog/mixed-signal IC designer | Potentiostat, TIA, ADC, DAC, references, regulators, oscillators, and mixed-signal interfaces |
| RFIC designer | PLL/DCO, PA, LNA, mixers, baseband, RF switch, matching, phase noise, blockers, and link budget |
| RTL design engineer | Digital microarchitecture and synthesizable SystemVerilog |
| Design-verification engineer | Test plans, constrained-random tests, assertions, scoreboards, coverage, and regressions |
| Formal-verification engineer | Properties, assumptions, proof decomposition, equivalence, and counterexample analysis |
| Firmware/BLE/security engineer | Boot, update, keys, CGM profile, storage, scheduler, link behavior, and threat testing |
| DFT/test engineer | Scan, memory BIST, analog/RF test access, wafer probe, final test, diagnosis, and test time |
| Physical-design and timing engineer | Floorplan, power grid, place/route, clock tree, STA, extraction, timing/signal integrity, and power integrity |
| Custom-layout/physical-verification engineer | Analog/RF matching layout, parasitics, guard rings, DRC/LVS/ERC, latch-up, antenna, and ESD implementation |
| Package/PCB/antenna engineer | WLCSP escape, crystal and RF passives, power delivery, matching, antenna, coexistence, and EM models |
| Product/yield/reliability/quality engineer | Corners, yield, burn-in, HTOL, ESD, latch-up, qualification, traceability, regulated design controls, and manufacturing release |

Small teams combine roles, but the review obligations do not disappear. The
important practice is independent review: the person who writes a block should
not be the only person who defines its pass criteria and signs off its evidence.

## What strong engineering teams use

Large semiconductor teams normally use a foundry-qualified commercial signoff
flow, even when much of their modeling and automation is written in Python,
Tcl, C++, or SystemVerilog. Representative stacks include Synopsys VCS/Verdi,
VC Formal/SpyGlass, PrimeTime/Formality and IC Compiler II; Cadence Xcelium,
Jasper, Genus/Innovus/Tempus/Voltus and Virtuoso/Spectre RF; and Siemens Questa
and Calibre. These names are illustrative, not an endorsement or a claim that
every company uses one fixed stack. The vendors themselves describe integrated
simulation, formal, static, implementation, timing, circuit, RF, and physical-
verification flows. [Synopsys verification family](https://www.synopsys.com/verification.html),
[Cadence digital and custom-IC products](https://www.cadence.com/Products_Nominal-Circuit-Analysis),
[Siemens Calibre circuit verification](https://www.siemens.com/en-gb/products/ic/calibre-design/circuit-verification/)

The reason is not simply speed. Production confidence depends on tool and model
qualification, complete language and methodology support, capacity, debug,
foundry deck support, and correlation to silicon. For RFIC work, the important
analyses include periodic steady state, periodic noise/phase noise, harmonic
balance, large-signal stability, source/load pull, S-parameters, corners and
Monte Carlo, plus EM-extracted passives and interconnect. Spectre RF is one
example of the production tool class that combines these analyses.
[Cadence Spectre RF analyses](https://www.cadence.com/en_US/home/tools/custom-ic-analog-rf-design/circuit-simulation/spectre-rf-option.html)

Open-source tools are still very valuable. They are good enough to build strong
requirements, architecture, RTL, formal, early analog, early RF, PCB, firmware,
and test-chip evidence. They should be treated as a complementary independent
flow and a way to find bugs early, not as automatic production signoff for PR11.

## Recommended Mac architecture

The machine inspected for this report is an Apple M5 Pro with 18 logical CPUs,
48 GiB RAM, and about 1.6 TiB free disk. That is more than adequate for the
current design and meaningful block-level analog/RF work. Very large extracted
RF, Monte Carlo, and full-chip regressions will eventually benefit from Linux
servers or a compute farm.

Use three execution lanes instead of forcing every tool into one installation.

### Lane A: fast native digital loop

Install a pinned `darwin-arm64` release of OSS CAD Suite. It provides a coherent
open-source digital stack including Yosys, Verilator, Icarus Verilog, `sby`
(SymbiYosys), SMT solvers, and related utilities. Current releases explicitly
support Apple Silicon macOS. Pin the archive date and checksum in the repository
rather than following a floating nightly build.
[OSS CAD Suite installation and Apple Silicon support](https://github.com/YosysHQ/oss-cad-suite-build)

Use:

- Verilator for fast regressions, lint, code coverage, and a second simulator;
- Icarus for the existing cocotb path and cross-simulator checks;
- cocotb for Python scoreboards, reference-model comparison, randomized tests,
  and functional coverage;
- SymbiYosys with an open SMT solver for safety/liveness assertions and covers;
- Yosys for synthesis and structural checks;
- Verible for formatting and style lint; and
- Surfer or GTKWave for waveforms.

SymbiYosys supports bounded and unbounded safety verification, cover generation,
and liveness flows. Verilator is not a drop-in replacement for every event-driven
SystemVerilog feature, so keeping both Verilator and Icarus is useful independent
evidence. [SymbiYosys tasks](https://symbiyosys.readthedocs.io/en/latest/),
[Verilator scope and licensing](https://verilator.org/guide/latest/faq.html),
[cocotb simulator support](https://www.cocotb.org/)

### Lane B: reproducible Linux ASIC and analog environment

Keep the repository's pinned IIC-OSIC-TOOLS image for reproducibility. It supports
both `aarch64` and `x86_64` and bundles open-source digital and analog IC tools.
Replace the current Docker Desktop runtime with Colima plus the open Docker CLI,
or Podman, if the goal is to eliminate Docker Desktop subscription ambiguity.
Colima is MIT-licensed, supports Apple Silicon, and exposes a Docker-compatible
runtime. Podman Desktop is Apache-2.0-licensed and supports Apple Silicon.
[Colima](https://github.com/abiosoft/colima),
[Podman Desktop](https://podman-desktop.io/downloads/macos),
[IIC-OSIC-TOOLS](https://github.com/chiplicity/iic-osic-tools)

A practical Colima bootstrap is:

```bash
brew install colima docker
colima start --cpu 12 --memory 24 --disk 150
docker context show
make container-check
make container-gf180-signoff
```

Do not use `latest` images. Keep the existing image tag, record its immutable
digest, and archive the PDK commit, flow configuration, tool versions, commands,
and results for every signoff candidate.

LibreLane is the right open-source RTL-to-GDS flow for this repository. Its
documentation recommends Nix and provides native Apple Silicon builds; its
sequential flow uses Yosys, OpenROAD, KLayout, Magic, and Netgen. Use native Nix
for interactive exploration if desired, but keep one pinned container lane as
the reproducibility authority. [LibreLane installation](https://librelane.readthedocs.io/en/stable/installation/index.html),
[LibreLane flow](https://librelane.readthedocs.io/en/latest/reference/flows.html),
[OpenROAD RTL-to-GDS stages](https://openroad.readthedocs.io/en/latest/main/README.html)

### Lane C: native board, circuit, firmware, and RF exploration

Install these as needs arise:

| Tool | Use | License posture and Mac status |
|---|---|---|
| ngspice | DC, AC, transient, noise, corners, mixed-level and early AFE/RF circuit simulation | Open source; current Homebrew formula; native macOS. GF180 provides ngspice-compatible models. |
| Xschem | IC schematic capture and netlisting | Open source; usable natively with XQuartz or in IIC-OSIC-TOOLS. A documented GF180 Apple Silicon flow exists, but the container is simpler to reproduce. |
| Xyce | Large circuit simulation, noise, S-parameters, harmonic balance, sampling, and parallel runs | GPLv3; macOS supported. Build from source for an unambiguously open-source binary. [Xyce capabilities](https://xyce.sandia.gov/about-xyce/) |
| Qucs-S/QucsatorRF | Schematic GUI, sweeps, RF networks, S-parameters, and ngspice/Xyce backends | Open source; current macOS package available. ngspice must be installed separately. [Qucs-S backends](https://qucs-s-help.readthedocs.io/en/latest/overview/choosing-a-sim-backend.html) |
| KLayout, Magic, Netgen | Layout inspection/editing, DRC, extraction support, and LVS | Open source; already available in the pinned IC environment; KLayout also has a native Mac package. |
| KiCad | Board schematic, PCB layout, Gerber review, and basic ngspice simulation | GPLv3+ with official macOS support. [KiCad licensing](https://www.kicad.org/about/licenses/), [KiCad SPICE](https://www.kicad.org/discover/spice/) |
| openEMS | FDTD EM simulation of antennas, package structures, passives, and board interconnect | Free/open source; macOS requires a manual source build at present. [openEMS install status](https://docs.openems.de/en/latest/install/package.html) |
| scikit-rf | Touchstone/S-parameter manipulation, de-embedding, calibration, network cascading, plotting, and measurement automation | Permissive Python library. [scikit-rf networks](https://scikit-rf.readthedocs.io/en/latest/tutorials/Networks.html) |
| Renode + Zephyr | Firmware and multi-node BLE behavior, fault scenarios, and phone/controller interaction before custom CPU hardware exists | Renode is MIT-licensed and provides an Apple Silicon package; its BLE medium runs Zephyr examples. [Renode BLE simulation](https://renode.readthedocs.io/en/latest/tutorials/ble-simulation.html) |
| Zephyr BabbleSim | Multi-device BLE physical/link behavior and repeatable interference scenarios | Open-source simulator integrated with Zephyr. [BabbleSim](https://docs.zephyrproject.org/latest/develop/test/bsim.html) |

Suggested native packages that are currently present in Homebrew include
`ngspice`, `iverilog`, `verilator`, `yosys`, `klayout`, and the KiCad cask. Qucs-S
uses its project's Homebrew tap; openEMS currently requires a source build.

The tools may be open source, but every PDK, standard-cell library, memory macro,
Bluetooth IP block, firmware component, model, and third-party core has its own
terms. “No license server” is achievable; “no license review” is not. Keep a
software bill of materials and provenance file for both software and silicon IP.

## Verification that produces the most confidence

### 1. Requirements as executable contracts

Give every PR11 “shall” a stable identifier, owner, verification method, pass
threshold, applicable PVT/load/workload conditions, artifact path, and state.
Numbers without conditions are not verifiable. The 7 uA average-current target,
for example, is meaningful only with the complete 60-second workload, state
residency, retry distribution, supply, temperature, and regulator loss.

Maintain two models:

- a fast architecture model for energy, link budget, memory, timing, yield and
  cost; and
- an independent bit/cycle-accurate reference for packet, DSP, control, and
  security-visible behavior.

Do not derive the test oracle from the RTL being tested.

### 2. Digital verification

Use all of the following:

1. Parser/style lint and synthesis warnings as errors, with reviewed waivers.
2. Deterministic unit tests and randomized/property-based tests against the
   independent Python model.
3. Assertions for protocol, handshakes, ordering, legal state transitions,
   reset, no data loss, no deadlock, and bounded completion.
4. Formal proof on small critical blocks and interfaces. For this repository,
   good first properties are CRC equivalence, whitening invertibility, exact
   packet length, no dropped/duplicated symbols, `done` only after the final
   sample, register-bus legality, and safe reset from every state.
5. Functional, assertion, toggle, branch, and code coverage with reviewed
   unreachable exclusions. A high percentage is not closure unless every PR11
   scenario is represented.
6. Cross-simulation with Icarus and Verilator; investigate disagreement rather
   than choosing the preferred result.
7. RTL-to-netlist equivalence where the open flow supports it, plus gate-level
   reset/X checks for cases not covered by equivalence.
8. Multi-corner post-route STA, clock/reset-domain analysis, extracted timing,
   and power from realistic switching activity.

Simulation finds sampled behaviors; formal explores all behaviors within the
model and assumptions. Neither proves that the specification or environment
model is correct, so both are required.

### 3. AFE and power-management verification

At schematic and extracted-layout levels, run:

- operating point and safe device-voltage checks;
- input-current range, gain, offset, leakage, compliance, saturation, recovery,
  and electrode open/short scenarios;
- integrated input-referred noise over the actual measurement bandwidth;
- transient startup, settling, multiplexing, conversion, calibration, sleep,
  wake, brownout, and power sequencing;
- PSRR, CMRR, loop gain/stability, reference and regulator load/line transients;
- ADC/DAC DNL, INL, missing-code, SNDR/ENOB and monotonicity tests;
- process/voltage/temperature corners, supply/load sweeps, and local/global
  statistical mismatch Monte Carlo; and
- extracted RC and coupling with package/board parasitics.

The PR11 sensor-characterization gate must come first. A beautiful TIA optimized
for guessed electrode current, impedance, noise, drift, or aging is not evidence
for a CGM product.

GF180 documentation includes statistical-model and reliability material, but
parts of the public statistical-model instructions are visibly incomplete. That
is another reason to treat the open kit as a test-chip environment, not the final
production evidence source. [GF180 statistical models](https://gf180mcu-pdk.readthedocs.io/en/latest/analog/model_parameters/HV/HV_4_1.html)

### 4. RF and clock verification

Use a hierarchy of models:

1. Python/GNU Radio-style complex-baseband model for BLE packets, modulation,
   CFO, drift, phase noise, timing error, noise, adjacent-channel interference,
   blockers, nonlinearity, fading, and BER/PER sweeps.
2. Behavioral PLL/DCO/PA/RX models connected to the RTL and firmware workload.
3. Transistor-level DC/AC/noise/transient, S-parameter, harmonic-balance or
   periodic steady-state/noise analyses as appropriate.
4. EM-extracted inductors, transformers, transmission lines, matching network,
   WLCSP escape, PCB, and antenna imported as Touchstone networks.
5. Post-layout co-simulation across PVT, supply, load mismatch, package, antenna,
   and statistical variation.

Required metrics include PLL startup and lock, center-frequency error and drift,
phase noise/integrated jitter, modulation index and deviation, spectral mask and
adjacent-channel power, PA output/efficiency/harmonics/stability/load pull, LNA
noise figure and stability, RX gain/noise/IIP2/IIP3, sensitivity, maximum input,
co-channel/adjacent/image rejection, blocker response, and BER/PER.

ngspice and Xyce can find many early errors. Qucs-S, scikit-rf, and openEMS are
useful for networks and EM. They do not by themselves create a foundry-qualified
production BLE-radio signoff flow. The handoff to a production PDK and a
qualified RF simulator must be planned before the radio architecture is frozen.

### 5. Firmware, BLE, security, and system verification

Before custom silicon exists, run production-intent firmware on an emulated MCU
or a COTS reference board. Exercise:

- CGM Service/Profile discovery, encrypted notification, record recovery,
  reconnect, pairing, bond replacement, link loss, alarm timing, and update;
- corrupted/truncated/replayed/out-of-order packets and NVM records;
- power loss during record append, key provisioning, boot and update;
- invalid signatures, rollback, debug unlock attempts, malformed GATT/HCI input,
  resource exhaustion, and fuzzing; and
- 15-day accelerated virtual time with disconnect and retry distributions.

Renode can simulate multi-node BLE systems and connect an emulated BLE device to
an Android emulator through HCI. This is strong pre-board software evidence, but
it is not RF conformance or phone interoperability evidence.
[Renode BLE HCI integration](https://renode.readthedocs.io/en/latest/tutorials/ble-hci-integration.html)

### 6. Physical, package, board, and production verification

For the digital test chip, continue through synthesis, floorplan, placement,
CTS, route, extraction, STA, DRC, LVS, antenna, density, XOR, and PDN analysis.
Resolve the existing slew and capacitance violations rather than treating clean
setup/hold as complete timing signoff.

For the production chip add ERC, voltage-aware checks, latch-up, ESD paths,
current density/electromigration, signal integrity, dynamic IR drop, thermal,
DFM, test structures, scan/MBIST, analog/RF test access, package LVS, and package-
board-antenna co-verification. GF180's own reliability manual says its guidance
is not all-inclusive and assigns final reliability/manufacturability to the
designer. [GF180 reliability scope](https://gf180mcu-pdk.readthedocs.io/en/latest/physical_verification/design_manual/drm_14.html)

Finally, simulation cannot replace measurements. A new BLE design may require
Category-A RF/PHY results from a recognized qualification facility, and every
marketed Bluetooth product must complete the qualification process. Regulatory
radio testing is separate. [Bluetooth qualification](https://www.bluetooth.com/develop-with-bluetooth/qualify/),
[Bluetooth qualification test facilities](https://www.bluetooth.com/develop-with-bluetooth/qualify/qualification-test-facilities/)

## Tapeout confidence gates

Do not use “all tests passed” as one undifferentiated gate. Use evidence gates:

| Gate | Minimum exit evidence |
|---|---|
| 0. Product feasibility | Selected sensor characterized; transport chosen; link, energy, memory, area, package, yield and cost budgets close with margin; open assumptions assigned owners |
| 1. Architecture | Executable 60-second workload; bit-accurate BLE model; threat model; reference-board measurements; architecture reviews close |
| 2. RTL and firmware | Requirements coverage closed; two simulators agree; critical formal properties pass without vacuity; functional/code/assertion coverage reviewed; boot/update/storage fault tests pass |
| 3. Circuit blocks | AFE, clock, power and RF blocks pass schematic PVT, noise, stability and statistical verification with documented model validity and margin |
| 4. Layout and top-level | Extracted PVT/Monte Carlo passes; AMS interactions pass; timing, DRC/LVS/ERC, EM/IR, antenna, latch-up, ESD and DFT evidence close using foundry-qualified decks |
| 5. Package and board | EM-extracted package/board/antenna co-simulation closes; crystal/matching/power/ESD networks reviewed; test and calibration plan demonstrated |
| 6. Tapeout review | Frozen manifest of RTL/netlists/GDS/decks/models/tool versions; all waivers signed; independent reviewers sign each domain; no unresolved red requirement |
| 7. Product release | Silicon characterization, Bluetooth qualification, regulatory, security, reliability, yield, test coverage, clinical/system validation, and cost evidence close |

Tapeout occurs after Gate 6. Board spins and reference prototypes should happen
well before it; they are an inexpensive way to discover product and interface
errors that no transistor simulation can reveal.

## How to use Codex effectively

Codex should orchestrate deterministic tools and maintain evidence; it should
not be the source of truth for whether a chip is safe or tapeout-ready.

The companion [agentic EDA landscape and PR11 adoption plan](pr11-agentic-eda-landscape.md)
compares the emerging commercial and open-source systems and translates their
strongest patterns into a practical, license-conscious PR11 architecture.

Recommended repository structure:

```text
AGENTS.md
requirements/
  pr11.yaml
verification/
  plans/
  formal/
  analog/
  rf/
  firmware/
evidence/
  manifests/
  digital/
  physical/
  analog/
  rf/
```

Add stable commands such as:

```text
make verify-fast       # lint, Python, RTL unit tests
make verify-formal     # assertions/proofs/covers
make verify-coverage   # randomized regression and coverage merge
make verify-physical   # pinned synthesis/P&R/STA/DRC/LVS
make verify-analog     # pinned SPICE corners and measurements
make verify-system     # BLE/firmware/workload/fault scenarios
make evidence          # hash inputs and assemble the requirements matrix
```

`AGENTS.md` should tell Codex which commands are safe, what a pass means, which
outputs are derived, and that it must never hide, waive, or reclassify a failure
without recording the reason and reviewer. A small project-local skill can later
teach Codex the PR11 verification workflow, result parsers, required artifact
schema, and review checklist. Official OpenAI documentation describes skills as
reusable instructions plus scripts and references, and recommends keeping
repository conventions and test commands in `AGENTS.md`.
[OpenAI skills documentation](https://developers.openai.com/api/docs/guides/tools-skills),
[OpenAI guidance on `AGENTS.md` and repeatable workflows](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)

Good Codex tasks include:

- generate a candidate property or test from a specific requirement;
- run the relevant regression and preserve logs, seeds, waves and tool versions;
- minimize a failing seed or formal counterexample;
- compare RTL, Python and gate-level outputs;
- identify uncovered requirements and untested boundary conditions;
- sweep PVT/load parameters and summarize worst cases without discarding data;
- review a layout/STA/DRC report for regressions; and
- assemble a tapeout dashboard with links to immutable artifacts.

Every AI-generated assertion, test, model, waiver, and conclusion still needs
engineering review. A wrong property can formally prove the wrong design, and a
wrong compact model can produce an extremely precise wrong answer.

## Recommended next actions

### First week: establish the trustworthy digital loop

1. Install Colima and switch the pinned container flow away from Docker Desktop.
2. Install and pin the Apple Silicon OSS CAD Suite.
3. Run the existing suite under both Icarus and Verilator.
4. Add Verilator lint and coverage reports; keep seeds and waves on failure.
5. Create the first SymbiYosys properties for reset, packet length, CRC/whitening,
   and the packet-to-GFSK ready/valid path.
6. Convert PR11 into a machine-readable requirements/evidence matrix.
7. Re-run full GF180 signoff and make slew/capacitance repair a blocking issue.

### First month: validate the product architecture

1. Build the 60-second workload/energy/storage model, including startup, receive
   windows, retries, NVM maintenance, sensor bias, and regulator loss.
2. Characterize the candidate electrochemical sensor; do not freeze the AFE from
   the market-derived range alone.
3. Prototype the CGM Service/Profile, encrypted connection, history recovery,
   link loss, pairing and update in Zephyr/Renode and on real phones.
4. Measure a COTS BLE-plus-AFE reference board to calibrate the energy and sensor
   models.
5. Build a complex-baseband BLE/RF impairment model and reproduce every PHY
   limit in the requirements ledger.

### Before any production custom-radio commitment

1. Select the production foundry process, package, memory/OTP, ESD/I/O and RF
   options against area, power, noise, yield, test and cost.
2. Obtain foundry-qualified PDK/models/decks and confirm the supported signoff
   tool versions.
3. Identify owners for analog/RF, physical verification, DFT, package/antenna,
   reliability, Bluetooth qualification, regulatory, security, and product
   quality.
4. Create a correlation plan: open-source exploration versus production
   simulator, schematic versus extracted, simulated versus test structure, and
   pre-silicon versus bench measurement.
5. Do not claim the $0.30 target until foundry, OSAT, test, yield and IP inputs
   close the per-good-unit model at the declared volume.

## Bottom line

The best local setup is not a single application. It is a reproducible evidence
pipeline: OSS CAD Suite for the native digital loop, a pinned IIC-OSIC/LibreLane
environment for ASIC implementation, ngspice/Xyce/Qucs-S for circuit and early
RF work, KiCad/openEMS/scikit-rf for board and EM work, and Renode/Zephyr for BLE
and firmware behavior. Codex can make that pipeline unusually productive by
running, cross-checking, and documenting it.

That setup can find a large fraction of architecture, RTL, protocol, circuit,
layout, and integration bugs before money is spent. The final increment of
confidence for PR11 comes only from a production PDK and signoff flow, independent
review, instrumented prototypes, test silicon, and qualification measurements.
