#!/usr/bin/env python3
"""Characterize a first GF180 common-gate BLE LNA."""

from __future__ import annotations

import json
import math
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "analog" / "gf180_lna_tb.spice"
REPORT = ROOT / "reports" / "gf180_lna.json"
MODEL_FILE = os.environ.get(
    "GF180_MODEL_FILE",
    "/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice",
)
DESIGN_FILE = os.environ.get(
    "GF180_DESIGN_FILE",
    "/foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice",
)
FREQUENCY_HZ = 2.44e9
VDD_V = 1.8
SOURCE_RESISTANCE_OHM = 50.0
BOLTZMANN_CONSTANT_J_K = 1.380649e-23
CORNERS = (("typical", 25), ("ff", -40), ("ss", 85))
WIDTH_CANDIDATES_UM = (120.0, 160.0, 200.0, 240.0, 280.0)
BIAS_CURRENT_CANDIDATES_A = (0.8e-3, 1.0e-3, 1.2e-3, 1.4e-3, 1.6e-3)
GATE_BIAS_V = 0.9
TARGET_DRAIN_V = 0.78
LOAD_CAPACITANCE_F = 25e-15
MINIMUM_INTRINSIC_GAIN_DB = 12.0
MAXIMUM_NOISE_FIGURE_DB = 4.0
MINIMUM_INPUT_RETURN_LOSS_DB = 10.0
MINIMUM_DRAIN_SOURCE_V = 0.5


def read_last_row(path: Path) -> list[float]:
    rows = []
    for line in path.read_text().splitlines():
        fields = line.split()
        if not fields or fields[0].lower() in {"frequency", "scale"}:
            continue
        try:
            rows.append([float(field) for field in fields])
        except ValueError:
            continue
    if not rows:
        raise RuntimeError(f"ngspice produced no data in {path}")
    return rows[-1]


def lna_device_lines(total_width_um: float) -> str:
    parallel_devices = math.ceil(total_width_um / 14.08)
    width_um = total_width_um / parallel_devices
    fingers = min(10, max(1, round(width_um / 0.88)))
    return "\n".join(
        f"XLNA_{index} drain gate source 0 nfet_03v3 l=0.28u "
        f"w={width_um:.12g}u nf={fingers}"
        for index in range(parallel_devices)
    )


def simulate(configuration: dict, corner: str, temperature_c: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="gf180-lna-") as temporary_dir:
        temporary = Path(temporary_dir)
        op_file = temporary / "op.txt"
        ac_file = temporary / "ac.txt"
        noise_file = temporary / "noise.txt"
        netlist = (
            TEMPLATE.read_text()
            .replace("@@DESIGN_FILE@@", DESIGN_FILE)
            .replace("@@MODEL_FILE@@", MODEL_FILE)
            .replace("@@CORNER@@", corner)
            .replace("@@TEMP_C@@", str(temperature_c))
            .replace("@@FREQUENCY_HZ@@", str(FREQUENCY_HZ))
            .replace(
                "@@LNA_DEVICES@@",
                lna_device_lines(configuration["nmos_width_um"]),
            )
            .replace("@@BIAS_CURRENT_A@@", str(configuration["bias_current_a"]))
            .replace("@@GATE_BIAS_V@@", str(GATE_BIAS_V))
            .replace(
                "@@LOAD_RESISTANCE_OHM@@",
                str(configuration["load_resistance_ohm"]),
            )
            .replace("@@LOAD_CAPACITANCE_F@@", str(LOAD_CAPACITANCE_F))
            .replace("@@OPERATING_POINT_FILE@@", str(op_file))
            .replace("@@AC_FILE@@", str(ac_file))
            .replace("@@NOISE_FILE@@", str(noise_file))
        )
        path = temporary / "bench.spice"
        path.write_text(netlist)
        result = subprocess.run(
            ["ngspice", "-b", str(path)],
            cwd=temporary,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode or not noise_file.exists():
            output = result.stdout + result.stderr
            raise RuntimeError(f"GF180 LNA simulation failed\n{output[-8000:]}")
        op = read_last_row(op_file)
        ac = read_last_row(ac_file)
        noise = read_last_row(noise_file)

    supply_current_a = -op[1]
    drain_voltage_v = op[2]
    source_voltage_v = op[3]
    output_voltage = complex(ac[1], ac[2])
    source_voltage = complex(ac[3], ac[4])
    external_input_voltage = complex(ac[5], ac[6])
    input_impedance = (
        SOURCE_RESISTANCE_OHM
        * external_input_voltage
        / (1.0 - external_input_voltage)
    )
    reflection_coefficient = (
        input_impedance - SOURCE_RESISTANCE_OHM
    ) / (input_impedance + SOURCE_RESISTANCE_OHM)
    source_noise_v_sqrt_hz = math.sqrt(
        4.0
        * BOLTZMANN_CONSTANT_J_K
        * (temperature_c + 273.15)
        * SOURCE_RESISTANCE_OHM
    )
    return {
        "corner": corner,
        "temperature_c": temperature_c,
        "supply_current_a": supply_current_a,
        "supply_power_w": VDD_V * supply_current_a,
        "drain_voltage_v": drain_voltage_v,
        "source_voltage_v": source_voltage_v,
        "drain_source_voltage_v": drain_voltage_v - source_voltage_v,
        "generator_voltage_gain_db": 20.0 * math.log10(abs(output_voltage)),
        "intrinsic_voltage_gain_db": 20.0
        * math.log10(abs(output_voltage / source_voltage)),
        "input_resistance_ohm": input_impedance.real,
        "input_reactance_ohm": input_impedance.imag,
        "input_return_loss_db": -20.0
        * math.log10(abs(reflection_coefficient)),
        "output_noise_v_sqrt_hz": noise[1],
        "input_referred_noise_v_sqrt_hz": noise[2],
        "noise_figure_db": 20.0
        * math.log10(noise[2] / source_noise_v_sqrt_hz),
    }


def main() -> None:
    candidates = []
    for nmos_width_um in WIDTH_CANDIDATES_UM:
        for bias_current_a in BIAS_CURRENT_CANDIDATES_A:
            configuration = {
                "nmos_width_um": nmos_width_um,
                "bias_current_a": bias_current_a,
                "load_resistance_ohm": (VDD_V - TARGET_DRAIN_V)
                / bias_current_a,
            }
            points = [
                simulate(configuration, corner, temperature_c)
                for corner, temperature_c in CORNERS
            ]
            summary = {
                **configuration,
                "minimum_intrinsic_voltage_gain_db": min(
                    point["intrinsic_voltage_gain_db"] for point in points
                ),
                "maximum_noise_figure_db": max(
                    point["noise_figure_db"] for point in points
                ),
                "minimum_input_return_loss_db": min(
                    point["input_return_loss_db"] for point in points
                ),
                "minimum_drain_source_voltage_v": min(
                    point["drain_source_voltage_v"] for point in points
                ),
                "maximum_supply_power_w": max(
                    point["supply_power_w"] for point in points
                ),
                "points": points,
            }
            summary["passed"] = (
                summary["minimum_intrinsic_voltage_gain_db"]
                >= MINIMUM_INTRINSIC_GAIN_DB
                and summary["maximum_noise_figure_db"] <= MAXIMUM_NOISE_FIGURE_DB
                and summary["minimum_input_return_loss_db"]
                >= MINIMUM_INPUT_RETURN_LOSS_DB
                and summary["minimum_drain_source_voltage_v"]
                >= MINIMUM_DRAIN_SOURCE_V
            )
            candidates.append(summary)

    passing = [candidate for candidate in candidates if candidate["passed"]]
    if not passing:
        for candidate in candidates:
            print(
                candidate["nmos_width_um"],
                candidate["bias_current_a"],
                candidate["minimum_intrinsic_voltage_gain_db"],
                candidate["maximum_noise_figure_db"],
                candidate["minimum_input_return_loss_db"],
                candidate["minimum_drain_source_voltage_v"],
            )
        raise RuntimeError("no common-gate LNA candidate meets the sampled gates")
    selected = min(
        passing,
        key=lambda candidate: (
            candidate["maximum_supply_power_w"],
            candidate["maximum_noise_figure_db"],
        ),
    )
    report = {
        "schema_version": 1,
        "purpose": "GF180 common-gate BLE LNA feasibility",
        "frequency_hz": FREQUENCY_HZ,
        "source_resistance_ohm": SOURCE_RESISTANCE_OHM,
        "gate_bias_v": GATE_BIAS_V,
        "target_drain_voltage_v": TARGET_DRAIN_V,
        "load_capacitance_f": LOAD_CAPACITANCE_F,
        "selection_gates": {
            "minimum_intrinsic_voltage_gain_db": MINIMUM_INTRINSIC_GAIN_DB,
            "maximum_noise_figure_db": MAXIMUM_NOISE_FIGURE_DB,
            "minimum_input_return_loss_db": MINIMUM_INPUT_RETURN_LOSS_DB,
            "minimum_drain_source_voltage_v": MINIMUM_DRAIN_SOURCE_V,
        },
        "selected": selected,
        "accepted_for_next_stage": selected["passed"],
        "candidate_count": len(candidates),
        "passing_candidate_count": len(passing),
        "candidates": candidates,
        "limitations": [
            "The source bias uses an ideal noiseless current sink.",
            "The output is a provisional 25 fF high-impedance mixer-gate load.",
            "No input matching network, linearity, blockers, stability, mismatch, or layout is modeled.",
            "Noise figure is derived from ngspice input-referred noise and the 50 ohm source thermal noise.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")


if __name__ == "__main__":
    main()
