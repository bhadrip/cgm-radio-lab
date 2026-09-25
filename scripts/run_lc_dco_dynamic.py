#!/usr/bin/env python3
"""Drive the GF180 LC-DCO with a short 16 MHz Gaussian control sequence."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from model.dco import ble_channel_center_hz
from model.lc_dco_dac import VoltageDac
from model.lc_dco_modulation import control_waveform


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "analog" / "gf180_lc_dco_dynamic_tb.spice"
STATIC_SWEEP = ROOT / "reports" / "lc_dco_sweep.json"
LOCAL_CALIBRATION = ROOT / "reports" / "lc_dco_local_calibration.json"
REPORT = ROOT / "reports" / "lc_dco_dynamic.json"
MODEL_FILE = os.environ.get(
    "GF180_MODEL_FILE",
    "/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice",
)
DESIGN_FILE = os.environ.get(
    "GF180_DESIGN_FILE",
    "/foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice",
)
BITS = (0, 0, 0, 0, 1, 0, 1)
SAMPLE_PERIOD_S = 1 / 16_000_000
MEASURE_START_SAMPLE = 4 * 16
MAXIMUM_ERROR_LIMIT_HZ = 50_000
MEAN_ERROR_LIMIT_HZ = 10_000
DAC_BITS = int(os.environ.get("LC_DCO_DAC_BITS", "12"))
FREQUENCY = re.compile(r"^freq_(\d+)\s*=\s*([-+0-9.eE]+)", re.MULTILINE)
SCALAR = re.compile(
    r"^(differential_vpp|supply_current_a|power_w)\s*=\s*([-+0-9.eE]+)",
    re.MULTILINE,
)


def coarse_instances(count: int) -> str:
    lines = []
    for index in range(count):
        lines.extend(
            (
                f"XCOARSEP{index} outp 0 cap_mim_1f5_m4m5_noshield "
                "c_width=5u c_length=5u",
                f"XCOARSEN{index} outn 0 cap_mim_1f5_m4m5_noshield "
                "c_width=5u c_length=5u",
            )
        )
    return "\n".join(lines)


def control_pwl(voltages: list[float]) -> str:
    transition_s = 1e-9
    points = [(0.0, voltages[0])]
    for index, voltage in enumerate(voltages[1:], start=1):
        edge_s = index * SAMPLE_PERIOD_S
        points.append((edge_s - transition_s, voltages[index - 1]))
        points.append((edge_s, voltage))
    stop_s = len(voltages) * SAMPLE_PERIOD_S
    points.append((stop_s, voltages[-1]))
    return " ".join(f"{time_s:.12g} {voltage:.12g}" for time_s, voltage in points)


def measurements(sample_count: int) -> str:
    lines = []
    for sample in range(MEASURE_START_SAMPLE, sample_count):
        delay_s = sample * SAMPLE_PERIOD_S + 5e-9
        lines.extend(
            (
                f".measure tran span_{sample:03d} TRIG v(diff) VAL=0 "
                f"RISE=1 TD={delay_s:.12g}",
                f"+ TARG v(diff) VAL=0 RISE=101 TD={delay_s:.12g}",
                f".measure tran freq_{sample:03d} PARAM='100/span_{sample:03d}'",
            )
        )
    return "\n".join(lines)


def main() -> None:
    static_points = json.loads(STATIC_SWEEP.read_text())["points"]
    static_points += json.loads(LOCAL_CALIBRATION.read_text())["points"]
    calibration, offsets_hz, ideal_voltages = control_waveform(
        static_points, "typical", 37, BITS
    )
    dac = VoltageDac(DAC_BITS)
    codes = [dac.code_for_voltage(voltage) for voltage in ideal_voltages]
    voltages = [dac.voltage_for_code(code) for code in codes]
    stop_s = len(voltages) * SAMPLE_PERIOD_S
    netlist = (
        TEMPLATE.read_text()
        .replace("@@DESIGN_FILE@@", DESIGN_FILE)
        .replace("@@MODEL_FILE@@", MODEL_FILE)
        .replace("@@CONTROL_PWL@@", control_pwl(voltages))
        .replace("@@COARSE_CAPS@@", coarse_instances(calibration.coarse_code))
        .replace("@@MEASUREMENTS@@", measurements(len(voltages)))
        .replace("@@STOP_TIME@@", f"{stop_s:.12g}")
    )
    with tempfile.TemporaryDirectory(prefix="lc-dco-dynamic-") as temporary_dir:
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
    measured = {int(index): float(value) for index, value in FREQUENCY.findall(output)}
    scalars = {name: float(value) for name, value in SCALAR.findall(output)}
    expected_samples = len(voltages) - MEASURE_START_SAMPLE
    if result.returncode or len(measured) != expected_samples or len(scalars) != 3:
        raise RuntimeError(f"dynamic ngspice run failed\n{output[-8000:]}")
    center_hz = ble_channel_center_hz(37)
    samples = [
        {
            "sample": sample,
            "time_s": sample * SAMPLE_PERIOD_S,
            "requested_frequency_hz": center_hz + offsets_hz[sample],
            "measured_frequency_hz": measured[sample],
            "error_hz": measured[sample] - (center_hz + offsets_hz[sample]),
            "ideal_control_voltage_v": ideal_voltages[sample],
            "dac_code": codes[sample],
            "control_voltage_v": voltages[sample],
        }
        for sample in range(MEASURE_START_SAMPLE, len(voltages))
    ]
    errors = [sample["error_hz"] for sample in samples]
    mean_error_hz = sum(errors) / len(errors)
    maximum_error_hz = max(abs(error) for error in errors)
    passed = (
        maximum_error_hz <= MAXIMUM_ERROR_LIMIT_HZ
        and abs(mean_error_hz) <= MEAN_ERROR_LIMIT_HZ
    )
    report = {
        "schema_version": 1,
        "corner": "typical",
        "channel": 37,
        "coarse_code": calibration.coarse_code,
        "bits": list(BITS),
        "sample_rate_hz": 16_000_000,
        "dac_bits": dac.bits,
        "dac_lsb_v": dac.lsb_v,
        "measured_samples": len(samples),
        "mean_frequency_error_hz": mean_error_hz,
        "maximum_absolute_frequency_error_hz": maximum_error_hz,
        "mean_frequency_error_limit_hz": MEAN_ERROR_LIMIT_HZ,
        "maximum_absolute_frequency_error_limit_hz": MAXIMUM_ERROR_LIMIT_HZ,
        "passed": passed,
        "differential_vpp": scalars["differential_vpp"],
        "supply_current_a": -scalars["supply_current_a"],
        "power_w": scalars["power_w"],
        "samples": samples,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")
    if not passed:
        raise RuntimeError(
            f"dynamic frequency error failed limits: mean={mean_error_hz} Hz, "
            f"maximum={maximum_error_hz} Hz"
        )


if __name__ == "__main__":
    main()
