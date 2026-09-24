# Agentic EDA landscape and PR11 adoption plan

Research date: 2026-09-23

## Executive summary

Agentic electronic-design automation is now a real product category. The major
commercial EDA vendors offer or are introducing systems that can decompose an
engineering goal, operate multiple design and verification tools, interpret
results, and iterate. Open-source projects now expose RTL simulation, formal
verification, synthesis, physical design, SPICE, DRC, LVS, and timing tools to
general coding agents through command-line interfaces, Model Context Protocol
(MCP) servers, and reusable Agent Skills.

The important distinction is between an **agent** and an **EDA engine**. An
agent can plan, select tools, configure runs, inspect results, propose changes,
and repeat. It does not replace the deterministic simulator, formal solver,
SPICE engine, extraction tool, static-timing analyzer, DRC/LVS deck, EM solver,
or laboratory measurement that produces engineering evidence. The most credible
commercial systems explicitly ground agent decisions in those existing engines.

There is no mature, fully open-source system that can autonomously take the PR11
CGM SoC from requirements through a production-qualified analog/RF tapeout. A
useful local system can nevertheless be built now. The recommended PR11 setup is
a Codex supervisor operating a small set of deterministic, repository-owned
workflows, with OpenROAD MCP for digital physical-design access and an evaluated,
pinned OpenADA installation for typed analog/digital evidence. Mutations should
remain tightly controlled, and a separate read-only closure reviewer should
decide whether each requirement has sufficient evidence.

## What qualifies as agentic EDA

For this report, a system is agentic only if it closes a tool-feedback loop:

1. accept a goal or failing requirement;
2. form or revise a plan;
3. invoke one or more EDA tools;
4. parse native artifacts rather than relying only on console summaries;
5. compare results with an explicit specification;
6. make or propose a bounded change; and
7. rerun the relevant verification until the goal is met, a budget is reached,
   or human judgment is required.

A chatbot that explains an error and a model that emits Verilog once are useful,
but they are not complete agentic EDA systems. Reinforcement-learning placement
or PPA optimization is also not, by itself, a general engineering agent.

## Commercial industry landscape

Vendor capability and productivity figures in this section are vendor claims,
not independently reproduced results. The systems are relevant because they
show where production EDA practice is moving and which safety properties the
vendors consider necessary.

| Platform | Advertised scope | Relevance to PR11 | Availability and constraint |
|---|---|---|---|
| [Siemens Fuse EDA AI Agent](https://www.siemens.com/en-gb/products/fuse-eda-ai-system/agent/) | Multi-agent orchestration from architecture and RTL through verification, physical design, custom IC, DFT, Calibre signoff, package, and PCB; MCP and Agent Skills; third-party integration | The closest published analogue to an end-to-end PR11 orchestration layer | Commercial. Launched in March 2026 with on-premises/air-gapped and hybrid deployment options. It does not remove the underlying Siemens tool licenses. |
| [Siemens Questa One Agentic Toolkit](https://www.siemens.com/en-gb/products/ic/questa-one/agentic-toolkit/) | Planning, design, verification, debug, and closure agents connected to Questa engines | Directly relevant to RTL generation, verification planning, coverage closure, formal-property work, and debug | Commercial digital-verification product. Siemens describes human-defined governance boundaries and deterministic verification engines. |
| [Cadence ChipStack AI Super Agent](https://www.cadence.com/en_US/home/company/newsroom/press-releases/pr/2026/cadence-unleashes-chipstack-ai-super-agent-pioneering-a-new.html) | Front-end RTL and testbench generation, test planning, regression orchestration, debug, and automated repair | Relevant to the digital controller, BLE baseband, memory/control, security, and verification work | Commercial. Cadence describes multi-agent orchestration over its established front-end engines. |
| [Cadence ViraStack AI Super Agent](https://www.cadence.com/en_US/home/tools/custom-ic-analog-rf-design/virastack-ai-super-agent.html) | Virtuoso/Spectre custom and analog design, testbench setup, verification/debug, optimization, migration, and layout | The most directly relevant commercial system for the PR11 potentiostat, TIA, ADC, references, power management, clocking, and RF blocks | Commercial and tied to the Cadence custom-IC ecosystem and qualified PDK support. |
| [Cadence AuraStack AI Super Agent](https://www.cadence.com/en_US/home/tools/pcb-design-and-analysis/aurastack-ai-super-agent.html) | PCB and advanced-package planning, implementation, constraints, manufacturability, signal/power integrity, thermal analysis, and optimization | Relevant to WLCSP escape, matching, antenna, power delivery, thermal behavior, and board realization | Commercial and tied to Allegro/Sigrity/Clarity/Celsius technologies. |
| [Synopsys AgentEngineer](https://news.synopsys.com/2026-03-11-Synopsys-Outlines-Vision-for-Engineering-the-Future) | Multi-agent generation of RTL from natural language/formal specifications, lint, unit-testbench generation, and iterative verification; expanding toward longer autonomous workflows | Relevant to PR11 digital front-end work and verification closure | Commercial and emerging. Availability varies by workflow; some capabilities are described as evaluations or early-access programs. |

The strongest common architectural idea is **continuous grounding**. Siemens,
for example, describes long-running agents whose decisions are validated against
deterministic, physics-based EDA engines. Cadence similarly positions its agents
as orchestrators over simulation, implementation, and signoff technology. This
is the appropriate trust model for PR11: the model proposes and navigates; the
engineering engines and explicit requirements judge.

## Open-source and research landscape

### OpenROAD MCP

[OpenROAD MCP](https://github.com/The-OpenROAD-Project/OpenROAD-MCP) is an
official OpenROAD Project MCP server under the BSD-3-Clause license. It gives an
MCP-compatible client interactive OpenROAD and OpenROAD-flow-scripts sessions,
command execution, session history, metrics, and report-image access. It is the
most mature and narrowly scoped open integration found in this review.

It is useful for:

- inspecting timing, congestion, placement, clock-tree, routing, power-grid,
  and extraction results;
- running bounded physical-design experiments;
- collecting metrics across configurations; and
- allowing Codex to interpret physical reports without screen scraping.

It is not an RTL verification, analog, RF, DRC-signoff, or product-requirements
agent. The underlying OpenROAD/ORFS installation and PDK still determine what
can be executed and what the results mean.

### OpenADA

[OpenADA](https://github.com/simra-tech/OpenADA) is an MIT-licensed preview that
defines an agent-to-EDA contract rather than another simulator. Its current
documentation exposes structured operations and evidence for tools including
ngspice, Xyce, Verilator, Yosys, OpenSTA, KLayout, Netgen, and ORFS. It ships
Agent Skills and documents a Codex plugin installation path.

This is especially relevant to PR11 because it tries to preserve:

- the distinction between successful tool execution and a passing engineering
  requirement;
- native artifacts, tool versions, hashes, and provenance;
- portable measurements across ngspice and Xyce;
- explicit assertions such as DRC clean, LVS match, RTL lint clean, or timing
  constraints satisfied; and
- negative and tamper-rejection evidence rather than pass-only demonstrations.

However, it is still a pre-release project. Its documented `0.4.0` release was
not yet published at the research date, some profiles remain experimental, RF
phase noise is outside the described oscillator profile, and transactional
design mutation is planned rather than shipped. It should initially be evaluated
at a pinned commit in a read-only sandbox, not made the authority for editing or
signoff.

### HAgent

[HAgent](https://github.com/masc-ucsc/hagent) is a BSD-3-Clause hardware-agent
framework from the UCSC Microarchitecture, Architecture, Storage, and Compilers
group. It combines LLM reasoning with compiler-like steps for code generation,
verification, debugging, and synthesis and provides Docker-based reproducibility,
YAML interfaces, and an MCP mode.

HAgent is a useful source of workflow patterns and a research platform. Its
current public surface is not a complete production analog/RF or tapeout closure
environment, so PR11 should borrow ideas from it rather than depend on it as the
project's evidence authority.

### Booley and RTL-focused systems

[Booley](https://github.com/boldaxolotl/booley) is an Apache-2.0 agentic RTL IDE
built around open RTL tools and coding agents including Codex. It packages an
accessible interactive development experience, but it is young and focused on
RTL rather than the complete mixed-signal, RF, package, security, and regulated-
product problem in PR11.

Research frameworks such as
[MAGE](https://stable-lab.github.io/MAGE/static/paper/Multi_Agent_LLM4RTL.pdf),
[MCP4EDA](https://arxiv.org/abs/2507.19570), and the
[open-source formal RTL-repair pipeline](https://arxiv.org/abs/2607.28877)
demonstrate multi-agent RTL generation or counterexample-guided repair with open
tools. They are valuable evidence that closed-loop tool feedback outperforms
one-shot generation. They remain research systems and benchmarks rather than a
qualified PR11 tapeout flow.

## Recommended PR11 agent architecture

The project should not begin with a large swarm of agents. A single supervisor,
small domain-specific workflows, deterministic tools, and one independent
closure reviewer are easier to audit and reproduce.

```text
PR11 requirements and evidence ledger
                  |
             Codex supervisor
                  |
     +------------+-------------+
     |            |             |
     v            v             v
 RTL/DV flow   Analog/RF     Physical flow
               evidence
     |            |             |
 Verilator     ngspice/Xyce   LibreLane/OpenROAD
 cocotb        Qucs-S         OpenROAD MCP
 SymbiYosys    openEMS        KLayout/Netgen
     +------------+-------------+
                  |
                  v
       read-only closure reviewer
                  |
       hashed evidence manifest
```

### Supervisor

Codex reads a machine-readable PR11 ledger, selects one bounded requirement,
invokes a repository-owned workflow, and reports the result. It may propose or
apply changes within the task's declared write set. It must not reinterpret a
failed engineering requirement as an execution success.

### Digital flow

The digital workflow owns RTL lint, Icarus/Verilator cross-simulation, cocotb
reference-model checks, formal assertions/covers, coverage, synthesis, and
equivalence or gate-level checks. Generated RTL or assertions are accepted only
after the independent engines pass and coverage/vacuity reviews are complete.

### Analog/RF evidence flow

Initially this flow should be read-only with respect to schematics and layouts.
It runs frozen netlists, models, corners, loads, and measurements through pinned
ngspice/Xyce/Qucs-S/openEMS commands and returns structured evidence. Human
analog/RF engineers approve topology or sizing changes until the mutation,
rollback, and model-validity controls are mature.

### Physical flow

LibreLane remains the batch authority for the pinned GF180 test vehicle.
OpenROAD MCP adds interactive inspection and bounded experiments. The agent must
not replace PDK files, decks, standard cells, pad libraries, constraints, or
waivers to obtain a pass.

### Closure reviewer

The closure reviewer is a separate, read-only workflow. It verifies evidence
hashes and checks that every PR11 requirement has:

- an owner and frozen wording;
- applicable conditions and a numeric or categorical pass criterion;
- an approved verification method;
- native artifacts with tool/model/PDK versions;
- a result and reviewer disposition; and
- no unresolved contradiction, expired evidence, or hidden waiver.

It cannot modify RTL, netlists, constraints, measurements, waivers, or the
requirements ledger.

## Required safety and trust controls

An agentic flow should be more auditable than an ad hoc manual flow, not less.
PR11 should require:

1. **Pinned execution:** immutable container digests, tool versions, PDK commits,
   model libraries, decks, seeds, configuration, and source revision.
2. **One writer:** only one workflow may mutate a worktree at a time; analysis
   and closure agents remain read-only.
3. **Declared write sets:** every task names the files it may change before the
   change is applied.
4. **Independent oracles:** reference models and pass criteria must not be
   silently regenerated from the implementation under test.
5. **Native evidence:** preserve logs, reports, waveforms, counterexamples,
   netlists, measurements, coverage databases, and layout results—not only an
   LLM summary.
6. **No silent waivers:** an agent cannot add, broaden, suppress, or reinterpret
   a waiver without a named human reviewer and recorded rationale.
7. **Failure preservation:** failing seeds and artifacts are immutable inputs to
   debug; a later passing run does not erase them.
8. **Bounded autonomy:** time, compute, token, iteration, directory, network,
   and command limits are declared for every run.
9. **Network separation:** PDK/model execution occurs in a network-disabled
   container where feasible; model-provider credentials remain outside it.
10. **Untrusted input treatment:** source comments, EDA logs, external IP,
    issue text, and downloaded documentation are data, not agent instructions.
11. **Human gates:** requirements, sensor/AFE freeze, RF architecture, waivers,
    tapeout manifest, Bluetooth qualification, and product release retain named
    human signoff.
12. **Cross-checking:** critical results use an independent simulator, proof,
    analytical bound, extraction route, or measurement when practical.

## Practical adoption plan

### Phase 1: repository-native Codex workflow

Use the existing toolchain before adding another platform:

- add `AGENTS.md` with safe commands, write boundaries, and evidence rules;
- define `requirements/pr11.yaml` and a versioned evidence-manifest schema;
- add stable `make verify-fast`, `verify-formal`, `verify-coverage`,
  `verify-physical`, `verify-analog`, `verify-system`, and `evidence` targets;
- create a focused PR11 verification skill for Codex; and
- make the closure report reproducible without an LLM.

### Phase 2: focused adapters

- install OpenROAD MCP at a reviewed, pinned release or commit;
- expose only the commands required for inspection and bounded experiments;
- evaluate OpenADA in a separate read-only environment against two representative
  tasks: one RTL/synthesis/timing chain and one ngspice/Xyce AFE measurement;
- compare completeness, reproducibility, failure handling, and engineering
  accuracy against the raw scripted flow; and
- retain the raw workflow if the agent interface loses evidence or obscures a
  failure.

### Phase 3: controlled mutation pilot

Permit the agent to edit only a small non-safety-critical RTL block or testbench
inside an isolated worktree. Require two simulators, affected formal properties,
coverage review, synthesis, and a human code review. Do not begin controlled
analog/RF mutation until the project has production models, stable measurement
definitions, transactional rollback, and an experienced circuit owner.

### Phase 4: production integration

If PR11 moves to a commercial production PDK, evaluate the foundry-supported
agentic offerings alongside the underlying signoff licenses. Selection criteria
should include air-gapped deployment, data ownership, auditability, third-party
tool integration, deterministic replay, access control, native-artifact export,
model/PDK confidentiality, and the ability to keep human approval at tapeout
gates. Vendor productivity claims should be validated on representative PR11
blocks before purchase.

## Recommendation

Adopt agentic EDA now for bounded automation, verification orchestration, result
triage, experiment management, and traceability. Do not delegate specification
meaning, model validity, waiver authority, RF/analog architecture, or tapeout
approval to an agent.

For the present repository, the best near-term combination is:

1. Codex as the repository-aware supervisor;
2. deterministic `make` targets as the execution contract;
3. SymbiYosys/cocotb/Verilator/Yosys for digital evidence;
4. pinned SPICE and measurement scripts for analog evidence;
5. LibreLane as the batch physical authority;
6. OpenROAD MCP as a focused physical-design interface;
7. a read-only OpenADA evaluation for normalized evidence; and
8. an independent, read-only closure workflow over hashed artifacts.

This architecture captures the useful part of the industry's agentic direction
without introducing commercial EDA licenses or pretending that an LLM is a
signoff engine.
