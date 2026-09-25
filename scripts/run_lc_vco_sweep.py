#!/usr/bin/env python3
"""Sweep a GF180 LC oscillator core with an assumed lumped inductor."""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "analog" / "gf180_lc_vco_tb.spice"
REPORT_JSON = ROOT / "reports" / "lc_vco_sweep.json"
REPORT_CSV = ROOT / "reports" / "lc_vco_sweep.csv"
MODEL_FILE = os.environ.get(
    "GF180_MODEL_FILE",
    "/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice",
)
DESIGN_FILE = os.environ.get(
    "GF180_DESIGN_FILE",
    "/foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice",
)
CAP_SIDES_UM = (24, 26, 28, 30, 32, 34)
TAIL_CURRENTS_UA = (500, 700, 1000)
CORNERS = (
    ("typical", "mimcap_typical", 25),
    ("ff", "mimcap_ff", -40),
    ("ss", "mimcap_ss", 125),
)
MEASUREMENT = re.compile(
    r"^(frequency_hz|differential_vpp|supply_current_a|power_w)"
    r"\s*=\s*([-+0-9.eE]+)",
    re.MULTILINE,
)


def run_point(
    template: str,
    corner: str,
    mim_corner: str,
    temperature_c: int,
    cap_side_um: int,
    tail_current_ua: int,
) -> dict:
    netlist = (
        template.replace("@@DESIGN_FILE@@", DESIGN_FILE)
        .replace("@@MODEL_FILE@@", MODEL_FILE)
        .replace("@@MIM_CORNER@@", mim_corner)
        .replace("@@CORNER@@", corner)
        .replace("@@TEMP_C@@", str(temperature_c))
        .replace("@@CAP_SIDE@@", f"{cap_side_um}u")
        .replace("@@TAIL_CURRENT@@", f"{tail_current_ua}u")
    )
    with tempfile.TemporaryDirectory(prefix="lc-vco-") as temporary_dir:
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
            f"ngspice failed for {corner}, {cap_side_um} um, "
            f"{tail_current_ua} uA\n{output[-4000:]}"
        )
    values["supply_current_a"] = -values["supply_current_a"]
    frequency_hz = values.get("frequency_hz")
    return {
        "corner": corner,
        "temperature_c": temperature_c,
        "cap_side_um": cap_side_um,
        "tail_current_ua": tail_current_ua,
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
            temperature_c,
            cap_side_um,
            tail_current_ua,
        )
        for corner, mim_corner, temperature_c in CORNERS
        for cap_side_um in CAP_SIDES_UM
        for tail_current_ua in TAIL_CURRENTS_UA
    ]
    band_low_hz = 2_402_000_000
    band_high_hz = 2_480_000_000
    corner_summaries = []
    for corner, _, temperature_c in CORNERS:
        corner_points = [
            point
            for point in points
            if point["corner"] == corner
            and point["tail_current_ua"] == max(TAIL_CURRENTS_UA)
            and point["sustained_oscillation"]
        ]
        frequencies = [point["frequency_hz"] for point in corner_points]
        corner_summaries.append(
            {
                "corner": corner,
                "temperature_c": temperature_c,
                "tail_current_ua": max(TAIL_CURRENTS_UA),
                "minimum_sustained_frequency_hz": min(frequencies),
                "maximum_sustained_frequency_hz": max(frequencies),
                "sampled_envelope_brackets_ble_band": min(frequencies)
                <= band_low_hz
                and max(frequencies) >= band_high_hz,
            }
        )
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "circuit": "gf180_cross_coupled_nmos_lc_oscillator",
                "purpose": "active-core-and-tank-assumption-feasibility-only",
                "vdd_v": 1.8,
                "nmos_w_parameter_um": 40.0,
                "nmos_length_um": 0.28,
                "nmos_fingers": 10,
                "tail_current_sweep_a": [value * 1e-6 for value in TAIL_CURRENTS_UA],
                "tank_inductance_h_per_branch": 3e-9,
                "tank_series_resistance_ohm_per_branch": 4.6,
                "assumed_inductor_q_at_2p44_ghz": 10.0,
                "ble_band_hz": {"low": band_low_hz, "high": band_high_hz},
                "corner_summary_at_1ma": corner_summaries,
                "points": points,
            },
            indent=2,
        )
        + "\n"
    )
    with REPORT_CSV.open("w", newline="") as output:
        writer = csv.DictWriter(
            output, fieldnames=points[0].keys(), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(points)
    print(REPORT_JSON.read_text(), end="")


if __name__ == "__main__":
    main()
