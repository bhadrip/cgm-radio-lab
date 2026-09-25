#!/usr/bin/env python3
"""Translate the LC sweep into a coarse/fine tuning-bank requirement."""

from __future__ import annotations

import json
import math
from pathlib import Path

from model.lc_dco import (
    MIM_CORNER_SCALE,
    MOSCAP_CORNER_SCALE,
    MIM_MIN_SIDE_UM,
    MOSCAP_MIN_SIDE_UM,
    NMOSCAP_CVAR3,
    NMOSCAP_CVAR4,
    estimate_tuning,
    mim_capacitance_ff,
    nmoscap_capacitance_ff,
    nmoscap_slope_ff_per_v,
)


ROOT = Path(__file__).resolve().parents[1]
SWEEP = ROOT / "reports" / "lc_vco_sweep.json"
REPORT = ROOT / "reports" / "lc_dco_bank.json"
CORNERS = ("typical", "ff", "ss")
TARGETS_HZ = (2_480_000_000, 2_441_000_000, 2_402_000_000)
VARACTOR_COUNT = 16


def main() -> None:
    points = json.loads(SWEEP.read_text())["points"]
    estimates = [
        estimate_tuning(points, corner, target)
        for corner in CORNERS
        for target in TARGETS_HZ
    ]
    nominal_sides = [estimate.interpolated_side_um for estimate in estimates]
    geometry_span_ff = mim_capacitance_ff(max(nominal_sides)) - mim_capacitance_ff(
        min(nominal_sides)
    )
    minimum_mim_by_corner = {
        corner: mim_capacitance_ff(MIM_MIN_SIDE_UM, corner) for corner in CORNERS
    }
    minimum_mim_nominal_ff = minimum_mim_by_corner["typical"]
    coarse_intervals = math.ceil(geometry_span_ff / minimum_mim_nominal_ff)
    varactor_transition_v = -NMOSCAP_CVAR4 / NMOSCAP_CVAR3
    center_estimates = {
        estimate.corner: estimate
        for estimate in estimates
        if estimate.target_frequency_hz == 2_441_000_000
    }
    fine_by_corner = {}
    for corner in CORNERS:
        minimum_cap = nmoscap_capacitance_ff(0.0, VARACTOR_COUNT, corner)
        maximum_cap = nmoscap_capacitance_ff(1.8, VARACTOR_COUNT, corner)
        slope = nmoscap_slope_ff_per_v(
            varactor_transition_v, VARACTOR_COUNT, corner
        )
        local_gain = center_estimates[corner].local_gain_hz_per_ff
        fine_by_corner[corner] = {
            "minimum_capacitance_ff_at_0v": minimum_cap,
            "maximum_capacitance_ff_at_1p8v": maximum_cap,
            "tuning_span_ff": maximum_cap - minimum_cap,
            "minimum_mim_unit_ff": minimum_mim_by_corner[corner],
            "overlaps_one_coarse_step": maximum_cap - minimum_cap
            >= minimum_mim_by_corner[corner],
            "mid_slope_capacitance_ff_per_v": slope,
            "estimated_frequency_gain_hz_per_v": slope * local_gain,
            "control_step_v_for_50khz": 50_000.0 / (slope * local_gain),
        }
    report = {
        "schema_version": 1,
        "source": str(SWEEP.relative_to(ROOT)),
        "target_frequency_hz": 2_441_000_000,
        "frequency_code_step_hz": 50_000,
        "pdk_minimum_mim_side_um": MIM_MIN_SIDE_UM,
        "pdk_minimum_moscap_side_um": MOSCAP_MIN_SIDE_UM,
        "mim_corner_scale": MIM_CORNER_SCALE,
        "moscap_corner_scale": MOSCAP_CORNER_SCALE,
        "interpolated_tuning": [estimate.__dict__ for estimate in estimates],
        "nominal_geometry_capacitance_span_ff": geometry_span_ff,
        "minimum_mim_unit_ff": minimum_mim_nominal_ff,
        "minimum_coarse_intervals": coarse_intervals,
        "recommended_coarse_codes": 16,
        "recommended_coarse_bits": 4,
        "recommended_minimum_mos_varactors": VARACTOR_COUNT,
        "nmoscap_transition_voltage_v": varactor_transition_v,
        "fine_tuning": fine_by_corner,
        "decision": (
            "replace the single linear DCO code with a calibrated 4-bit coarse "
            "MIM bank plus analog MOS-varactor fine control"
        ),
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")


if __name__ == "__main__":
    main()
