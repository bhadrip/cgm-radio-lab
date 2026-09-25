#!/usr/bin/env python3
"""Bound fast-DAC code-transition glitch against the control-error margin."""

from __future__ import annotations

import json
import math
from pathlib import Path

from model.ble import CgmMeasurement, build_cgm_air_packet_bits
from model.dco import ble_channel_center_hz
from model.lc_dco_dac import (
    SegmentedDacEncoding,
    SegmentedVoltageDac,
    VoltageDac,
)
from model.lc_dco_modulation import (
    control_voltage_for_frequency,
    control_waveform,
    maximum_tuning_gain_hz_per_v,
)


ROOT = Path(__file__).resolve().parents[1]
STATIC_SWEEP = ROOT / "reports" / "lc_dco_sweep.json"
LOCAL_CALIBRATION = ROOT / "reports" / "lc_dco_local_calibration.json"
SEGMENTED_DAC = ROOT / "reports" / "lc_dco_segmented_dac.json"
NONIDEALITY_BUDGET = ROOT / "reports" / "lc_dco_dac_nonidealities.json"
DRIVE_SETTLING = ROOT / "reports" / "lc_dco_drive_settling.json"
REPORT = ROOT / "reports" / "lc_dco_dac_transition.json"
CORNERS = ("typical", "ff", "ss")
CHANNELS = (37, 38, 39)
SWITCH_SKEW_TARGET_S = 750e-12
ADDRESS = 0xC0DEC0FFEE01
MEASUREMENT = CgmMeasurement(0x1234, 123, -256, 0x03, 91)


def main() -> None:
    points = json.loads(STATIC_SWEEP.read_text())["points"]
    points += json.loads(LOCAL_CALIBRATION.read_text())["points"]
    segmented = json.loads(SEGMENTED_DAC.read_text())
    nonidealities = json.loads(NONIDEALITY_BUDGET.read_text())
    drive = json.loads(DRIVE_SETTLING.read_text())
    selected_nonideality = next(
        summary
        for summary in nonidealities["summaries"]
        if summary["modulation_bits"]
        == nonidealities["selected_modulation_bits"]
    )
    frequency_margin_hz = (
        nonidealities["total_frequency_error_limit_hz"]
        - selected_nonideality["conservative_total_error_hz"]
    )
    dac = SegmentedVoltageDac(
        VoltageDac(
            segmented["selected_bias_bits"],
            segmented["bias_range_v"]["minimum"],
            segmented["bias_range_v"]["maximum"],
        ),
        VoltageDac(
            nonidealities["selected_modulation_bits"],
            segmented["modulation_range_v"]["minimum"],
            segmented["modulation_range_v"]["maximum"],
        ),
    )
    transitions = []
    maximum_tuning_gain = 0.0
    code_minimum = dac.modulation.maximum_code
    code_maximum = 0
    sample_count = 0
    for corner in CORNERS:
        for channel in CHANNELS:
            bits = build_cgm_air_packet_bits(MEASUREMENT, ADDRESS, channel)
            calibration, _, voltages_v = control_waveform(
                points, corner, channel, bits
            )
            center_v = control_voltage_for_frequency(
                points, calibration, ble_channel_center_hz(channel)
            )
            _, codes, _ = dac.quantize_waveform(center_v, voltages_v)
            sample_count += len(codes)
            code_minimum = min(code_minimum, *codes)
            code_maximum = max(code_maximum, *codes)
            maximum_tuning_gain = max(
                maximum_tuning_gain,
                maximum_tuning_gain_hz_per_v(points, calibration),
            )
            transitions.extend(
                {
                    "corner": corner,
                    "channel": channel,
                    "previous_code": previous_code,
                    "next_code": next_code,
                }
                for previous_code, next_code in zip(codes, codes[1:])
            )

    drive_resistance_ohm = drive["recommended_maximum_output_resistance_ohm"]
    control_load_f = drive["recommended_bypass_capacitance_f"]
    time_constant_s = drive_resistance_ohm * control_load_f
    rc_peak_fraction = 1 - math.exp(-SWITCH_SKEW_TARGET_S / time_constant_s)
    summaries = []
    for thermometer_bits in range(dac.modulation.bits + 1):
        encoding = SegmentedDacEncoding(dac.modulation.bits, thermometer_bits)
        maximum_excursion_codes = 0
        worst_transition = None
        for transition in transitions:
            excursion_codes = encoding.worst_case_glitch_excursion_codes(
                transition["previous_code"], transition["next_code"]
            )
            if excursion_codes > maximum_excursion_codes:
                maximum_excursion_codes = excursion_codes
                worst_transition = {**transition, "excursion_codes": excursion_codes}
        source_excursion_v = maximum_excursion_codes * dac.modulation.lsb_v
        unfiltered_frequency_excursion_hz = (
            source_excursion_v * maximum_tuning_gain
        )
        node_frequency_excursion_hz = (
            unfiltered_frequency_excursion_hz * rc_peak_fraction
        )
        combined_frequency_error_hz = (
            selected_nonideality["conservative_total_error_hz"]
            + node_frequency_excursion_hz
        )
        if unfiltered_frequency_excursion_hz <= frequency_margin_hz:
            maximum_allowed_skew_s = None
        else:
            maximum_allowed_skew_s = -time_constant_s * math.log(
                1 - frequency_margin_hz / unfiltered_frequency_excursion_hz
            )
        summaries.append(
            {
                "thermometer_msb_bits": thermometer_bits,
                "binary_lsb_bits": encoding.binary_lsb_bits,
                "switched_element_count": encoding.switched_element_count,
                "maximum_glitch_excursion_codes": maximum_excursion_codes,
                "maximum_source_glitch_v": source_excursion_v,
                "maximum_node_glitch_v": source_excursion_v * rc_peak_fraction,
                "maximum_glitch_frequency_error_hz": node_frequency_excursion_hz,
                "combined_frequency_error_hz": combined_frequency_error_hz,
                "maximum_allowed_switch_skew_s": maximum_allowed_skew_s,
                "meets_error_limit": combined_frequency_error_hz
                <= nonidealities["total_frequency_error_limit_hz"],
                "worst_transition": worst_transition,
            }
        )
    selected = next(summary for summary in summaries if summary["meets_error_limit"])
    report = {
        "schema_version": 1,
        "method": "arbitrary changed-element order within the switch-skew window",
        "sample_count": sample_count,
        "transition_count": len(transitions),
        "maximum_sample_code_step": max(
            abs(transition["next_code"] - transition["previous_code"])
            for transition in transitions
        ),
        "observed_modulation_code_range": {
            "minimum": code_minimum,
            "maximum": code_maximum,
        },
        "switch_skew_target_s": SWITCH_SKEW_TARGET_S,
        "drive_resistance_ohm": drive_resistance_ohm,
        "control_load_f": control_load_f,
        "drive_time_constant_s": time_constant_s,
        "rc_peak_fraction": rc_peak_fraction,
        "maximum_tuning_gain_hz_per_v": maximum_tuning_gain,
        "frequency_error_limit_hz": nonidealities["total_frequency_error_limit_hz"],
        "frequency_error_before_glitch_hz": selected_nonideality[
            "conservative_total_error_hz"
        ],
        "frequency_margin_for_glitch_hz": frequency_margin_hz,
        "selected_thermometer_msb_bits": selected["thermometer_msb_bits"],
        "selected_binary_lsb_bits": selected["binary_lsb_bits"],
        "selected_switched_element_count": selected["switched_element_count"],
        "passed": selected["thermometer_msb_bits"] == 5,
        "summaries": summaries,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")
    if not report["passed"]:
        raise RuntimeError("DAC transition architecture changed from reviewed result")


if __name__ == "__main__":
    main()
