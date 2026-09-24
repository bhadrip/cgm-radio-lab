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

from model.ble import add_crc, build_test_pdu, run_hard_bit_loop

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
SEED = 49374
PACKETS_PER_POINT = 2000
ERROR_RATES = (0.0, 0.0001, 0.001, 0.01)
CHANNEL = 37


def git_revision() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "uncommitted"


def run_point(rng: random.Random, raw_ber: float) -> dict[str, float | int]:
    packet_errors = 0
    payload_errors = 0
    flipped_bits = 0
    transmitted_bits = 0

    for _ in range(PACKETS_PER_POINT):
        payload = rng.randbytes(8)
        bit_count = len(add_crc(build_test_pdu(payload)))
        error_mask = [int(rng.random() < raw_ber) for _ in range(bit_count)]
        result = run_hard_bit_loop(payload, CHANNEL, error_mask)
        transmitted_bits += result.transmitted_bits
        flipped_bits += result.flipped_bits
        packet_errors += int(not result.crc_passed)
        payload_errors += int(not result.payload_recovered)

    return {
        "requested_raw_ber": raw_ber,
        "measured_raw_ber": flipped_bits / transmitted_bits,
        "packets": PACKETS_PER_POINT,
        "packet_errors": packet_errors,
        "packet_error_rate": packet_errors / PACKETS_PER_POINT,
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
        "slice": "ble-hard-bit-loop",
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
        writer = csv.DictWriter(handle, fieldnames=points[0].keys())
        writer.writeheader()
        writer.writerows(points)

    print(json.dumps(summary, indent=2))
    return 0 if points[0]["packet_errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

