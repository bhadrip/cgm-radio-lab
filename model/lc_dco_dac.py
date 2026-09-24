"""Quantized voltage-control model for the calibrated LC-DCO."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VoltageDac:
    bits: int
    minimum_v: float = 0.0
    maximum_v: float = 1.8

    def __post_init__(self) -> None:
        if self.bits <= 0:
            raise ValueError("DAC bits must be positive")
        if self.maximum_v <= self.minimum_v:
            raise ValueError("DAC maximum must exceed minimum")

    @property
    def maximum_code(self) -> int:
        return (1 << self.bits) - 1

    @property
    def lsb_v(self) -> float:
        return (self.maximum_v - self.minimum_v) / self.maximum_code

    def code_for_voltage(self, voltage_v: float) -> int:
        if not self.minimum_v <= voltage_v <= self.maximum_v:
            raise ValueError("voltage is outside the DAC range")
        return round((voltage_v - self.minimum_v) / self.lsb_v)

    def voltage_for_code(self, code: int) -> float:
        if not 0 <= code <= self.maximum_code:
            raise ValueError("code is outside the DAC range")
        return self.minimum_v + code * self.lsb_v

    def quantize(self, voltage_v: float) -> float:
        return self.voltage_for_code(self.code_for_voltage(voltage_v))


@dataclass(frozen=True)
class SegmentedVoltageDac:
    bias: VoltageDac
    modulation: VoltageDac

    def quantize_waveform(
        self, center_voltage_v: float, requested_voltages_v: list[float]
    ) -> tuple[int, list[int], list[float]]:
        bias_code = self.bias.code_for_voltage(center_voltage_v)
        bias_voltage_v = self.bias.voltage_for_code(bias_code)
        modulation_codes = [
            self.modulation.code_for_voltage(voltage_v - bias_voltage_v)
            for voltage_v in requested_voltages_v
        ]
        output_voltages_v = [
            bias_voltage_v + self.modulation.voltage_for_code(code)
            for code in modulation_codes
        ]
        return bias_code, modulation_codes, output_voltages_v


@dataclass(frozen=True)
class SegmentedDacEncoding:
    """Thermometer-MSB/binary-LSB encoding for one voltage DAC."""

    bits: int
    thermometer_msb_bits: int

    def __post_init__(self) -> None:
        if self.bits <= 0:
            raise ValueError("DAC bits must be positive")
        if not 0 <= self.thermometer_msb_bits <= self.bits:
            raise ValueError("thermometer bits must be within the DAC width")

    @property
    def binary_lsb_bits(self) -> int:
        return self.bits - self.thermometer_msb_bits

    @property
    def maximum_code(self) -> int:
        return (1 << self.bits) - 1

    @property
    def switched_element_count(self) -> int:
        return (1 << self.thermometer_msb_bits) - 1 + self.binary_lsb_bits

    def transition_events(self, previous_code: int, next_code: int) -> list[int]:
        """Return signed element weights for a code transition."""
        if not 0 <= previous_code <= self.maximum_code:
            raise ValueError("previous code is outside the DAC range")
        if not 0 <= next_code <= self.maximum_code:
            raise ValueError("next code is outside the DAC range")
        lsb_bits = self.binary_lsb_bits
        events = []
        for bit in range(lsb_bits):
            previous_state = (previous_code >> bit) & 1
            next_state = (next_code >> bit) & 1
            if previous_state != next_state:
                events.append((next_state - previous_state) * (1 << bit))
        previous_thermometer = previous_code >> lsb_bits
        next_thermometer = next_code >> lsb_bits
        thermometer_weight = 1 << lsb_bits
        events.extend(
            [thermometer_weight]
            * max(0, next_thermometer - previous_thermometer)
        )
        events.extend(
            [-thermometer_weight]
            * max(0, previous_thermometer - next_thermometer)
        )
        return events

    def worst_case_glitch_excursion_codes(
        self, previous_code: int, next_code: int
    ) -> int:
        """Bound excursion outside both endpoints for arbitrary switch order."""
        events = self.transition_events(previous_code, next_code)
        minimum_intermediate = previous_code + sum(
            event for event in events if event < 0
        )
        maximum_intermediate = previous_code + sum(
            event for event in events if event > 0
        )
        lower_endpoint = min(previous_code, next_code)
        upper_endpoint = max(previous_code, next_code)
        return max(
            0,
            lower_endpoint - minimum_intermediate,
            maximum_intermediate - upper_endpoint,
        )
