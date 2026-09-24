#!/usr/bin/env python3
"""Check normal and boosted LNA states at the PR11 maximum input."""

from __future__ import annotations

import json
import math
import subprocess
import tempfile
from pathlib import Path

from scripts.run_gf180_lna import (
    CORNERS,
    DESIGN_FILE,
    GATE_BIAS_V,
    LOAD_CAPACITANCE_F,
    MODEL_FILE,
    lna_device_lines,
    read_rows,
)
from scripts.run_gf180_lna_linearity import (
    available_power_source_peak_v,
    tone_amplitude,
)


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "analog" / "gf180_lna_single_tone_tb.spice"
LNA_REPORT = ROOT / "reports" / "gf180_lna.json"
BOOST_REPORT = ROOT / "reports" / "gf180_lna_bias_boost.json"
REPORT = ROOT / "reports" / "gf180_lna_single_tone.json"
FREQUENCY_HZ = 2.44e9
INPUT_POWERS_DBM = (-30.0, -25.0, -20.0, -15.0, -10.0, -5.0)
PR11_MAXIMUM_INPUT_DBM = -10.0
MAXIMUM_GAIN_COMPRESSION_DB = 1.0
TRANSIENT_START_S = 100e-9
TRANSIENT_STOP_S = 300e-9
TRANSIENT_STEP_S = 20e-12


def simulate(configuration: dict, corner: str, temperature_c: int, power_dbm: float) -> dict:
    with tempfile.TemporaryDirectory(prefix="gf180-lna-single-tone-") as temporary_dir:
        temporary = Path(temporary_dir)
        transient_file = temporary / "transient.txt"
        netlist = (
            TEMPLATE.read_text()
            .replace("@@DESIGN_FILE@@", DESIGN_FILE)
            .replace("@@MODEL_FILE@@", MODEL_FILE)
            .replace("@@CORNER@@", corner)
            .replace("@@TEMP_C@@", str(temperature_c))
            .replace("@@SOURCE_PEAK_V@@", str(available_power_source_peak_v(power_dbm)))
            .replace("@@FREQUENCY_HZ@@", str(FREQUENCY_HZ))
            .replace("@@LNA_DEVICES@@", lna_device_lines(configuration["nmos_width_um"]))
            .replace("@@BIAS_CURRENT_A@@", str(configuration["bias_current_a"]))
            .replace("@@GATE_BIAS_V@@", str(GATE_BIAS_V))
            .replace("@@LOAD_RESISTANCE_OHM@@", str(configuration["load_resistance_ohm"]))
            .replace("@@LOAD_CAPACITANCE_F@@", str(LOAD_CAPACITANCE_F))
            .replace("@@STEP_S@@", str(TRANSIENT_STEP_S))
            .replace("@@START_S@@", str(TRANSIENT_START_S))
            .replace("@@STOP_S@@", str(TRANSIENT_STOP_S))
            .replace("@@TRANSIENT_FILE@@", str(transient_file))
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
        if result.returncode or not transient_file.exists():
            output = result.stdout + result.stderr
            raise RuntimeError(f"GF180 LNA single-tone simulation failed\n{output[-8000:]}")
        rows = read_rows(transient_file)
    output_v = tone_amplitude(rows, 1, FREQUENCY_HZ)
    source_v = tone_amplitude(rows, 2, FREQUENCY_HZ)
    return {
        "input_power_dbm": power_dbm,
        "source_peak_v": available_power_source_peak_v(power_dbm),
        "source_node_peak_v": source_v,
        "output_peak_v": output_v,
        "intrinsic_voltage_gain_db": 20.0 * math.log10(output_v / source_v),
    }


def main() -> None:
    normal = json.loads(LNA_REPORT.read_text())["selected"]
    boost = json.loads(BOOST_REPORT.read_text())["selected"]
    modes = []
    for name, source in (("normal", normal), ("bias_boost", boost)):
        configuration = {
            "nmos_width_um": source["nmos_width_um"],
            "bias_current_a": source["bias_current_a"],
            "load_resistance_ohm": source["load_resistance_ohm"],
        }
        summaries = []
        for corner, temperature_c in CORNERS:
            points = [
                simulate(configuration, corner, temperature_c, power_dbm)
                for power_dbm in INPUT_POWERS_DBM
            ]
            reference_gain_db = points[0]["intrinsic_voltage_gain_db"]
            for point in points:
                point["gain_compression_db"] = (
                    reference_gain_db - point["intrinsic_voltage_gain_db"]
                )
            maximum_input_point = next(
                point
                for point in points
                if point["input_power_dbm"] == PR11_MAXIMUM_INPUT_DBM
            )
            summaries.append(
                {
                    "corner": corner,
                    "temperature_c": temperature_c,
                    "reference_gain_db": reference_gain_db,
                    "maximum_input_gain_compression_db": maximum_input_point[
                        "gain_compression_db"
                    ],
                    "points": points,
                }
            )
        maximum_compression_db = max(
            summary["maximum_input_gain_compression_db"] for summary in summaries
        )
        modes.append(
            {
                "name": name,
                "configuration": configuration,
                "maximum_input_gain_compression_db": maximum_compression_db,
                "passed": maximum_compression_db <= MAXIMUM_GAIN_COMPRESSION_DB,
                "summaries": summaries,
            }
        )
    report = {
        "schema_version": 1,
        "purpose": "PR11 maximum-input single-tone LNA schematic screen",
        "frequency_hz": FREQUENCY_HZ,
        "input_powers_dbm": list(INPUT_POWERS_DBM),
        "pr11_maximum_input_dbm": PR11_MAXIMUM_INPUT_DBM,
        "maximum_gain_compression_db": MAXIMUM_GAIN_COMPRESSION_DB,
        "accepted_mode": "bias_boost",
        "accepted_for_next_stage": next(
            mode["passed"] for mode in modes if mode["name"] == "bias_boost"
        ),
        "modes": modes,
        "limitations": [
            "This is a schematic single-tone compression screen, not a Bluetooth qualification or measurement.",
            "Bias switching, blocker combinations, desensitization, package, layout, and mismatch remain open.",
            "The same ideal-bias and provisional high-impedance mixer-load limitations apply.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")
    if not report["accepted_for_next_stage"]:
        raise RuntimeError("bias-boost state misses the PR11 single-tone screen")


if __name__ == "__main__":
    main()
