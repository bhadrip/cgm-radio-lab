#!/usr/bin/env python3
"""Screen selected GF180 LNA two-tone linearity across sampled PVT."""

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
    SOURCE_RESISTANCE_OHM,
    lna_device_lines,
    read_rows,
)


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "analog" / "gf180_lna_two_tone_tb.spice"
LNA_REPORT = ROOT / "reports" / "gf180_lna.json"
REPORT = ROOT / "reports" / "gf180_lna_linearity.json"
TONE1_HZ = 2.43e9
TONE2_HZ = 2.45e9
LOWER_IM3_HZ = 2.0 * TONE1_HZ - TONE2_HZ
UPPER_IM3_HZ = 2.0 * TONE2_HZ - TONE1_HZ
INPUT_POWERS_DBM = (-30.0, -25.0, -20.0, -15.0, -10.0, -5.0, 0.0)
TRANSIENT_START_S = 100e-9
TRANSIENT_STOP_S = 300e-9
TRANSIENT_STEP_S = 20e-12


def available_power_source_peak_v(power_dbm: float) -> float:
    power_w = 10.0 ** ((power_dbm - 30.0) / 10.0)
    return math.sqrt(8.0 * SOURCE_RESISTANCE_OHM * power_w)


def tone_amplitude(rows: list[list[float]], column: int, frequency_hz: float) -> float:
    integral = 0j
    for left, right in zip(rows, rows[1:]):
        left_value = left[column] * complex(
            math.cos(-2.0 * math.pi * frequency_hz * left[0]),
            math.sin(-2.0 * math.pi * frequency_hz * left[0]),
        )
        right_value = right[column] * complex(
            math.cos(-2.0 * math.pi * frequency_hz * right[0]),
            math.sin(-2.0 * math.pi * frequency_hz * right[0]),
        )
        integral += 0.5 * (left_value + right_value) * (right[0] - left[0])
    duration_s = rows[-1][0] - rows[0][0]
    return 2.0 * abs(integral) / duration_s


def simulate(configuration: dict, corner: str, temperature_c: int, power_dbm: float) -> dict:
    with tempfile.TemporaryDirectory(prefix="gf180-lna-linearity-") as temporary_dir:
        temporary = Path(temporary_dir)
        transient_file = temporary / "transient.txt"
        netlist = (
            TEMPLATE.read_text()
            .replace("@@DESIGN_FILE@@", DESIGN_FILE)
            .replace("@@MODEL_FILE@@", MODEL_FILE)
            .replace("@@CORNER@@", corner)
            .replace("@@TEMP_C@@", str(temperature_c))
            .replace("@@SOURCE_PEAK_V@@", str(available_power_source_peak_v(power_dbm)))
            .replace("@@TONE1_HZ@@", str(TONE1_HZ))
            .replace("@@TONE2_HZ@@", str(TONE2_HZ))
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
            raise RuntimeError(f"GF180 LNA two-tone simulation failed\n{output[-8000:]}")
        rows = read_rows(transient_file)

    fundamental_v = math.sqrt(
        (
            tone_amplitude(rows, 1, TONE1_HZ) ** 2
            + tone_amplitude(rows, 1, TONE2_HZ) ** 2
        )
        / 2.0
    )
    im3_v = math.sqrt(
        (
            tone_amplitude(rows, 1, LOWER_IM3_HZ) ** 2
            + tone_amplitude(rows, 1, UPPER_IM3_HZ) ** 2
        )
        / 2.0
    )
    source_fundamental_v = math.sqrt(
        (
            tone_amplitude(rows, 2, TONE1_HZ) ** 2
            + tone_amplitude(rows, 2, TONE2_HZ) ** 2
        )
        / 2.0
    )
    fundamental_to_im3_db = 20.0 * math.log10(fundamental_v / im3_v)
    return {
        "input_power_per_tone_dbm": power_dbm,
        "source_peak_v": available_power_source_peak_v(power_dbm),
        "source_node_fundamental_peak_v": source_fundamental_v,
        "output_fundamental_peak_v": fundamental_v,
        "output_im3_peak_v": im3_v,
        "intrinsic_voltage_gain_db": 20.0 * math.log10(
            fundamental_v / source_fundamental_v
        ),
        "fundamental_to_im3_db": fundamental_to_im3_db,
        "iip3_estimate_dbm": power_dbm + fundamental_to_im3_db / 2.0,
    }


def main() -> None:
    selected = json.loads(LNA_REPORT.read_text())["selected"]
    configuration = {
        "nmos_width_um": selected["nmos_width_um"],
        "bias_current_a": selected["bias_current_a"],
        "load_resistance_ohm": selected["load_resistance_ohm"],
    }
    summaries = []
    for corner, temperature_c in CORNERS:
        points = [
            simulate(configuration, corner, temperature_c, power_dbm)
            for power_dbm in INPUT_POWERS_DBM
        ]
        low_level_gain_db = points[0]["intrinsic_voltage_gain_db"]
        first_compressed_index = next(
            (
                index
                for index, point in enumerate(points)
                if low_level_gain_db - point["intrinsic_voltage_gain_db"] >= 1.0
            ),
            None,
        )
        uncompressed_points = [
            point
            for point in points
            if low_level_gain_db - point["intrinsic_voltage_gain_db"] <= 0.5
        ]
        summaries.append(
            {
                "corner": corner,
                "temperature_c": temperature_c,
                "low_level_intrinsic_voltage_gain_db": low_level_gain_db,
                "two_tone_1db_compression_bracket_per_tone_dbm": (
                    [
                        points[first_compressed_index - 1]["input_power_per_tone_dbm"],
                        points[first_compressed_index]["input_power_per_tone_dbm"],
                    ]
                    if first_compressed_index not in {None, 0}
                    else None
                ),
                "minimum_uncompressed_iip3_estimate_dbm": min(
                    point["iip3_estimate_dbm"] for point in uncompressed_points
                ),
                "points": points,
            }
        )
    report = {
        "schema_version": 1,
        "purpose": "selected GF180 LNA two-tone linearity screen",
        "configuration": configuration,
        "tone_frequencies_hz": [TONE1_HZ, TONE2_HZ],
        "im3_frequencies_hz": [LOWER_IM3_HZ, UPPER_IM3_HZ],
        "input_powers_per_tone_dbm": list(INPUT_POWERS_DBM),
        "minimum_uncompressed_iip3_estimate_dbm": min(
            summary["minimum_uncompressed_iip3_estimate_dbm"]
            for summary in summaries
        ),
        "summaries": summaries,
        "limitations": [
            "IIP3 is a finite-level two-tone estimate, not a small-signal extrapolation or measurement.",
            "The ideal source-bias sink and provisional high-impedance mixer load remain in the bench.",
            "Package, matching, blocker response, mismatch, extracted layout, and measured RF remain open.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")


if __name__ == "__main__":
    main()
