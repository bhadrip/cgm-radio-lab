#!/usr/bin/env python3
"""Screen the BLE LE 1M GFSK complex-envelope adjacent-channel spectrum."""

from __future__ import annotations

import cmath
import json
import math
from pathlib import Path

from model.gfsk import (
    SAMPLE_RATE_HZ,
    SAMPLES_PER_SYMBOL,
    frequency_samples,
    frequency_words,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "gfsk_spectrum.json"
SYMBOL_COUNT = 4096
CHANNEL_BANDWIDTH_HZ = 1_000_000
OFFSETS_HZ = (2_000_000, 3_000_000, 4_000_000)
LIMITS_DBM = {2_000_000: -20.0, 3_000_000: -30.0, 4_000_000: -30.0}
MAXIMUM_TX_POWER_DBM = 0.0


def prbs9_bits(count: int) -> list[int]:
    state = 0x1FF
    bits = []
    for _ in range(count):
        bits.append(state & 1)
        feedback = ((state >> 8) ^ (state >> 4)) & 1
        state = ((state << 1) & 0x1FF) | feedback
    return bits


def iq_from_frequency(frequencies_hz: list[float] | list[int]) -> list[complex]:
    phase = 0.0
    samples = []
    count = len(frequencies_hz)
    for index, frequency_hz in enumerate(frequencies_hz):
        phase += 2.0 * math.pi * frequency_hz / SAMPLE_RATE_HZ
        window = 0.5 - 0.5 * math.cos(2.0 * math.pi * index / count)
        samples.append(cmath.exp(1j * phase) * window)
    return samples


def fft(values: list[complex]) -> list[complex]:
    count = len(values)
    if count == 0 or count & (count - 1):
        raise ValueError("FFT length must be a nonzero power of two")
    output = list(values)
    reversed_index = 0
    for index in range(1, count):
        bit = count >> 1
        while reversed_index & bit:
            reversed_index ^= bit
            bit >>= 1
        reversed_index ^= bit
        if index < reversed_index:
            output[index], output[reversed_index] = (
                output[reversed_index],
                output[index],
            )
    length = 2
    while length <= count:
        rotation = cmath.exp(-2j * math.pi / length)
        half = length // 2
        for start in range(0, count, length):
            phasor = 1.0 + 0.0j
            for index in range(start, start + half):
                even = output[index]
                odd = output[index + half] * phasor
                output[index] = even + odd
                output[index + half] = even - odd
                phasor *= rotation
        length *= 2
    return output


def channel_powers(frequencies_hz: list[float] | list[int]) -> dict[int, float]:
    transform = fft(iq_from_frequency(frequencies_hz))
    powers = [abs(value) ** 2 for value in transform]
    total_power = sum(powers)
    count = len(powers)
    half_bandwidth_hz = CHANNEL_BANDWIDTH_HZ / 2
    results = {}
    for center_hz in (0, *OFFSETS_HZ, *(-offset for offset in OFFSETS_HZ)):
        channel_power = 0.0
        for index, power in enumerate(powers):
            frequency_hz = index * SAMPLE_RATE_HZ / count
            if index >= count // 2:
                frequency_hz -= SAMPLE_RATE_HZ
            if center_hz - half_bandwidth_hz <= frequency_hz < center_hz + half_bandwidth_hz:
                channel_power += power
        results[center_hz] = 10.0 * math.log10(channel_power / total_power)
    return results


def main() -> None:
    bits = prbs9_bits(SYMBOL_COUNT)
    ideal = channel_powers(frequency_samples(bits))
    quantized = channel_powers(frequency_words(bits))
    measurements = []
    for offset_hz in OFFSETS_HZ:
        for side in (-1, 1):
            signed_offset_hz = side * offset_hz
            relative_power_db = quantized[signed_offset_hz]
            absolute_power_dbm = MAXIMUM_TX_POWER_DBM + relative_power_db
            measurements.append(
                {
                    "offset_hz": signed_offset_hz,
                    "relative_power_db": relative_power_db,
                    "absolute_power_at_0dbm_tx_dbm": absolute_power_dbm,
                    "limit_dbm": LIMITS_DBM[offset_hz],
                    "margin_db": LIMITS_DBM[offset_hz] - absolute_power_dbm,
                    "quantization_delta_db": relative_power_db
                    - ideal[signed_offset_hz],
                    "passed": absolute_power_dbm <= LIMITS_DBM[offset_hz],
                }
            )
    report = {
        "schema_version": 1,
        "purpose": "BLE LE 1M complex-envelope adjacent-channel screening",
        "stimulus": "PRBS9",
        "symbol_count": SYMBOL_COUNT,
        "sample_rate_hz": SAMPLE_RATE_HZ,
        "sample_count": len(bits) * SAMPLES_PER_SYMBOL,
        "frequency_bin_hz": SAMPLE_RATE_HZ
        / (len(bits) * SAMPLES_PER_SYMBOL),
        "window": "periodic Hann",
        "integration_bandwidth_hz": CHANNEL_BANDWIDTH_HZ,
        "maximum_tx_power_dbm": MAXIMUM_TX_POWER_DBM,
        "in_band_relative_power_db": quantized[0],
        "worst_margin_db": min(measurement["margin_db"] for measurement in measurements),
        "maximum_absolute_quantization_delta_db": max(
            abs(measurement["quantization_delta_db"])
            for measurement in measurements
        ),
        "passed": all(measurement["passed"] for measurement in measurements),
        "measurements": measurements,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(REPORT.read_text(), end="")
    if not report["passed"]:
        raise RuntimeError("GFSK adjacent-channel screen failed")


if __name__ == "__main__":
    main()
