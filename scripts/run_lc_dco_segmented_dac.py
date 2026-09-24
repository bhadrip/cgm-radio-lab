#!/usr/bin/env python3
"""Size slow-bias and fast-modulation DACs for the calibrated LC-DCO."""

from __future__ import annotations

import json
from pathlib import Path

from model.ble import CgmMeasurement, build_cgm_air_packet_bits
from model.dco import ble_channel_center_hz
from model.lc_dco_dac import SegmentedVoltageDac, VoltageDac
from model.lc_dco_modulation import (
    control_voltage_for_frequency,
    control_waveform,
    frequency_for_control_voltage,
)


ROOT = Path(__file__).resolve().parents[1]
STATIC_SWEEP = ROOT / "reports" / "lc_dco_sweep.json"
LOCAL_CALIBRATION = ROOT / "reports" / "lc_dco_local_calibration.json"
REPORT = ROOT / "reports" / "lc_dco_segmented_dac.json"
CORNERS = ("typical", "ff", "ss")
CHANNELS = (37, 38, 39)
BIAS_RANGE_V = (0.9, 1.4)
MODULATION_RANGE_V = (-0.008, 0.008)
CANDIDATE_BIAS_BITS = range(6, 11)
CANDIDATE_MODULATION_BITS = range(4, 8)
COMBINED_ERROR_LIMIT_HZ = 40_000
HEADROOM_LIMIT_V = 0.003
ADDRESS = 0xC0DEC0FFEE01
MEASUREMENT = CgmMeasurement(0x1234, 123, -256, 0x03, 91)


def main() -> None:
    points = json.loads(STATIC_SWEEP.read_text())["points"]
    calibration_report = json.loads(LOCAL_CALIBRATION.read_text())
    points += calibration_report["points"]
    calibration_error_hz = calibration_report[
        "maximum_final_calibration_error_hz"
    ]
    waveforms = []
    for corner in CORNERS:
        for channel in CHANNELS:
            packet = build_cgm_air_packet_bits(MEASUREMENT, ADDRESS, channel)
            calibration, offsets_hz, voltages_v = control_waveform(
                points, corner, channel, packet
            )
            waveforms.append(
                (
                    corner,
                    channel,
                    calibration,
                    offsets_hz,
                    voltages_v,
                    control_voltage_for_frequency(
                        points, calibration, ble_channel_center_hz(channel)
                    ),
                )
            )

    summaries = []
    for bias_bits in CANDIDATE_BIAS_BITS:
        for modulation_bits in CANDIDATE_MODULATION_BITS:
            dac = SegmentedVoltageDac(
                VoltageDac(bias_bits, *BIAS_RANGE_V),
                VoltageDac(modulation_bits, *MODULATION_RANGE_V),
            )
            saturated = False
            maximum_residual_v = 0.0
            maximum_error_hz = 0.0
            worst_case = None
            for corner, channel, calibration, offsets_hz, voltages_v, center_v in waveforms:
                bias_code = dac.bias.code_for_voltage(center_v)
                bias_v = dac.bias.voltage_for_code(bias_code)
                residuals_v = [voltage_v - bias_v for voltage_v in voltages_v]
                maximum_residual_v = max(
                    maximum_residual_v, max(abs(value) for value in residuals_v)
                )
                if any(
                    not dac.modulation.minimum_v
                    <= residual_v
                    <= dac.modulation.maximum_v
                    for residual_v in residuals_v
                ):
                    saturated = True
                    continue
                _, modulation_codes, outputs_v = dac.quantize_waveform(
                    center_v, voltages_v
                )
                center_hz = ble_channel_center_hz(channel)
                for offset_hz, code, output_v in zip(
                    offsets_hz, modulation_codes, outputs_v
                ):
                    realized_hz = frequency_for_control_voltage(
                        points, calibration, output_v
                    )
                    error_hz = realized_hz - (center_hz + offset_hz)
                    if abs(error_hz) > maximum_error_hz:
                        maximum_error_hz = abs(error_hz)
                        worst_case = {
                            "corner": corner,
                            "channel": channel,
                            "requested_offset_hz": offset_hz,
                            "modulation_code": code,
                            "output_voltage_v": output_v,
                            "error_hz": error_hz,
                        }
            voltage_headroom_v = dac.modulation.maximum_v - maximum_residual_v
            combined_error_hz = maximum_error_hz + calibration_error_hz
            meets_limits = (
                not saturated
                and voltage_headroom_v >= HEADROOM_LIMIT_V
                and combined_error_hz <= COMBINED_ERROR_LIMIT_HZ
            )
            summaries.append(
                {
                    "bias_bits": bias_bits,
                    "modulation_bits": modulation_bits,
                    "bias_lsb_v": dac.bias.lsb_v,
                    "modulation_lsb_v": dac.modulation.lsb_v,
                    "maximum_residual_v": maximum_residual_v,
                    "voltage_headroom_v": voltage_headroom_v,
                    "saturated": saturated,
                    "maximum_quantization_error_hz": maximum_error_hz,
                    "calibration_error_bound_hz": calibration_error_hz,
                    "conservative_combined_error_hz": combined_error_hz,
                    "meets_limits": meets_limits,
                    "worst_case": worst_case,
                }
            )
    selected = next(summary for summary in summaries if summary["meets_limits"])
    report = {
        "schema_version": 1,
        "bias_range_v": {"minimum": BIAS_RANGE_V[0], "maximum": BIAS_RANGE_V[1]},
        "modulation_range_v": {
            "minimum": MODULATION_RANGE_V[0],
            "maximum": MODULATION_RANGE_V[1],
        },
        "combined_error_limit_hz": COMBINED_ERROR_LIMIT_HZ,
        "minimum_voltage_headroom_v": HEADROOM_LIMIT_V,
        "packet_samples_per_corner_channel": 224 * 16,
        "corner_channel_combinations": len(waveforms),
        "selected_bias_bits": selected["bias_bits"],
        "selected_modulation_bits": selected["modulation_bits"],
        "passed": selected["bias_bits"] == 7 and selected["modulation_bits"] == 6,
        "summaries": summaries,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")
    if not report["passed"]:
        raise RuntimeError(
            "segmented DAC selection changed from the reviewed 7-bit + 6-bit result"
        )


if __name__ == "__main__":
    main()
