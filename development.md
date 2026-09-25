# Local development

This is the supported path for reproducing the CGM Radio Lab on a new
computer. The project deliberately runs its EDA tools in a pinned Docker image
so that contributors do not need to assemble a compatible simulator, PDK, and
synthesis toolchain on the host.

## Prerequisites

Install:

- Git;
- Docker Desktop (or Docker Engine on Linux); and
- a GitHub account with access to `bhadrip/cgm-radio-lab`.

On Windows, use a WSL2 Ubuntu terminal for the repository and all commands
below. Enable Docker Desktop's WSL integration for that distribution, keep the
checkout in the WSL filesystem (for example, under `~/src`, not `/mnt/c`), and
confirm that `docker run` works from WSL. This avoids path translation,
permissions, performance, and line-ending problems.

The pinned image is:

```text
docker.io/hpretl/iic-osic-tools:2026.08
```

It publishes both `linux/amd64` and `linux/arm64` images. Docker selects the
correct one for Intel/AMD PCs and Apple Silicon automatically.

## Clone and initialize

From a WSL, Linux, or macOS terminal:

```bash
mkdir -p ~/src
cd ~/src
git clone --recurse-submodules https://github.com/bhadrip/cgm-radio-lab.git
cd cgm-radio-lab
git submodule update --init --recursive
git status
```

If GitHub rejects the clone, first verify that the signed-in GitHub account is
a repository collaborator. For a private repository, authenticate with GitHub
CLI (`gh auth login`) or use an SSH remote associated with an authorized key.
Do not put a personal access token in the remote URL, a checked-in file, or a
prompt sent to an AI agent.

## Verify the environment

Confirm Docker is reachable and pull the pinned image:

```bash
docker version
docker pull docker.io/hpretl/iic-osic-tools:2026.08
```

Run the complete reproducible test and synthesis loop from the repository
root:

```bash
make container-check
```

This is the main acceptance command. It mounts the checkout at
`/foss/designs/cgm-radio-lab`, runs as the host user, and supplies Python,
Icarus Verilog, cocotb, Yosys, ngspice, and the GF180 PDK from the image. It can
take substantially longer than a software-only test because it runs analog
sweeps and regenerates tracked reports. After it finishes, inspect `git status`
and `git diff`. Numerical results should reproduce; `reports/experiment.json`
also records the current Git revision, so that metadata can change on a newer
commit even when its measurements are identical.

For the longer settled LC-DCO and RF characterization flow, run:

```bash
make container-rf-characterization
```

Run this only when the change affects that evidence or when a full RF refresh
is requested.

## Faster development loops

The Makefile lists focused targets such as `python-test`, `rtl-test`,
`gf180-lna-test`, and `yosys-stat`. They can be run directly only when their
host dependencies are installed. To run one target with the pinned container,
use:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  --entrypoint /bin/bash \
  -e HOME=/tmp \
  -v "$PWD:/foss/designs/cgm-radio-lab" \
  -w /foss/designs/cgm-radio-lab \
  docker.io/hpretl/iic-osic-tools:2026.08 \
  -lc 'make python-test'
```

Replace `python-test` with the narrow target relevant to the change. Before a
pull request, run the narrowest meaningful checks and then
`make container-check` when the scope or runtime makes that practical. State
exactly what was and was not run in the pull-request description.

## Using Claude Code

Start Claude from the repository root after the clone and submodule setup:

```bash
cd ~/src/cgm-radio-lab
claude
```

The root `CLAUDE.md` imports `AGENTS.md`, which is the shared instruction file
for Claude, Codex, and human contributors. Ask Claude to read
`development.md`, `AGENTS.md`, `spec.yaml`, and
`docs/engineering-basis.md` before proposing design work. Keep Claude inside
the repository, review its diff, and require it to run the relevant commands;
an agent's narrative is not verification evidence.

A useful first prompt is:

```text
Read CLAUDE.md and development.md, then inspect the repository without changing
files. Summarize the current design boundary, the evidence hierarchy, and the
commands you would run for the task I give you next.
```

Never paste secrets, proprietary PDK material, foundry credentials, or
unpublished product data into Claude. The checked-in GF180 material is open;
that does not make unrelated foundry data safe to share.

## Repository map

- `spec.yaml`: machine-readable project constants and provisional targets.
- `docs/engineering-basis.md`: requirements ledger, open product questions,
  evidence boundaries, and review gates.
- `model/`: executable Python reference models.
- `rtl/`: synthesizable SystemVerilog.
- `analog/`: ngspice testbench templates.
- `scripts/`: deterministic experiments and report generation.
- `tests/`: Python unit tests and cocotb RTL tests.
- `reports/`: checked-in machine-readable results and engineering conclusions.
- `wafer_space/`: GF180 wrapper and physical-design configuration.
- `third_party/gf180mcu-project-template/`: pinned Git submodule used by the
  Wafer.Space flow.

## Daily contribution workflow

Start from an up-to-date `main` and use one branch per vertical slice:

```bash
git switch main
git pull --ff-only
git submodule update --init --recursive
git switch -c slice/<short-description>
```

Keep generated evidence with the change that produced it. A typical circuit
slice updates the testbench, runner, model-level tests, JSON/CSV result,
engineering report, Makefile target/cleanup, and README summary together. A
failed candidate is a valid result when the experiment, rejection gate, and
next decision are recorded clearly.

Before committing:

```bash
git status --short
git diff --check
git diff
```

Do not commit simulator build directories, waveforms, credentials, or local
tool state. Do commit intentional, deterministic reports because they are part
of the project's reviewable evidence.

## Troubleshooting

- **`docker: command not found` or daemon connection failure:** start Docker
  Desktop/Engine, enable WSL integration if applicable, then rerun
  `docker version`.
- **Submodule directory is empty:** run
  `git submodule update --init --recursive` from the repository root.
- **Permission-denied files after a container run:** use the repository's
  Make targets or include `--user "$(id -u):$(id -g)"` in manual Docker runs.
- **GF180 model file missing during a native run:** use the container. Native
  analog scripts expect the image paths under `/foss/pdks/gf180mcuD` unless
  `GF180_MODEL_FILE` and `GF180_DESIGN_FILE` are explicitly set.
- **Windows shell/path errors:** move the checkout into WSL and run GNU `make`
  from the WSL terminal rather than PowerShell or Command Prompt.
- **Tests changed tracked reports:** inspect the diff. Keep it only if the
  source change intentionally changes the measurements; otherwise investigate
  the reproducibility failure instead of discarding it blindly. A metadata-only
  `git_revision` update in `reports/experiment.json` is expected when rerunning
  the experiment from a different commit.
