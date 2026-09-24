#!/usr/bin/env python3
"""Co-simulate and retune the GF180 PA with a low-pass output match."""

from __future__ import annotations

import json
import math
import subprocess
import tempfile
from pathlib import Path

from scripts.run_gf180_pa import (
    CGM_BURST_S,
    CORNERS,
    DESIGN_FILE,
    FREQUENCY_HZ,
    LOAD_OHM,
    MAXIMUM_LEVEL_ERROR_DB,
    MODEL_FILE,
    UNIT_NMOS_WIDTH_UM,
    VDD_V,
    average_supply_power,
    pa_device_lines,
    read_waveform,
    tone_rms,
)


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "analog" / "gf180_pa_match_tb.spice"
PA_REPORT = ROOT / "reports" / "gf180_pa.json"
REPORT = ROOT / "reports" / "gf180_pa_match.json"
TARGET_POWER_DBM = 0.0
INDUCTOR_Q = 10.0
INDUCTANCE_CANDIDATES_H = (4.5e-9, 5.0e-9, 5.5e-9, 6.0e-9, 6.5e-9)
CAPACITANCE_CANDIDATES_F = (0.5e-12, 0.6e-12, 0.7e-12, 0.8e-12, 0.9e-12)
SELECTION_MAXIMUM_POWER_ERROR_DB = 0.1
SELECTION_MINIMUM_CODE_HEADROOM = 8
SELECTION_MAXIMUM_BURST_ENERGY_J = 1e-6


def simulate_match(
    power_code: int,
    corner: str,
    temperature_c: int,
    inductance_h: float,
    capacitance_f: float,
) -> dict:
    devices, _, _ = pa_device_lines(power_code * UNIT_NMOS_WIDTH_UM)
    inductor_resistance_ohm = (
        2.0 * math.pi * FREQUENCY_HZ * inductance_h / INDUCTOR_Q
    )
    with tempfile.TemporaryDirectory(prefix="gf180-pa-match-") as temporary_dir:
        temporary = Path(temporary_dir)
        waveform = temporary / "waveform.txt"
        netlist = (
            TEMPLATE.read_text()
            .replace("@@DESIGN_FILE@@", DESIGN_FILE)
            .replace("@@MODEL_FILE@@", MODEL_FILE)
            .replace("@@CORNER@@", corner)
            .replace("@@TEMP_C@@", str(temperature_c))
            .replace("@@PA_DEVICES@@", devices)
            .replace("@@SHUNT_CAPACITANCE_F@@", f"{capacitance_f:.12g}")
            .replace("@@INDUCTOR_RESISTANCE_OHM@@", f"{inductor_resistance_ohm:.12g}")
            .replace("@@SERIES_INDUCTANCE_H@@", f"{inductance_h:.12g}")
            .replace("@@WAVEFORM_FILE@@", str(waveform))
        )
        path = temporary / "bench.spice"
        path.write_text(netlist)
        result = subprocess.run(
            ["ngspice", "-b", str(path)],
            cwd=temporary,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            output = result.stdout + result.stderr
            raise RuntimeError(f"GF180 matched PA simulation failed\n{output[-8000:]}")
        times_s, output_v, supply_current_a = read_waveform(waveform)
    tone_power_w = {
        harmonic: tone_rms(times_s, output_v, harmonic) ** 2 / LOAD_OHM
        for harmonic in (1, 2, 3)
    }
    supply_power_w = average_supply_power(times_s, supply_current_a)
    return {
        "power_code": power_code,
        "fundamental_output_power_dbm": 10.0
        * math.log10(tone_power_w[1] / 1e-3),
        "second_harmonic_output_power_dbm": 10.0
        * math.log10(tone_power_w[2] / 1e-3),
        "second_harmonic_dbc": 10.0
        * math.log10(tone_power_w[2] / tone_power_w[1]),
        "third_harmonic_output_power_dbm": 10.0
        * math.log10(tone_power_w[3] / 1e-3),
        "third_harmonic_dbc": 10.0
        * math.log10(tone_power_w[3] / tone_power_w[1]),
        "supply_power_w": supply_power_w,
        "drain_efficiency": tone_power_w[1] / supply_power_w,
        "energy_per_224us_burst_j": supply_power_w * CGM_BURST_S,
    }


def calibrate(
    corner: str,
    temperature_c: int,
    inductance_h: float,
    capacitance_f: float,
) -> dict:
    cache = {}

    def point(power_code: int) -> dict:
        if power_code not in cache:
            cache[power_code] = simulate_match(
                power_code,
                corner,
                temperature_c,
                inductance_h,
                capacitance_f,
            )
        return cache[power_code]

    low = 1
    high = 128
    while low <= high:
        middle = (low + high) // 2
        if point(middle)["fundamental_output_power_dbm"] < TARGET_POWER_DBM:
            low = middle + 1
        else:
            high = middle - 1
    candidate_codes = {max(1, min(128, code)) for code in (high, low)}
    return min(
        (point(code) for code in candidate_codes),
        key=lambda result: abs(
            result["fundamental_output_power_dbm"] - TARGET_POWER_DBM
        ),
    )


def main() -> None:
    raw_pa = json.loads(PA_REPORT.read_text())
    raw_worst_third_harmonic_dbc = raw_pa[
        "worst_selected_third_harmonic_dbc"
    ]
    candidates = []
    for inductance_h in INDUCTANCE_CANDIDATES_H:
        for capacitance_f in CAPACITANCE_CANDIDATES_F:
            corners = [
                {
                    "corner": corner,
                    "temperature_c": temperature_c,
                    **calibrate(
                        corner,
                        temperature_c,
                        inductance_h,
                        capacitance_f,
                    ),
                }
                for corner, temperature_c in CORNERS
            ]
            candidates.append(
                {
                    "series_inductance_h": inductance_h,
                    "shunt_capacitance_f": capacitance_f,
                    "inductor_series_resistance_ohm": 2.0
                    * math.pi
                    * FREQUENCY_HZ
                    * inductance_h
                    / INDUCTOR_Q,
                    "maximum_absolute_power_error_db": max(
                        abs(point["fundamental_output_power_dbm"] - TARGET_POWER_DBM)
                        for point in corners
                    ),
                    "worst_third_harmonic_dbc": max(
                        point["third_harmonic_dbc"] for point in corners
                    ),
                    "maximum_energy_per_224us_burst_j": max(
                        point["energy_per_224us_burst_j"] for point in corners
                    ),
                    "maximum_power_code": max(
                        point["power_code"] for point in corners
                    ),
                    "corners": corners,
                }
            )
    robust_candidates = [
        candidate
        for candidate in candidates
        if candidate["maximum_absolute_power_error_db"]
        <= SELECTION_MAXIMUM_POWER_ERROR_DB
        and candidate["maximum_power_code"]
        <= 128 - SELECTION_MINIMUM_CODE_HEADROOM
        and candidate["maximum_energy_per_224us_burst_j"]
        <= SELECTION_MAXIMUM_BURST_ENERGY_J
    ]
    if not robust_candidates:
        raise RuntimeError("no output-match candidate meets the selection screens")
    selected = min(
        robust_candidates,
        key=lambda candidate: (
            candidate["worst_third_harmonic_dbc"],
            candidate["maximum_energy_per_224us_burst_j"],
        ),
    )
    report = {
        "schema_version": 1,
        "purpose": "GF180 transistor PA and output-match co-simulation",
        "target_output_power_dbm": TARGET_POWER_DBM,
        "load_ohm": LOAD_OHM,
        "inductor_q_at_fundamental": INDUCTOR_Q,
        "selection_screens": {
            "maximum_power_error_db": SELECTION_MAXIMUM_POWER_ERROR_DB,
            "minimum_power_code_headroom": SELECTION_MINIMUM_CODE_HEADROOM,
            "maximum_energy_per_224us_burst_j": SELECTION_MAXIMUM_BURST_ENERGY_J,
        },
        "raw_pa_worst_third_harmonic_dbc": raw_worst_third_harmonic_dbc,
        "selected": selected,
        "minimum_third_harmonic_improvement_db": (
            raw_worst_third_harmonic_dbc
            - selected["worst_third_harmonic_dbc"]
        ),
        "calibration_passed": selected["maximum_absolute_power_error_db"]
        <= MAXIMUM_LEVEL_ERROR_DB,
        "accepted_for_next_stage": (
            selected["maximum_absolute_power_error_db"]
            <= SELECTION_MAXIMUM_POWER_ERROR_DB
            and selected["maximum_power_code"]
            <= 128 - SELECTION_MINIMUM_CODE_HEADROOM
            and selected["maximum_energy_per_224us_burst_j"]
            <= SELECTION_MAXIMUM_BURST_ENERGY_J
        ),
        "candidates": candidates,
        "limitations": [
            "The input driver and disabled PA slices are not modeled.",
            "The inductor is ideal except for fixed series resistance set by Q at 2.44 GHz.",
            "No passive PVT, self-resonance, package, antenna, stability, mismatch, or modulation is modeled.",
            "This is not regulatory, Bluetooth qualification, or tapeout signoff evidence.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")


if __name__ == "__main__":
    main()
