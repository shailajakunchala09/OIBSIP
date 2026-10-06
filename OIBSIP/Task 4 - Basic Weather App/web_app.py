from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

# Load the local .env file before reading the API key.
load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()

CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/reverse"

REQUEST_TIMEOUT = 12


def api_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def weather_icon(icon_code: str) -> str:
    """Convert OpenWeather icon codes to SkyPulse weather categories."""
    code = (icon_code or "").lower()

    mapping = {
        "01d": "sun",
        "01n": "moon",
        "02d": "partly-day",
        "02n": "partly-night",
        "03d": "cloud",
        "03n": "cloud",
        "04d": "cloud",
        "04n": "cloud",
        "09d": "rain",
        "09n": "rain",
        "10d": "rain",
        "10n": "rain",
        "11d": "storm",
        "11n": "storm",
        "13d": "snow",
        "13n": "snow",
        "50d": "fog",
        "50n": "fog",
    }

    return mapping.get(code, "cloud")


def compass_direction(degrees: float | int | None) -> str:
    if degrees is None:
        return "—"

    directions = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]

    index = int((float(degrees) + 11.25) / 22.5) % 16
    return directions[index]


def beaufort_label(speed_mps: float) -> str:
    """Return the same kind of human-readable wind description used by SkyPulse."""
    speed = float(speed_mps)

    if speed < 0.5:
        return "Calm"
    if speed < 1.6:
        return "Light air"
    if speed < 3.4:
        return "Light breeze"
    if speed < 5.5:
        return "Gentle breeze"
    if speed < 8.0:
        return "Moderate breeze"
    if speed < 10.8:
        return "Fresh breeze"
    if speed < 13.9:
        return "Strong breeze"
    if speed < 17.2:
        return "Near gale"
    if speed < 20.8:
        return "Gale"
    if speed < 24.5:
        return "Strong gale"
    if speed < 28.5:
        return "Storm"
    if speed < 32.7:
        return "Violent storm"

    return "Hurricane force"


def format_time(timestamp: int | float | None, offset: int = 0) -> str:
    if timestamp is None:
        return "—"

    try:
        value = datetime.fromtimestamp(
            float(timestamp) + int(offset),
            tz=timezone.utc,
        )
        return value.strftime("%I:%M %p").lstrip("0")
    except (TypeError, ValueError, OverflowError):
        return "—"


def format_date(timestamp: int | float | None, offset: int = 0) -> str:
    if timestamp is None:
        return "—"

    try:
        value = datetime.fromtimestamp(
            float(timestamp) + int(offset),
            tz=timezone.utc,
        )
        return f"{value.strftime('%a, %b')} {value.day}"
    except (TypeError, ValueError, OverflowError):
        try:
            value = datetime.fromtimestamp(
                float(timestamp) + int(offset),
                tz=timezone.utc,
            )
            return value.strftime("%a, %b %d").replace(" 0", " ")
        except Exception:
            return "—"


def local_datetime(timestamp: int | float, offset: int) -> datetime:
    return datetime.fromtimestamp(
        float(timestamp) + int(offset),
        tz=timezone.utc,
    )


def condition_kind(main: str, icon_code: str) -> str:
    main = (main or "").lower()
    icon_code = (icon_code or "").lower()

    if main == "clear":
        return "clear"

    if main in {"thunderstorm"}:
        return "storm"

    if main in {"rain", "drizzle"}:
        return "rain"

    if main == "snow":
        return "snow"

    if main in {"mist", "smoke", "haze", "dust", "fog", "sand", "ash", "squall"}:
        return "fog"

    if main in {"clouds"}:
        return "clouds"

    if icon_code.startswith("01"):
        return "clear"

    return "clouds"


def build_current(data: dict[str, Any]) -> dict[str, Any]:
    weather = data.get("weather", [{}])[0]
    main = data.get("main", {})
    wind = data.get("wind", {})
    sys_data = data.get("sys", {})

    icon_code = weather.get("icon", "")
    kind = condition_kind(weather.get("main", ""), icon_code)

    return {
        "city": data.get("name", "Unknown"),
        "country": sys_data.get("country", ""),
        "country_name": sys_data.get("country", ""),
        "temperature": main.get("temp"),
        "feels_like": main.get("feels_like"),
        "temp_min": main.get("temp_min"),
        "temp_max": main.get("temp_max"),
        "humidity": main.get("humidity"),
        "pressure": main.get("pressure"),
        "visibility": data.get("visibility"),
        "clouds": data.get("clouds", {}).get("all"),
        "wind_speed": wind.get("speed"),
        "wind_direction": wind.get("deg"),
        "wind_compass": compass_direction(wind.get("deg")),
        "wind_label": beaufort_label(wind.get("speed", 0)),
        "condition": weather.get("description", "").title(),
        "main_condition": weather.get("main", ""),
        "icon": weather_icon(icon_code),
        "icon_code": icon_code,
        "kind": kind,
        "sunrise": sys_data.get("sunrise"),
        "sunset": sys_data.get("sunset"),
        "timezone": data.get("timezone", 0),
        "timestamp": data.get("dt"),
    }


def build_hourly(forecast: dict[str, Any]) -> list[dict[str, Any]]:
    items = forecast.get("list", [])
    city = forecast.get("city", {})
    offset = city.get("timezone", 0)

    result: list[dict[str, Any]] = []

    for item in items[:6]:
        weather = item.get("weather", [{}])[0]
        main = item.get("main", {})
        rain = item.get("rain", {})
        snow = item.get("snow", {})

        precipitation = 0.0

        if isinstance(rain, dict):
            precipitation += float(rain.get("3h", 0) or 0)

        if isinstance(snow, dict):
            precipitation += float(snow.get("3h", 0) or 0)

        result.append(
            {
                "timestamp": item.get("dt"),
                "time": format_time(item.get("dt"), offset),
                "temperature": main.get("temp"),
                "feels_like": main.get("feels_like"),
                "condition": weather.get("description", "").title(),
                "icon": weather_icon(weather.get("icon", "")),
                "icon_code": weather.get("icon", ""),
                "pop": round(float(item.get("pop", 0) or 0) * 100),
                "precipitation": precipitation,
            }
        )

    return result


def build_daily(forecast: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Convert OpenWeather's 3-hour forecast into five daily forecast cards.

    The forecast API normally provides multiple entries per day. We group
    those entries by the city's local calendar date and calculate a useful
    high/low range from the available entries.
    """
    items = forecast.get("list", [])
    city = forecast.get("city", {})
    offset = int(city.get("timezone", 0) or 0)

    groups: dict[str, list[dict[str, Any]]] = {}

    for item in items:
        dt = item.get("dt")

        if dt is None:
            continue

        local = local_datetime(dt, offset)
        key = local.strftime("%Y-%m-%d")

        groups.setdefault(key, []).append(item)

    days: list[dict[str, Any]] = []

    for date_key, entries in list(groups.items())[:5]:
        temperatures: list[float] = []
        representative = entries[len(entries) // 2]

        highest_pop = 0.0

        for entry in entries:
            temp = entry.get("main", {}).get("temp")
            if temp is not None:
                temperatures.append(float(temp))

            highest_pop = max(
                highest_pop,
                float(entry.get("pop", 0) or 0),
            )

        weather = representative.get("weather", [{}])[0]
        representative_dt = representative.get("dt")

        local = local_datetime(representative_dt, offset)

        days.append(
            {
                "date": date_key,
                "day": local.strftime("%a"),
                "date_label": f"{local.strftime('%b')} {local.day}",
                "date_label_fallback": local.strftime("%b %d").replace(" 0", " "),
                "temperature": representative.get("main", {}).get("temp"),
                "high": max(temperatures) if temperatures else None,
                "low": min(temperatures) if temperatures else None,
                "condition": weather.get("description", "").title(),
                "icon": weather_icon(weather.get("icon", "")),
                "icon_code": weather.get("icon", ""),
                "pop": round(highest_pop * 100),
            }
        )

    return days


def fetch_weather(city: str) -> dict[str, Any]:
    if not API_KEY:
        raise RuntimeError("Weather service is not configured.")

    current_response = requests.get(
        CURRENT_URL,
        params={
            "q": city,
            "appid": API_KEY,
            "units": "metric",
        },
        timeout=REQUEST_TIMEOUT,
    )

    try:
        current_data = current_response.json()
    except ValueError:
        current_data = {}

    if current_response.status_code != 200:
        message = current_data.get(
            "message",
            "Unable to fetch current weather.",
        )
        raise ValueError(message.title())

    forecast_response = requests.get(
        FORECAST_URL,
        params={
            "lat": current_data["coord"]["lat"],
            "lon": current_data["coord"]["lon"],
            "appid": API_KEY,
            "units": "metric",
        },
        timeout=REQUEST_TIMEOUT,
    )

    try:
        forecast_data = forecast_response.json()
    except ValueError:
        forecast_data = {}

    if forecast_response.status_code != 200:
        message = forecast_data.get(
            "message",
            "Unable to fetch the forecast.",
        )
        raise ValueError(message.title())

    current = build_current(current_data)

    return {
        "ok": True,
        "current": current,
        "hourly": build_hourly(forecast_data),
        "daily": build_daily(forecast_data),
        "meta": {
            "requested_city": city,
            "fetched_at": int(datetime.now(tz=timezone.utc).timestamp()),
        },
    }


def fetch_weather_by_coordinates(
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    if not API_KEY:
        raise RuntimeError("Weather service is not configured.")

    current_response = requests.get(
        CURRENT_URL,
        params={
            "lat": latitude,
            "lon": longitude,
            "appid": API_KEY,
            "units": "metric",
        },
        timeout=REQUEST_TIMEOUT,
    )

    try:
        current_data = current_response.json()
    except ValueError:
        current_data = {}

    if current_response.status_code != 200:
        message = current_data.get(
            "message",
            "Unable to fetch weather for your location.",
        )
        raise ValueError(message.title())

    forecast_response = requests.get(
        FORECAST_URL,
        params={
            "lat": latitude,
            "lon": longitude,
            "appid": API_KEY,
            "units": "metric",
        },
        timeout=REQUEST_TIMEOUT,
    )

    try:
        forecast_data = forecast_response.json()
    except ValueError:
        forecast_data = {}

    if forecast_response.status_code != 200:
        message = forecast_data.get(
            "message",
            "Unable to fetch the forecast.",
        )
        raise ValueError(message.title())

    return {
        "ok": True,
        "current": build_current(current_data),
        "hourly": build_hourly(forecast_data),
        "daily": build_daily(forecast_data),
        "meta": {
            "requested_city": current_data.get("name", "My Location"),
            "latitude": latitude,
            "longitude": longitude,
            "fetched_at": int(datetime.now(tz=timezone.utc).timestamp()),
        },
    }


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/weather")
def weather_api():
    city = request.args.get("city", "").strip()

    if not city:
        return api_error("Please enter a city name.")

    if not API_KEY:
        return api_error("Weather service is not configured.", 503)

    try:
        return jsonify(fetch_weather(city))
    except requests.RequestException:
        return api_error(
            "Unable to connect to the weather service. Please try again.",
            503,
        )
    except ValueError as exc:
        return api_error(str(exc), 400)
    except RuntimeError as exc:
        return api_error(str(exc), 503)
    except Exception:
        app.logger.exception("Unexpected weather API error")
        return api_error(
            "Something went wrong. Please try again.",
            500,
        )


@app.get("/api/weather/location")
def weather_location_api():
    latitude = request.args.get("lat", "").strip()
    longitude = request.args.get("lon", "").strip()

    if not latitude or not longitude:
        return api_error("Location coordinates are required.")

    try:
        lat = float(latitude)
        lon = float(longitude)

        if not (-90 <= lat <= 90):
            return api_error("Invalid latitude.")

        if not (-180 <= lon <= 180):
            return api_error("Invalid longitude.")

    except ValueError:
        return api_error("Invalid location coordinates.")

    if not API_KEY:
        return api_error("Weather service is not configured.", 503)

    try:
        return jsonify(fetch_weather_by_coordinates(lat, lon))
    except requests.RequestException:
        return api_error(
            "Unable to connect to the weather service. Please try again.",
            503,
        )
    except ValueError as exc:
        return api_error(str(exc), 400)
    except RuntimeError as exc:
        return api_error(str(exc), 503)
    except Exception:
        app.logger.exception("Unexpected location weather error")
        return api_error(
            "Something went wrong while getting your location.",
            500,
        )


@app.get("/health")
def health():
    return jsonify(
        {
            "ok": True,
            "weather_service_configured": bool(API_KEY),
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
    )
