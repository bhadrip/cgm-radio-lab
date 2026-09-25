#!/usr/bin/env python3
"""Map a complete CGM packet's GFSK samples onto LC-DCO fine control."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from model.ble import CgmMeasurement, build_cgm_air_packet_bits
from model.dco import ble_channel_center_hz
from model.lc_dco_modulation import (
    control_voltage_for_frequency,
    control_waveform,
    maximum_slew_v_per_s,
)


ROOT = Path(__file__).resolve().parents[1]
SWEEP = ROOT / "reports" / "lc_dco_sweep.json"
REPORT = ROOT / "reports" / "lc_dco_modulation.json"
NOMINAL_CSV = ROOT / "reports" / "lc_dco_modulation_nominal_ch37.csv"
CORNERS = ("typical", "ff", "ss")
CHANNELS = (37, 38, 39)
MEASUREMENT = CgmMeasurement(
    sequence=0x1234,
    glucose_mg_dl=123,
    trend_q8_8=-256,
    status=0x03,
    battery_percent=91,
)
ADDRESS = 0xC0DEC0FFEE01


def main() -> None:
    sweep = json.loads(SWEEP.read_text())
    points = sweep["points"]
    summaries = []
    nominal_rows = []
    for corner in CORNERS:
        for channel in CHANNELS:
            bits = build_cgm_air_packet_bits(MEASUREMENT, ADDRESS, channel)
            calibration, offsets_hz, voltages = control_waveform(
                points, corner, channel, bits
            )
            center_hz = ble_channel_center_hz(channel)
            center_voltage = control_voltage_for_frequency(
                points, calibration, center_hz
            )
            summaries.append(
                {
                    "corner": corner,
                    "channel": channel,
                    "center_frequency_hz": center_hz,
                    "coarse_code": calibration.coarse_code,
                    "calibration_margin_hz": calibration.worst_case_margin_hz,
                    "center_control_voltage_v": center_voltage,
                    "minimum_control_voltage_v": min(voltages),
                    "maximum_control_voltage_v": max(voltages),
                    "control_peak_to_peak_v": max(voltages) - min(voltages),
                    "maximum_sample_step_v": max(
                        abs(current - previous)
                        for previous, current in zip(voltages, voltages[1:])
                    ),
                    "maximum_slew_v_per_s": maximum_slew_v_per_s(voltages),
                    "samples": len(voltages),
                    "coarse_switches_during_packet": 0,
                }
            )
            if corner == "typical" and channel == 37:
                nominal_rows = [
                    {
                        "sample": index,
                        "time_s": index / 16_000_000,
                        "frequency_offset_hz": offset,
                        "control_voltage_v": voltage,
                    }
                    for index, (offset, voltage) in enumerate(
                        zip(offsets_hz, voltages)
                    )
                ]
    report = {
        "schema_version": 1,
        "source": str(SWEEP.relative_to(ROOT)),
        "packet_bits": 224,
        "samples_per_symbol": 16,
        "sample_rate_hz": 16_000_000,
        "modulation_index": 0.5,
        "nominal_deviation_hz": 250_000,
        "mapping": "piecewise-linear inverse of transistor-level static sweep",
        "summaries": summaries,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    with NOMINAL_CSV.open("w", newline="") as output:
        writer = csv.DictWriter(
            output, fieldnames=nominal_rows[0].keys(), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(nominal_rows)
    print(REPORT.read_text(), end="")


if __name__ == "__main__":
    main()
