#!/usr/bin/env python3
"""Drive the GF180 LC-DCO with a short 16 MHz Gaussian control sequence."""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import tempfile
from pathlib import Path

from model.dco import ble_channel_center_hz
from model.lc_dco_dac import SegmentedVoltageDac, VoltageDac
from model.lc_dco_modulation import (
    control_voltage_for_frequency,
    control_waveform,
    frequency_for_control_voltage,
)


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "analog" / "gf180_lc_dco_dynamic_tb.spice"
STATIC_SWEEP = ROOT / "reports" / "lc_dco_sweep.json"
LOCAL_CALIBRATION = ROOT / "reports" / "lc_dco_local_calibration.json"
SEGMENTED_DAC = ROOT / "reports" / "lc_dco_segmented_dac.json"
NONIDEALITY_BUDGET = ROOT / "reports" / "lc_dco_dac_nonidealities.json"
REPORT = ROOT / "reports" / "lc_dco_dynamic.json"
MODEL_FILE = os.environ.get(
    "GF180_MODEL_FILE",
    "/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice",
)
DESIGN_FILE = os.environ.get(
    "GF180_DESIGN_FILE",
    "/foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice",
)
BITS = (0, 0, 0, 0, 1, 0, 1)
SAMPLE_PERIOD_S = 1 / 16_000_000
MEASURE_START_SAMPLE = 4 * 16
MAXIMUM_ERROR_LIMIT_HZ = 40_000
MEAN_ERROR_LIMIT_HZ = 10_000
DEFAULT_DRIVE_RESISTANCE_OHM = float(
    os.environ.get("LC_DCO_DRIVE_RESISTANCE_OHM", "1000")
)
DEFAULT_CONTROL_LOAD_F = float(os.environ.get("LC_DCO_CONTROL_LOAD_F", "10e-12"))
DEFAULT_MODULATION_TRIM_CODES = int(os.environ.get("LC_DCO_MODULATION_TRIM_CODES", "-2"))
FREQUENCY = re.compile(r"^freq_(\d+)\s*=\s*([-+0-9.eE]+)", re.MULTILINE)
SCALAR = re.compile(
    r"^(differential_vpp|supply_current_a|power_w)\s*=\s*([-+0-9.eE]+)",
    re.MULTILINE,
)


def coarse_instances(count: int) -> str:
    lines = []
    for index in range(count):
        lines.extend(
            (
                f"XCOARSEP{index} outp 0 cap_mim_1f5_m4m5_noshield "
                "c_width=5u c_length=5u",
                f"XCOARSEN{index} outn 0 cap_mim_1f5_m4m5_noshield "
                "c_width=5u c_length=5u",
            )
        )
    return "\n".join(lines)


def control_pwl(voltages: list[float]) -> str:
    transition_s = 1e-9
    points = [(0.0, voltages[0])]
    for index, voltage in enumerate(voltages[1:], start=1):
        edge_s = index * SAMPLE_PERIOD_S
        points.append((edge_s - transition_s, voltages[index - 1]))
        points.append((edge_s, voltage))
    stop_s = len(voltages) * SAMPLE_PERIOD_S
    points.append((stop_s, voltages[-1]))
    return " ".join(f"{time_s:.12g} {voltage:.12g}" for time_s, voltage in points)


def measurements(sample_count: int) -> str:
    lines = []
    for sample in range(MEASURE_START_SAMPLE, sample_count):
        delay_s = sample * SAMPLE_PERIOD_S + 5e-9
        lines.extend(
            (
                f".measure tran span_{sample:03d} TRIG v(diff) VAL=0 "
                f"RISE=1 TD={delay_s:.12g}",
                f"+ TARG v(diff) VAL=0 RISE=101 TD={delay_s:.12g}",
                f".measure tran freq_{sample:03d} PARAM='100/span_{sample:03d}'",
            )
        )
    return "\n".join(lines)


def run_dynamic(
    drive_resistance_ohm: float = DEFAULT_DRIVE_RESISTANCE_OHM,
    control_load_f: float = DEFAULT_CONTROL_LOAD_F,
    modulation_trim_codes: int = DEFAULT_MODULATION_TRIM_CODES,
) -> dict:
    if drive_resistance_ohm <= 0 or control_load_f <= 0:
        raise ValueError("drive resistance and control load must be positive")
    static_points = json.loads(STATIC_SWEEP.read_text())["points"]
    static_points += json.loads(LOCAL_CALIBRATION.read_text())["points"]
    calibration, offsets_hz, ideal_voltages = control_waveform(
        static_points, "typical", 37, BITS
    )
    dac_report = json.loads(SEGMENTED_DAC.read_text())
    nonideality_report = json.loads(NONIDEALITY_BUDGET.read_text())
    dac = SegmentedVoltageDac(
        VoltageDac(
            dac_report["selected_bias_bits"],
            dac_report["bias_range_v"]["minimum"],
            dac_report["bias_range_v"]["maximum"],
        ),
        VoltageDac(
            nonideality_report["selected_modulation_bits"],
            dac_report["modulation_range_v"]["minimum"],
            dac_report["modulation_range_v"]["maximum"],
        ),
    )
    center_voltage_v = control_voltage_for_frequency(
        static_points, calibration, ble_channel_center_hz(37)
    )
    bias_code, modulation_codes, _ = dac.quantize_waveform(
        center_voltage_v, ideal_voltages
    )
    modulation_codes = [code + modulation_trim_codes for code in modulation_codes]
    if any(code < 0 or code > dac.modulation.maximum_code for code in modulation_codes):
        raise ValueError("modulation trim saturates the fast DAC")
    bias_voltage_v = dac.bias.voltage_for_code(bias_code)
    voltages = [
        bias_voltage_v + dac.modulation.voltage_for_code(code)
        for code in modulation_codes
    ]
    _, center_codes, center_outputs = dac.quantize_waveform(
        center_voltage_v, [center_voltage_v]
    )
    center_code = center_codes[0]
    adjacent_code = center_code + 1 if center_code < dac.modulation.maximum_code else center_code - 1
    adjacent_voltage_v = bias_voltage_v + dac.modulation.voltage_for_code(adjacent_code)
    center_frequency_hz = frequency_for_control_voltage(
        static_points, calibration, center_outputs[0]
    )
    adjacent_frequency_hz = frequency_for_control_voltage(
        static_points, calibration, adjacent_voltage_v
    )
    modeled_code_step_hz = abs(adjacent_frequency_hz - center_frequency_hz)
    stop_s = len(voltages) * SAMPLE_PERIOD_S
    netlist = (
        TEMPLATE.read_text()
        .replace("@@DESIGN_FILE@@", DESIGN_FILE)
        .replace("@@MODEL_FILE@@", MODEL_FILE)
        .replace("@@CONTROL_PWL@@", control_pwl(voltages))
        .replace("@@DRIVE_RESISTANCE_OHM@@", f"{drive_resistance_ohm:.12g}")
        .replace("@@CONTROL_LOAD_F@@", f"{control_load_f:.12g}")
        .replace("@@COARSE_CAPS@@", coarse_instances(calibration.coarse_code))
        .replace("@@MEASUREMENTS@@", measurements(len(voltages)))
        .replace("@@STOP_TIME@@", f"{stop_s:.12g}")
    )
    with tempfile.TemporaryDirectory(prefix="lc-dco-dynamic-") as temporary_dir:
        path = Path(temporary_dir) / "bench.spice"
        path.write_text(netlist)
        result = subprocess.run(
            ["ngspice", "-b", str(path)],
            cwd=temporary_dir,
            text=True,
            capture_output=True,
            check=False,
        )
    output = result.stdout + result.stderr
    measured = {int(index): float(value) for index, value in FREQUENCY.findall(output)}
    scalars = {name: float(value) for name, value in SCALAR.findall(output)}
    expected_samples = len(voltages) - MEASURE_START_SAMPLE
    if result.returncode or len(measured) != expected_samples or len(scalars) != 3:
        raise RuntimeError(f"dynamic ngspice run failed\n{output[-8000:]}")
    center_hz = ble_channel_center_hz(37)
    samples = [
        {
            "sample": sample,
            "time_s": sample * SAMPLE_PERIOD_S,
            "requested_frequency_hz": center_hz + offsets_hz[sample],
            "measured_frequency_hz": measured[sample],
            "error_hz": measured[sample] - (center_hz + offsets_hz[sample]),
            "ideal_control_voltage_v": ideal_voltages[sample],
            "modulation_code": modulation_codes[sample],
            "control_voltage_v": voltages[sample],
        }
        for sample in range(MEASURE_START_SAMPLE, len(voltages))
    ]
    errors = [sample["error_hz"] for sample in samples]
    mean_error_hz = sum(errors) / len(errors)
    maximum_error_hz = max(abs(error) for error in errors)
    passed = (
        maximum_error_hz <= MAXIMUM_ERROR_LIMIT_HZ
        and abs(mean_error_hz) <= MEAN_ERROR_LIMIT_HZ
    )
    report = {
        "schema_version": 1,
        "corner": "typical",
        "channel": 37,
        "coarse_code": calibration.coarse_code,
        "bits": list(BITS),
        "sample_rate_hz": 16_000_000,
        "bias_dac_bits": dac.bias.bits,
        "bias_dac_code": bias_code,
        "bias_dac_voltage_v": bias_voltage_v,
        "modulation_dac_bits": dac.modulation.bits,
        "modulation_dac_lsb_v": dac.modulation.lsb_v,
        "modulation_trim_codes": modulation_trim_codes,
        "modeled_modulation_code_step_hz": modeled_code_step_hz,
        "drive_resistance_ohm": drive_resistance_ohm,
        "control_load_f": control_load_f,
        "drive_time_constant_s": drive_resistance_ohm * control_load_f,
        "drive_bandwidth_hz": 1 / (
            2 * math.pi * drive_resistance_ohm * control_load_f
        ),
        "measured_samples": len(samples),
        "mean_frequency_error_hz": mean_error_hz,
        "maximum_absolute_frequency_error_hz": maximum_error_hz,
        "mean_frequency_error_limit_hz": MEAN_ERROR_LIMIT_HZ,
        "maximum_absolute_frequency_error_limit_hz": MAXIMUM_ERROR_LIMIT_HZ,
        "passed": passed,
        "differential_vpp": scalars["differential_vpp"],
        "supply_current_a": -scalars["supply_current_a"],
        "power_w": scalars["power_w"],
        "samples": samples,
    }
    return report


def main() -> None:
    report = run_dynamic()
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")
    if not report["passed"]:
        raise RuntimeError(
            "dynamic frequency error failed limits: "
            f"mean={report['mean_frequency_error_hz']} Hz, "
            f"maximum={report['maximum_absolute_frequency_error_hz']} Hz"
        )


if __name__ == "__main__":
    main()
