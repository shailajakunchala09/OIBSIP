"""Plain data models plus weather classification helpers.

All datetimes are *naive city-local* times (UTC + the city's timezone offset),
so the UI can display them directly without further conversion.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

# ── Classification ────────────────────────────────────────────────────────────
CLEAR, CLOUDS, RAIN, STORM, SNOW, FOG = "clear", "clouds", "rain", "storm", "snow", "fog"

STATUS = {
    CLEAR: ("Clear skies", "Great conditions to be outdoors"),
    CLOUDS: ("Cloudy", "Soft, overcast light today"),
    RAIN: ("Rainy", "Keep an umbrella handy"),
    STORM: ("Thunderstorm", "Stay indoors if you can"),
    SNOW: ("Snowfall", "Dress warmly — surfaces may be slippery"),
    FOG: ("Low visibility", "Take extra care when travelling"),
}


def classify(condition_id: int) -> str:
    """Map an OpenWeatherMap condition id to a coarse weather kind."""
    if 200 <= condition_id < 300 or condition_id in (771, 781):
        return STORM
    if 300 <= condition_id < 600:
        return RAIN
    if 600 <= condition_id < 700:
        return SNOW
    if 700 <= condition_id < 800:
        return FOG
    if condition_id == 800:
        return CLEAR
    return CLOUDS


def status_for(kind: str, night: bool = False) -> tuple[str, str]:
    if kind == CLEAR and night:
        return "Clear night", "A calm sky for stargazing"
    return STATUS.get(kind, STATUS[CLOUDS])


def icon_name(condition_id: int, night: bool) -> str:
    """Pick one of the bundled icon names for a condition."""
    kind = classify(condition_id)
    if kind == STORM:
        return "storm"
    if kind == RAIN:
        return "rain"
    if kind == SNOW:
        return "snow"
    if kind == FOG:
        return "fog"
    if condition_id == 800:
        return "moon" if night else "sun"
    if condition_id in (801, 802):
        return "partly-night" if night else "partly-day"
    return "cloud"


def is_night_icon(icon_code: str) -> bool:
    return icon_code.endswith("n")


def local_time(timestamp: int | float, tz_offset: int) -> datetime:
    """Convert a UTC unix timestamp to a naive datetime in the city's local time."""
    utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return (utc + timedelta(seconds=tz_offset)).replace(tzinfo=None)


# ── Data models ───────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class CurrentWeather:
    city: str
    country: str
    lat: float
    lon: float
    temp_c: float
    feels_like_c: float
    temp_min_c: float
    temp_max_c: float
    humidity: int
    pressure_hpa: float
    wind_speed_ms: float
    wind_deg: float | None
    visibility_m: float | None
    clouds: int
    condition_id: int
    condition_main: str
    description: str
    night: bool
    observed_at: datetime
    sunrise: datetime | None
    sunset: datetime | None
    tz_offset: int

    @property
    def kind(self) -> str:
        return classify(self.condition_id)

    @property
    def icon(self) -> str:
        return icon_name(self.condition_id, self.night)

    def city_now(self) -> datetime:
        """The current time in the city, derived from this machine's UTC clock."""
        return local_time(datetime.now(timezone.utc).timestamp(), self.tz_offset)

    @property
    def day_length_minutes(self) -> int | None:
        if self.sunrise is None or self.sunset is None:
            return None
        return int((self.sunset - self.sunrise).total_seconds() // 60)


@dataclass(frozen=True)
class ForecastEntry:
    """One 3-hour step from the OpenWeatherMap forecast endpoint."""

    time: datetime
    temp_c: float
    temp_min_c: float
    temp_max_c: float
    condition_id: int
    condition_main: str
    description: str
    night: bool
    pop: float = 0.0  # probability of precipitation, 0..1


@dataclass(frozen=True)
class HourlyPoint:
    time: datetime
    temp_c: float
    condition_id: int
    condition_main: str
    description: str
    night: bool
    pop: float = 0.0

    @property
    def icon(self) -> str:
        return icon_name(self.condition_id, self.night)


@dataclass(frozen=True)
class DailyForecast:
    day: date
    high_c: float
    low_c: float
    condition_id: int
    condition_main: str
    description: str
    pop: float
    is_today: bool = False

    @property
    def kind(self) -> str:
        return classify(self.condition_id)

    @property
    def icon(self) -> str:
        return icon_name(self.condition_id, False)


@dataclass(frozen=True)
class WeatherReport:
    current: CurrentWeather
    hourly: list[HourlyPoint] = field(default_factory=list)
    daily: list[DailyForecast] = field(default_factory=list)
    fetched_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class GeoLocation:
    city: str
    country: str
    lat: float
    lon: float
    provider: str = ""


@dataclass(frozen=True)
class WeatherQuery:
    """Either a city name or a coordinate pair (used by auto-location)."""

    city: str | None = None
    lat: float | None = None
    lon: float | None = None
    display_name: str | None = None

    @classmethod
    def for_location(cls, loc: GeoLocation) -> "WeatherQuery":
        return cls(lat=loc.lat, lon=loc.lon, display_name=loc.city or None)


# ── Small country lookup for the hero card (falls back to the ISO code) ──────
COUNTRIES = {
    "AE": "United Arab Emirates", "AR": "Argentina", "AT": "Austria", "AU": "Australia",
    "BD": "Bangladesh", "BE": "Belgium", "BR": "Brazil", "CA": "Canada", "CH": "Switzerland",
    "CL": "Chile", "CN": "China", "CO": "Colombia", "CZ": "Czechia", "DE": "Germany",
    "DK": "Denmark", "EG": "Egypt", "ES": "Spain", "FI": "Finland", "FR": "France",
    "GB": "United Kingdom", "GR": "Greece", "HK": "Hong Kong", "HU": "Hungary",
    "ID": "Indonesia", "IE": "Ireland", "IL": "Israel", "IN": "India", "IR": "Iran",
    "IT": "Italy", "JP": "Japan", "KE": "Kenya", "KR": "South Korea", "LK": "Sri Lanka",
    "MX": "Mexico", "MY": "Malaysia", "NG": "Nigeria", "NL": "Netherlands", "NO": "Norway",
    "NP": "Nepal", "NZ": "New Zealand", "PE": "Peru", "PH": "Philippines", "PK": "Pakistan",
    "PL": "Poland", "PT": "Portugal", "QA": "Qatar", "RO": "Romania", "RU": "Russia",
    "SA": "Saudi Arabia", "SE": "Sweden", "SG": "Singapore", "TH": "Thailand", "TR": "Türkiye",
    "TW": "Taiwan", "UA": "Ukraine", "US": "United States", "VN": "Vietnam", "ZA": "South Africa",
}


def country_name(code: str) -> str:
    return COUNTRIES.get((code or "").upper(), (code or "").upper())
