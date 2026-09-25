"""Sizing helpers for the coarse/fine LC-DCO tuning interface."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping


MIM_CORNER_SCALE = {"typical": 1.0, "ff": 0.845, "ss": 1.155}
MOSCAP_CORNER_SCALE = {"typical": 1.0, "ff": 0.9, "ss": 1.1}
MIM_MIN_SIDE_UM = 5.0
MOSCAP_MIN_SIDE_UM = 1.0
NMOSCAP_CVAR1 = 0.002003
NMOSCAP_CVAR2 = 0.00198
NMOSCAP_CVAR3 = 6.25
NMOSCAP_CVAR4 = -3.9375


@dataclass(frozen=True)
class TuningEstimate:
    corner: str
    target_frequency_hz: float
    interpolated_side_um: float
    mim_capacitance_ff: float
    local_gain_hz_per_ff: float
    capacitance_for_50khz_ff: float


def mim_capacitance_ff(side_um: float, corner: str = "typical") -> float:
    """Return the modeled 1.5 fF/um^2 square MIM capacitance."""
    if side_um <= 0:
        raise ValueError("side_um must be positive")
    scale = MIM_CORNER_SCALE[corner]
    area_ff = 1.47 * side_um * side_um
    perimeter_ff = 0.379 * 4.0 * side_um
    return scale * (area_ff + perimeter_ff)


def nmoscap_capacitance_ff(
    voltage_v: float,
    count: int = 1,
    corner: str = "typical",
    side_um: float = MOSCAP_MIN_SIDE_UM,
) -> float:
    """Return the GF180 3.3 V NMOS-cap model value for square devices."""
    if count < 1 or side_um <= 0:
        raise ValueError("count and side_um must be positive")
    density_f_per_m2 = NMOSCAP_CVAR1 + NMOSCAP_CVAR2 * math.tanh(
        NMOSCAP_CVAR3 * voltage_v + NMOSCAP_CVAR4
    )
    return (
        MOSCAP_CORNER_SCALE[corner]
        * count
        * side_um
        * side_um
        * density_f_per_m2
        * 1_000.0
    )


def nmoscap_slope_ff_per_v(
    voltage_v: float,
    count: int = 1,
    corner: str = "typical",
    side_um: float = MOSCAP_MIN_SIDE_UM,
) -> float:
    argument = NMOSCAP_CVAR3 * voltage_v + NMOSCAP_CVAR4
    sech_squared = 1.0 / math.cosh(argument) ** 2
    return (
        MOSCAP_CORNER_SCALE[corner]
        * count
        * side_um
        * side_um
        * NMOSCAP_CVAR2
        * NMOSCAP_CVAR3
        * sech_squared
        * 1_000.0
    )


def estimate_tuning(
    points: Iterable[Mapping[str, object]],
    corner: str,
    target_frequency_hz: float,
    tail_current_ua: int = 1000,
) -> TuningEstimate:
    """Interpolate the measured sweep in capacitance around one target."""
    candidates = sorted(
        (
            point
            for point in points
            if point["corner"] == corner
            and point["tail_current_ua"] == tail_current_ua
            and point["sustained_oscillation"]
        ),
        key=lambda point: float(point["cap_side_um"]),
    )
    for high, low in zip(candidates, candidates[1:]):
        high_frequency = float(high["frequency_hz"])
        low_frequency = float(low["frequency_hz"])
        if high_frequency >= target_frequency_hz >= low_frequency:
            fraction = (high_frequency - target_frequency_hz) / (
                high_frequency - low_frequency
            )
            high_side = float(high["cap_side_um"])
            low_side = float(low["cap_side_um"])
            side_um = high_side + fraction * (low_side - high_side)
            high_cap = mim_capacitance_ff(high_side, corner)
            low_cap = mim_capacitance_ff(low_side, corner)
            gain = (high_frequency - low_frequency) / (low_cap - high_cap)
            return TuningEstimate(
                corner=corner,
                target_frequency_hz=target_frequency_hz,
                interpolated_side_um=side_um,
                mim_capacitance_ff=mim_capacitance_ff(side_um, corner),
                local_gain_hz_per_ff=gain,
                capacitance_for_50khz_ff=50_000.0 / gain,
            )
    raise ValueError(f"{corner} sweep does not bracket {target_frequency_hz} Hz")
