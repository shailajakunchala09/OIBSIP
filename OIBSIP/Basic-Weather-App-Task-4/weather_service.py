"""OpenWeatherMap client: HTTP calls, error mapping and JSON parsing."""
from __future__ import annotations

import logging
from datetime import datetime

import requests

from config import APP_NAME, APP_VERSION, Settings
from errors import (
    CityNotFoundError, InvalidApiKeyError, MalformedResponseError, MissingApiKeyError,
    NoConnectionError, RateLimitError, RequestTimeoutError, ServiceUnavailableError,
)
from forecast import build_daily, build_hourly
from models import (
    CurrentWeather, ForecastEntry, WeatherQuery, WeatherReport, is_night_icon, local_time,
)
from validators import validate_city

log = logging.getLogger(__name__)


# ── Parsing (pure functions, unit-tested) ─────────────────────────────────────
def parse_current(data: dict) -> CurrentWeather:
    """Turn a ``/weather`` JSON payload into a :class:`CurrentWeather`."""
    try:
        tz = int(data.get("timezone", 0))
        cond = data["weather"][0]
        main = data["main"]
        sys_ = data.get("sys", {})
        wind = data.get("wind", {})
        temp = float(main["temp"])
        sunrise, sunset = sys_.get("sunrise"), sys_.get("sunset")
        visibility = data.get("visibility")
        return CurrentWeather(
            city=str(data.get("name") or "Unknown location"),
            country=str(sys_.get("country", "")),
            lat=float(data.get("coord", {}).get("lat", 0.0)),
            lon=float(data.get("coord", {}).get("lon", 0.0)),
            temp_c=temp,
            feels_like_c=float(main.get("feels_like", temp)),
            temp_min_c=float(main.get("temp_min", temp)),
            temp_max_c=float(main.get("temp_max", temp)),
            humidity=int(main.get("humidity", 0)),
            pressure_hpa=float(main.get("pressure", 0)),
            wind_speed_ms=float(wind.get("speed", 0.0)),
            wind_deg=float(wind["deg"]) if wind.get("deg") is not None else None,
            visibility_m=float(visibility) if visibility is not None else None,
            clouds=int(data.get("clouds", {}).get("all", 0)),
            condition_id=int(cond["id"]),
            condition_main=str(cond.get("main", "")),
            description=str(cond.get("description", "")),
            night=is_night_icon(str(cond.get("icon", "01d"))),
            observed_at=local_time(data["dt"], tz),
            sunrise=local_time(sunrise, tz) if sunrise else None,
            sunset=local_time(sunset, tz) if sunset else None,
            tz_offset=tz,
        )
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise MalformedResponseError() from exc


def parse_forecast(data: dict) -> list[ForecastEntry]:
    """Turn a ``/forecast`` (3-hour steps) payload into sorted :class:`ForecastEntry` items."""
    try:
        tz = int(data.get("city", {}).get("timezone", 0))
        entries = []
        for item in data["list"]:
            cond = item["weather"][0]
            main = item["main"]
            temp = float(main["temp"])
            entries.append(ForecastEntry(
                time=local_time(item["dt"], tz),
                temp_c=temp,
                temp_min_c=float(main.get("temp_min", temp)),
                temp_max_c=float(main.get("temp_max", temp)),
                condition_id=int(cond["id"]),
                condition_main=str(cond.get("main", "")),
                description=str(cond.get("description", "")),
                night=is_night_icon(str(cond.get("icon", "01d"))),
                pop=float(item.get("pop", 0.0)),
            ))
        if not entries:
            raise ValueError("empty forecast")
        return sorted(entries, key=lambda e: e.time)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise MalformedResponseError() from exc


# ── Service ───────────────────────────────────────────────────────────────────
class WeatherService:
    """Fetches current weather + forecast and assembles a :class:`WeatherReport`."""

    def __init__(self, settings: Settings, session: requests.Session | None = None):
        self.settings = settings
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", f"{APP_NAME}/{APP_VERSION}")

    def fetch_report(self, query: WeatherQuery, now: datetime | None = None) -> WeatherReport:
        params = self._location_params(query)
        current = parse_current(self._get("weather", params))
        entries = parse_forecast(self._get("forecast", params))
        if query.display_name:  # e.g. the city name found by IP geolocation
            from dataclasses import replace
            current = replace(current, city=query.display_name)
        now = now or current.city_now()
        return WeatherReport(
            current=current,
            hourly=build_hourly(current, entries, now=now),
            daily=build_daily(current, entries, now=now),
        )

    # -- internals -----------------------------------------------------------
    @staticmethod
    def _location_params(query: WeatherQuery) -> dict:
        if query.lat is not None and query.lon is not None:
            return {"lat": query.lat, "lon": query.lon}
        return {"q": validate_city(query.city)}

    def _get(self, endpoint: str, params: dict) -> dict:
        if not self.settings.has_api_key:
            raise MissingApiKeyError()

        full = {**params, "appid": self.settings.api_key, "units": "metric"}
        try:
            resp = self.session.get(f"{self.settings.base_url}/{endpoint}", params=full,
                                    timeout=self.settings.timeout)
        except requests.exceptions.Timeout as exc:  # includes ConnectTimeout
            raise RequestTimeoutError() from exc
        except requests.exceptions.ConnectionError as exc:
            raise NoConnectionError() from exc
        except requests.exceptions.RequestException as exc:
            raise ServiceUnavailableError() from exc
        # NB: exception text is never shown or logged — it can contain the request URL (and key).

        status = resp.status_code
        if status == 200:
            try:
                payload = resp.json()
            except ValueError as exc:
                raise MalformedResponseError() from exc
            if not isinstance(payload, dict):
                raise MalformedResponseError()
            return payload
        if status == 401:
            raise InvalidApiKeyError()
        if status in (400, 404):
            raise CityNotFoundError()
        if status == 429:
            raise RateLimitError()
        log.warning("Unexpected HTTP status %s from OpenWeatherMap", status)
        raise ServiceUnavailableError()
