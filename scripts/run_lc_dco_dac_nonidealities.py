#!/usr/bin/env python3
"""Budget segmented-DAC quantization, INL, DNL, and control noise."""

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
SEGMENTED_DAC = ROOT / "reports" / "lc_dco_segmented_dac.json"
REPORT = ROOT / "reports" / "lc_dco_dac_nonidealities.json"
CORNERS = ("typical", "ff", "ss")
CHANNELS = (37, 38, 39)
CANDIDATE_MODULATION_BITS = (6, 7, 8)
INL_LIMIT_LSB = 0.5
DNL_LIMIT_LSB = 0.5
CONTROL_NOISE_RMS_V = 25e-6
NOISE_SIGMA_MULTIPLIER = 3
TOTAL_ERROR_LIMIT_HZ = 50_000
ADDRESS = 0xC0DEC0FFEE01
MEASUREMENT = CgmMeasurement(0x1234, 123, -256, 0x03, 91)


def main() -> None:
    points = json.loads(STATIC_SWEEP.read_text())["points"]
    calibration_report = json.loads(LOCAL_CALIBRATION.read_text())
    points += calibration_report["points"]
    calibration_error_hz = calibration_report[
        "maximum_final_calibration_error_hz"
    ]
    segmented = json.loads(SEGMENTED_DAC.read_text())
    bias_bits = segmented["selected_bias_bits"]
    bias_range = segmented["bias_range_v"]
    modulation_range = segmented["modulation_range_v"]
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
    for modulation_bits in CANDIDATE_MODULATION_BITS:
        dac = SegmentedVoltageDac(
            VoltageDac(bias_bits, bias_range["minimum"], bias_range["maximum"]),
            VoltageDac(
                modulation_bits,
                modulation_range["minimum"],
                modulation_range["maximum"],
            ),
        )
        maximum_quantization_error_hz = 0.0
        maximum_inl_error_hz = 0.0
        maximum_noise_error_hz = 0.0
        worst_case = None
        for corner, channel, calibration, offsets_hz, voltages_v, center_v in waveforms:
            _, codes, outputs_v = dac.quantize_waveform(center_v, voltages_v)
            center_hz = ble_channel_center_hz(channel)
            for offset_hz, code, output_v in zip(offsets_hz, codes, outputs_v):
                requested_hz = center_hz + offset_hz
                realized_hz = frequency_for_control_voltage(
                    points, calibration, output_v
                )
                quantization_error_hz = abs(realized_hz - requested_hz)
                inl_error_hz = max(
                    abs(
                        frequency_for_control_voltage(
                            points,
                            calibration,
                            output_v + direction * INL_LIMIT_LSB * dac.modulation.lsb_v,
                        )
                        - realized_hz
                    )
                    for direction in (-1, 1)
                )
                noise_error_hz = max(
                    abs(
                        frequency_for_control_voltage(
                            points,
                            calibration,
                            output_v
                            + direction
                            * NOISE_SIGMA_MULTIPLIER
                            * CONTROL_NOISE_RMS_V,
                        )
                        - realized_hz
                    )
                    for direction in (-1, 1)
                )
                maximum_inl_error_hz = max(maximum_inl_error_hz, inl_error_hz)
                maximum_noise_error_hz = max(maximum_noise_error_hz, noise_error_hz)
                if quantization_error_hz > maximum_quantization_error_hz:
                    maximum_quantization_error_hz = quantization_error_hz
                    worst_case = {
                        "corner": corner,
                        "channel": channel,
                        "requested_offset_hz": offset_hz,
                        "modulation_code": code,
                        "output_voltage_v": output_v,
                        "quantization_error_hz": quantization_error_hz,
                    }
        conservative_total_hz = (
            calibration_error_hz
            + maximum_quantization_error_hz
            + maximum_inl_error_hz
            + maximum_noise_error_hz
        )
        summaries.append(
            {
                "bias_bits": bias_bits,
                "modulation_bits": modulation_bits,
                "modulation_lsb_v": dac.modulation.lsb_v,
                "calibration_error_bound_hz": calibration_error_hz,
                "maximum_quantization_error_hz": maximum_quantization_error_hz,
                "maximum_inl_error_hz": maximum_inl_error_hz,
                "maximum_three_sigma_noise_error_hz": maximum_noise_error_hz,
                "conservative_total_error_hz": conservative_total_hz,
                "meets_error_limit": conservative_total_hz <= TOTAL_ERROR_LIMIT_HZ,
                "worst_quantization_case": worst_case,
            }
        )
    selected = next(summary for summary in summaries if summary["meets_error_limit"])
    report = {
        "schema_version": 1,
        "total_frequency_error_limit_hz": TOTAL_ERROR_LIMIT_HZ,
        "inl_limit_lsb": INL_LIMIT_LSB,
        "dnl_limit_lsb": DNL_LIMIT_LSB,
        "dnl_requirement": "monotonic with no missing codes; not added separately from INL",
        "control_noise_rms_v": CONTROL_NOISE_RMS_V,
        "noise_sigma_multiplier": NOISE_SIGMA_MULTIPLIER,
        "packet_samples_per_corner_channel": 224 * 16,
        "corner_channel_combinations": len(waveforms),
        "selected_bias_bits": bias_bits,
        "selected_modulation_bits": selected["modulation_bits"],
        "passed": selected["modulation_bits"] == 7,
        "summaries": summaries,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")
    if not report["passed"]:
        raise RuntimeError("DAC non-ideality budget changed from the reviewed result")


if __name__ == "__main__":
    main()
