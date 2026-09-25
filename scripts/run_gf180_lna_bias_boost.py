#!/usr/bin/env python3
"""Select a temporary LNA bias-boost state for strong BLE inputs."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.run_gf180_lna import (
    CORNERS,
    TARGET_DRAIN_V,
    VDD_V,
    simulate as simulate_ac,
)
from scripts.run_gf180_lna_linearity import simulate as simulate_two_tone


ROOT = Path(__file__).resolve().parents[1]
LNA_REPORT = ROOT / "reports" / "gf180_lna.json"
REPORT = ROOT / "reports" / "gf180_lna_bias_boost.json"
BIAS_CURRENT_CANDIDATES_A = (1.4e-3,) + tuple(
    value * 1e-3 for value in range(2, 9)
)
LOW_INPUT_POWER_PER_TONE_DBM = -30.0
STRONG_INPUT_POWER_PER_TONE_DBM = -10.0
MAXIMUM_GAIN_COMPRESSION_DB = 1.0
MINIMUM_STRONG_SIGNAL_GAIN_DB = 10.0
MAXIMUM_NOISE_FIGURE_DB = 4.0
MINIMUM_INPUT_RETURN_LOSS_DB = 10.0
MINIMUM_DRAIN_SOURCE_V = 0.5
REFERENCE_ACTIVE_DURATION_S = 224e-6


def main() -> None:
    nominal = json.loads(LNA_REPORT.read_text())["selected"]
    candidates = []
    for bias_current_a in BIAS_CURRENT_CANDIDATES_A:
        configuration = {
            "nmos_width_um": nominal["nmos_width_um"],
            "bias_current_a": bias_current_a,
            "load_resistance_ohm": (VDD_V - TARGET_DRAIN_V) / bias_current_a,
        }
        points = []
        for corner, temperature_c in CORNERS:
            ac = simulate_ac(configuration, corner, temperature_c)
            low = simulate_two_tone(
                configuration,
                corner,
                temperature_c,
                LOW_INPUT_POWER_PER_TONE_DBM,
            )
            strong = simulate_two_tone(
                configuration,
                corner,
                temperature_c,
                STRONG_INPUT_POWER_PER_TONE_DBM,
            )
            points.append(
                {
                    "corner": corner,
                    "temperature_c": temperature_c,
                    "supply_power_w": ac["supply_power_w"],
                    "noise_figure_db": ac["noise_figure_db"],
                    "input_return_loss_db": ac["input_return_loss_db"],
                    "drain_source_voltage_v": ac["drain_source_voltage_v"],
                    "low_input_gain_db": low["intrinsic_voltage_gain_db"],
                    "strong_input_gain_db": strong["intrinsic_voltage_gain_db"],
                    "gain_compression_db": low["intrinsic_voltage_gain_db"]
                    - strong["intrinsic_voltage_gain_db"],
                    "strong_input_fundamental_to_im3_db": strong[
                        "fundamental_to_im3_db"
                    ],
                }
            )
        summary = {
            **configuration,
            "maximum_supply_power_w": max(point["supply_power_w"] for point in points),
            "reference_active_energy_j": max(
                point["supply_power_w"] for point in points
            )
            * REFERENCE_ACTIVE_DURATION_S,
            "maximum_gain_compression_db": max(
                point["gain_compression_db"] for point in points
            ),
            "minimum_strong_input_gain_db": min(
                point["strong_input_gain_db"] for point in points
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
            "points": points,
        }
        summary["passed"] = (
            summary["maximum_gain_compression_db"] <= MAXIMUM_GAIN_COMPRESSION_DB
            and summary["minimum_strong_input_gain_db"]
            >= MINIMUM_STRONG_SIGNAL_GAIN_DB
            and summary["maximum_noise_figure_db"] <= MAXIMUM_NOISE_FIGURE_DB
            and summary["minimum_input_return_loss_db"]
            >= MINIMUM_INPUT_RETURN_LOSS_DB
            and summary["minimum_drain_source_voltage_v"]
            >= MINIMUM_DRAIN_SOURCE_V
        )
        candidates.append(summary)

    passing = [candidate for candidate in candidates if candidate["passed"]]
    if not passing:
        raise RuntimeError("no sampled LNA bias-boost candidate passes")
    selected = min(passing, key=lambda candidate: candidate["bias_current_a"])
    report = {
        "schema_version": 1,
        "purpose": "strong-input LNA bias-boost selection",
        "low_input_power_per_tone_dbm": LOW_INPUT_POWER_PER_TONE_DBM,
        "strong_input_power_per_tone_dbm": STRONG_INPUT_POWER_PER_TONE_DBM,
        "reference_active_duration_s": REFERENCE_ACTIVE_DURATION_S,
        "gates": {
            "maximum_gain_compression_db": MAXIMUM_GAIN_COMPRESSION_DB,
            "minimum_strong_input_gain_db": MINIMUM_STRONG_SIGNAL_GAIN_DB,
            "maximum_noise_figure_db": MAXIMUM_NOISE_FIGURE_DB,
            "minimum_input_return_loss_db": MINIMUM_INPUT_RETURN_LOSS_DB,
            "minimum_drain_source_voltage_v": MINIMUM_DRAIN_SOURCE_V,
        },
        "selected": selected,
        "candidate_count": len(candidates),
        "passing_candidate_count": len(passing),
        "accepted_for_next_stage": selected["passed"],
        "candidates": candidates,
        "limitations": [
            "The -10 dBm per-tone stress is not the PR11 single-tone maximum-input test.",
            "Bias switching, settling, control logic, reference generation, and transition energy are not modeled.",
            "The same ideal-bias, provisional-load, package, matching, mismatch, layout, and measurement limits remain.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")


if __name__ == "__main__":
    main()
