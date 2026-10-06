"""Unit conversion and display formatting.

All data is fetched in metric units once; switching between Celsius and
Fahrenheit is a pure client-side conversion, so the toggle is instant.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class UnitSystem(str, Enum):
    METRIC = "metric"
    IMPERIAL = "imperial"

    @classmethod
    def parse(cls, value: str | None) -> "UnitSystem":
        try:
            return cls(value)
        except ValueError:
            return cls.METRIC


def round_half_up(value: float) -> int:
    """Round .5 upwards (Python's round() uses banker's rounding) and never return -0."""
    result = int(math.floor(value + 0.5))
    return 0 if result == 0 else result


def c_to_f(celsius: float) -> float:
    return celsius * 9.0 / 5.0 + 32.0


def ms_to_kmh(ms: float) -> float:
    return ms * 3.6


def ms_to_mph(ms: float) -> float:
    return ms * 2.236936


def m_to_km(meters: float) -> float:
    return meters / 1000.0


def m_to_mi(meters: float) -> float:
    return meters / 1609.344


def hpa_to_inhg(hpa: float) -> float:
    return hpa * 0.02953


_COMPASS = ("N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW")


def compass(degrees: float | None) -> str:
    if degrees is None:
        return ""
    return _COMPASS[int((degrees % 360) / 22.5 + 0.5) % 16]


# (upper bound m/s, label) — simplified Beaufort scale
_BEAUFORT = ((0.5, "Calm"), (1.6, "Light air"), (3.4, "Light breeze"), (5.5, "Gentle breeze"),
             (8.0, "Moderate breeze"), (10.8, "Fresh breeze"), (13.9, "Strong breeze"),
             (17.2, "Near gale"), (24.5, "Gale"), (32.7, "Storm"))


def beaufort_label(ms: float) -> str:
    for limit, label in _BEAUFORT:
        if ms < limit:
            return label
    return "Hurricane force"


@dataclass(frozen=True)
class Formatter:
    """Formats measurements for a chosen unit system."""

    system: UnitSystem = UnitSystem.METRIC

    @property
    def imperial(self) -> bool:
        return self.system is UnitSystem.IMPERIAL

    @property
    def temp_unit(self) -> str:
        return "°F" if self.imperial else "°C"

    def temp_value(self, celsius: float) -> int:
        return round_half_up(c_to_f(celsius) if self.imperial else celsius)

    def temp(self, celsius: float) -> str:
        return f"{self.temp_value(celsius)}°"

    def temp_full(self, celsius: float) -> str:
        return f"{self.temp_value(celsius)}{self.temp_unit}"

    def wind(self, ms: float) -> str:
        if self.imperial:
            return f"{round_half_up(ms_to_mph(ms))} mph"
        return f"{round_half_up(ms_to_kmh(ms))} km/h"

    def distance(self, meters: float | None) -> str:
        if meters is None:
            return "—"
        if self.imperial:
            miles = m_to_mi(meters)
            return f"{miles:.0f} mi" if miles >= 10 else f"{miles:.1f} mi"
        km = m_to_km(meters)
        return f"{km:.0f} km" if km >= 10 else f"{km:.1f} km"

    def pressure(self, hpa: float) -> str:
        if self.imperial:
            return f"{hpa_to_inhg(hpa):.2f} inHg"
        return f"{round_half_up(hpa)} hPa"


def fmt_clock(moment: datetime | None) -> str:
    """'6:12 AM' — portable replacement for the non-portable %-I directive."""
    if moment is None:
        return "—"
    return moment.strftime("%I:%M %p").lstrip("0")


def fmt_hour(moment: datetime) -> str:
    """'3 PM'."""
    return moment.strftime("%I %p").lstrip("0")


def fmt_duration(minutes: int) -> str:
    hours, mins = divmod(max(0, int(minutes)), 60)
    return f"{hours}h {mins:02d}m"
