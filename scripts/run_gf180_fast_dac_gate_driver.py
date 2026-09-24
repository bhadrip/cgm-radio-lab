#!/usr/bin/env python3
"""Evaluate transistor complementary-gate drivers on the fast-DAC carry."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.run_gf180_fast_dac import VDD_V
from scripts.run_gf180_fast_dac_steered import (
    element_definitions,
    run,
)


ROOT = Path(__file__).resolve().parents[1]
TRANSITION_BUDGET = ROOT / "reports" / "lc_dco_dac_transition.json"
REPORT = ROOT / "reports" / "gf180_fast_dac_gate_driver.json"
CORNERS = (("typical", 25), ("ff", -40), ("ss", 125))
TOPOLOGIES = ("one_stage_output_two_stage_dummy", "three_stage_output_two_stage_dummy")
DRIVE_SCALES = (0.5, 1.0, 2.0)
LOGIC_EDGE_S = 100e-12
DRIVER_TRANSITION_EDGE_S = 100e-9
MEASUREMENT_WINDOW_S = 10e-9
BASE_NMOS_WIDTH_UM = 0.44
BASE_PMOS_WIDTH_UM = 0.88


def logic_source(name: str, node: str, initial: bool, final: bool, edge_s: float) -> str:
    initial_v = VDD_V if initial else 0.0
    final_v = VDD_V if final else 0.0
    if initial == final:
        return f"VLOGIC_{name} {node} 0 {initial_v:.12g}"
    return (
        f"VLOGIC_{name} {node} 0 PWL(0 {initial_v:.12g} "
        f"{edge_s:.12g} {initial_v:.12g} "
        f"{edge_s + LOGIC_EDGE_S:.12g} {final_v:.12g})"
    )


def inverter(name: str, output: str, input_: str, scale: float) -> list[str]:
    nmos_width_um = BASE_NMOS_WIDTH_UM * scale
    pmos_width_um = BASE_PMOS_WIDTH_UM * scale
    return [
        f"XDRV_P_{name} {output} {input_} vdd vdd pfet_03v3 "
        f"l=0.28u w={pmos_width_um:.12g}u nf=1",
        f"XDRV_N_{name} {output} {input_} 0 0 nfet_03v3 "
        f"l=0.28u w={nmos_width_um:.12g}u nf=1",
    ]


def driver_controls(topology: str, scale: float) -> str:
    lines = []
    for name, _, active_for_code in element_definitions():
        initial = active_for_code(63)
        final = active_for_code(64)
        if initial == final:
            output_level_v = 0.0 if initial else VDD_V
            dummy_level_v = VDD_V if initial else 0.0
            lines.append(f"VSTATIC_OUT_{name} ctrl_out_{name} 0 {output_level_v}")
            lines.append(
                f"VSTATIC_DUMMY_{name} ctrl_dummy_{name} 0 {dummy_level_v}"
            )
            continue
        delay_s = 0.0 if name.startswith("binary") else 750e-12
        input_node = f"logic_{name}"
        lines.append(
            logic_source(
                name,
                input_node,
                initial,
                final,
                DRIVER_TRANSITION_EDGE_S + delay_s,
            )
        )
        if topology == "one_stage_output_two_stage_dummy":
            lines.extend(inverter(name + "_1", f"ctrl_out_{name}", input_node, scale))
            lines.extend(
                inverter(
                    name + "_2",
                    f"ctrl_dummy_{name}",
                    f"ctrl_out_{name}",
                    scale,
                )
            )
        elif topology == "three_stage_output_two_stage_dummy":
            first_node = f"driver_first_{name}"
            lines.extend(inverter(name + "_1", first_node, input_node, scale))
            lines.extend(
                inverter(name + "_2", f"ctrl_dummy_{name}", first_node, scale)
            )
            lines.extend(
                inverter(
                    name + "_3",
                    f"ctrl_out_{name}",
                    f"ctrl_dummy_{name}",
                    scale,
                )
            )
        else:
            raise ValueError(f"unsupported driver topology: {topology}")
    return "\n".join(lines)


def measurements() -> str:
    return "\n".join(
        (
            ".measure tran initial_voltage_v AVG v(out) FROM=20n TO=80n",
            ".measure tran final_voltage_v AVG v(out) FROM=220n TO=280n",
            ".measure tran minimum_transition_voltage_v MIN v(out) "
            "FROM=100n TO=200n",
            ".measure tran maximum_transition_voltage_v MAX v(out) "
            "FROM=100n TO=200n",
            ".measure tran initial_supply_current_a AVG i(VDD) FROM=20n TO=80n",
            ".measure tran final_supply_current_a AVG i(VDD) FROM=220n TO=280n",
            ".measure tran transition_supply_current_a AVG i(VDD) "
            "FROM=95n TO=105n",
        )
    )


def characterize(
    topology: str,
    scale: float,
    corner: str,
    temperature_c: int,
    reference_scale: float = 1.0,
) -> dict:
    result = run(
        driver_controls(topology, scale),
        measurements(),
        10e-12,
        300e-9,
        corner,
        temperature_c,
        reference_scale,
    )
    endpoint_minimum_v = min(result["initial_voltage_v"], result["final_voltage_v"])
    endpoint_maximum_v = max(result["initial_voltage_v"], result["final_voltage_v"])
    undershoot_v = max(0.0, endpoint_minimum_v - result["minimum_transition_voltage_v"])
    overshoot_v = max(0.0, result["maximum_transition_voltage_v"] - endpoint_maximum_v)
    peak_glitch_v = max(undershoot_v, overshoot_v)
    budget = json.loads(TRANSITION_BUDGET.read_text())
    glitch_frequency_error_hz = peak_glitch_v * budget["maximum_tuning_gain_hz_per_v"]
    combined_frequency_error_hz = (
        budget["frequency_error_before_glitch_hz"] + glitch_frequency_error_hz
    )
    baseline_current_a = -0.5 * (
        result["initial_supply_current_a"] + result["final_supply_current_a"]
    )
    transition_current_a = -result["transition_supply_current_a"]
    excess_transition_energy_j = max(
        0.0,
        (transition_current_a - baseline_current_a)
        * VDD_V
        * MEASUREMENT_WINDOW_S,
    )
    return {
        "topology": topology,
        "drive_scale": scale,
        "corner": corner,
        "temperature_c": temperature_c,
        "reference_current_scale": reference_scale,
        "logic_edge_s": LOGIC_EDGE_S,
        "input_element_skew_s": 750e-12,
        "undershoot_v": undershoot_v,
        "overshoot_v": overshoot_v,
        "peak_glitch_v": peak_glitch_v,
        "glitch_frequency_error_hz": glitch_frequency_error_hz,
        "combined_frequency_error_hz": combined_frequency_error_hz,
        "excess_transition_energy_j": excess_transition_energy_j,
        "passed": combined_frequency_error_hz <= budget["frequency_error_limit_hz"],
    }


def main() -> None:
    variants = []
    for topology in TOPOLOGIES:
        for scale in DRIVE_SCALES:
            corners = [characterize(topology, scale, "typical", 25)]
            variants.append(
                {
                    "topology": topology,
                    "drive_scale": scale,
                    "passed_typical": corners[0]["passed"],
                    "passed_pvt": None,
                    "worst_combined_frequency_error_hz": max(
                        corner["combined_frequency_error_hz"] for corner in corners
                    ),
                    "worst_peak_glitch_v": max(
                        corner["peak_glitch_v"] for corner in corners
                    ),
                    "worst_excess_transition_energy_j": max(
                        corner["excess_transition_energy_j"] for corner in corners
                    ),
                    "corners": corners,
                }
            )
    typical_passing = [variant for variant in variants if variant["passed_typical"]]
    ranked = sorted(
        typical_passing,
        key=lambda variant: (
            variant["worst_excess_transition_energy_j"],
            variant["worst_combined_frequency_error_hz"],
        ),
    )
    selected = None
    for variant in ranked:
        extra_corners = [
            characterize(
                variant["topology"],
                variant["drive_scale"],
                corner,
                temperature_c,
            )
            for corner, temperature_c in CORNERS[1:]
        ]
        variant["corners"].extend(extra_corners)
        variant["passed_pvt"] = all(
            corner["passed"] for corner in variant["corners"]
        )
        variant["worst_combined_frequency_error_hz"] = max(
            corner["combined_frequency_error_hz"] for corner in variant["corners"]
        )
        variant["worst_peak_glitch_v"] = max(
            corner["peak_glitch_v"] for corner in variant["corners"]
        )
        variant["worst_excess_transition_energy_j"] = max(
            corner["excess_transition_energy_j"] for corner in variant["corners"]
        )
        if variant["passed_pvt"]:
            selected = variant
            break
    report = {
        "schema_version": 1,
        "purpose": "transistor complementary-driver gate for the 6+1 fast DAC",
        "frequency_error_limit_hz": json.loads(TRANSITION_BUDGET.read_text())[
            "frequency_error_limit_hz"
        ],
        "selected_topology": selected["topology"] if selected else None,
        "selected_drive_scale": selected["drive_scale"] if selected else None,
        "passed": selected is not None,
        "variants": variants,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")
    if not report["passed"]:
        raise RuntimeError("no transistor complementary-driver variant passed")


if __name__ == "__main__":
    main()
