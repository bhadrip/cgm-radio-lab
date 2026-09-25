#!/usr/bin/env python3
"""Bound 6+1 fast-DAC unit-current matching with a seeded sensitivity sweep."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PVT_REPORT = ROOT / "reports" / "gf180_fast_dac_steered_pvt.json"
REPORT = ROOT / "reports" / "gf180_fast_dac_mismatch.json"
TRIALS = 50_000
SEED = 0xC6D0
TARGET_YIELD = 0.999
YIELD_CONFIDENCE = 0.95
ONE_SIDED_95_PERCENT_Z = 1.6448536269514722
LINEARITY_LIMIT_LSB = 0.5
UNIT_SIGMA_CANDIDATES = (0.0100, 0.0150, 0.0200, 0.0225, 0.0250)


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    return ordered[math.ceil(probability * len(ordered)) - 1]


def wilson_lower_bound(passing: int, total: int) -> float:
    probability = passing / total
    z = ONE_SIDED_95_PERCENT_Z
    denominator = 1.0 + z * z / total
    center = probability + z * z / (2.0 * total)
    radius = z * math.sqrt(
        probability * (1.0 - probability) / total
        + z * z / (4.0 * total * total)
    )
    return (center - radius) / denominator


def normalized_transfers(pvt: dict) -> list[dict]:
    transfers = []
    for summary in pvt["summaries"]:
        voltages = summary["code_voltages_v"]
        endpoint_lsb_v = (voltages[-1] - voltages[0]) / (len(voltages) - 1)
        transfers.append(
            {
                "corner": summary["corner"],
                "temperature_c": summary["temperature_c"],
                "codes_lsb": [
                    (voltage - voltages[0]) / endpoint_lsb_v
                    for voltage in voltages
                ],
            }
        )
    return transfers


def mismatch_error_lsb(rng: random.Random, unit_sigma: float) -> list[float]:
    # A weight-two thermometer source uses twice the active area, so its
    # relative sigma is scaled by 1/sqrt(2). Its absolute error is expressed in
    # nominal unit-current (one-LSB) units here.
    thermometer_errors = [
        2.0 * rng.gauss(0.0, unit_sigma / math.sqrt(2.0))
        for _ in range(63)
    ]
    binary_error = rng.gauss(0.0, unit_sigma)
    errors = [0.0]
    thermometer_sum = 0.0
    for code in range(1, 128):
        if code & 1:
            error = thermometer_sum + binary_error
        else:
            thermometer_sum += thermometer_errors[(code >> 1) - 1]
            error = thermometer_sum
        errors.append(error)
    return errors


def linearity(codes_lsb: list[float], errors_lsb: list[float]) -> tuple[float, float]:
    values = [base + error for base, error in zip(codes_lsb, errors_lsb)]
    fitted_lsb = (values[-1] - values[0]) / 127.0
    maximum_inl = max(
        abs((value - values[0]) / fitted_lsb - code)
        for code, value in enumerate(values)
    )
    maximum_dnl = max(
        abs((values[code] - values[code - 1]) / fitted_lsb - 1.0)
        for code in range(1, 128)
    )
    return maximum_inl, maximum_dnl


def sweep_candidate(transfers: list[dict], unit_sigma: float) -> dict:
    rng = random.Random(SEED + round(unit_sigma * 1_000_000))
    worst_inl_values = []
    worst_dnl_values = []
    passing_trials = 0
    for _ in range(TRIALS):
        errors_lsb = mismatch_error_lsb(rng, unit_sigma)
        corner_results = [
            linearity(transfer["codes_lsb"], errors_lsb)
            for transfer in transfers
        ]
        worst_inl = max(result[0] for result in corner_results)
        worst_dnl = max(result[1] for result in corner_results)
        worst_inl_values.append(worst_inl)
        worst_dnl_values.append(worst_dnl)
        passing_trials += (
            worst_inl <= LINEARITY_LIMIT_LSB
            and worst_dnl <= LINEARITY_LIMIT_LSB
        )
    observed_yield = passing_trials / TRIALS
    yield_lower_bound = wilson_lower_bound(passing_trials, TRIALS)
    return {
        "unit_current_sigma_fraction": unit_sigma,
        "passing_trials": passing_trials,
        "observed_yield": observed_yield,
        "yield_one_sided_95_percent_lower_bound": yield_lower_bound,
        "meets_yield_target": yield_lower_bound >= TARGET_YIELD,
        "p99_maximum_absolute_inl_lsb": percentile(worst_inl_values, 0.99),
        "p999_maximum_absolute_inl_lsb": percentile(worst_inl_values, 0.999),
        "p99_maximum_absolute_dnl_lsb": percentile(worst_dnl_values, 0.99),
        "p999_maximum_absolute_dnl_lsb": percentile(worst_dnl_values, 0.999),
    }


def main() -> None:
    pvt = json.loads(PVT_REPORT.read_text())
    transfers = normalized_transfers(pvt)
    summaries = [sweep_candidate(transfers, sigma) for sigma in UNIT_SIGMA_CANDIDATES]
    passing = [summary for summary in summaries if summary["meets_yield_target"]]
    selected = max(passing, key=lambda summary: summary["unit_current_sigma_fraction"])
    first_failing = next(
        (
            summary
            for summary in summaries
            if summary["unit_current_sigma_fraction"]
            > selected["unit_current_sigma_fraction"]
        ),
        None,
    )
    report = {
        "schema_version": 1,
        "purpose": "seeded mismatch sensitivity for the 6+1 current-steered fast DAC",
        "method": "behavioral unit-current perturbation over measured PVT transfers",
        "trial_count_per_candidate": TRIALS,
        "random_seed_base": SEED,
        "corner_count": len(transfers),
        "yield_target": TARGET_YIELD,
        "yield_confidence_level": YIELD_CONFIDENCE,
        "inl_limit_lsb": LINEARITY_LIMIT_LSB,
        "dnl_limit_lsb": LINEARITY_LIMIT_LSB,
        "selected_maximum_unit_current_sigma_fraction": selected[
            "unit_current_sigma_fraction"
        ],
        "selected_observed_yield": selected["observed_yield"],
        "selected_yield_one_sided_95_percent_lower_bound": selected[
            "yield_one_sided_95_percent_lower_bound"
        ],
        "first_failing_unit_current_sigma_fraction": (
            first_failing["unit_current_sigma_fraction"] if first_failing else None
        ),
        "passed": bool(passing) and first_failing is not None,
        "summaries": summaries,
        "limitations": [
            "Gaussian independent current errors are assumed; no foundry mismatch parameters are available.",
            "The same relative mismatch realization is applied at every sampled PVT point.",
            "Endpoint gain is removed, matching the calibrated INL definition.",
            "This sensitivity sweep is not device Monte Carlo or production yield signoff.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")
    if not report["passed"]:
        raise RuntimeError("mismatch sweep did not bracket the yield boundary")


if __name__ == "__main__":
    main()
