"""Builders for realistic OpenWeatherMap-shaped payloads used across the tests."""
from __future__ import annotations

from datetime import datetime, timezone

TZ = 3600  # London in summer (UTC+1)


def utc_ts(year, month, day, hour=0, minute=0) -> int:
    return int(datetime(year, month, day, hour, minute, tzinfo=timezone.utc).timestamp())


def current_payload(**over) -> dict:
    """Current weather for 'London' at 2026-09-29 14:20 local (13:20 UTC)."""
    data = {
        "coord": {"lon": -0.1257, "lat": 51.5085},
        "weather": [{"id": 803, "main": "Clouds", "description": "broken clouds", "icon": "04d"}],
        "main": {"temp": 18.4, "feels_like": 17.9, "temp_min": 16.2, "temp_max": 20.1,
                 "pressure": 1013, "humidity": 62},
        "visibility": 10000,
        "wind": {"speed": 4.1, "deg": 240},
        "clouds": {"all": 75},
        "dt": utc_ts(2026, 9, 29, 13, 20),
        "sys": {"country": "GB", "sunrise": utc_ts(2026, 9, 29, 5, 50),
                "sunset": utc_ts(2026, 9, 29, 17, 35)},
        "timezone": TZ,
        "name": "London",
        "cod": 200,
    }
    data.update(over)
    return data


def forecast_payload(start_hour_utc: int = 15, steps: int = 40, **over) -> dict:
    """40 three-hour steps beginning 2026-09-29 15:00 UTC (16:00 local)."""
    items = []
    for i in range(steps):
        ts = utc_ts(2026, 9, 29, start_hour_utc) + i * 3 * 3600
        hour_local = ((start_hour_utc + i * 3 + 1) % 24)
        night = hour_local >= 19 or hour_local < 6
        temp = 12 + 8 * (1 - abs(hour_local - 14) / 14)  # warmest mid-afternoon
        rainy = (i // 8) == 2
        items.append({
            "dt": ts,
            "main": {"temp": temp, "feels_like": temp - 1, "temp_min": temp - 0.8,
                     "temp_max": temp + 0.8, "pressure": 1012, "humidity": 70},
            "weather": [{"id": 500 if rainy else 802,
                         "main": "Rain" if rainy else "Clouds",
                         "description": "light rain" if rainy else "scattered clouds",
                         "icon": ("10" if rainy else "03") + ("n" if night else "d")}],
            "pop": 0.6 if rainy else 0.1,
        })
    data = {"cod": "200", "cnt": steps, "list": items, "city": {"name": "London", "timezone": TZ}}
    data.update(over)
    return data


class FakeResponse:
    def __init__(self, status=200, payload=None, json_error=False):
        self.status_code = status
        self._payload = payload
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise ValueError("bad json")
        return self._payload

    def raise_for_status(self):
        import requests
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"{self.status_code}")


class FakeSession:
    """Stands in for requests.Session; ``responder(url, params)`` returns a response or raises."""

    def __init__(self, responder):
        self.responder = responder
        self.headers = {}
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        return self.responder(url, params)
