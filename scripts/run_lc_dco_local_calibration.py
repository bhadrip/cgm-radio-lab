#!/usr/bin/env python3
"""Refine LC-DCO tuning curves around every advertising-channel bias point."""

from __future__ import annotations

import csv
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from model.dco import ble_channel_center_hz
from model.lc_dco_modulation import calibrate_channel
from scripts.run_lc_dco_sweep import TEMPLATE, run_point


ROOT = Path(__file__).resolve().parents[1]
STATIC_SWEEP = ROOT / "reports" / "lc_dco_sweep.json"
REPORT_JSON = ROOT / "reports" / "lc_dco_local_calibration.json"
REPORT_CSV = ROOT / "reports" / "lc_dco_local_calibration.csv"
CHANNELS = (37, 38, 39)
CORNERS = {
    "typical": ("mimcap_typical", "moscap_typical", 25),
    "ff": ("mimcap_ff", "moscap_ff", -40),
    "ss": ("mimcap_ss", "moscap_ss", 125),
}
TARGET_OFFSETS_HZ = (-250_000, 0, 250_000)
REFINEMENT_STEPS = 5
CALIBRATION_ERROR_LIMIT_HZ = 50_000


def solve_target(
    template: str,
    static_points: list[dict],
    corner: str,
    mim_corner: str,
    moscap_corner: str,
    temperature_c: int,
    channel: int,
    coarse_code: int,
    target_frequency_hz: int,
) -> list[dict]:
    curve = sorted(
        (
            point
            for point in static_points
            if point["corner"] == corner
            and point["coarse_code"] == coarse_code
            and point["sustained_oscillation"]
        ),
        key=lambda point: float(point["control_voltage_v"]),
    )
    brackets = [
        (low, high)
        for low, high in zip(curve, curve[1:])
        if float(low["frequency_hz"])
        <= target_frequency_hz
        <= float(high["frequency_hz"])
    ]
    if not brackets:
        raise ValueError(
            f"no voltage bracket for {corner} channel {channel} "
            f"at {target_frequency_hz} Hz"
        )
    low, high = brackets[0]
    solved = []
    for _ in range(REFINEMENT_STEPS):
        low_v = float(low["control_voltage_v"])
        high_v = float(high["control_voltage_v"])
        low_f = float(low["frequency_hz"])
        high_f = float(high["frequency_hz"])
        guess_v = low_v + (target_frequency_hz - low_f) * (high_v - low_v) / (
            high_f - low_f
        )
        point = run_point(
            template,
            corner,
            mim_corner,
            moscap_corner,
            temperature_c,
            coarse_code,
            guess_v,
        )
        point["channel"] = channel
        point["target_frequency_hz"] = target_frequency_hz
        point["calibration_error_hz"] = point["frequency_hz"] - target_frequency_hz
        solved.append(point)
        if point["frequency_hz"] < target_frequency_hz:
            low = point
        else:
            high = point
    return solved


def main() -> None:
    static_points = json.loads(STATIC_SWEEP.read_text())["points"]
    template = TEMPLATE.read_text()
    tasks = []
    for corner, (mim_corner, moscap_corner, temperature_c) in CORNERS.items():
        for channel in CHANNELS:
            calibration = calibrate_channel(static_points, corner, channel)
            for offset_hz in TARGET_OFFSETS_HZ:
                tasks.append(
                    (
                        template,
                        static_points,
                        corner,
                        mim_corner,
                        moscap_corner,
                        temperature_c,
                        channel,
                        calibration.coarse_code,
                        ble_channel_center_hz(channel) + offset_hz,
                    )
                )
    jobs = int(os.environ.get("LC_DCO_JOBS", "2"))
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        solved_groups = list(
            executor.map(lambda arguments: solve_target(*arguments), tasks)
        )
        points = [point for group in solved_groups for point in group]
    maximum_final_error_hz = max(
        abs(group[-1]["calibration_error_hz"]) for group in solved_groups
    )
    report = {
        "schema_version": 1,
        "source": str(STATIC_SWEEP.relative_to(ROOT)),
        "target_offsets_hz": list(TARGET_OFFSETS_HZ),
        "refinement_steps": REFINEMENT_STEPS,
        "calibration_error_limit_hz": CALIBRATION_ERROR_LIMIT_HZ,
        "maximum_final_calibration_error_hz": maximum_final_error_hz,
        "passed": maximum_final_error_hz <= CALIBRATION_ERROR_LIMIT_HZ,
        "points": points,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n")
    with REPORT_CSV.open("w", newline="") as output:
        writer = csv.DictWriter(
            output, fieldnames=points[0].keys(), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(points)
    print(REPORT_JSON.read_text(), end="")
    if not report["passed"]:
        raise RuntimeError(
            f"local calibration error {maximum_final_error_hz} Hz exceeds "
            f"{CALIBRATION_ERROR_LIMIT_HZ} Hz"
        )


if __name__ == "__main__":
    main()
