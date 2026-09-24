#!/usr/bin/env python3
"""Find the minimum full-scale DAC resolution for calibrated GFSK drive."""

from __future__ import annotations

import json
import math
from pathlib import Path

from model.ble import CgmMeasurement, build_cgm_air_packet_bits
from model.dco import ble_channel_center_hz
from model.lc_dco_dac import VoltageDac
from model.lc_dco_modulation import control_waveform, frequency_for_control_voltage


ROOT = Path(__file__).resolve().parents[1]
STATIC_SWEEP = ROOT / "reports" / "lc_dco_sweep.json"
LOCAL_CALIBRATION = ROOT / "reports" / "lc_dco_local_calibration.json"
REPORT = ROOT / "reports" / "lc_dco_dac_resolution.json"
CORNERS = ("typical", "ff", "ss")
CHANNELS = (37, 38, 39)
CANDIDATE_BITS = range(8, 15)
ERROR_BUDGET_HZ = 50_000
ADDRESS = 0xC0DEC0FFEE01
MEASUREMENT = CgmMeasurement(0x1234, 123, -256, 0x03, 91)


def main() -> None:
    points = json.loads(STATIC_SWEEP.read_text())["points"]
    calibration_report = json.loads(LOCAL_CALIBRATION.read_text())
    points += calibration_report["points"]
    calibration_error_hz = calibration_report[
        "maximum_final_calibration_error_hz"
    ]
    summaries = []
    for bits in CANDIDATE_BITS:
        dac = VoltageDac(bits)
        squared_error_sum = 0.0
        sample_count = 0
        maximum_error_hz = 0.0
        worst_case = None
        for corner in CORNERS:
            for channel in CHANNELS:
                packet = build_cgm_air_packet_bits(MEASUREMENT, ADDRESS, channel)
                calibration, offsets_hz, ideal_voltages = control_waveform(
                    points, corner, channel, packet
                )
                center_hz = ble_channel_center_hz(channel)
                for offset_hz, ideal_voltage_v in zip(offsets_hz, ideal_voltages):
                    code = dac.code_for_voltage(ideal_voltage_v)
                    quantized_voltage_v = dac.voltage_for_code(code)
                    realized_hz = frequency_for_control_voltage(
                        points, calibration, quantized_voltage_v
                    )
                    error_hz = realized_hz - (center_hz + offset_hz)
                    squared_error_sum += error_hz**2
                    sample_count += 1
                    if abs(error_hz) > maximum_error_hz:
                        maximum_error_hz = abs(error_hz)
                        worst_case = {
                            "corner": corner,
                            "channel": channel,
                            "requested_offset_hz": offset_hz,
                            "ideal_voltage_v": ideal_voltage_v,
                            "dac_code": code,
                            "quantized_voltage_v": quantized_voltage_v,
                            "error_hz": error_hz,
                        }
        conservative_error_hz = maximum_error_hz + calibration_error_hz
        summaries.append(
            {
                "bits": bits,
                "levels": dac.maximum_code + 1,
                "lsb_v": dac.lsb_v,
                "maximum_quantization_error_hz": maximum_error_hz,
                "rms_quantization_error_hz": math.sqrt(
                    squared_error_sum / sample_count
                ),
                "calibration_error_bound_hz": calibration_error_hz,
                "conservative_combined_error_hz": conservative_error_hz,
                "meets_error_budget": conservative_error_hz <= ERROR_BUDGET_HZ,
                "worst_case": worst_case,
            }
        )
    selected = next(summary for summary in summaries if summary["meets_error_budget"])
    report = {
        "schema_version": 1,
        "dac_range_v": {"minimum": 0.0, "maximum": 1.8},
        "frequency_error_budget_hz": ERROR_BUDGET_HZ,
        "packet_samples_per_corner_channel": 224 * 16,
        "corner_channel_combinations": len(CORNERS) * len(CHANNELS),
        "selected_bits": selected["bits"],
        "passed": selected["bits"] == 12,
        "summaries": summaries,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")
    if not report["passed"]:
        raise RuntimeError(f"expected 12-bit DAC candidate, got {selected['bits']} bits")


if __name__ == "__main__":
    main()
