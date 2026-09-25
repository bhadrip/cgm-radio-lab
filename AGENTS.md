# Repository instructions

These instructions apply to every human or AI agent working in this repository.
For machine setup and commands, read `development.md`. For the design contract,
read `spec.yaml` and `docs/engineering-basis.md` before making changes.

## Mission and boundary

Build a local, reproducible BLE LE 1M CGM-radio design loop in small vertical
slices. The current repository is an engineering test vehicle, not a complete
Bluetooth product or a tapeout-ready RFIC. Preserve that distinction in code,
reports, and review language.

The following are controlling sources, in order:

1. primary standards and foundry documentation;
2. `docs/engineering-basis.md` for fixed requirements, provisional targets,
   open questions, and review gates;
3. `spec.yaml` for the current executable configuration; and
4. checked-in models, tests, and reports as reproducible implementation
   evidence.

If these disagree, do not silently choose one. Identify the conflict, preserve
the stronger evidence boundary, and update the appropriate source in the same
change or ask for a product/design decision.

## How to work

- Work in one small, reviewable vertical slice at a time. Define the question,
  acceptance gates, and evidence needed before changing the implementation.
- Inspect existing code and reports before inventing a new pattern. Extend the
  established Makefile, Python runner, test, JSON/CSV, and Markdown-report
  conventions.
- Prefer deterministic scripts over manual GUI steps. Record random seeds,
  PVT points, loads, frequencies, tool/container versions, and assumptions that
  affect a result.
- Keep source, verification, generated measurements, and the engineering
  conclusion together. Update README summaries when the project boundary or
  accepted/rejected architecture changes.
- Treat a rejected design as useful evidence. Report the failed gate and the
  next decision; never tune a threshold after seeing a result merely to obtain
  a pass.
- Preserve unrelated user changes. Never discard a dirty worktree or rewrite
  history to make an agent task easier.

## Evidence rules

- Never claim silicon performance, Bluetooth compliance, tapeout readiness,
  production cost, yield, or foundry signoff from schematic or behavioral
  simulation.
- Label analytical, behavioral, schematic, sampled-PVT, Monte Carlo, EM,
  extracted-layout, and measured evidence accurately. A later evidence level
  does not exist until its artifact and method are present.
- Keep provisional values provisional. In particular, passive Q, package and
  antenna behavior, device mismatch, sensor requirements, workload, and cost
  assumptions must not be presented as qualified facts.
- Use primary sources for specification claims. Community posts and AI output
  may suggest leads but are not specification evidence.
- Do not hide unfavorable corners or failed candidates. Machine-readable
  reports should contain the sampled population or enough detail to reproduce
  the selection, not only the winning row.
- Every report must state limitations and the specific gate it does or does not
  satisfy.

## Implementation conventions

- Python reference models live in `model/`; executable experiments live in
  `scripts/`; tests use `unittest` and cocotb patterns already in `tests/`.
- RTL must be synthesizable SystemVerilog unless a testbench is explicitly
  simulation-only. Keep bit order, timing, reset behavior, widths, and signed
  arithmetic explicit.
- Analog netlists in `analog/` are templates. Keep model/design paths
  replaceable and run ngspice in temporary directories through a checked-in
  Python driver.
- Write deterministic report files with stable ordering and a trailing newline.
  JSON reports should include a schema version, purpose, inputs/conditions,
  gates, result or selection, and limitations.
- Add new targets to `.PHONY`, the appropriate aggregate target, and `clean`.
  Generated scratch files belong in ignored directories; intentional reports
  belong in `reports/`.
- Use relative repository paths in documentation. Do not commit host-specific
  absolute paths, tokens, proprietary models, or credentials.
- Preserve the laboratory-only meaning of company identifier `0xFFFF`; do not
  describe the prototype advertising packet as a production CGM profile.

## Verification

Run the narrowest relevant check while iterating. The supported full gate is:

```bash
make container-check
```

The longer RF refresh is:

```bash
make container-rf-characterization
```

Do not run the longer target unless the work affects it or a full refresh is
requested. Direct Make targets require host tools; the pinned container is the
portable source of the EDA environment.

For every change:

1. run tests that exercise the changed behavior, including failure/boundary
   cases;
2. regenerate affected reports from their scripts rather than hand-editing
   measured values;
3. run `git diff --check` and review the complete diff; and
4. state exactly which checks ran, their result, and any checks not run.

Do not claim that a command passed unless its exit status and output were
observed. Do not paper over a reproducibility difference by reverting the
result without understanding it.

## Pull requests

Use an imperative title. In the body, explain:

- the design question or setup problem;
- the implementation and evidence added;
- the result and its limitations;
- validation commands and outcomes; and
- follow-up work or unresolved decisions.

Keep a pull request scoped to one slice. Avoid unrelated formatting, generated
noise, dependency updates, and refactors.
