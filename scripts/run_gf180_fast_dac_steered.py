#!/usr/bin/env python3
"""Characterize a nominal GF180 continuously steered 6+1 fast DAC."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

from scripts.run_gf180_fast_dac import (
    CODE_PERIOD_S,
    DAC_BITS,
    DESIGN_FILE,
    MODEL_FILE,
    SWEEP_TRANSITION_S,
    TRANSITION_EDGE_S,
    TRANSITION_SWITCH_S,
    UNIT_CURRENT_A,
    VDD_V,
    level,
    sweep_measurements,
)


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "analog" / "gf180_fast_dac_steered_tb.spice"
TRANSITION_BUDGET = ROOT / "reports" / "lc_dco_dac_transition.json"
REPORT = ROOT / "reports" / "gf180_fast_dac_steered.json"
SWITCH_WIDTH_PER_WEIGHT_UM = 0.22
CHARGE_COMPENSATION_WIDTH_RATIO = 0.5
BINARY_BITS = 1
MEASURE = re.compile(
    r"^(code_\d+_(?:voltage_v|supply_current_a)|initial_voltage_v|"
    r"final_voltage_v|minimum_transition_voltage_v|glitch_below_endpoints_v)"
    r"\s*=\s*([-+0-9.eE]+)",
    re.MULTILINE,
)


def element_definitions():
    elements = []
    thermometer_count = (1 << (DAC_BITS - BINARY_BITS)) - 1
    for index in range(thermometer_count):
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
        switch_width_um = SWITCH_WIDTH_PER_WEIGHT_UM * weight
        compensation_width_um = max(
            0.22, switch_width_um * CHARGE_COMPENSATION_WIDTH_RATIO
        )
        lines.extend(
            (
                f"XCUR_{name} ncur_{name} vbp vdd vdd pfet_03v3 "
                f"l=1u w={weight}u nf={weight}",
                f"XSW_OUT_{name} out ctrl_out_{name} ncur_{name} vdd "
                f"pfet_03v3 l=0.28u w={switch_width_um:.12g}u nf=1",
                f"XSW_DUMMY_{name} dummy ctrl_dummy_{name} ncur_{name} vdd "
                f"pfet_03v3 l=0.28u w={switch_width_um:.12g}u nf=1",
                f"XCOMP_{name} out ctrl_dummy_{name} out vdd pfet_03v3 "
                f"l=0.28u w={compensation_width_um:.12g}u nf=1",
            )
        )
    return "\n".join(lines)


def pwl_source(name: str, node: str, states: list[bool]) -> str:
    points = [(0.0, level(states[0]))]
    previous = states[0]
    for code, current in enumerate(states[1:], start=1):
        if current == previous:
            continue
        edge_s = code * CODE_PERIOD_S
        points.append((edge_s - SWEEP_TRANSITION_S, level(previous)))
        points.append((edge_s, level(current)))
        previous = current
    rendered = " ".join(
        f"{time_s:.12g} {voltage_v:.12g}" for time_s, voltage_v in points
    )
    return f"VCTRL_{name} {node} 0 PWL({rendered})"


def sweep_controls() -> str:
    lines = []
    for name, _, active_for_code in element_definitions():
        output_states = [active_for_code(code) for code in range(1 << DAC_BITS)]
        lines.append(
            pwl_source(name + "_out", "ctrl_out_" + name, output_states)
        )
        lines.append(
            pwl_source(
                name + "_dummy",
                "ctrl_dummy_" + name,
                [not state for state in output_states],
            )
        )
    return "\n".join(lines)


def transition_source(
    source_name: str,
    node: str,
    initial: bool,
    final: bool,
    edge_s: float,
) -> str:
    if initial == final:
        return f"VCTRL_{source_name} {node} 0 {level(initial):.12g}"
    return (
        f"VCTRL_{source_name} {node} 0 PWL(0 {level(initial):.12g} "
        f"{edge_s:.12g} {level(initial):.12g} "
        f"{edge_s + TRANSITION_SWITCH_S:.12g} {level(final):.12g})"
    )


def transition_controls() -> str:
    lines = []
    for name, _, active_for_code in element_definitions():
        initial = active_for_code(63)
        final = active_for_code(64)
        delay_s = 0.0 if name.startswith("binary") else 750e-12
        edge_s = TRANSITION_EDGE_S + delay_s
        lines.append(
            transition_source(
                name + "_out", "ctrl_out_" + name, initial, final, edge_s
            )
        )
        lines.append(
            transition_source(
                name + "_dummy",
                "ctrl_dummy_" + name,
                not initial,
                not final,
                edge_s,
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
            ".measure tran glitch_below_endpoints_v "
            "PARAM='initial_voltage_v-minimum_transition_voltage_v'",
        )
    )


def run(
    control_sources: str,
    measurements: str,
    time_step_s: float,
    stop_time_s: float,
    corner: str,
    temperature_c: int,
) -> dict[str, float]:
    netlist = (
        TEMPLATE.read_text()
        .replace("@@DESIGN_FILE@@", DESIGN_FILE)
        .replace("@@MODEL_FILE@@", MODEL_FILE)
        .replace("@@CORNER@@", corner)
        .replace("@@TEMP_C@@", str(temperature_c))
        .replace("@@CONTROL_SOURCES@@", control_sources)
        .replace("@@DAC_CELLS@@", dac_cells())
        .replace("@@TIME_STEP@@", f"{time_step_s:.12g}")
        .replace("@@STOP_TIME@@", f"{stop_time_s:.12g}")
        .replace("@@MEASUREMENTS@@", measurements)
    )
    with tempfile.TemporaryDirectory(prefix="gf180-fast-dac-steered-") as temporary_dir:
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
        raise RuntimeError(f"steered fast-DAC ngspice run failed\n{output[-8000:]}")
    return values


def characterize(corner: str, temperature_c: int) -> dict:
    sweep = run(
        sweep_controls(),
        sweep_measurements(),
        1e-9,
        (1 << DAC_BITS) * CODE_PERIOD_S,
        corner,
        temperature_c,
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
        transition_controls(),
        transition_measurements(),
        10e-12,
        1.5e-6,
        corner,
        temperature_c,
    )
    glitch_v = max(0.0, transition["glitch_below_endpoints_v"])
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
    report = {
        "schema_version": 1,
        "corner": corner,
        "temperature_c": temperature_c,
        "architecture": "continuously steered matched output and dummy loads",
        "dac_bits": DAC_BITS,
        "thermometer_msb_bits": DAC_BITS - BINARY_BITS,
        "binary_lsb_bits": BINARY_BITS,
        "unit_current_target_a": UNIT_CURRENT_A,
        "switch_width_per_weight_um": SWITCH_WIDTH_PER_WEIGHT_UM,
        "charge_compensation_width_ratio": CHARGE_COMPENSATION_WIDTH_RATIO,
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
        "minimum_supply_current_a": min(supply_currents_a),
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
        "accepted_for_next_stage": static_linearity_passed and transition_passed,
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
    return report


def main() -> None:
    report = characterize("typical", 25)
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")
    if not report["accepted_for_next_stage"]:
        raise RuntimeError("steered GF180 fast DAC failed its reviewed limits")


if __name__ == "__main__":
    main()
