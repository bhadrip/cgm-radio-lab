#!/usr/bin/env python3
"""Run a deterministic hard-bit channel sweep and persist the measurements."""

from __future__ import annotations

import csv
import json
import os
import platform
import random
import subprocess
import sys
from pathlib import Path

from model.ble import CgmMeasurement, build_cgm_air_packet_bits, run_cgm_air_loop

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
SEED = 49374
PACKETS_PER_POINT = 2000
ERROR_RATES = (0.0, 0.0001, 0.001, 0.01)
CHANNEL = 37


def git_revision() -> str:
    try:
        return subprocess.check_output(
            ["git", "-c", f"safe.directory={ROOT}", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "uncommitted"


def run_point(rng: random.Random, raw_ber: float) -> dict[str, float | int]:
    packet_errors = 0
    format_errors = 0
    payload_errors = 0
    flipped_bits = 0
    transmitted_bits = 0

    for _ in range(PACKETS_PER_POINT):
        measurement = CgmMeasurement(
            sequence=rng.randrange(0x10000),
            glucose_mg_dl=rng.randrange(40, 401),
            trend_q8_8=rng.randrange(-5 * 256, 5 * 256 + 1),
            status=rng.randrange(0x100),
            battery_percent=rng.randrange(101),
        )
        address = 0xC0DEC0000000 | rng.randrange(1 << 24)
        bit_count = len(build_cgm_air_packet_bits(measurement, address, CHANNEL))
        error_mask = [int(rng.random() < raw_ber) for _ in range(bit_count)]
        result = run_cgm_air_loop(measurement, address, CHANNEL, error_mask)
        transmitted_bits += result.transmitted_bits
        flipped_bits += result.flipped_bits
        packet_errors += int(not (result.crc_passed and result.format_passed))
        format_errors += int(not result.format_passed)
        payload_errors += int(not result.payload_recovered)

    return {
        "requested_raw_ber": raw_ber,
        "measured_raw_ber": flipped_bits / transmitted_bits,
        "packets": PACKETS_PER_POINT,
        "packet_errors": packet_errors,
        "packet_error_rate": packet_errors / PACKETS_PER_POINT,
        "format_errors": format_errors,
        "payload_errors": payload_errors,
        "payload_error_rate": payload_errors / PACKETS_PER_POINT,
        "transmitted_bits": transmitted_bits,
        "flipped_bits": flipped_bits,
    }


def main() -> int:
    rng = random.Random(SEED)
    points = [run_point(rng, rate) for rate in ERROR_RATES]
    REPORTS.mkdir(parents=True, exist_ok=True)

    summary = {
        "schema_version": 1,
        "slice": "cgm-advertising-packet-loop",
        "git_revision": git_revision(),
        "container_image": os.environ.get(
            "EDA_IMAGE", "docker.io/hpretl/iic-osic-tools:2026.08"
        ),
        "python": platform.python_version(),
        "seed": SEED,
        "channel": CHANNEL,
        "payload_bytes": 8,
        "points": points,
    }
    (REPORTS / "experiment.json").write_text(json.dumps(summary, indent=2) + "\n")

    with (REPORTS / "per_curve.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=points[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(points)

    print(json.dumps(summary, indent=2))
    return 0 if points[0]["packet_errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
