#!/usr/bin/env python3
"""Size and screen a first 150-to-50-ohm low-pass PA L-match."""

from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "pa_match_screen.json"
FREQUENCY_HZ = 2.44e9
SOURCE_RESISTANCE_OHM = 150.0
LOAD_RESISTANCE_OHM = 50.0
INDUCTOR_Q_CANDIDATES = (5.0, 8.0, 10.0, 15.0, 20.0, 30.0)
SCREENING_INDUCTOR_Q = 10.0


def component_values() -> tuple[float, float]:
    quality_factor = math.sqrt(
        SOURCE_RESISTANCE_OHM / LOAD_RESISTANCE_OHM - 1.0
    )
    angular_frequency = 2.0 * math.pi * FREQUENCY_HZ
    series_inductance_h = (
        quality_factor * LOAD_RESISTANCE_OHM / angular_frequency
    )
    shunt_capacitance_f = quality_factor / (
        angular_frequency * SOURCE_RESISTANCE_OHM
    )
    return series_inductance_h, shunt_capacitance_f


def network_point(
    frequency_hz: float, inductor_q: float | None
) -> dict[str, float]:
    series_inductance_h, shunt_capacitance_f = component_values()
    angular_frequency = 2.0 * math.pi * frequency_hz
    inductor_resistance_ohm = (
        0.0
        if inductor_q is None
        else angular_frequency * series_inductance_h / inductor_q
    )
    series_branch_ohm = complex(
        LOAD_RESISTANCE_OHM + inductor_resistance_ohm,
        angular_frequency * series_inductance_h,
    )
    shunt_capacitor_ohm = 1.0 / (
        1j * angular_frequency * shunt_capacitance_f
    )
    input_impedance_ohm = 1.0 / (
        1.0 / series_branch_ohm + 1.0 / shunt_capacitor_ohm
    )
    input_voltage_v_rms = input_impedance_ohm / (
        SOURCE_RESISTANCE_OHM + input_impedance_ohm
    )
    load_current_a_rms = input_voltage_v_rms / series_branch_ohm
    load_power_w = abs(load_current_a_rms) ** 2 * LOAD_RESISTANCE_OHM
    available_source_power_w = 1.0 / (4.0 * SOURCE_RESISTANCE_OHM)
    return {
        "frequency_hz": frequency_hz,
        "input_resistance_ohm": input_impedance_ohm.real,
        "input_reactance_ohm": input_impedance_ohm.imag,
        "inductor_series_resistance_ohm": inductor_resistance_ohm,
        "transducer_gain_db": 10.0
        * math.log10(load_power_w / available_source_power_w),
    }


def main() -> None:
    series_inductance_h, shunt_capacitance_f = component_values()
    ideal = network_point(FREQUENCY_HZ, None)
    sweeps = []
    for inductor_q in INDUCTOR_Q_CANDIDATES:
        fundamental = network_point(FREQUENCY_HZ, inductor_q)
        second = network_point(2.0 * FREQUENCY_HZ, inductor_q)
        third = network_point(3.0 * FREQUENCY_HZ, inductor_q)
        sweeps.append(
            {
                "inductor_q": inductor_q,
                "fundamental_insertion_loss_db": -fundamental[
                    "transducer_gain_db"
                ],
                "second_harmonic_rejection_relative_to_fundamental_db": (
                    fundamental["transducer_gain_db"]
                    - second["transducer_gain_db"]
                ),
                "third_harmonic_rejection_relative_to_fundamental_db": (
                    fundamental["transducer_gain_db"]
                    - third["transducer_gain_db"]
                ),
                "input_resistance_ohm": fundamental["input_resistance_ohm"],
                "input_reactance_ohm": fundamental["input_reactance_ohm"],
                "inductor_series_resistance_ohm": fundamental[
                    "inductor_series_resistance_ohm"
                ],
            }
        )
    selected = next(
        point
        for point in sweeps
        if point["inductor_q"] == SCREENING_INDUCTOR_Q
    )
    report = {
        "schema_version": 1,
        "purpose": "linear first-pass PA output-network screen",
        "status": "candidate_only",
        "frequency_hz": FREQUENCY_HZ,
        "source_resistance_ohm": SOURCE_RESISTANCE_OHM,
        "load_resistance_ohm": LOAD_RESISTANCE_OHM,
        "topology": "shunt capacitor at PA, then series inductor to 50 ohms",
        "series_inductance_h": series_inductance_h,
        "shunt_capacitance_f": shunt_capacitance_f,
        "ideal_input_resistance_ohm": ideal["input_resistance_ohm"],
        "ideal_input_reactance_ohm": ideal["input_reactance_ohm"],
        "screening_inductor_q": SCREENING_INDUCTOR_Q,
        "screening_result": selected,
        "q_sweep": sweeps,
        "limitations": [
            "The nonlinear PA is replaced by a 150 ohm Thevenin source.",
            "Only inductor loss is modeled; capacitor and interconnect are ideal.",
            "No device stress, stability, package, antenna, or modulation is modeled.",
            "The component values are not tapeout-ready layout values.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")


if __name__ == "__main__":
    main()
