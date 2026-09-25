#!/usr/bin/env python3
"""Run a small GF180 ring-oscillator PVT/load feasibility sweep."""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "analog" / "gf180_ring_dco_tb.spice"
REPORT_JSON = ROOT / "reports" / "ring_dco_sweep.json"
REPORT_CSV = ROOT / "reports" / "ring_dco_sweep.csv"
MODEL_FILE = os.environ.get(
    "GF180_MODEL_FILE",
    "/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice",
)
DESIGN_FILE = os.environ.get(
    "GF180_DESIGN_FILE",
    "/foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice",
)
LOADS_FF = (0, 1, 2, 5, 10, 20, 40, 80)
CORNERS = (("typical", 25), ("ff", -40), ("ss", 125))
MEASUREMENT = re.compile(
    r"^(frequency_hz|supply_current_a|power_w)\s*=\s*([-+0-9.eE]+)",
    re.MULTILINE,
)


def run_point(template: str, corner: str, temperature_c: int, load_ff: int) -> dict:
    netlist = (
        template.replace("@@DESIGN_FILE@@", DESIGN_FILE)
        .replace("@@MODEL_FILE@@", MODEL_FILE)
        .replace("@@CORNER@@", corner)
        .replace("@@TEMP_C@@", str(temperature_c))
        .replace("@@CLOAD@@", f"{load_ff}f")
    )
    with tempfile.TemporaryDirectory(prefix="ring-dco-") as temporary_dir:
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
    if result.returncode or set(values) != {
        "frequency_hz",
        "supply_current_a",
        "power_w",
    }:
        raise RuntimeError(
            f"ngspice failed for {corner}, {load_ff} fF\n{output[-4000:]}"
        )
    values["supply_current_a"] = -values["supply_current_a"]
    return {
        "corner": corner,
        "temperature_c": temperature_c,
        "load_ff": load_ff,
        **values,
    }


def main() -> None:
    template = TEMPLATE.read_text()
    points = [
        run_point(template, corner, temperature_c, load_ff)
        for corner, temperature_c in CORNERS
        for load_ff in LOADS_FF
    ]
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "circuit": "gf180_three_stage_ring_oscillator",
                "purpose": "frequency-and-power-feasibility-only",
                "vdd_v": 1.8,
                "device_length_um": 0.28,
                "nmos_width_um": 1.0,
                "pmos_width_um": 2.0,
                "ble_band_hz": {"low": 2_402_000_000, "high": 2_480_000_000},
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
