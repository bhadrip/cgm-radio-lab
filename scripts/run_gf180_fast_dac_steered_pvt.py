#!/usr/bin/env python3
"""Sweep the 6+1 current-steered GF180 fast DAC across sampled PVT."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.run_gf180_fast_dac_steered import characterize


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "gf180_fast_dac_steered_pvt.json"
TYPICAL_REPORT = ROOT / "reports" / "gf180_fast_dac_steered.json"
CORNERS = (("ff", -40), ("ss", 125))


def main() -> None:
    typical = json.loads(TYPICAL_REPORT.read_text())
    typical.pop("codes")
    summaries = [typical]
    for corner, temperature_c in CORNERS:
        result = characterize(corner, temperature_c)
        result.pop("codes")
        summaries.append(result)
    passed = all(summary["accepted_for_next_stage"] for summary in summaries)
    report = {
        "schema_version": 1,
        "purpose": "sampled PVT gate for the 6+1 current-steered fast DAC",
        "corner_count": len(summaries),
        "passed": passed,
        "worst_absolute_inl_lsb": max(
            summary["maximum_absolute_inl_lsb"] for summary in summaries
        ),
        "worst_absolute_dnl_lsb": max(
            max(abs(summary["minimum_dnl_lsb"]), abs(summary["maximum_dnl_lsb"]))
            for summary in summaries
        ),
        "worst_glitch_v": max(
            summary["transition"]["glitch_below_endpoints_v"]
            for summary in summaries
        ),
        "worst_combined_frequency_error_hz": max(
            summary["transition"]["combined_frequency_error_hz"]
            for summary in summaries
        ),
        "maximum_static_power_w": max(
            summary["maximum_static_power_w"] for summary in summaries
        ),
        "summaries": summaries,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")
    if not report["passed"]:
        raise RuntimeError("current-steered fast DAC failed sampled PVT")


if __name__ == "__main__":
    main()
