#!/usr/bin/env python3
"""Characterize a nominal GF180 5+2 switched-current fast DAC."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "analog" / "gf180_fast_dac_tb.spice"
TRANSITION_BUDGET = ROOT / "reports" / "lc_dco_dac_transition.json"
REPORT = ROOT / "reports" / "gf180_fast_dac.json"
MODEL_FILE = os.environ.get(
    "GF180_MODEL_FILE",
    "/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice",
)
DESIGN_FILE = os.environ.get(
    "GF180_DESIGN_FILE",
    "/foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice",
)
VDD_V = 1.8
DAC_BITS = 7
THERMOMETER_BITS = 5
BINARY_BITS = 2
THERMOMETER_COUNT = (1 << THERMOMETER_BITS) - 1
LSB_V = 0.016 / ((1 << DAC_BITS) - 1)
UNIT_CURRENT_A = LSB_V / 1_000
CODE_PERIOD_S = 500e-9
SWEEP_TRANSITION_S = 1e-9
TRANSITION_SWITCH_S = 10e-12
TRANSITION_EDGE_S = 500e-9
MEASURE = re.compile(
    r"^(code_\d+_(?:voltage_v|supply_current_a)|initial_voltage_v|"
    r"final_voltage_v|minimum_transition_voltage_v)\s*=\s*([-+0-9.eE]+)",
    re.MULTILINE,
)


def element_definitions() -> list[tuple[str, int, Callable[[int], bool]]]:
    elements = []
    for index in range(THERMOMETER_COUNT):
        elements.append(
            (
                f"therm_{index:02d}",
                1 << BINARY_BITS,
                lambda code, i=index: (code >> BINARY_BITS) > i,
            )
        )
    for bit in range(BINARY_BITS):
        elements.append(
            (
                f"binary_{bit}",
                1 << bit,
                lambda code, b=bit: bool((code >> b) & 1),
            )
        )
    return elements


def dac_cells() -> str:
    lines = []
    for name, weight, _ in element_definitions():
        lines.extend(
            (
                f"XCUR_{name} ncur_{name} vbp vdd vdd pfet_03v3 "
                f"l=1u w={weight}u nf={weight}",
                f"XSW_{name} out ctrl_{name} ncur_{name} vdd pfet_03v3 "
                f"l=0.28u w={2 * weight}u nf={2 * weight}",
                f"RKEEP_{name} ncur_{name} vdd 1G",
            )
        )
    return "\n".join(lines)


def level(active: bool) -> float:
    return 0.0 if active else VDD_V


def sweep_controls() -> str:
    lines = []
    for name, _, active_for_code in element_definitions():
        points = [(0.0, level(active_for_code(0)))]
        previous = active_for_code(0)
        for code in range(1, 1 << DAC_BITS):
            current = active_for_code(code)
            if current == previous:
                continue
            edge_s = code * CODE_PERIOD_S
            points.append((edge_s - SWEEP_TRANSITION_S, level(previous)))
            points.append((edge_s, level(current)))
            previous = current
        rendered = " ".join(
            f"{time_s:.12g} {voltage_v:.12g}" for time_s, voltage_v in points
        )
        lines.append(f"VCTRL_{name} ctrl_{name} 0 PWL({rendered})")
    return "\n".join(lines)


def transition_controls() -> str:
    lines = []
    initial_code = 63
    final_code = 64
    for name, _, active_for_code in element_definitions():
        initial = active_for_code(initial_code)
        final = active_for_code(final_code)
        if initial == final:
            lines.append(f"VCTRL_{name} ctrl_{name} 0 {level(initial):.12g}")
            continue
        delay_s = 0.0 if name.startswith("binary") else 750e-12
        edge_s = TRANSITION_EDGE_S + delay_s
        lines.append(
            f"VCTRL_{name} ctrl_{name} 0 PWL(0 {level(initial):.12g} "
            f"{edge_s:.12g} {level(initial):.12g} "
            f"{edge_s + TRANSITION_SWITCH_S:.12g} {level(final):.12g})"
        )
    return "\n".join(lines)


def sweep_measurements() -> str:
    lines = []
    for code in range(1 << DAC_BITS):
        end_s = (code + 1) * CODE_PERIOD_S
        start_s = end_s - 100e-9
        lines.extend(
            (
                f".measure tran code_{code:03d}_voltage_v AVG v(out) "
                f"FROM={start_s:.12g} TO={end_s - 10e-9:.12g}",
                f".measure tran code_{code:03d}_supply_current_a AVG i(VDD) "
                f"FROM={start_s:.12g} TO={end_s - 10e-9:.12g}",
            )
        )
    return "\n".join(lines)


def transition_measurements() -> str:
    return "\n".join(
        (
            ".measure tran initial_voltage_v AVG v(out) FROM=100n TO=400n",
            ".measure tran final_voltage_v AVG v(out) FROM=1u TO=1.4u",
            ".measure tran minimum_transition_voltage_v MIN v(out) "
            "FROM=500n TO=600n",
        )
    )


def run(
    control_sources: str,
    measurements: str,
    time_step_s: float,
    stop_time_s: float,
) -> dict[str, float]:
    netlist = (
        TEMPLATE.read_text()
        .replace("@@DESIGN_FILE@@", DESIGN_FILE)
        .replace("@@MODEL_FILE@@", MODEL_FILE)
        .replace("@@CONTROL_SOURCES@@", control_sources)
        .replace("@@DAC_CELLS@@", dac_cells())
        .replace("@@TIME_STEP@@", f"{time_step_s:.12g}")
        .replace("@@STOP_TIME@@", f"{stop_time_s:.12g}")
        .replace("@@MEASUREMENTS@@", measurements)
    )
    with tempfile.TemporaryDirectory(prefix="gf180-fast-dac-") as temporary_dir:
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
    values = {name: float(value) for name, value in MEASURE.findall(output)}
    if result.returncode:
        raise RuntimeError(f"fast-DAC ngspice run failed\n{output[-8000:]}")
    return values


def main() -> None:
    sweep = run(
        sweep_controls(),
        sweep_measurements(),
        1e-9,
        (1 << DAC_BITS) * CODE_PERIOD_S,
    )
    voltages_v = [sweep[f"code_{code:03d}_voltage_v"] for code in range(128)]
    supply_currents_a = [
        -sweep[f"code_{code:03d}_supply_current_a"] for code in range(128)
    ]
    measured_lsb_v = (voltages_v[-1] - voltages_v[0]) / 127
    steps_v = [high - low for low, high in zip(voltages_v, voltages_v[1:])]
    dnl_lsb = [step / measured_lsb_v - 1 for step in steps_v]
    inl_lsb = [
        (voltage_v - (voltages_v[0] + code * measured_lsb_v)) / measured_lsb_v
        for code, voltage_v in enumerate(voltages_v)
    ]
    transition = run(
        transition_controls(), transition_measurements(), 10e-12, 1.5e-6
    )
    endpoint_minimum_v = min(
        transition["initial_voltage_v"], transition["final_voltage_v"]
    )
    glitch_v = max(
        0.0, endpoint_minimum_v - transition["minimum_transition_voltage_v"]
    )
    transition_budget = json.loads(TRANSITION_BUDGET.read_text())
    glitch_error_hz = glitch_v * transition_budget["maximum_tuning_gain_hz_per_v"]
    combined_error_hz = (
        transition_budget["frequency_error_before_glitch_hz"] + glitch_error_hz
    )
    static_linearity_passed = (
        all(step > 0 for step in steps_v)
        and max(abs(value) for value in inl_lsb) <= 0.5
        and max(abs(value) for value in dnl_lsb) <= 0.5
    )
    transition_passed = (
        combined_error_hz <= transition_budget["frequency_error_limit_hz"]
    )
    accepted_for_implementation = static_linearity_passed and transition_passed
    report = {
        "schema_version": 1,
        "corner": "typical",
        "temperature_c": 25,
        "architecture": (
            "31 thermometer elements of weight 4 plus binary weights 1 and 2"
        ),
        "dac_bits": DAC_BITS,
        "unit_current_target_a": UNIT_CURRENT_A,
        "output_resistance_ohm": 1_000,
        "control_load_f": 10e-12,
        "target_output_range_v": 0.016,
        "minimum_output_voltage_v": min(voltages_v),
        "maximum_output_voltage_v": max(voltages_v),
        "output_range_v": voltages_v[-1] - voltages_v[0],
        "range_gain_error_fraction": (voltages_v[-1] - voltages_v[0]) / 0.016
        - 1,
        "measured_lsb_v": measured_lsb_v,
        "maximum_absolute_inl_lsb": max(abs(value) for value in inl_lsb),
        "minimum_dnl_lsb": min(dnl_lsb),
        "maximum_dnl_lsb": max(dnl_lsb),
        "monotonic": all(step > 0 for step in steps_v),
        "static_linearity_passed": static_linearity_passed,
        "maximum_supply_current_a": max(supply_currents_a),
        "maximum_static_power_w": VDD_V * max(supply_currents_a),
        "transition": {
            "previous_code": 63,
            "next_code": 64,
            "switch_skew_s": 750e-12,
            **transition,
            "glitch_below_endpoints_v": glitch_v,
            "glitch_frequency_error_hz": glitch_error_hz,
            "combined_frequency_error_hz": combined_error_hz,
        },
        "frequency_error_limit_hz": transition_budget["frequency_error_limit_hz"],
        "transition_passed": transition_passed,
        "accepted_for_implementation": accepted_for_implementation,
        "codes": [
            {
                "code": code,
                "output_voltage_v": voltage_v,
                "supply_current_a": supply_current_a,
                "inl_lsb": inl_lsb[code],
            }
            for code, (voltage_v, supply_current_a) in enumerate(
                zip(voltages_v, supply_currents_a)
            )
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")
    reviewed_result = static_linearity_passed and not transition_passed
    if not reviewed_result:
        raise RuntimeError("nominal GF180 fast-DAC decision changed")


if __name__ == "__main__":
    main()
