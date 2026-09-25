# AI-enabled RFIC design lessons for the CGM radio

## Purpose and scope

This note preserves the project-specific conclusions from reviewing Kaushik
Sengupta's webinar, *AI-Enabled RFIC Design Beyond Human Intuition*, and the
papers most directly associated with the design methodology presented there.
It records what is applicable to the CGM radio, what is not yet applicable,
and how the ideas should change the local GF180 design flow.

The central recommendation is not to add a large AI model immediately. It is
to turn the existing reproducible simulator flow into a reusable,
data-producing inverse-design system. Electromagnetic extraction and unified
multi-objective optimization should come first. Learned surrogate and
generative models become useful only after the project has a sufficiently
large, trustworthy simulation and measurement dataset.

This document complements the broader
[PR11 local verification report](pr11-local-verification-report.md) and
[agentic EDA landscape](pr11-agentic-eda-landscape.md). The requirements and
evidence boundaries in those reports remain controlling.

## Sources reviewed

The review used the full auto-generated transcript of the webinar and the
following directly related publications:

- Kaushik Sengupta,
  [*AI-Enabled RFIC Design Beyond Human Intuition*](https://www.youtube.com/watch?v=qBQFvjvMY9k),
  IEEE Solid-State Circuits Society webinar, 2026.
- E. A. Karahan, Z. Liu, and K. Sengupta,
  [*Deep-Learning-Based Inverse-Designed Millimeter-Wave Passives and Power Amplifiers*](https://doi.org/10.1109/JSSC.2023.3276315),
  IEEE Journal of Solid-State Circuits, 2023.
- E. A. Karahan et al.,
  [*Deep-learning enabled generalized inverse design of multi-port radio-frequency and sub-terahertz passives and integrated circuits*](https://www.nature.com/articles/s41467-024-54178-1),
  Nature Communications, 2024.
- J. Zhou et al.,
  [*AI-Enabled Design Space Discovery and End-to-End Synthesis for RFICs with Reinforcement Learning and Inverse Methods*](https://collaborate.princeton.edu/en/publications/ai-enabled-design-space-discovery-and-end-to-end-synthesis-for-rf/),
  ISSCC, 2025.
- Y. Guo et al.,
  [*Dall-EM: Generative AI with Diffusion Models for New Design Space Discovery and Target-to-Electromagnetic Structure Synthesis*](https://par.nsf.gov/servlets/purl/10632716),
  IEEE IMS, 2025.
- K. Sengupta,
  [*AI-enabled RF-to-terahertz chip design beyond human intuition*](https://doi.org/10.1364/AO.568476),
  Applied Optics, 2025.

## What the published approach actually does

The method is a hierarchy of specialized numerical models rather than a
general-purpose language model designing a chip:

1. A forward surrogate predicts the RF behavior of a proposed geometry much
   faster than repeated full-wave electromagnetic simulation.
2. An inverse optimizer searches for a geometry that satisfies target
   impedances, scattering parameters, bandwidth, phase, or radiation behavior.
   The published examples use genetic algorithms, binary particle swarm,
   inverse neural networks, and conditional diffusion.
3. A reinforcement-learning outer loop can select active-circuit topology,
   device sizes, bias, stage count, power combining, and the impedances required
   between stages.
4. Candidate structures are still verified using full-wave EM, circuit
   simulation, extracted layout, fabrication, and measurement.

The AI therefore accelerates exploration; it does not replace physical
verification or signoff.

The strongest transferable principles are:

- Start from required electrical behavior rather than a preselected component
  value or matching-network template.
- Co-optimize active devices and passives because topology, impedance,
  passive loss, bias, and device size are strongly coupled.
- Preserve a Pareto front instead of choosing a single design before system,
  package, and workload constraints are known.
- Include process sensitivity, geometry perturbations, and robustness directly
  in the objective function.
- Allow the designer to restrict generated structures to an interpretable or
  manufacturable architectural style.
- Amortize expensive simulation data across many subsequent design targets.

## Evidence and limitations in the papers

The results are meaningful: the group fabricated and measured passive
structures and active circuits, rather than reporting surrogate predictions
alone. The Nature Communications work uses low- and high-fidelity EM data,
transfer learning, a learned forward EM model, inverse synthesis, HFSS
verification, and EMX full-die verification. The ISSCC work adds an outer
architecture/circuit optimization loop and reports fabricated power amplifiers.

There are nevertheless important limits for this project:

- The demonstrated integrated circuits operate mainly from approximately
  24 GHz to 120 GHz in a proprietary 90 nm SiGe process, not at the 2.4 GHz BLE
  band in open GF180.
- The Nature Communications training data and code are not public because they
  contain proprietary GF9HP PDK information.
- Transfer learning reduces the amount of target-process data; it does not
  eliminate the need for accurate target-process EM simulation and
  verification.
- Dall-EM used 145,000 simulated 18-by-18 structures and approximately ten A100
  GPU-hours. Its initial condition vector contained S21 magnitude across
  10--30 GHz, not every complex multi-port, return-loss, group-delay,
  robustness, or circuit-level requirement.
- Dall-EM candidates were ranked by a separate forward CNN and selected
  candidates were still checked with a full-wave solver. The generative model
  did not make verification unnecessary.
- Reported measurement agreement is not evidence of foundry-qualified
  statistical yield, BLE compliance, package behavior, or product reliability.

At 2.44 GHz, wavelength-scaled distributed or arbitrary pixelated structures
can occupy millimeters or more. They are less attractive inside the present
GF180 slot than at mm-wave frequencies. Parameterized lumped spirals, compact
coupled structures, package matching, PCB structures, and the antenna are more
realistic initial applications.

## Mapping to the current project

The local flow already has several prerequisites for data-driven design:

- reproducible scripts and a pinned EDA environment;
- machine-readable JSON and CSV reports;
- explicit requirements, assumptions, limitations, and review gates;
- sampled multi-corner transistor simulations;
- scripted candidate enumeration and explicit pass/fail criteria; and
- an energy-per-delivered-report system objective rather than block power alone.

The current circuit sweeps can be viewed as a deterministic prototype of the
outer optimization loop described in the webinar. The main gap is that the
project searches assumed circuit values rather than realizable passive
geometries.

The subsequent RF feasibility work currently depends on fixed-Q inductors:

- approximately 3 nH, Q=10 for the DCO tank;
- approximately 6--8 nH, Q=10 for LNA input matching; and
- approximately 4.5--6.5 nH, Q=10 for PA output matching.

Those assumptions must become DRC-clean geometries with extracted inductance,
Q, self-resonance, coupling, loss, and variation before an optimizer can make
trustworthy architecture decisions. Otherwise, an advanced optimizer would
mostly exploit errors in an idealized passive model.

The pinned IIC-OSIC-TOOLS image already contains openEMS and scikit-rf in
addition to ngspice. The project therefore has the main open-source engines
needed to begin a geometry-to-S-parameter loop without adding an ML runtime.

## Recommended implementation sequence

### 1. Establish an EM-qualified passive loop

Build a parameterized GF180 spiral and compact-metal-structure generator and
automate the following chain:

```text
geometry -> DRC -> openEMS -> Touchstone/S-parameters
         -> extracted circuit model -> ngspice block simulation
```

The design variables should initially include outer size, turns, conductor
width and spacing, metal selection, via arrays, underpass, guard or ground
spacing, and nearby-metal keep-out. Outputs should include complete complex
S-parameters, L(f), Q(f), self-resonance, area, loss, and coupling.

The DCO tank is the first target because the absence of an EM-qualified
inductor is an architecture-level blocker. The same passive flow can then be
reused for the LNA and PA.

Nominal open-PDK stack assumptions may be used for comparative screening, but
they must not be labeled foundry-qualified evidence. A passive test coupon with
appropriate de-embedding structures is eventually required to calibrate the EM
model against measurement.

### 2. Adopt a common experiment schema

Each candidate should record:

- topology and parameter vector;
- geometry and layout hash;
- PDK, model, container, and tool versions;
- PVT point, passive variation, package/load condition, and random seed;
- raw waveform and S-parameter artifacts;
- derived metrics, constraint margins, and failure reason; and
- simulation fidelity: analytical, schematic, EM, extracted, or measured.

Existing block-specific JSON reports are useful inputs, but a common schema is
needed before results can support reliable surrogate training or transfer
learning.

### 3. Use direct Pareto optimization before RL or diffusion

The present design spaces do not justify reinforcement learning. Begin with
Sobol or Latin-hypercube sampling followed by constrained differential
evolution or Bayesian optimization. Preserve all non-dominated candidates for
energy, area, gain or noise, efficiency, harmonics, robustness, and margin.

A small, explicitly enumerated set of understandable circuit topologies is
preferable to topology-generating RL until the passive and extracted models are
trustworthy. An optimizer coupled to an inaccurate EM model will optimize model
error more efficiently, not produce a better chip.

### 4. Close active/passive and system co-design

The objective functions should reflect the real block and system requirements:

- DCO: startup, tuning overlap, phase noise, modulation settling, supply
  pushing, load pulling, area, and burst energy.
- LNA: gain, noise figure, S11, unconditional stability, compression and IIP3,
  blockers, all BLE channels, area, and receive energy.
- PA: delivered power, PAE, harmonics and adjacent-channel power, power-code
  range, load/VSWR tolerance, area, and burst energy.
- System: energy per successfully delivered glucose report, including wake,
  startup, retries, receive windows, and sleep leakage.

Topology and device choices should see the actual passive loss and system cost
while they are being selected.

### 5. Treat robustness as an objective

Candidate evaluation should include transistor PVT and mismatch, metal and
dielectric uncertainty, component variation, geometry bias and corner rounding,
package and antenna impedance, supply and temperature, metal fill, and neighbor
coupling. Worst-case, percentile, or conditional-value-at-risk metrics should
be retained rather than checking only a nominal optimum.

Full-solver and extracted verification remains mandatory for every selected
candidate, even after a surrogate is introduced.

### 6. Add learned models only when justified by cost and data

The recommended progression is:

1. direct simulation and adaptive numerical optimization;
2. a simple uncertainty-aware forward surrogate after EM runtime becomes the
   measured bottleneck;
3. active learning that requests new simulations where uncertainty or expected
   improvement is high;
4. a neural forward model only if simpler models fail in a genuinely
   high-dimensional space; and
5. diffusion or reinforcement learning only after the dataset and topology
   space are large enough to justify them.

The learned model should accelerate a verified deterministic flow, not become
the source of signoff truth.

## Effect on the PR11 strategy

The first Wafer.Space submission should remain a digital control, packet,
clocking, test, and pad-integration vehicle unless RF-qualified models,
passives, extraction, and package/antenna plans become available. Clean digital
GDS does not establish RF performance.

In parallel, the next RF milestone should be:

> Generate a DRC-clean GF180 passive library, extract it with openEMS, import
> it into the existing ngspice experiments, and produce multi-corner Pareto
> fronts for the DCO, LNA, and PA.

That milestone captures the immediately useful part of Sengupta's work:
specifications-to-geometry automation, active/passive co-design, reusable
simulation data, robust multi-objective exploration, and mandatory physical
verification. It also creates the dataset from which later learned models can
provide real acceleration rather than false confidence.
