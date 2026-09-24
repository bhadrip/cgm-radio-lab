#!/usr/bin/env python3
"""Screen the GF180 PA against a small set of real load impedances."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.run_gf180_pa import (
    CORNERS,
    MAXIMUM_LEVEL_ERROR_DB,
    UNIT_NMOS_WIDTH_UM,
    simulate,
)


ROOT = Path(__file__).resolve().parents[1]
PA_REPORT = ROOT / "reports" / "gf180_pa.json"
REPORT = ROOT / "reports" / "gf180_pa_load_sweep.json"
LOADS_OHM = (25.0, 35.0, 50.0, 75.0, 100.0, 150.0, 200.0)
TARGET_POWER_DBM = 0.0


def maximum_power_code_by_corner() -> dict[str, int]:
    pa_report = json.loads(PA_REPORT.read_text())
    return {
        point["corner"]: point["selected_power_code"]
        for point in pa_report["calibration"]
        if point["target_output_power_dbm"] == TARGET_POWER_DBM
    }


def main() -> None:
    codes = maximum_power_code_by_corner()
    summaries = []
    for corner, temperature_c in CORNERS:
        code = codes[corner]
        points = [
            simulate(
                code * UNIT_NMOS_WIDTH_UM,
                corner,
                temperature_c,
                load_ohm,
            )
            for load_ohm in LOADS_OHM
        ]
        baseline = next(point for point in points if point["load_ohm"] == 50.0)
        maximum_power = max(
            points, key=lambda point: point["fundamental_output_power_dbm"]
        )
        maximum_efficiency = max(
            points, key=lambda point: point["drain_efficiency"]
        )
        summaries.append(
            {
                "corner": corner,
                "temperature_c": temperature_c,
                "power_code": code,
                "baseline_50_ohm_output_power_dbm": baseline[
                    "fundamental_output_power_dbm"
                ],
                "baseline_50_ohm_drain_efficiency": baseline[
                    "drain_efficiency"
                ],
                "maximum_power_load_ohm": maximum_power["load_ohm"],
                "maximum_output_power_dbm": maximum_power[
                    "fundamental_output_power_dbm"
                ],
                "maximum_efficiency_load_ohm": maximum_efficiency["load_ohm"],
                "maximum_drain_efficiency": maximum_efficiency[
                    "drain_efficiency"
                ],
                "points": [
                    {
                        "load_ohm": point["load_ohm"],
                        "fundamental_output_power_dbm": point[
                            "fundamental_output_power_dbm"
                        ],
                        "supply_power_w": point["supply_power_w"],
                        "drain_efficiency": point["drain_efficiency"],
                        "second_harmonic_dbc": point["second_harmonic_dbc"],
                        "third_harmonic_dbc": point["third_harmonic_dbc"],
                    }
                    for point in points
                ],
            }
        )
    report = {
        "schema_version": 1,
        "purpose": "real-load sensitivity at calibrated maximum PA power",
        "target_output_power_dbm": TARGET_POWER_DBM,
        "loads_ohm": LOADS_OHM,
        "passed": all(
            abs(summary["baseline_50_ohm_output_power_dbm"] - TARGET_POWER_DBM)
            <= MAXIMUM_LEVEL_ERROR_DB
            for summary in summaries
        ),
        "summaries": summaries,
        "limitations": [
            "Only real load impedances are tested; this is not complex load-pull.",
            "The input drive, coupling capacitor, and load are ideal.",
            "No package, matching network, antenna, or routed bank is included.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")
    if not report["passed"]:
        raise RuntimeError("50 ohm calibrated PA baselines moved outside tolerance")


if __name__ == "__main__":
    main()
