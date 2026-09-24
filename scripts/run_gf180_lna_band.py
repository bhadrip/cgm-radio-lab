#!/usr/bin/env python3
"""Sweep the selected GF180 LNA across all BLE channel centers."""

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
    GATE_BIAS_V,
    LOAD_CAPACITANCE_F,
    MAXIMUM_NOISE_FIGURE_DB,
    MINIMUM_INPUT_RETURN_LOSS_DB,
    MINIMUM_INTRINSIC_GAIN_DB,
    MODEL_FILE,
    SOURCE_RESISTANCE_OHM,
    TEMPLATE,
    lna_device_lines,
    read_rows,
)


ROOT = Path(__file__).resolve().parents[1]
LNA_REPORT = ROOT / "reports" / "gf180_lna.json"
REPORT = ROOT / "reports" / "gf180_lna_band.json"
CHANNEL_FREQUENCIES_HZ = tuple(2.402e9 + 2e6 * index for index in range(40))


def simulate_band(configuration: dict, corner: str, temperature_c: int) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="gf180-lna-band-") as temporary_dir:
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
            .replace("@@POINT_COUNT@@", str(len(CHANNEL_FREQUENCIES_HZ)))
            .replace("@@START_FREQUENCY_HZ@@", str(CHANNEL_FREQUENCIES_HZ[0]))
            .replace("@@STOP_FREQUENCY_HZ@@", str(CHANNEL_FREQUENCIES_HZ[-1]))
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
            raise RuntimeError(f"GF180 LNA band simulation failed\n{output[-8000:]}")
        ac_rows = read_rows(ac_file)
        noise_rows = read_rows(noise_file)
    if len(ac_rows) != 40 or len(noise_rows) != 40:
        raise RuntimeError("LNA band sweep did not return all BLE channels")

    source_noise_v_sqrt_hz = math.sqrt(
        4.0
        * BOLTZMANN_CONSTANT_J_K
        * (temperature_c + 273.15)
        * SOURCE_RESISTANCE_OHM
    )
    points = []
    for ac, noise in zip(ac_rows, noise_rows):
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
        points.append(
            {
                "frequency_hz": ac[0],
                "intrinsic_voltage_gain_db": 20.0
                * math.log10(abs(output_voltage / source_voltage)),
                "input_return_loss_db": -20.0
                * math.log10(abs(reflection_coefficient)),
                "noise_figure_db": 20.0
                * math.log10(noise[2] / source_noise_v_sqrt_hz),
            }
        )
    return points


def main() -> None:
    selected = json.loads(LNA_REPORT.read_text())["selected"]
    configuration = {
        "nmos_width_um": selected["nmos_width_um"],
        "bias_current_a": selected["bias_current_a"],
        "load_resistance_ohm": selected["load_resistance_ohm"],
    }
    summaries = []
    for corner, temperature_c in CORNERS:
        points = simulate_band(configuration, corner, temperature_c)
        summaries.append(
            {
                "corner": corner,
                "temperature_c": temperature_c,
                "minimum_intrinsic_voltage_gain_db": min(
                    point["intrinsic_voltage_gain_db"] for point in points
                ),
                "maximum_noise_figure_db": max(
                    point["noise_figure_db"] for point in points
                ),
                "minimum_input_return_loss_db": min(
                    point["input_return_loss_db"] for point in points
                ),
                "points": points,
            }
        )
    for summary in summaries:
        summary["passed"] = (
            summary["minimum_intrinsic_voltage_gain_db"]
            >= MINIMUM_INTRINSIC_GAIN_DB
            and summary["maximum_noise_figure_db"] <= MAXIMUM_NOISE_FIGURE_DB
            and summary["minimum_input_return_loss_db"]
            >= MINIMUM_INPUT_RETURN_LOSS_DB
        )
    report = {
        "schema_version": 1,
        "purpose": "selected GF180 LNA coverage across BLE channel centers",
        "configuration": configuration,
        "channel_count": len(CHANNEL_FREQUENCIES_HZ),
        "minimum_frequency_hz": CHANNEL_FREQUENCIES_HZ[0],
        "maximum_frequency_hz": CHANNEL_FREQUENCIES_HZ[-1],
        "gates": {
            "minimum_intrinsic_voltage_gain_db": MINIMUM_INTRINSIC_GAIN_DB,
            "maximum_noise_figure_db": MAXIMUM_NOISE_FIGURE_DB,
            "minimum_input_return_loss_db": MINIMUM_INPUT_RETURN_LOSS_DB,
        },
        "minimum_intrinsic_voltage_gain_db": min(
            summary["minimum_intrinsic_voltage_gain_db"] for summary in summaries
        ),
        "maximum_noise_figure_db": max(
            summary["maximum_noise_figure_db"] for summary in summaries
        ),
        "minimum_input_return_loss_db": min(
            summary["minimum_input_return_loss_db"] for summary in summaries
        ),
        "passed": all(summary["passed"] for summary in summaries),
        "summaries": summaries,
        "limitations": [
            "The same schematic and ideal-bias limitations as the center-frequency LNA sweep apply.",
            "Only nominal channel centers are sampled; no off-channel blocker or stability sweep is included.",
            "Voltage gain is not matched transducer power gain or S21.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")
    if not report["passed"]:
        raise RuntimeError("selected LNA does not hold its gates across the BLE band")


if __name__ == "__main__":
    main()
