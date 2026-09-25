"""Dependency-free BLE LE 1M Gaussian-FSK reference model.

The hardware interface emits one instantaneous frequency-offset word per
16 MHz clock. Sixteen samples form one 1 Msym/s BLE symbol. The Gaussian FIR is
represented as five symbol contributions at each sample phase, which is exactly
equivalent to a 65-tap, four-symbol-span sampled filter.
"""

from __future__ import annotations

import cmath
import math
from collections.abc import Iterable, Sequence

SYMBOL_RATE_HZ = 1_000_000
SAMPLES_PER_SYMBOL = 16
SAMPLE_RATE_HZ = SYMBOL_RATE_HZ * SAMPLES_PER_SYMBOL
BT = 0.5
MODULATION_INDEX = 0.5
DEVIATION_HZ = int(MODULATION_INDEX * SYMBOL_RATE_HZ / 2)
FILTER_SPAN_SYMBOLS = 4
HISTORY_SYMBOLS = FILTER_SPAN_SYMBOLS + 1


def _validated_bits(bits: Iterable[int]) -> list[int]:
    result = [int(bit) for bit in bits]
    if any(bit not in (0, 1) for bit in result):
        raise ValueError("bits must contain only zero or one")
    return result


def gaussian_taps(
    bt: float = BT,
    samples_per_symbol: int = SAMPLES_PER_SYMBOL,
    span_symbols: int = FILTER_SPAN_SYMBOLS,
) -> list[float]:
    """Return a unity-DC-gain sampled Gaussian impulse response.

    `bt` is the Gaussian filter 3 dB bandwidth-symbol-period product. An even
    span gives an odd tap count and an integer group delay.
    """

    if bt <= 0:
        raise ValueError("BT must be positive")
    if samples_per_symbol <= 0:
        raise ValueError("samples per symbol must be positive")
    if span_symbols <= 0 or span_symbols % 2:
        raise ValueError("filter span must be a positive even number")

    tap_count = span_symbols * samples_per_symbol + 1
    center = (tap_count - 1) / 2
    scale = math.sqrt(2 * math.pi) * bt / math.sqrt(math.log(2))
    taps = []
    for index in range(tap_count):
        time_symbols = (index - center) / samples_per_symbol
        exponent = -2 * math.pi**2 * bt**2 * time_symbols**2 / math.log(2)
        taps.append(scale * math.exp(exponent))
    total = sum(taps)
    return [tap / total for tap in taps]


def symbol_phase_weights(
    *,
    quantized_hz: bool = False,
    deviation_hz: int = DEVIATION_HZ,
) -> list[tuple[float, ...]] | list[tuple[int, ...]]:
    """Collapse the sampled FIR into five symbol weights for each phase."""

    taps = gaussian_taps()
    phases: list[tuple[float, ...]] = []
    for phase in range(SAMPLES_PER_SYMBOL):
        weights = []
        for age in range(HISTORY_SYMBOLS):
            contribution = sum(
                tap
                for tap_index, tap in enumerate(taps)
                if math.ceil((tap_index - phase) / SAMPLES_PER_SYMBOL) == age
            )
            weights.append(contribution)
        phases.append(tuple(weights))

    if not quantized_hz:
        return phases

    quantized: list[tuple[int, ...]] = []
    for weights in phases:
        words = [round(deviation_hz * weight) for weight in weights]
        largest = max(range(len(words)), key=words.__getitem__)
        words[largest] += deviation_hz - sum(words)
        quantized.append(tuple(words))
    return quantized


def frequency_samples(
    bits: Iterable[int],
    *,
    initial_bit: int = 0,
    deviation_hz: int = DEVIATION_HZ,
) -> list[float]:
    """Return ideal instantaneous-frequency samples for the input symbols.

    The causal realization has a two-symbol group delay. `initial_bit` models
    the symbol history before the first supplied bit.
    """

    data = _validated_bits(bits)
    if initial_bit not in (0, 1):
        raise ValueError("initial bit must be zero or one")
    weights = symbol_phase_weights()
    history = [initial_bit] * HISTORY_SYMBOLS
    output: list[float] = []
    for bit in data:
        history = [bit, *history[:-1]]
        signs = [1 if value else -1 for value in history]
        for phase_weights in weights:
            output.append(
                deviation_hz
                * sum(sign * weight for sign, weight in zip(signs, phase_weights))
            )
    return output


def frequency_words(
    bits: Iterable[int],
    *,
    initial_bit: int = 0,
    deviation_hz: int = DEVIATION_HZ,
) -> list[int]:
    """Return the integer-Hz words emitted by the synthesizable modulator."""

    data = _validated_bits(bits)
    if initial_bit not in (0, 1):
        raise ValueError("initial bit must be zero or one")
    weights = symbol_phase_weights(quantized_hz=True, deviation_hz=deviation_hz)
    history = [initial_bit] * HISTORY_SYMBOLS
    output: list[int] = []
    for bit in data:
        history = [bit, *history[:-1]]
        signs = [1 if value else -1 for value in history]
        for phase_weights in weights:
            output.append(
                sum(sign * weight for sign, weight in zip(signs, phase_weights))
            )
    return output


def iq_samples(
    bits: Sequence[int],
    *,
    initial_phase_rad: float = 0.0,
) -> list[complex]:
    """Integrate instantaneous frequency into constant-envelope complex IQ."""

    phase = initial_phase_rad
    output = []
    for frequency_hz in frequency_samples(bits):
        phase += 2 * math.pi * frequency_hz / SAMPLE_RATE_HZ
        output.append(cmath.exp(1j * phase))
    return output
