"""Map BLE frequency requests onto the measured coarse/fine LC-DCO controls."""

from __future__ import annotations

import bisect
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from model.dco import ble_channel_center_hz
from model.gfsk import DEVIATION_HZ, SAMPLE_RATE_HZ, frequency_words


@dataclass(frozen=True)
class ChannelCalibration:
    corner: str
    channel: int
    coarse_code: int
    minimum_frequency_hz: float
    maximum_frequency_hz: float
    worst_case_margin_hz: float


def _code_points(
    points: Iterable[Mapping[str, object]],
    corner: str,
    coarse_code: int,
    channel: int | None = None,
    prefer_local: bool = False,
) -> list[Mapping[str, object]]:
    matching = [
        point
        for point in points
        if point["corner"] == corner
        and point["coarse_code"] == coarse_code
        and point["sustained_oscillation"]
    ]
    if prefer_local and channel is not None:
        local = [point for point in matching if point.get("channel") == channel]
        if local:
            broad = [point for point in matching if point.get("channel") is None]
            local_min = min(float(point["frequency_hz"]) for point in local)
            local_max = max(float(point["frequency_hz"]) for point in local)
            below = [
                point for point in broad if float(point["frequency_hz"]) < local_min
            ]
            above = [
                point for point in broad if float(point["frequency_hz"]) > local_max
            ]
            matching = [*local]
            if below:
                matching.append(max(below, key=lambda point: float(point["frequency_hz"])))
            if above:
                matching.append(min(above, key=lambda point: float(point["frequency_hz"])))
    return sorted(matching, key=lambda point: float(point["frequency_hz"]))


def calibrate_channel(
    points: Sequence[Mapping[str, object]],
    corner: str,
    channel: int,
    deviation_hz: int = DEVIATION_HZ,
) -> ChannelCalibration:
    """Choose one coarse code with maximum symmetric modulation margin."""
    center_hz = ble_channel_center_hz(channel)
    codes = sorted(
        {
            int(point["coarse_code"])
            for point in points
            if point["corner"] == corner
        }
    )
    candidates = []
    for coarse_code in codes:
        code_points = _code_points(points, corner, coarse_code)
        if not code_points:
            continue
        minimum_hz = float(code_points[0]["frequency_hz"])
        maximum_hz = float(code_points[-1]["frequency_hz"])
        low_target = center_hz - deviation_hz
        high_target = center_hz + deviation_hz
        if minimum_hz <= low_target and maximum_hz >= high_target:
            margin_hz = min(low_target - minimum_hz, maximum_hz - high_target)
            candidates.append((margin_hz, coarse_code, minimum_hz, maximum_hz))
    if not candidates:
        raise ValueError(f"no coarse code covers channel {channel} at {corner}")
    margin_hz, coarse_code, minimum_hz, maximum_hz = max(candidates)
    return ChannelCalibration(
        corner=corner,
        channel=channel,
        coarse_code=coarse_code,
        minimum_frequency_hz=minimum_hz,
        maximum_frequency_hz=maximum_hz,
        worst_case_margin_hz=margin_hz,
    )


def control_voltage_for_frequency(
    points: Sequence[Mapping[str, object]],
    calibration: ChannelCalibration,
    target_frequency_hz: float,
) -> float:
    """Piecewise-linearly invert the measured static tuning curve."""
    curve = _code_points(
        points,
        calibration.corner,
        calibration.coarse_code,
        calibration.channel,
        prefer_local=True,
    )
    frequencies = [float(point["frequency_hz"]) for point in curve]
    if not frequencies[0] <= target_frequency_hz <= frequencies[-1]:
        raise ValueError("target frequency is outside the calibrated code range")
    upper = bisect.bisect_left(frequencies, target_frequency_hz)
    if upper == 0:
        return float(curve[0]["control_voltage_v"])
    if upper == len(curve):
        return float(curve[-1]["control_voltage_v"])
    low = curve[upper - 1]
    high = curve[upper]
    low_frequency = float(low["frequency_hz"])
    high_frequency = float(high["frequency_hz"])
    fraction = (target_frequency_hz - low_frequency) / (
        high_frequency - low_frequency
    )
    low_voltage = float(low["control_voltage_v"])
    high_voltage = float(high["control_voltage_v"])
    return low_voltage + fraction * (high_voltage - low_voltage)


def frequency_for_control_voltage(
    points: Sequence[Mapping[str, object]],
    calibration: ChannelCalibration,
    control_voltage_v: float,
) -> float:
    """Piecewise-linearly evaluate the measured static tuning curve."""
    curve = sorted(
        _code_points(
            points,
            calibration.corner,
            calibration.coarse_code,
            calibration.channel,
            prefer_local=True,
        ),
        key=lambda point: float(point["control_voltage_v"]),
    )
    voltages = [float(point["control_voltage_v"]) for point in curve]
    if not voltages[0] <= control_voltage_v <= voltages[-1]:
        raise ValueError("control voltage is outside the measured range")
    upper = bisect.bisect_left(voltages, control_voltage_v)
    if upper == 0:
        return float(curve[0]["frequency_hz"])
    if upper == len(curve):
        return float(curve[-1]["frequency_hz"])
    low = curve[upper - 1]
    high = curve[upper]
    low_voltage = float(low["control_voltage_v"])
    high_voltage = float(high["control_voltage_v"])
    fraction = (control_voltage_v - low_voltage) / (high_voltage - low_voltage)
    low_frequency = float(low["frequency_hz"])
    high_frequency = float(high["frequency_hz"])
    return low_frequency + fraction * (high_frequency - low_frequency)


def maximum_tuning_gain_hz_per_v(
    points: Sequence[Mapping[str, object]], calibration: ChannelCalibration
) -> float:
    """Return the largest local |df/dV| in one measured calibration curve."""
    curve = sorted(
        _code_points(
            points,
            calibration.corner,
            calibration.coarse_code,
            calibration.channel,
            prefer_local=True,
        ),
        key=lambda point: float(point["control_voltage_v"]),
    )
    slopes = []
    for low, high in zip(curve, curve[1:]):
        voltage_delta_v = float(high["control_voltage_v"]) - float(
            low["control_voltage_v"]
        )
        if voltage_delta_v == 0:
            continue
        frequency_delta_hz = float(high["frequency_hz"]) - float(
            low["frequency_hz"]
        )
        slopes.append(abs(frequency_delta_hz / voltage_delta_v))
    if not slopes:
        raise ValueError("calibration curve has no distinct voltage points")
    return max(slopes)


def control_waveform(
    points: Sequence[Mapping[str, object]],
    corner: str,
    channel: int,
    bits: Iterable[int],
) -> tuple[ChannelCalibration, list[int], list[float]]:
    offsets_hz = frequency_words(bits)
    calibration = calibrate_channel(points, corner, channel)
    center_hz = ble_channel_center_hz(channel)
    voltages = [
        control_voltage_for_frequency(points, calibration, center_hz + offset_hz)
        for offset_hz in offsets_hz
    ]
    return calibration, offsets_hz, voltages


def maximum_slew_v_per_s(voltages: Sequence[float]) -> float:
    if len(voltages) < 2:
        return 0.0
    return max(
        abs(current - previous) * SAMPLE_RATE_HZ
        for previous, current in zip(voltages, voltages[1:])
    )
