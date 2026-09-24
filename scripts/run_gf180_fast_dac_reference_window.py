#!/usr/bin/env python3
"""Derive the allowed fast-DAC reference-current window."""

from __future__ import annotations

import bisect
import json
from pathlib import Path

from model.ble import CgmMeasurement, build_cgm_air_packet_bits
from model.dco import ble_channel_center_hz
from model.lc_dco_modulation import (
    control_voltage_for_frequency,
    control_waveform,
    frequency_for_control_voltage,
)
from scripts.run_gf180_fast_dac_gate_driver import characterize as characterize_driver


ROOT = Path(__file__).resolve().parents[1]
STATIC_SWEEP = ROOT / "reports" / "lc_dco_sweep.json"
LOCAL_CALIBRATION = ROOT / "reports" / "lc_dco_local_calibration.json"
DAC_PVT = ROOT / "reports" / "gf180_fast_dac_steered_pvt.json"
REPORT = ROOT / "reports" / "gf180_fast_dac_reference_window.json"
CORNERS = (("typical", 25), ("ff", -40), ("ss", 125))
CHANNELS = (37, 38, 39)
REFERENCE_SCALES = (0.80, 0.825, 0.85, 0.90, 1.00, 1.05, 1.075, 1.10, 1.15)
MINIMUM_HEADROOM_V = 3e-3
INL_LIMIT_LSB = 0.5
CONTROL_NOISE_RMS_V = 25e-6
NOISE_SIGMA_MULTIPLIER = 3
TOTAL_ERROR_LIMIT_HZ = 50_000
DRIVER_TOPOLOGY = "three_stage_output_two_stage_dummy"
DRIVER_SCALE = 0.5
ADDRESS = 0xC0DEC0FFEE01
MEASUREMENT = CgmMeasurement(0x1234, 123, -256, 0x03, 91)


def nearest_code(transfer_v: list[float], requested_v: float) -> int:
    upper = bisect.bisect_left(transfer_v, requested_v)
    if upper == 0:
        return 0
    if upper == len(transfer_v):
        return len(transfer_v) - 1
    lower = upper - 1
    if requested_v - transfer_v[lower] <= transfer_v[upper] - requested_v:
        return lower
    return upper


def build_waveforms(points: list[dict]) -> list[dict]:
    waveforms = []
    for corner, _ in CORNERS:
        for channel in CHANNELS:
            packet = build_cgm_air_packet_bits(MEASUREMENT, ADDRESS, channel)
            calibration, offsets_hz, voltages_v = control_waveform(
                points, corner, channel, packet
            )
            center_v = control_voltage_for_frequency(
                points, calibration, ble_channel_center_hz(channel)
            )
            waveforms.append(
                {
                    "corner": corner,
                    "channel": channel,
                    "calibration": calibration,
                    "offsets_hz": offsets_hz,
                    "residuals_v": [voltage - center_v for voltage in voltages_v],
                    "center_v": center_v,
                }
            )
    return waveforms


def scaled_transfer(voltages_v: list[float], scale: float) -> list[float]:
    span_v = voltages_v[-1] - voltages_v[0]
    return [
        scale * ((voltage_v - voltages_v[0]) - span_v / 2.0)
        for voltage_v in voltages_v
    ]


def packet_errors(
    points: list[dict], waveforms: list[dict], transfers: dict[str, list[float]], scale: float
) -> dict:
    maximum_quantization_error_hz = 0.0
    maximum_inl_error_hz = 0.0
    maximum_noise_error_hz = 0.0
    minimum_headroom_v = float("inf")
    minimum_code = 127
    maximum_code = 0
    saturated = False
    for waveform in waveforms:
        transfer_v = scaled_transfer(transfers[waveform["corner"]], scale)
        lsb_v = (transfer_v[-1] - transfer_v[0]) / 127.0
        residuals_v = waveform["residuals_v"]
        lower_headroom_v = min(residuals_v) - transfer_v[0]
        upper_headroom_v = transfer_v[-1] - max(residuals_v)
        minimum_headroom_v = min(
            minimum_headroom_v, lower_headroom_v, upper_headroom_v
        )
        saturated |= lower_headroom_v < 0.0 or upper_headroom_v < 0.0
        channel_center_hz = ble_channel_center_hz(waveform["channel"])
        for offset_hz, residual_v in zip(waveform["offsets_hz"], residuals_v):
            code = nearest_code(transfer_v, residual_v)
            minimum_code = min(minimum_code, code)
            maximum_code = max(maximum_code, code)
            output_v = waveform["center_v"] + transfer_v[code]
            realized_hz = frequency_for_control_voltage(
                points, waveform["calibration"], output_v
            )
            requested_hz = channel_center_hz + offset_hz
            maximum_quantization_error_hz = max(
                maximum_quantization_error_hz, abs(realized_hz - requested_hz)
            )
            for direction in (-1, 1):
                maximum_inl_error_hz = max(
                    maximum_inl_error_hz,
                    abs(
                        frequency_for_control_voltage(
                            points,
                            waveform["calibration"],
                            output_v + direction * INL_LIMIT_LSB * lsb_v,
                        )
                        - realized_hz
                    ),
                )
                maximum_noise_error_hz = max(
                    maximum_noise_error_hz,
                    abs(
                        frequency_for_control_voltage(
                            points,
                            waveform["calibration"],
                            output_v
                            + direction
                            * NOISE_SIGMA_MULTIPLIER
                            * CONTROL_NOISE_RMS_V,
                        )
                        - realized_hz
                    ),
                )
    return {
        "saturated": saturated,
        "minimum_voltage_headroom_v": minimum_headroom_v,
        "minimum_used_code": minimum_code,
        "maximum_used_code": maximum_code,
        "maximum_quantization_error_hz": maximum_quantization_error_hz,
        "maximum_inl_error_hz": maximum_inl_error_hz,
        "maximum_three_sigma_noise_error_hz": maximum_noise_error_hz,
    }


def main() -> None:
    points = json.loads(STATIC_SWEEP.read_text())["points"]
    calibration = json.loads(LOCAL_CALIBRATION.read_text())
    points += calibration["points"]
    calibration_error_hz = calibration["maximum_final_calibration_error_hz"]
    pvt = json.loads(DAC_PVT.read_text())
    transfers = {
        summary["corner"]: summary["code_voltages_v"]
        for summary in pvt["summaries"]
    }
    waveforms = build_waveforms(points)
    summaries = []
    for reference_scale in REFERENCE_SCALES:
        packet = packet_errors(points, waveforms, transfers, reference_scale)
        driver_corners = [
            characterize_driver(
                DRIVER_TOPOLOGY,
                DRIVER_SCALE,
                corner,
                temperature_c,
                reference_scale,
            )
            for corner, temperature_c in CORNERS
        ]
        maximum_glitch_error_hz = max(
            corner["glitch_frequency_error_hz"] for corner in driver_corners
        )
        total_error_hz = (
            calibration_error_hz
            + packet["maximum_quantization_error_hz"]
            + packet["maximum_inl_error_hz"]
            + packet["maximum_three_sigma_noise_error_hz"]
            + maximum_glitch_error_hz
        )
        passed = (
            not packet["saturated"]
            and packet["minimum_voltage_headroom_v"] >= MINIMUM_HEADROOM_V
            and total_error_hz <= TOTAL_ERROR_LIMIT_HZ
        )
        summaries.append(
            {
                "reference_current_scale": reference_scale,
                **packet,
                "maximum_glitch_frequency_error_hz": maximum_glitch_error_hz,
                "calibration_error_bound_hz": calibration_error_hz,
                "conservative_total_frequency_error_hz": total_error_hz,
                "passed": passed,
                "driver_corners": [
                    {
                        "corner": corner["corner"],
                        "temperature_c": corner["temperature_c"],
                        "peak_glitch_v": corner["peak_glitch_v"],
                        "glitch_frequency_error_hz": corner[
                            "glitch_frequency_error_hz"
                        ],
                    }
                    for corner in driver_corners
                ],
            }
        )
    passing = [summary for summary in summaries if summary["passed"]]
    report = {
        "schema_version": 1,
        "purpose": "fast-DAC reference-current tolerance from packet and carry gates",
        "minimum_voltage_headroom_v": MINIMUM_HEADROOM_V,
        "frequency_error_limit_hz": TOTAL_ERROR_LIMIT_HZ,
        "selected_minimum_reference_current_scale": min(
            summary["reference_current_scale"] for summary in passing
        ),
        "selected_maximum_reference_current_scale": max(
            summary["reference_current_scale"] for summary in passing
        ),
        "passed": (
            bool(passing)
            and not summaries[0]["passed"]
            and not summaries[-1]["passed"]
        ),
        "summaries": summaries,
        "limitations": [
            "Packet mapping scales the measured nominal code-transfer shape with reference current.",
            "Carry glitches are re-simulated with GF180 transistor drivers at every scale and PVT point.",
            "No on-chip reference topology or qualified reference-noise model is claimed.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")
    if not report["passed"]:
        raise RuntimeError("reference-current sweep did not bracket a passing window")


if __name__ == "__main__":
    main()
