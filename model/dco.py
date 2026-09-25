"""Calibrated digital interface for a direct-modulation BLE DCO."""

from __future__ import annotations

from collections.abc import Iterable

DCO_CODE_BITS = 12
DCO_CODE_MAX = (1 << DCO_CODE_BITS) - 1
DCO_GAIN_HZ_PER_LSB = 50_000


def ble_channel_center_hz(channel: int) -> int:
    """Return the BLE RF channel center frequency."""

    if not 0 <= channel <= 39:
        raise ValueError("BLE channel must be in the range 0..39")
    if channel == 37:
        return 2_402_000_000
    if channel == 38:
        return 2_426_000_000
    if channel == 39:
        return 2_480_000_000
    if channel <= 10:
        return 2_404_000_000 + 2_000_000 * channel
    return 2_428_000_000 + 2_000_000 * (channel - 11)


def _round_divide(value: int, divisor: int) -> int:
    if divisor <= 0:
        raise ValueError("divisor must be positive")
    if value >= 0:
        return (value + divisor // 2) // divisor
    return -((-value + divisor // 2) // divisor)


def dco_codes(
    frequency_offsets_hz: Iterable[int],
    base_code: int,
    *,
    gain_hz_per_lsb: int = DCO_GAIN_HZ_PER_LSB,
) -> tuple[list[int], list[bool]]:
    """Noise-shape frequency offsets into calibrated integer DCO codes.

    ``base_code`` is measured during channel calibration. A first-order error
    accumulator dithers adjacent codes so the average frequency can resolve
    below one DCO LSB. Saturation clears the residual because the requested
    frequency is outside the calibrated actuator range.
    """

    if not 0 <= base_code <= DCO_CODE_MAX:
        raise ValueError("base code does not fit the DCO control word")
    if gain_hz_per_lsb <= 0:
        raise ValueError("DCO gain must be positive")

    residual_hz = 0
    codes: list[int] = []
    saturated: list[bool] = []
    for offset_hz in frequency_offsets_hz:
        combined_hz = int(offset_hz) + residual_hz
        step = _round_divide(combined_hz, gain_hz_per_lsb)
        candidate = base_code + step
        clipped = min(max(candidate, 0), DCO_CODE_MAX)
        hit_limit = clipped != candidate
        codes.append(clipped)
        saturated.append(hit_limit)
        residual_hz = (
            0 if hit_limit else combined_hz - step * gain_hz_per_lsb
        )
    return codes, saturated


def realized_offsets_hz(
    codes: Iterable[int],
    base_code: int,
    *,
    gain_hz_per_lsb: int = DCO_GAIN_HZ_PER_LSB,
) -> list[int]:
    return [(int(code) - base_code) * gain_hz_per_lsb for code in codes]
