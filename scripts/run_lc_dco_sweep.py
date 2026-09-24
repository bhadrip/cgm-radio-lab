#!/usr/bin/env python3
"""Validate a legal-size coarse/fine GF180 LC-DCO tuning network."""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "analog" / "gf180_lc_dco_tb.spice"
REPORT_JSON = ROOT / "reports" / "lc_dco_sweep.json"
REPORT_CSV = ROOT / "reports" / "lc_dco_sweep.csv"
MODEL_FILE = os.environ.get(
    "GF180_MODEL_FILE",
    "/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice",
)
DESIGN_FILE = os.environ.get(
    "GF180_DESIGN_FILE",
    "/foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice",
)
CORNERS = (
    ("typical", "mimcap_typical", "moscap_typical", 25, (4, 5, 6, 7)),
    ("ff", "mimcap_ff", "moscap_ff", -40, (10, 11, 12, 13)),
    ("ss", "mimcap_ss", "moscap_ss", 125, (0, 1, 2, 3)),
)
CONTROL_VOLTAGES = (0.0, 0.3, 0.5, 0.63, 0.75, 1.0, 1.8)
MEASUREMENT = re.compile(
    r"^(frequency_hz|differential_vpp|supply_current_a|power_w)"
    r"\s*=\s*([-+0-9.eE]+)",
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
    return "\n".join(lines) or "* no coarse cells selected"


def run_point(
    template: str,
    corner: str,
    mim_corner: str,
    moscap_corner: str,
    temperature_c: int,
    coarse_code: int,
    control_voltage_v: float,
) -> dict:
    netlist = (
        template.replace("@@DESIGN_FILE@@", DESIGN_FILE)
        .replace("@@MODEL_FILE@@", MODEL_FILE)
        .replace("@@MIM_CORNER@@", mim_corner)
        .replace("@@MOSCAP_CORNER@@", moscap_corner)
        .replace("@@CORNER@@", corner)
        .replace("@@TEMP_C@@", str(temperature_c))
        .replace("@@VCTRL@@", str(control_voltage_v))
        .replace("@@COARSE_CAPS@@", coarse_instances(coarse_code))
    )
    with tempfile.TemporaryDirectory(prefix="lc-dco-") as temporary_dir:
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
    values = {name: float(value) for name, value in MEASUREMENT.findall(output)}
    required = {"supply_current_a", "power_w", "differential_vpp"}
    if result.returncode or not required.issubset(values):
        raise RuntimeError(
            f"ngspice failed for {corner}, code {coarse_code}, "
            f"VCTRL={control_voltage_v}\n{output[-4000:]}"
        )
    values["supply_current_a"] = -values["supply_current_a"]
    frequency_hz = values.get("frequency_hz")
    return {
        "corner": corner,
        "temperature_c": temperature_c,
        "coarse_code": coarse_code,
        "control_voltage_v": control_voltage_v,
        "frequency_hz": frequency_hz,
        "differential_vpp": values["differential_vpp"],
        "supply_current_a": values["supply_current_a"],
        "power_w": values["power_w"],
        "sustained_oscillation": frequency_hz is not None
        and values["differential_vpp"] >= 0.1,
    }


def main() -> None:
    template = TEMPLATE.read_text()
    points = [
        run_point(
            template,
            corner,
            mim_corner,
            moscap_corner,
            temperature_c,
            coarse_code,
            control_voltage_v,
        )
        for corner, mim_corner, moscap_corner, temperature_c, coarse_codes in CORNERS
        for coarse_code in coarse_codes
        for control_voltage_v in CONTROL_VOLTAGES
    ]
    band_low_hz = 2_402_000_000
    band_high_hz = 2_480_000_000
    summaries = []
    for corner, _, _, temperature_c, coarse_codes in CORNERS:
        corner_points = [
            point
            for point in points
            if point["corner"] == corner and point["sustained_oscillation"]
        ]
        frequencies = [point["frequency_hz"] for point in corner_points]
        coarse_ranges = []
        for coarse_code in coarse_codes:
            code_frequencies = [
                point["frequency_hz"]
                for point in corner_points
                if point["coarse_code"] == coarse_code
            ]
            coarse_ranges.append(
                {
                    "coarse_code": coarse_code,
                    "minimum_frequency_hz": min(code_frequencies),
                    "maximum_frequency_hz": max(code_frequencies),
                }
            )
        adjacent_overlaps = [
            lower_code["maximum_frequency_hz"]
            - upper_code["minimum_frequency_hz"]
            for upper_code, lower_code in zip(coarse_ranges, coarse_ranges[1:])
        ]
        summaries.append(
            {
                "corner": corner,
                "temperature_c": temperature_c,
                "coarse_codes_tested": list(coarse_codes),
                "minimum_frequency_hz": min(frequencies),
                "maximum_frequency_hz": max(frequencies),
                "sampled_points_in_ble_band": sum(
                    band_low_hz <= frequency <= band_high_hz
                    for frequency in frequencies
                ),
                "sampled_envelope_brackets_ble_band": min(frequencies)
                <= band_low_hz
                and max(frequencies) >= band_high_hz,
                "coarse_code_ranges": coarse_ranges,
                "minimum_adjacent_overlap_hz": min(adjacent_overlaps),
            }
        )
    report = {
        "schema_version": 1,
        "circuit": "gf180_coarse_fine_lc_dco",
        "purpose": "tuning-network-feasibility-only",
        "vdd_v": 1.8,
        "tail_current_a": 0.001,
        "base_mim_side_um": 26,
        "coarse_mim_unit_side_um": 5,
        "nmos_varactor_count": 16,
        "nmos_varactor_unit_side_um": 1,
        "tank_inductance_h_per_branch": 3e-9,
        "assumed_inductor_q_at_2p44_ghz": 10.0,
        "ble_band_hz": {"low": band_low_hz, "high": band_high_hz},
        "corner_summary": summaries,
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


if __name__ == "__main__":
    main()
