#!/usr/bin/env python3
"""Test a low-headroom NMOS current-mirror bias for the selected GF180 LNA."""

from __future__ import annotations

import json
import math
import subprocess
import tempfile
from pathlib import Path

from scripts.run_gf180_lna import (
    BOLTZMANN_CONSTANT_J_K,
    CORNERS,
    DESIGN_FILE,
    FREQUENCY_HZ,
    GATE_BIAS_V,
    LOAD_CAPACITANCE_F,
    MODEL_FILE,
    SOURCE_RESISTANCE_OHM,
    VDD_V,
    lna_device_lines,
    read_last_row,
)


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "analog" / "gf180_lna_mirror_bias_tb.spice"
LNA_REPORT = ROOT / "reports" / "gf180_lna.json"
REPORT = ROOT / "reports" / "gf180_lna_mirror_bias.json"
MIRROR_RATIO = 16
UNIT_WIDTH_UM = 10.0
REFERENCE_PARALLEL_CANDIDATES = (2, 4, 8, 12, 16, 24)
TARGET_LNA_CURRENT_A = 1.4e-3
REFERENCE_CURRENT_A = TARGET_LNA_CURRENT_A / MIRROR_RATIO
MINIMUM_LNA_CURRENT_A = 1.2e-3
MAXIMUM_LNA_CURRENT_A = 1.6e-3
MINIMUM_INTRINSIC_GAIN_DB = 12.0
MAXIMUM_NOISE_FIGURE_DB = 4.0
MINIMUM_INPUT_RETURN_LOSS_DB = 10.0
MINIMUM_DRAIN_SOURCE_V = 0.5


def bias_device_lines(reference_parallel: int) -> str:
    reference = [
        f"XBIAS_REF_{index} bias_gate bias_gate 0 0 nfet_03v3 l=0.28u "
        f"w={UNIT_WIDTH_UM}u nf=10"
        for index in range(reference_parallel)
    ]
    output = [
        f"XBIAS_OUT_{index} source bias_gate 0 0 nfet_03v3 l=0.28u "
        f"w={UNIT_WIDTH_UM}u nf=10"
        for index in range(reference_parallel * MIRROR_RATIO)
    ]
    return "\n".join(reference + output)


def simulate(configuration: dict, corner: str, temperature_c: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="gf180-lna-mirror-") as temporary_dir:
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
            .replace("@@GATE_BIAS_V@@", str(GATE_BIAS_V))
            .replace("@@LNA_DEVICES@@", lna_device_lines(configuration["nmos_width_um"]))
            .replace("@@REFERENCE_CURRENT_A@@", str(REFERENCE_CURRENT_A))
            .replace(
                "@@BIAS_DEVICES@@",
                bias_device_lines(configuration["reference_parallel"]),
            )
            .replace("@@LOAD_RESISTANCE_OHM@@", str(configuration["load_resistance_ohm"]))
            .replace("@@LOAD_CAPACITANCE_F@@", str(LOAD_CAPACITANCE_F))
            .replace("@@FREQUENCY_HZ@@", str(FREQUENCY_HZ))
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
            raise RuntimeError(f"GF180 LNA mirror-bias simulation failed\n{output[-8000:]}")
        op = read_last_row(op_file)
        ac = read_last_row(ac_file)
        noise = read_last_row(noise_file)

    drain_voltage_v = op[2]
    source_voltage_v = op[3]
    output_voltage = complex(ac[1], ac[2])
    source_voltage = complex(ac[3], ac[4])
    external_input_voltage = complex(ac[5], ac[6])
    input_impedance = (
        SOURCE_RESISTANCE_OHM * external_input_voltage / (1.0 - external_input_voltage)
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
    lna_current_a = (VDD_V - drain_voltage_v) / configuration["load_resistance_ohm"]
    return {
        "corner": corner,
        "temperature_c": temperature_c,
        "supply_current_a": -op[1],
        "supply_power_w": -VDD_V * op[1],
        "lna_current_a": lna_current_a,
        "drain_voltage_v": drain_voltage_v,
        "source_voltage_v": source_voltage_v,
        "bias_gate_voltage_v": op[4],
        "drain_source_voltage_v": drain_voltage_v - source_voltage_v,
        "intrinsic_voltage_gain_db": 20.0
        * math.log10(abs(output_voltage / source_voltage)),
        "input_return_loss_db": -20.0 * math.log10(abs(reflection_coefficient)),
        "noise_figure_db": 20.0
        * math.log10(noise[2] / source_noise_v_sqrt_hz),
    }


def main() -> None:
    selected = json.loads(LNA_REPORT.read_text())["selected"]
    candidates = []
    for reference_parallel in REFERENCE_PARALLEL_CANDIDATES:
        configuration = {
            "nmos_width_um": selected["nmos_width_um"],
            "load_resistance_ohm": selected["load_resistance_ohm"],
            "reference_parallel": reference_parallel,
            "reference_width_um": reference_parallel * UNIT_WIDTH_UM,
            "output_width_um": reference_parallel * MIRROR_RATIO * UNIT_WIDTH_UM,
        }
        points = [
            simulate(configuration, corner, temperature_c)
            for corner, temperature_c in CORNERS
        ]
        summary = {
            **configuration,
            "minimum_lna_current_a": min(point["lna_current_a"] for point in points),
            "maximum_lna_current_a": max(point["lna_current_a"] for point in points),
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
            summary["minimum_lna_current_a"] >= MINIMUM_LNA_CURRENT_A
            and summary["maximum_lna_current_a"] <= MAXIMUM_LNA_CURRENT_A
            and summary["minimum_intrinsic_voltage_gain_db"]
            >= MINIMUM_INTRINSIC_GAIN_DB
            and summary["maximum_noise_figure_db"] <= MAXIMUM_NOISE_FIGURE_DB
            and summary["minimum_input_return_loss_db"]
            >= MINIMUM_INPUT_RETURN_LOSS_DB
            and summary["minimum_drain_source_voltage_v"]
            >= MINIMUM_DRAIN_SOURCE_V
        )
        candidates.append(summary)

    passing = [candidate for candidate in candidates if candidate["passed"]]
    report = {
        "schema_version": 1,
        "purpose": "low-headroom NMOS current-mirror LNA bias feasibility",
        "mirror_ratio": MIRROR_RATIO,
        "unit_width_um": UNIT_WIDTH_UM,
        "reference_current_a": REFERENCE_CURRENT_A,
        "gates": {
            "minimum_lna_current_a": MINIMUM_LNA_CURRENT_A,
            "maximum_lna_current_a": MAXIMUM_LNA_CURRENT_A,
            "minimum_intrinsic_voltage_gain_db": MINIMUM_INTRINSIC_GAIN_DB,
            "maximum_noise_figure_db": MAXIMUM_NOISE_FIGURE_DB,
            "minimum_input_return_loss_db": MINIMUM_INPUT_RETURN_LOSS_DB,
            "minimum_drain_source_voltage_v": MINIMUM_DRAIN_SOURCE_V,
        },
        "accepted_for_next_stage": bool(passing),
        "selected": min(passing, key=lambda item: item["output_width_um"])
        if passing
        else None,
        "candidate_count": len(candidates),
        "passing_candidate_count": len(passing),
        "candidates": candidates,
        "limitations": [
            "The reference current is ideal; a physical reference and startup remain open.",
            "Mirror mismatch, flicker noise, extracted parasitics, package, and layout are not modeled.",
            "Failure rejects only this low-headroom mirror implementation, not other LNA topologies.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")


if __name__ == "__main__":
    main()
