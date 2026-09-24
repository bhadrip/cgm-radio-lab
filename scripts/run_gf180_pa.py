#!/usr/bin/env python3
"""Characterize a minimal GF180 CMOS RF output stage into 50 ohms."""

from __future__ import annotations

import cmath
import json
import math
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "analog" / "gf180_pa_tb.spice"
REPORT = ROOT / "reports" / "gf180_pa.json"
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
LOAD_OHM = 50.0
CGM_BURST_S = 224e-6
CORNERS = (("typical", 25), ("ff", -40), ("ss", 125))
UNIT_NMOS_WIDTH_UM = 0.44
POWER_CODES = range(1, 129)
TARGET_POWER_LEVELS_DBM = (-20.0, -15.0, -10.0, -5.0, 0.0)
MAXIMUM_LEVEL_ERROR_DB = 1.0
HARMONICS = (2, 3)


def read_waveform(path: Path) -> tuple[list[float], list[float], list[float]]:
    rows = []
    for line in path.read_text().splitlines():
        fields = line.split()
        if not fields or fields[0].lower() == "time":
            continue
        rows.append([float(field) for field in fields])
    if not rows:
        raise RuntimeError("ngspice produced no PA waveform samples")
    column_count = len(rows[0])
    if column_count == 4:
        return (
            [row[0] for row in rows],
            [row[2] for row in rows],
            [row[3] for row in rows],
        )
    if column_count == 3:
        return (
            [row[0] for row in rows],
            [row[1] for row in rows],
            [row[2] for row in rows],
        )
    raise RuntimeError(f"unexpected ngspice waveform columns: {column_count}")


def tone_rms(
    times_s: list[float], values: list[float], harmonic: int = 1
) -> float:
    if harmonic < 1:
        raise ValueError("harmonic must be positive")
    final_time_s = times_s[-1]
    start_time_s = final_time_s - 16.0 / FREQUENCY_HZ
    selected = [
        (time_s, value)
        for time_s, value in zip(times_s, values)
        if time_s >= start_time_s
    ]
    duration_s = selected[-1][0] - selected[0][0]
    integral = 0j
    tone_hz = harmonic * FREQUENCY_HZ
    for (time_a, value_a), (time_b, value_b) in zip(selected, selected[1:]):
        phasor_a = value_a * cmath.exp(-2j * math.pi * tone_hz * time_a)
        phasor_b = value_b * cmath.exp(-2j * math.pi * tone_hz * time_b)
        integral += 0.5 * (phasor_a + phasor_b) * (time_b - time_a)
    peak_v = 2.0 * abs(integral) / duration_s
    return peak_v / math.sqrt(2.0)


def fundamental_rms(times_s: list[float], values: list[float]) -> float:
    return tone_rms(times_s, values)


def average_supply_power(
    times_s: list[float], supply_currents_a: list[float]
) -> float:
    start_time_s = times_s[-1] - 16.0 / FREQUENCY_HZ
    selected = [
        (time_s, -current_a)
        for time_s, current_a in zip(times_s, supply_currents_a)
        if time_s >= start_time_s
    ]
    charge_c = sum(
        0.5 * (current_a + current_b) * (time_b - time_a)
        for (time_a, current_a), (time_b, current_b) in zip(selected, selected[1:])
    )
    duration_s = selected[-1][0] - selected[0][0]
    return VDD_V * charge_c / duration_s


def simulate(width_um: float, corner: str, temperature_c: int) -> dict:
    parallel_devices = math.ceil(width_um / 14.08)
    device_nmos_width_um = width_um / parallel_devices
    device_pmos_width_um = 2.0 * device_nmos_width_um
    fingers = min(10, max(1, round(device_nmos_width_um / 0.88)))
    device_lines = []
    for index in range(parallel_devices):
        device_lines.append(
            f"XPA_P_{index} out in vdd vdd pfet_03v3 l=0.28u "
            f"w={device_pmos_width_um:.12g}u nf={fingers}"
        )
        device_lines.append(
            f"XPA_N_{index} out in 0 0 nfet_03v3 l=0.28u "
            f"w={device_nmos_width_um:.12g}u nf={fingers}"
        )
    devices = "\n".join(device_lines)
    with tempfile.TemporaryDirectory(prefix="gf180-pa-") as temporary_dir:
        temporary = Path(temporary_dir)
        waveform = temporary / "waveform.txt"
        netlist = (
            TEMPLATE.read_text()
            .replace("@@DESIGN_FILE@@", DESIGN_FILE)
            .replace("@@MODEL_FILE@@", MODEL_FILE)
            .replace("@@CORNER@@", corner)
            .replace("@@TEMP_C@@", str(temperature_c))
            .replace("@@PA_DEVICES@@", devices)
            .replace("@@WAVEFORM_FILE@@", str(waveform))
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
        if result.returncode:
            output = result.stdout + result.stderr
            raise RuntimeError(f"GF180 PA simulation failed\n{output[-8000:]}")
        times_s, output_v, supply_current_a = read_waveform(waveform)
    fundamental_voltage_rms_v = fundamental_rms(times_s, output_v)
    fundamental_power_w = fundamental_voltage_rms_v**2 / LOAD_OHM
    harmonic_power_w = {
        harmonic: tone_rms(times_s, output_v, harmonic) ** 2 / LOAD_OHM
        for harmonic in HARMONICS
    }
    supply_power_w = average_supply_power(times_s, supply_current_a)
    return {
        "corner": corner,
        "temperature_c": temperature_c,
        "nmos_width_um": width_um,
        "pmos_width_um": 2.0 * width_um,
        "parallel_device_pairs": parallel_devices,
        "fingers_per_device": fingers,
        "fundamental_voltage_rms_v": fundamental_voltage_rms_v,
        "fundamental_output_power_w": fundamental_power_w,
        "fundamental_output_power_dbm": 10.0 * math.log10(fundamental_power_w / 1e-3),
        "second_harmonic_output_power_dbm": 10.0
        * math.log10(harmonic_power_w[2] / 1e-3),
        "second_harmonic_dbc": 10.0
        * math.log10(harmonic_power_w[2] / fundamental_power_w),
        "third_harmonic_output_power_dbm": 10.0
        * math.log10(harmonic_power_w[3] / 1e-3),
        "third_harmonic_dbc": 10.0
        * math.log10(harmonic_power_w[3] / fundamental_power_w),
        "supply_power_w": supply_power_w,
        "drain_efficiency": fundamental_power_w / supply_power_w,
        "energy_per_224us_burst_j": supply_power_w * CGM_BURST_S,
    }


def main() -> None:
    points = [
        simulate(code * UNIT_NMOS_WIDTH_UM, corner, temperature_c)
        for code in POWER_CODES
        for corner, temperature_c in CORNERS
    ]
    calibration = []
    maximum_level_error_db = 0.0
    for corner, temperature_c in CORNERS:
        corner_points = [point for point in points if point["corner"] == corner]
        for target_dbm in TARGET_POWER_LEVELS_DBM:
            selected = min(
                corner_points,
                key=lambda point: abs(point["fundamental_output_power_dbm"] - target_dbm),
            )
            error_db = selected["fundamental_output_power_dbm"] - target_dbm
            maximum_level_error_db = max(maximum_level_error_db, abs(error_db))
            calibration.append(
                {
                    "corner": corner,
                    "temperature_c": temperature_c,
                    "target_output_power_dbm": target_dbm,
                    "selected_power_code": round(
                        selected["nmos_width_um"] / UNIT_NMOS_WIDTH_UM
                    ),
                    "realized_output_power_dbm": selected[
                        "fundamental_output_power_dbm"
                    ],
                    "level_error_db": error_db,
                    "second_harmonic_output_power_dbm": selected[
                        "second_harmonic_output_power_dbm"
                    ],
                    "second_harmonic_dbc": selected["second_harmonic_dbc"],
                    "third_harmonic_output_power_dbm": selected[
                        "third_harmonic_output_power_dbm"
                    ],
                    "third_harmonic_dbc": selected["third_harmonic_dbc"],
                    "supply_power_w": selected["supply_power_w"],
                    "energy_per_224us_burst_j": selected[
                        "energy_per_224us_burst_j"
                    ],
                    "drain_efficiency": selected["drain_efficiency"],
                }
            )
    curves = []
    for corner, temperature_c in CORNERS:
        corner_points = [point for point in points if point["corner"] == corner]
        curves.append(
            {
                "corner": corner,
                "temperature_c": temperature_c,
                "output_power_dbm_by_code": [
                    point["fundamental_output_power_dbm"] for point in corner_points
                ],
                "supply_power_w_by_code": [
                    point["supply_power_w"] for point in corner_points
                ],
            }
        )
    report = {
        "schema_version": 2,
        "purpose": "broadband GF180 RF output-stage feasibility",
        "frequency_hz": FREQUENCY_HZ,
        "load_ohm": LOAD_OHM,
        "burst_duration_s": CGM_BURST_S,
        "target_output_power_dbm": {"minimum": -20.0, "maximum": 0.0},
        "unit_nmos_width_um": UNIT_NMOS_WIDTH_UM,
        "unit_pmos_width_um": 2.0 * UNIT_NMOS_WIDTH_UM,
        "maximum_power_code": max(POWER_CODES),
        "maximum_level_error_db": maximum_level_error_db,
        "level_error_limit_db": MAXIMUM_LEVEL_ERROR_DB,
        "worst_selected_second_harmonic_dbc": max(
            point["second_harmonic_dbc"] for point in calibration
        ),
        "worst_selected_third_harmonic_dbc": max(
            point["third_harmonic_dbc"] for point in calibration
        ),
        "maximum_selected_second_harmonic_output_power_dbm": max(
            point["second_harmonic_output_power_dbm"] for point in calibration
        ),
        "maximum_selected_third_harmonic_output_power_dbm": max(
            point["third_harmonic_output_power_dbm"] for point in calibration
        ),
        "maximum_selected_supply_power_w": max(
            point["supply_power_w"] for point in calibration
        ),
        "maximum_selected_energy_per_224us_burst_j": max(
            point["energy_per_224us_burst_j"] for point in calibration
        ),
        "passed": maximum_level_error_db <= MAXIMUM_LEVEL_ERROR_DB,
        "calibration": calibration,
        "curves": curves,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")
    if not report["passed"]:
        raise RuntimeError("CMOS RF output stage did not span the target power range")


if __name__ == "__main__":
    main()
