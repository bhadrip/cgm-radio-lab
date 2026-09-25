#!/usr/bin/env python3
"""Build a first cascaded BLE LE 1M receiver noise and sensitivity budget."""

from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "rx_noise_budget.json"
BOLTZMANN_CONSTANT_J_K = 1.380649e-23
REFERENCE_TEMPERATURE_C = 25.0
MAXIMUM_OPERATING_TEMPERATURE_C = 85.0
NOISE_BANDWIDTH_HZ = 1_000_000.0
REQUIRED_DEMODULATOR_SNR_DB = 15.0
PROJECT_SENSITIVITY_TARGET_DBM = -80.0
BLUETOOTH_SENSITIVITY_LIMIT_DBM = -70.0
MAXIMUM_INPUT_LEVEL_DBM = -10.0

STAGES = (
    {"name": "RF switch and matching", "gain_db": -1.5, "noise_figure_db": 1.5},
    {"name": "LNA", "gain_db": 12.0, "noise_figure_db": 4.0},
    {"name": "mixer", "gain_db": 6.0, "noise_figure_db": 12.0},
    {"name": "baseband channel", "gain_db": 30.0, "noise_figure_db": 20.0},
)


def thermal_noise_density_dbm_hz(temperature_c: float) -> float:
    temperature_k = temperature_c + 273.15
    if temperature_k <= 0.0:
        raise ValueError("temperature must be above absolute zero")
    return 10.0 * math.log10(
        BOLTZMANN_CONSTANT_J_K * temperature_k / 1e-3
    )


def cascaded_noise_figure_db(stages: tuple[dict, ...] = STAGES) -> float:
    if not stages:
        raise ValueError("at least one receiver stage is required")
    cumulative_gain = 1.0
    cascade_factor = 0.0
    for index, stage in enumerate(stages):
        gain = 10.0 ** (stage["gain_db"] / 10.0)
        noise_factor = 10.0 ** (stage["noise_figure_db"] / 10.0)
        if gain <= 0.0 or noise_factor < 1.0:
            raise ValueError("stage gain and noise figure must be physical")
        if index == 0:
            cascade_factor = noise_factor
        else:
            cascade_factor += (noise_factor - 1.0) / cumulative_gain
        cumulative_gain *= gain
    return 10.0 * math.log10(cascade_factor)


def main() -> None:
    worst_noise_density_dbm_hz = thermal_noise_density_dbm_hz(
        MAXIMUM_OPERATING_TEMPERATURE_C
    )
    noise_floor_dbm = worst_noise_density_dbm_hz + 10.0 * math.log10(
        NOISE_BANDWIDTH_HZ
    )
    cascade_nf_db = cascaded_noise_figure_db()
    total_gain_db = sum(stage["gain_db"] for stage in STAGES)
    predicted_sensitivity_dbm = (
        noise_floor_dbm + cascade_nf_db + REQUIRED_DEMODULATOR_SNR_DB
    )
    maximum_nf_for_project_target_db = (
        PROJECT_SENSITIVITY_TARGET_DBM
        - noise_floor_dbm
        - REQUIRED_DEMODULATOR_SNR_DB
    )
    report = {
        "schema_version": 1,
        "purpose": "BLE LE 1M receiver architecture noise budget",
        "status": "provisional_architecture_allocation",
        "reference_temperature_c": REFERENCE_TEMPERATURE_C,
        "reference_thermal_noise_density_dbm_hz": thermal_noise_density_dbm_hz(
            REFERENCE_TEMPERATURE_C
        ),
        "budget_temperature_c": MAXIMUM_OPERATING_TEMPERATURE_C,
        "thermal_noise_density_dbm_hz": worst_noise_density_dbm_hz,
        "noise_bandwidth_hz": NOISE_BANDWIDTH_HZ,
        "integrated_thermal_noise_dbm": noise_floor_dbm,
        "required_demodulator_snr_db": REQUIRED_DEMODULATOR_SNR_DB,
        "project_sensitivity_target_dbm": PROJECT_SENSITIVITY_TARGET_DBM,
        "bluetooth_sensitivity_limit_dbm": BLUETOOTH_SENSITIVITY_LIMIT_DBM,
        "maximum_input_level_dbm": MAXIMUM_INPUT_LEVEL_DBM,
        "required_input_dynamic_range_db": (
            MAXIMUM_INPUT_LEVEL_DBM - PROJECT_SENSITIVITY_TARGET_DBM
        ),
        "maximum_cascade_nf_for_project_target_db": maximum_nf_for_project_target_db,
        "stages": STAGES,
        "cascade_noise_figure_db": cascade_nf_db,
        "total_small_signal_gain_db": total_gain_db,
        "predicted_sensitivity_dbm": predicted_sensitivity_dbm,
        "project_target_margin_db": (
            PROJECT_SENSITIVITY_TARGET_DBM - predicted_sensitivity_dbm
        ),
        "bluetooth_limit_margin_db": (
            BLUETOOTH_SENSITIVITY_LIMIT_DBM - predicted_sensitivity_dbm
        ),
        "noise_budget_passed": cascade_nf_db <= maximum_nf_for_project_target_db,
        "open_gates": [
            "The 15 dB demodulator SNR allocation needs BER simulation with the implemented detector.",
            "Gain control is required to span the 70 dB input range without baseband overload.",
            "Blocker, image, linearity, oscillator phase-noise, and reciprocal-mixing budgets remain open.",
            "Active current, startup time, duty cycle, and complete-report energy remain open.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")
    if not report["noise_budget_passed"]:
        raise RuntimeError("receiver cascade misses the provisional sensitivity target")


if __name__ == "__main__":
    main()
