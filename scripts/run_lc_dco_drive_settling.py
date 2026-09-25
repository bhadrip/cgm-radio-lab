#!/usr/bin/env python3
"""Sweep DAC output resistance against a conservative LC-DCO control load."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from scripts.run_lc_dco_dynamic import run_dynamic


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "lc_dco_drive_settling.json"
CANDIDATES = (
    (100, 5e-12),
    (100, 10e-12),
    (1_000, 5e-12),
    (1_000, 10e-12),
    (2_500, 10e-12),
    (5_000, 10e-12),
    (1_000, 20e-12),
)
RECOMMENDED_RESISTANCE_OHM = 1_000
RECOMMENDED_LOAD_F = 10e-12
CARRIER_PULL_LIMIT_HZ = 30_000
TRACKING_ERROR_LIMIT_HZ = 30_000


def summarize(report: dict) -> dict:
    errors_hz = [sample["error_hz"] for sample in report["samples"]]
    carrier_pull_hz = sum(errors_hz) / len(errors_hz)
    tracking_error_hz = max(abs(error - carrier_pull_hz) for error in errors_hz)
    summary = {
        key: report[key]
        for key in (
            "drive_resistance_ohm",
            "control_load_f",
            "drive_time_constant_s",
            "drive_bandwidth_hz",
            "mean_frequency_error_hz",
            "maximum_absolute_frequency_error_hz",
            "modeled_modulation_code_step_hz",
        )
    }
    summary.update(
        {
            "carrier_pull_hz": carrier_pull_hz,
            "maximum_mean_removed_tracking_error_hz": tracking_error_hz,
            "meets_pull_limit": abs(carrier_pull_hz) <= CARRIER_PULL_LIMIT_HZ,
            "meets_tracking_limit": tracking_error_hz <= TRACKING_ERROR_LIMIT_HZ,
        }
    )
    summary["passed"] = summary["meets_pull_limit"] and summary["meets_tracking_limit"]
    return summary


def main() -> None:
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(
                lambda candidate: run_dynamic(*candidate, 0),
                CANDIDATES,
            )
        )
    summaries = [summarize(result) for result in results]
    recommended_untrimmed = next(
        report
        for report in results
        if report["drive_resistance_ohm"] == RECOMMENDED_RESISTANCE_OHM
        and report["control_load_f"] == RECOMMENDED_LOAD_F
    )
    trim_codes = round(
        -recommended_untrimmed["mean_frequency_error_hz"]
        / recommended_untrimmed["modeled_modulation_code_step_hz"]
    )
    calibrated = run_dynamic(
        RECOMMENDED_RESISTANCE_OHM, RECOMMENDED_LOAD_F, trim_codes
    )
    report = {
        "schema_version": 1,
        "carrier_pull_limit_hz": CARRIER_PULL_LIMIT_HZ,
        "tracking_error_limit_hz": TRACKING_ERROR_LIMIT_HZ,
        "recommended_maximum_output_resistance_ohm": RECOMMENDED_RESISTANCE_OHM,
        "recommended_bypass_capacitance_f": RECOMMENDED_LOAD_F,
        "recommended_trim_codes": trim_codes,
        "calibrated_result": summarize(calibrated),
        "passed": calibrated["passed"],
        "summaries": summaries,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")
    if not report["passed"]:
        raise RuntimeError("DAC drive does not meet the reviewed settling target")


if __name__ == "__main__":
    main()
