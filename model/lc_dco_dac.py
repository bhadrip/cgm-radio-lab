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
